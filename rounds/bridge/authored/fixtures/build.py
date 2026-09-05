#!/usr/bin/env python3
"""build — the bridge's fixture-world builder (declared fixture
apparatus, never the conductor): renders the live-mode specs (the §3.6
surface templates via B4's pinned builder — the imported grammar,
never re-authored), writes the soft-config fixture files (the good
override and the four malformed/partial/absent-shaped cases), plants
the human's record through B0's LedgerWriter (the TTY act's stand-in,
P4a's attest-provider precedent), and pins the expected ledgers and
trails of the live-mode runs and the cold-restart run — bytes the
verifier regenerates with its own implementation.

The run itself never writes state attested and never invokes
cell-attest: the plant written here is the fixture world's declared
fiction (B3's assumption #4, carried).  Every ledger byte below is
written through fractal_ledger only — never by hand.

CLI:  python3 build.py --out fixtures
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys

# Never leave a bytecode cache beside a predecessor file: the pinned
# loads import by path and the workspace outside ./authored/ must stay
# untouched.
sys.dont_write_bytecode = True

_HERE = os.path.dirname(os.path.abspath(__file__))
_AUTHORED = os.path.dirname(_HERE)
if _AUTHORED not in sys.path:
    sys.path.insert(0, _AUTHORED)
sys.path.insert(0, os.environ.get("FRACTAL_LEDGER_DIR",
                                  "/home/deploy/the-cell/ledger"))

import surface_contract  # noqa: E402  (the sha-pinned seam)
from surface_contract import b4_build, softconfig  # noqa: E402
from fractal_ledger import LedgerLoader, LedgerWriter  # noqa: E402

TS = b4_build.TS
SOURCES_DIR = os.path.normpath(os.path.join(_AUTHORED, "..", "sources"))
NEEDLE = "∞0′ → ‖"  # the encoding-lens bytes (commission lens 4)


def base_spec(scope, cells, cycle_target, ceiling=None):
    """The B4 shape (its pinned builder renders the templates), with the
    bridge's sources dir."""
    spec = b4_build.build_spec(
        scope, cells, cycle_target, ceiling=ceiling, outages=(),
        blocked=(), sources_dir=SOURCES_DIR)
    return spec


def live_run_spec():
    """The live-mode run spec — desks resolved by label, the fence read;
    Q/V/P hold blocked (agent_not_found) under the live-box-shaped
    server, or the whole run completes under constituted=all (two
    cycles per cell — the second cycle's seed exercises the live
    source-reference rule).  The harness injects the scratch
    "live_socket" at run time."""
    spec = base_spec("bridge-live-run", ["", "G"], 4)
    spec["mode"] = "live"
    spec["soft_config"] = None
    spec["live_socket"] = None
    return spec


def restart_spec():
    """The cold-restart spec — the live mode resolved FROM the soft
    layer (spec mode null; the soft config's budget.default_mode is
    "live") and the prompt/budget bytes read from the soft file at
    runtime, so a NEW process re-arms the live mode + the config-read
    from disk alone (C7, lens 5)."""
    spec = base_spec("bridge-restart", ["", "G"], 4)
    spec["mode"] = None
    spec["soft_config"] = os.path.join(
        _HERE, "restart", "soft.json")
    spec["live_socket"] = None
    return spec


def write_spec(path, spec):
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(spec, ensure_ascii=False, sort_keys=True,
                                separators=(",", ":")) + "\n")


def read_spec(path):
    with open(path, "rb") as handle:
        return json.loads(handle.read().decode("utf-8"))


def soft_desk(desk, tag="SOFT LAYER (fixture)"):
    """One complete per-desk soft override, needle-bearing (lens 4) and
    clearly labelled fixture data — the runtime read must change the
    prompt bytes exactly by these."""
    return {
        "emphasis": [
            "%s emphasis %s op 1 — %s" % (tag, desk, NEEDLE),
            "%s emphasis %s op 2 — %s" % (tag, desk, NEEDLE),
        ],
        "voice": "%s voice %s — %s" % (tag, desk, NEEDLE),
        "model": "%s model %s" % (tag, desk),
    }


def good_soft_config():
    """The complete override — changes every runtime read: emphasis /
    voice / model per desk, the charges, and the default mode."""
    desks = {desk: soft_desk(desk) for desk in "SGQPV"}
    return {
        "desks": desks,
        "budget": {
            "default_mode": "re-prompted",
            "charges": {
                "re-prompted": {"G": 1234, "Q": 1500, "P": 1700,
                                "V": 4600},
                "sub-process": {"G": 2200, "Q": 2500, "P": 2900,
                                "V": 3800},
                "live": {"G": 2600, "Q": 3000, "P": 3400, "V": 4600},
            },
        },
    }


def restart_soft_config():
    """The restart run's soft layer: the default mode IS "live" (the
    spec declares none — the mode resolves from the soft layer, C3),
    the live charges are overridden (observable in the run-end spend),
    and the desk bytes are needle-bearing overrides."""
    return {
        "desks": {desk: soft_desk(desk, "RESTART SOFT LAYER (fixture)")
                  for desk in "SGQPV"},
        "budget": {
            "default_mode": "live",
            "charges": {
                "re-prompted": {"G": 2600, "Q": 3000, "P": 3400,
                                "V": 4600},
                "sub-process": {"G": 2200, "Q": 2500, "P": 2900,
                                "V": 3800},
                "live": {"G": 2000, "Q": 2400, "P": 2800, "V": 4000},
            },
        },
    }


MALFORMED_JSON = "{ this is not json ]"
PARTIAL_JSON = {
    "desks": {desk: soft_desk(desk) for desk in "SGQP"},  # V missing
}
WRONG_TYPE_JSON = {
    "desks": {desk: soft_desk(desk) for desk in "SGQPV"},
}
WRONG_TYPE_JSON["desks"]["G"]["voice"] = 123  # wrong type — a bad field


def write_soft_files(out_dir):
    soft_dir = os.path.join(out_dir, "soft_config")
    os.makedirs(soft_dir, exist_ok=True)
    with open(os.path.join(soft_dir, "good.json"), "w",
              encoding="utf-8") as handle:
        handle.write(json.dumps(good_soft_config(), ensure_ascii=False,
                                sort_keys=True, separators=(",", ":"))
                     + "\n")
    with open(os.path.join(soft_dir, "malformed.json"), "w",
              encoding="utf-8") as handle:
        handle.write(MALFORMED_JSON + "\n")
    with open(os.path.join(soft_dir, "partial.json"), "w",
              encoding="utf-8") as handle:
        handle.write(json.dumps(PARTIAL_JSON, ensure_ascii=False,
                                sort_keys=True, separators=(",", ":"))
                     + "\n")
    with open(os.path.join(soft_dir, "empty.json"), "wb") as handle:
        handle.write(b"")  # zero bytes — sha256 e3b0c44298fc…
    with open(os.path.join(soft_dir, "wrong_type.json"), "w",
              encoding="utf-8") as handle:
        handle.write(json.dumps(WRONG_TYPE_JSON, ensure_ascii=False,
                                sort_keys=True, separators=(",", ":"))
                     + "\n")


# ---------------------------------------------------------------------------
# The pinned runs — generated under the canonical relative work paths
# (cwd = authored/), so the trail bytes (which carry the ledger path)
# are comparable byte for byte across generation and verification.
# ---------------------------------------------------------------------------


def _run_live_variant(name, spec, socket_path, constituted, rel_work):
    """Run one live-mode variant in-process against the fixture live
    server and return (ledger_bytes, trail_bytes, result, server)."""
    import fixtures.live_server as live_server_module
    import run as run_module

    os.makedirs(rel_work, exist_ok=True)
    ledger = os.path.join(rel_work, "gates.jsonl")
    trailp = os.path.join(rel_work, "trail.jsonl")
    if os.path.exists(ledger):
        os.unlink(ledger)
    if os.path.exists(trailp):
        os.unlink(trailp)
    b4_build.write_plant(ledger)
    spec = dict(spec)
    spec["live_socket"] = socket_path
    server = live_server_module.LiveServer(
        spec, socket_path, constituted=constituted)
    server.start()
    try:
        conductor = run_module.Conductor(
            ledger, trailp, spec,
            socket_dir=os.path.join(rel_work, "sock"))
        result = conductor.run()
        conductor.close()
    finally:
        server.halt()
    with open(ledger, "rb") as handle:
        ledger_bytes = handle.read()
    with open(trailp, "rb") as handle:
        trail_bytes = handle.read()
    return ledger_bytes, trail_bytes, result, server


def _run_restart_variant(spec, socket_path, rel_work):
    """The uninterrupted restart-scenario run (the pins the cold-restart
    harness's split processes must reproduce byte for byte)."""
    import fixtures.live_server as live_server_module
    import run as run_module

    os.makedirs(rel_work, exist_ok=True)
    ledger = os.path.join(rel_work, "gates.jsonl")
    trailp = os.path.join(rel_work, "trail.jsonl")
    if os.path.exists(ledger):
        os.unlink(ledger)
    if os.path.exists(trailp):
        os.unlink(trailp)
    b4_build.write_plant(ledger)
    spec = dict(spec)
    spec["live_socket"] = socket_path
    server = live_server_module.LiveServer(
        spec, socket_path, constituted="all")
    server.start()
    try:
        conductor = run_module.Conductor(
            ledger, trailp, spec,
            socket_dir=os.path.join(rel_work, "sock"))
        result = conductor.run()
        conductor.close()
    finally:
        server.halt()
    with open(ledger, "rb") as handle:
        ledger_bytes = handle.read()
    with open(trailp, "rb") as handle:
        trail_bytes = handle.read()
    return ledger_bytes, trail_bytes, result


def generate(out_dir, keep=False):
    """Generate every fixture and its expected pins by running the
    conductor deterministically (fixed clock, the deterministic live
    server, the fixed soft files)."""
    rel_out = os.path.relpath(out_dir, _AUTHORED)

    # -- the live-mode run: two declared server configurations ----------
    live_dir = os.path.join(out_dir, "live_run")
    os.makedirs(os.path.join(live_dir, "expected"), exist_ok=True)
    write_spec(os.path.join(live_dir, "spec.json"), live_run_spec())
    spec = read_spec(os.path.join(live_dir, "spec.json"))

    box_work = os.path.join(rel_out, "live_run", "work-box")
    if os.path.exists(box_work):
        shutil.rmtree(box_work)
    box_ledger, box_trail, box_result, box_server = _run_live_variant(
        "box", spec,
        os.path.join(box_work, "live.sock"), ("G",), box_work)
    box_summary = {
        "requests": len(box_server.requests),
        "agent_not_found_errors": sum(
            1 for code, _method, _target in box_server.errors
            if code == "agent_not_found"),
        "prompt_targets": sorted(box_server.prompts.keys()),
    }
    with open(os.path.join(live_dir, "expected", "gates-box.jsonl"),
              "wb") as fh:
        fh.write(box_ledger)
    with open(os.path.join(live_dir, "expected", "trail-box.jsonl"),
              "wb") as fh:
        fh.write(box_trail)
    with open(os.path.join(live_dir, "expected", "run-result-box.json"),
              "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"result": box_result,
                             "server": box_summary},
                            ensure_ascii=False, sort_keys=True) + "\n")

    all_work = os.path.join(rel_out, "live_run", "work-all")
    if os.path.exists(all_work):
        shutil.rmtree(all_work)
    all_ledger, all_trail, all_result, all_server = _run_live_variant(
        "all", spec,
        os.path.join(all_work, "live.sock"), "all", all_work)
    all_summary = {
        "requests": len(all_server.requests),
        "methods": all_server.methods,
        "prompt_targets": sorted(all_server.prompts.keys()),
    }
    with open(os.path.join(live_dir, "expected", "gates-all.jsonl"),
              "wb") as fh:
        fh.write(all_ledger)
    with open(os.path.join(live_dir, "expected", "trail-all.jsonl"),
              "wb") as fh:
        fh.write(all_trail)
    with open(os.path.join(live_dir, "expected", "run-result-all.json"),
              "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"result": all_result,
                             "server": all_summary},
                            ensure_ascii=False, sort_keys=True) + "\n")

    # -- the absent-socket case (C2's other half): the live socket
    #    resolves to a path that binds nothing — every live turn holds
    #    outage, the run stalls, nothing reads clean, nothing is
    #    spawned --------------------------------------------------------
    absent_work = os.path.join(rel_out, "live_run", "work-absent")
    if os.path.exists(absent_work):
        shutil.rmtree(absent_work)
    absent_spec = dict(spec)
    absent_spec["live_socket"] = os.path.join(absent_work,
                                              "absent-herdr.sock")
    os.makedirs(absent_work, exist_ok=True)
    absent_ledger_path = os.path.join(absent_work, "gates.jsonl")
    absent_trail_path = os.path.join(absent_work, "trail.jsonl")
    b4_build.write_plant(absent_ledger_path)
    import run as run_module
    absent_conductor = run_module.Conductor(
        absent_ledger_path, absent_trail_path, absent_spec,
        socket_dir=os.path.join(absent_work, "sock"))
    absent_result = absent_conductor.run()
    absent_conductor.close()
    with open(absent_ledger_path, "rb") as handle:
        absent_ledger = handle.read()
    with open(absent_trail_path, "rb") as handle:
        absent_trail = handle.read()
    with open(os.path.join(live_dir, "expected", "gates-absent.jsonl"),
              "wb") as fh:
        fh.write(absent_ledger)
    with open(os.path.join(live_dir, "expected", "trail-absent.jsonl"),
              "wb") as fh:
        fh.write(absent_trail)
    with open(os.path.join(live_dir, "expected",
                           "run-result-absent.json"),
              "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"result": absent_result},
                            ensure_ascii=False, sort_keys=True) + "\n")
    if not keep:
        shutil.rmtree(os.path.join(live_dir, "work-box"),
                      ignore_errors=True)
        shutil.rmtree(os.path.join(live_dir, "work-all"),
                      ignore_errors=True)
        shutil.rmtree(os.path.join(live_dir, "work-absent"),
                      ignore_errors=True)

    # -- the cold-restart fixture: live mode + config-read from disk ----
    restart_dir = os.path.join(out_dir, "restart")
    os.makedirs(os.path.join(restart_dir, "expected"), exist_ok=True)
    write_spec(os.path.join(restart_dir, "spec.json"), restart_spec())
    with open(os.path.join(restart_dir, "soft.json"), "w",
              encoding="utf-8") as handle:
        handle.write(json.dumps(restart_soft_config(), ensure_ascii=False,
                                sort_keys=True, separators=(",", ":"))
                     + "\n")
    restart_spec_obj = read_spec(os.path.join(restart_dir, "spec.json"))
    restart_work = os.path.join(rel_out, "restart", "work")
    if os.path.exists(restart_work):
        shutil.rmtree(restart_work)
    restart_ledger, restart_trail, restart_result = _run_restart_variant(
        restart_spec_obj, os.path.join(restart_work, "live.sock"),
        restart_work)
    with open(os.path.join(restart_dir, "expected", "gates.jsonl"),
              "wb") as fh:
        fh.write(restart_ledger)
    with open(os.path.join(restart_dir, "expected", "trail.jsonl"),
              "wb") as fh:
        fh.write(restart_trail)
    with open(os.path.join(restart_dir, "expected", "run-result.json"),
              "w", encoding="utf-8") as fh:
        fh.write(json.dumps(restart_result, ensure_ascii=False,
                            sort_keys=True) + "\n")
    if not keep:
        shutil.rmtree(restart_work, ignore_errors=True)

    # -- the soft-config fixture files ------------------------------------
    write_soft_files(out_dir)

    print(json.dumps({
        "status": "generated",
        "live_box_result": box_result.get("status"),
        "live_all_result": all_result.get("status"),
        "restart_result": restart_result.get("status"),
        "out": out_dir,
    }, ensure_ascii=False, sort_keys=True))


def main(argv=None):
    parser = argparse.ArgumentParser(prog="build")
    parser.add_argument("--out", required=True)
    parser.add_argument("--keep", action="store_true")
    args = parser.parse_args(argv)
    generate(args.out, keep=args.keep)
    return 0


if __name__ == "__main__":
    sys.exit(main())
