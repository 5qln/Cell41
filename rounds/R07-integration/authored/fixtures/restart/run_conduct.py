#!/usr/bin/env python3
"""run_conduct — the cold-restart + run-lock fixture runner (the
integration round, fixture apparatus, lens 5): executes ``cellctl
conduct`` in a NEW process (the second process of the cold-restart
lens — the CLI rebuilds the plan + the whole run from disk alone)
and returns the process's exit code + output as JSON at --result.

The run-lock test uses the same runner while the test process itself
holds the flock: the child is expected to BLOCK until the lock is
released (C5 — a second /conduct on the same dir blocks, never
interleaves).  The harness is the caller's (deterministic fixture
apparatus; no live box — H-INT-1).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

sys.dont_write_bytecode = True

_HERE = os.path.dirname(os.path.abspath(__file__))
_AUTHORED = os.path.dirname(os.path.dirname(_HERE))
_CELLCTL = os.path.join(_AUTHORED, "cellctl")


def run_conduct(spec_path, max_steps=None, plan_only=False,
                scenario=None, timeout_s=120.0):
    argv = [sys.executable, _CELLCTL, "conduct", "--spec", spec_path]
    if plan_only:
        argv = [sys.executable, _CELLCTL, "conduct", "--plan-only",
                "--scenario", scenario]
    elif max_steps is not None:
        argv += ["--max-steps", str(max_steps)]
    completed = subprocess.run(argv, capture_output=True, text=True,
                               timeout=timeout_s,
                               cwd=_AUTHORED)
    return {"exit": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr}


def main(argv=None):
    parser = argparse.ArgumentParser(prog="run_conduct")
    parser.add_argument("--spec", required=True)
    parser.add_argument("--max-steps", type=int, default=None)
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--scenario", default=None)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--result", required=True)
    args = parser.parse_args(argv)
    report = run_conduct(args.spec, max_steps=args.max_steps,
                         plan_only=args.plan_only,
                         scenario=args.scenario,
                         timeout_s=args.timeout)
    with open(args.result, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(report, ensure_ascii=False,
                                sort_keys=True,
                                separators=(",", ":")) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
