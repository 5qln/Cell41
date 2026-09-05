#!/usr/bin/env python3
"""_cell_api.py — the plugin's shared read surface, REDUCED (the bindings
round, C4 finding i): the socket client is gone — no wire of any kind
lives in the plugin anymore.  The only socket client on the box remains
the pinned engine Instrument (K1).

WHAT CHANGED AND WHY (the round's design decision, declared here):
  * before: a ~60-line unix-socket client (a request envelope over the
    removed wire) — a second wire beside the engine's pinned
    Instrument;
  * after: the same reads the plugin bins consumed are re-served over
    the platform CLI's declared READ verbs (workspace list · pane list ·
    api snapshot · api schema — all read-only observations).  The CLI
    does the socket work inside the platform binary, which is the
    platform, not the soft layer — the plugin holds no client of its
    own;
  * the arbitrary-method path is REMOVED: there is no call() anymore,
    so no soft-layer file can reach a write verb through this module —
    its whole reach is the fixed read verbs below (C2 held by
    construction: /states remains the only desk-facing read through
    the seam; these helpers serve the pre-existing human-TTY and
    observer bins, never a desk drive).

The reduced read-only surface (the declared one):
    workspace_list()                -> the platform's workspace rows
    pane_list(workspace_id=None)    -> the pane rows (optionally filtered)
    pane_get(pane_id)               -> one pane row, by id
    snapshot()                      -> the live session snapshot (api)
    schema()                        -> the bundled api schema (api)
    context()                       -> the invocation context (env only)
    state_dir()                     -> the cell's own record dir

Failure discipline (lens 6): a read that fails (platform binary absent,
server unreachable, unparseable report, non-zero exit) raises
CellApiError carrying the raw payload — callers report INCONCLUSIVE or
drop the event, never substitute a value.  No retry loops, no guesses.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

# The platform CLI (data, one place to change).  HERDR_BIN is read here —
# this module is the one place the plugin resolves the platform binary.
DEFAULT_PLATFORM_BIN = "herdr"
CLI_TIMEOUT_S = 15.0

# The fixed read-verb surface — nothing else is reachable through this
# module (no arbitrary methods, no write verbs, no wire).
_READ_VERBS = (
    ("workspace", "list"),
    ("pane", "list"),
    ("api", "snapshot"),
    ("api", "schema"),
)


class CellApiError(RuntimeError):
    """A platform read failed — transport or report.  Carries the raw
    payload; the message is honest, never a substitution."""

    def __init__(self, message: str, payload=None):
        super().__init__(message)
        self.payload = payload


def _platform_bin() -> str:
    return os.environ.get("HERDR_BIN") or DEFAULT_PLATFORM_BIN


def _read_verb(*argv: str) -> dict:
    """Run ONE fixed read verb through the platform CLI and return its
    JSON result object.  Fail closed: any failure raises CellApiError."""
    verb = tuple(argv)
    if verb not in _READ_VERBS:
        raise CellApiError(
            "refusing an undeclared verb %r — this module's reach is "
            "the fixed read surface %s, never an arbitrary method"
            % (argv, [v[0] + " " + v[1] for v in _READ_VERBS]))
    command = [_platform_bin()] + list(argv)
    try:
        completed = subprocess.run(command, capture_output=True,
                                   timeout=CLI_TIMEOUT_S)
    except OSError as exc:
        raise CellApiError(
            "the platform CLI is unreachable (%s) — INCONCLUSIVE, "
            "never a stand-in" % exc) from exc
    except subprocess.TimeoutExpired as exc:
        raise CellApiError(
            "the platform read timed out after %.0fs — INCONCLUSIVE, "
            "never a stand-in" % CLI_TIMEOUT_S) from exc
    raw = completed.stdout
    try:
        envelope = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CellApiError(
            "unparseable platform report: %r (%s) — INCONCLUSIVE"
            % (raw[:200].decode("utf-8", "replace"), exc)) from exc
    if completed.returncode != 0 or not isinstance(envelope, dict):
        raise CellApiError(
            "the platform read failed (exit %d): %s — INCONCLUSIVE"
            % (completed.returncode,
               json.dumps(envelope.get("error", envelope)
                          if isinstance(envelope, dict) else envelope,
                          separators=(",", ":"))[:300]),
            envelope)
    return envelope.get("result", envelope) if isinstance(
        envelope, dict) else envelope


def workspace_list() -> list:
    """The platform's workspace rows (read-only observation)."""
    result = _read_verb("workspace", "list")
    return result.get("workspaces", []) if isinstance(result, dict) else []


def pane_list(workspace_id=None) -> list:
    """The platform's pane rows, optionally filtered by workspace id
    (read-only observation)."""
    result = _read_verb("pane", "list")
    panes = result.get("panes", []) if isinstance(result, dict) else []
    if workspace_id is None:
        return panes
    return [pane for pane in panes
            if pane.get("workspace_id") == workspace_id]


def pane_get(pane_id: str) -> dict:
    """One pane row by id, from the same read (never a wire write)."""
    for pane in pane_list():
        if pane.get("pane_id") == pane_id:
            return pane
    raise CellApiError(
        "no pane row for %r — INCONCLUSIVE, never a stand-in" % pane_id)


def snapshot() -> dict:
    """The live session snapshot (the api metadata read)."""
    result = _read_verb("api", "snapshot")
    if isinstance(result, dict) and isinstance(result.get("snapshot"),
                                                dict):
        return result["snapshot"]
    return result if isinstance(result, dict) else {}


def schema() -> dict:
    """The bundled api schema (the api metadata read)."""
    result = _read_verb("api", "schema")
    return result if isinstance(result, dict) else {}


def context() -> dict:
    """The PluginInvocationContext handed to this invocation (env only).
    Falls back to the flat env vars when the JSON blob is absent, so a
    script invoked outside a plugin context still knows where it stands
    instead of guessing."""
    raw = os.environ.get("HERDR_PLUGIN_CONTEXT_JSON")
    ctx: dict = {}
    if raw:
        try:
            ctx = json.loads(raw)
        except json.JSONDecodeError:
            ctx = {}
    ctx.setdefault("workspace_id", os.environ.get("HERDR_WORKSPACE_ID"))
    ctx.setdefault("tab_id", os.environ.get("HERDR_TAB_ID"))
    ctx.setdefault("focused_pane_id", os.environ.get("HERDR_PANE_ID"))
    return ctx


def state_dir() -> str:
    """Where the cell keeps its own records.  Never question.md."""
    return (os.environ.get("HERDR_PLUGIN_STATE_DIR")
            or "/home/deploy/the-cell/state")


def main(argv: list) -> int:
    if len(argv) < 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    verb = argv[1]
    try:
        if verb == "snapshot":
            print(json.dumps(snapshot(), ensure_ascii=False,
                             sort_keys=True))
        elif verb == "schema":
            print(json.dumps(schema(), ensure_ascii=False,
                             sort_keys=True))
        elif verb == "workspace-list":
            print(json.dumps(workspace_list(), ensure_ascii=False,
                             sort_keys=True))
        elif verb == "pane-list":
            print(json.dumps(pane_list(
                argv[2] if len(argv) > 2 else None),
                ensure_ascii=False, sort_keys=True))
        elif verb == "pane-get" and len(argv) > 2:
            print(json.dumps(pane_get(argv[2]), ensure_ascii=False,
                             sort_keys=True))
        else:
            print("usage: _cell_api.py snapshot|schema|workspace-list|"
                  "pane-list [workspace_id]|pane-get <pane_id>",
                  file=sys.stderr)
            return 2
    except CellApiError as exc:
        print("ERROR %s" % exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
