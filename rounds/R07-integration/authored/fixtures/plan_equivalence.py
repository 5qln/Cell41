#!/usr/bin/env python3
"""plan_equivalence — the C3 reference runner (the integration round,
fixture apparatus): the DIRECT engine calls the criterion names —
``word.decode_scenario`` + ``navigate.plan_walk`` over the same
scenario bytes — emitted with the declared serialization, so the
verifier can diff it byte-for-byte against ``cellctl conduct
--plan-only`` over the same file.  A non-zero diff proves the wrapper
adds something; a zero diff proves it adds nothing (C3).

The engine is reached THROUGH the sha-pinned surface_contract (the
seam is the import boundary — C7); the reference never imports a
pinned module directly.
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

import surface_contract as sc  # noqa: E402

# The declared serialization (SEAM_SURFACE.serialization) — the same
# formula cellctl uses for --plan-only.
_SERIALIZE = lambda report: json.dumps(  # noqa: E731
    report, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if len(argv) != 1:
        print("usage: plan_equivalence.py <scenario.json>",
              file=sys.stderr)
        return 2
    path = argv[0]
    try:
        with open(path, "rb") as handle:
            raw = handle.read()
    except OSError as exc:
        sys.stdout.write(_SERIALIZE(
            {"status": "absent",
             "reason": "no scenario file at %r (%s)" % (path, exc)})
            + "\n")
        return 1
    decode = sc.word.decode_scenario(raw)
    if decode.get("status") != "ok":
        sys.stdout.write(_SERIALIZE(
            {"status": decode.get("status"),
             "reason": decode.get("reason")}) + "\n")
        return 1
    plan = sc.navigate.plan_walk(decode["scenario"])
    sys.stdout.write(_SERIALIZE(plan) + "\n")
    return 0 if plan.get("status") == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
