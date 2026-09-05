#!/usr/bin/env python3
"""build — the bindings round's fixture-world builder (declared fixture
apparatus, never the production surface).  Binds the pinned R06 fixture
surface through the seam (the harness spec, the pattern scenarios) and
adds this round's own fixture data: the cell SPEC builder, the needle,
and the scratch-world helpers.  Every path is caller-supplied; nothing
touches the live box and nothing writes the live ledger (H-R08-1).
Deterministic, stdlib-only.
"""

from __future__ import annotations

import json
import os
import sys

sys.dont_write_bytecode = True

_HERE = os.path.dirname(os.path.abspath(__file__))
_AUTHORED = os.path.dirname(_HERE)
_SEAM = ("/home/deploy/the-cell/rounds/"
         "R07-integration/authored")
if _SEAM not in sys.path:
    sys.path.insert(0, _SEAM)
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import surface_contract as sc  # noqa: E402  (the seam — fixture apparatus import)

# The pinned R06 fixture surface, re-exported never re-authored.
harness_spec = sc.fixtures_build_r06.harness_spec
scenario_of = sc.fixtures_build_r06.scenario_of
NAMES = sc.fixtures_build_r06.NAMES
TS = sc.fixtures_build_r06.TS
NEEDLE = "∞0′ → ‖"

# The live plant's declared ref (read from the attested gates plant
# record — the question standing at the centre, byte-for-byte).
PLANT_REF = ("plant:sha256:a5935788fe3c6803284257c6bbc9e2914ac40"
             "a6698ec4ba62dce50345deb130e")


def cell_spec(work_dir, scenario, ledger, trail, live_socket=None,
              soft_config=None, materialize=None, materialized=None,
              scope="bindings-fixture", wait_timeout_ms=5000,
              timeout_s=5.0, max_steps=None, observe_states=True,
              notes=None):
    """The cell spec shape (the declared SPEC_SCHEMA data) — every path
    caller-supplied, the harness's own socket injected through
    ``live_socket`` (never the real box)."""
    spec = {
        "spec_version": 1,
        "round": "bindings-fixture",
        "work_dir": work_dir,
        "scenario": scenario,
        "ledger": ledger,
        "trail": trail,
        "live_socket": live_socket,
        "socket_dir": None,
        "materialize": materialize,
        "materialized": materialized,
        "soft_config": soft_config,
        "observe_states": observe_states,
        "block_version": "",
        "scope": scope,
        "clock": {"kind": "fixed", "ts": TS},
        "wait_timeout_ms": wait_timeout_ms,
        "timeout_s": timeout_s,
        "max_steps": max_steps,
    }
    if notes:
        spec["notes"] = dict(notes)
    return spec


def write_json(path, data):
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(data, ensure_ascii=False, sort_keys=True,
                                separators=(",", ":")) + "\n")


def read_json(path):
    with open(path, "rb") as handle:
        return json.loads(handle.read().decode("utf-8"))
