#!/usr/bin/env python3
"""run_restart — the cold-restart fixture harness (declared fixture
apparatus, lens 5): a NEW process re-arms the live mode AND the
config-read from disk alone, byte-identical.

The plan:

  1. build the scratch world under the canonical relative work path
     (cwd = authored/): the plant (B0's writer, the TTY stand-in), the
     run-spec (the committed spec + the injected scratch live socket),
     and the fixture live server (constituted=all) on its own socket;
  2. the spec declares NO mode and the soft config's budget.default_mode
     is "live" — so the first process resolves the LIVE mode FROM the
     soft layer, and every prompt/budget byte comes from the soft file
     at runtime (C3/C7);
  3. process ONE (a fresh python) runs the first N actions and stops
     step-limited;
  4. process TWO (a fresh python, no in-memory state from process one)
     rebuilds its next action from the ledger alone and finishes the
     run;
  5. assert byte-identity: the final ledger and trail equal the pinned
     bytes of the UNINTERRUPTED run (fixtures/restart/expected/*) — any
     duplicate or skipped gate, or any drift in the re-read soft
     values, would change those bytes — and assert no (address, gate)
     ever carries two records with the same turn_key;
  6. assert the soft values actually read through: the boot line's mode
     is "live" (resolved from the soft layer), the run-end spend equals
     the soft live charges, and the trail carries the soft override's
     needle bytes.

Exit 0 = the re-arm held; the report is JSON.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_AUTHORED = os.path.dirname(os.path.dirname(_HERE))
if _AUTHORED not in sys.path:
    sys.path.insert(0, _AUTHORED)
sys.path.insert(0, os.environ.get("FRACTAL_LEDGER_DIR",
                                  "/home/deploy/the-cell/ledger"))

import fixtures.build as build  # noqa: E402
import fixtures.live_server as live_server_module  # noqa: E402
from fractal_ledger import LedgerLoader  # noqa: E402

RESTART_DIR = _HERE
SPEC_PATH = os.path.join(RESTART_DIR, "spec.json")
SOFT_PATH = os.path.join(RESTART_DIR, "soft.json")
SPLIT_AT = 7
NEEDLE = build.NEEDLE


def _verify_no_duplicate_keys(ledger_path):
    loaded = LedgerLoader(ledger_path).load(write_index=False)
    seen = set()
    for record in loaded.records:
        pair = (record["address"], record["gate"], record["turn_key"])
        if pair in seen:
            raise RuntimeError("duplicate turn_key on the ledger: %r"
                               % (pair,))
        seen.add(pair)
    return loaded.count


def _spawn(ledger_path, trail_path, spec_path, socket_dir, max_actions,
           python):
    command = [python, os.path.join(_AUTHORED, "run.py"),
               "--ledger", ledger_path, "--trail", trail_path,
               "--spec", spec_path, "--socket-dir", socket_dir]
    if max_actions is not None:
        command += ["--max-actions", str(max_actions)]
    return subprocess.Popen(command, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, cwd=_AUTHORED)


def _collect(process, wanted, timeout=600):
    out, err = process.communicate(timeout=timeout)
    result = json.loads(out.decode("utf-8"))
    if result.get("status") != wanted:
        raise RuntimeError("conductor returned %r (wanted %r); stderr: "
                           "%s" % (result.get("status"), wanted,
                                   err.decode("utf-8", "replace")))
    return result


def run(python=None):
    python = python or sys.executable
    rel_work = os.path.relpath(RESTART_DIR, _AUTHORED)
    work = os.path.join(rel_work, "work")
    if os.path.exists(work):
        shutil.rmtree(work)
    os.makedirs(work)

    spec = build.read_spec(SPEC_PATH)
    if not isinstance(spec.get("soft_config"), str) \
            or not os.path.exists(spec["soft_config"]):
        raise RuntimeError("the restart spec does not declare its soft "
                           "config on disk — nothing to re-arm")
    spec["live_socket"] = os.path.join(work, "live.sock")
    run_spec_path = os.path.join(work, "run-spec.json")
    build.write_spec(run_spec_path, spec)

    ledger = os.path.join(work, "gates.jsonl")
    trailp = os.path.join(work, "trail.jsonl")
    build.b4_build.write_plant(ledger)

    # the fixture live box stays up across BOTH processes — like the
    # real live box, it is the environment, not the re-arm state
    server = live_server_module.LiveServer(spec, spec["live_socket"],
                                           constituted="all")
    server.start()
    try:
        first = _spawn(ledger, trailp, run_spec_path,
                       os.path.join(work, "sock1"), SPLIT_AT, python)
        _collect(first, "step-limited")
        second = _spawn(ledger, trailp, run_spec_path,
                        os.path.join(work, "sock2"), None, python)
        final = _collect(second, "complete")
    finally:
        server.halt()

    final_count = _verify_no_duplicate_keys(ledger)
    with open(ledger, "rb") as handle:
        actual_ledger = handle.read()
    with open(trailp, "rb") as handle:
        actual_trail = handle.read()
    with open(os.path.join(RESTART_DIR, "expected", "gates.jsonl"),
              "rb") as handle:
        expected_ledger = handle.read()
    with open(os.path.join(RESTART_DIR, "expected", "trail.jsonl"),
              "rb") as handle:
        expected_trail = handle.read()
    if actual_ledger != expected_ledger:
        raise RuntimeError("the re-armed ledger differs from the "
                           "uninterrupted run's pinned bytes — a "
                           "duplicate or skipped gate, or a drifted "
                           "re-read")
    if actual_trail != expected_trail:
        raise RuntimeError("the re-armed trail differs from the "
                           "uninterrupted run's pinned bytes — the "
                           "config-read or the live re-arm did not hold")

    # the re-armed run's own shape, re-derived independently here: the
    # boot resolved the mode FROM the soft layer, the soft needle
    # bytes rode the prompts, and the run-end spend equals the soft
    # live charges (cells × cycle_target turns per desk)
    lines = [json.loads(line) for line in open(trailp, encoding="utf-8")
             if line.strip()]
    boot = next(line for line in lines if line.get("event") == "boot")
    run_end = next(line for line in lines
                   if line.get("event") == "run-end")
    if boot["content"].get("mode") != "live":
        raise RuntimeError("the restart run did not resolve the live "
                           "mode from the soft layer: %r"
                           % (boot["content"],))
    if NEEDLE not in actual_trail.decode("utf-8"):
        raise RuntimeError("the soft override's needle bytes did not "
                           "ride the re-armed trail")
    soft_charges = build.restart_soft_config()["budget"]["charges"]["live"]
    # the spend re-derived independently from the LEDGER alone (the
    # same pure rule the conductor accounts) with the soft live charges
    desk_of_gate = {"y": "G", "z": "Q", "a": "P", "b": "V"}
    spend = 0
    for record in LedgerLoader(ledger).load(write_index=False).records:
        payload = record.get("payload_ref") or ""
        if not payload.startswith("fenced:"):
            continue
        desk = desk_of_gate.get(record.get("gate"))
        if desk is None:
            continue
        spend += soft_charges[desk]
    expected_spend = spend
    if run_end["content"].get("spend") != expected_spend:
        raise RuntimeError("the re-armed spend %r does not equal the "
                           "soft live charges %d"
                           % (run_end["content"].get("spend"),
                              expected_spend))

    return {"status": "re-armed", "split_at": SPLIT_AT,
            "final_result": final.get("status"),
            "final_records": final_count,
            "ledger_bytes": len(actual_ledger),
            "trail_bytes": len(actual_trail),
            "mode_from_soft": boot["content"].get("mode"),
            "spend": run_end["content"].get("spend")}


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(prog="run_restart")
    parser.parse_args(argv)
    result = run()
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
