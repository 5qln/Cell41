#!/usr/bin/env python3
"""codex — the held 5QLN codex and its attested carriers, pinned and
cross-checked (meta-implementation, one authoring generation).

This module is the load-bearing seam of the executable codex.  It:

  * pins the two held extractions (``../sources/5qln-codex.txt`` and
    ``../sources/5qln-codex-appendix-D-the-fractal.txt``) by their
    commission shas and refuses (ImportError) on any byte drift —
    fail closed, never substituted (lens 6);
  * loads the attested predecessor carriers BY FILE PATH under sha pins
    — P4a's ``surface.py`` (the one §3.6 contract), P4a's
    ``conformance.py`` (the enumerated equation byte forms + the §1.9
    symbol table + the five corruption codes), P4a's ``walker.py``
    (the course/gate data), P4b's ``grammar.py`` (the seat convention
    and the compiled-phase template) — never copied, never re-authored
    (commission: "you never re-author any predecessor; you import/build
    against them");
  * verifies (read-only) that the attested B0 ledger on the box is the
    pinned bytes — the engine itself never imports or writes the ledger
    (H-META-4: the engine is the language, not the gates);
  * extracts the compiler's byte-critical source lines from the held
    extractions at import time (Codex §3.1 constitutional block, §3.2
    compiled phases' CORRUPTION/LENSES lines, §3.3 context chain, §3.4
    R1–R13, §3.5 validation bullets, Appendix D §D.7/D.8/D.12/D.14),
    every slice anchored and asserted — a drifted extraction is an
    ImportError;
  * proves, at import, that every carrier agrees with every other
    carrier and with the held source bytes (the invariant end-to-end,
    lens 2): equation-form shas recomputed, source locations re-found,
    R1–R13 citations byte-equal, the 25 lens lines reconstructed from
    the attested lens table byte-equal to §3.2, the §1.9 vocabulary
    fully covered, the two attested equation tables byte-identical.

One declared, source-faithful difference is recorded rather than
asserted away (H-META-2): Codex §3.2's V compiled form writes its
EQUATION line with U+22C2 ``⋂`` while §3.1's constitutional block and
§1.3 write U+2229 ``∩``.  Both lines are carried here with their shas;
the enumerated accepted forms (the attested ``EQUATION_FORMS`` table)
remain exactly what the commission's fact block lists — three V forms —
and the EMISSION (compiler.py) uses the §3.1 constitutional form.  No
byte is ever normalised anywhere in this artifact: folding ``⋂→∩`` or
``′→'`` is itself renaming an L1 symbol (D.12 forbids it).

Stdlib only, deterministic, no network, no LLM, no wall clock.
``sys.dont_write_bytecode`` is set before any load so importing the
attested carriers writes no bytecode cache anywhere.
"""

from __future__ import annotations

import hashlib
import importlib.util
import os
import re
import sys

sys.dont_write_bytecode = True

__all__ = [
    "HERE",
    "SOURCES_DIR",
    "PINS",
    "SOURCE_PINS",
    # the attested §3.6 contract (P4a surface.py)
    "SURFACE_CONTRACT",
    "parse_surface",
    "PHASES",
    "DECODING_OPS",
    "LENSES",
    "OUTPUT_SYMBOLS",
    "COMPILED_OUTPUTS",
    "CONTEXT_IN",
    "CONTEXT_OUT",
    "SYMBOL_VOCABULARY",
    "CREATIVE_LINE",
    # the attested enumerated equation byte forms + §1.9 data
    "EQUATION_FORMS",
    "CORRUPTION_CODES",
    "CORRUPTION_FAILURES",
    "SYMBOL_TABLE",
    "SYMBOL_ALIASES",
    # the attested course / seat data
    "COURSE",
    "DESK_GATES",
    "DESK_ADDRESSES",
    "seat_address",
    "WORD_ORDER",
    "ADDRESS_CONVENTION",
    "PHASE_SLOTS",
    "PHASE_TRACE",
    "PHASE_SYMBOLS",
    "SYMBOL_ROWS",
    # the held-source extractions (byte-asserted at import)
    "CODEX_LINES",
    "APPD_LINES",
    "BLOCK_LINES",
    "COMPILED_SECTIONS",
    "CONTEXT_CHAIN_LINES",
    "RULE_LINES",
    "VALIDATION_LINES",
    "APPD_D12_LINES",
    "APPD_D14_LINES",
    "APPD_D14_HEADER",
    "APPD_START_LINE",
    "APPD_D8_LINES",
    "V_EQ_AXIS",
]

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCES_DIR = os.path.normpath(os.path.join(HERE, "..", "sources"))
PRED_DIR = os.path.normpath(os.path.join(HERE, "..", "predecessors"))
P4A_DIR = os.path.join(PRED_DIR, "p4a")
P4B_DIR = os.path.join(PRED_DIR, "p4b")
LEDGER_DIR = os.environ.get(
    "FRACTAL_LEDGER_DIR", "/home/deploy/the-cell/ledger")

# ---------------------------------------------------------------------------
# The pins — every byte this artifact builds against, with its role.
# ---------------------------------------------------------------------------

PINS = {
    "p4a/surface.py": (
        "776ff46393bf81db62841043021c97288e2c1414bec43971d275d1dfbdfac36d",
        "P4a's §3.6 surface contract and parser (the declared shape)"),
    "p4a/conformance.py": (
        "3391b9cac14f56e0d0d7aac954f77864ca84faf8401e36d82d978146e6ef404c",
        "P4a's D.12 check + the enumerated EQUATION_FORMS + SYMBOL_TABLE"),
    "p4a/walker.py": (
        "5889160a15c5bc6949c6cd65726aeb609d4ca54efa3f2702229da5a675a002e9",
        "P4a's read-only walker data (COURSE / DESK_GATES / DESK_ADDRESSES)"),
    "p4b/grammar.py": (
        "d7ab814ca89899ecce5b9fb065588fc185eae08b3debec5573144bfba1e97f63",
        "P4b's desk grammar (seat convention, compiled-phase template, "
        "EQUATION_FORMS)"),
    "b0/fractal_ledger.py": (
        "b291e65967e0d1f98205a9bd612507fa788ea4f9aa99e5d6b8fa5f366895546d",
        "B0 ledger — verified read-only here; the engine never imports or "
        "writes it (H-META-4)"),
}

SOURCE_PINS = {
    "5qln-codex.txt": (
        "e5f0c738d123efc1e412a14da1701a721606275867319e1c68d53b081445c133",
        "the held Codex extraction (page sha ccad26dd…)"),
    "5qln-codex-appendix-D-the-fractal.txt": (
        "6bb28c37cfe6267da1675eac16ac8bbf9679a1d0e5db0f08eb4495d2c22f6bf7",
        "the held Appendix D extraction (page sha a49e9413…)"),
}


def _sha_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def _read_pinned(path, expected, role):
    """Read ``path``'s bytes, refusing (ImportError) when the file is
    missing, unreadable, or drifted from its pin — fail closed, never
    substituted (lens 6)."""
    try:
        with open(path, "rb") as handle:
            raw = handle.read()
    except OSError as exc:
        raise ImportError(
            "codex: the pinned file %s is unreadable (%s) — the attested "
            "%s is INCONCLUSIVE, never substituted" % (path, exc, role)
        ) from None
    actual = _sha_bytes(raw)
    if actual != expected:
        raise ImportError(
            "codex: %s sha256 %s does not match the pinned %s — refusing "
            "to build against a drifted %s" % (path, actual, expected, role))
    return raw


def _load_module(path, module_name, expected_sha, role, path_entries=()):
    """Load one attested predecessor module by file path under
    ``module_name`` after pinning its bytes; ``path_entries`` are
    inserted at sys.path[0] for the load only, so the module's sibling
    imports resolve inside its own round (the B3 seam's convention)."""
    _read_pinned(path, expected_sha, role)
    saved = sys.path[:]
    try:
        for entry in reversed(path_entries):
            sys.path.insert(0, entry)
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise ImportError(
                "codex: cannot build an import spec for %s" % path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path[:] = saved


# ---------------------------------------------------------------------------
# The attested carriers — loaded by path, pinned, never copied.
# ---------------------------------------------------------------------------

if LEDGER_DIR not in sys.path:
    sys.path.insert(0, LEDGER_DIR)

# B0's ledger: verified read-only.  The engine neither imports nor writes
# it — gate semantics live in fractal-engine and the attested B0 ledger,
# never here (H-META-4).  The pin is the contract the check above keeps.
_read_pinned(
    os.path.join(LEDGER_DIR, "fractal_ledger.py"),
    PINS["b0/fractal_ledger.py"][0],
    PINS["b0/fractal_ledger.py"][1])

# P4a's surface.py — the one §3.6 contract.  Its sibling imports are
# none; it loads standalone under the plain name "surface" so P4a's
# conformance (below) resolves its own peer exactly as it does in its
# own round.
_surface = _load_module(
    os.path.join(P4A_DIR, "surface.py"), "surface",
    PINS["p4a/surface.py"][0], PINS["p4a/surface.py"][1], path_entries=(P4A_DIR,))

# P4a's walker.py — the course/gate data tables.
_walker = _load_module(
    os.path.join(P4A_DIR, "walker.py"), "walker",
    PINS["p4a/walker.py"][0], PINS["p4a/walker.py"][1],
    path_entries=(P4A_DIR, LEDGER_DIR))

# P4a's conformance.py — its own "from surface import …" / "from walker
# import …" / "from fractal_ledger import …" resolve through the modules
# bound above and the ledger directory already on sys.path.
_conformance = _load_module(
    os.path.join(P4A_DIR, "conformance.py"), "conformance",
    PINS["p4a/conformance.py"][0], PINS["p4a/conformance.py"][1],
    path_entries=(P4A_DIR, LEDGER_DIR))

# P4b's grammar.py imports "from surface_contract import parse_surface" —
# P4b's own contract seam re-exports exactly P4a's parse_surface (the
# same 776ff463… bytes), so the attested surface module is bound under
# that plain name for the load (the B3 seam's own convention).
sys.modules.setdefault("surface_contract", _surface)
_grammar = _load_module(
    os.path.join(P4B_DIR, "grammar.py"), "grammar",
    PINS["p4b/grammar.py"][0], PINS["p4b/grammar.py"][1],
    path_entries=(P4B_DIR,))

# -- re-exports (the attested contract) -----------------------------------
SURFACE_CONTRACT = _surface.SURFACE_CONTRACT
parse_surface = _surface.parse_surface
PHASES = _surface.PHASES
DECODING_OPS = _surface.DECODING_OPS
LENSES = _surface.LENSES
OUTPUT_SYMBOLS = _surface.OUTPUT_SYMBOLS
COMPILED_OUTPUTS = _surface.COMPILED_OUTPUTS
CONTEXT_IN = _surface.CONTEXT_IN
CONTEXT_OUT = _surface.CONTEXT_OUT
SYMBOL_VOCABULARY = _surface.SYMBOL_VOCABULARY
CREATIVE_LINE = _surface.CREATIVE_LINE

EQUATION_FORMS = _conformance.EQUATION_FORMS
CORRUPTION_CODES = _conformance.CORRUPTION_CODES
CORRUPTION_FAILURES = _conformance.CORRUPTION_FAILURES
SYMBOL_TABLE = _conformance.SYMBOL_TABLE
SYMBOL_ALIASES = _conformance.SYMBOL_ALIASES

COURSE = tuple(_walker.COURSE)
DESK_GATES = dict(_walker.DESK_GATES)
DESK_ADDRESSES = dict(_walker.DESK_ADDRESSES)

seat_address = _grammar.seat_address
WORD_ORDER = _grammar.WORD_ORDER
ADDRESS_CONVENTION = _grammar.ADDRESS_CONVENTION
PHASE_SLOTS = _grammar.PHASE_SLOTS
PHASE_TRACE = _grammar.PHASE_TRACE
PHASE_SYMBOLS = _grammar.PHASE_SYMBOLS
SYMBOL_ROWS = _grammar.SYMBOL_ROWS

# ---------------------------------------------------------------------------
# The held extractions — read once, pinned, split into lines.
# ---------------------------------------------------------------------------

_CODEX_RAW = _read_pinned(
    os.path.join(SOURCES_DIR, "5qln-codex.txt"),
    SOURCE_PINS["5qln-codex.txt"][0], SOURCE_PINS["5qln-codex.txt"][1])
_APPD_RAW = _read_pinned(
    os.path.join(SOURCES_DIR, "5qln-codex-appendix-D-the-fractal.txt"),
    SOURCE_PINS["5qln-codex-appendix-D-the-fractal.txt"][0],
    SOURCE_PINS["5qln-codex-appendix-D-the-fractal.txt"][1])

CODEX_LINES = _CODEX_RAW.decode("utf-8").splitlines()
APPD_LINES = _APPD_RAW.decode("utf-8").splitlines()


def _slice(lines, start, end, what, first_anchor=None, last_anchor=None):
    """Lines ``start..end`` (1-based, inclusive) of a held extraction,
    asserted against content anchors — a drift is an ImportError."""
    segment = lines[start - 1:end]
    if not segment:
        raise ImportError("codex: %s (lines %d-%d) is empty" % (what, start, end))
    if first_anchor is not None and not segment[0].startswith(first_anchor):
        raise ImportError(
            "codex: %s line %d is %r — expected it to open with %r"
            % (what, start, segment[0], first_anchor))
    if last_anchor is not None and not segment[-1].startswith(last_anchor):
        raise ImportError(
            "codex: %s line %d is %r — expected it to end with %r"
            % (what, end, segment[-1], last_anchor))
    return tuple(segment)


# §3.1 — the constitutional block, byte-for-byte (13 lines).
BLOCK_LINES = _slice(
    CODEX_LINES, 254, 266, "Codex §3.1 constitutional block",
    "LAW: H = ∞0 | A = K",
    "CENTER: not a sixth phase — coherence only")

# §3.2 — the five compiled phases: per phase, the EQUATION / OUTPUT /
# CONTEXT IN / CONTEXT OUT / DECODING / CORRUPTION / LENSES lines,
# parsed from the held extraction, every section anchored.
_ANCHORS_32 = {
    "S": (268, 286), "G": (287, 305), "Q": (306, 324),
    "P": (325, 345), "V": (346, 371),
}


def _parse_compiled_sections():
    phases = {}
    for letter, (start, end) in _ANCHORS_32.items():
        block = _slice(CODEX_LINES, start, end,
                       "Codex §3.2 %s block" % letter,
                       "%s — " % letter)
        entry = {"equation": None, "output": None, "context_in": None,
                 "context_out": None, "decoding": [], "corruption": [],
                 "lenses": []}
        section = None
        for line in block:
            if line.startswith("EQUATION: "):
                entry["equation"] = line[len("EQUATION: "):]
                section = None
                continue
            if line.startswith("OUTPUT: "):
                entry["output"] = line[len("OUTPUT: "):]
                section = None
                continue
            if line.startswith("CONTEXT IN: "):
                entry["context_in"] = line[len("CONTEXT IN: "):]
                section = None
                continue
            if line.startswith("CONTEXT OUT: "):
                entry["context_out"] = line[len("CONTEXT OUT: "):]
                section = None
                continue
            if line.startswith("DECODING:"):
                section = "decoding"
                continue
            if line.startswith("CORRUPTION:"):
                entry["corruption"].append(line[len("CORRUPTION:"):].strip())
                section = "corruption"
                continue
            if line.startswith("LENSES:"):
                section = "lenses"
                continue
            if section == "decoding":
                match = re.match(r"\A(\d+)\.\s*(.+)\Z", line.strip())
                if match:
                    entry["decoding"].append(match.group(2).strip())
            elif section == "corruption" and line.strip():
                entry["corruption"].append(line.rstrip())
            elif section == "lenses" and line.strip():
                entry["lenses"].append(line.rstrip())
        phases[letter] = entry
    # the decoded operations must be the attested DECODING_OPS, byte for
    # byte, in order — §3.5 (drift): no decoding step omitted/reordered.
    for letter in COURSE:
        if tuple(phases[letter]["decoding"]) != tuple(DECODING_OPS[letter]):
            raise ImportError(
                "codex: §3.2's %s DECODING lines drifted from the attested "
                "DECODING_OPS table" % letter)
    # the four non-V compiled equations are the §3.1 forms verbatim.
    for letter in ("S", "G", "Q", "P"):
        if phases[letter]["equation"] != EQUATION_FORMS[letter][0]["form"]:
            raise ImportError(
                "codex: §3.2's %s EQUATION drifted from the enumerated "
                "constitutional form" % letter)
    # V wears the ⋂ axis in §3.2 — recorded, never folded (H-META-2).
    return phases


COMPILED_SECTIONS = _parse_compiled_sections()

# The declared V-axis fact: §3.2's V equation line (⋂, U+22C2) vs the
# §3.1 constitutional block line (∩, U+2229).  Both carried with shas;
# neither is ever folded into the other.
V_EQ_AXIS = {
    "section_3_1": {
        "form": BLOCK_LINES[7],
        "sha256": _sha_bytes(BLOCK_LINES[7].encode("utf-8")),
        "intersection": "∩ U+2229",
    },
    "section_3_2": {
        "form": COMPILED_SECTIONS["V"]["equation"],
        "sha256": _sha_bytes(
            COMPILED_SECTIONS["V"]["equation"].encode("utf-8")),
        "intersection": "⋂ U+22C2",
    },
}

# §3.3 — the adaptive context chain (five lines).
CONTEXT_CHAIN_LINES = _slice(
    CODEX_LINES, 373, 377, "Codex §3.3 adaptive context chain",
    "S decodes with: ∅ (or ∞0' from prior cycle) → produces X",
    "V decodes with: X + α + Y + Z + ∇ + A (full trace) → produces "
    "B + B'' + ∞0'")

# §3.4 — the thirteen decoder rules, the source's own numbering.
_RULE_RANGE = _slice(
    CODEX_LINES, 381, 393, "Codex §3.4 R1-R13",
    "R1 Each phase decodes one equation to form one output",
    "R13 Scale by repeating the lawful cell — decoding operations do "
    "not change at scale")
RULE_LINES = {}
for _line in _RULE_RANGE:
    _match = re.match(r"\A(R\d+) (.+)\Z", _line)
    if _match is None:
        raise ImportError(
            "codex: §3.4 line %r is not a numbered decoder rule" % _line)
    RULE_LINES[_match.group(1)] = _line

# §3.5 — the validation protocol: syntax (6) · semantic (6) · drift (6).
def _parse_bullets(lines, start, end, what, headers):
    block = _slice(lines, start, end, what)
    out = {key: [] for key in headers}
    current = None
    for line in block:
        stripped = line.strip()
        if stripped in headers:
            current = stripped
            continue
        if current is not None and stripped.startswith("□"):
            out[current].append(stripped)
    return out


VALIDATION_LINES = _parse_bullets(
    CODEX_LINES, 395, 415, "Codex §3.5 validation protocol",
    ("Syntax check", "Semantic check", "Drift check"))
for _pass, _expected in (("Syntax check", 6), ("Semantic check", 6),
                         ("Drift check", 6)):
    if len(VALIDATION_LINES[_pass]) != _expected:
        raise ImportError(
            "codex: §3.5 %s carries %d bullets, expected %d — the held "
            "extraction drifted" % (_pass, len(VALIDATION_LINES[_pass]),
                                    _expected))

# Appendix D — the addressing layer's held lines.
APPD_D12_LINES = _parse_bullets(
    APPD_LINES, 157, 174, "Appendix D §D.12 validation",
    ("Syntax check", "Semantic check", "Drift check"))
for _pass, _expected in (("Syntax check", 5), ("Semantic check", 5),
                         ("Drift check", 5)):
    if len(APPD_D12_LINES[_pass]) != _expected:
        raise ImportError(
            "codex: Appendix D §D.12 %s carries %d bullets, expected %d — "
            "the held extraction drifted"
            % (_pass, len(APPD_D12_LINES[_pass]), _expected))

APPD_START_LINE = _slice(
    APPD_LINES, 94, 94, "Appendix D §D.7 true start",
    "THE TRUE START: S = ∞0 → ?")[0]

APPD_D8_LINES = _slice(
    APPD_LINES, 102, 117, "Appendix D §D.8 ∞0′ ≡ ∞0",
    "D.8 The ∞0′ ≡ ∞0 Identity",
    "relation to origin is required.")

APPD_D14_HEADER = _slice(
    APPD_LINES, 203, 203, "Appendix D §D.14 header",
    "D.14 The Block (extended — visibly separate)")[0]

APPD_D14_LINES = _slice(
    APPD_LINES, 204, 213, "Appendix D §D.14 block",
    "LAW: H = ∞0 | A = K (membrane at every node)",
    "DOMINATION: geometry + signed path only — decentralized")

# ---------------------------------------------------------------------------
# Import-time cross-checks — one invariant proven across every carrier
# (lens 2: invariant end-to-end, never per call).
# ---------------------------------------------------------------------------


def _fail_cross(what):
    raise ImportError("codex: %s — refusing to run on a drifted contract" % what)


# 1. Every enumerated equation form's sha recomputes to its own table
#    value, and every declared source location carries the form verbatim
#    (the H-META-2 enumeration: source + sha, proven, never folded).
_SOURCE_LINE_FILES = {"5qln-codex.txt": CODEX_LINES,
                      "5qln-codex-appendix-D-the-fractal.txt": APPD_LINES}
for _letter, _entries in EQUATION_FORMS.items():
    for _entry in _entries:
        if _sha_bytes(_entry["form"].encode("utf-8")) != _entry["sha256"]:
            _fail_cross("the enumerated %s form %r does not hash to its "
                        "declared sha" % (_letter, _entry["form"]))
        for _filename, _line_no in _entry["locations"]:
            _lines = _SOURCE_LINE_FILES.get(_filename)
            if _lines is None:
                _fail_cross("equation location names unknown source %r"
                            % _filename)
            if not (0 <= _line_no - 1 < len(_lines)) or \
                    _entry["form"] not in _lines[_line_no - 1]:
                _fail_cross("the enumerated %s form %r is not verbatim at "
                            "%s line %d" % (_letter, _entry["form"],
                                            _filename, _line_no))

# 2. The attested P4b grammar equation table is byte-identical to the
#    attested P4a conformance table (both carry the same enumeration).
for _letter in COURSE:
    _here = {(e["form"], e["sha256"]) for e in EQUATION_FORMS[_letter]}
    _there = {(e["form"], e["sha256"])
              for e in _grammar.EQUATION_FORMS[_letter]}
    if _here != _there:
        _fail_cross("the two attested equation tables disagree on %s" % _letter)

# 3. The §3.1 block's five equation lines are the enumerated
#    constitutional forms (the block is byte-for-byte, C2).
if tuple(BLOCK_LINES[3:8]) != tuple(EQUATION_FORMS[p][0]["form"]
                                   for p in COURSE):
    _fail_cross("the §3.1 block equations are not the enumerated "
                "constitutional forms")

# 4. R1-R13, as extracted from the held codex, are byte-equal to the
#    attested conformance citations (the source's own numbering).
for _n in range(1, 14):
    _rule = "R%d" % _n
    _text = RULE_LINES[_rule].split(" ", 1)[1]
    if _text != _conformance.CHECKS[_rule]["citation"]:
        _fail_cross("%s drifted between the held codex and the attested "
                    "check table" % _rule)

# 5. Every one of the 25 lenses, reconstructed from the attested lens
#    table, appears verbatim among the held §3.2 lens lines.
for _lid, _lens in LENSES.items():
    _expected = "%s %s through %s: %s" % (_lid, _lens["equation"],
                                          _lens["quality"], _lens["question"])
    if _expected not in COMPILED_SECTIONS[_lid[0]]["lenses"]:
        _fail_cross("lens %s reconstructed from the attested table is not "
                    "verbatim in §3.2" % _lid)

# 6. The five corruption codes are exactly the sealed five, and the §1.9
#    vocabulary resolves fully (CX-DRF-1: no symbol renamed without its
#    source name present).
if CORRUPTION_CODES != frozenset(("L1", "L2", "L3", "L4", "V\u2205")):
    _fail_cross("the corruption codes are not exactly L1 L2 L3 L4 V∅")
_unresolved = sorted(
    name for name in SYMBOL_VOCABULARY
    if name not in SYMBOL_TABLE and name not in SYMBOL_ALIASES)
if _unresolved:
    _fail_cross("vocabulary symbol(s) without a §1.9 source name: %s"
                % ", ".join(_unresolved))

# 7. The course and gate data agree across the attested carriers.
if COURSE != tuple(_grammar.COURSE) or DESK_GATES != dict(_grammar.DESK_GATES):
    _fail_cross("the course/gate data drifted between the attested carriers")

# 8. The attested compiled-phase template's equations are the enumerated
#    constitutional forms (what the emission carries).
for _letter in COURSE:
    if _grammar.PHASE[_letter]["equation"] != EQUATION_FORMS[_letter][0]["form"]:
        _fail_cross("P4b's %s template equation is not the enumerated "
                    "constitutional form" % _letter)
