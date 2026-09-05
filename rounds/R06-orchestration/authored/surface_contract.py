#!/usr/bin/env python3
"""surface_contract — the orchestration round's contract seam: the
attested rounds read by path, sha-pinned (now including the bridge's
four files, this round's word / navigate / materialize, and the
fixture seam), and the orchestration surface declared against them.

The attested sides meet at one contract: P4a's ``surface.py`` declares
the §3.6 shape, P4b's grammar renders the desk bundles against it, B2's
driver + instrument own the prompt→fence→read mechanics and the real
herdr dialect (the live desk path), B3's descent owns the addressing
convention (the word, the signed path, the zoom primitives), B4's trail
owns the observability apparatus, the bridge owns the live desk mode
(``cost.DeskAdapter`` mode ``"live"``) and the runtime config-read
(``softconfig``), and B0's ledger owns the record chain.  This module
does not re-declare, re-invent or fork any of them — it reads each by
file path, pins the exact bytes it imported (sha256), and then declares
the orchestration surface (the scenario schema, the sign-walk patterns,
the materializer defaults, the trace conventions, the guard policy) in
one place, versioned.

Fail closed: if a pinned predecessor file is missing or its bytes drift
from the pin, importing this module raises ImportError — a contract
that cannot be verified is INCONCLUSIVE, never silently substituted
(commission lens 6).

Load-anchor note (declared, never hidden): the bridge's and B3's own
contract files resolve their sibling imports relative to their own
round directories (the bridge's ``_PRED``/``_ROUNDS`` anchors and B3's
``surface_contract``/``descent`` anchors), so — exactly as the bridge
itself reads B3 from B3's canonical round directory ("the staged bytes
are identical — the sha pins below are the contract either way") —
this round reads the bridge's four files from ``rounds/bridge/authored/``
and B3's two files from ``rounds/R04-B3/authored/``, pinned against the
staged ``./predecessors/`` bytes (verified identical on this box).  A
drifted canonical copy refuses the import the same as a drifted staged
copy: the pin is the contract.
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
    "PINNED_FILES",
    "CONTRACT_VERSION",
    "ORCHESTRATION_SURFACE",
    "SURFACE_CONTRACT",
    "parse_surface",
    "CREATIVE_LINE",
    "EQUATION_FORMS",
    "CORRUPTION_CODES",
    "PHASES",
    "grammar",
    "block",
    "arrangement",
    "install",
    "conformance",
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
    "validate_signed_path",
    "path_between",
    "apply_signed_path",
    "zoom_in",
    "zoom_out",
    "deep_letter",
    "validate_word",
    "EMPTY_SHA256",
    "DESK_FUNCTION_SPECS",
    "FOUNDING_SENTENCE",
    "ATTENTION_READINGS",
    "compose_answer",
    "b4_build",
    "b4_desk_server_path",
    "trail",
    "FormationTrail",
    "read_trail",
    "TRAIL_VERSION",
    "TRAIL_FIELDS",
    "cost",
    "DeskAdapter",
    "TurnContext",
    "live_socket_path",
    "softconfig",
    "load_soft_config",
    "DECLARED_MODEL",
    "bridge_run",
    "load_bridge_run",
    "seed_ref",
    "audit_payload_chains",
    "word",
    "navigate",
    "materialize",
    "DESK_FIDELITY_ITEMS",
    "GUARD_FLOW_ITEMS",
]

_HERE = os.path.dirname(os.path.abspath(__file__))
_PRED = os.path.normpath(os.path.join(_HERE, "..", "predecessors"))
_ROUNDS = os.path.normpath(os.path.join(_HERE, "..", ".."))
_LEDGER_DIR = os.environ.get(
    "FRACTAL_LEDGER_DIR", "/home/deploy/the-cell/ledger")

_B2_DIR = os.path.join(_PRED, "b2")
_P4A_DIR = os.path.join(_PRED, "p4a")
_P4B_DIR = os.path.join(_PRED, "p4b")
_B3_DIR = os.path.join(_PRED, "b3")
_B4_DIR = os.path.join(_PRED, "b4")
_BRIDGE_DIR = os.path.join(_PRED, "bridge")
# The canonical load anchors (see the module docstring): the bridge's and
# B3's own sibling-relative resolution lives inside their round dirs.
_BRIDGE_CANON_DIR = os.path.join(_ROUNDS, "bridge", "authored")
_B3_CANON_DIR = os.path.join(_ROUNDS, "R04-B3", "authored")

# ---------------------------------------------------------------------------
# The pinned predecessor files.  The staged bytes are the contract; the
# canonical bridge/B3 copies are the load anchors (identical bytes).
# ---------------------------------------------------------------------------

PINNED_FILES = (
    {
        "path": os.path.join(_LEDGER_DIR, "fractal_ledger.py"),
        "sha256": "b291e65967e0d1f98205a9bd612507fa788ea4f9aa99e5d6b8fa5f366895546d",
        "role": "B0 ledger and record (the chain — via FRACTAL_LEDGER_DIR, never copied)",
    },
    {
        "path": os.path.join(_B2_DIR, "dialects.py"),
        "sha256": "9ebc6d314bd265e5be14c9c22fb47a4b80f4fabab5c4a46dd3f9f1ca0e6a4208",
        "role": "B2 verdict dialects",
    },
    {
        "path": os.path.join(_B2_DIR, "instrument.py"),
        "sha256": "159c78c12328c8fbcc841b19d52570f99e90edaebf184e6bbb3e10b8ba4bca6b",
        "role": "B2 the herdr socket adapter (the attested prompt→fence→read — the live desk path)",
    },
    {
        "path": os.path.join(_B2_DIR, "lens.py"),
        "sha256": "ad46b895dc3ceb68379467d8c9b642affcfc1b214633a1de9f89d39240fd269a",
        "role": "B2 the Pi lens",
    },
    {
        "path": os.path.join(_B2_DIR, "walker.py"),
        "sha256": "5889160a15c5bc6949c6cd65726aeb609d4ca54efa3f2702229da5a675a002e9",
        "role": "B2 the read-only walker data (COURSE / DESK_GATES / DESK_ADDRESSES)",
    },
    {
        "path": os.path.join(_B2_DIR, "driver.py"),
        "sha256": "397f93fc0ae01ab09ab21d22b63655546a760ab35f5138055aa9c4c999f01cf2",
        "role": "B2 the turn machine (turn_key — the trace's keying)",
    },
    {
        "path": os.path.join(_P4A_DIR, "surface.py"),
        "sha256": "776ff46393bf81db62841043021c97288e2c1414bec43971d275d1dfbdfac36d",
        "role": "P4a's §3.6 surface contract and parser (the declared shape)",
    },
    {
        "path": os.path.join(_P4A_DIR, "conformance.py"),
        "sha256": "3391b9cac14f56e0d0d7aac954f77864ca84faf8401e36d82d978146e6ef404c",
        "role": "P4a's D.12 check (the per-step guard — imported, never re-authored)",
    },
    {
        "path": os.path.join(_P4A_DIR, "step.py"),
        "sha256": "7c02f316969fdc2a6a9825b2ce4cb264976de3c607d8438f58b4b1e94bd26edf",
        "role": "P4a's stepping surface (STEP_KINDS — the zoom glyph registry, data)",
    },
    {
        "path": os.path.join(_P4B_DIR, "block.py"),
        "sha256": "20ac2b38ff971056d8bc9368455577da93e1b4d0ef227b0dcfd00e68214d3f5a",
        "role": "P4b block model",
    },
    {
        "path": os.path.join(_P4B_DIR, "grammar.py"),
        "sha256": "d7ab814ca89899ecce5b9fb065588fc185eae08b3debec5573144bfba1e97f63",
        "role": "P4b desk grammar (COURSE, DESK_GATES, EQUATION_FORMS, PHASE, seat_address, render_bundle)",
    },
    {
        "path": os.path.join(_P4B_DIR, "arrangement.py"),
        "sha256": "6b50d3bb829bb2621520a87b4e3188a4976f3af57de0cda5f90433cb945e4d25",
        "role": "P4b arrangement model",
    },
    {
        "path": os.path.join(_P4B_DIR, "install.py"),
        "sha256": "06282c6e293e4c4d04b3077955ed6748341f4acecb025da7998780c60f01d22e",
        "role": "P4b the desk-bundle installer (imported — the constitution seats; this round never installs)",
    },
    {
        "path": os.path.join(_B3_DIR, "descent.py"),
        "sha256": "ccf33cbf5d2910393076eb076030475721b80229a8fcbeb04e4854043515828e",
        "role": "B3 descent (the address grammar: validate_signed_path, path_between, apply_signed_path, zoom primitives — imported, never re-authored)",
        "load_from": os.path.join(_B3_CANON_DIR, "descent.py"),
    },
    {
        "path": os.path.join(_B3_DIR, "surface_contract.py"),
        "sha256": "46f9ce58ce9c0db2cfcf01f9e3733a3cc4a9b9c086db918b120b12223ba6ef6f",
        "role": "B3's contract seam (DESCENT_SURFACE — the signed-path field's declaration)",
        "load_from": os.path.join(_B3_CANON_DIR, "surface_contract.py"),
    },
    {
        "path": os.path.join(_B4_DIR, "run.py"),
        "sha256": "5a798bbda07d037879a359e981c91f24962b86f48c285d03c87052e1b996896f",
        "role": "B4 the unattended run (pinned; the bridge's run.py is its carried-and-extended form — the load-bearing run)",
    },
    {
        "path": os.path.join(_B4_DIR, "cost.py"),
        "sha256": "f9ddb7a0bba616220937592b20ed5bc04556267433b9d5e61833f74404f5bb03",
        "role": "B4 cost (pinned; the bridge's cost.py is its carried-and-extended form — the load-bearing cost)",
    },
    {
        "path": os.path.join(_B4_DIR, "trail.py"),
        "sha256": "fd3f557c1983657077068e3a9f1f0acde4e8031c1f6fd8e70947169421da1903",
        "role": "B4 trail — the observability deliverable (imported by path, never re-authored)",
    },
    {
        "path": os.path.join(_B4_DIR, "surface_contract.py"),
        "sha256": "aa0ea654f55a093e81b445e8715ed72f2c9ab55b2f72cd6816e2b5c83bd1bb70",
        "role": "B4's contract seam (pinned; the bridge's surface_contract is its carried-and-extended form)",
    },
    {
        "path": os.path.join(_B4_DIR, "fixtures", "desk.py"),
        "sha256": "0d8c47fd90a69a47107b78c143f4a59c33d4468ee5ce18f52446f1119303a06d",
        "role": "B4 fixture desk — the codex §2 desk function-specs and the deterministic answer composer (the harness's bytes)",
    },
    {
        "path": os.path.join(_B4_DIR, "fixtures", "desk_server.py"),
        "sha256": "36e71eb81664a6e704dcf7f5fb3c18e2369051d4e459d0cf5dbcafcdc092a95d",
        "role": "B4 fixture desk server (spawned ONLY by the bridge's two fixture modes — never in live mode)",
    },
    {
        "path": os.path.join(_B4_DIR, "fixtures", "build.py"),
        "sha256": "b6a4e22190d1742750766fa6f28288e500352776d0472225571b584355aa3e1a",
        "role": "B4 fixture builder (the §3.6 surface-template renderer the harness reuses by path)",
    },
    {
        "path": os.path.join(_BRIDGE_DIR, "cost.py"),
        "sha256": "58ed8ccdc8eadb176fef8c9b92171d64a17d35df501f4eb6c4a3700ab7f6ef71",
        "role": "bridge cost — the live desk mode (DeskAdapter mode \"live\", TurnContext) — the immediate predecessor, imported",
        "load_from": os.path.join(_BRIDGE_CANON_DIR, "cost.py"),
    },
    {
        "path": os.path.join(_BRIDGE_DIR, "softconfig.py"),
        "sha256": "17ccf2ba65991f4c6c2f0dd5e618d013fb5c0817c73077998529dedfcfeb46b4",
        "role": "bridge softconfig — the runtime config-read (the READ-path; materialize.py is its WRITE-path complement)",
        "load_from": os.path.join(_BRIDGE_CANON_DIR, "softconfig.py"),
    },
    {
        "path": os.path.join(_BRIDGE_DIR, "run.py"),
        "sha256": "4d550f889bf56090dbfee68929a5243caeae3e7832e8a5fb72ab7429caaa8637",
        "role": "bridge run — the conductor (seed_ref and the dependency audit are imported, never re-authored)",
        "load_from": os.path.join(_BRIDGE_CANON_DIR, "run.py"),
    },
    {
        "path": os.path.join(_BRIDGE_DIR, "surface_contract.py"),
        "sha256": "477ba561e7e836eff01d11aeb31c8854dca5d31354f9b81520f4a451937fa0a8",
        "role": "bridge surface_contract — the immediate predecessor's contract seam",
        "load_from": os.path.join(_BRIDGE_CANON_DIR, "surface_contract.py"),
    },
    # This round's three new modules — pinned so a drifted copy refuses
    # the import (the write path itself is INCONCLUSIVE, never silently
    # substituted — lens 3/6).
    {
        "path": os.path.join(_HERE, "word.py"),
        "sha256": "4ecde1fea9828ba6bb359f1a1f184e7962fb8b62ff8251e629cd34155ece2f14",
        "role": "orchestration word — the scenario (word + signed paths), decode + validate (D.3/D.5)",
    },
    {
        "path": os.path.join(_HERE, "navigate.py"),
        "sha256": "e9d0aa1b996b9cbdb36455151147d392f423c63c238bdade3c34b440792369ce",
        "role": "orchestration navigate — the sign-walk (D.6) with the per-step D.12 check",
    },
    {
        "path": os.path.join(_HERE, "materialize.py"),
        "sha256": "52730dbd876c5269f32821db47d5cd097a6d3bb220cc731c3f6179f74d619e4b",
        "role": "orchestration materialize — the WRITE-path (zoom-in: each node its own ∞0|K cell)",
    },
)


def _pin_for(path):
    for pinned in PINNED_FILES:
        if os.path.abspath(pinned["path"]) == os.path.abspath(path):
            return pinned
    raise ImportError("surface_contract: no pin entry for %s" % path)


def _load_pinned(pinned, module_name, path_entries=(), bind_sc=False):
    """Load one pinned file by path under ``module_name``, refusing
    (ImportError) when the bytes drift from the pin.  ``path_entries``
    is inserted at sys.path[0] for the load only, so the module's sibling
    imports resolve inside its own round.  A pinned entry carrying a
    ``load_from`` anchor loads the canonical copy (byte-identical —
    verified against the pin before exec).  With ``bind_sc`` the plain
    name "surface_contract" is bound to the loading module for the
    exec's duration — the short-circuit the loaded round's own selftest
    had (the pinned p4b grammar's ``from surface_contract import
    parse_surface`` resolves against the contract, never against a
    staging copy whose own anchors are off)."""
    if pinned["sha256"].startswith("TBD"):
        raise ImportError(
            "surface_contract: %s has no pin (TBD placeholder) — the "
            "contract is INCONCLUSIVE, never substituted" % pinned["path"])
    source = pinned.get("load_from") or pinned["path"]
    try:
        with open(source, "rb") as handle:
            raw = handle.read()
    except OSError as exc:
        raise ImportError(
            "surface_contract: the pinned file %s is unreadable (%s) — the "
            "attested surface is INCONCLUSIVE, never substituted"
            % (source, exc)) from None
    actual = hashlib.sha256(raw).hexdigest()
    if actual != pinned["sha256"]:
        raise ImportError(
            "surface_contract: %s sha256 %s does not match the pinned %s — "
            "refusing to import a drifted contract"
            % (source, actual, pinned["sha256"]))
    saved = sys.path[:]
    saved_sc = sys.modules.get("surface_contract")
    try:
        for entry in reversed(path_entries):
            sys.path.insert(0, entry)
        spec = importlib.util.spec_from_file_location(module_name, source)
        if spec is None or spec.loader is None:
            raise ImportError(
                "surface_contract: cannot build an import spec for %s"
                % source)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        if bind_sc:
            sys.modules["surface_contract"] = module
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path[:] = saved
        if bind_sc:
            if saved_sc is None:
                sys.modules.pop("surface_contract", None)
            else:
                sys.modules["surface_contract"] = saved_sc


if _LEDGER_DIR not in sys.path:
    sys.path.insert(0, _LEDGER_DIR)
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

# -- the bridge's contract (the immediate predecessor) ----------------------
# Loaded with the plain name "surface_contract" bound during its exec —
# the same short-circuit the bridge's own round had (its selftest imports
# surface_contract first, so the pinned p4b grammar's ``from
# surface_contract import parse_surface`` resolves against the bridge's
# contract, never against a staging copy whose own anchors are off).
_bridge_sc = _load_pinned(
    _pin_for(os.path.join(_BRIDGE_DIR, "surface_contract.py")),
    "bridge_surface_contract", path_entries=(_BRIDGE_CANON_DIR,),
    bind_sc=True)

# The bridge's contract exports (the one §3.6 contract + the attested
# adapter surface, re-exported — never re-declared).
SURFACE_CONTRACT = _bridge_sc.SURFACE_CONTRACT
parse_surface = _bridge_sc.parse_surface
PHASES = _bridge_sc.PHASES
CREATIVE_LINE = _bridge_sc.CREATIVE_LINE
EQUATION_FORMS = _bridge_sc.EQUATION_FORMS
CORRUPTION_CODES = _bridge_sc.CORRUPTION_CODES
CONTRACT_VERSION = _bridge_sc.CONTRACT_VERSION
grammar = _bridge_sc.grammar
block = _bridge_sc.block
arrangement = _bridge_sc.arrangement
conformance = _bridge_sc.conformance
STEP_KINDS = _bridge_sc.STEP_KINDS
Driver = _bridge_sc.Driver
turn_key = _bridge_sc.turn_key
PROMPT_ATTEMPT = _bridge_sc.PROMPT_ATTEMPT
REFUSAL_ATTEMPT_PREFIX = _bridge_sc.REFUSAL_ATTEMPT_PREFIX
fence_marker = _bridge_sc.fence_marker
Instrument = _bridge_sc.Instrument
HerdrError = _bridge_sc.HerdrError
AgentNotFoundError = _bridge_sc.AgentNotFoundError
SocketTransportError = _bridge_sc.SocketTransportError
DeskResolutionError = _bridge_sc.DeskResolutionError
CentreWriteError = _bridge_sc.CentreWriteError
assert_not_centre = _bridge_sc.assert_not_centre
DESK_LABELS = _bridge_sc.DESK_LABELS
DESK_FUNCTION_SPECS = _bridge_sc.DESK_FUNCTION_SPECS
FOUNDING_SENTENCE = _bridge_sc.FOUNDING_SENTENCE
ATTENTION_READINGS = _bridge_sc.ATTENTION_READINGS
compose_answer = _bridge_sc.compose_answer
b4_build = _bridge_sc.b4_build
b4_desk_server_path = _bridge_sc.b4_desk_server_path
DESK_FIDELITY_ITEMS = _bridge_sc.DESK_FIDELITY_ITEMS
GUARD_FLOW_ITEMS = _bridge_sc.GUARD_FLOW_ITEMS
trail = _bridge_sc.trail
FormationTrail = trail.FormationTrail
read_trail = trail.read_trail
TRAIL_VERSION = trail.TRAIL_VERSION
TRAIL_FIELDS = trail.TRAIL_FIELDS
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()
softconfig = _bridge_sc.softconfig
load_soft_config = softconfig.load_soft_config
DECLARED_MODEL = softconfig.DECLARED_MODEL

# -- the bridge's cost (the live desk mode) ---------------------------------
cost = _load_pinned(
    _pin_for(os.path.join(_BRIDGE_DIR, "cost.py")), "cost",
    path_entries=(_BRIDGE_CANON_DIR,))
DeskAdapter = cost.DeskAdapter
TurnContext = cost.TurnContext
live_socket_path = cost.live_socket_path

# -- the bridge's run (seed_ref + the dependency audit — imported) ----------
_bridge_run = None


def load_bridge_run():
    """Load the bridge's run.py once, with the bridge's own plain names
    (surface_contract / cost / softconfig / trail) bound during the load
    — the same module environment its own round had."""
    global _bridge_run
    if _bridge_run is not None:
        return _bridge_run
    saved = {name: sys.modules.get(name) for name in (
        "surface_contract", "cost", "softconfig", "trail")}
    sys.modules["surface_contract"] = _bridge_sc
    sys.modules["cost"] = cost
    try:
        _bridge_run = _load_pinned(
            _pin_for(os.path.join(_BRIDGE_DIR, "run.py")), "bridge_run",
            path_entries=(_BRIDGE_CANON_DIR, _LEDGER_DIR))
    finally:
        for name, module in saved.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module
    return _bridge_run


bridge_run = None  # lazy — bound on first load_bridge_run() call


def seed_ref(source_ref, cell, cycle):
    return load_bridge_run().seed_ref(source_ref, cell, cycle)


def audit_payload_chains(records):
    return load_bridge_run().audit_payload_chains(records)


# -- B3's descent (the address grammar — imported, never re-authored) -------
_descent = None


def load_descent():
    """Load B3's descent once from its canonical round (its own
    ``surface_contract`` import resolves inside its own round — the
    load-anchor note in the module docstring)."""
    global _descent
    if _descent is not None:
        return _descent
    saved_sc = sys.modules.get("surface_contract")
    b3_sc = _load_pinned(
        _pin_for(os.path.join(_B3_DIR, "surface_contract.py")),
        "b3_surface_contract", path_entries=(_B3_CANON_DIR,))
    sys.modules["surface_contract"] = b3_sc
    try:
        _descent = _load_pinned(
            _pin_for(os.path.join(_B3_DIR, "descent.py")), "b3_descent",
            path_entries=(_B3_CANON_DIR, _LEDGER_DIR))
    finally:
        if saved_sc is None:
            sys.modules.pop("surface_contract", None)
        else:
            sys.modules["surface_contract"] = saved_sc
    return _descent


def descent():
    return load_descent()


validate_signed_path = None  # bound lazily below (kept importable)


def _bind_descent_names():
    global validate_signed_path
    if validate_signed_path is not None:
        return
    module = load_descent()
    for _name in ("validate_signed_path", "path_between",
                  "apply_signed_path", "zoom_in", "zoom_out",
                  "deep_letter", "validate_word"):
        globals()[_name] = getattr(module, _name)


_bind_descent_names()


def path_between(from_address, to_address):
    _bind_descent_names()
    return load_descent().path_between(from_address, to_address)


def apply_signed_path(from_address, text):
    _bind_descent_names()
    return load_descent().apply_signed_path(from_address, text)


def zoom_in(address, letter):
    _bind_descent_names()
    return load_descent().zoom_in(address, letter)


def zoom_out(address):
    _bind_descent_names()
    return load_descent().zoom_out(address)


def deep_letter(address):
    _bind_descent_names()
    return load_descent().deep_letter(address)


def validate_word(address):
    _bind_descent_names()
    return load_descent().validate_word(address)


# -- this round's three new modules (pinned above — imported, then pinned
#    for real by the fixture/verifier pass; the TBD pins refuse until the
#    pinning pass fills them) ------------------------------------------------
word = _load_pinned(_pin_for(os.path.join(_HERE, "word.py")), "word",
                    path_entries=(_HERE,))
navigate = _load_pinned(_pin_for(os.path.join(_HERE, "navigate.py")),
                        "navigate", path_entries=(_HERE,))
materialize = _load_pinned(_pin_for(os.path.join(_HERE, "materialize.py")),
                            "materialize", path_entries=(_HERE,))

# -- this round's contract version ------------------------------------------
_CONTRACT_VERSION = "orchestration-1"

# ---------------------------------------------------------------------------
# The orchestration surface — declared against the contract, in one place.
# Every field carries its citation; the declaration is data, never logic
# (B3's DESCENT_SURFACE precedent).
# ---------------------------------------------------------------------------

ORCHESTRATION_SURFACE = {
    "version": 1,
    "contract_version": _CONTRACT_VERSION,
    "round": "R06-orchestration (the executable Fractal)",
    "what": (
        "orchestration: the scenario is a WORD over {S,G,Q,P,V} plus the "
        "signed paths between its nodes (D.3/D.5 — data, never code); the "
        "navigation derives sequence/parallel/loop/custom from the SIGNS "
        "alone (D.6 — never a topology enum); the materializer is zoom-in "
        "(each node its own ∞0|K cell with its own tools on the K side — "
        "D.1/D.10); the orchestration drives a materialized word over the "
        "live desks via the bridge's attested live mode and lands the "
        "trace per-gate in the B0 ledger, format unchanged; every run "
        "ends in ∞0′ (no V without ∞0′)"),
    "scenario": {
        "rule": ("a scenario is DATA: {\"word\": <a non-empty word over "
                 "{S,G,Q,P,V} — the walk's letters in order>, \"seed\": "
                 "{address, ref, bound?}, \"paths\": [{\"from\", \"to\", "
                 "\"path\"} — the signed paths between the scenario's "
                 "nodes, D.5], \"nodes\": {<address>: <per-node "
                 "materialize overrides>}, \"loop\"?: {append, until "
                 "moved to seed.bound}} — never code, never a hardcoded "
                 "topology enum (any \"pattern\"/\"topology\"/\"shape\" "
                 "field is REFUSED: the signs are the topology, D.6)"),
        "word": ("D.3: \"A node is a word over the alphabet {S, G, Q, P, "
                 "V}.\" — the scenario's word lists the walk's node "
                 "letters in order; each letter's address falls out of "
                 "the declared signed paths"),
        "paths": ("D.5: \"addr(A → B) = +^k · (−x₁)(−x₂)…(−x_m)… All + "
                  "first, then all −.\" — every declared path must "
                  "normalize: it must equal path_between(from, to) "
                  "(B3's grammar, imported), and the walk's chain must "
                  "be consistent (paths[i].from == paths[i−1].to; "
                  "paths[0].from == seed.address)"),
        "validation": ("decode + validate against the Grammar: the "
                       "alphabet is P4b's grammar.COURSE (imported), the "
                       "path validator is B3's validate_signed_path "
                       "(imported — the ASCII hyphen is not the U+2212 "
                       "operator, never normalised, K2), and the "
                       "letter/address correspondence is derived through "
                       "B3's zoom primitives — a scenario that fails any "
                       "of these is malformed/INCONCLUSIVE with the "
                       "reason, never silently substituted"),
        "statuses": ("ok | absent (missing or empty — the sha256 of "
                     "empty is e3b0c44298fc…, never valid) | malformed "
                     "(not JSON, bad types, a path that does not "
                     "normalize) | inconclusive (an unbounded loop — "
                     "D.2 has no terminal condition; a declared bound "
                     "is the seed's boundary, never a navigator "
                     "constant)"),
    },
    "patterns": {
        "rule": ("orientation is read from the signs alone (D.6): "
                 "\"k = 0 → B within A (daughter) · m = 0 → A within B "
                 "(father) · k, m > 0 → neither (cousins)\".  The walk's "
                 "pattern label is DERIVED by the navigator — never "
                 "stored in the scenario"),
        "sequence": ("a daughter chain — every declared path has k = 0 "
                     "(zoom in = append, D.3's S → SG → SGQ chain)"),
        "parallel": ("cousins converging on a father — the walk holds a "
                     "cousins path (k, m > 0) whose common father "
                     "(the source stripped k letters) is later reached "
                     "by a father step (m = 0, k > 0) from the cousin "
                     "branch"),
        "loop": ("append until a bound — the scenario's seed declares "
                 "the bound (\"bound\": {kind, value}); the navigator "
                 "appends the loop's letters until the bound, and "
                 "REFUSES (INCONCLUSIVE) to expand a loop whose seed "
                 "declares no bound: D.2 \"The law has no base case and "
                 "no terminal condition\" — the bound is the seed's "
                 "boundary, never a hard-coded cap"),
        "custom": ("free word composition — any lawful walk whose signs "
                   "match none of the three named shapes (the cycle "
                   "S → G → Q → P → V → ∞0′ is one: daughter + cousins "
                   "steps, the return is V's slot, D.1/D.8)"),
        "precedence": ("loop > sequence > parallel > custom — declared "
                       "data, one place to change"),
    },
    "materialize": {
        "rule": ("the WRITE-path — the complement of the bridge's "
                 "softconfig READ-path: each node is its own lawful "
                 "cell with its own ∞0|K membrane and its own tools on "
                 "the K side (D.1, D.10).  Emitted per node: "
                 "SYSTEM.md (seat/equation/operation/hand-off — P4b "
                 "PHASE[letter] bytes), .pi/settings.json (model, "
                 "thinking, tools), skills/SKILL.md (the desk grammar "
                 "at this address — the P4b bundle), "
                 "tools/tool-surface.md (the K-side tool declaration)"),
        "defaults": ("declared DATA in materialize.MATERIALIZE_DEFAULTS: "
                     "system = PHASE[node][\"seat\"] + [\"phase_gate\"] "
                     "+ the enumerated equation + the hand-off bytes + "
                     "the One Law line (derived from the enumerated "
                     "seal form); settings = {model: "
                     "softconfig.DECLARED_MODEL (D6 — one model), "
                     "thinking: true, tools: [\"read\",\"grep\","
                     "\"bash\"] + the scenario's general tools}; "
                     "skills = grammar.render_bundle(address, letter); "
                     "tools = the declared general-tool surface.  All "
                     "caller-overridable through the scenario's node "
                     "declarations — bytes pass verbatim, never "
                     "normalised (K2)"),
        "general_tools": ("the K side may carry GENERAL tools (search / "
                          "write-doc / write-code / activate — "
                          "materialize.GENERAL_TOOLS, declared data); "
                          "the adapter stays tool-agnostic — nothing "
                          "forces 5qln-only (D.10: the membrane | is "
                          "the same line whether the K side holds a "
                          "5qln equation or a filesystem tool)"),
        "activate": ("H-ORCH-3: the materializer emits the tool "
                     "DECLARATION into the soft layer; whether a live "
                     "pi loads it is the constitution/run's concern — "
                     "the materializer declares, never executes"),
        "optional": ("\"not every run\": a run may use an "
                     "already-materialized word (the spec's "
                     "\"materialized\" dir, verified from disk — "
                     "absent/empty/drifted cells read INCONCLUSIVE, "
                     "never valid); the materialize step is optional "
                     "per run (the spec's \"materialize\" dir)"),
        "data_files": ("every emitted artifact is a data file (md / "
                       "json) — one place to change, diff-able, "
                       "versioned, never code (K5)"),
    },
    "trace": {
        "rule": ("the trace lands per-gate in the B0 ledger, format "
                 "unchanged: every record is written through "
                 "fractal_ledger.LedgerWriter (never by hand), in B2's "
                 "proposal shape — held-pending, mechanical, tentative, "
                 "attestation_ref null — keyed by B2's turn_key "
                 "(attempt \"step:<i>\"), payload_refs in the attested "
                 "conventions (fenced:sha256:<hex> / seed:sha256:<hex> "
                 "/ hold:<kind>:<detail>…).  Beside it, the "
                 "observability trail is B4's FormationTrail "
                 "(imported) — two files, never merged"),
        "hand_off": ("each turn's prompt carries the previous record's "
                     "payload_ref as CONTEXT (references only, D12); "
                     "the seed carries the scenario's declared ref; no "
                     "gate consumes a tentative seed as evidence"),
        "d12": ("the D.12 step check (P4a's conformance.evaluate, "
                "imported) runs after EVERY navigation step with the "
                "true observed context; a FAIL in DESK_FIDELITY_ITEMS "
                "holds the gate — the walk keeps moving, the hold is "
                "recorded, never auto-resolved (B4's policy, carried)"),
    },
    "return": {
        "rule": ("every run ends in ∞0′ — the seal: \"No V without "
                 "∞0'\" (R6).  A run reports complete ONLY when its "
                 "final gate is V's and the V answer's parsed surface "
                 "carries the ∞0′ slot; a V without ∞0′ is REFUSED "
                 "(a recorded hold), a walk that never reaches V ends "
                 "INCONCLUSIVE — never clean (lens 6).  The ∞0′ ref is "
                 "the run's return_question (B4's trail convention), "
                 "and it may seed the next cycle as new ∞0 (D.8)"),
    },
    "guard": {
        "centre": ("the centre guard refuses S/podium before any byte "
                   "(the imported B2 assert_not_centre — never "
                   "re-authored): the seed visit is never prompted "
                   "(the conductor is S, §4.8), and a walk whose "
                   "non-seed visit is S is refused at the guard — "
                   "zero bytes reach the socket (K4)"),
        "live": ("desk turns run through the bridge's attested live "
                 "mode: cost.DeskAdapter(mode=\"live\") → "
                 "TurnContext(live_socket, None) → the imported B2 "
                 "Instrument speaking the real herdr dialect "
                 "(label-resolve, agent.prompt, the fenced read to "
                 "⟦END …⟧).  An unreachable socket holds outage; a "
                 "desk resolving to a pane with no agent holds blocked "
                 "agent_not_found — never a fixture stand-in, never a "
                 "guessed answer, never clean (lens 6).  NO "
                 "desk_server.py spawn of any kind"),
        "states": ("the run reads real states at boot through the "
                   "attested instrument (read-only desk_states); an "
                   "absent socket is carried honestly "
                   "({\"status\": \"absent\"}) — never a fabricated "
                   "state"),
    },
    "holds": {
        "H-ORCH-1": "no desk is constituted in the live box — tested against the fixture desk harness (deterministic, no live box); a real agent.prompt to a live desk is the constitution's work",
        "H-ORCH-2": "the scenario schema is provisional (word + signed-path encoding) — candidate until Amihai touches it",
        "H-ORCH-3": "\"activate tools\" is provisional — the materializer declares, never executes",
        "H-ORCH-4": "the human's gate act is untouched — no podium write, no cell-attest, no typed word",
    },
    "lenses": {
        "1": "criterion match — each criterion measured AS WRITTEN (C1 word-not-code · C2 signs · C3 write-path · C4 general tools · C5 ledger · C6 ∞0′ · C7 prohibitions); every selftest names its criterion",
        "2": "invariant end-to-end — whole word-walk/run artifacts (sequence/parallel/loop/custom + the cycle), byte-pinned across the WHOLE run, never per call",
        "3": "absence vs validity — absent scenario / absent materialized cell / absent agent / empty file never read valid (sha256 of empty = e3b0c44298fc…)",
        "4": "encoding — ∞0′ → ‖ rides every string field (seed ref, node voice/emphasis/system overrides, the V slot) byte-verbatim; files opened binary-only, never text-mode byte sought",
        "5": "cold restart — a NEW process rebuilds the word-walk + materializer from disk alone; the selftest runs the second process",
        "6": "blind tool — an unavailable live socket or an unconstituted desk reports INCONCLUSIVE, never clean, never a fixture stand-in",
    },
}
