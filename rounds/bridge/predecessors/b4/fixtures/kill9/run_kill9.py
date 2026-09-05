#!/usr/bin/env python3
"""run_kill9 — the kill -9 fixture harness (declared fixture apparatus):
kill the conductor mid-run at a known point, then prove the FRESH
process re-arms from the ledger alone — no duplicate gate, no skipped
gate (C3, T-E3-01).

The plan:

  1. build the scratch world (the plant, through B0's writer) in the
     reference work directory;
  2. spawn the conductor as a subprocess (fresh python, its own
     session) with the fixture spec;
  3. tail the ledger from disk until it holds exactly KILL_AT records
     (a known mid-run point), then SIGKILL the conductor's whole
     process group;
  4. verify the interrupted chain from GENESIS (B0's verifier — a
     broken chain would halt, never repair);
  5. spawn a SECOND conductor process (fresh python) over the same
     ledger and trail — it must rebuild its next action from the ledger
     alone and finish the run;
  6. assert byte-identity: the final ledger and trail equal the pinned
     expected bytes of the UNINTERRUPTED run (fixtures/main_run/
     expected/*) — any duplicate or skipped gate would change those
     bytes — and assert no (address, gate) ever carries two records
     with the same turn_key.

The interrupted and re-armed runs use the same relative path string the
reference pins were generated under, so the trail bytes (which carry
the ledger path) are comparable byte for byte.  Exit 0 = the re-arm
held.  The harness is the fixture's own apparatus; the selftest runs it
as a fresh subprocess (the second process the commission's lens 5
demands).
"""

from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_AUTHORED = os.path.dirname(os.path.dirname(_HERE))
if _AUTHORED not in sys.path:
    sys.path.insert(0, _AUTHORED)
sys.path.insert(0, os.environ.get("FRACTAL_LEDGER_DIR",
                                  "/home/deploy/the-cell/ledger"))

from fractal_ledger import LedgerLoader  # noqa: E402

MAIN_DIR = os.path.normpath(os.path.join(_HERE, "..", "main_run"))
KILL_AT = 60


def _ledger_count(ledger_path):
    return LedgerLoader(ledger_path).load(write_index=False).count


def _spawn_conductor(ledger_path, trail_path, spec_path, socket_dir,
                     python):
    return subprocess.Popen(
        [python, os.path.join(_AUTHORED, "run.py"),
         "--ledger", ledger_path, "--trail", trail_path,
         "--spec", spec_path, "--socket-dir", socket_dir],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        start_new_session=True, cwd=_AUTHORED)


def _collect(process, timeout=600):
    out, err = process.communicate(timeout=timeout)
    result = json.loads(out.decode("utf-8"))
    if result.get("status") not in ("complete", "budget-held", "stalled",
                                    "step-limited"):
        raise RuntimeError("conductor returned %r; stderr: %s"
                           % (result, err.decode("utf-8", "replace")))
    return result


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


def run(python=None):
    # the interrupted and re-armed runs use the SAME relative path
    # string the reference pins were generated under, so the trail bytes
    # (which carry the ledger path) are comparable byte for byte
    rel_work = os.path.relpath(os.path.join(
        _AUTHORED, "fixtures", "main_run", "work"), _AUTHORED)
    work_dir = os.path.join(_AUTHORED, rel_work)
    python = python or sys.executable
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)
    os.makedirs(work_dir)
    spec_path = os.path.join(MAIN_DIR, "spec.json")
    ledger_path = os.path.join(work_dir, "gates.jsonl")
    trail_path = os.path.join(work_dir, "trail.jsonl")
    rel_ledger = os.path.join(rel_work, "gates.jsonl")
    rel_trail = os.path.join(rel_work, "trail.jsonl")
    rel_sock1 = os.path.join(rel_work, "sock1")
    rel_sock2 = os.path.join(rel_work, "sock2")

    # 1. the world's plant (B0's writer, the TTY stand-in — never the run)
    sys.path.insert(0, os.path.join(_AUTHORED, "fixtures"))
    import build as build_module
    build_module.write_plant(ledger_path)

    # 2. the first conductor — killed mid-run at a known point
    first = _spawn_conductor(rel_ledger, rel_trail, spec_path,
                             rel_sock1, python)
    deadline = time.monotonic() + 600
    count = 1
    while count < KILL_AT:
        if first.poll() is not None:
            raise RuntimeError("the conductor exited before the kill "
                               "point: %r" % (first.communicate(),))
        if time.monotonic() > deadline:
            first.kill()
            raise RuntimeError("the conductor never reached %d records "
                               "in time" % KILL_AT)
        time.sleep(0.05)
        count = _ledger_count(ledger_path)
    os.killpg(os.getpgid(first.pid), signal.SIGKILL)
    first.wait()

    # 3. the interrupted chain verifies from GENESIS; the kill point is
    # the count the ledger held when the kill fired (the poll and the
    # signal race by at most one record — still a known mid-run point,
    # far from both ends)
    interrupted = LedgerLoader(ledger_path).load(write_index=False)
    if not (KILL_AT <= interrupted.count <= KILL_AT + 2):
        raise RuntimeError("the kill point drifted to %d records "
                           "(wanted %d..%d)" % (interrupted.count,
                                                KILL_AT, KILL_AT + 2))
    kill_point = interrupted.count

    # 4. the SECOND process — re-arms from the ledger alone
    second = _spawn_conductor(rel_ledger, rel_trail, spec_path,
                              rel_sock2, python)
    result = _collect(second)
    if result.get("status") != "complete":
        raise RuntimeError("the re-armed run did not complete: %r"
                           % (result,))

    # 5. byte-identity with the uninterrupted run + no duplicate keys
    final_count = _verify_no_duplicate_keys(ledger_path)
    with open(ledger_path, "rb") as handle:
        actual_ledger = handle.read()
    with open(trail_path, "rb") as handle:
        actual_trail = handle.read()
    with open(os.path.join(MAIN_DIR, "expected", "gates.jsonl"),
              "rb") as handle:
        expected_ledger = handle.read()
    with open(os.path.join(MAIN_DIR, "expected", "trail.jsonl"),
              "rb") as handle:
        expected_trail = handle.read()
    if actual_ledger != expected_ledger:
        raise RuntimeError("the re-armed ledger differs from the "
                           "uninterrupted run's pinned bytes — a "
                           "duplicate or skipped gate")
    if actual_trail != expected_trail:
        raise RuntimeError("the re-armed trail differs from the "
                           "uninterrupted run's pinned bytes — the "
                           "observe repair did not hold")
    return {"status": "re-armed", "kill_point_records": kill_point,
            "final_records": final_count,
            "ledger_bytes": len(actual_ledger),
            "trail_bytes": len(actual_trail)}


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(prog="run_kill9")
    args = parser.parse_args(argv)
    result = run()
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
