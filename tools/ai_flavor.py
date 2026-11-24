#!/usr/bin/env python3
"""ai_flavor.py - AI-flavor wording detector, engine E1 detection body.

Purpose.  Scans a file or a directory tree for the 36 AI-flavor wording
  faces plus a separate em-dash battery (U+2014, target 0) and reports
  per-hit records with context windows; detection only, no rewriting,
  stdout reporting by default, zero files written unless --json is given.
Interface.  --file PATH [--json OUT] | --tree DIR [--json OUT] |
  --selftest, optional --word-map PATH (default: seeds/ai_flavor/
  word-map.json resolved from the tree root).  Report schema
  rocqwash.ai-flavor.report/1 with English keys {schema, file, batteries,
  em_dash_count, hits}; hits carry {line, battery, face_id, before,
  after}, each window at most 40 characters; tree mode adds {file} to
  every hit.  Pure functions for import: detect_text(text, word_map) ->
  report_dict and load_word_map(path) -> dict.
Dependencies.  Python 3 standard library only (argparse, json, os, re,
  sys); the 36 face regexes are read verbatim from the word map, no face
  literal is embedded in this body; zero network.
Evidence.  Parity with the shell instrument battery and exit codes;
  --selftest probe vectors; detail in the extended contract below.
Exit-codes.  0 clean (all batteries zero and em-dash zero); 1 wording
  or em-dash hits found, or selftest failure; 2 usage or data error
  (bad arguments, missing paths, unreadable or invalid word map); hits
  are data, not errors.
"""
# Extended contract (moved from the docstring to hold the 30-line header
# budget): Evidence detail.  Battery names, pattern literals, case sensitivity and
# exit codes follow the shell instrument (techdocs/ai_flavor_selfcheck.sh,
# detector lines 29/34/39/44/49/53-58) transcribed through the seed map
# detection_reference; wording counts are matching lines (grep -c
# semantics), the em-dash count is occurrences (grep -o | wc -l);
# wording batteries are case-sensitive for the zh battery and
# case-insensitive otherwise; the para battery branch is shared by three
# faces and hit attribution compares the matched token text.
# Self-exclusion: this file and the loaded word map are exempt from
# wording batteries only; the em-dash battery is exempt nowhere.

import argparse
import json
import os
import re
import sys

TOOL = "ai_flavor.py"
SCHEMA = "rocqwash.ai-flavor.report/1"
MAP_SCHEMA = "rocqwash.seeds.ai-flavor.word-map/1.0"
MAP_ENGINE = "ai_flavor"
WINDOW_CHARS = 40
EM_DASH = "\u2014"
SCAN_EXTENSIONS = frozenset((".py", ".sh", ".md", ".json", ".ts", ".v"))
CASE_SENSITIVE_BATTERIES = frozenset(("CH_3FAMILIES_10FACES",))
PARA_BATTERY = "EN_PARA_INITIAL_3FACES"
REQUIRED_FACE_KEYS = ("id", "face", "lang", "battery", "detector_regex_branch")
EXIT_CLEAN = 0
EXIT_HITS = 1
EXIT_USAGE = 2


def fail(message, code):
    sys.stderr.write(TOOL + ": " + message + "\n")
    raise SystemExit(code)


def _battery_flags(battery):
    # zh battery matches case-sensitive (instrument runs grep without -i
    # there); every other battery is case-insensitive (grep -i).
    if battery in CASE_SENSITIVE_BATTERIES:
        return 0
    return re.IGNORECASE


def load_word_map(path):
    """Load and validate the word map; raises OSError/ValueError on failure."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        raise ValueError("invalid JSON in word map %s: %s" % (path, exc))
    if not isinstance(data, dict):
        raise ValueError("word map %s: top level is not a JSON object" % path)
    if data.get("schema") != MAP_SCHEMA:
        raise ValueError("word map %s: schema %r != %r"
                         % (path, data.get("schema"), MAP_SCHEMA))
    if data.get("engine") != MAP_ENGINE:
        raise ValueError("word map %s: engine %r != %r"
                         % (path, data.get("engine"), MAP_ENGINE))
    faces = data.get("faces")
    if not isinstance(faces, list) or not faces:
        raise ValueError("word map %s: faces missing or empty" % path)
    declared = data.get("face_count")
    if isinstance(declared, bool) or not isinstance(declared, int) \
            or declared != len(faces):
        raise ValueError("word map %s: face_count %r != len(faces) %d"
                         % (path, declared, len(faces)))
    reference = data.get("detection_reference")
    battery_entries = reference.get("batteries") if isinstance(reference, dict) else None
    if not isinstance(battery_entries, list) or not battery_entries:
        raise ValueError("word map %s: detection_reference.batteries missing" % path)
    literals = {}
    for entry in battery_entries:
        name = entry.get("battery") if isinstance(entry, dict) else None
        literal = entry.get("pattern_literal") if isinstance(entry, dict) else None
        if not isinstance(name, str) or not name or not isinstance(literal, str):
            raise ValueError("word map %s: battery entry needs battery name "
                             "and pattern_literal" % path)
        re.compile(literal, _battery_flags(name))
        literals[name] = literal
    em_battery = data.get("structural_battery_em_dash")
    if not isinstance(em_battery, dict) \
            or em_battery.get("excluded_from_face_count") is not True:
        raise ValueError("word map %s: structural_battery_em_dash missing or "
                         "misdeclared (em-dash stays outside the face count)" % path)
    seen_ids = set()
    for face in faces:
        for key in REQUIRED_FACE_KEYS:
            value = face.get(key) if isinstance(face, dict) else None
            if not isinstance(value, str) or not value:
                raise ValueError("word map %s: face entry missing field %s"
                                 % (path, key))
        if face["id"] in seen_ids:
            raise ValueError("word map %s: duplicate face id %r"
                             % (path, face["id"]))
        seen_ids.add(face["id"])
        battery = face["battery"]
        if battery not in literals:
            raise ValueError("word map %s: face %s names unknown battery %r"
                             % (path, face["id"], battery))
        branch = face["detector_regex_branch"]
        # transcription integrity: each face branch must appear verbatim
        # inside its battery pattern literal (no rewritten regex faces)
        if branch not in literals[battery]:
            raise ValueError("word map %s: face %s branch is not verbatim "
                             "inside its battery literal" % (path, face["id"]))
        re.compile(branch, _battery_flags(battery))
    return data


def _compile_faces(word_map):
    """Compile per-face regexes; returns [(face, regex, shared_branch)]."""
    battery_flags = {}
    owners = {}
    for face in word_map["faces"]:
        battery = face["battery"]
        battery_flags.setdefault(battery, _battery_flags(battery))
        key = (battery, face["detector_regex_branch"])
        owners.setdefault(key, []).append(face["id"])
    compiled = []
    for face in word_map["faces"]:
        key = (face["battery"], face["detector_regex_branch"])
        shared = len(owners[key]) > 1
        regex = re.compile(face["detector_regex_branch"], battery_flags[face["battery"]])
        compiled.append((face, regex, shared))
    return compiled


def detect_text(text, word_map):
    """Pure detection: (text, word_map) -> report dict with file field empty."""
    compiled = _compile_faces(word_map)
    battery_lines = {}
    hits = []
    for line_number, line in enumerate(text.splitlines(), 1):
        for face, regex, shared in compiled:
            for match in regex.finditer(line):
                # shared branches (para battery) attribute by matched token
                if shared and match.group(0).strip().lower() != face["face"].strip().lower():
                    continue
                start, end = match.span()
                hits.append({
                    "line": line_number,
                    "battery": face["battery"],
                    "face_id": face["id"],
                    "before": line[max(0, start - WINDOW_CHARS):start],
                    "after": line[end:end + WINDOW_CHARS],
                })
                battery_lines.setdefault(face["battery"], set()).add(line_number)
    order = []
    for entry in word_map["detection_reference"]["batteries"]:
        if entry["battery"] not in order:
            order.append(entry["battery"])
    batteries = dict((name, len(battery_lines.get(name, ()))) for name in order)
    return {
        "schema": SCHEMA,
        "file": "",
        "batteries": batteries,
        "em_dash_count": text.count(EM_DASH),
        "hits": hits,
    }


def verdict_of(report):
    """(verdict string, exit code) from a report dict."""
    if report.get("em_dash_count", 0) > 0:
        return "RED", EXIT_HITS
    if report.get("hits"):
        return "RED", EXIT_HITS
    if any(report.get("batteries", {}).values()):
        return "RED", EXIT_HITS
    return "CLEAN", EXIT_CLEAN


def apply_wording_exemption(report):
    """Self-exclusion: drop wording hits, keep the em-dash count untouched."""
    exempted = dict(report)
    exempted["hits"] = []
    exempted["batteries"] = dict((name, 0) for name in report.get("batteries", {}))
    return exempted


def exemption_paths(map_path):
    """Real paths exempt from wording batteries: this module and the map."""
    paths = set()
    paths.add(os.path.realpath(__file__))
    if map_path:
        paths.add(os.path.realpath(map_path))
    return paths


def default_word_map_path():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, "seeds", "ai_flavor", "word-map.json")


def read_text(path):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return handle.read()
    except (OSError, UnicodeDecodeError) as exc:
        fail("unreadable target: %s (%s)" % (path, exc), EXIT_USAGE)


def write_json_report(path, report):
    try:
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    except OSError as exc:
        fail("cannot write report: %s (%s)" % (path, exc), EXIT_USAGE)


def scan_file(path, word_map, exempted):
    """Scan one file; applies wording exemption when the path is exempt."""
    text = read_text(path)
    report = detect_text(text, word_map)
    report["file"] = path
    if os.path.realpath(path) in exempted:
        report = apply_wording_exemption(report)
        print("EXEMPT wording batteries skipped for %s (em-dash still counted)" % path)
    return report


def collect_tree(root):
    """All scan-extension files under root; dot directories are skipped."""
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(name for name in dirnames if not name.startswith("."))
        for name in sorted(filenames):
            extension = os.path.splitext(name)[1].lower()
            if extension in SCAN_EXTENSIONS:
                found.append(os.path.join(dirpath, name))
    return found


def scan_tree(root, word_map, exempted):
    """Scan a tree; aggregates battery line counts and per-file hits."""
    batteries = {}
    em_total = 0
    hits = []
    for path in collect_tree(root):
        text = read_text(path)
        report = detect_text(text, word_map)
        relative = os.path.relpath(path, root).replace(os.sep, "/")
        if os.path.realpath(path) in exempted:
            report = apply_wording_exemption(report)
            print("EXEMPT wording batteries skipped for %s (em-dash still counted)"
                  % relative)
        for name, count in report["batteries"].items():
            batteries[name] = batteries.get(name, 0) + count
        em_total += report["em_dash_count"]
        for hit in report["hits"]:
            merged = {"file": relative}
            merged.update(hit)
            hits.append(merged)
        wording = sum(report["batteries"].values())
        if wording or report["em_dash_count"]:
            print("%s wording_lines=%d em_dash=%d"
                  % (relative, wording, report["em_dash_count"]))
    return {
        "schema": SCHEMA,
        "file": root,
        "batteries": batteries,
        "em_dash_count": em_total,
        "hits": hits,
    }


def print_battery_summary(report):
    total_lines = 0
    for name, count in report.get("batteries", {}).items():
        print("%s lines=%d" % (name, count))
        total_lines += count
    print("EM_DASH_U2014 count=%d (target 0)" % report.get("em_dash_count", 0))
    print("TOTAL_WORDING_LINES=%d" % total_lines)
    verdict = verdict_of(report)[0]
    if verdict == "CLEAN":
        print("VERDICT CLEAN (36 faces = 0; em-dash = 0)")
    else:
        print("VERDICT RED (wording battery or em-dash nonzero)")


def _first_face(faces_by_battery, battery):
    group = faces_by_battery.get(battery)
    if not group:
        raise ValueError("battery absent from word map: " + battery)
    return group[0]


def run_selftest(word_map_path, word_map):
    """Probe vectors; prints one PASS/FAIL line per vector, returns exit code."""
    checks = []

    def record(name, ok, detail=""):
        checks.append((name, ok, detail))
        print("%-40s %s %s" % (name, "PASS" if ok else "FAIL", detail))

    faces_by_battery = {}
    for face in word_map["faces"]:
        faces_by_battery.setdefault(face["battery"], []).append(face)
    zh_face = _first_face(faces_by_battery, "CH_3FAMILIES_10FACES")
    stem_face = _first_face(faces_by_battery, "EN_WORD_STEMS_15FACES")
    sent_face = _first_face(faces_by_battery, "EN_SENTENCE_8FACES")
    para_group = faces_by_battery.get(PARA_BATTERY, [])
    if not para_group:
        raise ValueError("battery absent from word map: " + PARA_BATTERY)
    para_face = para_group[1] if len(para_group) > 1 else para_group[0]

    record("load_word_map",
           word_map.get("schema") == MAP_SCHEMA and len(word_map["faces"]) > 0)

    # clean probe stays clean
    clean_report = detect_text("def add(a, b):\n    return a + b\n", word_map)
    record("clean_probe",
           not clean_report["hits"]
           and clean_report["em_dash_count"] == 0
           and verdict_of(clean_report) == ("CLEAN", EXIT_CLEAN),
           "probe verdict CLEAN")

    # polluted probe turns red; per-face attribution must be exact
    polluted = "\n".join([
        "plain prose line",
        "the register bans " + zh_face["face"] + " outright",
        "we " + stem_face["face"] + " this data carefully",
        "This " + sent_face["face"] + " a sample.",
        para_face["face"] + ", the probe continues.",
    ])
    polluted_report = detect_text(polluted, word_map)
    got_ids = sorted(hit["face_id"] for hit in polluted_report["hits"])
    expected_ids = sorted({zh_face["id"], stem_face["id"],
                           sent_face["id"], para_face["id"]})
    para_ids = set(face["id"] for face in para_group)
    claimed_para = [hit["face_id"] for hit in polluted_report["hits"]
                    if hit["face_id"] in para_ids]
    record("polluted_probe_red",
           got_ids == expected_ids
           and polluted_report["batteries"].get(zh_face["battery"]) == 1
           and polluted_report["batteries"].get(stem_face["battery"]) == 1
           and polluted_report["batteries"].get(sent_face["battery"]) == 1
           and polluted_report["batteries"].get(para_face["battery"]) == 1
           and claimed_para == [para_face["id"]]
           and polluted_report["em_dash_count"] == 0
           and verdict_of(polluted_report) == ("RED", EXIT_HITS),
           "probe verdict RED faces=%r" % (got_ids,))

    # em-dash battery: occurrence count, wording hits stay zero
    em_report = detect_text("alpha \u2014 beta\n", word_map)
    record("em_dash_battery",
           em_report["em_dash_count"] == 1
           and not em_report["hits"]
           and verdict_of(em_report) == ("RED", EXIT_HITS))

    # context windows: exactly 40 characters on each side of the known hit
    # span (spaces keep the stem isolated: a trailing word-chunk would be
    # swallowed by the stem's \\w* tail and shift the match end)
    window_probe = "x" * 50 + " " + stem_face["face"] + " " + "y" * 50
    window_start = 51
    window_end = window_start + len(stem_face["face"])
    window_report = detect_text(window_probe, word_map)
    windows = [(hit["before"], hit["after"]) for hit in window_report["hits"]]
    record("context_windows_40",
           windows == [(window_probe[window_start - 40:window_start],
                        window_probe[window_end:window_end + 40])]
           and all(len(part) == 40 for pair in windows for part in pair))

    # self-eating: raw scan of this module must find nothing at all
    own_text = read_text(os.path.realpath(__file__))
    raw_own = detect_text(own_text, word_map)
    record("self_eating_raw",
           not raw_own["hits"] and raw_own["em_dash_count"] == 0,
           "hits=%d em=%d" % (len(raw_own["hits"]), raw_own["em_dash_count"]))

    # exemption asymmetry on real battery data (the word map itself)
    map_text = read_text(word_map_path)
    raw_map = detect_text(map_text, word_map)
    exempted_map = apply_wording_exemption(raw_map)
    em_raw = map_text.count(EM_DASH)
    record("wording_exemption_asymmetry",
           len(raw_map["hits"]) > 0
           and not exempted_map["hits"]
           and all(count == 0 for count in exempted_map["batteries"].values())
           and exempted_map["em_dash_count"] == em_raw
           and em_raw > 0,
           "map wording hits=%d em=%d" % (len(raw_map["hits"]), em_raw))

    # deterministic rerun: identical input gives identical report
    record("deterministic_rerun",
           detect_text(polluted, word_map) == polluted_report)

    record("exit_code_mapping",
           verdict_of(clean_report) == ("CLEAN", EXIT_CLEAN)
           and verdict_of(polluted_report) == ("RED", EXIT_HITS)
           and verdict_of(em_report) == ("RED", EXIT_HITS))

    failed = [entry for entry in checks if not entry[1]]
    print("SELFTEST %d/%d checks passed" % (len(checks) - len(failed), len(checks)))
    if failed:
        print("SELFTEST FAIL")
        return EXIT_HITS
    print("SELFTEST PASS")
    return EXIT_CLEAN


def build_parser():
    parser = argparse.ArgumentParser(
        prog=TOOL,
        description="AI-flavor wording detector (engine E1 detection body).")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--file", metavar="PATH", help="scan one file")
    action.add_argument("--tree", metavar="DIR",
                        help="scan a tree: .py .sh .md .json .ts .v, dot dirs skipped")
    action.add_argument("--selftest", action="store_true",
                        help="run built-in probe vectors")
    parser.add_argument("--json", metavar="OUT_PATH",
                        help="write the JSON report to OUT_PATH")
    parser.add_argument("--word-map", dest="word_map", metavar="PATH",
                        help="word map path (default: seeds/ai_flavor/"
                             "word-map.json from the tree root)")
    return parser


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    namespace = build_parser().parse_args(argv)
    if namespace.selftest and namespace.json:
        fail("--json has no effect with --selftest (the selftest writes no "
             "report file)", EXIT_USAGE)
    map_path = namespace.word_map or default_word_map_path()
    try:
        word_map = load_word_map(map_path)
    except (OSError, ValueError) as exc:
        fail("word map load failed: %s (%s)" % (map_path, exc), EXIT_USAGE)
    exempted = exemption_paths(map_path)
    if namespace.selftest:
        return run_selftest(map_path, word_map)
    if namespace.file:
        if not os.path.isfile(namespace.file):
            fail("target file not found: %s" % namespace.file, EXIT_USAGE)
        report = scan_file(namespace.file, word_map, exempted)
    else:
        if not os.path.isdir(namespace.tree):
            fail("target directory not found: %s" % namespace.tree, EXIT_USAGE)
        report = scan_tree(namespace.tree, word_map, exempted)
    print_battery_summary(report)
    verdict, code = verdict_of(report)
    if namespace.json:
        write_json_report(namespace.json, report)
    return code


if __name__ == "__main__":
    sys.exit(main())
