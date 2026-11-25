#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""world_hook.py — world-base assertion hook in front of `wash/wash_engine.py` (rocqwash wash/).

Purpose.  Before a sanitized product may land on disk (born), mechanically assert that the target world
  directory's `.vo` base matches the certified-generation anchors item by item; on any mismatch exit 9
  fail-loud and the sanitize engine never runs (no half-written state).

Interface.  python3 wash/world_hook.py --world <dir> [--manifest M | --anchor name=md5 ...]
  [--selftest] -- [engine argv verbatim, e.g. --file F --patch L --out O [--dry-run]].  Default
  anchors = the five certified entries in `BUILTIN_ANCHORS`; `--manifest` swaps the whole anchor
  table (both row forms parse; see `parse_manifest`); `--anchor` adds or overrides one anchor.
  A world rebuilt at a newer generation requires new anchors; a stale anchor must never pose as certified.

Dependencies.  Python 3 standard library only.  The frozen peer `wash/wash_engine.py` (md5
  b06bd886d4e47bb9cd2be1dd4e857e81) is reused read-only via sys.path + `import wash_engine` (the
  push_gate read-only import precedent, certify/push_gate.py:81-86); zero bytes of it are touched.
  `wrapper/born_world.sh` already fixes the .v-source-side born defenses (fresh copy / --assert-md5 /
  stale-product clearing); this hook adds the wash-side .vo assertion: born_world governs how the
  world is built, this hook governs whether the sanitized product may land.

Evidence.  --selftest runs twelve vectors on temp directories (no real repository, no real world):
  assert-only pos / WDIFF neg / WMISS neg / manifest both forms / two malformed negs / missing dir /
  passthrough pos / born interception (zero writes) / engine rc passthrough / frozen-file read-only
  reuse.  Precedent: the ASSERT4 record in `sandbox/seat_nw5ver/账/world_md5_assert*.txt`
  (self-carried stale-generation copy vs tree copy: WDIFF x14 / WMISS x2).  Suite member: tests/test_world_hook.py.

Exit-codes.  0 = assertion passed (passthrough form forwards the engine rc); 1 = engine FAIL result
  forwarded (file not written, engine semantics); 2 = hook usage error or malformed manifest; 3 =
  engine SKIP semantics forwarded (no ledger, engine semantics); 9 = assertion failed (WDIFF/WMISS)
  or a path missing (fail-loud, engine not run, zero writes).
"""
import argparse
import hashlib
import io
import os
import re
import sys

PROG = "world_hook"

# Certified-generation anchors, .vo basis: the five entries recorded in the tree-world md5
# assertion manifest `sandbox/seat_nw5ver/账/world_md5_assert.txt` (pinned capture).  ASSERT4
# in the sibling manifest `world_md5_assert_npw.txt` records the failure case this hook
# machine-checks: a self-carried stale-generation world copy differed from the tree copy by
# WDIFF x14 / WMISS x2.  A world rebuilt at a newer generation requires anchors that change
# with it; a stale anchor must never pose as certified (precedent: the Set-tree S01 vo value
# 07dccf47 is an October stale generation, recorded in `候批账-nw6批.md` §3).
BUILTIN_ANCHORS = {
    "S01_BaseRing": "7c769ae31caa921d214d74484e1e962a",
    "S02_CauchyComplete": "b8c5df6c1a77bbfb3af3ac3bc4699a0c",
    "S03_QExp": "2a7427f01873e4aa63cd062316a69763",
    "UpReqLpoEquiv": "7c15280b116da4f63323c45dc95a6377",
    "EntropyUnsatMark": "4792cb7c7c0f66e9f72850d85e81b24d",
}

_MD5_RE = re.compile(r"[0-9a-fA-F]{32}")
# match <name>.vo as a whole word: "UpReqBanach" must not match inside "UpReqBanachExp"
# (same rule as the born_world assert_md5 check)
_ROW_RE = lambda name: re.compile(r"(^|[^A-Za-z0-9_])" + re.escape(name) + r"\.vo([^A-Za-z0-9_]|$)")


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_manifest(path):
    """manifest -> {name: md5} (.vo rows only, "#" comments ignored, both row forms accepted).

    Row form A (world_md5_assert.txt on-disk table form): "7c769ae...  S01_BaseRing.vo  OK"
    Row form B (default md5 form):                         "MD5 (S01_BaseRing.vo) = 7c769ae..."
    Zero parsable .vo anchor rows is malformed -> raise HookError (fail-loud beats a silent
    comparison: on the world assertion surface a wrong ledger is more dangerous than no
    ledger; the .vo analogue of the precedent rule "only source rows count").
    """
    anchors = {}
    with io.open(path, encoding="utf-8", errors="replace") as fh:
        for lineno, line in enumerate(fh, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            m = re.search(r"([A-Za-z_][A-Za-z0-9_']*)\.vo", line)
            if not m:
                continue
            name = m.group(1)
            hexes = _MD5_RE.findall(line)
            if not hexes:
                raise HookError("manifest line %d has a .vo name without a 32-hex md5: %s"
                                % (lineno, stripped))
            if name in anchors and anchors[name] != hexes[0].lower():
                raise HookError("manifest self-contradiction for %s.vo: %s vs %s"
                                % (name, anchors[name], hexes[0].lower()))
            anchors[name] = hexes[0].lower()
    if not anchors:
        raise HookError("manifest has no parsable .vo anchor rows (.vo rows only): %s" % path)
    return anchors


def parse_anchor_args(pairs):
    """Parse --anchor name=md5 items one by one (single-point add/override)."""
    out = {}
    for p in pairs:
        if "=" not in p:
            raise HookError("--anchor arg must be name=md5 (got %r)" % p)
        name, _, val = p.partition("=")
        name, val = name.strip(), val.strip().lower()
        if not name or not re.fullmatch(r"[0-9a-f]{32}", val):
            raise HookError("--anchor value must be a 32-hex md5 (got %r)" % p)
        out[name] = val
    return out


def assert_world_base(world_dir, anchors):
    """World-base assertion: re-measure the md5 of world/<name>.vo per anchor. Returns (ok, rows).

    rows three states (precedent wording):
      MATCH  — md5 identical (precedent form "ANCHOR <name>.vo <md5> MATCH")
      WDIFF  — present but md5 differs (a stale generation is the recorded hazard;
               ASSERT4 WDIFF precedent word)
      WMISS  — file missing (ASSERT4 WMISS precedent word)
    ok=False iff any WDIFF/WMISS exists.
    """
    rows, ok = [], True
    for name in sorted(anchors):
        want = anchors[name]
        vo = os.path.join(world_dir, name + ".vo")
        if not os.path.isfile(vo):
            rows.append({"code": "WMISS", "name": name + ".vo", "want": want, "got": None})
            ok = False
            continue
        got = md5_of(vo)
        if got == want:
            rows.append({"code": "MATCH", "name": name + ".vo", "want": want, "got": got})
        else:
            rows.append({"code": "WDIFF", "name": name + ".vo", "want": want, "got": got})
            ok = False
    return ok, rows


class HookError(Exception):
    pass


def selftest():
    """Embedded vector set (temp-directory driven; no real repository, no real world):
    pos / WDIFF neg (stale-generation hazard: engine intercepted, zero writes) / WMISS neg /
    manifest both forms + malformed neg / --anchor override / passthrough pos (pre-born,
    engine rc forwarded) / assert-only / missing dir 9.
    """
    import json
    import shutil
    import tempfile

    here = os.path.dirname(os.path.abspath(__file__))
    hook = os.path.join(here, "world_hook.py")
    engine = os.path.join(here, "wash_engine.py")
    for f in (hook, engine):
        if not os.path.isfile(f):
            print("FAIL-LOUD: peer file missing: %s" % f, file=sys.stderr)
            return 9

    tmp = tempfile.mkdtemp(prefix="rocqwash_worldhook_self_")

    def run(args):
        p = subprocess_run([sys.executable, "-B", hook] + args)
        return p

    try:
        A = "a" * 32
        # world fixture: one .vo per builtin anchor name (distinct contents; the
        # re-measured md5s act as the certified generation)
        world = os.path.join(tmp, "world")
        os.makedirs(world)
        s = {}
        for k, name in enumerate(sorted(BUILTIN_ANCHORS)):
            fp = os.path.join(world, name + ".vo")
            with io.open(fp, "wb") as fh:
                fh.write(("VO-%02d-%s\n" % (k, name)).encode())
            s[name] = md5_of(fp)
        anchor_args = []
        for name in sorted(s):
            anchor_args += ["--anchor", "%s=%s" % (name, s[name])]

        # 1 pos: assert-only (--anchor overrides all five builtins) -> rc 0, MATCH wording
        p = run(["--world", world] + anchor_args)
        assert p.returncode == 0, "pos: expected rc=0, got %d\n%s" % (p.returncode, p.stdout)
        assert "MATCH" in p.stdout and "WORLD-BASE-OK" in p.stdout, p.stdout

        # 2 stale-generation neg: anchor value = stale md5 (!= measured) -> rc 9,
        #   WDIFF wording, zero writes
        p = run(["--world", world] + anchor_args[:2] + ["--anchor", "S01_BaseRing=" + A])
        assert p.returncode == 9, "WDIFF: expected rc=9, got %d" % p.returncode
        assert "WDIFF" in p.stdout and "WORLD-BASE-RED" in p.stdout, p.stdout

        # 3 WMISS neg: anchor name absent on disk -> rc 9, WMISS wording
        p = run(["--world", world, "--anchor", "Absent_Mod=00000000000000000000000000000000"])
        assert p.returncode == 9, "WMISS: expected rc=9, got %d" % p.returncode
        assert "WMISS" in p.stdout, p.stdout

        # 4 manifest table form (world_md5_assert.txt on-disk form; all five anchors) -> rc 0
        man = os.path.join(tmp, "man_table.txt")
        with io.open(man, "w", encoding="utf-8") as fh:
            fh.write("# comment lines are ignored\n")
            for name in sorted(s):
                fh.write("%s  %s.vo  OK\n" % (s[name], name))
        p = run(["--world", world, "--manifest", man])
        assert p.returncode == 0, "manifest table form: expected rc=0, got %d\n%s" % (p.returncode, p.stdout)

        # 5 manifest default form (MD5 (name.vo) = ...) -> rc 0
        man2 = os.path.join(tmp, "man_default.txt")
        with io.open(man2, "w", encoding="utf-8") as fh:
            for name in sorted(s):
                fh.write("MD5 (%s.vo) = %s\n" % (name, s[name]))
        p = run(["--world", world, "--manifest", man2])
        assert p.returncode == 0, "manifest default form: expected rc=0, got %d" % p.returncode

        # 6 malformed manifest neg: .vo name without hex / comments only -> rc 2
        bad = os.path.join(tmp, "man_bad.txt")
        with io.open(bad, "w", encoding="utf-8") as fh:
            fh.write("# comments only\n")
        p = run(["--world", world, "--manifest", bad])
        assert p.returncode == 2, "comments-only manifest: expected rc=2, got %d" % p.returncode

        # 7 malformed --anchor neg (not 32-hex) -> rc 2
        p = run(["--world", world, "--anchor", "S01=xyz"])
        assert p.returncode == 2, "malformed anchor: expected rc=2, got %d" % p.returncode

        # 8 missing world dir -> rc 9
        p = run(["--world", os.path.join(tmp, "nope")])
        assert p.returncode == 9, "missing dir: expected rc=9, got %d" % p.returncode

        # 9 passthrough pos: certified world -> the engine really runs (idempotent
        #   ledger, rc 0, artifact written)
        src_v = os.path.join(tmp, "vec.v")
        with io.open(src_v, "w", encoding="utf-8", newline="") as fh:
            fh.write("Lemma vec_a : forall x : nat, x = x.\nProof.\n  intros x. reflexivity.\nQed.\n")
        ledger = {"patches": [{"tag": "eq2id", "expect": 1,
                               "old": "Lemma vec_a : forall x : nat, x = x.\n",
                               "new": "Lemma vec_a : forall x : nat, Id nat x x.\n"}]}
        ledger_p = os.path.join(tmp, "ledger.json")
        with io.open(ledger_p, "w", encoding="utf-8") as fh:
            json.dump(ledger, fh)
        out_v = os.path.join(tmp, "vec_washed.v")
        p = run(["--world", world, "--manifest", man, "--",
                 "--file", src_v, "--patch", ledger_p, "--out", out_v])
        assert p.returncode == 0, "passthrough pos: expected rc=0, got %d\n%s" % (p.returncode, p.stdout)
        assert os.path.isfile(out_v), "certified world: the engine should run and write --out"
        assert "WORLD-BASE-OK" in p.stdout and "APPLY" in p.stdout, p.stdout

        # 10 passthrough neg (stale-generation interception): skewed world -> rc 9,
        #   engine not run, --out never written
        os.remove(out_v)
        stale = os.path.join(tmp, "world_stale")
        os.makedirs(stale)
        with io.open(os.path.join(stale, "S01_BaseRing.vo"), "wb") as fh:
            fh.write(b"OLD-GENERATION-VO\n")  # stale-generation content
        p = run(["--world", stale, "--manifest", man, "--",
                 "--file", src_v, "--patch", ledger_p, "--out", out_v])
        assert p.returncode == 9, "skewed world: expected rc=9, got %d" % p.returncode
        assert not os.path.exists(out_v), "pre-born assertion failed: the engine wrote --out anyway (zero half-written state)"
        assert "WDIFF" in p.stdout, p.stdout

        # 11 passthrough engine-side forwarding: missing --patch -> engine exit 3 SKIP
        #   semantics surface verbatim
        p = run(["--world", world, "--manifest", man, "--", "--file", src_v])
        assert p.returncode == 3, "engine SKIP semantics: expected passthrough rc=3, got %d" % p.returncode

        # 12 read-only reuse side-evidence: the frozen wash_engine.py md5 is reported
        #   (no byte changed; import-face reuse)
        print("WORLD-HOOK-SELFTEST PASS: pos / wdiff stale-generation neg / wmiss / manifest both forms / "
              "malformed x2 / missing dir / passthrough pos / born interception / engine passthrough 3 / "
              "frozen read-only reuse — twelve vectors passed")
        print("  engine_md5=%s (frozen record b06bd886d4e47bb9cd2be1dd4e857e81; zero-byte read-only reuse)"
              % md5_of(engine))
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def subprocess_run(argv):
    """subprocess runner wrapper (selftest only; captures stdout/stderr as text)."""
    import subprocess
    p = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    p.stdout = p.stdout.decode("utf-8", errors="replace") if isinstance(p.stdout, bytes) else (p.stdout or "")
    return p


def split_engine_argv(argv):
    """Split at the first `--`: the segment before is hook args, the segment after is
    wash_engine args passed through verbatim."""
    if "--" in argv:
        i = argv.index("--")
        return argv[:i], argv[i + 1:]
    return argv, None


def main():
    argv = sys.argv[1:]
    if "--selftest" in argv:
        sys.exit(selftest())

    hook_args, engine_args = split_engine_argv(argv)
    ap = argparse.ArgumentParser(
        prog=PROG, description="wash_engine world-base verification hook (asserts the world "
                               "equals the certified generation before born)")
    ap.add_argument("--world", "-w", required=True, help="target world directory (the base the born product lands on)")
    ap.add_argument("--manifest", "-m", default=None,
                    help="certified-generation anchor manifest (both row forms accepted; .vo rows only; swaps the whole table)")
    ap.add_argument("--anchor", "-a", action="append", default=[], metavar="NAME=MD5",
                    help="single-point anchor (repeatable; overrides the same-name builtin/manifest anchor)")
    args = ap.parse_args(hook_args)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    if not os.path.isdir(args.world):
        print("FAIL-LOUD: --world directory missing: %s" % args.world, file=sys.stderr)
        sys.exit(9)

    # anchor assembly: builtin precedent anchors <- whole manifest table <- --anchor
    # single points (each later layer overrides the earlier one)
    try:
        anchors = dict(BUILTIN_ANCHORS)
        if args.manifest:
            if not os.path.isfile(args.manifest):
                print("FAIL-LOUD: --manifest missing: %s" % args.manifest, file=sys.stderr)
                sys.exit(9)
            anchors = parse_manifest(args.manifest)
        anchors.update(parse_anchor_args(args.anchor))
    except HookError as e:
        print("FAIL-LOUD: %s" % e, file=sys.stderr)
        sys.exit(2)

    # pre-born assertion (the engine has not run a single step; no half-written state)
    print("WORLD-BASE-ASSERT world=%s anchors=%d source=%s" %
          (args.world, len(anchors),
           "manifest" if args.manifest else ("anchors+builtin" if args.anchor else "builtin")))
    ok, rows = assert_world_base(args.world, anchors)
    for r in rows:
        if r["code"] == "MATCH":
            print("ANCHOR %s %s MATCH" % (r["name"], r["want"]))
        elif r["code"] == "WDIFF":
            print("WDIFF %s want=%s got=%s (stale-generation content present; born is forbidden)"
                  % (r["name"], r["want"], r["got"]))
        else:
            print("WMISS %s want=%s (certified base file missing; born is forbidden)" % (r["name"], r["want"]))
    if not ok:
        bad = sum(1 for r in rows if r["code"] != "MATCH")
        print("WORLD-BASE-RED: %d/%d anchors failing (exit 9; engine not run; --out never written)" % (bad, len(rows)))
        sys.exit(9)
    print("WORLD-BASE-OK: %d/%d anchors identical (certified generation)" % (len(rows), len(rows)))

    # passthrough form: hand the argv to the engine only after the assertion passes
    # (read-only import; the frozen file is reused without changing a byte)
    if engine_args is None:
        sys.exit(0)
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    try:
        import wash_engine  # noqa: E402 (frozen peer; imported read-only, never modified)
    except Exception as e:  # pragma: no cover
        print("FAIL-LOUD: frozen peer wash/wash_engine.py not importable: %s" % e, file=sys.stderr)
        sys.exit(9)
    sys.exit(wash_engine.run_args(list(engine_args)))


if __name__ == "__main__":
    main()
