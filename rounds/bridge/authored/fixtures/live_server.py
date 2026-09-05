#!/usr/bin/env python3
"""live_server — the fixture live server (the bridge, H-BRIDGE-1(a)):
a stand-in for the LIVE herdr box, speaking the REAL herdr dialect of
§3.1 / §6.3 on its OWN AF_UNIX socket — the B2 FakeHerdrServer shape
(one '\\n'-framed JSON request {"id","method","params"}; the response
echoes the request's string id; success carries ``result``, failure
carries ``error`` = {"code","message"}).

The pane world is modelled on the probed live state (commission §3,
read 2026-08-30, read-only — stated here, not re-derived): six panes —

  * ``w8:p2`` label ``podium``  (the centre, desk S — never an agent)
  * ``w8:p3`` label ``G``       (agent pi, idle — the one constituted
                                 desk on the live box)
  * ``w8:p5`` label ``Q``       (no agent — agent_status "unknown")
  * ``w8:p4`` label ``V``       (no agent — agent_status "unknown")
  * ``w8:p6`` label ``P``       (no agent — agent_status "unknown")
  * ``w7:p1`` label null        (an unrelated pane — never indexed)

``agent.prompt`` to a pane with no agent answers the structured error
``agent_not_found`` (the C2 fail-closed case — never a fake answer);
``agent.prompt`` to a constituted pane records the text and answers the
INERT success shape (H-B4-3 carried: the run reads the fenced read,
never the success shape); ``pane.wait_for_output`` on the prompted pane
answers ``output_matched`` with the deterministic fenced answer
(composed by the pinned B4 fixture desk from the spec's §3.6 surface
templates — the same fixture-fiction bytes B4's world used, clearly
labelled) or ``output_timeout`` when nothing was prompted (never a
guessed completion).

Two declared configurations:

  * ``constituted=("G",)`` (the default — the LIVE box as it is): only
    G carries an agent; prompting Q/V/P surfaces ``agent_not_found``;
  * ``constituted="all"`` (the declared fixture fiction for the
    full-path exercise): G/Q/P/V all carry agents and answer
    deterministically, so a whole cycle runs through the real dialect
    end-to-end (the podium stays agent-less — it is the centre).

The ABSENT-SOCKET case (C2's other half) is the *absence* of any server:
a conductor whose resolved live socket path binds nothing fails closed
into outage holds — exercised by the selftest against an unbound path,
never by this server (a stand-in never answers for an absent socket).

The centre guard is the CLIENT's (the imported B2 assert_not_centre
refuses S/podium before any byte), so this server never receives a
podium prompt from the conductor — but it models the live box's answer
(``agent_not_found``) for one that does arrive.  The one-request-per-
connection transport quirk of the live box is not re-modelled (the
attested B2 adapter's reconnect/retry already carries it — never
"optimise" that away); like B2's FakeHerdrServer, one connection may
carry several requests.

Deterministic and stdlib-only.  In-process (B2's FakeHerdrServer shape:
``server = LiveServer(spec, path, constituted=…); server.start();
…; server.halt()``) or as a subprocess (``python3 live_server.py --spec
<spec> --socket <path> [--constituted all]``).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import socket
import sys
import threading

# Never leave a bytecode cache beside a predecessor file: the pinned
# loads import by path and the workspace outside ./authored/ must stay
# untouched.
sys.dont_write_bytecode = True

_HERE = os.path.dirname(os.path.abspath(__file__))
_AUTHORED = os.path.dirname(_HERE)
if _AUTHORED not in sys.path:
    sys.path.insert(0, _AUTHORED)

from surface_contract import compose_answer  # noqa: E402

# The modelled pane world — the live box's probed state (commission
# §3), pane ids included so the label→desk resolution exercises the
# real paths (ids volatile, labels the truth).
PANES = (
    {"pane_id": "w8:p2", "workspace_id": "w8", "label": "podium"},
    {"pane_id": "w8:p3", "workspace_id": "w8", "label": "G"},
    {"pane_id": "w8:p5", "workspace_id": "w8", "label": "Q"},
    {"pane_id": "w8:p4", "workspace_id": "w8", "label": "V"},
    {"pane_id": "w8:p6", "workspace_id": "w8", "label": "P"},
    {"pane_id": "w7:p1", "workspace_id": "w7", "label": None},
)

_TURN_RE = re.compile(
    r"⟦TURN cell=([^ ]*) cycle=([0-9]+) desk=([SGQPV])⟧")
_MARKER_RE = re.compile(r"⟦END ([0-9a-f]{64})⟧")


def absent_socket_path(directory):
    """The C2 absent-socket fixture: a path under ``directory`` that is
    never bound — a conductor resolving the live socket here holds as
    outage, never a stand-in."""
    return os.path.join(directory, "absent-herdr.sock")


class LiveServer:
    """The fixture live box on its own socket (B2's FakeHerdrServer
    shape).  ``requests`` (full envelopes), ``methods`` and
    ``prompts`` (target → last prompt text) record every byte the
    dialect received — the selftest's evidence."""

    def __init__(self, spec, socket_path, constituted=("G",),
                 desk_labels=None):
        self.spec = spec
        self.path = socket_path
        self.constituted = set(constituted if constituted != "all"
                               else ("G", "Q", "P", "V"))
        if desk_labels is None:
            from surface_contract import DESK_LABELS
            desk_labels = DESK_LABELS
        self.desk_labels = dict(desk_labels)  # label -> desk key
        self.requests = []
        self.methods = []
        self.prompts = {}
        self.errors = []  # (code, method, target) per structured error
        self.connections = 0
        self._stop = False
        self._thread = None
        self._sock = None

    # -- the panes --------------------------------------------------------

    def _pane(self, pane_id):
        for pane in PANES:
            if pane["pane_id"] == pane_id:
                return pane
        return None

    def _desk_of_pane(self, pane_id):
        pane = self._pane(pane_id)
        if pane is None or not isinstance(pane.get("label"), str):
            return None
        return self.desk_labels.get(pane["label"])

    def _has_agent(self, pane_id):
        return self._desk_of_pane(pane_id) in self.constituted

    # -- the serving loop (FakeHerdrServer shape) --------------------------

    def start(self):
        try:
            os.unlink(self.path)
        except OSError:
            pass
        self._sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._sock.bind(self.path)
        self._sock.listen(4)
        self._sock.settimeout(0.2)
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    def halt(self):
        self._stop = True
        if self._thread is not None:
            self._thread.join(timeout=5.0)
        if self._sock is not None:
            try:
                self._sock.close()
            except OSError:
                pass
        try:
            os.unlink(self.path)
        except OSError:
            pass

    def _serve(self):
        while not self._stop:
            try:
                conn, _addr = self._sock.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            self.connections += 1
            buf = bytearray()
            try:
                while True:
                    while buf.find(b"\n") == -1:
                        chunk = conn.recv(65536)
                        if not chunk:
                            raise EOFError
                        buf += chunk
                    idx = buf.find(b"\n")
                    line = bytes(buf[:idx])
                    del buf[:idx + 1]
                    self._serve_line(conn, line)
            except (OSError, EOFError):
                pass
            finally:
                try:
                    conn.close()
                except OSError:
                    pass

    def _reply(self, conn, request, result):
        payload = json.dumps({"id": request.get("id"),
                              "result": result},
                             ensure_ascii=False).encode("utf-8") + b"\n"
        conn.sendall(payload)

    def _error(self, conn, request, code, message):
        self.errors.append((code, request.get("method"),
                            (request.get("params") or {}).get("target")))
        payload = json.dumps({"id": request.get("id"),
                              "error": {"code": code,
                                        "message": message}},
                             ensure_ascii=False).encode("utf-8") + b"\n"
        conn.sendall(payload)

    def _serve_line(self, conn, line):
        try:
            request = json.loads(line.decode("utf-8"))
        except Exception:
            return
        if not isinstance(request.get("id"), str):
            # the live dialect (§6.3): the envelope id must be a JSON
            # STRING — refused before dispatch, exactly as herdr 0.8.2
            # was probed to answer
            self._error(conn, request, "invalid_request",
                        "invalid request: invalid type for id")
            return
        self.requests.append(request)
        self.methods.append(request.get("method"))
        method = request.get("method")
        params = request.get("params") or {}
        if not isinstance(params, dict):
            self._error(conn, request, "invalid_request",
                        "params must be a JSON object")
            return
        if method == "pane.list":
            panes = [dict(pane) for pane in PANES]
            self._reply(conn, request, {"type": "pane_list",
                                        "panes": panes})
            return
        if method == "pane.get":
            pane_id = params.get("pane_id")
            pane = self._pane(pane_id)
            if pane is None:
                self._error(conn, request, "pane_not_found",
                            "no pane %r" % (pane_id,))
                return
            info = {
                "pane_id": pane_id,
                "workspace_id": pane["workspace_id"],
                "label": pane.get("label"),
                "agent_status": ("idle" if self._has_agent(pane_id)
                                 else "unknown"),
                "focused": False,
                "revision": 1,
            }
            if self._has_agent(pane_id):
                info["agent"] = {"agent_status": "idle"}
            self._reply(conn, request, {"type": "pane_info",
                                        "pane": info})
            return
        if method == "agent.get":
            pane_id = params.get("target")
            if self._pane(pane_id) is None:
                self._error(conn, request, "pane_not_found",
                            "no pane %r" % (pane_id,))
                return
            if not self._has_agent(pane_id):
                self._error(conn, request, "agent_not_found",
                            "no agent on pane %r" % (pane_id,))
                return
            self._reply(conn, request, {"type": "agent_info", "agent": {
                "agent_status": "idle"}})
            return
        if method == "agent.prompt":
            pane_id = params.get("target")
            text = params.get("text")
            if self._pane(pane_id) is None:
                self._error(conn, request, "pane_not_found",
                            "no pane %r" % (pane_id,))
                return
            if not self._has_agent(pane_id):
                # C2's fail-closed half: a desk resolving to a pane with
                # no agent surfaces agent_not_found — never a fake
                # answer, never a fixture stand-in.
                self._error(conn, request, "agent_not_found",
                            "no agent on pane %r" % (pane_id,))
                return
            if not isinstance(text, str):
                self._error(conn, request, "invalid_request",
                            "prompt text must be a string")
                return
            self.prompts[pane_id] = text
            # H-B4-3 carried: the success shape is INERT — the run reads
            # the answer from the fenced read below, never from here.
            self._reply(conn, request, {"type": "agent_prompted",
                                        "agent": {
                                            "agent_status": "running"}})
            return
        if method == "pane.wait_for_output":
            pane_id = params.get("pane_id")
            if self._pane(pane_id) is None:
                self._error(conn, request, "pane_not_found",
                            "no pane %r" % (pane_id,))
                return
            text = self.prompts.get(pane_id)
            read = self._compose_fenced_read(pane_id, text)
            if read is None:
                # nothing prompted / no marker: a legitimate wait end,
                # never a guessed completion (H-B2-3)
                self._reply(conn, request, {"type": "output_timeout",
                                            "pane_id": pane_id,
                                            "revision": 1,
                                            "read": None})
                return
            self._reply(conn, request, {"type": "output_matched",
                                        "pane_id": pane_id,
                                        "revision": 1,
                                        "read": read})
            return
        self._error(conn, request, "method_not_found",
                    "unknown method %r" % (method,))

    def _compose_fenced_read(self, pane_id, text):
        """The deterministic fenced answer of the prompted pane — the
        pinned B4 fixture desk composing the spec's §3.6 surface
        template (the fixture fiction, clearly labelled).  Returns the
        full PaneReadResult or None when nothing can be answered
        honestly."""
        if not isinstance(text, str):
            return None
        turn = _TURN_RE.search(text)
        if turn is None:
            return None
        markers = _MARKER_RE.findall(text)
        if not markers:
            return None
        desk = turn.group(3)
        if self._desk_of_pane(pane_id) != desk:
            return None  # a reminted id never gets another desk's answer
        template = (self.spec.get("surface_templates") or {}).get(desk)
        if template is None:
            return None
        marker = "⟦END " + markers[-1] + "⟧"
        answer = compose_answer(template, turn.group(1),
                                int(turn.group(2)), desk, marker)
        pane = self._pane(pane_id)
        return {
            "pane_id": pane_id,
            "workspace_id": pane["workspace_id"],
            "tab_id": "tab-0",
            "source": "visible",
            "format": "text",
            "text": answer,
            "truncated": False,
            "revision": 1,
        }


def main(argv=None):
    parser = argparse.ArgumentParser(prog="live_server")
    parser.add_argument("--spec", required=True)
    parser.add_argument("--socket", required=True)
    parser.add_argument("--constituted", default="G",
                        help="comma-separated desk keys carrying an "
                             "agent, or 'all' (G/Q/P/V)")
    args = parser.parse_args(argv)
    with open(args.spec, "rb") as handle:
        spec = json.loads(handle.read().decode("utf-8"))
    constituted = tuple(args.constituted.split(",")) \
        if args.constituted != "all" else "all"
    server = LiveServer(spec, args.socket, constituted=constituted)
    server.start()
    try:
        while server._thread is not None and server._thread.is_alive():
            server._thread.join(timeout=1.0)
    except KeyboardInterrupt:
        pass
    finally:
        server.halt()
    return 0


if __name__ == "__main__":
    sys.exit(main())
