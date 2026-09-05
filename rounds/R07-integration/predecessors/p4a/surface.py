#!/usr/bin/env python3
"""surface — the Codex §3.6 surface contract and its parser (P4a).

A desk's announced surface is parsed against a DECLARED contract derived
from Codex §3.6 Surface Emission Rules, quoted verbatim:

    "Every emitted surface must carry:
     Constitutional block (§3.1) — exact
     The active phase's compiled form WITH decoding operation (§3.2)
     The adaptive context chain (§3.3) — what feeds in, what feeds out
     The decoder rules (§3.4)
     Resolved symbols for every symbol used (§1.9)
     Surfaces may add behavioral, interface, and domain layers — visibly
     separate from the decoding."

The contract is DATA (``SURFACE_CONTRACT``), versioned, in one place — it
is the declared interface P4b's desk bundles will be written against.
``parse_surface`` returns REFERENCES ONLY (§4.7.5, commission P4a C3):
a slot's value leaves the parser as ``sha256`` + byte length, never as
text; a desk's answer text never travels into the trail.  Every verbatim
table in this module is copied from the held source files
(``sources/5qln-codex.txt``) and never re-worded.
"""

from __future__ import annotations

import hashlib
import re

__all__ = [
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
]

# ---------------------------------------------------------------------------
# The contract, as data (declared interface, versioned, in one place).
# ---------------------------------------------------------------------------

SURFACE_CONTRACT = {
    "version": 1,
    "source": (
        "Codex §3.6 Surface Emission Rules (verbatim): \"Every emitted "
        "surface must carry: Constitutional block (§3.1) — exact; The "
        "active phase's compiled form WITH decoding operation (§3.2); The "
        "adaptive context chain (§3.3) — what feeds in, what feeds out; "
        "The decoder rules (§3.4); Resolved symbols for every symbol used "
        "(§1.9). Surfaces may add behavioral, interface, and domain layers "
        "— visibly separate from the decoding.\""),
    "open_marker": "⟦SURFACE v1⟧",
    "close_marker": "⟦END SURFACE⟧",
    # Every section the parser accepts.  A surface missing any required
    # section is "malformed" (structure), never silently lawful.
    "required_sections": (
        "LAW", "CYCLE", "EQUATIONS", "OUTPUTS", "HOLOGRAPHIC",
        "COMPLETION", "CORRUPTION", "CENTER", "PHASE", "EQUATION",
        "OUTPUT", "CONTEXT IN", "CONTEXT OUT", "DECODING", "SLOTS",
        "COMPILED", "GATE", "SYMBOLS",
    ),
    "optional_sections": ("LENSES", "TRACE", "TRAIL"),
    # The five equation byte forms are enumerated in conformance
    # (EQUATION_FORMS, with source + sha256 per form); the parser takes
    # the table as a parameter and never folds, never normalises.
    "equation_table": "conformance.EQUATION_FORMS",
}

# ---------------------------------------------------------------------------
# The five phases, compiled forms verbatim from Codex §3.2 (268-371 of the
# held extraction).  These are the contract's vocabulary — the parser and
# every check compare against them byte for byte.
# ---------------------------------------------------------------------------

PHASES = {
    "S": {
        "equation": "S = ∞0 → ?",
        "output": "X (Validated Spark)",
        "context_in": "∅ (or ∞0' from prior cycle)",
        "context_out": "X",
    },
    "G": {
        "equation": "G = α ≡ {α'}",
        "output": "Y (Validated Pattern)",
        "context_in": "X",
        "context_out": "X + α + Y",
    },
    "Q": {
        "equation": "Q = φ ⋂ Ω",
        "output": "Z (Resonant Key)",
        "context_in": "X + α + Y",
        "context_out": "X + α + Y + φ⋂Ω + Z",
    },
    "P": {
        "equation": "P = δE/δV → ∇",
        "output": "A (Flow)",
        "context_in": "X + α + Y + Z",
        "context_out": "X + α + Y + Z + ∇ + A",
    },
    "V": {
        "equation": "V = (L ⋂ G → B'') → ∞0'",
        "output": "B (Benefit) + B'' (Fractal Seed) + ∞0' (Enriched Return)",
        "context_in": "X + α + Y + Z + ∇ + A (full trace)",
        "context_out": "B + B'' + ∞0' (∞0' may seed next cycle)",
    },
}

# The single output symbol per phase (Codex §3.1 "OUTPUTS: S→X G→Y Q→Z
# P→A V→B+B''+∞0'"; §3.2 compiled outputs).  Used by AD-DRF-5 / CX-DRF-6 /
# R3: a lens targets OUTPUT_SYMBOL[id[0]] — parent FIRST (commission
# P4a §3.7 lesson 2).
OUTPUT_SYMBOLS = {"S": "X", "G": "Y", "Q": "Z", "P": "A", "V": "B"}

# The full compiled output per phase (Codex §3.1 "OUTPUTS: S→X G→Y Q→Z
# P→A V→B+B''+∞0'"): what the gate record compiles (D12 / DC-COMPILE).
COMPILED_OUTPUTS = {
    "S": "X", "G": "Y", "Q": "Z", "P": "A", "V": "B+B''+∞0′",
}

# The adaptive context chain, verbatim Codex §3.3 (373-377): what each
# phase decodes with.
CONTEXT_IN = {
    "S": ["∅"],
    "G": ["X"],
    "Q": ["X", "α", "Y"],
    "P": ["X", "α", "Y", "Z"],
    "V": ["X", "α", "Y", "Z", "∇", "A"],
}
CONTEXT_OUT = {
    "S": ["X"],
    "G": ["X", "α", "Y"],
    "Q": ["X", "α", "Y", "φ⋂Ω", "Z"],
    "P": ["X", "α", "Y", "Z", "∇", "A"],
    "V": ["B", "B''", "∞0'"],
}

# The creative line's positions (Codex §1.7: "∞0 → X → α → Y → φ → Z →
# ∇ → A → B → ∞0′") — the cycle trace maps positions to actual content
# as it forms (R5).
CREATIVE_LINE = ("∞0", "X", "α", "Y", "φ", "Z", "∇", "A", "B", "∞0′")

# The decoding operations, one first-line text per numbered op, verbatim
# from Codex §3.2.  Multi-line ops keep their first line exactly (e.g. V
# op 5 ends with the source's own trailing colon); the two crystallisation
# passes live in the optional TRAIL section, visibly separate.
DECODING_OPS = {
    "S": [
        "HOLD ∞0 — resist closing. Nothing is sought. Nothing is assumed.",
        "RECEIVE → (Emergence) — when something stirs, it is emergence, not generation.",
        "NAME ? — what arrived is named as a question.",
        "VALIDATE X — genuine (from ∞0) not manufactured (from K).",
    ],
    "G": [
        "RECEIVE X — the validated question is the input.",
        "SEEK α — within X, what is the irreducible core? Remove it and X collapses.",
        "TEST ≡ (Identity Preservation) — does α remain unchanged across expressions?",
        "FIND {α'} — where does α echo at other scales? Each echo must be self-similar to α.",
        "VALIDATE Y — α is named, ≡ holds, {α'} confirm across scales.",
    ],
    "Q": [
        "RECEIVE X + α + Y — question and pattern are the input.",
        "HOLD φ (Self-Nature) — what does the inquirer directly perceive about Y?",
        "HOLD Ω (Universal Potential) — what does the larger context reveal about Y?",
        "WATCH FOR ⋂ (Natural Intersection) — not sought. It arrives.",
        "VALIDATE Z — the Resonant Key. What turned the lock. Confirmed, not argued.",
    ],
    "P": [
        "RECEIVE X + α + Y + Z — question, pattern, resonance are the input.",
        "MAP δE — where is energy going? Friction? Resistance? Effort?",
        "MAP δV — where is value appearing? What works without pushing?",
        "COMPUTE δE/δV — the ratio reveals the landscape.",
        "RECEIVE → (Reveals) — the ratio reveals ∇. The gradient is already present.",
        "VALIDATE A — the inquirer can identify where energy wants to go.",
    ],
    "V": [
        "RECEIVE full trace: X + α + Y + φ⋂Ω + Z + ∇ + A",
        "NAME L (Local Actualization) — what crystallized here and now?",
        "NAME G (Global Propagation) — what propagates beyond the local?",
        "FIND ⋂ — where do L and G genuinely meet?",
        "COMPOSE B'' (Fractal Seed) — read the formation trail:",
        "NAME B (Benefit) — the decoded output:",
        "FORM ∞0' — the return question. The question this cycle reveals that could",
    ],
}

# The 25 lenses, verbatim from Codex §3.2 LENSES blocks (281-371): id →
# {equation, quality, question}.  The id's FIRST letter is the parent —
# the phase whose decoding is refined; the second letter is the borrowed
# quality's phase.
LENSES = {
    "SS": {"equation": "∞0→?", "quality": "openness",
           "question": "Is the space truly open, or is ? being forced?"},
    "SG": {"equation": "∞0→?", "quality": "pattern",
           "question": "What structure does this question reveal?"},
    "SQ": {"equation": "∞0→?", "quality": "resonance",
           "question": "Does this question carry body-knowing?"},
    "SP": {"equation": "∞0→?", "quality": "flow",
           "question": "Where is the question's own momentum pulling?"},
    "SV": {"equation": "∞0→?", "quality": "benefit",
           "question": "What gift already lives in the act of asking?"},
    "GS": {"equation": "α≡{α'}", "quality": "openness",
           "question": "What unknown still lives within the pattern?"},
    "GG": {"equation": "α≡{α'}", "quality": "pattern",
           "question": "How does α express at deeper scales?"},
    "GQ": {"equation": "α≡{α'}", "quality": "resonance",
           "question": "Which echoes carry authentic signature vs. resemblance?"},
    "GP": {"equation": "α≡{α'}", "quality": "flow",
           "question": "Where does the pattern want to unfold next?"},
    "GV": {"equation": "α≡{α'}", "quality": "benefit",
           "question": "How is naming α itself already a gift?"},
    "QS": {"equation": "φ⋂Ω", "quality": "openness",
           "question": "Is this resonance real? What doubt tests it?"},
    "QG": {"equation": "φ⋂Ω", "quality": "pattern",
           "question": "Genuine resonance vs. intellectual attraction?"},
    "QQ": {"equation": "φ⋂Ω", "quality": "resonance",
           "question": "Is sensitivity to true pitch sharpening?"},
    "QP": {"equation": "φ⋂Ω", "quality": "flow",
           "question": "Is φ⋂Ω arriving by itself without searching?"},
    "QV": {"equation": "φ⋂Ω", "quality": "benefit",
           "question": "Is the resonance itself regenerative?"},
    "PS": {"equation": "δE/δV→∇", "quality": "openness",
           "question": "Where does energy actually want to go vs. assumption?"},
    "PG": {"equation": "δE/δV→∇", "quality": "pattern",
           "question": "Does flow follow α? Is essence guiding direction?"},
    "PQ": {"equation": "δE/δV→∇", "quality": "resonance",
           "question": "Not just \"works\" but \"works and it's true\"?"},
    "PP": {"equation": "δE/δV→∇", "quality": "flow",
           "question": "Are action and being becoming indistinguishable?"},
    "PV": {"equation": "δE/δV→∇", "quality": "benefit",
           "question": "Is flow creating surplus? Where does freed energy go?"},
    "VS": {"equation": "(L⋂G→B'')→∞0'", "quality": "openness",
           "question": "Is B'' surprising its origin?"},
    "VG": {"equation": "(L⋂G→B'')→∞0'", "quality": "pattern",
           "question": "Does B'' carry α faithfully?"},
    "VQ": {"equation": "(L⋂G→B'')→∞0'", "quality": "resonance",
           "question": "Does the artifact genuinely resonate?"},
    "VP": {"equation": "(L⋂G→B'')→∞0'", "quality": "flow",
           "question": "Can benefit flow naturally via ∇?"},
    "VV": {"equation": "(L⋂G→B'')→∞0'", "quality": "benefit",
           "question": "Is B'' becoming new ∞0? Fruit becoming seed?"},
}

# The symbol vocabulary (Codex §1.9 + the Appendix's U+2032 prime form +
# the compact φ⋂Ω used by §3.3).  A surface that DECLARES a symbol name
# outside this set has added or renamed an L1 symbol (AD-SYN-3).  The two
# intersection glyphs and both primes are all source forms — enumerated,
# never normalised (commission P4a §3.3).
SYMBOL_VOCABULARY = frozenset((
    "H", "∞0", "A", "K", "|", "S", "G", "Q", "P", "V",
    "?", "X", "α", "{α'}", "Y", "φ", "Ω", "Z",
    "δE", "δV", "δE/δV", "∇", "L", "B", "B''", "B″",
    "∞0'", "∞0′", "∞", "→", "≡", "⋂", "∩", "×", ":=", "∈",
    "∅", "φ⋂Ω", "No...without...",
))

_OPEN_MARKER = SURFACE_CONTRACT["open_marker"]
_CLOSE_MARKER = SURFACE_CONTRACT["close_marker"]
_REQUIRED = frozenset(SURFACE_CONTRACT["required_sections"])
_OPTIONAL = frozenset(SURFACE_CONTRACT["optional_sections"])
_SECTIONS = _REQUIRED | _OPTIONAL


def _ref(value):
    """The only shape a slot's bytes may leave this module in: a reference
    (sha256 + byte length) — never the text (§4.7.5)."""
    raw = value.encode("utf-8")
    return {"ref": "sha256:" + hashlib.sha256(raw).hexdigest(),
            "len": len(raw)}


def _sha(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _first_differing_codepoint(observed, candidates):
    """The first codepoint where the observed bytes differ from EVERY
    enumerated form — named as an integer (U+XXXX), never as text.  None
    when the observed string IS one of the forms."""
    for form in candidates:
        if observed == form:
            return None
    pos = 0
    while True:
        got = {form[pos:pos + 1] for form in candidates if pos < len(form)}
        observed_char = observed[pos:pos + 1]
        if observed_char not in got:
            return ord(observed_char) if observed_char else None
        pos += 1
        if all(pos >= len(form) for form in candidates):
            return None


def _match_form(observed, forms):
    """Compare observed bytes against the enumerated forms; never fold."""
    observed = "" if observed is None else observed
    for index, entry in enumerate(forms):
        if observed == entry["form"]:
            return {"match": True, "form_index": index,
                    "sha256": entry["sha256"],
                    "observed_sha256": _sha(observed),
                    "len": len(observed.encode("utf-8")),
                    "first_differing_codepoint": None}
    return {"match": False, "form_index": None,
            "sha256": None,
            "observed_sha256": _sha(observed),
            "len": len(observed.encode("utf-8")),
            "first_differing_codepoint": _first_differing_codepoint(
                observed, [e["form"] for e in forms])}


def parse_surface(text, equation_forms=None):
    """parse_surface(text, equation_forms) -> references only.

    Parse a desk's answer against the declared §3.6 contract.  ``text`` is
    the desk's answer (the fenced read); the surface block is delimited by
    ``⟦SURFACE v1⟧`` … ``⟦END SURFACE⟧`` — anything outside the block is a
    behavioral/domain layer and is ignored (never parsed, never copied).
    ``equation_forms`` is conformance's enumerated EQUATION_FORMS table
    (this module never imports conformance; the caller supplies it).

    Status: ``absent`` (no surface announced) | ``malformed`` (announced
    but structurally incomplete) | ``lawful`` (all required sections
    present and parseable).  Content verdicts — equation bytes against the
    enumerated forms, symbol vocabulary, lens targets — are left to the
    conformance checks: the result carries the *facts* (match flags, shas,
    codepoints) as references and structure, never the desk's text.
    """
    if not isinstance(text, str):
        return {"status": "absent", "version": 1, "errors": ["not text"]}
    start = text.find(_OPEN_MARKER)
    if start == -1:
        return {"status": "absent", "version": 1, "errors": []}
    end = text.find(_CLOSE_MARKER, start + len(_OPEN_MARKER))
    if end == -1:
        return {"status": "malformed", "version": 1,
                "errors": ["the surface close marker ⟦END SURFACE⟧ is missing"]}
    body = text[start + len(_OPEN_MARKER):end]
    lines = [line.rstrip("\r") for line in body.split("\n")]

    sections = {}
    current = None
    for number, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped == _OPEN_MARKER or stripped == _CLOSE_MARKER:
            continue
        if not stripped:
            continue
        if stripped in _SECTIONS:
            current = stripped
            sections.setdefault(current, [])
            continue
        # "SECTION: inline value" is also a header — the value rides the
        # header line (e.g. "LAW: H = ∞0 | A = K", "GATE: y")
        header = None
        for section in _SECTIONS:
            if stripped.startswith(section + ":"):
                header = section
                break
        if header is not None:
            current = header
            sections.setdefault(current, [])
            rest = stripped[len(header) + 1:].strip()
            if rest:
                sections[current].append((number, rest))
            continue
        if current is not None:
            sections[current].append((number, line.rstrip()))

    errors = []
    missing = _REQUIRED - set(sections)
    if missing:
        errors.append("required section(s) missing: %s" % ", ".join(sorted(missing)))
    if not sections.get("PHASE") or len(sections["PHASE"]) != 1:
        errors.append("PHASE section must name exactly one phase letter")
    if errors:
        return {"status": "malformed", "version": 1, "errors": errors}

    phase_line = sections["PHASE"][0][1].strip()
    phase = phase_line if phase_line in PHASES else None
    if phase is None:
        return {"status": "malformed", "version": 1,
                "errors": ["PHASE %r is not one of S G Q P V" % phase_line]}

    # -- the constitutional block's five equations ------------------------
    forms = equation_forms if equation_forms is not None else {}
    equations = {}
    by_phase = {}
    for number, line in sections.get("EQUATIONS", []):
        stripped = line.strip()
        matched = None
        for letter in PHASES:
            if stripped.startswith(letter + " ") or stripped.startswith(
                    letter + "="):
                matched = letter
                break
        if matched is None:
            continue
        by_phase[matched] = (number, stripped)
    for letter in PHASES:
        observed = by_phase.get(letter, (None, None))[1]
        equations[letter] = _match_form(observed, forms.get(letter, []))

    # -- the active phase's compiled form ---------------------------------
    active_lines = sections.get("EQUATION", [])
    active_equation = _match_form(
        active_lines[0][1].strip() if active_lines else None,
        forms.get(phase, []))
    output_lines = sections.get("OUTPUT", [])
    declared_output = (output_lines[0][1].strip()
                       if output_lines else None)
    output_matches = (
        declared_output == PHASES[phase]["output"]
        if declared_output is not None else None)

    context_in_raw = " ".join(line[1].strip()
                              for line in sections.get("CONTEXT IN", []))
    context_out_raw = " ".join(line[1].strip()
                               for line in sections.get("CONTEXT OUT", []))
    context_in = _split_context(context_in_raw)
    context_out = _split_context(context_out_raw)

    # -- decoding operations ---------------------------------------------
    decoding_lines = [line[1].strip()
                      for line in sections.get("DECODING", [])]
    ops = []
    for line in decoding_lines:
        m = re.match(r"\A\d+\.\s*(.+)\Z", line)
        if m:
            ops.append(m.group(1).strip())
    table = DECODING_OPS[phase]
    first_mismatch = None
    for index, (observed, expected) in enumerate(zip(ops, table)):
        if observed != expected:
            first_mismatch = index
            break
    if first_mismatch is None and len(ops) != len(table):
        first_mismatch = min(len(ops), len(table))
    decoding_matches = first_mismatch is None

    # -- slots (references only) -----------------------------------------
    slots = {}
    for number, line in sections.get("SLOTS", []):
        m = re.match(r"\A([^\s:]+):\s*(.*)\Z", line)
        if m:
            name, value = m.group(1), m.group(2)
            slots[name] = _ref(value)

    # -- compiled symbol and gate ----------------------------------------
    compiled_lines = sections.get("COMPILED", [])
    compiled_symbol = (compiled_lines[0][1].strip()
                       if compiled_lines else None)
    gate_lines = sections.get("GATE", [])
    gate = (gate_lines[0][1].strip() if gate_lines else None)
    symbol_matches = (
        compiled_symbol == OUTPUT_SYMBOLS[phase]
        if compiled_symbol is not None else None)
    gate_matches = (
        gate == {"S": "x", "G": "y", "Q": "z", "P": "a", "V": "b"}[phase]
        if gate is not None else None)

    # -- symbols: every USED name, and whether the SYMBOLS section covers
    #    it (names are the source's own vocabulary, never content) --------
    symbols_entries = {}
    for number, line in sections.get("SYMBOLS", []):
        m = re.match(r"\A([^\s:]+):\s*(.*)\Z", line)
        if m:
            symbols_entries[m.group(1)] = m.group(2)
    used = set()
    for name in slots:
        used.add(name)
    if compiled_symbol is not None and "+" not in compiled_symbol:
        # a single output symbol is a name; the composite B+B''+∞0′ is
        # checked against COMPILED_OUTPUTS, not the vocabulary
        used.add(compiled_symbol)
    used |= set(context_in) | set(context_out)
    for entry in symbols_entries:
        used.add(entry)
    used_symbols = sorted(used)
    symbols_report = [
        {"name": name, "covered": name in symbols_entries,
         "in_vocabulary": name in SYMBOL_VOCABULARY}
        for name in used_symbols]

    # -- corruption codes -------------------------------------------------
    corruption = []
    for number, line in sections.get("CORRUPTION", []):
        corruption = line.split()
        break

    # -- lenses -----------------------------------------------------------
    lenses = []
    for number, line in sections.get("LENSES", []):
        m = re.match(r"\A([SGQPV][SGQPV])\s+(\S+)\s+through\s+(\S+):\s*(.*?)\s*—\s*target:\s*(\S+)\s*\Z", line)
        if m:
            lid, equation, quality, question, target = m.groups()
            entry = LENSES.get(lid)
            lenses.append({
                "id": lid,
                "parent": lid[0],
                "equation_ok": entry is not None and equation == entry["equation"],
                "quality_ok": entry is not None and quality == entry["quality"],
                "question_ok": entry is not None and question == entry["question"],
                "target": target,
                "target_ok": (
                    target == OUTPUT_SYMBOLS[lid[0]]
                    if lid in LENSES else False),
            })

    # -- the optional cycle trace -----------------------------------------
    # TRACE lines map a creative-line position to one of the surface's
    # slots: "POSITION :: SLOTNAME" — the trace declares which positions
    # have formed and where their content lives (references only).
    trace = None
    for number, line in sections.get("TRACE", []):
        m = re.match(r"\A(\S+)\s*::\s*(\S+)\Z", line)
        if m:
            position, slot_name = m.group(1), m.group(2)
            if trace is None:
                trace = {"entries": [], "all_mapped": True}
            trace["entries"].append({
                "position": position, "slot": slot_name,
                "mapped": slot_name in slots})
            trace["all_mapped"] = trace["all_mapped"] and (
                slot_name in slots)

    # -- the optional formation trail (V) ---------------------------------
    trail = None
    if sections.get("TRAIL"):
        passes = {"Pass 1": False, "Pass 2": False}
        entries = []
        for number, line in sections["TRAIL"]:
            m_pass = re.match(r"\A(PASS 1|PASS 2|Pass 1|Pass 2):\s*(\S.*)\Z", line)
            if m_pass:
                passes[m_pass.group(1).title()] = bool(m_pass.group(2).strip())
                continue
            m_entry = re.match(r"\A(\d+)\.\s*\[([SGQPV][SGQPV])\s+lens\]\s*ref:\s*(\S.*)\Z", line)
            if m_entry:
                entries.append({
                    "index": int(m_entry.group(1)),
                    "lens": m_entry.group(2),
                    "ref_present": bool(m_entry.group(3).strip()),
                })
        trail = {"passes": passes, "entries": entries}

    return {
        "status": "lawful",
        "version": 1,
        "errors": errors,
        "phase": phase,
        "equations": equations,
        "active": {
            "phase": phase,
            "equation": active_equation,
            "output": declared_output,
            "output_matches": output_matches,
            "context_in": context_in,
            "context_out": context_out,
        },
        "decoding": {
            "ops": [op.split(" — ")[0].split(":")[0]
                    for op in ops],
            "lines": ops,
            "matches": decoding_matches,
            "first_mismatch_index": first_mismatch,
        },
        "slots": slots,
        "compiled": {
            "symbol": compiled_symbol,
            "gate": gate,
            "symbol_matches": symbol_matches,
            "gate_matches": gate_matches,
        },
        "symbols": symbols_report,
        "corruption_codes": corruption,
        "lenses": lenses,
        "trace": trace,
        "trail": trail,
    }


def _split_context(raw):
    """Split a CONTEXT IN/OUT line on '+' (and the V trace's full-trace
    words stay whole); tokens are the source's own symbols."""
    tokens = []
    for part in raw.split("+"):
        token = part.strip()
        if not token:
            continue
        if "(" in token:  # e.g. "∅ (or ∞0' from prior cycle)" — take ∅
            token = token.split("(")[0].strip()
        tokens.append(token)
    return tokens
