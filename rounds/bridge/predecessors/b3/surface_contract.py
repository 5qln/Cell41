#!/usr/bin/env python3
"""surface_contract — B3's contract seam: the §3.6 surface contract read
from the attested rounds by path, sha-pinned, and the descent surface
declared against it.

The two attested sides meet at one contract: P4a's ``surface.py`` declares
the shape a desk's emitted surface is parsed against (Codex §3.6, the
constitutional block + compiled form + context chain + decoder rules +
resolved symbols), and P4b's ``surface_contract.py`` re-exports that same
declaration from the desk-bundle side.  This module does not re-declare,
re-invent or fork either of them — it reads both by file path, pins the
exact bytes it imported (sha256, the verifier's fence values), and then
declares the DESCENT surface (the node record, the signed-path field, the
axis verdicts, the guard items, the return criterion) against that
contract, in one place, versioned.

Fail closed: if a pinned predecessor file is missing or its bytes drift
from the pin, importing this module raises ImportError — a contract that
cannot be verified is INCONCLUSIVE, never silently substituted
(commission lens 6).
"""

from __future__ import annotations

import hashlib
import importlib.util
import os

__all__ = [
    "DESCENT_SURFACE",
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
    "CONTRACT_VERSION",
    "PINNED_FILES",
]

# ---------------------------------------------------------------------------
# The pinned predecessor files — canonical paths, resolved from this file,
# never from a hardcoded absolute location, never from sys.path.  The shas
# are the attested-round values (commission §3: P4a surface sha 776ff463…).
# ---------------------------------------------------------------------------

_P4A_DIR = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "P4a-step-mode", "authored"))
_P4B_DIR = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "P4b-desk-bundles", "authored"))

PINNED_FILES = (
    {
        "path": os.path.join(_P4A_DIR, "surface.py"),
        "sha256": "776ff46393bf81db62841043021c97288e2c1414bec43971d275d1dfbdfac36d",
        "role": "P4a's §3.6 surface contract and parser (the declared shape)",
    },
    {
        "path": os.path.join(_P4B_DIR, "surface_contract.py"),
        "sha256": "fb166569f877d13bf5e8a8e8016f2ab37f711bde1ae8a1b0ecc3d77a3cbe199e",
        "role": "P4b's re-export of the same contract (the desk-bundle side)",
    },
    {
        "path": os.path.join(_P4B_DIR, "grammar.py"),
        "sha256": "d7ab814ca89899ecce5b9fb065588fc185eae08b3debec5573144bfba1e97f63",
        "role": "P4b's desk grammar the descent seats at child addresses "
                "(pinned here; imported by descent.py)",
    },
)


def _load_pinned(pinned, module_name):
    try:
        with open(pinned["path"], "rb") as handle:
            raw = handle.read()
    except OSError as exc:
        raise ImportError(
            "surface_contract: the pinned file %s is unreadable (%s) — the "
            "contract is INCONCLUSIVE, never substituted"
            % (pinned["path"], exc)) from None
    actual = hashlib.sha256(raw).hexdigest()
    if actual != pinned["sha256"]:
        raise ImportError(
            "surface_contract: %s sha256 %s does not match the pinned %s — "
            "refusing to import a drifted contract"
            % (pinned["path"], actual, pinned["sha256"]))
    spec = importlib.util.spec_from_file_location(module_name, pinned["path"])
    if spec is None or spec.loader is None:
        raise ImportError(
            "surface_contract: cannot build an import spec for %s"
            % pinned["path"])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_p4a_surface = _load_pinned(PINNED_FILES[0], "p4a_surface_contract_source")
_p4b_surface_contract = _load_pinned(
    PINNED_FILES[1], "p4b_surface_contract_module")

SURFACE_CONTRACT = _p4a_surface.SURFACE_CONTRACT
parse_surface = _p4a_surface.parse_surface
PHASES = _p4a_surface.PHASES
DECODING_OPS = _p4a_surface.DECODING_OPS
LENSES = _p4a_surface.LENSES
OUTPUT_SYMBOLS = _p4a_surface.OUTPUT_SYMBOLS
COMPILED_OUTPUTS = _p4a_surface.COMPILED_OUTPUTS
CONTEXT_IN = _p4a_surface.CONTEXT_IN
CONTEXT_OUT = _p4a_surface.CONTEXT_OUT
SYMBOL_VOCABULARY = _p4a_surface.SYMBOL_VOCABULARY
CREATIVE_LINE = _p4a_surface.CREATIVE_LINE

CONTRACT_VERSION = SURFACE_CONTRACT["version"]

# Import-time self-consistency: both attested sides must agree on the one
# contract (P4b's re-export carries P4a's declaration).
if _p4b_surface_contract.CONTRACT_VERSION != CONTRACT_VERSION:
    raise ImportError(
        "surface_contract: P4b's contract version %r differs from P4a's %r"
        % (_p4b_surface_contract.CONTRACT_VERSION, CONTRACT_VERSION))

# ---------------------------------------------------------------------------
# The descent surface — declared against the §3.6 contract, in one place.
# Every field carries its source citation; the declaration is data, never
# logic.  The letter-order question is NOT decided here: it lives in the
# declared WORD_ORDER parameter carried by P4b's grammar (H-B3-2).
# ---------------------------------------------------------------------------

DESCENT_SURFACE = {
    "version": 1,
    "round": "R04-B3",
    "what": (
        "the descent: gate-fails-to-lock → child node + address append + "
        "arrangement; byte-exact axis inheritance; guard pass at every "
        "depth; return criterion = artifact + genuine ∞0′ (PRD §B3)"),
    "node_layout": {
        "rule": ("PRD §5.3: \"Nodes are directories: nodes/<word>/"
                 "{question.md, cell.node.json}. Zoom in = append a "
                 "letter; zoom out = strip. Addressing is derived, never "
                 "stored\" — ε is written `_` on disk"),
        "question.md": "the podium — human-planted only; the descent has "
                       "no write path to it (PRD §2.1, T-R3-02)",
        "cell.node.json": "the node record — axis, signed path, tentative, "
                          "refs; never an address field",
        "seed.md": ("the tentative seed in the node's own file (PRD §13.1 "
                    "D7: \"tentative seeds live in the node's own file\") — "
                    "a ref to the carried field, never content"),
        "artifact.md": "the V desk's artifact (B″) — fixture world data",
        "return.md": "the V desk's ∞0′ — fixture world data",
    },
    "node_record_fields": {
        "required": ("axis", "signed_path", "tentative"),
        "optional": ("seed_ref", "arrangement", "claimed_surface",
                     "artifact_ref", "infinity_zero_prime_ref"),
        "forbidden": ("address",),
        "axis": ("the §5.4 token: field = {mode: inherited|anchored, "
                 "anchor: <durable ref>}, never empty; delta = ordered, "
                 "de-duplicated per-surface refs, never part of the "
                 "equality test"),
    },
    "signed_path": {
        "rule": ("Appendix D.5/AR3: \"Every address normalizes to "
                 "+^k · (−x₁)…(−x_m). All + first, then all −.\" A "
                 "separate field from the bare node word (PLAN-ADDENDUM "
                 "§C, commission C2)"),
        "glyphs": ("the descent operator is U+2212 `−`, ascent is U+002B "
                   "`+` — the same glyphs P4a's attested STEP_KINDS "
                   "registry declares (zoom_sign); ASCII `-` is not part "
                   "of the notation and no byte normalisation maps it "
                   "(commission K2)"),
        "empty": "the empty path is the same node (D.6)",
        "rejected": ("the malformed signed paths `-P-Q-P` and `+-G` "
                     "(commission §7) — ASCII hyphen, never the "
                     "U+2212 operator"),
    },
    "axis_verdicts": {
        "rule": ("PRD §5.4: MOVING iff fields differ · recast iff fields "
                 "equal and surfaces equal · STASIS iff fields equal and "
                 "surfaces differ. MOVING dominates: stop the descent at "
                 "the human's level, surface, log, wait."),
        "field_equality": "byte comparison of the canonical JSON of the "
                          "field objects — never per-call, one invariant "
                          "across the whole descent (lens 2)",
        "surface_identity": "the node's arrangement reference",
    },
    "guard_pass": {
        "rule": ("PRD §5.5: \"Guard pass at every node and depth: L1 L2 "
                 "L3 L4 V∅. No V without ∞0′ (R6).\""),
        "items": {
            "GS-L1": ("a gate record at the node whose predecessor (in "
                      "x y z a b order) has no record — the arrow was "
                      "skipped (L1 Closing)"),
            "GS-L2": ("the node's S-gate record is machine-posed "
                      "(tentative: true) — the manufacturing signal, "
                      "recorded honestly, never hidden (L2 Generating)"),
            "GS-L3": ("the node's claimed surface declares a symbol "
                      "outside the §1.9 vocabulary or a corruption code "
                      "beyond the five (L3 Claiming) — checked through "
                      "P4a's own parser, imported"),
            "GS-L4": ("a gate record whose payload_ref is empty or an "
                      "unfilled placeholder slot (L4 Performing)"),
            "GS-VOID": ("a V (gate b) record at the node with no ∞0′ — "
                        "REFUSED, never valid (V∅; seal line 8)"),
        },
        "verdicts": "PASS | FLAG | REFUSED | INCONCLUSIVE — anything "
                    "unobservable reads INCONCLUSIVE, never clean (lens 6)",
    },
    "return_criterion": {
        "rule": "PRD §B3: \"return criterion = artifact + genuine ∞0′\"",
        "genuine": ("the V record carries the human's act "
                    "(attestation_ref non-null) — the human's click is "
                    "the only authenticity authority; this module reports "
                    "presence, never judges genuineness (commission §6)"),
        "refused": "a V with no ∞0′, or an attested V missing its "
                   "artifact — half a return is not a return",
        "held": "an unattested V — surface and wait",
    },
    "commitments": {
        "C7-1": "no hard-coded maximum depth — any loop bound is a "
                "caller-supplied step budget, never a depth constant",
        "C7-2": ("the address alphabet is data (P4b's COURSE), never a "
                 "literal — a jump marker can exist beside "
                 "{S,G,Q,P,V} without touching the validator"),
        "C7-3": ("the walk loop stops on resources (budget, descent "
                 "material) or mandated refusals — never on semantic "
                 "completion; the return criterion is observed after "
                 "the loop, never a break condition"),
        "C7-4": ("nothing treats descent as narrowing — no size or "
                 "surface comparison prunes a child; a leap may open a "
                 "larger dimension"),
        "C7-5": ("no code assumes the current cell is the root — the "
                 "address is always a parameter; ε is a coordinate "
                 "anchor, never a privileged role (Appendix D.2: no "
                 "root, no leaf)"),
    },
}
