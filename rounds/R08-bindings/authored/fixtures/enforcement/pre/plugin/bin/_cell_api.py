#!/usr/bin/env python3
"""fixture _cell_api.py — the PRE-integration state, finding i: the
plugin's own socket client (a second wire).  Declared fixture
apparatus: this file exists ONLY to prove the enforcement suite fails
the pre state, and it is replaced by the authored reduced surface
(authored/enforcement/plugin-bin/_cell_api.py) before the suite may
read clean.  Never the production surface."""
from __future__ import annotations

import json
import os
import socket
import sys
import uuid

DEFAULT_SOCKET = os.path.expanduser("~/.config/herdr/herdr.sock")
TIMEOUT_S = 15.0


class CellApiError(RuntimeError):
    def __init__(self, message, payload=None):
        super().__init__(message)
        self.payload = payload


def call(method, params=None):
    path = os.environ.get("HERDR_SOCKET_PATH") or DEFAULT_SOCKET
    request = {"id": uuid.uuid4().hex[:12], "method": method,
               "params": params or {}}
    payload = (json.dumps(request, separators=(",", ":")) + "\n").encode()
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
    line = buffer.split(b"\n", 1)[0].strip()
    response = json.loads(line)
    if "result" not in response:
        raise CellApiError("error", response)
    return response["result"]


if __name__ == "__main__":
    print(__doc__.strip(), file=sys.stderr)
    sys.exit(2)
