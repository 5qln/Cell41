#!/usr/bin/env python3
"""run_conduct — the declared cold-restart fixture runner (the cold
restart + run-lock lenses, lens 5/C5): it executes /conduct as a NEW
process over a caller-supplied spec, and re-runs it as a SECOND
process — proving the run re-arms from disk alone (turn_key
idempotency: the second run observes, never re-runs) and that a
concurrent second /conduct BLOCKS on the seam's declared run lock
rather than interleaving (C5).

The binary it invokes is caller-supplied (--bin): point it at the
fixture fake for the binding-layer proof, or at the real attested
cellctl for the seam-level proof — the argv shape is the binding's
exact shape in both worlds (["conduct", "--spec", spec]).

usage: run_conduct.py --bin <cellctl> --spec <spec.json>
                      --journal <file> [--concurrent] [--hold-ms N]
                                        [--grace-ms N]

Deterministic: the ordering proof uses process completion order from
the journal, never a wall clock in the judgement (the lock hold and
the concurrency grace are caller-supplied fixture data — fixture
apparatus, not production logic).
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

sys.dont_write_bytecode = True


def _spawn(bin_path, spec, journal, extra_env):
    env = dict(os.environ)
    env["CELLCTL_JOURNAL"] = journal
    env.update(extra_env or {})
    return subprocess.Popen(
        [sys.executable, bin_path, "conduct", "--spec", spec],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)


def _run(bin_path, spec, journal):
    child = _spawn(bin_path, spec, journal, {})
    out, err = child.communicate(timeout=300)
    return child.returncode, out, err


def journal_entries(path):
    if not os.path.isfile(path):
        return []
    out = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def main(argv):
    parser = argparse.ArgumentParser(prog="run_conduct")
    parser.add_argument("--bin", required=True)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--journal", required=True)
    parser.add_argument("--concurrent", action="store_true",
                        help="fire a second /conduct while the first "
                             "still holds the run lock")
    parser.add_argument("--hold-ms", type=int, default=400,
                        help="the first run's lock hold (fixture data; "
                             "the fake honours FAKE_HOLD_MS)")
    parser.add_argument("--grace-ms", type=int, default=120,
                        help="fixture grace: long enough for the first "
                             "process to take the lock before the "
                             "second is fired (apparatus, not logic)")
    args = parser.parse_args(argv)

    first = _spawn(args.bin, args.spec, args.journal,
                   {"FAKE_HOLD_MS": str(args.hold_ms)})
    time.sleep(args.grace_ms / 1000.0)  # fixture apparatus
    second = None
    if args.concurrent:
        second_code, second_out, second_err = _run(args.bin, args.spec,
                                                   args.journal)
        second = {"exit": second_code,
                  "stdout": second_out.decode("utf-8"),
                  "stderr": second_err.decode("utf-8")}
    first_out, first_err = first.communicate(timeout=300)
    first_code = first.returncode

    report = {
        "first": {"exit": first_code,
                  "stdout": first_out.decode("utf-8"),
                  "stderr": first_err.decode("utf-8")},
        "second": second,
        "journal": journal_entries(args.journal),
    }
    sys.stdout.write(json.dumps(report, ensure_ascii=False,
                                sort_keys=True,
                                separators=(",", ":")) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
