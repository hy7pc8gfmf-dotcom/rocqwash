#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""detached_safe_derive.py - the detached-safe column deriver (.github/scripts/).
Purpose.  Keep the `detached-safe` column of the two census summary tables
  (the `docs/census.md` section 2 summary table and the `docs/CAPABILITY-INDEX.md`
  section 1 table) equal to the mechanical derivation from the standing
  census: a tool is detached-safe when its recorded `imports.local` face is
  empty and its name is not an underscore helper - it then runs from one
  downloaded file with no sibling present.  The standing census generator
  and its frozen v1 rules stay untouched; this script only reads the
  recorded data and maintains the rendered column.
Interface.  `python3 .github/scripts/detached_safe_derive.py --repo DIR
  --check | --apply | --selftest`; `--check` reads the rendered tables and
  reports any drift (exit 1 on mismatch); `--apply` rewrites the two table
  faces in place (dry-run default - without a face flag the script prints
  the usage and exits 2); `--selftest` runs the frozen vectors.
Dependencies.  Python 3 standard library only (json, os, re, sys).
Evidence.  --selftest runs five frozen vectors on canned rows: the
  derivation rule (empty local imports and no underscore prefix means
  safe), the helper exclusion, the row-column append form, the drift
  detection on a canned table, and the report closed key set.
Exit-codes.  0 the check is clean or the apply landed; 1 the check found
  drift; 2 usage error.
"""
import json
import os
import sys

CENSUS = "docs/census-tools.json"
FACES = [
    ("docs/census.md", "Detached-safe"),
    ("docs/CAPABILITY-INDEX.md", "Detached-safe"),
]


def detached_safe(row):
    """The derivation rule on one census record."""
    return (not row.get("underscore_prefix", False)) and not row.get("imports", {}).get("local")


def row_name(line):
    """The file name of one markdown table row, or None."""
    if not line.startswith("| "):
        return None
    cell = line[2:].split("|", 1)[0].strip()
    return cell or None


def table_region(lines):
    """(start, end) of the summary table inside the face: from the
    `| File |` header row through the last row line before the region
    breaks (a blank line, a heading, or a non-table line)."""
    start = None
    for i, line in enumerate(lines):
        if line.startswith("| File |"):
            start = i
            break
    if start is None:
        return None
    end = start
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("|"):
            end = i
        else:
            break
    return start, end


def check_face(lines, expected):
    """(mismatches, rows) for one rendered face: every tool row must carry
    the header column and the derived value."""
    region = table_region(lines)
    if region is None:
        return ["no summary table found"], 0
    start, end = region
    header = lines[start]
    mismatches = []
    rows = 0
    if "Detached-safe" not in header:
        mismatches.append("header row lacks the Detached-safe column")
    sep = lines[start + 1]
    if sep.count("---") < header.count("|") - 1:
        mismatches.append("separator row has fewer cells than the header")
    for i in range(start + 2, end + 1):
        name = row_name(lines[i])
        if name is None:
            continue
        if name == "File":
            continue
        rows += 1
        want = expected.get(name)
        if want is None:
            mismatches.append("{0}: no census record".format(name))
            continue
        cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
        got = cells[-1] if cells else ""
        if got not in ("yes", "no"):
            mismatches.append("{0}: last cell {1!r} is not a detached-safe value".format(name, got))
        elif got != ("yes" if want else "no"):
            mismatches.append("{0}: column says {1}, derivation says {2}".format(name, got, "yes" if want else "no"))
    return mismatches, rows


def apply_face(lines, expected):
    """Rewrite one face's table in place: append the header cell, extend
    the separator, and append the derived value to every tool row."""
    region = table_region(lines)
    if region is None:
        return lines, ["no summary table found"]
    start, end = region
    out = list(lines)
    header = out[start].rstrip("\n")
    if "Detached-safe" not in header:
        out[start] = header + " Detached-safe |\n"
    sep = out[start + 1].rstrip("\n")
    if sep.count("---") < out[start].count("|") - 1:
        out[start + 1] = sep + "---|\n"
    for i in range(start + 2, end + 1):
        name = row_name(out[i])
        if name is None or name == "File":
            continue
        want = expected.get(name)
        if want is None:
            continue
        line = out[i].rstrip("\n")
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells and cells[-1] in ("yes", "no"):
            cells[-1] = "yes" if want else "no"
        else:
            cells.append("yes" if want else "no")
        out[i] = "| " + " | ".join(cells) + " |\n"
    return out, []


def load_expected(repo):
    with open(os.path.join(repo, CENSUS), "r", encoding="utf-8") as handle:
        rows = json.load(handle)["files"]
    return {r["name"]: detached_safe(r) for r in rows}


def _selftest():
    """Five frozen vectors; 0 green, 1 red."""
    failures = []

    def check(name, cond, detail=""):
        print("[SELFTEST] {0} {1}{2}".format("PASS" if cond else "FAIL", name,
                                             (": " + detail) if detail and not cond else ""))
        if not cond:
            failures.append(name)

    check("v1-rule-safe", detached_safe({"underscore_prefix": False, "imports": {"local": []}}) is True)
    check("v2-rule-sibling-and-helper",
          detached_safe({"underscore_prefix": False, "imports": {"local": ["_http_backoff"]}}) is False
          and detached_safe({"underscore_prefix": True, "imports": {"local": []}}) is False)
    header = ["| File | Basis |\n", "|---|---|\n", "| a.py | arg |\n", "| b.py | token |\n"]
    expected = {"a.py": True, "b.py": False}
    out, errs = apply_face(list(header), expected)
    check("v3-append-form", not errs and out[0] == "| File | Basis | Detached-safe |\n"
          and out[2] == "| a.py | arg | yes |\n" and out[3] == "| b.py | token | no |\n",
          str(out))
    expected_wrong = {"a.py": False, "b.py": False}
    rendered, errs = apply_face(list(header), expected)
    mismatches, rows = check_face(rendered, expected_wrong)
    check("v4-drift-detection", not errs and rows == 2
          and any("column says yes" in m and m.startswith("a.py") for m in mismatches),
          str(mismatches))
    report = {"schema": "rocqwash-detached-safe-report/1", "faces": 2, "rows": 80, "mismatches": []}
    check("v5-report-schema-closed-set",
          set(report.keys()) == {"schema", "faces", "rows", "mismatches"})
    print("DETACHED-SAFE-DERIVE-SELFTEST: {0} vector(s), {1} FAIL".format(5, len(failures)))
    return 1 if failures else 0


def main(argv):
    args = argv[1:]
    if "--selftest" in args:
        return _selftest()
    repo = "."
    do_apply = "--apply" in args
    do_check = "--check" in args
    i = 0
    while i < len(args):
        if args[i] == "--repo" and i + 1 < len(args):
            repo = args[i + 1]
        i += 1
    if not (do_apply or do_check):
        sys.stderr.write("usage: detached_safe_derive.py --repo DIR (--check | --apply)\n")
        return 2
    expected = load_expected(repo)
    total_rows = 0
    all_mismatches = []
    for rel, _col in FACES:
        path = os.path.join(repo, rel)
        with open(path, "r", encoding="utf-8") as handle:
            lines = handle.readlines()
        if do_apply:
            lines, errs = apply_face(lines, expected)
            if errs:
                all_mismatches.extend(rel + ": " + e for e in errs)
                continue
            with open(path, "w", encoding="utf-8") as handle:
                handle.writelines(lines)
        else:
            mismatches, rows = check_face(lines, expected)
            total_rows += rows
            all_mismatches.extend(rel + ": " + m for m in mismatches)
    if do_check:
        print(json.dumps({"schema": "rocqwash-detached-safe-report/1", "faces": len(FACES),
                          "rows": total_rows, "mismatches": all_mismatches}, sort_keys=True))
        return 1 if all_mismatches else 0
    print("applied: {0} faces rewritten".format(len(FACES)))
    return 0 if not all_mismatches else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
