#!/usr/bin/env python3
"""cost — the desk invocation surface and the per-turn memory/token cost
accounting (R05 · B4, H-B4-2 — extended by the bridge, C1/C2/C6).

Three modes, all real, all instrumented:

  * ``sub-process`` (persistent) — one long-lived fixture desk process
    per cell; the desk bundle is sent once; per-turn cost is prompt +
    answer tokens, and the memory cost is the live process's resident
    footprint (measured from /proc/<pid>/status — VmRSS);
  * ``re-prompted`` (stateless) — a fresh desk process per turn; the
    full desk bundle is re-sent EVERY turn (the re-prompt cost) and
    nothing is retained between turns (memory cost 0);
  * ``live`` (the bridge — joined to the live herdr socket, never a
    stand-in) — ``open_turn`` returns a ``TurnContext`` whose socket is
    the LIVE herdr socket (``HERDR_SOCKET_PATH``, else
    ``~/.config/herdr/herdr.sock``) and whose process is ``None``: no
    fixture ``desk_server.py`` is ever spawned (C2 — the mode fails
    closed into holds at the conductor, never into a fixture).  The
    conductor's imported B2 ``Instrument`` speaks the real herdr
    dialect on that socket; the per-turn cost is measured exactly like
    the other modes, with memory 0 (nothing local is retained) and no
    bundle re-sent.

The two fixture modes are byte-identical to B4 (C6 — nothing attested
is un-done): the same declared charges, the same default mode, the same
spawn path (B4's pinned ``fixtures/desk_server.py``, never the live
socket — H-B4-1).  The conservative default is DECLARED DATA —
``COST_MODEL["default_mode"]`` — never hard-coded logic: the conductor
resolves its mode from this table through ``softconfig`` (see run.py).

The spend ceiling is enforced from declared charges, never from the
measurements: each charge is a conservative stand-in (declared ≥ the
measured per-turn cost — asserted by the selftest), so a ceiling reached
surfaces as a held gate, never a silent kill, never an overspend (C4).
The live mode's charges are the same declared stand-ins (the live
per-Pi measurement awaits a constituted desk — H-B4-2 carried into
H-BRIDGE-1) and are soft-config-overridable like every other charge.

Deterministic and stdlib-only (the desk processes the two fixture modes
spawn are B4's fixture desk server — pinned by surface_contract; the
live mode's only I/O is the live socket, and it is the attested B2
instrument's).
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
    "live_socket_path",
    "spend_from_records",
]

_HERE = os.path.dirname(os.path.abspath(__file__))
# The fixture desk server is B4's pinned file (the immediate
# predecessor's fixtures — imported by path via surface_contract's sha
# pin, never copied, never re-authored).  The two fixture modes spawn
# exactly it; the live mode never does.
_B4_FIXTURES = os.path.normpath(os.path.join(
    _HERE, "..", "predecessors", "b4", "fixtures"))


def desk_server_path():
    return os.path.join(_B4_FIXTURES, "desk_server.py")


def live_socket_path(override=None):
    """The live herdr socket (C1): the caller's ``override``, else
    ``HERDR_SOCKET_PATH``, else the declared default
    ``~/.config/herdr/herdr.sock`` (commission §3: the env var is empty
    on the box — the default is resolved).  Resolved fresh on every
    call, never remembered."""
    if override:
        return override
    return (os.environ.get("HERDR_SOCKET_PATH")
            or os.path.expanduser("~/.config/herdr/herdr.sock"))


# ---------------------------------------------------------------------------
# The declared cost model — DATA.  The default mode and the per-desk
# charges live here, never in the conductor's control flow (H-B4-2): the
# conductor reads them through softconfig, whose declared defaults are
# exactly these bytes (C3/C4).
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
        "live": {
            "retained": "none-local",
            "bundle_sent_each_turn": False,
            "memory": "none-measured",
            "description": ("the live herdr socket (the bridge, C1/C2): "
                            "the turn speaks the real herdr dialect "
                            "through the imported B2 Instrument — the "
                            "desk is resolved by pane label, prompted "
                            "with agent.prompt, read to the ⟦END …⟧ "
                            "fence; NO fixture desk_server.py is ever "
                            "spawned (process is None); memory = 0"),
        },
    },
    # Declared per-desk per-turn charges (token units) — conservative
    # stand-ins: each charge is ≥ the measured per-turn cost (prompt
    # tokens + 3× answer tokens + bundle tokens when re-sent) for every
    # fixture turn.  The live per-Pi measurement awaits a constituted
    # desk (H-B4-2 carried; H-BRIDGE-1 defers the paid turn).  The live
    # table mirrors the re-prompted stand-ins and is soft-config-
    # overridable like the rest (C3).
    "charges": {
        "sub-process": {"G": 2200, "Q": 2500, "P": 2900, "V": 3800},
        "re-prompted": {"G": 2600, "Q": 3000, "P": 3400, "V": 4600},
        "live": {"G": 2600, "Q": 3000, "P": 3400, "V": 4600},
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
    declared-default reader; the conductor reads charges through
    softconfig.budget_of, whose defaults are these bytes)."""
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


def spend_from_records(records, mode, charge_for=charge_for):
    """The spend the ledger accounts — a pure function of the completed
    turn records alone (each gate letter charges once per record), so a
    fresh process recomputes the same spend from the ledger alone (C3,
    C4: accounted BEFORE each turn).  Seed, hold and plant records
    charge nothing (no model turn happened).

    ``charge_for`` defaults to the declared-data reader; the conductor
    passes its soft-config-aware resolver so the budget path reads
    through the soft layer (C3)."""
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
# The desk processes (the two fixture modes run B4's fixture server;
# the live mode runs none).
# ---------------------------------------------------------------------------


class DeskAdapterError(Exception):
    """A desk process could not be started or observed."""


class TurnContext:
    """One turn's desk surface: the socket path the imported B2
    instrument speaks on, and the process handle (``None`` in live mode
    — the turn is joined to the live socket, no process was spawned)."""

    def __init__(self, socket_path, process):
        self.socket_path = socket_path
        self.process = process
        self._memory_bytes = None

    def memory_bytes(self):
        """The live process's resident footprint (VmRSS) — measured
        from /proc/<pid>/status.  A process already gone measures 0
        (re-prompted turns are stateless by construction), and a live
        turn has no process at all: 0 (nothing local is retained)."""
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
    """The desk invocation surface — three modes.

    ``DeskAdapter(spec, socket_dir, mode=None, python=None,
    live_socket=None)`` — ``mode`` defaults to the DECLARED data table
    (COST_MODEL["default_mode"]); the spec is written to a scratch file
    the desk server reads (cells, surface templates, outages, blocked
    turns — all caller-supplied data).

    sub-process: the cell's server process is started once and reused
    for every turn of that cell (persistent).  re-prompted: a fresh
    server process is started per turn and joined when the turn closes
    (stateless).  Every spawned process speaks the attested herdr
    dialect on its OWN socket (H-B4-1: never the live socket).

    live (the bridge, C1/C2): ``open_turn`` returns
    ``TurnContext(live_socket_path, None)`` — the resolved live herdr
    socket (``live_socket`` arg > ``HERDR_SOCKET_PATH`` > the declared
    default), resolved fresh per turn, never remembered.  NO
    ``desk_server.py`` is ever spawned by this mode: an unreachable
    socket or a no-agent desk surfaces as a hold at the conductor (the
    adapter reports nothing it has not read — lens 6).
    """

    def __init__(self, spec, socket_dir, mode=None, python=None,
                 live_socket=None):
        self.mode = mode if mode is not None else DEFAULT_MODE
        if self.mode not in COST_MODEL["modes"]:
            raise DeskAdapterError("unknown desk mode %r" % (self.mode,))
        self.spec = spec
        self.socket_dir = socket_dir
        self.python = python if python is not None else sys.executable
        self.live_socket_override = live_socket
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
        if self.mode == "live":
            # The live branch: the turn is joined to the LIVE herdr
            # socket — resolved fresh (env or the declared default),
            # process None, no spawn of any kind (C1/C2).  Whether the
            # socket is reachable is decided by the conductor's attested
            # instrument when it actually speaks — never guessed here.
            return TurnContext(live_socket_path(self.live_socket_override),
                               None)
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
        is retained); sub-process keeps the persistent server; live has
        no process (no-op)."""
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
        # the fixture server imports its desk module from the pinned B4
        # predecessor directory — never let the subprocess leave a
        # bytecode cache beside a predecessor file (the workspace
        # outside ./authored/ must stay untouched)
        env = dict(os.environ)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        process = subprocess.Popen(
            command, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, env=env)
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
