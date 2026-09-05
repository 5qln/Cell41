#!/usr/bin/env python3
"""corruption — the corruption taxonomy (Codex §2.8), the closed set of
exactly five, made executable.

The taxonomy is §2.8's own table, carried from the attested carrier
(``codex.CORRUPTION_CODES`` / ``codex.CORRUPTION_FAILURES``) and never
extended: L1 L2 L3 L4 V∅ — no sixth code exists anywhere in this
artifact, and ``scan_engine_sources`` proves that from the engine's own
AST constants (a mutated twin re-scans).

Each code names ONE specific decoding failure (R9 / C4).  The detectors
below are deterministic functions of declared evidence — structural
signals the caller (the fixture world standing in for the desk) or the
compiler's validation supplies.  They never judge semantics, and they
never judge authenticity: a machine that reports resonance has failed
the measure.

The L3 claim register detects the commission's exact case: a decode
that CLAIMS to have reached ∞0.  Such a decode is reported as
corruption L3 — never as arrival.  The register is byte-scoped: the
enriched return ``∞0′`` (prime, either source spelling) is the lawful
V output and is deliberately excluded from the claim patterns, because
reaching ∞0′ is forming the return question — reaching ∞0 is the claim
§2.8 forbids.

Stdlib only, deterministic, no LLM.
"""

from __future__ import annotations

import ast
import os
import re

from codex import CORRUPTION_CODES, CORRUPTION_FAILURES

__all__ = [
    "CODES",
    "CODE_NAMES",
    "CODE_FAILURES",
    "CLAIM_PATTERNS",
    "detect_claims",
    "evaluate",
    "classify",
    "scan_engine_sources",
    "ENGINE_MODULES",
    "TRAIL_TAGS",
]

# The sealed order of the five codes (the source's own listing order) —
# the tie-break order of classification, never a sixth anything.
CODES = ("L1", "L2", "L3", "L4", "V\u2205")
assert frozenset(CODES) == CORRUPTION_CODES, (
    "the corruption codes drifted from the attested five")

CODE_NAMES = {code: CORRUPTION_FAILURES[code][0] for code in CODES}
CODE_FAILURES = {code: CORRUPTION_FAILURES[code][1] for code in CODES}

# The formation trail's four Pass-1 extraction kinds — the codex's own
# words (§3.2 V op 5: "extract α thread, φ⋂Ω confirmation, ∇, turning
# points").  No new L1 symbol: these are plain-language tags of the
# declared Appendix-D trail jacket, never phase-equation symbols.
TRAIL_TAGS = ("α thread", "φ⋂Ω confirmation", "∇", "turning point")

# ---------------------------------------------------------------------------
# The L3 claim register — the load-bearing refusal's detector.
#
# A decode that claims to have reached ∞0 is corruption L3 and is
# reported as such — never as arrival, never as a decode of ∞0 itself
# (∞0 reveals itself; it cannot be accessed — §2.8).  The prime-lookahead
# keeps the lawful enriched return ∞0' / ∞0′ out of the register: the
# engine must never mistake forming the return question for claiming the
# open space.
# ---------------------------------------------------------------------------

CLAIM_PATTERNS = (
    re.compile(r"\breached\s+∞0(?!['\u2032])\b"),
    re.compile(r"\barrived\s+at\s+∞0(?!['\u2032])\b"),
    re.compile(r"\bdecoded\s+∞0\s+directly\b"),
    re.compile(r"\bdecodes\s+∞0\s+directly\b"),
    re.compile(r"\bclaims\s+to\s+decode\s+∞0\b"),
)


def detect_claims(texts):
    """The claim register over an iterable of strings — returns the
    matched claim fragments (or an empty list).  Deterministic and
    byte-scoped: never normalised, never judged."""
    found = []
    for text in texts or ():
        if not isinstance(text, str):
            continue
        for pattern in CLAIM_PATTERNS:
            for match in pattern.finditer(text):
                found.append(match.group(0))
    return found


# ---------------------------------------------------------------------------
# The five detectors — one per code, each a named decoding failure.
# ---------------------------------------------------------------------------

def evaluate(phase, evidence):
    """Run the five detectors over declared evidence and return the
    detections (the sealed order's first flagged code is the phase's
    corruption).  ``evidence`` keys:

      * ``inserted_answer`` (bool) — an answer was inserted where
        emergence should occur (the arrow was skipped);
      * ``x_generated`` (bool) — the X at S came from the machine's
        channel, not from received emergence;
      * ``claims`` (list of str) — declared claims, plus slot texts, fed
        through the L3 claim register;
      * ``hollow_slots`` (list of slot names) — required slots missing,
        empty, or carrying the unfilled placeholder (the operation is
        empty);
      * ``arrow_skipped`` (bool) — a produced surface's DECODING section
        omits or reorders the arrow step (validation-side signal);
      * ``b2_without_infinity`` (bool) — at V, B'' formed but ∞0′
        missing or questionless;
      * ``premature`` (bool) — B'' before the cycle (L1 at scale).
    """
    evidence = dict(evidence or {})
    detections = []

    if evidence.get("inserted_answer") or evidence.get("arrow_skipped"):
        detections.append({"code": "L1", "signal": (
            "the arrow was skipped — an answer was inserted where "
            "emergence should occur")})
    if evidence.get("premature"):
        detections.append({"code": "L1", "signal": (
            "premature crystallization — B'' before the cycle (L1 at "
            "scale, §3.2 V)")})
    if evidence.get("x_generated"):
        detections.append({"code": "L2", "signal": (
            "X was generated from K instead of received from ∞0 — the "
            "spark was manufactured (the machine-posed signal, carried "
            "honestly)")})
    claimed = detect_claims(list(evidence.get("claims") or ()))
    if claimed:
        detections.append({"code": "L3", "signal": (
            "a claim to decode ∞0 directly / to have reached ∞0 — ∞0 "
            "reveals itself, it cannot be accessed; the claim is "
            "corruption, never arrival (reported claims: %s)"
            % ", ".join(claimed))})
    hollow = list(evidence.get("hollow_slots") or ())
    if hollow:
        detections.append({"code": "L4", "signal": (
            "the decoding is performed but the operation is empty — "
            "form without substance (unfilled slot(s): %s)"
            % ", ".join(hollow))})
    if evidence.get("b2_without_infinity"):
        detections.append({"code": "V\u2205", "signal": (
            "B'' was formed but ∞0' was not — the return question is "
            "missing, the cycle has no continuity")})
    return detections


def classify(phase, evidence):
    """The first flagged code in the sealed order — or None when no
    detector fires.  Never a sixth code; never an authenticity verdict."""
    detections = evaluate(phase, evidence)
    if not detections:
        return None, detections
    for code in CODES:
        for detection in detections:
            if detection["code"] == code:
                return code, detections
    return None, detections  # unreachable — CODES covers every detector


# ---------------------------------------------------------------------------
# The static sixth-code scan — over the ENGINE's own AST constants only
# (test apparatus is not part of what the check judges, the P4a
# convention).  A string constant shaped like L<digits> or V<symbol>
# outside the sealed five is a sixth corruption code.
# ---------------------------------------------------------------------------

ENGINE_MODULES = ("codex.py", "corruption.py", "decoder.py", "compiler.py")

_SIXTH_L = re.compile(r"\AL[0-9]+\Z")
_SIXTH_V = re.compile(r"\AV[^\sA-Za-z0-9]{1,2}\Z")


def scan_engine_sources(root):
    """AST constant scan of the engine modules for a sixth corruption
    code.  Returns the findings (path:line string) — empty means the
    only corruption-code strings in the engine are the sealed five."""
    findings = []
    for name in ENGINE_MODULES:
        path = os.path.join(root, name)
        try:
            with open(path, encoding="utf-8") as handle:
                source = handle.read()
        except OSError:
            continue
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                value = node.value
                if (_SIXTH_L.match(value) or _SIXTH_V.match(value)) and \
                        value not in CORRUPTION_CODES:
                    findings.append("%s:%d %r" % (name, node.lineno, value))
    return findings
