#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""coqtop_batch.py - batch statement feed through coqtop with error classification (rocqwash tools/).
Purpose.  One deterministic batch face for the external-evaluation gap
  finding "coqtop-stdin multi-error batch collection": feeds one statement
  file to coqtop over stdin, chunks the transcript on the prompt markers,
  and classifies per-statement outcomes (ok / error with the captured
  message lines / unmatched tail), so a multi-error session yields every
  error at once with statement attribution instead of one-compile-one-error
  triage (probe_engine.py covers the single-error compile face; this tool
  covers the interactive batch face).  Zero network, zero files written
  beyond the caller-named --json.
Interface.  python -I tools/coqtop_batch.py --input FILE [--coqtop BIN]
  [--timeout SEC] [--json OUT] | --selftest.  Binary resolves per flag,
  then ROCWASH_COQTOP, then honest skip 111 (verify/ convention: judged
  nothing, reported not simulated).  Exit-codes.  0 clean transcript; 1
  errors found (classified, rc is data); 2 usage; 9 binary configured but
  missing, launch failure, or timeout (fail-loud); 111 honest skip;
  --selftest red = 1.  The selftest never launches a toolchain: the
  classification vectors run over canned transcript fixtures and the
  resolution/exit vectors over the pure faces (the live face is exercised
  by the operator with the on-machine toolchain, not by CI).
Dependencies.  Python 3 standard library only; coqtop binary from flags
  or environment (never downloaded, never simulated).
Evidence.  Deterministic: the same transcript bytes give the
  byte-identical report on a double run (sorted keys, no wall clock).
  Thermal: no embedded guard, wrap guarded real runs in
  tools/cpu_guard.sh (the coqtop child stays in the guard's process
  tree; the selftest and the honest-skip face never launch a toolchain).
"""
# Extended contract:
# Chunking.  The transcript is split on the frozen prompt marker
#   "Coq < " at line starts; chunk i carries the output produced while
#   statement i+1 was being read (the prompt precedes each read).  The
#   pre-first-prompt head is the banner chunk (unattributed).  Each
#   chunk's verdict: "error" when it contains a line matching the frozen
#   error regex (^Error:|^Error ) with the message captured to the next
#   blank line or chunk end; else "ok".  The tail after the last prompt
#   is the "unmatched" face (never silently dropped).
# Statement attribution.  Statements are counted as the prompt chunks;
#   the report lists one row per prompt chunk {index, verdict,
#   error_message[]} plus the unmatched tail if non-empty.
import argparse
import io
import json
import os
import re
import subprocess
import sys

PROG = "coqtop_batch"
SCHEMA = "rocqwash-coqtop-batch/1"
PROMPT_RE = re.compile(r"^(?:Rocq|Coq) < ", re.M)  # 9.3 renamed the prompt; both eras match
ERROR_RE = re.compile(r"^(Error:|Error )", re.M)
SKIP_LINE = ("SKIP: coqtop not configured (flag or ROCWASH_COQTOP); the "
             "batch collector honestly skips and judges nothing (rc 111)")


def chunk_transcript(text):
    """Split the transcript on prompt markers; returns (chunks, tail) with
    chunks a list of output strings (chunk i = output after prompt i) and
    tail the post-last-prompt remainder ("" when the transcript ends on a
    prompt)."""
    marks = [m.start() for m in PROMPT_RE.finditer(text)]
    if not marks:
        return [], text
    chunks = []
    for i, start in enumerate(marks):
        end = marks[i + 1] if i + 1 < len(marks) else len(text)
        chunks.append(text[start:end])
    tail = ""
    # the last prompt chunk may carry trailing output after the final
    # prompt line plus its reading; that stays inside the chunk - the
    # "unmatched" face is output BEFORE the first prompt (banner)
    head_end = marks[0]
    tail = text[:head_end]
    return chunks, tail


def extract_error(chunk):
    """Returns the list of error message blocks (each a list of lines from
    the Error line to the next blank line or chunk end), [] when clean."""
    blocks = []
    pos = 0
    while True:
        m = ERROR_RE.search(chunk, pos)
        if m is None:
            break
        lines = []
        for ln in chunk[m.start():].splitlines():
            if not ln.strip() and lines:
                break
            lines.append(ln)
        blocks.append(lines)
        pos = m.start() + sum(len(l) + 1 for l in lines)
    return blocks


def classify_transcript(text):
    """The pure classification face: returns the report rows."""
    chunks, banner = chunk_transcript(text)
    rows = []
    for i, chunk in enumerate(chunks):
        blocks = extract_error(chunk)
        rows.append({
            "index": i,
            "verdict": "error" if blocks else "ok",
            "error_message": ["\n".join(b) for b in blocks],
        })
    return rows, banner


def run_batch(binary, text, timeout):
    """Feed text to coqtop stdin; returns (rc, transcript, error) with
    error None on a clean launch, "timeout", or an OS message string."""
    try:
        p = subprocess.run([binary, "-q", "-quiet"], input=text.encode("utf-8"),
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           timeout=timeout)
        out = p.stdout.decode("utf-8", "replace").replace("\r\n", "\n")
        return p.returncode, out, None
    except subprocess.TimeoutExpired as e:
        partial = (e.stdout or b"").decode("utf-8", "replace")
        return None, partial, "timeout"
    except OSError as e:
        return None, "", str(e)


def resolve_binary(flag_value):
    if flag_value:
        return flag_value, None
    env = os.environ.get("ROCWASH_COQTOP", "")
    if env:
        return env, None
    return None, SKIP_LINE


def build_report(input_path, binary, transcript, rows, banner, note):
    return {
        "schema": SCHEMA,
        "input": input_path,
        "coqtop": binary,
        "statements": len(rows),
        "errors": sum(1 for r in rows if r["verdict"] == "error"),
        "banner_unmatched": banner[-200:] if banner else "",
        "note": note or "",
        "rows": rows,
    }


def main():
    argv = sys.argv[1:]
    if "--selftest" in argv:
        if len(argv) != 1:
            print("FAIL: --selftest takes no other flags", file=sys.stderr)
            sys.exit(2)
        sys.exit(selftest())
    ap = argparse.ArgumentParser(prog=PROG,
                                 description="coqtop batch statement feed "
                                             "with per-statement error "
                                             "classification")
    ap.add_argument("--input", required=True, help="statements file")
    ap.add_argument("--coqtop", default="",
                    help="coqtop binary (default ROCWASH_COQTOP)")
    ap.add_argument("--timeout", type=int, default=300,
                    help="per-run timeout seconds (default 300)")
    ap.add_argument("--json", dest="json_out", default=None,
                    help="report output path (absent = stdout)")
    args = ap.parse_args(argv)
    if not os.path.isfile(args.input):
        print("FAIL-LOUD: --input path missing: %s" % args.input,
              file=sys.stderr)
        sys.exit(9)
    binary, skip_line = resolve_binary(args.coqtop)
    if binary is None:
        print(skip_line, file=sys.stderr)
        sys.exit(111)
    if not os.path.exists(binary):
        print("FAIL-LOUD: coqtop configured but binary missing: %s" % binary,
              file=sys.stderr)
        sys.exit(9)
    with io.open(args.input, "r", encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    rc, transcript, err = run_batch(binary, text, args.timeout)
    if err is not None:
        print("FAIL-LOUD: coqtop launch failure (%s)" % err, file=sys.stderr)
        sys.exit(9)
    rows, banner = classify_transcript(transcript)
    report = build_report(args.input, binary, transcript, rows, banner, "")
    blob = json.dumps(report, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    if args.json_out:
        with io.open(args.json_out, "w", encoding="utf-8", newline="") as fh:
            fh.write(blob)
        print("report -> %s" % args.json_out)
    else:
        sys.stdout.write(blob)
    print("coqtop-batch: statements=%d errors=%d coqtop-rc=%s"
          % (len(rows), sum(1 for r in rows if r["verdict"] == "error"), rc))
    sys.exit(1 if any(r["verdict"] == "error" for r in rows) else 0)


# ---- selftest (offline vectors over canned transcripts; zero toolchain) ----

CLEAN_TEXT = "Welcome to Rocq\n\nRocq < Lemma ok : 1 = 1.\n     \nRocq < \n"
ERROR_TEXT = ("Welcome\n\n"
              "Rocq < Lemma bad : 1 = 2.\n"
              "Error: The statement proved to be false.\n"
              "\n"
              "Rocq < Qed.\n")


def selftest():
    import tempfile
    failures = []
    total = [0]

    def vec(name, ok, detail):
        total[0] += 1
        print(("PASS " if ok else "FAIL ") + name + " - " + detail)
        if not ok:
            failures.append(name)

    rows, banner = classify_transcript(CLEAN_TEXT)
    vec("clean-transcript", len(rows) == 2 and
        all(r["verdict"] == "ok" for r in rows) and
        "Welcome" in banner,
        "rows=%d banner=%r" % (len(rows), banner[:20]))
    rows, _ = classify_transcript(ERROR_TEXT)
    vec("error-attribution", len(rows) == 2 and
        rows[0]["verdict"] == "error" and rows[1]["verdict"] == "ok" and
        "proved to be false" in rows[0]["error_message"][0],
        "row0=%s" % rows[0]["verdict"])
    rows, _ = classify_transcript(
        "Coq < a.\nError: one.\n\nCoq < b.\nError: two.\n\n")
    vec("multi-error-batch", len(rows) == 2 and
        all(r["verdict"] == "error" and len(r["error_message"]) == 1
            for r in rows) and "one" in rows[0]["error_message"][0]
        and "two" in rows[1]["error_message"][0],
        "both statements carry their own error")
    # determinism face: the same bytes classify identically twice
    a = classify_transcript(ERROR_TEXT)
    b = classify_transcript(ERROR_TEXT)
    vec("double-run-identical", a == b, "pure function identity")
    # resolution order: flag wins over env; neither -> skip line
    b1, s1 = resolve_binary("flag.bin")
    b2, s2 = resolve_binary("")
    vec("resolution-order", b1 == "flag.bin" and s1 is None
        and b2 is None and s2 == SKIP_LINE,
        "flag > env > honest skip")
    # no-prompt transcript: everything lands in the banner tail
    rows, banner = classify_transcript("no prompts at all\nError: x\n")
    vec("no-prompt-banner", rows == [] and "Error: x" in banner,
        "rows=%d banner-has-error=True" % len(rows))
    rows, _ = classify_transcript(
        "Rocq < Lemma a.\n"
        "a < Proof.\n"
        "a < Qed.\n"
        "Rocq < Lemma b.\n"
        "Error: no such b.\n"
        "\n")
    vec("nested-proof-prompts-one-chunk", len(rows) == 2 and
        rows[0]["verdict"] == "ok" and rows[1]["verdict"] == "error",
        "a proof session stays one chunk; rows=%d" % len(rows))
    print("COQTOP-BATCH-SELFTEST: %d vector(s), %d FAIL"
          % (total[0], len(failures)))
    return 1 if failures else 0


if __name__ == "__main__":
    main()
