#!/usr/bin/env python3
"""desk — the deterministic fixture desk of the unattended run (H-B4-1).

The folded item, carried byte-faithful: the five desk function-specs are
the codex §2 decoding operations, run in attention mode on the
not-yet-found question (commission §5).  Nothing here is new doctrine —
no new decoding operation, no new L1 symbol, no renamed symbol (D.12).
Every quote below is the held codex's bytes (sources/5qln-codex.txt,
§2.1–2.5 "Decoding operation" blocks and the §2.1 success criterion),
copied verbatim — including the codex's own ∞0' glyph forms where the
source writes them, and the multi-line operations with their exact line
breaks.  The glyphs are enumerated, never normalised (K2): the source's
"∞0'" (U+0027, §2.5 op 7) and the commission table's "∞0′" (U+2032) are
two distinct byte forms and both are carried.

The fixture desk is a STAND-IN (H-B4-1: no desk is constituted on the
box): its attention-mode answers are deterministic fiction over (cell,
cycle, desk), clearly labelled as such, and they announce a lawful §3.6
surface block (the P4b grammar's rendering, slot placeholders filled
when this desk speaks).  The fixture never judges authenticity (K4).

Deterministic and stdlib-only: no network, no LLM, no wall-clock.
"""

from __future__ import annotations

__all__ = [
    "FOUNDING_SENTENCE",
    "DESK_FUNCTION_SPECS",
    "DESK_SHORT_OPS",
    "ATTENTION_READINGS",
    "NEEDLE",
    "slot_content",
    "fill_slots",
    "compose_answer",
]

# The founding sentence — Codex §2.1, the success criterion, verbatim
# (sources/5qln-codex.txt L114).
FOUNDING_SENTENCE = (
    "∞0 is not a step to complete — it is a state to hold. → is not an "
    "action to perform — it is an emergence to receive. ? is not a "
    "question to formulate — it is a question to recognize as it arrives."
)

# The five desk function-specs — the codex §2 decoding operations,
# byte-faithful.  Multi-line operations are one string per operation with
# the source's exact line breaks ("\n" joins the source lines verbatim).
DESK_FUNCTION_SPECS = {
    "S": (
        "1. HOLD ∞0 — resist closing the space. Nothing is sought. Nothing is assumed.",
        "2. RECEIVE → — when something stirs, it is emergence, not generation.",
        "3. NAME ? — what arrived is named as a question.",
        "4. VALIDATE X — the question is genuine (arising from ∞0) not manufactured (assembled from K).",
    ),
    "G": (
        "1. RECEIVE X — the validated question from S is the input.",
        "2. SEEK α — within X, what is the irreducible core? What pattern, if removed, makes X collapse?",
        "3. TEST ≡ — does α remain unchanged when expressed in different forms? If it shifts, it is not α.",
        ("4. FIND {α'} — where does α echo? At what scales? In what domains? Each echo must be\n"
         "self-similar to α (not merely topically related)."),
        ("5. VALIDATE Y — the pattern is validated when α is named, ≡ holds, and {α'} confirm it\n"
         "across multiple scales."),
    ),
    "Q": (
        "1. RECEIVE X + α + Y — the question and its validated pattern are the input.",
        ("2. HOLD φ — what does the inquirer actually perceive about Y?\n"
         "Not what they think. Not what the data says. What lands in direct perception."),
        ("3. HOLD Ω — what does the larger context (universal patterns, collective knowing,\n"
         "the field beyond the individual) reveal about Y?"),
        ("4. WATCH FOR ⋂ — the Natural Intersection is not sought. It arrives.\n"
         "It is the moment φ and Ω meet and something locks into place."),
        ("5. VALIDATE Z — the Resonant Key is validated when ⋂ has landed.\n"
         "Z is what turned the lock. It cannot be argued into place — only confirmed."),
    ),
    "P": (
        "1. RECEIVE X + α + Y + Z — the question, its pattern, and its resonance are the input.",
        "2. MAP δE — where is energy going? What takes effort? Where is friction? Where is resistance?",
        "3. MAP δV — where is value appearing? What is working? Where does movement happen without pushing?",
        ("4. COMPUTE δE/δV — the ratio reveals the landscape. High δE/low δV = wasted effort.\n"
         "Low δE/high δV = natural leverage."),
        ("5. RECEIVE → — the ratio reveals (not computes) the gradient. ∇ is already present in the\n"
         "situation — δE/δV makes it visible."),
        ("6. VALIDATE A — Flow is validated when ∇ is visible and the inquirer can identify where energy\n"
         "wants to go — not where it should go."),
    ),
    "V": (
        "1. RECEIVE full trace: X + α + Y + φ⋂Ω + Z + ∇ + A",
        ("2. NAME L — what actually crystallized here and now? What is the tangible, specific result\n"
         "of this cycle?"),
        ("3. NAME G — what propagates beyond the local? What potentiality manifested that serves\n"
         "beyond the inquiry's own aim?"),
        "4. FIND ⋂ — where do L and G meet? Where does the specific result have universal reach?",
        ("5. COMPOSE B'' — the Fractal Seed. Read the formation trail. The artifact must carry α\n"
         "faithfully. Two passes:\n"
         "Pass 1 (Analysis): extract α thread, φ⋂Ω confirmation, ∇, turning points\n"
         "Pass 2 (Composition): compose the artifact from the analysis"),
        ("6. NAME B — the decoded output. Two dimensions:\n"
         "- Fulfillment: what this cycle produced for the inquiry's own aim\n"
         "- Propagation: what this cycle gives beyond itself"),
        ("7. FORM ∞0' — the return question. Not a summary. Not a conclusion. The question this cycle\n"
         "reveals that could not have been asked before the cycle. The enrichment IS the question."),
    ),
}

# The commission §5 table's first column — the short operation names the
# five specs fold into (quoted from the commission, carried for the
# record; the byte forms above are the operations themselves).
DESK_SHORT_OPS = {
    "S": ("HOLD ∞0", "RECEIVE →", "NAME ?", "VALIDATE X"),
    "G": ("RECEIVE X", "SEEK α", "TEST ≡", "FIND {α′}", "VALIDATE Y"),
    "Q": ("RECEIVE X+α+Y", "HOLD φ", "HOLD Ω", "WATCH FOR ⋂", "VALIDATE Z"),
    "P": ("RECEIVE X+α+Y+Z", "MAP δE", "MAP δV", "COMPUTE δE/δV",
          "RECEIVE →", "VALIDATE A"),
    "V": ("RECEIVE full trace", "NAME L", "NAME G", "FIND ⋂",
          "COMPOSE B″", "NAME B", "FORM ∞0′"),
}

# The commission §5 table's third column — the attention-mode reading of
# each spec (his word, folded into the commission; quoted verbatim).
ATTENTION_READINGS = {
    "S": ("receives the human's raw parts of interest (not a question); "
          "names the question only as it arrives; suggests what kind of "
          "question (How? Why? …) — his word; validates it is genuine "
          "(from ∞0), never manufactured."),
    "G": ("seeks the core hiding in the yet-not-found question (his "
          "word: \"SG seeks the core in the yet-not-found question\"); "
          "α sought within X, never invented alongside it."),
    "Q": ("holds direct perception (φ) and the larger field (Ω) open; "
          "⋂ is not sought — it arrives. The lock is the human's click; "
          "never forced."),
    "P": ("maps where energy drains and where value stirs; makes the "
          "ratio visible; the gradient reveals itself, never invented."),
    "V": ("composes the seed from the trail, never from nothing; forms "
          "the return question; never closes without ∞0′."),
}

# The encoding-lens bytes (commission lens 4) — carried through every
# slot string the fixture desk speaks.
NEEDLE = "∞0′ → ‖"


def slot_content(cell, cycle, desk, slot):
    """The deterministic fixture content of one decoded slot — clearly
    labelled stand-in fiction, never a claim about anything real
    (H-B4-1).  Single-line (the §3.6 SLOTS section is line-based) and
    needle-bearing (lens 4)."""
    name = cell if cell else "ε"
    if slot == "∞0′":
        return ("∞0′ → ‖ what does cycle %d of cell %s open for the "
                "next S — the question this cycle reveals, asked before "
                "it closes" % (cycle, name))
    if slot == "B''":
        return ("∞0′ → ‖ the artifact of cycle %d of cell %s carries α "
                "faithfully — composed from the trail, never from "
                "nothing" % (cycle, name))
    return ("⟦fixture stand-in — attention mode⟧ %s of %s at %s cycle "
            "%d: ∞0′ → ‖ held open, nothing manufactured"
            % (slot, desk, name, cycle))


def fill_slots(surface_block, cell, cycle, desk):
    """Fill the grammar's declared slot placeholders (P4b's
    SLOT_PLACEHOLDER / SLOT_PLACEHOLDER_PROBE — \"filled when this desk
    speaks\") with the deterministic attention-mode content, and (for V)
    leave the two crystallisation passes declared.  The block's fixed
    body — seal equations, decoding operations, symbols — is the
    grammar's rendering, never touched here."""
    out = []
    for line in surface_block.split("\n"):
        if "⟦runtime slot" in line:
            slot, _sep, _placeholder = line.partition(": ")
            out.append("%s: %s" % (slot.strip(), slot_content(
                cell, cycle, desk, slot.strip())))
            continue
        out.append(line)
    return "\n".join(out)


def compose_answer(surface_template, cell, cycle, desk, marker):
    """The desk's full fenced answer: an attention-mode header (the
    behavioral layer — outside the surface block, never parsed, never
    copied), the §3.6 surface block with the slots filled, then the
    unique end marker on its own line (the §4.5 fence, echoed from the
    prompt's instruction).  Deterministic in every byte."""
    name = cell if cell else "ε"
    header = (
        "⟦ATTENTION MODE — fixture stand-in (H-B4-1)⟧\n"
        "desk %s · cell %s · cycle %d\n"
        "%s\n"
        "the question is not yet found — this desk attends, never "
        "manufactures.\n" % (desk, name, cycle, FOUNDING_SENTENCE))
    surface = fill_slots(surface_template, cell, cycle, desk)
    return header + surface.rstrip("\n") + "\n" + marker + "\n"
