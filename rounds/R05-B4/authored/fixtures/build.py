#!/usr/bin/env python3
"""build — the fixture world builder (declared fixture apparatus, never
the conductor): renders the run spec (with the §3.6 surface templates
rendered by P4b's imported grammar — never re-authored), plants the
human's record through B0's LedgerWriter (the TTY act's stand-in, P4a's
attest-provider precedent), and writes the byte-pinned expected ledgers
and trails the verifier regenerates with its own implementation.

The run itself never writes state attested and never invokes cell-attest:
the plant written here is the fixture world's declared fiction (B3's
assumption #4, carried).  Every ledger byte below is written through
fractal_ledger only — never by hand.

CLI:  python3 build.py --out <fixtures-dir>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_AUTHORED = os.path.dirname(_HERE)
if _AUTHORED not in sys.path:
    sys.path.insert(0, _AUTHORED)

import surface_contract  # noqa: E402
from surface_contract import grammar  # noqa: E402
from fractal_ledger import LedgerWriter, make_record  # noqa: E402

TS = "2026-08-29T12:00:00.000000Z"

# The human's origin question content ref — the fixture world's field
# anchor (a bare hex fingerprint, R11's lawful shape, needle-bearing).
ANCHOR = hashlib.sha256(
    "∞0′ → ‖ the origin question (fixture world stand-in — the human's "
    "TTY plant)".encode("utf-8")).hexdigest()

SOURCES_DIR = os.path.normpath(os.path.join(_AUTHORED, "..", "sources"))


def render_templates():
    """The §3.6 surface block of each desk's P4b bundle, slot
    placeholders intact (the desk fills them when it speaks — the
    grammar's own declared convention).  The V block additionally
    carries the two crystallisation passes and one lens-tagged
    formation-trail entry (R7 / R6, the V desk's announced form)."""
    templates = {}
    for letter in grammar.COURSE:
        bundle = grammar.render_bundle("", letter)
        start = bundle.find("⟦SURFACE v1⟧")
        end = bundle.find("⟦END SURFACE⟧", start) + len("⟦END SURFACE⟧")
        block = bundle[start:end]
        if letter == "V":
            entry = hashlib.sha256(
                b"fixture-v-trail-entry").hexdigest()
            block = block.replace(
                "⟦END SURFACE⟧",
                "TRAIL:\nPASS 1: yes\nPASS 2: yes\n1. [VG lens] ref: "
                "sha256:%s\n⟦END SURFACE⟧" % entry)
        templates[letter] = block + "\n"
    return templates


def build_spec(scope, cells, cycle_target, ceiling=None, outages=(),
               blocked=(), sources_dir=None):
    return {
        "scope": scope,
        "cells": list(cells),
        "cycle_target": cycle_target,
        "budget": {"ceiling": ceiling},
        "mode": None,
        "clock": {"kind": "fixed", "ts": TS},
        "outages": [dict(entry) for entry in outages],
        "blocked": [dict(entry) for entry in blocked],
        "surface_templates": render_templates(),
        "block_version": "",
        "wait_timeout_ms": 5000,
        "timeout_s": 5.0,
        "sources_dir": sources_dir or SOURCES_DIR,
    }


def write_spec(path, spec):
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(spec, ensure_ascii=False, sort_keys=True,
                                separators=(",", ":")) + "\n")


def read_spec(path):
    with open(path, "rb") as handle:
        return json.loads(handle.read().decode("utf-8"))


def plant_record():
    """The human's plant — gate x, address "", attested, emergent, his
    attestation ref.  Written through B0's writer by the fixture world,
    never by the run."""
    return make_record(
        address="", gate="x", state="attested", mark="emergent",
        payload_ref=ANCHOR,
        axis={"field": {"mode": "anchored", "anchor": ANCHOR},
              "delta": []},
        axis_verdict=None, corruption=None, tentative=False,
        turn_key=None, block_version="g-essence@3",
        attestation_ref=("∞0′ → ‖ his TTY plant (fixture world "
                         "stand-in)"))

def write_plant(ledger_path):
    with LedgerWriter(ledger_path, clock=lambda: TS) as writer:
        return writer.append(plant_record())


def run_conductor(ledger_path, trail_path, spec, socket_dir, max_actions=None,
                  mode=None, python=None):
    """Run the conductor (optionally as a fresh subprocess — the cold
    restart's second process) and return the parsed result JSON."""
    if python is None:
        import run as run_module
        conductor = run_module.Conductor(
            ledger_path, trail_path, spec, socket_dir=socket_dir,
            mode=mode, max_actions=max_actions)
        result = conductor.run()
        conductor.close()
        return result
    command = [python, os.path.join(_AUTHORED, "run.py"),
               "--ledger", ledger_path, "--trail", trail_path,
               "--spec", os.path.join(socket_dir, "spec.json"),
               "--socket-dir", socket_dir]
    if max_actions is not None:
        command += ["--max-actions", str(max_actions)]
    if mode is not None:
        command += ["--mode", mode]
    completed = subprocess.run(command, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, timeout=600)
    return json.loads(completed.stdout.decode("utf-8"))


def pin_bytes(path):
    with open(path, "rb") as handle:
        return handle.read()


def generate(out_dir, keep=False):
    """Generate every fixture and its expected pins by running the
    conductor deterministically (fixed clock, deterministic desks)."""
    main = os.path.join(out_dir, "main_run")
    hold = os.path.join(out_dir, "hold")
    budget = os.path.join(out_dir, "budget")
    tentative = os.path.join(out_dir, "tentative")
    kill9 = os.path.join(out_dir, "kill9")

    # -- the ≥20-cycle unattended run (with one outage hold inside) --------
    spec = build_spec(
        "b4-main-20cycle",
        cells=["", "G", "Q", "P", "V"],
        cycle_target=20,
        ceiling=None,
        outages=[{"cell": "P", "cycle": 3, "desk": "Q"}],
    )
    work = os.path.join(main, "work")
    os.makedirs(os.path.join(main, "expected"), exist_ok=True)
    if os.path.exists(work):
        shutil.rmtree(work)
    os.makedirs(work)
    write_spec(os.path.join(main, "spec.json"), spec)
    write_plant(os.path.join(work, "gates.jsonl"))
    result = run_conductor(
        os.path.join(work, "gates.jsonl"),
        os.path.join(work, "trail.jsonl"), spec,
        socket_dir=os.path.join(work, "sock"))
    with open(os.path.join(main, "expected", "gates.jsonl"), "wb") as fh:
        fh.write(pin_bytes(os.path.join(work, "gates.jsonl")))
    with open(os.path.join(main, "expected", "trail.jsonl"), "wb") as fh:
        fh.write(pin_bytes(os.path.join(work, "trail.jsonl")))
    with open(os.path.join(main, "expected", "run-result.json"),
              "w", encoding="utf-8") as fh:
        fh.write(json.dumps(result, ensure_ascii=False, sort_keys=True) +
                 "\n")
    if not keep:
        shutil.rmtree(work)

    # -- the kill -9 fixture reuses the main spec (its harness compares
    #    the killed-and-restarted bytes against the main-run pins) --------
    os.makedirs(os.path.join(kill9, "expected"), exist_ok=True)
    shutil.copyfile(os.path.join(main, "spec.json"),
                    os.path.join(kill9, "spec.json"))
    shutil.copyfile(os.path.join(main, "expected", "gates.jsonl"),
                    os.path.join(kill9, "expected", "gates.jsonl"))
    shutil.copyfile(os.path.join(main, "expected", "trail.jsonl"),
                    os.path.join(kill9, "expected", "trail.jsonl"))

    # -- the hold fixture: two holds (outage + blocked) that do NOT stop
    #    the run; the other cell's cycles complete; stalls with the holds
    #    still held --------------------------------------------------------
    spec = build_spec(
        "b4-hold-does-not-stop",
        cells=["G", "Q"],
        cycle_target=99,
        ceiling=None,
        outages=[{"cell": "G", "cycle": 1, "desk": "G"}],
        blocked=[{"cell": "Q", "cycle": 1, "desk": "Q"}],
    )
    work = os.path.join(hold, "work")
    os.makedirs(os.path.join(hold, "expected"), exist_ok=True)
    if os.path.exists(work):
        shutil.rmtree(work)
    os.makedirs(work)
    write_spec(os.path.join(hold, "spec.json"), spec)
    write_plant(os.path.join(work, "gates.jsonl"))
    result = run_conductor(
        os.path.join(work, "gates.jsonl"),
        os.path.join(work, "trail.jsonl"), spec,
        socket_dir=os.path.join(work, "sock"))
    with open(os.path.join(hold, "expected", "gates.jsonl"), "wb") as fh:
        fh.write(pin_bytes(os.path.join(work, "gates.jsonl")))
    with open(os.path.join(hold, "expected", "trail.jsonl"), "wb") as fh:
        fh.write(pin_bytes(os.path.join(work, "trail.jsonl")))
    with open(os.path.join(hold, "expected", "run-result.json"),
              "w", encoding="utf-8") as fh:
        fh.write(json.dumps(result, ensure_ascii=False, sort_keys=True) +
                 "\n")
    if not keep:
        shutil.rmtree(work)

    # -- the budget fixture: a ceiling crossed mid-run → a held gate, no
    #    overspend, clean stop --------------------------------------------
    spec = build_spec(
        "b4-budget-ceiling",
        cells=["G"],
        cycle_target=9999,
        ceiling=19000,
    )
    work = os.path.join(budget, "work")
    os.makedirs(os.path.join(budget, "expected"), exist_ok=True)
    if os.path.exists(work):
        shutil.rmtree(work)
    os.makedirs(work)
    write_spec(os.path.join(budget, "spec.json"), spec)
    write_plant(os.path.join(work, "gates.jsonl"))
    result = run_conductor(
        os.path.join(work, "gates.jsonl"),
        os.path.join(work, "trail.jsonl"), spec,
        socket_dir=os.path.join(work, "sock"))
    with open(os.path.join(budget, "expected", "gates.jsonl"), "wb") as fh:
        fh.write(pin_bytes(os.path.join(work, "gates.jsonl")))
    with open(os.path.join(budget, "expected", "trail.jsonl"), "wb") as fh:
        fh.write(pin_bytes(os.path.join(work, "trail.jsonl")))
    with open(os.path.join(budget, "expected", "run-result.json"),
              "w", encoding="utf-8") as fh:
        fh.write(json.dumps(result, ensure_ascii=False, sort_keys=True) +
                 "\n")
    if not keep:
        shutil.rmtree(work)

    # -- the torn/partial trail fixture: a real trail prefix torn
    #    mid-line (the kill -9 tail), and a mid-file damaged variant —
    #    the reader must replay the complete prefix consistently, flag
    #    the fragment, and fail closed on the mid-file break --------------
    torn_dir = os.path.join(out_dir, "torn")
    os.makedirs(os.path.join(torn_dir, "expected"), exist_ok=True)
    main_trail = pin_bytes(os.path.join(main, "expected", "trail.jsonl"))
    lines = main_trail.split(b"\n")
    prefix = b"\n".join(lines[:10]) + b"\n"
    fragment = b'{"trail_version":"1","scope":"b4-torn","seq":10,"ts":'
    torn_bytes = prefix + fragment
    with open(os.path.join(torn_dir, "torn_trail.jsonl"), "wb") as fh:
        fh.write(torn_bytes)
    with open(os.path.join(torn_dir, "expected", "replay.json"),
              "w", encoding="utf-8") as fh:
        import hashlib as _h
        import trail as _trail
        report = _trail.read_trail(os.path.join(torn_dir,
                                                "torn_trail.jsonl"))
        fh.write(json.dumps({
            "status": report["status"],
            "lines": len(report["lines"]),
            "chain": report["chain"]["status"],
            "torn": report["tail"]["torn"],
            "fragment_sha256": report["tail"]["fragment_sha256"],
        }, ensure_ascii=False, sort_keys=True) + "\n")
    damaged = bytearray(main_trail)
    damaged[len(damaged) // 2] ^= 0x01  # one byte, mid-file
    with open(os.path.join(torn_dir, "damaged_trail.jsonl"), "wb") as fh:
        fh.write(bytes(damaged))
    report = _trail.read_trail(os.path.join(torn_dir,
                                            "damaged_trail.jsonl"))
    with open(os.path.join(torn_dir, "expected", "damaged-replay.json"),
              "w", encoding="utf-8") as fh:
        fh.write(json.dumps({
            "status": report["status"],
            "damage_kind": report["damage"].get("kind")
            if report["damage"] else None,
        }, ensure_ascii=False, sort_keys=True) + "\n")

    # -- the tentative fixture: the seeded S is tentative and never
    #    consumed (the audit PASSES over the main-run ledger); the
    #    consumed variant (a downstream gate record whose payload chains
    #    to a tentative seed) FAILS the audit -----------------------------
    work = os.path.join(tentative, "work")
    os.makedirs(os.path.join(tentative, "expected"), exist_ok=True)
    if os.path.exists(work):
        shutil.rmtree(work)
    os.makedirs(work)
    shutil.copyfile(os.path.join(main, "spec.json"),
                    os.path.join(tentative, "spec.json"))
    shutil.copyfile(os.path.join(main, "expected", "gates.jsonl"),
                    os.path.join(work, "gates.jsonl"))
    from fractal_ledger import LedgerLoader, canonical_json
    loaded = LedgerLoader(os.path.join(work, "gates.jsonl")).load(
        write_index=False)
    seed_record = next(r for r in loaded.records
                       if (r.get("payload_ref") or "").startswith(
                           "seed:"))
    consumed = make_record(
        address="VQ", gate="b", state="held-pending", mark="mechanical",
        payload_ref=seed_record["payload_ref"],
        axis={"field": {"mode": "anchored",
                        "anchor": seed_record["payload_ref"]},
              "delta": []},
        axis_verdict=None, corruption=None, tentative=True,
        turn_key=None, block_version="",
        attestation_ref=None)
    # a deterministic turn_key for the injected world record (never a
    # collision with the run's keys — "world:" attempt slot)
    import run as run_module
    from surface_contract import turn_key
    consumed["turn_key"] = turn_key("VQ", "b", "world:consumed", "")
    with LedgerWriter(os.path.join(work, "gates.jsonl"),
                      clock=lambda: TS) as writer:
        writer.append(consumed)
    with open(os.path.join(tentative, "expected",
                           "consumed_gates.jsonl"), "wb") as fh:
        fh.write(pin_bytes(os.path.join(work, "gates.jsonl")))
    audit = run_module.audit_payload_chains(
        LedgerLoader(os.path.join(work, "gates.jsonl")).load(
            write_index=False).records)
    with open(os.path.join(tentative, "expected", "consumed-audit.json"),
              "w", encoding="utf-8") as fh:
        fh.write(json.dumps(audit, ensure_ascii=False, sort_keys=True) +
                 "\n")
    shutil.rmtree(work)
    print(json.dumps({"status": "generated",
                      "main_result": result.get("status"),
                      "hold_result": None, "budget_result": None,
                      "consumed_audit": audit["verdict"],
                      "out": out_dir},
                     ensure_ascii=False, sort_keys=True))


def main(argv=None):
    parser = argparse.ArgumentParser(prog="build")
    parser.add_argument("--out", required=True)
    parser.add_argument("--keep", action="store_true")
    args = parser.parse_args(argv)
    generate(args.out, keep=args.keep)
    return 0


if __name__ == "__main__":
    sys.exit(main())
