#!/usr/bin/env python3
"""desk_server — the fixture desk's process (the WORLD, never the
conductor).

A stand-in pane server speaking the attested herdr dialect of §3.1 /
§6.3 on its OWN AF_UNIX socket — the same fixture apparatus shape B2's
own selftest ships (FakeHerdrServer): one '\\n'-framed JSON request
{"id","method","params"}; the response echoes the request's string id;
success carries ``result``, failure carries ``error``.  Never the live
herdr socket, never a live pane (H-B4-1).

The server runs the deterministic fixture desk (fixtures/desk.py — the
folded codex §2 desk function-specs, byte-faithful) in attention mode:
``pane.wait_for_output`` returns the desk's deterministic fenced answer
(the §3.6 surface block with the slots filled + the ⟦END <turn_key>⟧
marker echoed from the prompt's fence instruction).  The
``agent.prompt`` success shape is INERT (H-B4-3, carried from B2): the
conductor reads the desk's answer from the fenced read, never from the
success shape.

Scripted world events, all caller-supplied data from the spec:

  * ``outages`` — a (cell, cycle, desk) entry makes the desk process die
    immediately after receiving its prompt, before any answer (the
    model/provider outage — an adapter error, PRD §10.3);
  * ``blocked`` — a (cell, cycle, desk) entry makes the desk answer
    "⟦BLOCKED⟧ needs a human" with no surface block (the blocked
    dialect signal — nothing was decoded).

One server serves one cell (sub-process mode: persistent, all five seat
panes) or one desk of one turn (re-prompted mode: ``--desk``, fresh per
turn, stateless).  Exit code 0 on a clean end.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import socket
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from desk import compose_answer  # noqa: E402

PANES_BY_DESK = {"S": "podium", "G": "G", "Q": "Q", "P": "P", "V": "V"}

_TURN_RE = re.compile(
    r"⟦TURN cell=([^ ]*) cycle=([0-9]+) desk=([SGQPV])⟧")
_MARKER_RE = re.compile(r"⟦END ([0-9a-f]{64})⟧")


def _parse_turn(prompt_text):
    match = _TURN_RE.search(prompt_text)
    if match is None:
        return None
    marker = _MARKER_RE.findall(prompt_text)
    return {
        "cell": match.group(1),
        "cycle": int(match.group(2)),
        "desk": match.group(3),
        "marker": marker[-1] if marker else None,
    }


def _is_scripted(spec, kind, cell, cycle, desk):
    for entry in spec.get(kind) or []:
        if (entry.get("cell") == cell and entry.get("cycle") == cycle
                and entry.get("desk") == desk):
            return True
    return False


def _pane_id(desk, cell):
    return "pane-%s-%s" % (desk.lower(), cell if cell else "epsilon")


class DeskServer:
    def __init__(self, spec, socket_path, cell, desk_only=None):
        self.spec = spec
        self.path = socket_path
        self.cell = cell
        self.desk_only = desk_only
        self._sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._sock.bind(self.path)
        self._sock.listen(4)
        self._sock.settimeout(0.2)
        self._stop = False
        self._last_prompt = None

    def serve(self):
        while not self._stop:
            try:
                conn, _addr = self._sock.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            try:
                self._serve_connection(conn)
            except (OSError, EOFError):
                pass
            finally:
                try:
                    conn.close()
                except OSError:
                    pass

    def _serve_connection(self, conn):
        buf = bytearray()
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

    def _serve_line(self, conn, line):
        try:
            request = json.loads(line.decode("utf-8"))
        except Exception:
            return
        if not isinstance(request.get("id"), str):
            conn.sendall(json.dumps({
                "id": "", "error": {"code": "invalid_request",
                                    "message": "invalid type for id"}},
                ensure_ascii=False).encode("utf-8") + b"\n")
            return
        method = request.get("method")
        params = request.get("params") or {}
        if method == "pane.list":
            desks = [self.desk_only] if self.desk_only else list(
                PANES_BY_DESK)
            panes = []
            for desk in desks:
                panes.append({
                    "pane_id": _pane_id(desk, self.cell),
                    "workspace_id": "ws-" + (self.cell or "epsilon"),
                    "label": PANES_BY_DESK[desk],
                })
            self._reply(conn, request, {"type": "pane_list",
                                        "panes": panes})
            return
        if method == "pane.get":
            desk = self._desk_of_pane(params.get("pane_id"))
            self._reply(conn, request, {"type": "pane_info", "pane": {
                "pane_id": params.get("pane_id"),
                "workspace_id": "ws-" + (self.cell or "epsilon"),
                "label": PANES_BY_DESK.get(desk, ""),
                "agent_status": "idle",
                "focused": False,
                "revision": 1,
                "agent": {"agent_status": "idle"},
            }})
            return
        if method == "agent.prompt":
            self._last_prompt = params.get("text")
            turn = _parse_turn(self._last_prompt or "")
            if turn is None:
                self._reply(conn, request, {"type": "agent_prompted",
                                            "agent": {
                                                "agent_status": "idle"}})
                return
            if _is_scripted(self.spec, "outages", turn["cell"],
                            turn["cycle"], turn["desk"]):
                # the outage: the desk dies mid-turn, before any answer —
                # the adapter error the conductor holds the gate on
                os._exit(0)
            # H-B4-3: the success shape is INERT — the conductor reads
            # the answer from the fenced read below, never from here.
            self._reply(conn, request, {"type": "agent_prompted",
                                        "agent": {
                                            "agent_status": "running"}})
            return
        if method == "pane.wait_for_output":
            turn = _parse_turn(self._last_prompt or "")
            if turn is None or turn.get("marker") is None:
                self._reply(conn, request, {"type": "output_timeout",
                                            "pane_id": params.get(
                                                "pane_id"),
                                            "revision": 1,
                                            "read": None})
                return
            marker = "⟦END " + turn["marker"] + "⟧"
            if _is_scripted(self.spec, "blocked", turn["cell"],
                            turn["cycle"], turn["desk"]):
                text = "⟦BLOCKED⟧ needs a human\n" + marker + "\n"
            else:
                desk = turn["desk"]
                template = (self.spec.get("surface_templates") or {}).get(
                    desk)
                if template is None:
                    self._reply(conn, request, {"type": "output_timeout",
                                                "pane_id": params.get(
                                                    "pane_id"),
                                                "revision": 1,
                                                "read": None})
                    return
                text = compose_answer(template, turn["cell"],
                                      turn["cycle"], desk, marker)
            self._reply(conn, request, {"type": "output_matched",
                                        "pane_id": params.get("pane_id"),
                                        "revision": 1,
                                        "read": {
                                            "pane_id": params.get(
                                                "pane_id"),
                                            "workspace_id": "ws-" + (
                                                self.cell or "epsilon"),
                                            "tab_id": "tab-0",
                                            "source": "visible",
                                            "format": "text",
                                            "text": text,
                                            "truncated": False,
                                            "revision": 1,
                                        }})
            return
        self._reply(conn, request, {"type": "unsupported", "method":
                                    method})

    def _desk_of_pane(self, pane_id):
        for desk, label in PANES_BY_DESK.items():
            if _pane_id(desk, self.cell) == pane_id:
                return desk
        return ""

    def _reply(self, conn, request, result):
        payload = json.dumps({"id": request.get("id"),
                              "result": result},
                             ensure_ascii=False).encode("utf-8") + b"\n"
        conn.sendall(payload)

    def close(self):
        self._stop = True
        try:
            self._sock.close()
        except OSError:
            pass


def main(argv=None):
    parser = argparse.ArgumentParser(prog="desk_server")
    parser.add_argument("--spec", required=True)
    parser.add_argument("--socket", required=True)
    parser.add_argument("--cell", required=True)
    parser.add_argument("--desk", default=None)
    args = parser.parse_args(argv)
    with open(args.spec, "rb") as handle:
        spec = json.loads(handle.read().decode("utf-8"))
    try:
        os.unlink(args.socket)
    except OSError:
        pass
    server = DeskServer(spec, args.socket, args.cell, desk_only=args.desk)
    try:
        server.serve()
    finally:
        server.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
