#!/usr/bin/env python3
"""surface_contract — the bridge's contract seam: the attested rounds
read by path, sha-pinned (now including B4's carried trail/fixture
apparatus and this round's softconfig), and the bridge surface declared
against them.

The attested sides meet at one contract: P4a's ``surface.py`` declares
the §3.6 shape, P4b's grammar renders the desk bundles against it, B2's
driver owns the prompt→fence→read→propose mechanics (and the instrument
owns the real herdr dialect — the live desk path, C1/C2), B3's descent
owns the addressing convention, and B0's ledger owns the record chain.
This module does not re-declare, re-invent or fork any of them — it
reads each by file path, pins the exact bytes it imported (sha256), and
then declares the bridge surface (the record conventions, the trail
contract, the dependency audit, the guard policy, the cost contract,
the LIVE desk mode, and the SOFT config-read) against that contract, in
one place, versioned.

Fail closed: if a pinned predecessor file is missing or its bytes drift
from the pin, importing this module raises ImportError — a contract
that cannot be verified is INCONCLUSIVE, never silently substituted
(commission lens 6).

The folded item (commission §5) is carried here as data — the codex §2
decoding operations quoted byte-faithful, sourced from B4's pinned
``fixtures/desk.py`` so the fixture desk subprocess (and this round's
softconfig defaults) import the same bytes without pulling this
module's heavy loaders.
"""

from __future__ import annotations

import hashlib
import importlib.util
import os
import sys

# The pinned loads import the predecessors by path — never leave a
# bytecode cache beside a predecessor file (the workspace outside
# ./authored/ must stay untouched).
sys.dont_write_bytecode = True

__all__ = [
    "RUN_SURFACE",
    "CONTRACT_VERSION",
    "PINNED_FILES",
    "DESK_FIDELITY_ITEMS",
    "GUARD_FLOW_ITEMS",
    "parse_surface",
    "SURFACE_CONTRACT",
    "PHASES",
    "DECODING_OPS",
    "LENSES",
    "OUTPUT_SYMBOLS",
    "COMPILED_OUTPUTS",
    "CONTEXT_IN",
    "CONTEXT_OUT",
    "SYMBOL_VOCABULARY",
    "CREATIVE_LINE",
    "EQUATION_FORMS",
    "CORRUPTION_CODES",
    "conformance",
    "grammar",
    "block",
    "arrangement",
    "step",
    "STEP_KINDS",
    "Driver",
    "turn_key",
    "PROMPT_ATTEMPT",
    "REFUSAL_ATTEMPT_PREFIX",
    "fence_marker",
    "Instrument",
    "HerdrError",
    "AgentNotFoundError",
    "SocketTransportError",
    "DeskResolutionError",
    "CentreWriteError",
    "assert_not_centre",
    "DESK_LABELS",
    "descent",
    "load_descent",
    "DESK_FUNCTION_SPECS",
    "FOUNDING_SENTENCE",
    "ATTENTION_READINGS",
    "DESK_SHORT_OPS",
    "NEEDLE",
    "compose_answer",
    "trail",
    "b4_desk_server_path",
    "b4_build",
    "softconfig",
]

# ---------------------------------------------------------------------------
# The pinned predecessor files.  b2/p4a/p4b are the staged copies
# (commission §4: "staged under ./predecessors/…"); b3's descent and
# surface_contract and p4b's surface_contract are read from their
# canonical round directories because their own sibling-relative path
# resolution is anchored to those directories (the staged bytes are
# identical — the sha pins below are the contract either way).  B4's
# trail and fixture apparatus (the immediate predecessor — carried,
# extended, never re-authored) are read from ./predecessors/b4/, and
# this round's softconfig is pinned from ./authored/.
# ---------------------------------------------------------------------------

_HERE = os.path.dirname(os.path.abspath(__file__))
_PRED = os.path.normpath(os.path.join(_HERE, "..", "predecessors"))
_ROUNDS = os.path.normpath(os.path.join(_HERE, "..", ".."))
_LEDGER_DIR = os.environ.get(
    "FRACTAL_LEDGER_DIR", "/home/deploy/the-cell/ledger")

_B2_DIR = os.path.join(_PRED, "b2")
_P4A_DIR = os.path.join(_PRED, "p4a")
_P4B_DIR = os.path.join(_PRED, "p4b")
_B4_DIR = os.path.join(_PRED, "b4")
_P4B_CANON_DIR = os.path.join(_ROUNDS, "P4b-desk-bundles", "authored")
_B3_CANON_DIR = os.path.join(_ROUNDS, "R04-B3", "authored")

PINNED_FILES = (
    # B0 — the ledger (imported via FRACTAL_LEDGER_DIR, never copied).
    {
        "path": os.path.join(_LEDGER_DIR, "fractal_ledger.py"),
        "sha256": "b291e65967e0d1f98205a9bd612507fa788ea4f9aa99e5d6b8fa5f366895546d",
        "role": "B0 ledger and record (the chain)",
    },
    # B2 — the one-cell walk and the herdr socket surface.
    {
        "path": os.path.join(_B2_DIR, "dialects.py"),
        "sha256": "9ebc6d314bd265e5be14c9c22fb47a4b80f4fabab5c4a46dd3f9f1ca0e6a4208",
        "role": "B2 verdict dialects (unused by the run — imported as a peer of driver.py)",
    },
    {
        "path": os.path.join(_B2_DIR, "instrument.py"),
        "sha256": "159c78c12328c8fbcc841b19d52570f99e90edaebf184e6bbb3e10b8ba4bca6b",
        "role": "B2 the herdr socket adapter (the attested prompt→fence→read — the live desk path, C1)",
    },
    {
        "path": os.path.join(_B2_DIR, "lens.py"),
        "sha256": "ad46b895dc3ceb68379467d8c9b642affcfc1b214633a1de9f89d39240fd269a",
        "role": "B2 the Pi lens (never invoked — the fixture stand-in lens replaces it, H-B4-1 carried)",
    },
    {
        "path": os.path.join(_B2_DIR, "walker.py"),
        "sha256": "5889160a15c5bc6949c6cd65726aeb609d4ca54efa3f2702229da5a675a002e9",
        "role": "B2 the read-only walker data (COURSE / DESK_GATES / DESK_ADDRESSES)",
    },
    {
        "path": os.path.join(_B2_DIR, "driver.py"),
        "sha256": "397f93fc0ae01ab09ab21d22b63655546a760ab35f5138055aa9c4c999f01cf2",
        "role": "B2 the turn machine the run extends per cycle",
    },
    # P4a — the §3.6 contract, the D.12 check, the step surface.
    {
        "path": os.path.join(_P4A_DIR, "surface.py"),
        "sha256": "776ff46393bf81db62841043021c97288e2c1414bec43971d275d1dfbdfac36d",
        "role": "P4a's §3.6 surface contract and parser (the declared shape)",
    },
    {
        "path": os.path.join(_P4A_DIR, "conformance.py"),
        "sha256": "3391b9cac14f56e0d0d7aac954f77864ca84faf8401e36d82d978146e6ef404c",
        "role": "P4a's D.12 check (the run's per-step guard — imported, never re-authored)",
    },
    {
        "path": os.path.join(_P4A_DIR, "step.py"),
        "sha256": "7c02f316969fdc2a6a9825b2ce4cb264976de3c607d8438f58b4b1e94bd26edf",
        "role": "P4a's stepping surface (STEP_KINDS — the zoom glyph registry, data)",
    },
    # P4b — the desk grammar, the block model, the arrangement model.
    {
        "path": os.path.join(_P4B_DIR, "block.py"),
        "sha256": "20ac2b38ff971056d8bc9368455577da93e1b4d0ef227b0dcfd00e68214d3f5a",
        "role": "P4b block model (the run stores no blocks — imported as the grammar's peer)",
    },
    {
        "path": os.path.join(_P4B_DIR, "grammar.py"),
        "sha256": "d7ab814ca89899ecce5b9fb065588fc185eae08b3debec5573144bfba1e97f63",
        "role": "P4b desk grammar (COURSE, DESK_GATES, EQUATION_FORMS, PHASE, seat_address, render_bundle)",
    },
    {
        "path": os.path.join(_P4B_DIR, "arrangement.py"),
        "sha256": "6b50d3bb829bb2621520a87b4e3188a4976f3af57de0cda5f90433cb945e4d25",
        "role": "P4b arrangement model (the run seats no arrangement — imported as the grammar's peer)",
    },
    {
        "path": os.path.join(_P4B_CANON_DIR, "surface_contract.py"),
        "sha256": "fb166569f877d13bf5e8a8e8016f2ab37f711bde1ae8a1b0ecc3d77a3cbe199e",
        "role": "P4b's re-export of the same contract (the desk-bundle side)",
    },
    # B3 — the descent (the addressing convention the run derives cells from).
    {
        "path": os.path.join(_B3_CANON_DIR, "surface_contract.py"),
        "sha256": "46f9ce58ce9c0db2cfcf01f9e3733a3cc4a9b9c086db918b120b12223ba6ef6f",
        "role": "B3's contract seam (DESCENT_SURFACE; loads p4a/p4b canonically)",
    },
    {
        "path": os.path.join(_B3_CANON_DIR, "descent.py"),
        "sha256": "ccf33cbf5d2910393076eb076030475721b80229a8fcbeb04e4854043515828e",
        "role": "B3 descent (cell_desk_addresses — the run's per-cell seating, imported)",
    },
    # B4 — the immediate predecessor (carried, extended, never re-authored):
    # the observability trail, the folded-item carrier, the fixture desk
    # server (spawned ONLY by the two fixture modes — never in live mode),
    # and the fixture builder (the plant writer / template renderer).
    {
        "path": os.path.join(_B4_DIR, "trail.py"),
        "sha256": "fd3f557c1983657077068e3a9f1f0acde4e8031c1f6fd8e70947169421da1903",
        "role": "B4 trail — the observability deliverable (imported by path, never re-authored)",
    },
    {
        "path": os.path.join(_B4_DIR, "fixtures", "desk.py"),
        "sha256": "0d8c47fd90a69a47107b78c143f4a59c33d4468ee5ce18f52446f1119303a06d",
        "role": "B4 fixture desk — the codex §2 desk function-specs, byte-faithful (the folded item; the softconfig defaults' bytes)",
    },
    {
        "path": os.path.join(_B4_DIR, "fixtures", "desk_server.py"),
        "sha256": "36e71eb81664a6e704dcf7f5fb3c18e2369051d4e459d0cf5dbcafcdc092a95d",
        "role": "B4 fixture desk server — spawned ONLY by the two fixture modes (H-B4-1); the live mode never spawns it (C2)",
    },
    {
        "path": os.path.join(_B4_DIR, "fixtures", "build.py"),
        "sha256": "b6a4e22190d1742750766fa6f28288e500352776d0472225571b584355aa3e1a",
        "role": "B4 fixture builder — the plant writer and the §3.6 template renderer (the bridge's fixtures reuse it by path)",
    },
    # This round's config-read — pinned so a drifted softconfig refuses
    # the import: the read path itself is INCONCLUSIVE, never silently
    # substituted (lens 3/6).
    {
        "path": os.path.join(_HERE, "softconfig.py"),
        "sha256": "17ccf2ba65991f4c6c2f0dd5e618d013fb5c0817c73077998529dedfcfeb46b4",
        "role": "bridge softconfig — the runtime config-read (C3/C4)",
    },
)


def _load_pinned(pinned, module_name, path_entries=()):
    """Load one pinned file by path under ``module_name``, refusing
    (ImportError) when the bytes drift from the pin.  ``path_entries``
    is inserted at sys.path[0] for the load only, so the module's sibling
    imports resolve inside its own round."""
    if pinned["sha256"].startswith("TBD"):
        raise ImportError(
            "surface_contract: %s has no pin (TBD placeholder) — the "
            "contract is INCONCLUSIVE, never substituted" % pinned["path"])
    try:
        with open(pinned["path"], "rb") as handle:
            raw = handle.read()
    except OSError as exc:
        raise ImportError(
            "surface_contract: the pinned file %s is unreadable (%s) — the "
            "attested surface is INCONCLUSIVE, never substituted"
            % (pinned["path"], exc)) from None
    actual = hashlib.sha256(raw).hexdigest()
    if actual != pinned["sha256"]:
        raise ImportError(
            "surface_contract: %s sha256 %s does not match the pinned %s — "
            "refusing to import a drifted contract"
            % (pinned["path"], actual, pinned["sha256"]))
    saved = sys.path[:]
    try:
        for entry in reversed(path_entries):
            sys.path.insert(0, entry)
        spec = importlib.util.spec_from_file_location(module_name, pinned["path"])
        if spec is None or spec.loader is None:
            raise ImportError(
                "surface_contract: cannot build an import spec for %s"
                % pinned["path"])
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path[:] = saved


def _pin_for(path):
    for pinned in PINNED_FILES:
        if os.path.abspath(pinned["path"]) == os.path.abspath(path):
            return pinned
    raise ImportError("surface_contract: no pin entry for %s" % path)


if _LEDGER_DIR not in sys.path:
    sys.path.insert(0, _LEDGER_DIR)
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

# -- the one §3.6 contract (P4a's surface.py) -------------------------------
_surface = _load_pinned(_pin_for(os.path.join(_P4A_DIR, "surface.py")),
                        "surface", path_entries=(_P4A_DIR,))

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

# -- B4's fixture desk's folded specs (stdlib-only; pinned above) ----------
# The codex §2 desk function-specs and his-word attention readings — the
# bytes the softconfig declared defaults are (byte-exact, C4).
_desk = _load_pinned(
    _pin_for(os.path.join(_B4_DIR, "fixtures", "desk.py")), "b4_desk",
    path_entries=(os.path.join(_B4_DIR, "fixtures"),))
DESK_FUNCTION_SPECS = _desk.DESK_FUNCTION_SPECS
FOUNDING_SENTENCE = _desk.FOUNDING_SENTENCE
ATTENTION_READINGS = _desk.ATTENTION_READINGS
DESK_SHORT_OPS = _desk.DESK_SHORT_OPS
NEEDLE = _desk.NEEDLE
compose_answer = _desk.compose_answer

# -- B2's driver chain ------------------------------------------------------
_dialects = _load_pinned(_pin_for(os.path.join(_B2_DIR, "dialects.py")),
                         "dialects", path_entries=(_B2_DIR,))
_instrument = _load_pinned(_pin_for(os.path.join(_B2_DIR, "instrument.py")),
                           "instrument", path_entries=(_B2_DIR,))
_lens = _load_pinned(_pin_for(os.path.join(_B2_DIR, "lens.py")),
                     "lens", path_entries=(_B2_DIR,))
_walker = _load_pinned(_pin_for(os.path.join(_B2_DIR, "walker.py")),
                       "walker", path_entries=(_B2_DIR,))
_driver = _load_pinned(_pin_for(os.path.join(_B2_DIR, "driver.py")),
                       "driver", path_entries=(_B2_DIR,))

Driver = _driver.Driver
turn_key = _driver.turn_key
PROMPT_ATTEMPT = _driver.PROMPT_ATTEMPT
REFUSAL_ATTEMPT_PREFIX = _driver.REFUSAL_ATTEMPT_PREFIX
fence_marker = _instrument.fence_marker
Instrument = _instrument.Instrument
HerdrError = _instrument.HerdrError
AgentNotFoundError = _instrument.AgentNotFoundError
SocketTransportError = _instrument.SocketTransportError
DeskResolutionError = _instrument.DeskResolutionError
CentreWriteError = _instrument.CentreWriteError
assert_not_centre = _instrument.assert_not_centre
DESK_LABELS = _instrument.DESK_LABELS

# -- P4a's D.12 check and the step registry ---------------------------------
conformance = _load_pinned(
    _pin_for(os.path.join(_P4A_DIR, "conformance.py")), "conformance",
    path_entries=(_P4A_DIR,))
step = _load_pinned(_pin_for(os.path.join(_P4A_DIR, "step.py")), "p4a_step",
                    path_entries=(_P4A_DIR,))
STEP_KINDS = step.STEP_KINDS
# conformance evaluates lazily with the plain names of its own round —
# bind them so the imported check resolves its peers, never substitutes.
sys.modules["step"] = step
sys.modules.setdefault("surface", _surface)

# -- P4b's grammar / block / arrangement -----------------------------------
block = _load_pinned(_pin_for(os.path.join(_P4B_DIR, "block.py")), "block",
                     path_entries=(_P4B_DIR,))
grammar = _load_pinned(_pin_for(os.path.join(_P4B_DIR, "grammar.py")),
                       "grammar", path_entries=(_P4B_DIR,))
arrangement = _load_pinned(_pin_for(os.path.join(_P4B_DIR, "arrangement.py")),
                           "arrangement", path_entries=(_P4B_DIR,))
_p4b_surface_contract = _load_pinned(
    _pin_for(os.path.join(_P4B_CANON_DIR, "surface_contract.py")),
    "p4b_surface_contract_module", path_entries=(_P4B_CANON_DIR,))

EQUATION_FORMS = grammar.EQUATION_FORMS
CORRUPTION_CODES = tuple(("L1", "L2", "L3", "L4", "V∅"))

CONTRACT_VERSION = SURFACE_CONTRACT["version"]
if _p4b_surface_contract.CONTRACT_VERSION != CONTRACT_VERSION:
    raise ImportError(
        "surface_contract: P4b's contract version %r differs from P4a's %r"
        % (_p4b_surface_contract.CONTRACT_VERSION, CONTRACT_VERSION))

# -- B4's carried apparatus -------------------------------------------------
trail = _load_pinned(_pin_for(os.path.join(_B4_DIR, "trail.py")), "trail",
                     path_entries=(_B4_DIR,))
_desk_server = _load_pinned(
    _pin_for(os.path.join(_B4_DIR, "fixtures", "desk_server.py")),
    "b4_desk_server", path_entries=(os.path.join(_B4_DIR, "fixtures"),))
b4_desk_server_path = os.path.join(_B4_DIR, "fixtures", "desk_server.py")
b4_build = _load_pinned(
    _pin_for(os.path.join(_B4_DIR, "fixtures", "build.py")), "b4_build",
    path_entries=(os.path.join(_B4_DIR, "fixtures"),))

# -- B3's descent (lazy: its own surface_contract must bind the plain name
#    "surface_contract" while it loads) -------------------------------------
_descent = None


def load_descent():
    """Load B3's descent once (its ``import surface_contract`` resolves
    against B3's own contract seam, then the plain name is restored)."""
    global _descent
    if _descent is not None:
        return _descent
    for _name, _path in (("P4B_DESK_BUNDLES_DIR",
                          os.path.join(_ROUNDS, "P4b-desk-bundles", "authored")),
                         ("P4A_STEP_MODE_DIR",
                          os.path.join(_ROUNDS, "P4a-step-mode", "authored")),
                         ("B2_DRIVER_DIR",
                          os.path.join(_ROUNDS, "R03-B2", "authored"))):
        os.environ.setdefault(_name, _path)
    b3_sc = _load_pinned(
        _pin_for(os.path.join(_B3_CANON_DIR, "surface_contract.py")),
        "b3_surface_contract", path_entries=(_B3_CANON_DIR,))
    saved_sc = sys.modules.get("surface_contract")
    sys.modules["surface_contract"] = b3_sc
    try:
        _descent = _load_pinned(
            _pin_for(os.path.join(_B3_CANON_DIR, "descent.py")),
            "b3_descent", path_entries=(_B3_CANON_DIR,))
    finally:
        if saved_sc is None:
            sys.modules.pop("surface_contract", None)
        else:
            sys.modules["surface_contract"] = saved_sc
    return _descent


def descent():
    return load_descent()


# -- this round's config-read (pinned above — a drifted softconfig refuses
#    the import) ------------------------------------------------------------
softconfig = _load_pinned(_pin_for(os.path.join(_HERE, "softconfig.py")),
                          "softconfig", path_entries=(_HERE,))


# ---------------------------------------------------------------------------
# The bridge's declared surface — the guard policy, the record conventions,
# the trail contract, the audit, the budget, the LIVE desk mode, and the
# SOFT config-read.  Every field carries its citation; the declaration is
# data, never logic (B3's DESCENT_SURFACE precedent).
# ---------------------------------------------------------------------------

# The per-step guard (the imported D.12 check, conformance.evaluate) runs
# after every step with the true observed context.  The run's TURN-VALIDITY
# policy on the report is this data: a FAIL in any DESK-FIDELITY item (an
# item whose subject is the desk's own emitted surface or decoding) holds
# the gate — the turn never completes, the hold is recorded, the run keeps
# moving.  A FAIL in a GUARD-FLOW item (P4a's attestation-based reading of
# "context flows father → daughter") is the unattended world's own truth —
# nothing is attested by design (T-R5-03) — and is carried, never hidden,
# beside the run's own schedule invariant RUN-FLOW (separately numbered,
# B3's GS-* precedent: the D.12-class check, never re-numbered).
DESK_FIDELITY_ITEMS = frozenset((
    "AD-SYN-2", "AD-SYN-3", "AD-SYN-4", "AD-SYN-5",
    "CX-SYN-1", "CX-SYN-2", "CX-SYN-3", "CX-SYN-4", "CX-SYN-5", "CX-SYN-6",
    "R1", "R2", "R7", "R8",
))
GUARD_FLOW_ITEMS = frozenset(("AD-SEM-1", "CX-SEM-1", "DC-DECODE"))

RUN_SURFACE = {
    "version": 2,
    "round": "bridge (R05-B4 extended)",
    "what": (
        "the bridge: a LIVE desk mode joins the conductor to the live "
        "herdr socket through the attested B2 instrument (C1/C2), and a "
        "runtime config-read (softconfig) replaces the hard-coded "
        "DESK_FUNCTION_SPECS / COST_MODEL literals as the conductor's "
        "source of truth (C3/C4) — everything attested in B4 is carried "
        "unchanged (C6)"),
    "cells": {
        "rule": ("the run's cells are caller-supplied data (the spec's "
                 "\"cells\" list), never a literal — no code assumes the "
                 "current cell is the root (Appendix D.2); the address "
                 "alphabet is P4b's grammar.COURSE, imported"),
        "seating": ("each cell's seat addresses derive through B3's "
                    "descent.cell_desk_addresses (the D.2 inner-first "
                    "convention, imported — never re-authored)"),
    },
    "schedule": {
        "rule": ("the run's next action is a pure function of the ledger "
                 "alone: verify the chain, then scan ROUNDS of one cycle "
                 "per cell — cells in declared order, cycles ascending, "
                 "stages in COURSE order; the first due action in that "
                 "order is next.  A cycle's seed precedes its turns; a "
                 "turn is due only when its father's completed record "
                 "exists (RUN-FLOW — the D.12 semantic flow, read on "
                 "the unattended record surface); a hold at a gate "
                 "suspends that cell's cycle forever (never retried, "
                 "never resolved) while other cells keep moving"),
        "stop": ("the loop stops only on resources: the caller-supplied "
                 "cycle target (a budget, never a hard-coded cap), the "
                 "spend ceiling (a recorded hold), a step limit, or a "
                 "stall (no runnable material — every gate held or "
                 "complete).  The return criterion is observed after the "
                 "loop, never a break condition"),
    },
    "turn_key": {
        "formula": ("B2's turn_key imported: sha256(address ‖ gate ‖ "
                    "attempt ‖ block_version), no separator"),
        "attempt": ("\"cycle:<c>\" for the seed and the four turns of "
                    "cycle c — derived from the ledger alone, so a fresh "
                    "process recomputes the same key (C3 idempotency); "
                    "\"hold:<n>\" (n = records at the (address, gate)) "
                    "for hold records — B2's refusal keying pattern"),
        "block_version": "\"\" — no block identity is observable, and inventing one is forbidden (H-B3-5 carried)",
    },
    "records": {
        "seed": ("gate x at the cell's S seat: held-pending, mechanical, "
                 "tentative true, corruption L2 (the machine-posed "
                 "signal, carried honestly — B3's precedent), "
                 "attestation_ref null, axis anchored at the seed ref. "
                 "The seed never reaches the podium and is never "
                 "prompted (T-R3-02, H-B4-4)"),
        "turn": ("gates y z a b: held-pending, mechanical, tentative "
                 "true, corruption null, attestation_ref null, axis "
                 "anchored at the payload ref — B2's proposal shape, "
                 "carried"),
        "hold": ("the gate that failed to lock: held-pending, "
                 "mechanical, tentative true, attestation_ref null; "
                 "kinds: outage (adapter error — an unreachable live "
                 "socket included, C2) · blocked (the desk announced no "
                 "surface, or the live desk resolves to a pane with no "
                 "agent — detail \"agent_not_found\", C2) · guard-fail "
                 "(a DESK-FIDELITY FAIL) · budget-ceiling (the "
                 "run-ending stop).  A hold is never auto-resolved: no "
                 "code path writes attested or attestation_ref on any "
                 "machine record (T-O5-02)"),
        "payload_ref": {
            "kinds": ("\"fenced:sha256:<hex>\" — the desk's fenced answer "
                      "(B2's convention, imported); \"seed:sha256:<hex>\" "
                      "— a durable ref binding the carried ∞0′ (or the "
                      "plant's field anchor, for a cell's cycle 0) to "
                      "the seeding place, hex = sha256(source_ref ‖ \" ‖ "
                      "cell \" ‖ cell ‖ \" ‖ cycle \" ‖ c); "
                      "\"hold:<kind>:<detail>\" — space-free, "
                      "scheme-prefixed (R11's lawful ref shape)"),
            "rule": ("a durable reference, never content (§4.7.5, D12)"),
        },
        "plant": ("the human's record (gate x, address \"\", attested, "
                  "emergent) is the run's origin — the fixture world "
                  "writes it (the TTY act's stand-in, P4a's "
                  "attest-provider precedent); the run never writes "
                  "state attested and never invokes cell-attest (C6)"),
    },
    "seeding": {
        "rule": ("when a cycle's V answer carries an ∞0′ slot, the run "
                 "seeds the cell's next S with tentative: true (C2, "
                 "§5.5); the seed carries the ∞0′ reference, never its "
                 "content, and no downstream gate may consume it as "
                 "evidence (C5)"),
        "cycle0": ("a non-root cell's cycle-0 seed carries the plant's "
                   "field anchor ref; the root cell's cycle 0 S IS the "
                   "plant (nothing is written — the human's act)"),
        "live": ("in live mode the V answer's bytes exist nowhere on "
                 "disk (D12: references, never content), so the seed's "
                 "source reference is the V turn record's own "
                 "payload_ref (fenced:sha256:<digest>) — re-derivable "
                 "from the ledger alone, never regenerated, never "
                 "guessed (C7)"),
    },
    "budget": {
        "rule": ("model spend is accounted BEFORE each turn: the charge "
                 "for the due turn is added to the spend the ledger "
                 "already accounts (a pure function of the completed "
                 "turn records — re-armable from the ledger alone); "
                 "spend + charge > ceiling ⇒ a held gate is recorded at "
                 "the due (address, gate) and the run stops cleanly — "
                 "never a silent kill, never a spend past the ceiling "
                 "(C4, PRD §10.3)"),
        "charges": ("read through softconfig.budget_of — the declared "
                    "defaults are cost.COST_MODEL['charges'] "
                    "(conservative: each charge ≥ the measured turn "
                    "cost; the live per-Pi measurement awaits a "
                    "constituted desk, H-B4-2 carried), and the soft "
                    "layer overrides them at runtime (C3)"),
    },
    "live_mode": {
        "rule": ("cost.DeskAdapter's third mode: open_turn returns "
                 "TurnContext(live_socket_path, None) — the resolved "
                 "live herdr socket (the spec's \"live_socket\" override"
                 " > HERDR_SOCKET_PATH > ~/.config/herdr/herdr.sock), "
                 "process None, NO desk_server.py spawn of any kind "
                 "(C1/C2).  The conductor's existing Instrument path "
                 "then speaks the real herdr dialect through the "
                 "imported B2 adapter: label-resolve on every turn, "
                 "agent.prompt to the resolved pane, fenced read via "
                 "pane.wait_for_output to ⟦END …⟧ (C1)"),
        "fail_closed": ("an unreachable live socket surfaces as an "
                        "outage hold; a desk resolving to a pane with "
                        "no agent (agent_not_found) surfaces as a "
                        "blocked hold with detail \"agent_not_found\" — "
                        "never a fixture stand-in, never a guessed "
                        "answer, never clean (C2, lens 6); the centre "
                        "guard refuses S/podium before any byte (K4, "
                        "T-R3-02)"),
    },
    "soft_config": {
        "rule": ("the conductor's prompt and budget paths read through "
                 "softconfig: each desk's codex §2 emphasis, voice and "
                 "model, and the declared charges + default mode, come "
                 "from a soft-layer config file at runtime — the "
                 "hard-coded DESK_FUNCTION_SPECS / COST_MODEL literals "
                 "are the DECLARED DEFAULTS, never the conductor's "
                 "source of truth (C3, K5)"),
        "path": ("the spec's \"soft_config\" (caller-supplied data) > "
                 "the SOFT_CONFIG_PATH env var > "
                 "~/.config/herdr/soft.json (the declared default "
                 "location — H-BRIDGE-2: provisional; the constitution "
                 "writes the real soft files)"),
        "statuses": ("defaults (absent file → B4's exact bytes/values — "
                     "the fixture run is unchanged, C4/C6) · ok (a "
                     "complete soft config was read and validated) · "
                     "inconclusive (empty / malformed / partial file — "
                     "the conductor refuses to boot with the reason, "
                     "never a silently substituted value, lens 3/6)"),
        "bytes": ("every emphasis/voice/model/charge byte passes "
                  "through verbatim — the enumerated glyph forms and "
                  "the encoding-lens bytes (∞0′ → ‖) are never "
                  "normalised (K2, lens 4)"),
    },
    "trail": {
        "two_trails": ("the formation trail (the field — everything that "
                       "happened) and the gate ledger (the chain — only "
                       "B″ fruits and his attestations) are two files, "
                       "never merged: trail.py refuses a trail path "
                       "equal to the ledger path, and the ledger is "
                       "written through fractal_ledger only, never by "
                       "hand"),
        "contract": ("trail.py's TRAIL_SCHEMA: append-only JSONL, one "
                     "line per event, prev_hash + event_hash chained, "
                     "UTF-8 passthrough, fsync per line; readable "
                     "mid-run — a reader replays the complete prefix "
                     "(a torn tail is flagged and discarded, never a "
                     "line, never valid) and projects a consistent "
                     "partial view"),
        "d12": ("the trail records what the context decoded TO — slot "
                "references (sha256 + byte length), never the desk's "
                "text, never the context (D12)"),
    },
    "audit": {
        "rule": ("the dependency audit (C5, T-R5-02) walks every gate "
                 "record's payload_ref chain — each payload_ref resolves "
                 "to the FIRST record in chain order carrying that "
                 "reference (the producer: every run record anchors its "
                 "axis at its own payload_ref), transitively; a later "
                 "record carrying the same reference consumed it as "
                 "evidence, and any gate whose evidence chain reaches a "
                 "tentative: true record is a FAIL.  The audit runs "
                 "end-to-end over the whole ledger, once, after the "
                 "loop — the run surfaces the report, never repairs, "
                 "never resolves"),
        "verdicts": ("PASS (no chain reaches a tentative record) | FAIL "
                     "(with the consuming record and the tentative "
                     "record reached) | INCONCLUSIVE (no records — "
                     "nothing is observable, lens 6)"),
    },
    "guard": {
        "check": ("conformance.evaluate — P4a's D.12 check, imported, "
                  "run after every step with the true observed context "
                  "and recorded in the trail line"),
        "policy": ("a FAIL in any DESK-FIDELITY_ITEMS item (or an "
                   "answer whose surface does not parse lawful) holds "
                   "the gate — the turn never completes; a FAIL in "
                   "GUARD_FLOW_ITEMS is the unattended world's own "
                   "truth (nothing is attested, T-R5-03) and is carried "
                   "beside the RUN-FLOW invariant above — never hidden, "
                   "never read as clean (lens 6)"),
    },
    "folded_item": {
        "rule": ("the five desk function-specs are the codex §2 decoding "
                 "operations, run in attention mode on the not-yet-found "
                 "question — quoted byte-faithful (DESK_FUNCTION_SPECS, "
                 "sourced from B4's pinned fixtures/desk.py; they are "
                 "the softconfig defaults' bytes, C4); no new decoding "
                 "operation, no new L1 symbol, no renamed symbol (D.12)"),
        "founding_sentence": FOUNDING_SENTENCE,
        "specs": DESK_FUNCTION_SPECS,
        "attention_readings": ATTENTION_READINGS,
        "short_ops": DESK_SHORT_OPS,
    },
}
