#!/usr/bin/env python3
"""surface_contract — the Codex §3.6 surface contract, in one place, versioned.

P4b is the positive side of the desk interface; P4a is the negative side
(commission §4).  The two meet at the §3.6 surface contract: P4a's
``surface.py`` declares the shape a desk's emitted surface is parsed
against, and P4b's desk bundles are written against that same declaration.
This module therefore does **not** re-declare, re-invent or fork the
contract — it imports P4a's module from ``predecessors/`` by file path,
pins the exact bytes it was imported from (sha256), and re-exports the
contract and the parser as the single place every P4b module consults.

Codex §3.6 (verbatim): "Every emitted surface must carry:
Constitutional block (§3.1) — exact
The active phase's compiled form WITH decoding operation (§3.2)
The adaptive context chain (§3.3) — what feeds in, what feeds out
The decoder rules (§3.4)
Resolved symbols for every symbol used (§1.9)
Surfaces may add behavioral, interface, and domain layers — visibly
separate from the decoding."

Fail closed: if the predecessor file is missing or its bytes do not match
the pinned sha256, importing this module raises ImportError — a contract
that cannot be verified is INCONCLUSIVE, never silently substituted.
"""

from __future__ import annotations

import hashlib
import importlib.util
import os

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
    "CREATIVE_LINE",
    "CONTRACT_VERSION",
    "CONTRACT_SOURCE_FILE",
    "CONTRACT_SOURCE_SHA256",
]

# The pinned predecessor file (P4a authored; the verifier's fence pins the
# same bytes).  Path is resolved from this file, never from a hardcoded
# absolute location, and never from sys.path.
_PREDECESSORS_DIR = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "predecessors"))
CONTRACT_SOURCE_FILE = os.path.join(_PREDECESSORS_DIR, "surface.py")
CONTRACT_SOURCE_SHA256 = (
    "776ff46393bf81db62841043021c97288e2c1414bec43971d275d1dfbdfac36d")


def _load_predecessor():
    try:
        with open(CONTRACT_SOURCE_FILE, "rb") as handle:
            raw = handle.read()
    except OSError as exc:
        raise ImportError(
            "surface_contract: the P4a contract file %s is unreadable (%s) — "
            "the §3.6 contract is INCONCLUSIVE, never substituted"
            % (CONTRACT_SOURCE_FILE, exc)) from None
    actual = hashlib.sha256(raw).hexdigest()
    if actual != CONTRACT_SOURCE_SHA256:
        raise ImportError(
            "surface_contract: %s sha256 %s does not match the pinned %s — "
            "refusing to import a drifted contract"
            % (CONTRACT_SOURCE_FILE, actual, CONTRACT_SOURCE_SHA256))
    spec = importlib.util.spec_from_file_location(
        "predecessor_surface", CONTRACT_SOURCE_FILE)
    if spec is None or spec.loader is None:
        raise ImportError(
            "surface_contract: cannot build an import spec for %s"
            % CONTRACT_SOURCE_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_surface = _load_predecessor()

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

CONTRACT_VERSION = SURFACE_CONTRACT["version"]

# Import-time self-consistency: the contract is the one P4a declared.
if CONTRACT_VERSION != 1:
    raise ImportError(
        "surface_contract: unexpected SURFACE_CONTRACT version %r"
        % (CONTRACT_VERSION,))
