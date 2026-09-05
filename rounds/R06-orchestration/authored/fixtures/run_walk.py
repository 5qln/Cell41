#!/usr/bin/env python3
"""run_walk — the cold-restart fixture runner (R06 · orchestration,
H-ORCH-1, lens 5): one CLI that starts the fixture desk harness in
its own process and runs the orchestration against it — every run is
a NEW python process rebuilding the word-walk + the materializer from
disk alone (the scenario file, the ledger, the trail, the
materialized directory).  The restart selftest splits a walk across
two such processes (--max-steps on the first) and compares the final
ledger + trail bytes against the uninterrupted run's.

The harness is deterministic fixture apparatus (no live box — the
live socket the conductor resolves is the harness's own, injected
through the spec).  Result written to --result (JSON).
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.dont_write_bytecode = True

_HERE = os.path.dirname(os.path.abspath(__file__))
_AUTHORED = os.path.dirname(_HERE)
if _AUTHORED not in sys.path:
    sys.path.insert(0, _AUTHORED)

import fixtures.desk_harness as desk_harness  # noqa: E402
import orchestrate  # noqa: E402


def main(argv=None):
    parser = argparse.ArgumentParser(prog="run_walk")
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--harness-spec", required=True)
    parser.add_argument("--ledger", required=True)
    parser.add_argument("--trail", required=True)
    parser.add_argument("--socket", required=True,
                        help="the harness's own socket path")
    parser.add_argument("--work", required=True,
                        help="the work dir (spec + socket dirs)")
    parser.add_argument("--constituted", default="all")
    parser.add_argument("--materialize", default=None)
    parser.add_argument("--materialized", default=None)
    parser.add_argument("--max-steps", type=int, default=None)
    parser.add_argument("--result", required=True)
    parser.add_argument("--observe-states", type=int, default=1)
    args = parser.parse_args(argv)

    os.makedirs(args.work, exist_ok=True)
    with open(args.harness_spec, "rb") as handle:
        harness_spec = json.loads(handle.read().decode("utf-8"))
    constituted = tuple(args.constituted.split(",")) \
        if args.constituted not in ("", "all") else (
            "all" if args.constituted == "all" else ())
    server = desk_harness.DeskHarness(harness_spec, args.socket,
                                      constituted=constituted)
    server.start()
    try:
        from fixtures.build import orchestrate_spec
        spec = orchestrate_spec(
            live_socket=args.socket,
            materialize=args.materialize,
            materialized=args.materialized,
            observe_states=bool(args.observe_states),
            scope="orchestration-fixture")
        spec_path = os.path.join(args.work, "orchestrate-spec.json")
        with open(spec_path, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(spec, ensure_ascii=False,
                                    sort_keys=True,
                                    separators=(",", ":")) + "\n")
        conductor = orchestrate.Orchestrator(
            args.scenario, args.ledger, args.trail, spec,
            socket_dir=os.path.join(args.work, "sockdir"))
        result = conductor.run(max_steps=args.max_steps)
        conductor.close()
        with open(args.result, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(result, ensure_ascii=False,
                                    sort_keys=True,
                                    separators=(",", ":")) + "\n")
    finally:
        server.halt()
    return 0


if __name__ == "__main__":
    sys.exit(main())
