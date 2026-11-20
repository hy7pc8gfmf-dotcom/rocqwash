#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_retrofit_dryrun.py — dry-run selftest for `verify/retrofit_gate7_irr.py` (rocqwash tests/).

Purpose.  Drive the real main() of `verify/retrofit_gate7_irr.py` over the fixture
  `tests/fixtures/retrofit_cn_sample.v` (a Chinese-comment sample) and mechanically prove
  the dry run writes nothing.  The tool takes no CLI arguments; SRC/OUT/FROZEN_MD5 are
  hardcoded module paths (`retrofit_gate7_irr.py:7-11`), so the test imports the module,
  patches the constants, and guards the io.open write channel: write requests are
  intercepted into memory and no byte reaches disk (the mechanical proof of a no-write
  dry run).  Criteria (all pass -> exit 0, any failure -> nonzero):
  R1 the fixture and the module anchor table mod.M are mechanically co-sourced
    (in-memory rebuild md5 == on-tree fixture md5);
  R2 the dry-run main() passes all built-in assertions (token-stream identity,
    line-count arithmetic, output ASCII — asserted inside main);
  R3 exactly one write-mode open, target exactly the patched OUT, and that
    path does not exist after the dry run (nothing on disk);
  R4 output CJK -> 0, non-ASCII -> 0, all five fields present;
  R5 the source fixture md5 is unchanged across the run (read-only).

Interface.  python3 tests/test_retrofit_dryrun.py            # run the test (no file change);
  python3 tests/test_retrofit_dryrun.py --regen  # rebuild the fixture from mod.M (maintenance).

Dependencies.  Python 3 standard library only (hashlib, importlib.util, io, os, re, sys, types);
  imports `verify/retrofit_gate7_irr.py` as a module (main() only executes under __main__).

Evidence.  R3 is the mechanical no-write proof (write count == 1, sentinel path absent,
  original OUT md5 stable); R1 pins fixture drift (FAIL-LOUD FIXTURE-DRIFT); R4/R5 pin output and source integrity by md5.

Exit-codes.  0 = all criteria pass; 1 = any criterion failing (fail loud).
"""
import hashlib
import importlib.util
import io as real_io
import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
TOOL = os.path.join(REPO, "verify", "retrofit_gate7_irr.py")
FIXTURE = os.path.join(HERE, "fixtures", "retrofit_cn_sample.v")

import re  # noqa: E402
CJK_RE = re.compile(r"[\u4e00-\u9fff]")
CJKPUNCT_RE = re.compile(
    r"[\u3000-\u303f\uff00-\uffef\u2018\u2019\u201c\u201d\u2026\u00b7"
    r"\u2190-\u2193\u21d0-\u21d4\u2200-\u2203\u2207\u2212\u2208\u220b"
    r"\u2264\u2265\u2260\u2248\u2211\u221a\u221e\u2229\u222a\u2295\u2297"
    r"\u2550\u2500\u27f6\u27fa]")
FIELDS = ("Mission.", "Dependencies.", "References.", "Constructivity.", "Build.")


def load_tool():
    spec = importlib.util.spec_from_file_location("retrofit_gate7_irr", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # main() only executes under __main__, so importing is safe
    return mod


def wrap_anchor(anchor, ln):
    """Wrap the anchor string into a single-line comment while keeping the
    nested-comment depth at zero and the anchor text verbatim-contiguous.
    An anchor that itself carries "*)" (e.g. the line-399 closing continuation
    anchor) must not receive an extra suffix; an anchor that cannot be wrapped
    as a single-line comment (its "*)" closes the depth early with characters
    trailing) returns None (fail loud)."""
    line = "(* " + anchor
    depth, i = 1, 0
    while i < len(anchor):
        if anchor.startswith("*)", i):
            depth -= 1; i += 2
        elif anchor.startswith("(*", i):
            depth += 1; i += 2
        else:
            i += 1
        if depth == 0 and i < len(anchor):
            return None
        if depth < 0:
            return None
    return line + " " + "*)" * depth


def build_fixture_text(mod):
    """Synthesize the 843-line (842 lines plus trailing newline) Chinese-comment
    sample mechanically from the mod.M anchor table.  Shape assertions come
    from `retrofit_gate7_irr.py` main(): L34 opens with "(* ====" and is
    self-closing (strip_comments depth conservation), L35 is empty, L36 is
    exactly 'Require Import S01_BaseRing.'; every anchor line carries its
    Chinese anchor string; the remaining lines are pure ASCII (the coverage
    assertion requires zero CJK on unmapped lines)."""
    n_lines = 842
    lines = ["(* rocqwash selftest filler line %d *)" % (i + 1) for i in range(33)]
    lines.append("(* ==== legacy header separator (replaced wholesale) ==== *)")  # L34
    lines.append("")                                                              # L35
    lines.append("Require Import S01_BaseRing.")                                  # L36
    lines += ["(* filler line %d *)" % (i + 1) for i in range(36, n_lines)]
    for ln, (anchor, _new) in mod.M.items():
        assert 37 <= ln <= n_lines, "anchor line %d out of body range" % ln
        assert CJK_RE.search(anchor) or CJKPUNCT_RE.search(anchor), \
            "anchor %d has no CJK/CJKPUNCT (coverage 断言会红)" % ln
        wrapped = wrap_anchor(anchor, ln)
        assert wrapped is not None, \
            "anchor %d 无法单行注释包裹（嵌套深度归零于锚中）" % ln
        lines[ln - 1] = wrapped
    for i, l in enumerate(lines[mod.HEADER_OLD_LINES:], mod.HEADER_OLD_LINES + 1):
        if i not in mod.M:
            assert not (CJK_RE.search(l) or CJKPUNCT_RE.search(l)), \
                "filler line %d must be ASCII" % i
    return "\n".join(lines) + "\n"


def md5_of(path):
    return hashlib.md5(real_io.open(path, "rb").read()).hexdigest()


def main(argv):
    mod = load_tool()

    if "--regen" in argv:
        text = build_fixture_text(mod)
        real_io.open(FIXTURE, "w", encoding="utf-8", newline="").write(text)
        print("REGEN %s (%d bytes, md5 %s)" % (FIXTURE, len(text.encode()), md5_of(FIXTURE)))
        return 0

    # R1: the fixture and the anchor table share one source
    expected_text = build_fixture_text(mod)
    if not os.path.exists(FIXTURE):
        print("FAIL-LOUD: fixture missing: %s （--regen 重建）" % FIXTURE)
        return 1
    fixture_md5_before = md5_of(FIXTURE)
    if fixture_md5_before != hashlib.md5(expected_text.encode("utf-8")).hexdigest():
        print("FAIL-LOUD: FIXTURE-DRIFT: %s 与 mod.M 锚表不同源（--regen 重建）" % FIXTURE)
        return 1
    n_cjk_lines = sum(1 for l in expected_text.split("\n") if CJK_RE.search(l))
    assert n_cjk_lines >= 50, "中文注释样例应含 ≥50 行中文（实测 %d）" % n_cjk_lines

    # Constant patch: source = the on-tree fixture; OUT = a sentinel path that
    # never exists (and must still not exist after the dry run)
    mod.SRC = FIXTURE
    mod.FROZEN_MD5 = fixture_md5_before
    sentinel_out = os.path.join(HERE, ".dryrun_sentinel_never_written.v")
    orig_out = mod.OUT
    orig_out_md5_before = md5_of(orig_out) if os.path.exists(orig_out) else None
    mod.OUT = sentinel_out

    # Write-channel guard: every write-mode open is intercepted into memory;
    # a later read of a virtually written path (the md5_of(OUT) readback at the
    # end of main, retrofit_gate7_irr.py:204) is served from the memory copy —
    # zero bytes reach disk for the whole run.
    writes = []
    written = {}
    real_open = mod.io.open

    def guarded_open(file, mode="r", *a, **k):
        m = str(file)
        if any(ch in mode for ch in "wax+"):
            buf = []

            class _Sink(object):
                def write(self, s):
                    buf.append(s)
                    return len(s)

            writes.append((m, buf))
            written[m] = buf
            return _Sink()
        if m in written:
            import io as _io
            return _io.BytesIO("".join(written[m]).encode("utf-8"))
        return real_open(file, mode, *a, **k)

    mod.io = types.SimpleNamespace(open=guarded_open)

    # R2: dry-run main() — any built-in fail-loud assertion (md5/line shape/
    #     anchors/coverage/ASCII/token identity) raises AssertionError and the
    #     test exits nonzero.
    mod.main()

    # R3: exactly one write request, target = the patched OUT, and that path
    #     does not exist (the on-disk proof of a no-write run)
    assert len(writes) == 1, "写模式 open 应恰 1 次，实测 %d" % len(writes)
    wpath, wbuf = writes[0]
    assert wpath == sentinel_out, "写目标应为哨兵 OUT，实测 %s" % wpath
    assert not os.path.exists(sentinel_out), "干跑落盘了！哨兵路径出现实体文件"
    if orig_out_md5_before is None:
        assert not os.path.exists(orig_out), "原席位 OUT 被干跑创建（违规）: %s" % orig_out
    else:
        assert md5_of(orig_out) == orig_out_md5_before, "原席位 OUT md5 被改（违规）: %s" % orig_out

    # R4: output CJK -> 0 / non-ASCII -> 0 / all five fields present
    out_text = "".join(wbuf)
    assert not CJK_RE.search(out_text), "产物残留 CJK"
    assert not CJKPUNCT_RE.search(out_text), "产物残留 CJK 标点"
    assert all(ord(ch) < 128 for ch in out_text), "产物残留非 ASCII"
    for field in FIELDS:
        assert field in out_text, "产物缺字段 %s" % field
    n_out = len(out_text.split("\n"))
    n_src = len(expected_text.split("\n"))  # 843
    assert n_out == len(mod.HEADER) - mod.HEADER_OLD_LINES + n_src, "行数算术 %d" % n_out

    # R5: the source sample is read-only (md5 identical before and after the
    #     dry run)
    assert md5_of(FIXTURE) == fixture_md5_before, "源样例 md5 变化（被写）"

    print("RETROFIT-DRYRUN PASS: main() 全断言过；写请求 %d 次全部截获（零落盘）；"
          "产物 %d 行 ASCII·五字段齐备；源样例 md5 %s 未动"
          % (len(writes), n_out - 1, fixture_md5_before[:12]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
