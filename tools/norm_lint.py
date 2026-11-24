#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""norm_lint: annotation-face normalization lint, report-only first form.

Purpose.  Machine-checks prose faces (comments, docstrings, shell help,
  documentation) of .py/.sh/.md/.v files: (1) header shape, error -- banner
  plus five-field block, names Purpose. / Interface. / Dependencies. /
  Evidence. / Exit-codes. verbatim, all five present; (2) jargon, error --
  mapping-table terms on prose lines (word boundaries for ASCII, whole-
  word adjacency for CJK, backtick citations exempt); (3) CJK residue,
  warn -- one finding per file above --cjk-threshold unless whitelisted;
  (4) process-name classes, warn; (5) header budget, warn -- header over
  30 lines.  Findings are data; the exit code never escalates on them.

Interface.  --tree DIR | --file PATH [--jargon-map P] [--cjk-threshold F]
  [--cjk-whitelist P] [--ai-flavor-map P] [--json P] [--md P] | --selftest.
  Schema rocqwash-norm-lint/1: findings carry {line, kind, term, suggest},
  kinds {header, jargon, ai_flavor, em_dash, cjk, forbidden, budget, parse}.
  Scans skip dot directories, *.zh.md and docs/zh/ archives, report targets
  and docs/norm-lint-baseline-*.md faces; the mapping table (default
  docs/jargon-to-standard-mapping-v1.md, missing exits 9) is exempt from
  the jargon check only.

Dependencies.  Python 3 standard library only; the mapping table and the
  optional CJK whitelist are path-parameterized data faces.

Evidence.  --selftest covers six vectors on temporary fixtures (jargon hit,
  fields missing, substring and technical-usage exemption, whitelist
  exemption, compliant English triple, Coq comment face; byte-identical reruns).

Exit-codes.  0 accounted (findings are data); 1 instrument failure; 2 usage; 9 missing input.
"""
# Extended contract (help face; kept outside the five-field block so the
# header stays within the 30-line budget of the annotation standard):
# --tree DIR         scan DIR recursively for .py/.sh/.md/.v; dot directories,
#                    *.zh.md archives and docs/zh/ grandfathered archives are
#                    excluded from all checks; relative input paths
#                    (--jargon-map, --cjk-whitelist) resolve tree-root first,
#                    then working directory; output paths resolve against the
#                    working directory.
# --file PATH        lint one file of the four faces; other extensions are a
#                    usage error.
# --jargon-map P     three-column mapping table (face | standard | note); a
#                    row may carry an optional fourth cell with ';'-separated
#                    exempt regexes applied line-scoped; the loaded table
#                    itself is exempt from the jargon check only (it carries
#                    the faces by design, so matching it would be circular).
# --cjk-threshold F  CJK share limit, default 0.0 (the zero-CJK end state);
#                    a file whose ratio exceeds it draws one warn unless it
#                    is listed in the whitelist; the ratio is always
#                    reported per file and in the summary.
# --cjk-whitelist P  tree-relative paths exempt from the CJK check while
#                    their translation is pending; '#' starts a comment.
# --ai-flavor-map P  optional report face (engine-body batch): load the
#                    36-face word map through tools/ai_flavor.py and add
#                    ai_flavor findings (one per face hit on a prose line,
#                    suggest = the map's candidate kinds) plus em_dash
#                    findings (one per prose line carrying U+2014); both are
#                    error-level data.  Absent flag = the face is off and the
#                    report is byte-identical to the pre-batch form.  The map
#                    file is exempt from the wording battery only (it carries
#                    the faces by design); the em-dash count is exempt nowhere.
# --json P / --md P  report targets, schema rocqwash-norm-lint/1.
# --selftest         six vectors on temporary fixtures; runs standalone.
# --gate / --strict  reserved for the future gated form; passing either
#                    today is a usage error (exit 2).  Grading follows the
#                    annotation standard card: header and jargon findings are
#                    error-level, CJK residue, forbidden classes and header
#                    budget are warn-level; this report-only form counts them
#                    in the summary without ever escalating the exit code.
# Prose-face extraction: python docstrings (statement-position strings) plus
# comments via tokenize; shell leading comment block plus heredoc bodies;
# markdown files contribute their whole text; Coq (* *) comment lines are
# extracted nested-aware with the vernacular body and string bodies masked
# (the complement of anchor_guard mask_comments_strings).  Backtick spans are
# identifier citations and are masked out of the jargon and CJK faces alike.
# Determinism: findings and files are sorted, reports carry no wall-clock
# fields, and identical inputs rerun byte-identical.

import argparse
import fnmatch
import io
import json
import os
import re
import shutil
import sys
import tempfile
import tokenize

SCHEMA = "rocqwash-norm-lint/1"
TOOL = "norm_lint"
FACES = (".py", ".sh", ".md", ".v")
FIELDS = ("Purpose.", "Interface.", "Dependencies.", "Evidence.", "Exit-codes.")
DEFAULT_JARGON_MAP = "docs/jargon-to-standard-mapping-v1.md"
HEADER_BUDGET = 30  # annotation card: gate4 length_cap=30 review-grade default

RE_CJK = re.compile(
    "[\u2e80-\u2eff\u3000-\u303f\u3040-\u30ff\u3400-\u4dbf"
    "\u4e00-\u9fff\uf900-\ufaff\uff00-\uffef]")
# whole-word rule for CJK terms: a term refuses to fire when the neighbouring
# character on that side is itself a CJK ideograph (mapping-table precedent)
RE_CJK_ADJ = re.compile("[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
RE_BACKTICK = re.compile(r"`[^`\n]*`")

FIELD_BODY = "|".join(re.escape(f) for f in FIELDS)
# banner check: does a line OPEN with a field name (then it is not a banner)
FIELD_LINE = {
    "py": re.compile("^[ \t]*(" + FIELD_BODY + ")(?:\\s|$)"),
    "sh": re.compile("^[ \t]*#[ \t]*(" + FIELD_BODY + ")(?:\\s|$)"),
    "md": re.compile("^[ \t]*>?[ \t]*(" + FIELD_BODY + ")(?:\\s|$)"),
    "v": re.compile("^[ \t]*(" + FIELD_BODY + ")(?:\\s|$)"),
}
# field-presence check: one regex per field, line-anchored, period verbatim
FIELD_ONE = {}
for _kind, _prefix in (("py", "^[ \t]*"), ("sh", "^[ \t]*#[ \t]*"),
                       ("md", "^[ \t]*>?[ \t]*"), ("v", "^[ \t]*")):
    FIELD_ONE[_kind] = dict(
        (f, re.compile("(?m)" + _prefix + re.escape(f) + r"(?:\s|$)"))
        for f in FIELDS)

# forbidden classes (warn), the card's process-narration classes narrowed to
# what the issuing task lists: internal role-name compounds the whole-word
# rule cannot split, and date-stamp annotation forms.  The organization faces
# proper (the English slang family and their Chinese compounds) are already
# error-level through the mapping table.
FORBIDDEN = (
    (re.compile("主会话|工装席|编译席|洗波席|深挖席|收包席|清洗席|判读席|复盘席|勘形席|J[1-9]席"),
     "replace the internal role name with the plain role wording"),
    (re.compile(r"\b20\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\b|\b20\d{2}-\d{2}-\d{2}\b"),
     "drop the date stamp from the prose face; dates belong in the ledger surface"),
)

RE_HEREDOC = re.compile(r"<<-?\s*['\"]?([A-Za-z_][A-Za-z0-9_]*)['\"]?")
RE_MD_HEADING2 = re.compile(r"^##\s")
RE_FW_PAREN = re.compile("（[^）]*）")

DOCSTRING_SUGGEST = {
    "py": "add a two-part module docstring: banner line, then the five-field block",
    "sh": "add a two-part leading comment block: banner line, then the five-field block",
    "md": "add a two-part header: H1 banner, then the five-field block before the first section",
    "v": "add a two-part leading comment block: banner line, then the five-field block",
}


def fail(msg, code):
    sys.stderr.write(TOOL + ": " + msg + "\n")
    raise SystemExit(code)


def mk(line, kind, term, suggest):
    return {"line": line, "kind": kind, "term": term, "suggest": suggest}


class JargonTerm(object):
    __slots__ = ("term", "suggest", "regex", "exempts")

    def __init__(self, term, suggest, exempts):
        self.term = term
        self.suggest = suggest
        left = "(?<!" + RE_CJK_ADJ.pattern + ")" if RE_CJK_ADJ.match(term[:1]) else r"\b"
        right = "(?!" + RE_CJK_ADJ.pattern + ")" if RE_CJK_ADJ.match(term[-1:]) else r"\b"
        self.regex = re.compile(left + re.escape(term) + right)
        self.exempts = [re.compile(x) for x in exempts]


def load_jargon_map(path):
    try:
        with io.open(path, "r", encoding="utf-8") as fh:
            raw = fh.read()
    except OSError as exc:
        fail("jargon map unreadable: " + path + " (" + str(exc) + ")", 9)
    # JSON seed form (schema rocqwash-jargon-map/1): entries[] carrying
    # face/standard/exempts — the sync tool's cast shape (20261118 wave59).
    # The md-table parser below stays for the docs/ detection-table form.
    if raw.lstrip().startswith("{"):
        try:
            data = json.loads(raw)
        except ValueError as exc:
            fail("jargon map JSON malformed: " + path + " (" + str(exc) + ")", 1)
        terms = []
        seen = set()
        for e in data.get("entries") or []:
            face = (e.get("face") or "").strip()
            std = (e.get("standard") or "").strip()
            if not face:
                continue
            if face in seen:
                fail("duplicate jargon face %r in %s" % (face, path), 1)
            seen.add(face)
            exempts = [x.strip() for x in (e.get("exempts") or [])
                       if x.strip()]
            terms.append(JargonTerm(face, std, exempts))
        if not terms:
            fail("jargon map has no active rows: " + path, 1)
        terms.sort(key=lambda t: (-len(t.term), t.term))
        return terms
    rows = raw.splitlines()
    terms = []
    seen = set()
    for lineno, raw in enumerate(rows, 1):
        line = raw.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        first = cells[0] if cells else ""
        if not first or "黑话" in first or set(first) <= set("- "):
            continue
        if len(cells) < 3:
            fail("malformed jargon map row at %s:%d (need face|standard|note)"
                 % (path, lineno), 1)
        face = RE_FW_PAREN.sub("", first).strip()
        suggest = cells[1]
        exempt_cell = cells[3] if len(cells) > 3 else ""
        for part in re.split(r"／|/", face):
            term = part.strip()
            if not term:
                continue
            if term in seen:
                fail("duplicate jargon face %r at %s:%d" % (term, path, lineno), 1)
            seen.add(term)
            exempts = [x.strip() for x in exempt_cell.split(";") if x.strip()]
            terms.append(JargonTerm(term, suggest, exempts))
    if not terms:
        fail("jargon map has no active rows: " + path, 1)
    terms.sort(key=lambda t: (-len(t.term), t.term))
    return terms


def load_whitelist(path):
    try:
        with io.open(path, "r", encoding="utf-8") as fh:
            rows = fh.read().splitlines()
    except OSError as exc:
        fail("cjk whitelist unreadable: " + path + " (" + str(exc) + ")", 9)
    items = set()
    for raw in rows:
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        items.add(s.replace("\\", "/"))
    return items


def mask_backticks(text):
    # identifier citations in backticks are exempt (mapping table register);
    # spans are blanked with NUL, keeping positions and lengths intact
    return RE_BACKTICK.sub(lambda m: "`" + "\x00" * (len(m.group(0)) - 2) + "`", text)


def py_docface(text):
    """Return (segments, first_docstring_span, error)."""
    lines = text.splitlines()
    try:
        toks = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError,
            UnicodeDecodeError, ValueError) as exc:
        return None, None, str(exc)
    face = {}
    spans = []
    for idx, tok in enumerate(toks):
        if tok.type == tokenize.COMMENT:
            face.setdefault(tok.start[0], tok.string)
        elif tok.type == tokenize.STRING:
            prev = toks[idx - 1] if idx else None
            # NL covers a module docstring preceded by shebang/coding comment
            # lines; NEWLINE covers a docstring after another statement
            prev_ok = prev is None or prev.type in (
                tokenize.NEWLINE, tokenize.NL, tokenize.INDENT,
                tokenize.DEDENT, tokenize.ENDMARKER)
            # a docstring is a bare-string statement: only same-line trailing
            # comments may sit between the string and its NEWLINE
            nxt_ok = True
            j = idx + 1
            while j < len(toks):
                t2 = toks[j]
                if t2.type == tokenize.COMMENT:
                    j += 1
                    continue
                nxt_ok = t2.type in (tokenize.NEWLINE, tokenize.ENDMARKER)
                break
            if prev_ok and nxt_ok:
                a, b = tok.start[0], tok.end[0]
                spans.append((a, b))
                for ln in range(a, b + 1):
                    if ln <= len(lines):
                        face[ln] = lines[ln - 1]
    segs = [(ln, face[ln]) for ln in sorted(face)]
    return segs, (spans[0] if spans else None), None


def sh_docface(text):
    """Leading comments plus heredoc bodies as (segments, None)."""
    lines = text.splitlines()
    face = {}
    i, n = 0, len(lines)
    while i < n:
        stripped = lines[i].strip()
        if stripped.startswith("#"):
            face[i + 1] = lines[i]
            i += 1
            continue
        m = RE_HEREDOC.search(lines[i])
        i += 1
        if m:
            delim = m.group(1)
            while i < n and lines[i].strip() != delim:
                face[i + 1] = lines[i]
                i += 1
            if i < n:
                i += 1
    segs = [(ln, face[ln]) for ln in sorted(face)]
    return segs, None


def sh_leading_block(text):
    block = []
    for ln in text.splitlines():
        s = ln.strip()
        if s == "" or s.startswith("#"):
            block.append(ln)
        else:
            break
    while block and block[-1].strip() == "":
        block.pop()
    return block


def md_region(text):
    region = []
    for ln in text.splitlines():
        if RE_MD_HEADING2.match(ln):
            break
        region.append(ln)
    while region and region[-1].strip() == "":
        region.pop()
    return region


def v_prose_mask(text):
    """Keep Coq comment bodies (nested (* *) counted); blank vernacular code
    and string literal bodies so the prose face carries comment text only
    (the complement of anchor_guard mask_comments_strings; backslash escapes
    are honored inside strings; newlines are preserved so line numbering
    stays intact)."""
    out = []
    i, n = 0, len(text)
    depth = 0
    while i < n:
        ch = text[i]
        if ch == "\n":
            out.append(ch)
            i += 1
        elif depth > 0:
            if text.startswith("(*", i):
                depth += 1
                out.append("(*")
                i += 2
            elif text.startswith("*)", i):
                depth -= 1
                out.append("*)")
                i += 2
            else:
                out.append(ch)
                i += 1
        elif text.startswith("(*", i):
            depth = 1
            out.append("(*")
            i += 2
        elif ch == '"':
            start = i
            i += 1
            while i < n:
                if text[i] == "\\":
                    i += 2
                elif text[i] == '"':
                    i += 1
                    break
                else:
                    i += 1
            span = text[start:i]
            out.append("".join(c if c == "\n" else " " for c in span))
        else:
            out.append(" ")
            i += 1
    return "".join(out)


def v_docface(text):
    """Coq prose face as (segments, leading block): comment lines only,
    nested-aware; the vernacular body is masked before the line split, so
    segment lines carry comment text with code positions blanked.  The
    leading block runs to the first code line: original blank lines keep
    it open, a line with content but no comment text closes it."""
    masked_lines = v_prose_mask(text).splitlines()
    lines = text.splitlines()
    segs = []
    block = []
    in_lead = True
    for idx in range(min(len(lines), len(masked_lines))):
        if masked_lines[idx].strip():
            segs.append((idx + 1, masked_lines[idx]))
            if in_lead:
                block.append(masked_lines[idx])
        elif lines[idx].strip() == "" and in_lead:
            block.append(masked_lines[idx])
        else:
            in_lead = False
    while block and block[-1].strip() == "":
        block.pop()
    return segs, block


def header_findings(kind, header_text, start_line):
    line_res = FIELD_LINE[kind]
    one_res = FIELD_ONE[kind]
    findings = []
    if header_text is None or not header_text.strip():
        findings.append(mk(start_line, "header", "docstring",
                           DOCSTRING_SUGGEST[kind]))
        for f in FIELDS:
            findings.append(mk(start_line, "header", f,
                               "add the " + f + " field per the annotation standard"))
        return findings
    banner = next((l for l in header_text.splitlines() if l.strip()), "")
    if line_res.match(banner):
        findings.append(mk(start_line, "header", "banner",
                           "start the header with a one-line banner before the field block"))
    for f in FIELDS:
        if not one_res[f].search(header_text):
            findings.append(mk(start_line, "header", f,
                               "add the " + f + " field per the annotation standard"))
    return findings


def jargon_findings(segs, terms):
    findings = []
    for ln, txt in segs:
        work = mask_backticks(txt)
        taken = []
        seen = set()
        for t in terms:  # longest face first, so phrases win over their substrings
            if t.term in seen:
                continue
            if any(x.search(work) for x in t.exempts):
                continue
            hit = None
            for m in t.regex.finditer(work):
                s, e = m.span()
                if any(s < pe and ps < e for ps, pe in taken):
                    continue
                hit = (s, e)
                break
            if hit is not None:
                taken.append(hit)
                seen.add(t.term)
                findings.append(mk(ln, "jargon", t.term, t.suggest))
    return findings


def forbidden_findings(segs):
    findings = []
    for ln, txt in segs:
        seen = set()
        for rx, suggest in FORBIDDEN:
            for m in rx.finditer(txt):
                face = m.group(0)
                if face in seen:
                    continue
                seen.add(face)
                findings.append(mk(ln, "forbidden", face, suggest))
    return findings


def cjk_stats(segs):
    cjk = 0
    total = 0
    first = None
    for ln, txt in segs:
        work = mask_backticks(txt)
        nonws = "".join(work.split())
        total += len(nonws)
        k = len(RE_CJK.findall(nonws))
        cjk += k
        if k and first is None:
            first = ln
    return cjk, total, (first if first is not None else 1)


def load_ai_flavor(map_path):
    """Optional ai-flavor face: load the detector module beside this file and
    the word map; returns (module, word_map).  Missing module or map exits 9;
    an invalid map is an instrument failure (exit 1)."""
    mod_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "ai_flavor.py")
    if not os.path.isfile(mod_path):
        fail("ai-flavor detector module missing: " + mod_path, 9)
    import importlib.util
    spec = importlib.util.spec_from_file_location("rqw_ai_flavor_host", mod_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    try:
        word_map = mod.load_word_map(map_path)
    except OSError as exc:
        fail("ai-flavor map unreadable: " + map_path + " (" + str(exc) + ")", 9)
    except ValueError as exc:
        fail("ai-flavor map invalid: " + str(exc), 1)
    return mod, word_map


def ai_flavor_suggest(face):
    """Suggestion cell for one face: the candidate kinds of the word map,
    with the register-enumerated values where the map lists them."""
    by_kind = {}
    order = []
    for cand in face.get("candidates") or []:
        kind = cand.get("kind") or ""
        if kind not in by_kind:
            by_kind[kind] = []
            order.append(kind)
        value = cand.get("value")
        if isinstance(value, str) and value and len(value) <= 24:
            by_kind[kind].append(value)
    parts = []
    for kind in order:
        vals = by_kind[kind]
        parts.append(kind + (": " + " / ".join(vals) if vals else ""))
    return "; ".join(parts) or "see the word map entry"


def ai_flavor_findings(segs, afmod, word_map, wording_exempt):
    """ai_flavor and em_dash findings over the prose lines: the detector
    runs line by line so findings keep their real line numbers; the wording
    battery is skipped for the map file itself, the em-dash count never is."""
    findings = []
    faces = dict((f["id"], f) for f in word_map["faces"])
    for ln, txt in segs:
        rep = afmod.detect_text(txt, word_map)
        if not wording_exempt:
            seen = set()
            for hit in rep["hits"]:
                fid = hit["face_id"]
                if fid in seen:
                    continue
                seen.add(fid)
                findings.append(mk(ln, "ai_flavor", fid,
                                   ai_flavor_suggest(faces.get(fid, {}))))
        if rep["em_dash_count"]:
            findings.append(mk(ln, "em_dash", "U+2014",
                               "remove the em-dash (register target 0; count on"
                               " this line: %d)" % rep["em_dash_count"]))
    return findings


def scan_file(rel, abspath, kind, terms, threshold, whitelist, map_abspath,
              afmod=None, af_map=None, af_map_abspath=None):
    try:
        with io.open(abspath, "r", encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
        fail("unreadable: " + rel + " (" + str(exc) + ")", 9)
    text = text.lstrip("\ufeff")
    findings = []
    header_text = None
    budget = None
    err = None
    if kind == "py":
        segs, first_doc, err = py_docface(text)
        if err:
            findings.append(mk(1, "parse", "tokenize",
                               "fix the syntax error so the prose face can be scanned"))
        elif first_doc:
            a, b = first_doc
            header_text = "\n".join(text.splitlines()[a - 1:b])
            budget = b - a + 1
    elif kind == "sh":
        segs, _ = sh_docface(text)
        block = sh_leading_block(text)
        if any(l.strip().startswith("#") for l in block):
            header_text = "\n".join(block)
            budget = len(block)
    elif kind == "v":
        segs, block = v_docface(text)
        if any(l.strip() for l in block):
            header_text = "\n".join(block)
            budget = len(block)
    else:
        segs = [(i + 1, l) for i, l in enumerate(text.splitlines())]
        region = md_region(text)
        if region:
            header_text = "\n".join(region)
            budget = len(region)
    findings.extend(header_findings(kind, header_text, 1))
    if budget is not None and budget > HEADER_BUDGET:
        findings.append(mk(1, "budget", "header-budget",
                           "compress the header block to the 30-line budget (banner + doc block)"))
    if abspath != map_abspath:
        findings.extend(jargon_findings(segs, terms))
    if af_map is not None:
        findings.extend(ai_flavor_findings(segs, afmod, af_map,
                                           abspath == af_map_abspath))
    findings.extend(forbidden_findings(segs))
    cjk, total, first = cjk_stats(segs)
    ratio = round(cjk / float(total), 6) if total else 0.0
    if total and ratio > threshold and rel not in whitelist:
        findings.append(mk(first, "cjk", "cjk_ratio",
                           "translate the prose face to English so the CJK share drops below the threshold (%s)" % repr(threshold)))
    findings.sort(key=lambda f: (f["line"], f["kind"], f["term"]))
    return {"path": rel, "kind": kind, "cjk_ratio": ratio,
            "cjk_chars": cjk, "face_chars": total, "findings": findings}


def collect_files(root_abs, skip_abs):
    out = []
    archives = 0
    for dirpath, dirnames, filenames in os.walk(root_abs):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for fn in sorted(filenames):
            ext = os.path.splitext(fn)[1].lower()
            if ext not in FACES:
                continue
            ap = os.path.join(dirpath, fn)
            rel = os.path.relpath(ap, root_abs).replace(os.sep, "/")
            if rel.endswith(".zh.md") or rel.startswith("docs/zh/"):
                archives += 1
                continue
            if ap in skip_abs or fnmatch.fnmatch(rel, "docs/norm-lint-baseline-*.md"):
                # report faces are skipped without a counter: the run creates
                # them itself, so counting them would differ between the
                # first run and its reruns
                continue
            out.append((rel, ap, ext[1:]))
    out.sort(key=lambda t: t[0])
    return out, archives


def resolve_input(p, root_abs, label):
    if os.path.isabs(p):
        if os.path.isfile(p):
            return os.path.abspath(p)
        fail(label + " not found: " + p, 9)
    cands = []
    if root_abs:
        cands.append(os.path.join(root_abs, p))
    cands.append(os.path.join(os.getcwd(), p))
    for c in cands:
        if os.path.isfile(c):
            return os.path.abspath(c)
    fail(label + " not found: " + p + " (tried: " + ", ".join(cands) + ")", 9)


def display_path(p, root_abs):
    ap = os.path.abspath(p)
    if root_abs and (ap == root_abs or ap.startswith(root_abs + os.sep)):
        return os.path.relpath(ap, root_abs).replace(os.sep, "/")
    return ap


def write_output(path, content):
    p = os.path.abspath(path)
    d = os.path.dirname(p)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with io.open(p, "w", encoding="utf-8") as fh:
        fh.write(content)


def render_md(report):
    out = ["# norm-lint report — " + SCHEMA, ""]
    pol = report["policy"]
    s = report["summary"]
    out.append("- mode: " + report["mode"] + " · root: " + report["root"])
    out.append("- jargon map: " + pol["jargon_map"] + " (" + str(pol["active_faces"]) + " active faces)")
    if pol.get("ai_flavor_map"):
        out.append("- ai-flavor map: " + pol["ai_flavor_map"] + " ("
                   + str(pol["ai_flavor_faces"]) + " faces; optional report face on)")
    wl = pol["cjk_whitelist"] or "(none)"
    out.append("- cjk threshold: " + repr(pol["cjk_threshold"]) + " · whitelist: " + wl
               + " (" + str(pol["whitelisted_files"]) + " files) · gate: off (report-only)")
    out.append("- files scanned: " + str(s["files"]) + " · error: " + str(s["error"])
               + " · warn: " + str(s["warn"]) + " · cjk_ratio: " + ("%.6f" % s["cjk_ratio"]))
    out.append("")
    flagged = [f for f in report["files"] if f["findings"]]
    clean = [f["path"] for f in report["files"] if not f["findings"]]
    out.append("## files with findings (" + str(len(flagged)) + ")")
    out.append("")
    for f in flagged:
        out.append("### " + f["path"] + " (" + f["kind"] + ", cjk_ratio "
                   + ("%.6f" % f["cjk_ratio"]) + ")")
        out.append("")
        for fd in f["findings"]:
            level = "warn" if fd["kind"] in ("cjk", "forbidden", "budget") else "error"
            out.append("- L" + str(fd["line"]) + " " + level + " " + fd["kind"] + ": "
                       + fd["term"] + " → " + fd["suggest"])
        out.append("")
    out.append("## clean files (" + str(len(clean)) + ")")
    out.append("")
    for p in clean:
        out.append("- " + p)
    out.append("")
    return "\n".join(out)


def run_scan(args):
    mode = "tree" if args.tree else "file"
    root_abs = None
    if mode == "tree":
        if not os.path.isdir(args.tree):
            fail("tree root not found: " + args.tree, 9)
        root_abs = os.path.abspath(args.tree)
        files_root = root_abs
    else:
        if not os.path.isfile(args.file):
            fail("file not found: " + args.file, 9)
        if os.path.splitext(args.file)[1].lower() not in FACES:
            fail("unsupported face (need .py/.sh/.md/.v): " + args.file, 2)
        files_root = os.path.dirname(os.path.abspath(args.file))
    map_path = resolve_input(args.jargon_map, root_abs, "jargon map")
    terms = load_jargon_map(map_path)
    wl_path = None
    whitelist = set()
    if args.cjk_whitelist:
        wl_path = resolve_input(args.cjk_whitelist, root_abs, "cjk whitelist")
        whitelist = load_whitelist(wl_path)
    afmod = None
    af_map = None
    af_path = None
    if args.ai_flavor_map:
        af_path = resolve_input(args.ai_flavor_map, root_abs, "ai-flavor map")
        afmod, af_map = load_ai_flavor(af_path)
    skip_abs = set()
    for p in (args.json, args.md):
        if p:
            skip_abs.add(os.path.abspath(p))
    if mode == "tree":
        files, archives = collect_files(root_abs, skip_abs)
        rels = [(rel, ap, kind) for rel, ap, kind in files]
    else:
        ap = os.path.abspath(args.file)
        rel = os.path.basename(ap)
        kind = os.path.splitext(rel)[1].lower()[1:]
        archives = 0
        rels = [(rel, ap, kind)]
    records = [scan_file(rel, ap, kind, terms, args.cjk_threshold,
                         whitelist, map_path, afmod, af_map, af_path)
               for rel, ap, kind in rels]
    error = 0
    warn = 0
    sum_cjk = 0
    sum_total = 0
    for rec in records:
        for fd in rec["findings"]:
            if fd["kind"] in ("cjk", "forbidden", "budget"):
                warn += 1
            else:
                error += 1
        sum_cjk += rec["cjk_chars"]
        sum_total += rec["face_chars"]
    agg = round(sum_cjk / float(sum_total), 6) if sum_total else 0.0
    report = {
        "schema": SCHEMA,
        "tool": TOOL,
        "mode": mode,
        "root": root_abs if root_abs else os.path.dirname(os.path.abspath(args.file)),
        "scan": {"archives_skipped": archives},
        "policy": {
            "jargon_map": display_path(map_path, root_abs),
            "active_faces": len(terms),
            "cjk_threshold": args.cjk_threshold,
            "cjk_whitelist": display_path(wl_path, root_abs) if wl_path else None,
            "whitelisted_files": len(whitelist),
            "gate": False,
        },
        "files": records,
        "summary": {"files": len(records), "error": error, "warn": warn,
                    "cjk_ratio": agg},
    }
    if af_map is not None:
        report["policy"]["ai_flavor_map"] = display_path(af_path, root_abs)
        report["policy"]["ai_flavor_faces"] = len(af_map["faces"])
    if args.json:
        write_output(args.json, json.dumps(report, ensure_ascii=False, indent=1,
                                           sort_keys=True) + "\n")
    if args.md:
        write_output(args.md, render_md(report))
    print("norm-lint " + SCHEMA + ": files=" + str(len(records))
          + " error=" + str(error) + " warn=" + str(warn)
          + " cjk_ratio=" + ("%.6f" % agg)
          + " (report-only: findings are data)")
    if args.json:
        print("json: " + os.path.abspath(args.json))
    if args.md:
        print("md: " + os.path.abspath(args.md))
    return 0


SELFTEST_MAP = """# fixture jargon map (selftest)

| 黑话 (jargon face) | 标准 (standard expression) | 语境注记 (context note) | exempt |
|---|---|---|---|
| 落盘 | persist to file | JARGON base row | |
| red | failing (test-suite state) | task example | red/green |
| wave | release | card face | |
"""

V1 = '''"""v1_jargon: jargon-hit vector.

Purpose.  Fixture carrying a known jargon term in a comment line.
Interface.  None (fixture).
Dependencies.  None.
Evidence.  Selftest vector 1.
Exit-codes.  0.
"""
# 落盘 here
x = 1
'''

V2 = '''"""v2_fields: field-missing vector.

Purpose.  Fixture missing four of the five fields on purpose.
"""
x = 1
'''

V3 = '''"""v3_substring: exemption vector.

Purpose.  Fixture proving substring and technical-usage exemptions.
Interface.  None (fixture).
Dependencies.  None.
Evidence.  Selftest vector 3.
Exit-codes.  0.
"""
# reduced and predicted and shared stay untouched
# the counting form 0red stays untouched
# the paired form red/green stays untouched
# cited identifiers `red_dispatch` and `wave` stay untouched
# but the suite went red today
'''

V4 = '''"""v4_whitelist: cjk-exemption vector.

Purpose.  Fixture carrying one Chinese comment line.
Interface.  None (fixture).
Dependencies.  None.
Evidence.  Selftest vector 4.
Exit-codes.  0.
"""
# 中文注释一行
x = 1
'''

V5_PY = '''"""v5_clean_py: clean vector.

Purpose.  Fixture proving a compliant python file returns zero findings.
Interface.  None (fixture).
Dependencies.  None.
Evidence.  Selftest vector 5.
Exit-codes.  0.
"""
# the reason this holds is the invariant on the loop counter
y = 2
'''

V5_SH = '''#!/bin/sh
# v5_clean_sh: clean vector.
#
# Purpose.  Fixture proving a compliant shell file returns zero findings.
# Interface.  None (fixture).
# Dependencies.  None.
# Evidence.  Selftest vector 5.
# Exit-codes.  0.
exit 0
'''

V5_MD = '''# v5_clean_md — clean vector.

Purpose.  Fixture proving a compliant markdown face returns zero findings.

Interface.  None (fixture).

Dependencies.  None.

Evidence.  Selftest vector 5.

Exit-codes.  0.

## Body

Plain body text.
'''

V6_V = '''(* v6_coq_face: jargon-hit vector.
Purpose.  Fixture proving the Coq comment face carries the prose scan.
Interface.  None (fixture).
Dependencies.  None.
Evidence.  Selftest vector 6.
Exit-codes.  0.
*)
(* the change shall not be red by default *)
Lemma red : True.
Proof. exact I. Qed.
'''


def write_text(path, content):
    with io.open(path, "w", encoding="utf-8") as fh:
        fh.write(content)


def run_selftest():
    tmp = tempfile.mkdtemp(prefix="norm_lint_selftest_")
    results = []

    def check(name, ok, detail):
        results.append((name, bool(ok), detail))

    try:
        docs = os.path.join(tmp, "docs")
        os.makedirs(docs)
        map_path = os.path.join(docs, "jargon-to-standard-mapping-v1.md")
        write_text(map_path, SELFTEST_MAP)
        terms = load_jargon_map(map_path)
        names = sorted(t.term for t in terms)
        check("map-load", len(terms) == 3 and names == ["red", "wave", "落盘"],
              "active faces: " + ", ".join(names))

        # vector 1: jargon hit with the replacement suggestion
        p1 = os.path.join(tmp, "v1_jargon.py")
        write_text(p1, V1)
        r1 = scan_file("v1_jargon.py", p1, "py", terms, 0.0, set(), map_path)
        j1 = [f for f in r1["findings"] if f["kind"] == "jargon"]
        h1 = [f for f in r1["findings"] if f["kind"] == "header"]
        want_line = V1.splitlines().index("# 落盘 here") + 1
        check("jargon-hit",
              len(j1) == 1 and j1[0]["term"] == "落盘"
              and j1[0]["suggest"] == "persist to file" and j1[0]["line"] == want_line
              and not h1,
              "jargon findings: " + json.dumps(j1, ensure_ascii=False)
              + "; header findings: " + str(len(h1)))

        # vector 2: header fields missing
        p2 = os.path.join(tmp, "v2_fields.py")
        write_text(p2, V2)
        r2 = scan_file("v2_fields.py", p2, "py", terms, 0.0, set(), map_path)
        h2 = [f for f in r2["findings"] if f["kind"] == "header"]
        want = sorted(["Interface.", "Dependencies.", "Evidence.", "Exit-codes."])
        check("fields-missing",
              sorted(f["term"] for f in h2) == want
              and all(f["line"] == 1 for f in h2),
              "header terms: " + ", ".join(sorted(f["term"] for f in h2)))

        # vector 3: substring and technical-usage exemption
        p3 = os.path.join(tmp, "v3_substring.py")
        write_text(p3, V3)
        r3 = scan_file("v3_substring.py", p3, "py", terms, 0.0, set(), map_path)
        j3 = [f for f in r3["findings"] if f["kind"] == "jargon"]
        want_line = V3.splitlines().index("# but the suite went red today") + 1
        check("substring-exemption",
              len(j3) == 1 and j3[0]["term"] == "red" and j3[0]["line"] == want_line,
              "jargon findings: " + json.dumps(j3, ensure_ascii=False))

        # vector 4: whitelist exemption of the CJK check
        p4 = os.path.join(tmp, "v4_whitelist.py")
        write_text(p4, V4)
        r4a = scan_file("v4_whitelist.py", p4, "py", terms, 0.001, set(), map_path)
        r4b = scan_file("v4_whitelist.py", p4, "py", terms, 0.001,
                        {"v4_whitelist.py"}, map_path)
        c4a = [f for f in r4a["findings"] if f["kind"] == "cjk"]
        c4b = [f for f in r4b["findings"] if f["kind"] == "cjk"]
        check("whitelist-exemption",
              len(c4a) == 1 and not c4b and r4a["cjk_ratio"] > 0.001,
              "unwhitelisted cjk findings: " + str(len(c4a))
              + "; whitelisted: " + str(len(c4b))
              + "; ratio: " + repr(r4a["cjk_ratio"]))

        # vector 5: compliant english file triple returns zero findings
        p5py = os.path.join(tmp, "v5_clean_py.py")
        p5sh = os.path.join(tmp, "v5_clean_sh.sh")
        p5md = os.path.join(tmp, "v5_clean_md.md")
        write_text(p5py, V5_PY)
        write_text(p5sh, V5_SH)
        write_text(p5md, V5_MD)
        r5py = scan_file("v5_clean_py.py", p5py, "py", terms, 0.0, set(), map_path)
        r5sh = scan_file("v5_clean_sh.sh", p5sh, "sh", terms, 0.0, set(), map_path)
        r5md = scan_file("v5_clean_md.md", p5md, "md", terms, 0.0, set(), map_path)
        all5 = r5py["findings"] + r5sh["findings"] + r5md["findings"]
        check("english-clean",
              not all5,
              "combined findings: " + json.dumps(all5, ensure_ascii=False))

        # vector 6: the Coq comment face carries the prose scan; the
        # vernacular body stays out of it (the code identifier on the
        # Lemma line shares the jargon term and must not fire)
        p6 = os.path.join(tmp, "v6_coq_face.v")
        write_text(p6, V6_V)
        r6 = scan_file("v6_coq_face.v", p6, "v", terms, 0.0, set(), map_path)
        j6 = [f for f in r6["findings"] if f["kind"] == "jargon"]
        other6 = [f for f in r6["findings"] if f["kind"] != "jargon"]
        want_line6 = V6_V.splitlines().index(
            "(* the change shall not be red by default *)") + 1
        check("coq-comment-face",
              len(j6) == 1 and j6[0]["term"] == "red"
              and j6[0]["line"] == want_line6 and not other6,
              "jargon findings: " + json.dumps(j6, ensure_ascii=False)
              + "; non-jargon findings: " + str(len(other6)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    ok_all = all(ok for _, ok, _ in results)
    for name, ok, detail in results:
        print(("PASS " if ok else "FAIL ") + name + " — " + detail)
    if not ok_all:
        sys.stderr.write(TOOL + ": selftest red\n")
        return 1
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog=TOOL,
        description="annotation-face normalization lint (report-only first form)")
    group = ap.add_mutually_exclusive_group()
    group.add_argument("--tree", metavar="DIR",
                       help="scan DIR recursively for .py/.sh/.md/.v faces")
    group.add_argument("--file", metavar="PATH", help="lint one face file")
    ap.add_argument("--jargon-map", default=DEFAULT_JARGON_MAP,
                    help="jargon-to-standard mapping table")
    ap.add_argument("--cjk-threshold", type=float, default=0.0,
                    help="CJK share limit; default 0.0 (zero-CJK end state)")
    ap.add_argument("--cjk-whitelist", metavar="P",
                    help="tree-relative paths exempt from the CJK check")
    ap.add_argument("--json", metavar="P", help="write the rocqwash-norm-lint/1 report there")
    ap.add_argument("--ai-flavor-map", dest="ai_flavor_map", metavar="P",
                    default=None,
                    help="optional ai-flavor report face: word map path loaded"
                         " through tools/ai_flavor.py; adds ai_flavor and"
                         " em_dash findings (data, error level)")
    ap.add_argument("--md", metavar="P", help="write the human-readable report there")
    ap.add_argument("--selftest", action="store_true",
                    help="run the six selftest vectors on temporary fixtures")
    args = ap.parse_args(argv)
    if args.selftest:
        if args.tree or args.file or args.json or args.md or args.cjk_whitelist:
            fail("--selftest runs standalone; combine it with no scan flags", 2)
        return run_selftest()
    if not args.tree and not args.file:
        ap.error("one of the arguments --tree --file is required")
    if args.tree and args.file:
        ap.error("--tree and --file are mutually exclusive")
    if args.cjk_threshold < 0:
        fail("--cjk-threshold must be non-negative", 2)
    return run_scan(args)


if __name__ == "__main__":
    sys.exit(main())
