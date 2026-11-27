#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""wash_shape.py: shape-normalizing tool, canonical seven-wash pipeline (rocqwash tools/).
Purpose.  Applies the canonical wash pipeline to every target file in
  order (each wash selectable via --only): 1 lexical, 2 token, 3 header,
  4 eol, 5 anchor, 6 jargon, 7 ai-flavor (advisory); per-wash contracts
  (engines, rewrite faces, gate semantics) in the contract block below.
  Two phases: plan (zero writes; per-wash {kind,action,status,detail} list plus stats) then --apply (execute
  would-fix items, re-run all washes, verdict shaped only when the
  rescan is fully clean).  verdict: clean | shaped | partial | plan-miss;
  dry run by default, writes only under --apply.
Interface.  python3 tools/wash_shape.py --file A.v [--file B.v ...]
  [--json OUT] | --dir TREE [--exclude NAME ...] [--only 1,3,6] [--apply]
  [--header-map M.json | --header-map-preset NAME] [--anchor-src DIR]
  | --loop [--interval S] [--max-rounds N] [--events FILE] | --selftest.
  Report schema rocqwash-shape/1; loop events rocqwash-sentinel-event/1;
  the probe order, exclusivity, and frozen-surface rules are in the
  contract block below.
Dependencies.  Python 3 standard library only; every path parameterized,
  zero hardcoded absolute paths, zero network.  The wash engines run as
  subprocesses (`python3 -B <engine>`): orchestration, never
  re-implementation; --injector cans the subprocess call layer;
  --sleep-scale scales sleeps to zero for the selftest.
Evidence.  --selftest: 18 frozen vectors on temporary fixtures covering
  per-wash plan verdicts, zero-write plan, plan-miss honesty,
  apply->rescan->shaped, idempotence, frozen-roster exclusion, injector
  layer, CLI codes, loop/once modes, determinism, the preset chain, plan-cache invalidation; suite tests/test_wash_shape.py.
Exit-codes.  0 clean/shaped; 1 partial/plan-miss (reported loudly); 2
  usage/assertion (frozen rejection, engine exit, malformed JSON,
  same-slot exclusivity); 9 missing input path (per-case detail in the
  extended contract).
"""

# Former-header detail (carried out of the header on the RIS-19 budget
# cure, verbatim in substance):
# Exit-code detail: 9 = missing input path (--file/--dir/engine file/
#   template library/env map/--injector/--events write failure).
# Template-source probe order: --header-map > --header-map-preset > env
#   ROCWASH_HEADER_MAP > none (= plan-miss, reported honestly);
#   --header-map and --header-map-preset are same-slot mutually exclusive
#   (rc 2).  The preset source rewrites only gate4 header-domain hard
#   items and never aligns an already-conforming five-field header (a
#   human-curated face is never machine-rewritten).  Frozen surfaces
#   (the certify/frozen8.py roster and the frozen ledger) are
#   auto-excluded on --dir and hard-rejected on explicit --file (exit 2).

# Extended contract (kept outside the five-field block per the annotation
# standard 30-line header budget):
# wash 1 lexical  subprocess `verify/gate4_comment_guard.py --file` (five check
#                 items, v2.1 EXT; rc 0/1/2 routing follows the tools/pushci.py
#                 gate4_prescan precedent).  FAIL items (hard word-face items)
#                 and review dual-sense items are looked up in the
#                 `wash/comment_pack.json` flag_words table for the canonical
#                 same-meaning rewrite (the sidecar declares trigger = "gate4
#                 comment-guard review findings"; flag_word_note = "Context-biaised
#                 review words exchange to their neutral English term"; the
#                 dual-sense review items are exactly that pack's exchange
#                 targets).  The rewrite is applied by `wash/comment_sweep.py
#                 --apply` (a comment_pack consumer: nesting/string-aware state
#                 machine with a code-line equality assertion).  No entry ->
#                 plan-miss (never synthesized; same rule as comment_pack's
#                 "never synthesized").
# wash 2 token    `scan/scan_v4_token.py --file` survey (token level; closes the
#                 W5 mixed-line blind spot) -> `wash/cure_applier.py` canonical
#                 pack (cure_pack v1.3) dry run (that engine is dry run by
#                 default) -> --apply applies the rewrite (a second-pass
#                 zero-residue assertion is built in; rc 1 writes nothing).
#                 Stations without an entry -> plan-miss; exclusive-group
#                 conflict (rc 4) -> plan-miss and the operator must pick one
#                 via --only (cure_applier variant-choice discipline).
# wash 3 header   two-part header + five-field missing checks (gate4 already
#                 reports: no header / header not first block / missing fields /
#                 over-budget header).  The missing-field cure = comment_pack
#                 style full-header rewrite template (--header-map, per-file
#                 data; comment_sweep --header-map replaces the leading comment
#                 zone wholesale and never synthesizes content); or
#                 --header-map-preset designated templates (the tests/fixtures/
#                 header_map_v1.json distilled library, schema
#                 rocqwash-header-map/1; placeholders {name}/{deps_stdlib}/
#                 {deps_dev} derive from the target's Require faces and file
#                 name; {bundle}/{summary}/{mission} carry the existing header
#                 verbatim; any unbound placeholder is plan-miss, never
#                 synthesized; the rendered text is still applied through
#                 comment_sweep --header-map).  No template -> plan-miss.
# wash 4 eol      CRLF->LF normalization (final-newline form preserved; the 3KB
#                 probe window follows tools/registry_union.py detect_eol
#                 EOL_PROBE_BYTES).  Earlier universal-newline engine write-backs
#                 already normalize as a side effect; this wash's apply reports
#                 what the on-disk bytes actually show, including a zero-change
#                 pass, honestly.
# wash 5 anchor   order.txt line anchors -> registry_union.py --reanchor
#                 canonical form (#R<seq>-<md5 first 8 hex>; both sequence-only
#                 anchors and cross-batch anchor collisions are cured here;
#                 --reanchor pairs with --anchor-src; --apply requires --out
#                 and lands via a temp file os.replace).  coqproject rows carry
#                 no anchors -> not applicable.  Missing entity / ambiguous
#                 entity / anchorless row -> plan-miss (same rule as
#                 registry_union's honest skip listing).
# wash 6 jargon   tools/jargon_apply.py over the .py/.sh/.md prose faces
#                 (the engine-body ticket, lane 2; roadmap
#                 step 2 wiring).  Plan runs the engine's --plan (zero
#                 writes): machine-applicable occurrences from the 62-entry
#                 seed map are would-fix; guarded and rewrite_or_delete rows
#                 are human findings -> plan-miss items (never machine
#                 applied).  --apply runs the engine's --apply, whose own
#                 rescan keeps residue zero as the exit-zero gate; the
#                 shaper's re-run of all washes verifies the same state.
# wash 7 ai-flavor advisory stage (engine-body batch lane 3; ai-flavor seed
#                 SPEC section 4 path 1; design change: every write goes
#                 through the rewrite provider, machine substitution stays
#                 banned).  Plan runs tools/ai_flavor_apply.py plan mode
#                 (zero writes): provider-eligible suggestions (neutral
#                 direct forms, delete-or-restate) are would-fix with the
#                 handoff route as their action; ban-remediation faces and
#                 em-dash occurrences are human items -> plan-miss items.
#                 --apply runs the engine's --emit-handoff (the package
#                 lands in the shaper's process working directory: the
#                 subprocess inherits the caller's CWD and the emit path
#                 is a bare basename, so the file lands next to where
#                 wash_shape runs, not beside the target; the target
#                 itself is untouched):
#                 the write completes only after the provider fills the rows
#                 and --apply-handoff ingests them, so until that round trip
#                 the rescan reports the residual findings loudly (verdict
#                 partial, never a silent shaped).
# two phases      plan (zero writes; per-file per-wash {kind,action,
#                 status: would-fix|clean|plan-miss, detail} list + stats)
#                 -> --apply (execute would-fix items -> re-run all washes
#                 -> verdict shaped only when fully clean; a dirty rescan is
#                 verdict partial with the residual items listed honestly).
# loop mode       --loop watch mode: one pass per round; the plan cache keys on
#                 the {abspath: md5} set of scope files plus wash-5 anchor
#                 entities: a stable domain reuses the previous plan (cache
#                 hit, zero engine re-runs), any source md5 change invalidates
#                 and recomputes.  First round always recomputes; --once skips
#                 the cache; rescan always computes fresh (post-apply disk
#                 state is never reused).  Loud accounting = report["plan_cache"]
#                 {hit} (loop mode only) plus the round event plan_cache_hit.

import argparse
import datetime
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

PROG = "wash_shape"
SCHEMA = "rocqwash-shape/1"
EVENT_SCHEMA = "rocqwash-sentinel-event/1"   # --loop event stream, same shape as cw_sentinel

# wash kinds (canonical order; --only number map 1..7)
KIND_LEXICAL = "lexical"    # wash 1: lexical
KIND_TOKEN = "token"        # wash 2: token
KIND_HEADER = "header"      # wash 3: header
KIND_EOL = "eol"            # wash 4: eol
KIND_ANCHOR = "anchor"      # wash 5: anchor
KIND_JARGON = "jargon"      # wash 6: jargon (engine-body batch, roadmap step 2)
KIND_AIFLAVOR = "ai-flavor"  # wash 7: ai-flavor advisory (provider-gated)
KINDS = (KIND_LEXICAL, KIND_TOKEN, KIND_HEADER, KIND_EOL, KIND_ANCHOR,
         KIND_JARGON, KIND_AIFLAVOR)
KIND_ALIASES = {
    "1": KIND_LEXICAL, "2": KIND_TOKEN, "3": KIND_HEADER,
    "4": KIND_EOL, "5": KIND_ANCHOR, "6": KIND_JARGON, "7": KIND_AIFLAVOR,
    KIND_LEXICAL: KIND_LEXICAL, KIND_TOKEN: KIND_TOKEN,
    KIND_HEADER: KIND_HEADER, KIND_EOL: KIND_EOL, KIND_ANCHOR: KIND_ANCHOR,
    KIND_JARGON: KIND_JARGON, KIND_AIFLAVOR: KIND_AIFLAVOR,
    "ai_flavor": KIND_AIFLAVOR,
}

STATUS_WOULD_FIX = "would-fix"
STATUS_CLEAN = "clean"
STATUS_PLAN_MISS = "plan-miss"

VERDICT_CLEAN = "clean"
VERDICT_SHAPED = "shaped"
VERDICT_PARTIAL = "partial"
VERDICT_PLAN_MISS = "plan-miss"

# gate4 header-domain hard-item types (wash 3 territory; not counted by the
# lexical wash).  Tuple and tag values are gate4's own output vocabulary,
# interface data, kept verbatim.
HEADER_ITEM_TYPES = ("缺字段", "无头注", "头注非首块", "头注超标")
REVIEW_DUAL = "语境双义复核"   # comment_pack exchange target (flag_word_note sense)

# anchor canonical form mirrors registry_union.ANCHOR_RE 1:1; eol probe window mirrors detect_eol
ANCHOR_RE = re.compile(r"#(R\d+(?:-[0-9A-Fa-f]+)?)")
EOL_PROBE_BYTES = 3072

REGISTRY_KINDS = {"order.txt": "order", "_CoqProject": "coqproject"}
LEDGER_NAME = "更新账.md"   # frozen-surface filename (auto-excluded; explicit naming is a hard rejection)

ACTION_SWEEP = "wash/comment_sweep.py --apply"
ACTION_SWEEP_MAP = "wash/comment_sweep.py --header-map <MAP> --apply"
ACTION_SWEEP_MAP_PRESET = "wash/comment_sweep.py --header-map <preset 渲染> --apply"
ACTION_CURE = "wash/cure_applier.py --apply"
ACTION_EOL = "wash_shape:eol-rewrite(CRLF->LF)"
ACTION_REGU = "tools/registry_union.py --reanchor --apply"
ACTION_JARGON = "tools/jargon_apply.py --apply"
ACTION_AIFLAVOR = ("tools/ai_flavor_apply.py --emit-handoff <OUT.jsonl>"
                   " -> provider fills rows -> --apply-handoff <IN.jsonl>"
                   " --state <P>")

# prose-face extension sets of the two engine-body stages (the faces their
# engines document; a target outside the set is not applicable, reported clean)
JARGON_FACES = (".py", ".sh", ".md")
AIFLAVOR_FACES = (".py", ".sh", ".md", ".json", ".ts")

# wash-3 header template source (probe order --header-map > --header-map-preset > env > none=plan-miss)
HEADER_LIB_REL = os.path.join("tests", "fixtures", "header_map_v1.json")
HEADER_LIB_SCHEMA = "rocqwash-header-map/1"
ENV_HEADER_MAP = "ROCWASH_HEADER_MAP"
PH_RE = re.compile(r"\{([a-z_]+)\}")
RE_BUNDLE_L1 = re.compile(
    r"^\(\*\s*ConstructiveWorld-Set\s*--\s+(.+?)\.\s*\*\)\s*$")
RE_TITLE_LINE = re.compile(
    r"^\(\*\*\s*\*\s*[A-Za-z0-9_']+\s*:\s+(.+?)\.\s*$")
RE_MISSION_LABEL = re.compile(r"^\s*Mission\.\s*(.*)$")
RE_NEXT_FIELD = re.compile(
    r"^\s*(?:Dependencies|References|Constructivity|Build)\.")
RE_FROM_STDLIB = re.compile(
    r"^From\s+Stdlib\s+Require(?:\s+(?:Import|Export))?\s+(.+?)\s*\.\s*$")
RE_FROM_OTHER = re.compile(
    r"^From\s+(?!Stdlib\b)(\S+)\s+Require(?:\s+(?:Import|Export))?\s+"
    r"(.+?)\s*\.\s*$")
RE_BARE_REQUIRE = re.compile(
    r"^Require(?:\s+(?:Import|Export))?\s+(.+?)\s*\.\s*$")


class UsageError(Exception):
    """Usage/assertion failure (exit 2: frozen-surface rejection, engine out-of-shape exit, malformed JSON)."""


class MissingInput(Exception):
    """Missing input path (exit 9)."""


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def sleep_scaled(sec, scale):
    """time.sleep(sec*scale); scale=0 means no real sleep (selftest vector dependency; same form as pushci)."""
    time.sleep(max(0.0, float(sec) * float(scale)))


def now_iso():
    """UTC ISO8601 second-precision Z form (event ts field; same shape as cw_sentinel.now_iso)."""
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def make_event(seq, kind, fields, ts_enabled):
    """--loop event assembly (same shape as cw_sentinel.make_event): schema/
    seq/kind header plus fields; ts comes from the clock, and ts_enabled=False
    (--sleep-scale 0) drops ts and annotates note "ts=off" (deterministic;
    merges cleanly when fields already carry a note)."""
    ev = {"schema": EVENT_SCHEMA, "seq": seq, "kind": kind}
    ev.update(fields)
    if ts_enabled:
        ev["ts"] = now_iso()
    else:
        # KEEP (data face): the note value and its joiner are rocqwash-sentinel-event/1
        # schema data: shared parsing face with cw_sentinel, kept verbatim.
        off = "ts=off（--sleep-scale 0·确定性输出）"
        base = ev.pop("note", None)
        ev["note"] = (off + "｜" + base) if base else off
    return ev


def events_seq_base(path):
    """Number of existing non-empty lines in --events (cross-process seq base;
    same rule as cw_sentinel emit_seq_base: an append stream continues
    numbering from its existing lines).  Read failure -> 9."""
    try:
        with io.open(path, "r", encoding="utf-8") as fh:
            return sum(1 for ln in fh if ln.strip())
    except OSError as e:
        raise MissingInput("--events seq base read failed: %s (%s)" % (path, e))


def first_code_offset(text):
    """Offset of the first code character (depth 0, non-whitespace, comment/
    string aware): the leading header-zone boundary.  A 1:1 local
    re-implementation of wash/comment_sweep.py first_code_offset (no import;
    engine drift must not couple into this file; same rule as the
    wash_engine.py local re-implementation)."""
    n = len(text)
    i = 0
    depth = 0
    in_str = False
    while i < n:
        c = text[i]
        if in_str:
            if c == "\\" and i + 1 < n:
                i += 2
                continue
            if c == '"':
                in_str = False
            i += 1
            continue
        if depth > 0:
            if text.startswith("(*", i):
                depth += 1
                i += 2
                continue
            if text.startswith("*)", i):
                depth -= 1
                i += 2
                continue
            i += 1
            continue
        if text.startswith("(*", i):
            depth = 1
            i += 2
            continue
        if c == '"':
            in_str = True
            i += 1
            continue
        if not c.isspace():
            return i
        i += 1
    return None


def resolve_entity(name, anchor_src):
    """Resolve the same-named .v entity under anchor_src (os.walk recursive).
    Zero hits -> None; multiple hits -> an ambiguity string.
    1:1 with registry_union.resolve_entity."""
    target = name + ".v"
    direct = os.path.join(anchor_src, target)
    if os.path.isfile(direct):
        return direct
    hits = []
    for root, _dirs, files in os.walk(anchor_src):
        if target in files:
            hits.append(os.path.join(root, target))
    if len(hits) > 1:
        return "AMBIGUOUS:" + ",".join(sorted(hits))
    return hits[0] if hits else None


def md5_8_of(path):
    """First 8 hex of the entity md5 (anchor canonical fingerprint source; mirrors registry_union.md5_8_of)."""
    return md5_of(path)[:8]


def tail_of(text, n=200):
    t = (text or "").strip()
    return t[-n:] if len(t) > n else t


def strip_comment_spans(text):
    """Strip comment spans (newlines kept, string-aware): the Require-face
    extraction precondition.  A 1:1 local re-implementation of
    wash/comment_sweep.py strip_comments (no import; engine drift must not
    couple into this file; same rule as first_code_offset)."""
    out = []
    i, n = 0, len(text)
    depth = 0
    in_str = False
    while i < n:
        c = text[i]
        if in_str:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 2
                continue
            if c == '"':
                in_str = False
            i += 1
            continue
        if depth > 0:
            if text.startswith("(*", i):
                depth += 1
                i += 2
                continue
            if text.startswith("*)", i):
                depth -= 1
                i += 2
                continue
            if c == "\n":
                out.append(c)
            i += 1
            continue
        if text.startswith("(*", i):
            depth += 1
            i += 2
            continue
        if c == '"':
            in_str = True
            out.append(c)
            i += 1
            continue
        out.append(c)
        i += 1
    return "".join(out)


def wrap_long_line(line, width=76, sub="      "):
    """Greedy word wrap (wraps only when >width and containing spaces;
    continuation lines indent by 6; an over-long single word is kept whole),
    the preset render wrapping form (corpus files wrap at width ~76 with 6-space
    continuations; shape evidenced by DecBridge6.v:19-29)."""
    if len(line) <= width or " " not in line.strip():
        return [line]
    words = line.split(" ")
    rows, cur = [], words[0]
    for w in words[1:]:
        if len(cur) + 1 + len(w) <= width:
            cur = cur + " " + w
        else:
            rows.append(cur)
            cur = w
    rows.append(cur)
    return [rows[0]] + [sub + r for r in rows[1:]]


def require_faces(text):
    """Two-column Require-face extraction (the wash-3 preset placeholder
    {deps_stdlib}/{deps_dev} data source; names taken one by one from the
    target file's own statements, never synthesized).  After comment-aware
    stripping (strip_comment_spans) only column-0 top-level statement lines
    count:
      From Stdlib Require [Import|Export] A B.  -> stdlib column
      Require [Import|Export] A B.              -> dev column
      From <X> Require [Import|Export] A B.     -> dev column (qualified X.A;
        the corpus grep found zero bare-From cases; the mechanical
        completeness arm).
    Order = order of appearance in the file, deduplicated preserving first
    occurrence.  Corpus evidence: ConstructiveWorld-Set @6e805d1
    LW3Kills.v:30-38 (three From Stdlib lines + six bare lines) against its
    header columns :13-17; abl_tail_supply_67.v:32-35 against :15-16."""
    stdlib, dev = [], []
    for ln in strip_comment_spans(text).split("\n"):
        ln = ln.rstrip()
        names, is_std = None, False
        m = RE_FROM_STDLIB.match(ln)
        if m:
            names, is_std = m.group(1).split(), True
        else:
            m = RE_FROM_OTHER.match(ln)
            if m:
                names = ["%s.%s" % (m.group(1), n) for n in m.group(2).split()]
            else:
                m = RE_BARE_REQUIRE.match(ln)
                if m:
                    names = m.group(1).split()
        if not names:
            continue
        tgt = stdlib if is_std else dev
        for nm in names:
            if nm not in tgt:
                tgt.append(nm)
    return stdlib, dev


def header_carry(text):
    """Verbatim-carry extraction of the existing leading header zone (the
    binding source for the preset placeholders {bundle}/{summary}/{mission}).
    Returns a dict: a missing key means that placeholder cannot bind (the
    judge records plan-miss honestly, never synthesizes):
      bundle  = the inside of the L1 `(* ConstructiveWorld-Set -- <body>. *)`
                line (the final period belongs to the template line);
      summary = the inside of the `(** * <name>: <body>.` title line (the
                final period belongs to the template line);
      mission = the Mission field body (label-line remainder plus continuation
                lines up to the next field label / comment close, newline and
                indentation carried verbatim).
    Corpus evidence: ConstructiveWorld-Set @6e805d1 DecBridge6.v:1/:3/:5-14,
    the three canonical bodies; header body content is never synthesized
    (same rule as comment_pack header_spec)."""
    off = first_code_offset(text)
    zone = text[:off] if off is not None else text
    lines = zone.split("\n")
    carry = {}
    for ln in lines:
        if "bundle" not in carry:
            m = RE_BUNDLE_L1.match(ln)
            if m:
                carry["bundle"] = m.group(1).strip()
        if "summary" not in carry:
            m = RE_TITLE_LINE.match(ln)
            if m:
                carry["summary"] = m.group(1).strip()
    for i, ln in enumerate(lines):
        m = RE_MISSION_LABEL.match(ln)
        if not m:
            continue
        parts = [m.group(1).rstrip()] if m.group(1).strip() else []
        j = i + 1
        while j < len(lines):
            l2 = lines[j]
            if RE_NEXT_FIELD.match(l2) or l2.lstrip().startswith("*)"):
                break
            parts.append(l2.rstrip())
            j += 1
        while parts and not parts[0].strip():
            parts.pop(0)
        while parts and not parts[-1].strip():
            parts.pop()
        carry["mission"] = "\n".join(parts)
        break
    return carry


class Injector(object):
    """--injector scenario: canning the subprocess call layer (offline
    testability).  Scenario JSON {engine key: {"rc": int, "stdout": str,
    "report": obj?}}; an engine call whose key matches always returns the
    canned response (same response per call); no real subprocess.  Key set =
    gate4/scan_v4/cure/sweep/registry_union/frozen8/jargon/ai_flavor."""

    KEYS = ("gate4", "scan_v4", "cure", "sweep", "registry_union", "frozen8",
            "jargon", "ai_flavor")

    def __init__(self, path):
        if not os.path.isfile(path):
            raise MissingInput("injector scenario missing: %s" % path)
        try:
            with io.open(path, "r", encoding="utf-8") as fh:
                scen = json.load(fh)
        except Exception as e:
            raise UsageError("injector scenario JSON malformed: %s (%s)" % (path, e))
        if not isinstance(scen, dict):
            raise UsageError("injector scenario must be a dict: %s" % path)
        bad = [k for k in scen if k not in self.KEYS]
        if bad:
            raise UsageError("unknown injector scenario key (need one of %s):"
                             " %s" % (",".join(self.KEYS), sorted(bad)))
        self.scen = scen

    def canned(self, key):
        ent = self.scen.get(key)
        if ent is None:
            return None
        if not isinstance(ent, dict):
            raise UsageError("injector canned entry must be a dict: %s" % key)
        return ent


class WashShape(object):
    """Shaper body: collect files -> per-wash plan -> per-wash apply -> rescan verification."""

    def __init__(self, args):
        self.args = args
        here = os.path.dirname(os.path.abspath(__file__))
        self.repo_root = os.path.abspath(args.repo_root or
                                         os.path.dirname(here))
        self.tool_gate4 = os.path.join(self.repo_root, "verify",
                                       "gate4_comment_guard.py")
        self.tool_scan4 = os.path.join(self.repo_root, "scan",
                                       "scan_v4_token.py")
        self.tool_cure = os.path.join(self.repo_root, "wash",
                                      "cure_applier.py")
        self.tool_sweep = os.path.join(self.repo_root, "wash",
                                       "comment_sweep.py")
        self.tool_regu = os.path.join(self.repo_root, "tools",
                                      "registry_union.py")
        self.tool_frozen8 = os.path.join(self.repo_root, "certify",
                                         "frozen8.py")
        self.pack_comment = os.path.join(self.repo_root, "wash",
                                         "comment_pack.json")
        # engine-body batch stages (washes 6/7): paths resolved here but
        # existence-checked lazily in their judge faces, so a --only selection
        # that never names them keeps working in a tree that lacks the batch
        self.tool_jargon = os.path.join(self.repo_root, "tools",
                                        "jargon_apply.py")
        self.tool_aiflavor_detect = os.path.join(self.repo_root, "tools",
                                                 "ai_flavor_apply.py")
        for label, p in (("gate4", self.tool_gate4),
                         ("scan_v4", self.tool_scan4),
                         ("cure", self.tool_cure),
                         ("sweep", self.tool_sweep),
                         ("registry_union", self.tool_regu),
                         ("frozen8", self.tool_frozen8),
                         ("comment_pack", self.pack_comment)):
            if not os.path.isfile(p):
                raise MissingInput("engine file missing (%s): %s" % (label, p))
        if args.anchor_src and not os.path.isdir(args.anchor_src):
            raise MissingInput("--anchor-src directory missing: %s" % args.anchor_src)
        self.injector = Injector(args.injector) if args.injector else None
        self.flag_words = self._load_flag_words()
        # wash-3 template source probe (exclusivity already enforced rc 2 in main; order map > preset > env > none)
        self.header_map = None
        self.header_source = "none"
        self.header_map_path = None
        self.header_preset_name = None
        self.header_library_path = None
        self.header_preset = None
        self._preset_render_cache = {}
        self._resolve_header_source()
        self.kinds = parse_only(args.only)
        self.frozen_abs, self.frozen_rel, self.frozen_source = \
            self._load_frozen_roster()
        self.excludes = list(args.exclude or [])
        # --loop event seq (cross-process base fixed in run_loop) + cross-round plan cache
        self._seq = 1
        self._plan_cache = None
        self._plan_md5s = None

    # ---- data plane ----

    def _resolve_header_source(self):
        """wash-3 template source probe (default probe order): --header-map >
        --header-map-preset > env ROCWASH_HEADER_MAP (a map file path, same
        shape as --header-map) > none = plan-miss reported honestly (the
        judge_header default arm).  --header-map and --header-map-preset are
        same-slot exclusive rc 2 (enforced up front in main)."""
        args = self.args
        env_map = os.environ.get(ENV_HEADER_MAP)
        if args.header_map:
            self.header_source = "map"
            self.header_map_path = args.header_map
            self.header_map = self._load_header_map(args.header_map,
                                                    "--header-map")
        elif args.header_map_preset:
            self.header_source = "preset"
            self.header_preset_name = args.header_map_preset
            self.header_library_path = os.path.join(self.repo_root,
                                                    HEADER_LIB_REL)
            self.header_preset = self._load_header_preset()
        elif env_map:
            self.header_source = "map"
            self.header_map_path = env_map
            self.header_map = self._load_header_map(env_map,
                                                    "env " + ENV_HEADER_MAP)

    def _load_flag_words(self):
        """comment_pack.json flag_words (the canonical same-meaning rewrite table; data-driven, never synthesized)."""
        try:
            with io.open(self.pack_comment, "r", encoding="utf-8") as fh:
                pack = json.load(fh)
        except Exception as e:
            raise UsageError("comment_pack JSON malformed: %s (%s)"
                             % (self.pack_comment, e))
        fw = pack.get("flag_words")
        if not isinstance(fw, dict):
            raise UsageError("comment_pack missing the flag_words table: %s"
                             % self.pack_comment)
        return fw

    def _load_header_map(self, path, label):
        """Header map load (comment_pack style full-header rewrite template;
        per-file data; {basename: text}).  Missing = 9; malformed = 2 (label
        names the source: --header-map or env ROCWASH_HEADER_MAP)."""
        if not os.path.isfile(path):
            raise MissingInput("%s missing: %s" % (label, path))
        try:
            with io.open(path, "r", encoding="utf-8") as fh:
                m = json.load(fh)
        except Exception as e:
            raise UsageError("%s JSON malformed: %s (%s)" % (label, path, e))
        if not isinstance(m, dict):
            raise UsageError("%s must be {basename: header text}: %s" % (label, path))
        return m

    def _load_header_preset(self):
        """Designated-template load plus fail-loud shape checks (schema
        rocqwash-header-map/1): missing library = 9; malformed JSON / unknown
        schema / unknown preset name / placeholder outside the allowlist /
        variants without an else fallback / any template line missing its
        evidence citation = 2 (the gold-standard discipline mechanized:
        evidence required before issuance)."""
        path = self.header_library_path
        if not os.path.isfile(path):
            raise MissingInput("--header-map-preset template library missing: %s" % path)
        try:
            with io.open(path, "r", encoding="utf-8") as fh:
                lib = json.load(fh)
        except Exception as e:
            raise UsageError("template library JSON malformed: %s (%s)" % (path, e))
        if not isinstance(lib, dict) or lib.get("schema") != HEADER_LIB_SCHEMA:
            raise UsageError("template library schema unrecognized (need %s):"
                             " %s" % (HEADER_LIB_SCHEMA, path))
        presets = lib.get("presets")
        if not isinstance(presets, dict) or not presets:
            raise UsageError("template library missing the presets table: %s" % path)
        name = self.header_preset_name
        if name not in presets:
            raise UsageError("preset name unrecognized (library %s has: %s):"
                             " %s" % (path, ",".join(sorted(presets)), name))
        pre = presets[name]
        known = lib.get("placeholders")
        if not isinstance(known, dict) or not known:
            raise UsageError("template library missing the placeholders allowlist: %s" % path)
        if not isinstance(pre.get("evidence"), list) or not pre["evidence"]:
            raise UsageError("preset %r missing its evidence citations (evidence"
                             " required before issuance): %s" % (name, path))
        lines = pre.get("lines")
        if not isinstance(lines, list) or not lines:
            raise UsageError("preset %r missing its lines template rows: %s" % (name, path))

        def ph_scan(s, where):
            bad = sorted(set(m.group(1) for m in PH_RE.finditer(s)
                             if m.group(1) not in known))
            if bad:
                raise UsageError("placeholder outside the allowlist (%s): %s" % (where, ",".join(bad)))

        for ent in lines:
            if isinstance(ent, str):
                ph_scan(ent, "line-style template")
                continue
            if not isinstance(ent, dict) or not isinstance(
                    ent.get("variants"), list) or not ent["variants"]:
                raise UsageError("variants slot-style template malformed (need"
                                 " {slot, variants}): %s" % path)
            has_else = False
            for v in ent["variants"]:
                if not isinstance(v, dict) or not isinstance(v.get("line"), str):
                    raise UsageError("variant malformed (need {when, line,"
                                     " evidence}): %s" % path)
                ph_scan(v["line"], "variants entry")
                ev = v.get("evidence")
                if not isinstance(ev, list) or not ev:
                    raise UsageError("variant missing its evidence citation"
                                     " (evidence required before issuance): %s"
                                     % path)
                when = v.get("when")
                if when == "else":
                    has_else = True
                elif isinstance(when, dict) and when:
                    badk = [k for k in when if k not in known
                            or not isinstance(when[k], bool)]
                    if badk:
                        raise UsageError("when key outside the allowlist or not"
                                         " boolean: %s" % ",".join(sorted(badk)))
                else:
                    raise UsageError("when must be 'else' or a non-empty bool dict: %s" % path)
            if not has_else:
                raise UsageError("variants has no else fallback (rendering must"
                                 " decide for every state): %s" % path)
        return {"desc": pre.get("desc", ""), "lines": lines}

    def render_preset_header(self, path, text):
        """Preset render (wash 3, placeholder substitution): template rows get
        their placeholders replaced one by one, then over-wide lines wrap
        greedily (wrap_long_line).  Every placeholder value comes from the
        target file itself: {name} = basename minus .v, {deps_stdlib}/
        {deps_dev} = the require_faces two columns, {bundle}/{summary}/
        {mission} = header_carry verbatim, never synthesized.  Any unbound
        placeholder -> (None, missing list) (the judge records plan-miss
        honestly).  Cache key = (abspath, text md5) (re-judged per loop round;
        same file same text stays identical, a changed file re-renders)."""
        key = (os.path.abspath(path), hashlib.md5(
            text.encode("utf-8", "replace")).hexdigest())
        if key in self._preset_render_cache:
            return self._preset_render_cache[key]
        base = os.path.basename(path)
        stdlib, dev = require_faces(text)
        carry = header_carry(text)
        vals = {"name": base[:-2] if base.endswith(".v") else base,
                "deps_stdlib": ", ".join("[%s]" % n for n in stdlib),
                "deps_dev": ", ".join("[%s]" % n for n in dev),
                "bundle": carry.get("bundle"),
                "summary": carry.get("summary"),
                "mission": carry.get("mission")}
        missing = sorted(k for k, v in vals.items() if v is None)
        out_rows = []
        if not missing:
            for ent in self.header_preset["lines"]:
                if isinstance(ent, str):
                    rows = [ent]
                else:
                    chosen = None
                    for v in ent["variants"]:
                        when = v["when"]
                        if when == "else" or all(
                                bool(vals[k]) == w for k, w in when.items()):
                            chosen = v["line"]
                            break
                    rows = [chosen]  # else fallback verified at load; chosen is never None
                for row in rows:
                    filled = PH_RE.sub(lambda m: vals[m.group(1)], row)
                    for phys in filled.split("\n"):
                        if phys.startswith("    "):
                            # wrap only field-body lines (4-space indent): the
                            # L1 bundle line and the title line stay single-line
                            # across the whole corpus (DecBridge6.v:1 103 cols /
                            # :3 96 cols; abl_tail_supply_66.v:1 95 cols).
                            out_rows.extend(wrap_long_line(phys))
                        else:
                            out_rows.append(phys)
            rendered = "\n".join(out_rows) + "\n"
        self._preset_render_cache[key] = \
            (rendered, None) if not missing else (None, missing)
        return self._preset_render_cache[key]

    def header_map_entry(self, basename):
        """Map lookup (basename tried with and without .v; same form as
        comment_sweep.run).  Map source only (--header-map/env); the preset
        source goes through render_preset_header."""
        if not self.header_map:
            return None
        keys = [basename, basename[:-2]] if basename.endswith(".v") \
            else [basename]
        for k in keys:
            if k in self.header_map:
                return self.header_map[k]
        return None

    def _load_frozen_roster(self):
        """certify/frozen8.py --ledger -> (abs set, rel set, source note).
        --ledger only prints the ledger-loaded constants (offline, no disk
        verification); the injector can replace it.  Line form
        "md5<whitespace>relpath"; absolute-path lines collect as abs; relative
        lines resolve against repo_root."""
        rc, out, _rep, canned = self.run_engine(
            "frozen8", self.tool_frozen8, ["--ledger"])
        if rc != 0:
            raise UsageError("frozen8 --ledger out-of-shape exit rc=%d: %s"
                             % (rc, tail_of(out)))
        abs_set, rel_set = set(), set()
        for ln in out.splitlines():
            parts = ln.split()
            if len(parts) < 2:
                continue
            rel = parts[1]
            if os.path.isabs(rel):
                abs_set.add(os.path.normpath(rel))
            else:
                rel_set.add(os.path.normpath(rel))
                abs_set.add(os.path.normpath(
                    os.path.join(self.repo_root, rel)))
        src = "injector-canned" if canned else "certify/frozen8.py --ledger"
        return abs_set, rel_set, src

    def is_frozen(self, path):
        ap = os.path.abspath(path)
        if ap in self.frozen_abs:
            return True
        try:
            rel = os.path.relpath(ap, self.repo_root)
        except ValueError:
            return False
        return rel in self.frozen_rel

    def is_forbidden(self, path):
        """Non-negotiable frozen surfaces: the frozen-eight roster plus the frozen ledger."""
        return self.is_frozen(path) or \
            os.path.basename(path) == LEDGER_NAME

    # ---- engine call layer (injection point) ----

    def run_engine(self, key, tool_abs, cli, want_json=False):
        """Subprocess call layer: an injector key hit returns the canned
        response constantly; otherwise a real subprocess [sys.executable, -B,
        tool] + cli runs (stdout+stderr merged; the pushci _run_py form).
        want_json appends --json tmp, parses, then deletes it.  Returns
        (rc, stdout, report|None, canned_flag)."""
        canned = self.injector.canned(key) if self.injector else None
        if canned is not None:
            rep = canned.get("report")
            return (int(canned.get("rc", 0)), str(canned.get("stdout", "")),
                    rep, True)
        if not os.path.isfile(tool_abs):
            raise MissingInput("engine file missing: %s" % tool_abs)
        full_cli = list(cli)
        tmp = None
        if want_json:
            fd, tmp = tempfile.mkstemp(prefix="wash_shape_eng_")
            os.close(fd)
            full_cli = full_cli + ["--json", tmp]
        try:
            p = subprocess.run([sys.executable, "-B", tool_abs] + full_cli,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
            out = p.stdout.decode("utf-8", "replace") \
                if isinstance(p.stdout, bytes) else (p.stdout or "")
            rep = None
            if want_json and tmp and os.path.isfile(tmp) and \
                    os.path.getsize(tmp) > 0:
                try:
                    with io.open(tmp, "r", encoding="utf-8") as fh:
                        rep = json.load(fh)
                except Exception:
                    rep = None
            return p.returncode, out, rep, False
        finally:
            if tmp:
                try:
                    os.unlink(tmp)
                except OSError:
                    pass

    # ---- file collection ----

    def collect_files(self):
        """--file explicit (existence 9; frozen-surface rejection 2) plus --dir
        whole-tree (.v excluding _-prefixed, the two registry names, hidden
        dirs skipped; frozen surfaces and --exclude auto-excluded).  When the
        selection names wash 6/7, the engine-body prose faces (.py/.sh/.md,
        plus .json/.ts for wash 7) join the --dir collection; the selection
        keeps the legacy .v-only collection byte-identical when 6/7 are not
        named.  Dedup by abspath; order by constructed path string
        (deterministic).  Returns (files, excluded records)."""
        args = self.args
        files, seen = [], set()
        excluded = []
        batch_exts = set()
        if KIND_JARGON in self.kinds:
            batch_exts.update(JARGON_FACES)
        if KIND_AIFLAVOR in self.kinds:
            batch_exts.update(AIFLAVOR_FACES)

        def add(path):
            ap = os.path.abspath(path)
            if ap in seen:
                return
            seen.add(ap)
            files.append(path)

        for p in (args.file or []):
            if not os.path.exists(p):
                raise MissingInput("--file missing: %s" % p)
            if self.is_forbidden(p):
                raise UsageError("FATAL frozen-surface rejection: %s (on the "
                                 "certify/frozen8.py roster or the frozen ledger;"
                                 " non-negotiable constraint — the shaper refuses)"
                                 % p)
            add(p)
        for d in (args.dir or []):
            if not os.path.isdir(d):
                raise MissingInput("--dir missing: %s" % d)
            for root, dirs, names in os.walk(d):
                dirs[:] = sorted(x for x in dirs
                                 if not x.startswith("."))
                for n in sorted(names):
                    p = os.path.join(root, n)
                    if self.is_forbidden(p):
                        excluded.append({"path": p, "reason": "frozen8-roster"
                                         if self.is_frozen(p) else "更新账"})
                        continue
                    if self.user_excluded(p):
                        excluded.append({"path": p, "reason": "--exclude"})
                        continue
                    if n.endswith(".v"):
                        if n.startswith("_"):
                            excluded.append({"path": p,
                                             "reason": "underscore-guard"})
                            continue
                        add(p)
                    elif n in REGISTRY_KINDS:
                        add(p)
                    elif batch_exts and \
                            os.path.splitext(n)[1].lower() in batch_exts:
                        add(p)
        files = sorted(files, key=lambda x: os.path.abspath(x))
        return files, excluded

    def user_excluded(self, path):
        base = os.path.basename(path)
        for name in self.excludes:
            if not name:
                continue
            if name == base or name in path.split(os.sep):
                return True
        return False

    # ---- per-wash judging (plan; zero writes) ----

    def gate4_report(self, path):
        """gate4 single-file report (rc 0/1/2 normal; out-of-shape / malformed JSON -> engine failure exit 2)."""
        rc, out, rep, _c = self.run_engine("gate4", self.tool_gate4,
                                           ["--file", path], want_json=True)
        if rc not in (0, 1, 2):
            raise UsageError("gate4 out-of-shape exit rc=%d: %s" % (rc, tail_of(out)))
        if not isinstance(rep, dict) or not rep.get("results"):
            raise UsageError("gate4 JSON report missing/malformed: %s" % tail_of(out))
        return rep["results"][0]

    def judge_lexical(self, path, g4):
        """Wash 1 lexical: gate4 hard word-face items plus review dual-sense items -> flag_words rewrite lookup."""
        hard = g4.get("hard") or []
        review = g4.get("review") or []
        verdict = g4.get("verdict", "?")
        if verdict == "UNREADABLE":
            return self._w(KIND_LEXICAL, STATUS_PLAN_MISS,
                           "gate4 UNREADABLE (face unreadable; nothing applicable)")
        lex = [it for it in hard if it[2] not in HEADER_ITEM_TYPES]
        dual = [it for it in review if it[2] == REVIEW_DUAL]
        manual = len(review) - len(dual)
        fixable, unfix = [], []
        for it in lex:
            w = it[3]
            tag = it[2]
            if w in self.flag_words:
                fixable.append("%s:%s→%s" % (tag, w, self.flag_words[w]))
            else:
                unfix.append("%s:%s" % (tag, w))
        for it in dual:
            w = it[3].split("（", 1)[0]  # fullwidth paren = gate4 review-text format (interface, kept)
            if w in self.flag_words:
                fixable.append("dual:%s->%s" % (w, self.flag_words[w]))
            else:
                unfix.append("dual:%s (no rewrite entry)" % w)
        detail = ("gate4=%s hard=%d(lexical=%d) review=%d(dual=%d manual=%d)"
                  " fixable=%d unfixable=%d" % (verdict, len(hard), len(lex),
                                                len(review), len(dual), manual,
                                                len(fixable), len(unfix)))
        if fixable:
            detail += " fixable[" + ";".join(fixable[:8]) + "]"
        if unfix:
            detail += " unfixable[" + ";".join(unfix[:8]) + "]"
        status = (STATUS_WOULD_FIX if fixable
                  else (STATUS_PLAN_MISS if unfix else STATUS_CLEAN))
        return self._w(KIND_LEXICAL, status, detail,
                       n_fix=len(fixable), n_miss=len(unfix))

    def judge_token(self, path):
        """Wash 2 token: scan_v4 survey -> cure_applier canonical-pack dry run."""
        rc, out, cen, _c = self.run_engine("scan_v4", self.tool_scan4,
                                           ["--file", path], want_json=True)
        if rc != 0:
            raise UsageError("scan_v4 out-of-shape exit rc=%d: %s" % (rc, tail_of(out)))
        if not isinstance(cen, dict):
            raise UsageError("scan_v4 census JSON missing/malformed: %s"
                             % tail_of(out))
        n = int(cen.get("station_count", 0) or 0)
        if n == 0:
            return self._w(KIND_TOKEN, STATUS_CLEAN,
                           "census stations=0 (tracked=%s)"
                           % ",".join(cen.get("tracked_ids") or []))
        rc2, out2, crep, _c2 = self.run_engine("cure", self.tool_cure,
                                               ["--file", path],
                                               want_json=True)
        if rc2 == 4:
            return self._w(KIND_TOKEN, STATUS_PLAN_MISS,
                           "census stations=%d; canonical-pack exclusive-group"
                           " conflict (both variants matched; the operator must"
                           " pick one via --only): %s" % (n, tail_of(out2, 160)))
        if rc2 != 0:
            raise UsageError("cure_applier dry run out-of-shape exit rc=%d: %s"
                             % (rc2, tail_of(out2)))
        total = sum(int(v.get("matches", 0) or 0)
                    for v in ((crep or {}).get("report") or {}).values())
        if total:
            return self._w(KIND_TOKEN, STATUS_WOULD_FIX,
                           "census stations=%d; canonical-pack dry-run hits=%d" % (n, total),
                           n_fix=total)
        return self._w(KIND_TOKEN, STATUS_PLAN_MISS,
                       "census stations=%d; canonical-pack zero hits (no rewrite entry)" % n,
                       n_miss=n)

    def judge_header(self, path, g4, text):
        """Wash 3 header: gate4 header-domain hard items plus template judging
        (map source = per-file data, alignment and rewrite judged together;
        preset source = designated-template render: rewrites only hard items
        and never aligns an already-conforming five-field header, so a
        human-curated face is never machine-rewritten; no source = plan-miss
        reported honestly)."""
        items = [it for it in (g4.get("hard") or [])
                 if it[2] in HEADER_ITEM_TYPES]
        item_strs = ["%s:%s" % (it[2], it[3]) for it in items]
        miss_ph = None
        if self.header_source == "map":
            mapped = self.header_map_entry(os.path.basename(path))
        elif self.header_source == "preset":
            mapped, miss_ph = self.render_preset_header(path, text)
        else:
            mapped = None
        if mapped is not None:
            if items:
                how = "comment_pack-style template full rewrite" \
                    if self.header_source == "map" else "designated-template full rewrite"
                return self._w(KIND_HEADER, STATUS_WOULD_FIX,
                               "header items=%d[%s]; %s"
                               % (len(items), ";".join(item_strs[:6]), how))
            if self.header_source == "map":
                off = first_code_offset(text)
                cur = text[:off] if off is not None else ""
                if cur != mapped:
                    return self._w(KIND_HEADER, STATUS_WOULD_FIX,
                                   "header shape differs from the map (full-rewrite alignment)")
                return self._w(KIND_HEADER, STATUS_CLEAN,
                               "header already canonical (map text in place)")
            return self._w(KIND_HEADER, STATUS_CLEAN,
                           "no header items (first block, five fields complete; preset never aligns-rewrites)")
        if items:
            if miss_ph:
                return self._w(KIND_HEADER, STATUS_PLAN_MISS,
                               "preset render cannot bind placeholders [%s]"
                               " (file lacks a carried header body); never"
                               " synthesized: [%s]"
                               % (",".join(miss_ph),
                                  ";".join(item_strs[:6])),
                               n_miss=len(items))
            return self._w(KIND_HEADER, STATUS_PLAN_MISS,
                           "no rewrite template (template source=%s not"
                           " configured / no entry); never synthesized: [%s]"
                           % (self.header_source,
                              ";".join(item_strs[:6])),
                           n_miss=len(items))
        return self._w(KIND_HEADER, STATUS_CLEAN,
                       "no header items (first block, five fields complete)")

    def judge_eol(self, path, raw):
        """Wash 4 eol: CRLF->LF normalization (final-newline form preserved)."""
        n = raw.count(b"\r\n")
        lone = raw.count(b"\r") - n
        fin = "present" if raw.endswith(b"\n") else "absent"
        if n == 0:
            detail = "CRLF=0; LF already normalized (final newline=%s)" % fin
            if lone:
                detail += "; lone_CR=%d (not CRLF, left unchanged)" % lone
            return self._w(KIND_EOL, STATUS_CLEAN, detail)
        return self._w(KIND_EOL, STATUS_WOULD_FIX,
                       "CRLF line endings=%d (final-newline form preserved)" % n
                       + ("·lone_CR=%d" % lone if lone else ""),
                       n_fix=n)

    def judge_anchor(self, path, raw):
        """Wash 5 anchor: order.txt line-anchor canonical-form judging (#R<seq>-<md5-8>)."""
        base = os.path.basename(path)
        kind = REGISTRY_KINDS.get(base)
        if kind is None:
            return self._w(KIND_ANCHOR, STATUS_CLEAN,
                           "not a registry file (order.txt/_CoqProject); wash not applicable")
        if kind == "coqproject":
            return self._w(KIND_ANCHOR, STATUS_CLEAN,
                           "coqproject rows carry no anchors (registry_union sense); not applicable")
        anchor_src = self.args.anchor_src or \
            os.path.dirname(os.path.abspath(path))
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as e:
            return self._w(KIND_ANCHOR, STATUS_PLAN_MISS,
                           "registry face not UTF-8: %s" % e, n_miss=1)
        lines = [ln.rstrip("\r\n").strip()
                 for ln in text.split("\n")]
        while lines and lines[-1] == "":
            lines.pop()
        fix_rows, miss_rows = [], []
        modules = []
        for ln in lines:
            if not ln:
                continue
            head = ln.split("#", 1)[0].strip()
            if not head:
                continue  # pure comment line (registry_union key_of=None rule)
            m = ANCHOR_RE.search(ln)
            if m is None:
                miss_rows.append("anchorless row cannot re-anchor (no seq to carry): %s" % ln)
                continue
            anchor = m.group(0)
            seq = anchor[2:].split("-", 1)[0]
            module = head[:-2] if head.endswith(".v") else head
            entity = resolve_entity(module, anchor_src)
            if entity is None:
                miss_rows.append("missing entity (%s has no %s.v): %s"
                                 % (anchor_src, module, ln))
                continue
            if entity.startswith("AMBIGUOUS:"):
                miss_rows.append("ambiguous entity (registry_union refuses to anchor): %s"
                                 % entity[len("AMBIGUOUS:"):])
                continue
            fp = md5_8_of(entity)
            canonical = "#R%s-%s" % (seq, fp)
            if anchor != canonical:
                fix_rows.append("%s: %s→%s" % (module, anchor, canonical))
                if module not in modules:
                    modules.append(module)
        detail = "order anchor check: non-canonical=%d unfixable=%d" % (len(fix_rows),
                                                   len(miss_rows))
        if fix_rows:
            detail += " [" + ";".join(fix_rows[:8]) + "]"
        if miss_rows:
            detail += " unfixable[" + ";".join(miss_rows[:6]) + "]"
        status = (STATUS_WOULD_FIX if fix_rows
                  else (STATUS_PLAN_MISS if miss_rows else STATUS_CLEAN))
        return self._w(KIND_ANCHOR, status, detail,
                       n_fix=len(fix_rows), n_miss=len(miss_rows),
                       modules=modules)

    def judge_jargon(self, path):
        """Wash 6 jargon: jargon_apply --plan (zero writes) over the
        .py/.sh/.md prose faces; machine-applicable occurrences are would-fix,
        guarded and rewrite_or_delete rows are human findings -> plan-miss
        items (the engine never machine-applies them)."""
        if not os.path.isfile(self.tool_jargon):
            raise MissingInput("engine file missing (jargon): %s"
                               % self.tool_jargon)
        rc, out, rep, _c = self.run_engine("jargon", self.tool_jargon,
                                           ["--file", path, "--plan"],
                                           want_json=True)
        if rc not in (0, 1):
            raise UsageError("jargon_apply plan out-of-shape exit rc=%d: %s"
                             % (rc, tail_of(out)))
        if not isinstance(rep, dict) or not isinstance(rep.get("summary"), dict):
            raise UsageError("jargon_apply plan JSON missing/malformed: %s"
                             % tail_of(out))
        summary = rep["summary"]
        n_fix = int(summary.get("would_fix", 0) or 0)
        n_miss = int(summary.get("human", 0) or 0)
        parse_errors = int(summary.get("parse_errors", 0) or 0)
        if parse_errors:
            return self._w(KIND_JARGON, STATUS_PLAN_MISS,
                           "prose-face parse error (%d); the face needs a"
                           " syntax fix before the jargon plan can scan it"
                           % parse_errors, n_miss=parse_errors)
        if n_fix:
            detail = ("machine-applicable=%d human=%d (62-entry seed map)"
                      % (n_fix, n_miss))
            if n_miss:
                detail += "; human rows never machine-applied"
            return self._w(KIND_JARGON, STATUS_WOULD_FIX, detail,
                           n_fix=n_fix, n_miss=n_miss)
        if n_miss:
            return self._w(KIND_JARGON, STATUS_PLAN_MISS,
                           "human findings=%d (guarded or rewrite_or_delete"
                           " rows; per-row handling before any apply)" % n_miss,
                           n_miss=n_miss)
        return self._w(KIND_JARGON, STATUS_CLEAN,
                       "no jargon occurrences on the prose face")

    def judge_aiflavor(self, path):
        """Wash 7 ai-flavor: ai_flavor_apply plan mode (advisory, zero
        writes); provider-eligible suggestions are would-fix with the
        handoff route as their action, ban-remediation faces and em-dash
        occurrences are human items -> plan-miss items."""
        if not os.path.isfile(self.tool_aiflavor_detect):
            raise MissingInput("engine file missing (ai_flavor): %s"
                               % self.tool_aiflavor_detect)
        rc, out, rep, _c = self.run_engine("ai_flavor", self.tool_aiflavor_detect,
                                           ["--file", path],
                                           want_json=True)
        if rc not in (0, 1):
            raise UsageError("ai_flavor_apply plan out-of-shape exit rc=%d: %s"
                             % (rc, tail_of(out)))
        if not isinstance(rep, dict) or "findings_total" not in rep:
            raise UsageError("ai_flavor_apply plan JSON missing/malformed: %s"
                             % tail_of(out))
        n_fix = int(rep.get("findings_provider", 0) or 0)
        n_human = int(rep.get("findings_human", 0) or 0)
        em = int(rep.get("em_dash_count", 0) or 0)
        n_miss = n_human + em
        if n_fix:
            detail = ("provider-eligible=%d human=%d em_dash=%d (advisory;"
                      " writes only through the provider round trip)"
                      % (n_fix, n_human, em))
            if n_miss:
                detail += "; human items never machine-written"
            return self._w(KIND_AIFLAVOR, STATUS_WOULD_FIX, detail,
                           n_fix=n_fix, n_miss=n_miss)
        if n_miss:
            return self._w(KIND_AIFLAVOR, STATUS_PLAN_MISS,
                           "human findings=%d em_dash=%d (ban-remediation"
                           " faces and em-dash are never machine-written)"
                           % (n_human, em), n_miss=n_miss)
        return self._w(KIND_AIFLAVOR, STATUS_CLEAN,
                       "no ai-flavor faces and em-dash zero")

    # ---- plan assembly ----

    def plan_file(self, path):
        """Per-file wash judging (canonical order 1->5; zero writes)."""
        kinds = self.kinds
        try:
            with open(path, "rb") as fh:
                raw = fh.read()
        except OSError as e:
            return {"file": path, "washes": [
                self._w(k, STATUS_PLAN_MISS, "file unreadable: %s" % e, n_miss=1)
                for k in kinds]}
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("utf-8", errors="replace")
        is_v = path.endswith(".v")
        ext = os.path.splitext(path)[1].lower()
        g4 = None
        if is_v and (KIND_LEXICAL in kinds or KIND_HEADER in kinds):
            g4 = self.gate4_report(path)
        washes = []
        if is_v:
            if KIND_LEXICAL in kinds:
                washes.append(self.judge_lexical(path, g4))
            if KIND_TOKEN in kinds:
                washes.append(self.judge_token(path))
            if KIND_HEADER in kinds:
                washes.append(self.judge_header(path, g4, text))
            for k, note in ((KIND_JARGON,
                             "not a tool-repo prose face; jargon wash not"
                             " applicable to .v certification faces"),
                            (KIND_AIFLAVOR,
                             "not a tool-repo prose face; ai-flavor wash not"
                             " applicable to .v certification faces")):
                if k in kinds:
                    washes.append(self._w(k, STATUS_CLEAN, note))
        else:
            for k, note in ((KIND_LEXICAL,
                             "not a .v source; lexical wash not applicable"),
                            (KIND_TOKEN,
                             "not a .v source; token wash not applicable"),
                            (KIND_HEADER,
                             "not a .v source; header wash not applicable")):
                if k in kinds:
                    washes.append(self._w(k, STATUS_CLEAN, note))
            if KIND_JARGON in kinds:
                if ext in JARGON_FACES:
                    washes.append(self.judge_jargon(path))
                else:
                    washes.append(self._w(
                        KIND_JARGON, STATUS_CLEAN,
                        "extension outside .py/.sh/.md; jargon wash not"
                        " applicable"))
            if KIND_AIFLAVOR in kinds:
                if ext in AIFLAVOR_FACES:
                    washes.append(self.judge_aiflavor(path))
                else:
                    washes.append(self._w(
                        KIND_AIFLAVOR, STATUS_CLEAN,
                        "extension outside .py/.sh/.md/.json/.ts; ai-flavor"
                        " wash not applicable"))
        if KIND_EOL in kinds:
            washes.append(self.judge_eol(path, raw))
        if KIND_ANCHOR in kinds:
            washes.append(self.judge_anchor(path, raw))
        return {"file": path, "washes": washes}

    def compute_plan(self):
        """Whole-scope plan (zero writes) -> {"files": [...], "stats": {...}}."""
        entries = [self.plan_file(p) for p in self.files]
        return {"files": entries, "stats": stats_of(entries)}

    # ---- plan cache (--loop cross-round; any source md5 change recomputes) ----

    def plan_scope_md5s(self):
        """Plan-cache invalidation domain {abspath: md5}: scope files
        (--file/--dir collection) plus wash-5 anchor entities (order.txt line
        anchor entities resolved via anchor_src: an entity md5 change is a
        source change).  Entity appearance/disappearance/ambiguation enters the
        domain under a marker key (a domain-set change invalidates); an
        unreadable file records None (its state change triggers recompute;
        fail-soft domain accounting).  Re-measuring this domain per round is a
        cheap md5 pass (zero wash-engine re-runs); a stable domain means a
        cache hit."""
        out = {}
        for p in self.files:
            ap = os.path.abspath(p)
            try:
                out[ap] = md5_of(p)
            except OSError:
                out[ap] = None
        asrc = self.args.anchor_src
        for p in self.files:
            if os.path.basename(p) != "order.txt":
                continue
            try:
                with open(p, "rb") as fh:
                    text = fh.read().decode("utf-8", errors="replace")
            except OSError:
                continue            # unreadable file already recorded None in the scope domain
            anchor_src = asrc or os.path.dirname(os.path.abspath(p))
            for ln in text.split("\n"):
                head = ln.split("#", 1)[0].strip()
                if not head or ANCHOR_RE.search(ln) is None:
                    continue
                module = head[:-2] if head.endswith(".v") else head
                ent = resolve_entity(module, anchor_src)
                if ent is None:
                    out["<missing:%s>" % module] = None
                elif ent.startswith("AMBIGUOUS:"):
                    out[ent] = ent  # the ambiguity string itself enters the domain (set change = domain change)
                else:
                    ap = os.path.abspath(ent)
                    try:
                        out[ap] = md5_of(ent)
                    except OSError:
                        out[ap] = None
        return out

    def plan_cached(self):
        """Cross-round plan cache (--loop watch mode): a stable invalidation
        domain (plan_scope_md5s) reuses the previous plan (cache hit; zero
        wash-engine re-runs); any source md5 change invalidates, recomputes and
        refreshes the domain (source md5 change -> plan recompute; fixed
        semantics).  The first round always recomputes (cache empty).
        Returns (plan, hit)."""
        cur = self.plan_scope_md5s()
        if self._plan_cache is not None and cur == self._plan_md5s:
            return self._plan_cache, True
        plan = self.compute_plan()
        self._plan_cache = plan
        self._plan_md5s = cur
        return plan, False

    # ---- per-wash apply (phase two of the two-phase form) ----

    def apply_lexical(self, path):
        rc, out, rep, canned = self.run_engine(
            "sweep", self.tool_sweep, ["--file", path, "--apply"],
            want_json=True)
        if rc != 0:
            raise UsageError("comment_sweep --apply engine failure rc=%d: %s"
                             % (rc, tail_of(out)))
        r = (rep or {}).get("report") or {}
        return {"file": path, "kind": KIND_LEXICAL,
                "engine": "wash/comment_sweep.py", "rc": 0,
                "detail": "flag_swaps=%d%s" % (int(r.get("flag_swaps", 0) or 0),
                                               " (injector canned)" if canned
                                               else "")}

    def apply_token(self, path):
        rc, out, rep, canned = self.run_engine(
            "cure", self.tool_cure, ["--file", path, "--apply"],
            want_json=True)
        if rc != 0:
            raise UsageError("cure_applier --apply engine failure rc=%d"
                             " (nothing written; built-in second-pass zero-residue"
                             " assertion): %s" % (rc, tail_of(out)))
        hits = sum(int(v.get("matches", 0) or 0)
                   for v in ((rep or {}).get("report") or {}).values())
        return {"file": path, "kind": KIND_TOKEN,
                "engine": "wash/cure_applier.py", "rc": 0,
                "detail": "pattern_hits=%d%s" % (hits,
                                                 " (injector canned)" if canned
                                                 else "")}

    def apply_jargon(self, path):
        """Wash 6 apply: jargon_apply --apply (the engine splices the mapped
        standards and re-runs its own detector; residue zero is its
        exit-zero gate, rc 1 = verification red which the shaper's rescan
        then reports as residual items)."""
        rc, out, rep, canned = self.run_engine(
            "jargon", self.tool_jargon, ["--file", path, "--apply"],
            want_json=True)
        if rc not in (0, 1):
            raise UsageError("jargon_apply --apply engine failure rc=%d: %s"
                             % (rc, tail_of(out)))
        r = (rep or {}).get("summary") or {}
        residue = int(r.get("residue_jargon", 0) or 0)
        if rc == 1 or residue:
            raise UsageError("jargon_apply --apply verification red"
                             " (residue=%d; nothing further staged): %s"
                             % (residue, tail_of(out)))
        return {"file": path, "kind": KIND_JARGON,
                "engine": "tools/jargon_apply.py", "rc": 0,
                "detail": "applied=%d residue=0%s"
                          % (int(r.get("applied", 0) or 0),
                             " (injector canned)" if canned else "")}

    def apply_aiflavor(self, path):
        """Wash 7 apply: ai_flavor_apply --emit-handoff only.  The provider
        round trip (fill rows, --apply-handoff) is the write face and lives
        outside this pass, so the emitted package is named in the detail and
        the rescan keeps reporting the residual suggestions loudly."""
        base = os.path.basename(path)
        out_path = base + ".ai-flavor-handoff.jsonl"
        rc, out, rep, canned = self.run_engine(
            "ai_flavor", self.tool_aiflavor_detect,
            ["--file", path, "--emit-handoff", out_path],
            want_json=True)
        if rc not in (0, 1):
            raise UsageError("ai_flavor_apply --emit-handoff engine failure"
                             " rc=%d: %s" % (rc, tail_of(out)))
        rows = int((rep or {}).get("handoff_rows", 0) or 0)
        return {"file": path, "kind": KIND_AIFLAVOR,
                "engine": "tools/ai_flavor_apply.py", "rc": 0,
                "detail": "handoff package=%s rows=%d (fill the rows and run"
                          " --apply-handoff to complete the provider round"
                          " trip)%s"
                          % (out_path, rows,
                             " (injector canned)" if canned else "")}

    def apply_header(self, path):
        """Wash 3 apply: comment_sweep --header-map <concrete map> --apply (the
        engine is always comment_sweep; orchestration adds no new engine).  Map
        source = the explicit/env path; preset source = the freshly rendered
        single-file map written to a temp file ({basename: rendered text},
        deleted after use; rendered values come from the file's own data;
        orchestration persists nothing).  Unbindable placeholders (the file
        drifted after plan) -> engine failure rc 2 fail-loud."""
        tmp = None
        try:
            if self.header_source == "preset":
                with open(path, "rb") as fh:
                    text = fh.read().decode("utf-8")
                rendered, miss_ph = self.render_preset_header(path, text)
                if rendered is None:
                    raise UsageError(
                        "preset render cannot bind placeholders [%s] (file"
                        " drifted after plan): %s"
                        % (",".join(miss_ph), path))
                fd, tmp = tempfile.mkstemp(prefix="wash_shape_hmap_")
                with os.fdopen(fd, "w", encoding="utf-8") as fh:
                    json.dump({os.path.basename(path): rendered}, fh,
                              ensure_ascii=False, sort_keys=True)
                map_path = tmp
            else:
                map_path = self.header_map_path
            rc, out, rep, canned = self.run_engine(
                "sweep", self.tool_sweep,
                ["--file", path, "--header-map", map_path, "--apply"],
                want_json=True)
        finally:
            if tmp:
                try:
                    os.unlink(tmp)
                except OSError:
                    pass
        if rc != 0:
            raise UsageError("comment_sweep --header-map --apply engine failure"
                             " rc=%d: %s" % (rc, tail_of(out)))
        r = (rep or {}).get("report") or {}
        return {"file": path, "kind": KIND_HEADER,
                "engine": "wash/comment_sweep.py", "rc": 0,
                "detail": "header_replaced=%s flag_swaps=%d%s"
                          % (r.get("header_replaced"),
                             int(r.get("flag_swaps", 0) or 0),
                             " (injector canned)" if canned else "")}

    def apply_eol(self, path, raw):
        n = raw.count(b"\r\n")
        if n == 0:
            return {"file": path, "kind": KIND_EOL, "engine": "wash_shape",
                    "rc": 0,
                    "detail": "crlf_converted=0 changed=False (an earlier"
                              " engine write-back already normalized; reported"
                              " as observed)"}
        with open(path, "wb") as fh:
            fh.write(raw.replace(b"\r\n", b"\n"))
        return {"file": path, "kind": KIND_EOL, "engine": "wash_shape",
                "rc": 0, "detail": "crlf_converted=%d changed=True (final-newline"
                                   " form preserved)" % n}

    def apply_anchor(self, path, modules):
        anchor_src = self.args.anchor_src or \
            os.path.dirname(os.path.abspath(path))
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(path)),
                                   prefix=".wash_shape_reanchor_")
        os.close(fd)
        try:
            rc, out, rep, canned = self.run_engine(
                "registry_union", self.tool_regu,
                ["--base", path, "--main", path, "--branch", path,
                 "--kind", "order", "--reanchor", ",".join(modules),
                 "--anchor-src", anchor_src, "--out", tmp, "--apply"],
                want_json=True)
            if rc != 0:
                raise UsageError("registry_union --reanchor engine failure"
                                 " rc=%d (zero writes): %s" % (rc, tail_of(out)))
            rewrites = ((rep or {}).get("reanchor") or {}).get("rewrites") or []
            if canned:
                return {"file": path, "kind": KIND_ANCHOR,
                        "engine": "tools/registry_union.py", "rc": 0,
                        "detail": "rewrites=%d (injector canned; not moved"
                                  " into place)" % len(rewrites)}
            os.replace(tmp, path)
            tmp = None
            return {"file": path, "kind": KIND_ANCHOR,
                    "engine": "tools/registry_union.py", "rc": 0,
                    "detail": "rewrites=%d modules=%s"
                              % (len(rewrites), ",".join(modules))}
        finally:
            if tmp and os.path.exists(tmp):
                try:
                    os.unlink(tmp)
                except OSError:
                    pass

    def apply_one(self, path, wash):
        """Apply one wash (dispatched on the plan verdict; canonical order guaranteed by the caller)."""
        kind = wash["kind"]
        if kind == KIND_LEXICAL:
            return self.apply_lexical(path)
        if kind == KIND_TOKEN:
            return self.apply_token(path)
        if kind == KIND_HEADER:
            return self.apply_header(path)
        if kind == KIND_EOL:
            with open(path, "rb") as fh:
                return self.apply_eol(path, fh.read())
        if kind == KIND_ANCHOR:
            return self.apply_anchor(path, wash.get("_modules") or [])
        if kind == KIND_JARGON:
            return self.apply_jargon(path)
        if kind == KIND_AIFLAVOR:
            return self.apply_aiflavor(path)
        raise UsageError("unknown wash kind: %s" % kind)

    # ---- verdict and report ----

    def verdict_of(self, entries, n_applied, apply_mode):
        """verdict: any item-level miss (wash-level plan-miss or _n_miss>0) ->
        plan-miss; otherwise any would-fix -> partial; apply mode with applied
        items -> shaped; otherwise clean."""
        miss = any(w["status"] == STATUS_PLAN_MISS or w.get("_n_miss", 0) > 0
                   for f in entries for w in f["washes"])
        pend = any(w["status"] == STATUS_WOULD_FIX
                   for f in entries for w in f["washes"])
        if miss:
            return VERDICT_PLAN_MISS
        if pend:
            return VERDICT_PARTIAL
        if apply_mode and n_applied:
            return VERDICT_SHAPED
        return VERDICT_CLEAN

    def report_of(self, plan, applied, rescan, verdict, excluded,
                  cache_hit=None):
        rep = {
            "schema": SCHEMA,
            "mode": "loop" if self.args.loop else
                    ("apply" if self.args.apply else "plan"),
            "scope": {"only": list(self.kinds),
                      "header_map": {"source": self.header_source,
                                     "path": self.header_map_path,
                                     "preset": self.header_preset_name,
                                     "library": self.header_library_path},
                      "frozen_roster_source": self.frozen_source,
                      "excluded": sorted(excluded,
                                         key=lambda x: (x["path"],
                                                        x["reason"]))},
            "verdict": verdict,
        }
        if cache_hit is not None:   # --loop cross-round plan cache (loud accounting)
            rep["plan_cache"] = {"hit": bool(cache_hit)}
        if self.args.apply:
            rep["apply"] = {"applied": applied,
                            "rescan": project_plan(rescan) if rescan else None}
        rep["plan"] = project_plan(plan)
        return rep

    def dump_report(self, path, rep):
        """Deterministic JSON write (sort_keys + indent=1; the
        registry_union.dump_json rule; atomic write)."""
        d = os.path.dirname(os.path.abspath(path))
        if not os.path.isdir(d):
            raise MissingInput("--json output directory missing: %s" % path)
        fd, tmp = tempfile.mkstemp(dir=d, prefix=".wash_shape_json_")
        os.close(fd)   # the open handle blocks os.replace on Windows (report fd face)
        try:
            with io.open(tmp, "w", encoding="utf-8", newline="\n") as fh:
                json.dump(rep, fh, indent=1, ensure_ascii=False,
                          sort_keys=True)
            os.replace(tmp, path)
        except Exception:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise

    # ---- main flow ----

    def one_pass(self, round_no=None):
        """One complete pass: plan (--loop uses the cross-round cache; a stable
        source-md5 domain hits the cache, any change recomputes; --once computes
        directly without the cache) -> (--apply? apply, then re-run all
        washes; rescan always computes fresh, never reuses the cache) ->
        (verdict, report, n_applied)."""
        if self.args.loop:
            plan, cache_hit = self.plan_cached()
        else:
            plan, cache_hit = self.compute_plan(), None
        applied = []
        rescan = None
        if self.args.apply:
            for fentry in plan["files"]:
                for w in fentry["washes"]:
                    if w["status"] == STATUS_WOULD_FIX:
                        applied.append(self.apply_one(fentry["file"], w))
            rescan = self.compute_plan()
            current = rescan
        else:
            current = plan
        verdict = self.verdict_of(current["files"], len(applied),
                                  self.args.apply)
        report = self.report_of(plan, applied, rescan, verdict,
                                self.excluded_records, cache_hit=cache_hit)
        return verdict, report, len(applied)

    def run_once(self):
        verdict, report, n_applied = self.one_pass()
        if self.args.jsonout:
            self.dump_report(self.args.jsonout, report)
        self.print_summary(report, verdict, n_applied)
        return exit_code_of(verdict)

    def _emit_event(self, ev):
        """Event emission (stdout mirror + --events append; sort_keys canonical
        one-line JSON; per-line flush+fsync, the cw_sentinel.emit_event rule).
        Write failure -> 9."""
        line = json.dumps(ev, ensure_ascii=False, sort_keys=True)
        print(line)
        sys.stdout.flush()
        if self.args.events:
            try:
                with io.open(self.args.events, "a", encoding="utf-8",
                             newline="\n") as fh:
                    fh.write(line + "\n")
                    fh.flush()
                    os.fsync(fh.fileno())
            except OSError as e:
                raise MissingInput("--events write failed: %s (%s)"
                                   % (self.args.events, e))

    def run_loop(self):
        """Watch mode: one_pass per round (cross-round plan cache; any source
        md5 change recomputes); the JSONL event stream keeps the same shape
        (rocqwash-sentinel-event/1; schema/seq/kind; sort_keys canonical form;
        seq continues across processes from the existing --events line count;
        ts drops when --sleep-scale 0); --events appends; --max-rounds bounds
        the run (0 = unbounded; a stop event is emitted at the cap)."""
        ts_enabled = self.args.sleep_scale != 0
        if self.args.events and os.path.isfile(self.args.events):
            self._seq = events_seq_base(self.args.events) + 1
        rnd = 0
        last_rc = 0
        while True:
            rnd += 1
            verdict, report, n_applied = self.one_pass(round_no=rnd)
            if self.args.jsonout:
                self.dump_report(self.args.jsonout, report)
            stats = (report.get("apply") or {}).get("rescan", {}) \
                if self.args.apply else report["plan"]
            st = stats.get("stats", {})
            event = make_event(self._seq, "round", {
                "round": rnd, "mode": "loop",
                "apply": bool(self.args.apply), "verdict": verdict,
                "files": st.get("files", 0),
                "n_would_fix": st.get("would_fix", 0),
                "n_plan_miss": st.get("plan_miss", 0),
                "n_plan_miss_items": st.get("plan_miss_items", 0),
                "n_applied": n_applied,
                "plan_cache_hit": bool(
                    (report.get("plan_cache") or {}).get("hit", False))},
                ts_enabled)
            self._seq += 1
            self._emit_event(event)
            last_rc = exit_code_of(verdict)
            if self.args.max_rounds and rnd >= self.args.max_rounds:
                stop = make_event(self._seq, "stop", {
                    "round": rnd, "reason": "max-rounds",
                    "verdict": verdict}, ts_enabled)
                self._seq += 1
                self._emit_event(stop)
                break
            sleep_scaled(self.args.interval, self.args.sleep_scale)
        return last_rc

    def print_summary(self, report, verdict, n_applied):
        plan = report["plan"]
        st = plan["stats"]
        head = "== WASH-SHAPE verdict=%s files=%d would_fix=%d clean=%d " \
               "plan_miss=%d(plan_miss_items=%d)" % (
                   verdict, st["files"], st["would_fix"], st["clean"],
                   st["plan_miss"], st["plan_miss_items"])
        if self.args.apply:
            head += " applied=%d" % n_applied
        head += " =="
        print(head)
        for f in plan["files"]:
            for w in f["washes"]:
                if w["status"] != STATUS_CLEAN:
                    print("  %s %s %s %s" % (w["status"].upper(),
                                             f["file"], w["kind"],
                                             w["detail"]))
        if self.args.apply and report.get("apply"):
            rs = report["apply"]["rescan"]
            rst = rs["stats"]
            print("RESCAN: would_fix=%d plan_miss=%d(plan_miss_items=%d)"
                  % (rst["would_fix"], rst["plan_miss"],
                     rst["plan_miss_items"]))
            for f in rs["files"]:
                for w in f["washes"]:
                    if w["status"] != STATUS_CLEAN:
                        print("  residual %s %s %s %s" % (w["status"].upper(),
                                                      f["file"], w["kind"],
                                                      w["detail"]))
        for e in report["scope"]["excluded"]:
            print("  EXCLUDED %s (%s)" % (e["path"], e["reason"]))

    # ---- internals ----

    def _w(self, kind, status, detail, n_fix=0, n_miss=0, modules=None):
        """Wash entry: the four schema-surface keys (kind/action/status/detail)
        plus internal stat keys (`_`-prefixed; stripped by the on-disk
        projection)."""
        action = "none"
        if status == STATUS_WOULD_FIX:
            action = {KIND_LEXICAL: ACTION_SWEEP,
                      KIND_TOKEN: ACTION_CURE,
                      KIND_HEADER: (ACTION_SWEEP_MAP
                                    if self.header_source == "map" else
                                    (ACTION_SWEEP_MAP_PRESET
                                     if self.header_source == "preset"
                                     else "none")),
                      KIND_EOL: ACTION_EOL,
                      KIND_ANCHOR: ACTION_REGU,
                      KIND_JARGON: ACTION_JARGON,
                      KIND_AIFLAVOR: ACTION_AIFLAVOR}.get(kind, "none")
        ent = {"kind": kind, "action": action, "status": status,
               "detail": detail, "_n_fix": n_fix, "_n_miss": n_miss}
        if modules is not None:
            ent["_modules"] = modules
        return ent


def project_entry(ent):
    """Wash entry -> the four schema-surface keys (`_`-prefixed internal keys stripped)."""
    return {"kind": ent["kind"], "action": ent["action"],
            "status": ent["status"], "detail": ent["detail"]}


def project_plan(plan):
    files = [{"file": f["file"],
              "washes": [project_entry(w) for w in f["washes"]]}
             for f in plan["files"]]
    return {"files": files, "stats": plan["stats"]}


def stats_of(entries):
    """Plan stats: files/wash_entries/would_fix/clean/plan_miss (wash level) /
    plan_miss_items (item level)."""
    st = {"files": len(entries), "wash_entries": 0, "would_fix": 0,
          "clean": 0, "plan_miss": 0, "plan_miss_items": 0,
          "would_fix_items": 0}
    for f in entries:
        for w in f["washes"]:
            st["wash_entries"] += 1
            st["plan_miss_items"] += w.get("_n_miss", 0)
            st["would_fix_items"] += w.get("_n_fix", 0)
            if w["status"] == STATUS_WOULD_FIX:
                st["would_fix"] += 1
            elif w["status"] == STATUS_CLEAN:
                st["clean"] += 1
            elif w["status"] == STATUS_PLAN_MISS:
                st["plan_miss"] += 1
    return st


def exit_code_of(verdict):
    """Exit-code rule: 0 = clean/shaped; 1 = partial/plan-miss."""
    return 0 if verdict in (VERDICT_CLEAN, VERDICT_SHAPED) else 1


def parse_only(spec):
    """--only parsing: comma/space split; both the numbers 1-7 and kind names
    are accepted; an unknown token is a usage failure; the returned list keeps
    canonical order."""
    if not spec:
        return list(KINDS)
    got = set()
    for tok in re.split(r"[,\s]+", spec.strip()):
        if not tok:
            continue
        k = KIND_ALIASES.get(tok)
        if k is None:
            raise UsageError("unknown --only item (need %s or 1-7): %s"
                             % (",".join(KINDS), tok))
        got.add(k)
    if not got:
        raise UsageError("--only list empty: %r" % spec)
    return [k for k in KINDS if k in got]


# ---------- selftest ----------

def selftest():
    """Frozen selftest vectors (tmp fixtures; zero real network, zero real
    compiles; real engines driven offline):

    v1   per-wash plan verdicts on the dirty file (lexical would-fix /
         token clean / header clean / eol would-fix / anchor not
         applicable) -> partial rc1
    v2   clean-file control, all clean -> clean rc0
    v3   plan writes nothing; --apply defaults off (md5 unchanged)
    v4   plan-miss honesty (an unrewritable word-face file -> plan-miss;
         a mixed file -> would-fix the fixable and plan-miss the unfixable)
    v5   apply -> rescan clean -> shaped rc0 (word-face exchange / CRLF
         normalization / anchor canonical md5_8 verified)
    v6   idempotence (second plan all clean -> clean rc0; re-apply applies 0)
    v7   anchor missing entity -> plan-miss
    v8   frozen-roster exclusion (injector-canned roster: --dir auto-excludes
         plus explicit --file hard rejection rc2; the real frozen8 --ledger
         eight files and a real rostered file also hard-reject)
    v9   subprocess-layer injection (canned gate4 verdict face)
    v10  CLI four codes (help 0 / bogus 2 / no-input 2 / missing 9)
    v11  --once/--loop modes (loop --max-rounds 2: two round events + stop)
    v12  determinism (plan --json reruns are byte-identical)
    v13  preset chain (--header-map-preset loads; conforming files untouched
         rc0; probe order: preset beats env, --header-map beats env;
         env ROCWASH_HEADER_MAP tested both ways)
    v14  preset placeholder render -> apply end to end (missing-field file
         renders a full rewrite -> rescan clean -> shaped rc0 -> rerun
         idempotent clean; rendered text asserted name by name [name / both
         deps columns / bundle / build command / Axioms exemption face])
    v15  same-slot exclusivity (--header-map + --header-map-preset rc2;
         unknown preset name rc2)
    v16  no-source plan-miss honesty (no flag and no env -> missing-field
         file header plan-miss) + missing template library rc9 (isolated
         --repo-root with seven engine symlinks)
    v17  --loop event-stream shape (rocqwash-sentinel-event/1; --events lines
         sort_keys canonical; seq continues across processes without reuse;
         kinds round/stop; ts=off note)
    v18  plan-cache invalidation (a scope-file md5 change -> recompute miss /
         stable -> hit reuse [F,F,T]; a wash-5 anchor-entity md5 change is
         also a source change [F,F,F,T]; a domain missing its entity would
         be a false hit)
    """
    import tempfile

    def run(args, env=None):
        p = subprocess.run([sys.executable, "-B",
                            os.path.join(os.path.dirname(
                                os.path.abspath(__file__)),
                                PROG + ".py")] + args,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           env=env)
        out = p.stdout.decode("utf-8", "replace") \
            if isinstance(p.stdout, bytes) else (p.stdout or "")
        return p.returncode, out

    def wf(path, text, newline="\n"):
        # fixture writer pins newline to "\n" so fixture bytes are identical on
        # every platform; the previous default (None) let Windows text mode turn
        # the LF-only fixtures into CRLF, which shifted the eol wash verdicts
        # and made the selftest red off-macOS (the T0-5 platform-defect family).
        with io.open(path, "w", encoding="utf-8", newline=newline) as fh:
            fh.write(text)
        return path

    ok = True
    tmp = tempfile.mkdtemp(prefix="rocqwash_wash_shape_self_")
    try:
        src = os.path.join(tmp, "src")
        os.makedirs(src)
        asrc = os.path.join(tmp, "asrc")
        os.makedirs(asrc)
        src_miss = os.path.join(tmp, "src_miss")
        os.makedirs(src_miss)
        # fixture .v header: Chinese field labels are the gate4 check input
        # (interface data consumed by the frozen engine), kept verbatim.
        header = ("(* 使命：洗形器自测夹具。\n"
                  "   依赖：无。\n"
                  "   对标：无。\n"
                  "   构造性：全闭合。\n"
                  "   编译配方：rocq c -Q . \"\" fixture.v。 *)\n")
        dirty_lf = header + "Definition a := 1. (* 这里埋一个载体词 *)\n" \
                            "Definition b := 2.\n"  # fixture data: 载体 is a comment_pack flag_words key
        dirty_v = wf(os.path.join(src, "dirty.v"), dirty_lf.replace(
            "\n", "\r\n"), newline="")
        clean_v = wf(os.path.join(src, "clean.v"),
                     header + "Definition a := 1.\nDefinition b := 2.\n")
        missy_v = wf(os.path.join(src, "missy.v"),
                     header + "Definition c := 3. (* 这是一个探针词面 *)\n")
        mixed_v = wf(os.path.join(src, "mixed.v"),
                     header + "Definition d := 4. (* 载体一词与探针词面并存"
                              " *)\n")
        order_txt = wf(os.path.join(src, "order.txt"),
                       "ToyA.v#R7\nToyB.v#R8-deadbeef\n")
        order_miss = wf(os.path.join(src_miss, "order.txt"),
                        "Ghost.v#R9\n")
        wf(os.path.join(asrc, "ToyA.v"), "Definition ta := 1.\n")
        wf(os.path.join(asrc, "ToyB.v"), "Definition tb := 2.\n")
        # v13/14/16 preset-vector fixture: a `**`-style header missing two
        # fields (drives the gate4 missing-field hard item); Require face =
        # one From Stdlib line + two bare lines
        fx_header = (
            "(* ConstructiveWorld-Set -- fixture bundle for the wash shape "
            "header-map preset selftest. *)\n"
            "\n"
            "(** * hdmap_fx: the render-vector fixture module of the wash "
            "shape header-map preset.\n"
            "\n"
            "    Mission.  Supplies the fixture interface slot for the wash "
            "shape\n"
            "      selftest render vector: [tsp_fx_slot] closes the toy slot "
            "over\n"
            "      Set data and the companion discharge restates the exit "
            "shape.\n"
            "\n"
            "    Dependencies.  Rocq standard library only.\n"
            "*)\n")
        fx_body = ("\nFrom Stdlib Require Import QArith.\n"
                   "Require Import S01_BaseRing.\n"
                   "Require Import S02_Cauchy.\n"
                   "\n"
                   "Definition fx_slot : True.\n"
                   "Proof. exact I. Qed.\n")
        fx_v = wf(os.path.join(src, "hdmap_fx.v"), fx_header + fx_body)
        # v16-only copy (the v14 apply would wash hdmap_fx.v into a
        # five-field-complete file; the plan-miss vector needs the
        # untouched missing-field file)
        fx2_v = wf(os.path.join(src, "hdmap_fx2.v"), fx_header + fx_body)

        def load_json(path):
            with io.open(path, "r", encoding="utf-8") as fh:
                return json.load(fh)

        def washes_of(rep, name_suffix):
            for f in rep["plan"]["files"]:
                if f["file"].endswith(name_suffix):
                    return dict((w["kind"], w) for w in f["washes"])
            return {}

        # v1 per-wash plan verdicts (dirty file)
        j1 = os.path.join(tmp, "j1.json")
        rc, out = run(["--file", dirty_v, "--json", j1])
        rep1 = load_json(j1)
        w1 = washes_of(rep1, "dirty.v")
        c1 = (rc == 1 and rep1["schema"] == SCHEMA
              and rep1["verdict"] == "partial"
              and w1["lexical"]["status"] == "would-fix"
              and "载体" in w1["lexical"]["detail"]  # 载体 comes from the comment_pack data key
              and w1["token"]["status"] == "clean"
              and w1["header"]["status"] == "clean"
              and w1["eol"]["status"] == "would-fix"
              and w1["anchor"]["status"] == "clean"
              and "not applicable" in w1["anchor"]["detail"])
        print("v1 per-wash plan verdicts (dirty file partial):", c1)
        ok = ok and c1

        # v2 clean-file control
        rc, out = run(["--file", clean_v, "--json",
                       os.path.join(tmp, "j2.json")])
        rep2 = load_json(os.path.join(tmp, "j2.json"))
        c2 = rc == 0 and rep2["verdict"] == "clean" and \
            all(w["status"] == "clean"
                for f in rep2["plan"]["files"] for w in f["washes"])
        print("v2 clean-file control all clean:", c2)
        ok = ok and c2

        # v3 plan writes nothing; --apply defaults off
        md5_before = md5_of(dirty_v)
        c3 = md5_of(dirty_v) == md5_before
        print("v3 plan writes nothing (--apply defaults off):", c3)
        ok = ok and c3

        # v4 plan-miss honesty (unrewritable + mixed files)
        rc, out = run(["--file", missy_v])
        m_miss = ("PLAN-MISS" in out and "禁词:探针" in out
                  and "no rewrite entry" not in out)  # 禁词 = gate4 output tag (interface)
        rc, out = run(["--file", mixed_v, "--json",
                       os.path.join(tmp, "j4.json")])
        rep4 = load_json(os.path.join(tmp, "j4.json"))
        w4 = washes_of(rep4, "mixed.v")
        c4 = (rc == 1 and rep4["verdict"] == "plan-miss"
              and w4["lexical"]["status"] == "would-fix"
              and "unfixable[禁词:探针]" in w4["lexical"]["detail"]
              and rep4["plan"]["stats"]["plan_miss_items"] == 1)
        print("v4 plan-miss honesty (unrewritable/mixed files):", c4, m_miss)
        ok = ok and c4 and m_miss

        # v5 apply -> rescan clean -> shaped (word-face / CRLF / anchor verified)
        rc, out = run(["--file", dirty_v, "--file", order_txt,
                       "--anchor-src", asrc, "--apply", "--json",
                       os.path.join(tmp, "j5.json")])
        rep5 = load_json(os.path.join(tmp, "j5.json"))
        dirty_txt = io.open(dirty_v, "rb").read().decode("utf-8")
        order_txt_now = io.open(order_txt, "r", encoding="utf-8").read()
        fp_a = md5_8_of(os.path.join(asrc, "ToyA.v"))
        fp_b = md5_8_of(os.path.join(asrc, "ToyB.v"))
        rescan_w = {}
        for f in rep5["apply"]["rescan"]["files"]:
            rescan_w[f["file"]] = dict((w["kind"], w["status"])
                                       for w in f["washes"])
        c5 = (rc == 0 and rep5["verdict"] == "shaped"
              and "载体" not in dirty_txt and "carrier" in dirty_txt
              and "\r" not in dirty_txt
              and ("ToyA.v#R7-%s" % fp_a) in order_txt_now
              and ("ToyB.v#R8-%s" % fp_b) in order_txt_now
              and len(rep5["apply"]["applied"]) >= 3
              and all(s == "clean"
                      for d in rescan_w.values() for s in d.values()))
        print("v5 apply->rescan clean->shaped (word-face/CRLF/anchor):", c5)
        ok = ok and c5

        # v6 idempotence (second plan all clean; re-apply applies zero)
        rc, out = run(["--file", dirty_v, "--file", order_txt,
                       "--anchor-src", asrc, "--json",
                       os.path.join(tmp, "j6.json")])
        rep6 = load_json(os.path.join(tmp, "j6.json"))
        rc6b, out6b = run(["--file", dirty_v, "--file", order_txt,
                           "--anchor-src", asrc, "--apply"])
        c6 = (rc == 0 and rep6["verdict"] == "clean"
              and all(w["status"] == "clean"
                      for f in rep6["plan"]["files"] for w in f["washes"])
              and rc6b == 0 and "applied=0" in out6b)
        print("v6 idempotence (second plan all clean / re-apply zero applied):", c6)
        ok = ok and c6

        # v7 anchor missing entity -> plan-miss
        rc, out = run(["--file", order_miss, "--anchor-src", asrc])
        c7 = rc == 1 and "PLAN-MISS" in out and "missing entity" in out
        print("v7 anchor missing entity plan-miss:", c7)
        ok = ok and c7

        # v8 frozen-roster exclusion (injector-canned roster + real frozen8 roster)
        vault = os.path.join(tmp, "vault")
        os.makedirs(vault)
        frozen_me = wf(os.path.join(vault, "frozen_me.py"), "x = 1\n")
        wf(os.path.join(vault, "okfile.v"),
           header + "Definition e := 5.\n")
        inj = wf(os.path.join(tmp, "inj.json"), json.dumps(
            {"frozen8": {"rc": 0, "stdout":
                         "deadbeefdeadbeefdeadbeefdeadbeef  %s\n" % frozen_me}},
            ensure_ascii=False))
        rc, out = run(["--dir", vault, "--injector", inj, "--json",
                       os.path.join(tmp, "j8.json")])
        rep8 = load_json(os.path.join(tmp, "j8.json"))
        excl_paths = " ".join(e["path"] for e in rep8["scope"]["excluded"])
        plan_files = " ".join(f["file"] for f in rep8["plan"]["files"])
        rc8b, out8b = run(["--file", frozen_me, "--injector", inj])
        rc8c, out8c = run(["--file", os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "scan", "mac_stmt_scan.py"), "--only", "eol"])
        c8 = (rc == 0 and "frozen_me.py" in excl_paths
              and "frozen_me.py" not in plan_files
              and rc8b == 2 and "rejection" in out8b
              and rc8c == 2 and "rejection" in out8c
              and rep8["scope"]["frozen_roster_source"] == "injector-canned")
        print("v8 frozen-roster exclusion (canned --dir exclusion / explicit rejection rc2 / real roster rejection):", c8)
        ok = ok and c8

        # v9 subprocess-layer injection (canned gate4 verdict face)
        inj2 = wf(os.path.join(tmp, "inj2.json"), json.dumps(
            {"gate4": {"rc": 1, "stdout": "canned-gate4",
                       "report": {"results": [
                           {"file": dirty_v, "verdict": "FAIL",
                            "hard": [[6, "体内散块", "禁词", "探针"]],
                            "review": []}]}}}, ensure_ascii=False))
        rc, out = run(["--file", dirty_v, "--injector", inj2,
                       "--only", "lexical"])
        c9 = rc == 1 and "PLAN-MISS" in out and "gate4=FAIL" in out \
            and "禁词:探针" in out
        print("v9 subprocess-layer injection (canned gate4 face):", c9)
        ok = ok and c9

        # v10 CLI four codes
        rc_h, out_h = run(["--help"])
        rc_b, out_b = run(["--bogus"])
        rc_n, out_n = run([])
        rc_m, out_m = run(["--file", os.path.join(tmp, "nope.v")])
        c10 = (rc_h == 0 and "usage" in out_h.lower()
               and rc_b == 2 and rc_n == 2 and rc_m == 9)
        print("v10 CLI four codes (help0/bogus2/no-input2/missing9):", c10)
        ok = ok and c10

        # v11 --once/--loop modes (two watch rounds + stop event; event-stream
        # shape: schema/seq/kind; sort_keys canonical form; ts=off note)
        rc, out = run(["--file", clean_v, "--only", "eol", "--loop",
                       "--interval", "0", "--sleep-scale", "0",
                       "--max-rounds", "2"])
        ev_pairs = []
        for ln in out.splitlines():
            ln = ln.strip()
            if not ln.startswith("{"):
                continue
            try:
                e = json.loads(ln)
            except ValueError:
                continue
            if isinstance(e, dict) and e.get("schema") == EVENT_SCHEMA:
                ev_pairs.append((ln, e))     # stdout mirror line by line (loud)
        evs11 = [e for _, e in ev_pairs]
        c11 = (rc == 0 and len(evs11) == 3
               and [e["kind"] for e in evs11] == ["round", "round", "stop"]
               and [e["seq"] for e in evs11] == [1, 2, 3]
               and all(ln == json.dumps(e, ensure_ascii=False,
                                        sort_keys=True) for ln, e in ev_pairs)
               and all("ts=off" in e.get("note", "") for e in evs11))
        print("v11 --loop watch mode (max-rounds 2 / event shape schema+seq+kind):", c11)
        ok = ok and c11

        # v12 determinism (plan --json reruns byte-identical)
        ja = os.path.join(tmp, "ja.json")
        jb = os.path.join(tmp, "jb.json")
        run(["--file", missy_v, "--file", order_miss, "--anchor-src",
             asrc, "--json", ja])
        run(["--file", missy_v, "--file", order_miss, "--anchor-src",
             asrc, "--json", jb])
        c12 = io.open(ja, "rb").read() == io.open(jb, "rb").read()
        print("v12 determinism (plan --json reruns byte-identical):", c12)
        ok = ok and c12

        # v13 preset chain (loads; conforming files untouched; probe order preset/--header-map beats env)
        j13a = os.path.join(tmp, "j13a.json")
        rc, out = run(["--file", clean_v, "--header-map-preset",
                       "campaign_set_diamond", "--json", j13a])
        rep13a = load_json(j13a)
        hm13 = rep13a["scope"]["header_map"]
        envmap_empty = wf(os.path.join(tmp, "envmap_empty.json"), "{}")
        envmap_fx = wf(os.path.join(tmp, "envmap_fx.json"), json.dumps(
            {"hdmap_fx": "(* env-side header *)"}, ensure_ascii=False))
        env_preset = dict(os.environ)
        env_preset[ENV_HEADER_MAP] = envmap_empty
        env_explicit = dict(os.environ)
        env_explicit[ENV_HEADER_MAP] = envmap_fx
        rc13b, out13b = run(["--file", fx_v, "--header-map-preset",
                             "campaign_set_diamond", "--only", "header"],
                            env=env_preset)
        rc13c, out13c = run(["--file", fx_v, "--header-map", envmap_empty,
                             "--only", "header"], env=env_explicit)
        c13 = (rc == 0 and rep13a["verdict"] == "clean"
               and hm13["source"] == "preset"
               and hm13["preset"] == "campaign_set_diamond"
               and rc13b == 1 and "designated-template full rewrite" in out13b
               and rc13c == 1 and "no rewrite template (template source=map" in out13c)
        print("v13 preset chain (loads / conforming untouched / preset>--header-map beats env):", c13)
        ok = ok and c13

        # v14 preset placeholder render -> apply end to end (missing-field file -> full rewrite -> shaped -> idempotent)
        j14a = os.path.join(tmp, "j14a.json")
        rc, out = run(["--file", fx_v, "--header-map-preset",
                       "campaign_set_diamond", "--json", j14a])
        rep14a = load_json(j14a)
        w14 = washes_of(rep14a, "hdmap_fx.v")
        c14a = (rc == 1 and rep14a["verdict"] == "partial"
                and w14["header"]["status"] == "would-fix"
                and "designated-template full rewrite" in w14["header"]["detail"]
                and "缺字段" in w14["header"]["detail"]  # 缺字段 = gate4 output tag (interface, kept)
                and w14["header"]["action"] == ACTION_SWEEP_MAP_PRESET)
        rc, out = run(["--file", fx_v, "--header-map-preset",
                       "campaign_set_diamond", "--apply", "--json",
                       os.path.join(tmp, "j14b.json")])
        rep14b = load_json(os.path.join(tmp, "j14b.json"))
        fx_txt = io.open(fx_v, "r", encoding="utf-8").read()
        c14b = (rc == 0 and rep14b["verdict"] == "shaped"
                and "Stdlib [QArith]. Requires [S01_BaseRing]" in fx_txt
                and "[S02_Cauchy]" in fx_txt
                and "(* ConstructiveWorld-Set -- fixture bundle" in fx_txt
                and "coqc -native-compiler no -q -Q . \"\" hdmap_fx.v"
                in fx_txt
                and "Axioms: none" in fx_txt
                and "Rocq standard library only." not in fx_txt)
        rc, out = run(["--file", fx_v, "--header-map-preset",
                       "campaign_set_diamond", "--json",
                       os.path.join(tmp, "j14c.json")])
        rep14c = load_json(os.path.join(tmp, "j14c.json"))
        c14c = rc == 0 and rep14c["verdict"] == "clean" and all(
            w["status"] == "clean"
            for f in rep14c["plan"]["files"] for w in f["washes"])
        c14 = c14a and c14b and c14c
        print("v14 preset placeholder render->apply end to end (partial->shaped"
              "->idempotent / render asserted name by name):", c14)
        ok = ok and c14

        # v15 same-slot exclusivity (both flags rc2; unknown preset name rc2)
        rc, out = run(["--file", clean_v, "--header-map", envmap_empty,
                       "--header-map-preset", "campaign_set_diamond"])
        rc15b, out15b = run(["--file", clean_v, "--header-map-preset",
                             "no_such_preset"])
        c15 = (rc == 2 and "same-slot" in out
               and rc15b == 2 and "unrecognized" in out15b)
        print("v15 same-slot exclusivity (both flags rc2 / unknown name rc2):", c15)
        ok = ok and c15

        # v16 no-source plan-miss honesty + missing template library rc9 (isolated repo_root)
        env_clean = dict(os.environ)
        env_clean.pop(ENV_HEADER_MAP, None)
        rc, out = run(["--file", fx2_v, "--only", "header"], env=env_clean)
        iso = os.path.join(tmp, "iso")
        for sub in ("verify", "scan", "wash", "tools", "certify"):
            os.makedirs(os.path.join(iso, sub))
        real_root = os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))
        for rel in ("verify/gate4_comment_guard.py",
                    "scan/scan_v4_token.py",
                    "wash/cure_applier.py",
                    "wash/comment_sweep.py",
                    "wash/comment_pack.json",
                    "tools/registry_union.py",
                    "certify/frozen8.py"):
            # plain copy, not os.symlink: Windows symlink creation needs
            # SeCreateSymbolicLinkPrivilege (WinError 1314 without admin or
            # developer mode), which crashed this vector off-admin machines
            # (T0-5 platform-defect family). The vector only needs the seven
            # engine files present at their canonical relative paths, and a
            # copy satisfies that identically.
            shutil.copyfile(os.path.join(real_root, rel),
                            os.path.join(iso, rel))
        rc16b, out16b = run(["--file", clean_v, "--header-map-preset",
                             "campaign_set_diamond", "--repo-root", iso])
        c16 = (rc == 1 and "PLAN-MISS" in out
               and "no rewrite template (template source=none" in out
               and rc16b == 9 and "template library missing" in out16b)
        print("v16 no-source plan-miss honesty / missing template library rc9:", c16)
        ok = ok and c16

        # v17 --loop event-stream shape (--events lines canonical; flush+fsync;
        # seq continues across processes without reuse)
        ev17 = os.path.join(tmp, "ev17.jsonl")
        rc, out = run(["--file", clean_v, "--only", "eol", "--loop",
                       "--interval", "0", "--sleep-scale", "0",
                       "--max-rounds", "2", "--events", ev17])
        rc17b, out17b = run(["--file", clean_v, "--only", "eol", "--loop",
                             "--interval", "0", "--sleep-scale", "0",
                             "--max-rounds", "1", "--events", ev17])
        lines17 = [ln for ln in
                   io.open(ev17, encoding="utf-8").read().splitlines() if ln]
        evs17 = [json.loads(ln) for ln in lines17]
        c17 = (rc == 0 and rc17b == 0
               and [e["seq"] for e in evs17] == [1, 2, 3, 4, 5]
               and [e["kind"] for e in evs17] == ["round", "round", "stop",
                                                  "round", "stop"]
               and all(e["schema"] == EVENT_SCHEMA for e in evs17)
               and all(ln == json.dumps(json.loads(ln), ensure_ascii=False,
                                        sort_keys=True) for ln in lines17))
        print("v17 event-stream shape (--events canonical lines / seq continues across processes):", c17)
        ok = ok and c17

        # v18 plan-cache invalidation (source md5 change -> recompute; stable
        # -> cache hit):
        # a) scope-file md5 change: loop --apply three rounds, round 1 miss ->
        #    apply CRLF->LF (file changes) -> round 2 must miss (eol clean after
        #    recompute) -> round 3 stable hit reuse;
        # b) a wash-5 anchor-entity md5 change is also a source change:
        #    ToyE.v (the entity) is eol-applied in round 1 while order_e.txt is
        #    untouched -> round 2 misses purely from the entity domain (a domain
        #    missing its entity would be a false hit) -> round 2 applies and
        #    changes order_e.txt -> round 3 misses -> round 4 stable hit
        #    (sequence [F,F,F,T]).
        cache_v = wf(os.path.join(src, "cache_probe.v"),
                     header + "Definition z := 0.\r\n", newline="")
        ev18 = os.path.join(tmp, "ev18.jsonl")
        j18 = os.path.join(tmp, "j18.json")
        rc, out = run(["--file", cache_v, "--only", "eol", "--loop", "--apply",
                       "--interval", "0", "--sleep-scale", "0",
                       "--max-rounds", "3", "--events", ev18, "--json", j18])
        evs18 = [json.loads(ln) for ln in io.open(ev18, encoding="utf-8")
                 if ln.strip() and json.loads(ln)["kind"] == "round"]
        rep18 = load_json(j18)
        c18a = (rc == 0
                and [e["plan_cache_hit"] for e in evs18] == [False, False, True]
                and rep18["plan_cache"]["hit"] is True
                and evs18[0]["n_applied"] == 1     # round 1 applied CRLF->LF
                and evs18[1]["n_applied"] == 0     # round 2 clean after recompute
                and all(w["status"] == "clean"
                        for f in rep18["plan"]["files"]
                        for w in f["washes"]))
        print("v18a plan cache (scope md5 change -> recompute miss / stable -> hit reuse):", c18a)
        ok = ok and c18a

        asrc18 = os.path.join(tmp, "asrc18")
        os.makedirs(asrc18)
        src18 = os.path.join(tmp, "src18")
        os.makedirs(src18)
        toy_e = wf(os.path.join(asrc18, "ToyE.v"),
                   "Definition te := 1.\r\nDefinition tf := 2.\r\n",
                   newline="")
        order_e = wf(os.path.join(src18, "order.txt"),
                     "ToyE.v#R9-%s\n" % md5_8_of(toy_e))
        ev18b = os.path.join(tmp, "ev18b.jsonl")
        j18b = os.path.join(tmp, "j18b.json")
        rc, out = run(["--file", order_e, "--file", toy_e,
                       "--anchor-src", asrc18, "--only", "eol,anchor",
                       "--loop", "--apply", "--interval", "0",
                       "--sleep-scale", "0", "--max-rounds", "4",
                       "--events", ev18b, "--json", j18b])
        evs18b = [json.loads(ln) for ln in io.open(ev18b, encoding="utf-8")
                  if ln.strip() and json.loads(ln)["kind"] == "round"]
        rep18b = load_json(j18b)
        c18b = (rc == 0
                and [e["plan_cache_hit"] for e in evs18b]
                == [False, False, False, True]
                and [e["n_applied"] for e in evs18b] == [1, 1, 0, 0]
                and rep18b["plan_cache"]["hit"] is True
                and all(w["status"] == "clean"
                        for f in rep18b["plan"]["files"]
                        for w in f["washes"]))
        print("v18b plan cache (anchor-entity md5 change -> recompute miss;"
              " sequence [F,F,F,T]):", c18b)
        ok = ok and c18b

        print("WASH-SHAPE-SELFTEST:",
              "PASS (all 18 vectors)" if ok else "FAIL")
        return 0 if ok else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---------- main ----------

def main():
    argv = sys.argv[1:]
    if "--selftest" in argv:
        sys.exit(selftest())
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(
        prog=PROG,
        description="shape-normalizing tool: canonical wash pipeline"
                    " (gate4 word-face / token survey + canonical pack / header"
                    " template / eol normalization / registry re-anchor /"
                    " jargon map apply / ai-flavor advisory provider route;"
                    " two-phase plan->apply with rescan verification; schema"
                    " rocqwash-shape/1)")
    ap.add_argument("--file", action="append", default=[], metavar="PATH",
                    help="target files (repeatable; .v runs washes 1-3;"
                         " .py/.sh/.md runs washes 6-7 too; .json/.ts runs"
                         " wash 7; order.txt/_CoqProject runs wash 5; any"
                         " text file runs wash 4)")
    ap.add_argument("--dir", action="append", default=[], metavar="DIR",
                    help="whole-tree collection (.v plus order.txt/_CoqProject;"
                         " the wash-6/7 prose faces .py/.sh/.md/.json/.ts join"
                         " the collection when the selection names jargon or"
                         " ai-flavor; repeatable)")
    ap.add_argument("--exclude", action="append", default=[], metavar="NAME",
                    help="additional excluded names (a basename or a path"
                         " segment; rostered frozen files are auto-excluded)")
    ap.add_argument("--only", default=None, metavar="KINDS",
                    help="wash subset (comma-separated: lexical,token,header,"
                         "eol,anchor,jargon,ai-flavor or 1-7; default all"
                         " seven)")
    ap.add_argument("--header-map", dest="header_map", default=None,
                    metavar="MAP.json",
                    help="wash-3 header full-rewrite template ({basename: header"
                         " text}; per-file data; same-slot exclusive with"
                         " --header-map-preset, rc 2)")
    ap.add_argument("--header-map-preset", dest="header_map_preset",
                    default=None, metavar="NAME",
                    help="wash-3 header designated template (a preset name in"
                         " the tests/fixtures/header_map_v1.json distilled"
                         " library; placeholders derive from the target's own"
                         " faces / carried header; probe order --header-map >"
                         " this flag > env ROCWASH_HEADER_MAP > none ="
                         " plan-miss)")
    ap.add_argument("--anchor-src", dest="anchor_src", default=None,
                    metavar="DIR",
                    help="wash-5 anchor entity source directory (default = the"
                         " registry file's own directory)")
    ap.add_argument("--repo-root", dest="repo_root", default=None,
                    metavar="DIR",
                    help="engine files root (default = this script's"
                         " grandparent; fully parameterized)")
    ap.add_argument("--json", dest="jsonout", default=None, metavar="OUT",
                    help="report output path (schema rocqwash-shape/1)")
    ap.add_argument("--apply", action="store_true",
                    help="phase two: execute would-fix items and re-run all"
                         " washes for verification (default: plan, zero writes)")
    ap.add_argument("--loop", action="store_true",
                    help="watch mode: one pass per round plus a JSONL event"
                         " stream (default: --once, a single pass)")
    ap.add_argument("--interval", type=float, default=5.0, metavar="S",
                    help="seconds between loop rounds (default 5; adjustable)")
    ap.add_argument("--sleep-scale", dest="sleep_scale", type=float,
                    default=1.0, metavar="S",
                    help="sleep scale (0 = no real sleep; selftest dependency)")
    ap.add_argument("--max-rounds", dest="max_rounds", type=int, default=0,
                    metavar="N", help="loop round cap (0 = unbounded)")
    ap.add_argument("--events", default=None, metavar="FILE",
                    help="loop JSONL event append file (stdout always flows;"
                         " this flag additionally writes to disk)")
    ap.add_argument("--injector", default=None, metavar="SCEN.json",
                    help="subprocess-layer canning scenario {engine key:"
                         " {rc,stdout,report}} (key set gate4/scan_v4/cure/"
                         "sweep/registry_union/frozen8)")
    args = ap.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    try:
        if not args.file and not args.dir:
            print("FAIL-LOUD: --file/--dir: at least one is required"
                  " (collection surface)", file=sys.stderr)
            sys.exit(2)
        if args.interval < 0 or args.sleep_scale < 0 or args.max_rounds < 0:
            print("FAIL-LOUD: --interval/--sleep-scale/--max-rounds must be >= 0",
                  file=sys.stderr)
            sys.exit(2)
        if args.header_map and args.header_map_preset:
            print("FAIL-LOUD: --header-map and --header-map-preset are"
                  " same-slot exclusive (rc 2 same-slot rule — pass exactly one"
                  " wash-3 template source)", file=sys.stderr)
            sys.exit(2)
        ws = WashShape(args)
        ws.files, ws.excluded_records = ws.collect_files()
        print("== WASH-SHAPE (%s) kinds=%s files=%d excluded=%d =="
              % ("loop" if args.loop else
                 ("apply" if args.apply else "plan"),
                 ",".join(ws.kinds), len(ws.files),
                 len(ws.excluded_records)))
        if args.loop:
            rc = ws.run_loop()
        else:
            rc = ws.run_once()
        sys.exit(rc)
    except UsageError as e:
        print("FAIL-LOUD: %s" % e, file=sys.stderr)
        sys.exit(2)
    except MissingInput as e:
        print("FAIL-LOUD: %s" % e, file=sys.stderr)
        sys.exit(9)


if __name__ == "__main__":
    main()
