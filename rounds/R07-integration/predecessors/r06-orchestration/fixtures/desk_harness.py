#!/usr/bin/env python3
"""desk_harness — the fixture desk harness (R06 · orchestration,
H-ORCH-1): a deterministic fake desk box for the authoring pass — no
live box, no constituted desks.  It speaks the REAL herdr dialect
(one '\\n'-framed JSON request {"id","method","params"}; the response
echoes the request's string id; success carries ``result``, failure
carries ``error`` = {"code","message"}) on its OWN AF_UNIX socket —
the bridge's fixture live-server shape, which is B2's
FakeHerdrServer shape.  The dialect itself is the attested B2
adapter's, imported by the conductor — this harness is declared
fixture apparatus, never the production surface (the production
surface is the imported instrument; no re-implementation rides the
orchestration path).

The pane world is the probed live box's shape (stated, not
re-derived): podium (label ``podium``, desk S — never an agent), the
four corner desks G/Q/P/V, and one unlabelled pane that is never
indexed.  ``constituted`` declares which desks carry an agent:

  * ``constituted=()`` / a subset — the unconstituted-desk case:
    ``agent.prompt`` to a pane with no agent answers the structured
    error ``agent_not_found`` (never a fake answer, never a fixture
    stand-in — lens 6);
  * ``constituted="all"`` — G/Q/P/V all carry agents and answer
    deterministically (the declared fixture fiction for the full-path
    exercise; the podium stays agent-less — it is the centre).

The deterministic fenced answer is composed by the pinned B4 fixture
desk (compose_answer — imported, never re-authored) from the harness
spec's §3.6 surface templates, keyed by the prompt's
``⟦TURN cell=… step=… desk=…⟧`` header and the fence marker.  The
answers are clearly labelled stand-in fiction (H-B4-1 carried) and
carry the encoding needle (∞0′ → ‖) in the V slot (lens 4).  With
``omit_infinity`` declared, the V answer's ∞0′ slot is renamed away —
a still-lawful surface whose return slot is absent — the
no-V-without-∞0′ refusal case (seal line 8, R6).

The ABSENT-SOCKET case is the *absence* of any server: a conductor
whose resolved live socket path binds nothing fails closed into
outage holds — exercised by the selftest against an unbound path,
never by this harness (a stand-in never answers for an absent
socket).

The centre guard is the CLIENT's (the imported B2 assert_not_centre
refuses S/podium before any byte), so this harness never receives a
podium prompt from the conductor — but it records every byte it does
receive (``requests`` / ``methods`` / ``prompts`` / ``errors`` /
``connections``), so the selftest can assert ZERO podium prompts and
ZERO connections for a refused write.

Deterministic and stdlib-only.  In-process (B2's FakeHerdrServer
shape) or as a subprocess.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import socket
import sys
import threading

sys.dont_write_bytecode = True

_HERE = os.path.dirname(os.path.abspath(__file__))
_AUTHORED = os.path.dirname(_HERE)
if _AUTHORED not in sys.path:
    sys.path.insert(0, _AUTHORED)

from surface_contract import compose_answer  # noqa: E402

# The modelled pane world — the probed live box's shape (pane ids
# included so the label→desk resolution exercises the real paths).
PANES = (
    {"pane_id": "w8:p2", "workspace_id": "w8", "label": "podium"},
    {"pane_id": "w8:p3", "workspace_id": "w8", "label": "G"},
    {"pane_id": "w8:p5", "workspace_id": "w8", "label": "Q"},
    {"pane_id": "w8:p4", "workspace_id": "w8", "label": "V"},
    {"pane_id": "w8:p6", "workspace_id": "w8", "label": "P"},
    {"pane_id": "w7:p1", "workspace_id": "w7", "label": None},
)

_TURN_RE = re.compile(
    r"⟦TURN cell=([^ ]*) step=([0-9]+) desk=([SGQPV])⟧")
_MARKER_RE = re.compile(r"⟦END ([0-9a-f]{64})⟧")


def absent_socket_path(directory):
    """The absent-socket fixture: a path under ``directory`` that is
    never bound — a conductor resolving the live socket here holds as
    outage, never a stand-in (lens 6)."""
    return os.path.join(directory, "absent-herdr.sock")


class DeskHarness:
    """The fixture desk box on its own socket.  ``requests`` (full
    envelopes), ``methods``, ``prompts`` (pane id → last prompt text),
    ``errors`` and ``connections`` record every byte the dialect
    received — the selftest's evidence."""

    def __init__(self, spec, socket_path, constituted="all",
                 desk_labels=None):
        self.spec = spec
        self.path = socket_path
        self.constituted = set(constituted if constituted != "all"
                               else ("G", "Q", "P", "V"))
        self.omit_infinity = bool((spec or {}).get("omit_infinity"))
        if desk_labels is None:
            from surface_contract import DESK_LABELS
            desk_labels = DESK_LABELS
        self.desk_labels = dict(desk_labels)
        self.requests = []
        self.methods = []
        self.prompts = {}
        self.errors = []
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

    # -- the serving loop (B2's FakeHerdrServer shape) --------------------

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
            self._reply(conn, request, {"type": "pane_list",
                                        "panes": [dict(pane)
                                                  for pane in PANES]})
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
                # the unconstituted-desk case: agent_not_found — never
                # a fake answer, never a fixture stand-in (lens 6)
                self._error(conn, request, "agent_not_found",
                            "no agent on pane %r" % (pane_id,))
                return
            if not isinstance(text, str):
                self._error(conn, request, "invalid_request",
                            "prompt text must be a string")
                return
            self.prompts[pane_id] = text
            # the success shape is INERT (H-B4-3 carried): the
            # conductor reads the fenced read, never this
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
        pinned B4 fixture desk composing the harness spec's §3.6
        surface template (stand-in fiction, clearly labelled)."""
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
        if self.omit_infinity and desk == "V":
            # the no-V-without-∞0′ refusal case: the V answer's ∞0′
            # slot is renamed away — a still-LAWFUL surface whose
            # return slot is absent, so the conductor must REFUSE
            # (seal line 8, R6), never hold on a parse accident
            answer = answer.replace("∞0':", "RENAMED':")
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
    parser = argparse.ArgumentParser(prog="desk_harness")
    parser.add_argument("--spec", required=True)
    parser.add_argument("--socket", required=True)
    parser.add_argument("--constituted", default="all",
                        help="comma-separated desk keys carrying an "
                             "agent, or 'all' (G/Q/P/V); empty string "
                             "= none")
    args = parser.parse_args(argv)
    with open(args.spec, "rb") as handle:
        spec = json.loads(handle.read().decode("utf-8"))
    constituted = tuple(args.constituted.split(",")) \
        if args.constituted not in ("", "all") else (
            "all" if args.constituted == "all" else ())
    server = DeskHarness(spec, args.socket, constituted=constituted)
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
