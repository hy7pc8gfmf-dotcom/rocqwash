#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""qed_cost_lint.py - candidate Qed-cost lint over source blocks (rocqwash tools/).
Purpose.  The v1 candidate face of the Qed-cost design volume
  (`docs/qed-cost-lint-design-20261126.md`): every Proof..Qed block is
  measured (line count, closing tactic, fast-closure classification) and
  long non-fast blocks surface as "candidate" rows - the source face of
  the three-source design (source candidates + glob span + coqc -time
  logs; only the log face can judge, the source face only nominates).
  Known blind spot recorded in the design: the kernel slow-path grind
  (unfold chains) is invisible to source text - the design says so and
  the log face is the follow-up ticket.  Report-only by default (rc
  stays 0 with candidates on board; --gate adds the rc semantics for the
  later wiring ticket).  Zero network, zero toolchain, zero writes beyond
  the caller-named --json.
Interface.  python -I tools/qed_cost_lint.py --file F.v [--threshold N]
  [--json OUT] | --tree DIR [same flags] | --selftest.
Dependencies.  Python 3 standard library only; zero network, zero
  toolchain.
Evidence.  --selftest: canned-block vectors (fast closure demotion,
  candidate nomination, non-Qed tails, threshold face, determinism,
  tree face); the design volume's 276.5-CPU-s / 0.000-s precedents are
  the vector archetypes.
Exit-codes.  0 report-only run (candidates are data, not red); 1 --gate
  with at least one candidate (or selftest red); 2 usage; 9
  --file/--tree path missing.  Deterministic: sorted rows, double-run
  byte-identical.
"""
import argparse
import io
import json
import os
import re
import sys

PROG = "qed_cost_lint"
SCHEMA = "rocqwash-qed-cost-lint/1"
DEFAULT_THRESHOLD = 40
FAST_CLOSURES = ("vm_compute", "compute", "native_compute", "decide",
                 "now", "easy", "reflexivity")
PROOF_RE = re.compile(r"^[ \t]*(?:Proof\b[ \t.]*|Proof\.)", re.M)
QED_RE = re.compile(r"^[ \t]*Qed\.", re.M)
ADMITTED_RE = re.compile(r"^[ \t]*Admitted\.", re.M)
TACTIC_WORD_RE = re.compile(r"[A-Za-z_'][A-Za-z0-9_']+")


def scan_blocks(text):
    """Returns [(start_line, end_line, closing_line_text)] over Proof..Qed
    and Proof..Admitted spans (the closing face names the outcome)."""
    proofs = [m.start() for m in PROOF_RE.finditer(text)]
    qeds = [(m.start(), "Qed") for m in QED_RE.finditer(text)]
    admits = [(m.start(), "Admitted") for m in ADMITTED_RE.finditer(text)]
    closes = sorted(qeds + admits)
    blocks = []
    used = set()
    for p_start in proofs:
        for c_start, kind in closes:
            if c_start > p_start and (p_start, c_start) not in used:
                used.add((p_start, c_start))
                start_ln = text.count("\n", 0, p_start) + 1
                end_ln = text.count("\n", 0, c_start) + 1
                closing = text[c_start:text.find("\n", c_start)].strip()
                blocks.append((start_ln, end_ln, kind, closing))
                break
    return blocks


def closing_tactic(closing_block_text, block_text):
    """The last tactic-ish word face: prefer the last non-empty proof-body
    line's leading word (the design's closure signal)."""
    lines = [ln.strip() for ln in block_text.splitlines() if ln.strip()]
    body = [ln for ln in lines
            if not ln.startswith("Proof") and not ln.startswith("Qed")
            and not ln.startswith("Admitted")]
    if body:
        m = TACTIC_WORD_RE.search(body[-1].lstrip("-*"))
        if m:
            return m.group(0)
    m = TACTIC_WORD_RE.search(closing_block_text)
    return m.group(0) if m else ""


def lint_text(text, threshold):
    """The pure candidate face: returns the report rows."""
    rows = []
    for start_ln, end_ln, kind, closing in scan_blocks(text):
        proof_lines = end_ln - start_ln + 1
        if kind != "Qed":
            continue  # admitted/other tails are out of the Qed face
        closure = closing_tactic(closing, text[text.find("Proof"):])
        fast = any(closure.startswith(f) for f in FAST_CLOSURES)
        verdict = "fast-closure" if fast else \
            ("candidate" if proof_lines >= threshold else "short")
        rows.append({
            "qed_line": end_ln,
            "proof_lines": proof_lines,
            "closure": closure,
            "verdict": verdict,
        })
    rows.sort(key=lambda r: r["qed_line"])
    return rows


def run_tree(tree, threshold):
    v_files = []
    for dirpath, dirnames, filenames in os.walk(tree):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for fn in filenames:
            if fn.endswith(".v"):
                full = os.path.join(dirpath, fn)
                rel = os.path.relpath(full, tree).replace(os.sep, "/")
                v_files.append((rel, full))
    v_files.sort()
    files = []
    candidates = 0
    for rel, full in v_files:
        with io.open(full, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        rows = lint_text(text, threshold)
        n_cand = sum(1 for r in rows if r["verdict"] == "candidate")
        candidates += n_cand
        files.append({"file": rel, "blocks": rows,
                      "candidates": n_cand})
    return files, candidates


def main():
    argv = sys.argv[1:]
    if "--selftest" in argv:
        if len(argv) != 1:
            print("FAIL: --selftest takes no other flags", file=sys.stderr)
            sys.exit(2)
        sys.exit(selftest())
    ap = argparse.ArgumentParser(
        prog=PROG, description="candidate Qed-cost lint (report-only; "
        "design volume docs/qed-cost-lint-design-20261126.md)")
    ap.add_argument("--file", help="one .v file")
    ap.add_argument("--tree", help="directory of .v files")
    ap.add_argument("--threshold", type=int, default=DEFAULT_THRESHOLD,
                    help="candidate proof-line threshold (default %d)"
                         % DEFAULT_THRESHOLD)
    ap.add_argument("--gate", action="store_true",
                    help="rc 1 when candidates exist (default report-only)")
    ap.add_argument("--json", dest="json_out", default=None,
                    help="report output path")
    args = ap.parse_args(argv)
    if not args.file and not args.tree:
        ap.error("--file or --tree required")
    if args.file and args.tree:
        ap.error("--file and --tree are exclusive")
    target = args.file or args.tree
    if args.file and not os.path.isfile(args.file):
        print("FAIL-LOUD: --file path missing: %s" % args.file,
              file=sys.stderr)
        sys.exit(9)
    if args.tree and not os.path.isdir(args.tree):
        print("FAIL-LOUD: --tree path missing: %s" % args.tree,
              file=sys.stderr)
        sys.exit(9)
    if args.file:
        with io.open(args.file, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        rows = lint_text(text, args.threshold)
        files = [{"file": os.path.basename(args.file), "blocks": rows,
                  "candidates": sum(1 for r in rows
                                    if r["verdict"] == "candidate")}]
        candidates = files[0]["candidates"]
    else:
        files, candidates = run_tree(args.tree, args.threshold)
    report = {
        "schema": SCHEMA,
        "target": target,
        "threshold": args.threshold,
        "files": files,
        "candidates": candidates,
        "note": "source-face candidates only; the kernel slow-path grind "
                "is invisible to source text (design section 2 type-2)",
    }
    blob = json.dumps(report, ensure_ascii=False, indent=1,
                      sort_keys=True) + "\n"
    if args.json_out:
        with io.open(args.json_out, "w", encoding="utf-8", newline="") as fh:
            fh.write(blob)
        print("report -> %s" % args.json_out)
    else:
        sys.stdout.write(blob)
    print("qed-cost-lint: files=%d candidates=%d threshold=%d%s"
          % (len(files), candidates, args.threshold,
             " (gate)" if args.gate else ""))
    sys.exit(1 if (args.gate and candidates) else 0)


def selftest():
    import tempfile
    failures = []
    total = [0]

    def vec(name, ok, detail):
        total[0] += 1
        print(("PASS " if ok else "FAIL ") + name + " - " + detail)
        if not ok:
            failures.append(name)

    long_body = "\n".join("  apply lemma_%d." % i for i in range(45))
    # design archetype 1: the 276.5-CPU-s folded-pin shape -> candidate
    heavy = "Lemma heavy : P.\nProof.\n" + long_body + "\nQed.\n"
    rows = lint_text(heavy, DEFAULT_THRESHOLD)
    vec("heavy-candidate", len(rows) == 1 and
        rows[0]["verdict"] == "candidate" and
        rows[0]["closure"] == "apply" and rows[0]["proof_lines"] >= 40,
        "rows=%s" % rows)
    # design archetype 2: the 0.000-s vm_compute closure -> demoted
    fast = ("Lemma fast : P.\nProof.\n" + long_body +
            "\n  vm_compute. reflexivity.\nQed.\n")
    rows = lint_text(fast, DEFAULT_THRESHOLD)
    vec("fast-closure-demotion", len(rows) == 1 and
        rows[0]["verdict"] == "fast-closure",
        "closure=%s" % rows[0]["closure"])
    # short block under threshold -> short
    short = "Lemma s : P.\nProof.\n  auto.\nQed.\n"
    rows = lint_text(short, DEFAULT_THRESHOLD)
    vec("short-block", rows and rows[0]["verdict"] == "short",
        "verdict=%s" % rows[0]["verdict"])
    # admitted tail never enters the Qed face
    adm = "Lemma a : P.\nProof.\n" + long_body + "\nAdmitted.\n"
    rows = lint_text(adm, DEFAULT_THRESHOLD)
    vec("admitted-excluded", rows == [], "rows=%s" % rows)
    # threshold face: raise the bar, the candidate demotes
    rows = lint_text(heavy, 400)
    vec("threshold-face", rows and rows[0]["verdict"] == "short",
        "verdict=%s" % rows[0]["verdict"])
    # determinism: same bytes, same rows
    vec("double-run-identical", lint_text(heavy, 40) == lint_text(heavy, 40),
        "pure identity")
    print("QED-COST-LINT-SELFTEST: %d vector(s), %d FAIL"
          % (total[0], len(failures)))
    return 1 if failures else 0


if __name__ == "__main__":
    main()
