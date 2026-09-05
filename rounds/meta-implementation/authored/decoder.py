#!/usr/bin/env python3
"""decoder — D1 made callable (Codex §2.1-2.5, §2.6/§3.3 adaptive
context, §2.9 scale).

Each phase's numbered decoding operation is one callable path::

    decode(phase, context=…, values=…, trail=…, lenses=…, claims=…)

takes the adaptive context (the accumulated outputs of the prior
phases, §2.6/§3.3) and returns the phase's filled symbol slots.  The
operation list is the attested ``DECODING_OPS`` table — walked
symbol-by-symbol, in order, every time, at every scale (§2.9: the
decoding operations do not change at scale; the engine has no scale
branch).  The engine NEVER generates slot content: the ``values``
channel is the caller's deterministic stand-in for the desk (fixture
world — H-META-3: no desk is constituted on the box, so the engine is
fixture-tested against deterministic inputs, never a live Pi desk).
Slot text leaves the report as references only (sha256 + byte length),
never as content.

Fail closed (H-META-3): any context the engine cannot resolve — an
unknown context symbol, a missing prior output, a slot name outside the
phase's §3.2 slots, a lens whose parent is not the phase, a
crystallization trail for a non-V phase, a V's B'' without the
formation trail it must read — raises ``DecoderError``.  A context it
cannot resolve is refused, never guessed, never silently continued.

The load-bearing refusal (C7): the decoder NEVER decides whether a
decode is authentic.  The report carries no authenticity field of any
kind — only filled slots (references), the walked operations, and the
corruption detections.  A decode whose inputs claim to have reached ∞0
is reported as corruption L3 — never as arrival.

Deterministic, stdlib only, no LLM, no network, no wall clock.
"""

from __future__ import annotations

import hashlib
import re

from codex import (COURSE, CONTEXT_IN, DECODING_OPS, EQUATION_FORMS,
                   LENSES, PHASE_SLOTS)
from corruption import CODE_NAMES, TRAIL_TAGS, classify

__all__ = [
    "DecoderError",
    "decode",
    "ref_text",
    "coerce_ref",
    "REQUIRED_CONTEXT",
    "S_PRIOR_SPELLINGS",
    "PRODUCES",
    "make_trail_entry",
    "validate_trail",
    "trail_passes",
]

# A slot's only report shape: a reference (sha256 + byte length), never
# the text (R11: provenance travels with fingerprint hashes; §4.7.5:
# references only).
_EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()  # e3b0c44298fc… — never valid


def ref_text(text):
    """The reference of a string's exact UTF-8 bytes."""
    raw = text.encode("utf-8")
    return {"ref": "sha256:" + hashlib.sha256(raw).hexdigest(),
            "len": len(raw)}


class DecoderError(ValueError):
    """A context the decoder cannot resolve — fail closed, never guessed."""


# The §3.3 adaptive context, from the attested table: what each phase
# decodes with.  S is the one exception the source itself states:
# ∅ — or ∞0′ from the prior cycle (either source spelling; recorded,
# never folded).
REQUIRED_CONTEXT = {phase: tuple(CONTEXT_IN[phase]) for phase in COURSE}
S_PRIOR_SPELLINGS = ("∞0'", "∞0′")

# Which phase produces which prior outputs (the chain's producer map —
# §3.3 "produces" column).
PRODUCES = {
    "S": ("X",),
    "G": ("α", "Y"),
    "Q": ("Z",),
    "P": ("∇", "A"),
}

# The V's op 1 full trace carries φ⋂Ω alongside the §3.3 six (§2.5:
# "RECEIVE full trace: X + α + Y + φ⋂Ω + Z + ∇ + A").
V_EXTRA_CONTEXT = ("φ⋂Ω",)

_WORD_RE = None


def _validate_cell_address(address):
    global _WORD_RE
    if _WORD_RE is None:
        _WORD_RE = re.compile(r"\A[%s]*\Z" % re.escape("".join(COURSE)))
    if not isinstance(address, str) or _WORD_RE.fullmatch(address) is None:
        raise DecoderError(
            "cell address %r is not a word over {%s}"
            % (address, ", ".join(COURSE)))


def coerce_ref(value):
    """Accept a string (→ its reference) or an already-referenced value
    ({"ref": "sha256:…", "len": n}) — anything else is unresolvable."""
    if isinstance(value, str):
        return ref_text(value)
    if isinstance(value, dict) and isinstance(value.get("ref"), str) and \
            value["ref"].startswith("sha256:") and \
            isinstance(value.get("len"), int) and value["len"] >= 0:
        return {"ref": value["ref"], "len": value["len"]}
    raise DecoderError(
        "context value %r is neither text nor a reference — the adaptive "
        "context is unresolvable (fail closed)" % (value,))


def _resolve_context(phase, context):
    """Resolve the adaptive context — fail closed on anything outside
    §2.6/§3.3.  Returns (kind, refs, prior_spelling) where kind is
    "empty" (S with ∅) | "prior_infinity" (S with ∞0′) | "trace"."""
    context = dict(context or {})
    if phase == "S":
        if not context:
            return "empty", {}, None
        unknown = set(context) - set(S_PRIOR_SPELLINGS)
        if unknown:
            raise DecoderError(
                "S decodes with ∅ (or ∞0' from the prior cycle) — context "
                "carries unresolvable symbol(s): %s"
                % ", ".join(sorted(unknown)))
        spellings = [key for key in S_PRIOR_SPELLINGS if key in context]
        if len(spellings) > 1:
            raise DecoderError(
                "S context carries both ∞0' spellings at once — "
                "unresolvable (the prior cycle's return is ONE question)")
        spelling = spellings[0]
        return "prior_infinity", {spelling: coerce_ref(context[spelling])}, \
            spelling
    required = REQUIRED_CONTEXT[phase]
    allowed = set(required) | (set(V_EXTRA_CONTEXT) if phase == "V" else set())
    unknown = set(context) - allowed
    if unknown:
        raise DecoderError(
            "%s decodes with %s — context carries unresolvable symbol(s): "
            "%s" % (phase, " + ".join(required), ", ".join(sorted(unknown))))
    missing = [symbol for symbol in required if symbol not in context]
    if missing:
        raise DecoderError(
            "the adaptive context for %s is missing prior output(s): %s — "
            "the chain is broken (fail closed)"
            % (phase, ", ".join(missing)))
    refs = {symbol: coerce_ref(context[symbol]) for symbol in context}
    return "trace", refs, None


def _resolve_values(phase, values):
    """Resolve the slot channel.  A slot name outside the phase's §3.2
    slots is an added/renamed L1 symbol — fail closed (AD-SYN-3)."""
    values = dict(values or {})
    slots = PHASE_SLOTS[phase]
    unknown = set(values) - set(slots)
    if unknown:
        raise DecoderError(
            "slot name(s) outside %s's §3.2 slots: %s — an added or "
            "renamed L1 symbol is refused, never decoded"
            % (phase, ", ".join(sorted(unknown))))
    entries = {}
    for name, value in values.items():
        if isinstance(value, str):
            entries[name] = {"text": value, "channel": "received"}
        elif isinstance(value, dict) and isinstance(value.get("text"), str):
            channel = value.get("channel", "received")
            if channel not in ("received", "generated"):
                raise DecoderError(
                    "slot %s carries an unresolvable channel %r"
                    % (name, channel))
            entries[name] = {"text": value["text"], "channel": channel}
        else:
            raise DecoderError(
                "slot %s value %r is neither text nor a slot entry — "
                "unresolvable (fail closed)" % (name, value))
    return entries


def _resolve_lenses(phase, lenses):
    """Lens ids must exist and refine THIS phase's decoding (R3 — the
    lens borrows a quality for the parent's equation; the parent is the
    phase being decoded)."""
    for lid in lenses or ():
        if lid not in LENSES:
            raise DecoderError("lens %r is not one of the 25 sub-phases" % lid)
        if lid[0] != phase:
            raise DecoderError(
                "lens %s refines phase %s's decoding — it cannot refine "
                "phase %s (the borrowed quality serves the parent's "
                "output, R3)" % (lid, lid[0], phase))
    return list(lenses or ())


# ---------------------------------------------------------------------------
# The formation trail (R6) and the two crystallization passes (R7).
# ---------------------------------------------------------------------------

def make_trail_entry(index, lens, tag, text):
    """Build one ordered, lens-tagged trail record: what the B'' reads
    (R6).  ``text`` is referenced; the content never enters the trail."""
    if lens not in LENSES:
        raise DecoderError("trail lens %r is not one of the 25" % lens)
    if tag not in TRAIL_TAGS:
        raise DecoderError(
            "trail tag %r is not one of the Pass-1 kinds (%s)"
            % (tag, " · ".join(TRAIL_TAGS)))
    return {"index": int(index), "lens": lens, "tag": tag,
            "ref": ref_text(text)}


def validate_trail(entries):
    """Validate a caller-supplied formation trail: ordered (gapless,
    ascending), lens-tagged, referenced, and carrying all four Pass-1
    kinds — the analysis of the trail cannot extract what the trail does
    not hold (fail closed)."""
    entries = list(entries or ())
    if not entries:
        raise DecoderError(
            "the formation trail is empty — crystallization reads the "
            "formation trail, never nothing (fail closed)")
    seen_indexes = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise DecoderError("a trail entry is not a record")
        index = entry.get("index")
        if not isinstance(index, int) or index < 1:
            raise DecoderError(
                "trail entry %r carries no positive index — the trail is "
                "not an ordered record" % (entry,))
        seen_indexes.append(index)
        lens = entry.get("lens")
        if lens not in LENSES:
            raise DecoderError(
                "trail entry %d is not lens-tagged with one of the 25 "
                "lenses: %r" % (index, lens))
        tag = entry.get("tag")
        if tag not in TRAIL_TAGS:
            raise DecoderError(
                "trail entry %d carries a tag outside the Pass-1 kinds: "
                "%r" % (index, tag))
        try:
            ref = coerce_ref(entry.get("ref"))
        except DecoderError as exc:
            raise DecoderError("trail entry %d is unreferenced: %s"
                               % (index, exc)) from None
        entry["ref"] = ref
    if seen_indexes != sorted(seen_indexes):
        raise DecoderError("the trail indexes are not ordered (R6: a "
                           "per-output ordered record)")
    if seen_indexes != list(range(1, len(entries) + 1)):
        raise DecoderError("the trail indexes are not gapless (R6)")
    present_tags = {entry["tag"] for entry in entries}
    missing_tags = [tag for tag in TRAIL_TAGS if tag not in present_tags]
    if missing_tags:
        raise DecoderError(
            "the trail carries no %s — Pass 1 cannot extract what the "
            "trail does not hold (fail closed)"
            % " · ".join(missing_tags))
    return entries


def trail_passes(entries, b2_text=None):
    """The two crystallization passes (§3.2 V op 5; R7):
    Pass 1 (analysis) — extract the α thread, φ⋂Ω confirmation, ∇, and
    turning points from the ordered trail; Pass 2 (composition) —
    compose the artifact from the analysis.  Both digests are sha256 of
    the exact bytes they consumed; the passes are recorded, the content
    never leaves as anything but references."""
    entries = validate_trail(entries)
    pass1_refs = [entry["ref"]["ref"] for entry in entries]
    pass1_digest = hashlib.sha256(
        "\n".join(pass1_refs).encode("utf-8")).hexdigest()
    pass2_digest = None
    if b2_text is not None:
        pass2_digest = hashlib.sha256(b2_text.encode("utf-8")).hexdigest()
    return {
        "passes": {"Pass 1": pass1_digest, "Pass 2": pass2_digest},
        "analysis": {tag: [entry for entry in entries
                           if entry["tag"] == tag]
                     for tag in TRAIL_TAGS},
        "consumed": [entry["index"] for entry in entries],
    }


# ---------------------------------------------------------------------------
# The decode callable — one phase, its numbered operation, its filled
# slots.
# ---------------------------------------------------------------------------

def decode(phase, context=None, values=None, trail=None, lenses=None,
           claims=None, cell_address="", inserted_answer=False):
    """Decode one phase's equation, symbol-by-symbol, over the adaptive
    context.  Returns the phase's filled symbol slots as references.

    ``context`` — the §2.6/§3.3 adaptive context (prior outputs, as
    text or references; S takes ∅ or the prior cycle's ∞0′).
    ``values`` — the caller's deterministic stand-in for the desk: the
    slot content (text, or {"text", "channel"}), never generated here.
    ``trail`` — the formation trail (V only; required whenever B'' is
    formed — crystallization reads the trail, R7/CX-SEM-5).
    ``lenses`` — sub-phase lens ids refining THIS phase (R3).
    ``claims`` — declared claims, fed to the L3 register.
    ``inserted_answer`` — declared signal: an answer was inserted where
    emergence should occur (L1).

    The engine never decides authenticity (C7): the report carries
    references, walked operations, and corruption detections — nothing
    else.
    """
    if phase not in COURSE:
        raise DecoderError("phase %r is not one of S G Q P V" % (phase,))
    _validate_cell_address(cell_address)

    kind, context_refs, prior_spelling = _resolve_context(phase, context)
    entries = _resolve_values(phase, values)
    lens_ids = _resolve_lenses(phase, lenses)
    claim_texts = [claim for claim in (claims or ())
                   if isinstance(claim, str)]
    claim_texts += [entry["text"] for entry in entries.values()]

    # -- the numbered decoding operation, walked symbol-by-symbol, in
    #    order, at every scale (§2.9 / §3.5 drift) -------------------------
    operations = [
        {"n": index, "op": text}
        for index, text in enumerate(DECODING_OPS[phase], start=1)]

    # -- filled symbol slots (references only) -----------------------------
    slots = {}
    hollow = []
    for name in PHASE_SLOTS[phase]:
        if name not in entries:
            hollow.append(name)
            continue
        text = entries[name]["text"]
        slots[name] = ref_text(text)
        if not text or text.startswith("⟦runtime slot"):
            hollow.append(name)
    slots_missing = [name for name in PHASE_SLOTS[phase]
                     if name not in entries]

    # -- crystallization (V only, R7) --------------------------------------
    trail_report = None
    if phase == "V":
        b2_present = "B''" in entries
        if trail is not None:
            validated = validate_trail(trail)
            b2_text = entries["B''"]["text"] if b2_present else None
            trail_report = trail_passes(validated, b2_text=b2_text)
        elif b2_present:
            raise DecoderError(
                "a V formed B'' without the formation trail it must read "
                "— crystallization reads the trail, never nothing "
                "(CX-SEM-5, R7; fail closed)")
    elif trail is not None:
        raise DecoderError(
            "crystallization happens at V only (R7) — a %s decode "
            "carries a trail it must not read" % phase)

    # -- corruption detection (never authenticity) -------------------------
    # The V∅ pattern is specific: B'' formed but ∞0′ missing or
    # questionless.  When it fires, the ∞0′ slot is excluded from the
    # hollow-slot signal so the named failure V∅ wins over the generic
    # L4 (each code names ONE specific decoding failure — R9).
    b2_without_infinity = bool(
        phase == "V" and "B''" in entries and (
            "∞0'" not in entries or (
                not entries["∞0'"]["text"]
                or entries["∞0'"]["text"].startswith("⟦runtime slot"))))
    if b2_without_infinity:
        hollow = [name for name in hollow if name != "∞0'"]
    evidence = {
        "inserted_answer": bool(inserted_answer),
        "x_generated": bool(
            phase == "S" and entries.get("X", {}).get("channel")
            == "generated"),
        "claims": claim_texts,
        "hollow_slots": hollow,
        "arrow_skipped": False,
        "b2_without_infinity": b2_without_infinity,
    }
    corruption, detections = classify(phase, evidence)
    detections = [
        {"code": d["code"], "name": CODE_NAMES[d["code"]],
         "failure": d["signal"]} for d in detections]

    report = {
        "phase": phase,
        "mark": "mechanical",
        "cell_address": cell_address,
        "equation": EQUATION_FORMS[phase][0]["form"],
        "equation_sha256": EQUATION_FORMS[phase][0]["sha256"],
        "context_kind": kind,
        "context_refs": context_refs,
        "prior_infinity_spelling": prior_spelling,
        "operations": operations,
        "slots": slots,
        "slots_missing": slots_missing,
        "lens_ids": lens_ids,
        "trail": trail_report,
        "corruption": corruption,
        "corruption_detections": detections,
    }
    return report
