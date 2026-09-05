#!/usr/bin/env python3
"""compiler — C1 made callable (Codex §3.1-3.6), the executable
compiler.

What this module enforces, exactly as the codex states it:

  §3.1  the constitutional block, byte-for-byte (extracted from the
        held codex at import, cross-checked against the attested
        carriers — see codex.py);
  §3.2  the five compiled phases, each with EQUATION / OUTPUT /
        CONTEXT IN / CONTEXT OUT / DECODING / CORRUPTION / LENSES
        (the §3.2 source lines, parsed from the held extraction);
  §3.3  the adaptive context chain (verbatim, carried on every
        emission);
  §3.4  the thirteen decoder rules in checkable form — R1..R13, the
        source's own numbering, each enforced as a check with its
        verbatim citation;
  §3.5  the validation protocol — syntax (6), semantic (6), drift (6)
        — applied to ANY produced surface, plus Appendix D §D.12's
        addressing checks (syntax 5 · semantic 5 · drift 5) and the
        two HC checks below;
  §3.6  the surface emission: the constitutional block exact, the
        active phase's compiled form WITH its decoding operation, the
        adaptive context chain, the decoder rules, and resolved
        symbols for every symbol used — emitted against the attested
        ``parse_surface`` contract, so the engine's surfaces remain
        parseable by the attested ``surface_contract.py``.  The
        Appendix-D jacket (addressing) rides OUTSIDE the surface
        block, visibly separate (D14's own rule).

The load-bearing refusal (C7): HC-1 ("a machine click is never a
verdict") and HC-2 (whether the ∞0′ question is more alive than the X
it came from) are PERMANENTLY INCONCLUSIVE — no code path emits any
authenticity verdict, no write path produces ``state: attested``, and
no non-null attestation reference exists anywhere in this artifact (the
engine neither reads nor writes the ledger — H-META-4).  A decode that
claims to have reached ∞0 is corruption L3, reported as such, never as
arrival.

Deterministic, stdlib only, no LLM, no network, no wall clock.  Every
check's verdict is a pure function of its inputs; the verifier
recomputes each one independently.
"""

from __future__ import annotations

import ast
import os
import re

from codex import (APPD_D12_LINES, APPD_D14_HEADER, APPD_D14_LINES,
                   APPD_D8_LINES, APPD_START_LINE, BLOCK_LINES,
                   COMPILED_SECTIONS, CONTEXT_CHAIN_LINES, CONTEXT_IN,
                   COURSE, CREATIVE_LINE, DECODING_OPS, DESK_GATES,
                   EQUATION_FORMS, LENSES, OUTPUT_SYMBOLS, PHASES,
                   PHASE_SLOTS, PHASE_SYMBOLS, PHASE_TRACE, RULE_LINES,
                   SURFACE_CONTRACT, SYMBOL_ROWS, SYMBOL_TABLE,
                   SYMBOL_ALIASES, SYMBOL_VOCABULARY, VALIDATION_LINES,
                   V_EQ_AXIS, parse_surface, seat_address)
from corruption import (CODE_FAILURES, CODE_NAMES, CODES, classify,
                        scan_engine_sources)
from decoder import (PRODUCES, REQUIRED_CONTEXT, DecoderError, decode)

__all__ = [
    "CONSTITUTIONAL_BLOCK",
    "COMPILED",
    "CONTEXT_CHAIN_TEXT",
    "RULES",
    "render_surface",
    "render_jacket",
    "emit",
    "compile_artifact",
    "compile_cycle",
    "validate",
    "validate_surface_text",
    "aggregate",
    "VALIDATION_ORDER",
    "CHECK_META",
]

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# §3.1 / §3.2 / §3.3 / §3.4 — the compiler's source data.
# ---------------------------------------------------------------------------

# The constitutional block, byte-for-byte (§3.1, from the held codex).
CONSTITUTIONAL_BLOCK = "\n".join(BLOCK_LINES)

# The five compiled phases (§3.2): EQUATION / OUTPUT / CONTEXT IN /
# CONTEXT OUT / DECODING / CORRUPTION / LENSES — §3.2's own lines.
# ``emission_equation`` is the enumerated §3.1 constitutional form the
# surface carries (for S/G/Q/P identical to the §3.2 line; for V the
# declared ∩/⋂ axis difference — see V_EQ_AXIS, H-META-2).
COMPILED = {}
for _letter in COURSE:
    _section = COMPILED_SECTIONS[_letter]
    COMPILED[_letter] = {
        "equation": _section["equation"],
        "emission_equation": EQUATION_FORMS[_letter][0]["form"],
        "output": _section["output"],
        "context_in": _section["context_in"],
        "context_out": _section["context_out"],
        "decoding": tuple(DECODING_OPS[_letter]),
        "corruption": tuple(_section["corruption"]),
        "lenses": tuple(_section["lenses"]),
    }

# Import-time cross-checks of the compiled-phase data against the
# attested carriers — fail closed on any drift (lens 2).
for _letter in COURSE:
    if COMPILED[_letter]["output"] != PHASES[_letter]["output"]:
        raise ImportError(
            "compiler: §3.2's %s OUTPUT drifted from the attested table"
            % _letter)
    if COMPILED[_letter]["context_in"] != PHASES[_letter]["context_in"]:
        raise ImportError(
            "compiler: §3.2's %s CONTEXT IN drifted from the attested table"
            % _letter)
    if COMPILED[_letter]["context_out"] != PHASES[_letter]["context_out"]:
        raise ImportError(
            "compiler: §3.2's %s CONTEXT OUT drifted from the attested table"
            % _letter)
assert V_EQ_AXIS["section_3_1"]["form"] == BLOCK_LINES[7], (
    "the recorded §3.1 V form drifted from the held block")
assert V_EQ_AXIS["section_3_2"]["form"] == COMPILED["V"]["equation"], (
    "the recorded §3.2 V form drifted from the held compiled phase")

# The emission's cycle trace (§1.7 creative line positions mapped to the
# actual content as it forms, R5).  S/G/Q/P carry the attested template;
# V maps exactly the two creative-line positions V forms — B and ∞0′.
# B'' is NOT a creative-line position: it is the artifact, recorded by
# the formation trail (R6/R7), never a trace position.  The compact
# spellings φ⋂Ω / ∞0' are the codex's own §3.3 output forms — accepted
# as the source's spellings of the φ / ∞0′ positions, enumerated, never
# folded (H-META-2).
TRACE_TABLE = {
    letter: tuple(PHASE_TRACE[letter]) for letter in ("S", "G", "Q", "P")
}
TRACE_TABLE["V"] = (("B", "B"), ("∞0'", "∞0'"))
COMPACT_POSITIONS = {"φ⋂Ω": "φ", "∞0'": "∞0′"}

# The §3.3 adaptive context chain, verbatim.
CONTEXT_CHAIN_TEXT = "\n".join(CONTEXT_CHAIN_LINES)

# The thirteen decoder rules, checkable (§3.4) — the source's own
# numbering, carried verbatim, enforced as the R1..R13 checks below.
RULES = dict(RULE_LINES)

# ---------------------------------------------------------------------------
# The validation protocol — the check table.  Appendix D §D.12 (15),
# Codex §3.5 (18), Codex §3.4 R1-R13 (13), and the two HC checks (2) —
# 48 items, every one re-emitted, an undecidable item reads INCONCLUSIVE
# with a reason, never clean (lens 6).
# ---------------------------------------------------------------------------

_AD_SYN = [line[2:] for line in APPD_D12_LINES["Syntax check"]]
_AD_SEM = [line[2:] for line in APPD_D12_LINES["Semantic check"]]
_AD_DRF = [line[2:] for line in APPD_D12_LINES["Drift check"]]
_CX_SYN = [line[2:] for line in VALIDATION_LINES["Syntax check"]]
_CX_SEM = [line[2:] for line in VALIDATION_LINES["Semantic check"]]
_CX_DRF = [line[2:] for line in VALIDATION_LINES["Drift check"]]

CHECK_META = {}
for _i in range(1, 6):
    CHECK_META["AD-SYN-%d" % _i] = {
        "source": "Appendix D §D.12 (syntax)", "citation": _AD_SYN[_i - 1],
        "scope": "cell", "derived": False}
    CHECK_META["AD-SEM-%d" % _i] = {
        "source": "Appendix D §D.12 (semantic)", "citation": _AD_SEM[_i - 1],
        "scope": "cell", "derived": False}
    CHECK_META["AD-DRF-%d" % _i] = {
        "source": "Appendix D §D.12 (drift)", "citation": _AD_DRF[_i - 1],
        "scope": "static", "derived": False}
for _i in range(1, 7):
    CHECK_META["CX-SYN-%d" % _i] = {
        "source": "Codex §3.5 (syntax)", "citation": _CX_SYN[_i - 1],
        "scope": "cell", "derived": False}
    CHECK_META["CX-SEM-%d" % _i] = {
        "source": "Codex §3.5 (semantic)", "citation": _CX_SEM[_i - 1],
        "scope": "artifact", "derived": False}
    CHECK_META["CX-DRF-%d" % _i] = {
        "source": "Codex §3.5 (drift)", "citation": _CX_DRF[_i - 1],
        "scope": "static", "derived": False}
for _n in range(1, 14):
    CHECK_META["R%d" % _n] = {
        "source": "Codex §3.4 R%d" % _n,
        "citation": RULES["R%d" % _n], "scope": "artifact",
        "derived": False}
CHECK_META["HC-1"] = {
    "source": "commission C7 + his decision (K3)",
    "citation": ("a machine click is never a verdict — whether a decode "
                 "is authentic is the human's click.  The engine checks "
                 "that the slots are filled and referenced, never that "
                 "the decode is true."),
    "scope": "artifact", "derived": True}
CHECK_META["HC-2"] = {
    "source": "commission C7 + Codex §2.5 success criterion",
    "citation": ("Codex §2.5: \"The decoding succeeds when B'' carries α "
                 "faithfully AND ∞0' contains a question that is more "
                 "alive than X was.\" — whether this ∞0′ question is "
                 "more alive than the X it came from is the human's "
                 "click; the engine checks that both slots are filled "
                 "and referenced, never that one is more alive."),
    "scope": "artifact", "derived": True}

VALIDATION_ORDER = (
    tuple("AD-SYN-%d" % i for i in range(1, 6))
    + tuple("AD-SEM-%d" % i for i in range(1, 6))
    + tuple("AD-DRF-%d" % i for i in range(1, 6))
    + tuple("CX-SYN-%d" % i for i in range(1, 7))
    + tuple("CX-SEM-%d" % i for i in range(1, 7))
    + tuple("CX-DRF-%d" % i for i in range(1, 7))
    + tuple("R%d" % n for n in range(1, 14))
    + ("HC-1", "HC-2"))
assert set(VALIDATION_ORDER) == set(CHECK_META), (
    "the check table and the evaluation order drifted apart")

# ---------------------------------------------------------------------------
# Static facts about THIS artifact — decided by reading its own source
# (AST), never by text search, never by opinion.
# ---------------------------------------------------------------------------

_FLAG_WORDS = ("address", "word", "zoom", "frame", "daughter", "node",
               "path", "father")
_CAP_NAMES = re.compile(r".*depth.*", re.IGNORECASE)
_GRAMMAR_NEEDLE = "\\[" + "SGQPV" + "\\]"  # built, never a literal
_GRAMMAR = re.compile(_GRAMMAR_NEEDLE)
_ENGINE_MODULES = ("codex.py", "corruption.py", "decoder.py", "compiler.py")


def _cap_scan(tree, path):
    findings = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and _CAP_NAMES.match(node.id):
            findings.append("%s:%d identifier %r" % (path, node.lineno,
                                                     node.id))
        if isinstance(node, ast.Compare) and node.ops and node.comparators:
            if not any(isinstance(op, (ast.Lt, ast.LtE, ast.Gt, ast.GtE))
                       for op in node.ops):
                continue
            if not all(isinstance(c, ast.Constant)
                       and isinstance(c.value, (int, float))
                       for c in node.comparators):
                continue
            left = node.left
            if (isinstance(left, ast.Call)
                    and isinstance(left.func, ast.Name)
                    and left.func.id == "len" and left.args):
                arg = left.args[0]
                name = None
                if isinstance(arg, ast.Name):
                    name = arg.id
                elif isinstance(arg, ast.Attribute):
                    name = arg.attr
                if name and any(flag in name for flag in _FLAG_WORDS):
                    findings.append("%s:%d len(...) compared against a "
                                    "constant" % (path, node.lineno))
    return findings


def _grammar_scan(tree, path):
    findings = []
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "compile" and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
                and _GRAMMAR.search(node.args[0].value)):
            findings.append("%s:%d re.compile(%r)"
                            % (path, node.lineno, node.args[0].value))
    return findings


def _static_facts():
    caps, grammars = [], []
    for name in _ENGINE_MODULES:
        path = os.path.join(HERE, name)
        try:
            with open(path, encoding="utf-8") as handle:
                source = handle.read()
        except OSError:
            continue
        tree = ast.parse(source)
        caps.extend(_cap_scan(tree, name))
        grammars.extend(_grammar_scan(tree, name))
    signed_equations = []
    for letter, entries in EQUATION_FORMS.items():
        for entry in entries:
            if "+" in entry["form"] or "−" in entry["form"]:
                signed_equations.append("%s %r" % (letter, entry["form"]))
    return {
        "sixth_codes": scan_engine_sources(HERE),
        "caps": caps,
        "grammar_reimpls": grammars,
        "signed_equations": signed_equations,
        "phases": tuple(sorted(PHASES)) == tuple(sorted(COURSE))
                  and len(PHASES) == 5,
        "lenses_25": len(LENSES) == 25 and set(LENSES) == {
            a + b for a in "SGQPV" for b in "SGQPV"},
        "vocabulary_resolved": all(
            name in SYMBOL_TABLE or name in SYMBOL_ALIASES
            for name in SYMBOL_VOCABULARY),
    }


_STATIC = _static_facts()

# ---------------------------------------------------------------------------
# §3.6 — the surface emission path.
# ---------------------------------------------------------------------------

_OPEN = SURFACE_CONTRACT["open_marker"]
_CLOSE = SURFACE_CONTRACT["close_marker"]
_REF_SHAPE = re.compile(r"\A[a-z][a-z0-9_.+-]*:[^\s]{1,200}\Z")
_HEX64 = re.compile(r"\A[0-9a-f]{64}\Z")


def render_surface(phase, slot_texts, lens_ids=(), trail_report=None):
    """The §3.6 surface block for one active phase — parseable by the
    attested ``parse_surface`` (contract v1).  Slot texts are the
    caller's deterministic stand-in for the desk; everything else is
    byte-faithful source data (the §3.1 block, the §3.2 compiled form,
    the §3.3 chain in/out, the §1.9 resolved symbols)."""
    if phase not in COURSE:
        raise DecoderError("phase %r is not one of S G Q P V" % (phase,))
    slot_texts = dict(slot_texts or {})
    unknown = set(slot_texts) - set(PHASE_SLOTS[phase])
    if unknown:
        raise DecoderError(
            "slot name(s) outside %s's §3.2 slots: %s — refused, never "
            "emitted" % (phase, ", ".join(sorted(unknown))))
    lines = [_OPEN]
    lines.extend(BLOCK_LINES[:3])
    lines.extend(BLOCK_LINES[3:8])
    lines.extend(BLOCK_LINES[8:])
    compiled = COMPILED[phase]
    lines.append("PHASE: %s" % phase)
    lines.append("EQUATION: %s" % compiled["emission_equation"])
    lines.append("OUTPUT: %s" % compiled["output"])
    lines.append("CONTEXT IN: %s" % compiled["context_in"])
    lines.append("CONTEXT OUT: %s" % compiled["context_out"])
    lines.append("DECODING:")
    for index, op in enumerate(compiled["decoding"], start=1):
        lines.append("%d. %s" % (index, op))
    lines.append("SLOTS:")
    for name in PHASE_SLOTS[phase]:
        if name in slot_texts:
            lines.append("%s: %s" % (name, slot_texts[name]))
    lines.append("COMPILED: %s" % OUTPUT_SYMBOLS[phase])
    lines.append("GATE: %s" % DESK_GATES[phase])
    lines.append("SYMBOLS:")
    for name in PHASE_SYMBOLS[phase]:
        row = SYMBOL_ROWS[name]
        lines.append("%s: %s | %s" % (name, row[0], row[1]))
    if lens_ids:
        lines.append("LENSES:")
        for lid in lens_ids:
            if lid not in LENSES or lid[0] != phase:
                raise DecoderError(
                    "lens %r does not refine phase %s's decoding (R3)"
                    % (lid, phase))
            lens = LENSES[lid]
            lines.append("%s %s through %s: %s — target: %s"
                         % (lid, lens["equation"], lens["quality"],
                            lens["question"], OUTPUT_SYMBOLS[lid[0]]))
    lines.append("TRACE:")
    for position, slot in TRACE_TABLE[phase]:
        lines.append("%s :: %s" % (position, slot))
    if phase == "V" and trail_report:
        lines.append("TRAIL:")
        passes = trail_report.get("passes") or {}
        lines.append("PASS 1: analysis — %s"
                     % passes.get("Pass 1", "undecided"))
        if passes.get("Pass 2"):
            lines.append("PASS 2: composition — %s" % passes["Pass 2"])
        for entry in trail_report.get("entries", ()):
            lines.append("%d. [%s lens] ref: %s"
                         % (entry["index"], entry["lens"],
                            entry["ref"]["ref"]))
    lines.append(_CLOSE)
    return "\n".join(lines) + "\n"


def render_jacket(cell_address, phase=None):
    """The declared Appendix-D jacket — behavioral/interface/domain
    layers, VISIBLY SEPARATE from the decoding (Codex §3.6 / D.14):
    the decoder rules (§3.4), the context chain (§3.3), and the
    addressing layer (4+1 cell, AR5 signless start, the D.8 identity,
    the D.14 block verbatim).  It rides OUTSIDE the ⟦SURFACE v1⟧ block
    and is never parsed by the surface contract."""
    lines = ["⟦DECODER RULES⟧"]
    for n in range(1, 14):
        lines.append(RULES["R%d" % n])
    lines.append("⟦END DECODER RULES⟧")
    lines.append("⟦CONTEXT CHAIN⟧")
    lines.extend(CONTEXT_CHAIN_LINES)
    lines.append("⟦END CONTEXT CHAIN⟧")
    lines.append("⟦APPENDIX-D JACKET⟧")
    lines.append(
        "DERIVED: %s — this layer is the declared Appendix-D jacket, "
        "visibly separate from the decoding (§3.6 / §1.10 "
        "source-authoritative); the divergence log lives in "
        "phase-card.md §D14" % APPD_D14_HEADER)
    lines.append("CELL: %s — 4+1: center S (signless) + corners G Q P V "
                 "(D.1; never 3+1, never 6+1)"
                 % (cell_address if cell_address else "ε"))
    lines.append("SEATS: " + " · ".join(
        "%s@%s" % (letter, seat_address(cell_address, letter))
        for letter in COURSE))
    lines.append("START: %s" % APPD_START_LINE)
    lines.append("IDENTITY: ∞0′ ≡ ∞0 (D.8)")
    lines.extend(APPD_D8_LINES)
    lines.append("BLOCK (D.14, extended — verbatim):")
    lines.extend(APPD_D14_LINES)
    lines.append("⟦END APPENDIX-D JACKET⟧")
    return "\n".join(lines) + "\n"


def emit(phase, slot_texts, lens_ids=(), trail_report=None,
         cell_address="", include_layers=True):
    """The full emitted surface: the §3.6 block plus (default) the
    visible decoder-rules / context-chain / Appendix-D jacket layers."""
    surface = render_surface(phase, slot_texts, lens_ids=lens_ids,
                             trail_report=trail_report)
    if not include_layers:
        return surface
    return surface + "\n" + render_jacket(cell_address, phase)


# ---------------------------------------------------------------------------
# The checks — 48 evaluations, each a deterministic function of the
# context.  Verdicts: PASS | FAIL | INCONCLUSIVE (with a reason —
# anything unobservable is INCONCLUSIVE, never clean).
# ---------------------------------------------------------------------------

def _pass(evidence=None):
    return {"verdict": "PASS", "evidence": list(evidence or []),
            "reason": None}


def _fail(reason, evidence=None):
    return {"verdict": "FAIL", "evidence": list(evidence or []),
            "reason": reason}


def _inc(reason, evidence=None):
    return {"verdict": "INCONCLUSIVE", "evidence": list(evidence or []),
            "reason": reason}


def _parsed(ctx):
    return ctx.get("parsed") or {}


def _decode(ctx):
    return ctx.get("decode") or {}


def _surface(ctx):
    return ctx.get("surface")


def _cell(ctx):
    return ctx.get("cell") or {}


def _cycle(ctx):
    return ctx.get("cycle") or []


def _phase(ctx):
    return ctx.get("phase")


def _static(ctx):
    return ctx.get("static") or _STATIC


def _surface_status(ctx):
    parsed = _parsed(ctx)
    if not parsed:
        return "absent"
    return parsed.get("status") or "absent"


def _is_v(ctx):
    return _phase(ctx) == "V"


def _slot(ctx, *names):
    for name in names:
        slots = _decode(ctx).get("slots") or {}
        if name in slots:
            return name, slots[name]
    return None, None


def _cycle_slot_refs(ctx, symbol):
    """Collect every artifact's decode slot ref for ``symbol`` (cycle
    order)."""
    refs = []
    for artifact in _cycle(ctx):
        slots = ((artifact or {}).get("decode") or {}).get("slots") or {}
        if symbol in slots:
            refs.append(slots[symbol]["ref"])
    return refs


def _producer_of(symbol):
    for letter, symbols in PRODUCES.items():
        if symbol in symbols:
            return letter
    return None


# -- Appendix D §D.12, syntax ---------------------------------------------

def _ev_AD_SYN_1(ctx):
    cell = _cell(ctx)
    arrangement = cell.get("arrangement")
    if not arrangement:
        return _inc("no cell observed — no desk is constituted on the "
                    "box; the engine is fixture-tested against "
                    "deterministic inputs, never a live Pi desk "
                    "(H-META-3, lens 6)")
    desks = sorted(arrangement)
    if len(desks) > 5:
        return _fail("6+1: the observed cell carries %d seat(s) — extra "
                     "seat(s) beyond the one centre and the four corners"
                     % len(desks), desks)
    missing = sorted(set(COURSE) - set(desks))
    if missing:
        return _fail("3+1: the observed cell misses %s"
                     % ", ".join(missing), desks)
    return _pass(desks)


def _ev_AD_SYN_2(ctx):
    parsed = _parsed(ctx)
    status = _surface_status(ctx)
    if status == "absent":
        return _inc("no surface announced — no cell's equations are "
                    "observable")
    if status == "malformed":
        return _fail("the surface is malformed, not lawful",
                     list(parsed.get("errors") or ()))
    equations = parsed.get("equations") or {}
    evidence = []
    for letter in COURSE:
        entry = equations.get(letter) or {}
        if not entry.get("match"):
            if not entry.get("observed_sha256") or not entry.get("len"):
                return _fail("the surface carries no equation line for "
                             "phase %s — the five equations do not all "
                             "appear at the cell" % letter, [letter])
            codepoint = entry.get("first_differing_codepoint")
            return _fail(
                "paraphrased equation for phase %s: the observed bytes "
                "match no enumerated form — first differing codepoint %s "
                "(observed sha256 %s, %d bytes)"
                % (letter, ("U+%04X" % codepoint)
                   if codepoint is not None else "end-of-string",
                   entry.get("observed_sha256"), entry.get("len")),
                [letter, entry.get("observed_sha256"), codepoint])
        evidence.append({"phase": letter, "form_sha256": entry["sha256"]})
    return _pass(evidence)


def _ev_AD_SYN_3(ctx):
    parsed = _parsed(ctx)
    if _surface_status(ctx) != "lawful":
        return _inc("no lawful surface observed — no symbol usage is "
                    "observable")
    rogue = [entry.get("name") for entry in (parsed.get("symbols") or [])
             if not entry.get("in_vocabulary")]
    if rogue:
        return _fail("an L1 symbol was added or renamed: %s"
                     % ", ".join(rogue), rogue)
    return _pass(sorted({entry["name"] for entry in parsed.get("symbols", [])}))


def _ev_AD_SYN_4(ctx):
    static = _static(ctx)
    if static["signed_equations"]:
        return _fail("the artifact's own equation constants carry a sign: "
                     "%s" % ", ".join(static["signed_equations"]),
                     static["signed_equations"])
    status = _surface_status(ctx)
    if status != "lawful":
        return _inc("the engine's equation constants carry no +/− (static "
                    "scan over %s), but no lawful surface was observed — "
                    "the cell half is unobservable"
                    % ", ".join(_ENGINE_MODULES))
    for letter in COURSE:
        entry = ((_parsed(ctx).get("equations") or {}).get(letter) or {})
        if entry.get("first_differing_codepoint") in (ord("+"), ord("-"),
                                                      ord("−")):
            return _fail("the sign +/− appears inside the equation for "
                         "phase %s" % letter, [letter])
    return _pass(["static: no sign in any enumerated equation constant"])


def _ev_AD_SYN_5(ctx):
    parsed = _parsed(ctx)
    if _surface_status(ctx) != "lawful":
        return _inc("no lawful surface observed — no corruption line is "
                    "observable")
    observed = set(parsed.get("corruption_codes") or ())
    if not observed:
        return _fail("the surface announces no corruption line — the "
                     "constitutional block is not exact")
    if observed != set(CODES):
        extra = sorted(observed - set(CODES))
        if extra:
            return _fail("a corruption code beyond L1 L2 L3 L4 V∅ is "
                         "announced: %s" % ", ".join(extra), sorted(observed))
        return _fail("the surface announces fewer than the five codes: %s"
                     % ", ".join(sorted(observed)), sorted(observed))
    return _pass(sorted(CODES))


# -- Appendix D §D.12, semantic --------------------------------------------

def _ev_AD_SEM_1(ctx):
    decode_report = _decode(ctx)
    if not decode_report:
        return _inc("no decode report is observable — no context flow can "
                    "be judged")
    phase = _phase(ctx)
    if phase == "S":
        return _pass(["the start receives no father's output — ∅ (or the "
                      "prior cycle's ∞0′) is the lawful S context (D.8)"])
    context_refs = decode_report.get("context_refs") or {}
    problems = []
    for symbol in REQUIRED_CONTEXT[phase]:
        got = (context_refs.get(symbol) or {}).get("ref")
        father_refs = [ref for ref in _cycle_slot_refs(ctx, symbol)]
        if not father_refs:
            problems.append("no father's output for %s" % symbol)
        elif got not in father_refs:
            problems.append("%s does not carry the father's output "
                            "(k = the frames to climb)" % symbol)
    if problems:
        return _fail("context does not flow father → daughter: %s"
                     % "; ".join(problems), problems)
    return _pass(list(REQUIRED_CONTEXT[phase]))


def _ev_AD_SEM_2(ctx):
    cell = _cell(ctx)
    if not cell or "address" not in cell:
        return _inc("no cell is observed — the sign's vantage is not "
                    "observable")
    seats = cell.get("seats") or {}
    wrong = [letter for letter in COURSE
             if seats.get(letter) != seat_address(cell["address"], letter)]
    if wrong:
        return _fail("the sign is not relative to the vantage: seat(s) %s "
                     "do not derive from the cell's address through the "
                     "declared convention" % ", ".join(wrong), wrong)
    return _pass(["seats derive from %r through %s (D.2 inner-first — "
                  "his word, keep)" % (cell["address"], "XY := X within Y")])


def _ev_AD_SEM_3(ctx):
    phase = _phase(ctx)
    decode_report = _decode(ctx)
    if phase == "V":
        name, ref = _slot(ctx, "∞0'", "∞0′")
        if name is None:
            return _fail("a V closed without ∞0′ — the Completion Rule is "
                         "broken across the cell boundary")
        if not ref.get("len"):
            return _fail("the V's ∞0′ carries no question — a questionless "
                         "return preserves no continuity across cells")
        return _pass([name, ref.get("ref"), ref.get("len")])
    if phase == "S" and decode_report.get("context_kind") == "prior_infinity":
        spelling = decode_report.get("prior_infinity_spelling")
        got = (decode_report.get("context_refs") or {}).get(spelling, {}).get(
            "ref")
        prior_returns = [
            ref for artifact in _cycle(ctx)
            for ref in _cycle_slot_refs(ctx, "∞0'")]
        if not prior_returns:
            return _inc("no prior V artifact is observable in the cycle — "
                        "the ∞0′ ≡ ∞0 bridge cannot be judged")
        if got in prior_returns:
            return _pass(["the next S received the prior V's ∞0′ — ∞0′ ≡ "
                          "∞0 preserves the Completion Rule across cells"])
        return _fail("the next S's ∞0′ reference does not equal the prior "
                     "V's return — ∞0′ ≡ ∞0 is broken across the cell "
                     "boundary", [got, prior_returns])
    return _inc("no cell boundary is crossed on this artifact")


def _ev_AD_SEM_4(ctx):
    surface = _surface(ctx)
    if not isinstance(surface, str):
        return _inc("no emission is observable — the true start cannot be "
                    "judged")
    if surface.count(APPD_START_LINE) != 1:
        return _fail("the emission does not carry the signless true start "
                     "verbatim (D.7 / AR5)")
    for signed in ("+%s" % APPD_START_LINE, "−%s" % APPD_START_LINE):
        if signed in surface:
            return _fail("a signed true start: the start carries a sign — "
                         "the true start is bare · silent · no prefix · no "
                         "sign (AR5)", [signed])
    return _pass([APPD_START_LINE])


def _ev_AD_SEM_5(ctx):
    refs = _cycle_slot_refs(ctx, "X")
    if not refs:
        return _inc("no observed artifact declares an X slot — the shared "
                    "question's reference is not observable")
    distinct = set(refs)
    if len(distinct) > 1:
        return _fail("the shared question is not one ∞0-field: the X "
                     "references disagree across the cycle",
                     [{"ref": ref} for ref in sorted(distinct)])
    return _pass(["one X reference across the observed artifacts"])


# -- Appendix D §D.12, drift -----------------------------------------------

def _ev_AD_DRF_1(ctx):
    static = _static(ctx)
    if static["caps"]:
        return _fail("a hard-coded cap on the address word exists in the "
                     "artifact: %s" % "; ".join(static["caps"]),
                     static["caps"])
    return _pass(["AST scan over %s: no identifier names a depth and no "
                  "len(address-like) is compared against a constant — 25 "
                  "is the first in-zoom, never a cap"
                  % ", ".join(_ENGINE_MODULES)])


def _ev_AD_DRF_2(ctx):
    surface = _surface(ctx)
    if not isinstance(surface, str):
        return _inc("no emission is observable — the derived reading's "
                    "marker cannot be judged")
    if "DERIVED:" not in surface or "Appendix-D jacket" not in surface:
        return _fail("the zoom-out inverse's derived reading is not marked "
                     "on the emission")
    return _pass(["the jacket declares itself the derived Appendix-D "
                  "layer, visibly separate (§1.10 source-authoritative)"])


def _ev_AD_DRF_3(ctx):
    return _ev_CX_DRF_3(ctx)  # mirror by source design (both state the
    # no-omission/reordering rule)


def _ev_AD_DRF_4(ctx):
    return _ev_CX_DRF_4(ctx)  # mirror by source design (both state the
    # five-code rule; the scan is the same scan)


def _ev_AD_DRF_5(ctx):
    return _ev_CX_DRF_6(ctx)  # mirror by source design (both end with the
    # same lens rule)


# -- Codex §3.5, syntax -----------------------------------------------------

def _ev_CX_SYN_1(ctx):
    parsed = _parsed(ctx)
    if _surface_status(ctx) != "lawful":
        return _inc("no lawful surface observed — symbol resolution is not "
                    "observable")
    uncovered = [entry.get("name") for entry in (parsed.get("symbols") or [])
                 if not entry.get("covered")]
    if uncovered:
        return _fail("symbol(s) used but resolving to no §1.9 symbol-table "
                     "row: %s" % ", ".join(uncovered), uncovered)
    return _pass(["every used symbol resolves"])


def _ev_CX_SYN_2(ctx):
    parsed = _parsed(ctx)
    status = _surface_status(ctx)
    if status == "absent":
        return _inc("no surface announced — no phase equation is "
                    "observable")
    if status == "malformed":
        return _fail("the surface is malformed, not lawful",
                     list(parsed.get("errors") or ()))
    active = parsed.get("active") or {}
    equation = active.get("equation") or {}
    if not equation.get("match"):
        codepoint = equation.get("first_differing_codepoint")
        return _fail(
            "the compiled form of phase %s does not carry its exact "
            "equation — the observed bytes match no enumerated form "
            "(first differing codepoint %s, observed sha256 %s)"
            % (active.get("phase"),
               ("U+%04X" % codepoint) if codepoint is not None
               else "end-of-string", equation.get("observed_sha256")),
            [active.get("phase"), equation.get("observed_sha256"), codepoint])
    return _pass([active.get("phase"), equation.get("sha256")])


def _ev_CX_SYN_3(ctx):
    parsed = _parsed(ctx)
    if _surface_status(ctx) != "lawful":
        return _inc("no lawful surface observed — no decoding operation is "
                    "observable")
    decoding = parsed.get("decoding") or {}
    if decoding.get("matches") is not True:
        return _fail("the decoding operation does not follow D1 "
                     "symbol-by-symbol — first mismatch at operation index "
                     "%s" % decoding.get("first_mismatch_index"),
                     [decoding.get("first_mismatch_index")])
    return _pass(["the decoding follows D1 symbol-by-symbol"])


def _ev_CX_SYN_4(ctx):
    static = _static(ctx)
    if static["phases"] and static["lenses_25"]:
        return _pass(["5 phases present, 25 sub-phases available (the "
                      "data tables)"])
    return _fail("the phase or sub-phase tables are incomplete: %d "
                 "phases, %d lenses" % (len(PHASES), len(LENSES)))


def _ev_CX_SYN_5(ctx):
    if set(CODES) == {"L1", "L2", "L3", "L4", "V\u2205"}:
        return _pass(sorted(CODES))
    return _fail("the corruption-code table is not exactly the five codes",
                 sorted(CODES))


def _ev_CX_SYN_6(ctx):
    if not _is_v(ctx):
        return _inc("no V closes on this artifact")
    name, ref = _slot(ctx, "∞0'", "∞0′")
    if name is None:
        return _fail("a V closed without ∞0′ — the completion rule is not "
                     "enforceable at this cell")
    return _pass([name, ref.get("ref"), ref.get("len")])


# -- Codex §3.5, semantic ---------------------------------------------------

def _ev_CX_SEM_1(ctx):
    parsed = _parsed(ctx)
    if _surface_status(ctx) != "lawful":
        return _inc("no lawful surface observed — the adaptive context is "
                    "not observable")
    active = parsed.get("active") or {}
    phase = active.get("phase")
    if phase not in PHASES:
        return _inc("the active phase is not observable")
    declared = active.get("context_in")
    expected = list(CONTEXT_IN[phase])
    if declared != expected:
        return _fail("the decoding of phase %s receives the wrong adaptive "
                     "context: %s (Codex §3.3 expects %s)"
                     % (phase, " + ".join(declared or []),
                        " + ".join(expected)), [phase, declared, expected])
    return _pass(["phase %s receives its §3.3 context" % phase])


def _chain_check(ctx, phase):
    """The shared chain evaluation: every prior output, by producer,
    flows into the daughter's context (S→G→Q→P→V)."""
    decode_report = _decode(ctx)
    if not decode_report:
        return _inc("no decode report is observable — the chain cannot be "
                    "judged")
    if phase == "S":
        return _pass(["S is the chain's start — it receives no prior "
                      "output"])
    context_refs = decode_report.get("context_refs") or {}
    problems = []
    for symbol in REQUIRED_CONTEXT[phase]:
        producer = _producer_of(symbol)
        got = (context_refs.get(symbol) or {}).get("ref")
        father_refs = _cycle_slot_refs(ctx, symbol)
        if not father_refs:
            problems.append({"symbol": symbol, "missing": producer})
        elif got not in father_refs:
            problems.append({"symbol": symbol, "got": got,
                             "fathers": father_refs})
    if problems:
        return _fail("the context chain is broken at this step: %s"
                     % problems, problems)
    return _pass(list(REQUIRED_CONTEXT[phase]))


def _ev_CX_SEM_2(ctx):
    return _chain_check(ctx, _phase(ctx))


def _ev_CX_SEM_3(ctx):
    if not _is_v(ctx):
        return _inc("no V output forms on this artifact")
    names = []
    for name in ("B", "B''", "B″"):
        found, ref = _slot(ctx, name)
        if found is not None:
            names.append((found, ref))
    for name in ("∞0'", "∞0′"):
        found, ref = _slot(ctx, name)
        if found is not None:
            names.append((found, ref))
    if len(names) < 3:
        return _inc("not all of B, B'' and ∞0′ are observable (the "
                    "absence itself is CX-SYN-6's failure) — the "
                    "distinctness of absent slots cannot be judged")
    refs = [ref["ref"] for _name, ref in names]
    if len(set(refs)) < len(refs):
        return _fail("B, B'' and ∞0′ are not three distinct things — two "
                     "slots share one reference", [names])
    distinct_ops = [
        op for op in (DECODING_OPS["V"] or ())
        if op.startswith(("NAME B ", "COMPOSE B'' ", "FORM ∞0' "))]
    if len(distinct_ops) != 3:
        return _fail("B, B'' and ∞0′ lack three distinct decoding steps",
                     distinct_ops)
    return _pass(["three distinct things, three distinct decoding steps",
                  names])


def _ev_CX_SEM_4(ctx):
    parsed = _parsed(ctx)
    if _surface_status(ctx) != "lawful":
        return _inc("no lawful surface observed — no lens is observable")
    lenses = parsed.get("lenses") or []
    if not lenses:
        return _inc("no observed surface carries a lens section")
    for lens in lenses:
        if not lens.get("equation_ok"):
            return _fail("lens %s refines the wrong equation (the lens "
                         "must carry the parent's equation, id[0])"
                         % lens.get("id"), [lens])
    return _pass([lens["id"] for lens in lenses])


def _ev_CX_SEM_5(ctx):
    if not _is_v(ctx):
        return _inc("no crystallization happens on this artifact")
    decode_report = _decode(ctx)
    if decode_report:
        trail = decode_report.get("trail")
        slots = decode_report.get("slots") or {}
        if trail is None:
            if "B''" in slots:
                return _fail("crystallization did not read the formation "
                             "trail — B'' was generated from nothing",
                             ["B'' present, no trail"])
            return _inc("no crystallization is observable — neither B'' "
                        "nor a trail is present")
        passes = trail.get("passes") or {}
        if not (passes.get("Pass 1") and passes.get("Pass 2")):
            return _fail("crystallization did not run its two passes — "
                         "analysis of the trail → composition of the "
                         "artifact (R7)", [passes])
        return _pass([passes, "entries consumed: %s"
                      % trail.get("consumed")])
    parsed = _parsed(ctx)
    if _surface_status(ctx) != "lawful":
        return _inc("the V surface is not observable")
    slots = parsed.get("slots") or {}
    trail = parsed.get("trail")
    if trail is None:
        if "B''" in slots or "B″" in slots:
            return _fail("the V surface carries B'' but no formation-trail "
                         "section — crystallization did not read the trail",
                         ["B'' present, no TRAIL section"])
        return _inc("no formation-trail section is observable")
    passes = trail.get("passes") or {}
    if not (passes.get("Pass 1") and passes.get("Pass 2")):
        return _fail("crystallization did not read the formation trail: "
                     "the two passes (analysis of trail → composition of "
                     "artifact) are not both declared", [passes])
    return _pass([passes])


def _ev_CX_SEM_6(ctx):
    if not _is_v(ctx):
        return _inc("no ∞0′ forms on this artifact")
    name, ref = _slot(ctx, "∞0'", "∞0′")
    if name is None:
        return _inc("no ∞0′ slot is observable (its absence is CX-SYN-6's "
                    "failure)")
    if ref.get("len"):
        return _pass([name, ref.get("ref"), ref.get("len")])
    return _fail("the ∞0′ slot is empty — a questionless ∞0′ is not ∞0′ "
                 "(no question = not ∞0′)", [name, ref.get("ref"), 0])


# -- Codex §3.5, drift ------------------------------------------------------

def _ev_CX_DRF_1(ctx):
    static = _static(ctx)
    if static["vocabulary_resolved"]:
        return _pass(["every vocabulary symbol carries its §1.9 source "
                      "name — nothing was renamed"])
    return _fail("symbol(s) renamed without a source name present")


def _ev_CX_DRF_2(ctx):
    return _pass(["every enumerated equation form's sha recomputes to its "
                  "declared value and the form sits verbatim at its "
                  "declared source line — the symbolic forms are exact, "
                  "never paraphrased, never folded (the import-time "
                  "enumeration in codex.py)"])


def _ev_CX_DRF_3(ctx):
    parsed = _parsed(ctx)
    if _surface_status(ctx) != "lawful":
        return _inc("no lawful surface observed — no decoding sequence is "
                    "observable")
    decoding = parsed.get("decoding") or {}
    if decoding.get("matches") is not True:
        return _fail("a decoding step was omitted or reordered — first "
                     "mismatch at operation index %s"
                     % decoding.get("first_mismatch_index"),
                     [decoding.get("first_mismatch_index")])
    return _pass(["the decoding steps follow D1 order"])


def _ev_CX_DRF_4(ctx):
    static = _static(ctx)
    if static["sixth_codes"]:
        return _fail("a sixth corruption code exists in the artifact: %s"
                     % "; ".join(static["sixth_codes"]), static["sixth_codes"])
    return _pass(["AST constant scan over %s: the only corruption-code "
                  "strings are L1 L2 L3 L4 V∅" % ", ".join(_ENGINE_MODULES)])


def _ev_CX_DRF_5(ctx):
    return _chain_check(ctx, _phase(ctx))


def _ev_CX_DRF_6(ctx):
    parsed = _parsed(ctx)
    if _surface_status(ctx) != "lawful":
        return _inc("no lawful surface observed — no lens question is "
                    "observable")
    lenses = parsed.get("lenses") or []
    if not lenses:
        return _inc("no observed surface carries a lens section")
    for lens in lenses:
        if not lens.get("target_ok"):
            return _fail(
                "lens %s targets %s — the parent output is %s (the "
                "question must target OUTPUT_SYMBOL[id[0]], parent FIRST)"
                % (lens.get("id"), lens.get("target"),
                   OUTPUT_SYMBOLS[lens.get("id")[0]]), [lens])
    return _pass([lens["id"] for lens in lenses])


# -- Codex §3.4, R1-R13 -----------------------------------------------------

def _ev_R1(ctx):
    decode_report = _decode(ctx)
    phase = _phase(ctx)
    if not decode_report or phase not in COURSE:
        if _surface_status(ctx) == "lawful":
            active = _parsed(ctx).get("active") or {}
            if active.get("output_matches") is True:
                return _pass([phase, active.get("output")])
            return _fail("the phase did not decode its one equation to its "
                         "one output: the announced OUTPUT is %r, Codex "
                         "§3.2 expects %r"
                         % (active.get("output"), PHASES.get(phase, {}).get(
                             "output")), [phase, active.get("output")])
        return _inc("no phase decode is observable")
    output_symbol = OUTPUT_SYMBOLS[phase]
    slots = decode_report.get("slots") or {}
    if output_symbol in slots and slots[output_symbol].get("len"):
        return _pass([phase, output_symbol, slots[output_symbol]])
    return _fail("the phase did not decode its one equation to its one "
                 "output: the %s slot is unfilled" % output_symbol,
                 [phase, decode_report.get("slots_missing")])


def _ev_R2(ctx):
    if not _is_v(ctx):
        return _inc("no V output forms on this artifact")
    slots = _decode(ctx).get("slots") or {}
    missing = [name for name in ("B", "B''", "∞0'") if name not in slots]
    if missing:
        return _fail("the three things of R2 are not all formed at V: "
                     "missing %s" % ", ".join(missing), missing)
    return _pass(["B", "B''", "∞0'"])


def _ev_R3(ctx):
    decode_report = _decode(ctx)
    if not decode_report:
        if _surface_status(ctx) == "lawful":
            lenses = _parsed(ctx).get("lenses") or []
            for lens in lenses:
                if not (lens.get("target_ok") and lens.get("quality_ok")):
                    return _fail(
                        "sub-phase lens %s does not refine through a "
                        "borrowed quality while keeping the parent's "
                        "output (target %s)"
                        % (lens.get("id"), lens.get("target")), [lens])
            if lenses:
                return _pass([lens["id"] for lens in lenses])
        return _inc("no sub-phase lens is observable")
    lens_ids = decode_report.get("lens_ids") or []
    if not lens_ids:
        return _inc("no sub-phase lens is observable")
    phase = _phase(ctx)
    output_symbol = OUTPUT_SYMBOLS[phase]
    slots = decode_report.get("slots") or {}
    for lid in lens_ids:
        lens = LENSES[lid]
        if lid[0] != phase or output_symbol not in slots:
            return _fail("sub-phase lens %s does not refine phase %s's "
                         "decoding while keeping the parent's output"
                         % (lid, phase), [lid])
        if lens["quality"] not in ("openness", "pattern", "resonance",
                                   "flow", "benefit"):
            return _fail("lens %s borrows no phase quality" % lid, [lid])
    return _pass(["the lens input serves the output — it never replaces "
                  "it: %s" % ", ".join(lens_ids)])


def _ev_R4(ctx):
    static = _static(ctx)
    if static["lenses_25"]:
        return _pass(["the 25-lens table is complete"])
    return _fail("the 25-lens table is incomplete: %d of 25" % len(LENSES))


def _ev_R5(ctx):
    parsed = _parsed(ctx)
    if _surface_status(ctx) != "lawful":
        return _inc("no lawful surface observed — no cycle trace is "
                    "observable")
    trace = parsed.get("trace")
    if trace is None:
        return _inc("no observed surface carries a cycle trace")
    entries = trace.get("entries") or []
    if not entries:
        return _fail("the cycle trace declares no positions")
    unmapped = [entry.get("position") for entry in entries
                if not entry.get("mapped")]
    if unmapped:
        return _fail("the cycle trace does not map every declared position "
                     "to actual content as it forms: unmapped %s"
                     % ", ".join(unmapped), unmapped)
    positions = [entry.get("position") for entry in entries]
    canonical = [COMPACT_POSITIONS.get(pos, pos) for pos in positions]
    foreign = [pos for pos in canonical if pos not in CREATIVE_LINE]
    if foreign:
        return _fail("the cycle trace carries a position outside the "
                     "creative line: %s" % ", ".join(foreign), foreign)
    indices = [CREATIVE_LINE.index(pos) for pos in canonical]
    if indices != sorted(indices):
        return _fail("the cycle trace reorders the creative line",
                     positions)
    return _pass(["every declared trace position maps to a filled slot, "
                  "in creative-line order"])


def _ev_R6(ctx):
    if not _is_v(ctx):
        return _inc("no V output forms on this artifact")
    decode_report = _decode(ctx)
    if decode_report and decode_report.get("trail"):
        trail = decode_report["trail"]
        return _pass(["the formation trail is an ordered, lens-tagged, "
                      "referenced record — what B'' reads",
                      trail.get("consumed")])
    parsed = _parsed(ctx)
    if _surface_status(ctx) != "lawful":
        return _inc("no formation trail is observable")
    trail = parsed.get("trail")
    if trail is None:
        return _inc("no observed surface carries a formation trail")
    entries = trail.get("entries") or []
    if not entries:
        return _fail("the formation trail is declared but carries no "
                     "ordered record")
    for entry in entries:
        if entry.get("lens") not in LENSES or not entry.get("ref_present"):
            return _fail("a formation-trail record is not lens-tagged or "
                         "carries no reference", [entry])
    return _pass(["every formation-trail record is ordered, lens-tagged "
                  "and referenced"])


def _ev_R7(ctx):
    if not _is_v(ctx):
        parsed = _parsed(ctx)
        if _surface_status(ctx) == "lawful" and parsed.get("trail") is not None:
            return _fail("crystallization is claimed outside V — "
                         "crystallization happens at V only (R7)")
        return _pass(["no crystallization is claimed on this artifact — "
                      "crystallization happens at V only"])
    decode_report = _decode(ctx)
    if decode_report:
        trail = decode_report.get("trail")
        if trail is None:
            return _inc("the V carries no formation-trail report — the two "
                        "passes are not observable")
        passes = trail.get("passes") or {}
        if not (passes.get("Pass 1") and passes.get("Pass 2")):
            return _fail("crystallization at V did not run its two passes "
                         "(analysis of trail → composition of artifact)",
                         [passes])
        return _pass([passes])
    parsed = _parsed(ctx)
    if _surface_status(ctx) != "lawful":
        return _inc("the V surface is not observable")
    trail = parsed.get("trail")
    if trail is None:
        return _inc("the V surface carries no formation-trail section")
    passes = trail.get("passes") or {}
    if not (passes.get("Pass 1") and passes.get("Pass 2")):
        return _fail("crystallization at V did not run its two passes "
                     "(analysis of trail → composition of artifact)",
                     [passes])
    return _pass([passes])


def _ev_R8(ctx):
    if not _is_v(ctx):
        return _inc("no V output forms on this artifact")
    name, ref = _slot(ctx, "∞0'", "∞0′")
    if name is None:
        return _fail("no V without ∞0' — the V closed with no return "
                     "question")
    if not ref.get("len"):
        return _fail("the ∞0′ carries no question — no question = not ∞0′")
    return _pass([name, ref.get("ref"), ref.get("len")])


def _ev_R9(ctx):
    if set(CODES) != {"L1", "L2", "L3", "L4", "V\u2205"}:
        return _fail("the corruption-code table is not exactly the five",
                     sorted(CODES))
    missing = [code for code in CODES
               if code not in CODE_NAMES or code not in CODE_FAILURES]
    if missing:
        return _fail("corruption code(s) name no specific decoding "
                     "failure: %s" % ", ".join(missing), missing)
    return _pass(["each of the five codes names its §2.8 decoding "
                  "failure: %s" % " · ".join(
                      "%s %s" % (code, CODE_NAMES[code]) for code in CODES)])


def _ev_R10(ctx):
    artifact = ctx.get("artifact") or {}
    mark = artifact.get("mark")
    surface = _surface(ctx)
    if not isinstance(surface, str):
        return _inc("no surface is observable — the asymmetry cannot be "
                    "judged")
    if mark is None:
        return _inc("the artifact carries no mark — which side of the "
                    "membrane it speaks from is not observable")
    if mark != "mechanical":
        return _fail("the membrane is crossed: a %r-marked artifact "
                     "speaks from the ∞0 side — H = ∞0 | A = K keeps the "
                     "machine on the K side" % (mark,), [mark])
    if "LAW: H = ∞0 | A = K" not in surface:
        return _fail("the surface does not carry the One Law line exactly")
    return _pass([mark, "LAW: H = ∞0 | A = K"])


def _ev_R11(ctx):
    decode_report = _decode(ctx)
    refs = []
    if decode_report:
        refs.extend(slot["ref"] for slot in
                    (decode_report.get("slots") or {}).values())
        trail = decode_report.get("trail")
        if trail:
            refs.extend(entry["ref"]["ref"]
                        for entry in trail.get("entries", ()))
    elif _surface_status(ctx) == "lawful":
        refs.extend(slot.get("ref", "") for slot in
                    (_parsed(ctx).get("slots") or {}).values())
    if not refs:
        return _inc("no reference is observable — provenance is not "
                    "observable")
    offenders = [ref for ref in refs
                 if not (_REF_SHAPE.match(ref) or _HEX64.match(ref))]
    if offenders:
        return _fail("a reference is not a reference: provenance travels "
                     "with fingerprint hashes, invariant only — scheme-"
                     "prefixed locators or bare 64-hex fingerprints are "
                     "the only lawful shapes", offenders)
    return _pass(["every reference is a fingerprint hash or a scheme-"
                  "prefixed locator — content never travels as provenance"])


def _ev_R12(ctx):
    surface = _surface(ctx)
    if not isinstance(surface, str):
        return _inc("no surface is observable — the centre cannot be "
                    "judged")
    if "CENTER: not a sixth phase — coherence only" not in surface:
        return _fail("the surface does not carry the centre line exactly — "
                     "the centre is coherence only, never a sixth phase")
    if len(PHASES) != 5:
        return _fail("the block declares %d phases — a sixth phase exists"
                     % len(PHASES))
    return _pass(["CENTER: not a sixth phase — coherence only"])


def _ev_R13(ctx):
    static = _static(ctx)
    problems = []
    if static["grammar_reimpls"]:
        problems.append("a second address grammar is compiled in the "
                        "artifact: %s"
                        % "; ".join(static["grammar_reimpls"]))
    if static["caps"]:
        problems.append("a hard-coded cap exists: %s"
                        % "; ".join(static["caps"]))
    if COURSE != ("S", "G", "Q", "P", "V"):
        problems.append("the course is not the data table S G Q P V")
    if problems:
        return _fail("scale by repeating the lawful cell is broken: %s"
                     % " | ".join(problems), problems)
    return _pass(["one decoding-operation table at every scale, no depth "
                  "cap, no root assumption — scale repeats the lawful "
                  "cell, never the syntax (§2.9)"])


# -- the two HC checks (derived) — permanent INCONCLUSIVE -------------------

def _ev_HC_1(ctx):
    reason = ("a machine click is never a verdict — whether a decode is "
              "authentic is the human's click (commission C7 / his "
              "decision, K3).  The engine checks that the slots are "
              "filled and referenced, never that the decode is true.  A "
              "machine that reports resonance has failed the measure.")
    decode_report = _decode(ctx)
    if decode_report:
        evidence = [{"slot": name, "ref": ref["ref"], "len": ref["len"]}
                    for name, ref in
                    sorted((decode_report.get("slots") or {}).items())]
        return _inc(reason, evidence or ["no slot is filled"])
    return _inc(reason, ["no decode is observable on this artifact"])


def _ev_HC_2(ctx):
    reason = ("Codex §2.5: \"The decoding succeeds when B'' carries α "
              "faithfully AND ∞0' contains a question that is more alive "
              "than X was.\" — whether this ∞0′ question is more alive "
              "than the X it came from is the human's click (commission "
              "C7 / his decision, K3).  The engine checks that both "
              "slots are filled and referenced, never that one is more "
              "alive.")
    decode_report = _decode(ctx)
    if _is_v(ctx) and decode_report:
        _, infinity_ref = _slot(ctx, "∞0'", "∞0′")
        _, x_ref = _slot(ctx, "X")
        evidence = [
            {"slot": "∞0'", "ref": infinity_ref["ref"],
             "len": infinity_ref["len"]} if infinity_ref is not None
            else "no ∞0′ slot observed",
            {"slot": "X", "ref": x_ref["ref"], "len": x_ref["len"]}
            if x_ref is not None else "no X slot observed"]
        return _inc(reason, evidence)
    return _inc(reason, ["no V output is observable on this artifact"])


_EVALUATORS = {
    "AD-SYN-1": _ev_AD_SYN_1, "AD-SYN-2": _ev_AD_SYN_2,
    "AD-SYN-3": _ev_AD_SYN_3, "AD-SYN-4": _ev_AD_SYN_4,
    "AD-SYN-5": _ev_AD_SYN_5,
    "AD-SEM-1": _ev_AD_SEM_1, "AD-SEM-2": _ev_AD_SEM_2,
    "AD-SEM-3": _ev_AD_SEM_3, "AD-SEM-4": _ev_AD_SEM_4,
    "AD-SEM-5": _ev_AD_SEM_5,
    "AD-DRF-1": _ev_AD_DRF_1, "AD-DRF-2": _ev_AD_DRF_2,
    "AD-DRF-3": _ev_AD_DRF_3, "AD-DRF-4": _ev_AD_DRF_4,
    "AD-DRF-5": _ev_AD_DRF_5,
    "CX-SYN-1": _ev_CX_SYN_1, "CX-SYN-2": _ev_CX_SYN_2,
    "CX-SYN-3": _ev_CX_SYN_3, "CX-SYN-4": _ev_CX_SYN_4,
    "CX-SYN-5": _ev_CX_SYN_5, "CX-SYN-6": _ev_CX_SYN_6,
    "CX-SEM-1": _ev_CX_SEM_1, "CX-SEM-2": _ev_CX_SEM_2,
    "CX-SEM-3": _ev_CX_SEM_3, "CX-SEM-4": _ev_CX_SEM_4,
    "CX-SEM-5": _ev_CX_SEM_5, "CX-SEM-6": _ev_CX_SEM_6,
    "CX-DRF-1": _ev_CX_DRF_1, "CX-DRF-2": _ev_CX_DRF_2,
    "CX-DRF-3": _ev_CX_DRF_3, "CX-DRF-4": _ev_CX_DRF_4,
    "CX-DRF-5": _ev_CX_DRF_5, "CX-DRF-6": _ev_CX_DRF_6,
    "R1": _ev_R1, "R2": _ev_R2, "R3": _ev_R3, "R4": _ev_R4,
    "R5": _ev_R5, "R6": _ev_R6, "R7": _ev_R7, "R8": _ev_R8,
    "R9": _ev_R9, "R10": _ev_R10, "R11": _ev_R11, "R12": _ev_R12,
    "R13": _ev_R13,
    "HC-1": _ev_HC_1, "HC-2": _ev_HC_2,
}
assert frozenset(_EVALUATORS) == frozenset(CHECK_META), (
    "the evaluator set drifted from the check table")


# ---------------------------------------------------------------------------
# The public surface: compile, validate, aggregate.
# ---------------------------------------------------------------------------

def validate(artifact, cycle=None):
    """Run all 48 checks against one artifact (+ its cycle).  Every item
    is re-emitted — no item is ever silently omitted; an undecidable
    item reads INCONCLUSIVE with a reason, never clean.  The report's
    verdict: FAIL if any item FAILed, INCONCLUSIVE if any item is
    INCONCLUSIVE (HC-1/HC-2 are INCONCLUSIVE by design — a machine can
    never report a fully clean artifact), else PASS."""
    ctx = {
        "artifact": dict(artifact or {}),
        "parsed": (artifact or {}).get("parsed"),
        "decode": (artifact or {}).get("decode"),
        "surface": (artifact or {}).get("surface"),
        "phase": (artifact or {}).get("phase"),
        "cell": (artifact or {}).get("cell"),
        "trail": (artifact or {}).get("trail"),
        "cycle": list(cycle or []),
        "static": _STATIC,
    }
    items = []
    counts = {"PASS": 0, "FAIL": 0, "INCONCLUSIVE": 0}
    for item_id in VALIDATION_ORDER:
        meta = CHECK_META[item_id]
        result = _EVALUATORS[item_id](ctx)
        entry = {
            "id": item_id,
            "source": meta["source"],
            "citation": meta["citation"],
            "scope": meta["scope"],
            "verdict": result["verdict"],
            "evidence": result["evidence"],
        }
        if result["reason"] is not None:
            entry["reason"] = result["reason"]
        if meta["derived"]:
            entry["derived"] = True
        counts[result["verdict"]] += 1
        items.append(entry)
    if counts["FAIL"]:
        verdict = "FAIL"
    elif counts["INCONCLUSIVE"]:
        verdict = "INCONCLUSIVE"
    else:
        verdict = "PASS"
    report = {"verdict": verdict, "counts": counts, "items": items}
    # The corruption taxonomy applies to any produced surface, not only
    # to engine decodes: classify the parsed surface's observable
    # signals (an arrow skipped, unfilled slots, B'' without ∞0′).
    # L3 (a claim) is text-scoped and not observable from references —
    # the decode path's claim register covers it.  The classification is
    # corruption, never an authenticity verdict (C7).
    code, detections = _classify_surface(ctx)
    if code is not None:
        report["corruption"] = code
        report["corruption_detections"] = detections
    return report


def _classify_surface(ctx):
    """The five-code classification of a PARSED surface (references
    only): structural signals — never semantics, never authenticity."""
    parsed = ctx.get("parsed") or {}
    phase = ctx.get("phase")
    if not parsed or parsed.get("status") != "lawful" or phase not in COURSE:
        return None, []
    decoding = parsed.get("decoding") or {}
    evidence = {}
    observed_ops = list(decoding.get("ops") or [])
    expected_receives = sum(
        1 for op in DECODING_OPS[phase] if op.split(" ")[0] == "RECEIVE")
    observed_receives = sum(
        1 for op in observed_ops
        if (op or "").split(" ")[0] == "RECEIVE")
    if decoding.get("matches") is not True and \
            observed_receives < expected_receives:
        evidence["arrow_skipped"] = True
    slots = parsed.get("slots") or {}
    hollow = [name for name, slot in slots.items() if not slot.get("len")]
    hollow += [name for name in PHASE_SLOTS[phase] if name not in slots]
    if phase == "V":
        b2_present = "B''" in slots or "B″" in slots
        infinity = slots.get("∞0'") or slots.get("∞0′")
        if b2_present and (infinity is None or not infinity.get("len")):
            evidence["b2_without_infinity"] = True
            hollow = [name for name in hollow
                      if name not in ("∞0'", "∞0′")]
    evidence["hollow_slots"] = hollow
    return classify(phase, evidence)


def validate_surface_text(text, cycle=None, cell=None):
    """Apply the validation protocol to ANY produced surface — the
    three §3.5 passes included.  Missing/empty/404 content is never
    valid: absent text reads absent (sha256 of empty is
    e3b0c44298fc… — not a surface), and every surface-dependent item
    reads INCONCLUSIVE with that reason, never clean (lens 3)."""
    parsed = parse_surface(text, EQUATION_FORMS) if isinstance(text, str) \
        else {"status": "absent", "version": 1, "errors": ["not text"]}
    artifact = {
        "phase": parsed.get("phase"),
        "mark": None,
        "cell": cell,
        "decode": None,
        "surface": text,
        "parsed": parsed,
        "trail": None,
    }
    return validate(artifact, cycle=cycle)


def aggregate(reports):
    """The cycle/session aggregate: FAIL if any item ever FAILed, PASS
    only if every item decided PASS, otherwise INCONCLUSIVE listing
    every item that never decided — silence is never a pass."""
    reports = list(reports or [])
    finals = {}
    for report in reports:
        for entry in report.get("items", []):
            verdict = entry["verdict"]
            prior = finals.get(entry["id"])
            if prior == "FAIL" or verdict == "FAIL":
                finals[entry["id"]] = "FAIL"
            elif prior == "PASS" or verdict == "PASS":
                finals[entry["id"]] = "PASS"
            else:
                finals.setdefault(entry["id"], "INCONCLUSIVE")
    never_decided = []
    counts = {"PASS": 0, "FAIL": 0, "INCONCLUSIVE": 0}
    for item_id in VALIDATION_ORDER:
        verdict = finals.get(item_id)
        if verdict is None:
            verdict = "INCONCLUSIVE"
            finals[item_id] = verdict
            never_decided.append(item_id)
        elif verdict == "INCONCLUSIVE":
            never_decided.append(item_id)
        counts[verdict] += 1
    if counts["FAIL"]:
        verdict = "FAIL"
    elif counts["INCONCLUSIVE"]:
        verdict = "INCONCLUSIVE"
    else:
        verdict = "PASS"
    return {"verdict": verdict, "counts": counts,
            "never_decided": never_decided, "items": finals}


# ---------------------------------------------------------------------------
# The compiler's callables — decode → compile → emit → validate.
# ---------------------------------------------------------------------------

def compile_artifact(phase, context=None, values=None, trail=None,
                     lenses=None, claims=None, cell_address="",
                     inserted_answer=False, cycle=None):
    """Compile one phase: decode (fail closed on unresolvable context),
    emit the §3.6 surface with the Appendix-D jacket, parse it against
    the attested contract, and run the 48 checks.  Returns the complete
    artifact — mark always "mechanical", never "attested", never any
    attestation reference (C7)."""
    decode_report = decode(
        phase, context=context, values=values, trail=trail, lenses=lenses,
        claims=claims, cell_address=cell_address,
        inserted_answer=inserted_answer)
    slot_texts = {}
    for name, value in (values or {}).items():
        if isinstance(value, str):
            slot_texts[name] = value
        elif isinstance(value, dict) and isinstance(value.get("text"), str):
            slot_texts[name] = value["text"]
    surface_text = emit(
        phase, slot_texts, lens_ids=decode_report.get("lens_ids") or (),
        trail_report=decode_report.get("trail"), cell_address=cell_address)
    parsed = parse_surface(surface_text, EQUATION_FORMS)
    cell = {
        "address": cell_address,
        "arrangement": list(COURSE),
        "seats": {letter: seat_address(cell_address, letter)
                  for letter in COURSE},
    }
    artifact = {
        "phase": phase,
        "mark": "mechanical",
        "cell": cell,
        "decode": decode_report,
        "surface": surface_text,
        "parsed": parsed,
        "trail": decode_report.get("trail"),
    }
    artifact["validation"] = validate(artifact, cycle=cycle)
    artifact["corruption"] = decode_report.get("corruption")
    artifact["corruption_detections"] = \
        decode_report.get("corruption_detections")
    return artifact


def _producer_ref(artifacts, symbol):
    for artifact in artifacts:
        slots = ((artifact or {}).get("decode") or {}).get("slots") or {}
        if symbol in slots:
            return slots[symbol]
    raise DecoderError(
        "the chain is broken: no prior artifact produced %s — the cycle "
        "cannot proceed (fail closed)" % symbol)


def compile_cycle(values_by_phase=None, trail=None, lenses=None,
                  claims=None, cell_address="", prior_infinity=None,
                  prior_cycle=None, inserted_answer=None):
    """Compile the full S→G→Q→P→V cycle: each phase decodes over the
    accumulated prior outputs (§2.6/§3.3), each emission carries the
    block exactly, and the cycle aggregate reports across the whole
    path (lens 2).  ``prior_infinity`` is ("∞0'" | "∞0′", text-or-ref)
    for a continuation cycle — ∞0′ may seed the next cycle as new ∞0
    (D.8)."""
    values_by_phase = dict(values_by_phase or {})
    lenses = dict(lenses or {})
    claims = dict(claims or {})
    inserted_answer = dict(inserted_answer or {})
    artifacts = list(prior_cycle or [])
    fresh = []
    for phase in COURSE:
        context = {}
        if phase == "S":
            if prior_infinity is not None:
                spelling, value = prior_infinity
                if spelling not in ("∞0'", "∞0′"):
                    raise DecoderError(
                        "prior_infinity spelling %r is not one of the two "
                        "source forms — never normalised" % (spelling,))
                context[spelling] = value
        else:
            for symbol in REQUIRED_CONTEXT[phase]:
                context[symbol] = _producer_ref(artifacts + fresh, symbol)
            if phase == "V":
                for artifact in reversed(fresh):
                    slots = ((artifact or {}).get("decode") or {}) \
                        .get("slots") or {}
                    if "φ⋂Ω" in slots:
                        context["φ⋂Ω"] = slots["φ⋂Ω"]
                        break
        artifact = compile_artifact(
            phase, context=context,
            values=values_by_phase.get(phase),
            trail=trail if phase == "V" else None,
            lenses=lenses.get(phase),
            claims=claims.get(phase),
            cell_address=cell_address,
            inserted_answer=bool(inserted_answer.get(phase)),
            cycle=artifacts + fresh)
        fresh.append(artifact)
    cycle_verdict = aggregate([artifact["validation"]
                               for artifact in fresh])
    return {"artifacts": fresh, "validation": cycle_verdict}
