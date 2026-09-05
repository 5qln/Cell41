#!/usr/bin/env python3
"""build — the integration round's fixture-world builder (declared
fixture apparatus, never the conductor).  BINDS the pinned R06 fixture
builder for the harness spec + the pattern scenarios (imported by
path/sha, never re-authored) and adds this round's own fixture data
builder: the live-cell SPEC (spec.json's schema — the provisional
declared data shape, H-INT-4) with every path caller-supplied.
Everything here is deterministic fixture fiction, clearly labelled;
nothing touches the live box and nothing writes the live ledger
(every path is caller-supplied — H-INT-1).
"""

from __future__ import annotations

import json
import os
import sys

sys.dont_write_bytecode = True

_HERE = os.path.dirname(os.path.abspath(__file__))
_AUTHORED = os.path.dirname(_HERE)
if _AUTHORED not in sys.path:
    sys.path.insert(0, _AUTHORED)

from surface_contract import fixtures_build_r06  # noqa: E402

# The pinned R06 fixture surface, re-exported never re-authored.
harness_spec = fixtures_build_r06.harness_spec
orchestrate_spec = fixtures_build_r06.orchestrate_spec
cycle_scenario = fixtures_build_r06.cycle_scenario
sequence_scenario = fixtures_build_r06.sequence_scenario
parallel_scenario = fixtures_build_r06.parallel_scenario
loop_scenario = fixtures_build_r06.loop_scenario
custom_scenario = fixtures_build_r06.custom_scenario
guard_scenario = fixtures_build_r06.guard_scenario
scenario_of = fixtures_build_r06.scenario_of
NAMES = fixtures_build_r06.NAMES
MALFORMED = fixtures_build_r06.MALFORMED

TS = fixtures_build_r06.TS
NEEDLE = fixtures_build_r06.NEEDLE
ANCHOR = fixtures_build_r06.ANCHOR
SCENARIOS_DIR = os.path.join(_HERE, "scenarios")

__all__ = [
    "harness_spec", "orchestrate_spec", "cycle_scenario",
    "sequence_scenario", "parallel_scenario", "loop_scenario",
    "custom_scenario", "guard_scenario", "scenario_of", "NAMES",
    "MALFORMED", "TS", "NEEDLE", "ANCHOR", "SCENARIOS_DIR",
    "cell_spec", "write_json", "read_json",
]


def cell_spec(work_dir, scenario, ledger, trail, live_socket=None,
              soft_config=None, materialize=None, materialized=None,
              scope="integration-fixture", wait_timeout_ms=5000,
              timeout_s=5.0, max_steps=None, observe_states=True,
              clock=fixtures_build_r06.TS, notes=None):
    """This round's live-cell spec shape (the declared data schema) —
    every path caller-supplied, the harness's own socket injected
    through ``live_socket`` (never the real box)."""
    spec = {
        "spec_version": 1,
        "round": "integration-fixture",
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
        "clock": {"kind": "fixed", "ts": clock},
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
