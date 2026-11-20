#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_retrofit_dryrun.py — verify/retrofit_gate7_irr.py 干跑自测（rocqwash tests/）。

被测件形制：retrofit_gate7_irr.py 无 CLI 参数，SRC/OUT/FROZEN_MD5 硬编码席位路径
（retrofit_gate7_irr.py:7-11）。本测以模块导入＋常量补丁方式，把其真实 main()
驱动到 tests/fixtures/retrofit_cn_sample.v（含中文注释样例）上，并守卫 io.open
写通道——写请求被截获到内存，**任何字节都不落盘**（dry-run 不落盘的机械化证明）。

判据（全过 exit 0，任一失锐非零）：
  R1 fixture 与模块锚表 mod.M 机械同源（内存重建 md5 == present in the tree fixture md5）；
  R2 dry run main() 全断言通过（含 token 流恒等、行数算术、输出 ASCII——main 内建）；
  R3 全程写模式 open 恰好 1 次、目标恰为补丁后的 OUT、该路径干跑后不存在（不落盘）；
  R4 干跑产物 CJK→0、非 ASCII→0、五字段齐备；
  R5 源样例件干跑前后 md5 不变（只读）。

用法：
  python3 tests/test_retrofit_dryrun.py            # 跑测（不改任何文件）
  python3 tests/test_retrofit_dryrun.py --regen    # 由 mod.M 重建 fixture（维护用）
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
    spec.loader.exec_module(mod)  # main() 仅在 __main__ 下执行，导入安全
    return mod


def wrap_anchor(anchor, ln):
    """把锚串包进单行注释且保证嵌套注释深度归零、锚串逐字连续。
    锚内自带「*)」（如 399 行「…转写） *）」收口续行锚）时不得再补尾缀；
    深度模拟不可包（锚中「*)」提前归零且后随字符）→ 返回 None fail-loud。"""
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
    """由 mod.M 锚表机械合成 843 行（842 行＋末换行）中文注释样例。
    形制断言源自 retrofit_gate7_irr.py main()：
      L34 以「(* ====」起且自闭合（strip_comments 深度守恒）· L35 空行 ·
      L36 恰为 'Require Import S01_BaseRing.'；
      每个锚行含对应中文锚串；其余行纯 ASCII（coverage 断言要求未映射行零 CJK）。"""
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

    # R1: fixture 与锚表同源
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

    # 常量补丁：源=present in the tree fixture；OUT=从不存在的哨兵路径（干跑后必须仍不存在）
    mod.SRC = FIXTURE
    mod.FROZEN_MD5 = fixture_md5_before
    sentinel_out = os.path.join(HERE, ".dryrun_sentinel_never_written.v")
    orig_out = mod.OUT
    orig_out_md5_before = md5_of(orig_out) if os.path.exists(orig_out) else None
    mod.OUT = sentinel_out

    # 写通道守卫：所有写模式 open 截获到内存；已「虚拟写入」路径的后续读
    # （main 末尾 md5_of(OUT) 回读，retrofit_gate7_irr.py:204）由内存副本供给——
    # 全程零字节落盘。
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

    # R2: dry run main()——任一内建 fail-loud 断言（md5/行形/锚/coverage/ASCII/token 恒等）
    #     失败即抛 AssertionError → 本测非零退出。
    mod.main()

    # R3: 恰一次写请求，目标=补丁后 OUT，且该路径不存在（不落盘铁证）
    assert len(writes) == 1, "写模式 open 应恰 1 次，实测 %d" % len(writes)
    wpath, wbuf = writes[0]
    assert wpath == sentinel_out, "写目标应为哨兵 OUT，实测 %s" % wpath
    assert not os.path.exists(sentinel_out), "干跑落盘了！哨兵路径出现实体文件"
    if orig_out_md5_before is None:
        assert not os.path.exists(orig_out), "原席位 OUT 被干跑创建（违规）: %s" % orig_out
    else:
        assert md5_of(orig_out) == orig_out_md5_before, "原席位 OUT md5 被改（违规）: %s" % orig_out

    # R4: 产物 CJK→0 / 非 ASCII→0 / 五字段齐备
    out_text = "".join(wbuf)
    assert not CJK_RE.search(out_text), "产物残留 CJK"
    assert not CJKPUNCT_RE.search(out_text), "产物残留 CJK 标点"
    assert all(ord(ch) < 128 for ch in out_text), "产物残留非 ASCII"
    for field in FIELDS:
        assert field in out_text, "产物缺字段 %s" % field
    n_out = len(out_text.split("\n"))
    n_src = len(expected_text.split("\n"))  # 843
    assert n_out == len(mod.HEADER) - mod.HEADER_OLD_LINES + n_src, "行数算术 %d" % n_out

    # R5: 源样例只读（干跑前后 md5 恒等）
    assert md5_of(FIXTURE) == fixture_md5_before, "源样例 md5 变化（被写）"

    print("RETROFIT-DRYRUN PASS: main() 全断言过；写请求 %d 次全部截获（零落盘）；"
          "产物 %d 行 ASCII·五字段齐备；源样例 md5 %s 未动"
          % (len(writes), n_out - 1, fixture_md5_before[:12]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
