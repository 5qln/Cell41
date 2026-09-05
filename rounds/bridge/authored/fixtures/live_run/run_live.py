#!/usr/bin/env python3
"""run_live — the live-mode run harness (declared fixture apparatus):
a whole unattended run joined to the fixture live server through the
REAL herdr dialect, byte-pinned (C1/C2, lens 2).

Two declared server configurations, one spec:

  1. ``box`` — the LIVE box as probed (commission §3): only G carries
     an agent.  The run resolves desks by pane LABEL on every turn, G's
     turns read the ⟦END …⟧ fence through pane.wait_for_output, and
     Q/V/P hold BLOCKED with detail ``agent_not_found`` (C2's fail
     closed half) — the run ends STALLED with the holds still held,
     never complete, never clean (lens 6);
  2. ``all`` — the declared fixture fiction (G/Q/P/V constituted): a
     whole cycle completes through the live dialect — every turn
     label-resolves, prompts and reads the fence, V's ∞0′ seeds the
     next S through the live source-reference rule, and the run ends
     COMPLETE (lens 2, end-to-end).

Both variants run in-process against the deterministic live server on
its own scratch socket (never the real live socket, never a paid Pi
turn — H-BRIDGE-1), under the canonical relative work paths the pins
were generated under (cwd = authored/), and every ledger and trail byte
is compared against fixtures/live_run/expected/*.  Exit 0 = every
pinned run held; the report is JSON.

The ABSENT-SOCKET case (C2's other half) is a THIRD pinned variant: the
same spec with the live socket resolving to an unbound path holds every
turn as OUTAGE (detail SocketTransportError), the run ends STALLED with
zero fenced records — this harness never stands in for an absent socket
(a stand-in never answers for absence).
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_AUTHORED = os.path.dirname(os.path.dirname(_HERE))
if _AUTHORED not in sys.path:
    sys.path.insert(0, _AUTHORED)
sys.path.insert(0, os.environ.get("FRACTAL_LEDGER_DIR",
                                  "/home/deploy/the-cell/ledger"))

import fixtures.build as build  # noqa: E402
import fixtures.live_server as live_server_module  # noqa: E402
import run as run_module  # noqa: E402
from fractal_ledger import LedgerLoader  # noqa: E402

LIVE_DIR = _HERE
SPEC_PATH = os.path.join(LIVE_DIR, "spec.json")


def _variant(name, constituted, rel_work):
    work = rel_work
    if os.path.exists(work):
        shutil.rmtree(work)
    os.makedirs(work)
    spec = build.read_spec(SPEC_PATH)
    spec["live_socket"] = os.path.join(work, "live.sock")
    ledger = os.path.join(work, "gates.jsonl")
    trailp = os.path.join(work, "trail.jsonl")
    build.b4_build.write_plant(ledger)
    server = live_server_module.LiveServer(
        spec, spec["live_socket"], constituted=constituted)
    server.start()
    try:
        conductor = run_module.Conductor(
            ledger, trailp, spec,
            socket_dir=os.path.join(work, "sock"))
        result = conductor.run()
        conductor.close()
    finally:
        server.halt()
    with open(ledger, "rb") as handle:
        actual_ledger = handle.read()
    with open(trailp, "rb") as handle:
        actual_trail = handle.read()
    with open(os.path.join(LIVE_DIR, "expected",
                           "gates-%s.jsonl" % name), "rb") as handle:
        expected_ledger = handle.read()
    with open(os.path.join(LIVE_DIR, "expected",
                           "trail-%s.jsonl" % name), "rb") as handle:
        expected_trail = handle.read()
    if actual_ledger != expected_ledger:
        raise RuntimeError("live-%s: the ledger differs from the pinned "
                           "bytes" % name)
    if actual_trail != expected_trail:
        raise RuntimeError("live-%s: the trail differs from the pinned "
                           "bytes" % name)
    return result, server


def _absent_variant(rel_work):
    """The absent-socket case: the live socket resolves to a path that
    binds nothing — NO server at all.  Every live turn holds outage,
    the run stalls, nothing reads clean."""
    work = rel_work
    if os.path.exists(work):
        shutil.rmtree(work)
    os.makedirs(work)
    spec = build.read_spec(SPEC_PATH)
    spec["live_socket"] = live_server_module.absent_socket_path(work)
    ledger = os.path.join(work, "gates.jsonl")
    trailp = os.path.join(work, "trail.jsonl")
    build.b4_build.write_plant(ledger)
    conductor = run_module.Conductor(
        ledger, trailp, spec,
        socket_dir=os.path.join(work, "sock"))
    result = conductor.run()
    conductor.close()
    with open(ledger, "rb") as handle:
        actual_ledger = handle.read()
    with open(trailp, "rb") as handle:
        actual_trail = handle.read()
    with open(os.path.join(LIVE_DIR, "expected",
                           "gates-absent.jsonl"), "rb") as handle:
        expected_ledger = handle.read()
    with open(os.path.join(LIVE_DIR, "expected",
                           "trail-absent.jsonl"), "rb") as handle:
        expected_trail = handle.read()
    if actual_ledger != expected_ledger:
        raise RuntimeError("live-absent: the ledger differs from the "
                           "pinned bytes")
    if actual_trail != expected_trail:
        raise RuntimeError("live-absent: the trail differs from the "
                           "pinned bytes")
    return result


def run():
    rel_live = os.path.relpath(LIVE_DIR, _AUTHORED)
    box_result, box_server = _variant(
        "box", ("G",), os.path.join(rel_live, "work-box"))
    all_result, all_server = _variant(
        "all", "all", os.path.join(rel_live, "work-all"))
    absent_result = _absent_variant(
        os.path.join(rel_live, "work-absent"))
    # the whole-run invariant, re-derived independently here (never
    # trusted from the pins): the box run held Q/V/P as agent_not_found
    # and never completed; the all run completed every cycle; the
    # absent run held every turn as outage with zero fenced records
    records_box = LedgerLoader(
        os.path.join(rel_live, "work-box", "gates.jsonl")).load(
            write_index=False).records
    blocked = [r for r in records_box
               if (r.get("payload_ref") or "").startswith(
                   "hold:blocked:agent_not_found:")]
    fenced = [r for r in records_box
              if (r.get("payload_ref") or "").startswith("fenced:")]
    if box_result.get("status") != "stalled" or not blocked or not fenced:
        raise RuntimeError("live-box: the pinned shape is not what the "
                           "pins declare: %r" % (box_result,))
    if all_result.get("status") != "complete":
        raise RuntimeError("live-all: the pinned shape is not complete: "
                           "%r" % (all_result,))
    if absent_result.get("status") != "stalled":
        raise RuntimeError("live-absent: the pinned shape is not a "
                           "stall: %r" % (absent_result,))
    records_absent = LedgerLoader(
        os.path.join(rel_live, "work-absent", "gates.jsonl")).load(
            write_index=False).records
    outage = [r for r in records_absent
              if (r.get("payload_ref") or "").startswith(
                  "hold:outage:SocketTransportError:")]
    fenced_absent = [r for r in records_absent
                     if (r.get("payload_ref") or "").startswith(
                         "fenced:")]
    if not outage or fenced_absent:
        raise RuntimeError("live-absent: the pinned shape is not outage "
                           "holds with zero fenced records")
    # no fixture desk_server.py was ever spawned by any variant — the
    # live server's socket is the ONLY one the runs touched (C2)
    report = {
        "status": "pinned",
        "box": {"run": box_result.get("status"),
                "blocked_holds": len(blocked),
                "fenced_turns": len(fenced),
                "prompt_targets": sorted(box_server.prompts.keys()),
                "connections": box_server.connections},
        "all": {"run": all_result.get("status"),
                "prompt_targets": sorted(all_server.prompts.keys()),
                "connections": all_server.connections},
        "absent": {"run": absent_result.get("status"),
                   "outage_holds": len(outage),
                   "fenced_records": len(fenced_absent)},
    }
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(prog="run_live")
    parser.parse_args(argv)
    run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
