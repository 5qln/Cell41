#!/usr/bin/env python3
"""build — the orchestration round's fixture-world builder (declared
fixture apparatus, never the conductor): the four pattern scenarios +
the cycle + the malformed set (DATA — JSON files, never code), the
harness spec (the §3.6 surface templates via B4's pinned builder —
the imported grammar, never re-authored), and the orchestrate spec
builder.  Everything here is deterministic fixture fiction, clearly
labelled; nothing touches the live box and nothing writes the live
ledger (every path is caller-supplied — H-ORCH-1).

The scenarios carry NO pattern/topology key (the signs are the
topology, D.6 — the navigator derives sequence/parallel/loop/custom
from the signed paths alone).  The scenario files are the diff-able
data artifacts (K5).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

sys.dont_write_bytecode = True

_HERE = os.path.dirname(os.path.abspath(__file__))
_AUTHORED = os.path.dirname(_HERE)
if _AUTHORED not in sys.path:
    sys.path.insert(0, _AUTHORED)

import surface_contract  # noqa: E402  (the sha-pinned seam)
from surface_contract import b4_build  # noqa: E402

TS = "2026-08-30T12:00:00.000000Z"
NEEDLE = "∞0′ → ‖"  # the encoding-lens bytes (commission lens 4)
ANCHOR = "plant:sha256:" + hashlib.sha256(
    b"fixture-plant-anchor").hexdigest()

SCENARIOS_DIR = os.path.join(_HERE, "scenarios")


def harness_spec(omit_infinity=False):
    """The desk harness spec — the §3.6 surface templates rendered by
    B4's pinned builder (the grammar's own surface blocks), the
    no-V-without-∞0′ refusal switch."""
    return {
        "surface_templates": b4_build.render_templates(),
        "omit_infinity": bool(omit_infinity),
    }


def orchestrate_spec(live_socket=None, materialize=None,
                     materialized=None, observe_states=True,
                     scope="orchestration-fixture"):
    """The orchestrate spec — every path a parameter; the live socket
    is the fixture harness's own (never the real box)."""
    return {
        "scope": scope,
        "live_socket": live_socket,
        "materialize": materialize,
        "materialized": materialized,
        "observe_states": observe_states,
        "block_version": "",
        "clock": {"kind": "fixed", "ts": TS},
        "wait_timeout_ms": 5000,
        "timeout_s": 5.0,
    }


def _scenario(word_value, seed, paths, nodes=None, loop=None):
    data = {"word": word_value, "seed": seed, "paths": paths}
    if nodes:
        data["nodes"] = nodes
    if loop:
        data["loop"] = loop
    return data


def cycle_scenario():
    """The 4+1 cycle — S (ε, the seed) → G → Q → P → V → ∞0′: the
    clockwise read of one cell (D.1).  The signs read daughter (ε →
    G) then cousins (G→Q, Q→P, P→V — the corners share the father ε);
    the return is V's ∞0′ slot, never a walk step (D.8)."""
    return _scenario(
        "SGQPV",
        {"address": "", "ref": ANCHOR},
        [
            {"from": "", "to": "G", "path": "−G"},
            {"from": "G", "to": "Q", "path": "+·−Q"},
            {"from": "Q", "to": "P", "path": "+·−P"},
            {"from": "P", "to": "V", "path": "+·−V"},
        ],
        nodes={
            "": {"general_tools": ["search"]},
            "G": {"general_tools": ["search", "write-doc"]},
            "Q": {"general_tools": ["search", "write-doc",
                                    "write-code"]},
            "P": {"general_tools": ["search", "write-doc", "write-code",
                                    "activate"]},
            "V": {"general_tools": ["activate"]},
        },
    )


def sequence_scenario():
    """Sequence — a daughter chain (every path k = 0): ε → G → QG →
    PQG — zoom in = append (D.3's S → SG → SGQ chain)."""
    return _scenario(
        "SGQP",
        {"address": "", "ref": ANCHOR},
        [
            {"from": "", "to": "G", "path": "−G"},
            {"from": "G", "to": "QG", "path": "−Q"},
            {"from": "QG", "to": "PQG", "path": "−P"},
        ],
    )


def parallel_scenario():
    """Parallel — cousins converging on a father: the branches QG and
    PG (cousins: QG → PG = +·−P, k = m = 1) both hand off to the
    shared father-frame G (PG → G = +, m = 0)."""
    return _scenario(
        "SGQPG",
        {"address": "", "ref": ANCHOR},
        [
            {"from": "", "to": "G", "path": "−G"},
            {"from": "G", "to": "QG", "path": "−Q"},
            {"from": "QG", "to": "PG", "path": "+·−P"},
            {"from": "PG", "to": "G", "path": "+"},
        ],
    )


def loop_scenario():
    """Loop — append until a bound: the seed declares the bound (word
    length 4 — the seed's boundary; D.2 has no terminal condition),
    the loop appends G Q G Q … until the address reaches it."""
    return _scenario(
        "SGGQG",
        {"address": "", "ref": ANCHOR,
         "bound": {"kind": "word_length", "value": 4}},
        [
            {"from": "", "to": "G", "path": "−G"},
        ],
        loop={"append": "GQ"},
    )


def custom_scenario():
    """Custom — a free word composition: daughter, daughter, then a
    cousins leap to V (QG → V = ++·−V, k = 2, m = 1).  The signs
    match none of the three named shapes."""
    return _scenario(
        "SGQV",
        {"address": "", "ref": ANCHOR},
        [
            {"from": "", "to": "G", "path": "−G"},
            {"from": "G", "to": "QG", "path": "−Q"},
            {"from": "QG", "to": "V", "path": "++·−V"},
        ],
    )


def guard_scenario():
    """The centre-guard fixture: the walk revisits the seed's address
    (a second S visit) — the conductor must refuse it before any
    byte (K4)."""
    return _scenario(
        "SGS",
        {"address": "", "ref": ANCHOR},
        [
            {"from": "", "to": "G", "path": "−G"},
            {"from": "G", "to": "", "path": "+"},
        ],
    )


MALFORMED = {
    "empty-word": {"word": "", "seed": {"address": "", "ref": ANCHOR},
                   "paths": [{"from": "", "to": "G", "path": "−G"}]},
    "bad-letter": {"word": "SGZPV",
                   "seed": {"address": "", "ref": ANCHOR},
                   "paths": [{"from": "", "to": "G", "path": "−G"}]},
    "ascii-hyphen": {"word": "SG",
                     "seed": {"address": "", "ref": ANCHOR},
                     "paths": [{"from": "", "to": "G", "path": "-G"}]},
    "not-normalized": {"word": "SGQ",
                       "seed": {"address": "", "ref": ANCHOR},
                       "paths": [{"from": "", "to": "G", "path": "−G"},
                                 {"from": "G", "to": "Q",
                                  "path": "−Q"}]},
    "word-mismatch": {"word": "SGP",
                      "seed": {"address": "", "ref": ANCHOR},
                      "paths": [{"from": "", "to": "G", "path": "−G"},
                                {"from": "G", "to": "Q",
                                 "path": "+·−Q"}]},
    "broken-chain": {"word": "SGQ",
                     "seed": {"address": "", "ref": ANCHOR},
                     "paths": [{"from": "", "to": "G", "path": "−G"},
                               {"from": "Q", "to": "Q",
                                "path": ""}]},
    "topology-enum": {"word": "SG", "pattern": "sequence",
                      "seed": {"address": "", "ref": ANCHOR},
                      "paths": [{"from": "", "to": "G", "path": "−G"}]},
    "unknown-tool": {"word": "SG",
                     "seed": {"address": "", "ref": ANCHOR},
                     "paths": [{"from": "", "to": "G", "path": "−G"}],
                     "nodes": {"G": {"general_tools": ["teleport"]}}},
    "unbounded-loop": {"word": "SGG",
                       "seed": {"address": "", "ref": ANCHOR},
                       "paths": [{"from": "", "to": "G", "path": "−G"}],
                       "loop": {"append": "G"}},
}

NAMES = ("cycle", "sequence", "parallel", "loop", "custom", "guard")


def scenario_of(name):
    return {
        "cycle": cycle_scenario,
        "sequence": sequence_scenario,
        "parallel": parallel_scenario,
        "loop": loop_scenario,
        "custom": custom_scenario,
        "guard": guard_scenario,
    }[name]()


def write_json(path, data):
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(data, ensure_ascii=False, sort_keys=True,
                                separators=(",", ":")) + "\n")


def read_json(path):
    with open(path, "rb") as handle:
        return json.loads(handle.read().decode("utf-8"))


def build_all(out_dir):
    """Write every fixture scenario file under out_dir (the diff-able
    data artifacts — K5) plus the harness spec."""
    for name in NAMES:
        write_json(os.path.join(out_dir, name + ".json"),
                   scenario_of(name))
    for name, data in MALFORMED.items():
        write_json(os.path.join(out_dir, "malformed-" + name + ".json"),
                   data)
    write_json(os.path.join(out_dir, "harness-spec.json"),
               harness_spec())
    write_json(os.path.join(out_dir, "harness-spec-omit-infinity.json"),
               harness_spec(omit_infinity=True))


def main(argv=None):
    parser = argparse.ArgumentParser(prog="build")
    parser.add_argument("--out", default=SCENARIOS_DIR)
    args = parser.parse_args(argv)
    os.makedirs(args.out, exist_ok=True)
    build_all(args.out)
    print("scenarios written under %s" % args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
