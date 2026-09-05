#!/usr/bin/env python3
"""cost — the dual-mode desk invocation surface and the per-turn
memory/token cost accounting (R05 · B4, H-B4-2).

Two modes, both real, both instrumented:

  * ``sub-process`` (persistent) — one long-lived fixture desk process
    per cell; the desk bundle is sent once; per-turn cost is prompt +
    answer tokens, and the memory cost is the live process's resident
    footprint (measured from /proc/<pid>/status — VmRSS);
  * ``re-prompted`` (stateless) — a fresh desk process per turn; the
    full desk bundle is re-sent EVERY turn (the re-prompt cost) and
    nothing is retained between turns (memory cost 0).

The conservative default is DECLARED DATA — ``COST_MODEL["default_mode"]``
— never hard-coded logic: the conductor resolves its mode from this table
(see run.py), and the live per-Pi measurement of which mode actually
costs less awaits a constituted desk (one paid Pi turn — not done here).

The spend ceiling is enforced from declared charges, never from the
measurements: each charge is a conservative stand-in (declared ≥ the
measured per-turn cost — asserted by the selftest), so a ceiling reached
surfaces as a held gate, never a silent kill, never an overspend (C4).

Deterministic and stdlib-only (the desk processes it spawns are the
fixture desk server — fixtures/desk_server.py, speaking the attested
herdr dialect on its own AF_UNIX socket, never the live socket).
"""

from __future__ import annotations

import math
import os
import subprocess
import sys
import time

__all__ = [
    "COST_MODEL",
    "DEFAULT_MODE",
    "chars_per_token",
    "charge_for",
    "measured_cost",
    "DeskAdapter",
    "TurnContext",
    "DeskAdapterError",
    "desk_server_path",
    "spend_from_records",
]

_HERE = os.path.dirname(os.path.abspath(__file__))
_FIXTURES = os.path.join(_HERE, "fixtures")


def desk_server_path():
    return os.path.join(_FIXTURES, "desk_server.py")


# ---------------------------------------------------------------------------
# The declared cost model — DATA.  The default mode and the per-desk
# charges live here, never in the conductor's control flow (H-B4-2).
# ---------------------------------------------------------------------------

COST_MODEL = {
    "default_mode": "re-prompted",
    "chars_per_token": 4,
    "modes": {
        "sub-process": {
            "retained": "persistent",
            "bundle_sent_each_turn": False,
            "memory": "measured-rss",
            "description": ("one long-lived desk process per cell — the "
                            "bundle is sent once; per-turn cost = prompt "
                            "+ answer tokens; memory = the live "
                            "process's resident footprint"),
        },
        "re-prompted": {
            "retained": "stateless",
            "bundle_sent_each_turn": True,
            "memory": "none-retained",
            "description": ("a fresh desk process per turn — the full "
                            "bundle is re-sent every turn (the re-prompt "
                            "cost); nothing is retained between turns; "
                            "memory = 0"),
        },
    },
    # Declared per-desk per-turn charges (token units) — conservative
    # stand-ins: each charge is ≥ the measured per-turn cost (prompt
    # tokens + 3× answer tokens + bundle tokens when re-sent) for every
    # fixture turn.  The live per-Pi measurement awaits a constituted
    # desk (H-B4-2).
    "charges": {
        "sub-process": {"G": 2200, "Q": 2500, "P": 2900, "V": 3800},
        "re-prompted": {"G": 2600, "Q": 3000, "P": 3400, "V": 4600},
    },
    "weights": {
        "prompt": 1.0,
        "answer": 3.0,
        "bundle": 1.0,
    },
}

DEFAULT_MODE = COST_MODEL["default_mode"]


def chars_per_token():
    return COST_MODEL["chars_per_token"]


def charge_for(mode, desk, prompt_bytes=None, bundle_bytes=None):
    """The declared charge of one turn — DATA, deterministic (the
    ceiling decision uses exactly this)."""
    if mode not in COST_MODEL["charges"]:
        raise DeskAdapterError("unknown desk mode %r" % (mode,))
    if desk not in COST_MODEL["charges"][mode]:
        raise DeskAdapterError(
            "no declared charge for desk %r in mode %r" % (desk, mode))
    return COST_MODEL["charges"][mode][desk]


def measured_cost(mode, desk, prompt_bytes, answer_bytes,
                  bundle_bytes=0, memory_bytes=0):
    """The measured per-turn cost (the instrumentation — never the
    ceiling decision): prompt tokens + 3× answer tokens (+ bundle tokens
    when the mode re-sends the bundle), and the memory footprint."""
    cpt = COST_MODEL["chars_per_token"]
    weights = COST_MODEL["weights"]
    prompt_tokens = math.ceil(prompt_bytes / cpt)
    answer_tokens = math.ceil(answer_bytes / cpt)
    bundle_tokens = (
        math.ceil(bundle_bytes / cpt)
        if COST_MODEL["modes"][mode]["bundle_sent_each_turn"]
        else 0)
    return {
        "mode": mode,
        "desk": desk,
        "prompt_bytes": prompt_bytes,
        "answer_bytes": answer_bytes,
        "bundle_bytes": bundle_bytes,
        "prompt_tokens": prompt_tokens,
        "answer_tokens": answer_tokens,
        "bundle_tokens": bundle_tokens,
        "tokens": int(weights["prompt"] * prompt_tokens
                      + weights["answer"] * answer_tokens
                      + weights["bundle"] * bundle_tokens),
        "memory_bytes": memory_bytes,
    }


def spend_from_records(records, mode):
    """The spend the ledger accounts — a pure function of the completed
    turn records alone (each gate letter charges once per record), so a
    fresh process recomputes the same spend from the ledger alone (C3,
    C4: accounted BEFORE each turn).  Seed, hold and plant records
    charge nothing (no model turn happened)."""
    desk_of_gate = {"y": "G", "z": "Q", "a": "P", "b": "V"}
    spend = 0
    for record in records:
        payload = record.get("payload_ref") or ""
        if not payload.startswith("fenced:"):
            continue
        desk = desk_of_gate.get(record.get("gate"))
        if desk is None:
            continue
        spend += charge_for(mode, desk)
    return spend


# ---------------------------------------------------------------------------
# The desk processes (both modes run the same fixture server).
# ---------------------------------------------------------------------------


class DeskAdapterError(Exception):
    """A desk process could not be started or observed."""


class TurnContext:
    """One turn's desk surface: the socket path the imported B2
    instrument speaks on, and the process handle."""

    def __init__(self, socket_path, process):
        self.socket_path = socket_path
        self.process = process
        self._memory_bytes = None

    def memory_bytes(self):
        """The live process's resident footprint (VmRSS) — measured
        from /proc/<pid>/status.  A process already gone measures 0
        (re-prompted turns are stateless by construction)."""
        if self._memory_bytes is not None:
            return self._memory_bytes
        pid = self.process.pid if self.process is not None else None
        value = 0
        if pid is not None:
            try:
                with open("/proc/%d/status" % pid, "rb") as handle:
                    raw = handle.read().decode("utf-8", "replace")
                for line in raw.split("\n"):
                    if line.startswith("VmRSS:"):
                        parts = line.split()
                        value = int(parts[1]) * 1024
                        break
            except (OSError, ValueError, IndexError):
                value = 0
        self._memory_bytes = value
        return value


class DeskAdapter:
    """The dual-mode desk invocation surface.

    ``DeskAdapter(spec, socket_dir, mode=None)`` — ``mode`` defaults to
    the DECLARED data table (COST_MODEL["default_mode"]); the spec is
    written to a scratch file the desk server reads (cells, surface
    templates, outages, blocked turns — all caller-supplied data).

    sub-process: the cell's server process is started once and reused
    for every turn of that cell (persistent).  re-prompted: a fresh
    server process is started per turn and joined when the turn closes
    (stateless).  Every spawned process speaks the attested herdr
    dialect on its OWN socket (H-B4-1: never the live socket).
    """

    def __init__(self, spec, socket_dir, mode=None, python=None):
        self.mode = mode if mode is not None else DEFAULT_MODE
        if self.mode not in COST_MODEL["modes"]:
            raise DeskAdapterError("unknown desk mode %r" % (self.mode,))
        self.spec = spec
        self.socket_dir = socket_dir
        self.python = python if python is not None else sys.executable
        os.makedirs(socket_dir, exist_ok=True)
        self.spec_path = os.path.join(socket_dir, "desk-spec.json")
        with open(self.spec_path, "w", encoding="utf-8") as handle:
            import json
            handle.write(json.dumps(
                spec, ensure_ascii=False, sort_keys=True,
                separators=(",", ":")) + "\n")
        self._servers = {}
        self._turn_seq = 0
        self._closed = False

    def open_turn(self, cell, cycle, desk):
        """Open the desk surface for one turn; returns a TurnContext."""
        if self._closed:
            raise DeskAdapterError("the desk adapter is closed")
        if self.mode == "sub-process":
            if cell not in self._servers:
                path = self._socket_path("cell-%s" % (cell or "epsilon"))
                process = self._spawn(path, cell=cell, desk=None)
                self._servers[cell] = (process, path)
            return TurnContext(self._servers[cell][1],
                               self._servers[cell][0])
        self._turn_seq += 1
        path = self._socket_path("turn-%d-%s" % (self._turn_seq, desk))
        process = self._spawn(path, cell=cell, desk=desk)
        return TurnContext(path, process)

    def close_turn(self, context):
        """Close one turn: re-prompted joins the fresh process (nothing
        is retained); sub-process keeps the persistent server."""
        if self.mode == "re-prompted" and context.process is not None:
            self._stop(context.process)

    def close(self):
        for process, _path in self._servers.values():
            self._stop(process)
        self._servers.clear()
        self._closed = True

    def _socket_path(self, name):
        return os.path.join(self.socket_dir, name + ".sock")

    def _spawn(self, path, cell, desk):
        command = [
            self.python, desk_server_path(),
            "--spec", self.spec_path,
            "--socket", path,
            "--cell", cell,
        ]
        if desk is not None:
            command += ["--desk", desk]
        process = subprocess.Popen(
            command, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL)
        # wait for the socket to appear (bounded; never a wall-clock in
        # any record)
        deadline = time.monotonic() + 10.0
        while time.monotonic() < deadline:
            if os.path.exists(path):
                return process
            if process.poll() is not None:
                raise DeskAdapterError(
                    "the desk server exited (%d) before binding its "
                    "socket" % process.returncode)
            time.sleep(0.01)
        raise DeskAdapterError(
            "the desk server did not bind %s in time" % path)

    @staticmethod
    def _stop(process):
        if process.poll() is None:
            try:
                process.terminate()
            except OSError:
                pass
            try:
                process.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                try:
                    process.kill()
                except OSError:
                    pass
                process.wait(timeout=5.0)
        elif process.returncode not in (0, None):
            pass  # the outage desk dies on purpose — never an error here

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False
