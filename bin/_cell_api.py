#!/usr/bin/env python3
"""_cell_api.py — the cell's own minimal herdr socket client.

WHY THIS EXISTS (OPEN-4, closed): there is no `herdr api call` verb. `herdr api` has
only `snapshot` and `schema`. Arbitrary methods are reached over the unix socket with
a request envelope {"id", "method", "params"} — all three required (schema
`request.required = [id, method, params]`, protocol 20).

The cell deliberately carries its own client rather than importing a helper from
outside the plugin: a plugin must not depend on files it does not ship. Sixty lines of
stdlib instead.

Usage (library):   from _cell_api import call, CellApiError
Usage (CLI):       _cell_api.py <method> ['<json params>' | @/path/params.json]

Never writes anything. Never calls a method it was not handed.
"""
from __future__ import annotations

import json
import os
import socket
import sys
import uuid

DEFAULT_SOCKET = os.path.expanduser("~/.config/herdr/herdr.sock")
TIMEOUT_S = 15.0


class CellApiError(RuntimeError):
    """A herdr error_response, or a transport failure. Carries the raw payload."""

    def __init__(self, message: str, payload=None):
        super().__init__(message)
        self.payload = payload


def socket_path() -> str:
    # HERDR_SOCKET_PATH is injected into every plugin invocation (verified env surface).
    return os.environ.get("HERDR_SOCKET_PATH") or DEFAULT_SOCKET


def call(method: str, params: dict | None = None) -> dict:
    """Send one request, return its `result` object. Raise CellApiError on anything else."""
    path = socket_path()
    request = {"id": uuid.uuid4().hex[:12], "method": method, "params": params or {}}
    payload = (json.dumps(request, separators=(",", ":")) + "\n").encode()

    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.settimeout(TIMEOUT_S)
            sock.connect(path)
            sock.sendall(payload)
            buffer = b""
            while b"\n" not in buffer:
                chunk = sock.recv(65536)
                if not chunk:
                    break
                buffer += chunk
    except OSError as exc:
        raise CellApiError(f"socket {path}: {exc}") from exc

    line = buffer.split(b"\n", 1)[0].strip()
    if not line:
        raise CellApiError(f"empty response from {path}")
    try:
        response = json.loads(line)
    except json.JSONDecodeError as exc:
        raise CellApiError(f"unparseable response: {line[:400]!r}") from exc

    if "result" not in response:
        raise CellApiError(
            "herdr returned an error: "
            + json.dumps(response.get("error", response), separators=(",", ":")),
            response,
        )
    return response["result"]


def context() -> dict:
    """The PluginInvocationContext handed to this invocation (OPEN-3, closed).

    Falls back to the flat env vars when the JSON blob is absent, so a script invoked
    outside a plugin context still knows where it stands instead of guessing.
    """
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
    """Where the cell keeps its own records. Never question.md."""
    path = os.environ.get("HERDR_PLUGIN_STATE_DIR") or os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))),
        "state",
    )  # bin/ → plugin/ → <cell root>/state — derived from this file's own location
    os.makedirs(path, exist_ok=True)
    return path


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    method = argv[1]
    params: dict = {}
    if len(argv) > 2:
        arg = argv[2]
        text = open(arg[1:], encoding="utf-8").read() if arg.startswith("@") else arg
        params = json.loads(text)
    try:
        print(json.dumps(call(method, params), indent=1))
    except CellApiError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
