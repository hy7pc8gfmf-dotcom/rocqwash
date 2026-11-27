#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""capability_index.py - census-rendered tool capability index CLI (R-4).
Purpose.  Renders the rocqwash tool capability index from the census
  masters instead of returning one opaque document: the primary master is
  docs/census-tools.json, the secondary master is docs/flag-shape.json,
  and the MCP roster is read AST-level from TOOL_SPECS in
  tools/mcp_server.py.  Three output faces share those same masters so a
  summary count and a full record can never disagree; the face semantics
  and the carried master-drift note live in the extended contract below.
Interface.  python3 tools/capability_index.py [--mode {full,summary}]
  [--tool NAME] | --selftest.  --mode full (default) prints the full
  index; --mode summary prints one line per tool; --tool NAME renders one
  full record.  Determinism, name-acceptance, and selftest semantics are
  in the extended contract.
Dependencies.  Python 3 standard library only; zero subprocess, zero
  network, read-only over docs/ and the tools/mcp_server.py text.
Evidence.  --selftest asserts the fixture vectors (one-phrase extractor
  pins, summary face, --tool/full block equality) and the real-master
  vectors (summary line-count face, --tool single-entry face, full-mode
  byte-stability face); the enumeration is in the extended contract.
Exit-codes.  0 green (a render completed or the selftest is green); 1
  red (selftest failure or a census master missing/unparseable); 2 usage
  error; the per-case detail is in the extended contract.
"""

# Extended contract (kept outside the five-field header so the header
# stays within the 30-line budget of the annotation standard; the moved
# facts are carried over from the former header verbatim in substance):
#
# Face semantics.  Mode full (the default, unchanged by R-4) renders the
#   complete index, one full record per censused tool, sorted by tool
#   name, with a three-line deterministic header (no timestamps,
#   byte-stable across runs).  Mode summary renders exactly one line per
#   tool - name, one-phrase purpose, MCP face count - and exists because
#   the full index overran harness response caps in two measured rounds
#   (130KB of full index against a 50KB cap); the stdout line count
#   equals the census tool count exactly.  --tool NAME renders the single
#   full record of one tool and is byte-equal to that tool's block in
#   full mode; it accepts the base name with or without the .py suffix
#   (chain_graph or chain_graph.py) and may not be combined with --mode
#   summary.  --selftest runs the fixture vectors and the real-master
#   vectors and prints one [PASS]/[FAIL] line per vector.
# Known master drift, carried not hidden: docs/flag-shape.json lags
#   docs/census-tools.json by seven files (the claim_watch,
#   lean_axiom_sweep, numeric_probe, release_chain, source_fetch,
#   statement_identity, sweep_verdict entries), so their flag_shape lines
#   render as "-" instead of inventing a shape.
# Evidence detail.  On in-memory fixtures: the one-phrase extractor pins
#   (name.py / name.py v2: / em-dash / "(v2)" prefixes, the parenthetical
#   and sentence cuts, the no-docstring fallback, the length cap with
#   ellipsis), a two-tool summary face (line count == tool count, every
#   line non-empty and name-prefixed, singular/plural face counting), and
#   the --tool/full block equality; on the real masters: the summary-mode
#   vector (stdout line count == census tool count, every line
#   non-empty), the --tool single-entry vector (exactly one entry header,
#   and the record is byte-equal to that tool's block in full mode), and
#   the full-mode byte-stability vector (two renders byte-identical,
#   entry headers sorted by tool name, entry count == census tool count).
#   All vectors were cast with R-4 and are executed by the acceptance
#   runner; this file's own selftest run is the caller's gate, not a
#   landed measurement.
# Exit-code detail: 1 red covers a selftest failure, or a census master
#   missing or unparseable - the message names the path and points at
#   docs/census.md section 1; 2 usage covers a bad --mode value,
#   --selftest combined with render flags, --tool combined with --mode
#   summary, or --tool naming a tool absent from the census.

import argparse
import ast
import json
import os
import re
import sys

TOOL = "capability_index"

CENSUS_REL = os.path.join("docs", "census-tools.json")
FLAG_SHAPE_REL = os.path.join("docs", "flag-shape.json")
ROSTER_REL = os.path.join("tools", "mcp_server.py")

PHRASE_CAP = 96
NO_DOCSTRING_PHRASE = "(no docstring head in census)"

# One-phrase extractor faces: a leading version token left after the name
# ("v2:", "(v2)"), the separator directly after the name (" - ", " - ", " - ",
# ":"), internal whitespace runs, and the cut tokens (earliest wins).
_LEAD_VERSION = re.compile(r"^\s*(?:\(v\d+\)|v\d+)\s*[:\-]?\s*")
_LEAD_SEP = re.compile(r"^\s*[:\-\u2014=]+\s*")
_WS = re.compile(r"\s+")
_CUT_TOKENS = (" (", ". ", " \u2014 ", ": ", " - ")


class MasterError(Exception):
    """A census master is missing or unparseable; exit 1, fail loud."""


def repo_root():
    """The rocqwash root: the parent of the tools/ directory holding us."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_census(root):
    """Load the primary master docs/census-tools.json (fail loud)."""
    path = os.path.join(root, CENSUS_REL)
    if not os.path.isfile(path):
        raise MasterError(
            "census master not found: {0} (regenerate it with the "
            "docs/census.md section 1 command)".format(path)
        )
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, ValueError) as exc:
        raise MasterError("census master unreadable: {0}: {1}".format(path, exc))
    files = payload.get("files")
    if not isinstance(files, list) or not files:
        raise MasterError(
            "census master carries no files list: {0}".format(path)
        )
    return path, files


def load_flag_shape(root):
    """Load the secondary master docs/flag-shape.json (may lag the census)."""
    path = os.path.join(root, FLAG_SHAPE_REL)
    if not os.path.isfile(path):
        raise MasterError(
            "flag-shape master not found: {0} (regenerate it with the "
            "docs/census.md section 1 command)".format(path)
        )
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, ValueError) as exc:
        raise MasterError(
            "flag-shape master unreadable: {0}: {1}".format(path, exc)
        )
    if not isinstance(payload, dict):
        raise MasterError(
            "flag-shape master is not a per-file object: {0}".format(path)
        )
    return path, payload


def load_roster(root):
    """MCP face counts per tool, AST-read from TOOL_SPECS in mcp_server.py.

    Returns {cli_target_py: [face name, ...]}; the roster is the only
    non-census input and only feeds the summary face-count field and the
    mcp_faces line of a full record.
    """
    path = os.path.join(root, ROSTER_REL)
    if not os.path.isfile(path):
        raise MasterError(
            "roster not found: {0} (TOOL_SPECS lives there)".format(path)
        )
    try:
        with open(path, "r", encoding="utf-8") as handle:
            tree = ast.parse(handle.read(), filename=path)
    except (OSError, SyntaxError, ValueError) as exc:
        raise MasterError("roster unparseable: {0}: {1}".format(path, exc))
    for node in tree.body:
        targets = getattr(node, "targets", ())
        if not any(
            isinstance(target, ast.Name) and target.id == "TOOL_SPECS"
            for target in targets
        ):
            continue
        if not isinstance(node.value, ast.List):
            raise MasterError(
                "TOOL_SPECS in {0} is not a list literal; the AST roster "
                "read refuses to guess".format(path)
            )
        faces = {}
        for element in node.value.elts:
            if not isinstance(element, ast.Dict):
                continue
            fields = {}
            for key, value in zip(element.keys, element.values):
                if isinstance(key, ast.Constant):
                    fields[key.value] = value
            name_node = fields.get("name")
            cli_node = fields.get("cli")
            name = None
            if isinstance(name_node, ast.Constant):
                name = name_node.value
            target = None
            if isinstance(cli_node, ast.Call):
                parts = [
                    arg.value
                    for arg in cli_node.args
                    if isinstance(arg, ast.Constant)
                ]
                if len(parts) == 2 and parts[0] == "tools":
                    target = parts[1]
            if isinstance(name, str) and isinstance(target, str):
                faces.setdefault(target, []).append(name)
        return faces
    raise MasterError(
        "TOOL_SPECS not found in {0}; the AST roster read refuses to guess"
        .format(path)
    )


def one_phrase(record):
    """The one-phrase purpose, deterministic, from the docstring head.

    Rule: first non-empty head line; strip the leading tool-name token (with
    or without .py); strip a leading version token and separator; collapse
    whitespace; cut at the earliest of " (", ". ", " - ", ": ", " - ";
    strip trailing punctuation; cap at PHRASE_CAP with "..." when longer.
    """
    doc = record.get("docstring") or {}
    head = doc.get("head") or ""
    lines = [line.strip() for line in head.splitlines() if line.strip()]
    text = lines[0] if lines else ""
    name = record.get("name") or ""
    stem = name[:-3] if name.endswith(".py") else name
    lowered = text.lower()
    for prefix in (name.lower(), stem.lower()):
        if prefix and lowered.startswith(prefix):
            text = text[len(prefix):]
            break
    text = _LEAD_VERSION.sub("", text)
    text = _LEAD_SEP.sub("", text)
    text = _WS.sub(" ", text).strip()
    cut_at = len(text)
    for token in _CUT_TOKENS:
        index = text.find(token)
        if 0 < index < cut_at:
            cut_at = index
    text = text[:cut_at].strip()
    text = text.rstrip(".,;:-")
    if not text:
        return NO_DOCSTRING_PHRASE
    if len(text) > PHRASE_CAP:
        text = text[:PHRASE_CAP].rstrip() + "..."
    return text


def _sorted_list(value):
    """Sorted string list for any record field that may be absent."""
    if isinstance(value, list):
        return sorted(str(item) for item in value)
    return []


def _bool_str(value):
    return "True" if value else "False"


def _flag_line(entry):
    """One argparse add_argument entry as a stable single line."""
    flags = entry.get("flags") or []
    kwargs = entry.get("kwargs") or {}
    spellings = []
    for flag in flags:
        spelling = str(flag)
        metavar = kwargs.get("metavar")
        if spelling.startswith("--") and metavar:
            spelling = "{0} {1}".format(spelling, metavar)
        spellings.append(spelling)
    help_text = _WS.sub(" ", str(kwargs.get("help") or "")).strip()
    line = "  {0}".format(" | ".join(spellings) if spellings else "-")
    if help_text:
        line = "{0} -- {1}".format(line, help_text)
    return line


def _argparse_block(record):
    """The argparse word face of a record as deterministic lines."""
    argparse_face = record.get("argparse") or {}
    added = argparse_face.get("add_argument") or []
    positionals = []
    optionals = []
    for entry in added:
        if not isinstance(entry, dict):
            continue
        flags = entry.get("flags") or []
        takes_value_flag = bool(flags) and str(flags[0]).startswith("--")
        if takes_value_flag:
            optionals.append(_flag_line(entry))
        else:
            positionals.append(_flag_line(entry))
    subcommands = argparse_face.get("subcommands") or []
    descriptions = [
        _WS.sub(" ", str(text)).strip()
        for text in (argparse_face.get("parser_descriptions") or [])
        if str(text).strip()
    ]
    header = "argparse: {0} positionals, {1} optionals, {2} subcommands".format(
        len(positionals), len(optionals), len(subcommands)
    )
    if descriptions:
        header = "{0} (parser description: {1})".format(
            header, "; ".join(descriptions)
        )
    lines = [header]
    lines.extend(positionals)
    lines.extend(optionals)
    return lines


def _summary_line(record, roster):
    """One summary line: name | one-phrase purpose | MCP face count."""
    name = record.get("name") or "(unnamed)"
    count = len(roster.get(name, ()))
    noun = "face" if count == 1 else "faces"
    return "{0} | {1} | {2} mcp {3}".format(name, one_phrase(record), count, noun)


def render_summary(files, roster):
    """The summary face: exactly one line per tool, nothing else."""
    lines = [_summary_line(record, roster) for record in sorted(
        files, key=lambda record: record.get("name") or "")]
    return "\n".join(lines) + "\n"


def render_record(record, flag_shape, roster):
    """One full record block; --tool output is exactly this text."""
    name = record.get("name") or "(unnamed)"
    shape = flag_shape.get(name) or {}
    shape_bools = _sorted_list(shape.get("bool_flags"))
    shape_values = _sorted_list(shape.get("value_flags"))
    shape_positionals = _sorted_list(shape.get("positionals"))
    imports = record.get("imports") or {}
    network = record.get("network") or {}
    git_face = network.get("git_subprocess_network_face") or {}
    skip = record.get("skip_face") or {}
    markers = skip.get("markers") or []
    marker_texts = []
    for marker in markers:
        if isinstance(marker, dict):
            marker_texts.append(
                "{0}({1})".format(marker.get("kind", "?"), marker.get("count", "?"))
            )
    mcp_names = sorted(roster.get(name, ()))
    invocation = record.get("invocation") or {}
    form = str(invocation.get("form") or "").strip() or "-"
    basis = str(invocation.get("basis") or "").strip() or "-"
    usage_face = record.get("usage_face") or []
    lines = [
        "### tools/{0}".format(name),
        "purpose: {0}".format(one_phrase(record)),
        "size: {0} bytes | {1} lines | sha256 {2}".format(
            record.get("bytes", "-"), record.get("lines", "-"),
            record.get("sha256", "-"),
        ),
        "invocation: {0} (basis: {1})".format(form, basis),
        "flag_shape: bool=[{0}] value=[{1}] positionals=[{2}]".format(
            ", ".join(shape_bools) or "-",
            ", ".join(shape_values) or "-",
            ", ".join(shape_positionals) or "-",
        ),
    ]
    lines.extend(_argparse_block(record))
    lines.append(
        "imports: stdlib=[{0}] third_party=[{1}] local=[{2}] guarded=[{3}]".format(
            ", ".join(_sorted_list(imports.get("modules"))) or "-",
            ", ".join(_sorted_list(imports.get("third_party"))) or "-",
            ", ".join(_sorted_list(imports.get("local"))) or "-",
            ", ".join(_sorted_list(imports.get("guarded_conditional"))) or "-",
        )
    )
    lines.append(
        "network: zero={0} transports=[{1}] literals=[{2}] adjacent=[{3}] "
        "subprocess_bridge_suspect={4} git_subprocess_face={5}".format(
            _bool_str(network.get("zero_network")),
            ", ".join(_sorted_list(network.get("transport_imports"))) or "-",
            ", ".join(_sorted_list(network.get("literal_face"))) or "-",
            ", ".join(_sorted_list(network.get("adjacent_imports"))) or "-",
            _bool_str(network.get("subprocess_bridge_suspect")),
            _bool_str(git_face.get("present")),
        )
    )
    if usage_face:
        lines.append("usage_face: {0} lines".format(len(usage_face)))
        for text in usage_face:
            lines.append("  {0}".format(_WS.sub(" ", str(text)).strip()))
    lines.append(
        "selftest: flag={0} token_face={1}".format(
            _bool_str(record.get("selftest_flag")),
            _bool_str(record.get("selftest_token_face")),
        )
    )
    lines.append(
        "skip_face: special_environment={0} markers=[{1}]".format(
            _bool_str(skip.get("needs_special_environment")),
            ", ".join(marker_texts) or "-",
        )
    )
    lines.append(
        "mcp_faces: {0} {1}".format(
            len(mcp_names), ", ".join(mcp_names) if mcp_names else "(none)"
        )
    )
    return "\n".join(lines) + "\n"


def render_full(files, flag_shape, roster):
    """The full index face: header plus one record block per sorted tool.

    Deterministic by construction: the header carries no timestamp, every
    list is sorted, and the master texts alone decide the bytes, so two runs
    over the same masters are byte-identical.
    """
    ordered = sorted(files, key=lambda record: record.get("name") or "")
    header = "\n".join([
        "# rocqwash tool capability index (census render)",
        "masters: {0} (primary) + {1} (secondary) + TOOL_SPECS roster from "
        "{2}".format(CENSUS_REL, FLAG_SHAPE_REL, ROSTER_REL),
        "tools: {0} | order: sorted by tool name | mode: full | generator: "
        "tools/{1}.py (no timestamps; stable across runs)".format(
            len(ordered), TOOL
        ),
    ])
    blocks = [
        render_record(record, flag_shape, roster) for record in ordered
    ]
    return header + "\n" + "\n".join(blocks)


def normalize_tool_name(raw):
    """Accept chain_graph, chain_graph.py or tools/chain_graph.py."""
    text = str(raw).strip().replace("\\", "/")
    if text.lower().startswith("tools/"):
        text = text[len("tools/"):]
    text = os.path.basename(text)
    if not text.lower().endswith(".py"):
        text = text + ".py"
    return text


def entry_block(full_text, name):
    """The one '### tools/<name>' block from a full render (for --tool)."""
    marker = "### tools/{0}\n".format(name)
    start = full_text.find(marker)
    if start < 0:
        return None
    nxt = full_text.find("\n### tools/", start + len(marker))
    # nxt sits on the separator newline the block join added, so slicing
    # up to it keeps exactly render_record's single trailing newline.
    block = full_text[start:] if nxt < 0 else full_text[start:nxt]
    return block


def _check(fails, name, ok, detail=""):
    if ok:
        print("[PASS] {0}".format(name))
    else:
        fails.append(name)
        print("[FAIL] {0} {1}".format(name, detail))


def run_selftest(root):
    """Fixture vectors, then the three real-master vectors; 0 green, 1 red."""
    fails = []

    # ---- fixture layer: the extractor and the render contracts, hermetic.
    fixture_records = [
        {
            "name": "alpha_probe.py",
            "docstring": {"head": "alpha_probe.py v2: R7 probe runner "
                                  "(fixpoint rounds, fail-loud).\n\nPurpose."},
            "bytes": 10, "lines": 2, "sha256": "a" * 64,
            "invocation": {"form": "python tools/alpha_probe.py <dir>",
                           "basis": "argparse-reconstructed"},
            "argparse": {"add_argument": [
                {"flags": ["--json"], "kwargs": {"metavar": "out.json",
                                                 "help": "json output"}},
                {"flags": ["src"], "kwargs": {"metavar": "SRC",
                                              "help": "source dir"}},
            ], "parser_descriptions": ["probe -> report"]},
            "imports": {"modules": ["os", "sys"], "third_party": [],
                        "local": [], "guarded_conditional": []},
            "network": {"zero_network": True, "transport_imports": [],
                        "literal_face": [], "adjacent_imports": [],
                        "subprocess_bridge_suspect": False,
                        "git_subprocess_network_face": {"present": False}},
            "usage_face": [], "selftest_flag": True,
            "selftest_token_face": False,
            "skip_face": {"needs_special_environment": False, "markers": []},
        },
        {
            "name": "beta_tool.py",
            "docstring": {"head": "beta_tool"},
            "bytes": 3, "lines": 1, "sha256": "b" * 64,
            "invocation": {"form": "", "basis": "not-reconstructed"},
            "argparse": {"add_argument": []},
            "imports": {}, "network": {},
            "usage_face": [], "selftest_flag": False,
            "selftest_token_face": False, "skip_face": {},
        },
    ]
    fixture_roster = {"alpha_probe.py": ["alpha_probe"], "beta_tool.py": []}
    fixture_shape = {
        "alpha_probe.py": {"positionals": [], "value_flags": ["--json"],
                           "bool_flags": []},
    }

    phrases = {r["name"]: one_phrase(r) for r in fixture_records}
    _check(fails, "fixture-phrase-version-prefix",
           phrases["alpha_probe.py"] == "R7 probe runner",
           "got %r" % phrases["alpha_probe.py"])
    _check(fails, "fixture-phrase-no-docstring",
           phrases["beta_tool.py"] == NO_DOCSTRING_PHRASE,
           "got %r" % phrases["beta_tool.py"])
    long_record = {
        "name": "gamma_long.py",
        "docstring": {"head": "gamma_long.py - " + ("word " * 30)},
    }
    long_phrase = one_phrase(long_record)
    _check(fails, "fixture-phrase-cap",
           long_phrase.endswith("...")
           and len(long_phrase) == PHRASE_CAP + 3,
           "got len=%d tail=%r" % (len(long_phrase), long_phrase[-10:]))

    fixture_summary = render_summary(fixture_records, fixture_roster)
    summary_lines = fixture_summary.splitlines()
    _check(fails, "fixture-summary-line-count",
           len(summary_lines) == len(fixture_records),
           "got %d lines for %d tools" % (len(summary_lines),
                                          len(fixture_records)))
    _check(fails, "fixture-summary-nonempty",
           all(line.strip() for line in summary_lines), "")
    _check(fails, "fixture-summary-name-prefixed",
           all(line.split(" | ")[0] == record["name"]
               for line, record in zip(summary_lines,
                                       sorted(fixture_records,
                                              key=lambda r: r["name"]))),
           "")
    _check(fails, "fixture-summary-face-counts",
           summary_lines[0].endswith("1 mcp face")
           and summary_lines[1].endswith("0 mcp faces"),
           "got %r / %r" % (summary_lines[0], summary_lines[1]))

    fixture_full = render_full(fixture_records, fixture_shape, fixture_roster)
    fixture_tool = render_record(fixture_records[0], fixture_shape,
                                 fixture_roster)
    _check(fails, "fixture-tool-block-equality",
           entry_block(fixture_full, "alpha_probe.py") == fixture_tool,
           "block and single render diverged")

    # ---- real-master layer: the three R-4 vectors over the actual census.
    census_path, files = load_census(root)
    flag_shape = load_flag_shape(root)[1]
    roster = load_roster(root)
    tool_count = len(files)
    names = sorted(record.get("name") or "" for record in files)
    name_set = set(names)

    summary_text = render_summary(files, roster)
    real_lines = summary_text.splitlines()
    _check(fails, "real-summary-line-count-equals-tool-count",
           len(real_lines) == tool_count,
           "got %d lines for %d tools in %s" % (len(real_lines), tool_count,
                                                census_path))
    _check(fails, "real-summary-every-line-nonempty",
           all(line.strip() for line in real_lines), "")
    _check(fails, "real-summary-name-prefixed",
           all(line.split(" | ")[0] in name_set for line in real_lines),
           "a summary line does not start with a census tool name")

    probe_tool = "chain_graph.py"
    if probe_tool not in name_set:
        probe_tool = names[0]
    tool_text = render_record(
        next(record for record in files
             if record.get("name") == probe_tool),
        flag_shape, roster,
    )
    full_text = render_full(files, flag_shape, roster)
    full_lines = full_text.splitlines()
    entry_markers = [
        line for line in full_lines if line.startswith("### tools/")
    ]
    _check(fails, "real-tool-single-entry",
           tool_text.startswith("### tools/{0}\n".format(probe_tool))
           and tool_text.count("### tools/") == 1
           and entry_block(full_text, probe_tool) == tool_text,
           "the --tool render is not exactly the one full-mode block")
    _check(fails, "real-full-byte-stability",
           render_full(files, flag_shape, roster) == full_text,
           "two full renders over the same masters differ")
    _check(fails, "real-full-sorted",
           entry_markers == ["### tools/{0}".format(name) for name in names],
           "entry headers are not the sorted tool set")
    _check(fails, "real-full-entry-count",
           len(entry_markers) == tool_count,
           "got %d entries for %d tools" % (len(entry_markers), tool_count))
    return 0 if not fails else 1


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="tools/{0}.py".format(TOOL),
        description="census-rendered tool capability index (full | summary "
                    "| single-tool record)",
    )
    parser.add_argument(
        "--mode", choices=("full", "summary"), default="full",
        help="full (default) renders the complete sorted record set; "
             "summary renders one line per tool (name, one-phrase purpose, "
             "MCP face count)",
    )
    parser.add_argument(
        "--tool", metavar="NAME", default=None,
        help="render only this tool's full record (with or without .py); "
             "full mode only",
    )
    parser.add_argument(
        "--selftest", action="store_true",
        help="run the fixture and real-master vectors; standalone",
    )
    args = parser.parse_args(argv)
    if args.selftest and (args.mode != "full" or args.tool):
        parser.error("--selftest runs standalone; combine it with no render "
                     "flags")
    if args.tool and args.mode == "summary":
        parser.error("--tool renders a full record; it may not be combined "
                     "with --mode summary")
    if args.selftest:
        return run_selftest(repo_root())
    root = repo_root()
    try:
        census_path, files = load_census(root)
        _, flag_shape = load_flag_shape(root)
        roster = load_roster(root)
    except MasterError as exc:
        sys.stderr.write("{0}: error: {1}\n".format(TOOL, exc))
        return 1
    if args.tool:
        name = normalize_tool_name(args.tool)
        record = None
        for candidate in files:
            if candidate.get("name") == name:
                record = candidate
                break
        if record is None:
            parser.error(
                "--tool: no census entry for {0!r} ({1} tools in {2}; pass "
                "the census name)".format(args.tool, len(files), census_path)
            )
        text = render_record(record, flag_shape, roster)
    elif args.mode == "summary":
        text = render_summary(files, roster)
    else:
        text = render_full(files, flag_shape, roster)
    sys.stdout.buffer.write(text.encode("utf-8"))
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
