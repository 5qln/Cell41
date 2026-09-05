#!/usr/bin/env python3
"""descent — the zoom-in module (R04 · B3, C1–C7, holds H-B3-1…5).

The descent, per the commission §1: given a node at an address, when its
gate fails to lock, the driver descends — it creates a child node by
appending a letter to the address (zoom in), seats an arrangement from
the P4b grammar at that child, carries the axis ``field`` byte-exact
from parent to child, runs the guard pass at every depth, and returns
an artifact + a genuine ∞0′ as the return criterion.  The criterion
this module measures, verbatim (PRD §B3, commission C1): *"a 3-deep
descent shows byte-identical axis.field from root to leaf; a
manufactured field change yields `MOVING` and a stop-and-surface"* — and
(commission C3, R6): *"a V with no ∞0′ is refused"*.

Address is derived, never stored (PRD §5.3: ``nodes/<word>/`` with ε
written ``_``; the node record carries no address field); the signed
path is a separate field (PLAN-ADDENDUM §C, commission C2); the axis
verdicts (MOVING / recast / STASIS) are computed from byte comparison
(PRD §5.4), MOVING dominates and stops the descent at the human's level;
and every one of the five quantum-jump commitments (C7) is a structural
constraint on this code — planned for, never implemented (H-B3-4).

The five commitments, as this module encodes them:

  C7-1  no hard-coded maximum depth — the walk's only bound is a
        caller-supplied step budget (a resource), never a depth constant;
  C7-2  the address alphabet is DATA (P4b's ``grammar.COURSE``, imported)
        — the word regex and the signed-path letter class are built from
        it, so a jump marker can exist beside {S,G,Q,P,V} without
        touching any validator;
  C7-3  the walk loop stops on RESOURCES (the budget, the descent
        material, the trigger data) or on mandated refusals (MOVING,
        V∅, a consumed tentative node) — never on semantic completion;
        the return criterion is OBSERVED after the loop, never a break
        condition;
  C7-4  nothing treats descent as narrowing — no size or surface
        comparison prunes a child; a leap may open a larger dimension;
  C7-5  no code assumes the current cell is the root — every function
        takes the address as a parameter; ε is a coordinate anchor of
        the reading, never a privileged role (Appendix D.2: no root,
        no leaf).  ``zoom_out("")`` is ``""``: the word language anchors
        at the assumed root and the SIGN carries what lies beyond it
        (D.3/D.7) — a coordinate fact, never a root assumption.

The letter-order hold (H-B3-2): D.2 reads the word inner-first, D.3/D.6
read it outer-first; the choice is HIS, later, and P4b already carries
it as the declared parameter ``grammar.WORD_ORDER``.  This module does
not hard-code either convention and no logic here depends on which end
is deep.  The letter-order touches this file in exactly TWO spots,
both delegating to the declared parameter:

  * ``zoom_in``  — the append side; delegates to the imported
    ``grammar.seat_address`` (P4b's parameterized seat convention);
  * ``zoom_out`` — the strip side; the only branch on
    ``grammar.WORD_ORDER`` in this file.

Every other address operation (``deep_letter``, ancestor chains,
``path_between``, ``apply_signed_path``) is built from those two
primitives alone, so flipping the parameter is a one-table change, never
a rewrite (H-B3-2).

Imports — the attested rounds, never re-authored (commission §4):
B0's ledger via FRACTAL_LEDGER_DIR (imported, never copied); B2's
driver (the gate walk — this module extends ``Driver`` and never
re-implements the herdr socket dialect: the descent never touches the
socket at all, H-B3-1); P4a's step (the reserved zoom kinds and the
D.12-class guard checks); P4b's block/arrangement/grammar (the child's
arrangement is a P4b arrangement).  P4a's surface contract is read
through this round's ``surface_contract`` (sha-pinned).  Every
predecessor file is sha-pinned at load — a drifted predecessor is an
ImportError, never a silent substitution (lens 6).

No desk is constituted here: the descent runs against fixture node trees
(H-B3-1); no socket, no live pane, no LLM, no wall clock in the logic
(the ledger clock is a caller-supplied parameter, defaulting to B0's).

Deterministic and stdlib-only.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import sys

# ---------------------------------------------------------------------------
# Imports — attested modules, by file path, sha-pinned.  Never copied.
# ---------------------------------------------------------------------------

_LEDGER_DIR = os.environ.get(
    "FRACTAL_LEDGER_DIR", "/home/deploy/the-cell/ledger")
if _LEDGER_DIR not in sys.path:
    sys.path.insert(0, _LEDGER_DIR)

from fractal_ledger import (  # noqa: E402
    LedgerLoader,
    LedgerWriter,
    canonical_json,
    make_record,
)

_B3_DIR = os.path.dirname(os.path.abspath(__file__))
_ROUNDS_DIR = os.path.dirname(os.path.dirname(_B3_DIR))
_P4B_DIR = os.environ.get(
    "P4B_DESK_BUNDLES_DIR",
    os.path.join(_ROUNDS_DIR, "P4b-desk-bundles", "authored"))
_P4A_DIR = os.environ.get(
    "P4A_STEP_MODE_DIR",
    os.path.join(_ROUNDS_DIR, "P4a-step-mode", "authored"))
_B2_DIR = os.environ.get(
    "B2_DRIVER_DIR",
    os.path.join(_ROUNDS_DIR, "R03-B2", "authored"))


def _load_by_path(filepath, module_name, expected_sha, path_entries=()):
    """Load one predecessor module by file path under ``module_name``,
    refusing (ImportError) when the bytes drift from ``expected_sha``.
    ``path_entries`` is inserted at sys.path[0] for the load only — the
    module's sibling imports resolve inside its own round, never across
    rounds (each round has same-named modules with different bytes)."""
    try:
        with open(filepath, "rb") as handle:
            raw = handle.read()
    except OSError as exc:
        raise ImportError(
            "descent: the predecessor file %s is unreadable (%s) — the "
            "attested surface is INCONCLUSIVE, never substituted"
            % (filepath, exc)) from None
    actual = hashlib.sha256(raw).hexdigest()
    if actual != expected_sha:
        raise ImportError(
            "descent: %s sha256 %s does not match the pinned %s — "
            "refusing to import a drifted predecessor"
            % (filepath, actual, expected_sha))
    saved = sys.path[:]
    try:
        for entry in reversed(path_entries):
            sys.path.insert(0, entry)
        spec = importlib.util.spec_from_file_location(module_name, filepath)
        if spec is None or spec.loader is None:
            raise ImportError(
                "descent: cannot build an import spec for %s" % filepath)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path[:] = saved


# This round's surface contract first — the plain name "surface_contract"
# binds THIS module, and P4b's grammar (loaded below) resolves its own
# ``from surface_contract import parse_surface`` through it: the two
# attested sides already meet at the one §3.6 contract (P4b's
# surface_contract pins P4a's surface.py — the same 776ff463… bytes).
if _B3_DIR not in sys.path:
    sys.path.insert(0, _B3_DIR)
import surface_contract  # noqa: E402
from surface_contract import (  # noqa: E402
    DESCENT_SURFACE,
    SYMBOL_VOCABULARY,
    parse_surface,
)

# P4b — the desk grammar, the block model, the arrangement model.
_SHA_GRAMMAR = "d7ab814ca89899ecce5b9fb065588fc185eae08b3debec5573144bfba1e97f63"
_SHA_BLOCK = "20ac2b38ff971056d8bc9368455577da93e1b4d0ef227b0dcfd00e68214d3f5a"
_SHA_ARRANGEMENT = "6b50d3bb829bb2621520a87b4e3188a4976f3af57de0cda5f90433cb945e4d25"
grammar = _load_by_path(
    os.path.join(_P4B_DIR, "grammar.py"), "grammar", _SHA_GRAMMAR,
    path_entries=(_P4B_DIR,))
block = _load_by_path(
    os.path.join(_P4B_DIR, "block.py"), "block", _SHA_BLOCK,
    path_entries=(_P4B_DIR,))
arrangement = _load_by_path(
    os.path.join(_P4B_DIR, "arrangement.py"), "arrangement", _SHA_ARRANGEMENT,
    path_entries=(_P4B_DIR,))

# P4a — the stepping surface: the reserved zoom kinds (which B3 now
# implements without touching the controller protocol or the trail
# schema, per step.py's own K5 note) and the D.12-class guard data.
_SHA_STEP = "7c02f316969fdc2a6a9825b2ce4cb264976de3c607d8438f58b4b1e94bd26edf"
_step = _load_by_path(
    os.path.join(_P4A_DIR, "step.py"), "p4a_step", _SHA_STEP,
    path_entries=(_P4A_DIR,))

# B2 — the driver, the gate walk.  Loaded as a chain (its siblings import
# each other by plain name); the plain name "walker" is deliberately
# rebound to B2's copy (P4a's conformance already bound its own
# references at its import time, so nothing is disturbed).
_SHA_DIALECTS = "9ebc6d314bd265e5be14c9c22fb47a4b80f4fabab5c4a46dd3f9f1ca0e6a4208"
_SHA_INSTRUMENT = "159c78c12328c8fbcc841b19d52570f99e90edaebf184e6bbb3e10b8ba4bca6b"
_SHA_LENS = "ad46b895dc3ceb68379467d8c9b642affcfc1b214633a1de9f89d39240fd269a"
_SHA_WALKER = "5889160a15c5bc6949c6cd65726aeb609d4ca54efa3f2702229da5a675a002e9"
_SHA_DRIVER = "397f93fc0ae01ab09ab21d22b63655546a760ab35f5138055aa9c4c999f01cf2"
for _name, _sha in (("dialects", _SHA_DIALECTS),
                    ("instrument", _SHA_INSTRUMENT),
                    ("lens", _SHA_LENS),
                    ("walker", _SHA_WALKER)):
    _load_by_path(os.path.join(_B2_DIR, _name + ".py"), _name, _sha,
                  path_entries=(_B2_DIR,))
_driver = _load_by_path(
    os.path.join(_B2_DIR, "driver.py"), "driver", _SHA_DRIVER,
    path_entries=(_B2_DIR,))

Driver = _driver.Driver          # the B2 turn machine — extended below
turn_key = _driver.turn_key      # §4.5 idempotency, carried to depth
PROMPT_ATTEMPT = _driver.PROMPT_ATTEMPT
REFUSAL_ATTEMPT_PREFIX = _driver.REFUSAL_ATTEMPT_PREFIX

__all__ = [
    "Descent",
    "zoom_in",
    "zoom_out",
    "validate_word",
    "deep_letter",
    "ancestor_chain",
    "validate_signed_path",
    "path_between",
    "apply_signed_path",
    "field_bytes",
    "field_handoff",
    "axis_verdict",
    "EMPTY_SHA256",
    "CORRUPTION_CODES",
    "ALPHABET",
    "SIGNED_PLUS",
    "SIGNED_MINUS",
    "SIGNED_SEPARATOR",
    "turn_key",
    "Driver",
]

# ---------------------------------------------------------------------------
# Data — the alphabet, the corruption codes, the sign glyphs.  All imported
# from the attested rounds where they live, never re-literalised (C7-2).
# ---------------------------------------------------------------------------

# The five corruption codes, seal line 9 — data, never extended.
CORRUPTION_CODES = ("L1", "L2", "L3", "L4", "V∅")

# The address alphabet — P4b's COURSE table, imported.  A jump marker can
# exist beside {S,G,Q,P,V} by extending this one table (C7-2).
ALPHABET = "".join(grammar.COURSE)
_WORD_RE = re.compile(r"\A[%s]*\Z" % re.escape(ALPHABET))

# The sign glyphs — P4a's attested STEP_KINDS registry declares them as
# data (zoom_in: "−" U+2212, zoom_out: "+" U+002B); the descent uses the
# registry's own values, never its own literals.  ASCII `-` is NOT part
# of the notation and no byte normalisation maps it (K2): that is
# exactly why the malformed signed paths `-P-Q-P` and `+-G` are
# rejected (commission §7).
_STEP_KINDS = _step.STEP_KINDS
SIGNED_MINUS = _STEP_KINDS["zoom_in"]["zoom_sign"]     # − (U+2212)
SIGNED_PLUS = _STEP_KINDS["zoom_out"]["zoom_sign"]     # + (U+002B)
SIGNED_SEPARATOR = "·"   # D.5's separator between the +^k and −x runs

EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()  # e3b0c44298fc… — never valid

# ---------------------------------------------------------------------------
# Address ops — the TWO spots where the letter-order question touches this
# file.  Everything else is built from these two primitives (H-B3-2).
# ---------------------------------------------------------------------------


def validate_word(address):
    """True iff ``address`` is a word over the alphabet data (ε = "").
    Built from the imported alphabet table, never from a five-letter
    literal (C7-2)."""
    if not isinstance(address, str):
        return False
    return _WORD_RE.fullmatch(address) is not None


def _check_word(address):
    if not validate_word(address):
        raise ValueError(
            "address %r is not a word over {%s}"
            % (address, ", ".join(grammar.COURSE)))


def zoom_in(address, letter):
    """ZOOM− — the child address: one letter appended to the word.

    SPOT 1 of the letter-order question (H-B3-2): the append side is
    NOT decided here — it delegates to P4b's imported ``seat_address``,
    which carries the declared ``WORD_ORDER`` parameter (D.2
    inner-first as carried; D.3/D.6 outer-first is his to confirm).
    One declared exception travels with the import: the root cell's
    centre S seats at ε itself (Appendix D.7 — the signless true
    start), so ``zoom_in("", "S") == ""``; the descent refuses that
    no-movement case instead of looping (C7-3).
    """
    _check_word(address)
    if not isinstance(letter, str) or letter not in grammar.COURSE:
        raise ValueError("letter %r is not in the alphabet" % (letter,))
    return grammar.seat_address(address, letter)


def zoom_out(address):
    """ZOOM+ — the father address: one letter stripped from the word.

    SPOT 2 of the letter-order question (H-B3-2): the only branch on
    ``grammar.WORD_ORDER`` in this file.  The strip removes the deep-end
    letter — whichever end the declared parameter says is deep — and
    nothing else in this module inspects word ends.  ``zoom_out("")``
    is ``""``: the word anchors at the reading's assumed root and the
    SIGN carries what lies beyond it (D.3/D.7) — a coordinate fact,
    never a root assumption (C7-5).
    """
    _check_word(address)
    if not address:
        return ""
    if grammar.WORD_ORDER == "inner_first":
        return address[1:]
    return address[:-1]


def deep_letter(address):
    """The deepest letter of ``address``, derived from the two zoom
    primitives alone (the inverse of ``zoom_in``) — no third spot ever
    inspects which end is deep."""
    if not address:
        return None
    remainder = zoom_out(address)
    for letter in grammar.COURSE:
        if zoom_in(remainder, letter) == address:
            return letter
    return None


def ancestor_chain(address):
    """The address's ancestor chain, shallow end first: [address, its
    father, …, the anchor ""].  Built from ``zoom_out`` alone."""
    _check_word(address)
    chain = []
    current = address
    while True:
        chain.append(current)
        father = zoom_out(current)
        if father == current:
            break
        current = father
    return chain


def word_to_disk(address):
    """ε is written `_` on disk (PRD §5.3)."""
    _check_word(address)
    return "_" if address == "" else address


def _gate_letter(gate):
    """The desk letter of a gate — the inverse of P4b's DESK_GATES data."""
    for letter, letter_gate in grammar.DESK_GATES.items():
        if letter_gate == gate:
            return letter
    raise ValueError("gate %r is not one of x y z a b" % (gate,))


def cell_desk_addresses(cell_address):
    """The five seat addresses of the cell at ``cell_address`` — derived
    through the imported seat convention, never stored (PRD §5.3)."""
    _check_word(cell_address)
    return {letter: grammar.seat_address(cell_address, letter)
            for letter in grammar.COURSE}


# ---------------------------------------------------------------------------
# The signed path — the AR3 field, a separate field from the address.
# ---------------------------------------------------------------------------


def validate_signed_path(text):
    """Validate a signed path against AR3 (\"+^k · (−x₁)…(−x_m). All +
    first, then all −.\").  Returns:

        {"status": "absent"|"malformed"|"ok", "k", "letters", "reason"}

    The path is a string over {+, −, ·, alphabet letters}; every − step
    carries exactly one letter, every letter rides a − step, pluses
    come first (a letter or a − may never follow a −-run's end back
    into +), and the `·` separator may only sit between the two runs.
    The empty path is the same node (D.6).

    The descent operator is U+2212 `−` — the glyph P4a's STEP_KINDS
    registry declares.  The ASCII hyphen `-` is not part of the
    notation and no byte normalisation maps it (K2): `-P-Q-P` and
    `+-G` are therefore malformed, exactly as the commission §7
    requires.
    """
    if text is None or not isinstance(text, str):
        return {"status": "absent", "k": None, "letters": None,
                "reason": "no signed path is present"}
    if text == "":
        return {"status": "ok", "k": 0, "letters": [],
                "reason": "the empty path — the same node (D.6)"}
    alphabet_set = set(ALPHABET)
    for index, char in enumerate(text):
        if char == SIGNED_PLUS or char == SIGNED_MINUS or char in alphabet_set:
            continue
        if char == SIGNED_SEPARATOR:
            continue
        if char == "-":
            return {"status": "malformed", "k": None, "letters": None,
                    "reason": ("the ASCII hyphen `-` (U+002D) is not the "
                               "descent operator `−` (U+2212) — no byte "
                               "normalisation maps it (K2); rejected at "
                               "position %d" % index)}
        return {"status": "malformed", "k": None, "letters": None,
                "reason": ("character %r at position %d is outside the "
                           "signed-path alphabet" % (char, index))}
    k = 0
    position = 0
    while position < len(text) and text[position] == SIGNED_PLUS:
        k += 1
        position += 1
    if position < len(text) and text[position] == SIGNED_SEPARATOR:
        position += 1
        if position >= len(text):
            return {"status": "ok", "k": k, "letters": [],
                    "reason": "a pure ascent: +^k with no − steps (m = 0)"}
    letters = []
    while position < len(text):
        if text[position] != SIGNED_MINUS:
            return {"status": "malformed", "k": None, "letters": None,
                    "reason": ("every step after the + run must open with "
                               "`−` (all + first, then all − — AR3); "
                               "position %d holds %r"
                               % (position, text[position]))}
        position += 1
        if position >= len(text) or text[position] not in alphabet_set:
            return {"status": "malformed", "k": None, "letters": None,
                    "reason": "a `−` step must carry exactly one letter "
                              "(which daughter — D.5)"}
        letters.append(text[position])
        position += 1
    return {"status": "ok", "k": k, "letters": letters,
            "reason": "normalized +^k · −x₁…−x_m"}


def path_between(from_address, to_address):
    """The normalized signed path from ``from_address`` to
    ``to_address``, built from the zoom primitives alone: k pluses for
    the frames to climb to the common father, then one − step per
    descent letter in descent (chronological) order — the same string
    under either WORD_ORDER value, because the address carries the
    convention and the path carries the steps (H-B3-2)."""
    _check_word(from_address)
    _check_word(to_address)
    chain_to = ancestor_chain(to_address)
    k = 0
    frame = from_address
    while frame not in chain_to:
        father = zoom_out(frame)
        if father == frame:
            break
        frame = father
        k += 1
    letters = []
    node = to_address
    while node != frame:
        letter = deep_letter(node)
        if letter is None:
            break
        letters.append(letter)
        node = zoom_out(node)
    letters.reverse()
    out = SIGNED_PLUS * k
    if k and letters:
        out += SIGNED_SEPARATOR
    for letter in letters:
        out += SIGNED_MINUS + letter
    return out


def apply_signed_path(from_address, text):
    """Apply a signed path to ``from_address`` through the zoom
    primitives alone, returning the target address.  A malformed path
    raises ValueError; a target beyond the anchor clamps at ε (the word
    cannot go below the empty word — the sign carries what lies beyond,
    D.3/D.7)."""
    report = validate_signed_path(text)
    if report["status"] == "absent":
        raise ValueError("no signed path to apply")
    if report["status"] == "malformed":
        raise ValueError("malformed signed path %r: %s"
                         % (text, report["reason"]))
    current = from_address
    _check_word(current)
    for _ in range(report["k"]):
        current = zoom_out(current)
    for letter in report["letters"]:
        current = zoom_in(current, letter)
    return current


# ---------------------------------------------------------------------------
# The axis — byte-exact field carry, the verdicts, MOVING dominates.
# ---------------------------------------------------------------------------


def field_bytes(field):
    """The exact bytes a field occupies — B0's canonical JSON (sorted
    keys, compact separators, UTF-8 passthrough).  All equality tests
    compare THESE bytes (lens 2: one invariant, byte-identical across
    the whole descent, never per call)."""
    return canonical_json(field).encode("utf-8")


def field_handoff(field):
    """The parent's handoff: the anchor carried byte-exact, provenance
    re-stamped to ``inherited``.  At a fresh start the field is
    ``anchored`` at its own birth (the plant record on the ledger); at
    a continuation the handoff IS the field — byte-identical.  The
    field is never empty (C1): a missing, malformed or empty anchor is
    refused, never inherited."""
    if not isinstance(field, dict):
        raise ValueError("the axis field is not an object — never empty (C1)")
    if field.get("mode") not in ("anchored", "inherited"):
        raise ValueError(
            "the axis field mode %r is not anchored|inherited — never "
            "empty (C1)" % (field.get("mode"),))
    anchor = field.get("anchor")
    if not isinstance(anchor, str) or not anchor:
        raise ValueError(
            "the axis field anchor is empty — the field of openness "
            "itself is the axis and is never empty (C1)")
    return {"mode": "inherited", "anchor": anchor}


def axis_verdict(parent_field, child_field, parent_surface, child_surface):
    """The §5.4 verdicts, computed from byte comparison:

        MOVING  iff the child's field bytes differ from the handoff
                bytes (the drift);
        recast  iff the fields are equal and the surfaces are equal;
        STASIS  iff the fields are equal and the surfaces differ.

    MOVING dominates: it is the descent's stop-and-surface signal
    (PRD §5.4; the cell: "MOVING dominates — stop the descent at the
    human's level, surface, log, wait").  Note the handoff, not the
    parent's stored field, is the comparison base: re-stamping
    provenance (anchored → inherited) is the descent's own act, never
    a drift.
    """
    handoff = field_handoff(parent_field)
    if field_bytes(child_field) != field_bytes(handoff):
        return "MOVING"
    if parent_surface == child_surface:
        return "recast"
    return "STASIS"


# ---------------------------------------------------------------------------
# Node IO — nodes/<word>/{…}; the address is derived from the directory
# name and never stored (PRD §5.3).
# ---------------------------------------------------------------------------

_NODE_REQUIRED = frozenset(DESCENT_SURFACE["node_record_fields"]["required"])
_NODE_OPTIONAL = frozenset(DESCENT_SURFACE["node_record_fields"]["optional"])
_NODE_KNOWN = _NODE_REQUIRED | _NODE_OPTIONAL


class NodeError(ValueError):
    """A node record refused by the descent's node validation."""


def validate_node_record(record):
    """Validate one cell.node.json record against the declared descent
    surface.  An ``address`` key is REFUSED — addressing is derived,
    never stored as a separate identity (C2); unknown keys are refused;
    a malformed signed path is refused; the axis field is never empty.
    Status: ok | absent | invalid | refused, with a reason."""
    if not isinstance(record, dict):
        return {"status": "invalid", "reason": "the node record is not an object"}
    if "address" in record:
        return {"status": "refused",
                "reason": ("the node record stores an address field — "
                           "addressing is derived from the node directory, "
                           "never stored as a separate identity (PRD §5.3)")}
    unknown = set(record.keys()) - _NODE_KNOWN
    if unknown:
        return {"status": "refused",
                "reason": "unknown node record field(s): %s"
                          % ", ".join(sorted(unknown))}
    missing = _NODE_REQUIRED - set(record.keys())
    if missing:
        return {"status": "invalid",
                "reason": "missing node record field(s): %s"
                          % ", ".join(sorted(missing))}
    field = record.get("axis", {}).get("field")
    try:
        field_handoff(field)
    except ValueError as exc:
        return {"status": "refused", "reason": str(exc)}
    if not isinstance(record.get("tentative"), bool):
        return {"status": "invalid",
                "reason": "tentative must be a bool (C5)"}
    path_report = validate_signed_path(record.get("signed_path"))
    if path_report["status"] != "ok":
        return {"status": "refused",
                "reason": "malformed signed path: %s"
                          % (record["signed_path"],)}
    return {"status": "ok", "reason": "the node record is lawful"}


class Descent(Driver):
    """The descent engine — extends B2's ``Driver`` (the gate walk and
    its ledger replay are inherited; the herdr socket surface is never
    re-implemented and never touched, H-B3-1).

    ``Descent(nodes_root=…, ledger_path=…, store_root=…, anchor="",
    block_version="", clock=None, resource_budget=None, world=None,
    skill_ref=…, tool_surface_ref=…, model_ref=…)`` — every path and
    quantity is a parameter.  ``clock`` is the ledger clock (default:
    B0's own); fixtures pass a fixed clock so a run is byte-reproducible
    (lens 5).  ``resource_budget`` is the walk's step budget — the only
    loop bound, and it is a RESOURCE, never a depth cap (C7-1, C7-3).
    ``world`` is the caller-supplied fixture world (the stand-in for
    the desk walk and the human's acts — P4a's attest-provider
    pattern); the engine never fabricates any of it and never writes
    ``state: "attested"``.
    """

    def __init__(self, nodes_root, ledger_path, store_root, anchor="",
                 block_version="", clock=None, resource_budget=None,
                 world=None, skill_ref="descent-skill@1",
                 tool_surface_ref="descent-tool@1",
                 model_ref="descent-model@1"):
        if not validate_word(anchor):
            raise ValueError("anchor %r is not a word" % (anchor,))
        super().__init__(
            ledger_path=ledger_path,
            desk_gates=grammar.DESK_GATES,
            desk_addresses=cell_desk_addresses(anchor),
            course=grammar.COURSE,
            blocks={},
            block_version="" if block_version is None else block_version,
            lens=_NeutralLens(),
            socket_path=None,
        )
        self.nodes_root = nodes_root
        self.store_root = store_root
        self.anchor = anchor
        self._clock = clock
        self.resource_budget = resource_budget
        self.world = world
        self.skill_ref = skill_ref
        self.tool_surface_ref = tool_surface_ref
        self.model_ref = model_ref
        self.block_store = block.BlockStore(store_root)
        self.arrangement_store = arrangement.ArrangementStore(
            os.path.join(store_root, "arrangements"))

    # -- node IO -----------------------------------------------------------

    def node_dir(self, address):
        _check_word(address)
        return os.path.join(self.nodes_root, word_to_disk(address))

    def read_node(self, address):
        """Read a node back, honestly classified: absent (missing or
        empty — sha256 of empty is e3b0c44298fc…, never valid) |
        invalid | refused | ok (lens 3)."""
        _check_word(address)
        path = os.path.join(self.node_dir(address), "cell.node.json")
        try:
            with open(path, "rb") as handle:
                raw = handle.read()
        except FileNotFoundError:
            return {"status": "absent", "address": address,
                    "reason": "no cell.node.json at nodes/%s"
                              % word_to_disk(address)}
        except OSError as exc:
            return {"status": "absent", "address": address,
                    "reason": "cell.node.json unreadable: %s" % exc}
        if not raw:
            return {"status": "absent", "address": address,
                    "sha256": EMPTY_SHA256,
                    "reason": ("the node record is empty — the sha256 of "
                               "empty is e3b0c44298fc…, never valid")}
        try:
            record = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            return {"status": "invalid", "address": address,
                    "reason": "cell.node.json is not JSON (%s)" % exc}
        report = validate_node_record(record)
        if report["status"] != "ok":
            return {"status": report["status"], "address": address,
                    "reason": report["reason"]}
        return {"status": "ok", "address": address, "record": record,
                "sha256": hashlib.sha256(raw).hexdigest()}

    def _write_node(self, address, field, delta, signed_path, tentative,
                    seed_ref=None, arrangement_ref=None):
        """Write one child node record.  The address is NEVER written —
        it is the directory's name, derived, not stored (PRD §5.3)."""
        record = {"axis": {"field": field, "delta": list(delta)},
                  "signed_path": signed_path,
                  "tentative": tentative}
        if seed_ref is not None:
            record["seed_ref"] = seed_ref
        if arrangement_ref is not None:
            record["arrangement"] = arrangement_ref
        node_dir = self.node_dir(address)
        os.makedirs(node_dir, exist_ok=True)
        with open(os.path.join(node_dir, "cell.node.json"), "w",
                  encoding="utf-8") as handle:
            handle.write(canonical_json(record) + "\n")
        return record

    def _write_seed(self, address, anchor):
        """The tentative seed in the node's own file (PRD §13.1 D7) — a
        ref to the carried field, never content, never the podium.  The
        descent has NO write path to question.md (PRD §2.1, T-R3-02)."""
        text = "⟦tentative seed⟧\nref: %s\n" % anchor
        seed_path = os.path.join(self.node_dir(address), "seed.md")
        with open(seed_path, "w", encoding="utf-8") as handle:
            handle.write(text)
        return ("nodes/%s/seed.md@sha256:%s"
                % (word_to_disk(address),
                   hashlib.sha256(text.encode("utf-8")).hexdigest()))

    # -- the arrangement (P4b, imported — never re-authored) --------------

    def seat_arrangement(self, cell_address):
        """Seat one full P4b arrangement at ``cell_address``: five desks
        at the cell's seat addresses, each instruction block the desk's
        full-cell bundle from the P4b grammar, each desk naming its four
        blocks (no naked agents — R4).  New cells only; re-seating an
        existing name@version raises (the toy changes by writing a new
        arrangement, never by editing — L2)."""
        _check_word(cell_address)
        stamp = hashlib.sha256(cell_address.encode("utf-8")).hexdigest()[:10]
        name = "cell-" + stamp
        version = "1"  # carried, never invented (H-B3-5)
        desks = {}
        for letter in grammar.COURSE:
            seat = grammar.seat_address(cell_address, letter)
            block_id = "cell-%s-%s" % (stamp, letter.lower())
            bundle = grammar.render_bundle(seat, letter)
            self.block_store.author(
                block_id, version, "instruction",
                {"instruction.md": bundle.encode("utf-8")},
                authored_by_run="R04-B3-descent@%s"
                                % (cell_address if cell_address else "_"),
                attested_by=None)
            desks[letter] = {
                "address": seat,
                "runtime": ("hermes-desk-adapter" if letter == "S"
                            else "pi"),
                "instruction": "%s@%s" % (block_id, version),
                "skills": [self.skill_ref],
                "tool_surface": self.tool_surface_ref,
                "model": self.model_ref,
                "model_route": "reasoning",
                "tars": _TARS[letter],
            }
        record = self.arrangement_store.author(
            name, version, desks,
            {"python": "3.12.3", "herdr": "0.8.2", "pi": "0.84.2",
             "node": "22.23.2"},
            {"ledger_path": self.ledger_path})
        return {"ref": "%s@%s" % (name, version), "record": record}

    # -- records (engine-written: seeds, refusals, the MOVING stop) --------

    def _append(self, record):
        with LedgerWriter(self.ledger_path, clock=self._clock) as writer:
            return writer.append(record)

    def _refusal_record(self, address, gate, payload_ref, corruption,
                        field, verdict, tentative):
        """A recorded refusal — a silent refusal is indistinguishable
        from a success and is therefore a bug (§8).  The keying follows
        B2's REFUSAL_ATTEMPT_PREFIX pattern, imported."""
        authority = self._authority()
        n = len(authority["by_pair"].get((address, gate), []))
        record = make_record(
            address=address, gate=gate, state="held-pending",
            mark="mechanical", payload_ref=payload_ref,
            axis={"field": field, "delta": []},
            axis_verdict=verdict, corruption=corruption,
            tentative=tentative,
            turn_key=turn_key(address, gate,
                              REFUSAL_ATTEMPT_PREFIX + str(n),
                              self.block_version),
            block_version=self.block_version, attestation_ref=None)
        return self._append(record)

    # -- the guard pass (D.12-class, GS-* — P4b's D-7 numbering pattern) --

    def guard_pass(self, address):
        """The guard pass at ONE node and depth — L1 L2 L3 L4 V∅
        (PRD §5.5).  Each item carries its citation; a V with no ∞0′ is
        REFUSED (seal line 8, R6); anything unobservable reads
        INCONCLUSIVE, never clean (lens 6).  The node's corruption is
        the first flagged code in the sealed order, or null."""
        node = self.read_node(address)
        authority = self._authority()
        records = [r for r in authority["records"]
                   if r.get("address") == address]
        items = []

        def item(item_id, verdict, citation, evidence):
            items.append({"id": item_id, "verdict": verdict,
                          "citation": citation, "evidence": evidence})

        node_record = node.get("record") or {}

        # GS-VOID — no V without ∞0′.
        b_records = [r for r in records if r.get("gate") == "b"]
        if not b_records:
            item("GS-VOID", "INCONCLUSIVE",
                 "seal line 8: \"No V without ∞0'\" · PRD §5.5 (R6)",
                 "no V record is observed at this node")
        else:
            infinity_ref = node_record.get("infinity_zero_prime_ref")
            missing = [r for r in b_records
                       if not r.get("payload_ref") or not infinity_ref]
            if missing:
                item("GS-VOID", "REFUSED",
                     "seal line 8: \"No V without ∞0'\" · PRD §5.5 (R6)",
                     "a V record at this node carries no ∞0′")
            else:
                item("GS-VOID", "PASS",
                     "seal line 8: \"No V without ∞0'\" · PRD §5.5 (R6)",
                     "the V at this node carries its ∞0′")

        # GS-L1 — the arrow was skipped: a gate with no predecessor record.
        order = ("x", "y", "z", "a", "b")
        present = {r.get("gate") for r in records}
        skipped = [order[i] for i in range(1, len(order))
                   if order[i] in present and order[i - 1] not in present]
        if not records:
            item("GS-L1", "INCONCLUSIVE",
                 "L1 Closing: \"→ was skipped; an answer inserted where "
                 "emergence should occur\"",
                 "no gate records are observed at this node")
        elif skipped:
            item("GS-L1", "FLAG",
                 "L1 Closing: \"→ was skipped; an answer inserted where "
                 "emergence should occur\"",
                 "gate(s) %s have no predecessor record — the arrow was "
                 "skipped" % ", ".join(skipped))
        else:
            item("GS-L1", "PASS",
                 "L1 Closing: \"→ was skipped; an answer inserted where "
                 "emergence should occur\"",
                 "no observed gate skips its predecessor")

        # GS-L2 — the manufacturing signal, recorded honestly, never hidden.
        x_records = [r for r in records if r.get("gate") == "x"]
        machine_posed = bool(node_record.get("tentative")) or any(
            r.get("tentative") for r in x_records)
        if machine_posed:
            item("GS-L2", "FLAG",
                 "L2 Generating: \"X was generated from K instead of "
                 "received from ∞0\" · C5: tentative is temporal, never "
                 "epistemic",
                 "the S at this node is machine-posed (tentative) — the "
                 "signal is carried, never hidden; the node is non-data "
                 "until a human converts it")
        else:
            item("GS-L2", "PASS",
                 "L2 Generating: \"X was generated from K instead of "
                 "received from ∞0\"",
                 "the S at this node is not machine-posed")

        # GS-L3 — a claimed surface outside the §1.9 vocabulary, or a
        # corruption code beyond the five.  Checked through P4a's own
        # parser, imported (never re-authored).
        claimed = node_record.get("claimed_surface")
        if claimed is None:
            item("GS-L3", "INCONCLUSIVE",
                 "L3 Claiming: \"someone claims to decode ∞0 directly\" · "
                 "no L1 symbol added or renamed",
                 "the node claims no surface — nothing is observable")
        else:
            parsed = parse_surface(claimed,
                                   equation_forms=grammar.EQUATION_FORMS)
            rogue = [entry["name"] for entry in parsed.get("symbols", [])
                     if not entry.get("in_vocabulary")]
            extra_codes = [code for code in parsed.get("corruption_codes", [])
                           if code not in CORRUPTION_CODES]
            if rogue or extra_codes:
                item("GS-L3", "FLAG",
                     "L3 Claiming: \"someone claims to decode ∞0 directly\"",
                     "the claimed surface declares symbol(s) outside the "
                     "§1.9 vocabulary (%s) or corruption code(s) beyond "
                     "the five (%s)" % (", ".join(rogue),
                                        ", ".join(extra_codes)))
            elif parsed.get("status") != "lawful":
                item("GS-L3", "INCONCLUSIVE",
                     "L3 Claiming: \"someone claims to decode ∞0 directly\"",
                     "the claimed surface does not parse lawful — %s"
                     % ", ".join(parsed.get("errors", [])))
            else:
                item("GS-L3", "PASS",
                     "L3 Claiming: \"someone claims to decode ∞0 directly\"",
                     "the claimed surface stays inside the §1.9 "
                     "vocabulary and the five codes")

        # GS-L4 — performed without substance: empty or unfilled payloads.
        if not records:
            item("GS-L4", "INCONCLUSIVE",
                 "L4 Performing: \"the decoding is performed but the "
                 "operation is empty\"",
                 "no gate records are observed at this node")
        else:
            hollow = [r for r in records
                      if not r.get("payload_ref")
                      or "⟦runtime slot" in r.get("payload_ref", "")]
            if hollow:
                item("GS-L4", "FLAG",
                     "L4 Performing: \"the decoding is performed but the "
                     "operation is empty\"",
                     "record(s) carry an empty or unfilled payload: %s"
                     % ", ".join(r["gate"] for r in hollow))
            else:
                item("GS-L4", "PASS",
                     "L4 Performing: \"the decoding is performed but the "
                     "operation is empty\"",
                     "every observed payload is a filled reference")

        corruption = None
        flagged = {}
        for it in items:
            if it["verdict"] in ("FLAG", "REFUSED"):
                flagged.setdefault(it["verdict"], []).append(it)
        for code in CORRUPTION_CODES:
            if any(it["id"] == "GS-" + code for it in items
                   if it["verdict"] in ("FLAG", "REFUSED")):
                corruption = code
                break
        if any(it["verdict"] == "REFUSED" for it in items):
            status = "refused"
        elif flagged:
            status = "flagged"
        elif any(it["verdict"] == "INCONCLUSIVE" for it in items):
            status = "inconclusive"
        else:
            status = "clean"
        return {"address": address, "status": status,
                "corruption": corruption, "items": items}

    # -- the tentative audit (C5 / T-R5-02) --------------------------------

    def _tentative_audit(self, address, records):
        """A tentative node is non-data: no downstream gate may consume
        it as evidence.  The audit: the node's tentative seed reference
        must not appear as any OTHER gate record's payload_ref."""
        seed_ref = None
        for record in records:
            if record.get("gate") == "x" and record.get("tentative"):
                seed_ref = record.get("payload_ref")
        if seed_ref is None:
            return {"consumed": False, "gate": None, "seed_ref": None}
        for record in records:
            if record.get("gate") == "x":
                continue
            payload = record.get("payload_ref") or ""
            if payload and (payload == seed_ref or seed_ref in payload):
                return {"consumed": True, "gate": record["gate"],
                        "seed_ref": seed_ref}
        return {"consumed": False, "gate": None, "seed_ref": seed_ref}

    # -- the descent step (C6: gate-fails-to-lock → child + append +
    #    arrangement) ------------------------------------------------------

    def descend(self, parent_address, gate, declared_field=None):
        """ONE descent step.  Requires a REAL trigger: the parent's
        (address, gate) record must exist, be held-pending, and carry
        no attestation — a gate that failed to lock.  Then: the child
        address is appended through the declared convention (spot 1),
        the arrangement is seated from the P4b grammar, the axis field
        is carried byte-exact from the parent's handoff, the guard pass
        runs at the child, and the step is recorded.

        ``declared_field`` is the world's observed field at the child
        (fixture channel).  When it differs from the handoff bytes the
        verdict is MOVING and the descent STOPS at the human's level:
        the child node exists (the world's truth — the engine never
        repairs a drift), the stop is logged as a record, and nothing
        descends further (C1).  A node whose tentative seed has been
        consumed by a downstream gate is REFUSED (C5, T-R5-02).
        """
        authority = self._authority()
        records = [r for r in authority["records"]
                   if r.get("address") == parent_address
                   and r.get("gate") == gate]
        locked = any(r.get("state") == "attested"
                     and r.get("attestation_ref") for r in records)
        failing = any(r.get("state") == "held-pending"
                      and r.get("attestation_ref") is None for r in records)
        if locked or not failing:
            return {"status": "no-trigger", "parent": parent_address,
                    "gate": gate,
                    "reason": ("the gate did not fail to lock: %s"
                               % ("it is attested" if locked
                                  else "no failing record exists at this "
                                       "node — there is no descent "
                                       "material"))}
        parent = self.read_node(parent_address)
        if parent["status"] != "ok":
            return {"status": "inconclusive", "parent": parent_address,
                    "gate": gate,
                    "reason": ("the parent node is %s: %s"
                               % (parent["status"], parent["reason"]))}
        audit = self._tentative_audit(parent_address,
                                      [r for r in authority["records"]
                                       if r.get("address") == parent_address])
        if audit["consumed"]:
            parent_field = parent["record"]["axis"]["field"]
            refusal = self._refusal_record(
                parent_address, audit["gate"],
                "refusal:tentative-consumed:%s" % audit["seed_ref"],
                None, parent_field, "STASIS", False)
            return {"status": "refused", "parent": parent_address,
                    "gate": gate,
                    "reason": ("a downstream gate consumed the tentative "
                               "node's seed as evidence — a tentative node "
                               "is non-data (C5, T-R5-02)"),
                    "refusal_record_id": refusal["record_id"]}
        letter = _gate_letter(gate)
        child = zoom_in(parent_address, letter)
        if child == parent_address:
            return {"status": "refused", "parent": parent_address,
                    "gate": gate, "letter": letter,
                    "reason": ("no-movement: the root cell's centre S "
                               "seats at ε itself (P4b's declared "
                               "exception, Appendix D.7) — a descent that "
                               "does not move is not a descent")}
        child_node = self.read_node(child)
        if child_node["status"] != "absent":
            return {"status": "refused", "parent": parent_address,
                    "gate": gate, "letter": letter, "child": child,
                    "reason": ("the child node already exists — the "
                               "descent never overwrites a node")}
        parent_field = parent["record"]["axis"]["field"]
        try:
            handoff = field_handoff(parent_field)
        except ValueError as exc:
            return {"status": "refused", "parent": parent_address,
                    "gate": gate, "reason": str(exc)}
        child_field = handoff if declared_field is None \
            else dict(declared_field)
        try:
            field_handoff(child_field)
        except ValueError as exc:
            return {"status": "refused", "parent": parent_address,
                    "gate": gate, "reason": "the declared child field is "
                    "not a lawful axis field: %s" % exc}
        parent_surface = parent["record"].get("arrangement")
        child_surface = "cell-%s@1" % hashlib.sha256(
            child.encode("utf-8")).hexdigest()[:10]
        verdict = axis_verdict(parent_field, child_field,
                               parent_surface, child_surface)
        signed_path = path_between(self.anchor, child)
        seating = self.seat_arrangement(child)
        if verdict == "MOVING":
            self._write_node(child, child_field, [], signed_path,
                             tentative=True,
                             arrangement_ref=seating["ref"])
            stop = self._append(make_record(
                address=child, gate="x", state="held-pending",
                mark="mechanical",
                payload_ref="axis:moving:stop-and-surface",
                axis={"field": child_field, "delta": []},
                axis_verdict="MOVING", corruption=None, tentative=True,
                turn_key=turn_key(child, "x", PROMPT_ATTEMPT,
                                  self.block_version),
                block_version=self.block_version, attestation_ref=None))
            guard = self.guard_pass(child)
            return {"status": "moving", "parent": parent_address,
                    "gate": gate, "letter": letter, "child": child,
                    "axis_verdict": "MOVING",
                    "handoff_bytes_sha256": hashlib.sha256(
                        field_bytes(handoff)).hexdigest(),
                    "child_field_bytes_sha256": hashlib.sha256(
                        field_bytes(child_field)).hexdigest(),
                    "record_id": stop["record_id"], "guard": guard,
                    "arrangement": seating["ref"],
                    "reason": ("the axis field moved — MOVING dominates: "
                               "the descent stops at the human's level, "
                               "surfaces, logs and waits (PRD §5.4)")}
        os.makedirs(self.node_dir(child), exist_ok=False)
        seed_ref = self._write_seed(child, handoff["anchor"])
        self._write_node(child, child_field, [seed_ref], signed_path,
                         tentative=True, seed_ref=seed_ref,
                         arrangement_ref=seating["ref"])
        seed = self._append(make_record(
            address=child, gate="x", state="held-pending",
            mark="mechanical", payload_ref=seed_ref,
            axis={"field": child_field, "delta": [seed_ref]},
            axis_verdict=verdict,
            corruption="L2",   # machine-posed seed — the signal is
                               # carried honestly, never hidden
            tentative=True,
            turn_key=turn_key(child, "x", PROMPT_ATTEMPT,
                              self.block_version),
            block_version=self.block_version, attestation_ref=None))
        guard = self.guard_pass(child)
        return {"status": "descended", "parent": parent_address,
                "gate": gate, "letter": letter, "child": child,
                "axis_verdict": verdict,
                "handoff_bytes_sha256": hashlib.sha256(
                    field_bytes(handoff)).hexdigest(),
                "child_field_bytes_sha256": hashlib.sha256(
                    field_bytes(child_field)).hexdigest(),
                "seed_ref": seed_ref, "record_id": seed["record_id"],
                "guard": guard, "arrangement": seating["ref"],
                "reason": ("the child node, the appended address and the "
                           "seated arrangement are recorded; the axis "
                           "field travelled byte-exact")}

    # -- the return criterion (C4) ------------------------------------------

    def _resolve_ref(self, ref):
        """Resolve a declared ``nodes/<disk>/<file>@sha256:<hex>``
        reference against the node tree: ok (with the byte facts) |
        absent | invalid.  Missing, empty or mismatching content never
        reads valid (lens 3)."""
        if not isinstance(ref, str) or "@sha256:" not in ref:
            return {"status": "invalid", "reason": "%r is not a durable "
                    "file reference" % (ref,)}
        prefix, _, expected = ref.partition("@sha256:")
        if not prefix.startswith("nodes/") or not expected:
            return {"status": "invalid", "reason": "%r is not a "
                    "nodes/<dir>/<file>@sha256:<hex> reference" % (ref,)}
        path = os.path.join(self.nodes_root, prefix[len("nodes/"):])
        try:
            with open(path, "rb") as handle:
                raw = handle.read()
        except OSError as exc:
            return {"status": "absent", "reason": "%s unreadable: %s"
                    % (ref, exc)}
        actual = hashlib.sha256(raw).hexdigest()
        if not raw:
            return {"status": "absent",
                    "reason": ("%s resolves to an empty file — the sha256 "
                               "of empty is e3b0c44298fc…, never valid"
                               % ref)}
        if actual != expected:
            return {"status": "invalid",
                    "reason": ("%s sha256 %s does not match the declared "
                               "%s" % (ref, actual, expected))}
        return {"status": "ok", "ref": ref, "sha256": actual,
                "bytes": len(raw)}

    def evaluate_return(self, address):
        """Observe the return criterion at ``address``: artifact +
        genuine ∞0′ (PRD §B3).  The V record must exist and carry the
        human's act (a non-null attestation_ref — the human's click is
        the only authenticity authority; this module reports its
        presence, never judges genuineness, commission §6).  An
        unattested V is HELD (surface and wait); a V with no ∞0′ is
        REFUSED (V∅); an attested V missing its artifact is REFUSED —
        half a return is not a return.  The engine returns references
        and byte facts, never content (§4.7.5)."""
        node = self.read_node(address)
        if node["status"] != "ok":
            return {"status": "inconclusive", "address": address,
                    "reason": "the node is %s: %s"
                              % (node["status"], node["reason"])}
        authority = self._authority()
        b_records = [r for r in authority["records"]
                     if r.get("address") == address and r.get("gate") == "b"]
        if not b_records:
            return {"status": "inconclusive", "address": address,
                    "reason": "no V record is observed — the return "
                              "cannot be read"}
        record = node["record"]
        b = b_records[-1]
        if b.get("attestation_ref") is None:
            return {"status": "held", "address": address,
                    "reason": ("the V is unattested — the human's click "
                               "is the only authenticity authority; "
                               "surface and wait")}
        field = record["axis"]["field"]
        infinity_ref = record.get("infinity_zero_prime_ref")
        if not infinity_ref:
            refusal = self._refusal_record(
                address, "b", "refusal:v-without-infinity-zero-prime",
                "V∅", field, "STASIS", False)
            return {"status": "refused", "address": address,
                    "corruption": "V∅",
                    "refusal_record_id": refusal["record_id"],
                    "reason": ("a V with no ∞0′ is refused (seal line 8, "
                               "R6) — no artifact is accepted; the "
                               "refusal is recorded (§8)")}
        artifact_ref = record.get("artifact_ref")
        if not artifact_ref:
            refusal = self._refusal_record(
                address, "b", "refusal:v-missing-artifact", None,
                field, "STASIS", False)
            return {"status": "refused", "address": address,
                    "refusal_record_id": refusal["record_id"],
                    "reason": ("an attested V missing its artifact — "
                               "half a return is not a return (PRD §B3); "
                               "the refusal is recorded (§8)")}
        artifact = self._resolve_ref(artifact_ref)
        infinity = self._resolve_ref(infinity_ref)
        if artifact["status"] != "ok" or infinity["status"] != "ok":
            bad = artifact if artifact["status"] != "ok" else infinity
            refusal = self._refusal_record(
                address, "b", "refusal:return-ref-unresolved", None,
                field, "STASIS", False)
            return {"status": "refused", "address": address,
                    "refusal_record_id": refusal["record_id"],
                    "reason": ("the declared return reference does not "
                               "resolve: %s — never valid; the refusal "
                               "is recorded (§8)" % bad["reason"])}
        return {"status": "returned", "address": address,
                "artifact": {"ref": artifact["ref"],
                             "sha256": artifact["sha256"],
                             "bytes": artifact["bytes"]},
                "infinity_zero_prime": {"ref": infinity["ref"],
                                        "sha256": infinity["sha256"],
                                        "bytes": infinity["bytes"]},
                "reason": "artifact + genuine ∞0′ — the return criterion"}

    # -- the walk (C7-3: resources, never semantic completion) --------------

    def walk(self, start_address, script):
        """Walk the descent from ``start_address`` along the script's
        descent material.  The loop stops ONLY on resources — the step
        budget (``resource_budget``), the script's end (no more descent
        material), a no-trigger node (the gates locked — no descent
        material) — or on mandated stops: MOVING, a refusal (V∅,
        tentative-consumption, malformed material), an unobservable
        parent.  The return criterion is OBSERVED after the loop; it is
        never a break condition (C7-3).  The guard pass runs at every
        node the walk visited, every depth (C3).

        ``script`` = {"steps": [{"gate": "z"|…, "field": <declared
        child field or absent>}…], "leaf": <the leaf's V evidence, the
        world's material>}.  ``world.prepare(address, spec)`` lays the
        node's walk state (the failing-gate record, and any declared
        consumption); ``world.materialize(address, leaf)`` plays the
        leaf's V evidence — both are the caller's fixture apparatus; the
        engine never fabricates any of it.
        """
        if not isinstance(script, dict):
            raise ValueError("walk needs a script object")
        plan = script.get("steps") or []
        if not isinstance(plan, list):
            raise ValueError("the script's steps must be a list")
        steps = []
        current = start_address
        visited = [start_address]
        stopped = None
        for spec in plan:
            if (self.resource_budget is not None
                    and len(steps) >= self.resource_budget):
                stopped = "resource-exhausted"
                break
            if not isinstance(spec, dict) or spec.get("gate") not in \
                    grammar.DESK_GATES.values():
                raise ValueError("script step %r is not a gate step"
                                 % (spec,))
            if self.world is not None:
                self.world.prepare(current, spec)
            report = self.descend(current, spec.get("gate"),
                                  declared_field=spec.get("field"))
            steps.append(report)
            if report.get("status") == "no-trigger":
                # the gate locked or never happened — the descent
                # material ends here (a resource, not a completion)
                break
            if report.get("status") in ("moving", "refused",
                                        "inconclusive"):
                if report.get("child"):
                    current = report["child"]
                    visited.append(current)
                stopped = report["status"]
                break
            current = report.get("child") or current
            visited.append(current)
        if stopped is None:
            if self.world is not None:
                self.world.materialize(current, script.get("leaf") or {})
        guards = [self.guard_pass(address) for address in visited]
        ret = self.evaluate_return(current)
        final = stopped if stopped is not None else ret["status"]
        return {"status": final,
                "start": start_address, "anchor": self.anchor,
                "budget": self.resource_budget,
                "steps_taken": len(steps), "steps": steps,
                "visited": visited, "guards": guards, "return": ret}


class _NeutralLens:
    """The descent never prompts a desk (H-B3-1): the inherited B2
    driver keeps its trust assertion behind this neutral stand-in, so
    the socket surface exists but is never exercised."""

    def assert_trust(self, desk, blocks):
        return {"desk": desk, "ok": True, "reason": "the descent never "
                "prompts — fixtures only (H-B3-1)"}


# The TARS register strings per desk — PRD §2.3 (the attested
# personality table), carried into the arrangement entries.
_TARS = {
    "S": "T3 — widen the field",
    "G": "T2 — steady digging",
    "Q": "T4 — poke, never manufacture",
    "P": "hold the delicate intersection",
    "V": "open, never close",
}
