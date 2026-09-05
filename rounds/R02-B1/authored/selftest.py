#!/usr/bin/env python3
"""selftest — R02 · B1 (the read-only walker), author-side checks.

Every test below names, in its first docstring line, the criterion ID it
exercises (C1, C2, C3, C4, K1, K2, K3, K4) and the quantity it measures;
a test that times something names the operation it timed.

The fake herdr server binds its OWN AF_UNIX socket inside a
tempfile-created directory and replays the transcripts in fixtures/ —
the live herdr socket is never touched, and every ledger path is inside
a tempfile-created directory (never the attested plant).  The fixtures
carry the §6.2 human-driven cycle and the restart / relabel / dialect
transcripts.  Run:  python3 selftest.py
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import random
import socket
import string
import subprocess
import sys
import tempfile
import threading
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
LEDGER_DIR = os.environ.get(
    "FRACTAL_LEDGER_DIR", "/home/deploy/the-cell/ledger")
sys.path.insert(0, LEDGER_DIR)

import dialects  # noqa: E402
import instrument as instrument_module  # noqa: E402
import walker as walker_module  # noqa: E402
from instrument import (  # noqa: E402
    DESK_LABELS,
    READ_ONLY_METHODS,
    AgentNotFoundError,
    DeskResolutionError,
    HerdrProtocolError,
    HerdrRemoteError,
    Instrument,
    MethodNotAllowedError,
    PaneNotFoundError,
    SocketTransportError,
)
from dialects import BLOCKED, NO_VERDICT, dominant, map_signal  # noqa: E402
from walker import COURSE, Walker, next_delay  # noqa: E402
from fractal_ledger import (  # noqa: E402
    GENESIS,
    LedgerLoader,
    LedgerVerifier,
    LedgerWriter,
    make_record,
    tail_record,
)

FIXTURES = os.path.join(HERE, "fixtures")

CYCLE_FIXTURE = "cycle_transcript.json"
BLOCKED_FIXTURE = "blocked_episode_transcript.json"
RESTART_FIXTURE = "restart_transcript.json"
RELABEL_FIXTURE = "relabel_transcript.json"
DIALECT_FIXTURE = "dialect_signals.json"
HUMAN_FIXTURE = "human_records.json"

NEEDLE = "∞0′ → ‖"  # the encoding-lens bytes (commission lens 4)


def load_fixture(name):
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as handle:
        return json.load(handle)


# ---------------------------------------------------------------------------
# The fake herdr server — the verifier's §6.2 shape: own AF_UNIX path in a
# tempfile directory, one '\n'-framed JSON request {"id","method","params"},
# records every method name (C3's evidence), answers from a handler, and can
# close the connection mid-run (C4).  Never a live socket.
# ---------------------------------------------------------------------------

class FakeHerdrServer:
    def __init__(self, directory, name="herdr-test.sock"):
        self.path = os.path.join(directory, name)
        self.requests = []       # full envelopes received (C3 evidence)
        self.methods = []        # method names only
        self.bytes_in = 0
        self.connections = 0
        self.handler = None      # callable(request) -> (response, close)
        self.mismatches = []     # request method != scripted expectation
        self._stop = False
        self._thread = None
        self._sock = None

    def start(self, handler):
        self.handler = handler
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
                        self.bytes_in += len(chunk)
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

    def _serve_line(self, conn, line):
        try:
            request = json.loads(line.decode("utf-8"))
        except Exception as exc:
            self.mismatches.append(("unparseable request", repr(exc)))
            return
        self.requests.append(request)
        self.methods.append(request.get("method"))
        # The live dialect (probed on herdr 0.8.2): the envelope id must be
        # a JSON string.  A non-string id is refused before dispatch with
        # {"id": "", "error": {"code": "invalid_request", ...}} — exactly
        # what the live server answered for id=7 and id=None.
        if not isinstance(request.get("id"), str):
            refusal = {"id": "", "error": {
                "code": "invalid_request",
                "message": "invalid request: invalid type for id"}}
            conn.sendall(json.dumps(refusal, ensure_ascii=False).encode(
                "utf-8") + b"\n")
            return
        if self.handler is None:
            return
        response, close = self.handler(request)
        if close:
            raise ConnectionResetError("scripted close (C4)")
        if response is not None:
            payload = json.dumps(response, ensure_ascii=False).encode(
                "utf-8") + b"\n"
            conn.sendall(payload)


# --- handlers ----------------------------------------------------------------

def arrangement_handler(arrangement):
    """Serve pane.list / pane.get / agent.get / pane.read / ping from a
    static arrangement {panes: [...], reads: {...}}; unknown pane ids get
    the structured pane_not_found error, agent.get without an agent gets
    agent_not_found.  pane.read revision is served as 0 while pane_info
    revision varies — the §3.4 trap."""
    panes_by_id = {pane["pane_id"]: pane for pane in arrangement["panes"]}
    reads = arrangement.get("reads", {})

    def handler(request):
        method = request.get("method")
        params = request.get("params") or {}
        req_id = request.get("id")
        if method == "ping":
            return {"id": req_id, "result": {
                "type": "pong", "version": "0.8.2", "protocol": 20,
                "capabilities": {"live_handoff": True,
                                 "detached_server_daemon": True}}}, False
        if method == "pane.list":
            return {"id": req_id, "result": {
                "type": "pane_list", "panes": arrangement["panes"]}}, False
        if method == "pane.get":
            pane = panes_by_id.get(params.get("pane_id"))
            if pane is None:
                return {"id": req_id, "error": {
                    "code": "pane_not_found",
                    "message": "pane %s not found" % params.get("pane_id")}}, False
            return {"id": req_id, "result": {
                "type": "pane_info", "pane": pane}}, False
        if method == "agent.get":
            pane = panes_by_id.get(params.get("target"))
            if pane is None or not pane.get("agent"):
                return {"id": req_id, "error": {
                    "code": "agent_not_found",
                    "message": "agent target %s not found"
                    % params.get("target")}}, False
            agent = dict(pane)
            agent.update({
                "name": pane["agent"], "interactive_ready": True,
                "launch_pending": False, "screen_detection_skipped": False,
                "state_change_seq": 0})
            return {"id": req_id, "result": {
                "type": "agent_info", "agent": agent}}, False
        if method == "pane.read":
            pane = panes_by_id.get(params.get("pane_id"))
            if pane is None:
                return {"id": req_id, "error": {
                    "code": "pane_not_found",
                    "message": "pane %s not found" % params.get("pane_id")}}, False
            read = {
                "pane_id": pane["pane_id"],
                "workspace_id": pane["workspace_id"],
                "tab_id": pane["tab_id"],
                "source": params.get("source", "visible"),
                "format": params.get("format", "text"),
                "text": reads.get(pane["pane_id"], ""),
                "truncated": False,
                "revision": 0,
            }
            return {"id": req_id, "result": {
                "type": "pane_read", "read": read}}, False
        return {"id": req_id, "error": {
            "code": "method_not_found",
            "message": "unknown method %s" % method}}, False

    return handler


def cycle_handler(fixture):
    """Serve the §6.2 human-driven cycle: each pane.list advances to the
    next transcript tick; the other requests resolve against the tick
    currently being observed."""
    ticks = fixture["ticks"]
    state = {"index": 0, "current": 0}

    def handler(request):
        method = request.get("method")
        req_id = request.get("id")
        if method == "pane.list":
            state["current"] = state["index"]
            state["index"] = min(state["index"] + 1, len(ticks) - 1)
            idx = state["current"]
            return {"id": req_id, "result": {
                "type": "pane_list", "panes": ticks[idx]["panes"]}}, False
        idx = state["current"]
        return arrangement_handler(ticks[idx])(request)

    return handler


def scripted_handler(script, arrangements, default, mismatches):
    """Replay a positional script across connections: each step is consumed
    per request; steps may answer from an arrangement, answer a structured
    error, or close the connection without answering (C4)."""
    position = {"index": 0}

    def handler(request):
        index = position["index"]
        position["index"] += 1
        method = request.get("method")
        if index < len(script):
            step = script[index]
            if step.get("expect") != method:
                mismatches.append(
                    ("step %d expected %r, got %r"
                     % (index, step.get("expect"), method)))
        else:
            step = None
        if step is None:
            return arrangement_handler(arrangements[default])(request)
        req_id = request.get("id")
        if step.get("close"):
            return None, True
        if "error" in step:
            return {"id": req_id, "error": step["error"]}, False
        result_from = step.get("result_from")
        if result_from is not None:
            return arrangement_handler(arrangements[result_from["arr"]])(request)
        return {"id": req_id, "result": step.get("result", {})}, False

    return handler


# --- ledger helpers (scratch ledgers only) -----------------------------------

def human_record(fixture_key):
    fixture = load_fixture(HUMAN_FIXTURE)[fixture_key]
    # The fixture discipline is read here, not copied: every simulated
    # human record keeps attestation_ref null (K4), and the artifact
    # only ever assigns the literal None.
    assert fixture["attestation_ref"] is None, fixture_key
    return make_record(
        address=fixture["address"], gate=fixture["gate"],
        state=fixture["state"], mark=fixture["mark"],
        payload_ref=fixture["payload_ref"], axis=fixture["axis"],
        axis_verdict=fixture["axis_verdict"],
        corruption=fixture["corruption"], tentative=fixture["tentative"],
        turn_key=None, block_version=fixture["block_version"],
        attestation_ref=None,
        attempt=fixture["turn_key_from"]["attempt"])


def plant_ledger(ledger_path):
    """Simulate the human's plant (gate x, address '', attested) in a
    scratch ledger."""
    with LedgerWriter(ledger_path) as writer:
        writer.append(human_record("plant"))


def append_human(fixture_key, ledger_path):
    """Simulate a human attestation record in a scratch ledger."""
    with LedgerWriter(ledger_path) as writer:
        return writer.append(human_record(fixture_key))


def idle_arrangement():
    """The blocked fixture with Q's agent_status set to the live normal
    'unknown' — nothing blocks, nothing changes across ticks."""
    fixture = load_fixture(BLOCKED_FIXTURE)
    arrangement = {
        "panes": [dict(pane) for pane in fixture["panes"]],
        "reads": dict(fixture["reads"]),
    }
    for pane in arrangement["panes"]:
        if pane["pane_id"] == "w8:p5":
            pane["agent_status"] = "unknown"
    return arrangement


def hold_records(ledger_path, address, gate):
    loaded = LedgerLoader(ledger_path).load(write_index=False)
    return [record for record in loaded.records
            if record["state"] == "held-pending"
            and record["address"] == address and record["gate"] == gate]


def verify_halts(ledger_path):
    """Quantity: chain verification halts (0 == the chain verifies)."""
    try:
        LedgerVerifier(ledger_path).verify()
        return 0
    except Exception:
        return 1


# ---------------------------------------------------------------------------
# The tests.  Each names the criterion ID it exercises and the quantity it
# measures (first docstring line).
# ---------------------------------------------------------------------------

class B1Selftest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmpdir = self._tmp.name
        self.ledger_path = os.path.join(self.tmpdir, "state", "gates.jsonl")
        self.server = FakeHerdrServer(self.tmpdir)

    def tearDown(self):
        self.server.halt()
        self._tmp.cleanup()

    # -- K1: the adapter ------------------------------------------------------

    def test_K1_envelope_and_tagged_union_unwrapping(self):
        """K1 — quantity measured: request envelope field count (3: id, method, params), PaneReadResult field count (8), and the unwrapped payload of ping / pane.get / pane.read / agent.get (each unwrapped from its method-specific key, not the envelope)."""
        self.server.start(arrangement_handler(load_fixture(BLOCKED_FIXTURE)))
        inst = Instrument(socket_path=self.server.path)
        pong = inst.ping()
        self.assertEqual(pong["type"], "pong")
        pane = inst.pane_info("w8:p3")
        self.assertEqual(pane["label"], "G")
        self.assertEqual(pane["agent_status"], "idle")
        read = inst.read_pane(pane_id="w8:p3")
        self.assertEqual(sorted(read.keys()), sorted([
            "pane_id", "workspace_id", "tab_id", "source", "format",
            "text", "truncated", "revision"]))
        agent = inst.agent_info("w8:p3")
        self.assertEqual(agent["agent_status"], "idle")
        self.assertEqual(agent["name"], "pi")
        for request in self.server.requests:
            self.assertEqual(sorted(request.keys()),
                             ["id", "method", "params"])
            self.assertIsInstance(request["id"], str)
            self.assertTrue(request["id"])  # a non-empty string id
            self.assertIsInstance(request["method"], str)
            self.assertIsInstance(request["params"], dict)
        inst.close()

    def test_K1_fake_server_refuses_non_string_id(self):
        """K1 — quantity measured: adapter request ids that are JSON strings (1, non-empty — the monotonic counter stringified) and echoed verbatim by the fake server (0 mismatches); the fake server's reply to a hand-sent integer id (1 refusal carrying id '' and code 'invalid_request')."""
        self.server.start(arrangement_handler(load_fixture(BLOCKED_FIXTURE)))
        inst = Instrument(socket_path=self.server.path)
        pong = inst.ping()
        self.assertEqual(pong["type"], "pong")
        for request in self.server.requests:
            self.assertIsInstance(request["id"], str)
            self.assertTrue(request["id"])
        inst.close()
        raw = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        raw.settimeout(5.0)
        raw.connect(self.server.path)
        raw.sendall(json.dumps({"id": 7, "method": "ping",
                                "params": {}}).encode("utf-8") + b"\n")
        response = json.loads(raw.recv(65536).decode("utf-8"))
        raw.close()
        self.assertEqual(response["id"], "")
        self.assertEqual(response["error"]["code"], "invalid_request")
        self.assertIn("message", response["error"])

    def test_K1_structured_errors_map_to_typed_exceptions(self):
        """K1 — quantity measured: structured error code → exception mappings (3: pane_not_found → PaneNotFoundError, agent_not_found → AgentNotFoundError, unknown code → HerdrRemoteError), each carrying its code and message; socket timeout → SocketTransportError (1)."""
        self.server.start(arrangement_handler(load_fixture(BLOCKED_FIXTURE)))
        inst = Instrument(socket_path=self.server.path)
        with self.assertRaises(PaneNotFoundError) as ctx:
            inst.pane_info("w8:nope")
        self.assertEqual(ctx.exception.code, "pane_not_found")
        self.assertIn("not found", ctx.exception.message)
        with self.assertRaises(AgentNotFoundError) as ctx:
            inst.agent_info("w8:p5")
        self.assertEqual(ctx.exception.code, "agent_not_found")
        inst.close()

        def weird_handler(request):
            return {"id": request.get("id"),
                    "error": {"code": "weird_code",
                              "message": "weird thing happened"}}, False

        server2 = FakeHerdrServer(self.tmpdir, name="herdr-test-2.sock")
        server2.start(weird_handler)
        try:
            inst2 = Instrument(socket_path=server2.path)
            with self.assertRaises(HerdrRemoteError) as ctx:
                inst2.call("pane.list", {})
            self.assertEqual(ctx.exception.code, "weird_code")
            self.assertEqual(ctx.exception.message, "weird thing happened")
            inst2.close()
        finally:
            server2.halt()

        def slow_handler(request):
            time.sleep(1.0)
            return {"id": request.get("id"), "result": {"type": "pong"}}, False

        server3 = FakeHerdrServer(self.tmpdir, name="herdr-test-3.sock")
        server3.start(slow_handler)
        try:
            inst3 = Instrument(socket_path=server3.path, timeout_s=0.3)
            with self.assertRaises(SocketTransportError):
                inst3.call("ping", {})
            inst3.close()
        finally:
            server3.halt()

    def test_K1_desks_resolved_by_label_on_every_use(self):
        """K1 — quantity measured: desks resolved by pane label (5), null-label panes indexed (0), stray-workspace desk panes adopted (0 — the workspace is derived from the labels resolved), and desks followed across a pane-id re-mint (5 desk keys keep the same meaning under changed ids)."""
        self.server.start(arrangement_handler(load_fixture(BLOCKED_FIXTURE)))
        inst = Instrument(socket_path=self.server.path)
        desks = inst.desks()
        self.assertEqual(desks, {
            "G": "w8:p3", "P": "w8:p6", "Q": "w8:p5",
            "S": "w8:p2", "V": "w8:p4"})
        self.assertEqual(len(desks), 5)
        inst.close()

        restart = load_fixture(RESTART_FIXTURE)
        arrangement_a = restart["arrangements"]["a"]
        server2 = FakeHerdrServer(self.tmpdir, name="herdr-test-4.sock")
        server2.start(arrangement_handler(arrangement_a))
        try:
            inst2 = Instrument(socket_path=server2.path)
            desks_a = inst2.desks()
            self.assertEqual(desks_a, {
                "G": "w2:p3", "P": "w2:p6", "Q": "w2:p5",
                "S": "w2:p2", "V": "w2:p4"})
            inst2.close()
        finally:
            server2.halt()

        remint_script = [
            {"expect": "pane.list", "result_from": {"arr": "a"}},
            {"expect": "pane.list", "close": True},
            {"expect": "pane.list", "result_from": {"arr": "b"}},
        ]
        mismatches = []
        server3 = FakeHerdrServer(self.tmpdir, name="herdr-test-5.sock")
        server3.start(scripted_handler(
            remint_script,
            {"a": restart["arrangements"]["a"],
             "b": restart["arrangements"]["b"]},
            "b", mismatches))
        try:
            inst3 = Instrument(socket_path=server3.path)
            before = inst3.desks()
            after = inst3.desks()
            self.assertEqual(set(before), set(after))
            self.assertNotEqual(before["G"], after["G"])
            self.assertEqual(after["G"], "w8:p3")
            self.assertEqual(inst3.reconnects, 1)
            self.assertEqual(mismatches, [])
            inst3.close()
        finally:
            server3.halt()

    def test_K1_desk_states_and_read_pane_desk_resolution(self):
        """K1 — quantity measured: desk_states() entries carrying agent_status (5), desk statuses sourced from agent.get for the pane with an agent (1 — the §4.4 signal path), and read_pane(desk=) resolved by label on the call (1)."""
        self.server.start(arrangement_handler(load_fixture(BLOCKED_FIXTURE)))
        inst = Instrument(socket_path=self.server.path)
        states = inst.desk_states()
        self.assertEqual(set(states), {"S", "G", "Q", "P", "V"})
        self.assertEqual(states["G"]["agent_status"], "idle")
        self.assertEqual(states["G"]["agent_status_source"], "agent.get")
        self.assertEqual(states["Q"]["agent_status"], "blocked")
        self.assertEqual(states["Q"]["agent_status_source"], "pane.get")
        self.assertEqual(states["P"]["agent_status"], "unknown")
        read = inst.read_pane(desk="Q")
        self.assertEqual(read["pane_id"], "w8:p5")
        self.assertEqual(read["text"],
                         "deploy@srv1707555: ~/the-cell$ \n")
        self.assertIs(read["truncated"], False)
        inst.close()

    def test_K1_relabelled_pane_cannot_change_record_meaning(self):
        """K1 — quantity measured: the hold record's address and gate written under relabelled panes (2 fields — still 'G' and 'y'), the relabelled centre resolved to desk S (1), and the stray workspace ignored (0 adopted)."""
        self.server.start(arrangement_handler(load_fixture(RELABEL_FIXTURE)))
        relabels = {"THE QUESTION": "S", "g-desk": "G",
                    "Q": "Q", "P": "P", "V": "V"}
        inst = Instrument(socket_path=self.server.path, desk_labels=relabels)
        desks = inst.desks()
        self.assertEqual(desks["S"], "w8:p1")
        self.assertEqual(desks["G"], "w8:p3")
        inst.close()
        walker = Walker(socket_path=self.server.path,
                        ledger_path=self.ledger_path,
                        desk_labels=relabels)
        frame = walker.tick()
        walker.close()
        holds = hold_records(self.ledger_path, "G", "y")
        self.assertEqual(len(holds), 1)
        self.assertEqual(holds[0]["address"], "G")
        self.assertEqual(holds[0]["gate"], "y")
        blocked = [df for df in frame["desks"] if df["desk"] == "G"]
        self.assertEqual(len(blocked), 1)

    # -- C3: zero pane writes -------------------------------------------------

    def test_C3_disallowed_method_raises_before_any_byte_reaches_the_socket(self):
        """C3 — quantity measured: bytes received (0) and connections accepted (0) by the fake server after a non-allowlisted call on a fresh instrument; and the method log after a non-allowlisted call on a warm, already-connected instrument (1 — only the allowlisted read that preceded it)."""
        self.server.start(arrangement_handler(load_fixture(BLOCKED_FIXTURE)))
        fresh = Instrument(socket_path=self.server.path)
        with self.assertRaises(MethodNotAllowedError):
            fresh.call("pane.poke", {})
        self.assertEqual(self.server.connections, 0)
        self.assertEqual(self.server.bytes_in, 0)
        fresh.close()
        warm = Instrument(socket_path=self.server.path)
        warm.call("pane.list", {})
        with self.assertRaises(MethodNotAllowedError):
            warm.call("agent.teleport", {})
        self.assertEqual(self.server.methods, ["pane.list"])
        warm.close()

    def test_C3_runtime_method_log_contains_only_allowlisted_reads(self):
        """C3 — quantity measured: methods sent to the socket during the full 6-tick human cycle that are not in READ_ONLY_METHODS (0), the distinct method names actually sent ({pane.list, pane.get, agent.get, pane.read}), and request envelopes missing the three required fields (0)."""
        fixture = load_fixture(CYCLE_FIXTURE)
        self.server.start(cycle_handler(fixture))
        plant_ledger(self.ledger_path)
        walker = Walker(socket_path=self.server.path,
                        ledger_path=self.ledger_path)
        for _ in range(4):
            walker.tick()
        append_human("attest_g", self.ledger_path)
        walker.tick()
        walker.tick()
        walker.close()
        self.assertEqual(
            len([m for m in self.server.methods
                 if m not in READ_ONLY_METHODS]), 0)
        self.assertEqual(set(self.server.methods),
                         {"pane.list", "pane.get", "agent.get",
                          "pane.read"})
        for request in self.server.requests:
            self.assertEqual(sorted(request.keys()),
                             ["id", "method", "params"])

    def test_C3_static_single_chokepoint_and_frozen_allowlist(self):
        """C3 — quantity measured (static AST read of the artifact): socket send call sites in instrument.py (1, inside call()), send/connect call sites in walker.py and dialects.py (0 each), and READ_ONLY_METHODS equality with the 18 §3.1 read methods (1 frozenset)."""
        src = open(os.path.join(HERE, "instrument.py"),
                   encoding="utf-8").read()
        tree = ast.parse(src)
        send_lines = []
        gate_line = None
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr in ("send", "sendall")):
                send_lines.append(node.lineno)
            if (isinstance(node, ast.Compare)
                    and isinstance(node.left, ast.Name)
                    and node.left.id == "method"
                    and any(isinstance(op, ast.NotIn) for op in node.ops)
                    and any(isinstance(c, ast.Name)
                            and c.id == "READ_ONLY_METHODS"
                            for c in node.comparators)):
                gate_line = node.lineno
        self.assertEqual(len(send_lines), 1)
        call_range = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "call":
                call_range = (node.lineno, node.end_lineno)
        self.assertIsNotNone(call_range)
        self.assertTrue(call_range[0] <= send_lines[0] <= call_range[1])
        self.assertIsNotNone(gate_line)
        self.assertLess(gate_line, send_lines[0])
        expected = frozenset((
            "ping",
            "pane.list", "pane.get", "pane.read", "pane.process_info",
            "pane.current", "pane.layout", "pane.edges", "pane.neighbor",
            "agent.list", "agent.get", "agent.read",
            "tab.list", "workspace.list", "session.snapshot",
            "events.subscribe", "events.wait", "pane.wait_for_output"))
        self.assertEqual(READ_ONLY_METHODS, expected)
        self.assertIsInstance(READ_ONLY_METHODS, frozenset)
        for module_name in ("walker.py", "dialects.py"):
            module_src = open(os.path.join(HERE, module_name),
                              encoding="utf-8").read()
            module_tree = ast.parse(module_src)
            sites = []
            for node in ast.walk(module_tree):
                if (isinstance(node, ast.Call)
                        and isinstance(node.func, ast.Attribute)
                        and node.func.attr in ("send", "sendall", "connect")):
                    sites.append(node.lineno)
            self.assertEqual(sites, [], "%s send/connect sites" % module_name)
        dialects_src = open(os.path.join(HERE, "dialects.py"),
                            encoding="utf-8").read()
        dialects_tree = ast.parse(dialects_src)
        modules = set()
        for node in ast.walk(dialects_tree):
            if isinstance(node, ast.Import):
                modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                modules.add(node.module)
        self.assertFalse(modules & {"os", "sys", "io", "socket", "json",
                                    "time", "hashlib", "subprocess",
                                    "pathlib"})

    # -- C4: reconnect and re-resolve -----------------------------------------

    def test_C4_reconnect_and_reresolve_reminted_ids(self):
        """C4 — quantity measured: reconnect events during the mid-run close (1), desks followed by label after the re-mint (5, all w8:* ids in the same tick), script expectation mismatches (0), and desks followed identically on the next tick (5)."""
        restart = load_fixture(RESTART_FIXTURE)
        mismatches = []
        self.server.start(scripted_handler(
            restart["script"],
            {"a": restart["arrangements"]["a"],
             "b": restart["arrangements"]["b"]},
            restart["default"], mismatches))
        plant_ledger(self.ledger_path)
        walker = Walker(socket_path=self.server.path,
                        ledger_path=self.ledger_path)
        frame = walker.tick()
        self.assertTrue(frame["reresolved_this_tick"])
        pane_ids = {df["desk"]: df["pane_id"] for df in frame["desks"]}
        self.assertEqual(pane_ids, {
            "G": "w8:p3", "P": "w8:p6", "Q": "w8:p5",
            "S": "w8:p2", "V": "w8:p4"})
        self.assertEqual(walker.instrument.reconnects, 1)
        self.assertEqual(mismatches, [])
        frame2 = walker.tick()
        self.assertFalse(frame2["reresolved_this_tick"])
        pane_ids2 = {df["desk"]: df["pane_id"] for df in frame2["desks"]}
        self.assertEqual(pane_ids2, pane_ids)
        self.assertEqual(
            len([m for m in self.server.methods
                 if m not in READ_ONLY_METHODS]), 0)
        walker.close()

    # -- C2: exactly one held-pending record per blocked episode ----------------

    def test_C2_exactly_one_record_per_blocked_episode(self):
        """C2 — quantity measured: held-pending records for (Q, z) after ten consecutive blocked polls (1), after a human attestation for (Q, z) plus one more blocked poll (2 — a new episode, not a duplicate), after another blocked poll (2), and chain verification halts (0)."""
        self.server.start(arrangement_handler(load_fixture(BLOCKED_FIXTURE)))
        plant_ledger(self.ledger_path)
        walker = Walker(socket_path=self.server.path,
                        ledger_path=self.ledger_path)
        for _ in range(10):
            walker.tick()
        self.assertEqual(len(hold_records(self.ledger_path, "Q", "z")), 1)
        self.assertEqual(verify_halts(self.ledger_path), 0)
        append_human("attest_q", self.ledger_path)
        walker.tick()
        self.assertEqual(len(hold_records(self.ledger_path, "Q", "z")), 2)
        self.assertEqual(verify_halts(self.ledger_path), 0)
        walker.tick()
        self.assertEqual(len(hold_records(self.ledger_path, "Q", "z")), 2)
        holds = hold_records(self.ledger_path, "Q", "z")
        for hold in holds:
            self.assertEqual(hold["state"], "held-pending")
            self.assertEqual(hold["payload_ref"], "herdr:agent_status")
            self.assertIsNone(hold["attestation_ref"])
            self.assertIsNone(hold["axis_verdict"])
            self.assertEqual(hold["block_version"], "")
            self.assertIs(hold["tentative"], True)
            self.assertEqual(hold["mark"], "mechanical")
        self.assertEqual(holds[0]["turn_key"],
                         hashlib.sha256(b"Qz1").hexdigest())
        self.assertEqual(holds[1]["turn_key"],
                         hashlib.sha256(b"Qz3").hexdigest())
        walker.close()

    def test_C2_two_dialects_one_hold_and_moving_dominance(self):
        """C2 — quantity measured: held-pending records for Q when both the herdr dialect (blocked) and the cell MOVING axis fire in the same tick (1 — one hold, not two), dialect identities carried in payload_ref (2 references), axis_verdict MOVING (1), and records appended on the following tick (0 — the episode stays open)."""
        self.server.start(arrangement_handler(load_fixture(BLOCKED_FIXTURE)))
        plant_ledger(self.ledger_path)
        walker = Walker(
            socket_path=self.server.path, ledger_path=self.ledger_path,
            axis_provider=lambda: {"axis_verdict": "MOVING"})
        walker.tick()
        q_holds = hold_records(self.ledger_path, "Q", "z")
        self.assertEqual(len(q_holds), 1)
        self.assertIn("cell:moving", q_holds[0]["payload_ref"])
        self.assertIn("herdr:agent_status", q_holds[0]["payload_ref"])
        self.assertEqual(q_holds[0]["axis_verdict"], "MOVING")
        before = LedgerLoader(self.ledger_path).load(
            write_index=False).count
        walker.tick()
        after = LedgerLoader(self.ledger_path).load(
            write_index=False).count
        self.assertEqual(after, before)
        walker.close()

    def test_C2_cold_restart_mid_episode_writes_no_second_record(self):
        """C2 — quantity measured: held-pending records for (Q, z) after the SECOND process (a fresh subprocess, re-armed from disk alone) ticks once on the same ledger (1), and the two subprocess exit codes (0, 0)."""
        self.server.start(arrangement_handler(load_fixture(BLOCKED_FIXTURE)))
        plant_ledger(self.ledger_path)
        child = (
            "import sys\n"
            "from walker import Walker\n"
            "walker = Walker(socket_path=sys.argv[1], "
            "ledger_path=sys.argv[2])\n"
            "frame = walker.tick()\n"
            "print(frame['tick'])\n"
            "sys.exit(0 if frame['tick'] == 1 else 2)\n")
        env = dict(os.environ)
        env["PYTHONPATH"] = HERE + os.pathsep + LEDGER_DIR
        env["FRACTAL_LEDGER_DIR"] = LEDGER_DIR
        first = subprocess.run(
            [sys.executable, "-c", child, self.server.path,
             self.ledger_path],
            env=env, capture_output=True, text=True, cwd=HERE)
        second = subprocess.run(
            [sys.executable, "-c", child, self.server.path,
             self.ledger_path],
            env=env, capture_output=True, text=True, cwd=HERE)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(first.stdout.strip(), "1")
        self.assertEqual(second.stdout.strip(), "1")
        self.assertEqual(len(hold_records(self.ledger_path, "Q", "z")), 1)
        self.assertEqual(verify_halts(self.ledger_path), 0)

    # -- C1: the cycle reconstructed from polling alone ------------------------

    def test_C1_cycle_reconstructed_from_polls_alone(self):
        """C1 — quantity measured: the per-desk state sequences reconstructed from polling alone (G: working→idle with the output change flagged at tick 2; Q: unknown→blocked at tick 3 and blocked→unknown at tick 6; P: unknown on all 6 ticks with 0 transitions), the phase gate read from tail_record() (y, attested, at address G), and the holds appended (1, desk Q)."""
        fixture = load_fixture(CYCLE_FIXTURE)
        self.server.start(cycle_handler(fixture))
        plant_ledger(self.ledger_path)
        walker = Walker(socket_path=self.server.path,
                        ledger_path=self.ledger_path)
        for _ in range(4):
            walker.tick()
        append_human("attest_g", self.ledger_path)
        walker.tick()
        walker.tick()
        walker.close()
        recon = walker.reconstruct()
        self.assertEqual(recon["ticks"], 6)
        g_sequence = recon["desk_sequences"]["G"]
        self.assertEqual(g_sequence, [
            {"tick": 1, "status": "working", "output_changed": None},
            {"tick": 2, "status": "idle", "output_changed": True}])
        q_sequence = recon["desk_sequences"]["Q"]
        self.assertEqual(q_sequence, [
            {"tick": 1, "status": "unknown", "output_changed": None},
            {"tick": 3, "status": "blocked", "output_changed": False},
            {"tick": 6, "status": "unknown", "output_changed": False}])
        p_sequence = recon["desk_sequences"]["P"]
        self.assertEqual(len(p_sequence), 1)
        self.assertEqual(p_sequence[0]["status"], "unknown")
        self.assertEqual(p_sequence[0]["tick"], 1)
        q_transitions = [t for t in recon["transitions"]
                         if t["desk"] == "Q"]
        self.assertEqual(q_transitions, [
            {"tick": 3, "desk": "Q", "from": "unknown", "to": "blocked"},
            {"tick": 6, "desk": "Q", "from": "blocked", "to": "unknown"}])
        g_transitions = [t for t in recon["transitions"]
                         if t["desk"] == "G"]
        self.assertEqual(g_transitions, [
            {"tick": 2, "desk": "G", "from": "working", "to": "idle"}])
        self.assertEqual(len(recon["holds"]), 1)
        self.assertEqual(recon["holds"][0]["desk"], "Q")
        self.assertEqual(recon["holds"][0]["gate"], "z")
        self.assertEqual(recon["holds"][0]["tick"], 3)
        self.assertEqual(recon["gate_now"], "y")
        self.assertEqual(recon["phase_now"]["state"], "attested")
        self.assertEqual(recon["phase_now"]["address"], "G")
        self.assertEqual(recon["phase_now"]["source"], "tail_record")
        self.assertEqual(len(hold_records(self.ledger_path, "Q", "z")), 1)
        self.assertEqual(verify_halts(self.ledger_path), 0)
        tick2_g = [df for df in walker._observations[1]["desks"]
                   if df["desk"] == "G"][0]
        expected_text = fixture["ticks"][1]["reads"]["w8:p3"]
        self.assertEqual(tick2_g["output"]["text"], expected_text)
        self.assertIn(NEEDLE, expected_text)
        self.assertEqual(self.server.methods[0], "pane.list")

    # -- K2: the poll loop and its schedule ------------------------------------

    def test_K2_tick_is_callable_with_no_sleeping(self):
        """K2 — quantity measured: time.sleep invocations during one tick() (0 — tick is one pass, callable with no sleeping; the schedule lives in run())."""
        self.server.start(arrangement_handler(idle_arrangement()))
        walker = Walker(socket_path=self.server.path,
                        ledger_path=self.ledger_path)
        real_sleep = time.sleep
        calls = []

        def bomb(seconds):
            calls.append(seconds)
            raise AssertionError("tick() slept")

        walker_module.time.sleep = bomb
        try:
            frame = walker.tick()
        finally:
            walker_module.time.sleep = real_sleep
            walker.close()
        self.assertEqual(calls, [])
        self.assertEqual(frame["tick"], 1)

    def test_K2_backoff_schedule_is_pure_and_run_sleeps_per_schedule(self):
        """K2 — quantity measured: the pure schedule's delay sequence (3, 6, 12, 24, 30, 30 — doubling capped at 30, reset to 3 on change) and the exact sleep arguments of run() over 4 unchanged ticks (3.0, 6.0, 12.0)."""
        self.assertEqual(next_delay(True, 30.0), 3.0)
        self.assertEqual(next_delay(False, 3.0), 6.0)
        self.assertEqual(next_delay(False, 6.0), 12.0)
        self.assertEqual(next_delay(False, 12.0), 24.0)
        self.assertEqual(next_delay(False, 24.0), 30.0)
        self.assertEqual(next_delay(False, 30.0), 30.0)
        self.server.start(arrangement_handler(idle_arrangement()))
        walker = Walker(socket_path=self.server.path,
                        ledger_path=self.ledger_path)
        sleeps = []
        walker.run(max_ticks=4, sleep_fn=sleeps.append)
        walker.close()
        self.assertEqual(sleeps, [3.0, 6.0, 12.0])

    def test_K2_tick_poll_pass_timing(self):
        """K2 — timed operation: one full tick() poll pass over five desks (pane.list + 5× pane.get + 1× agent.get + 5× pane.read) against the in-process fake server.  Quantity measured: wall-clock seconds of the timed operation, asserted < 2.0."""
        self.server.start(arrangement_handler(idle_arrangement()))
        walker = Walker(socket_path=self.server.path,
                        ledger_path=self.ledger_path)
        started = time.monotonic()
        walker.tick()
        elapsed = time.monotonic() - started
        walker.close()
        self.assertLess(elapsed, 2.0)

    # -- K3: the three-dialect mapper ------------------------------------------

    def test_K3_three_dialects_map_blocked_from_fixtures(self):
        """K3 — quantity measured: fixture payloads of each §4.4 dialect mapped wrong (0): herdr/pi/dsh/cell blocked payloads → BLOCKED, every non-blocked payload → no verdict, every junk payload → no verdict without raising, and unknown dialect names → no verdict without raising (3)."""
        fx = load_fixture(DIALECT_FIXTURE)
        mismatches = 0
        for dialect in ("herdr", "pi", "dsh", "cell"):
            for payload in fx[dialect]["blocked"]:
                if not map_signal(dialect, payload).is_blocked:
                    mismatches += 1
            for payload in fx[dialect]["not_blocked"]:
                if map_signal(dialect, payload).is_blocked:
                    mismatches += 1
        for payload in fx["junk"]:
            for dialect in ("herdr", "pi", "dsh", "cell"):
                verdict = map_signal(dialect, payload)
                if verdict.name not in ("blocked", "no_verdict"):
                    mismatches += 1
        for dialect in ("esperanto", None, 42, ""):
            verdict = map_signal(dialect, {})
            if verdict.name != "no_verdict":
                mismatches += 1
        self.assertEqual(mismatches, 0)
        self.assertEqual(BLOCKED.name, "blocked")
        self.assertFalse(hasattr(dialects, "ATTESTED"))

    def test_K3_dsh_held_predicate_requires_a_usable_sid(self):
        """K3 — quantity measured: falsy dsh held payloads read as a hold (0 — False, "", 0, and whitespace-only are absences, never session ids), and a usable held SID still mapping to BLOCKED (1, with the dsh:held signal)."""
        for falsy in (False, "", 0, "   ", "\t\n "):
            verdict = map_signal("dsh", {"held": falsy})
            self.assertFalse(verdict.is_blocked)
            self.assertEqual(verdict.signals, ())
        usable = map_signal("dsh", {"held": "sid-42"})
        self.assertTrue(usable.is_blocked)
        self.assertEqual(usable.signals, ("dsh:held",))

    def test_K3_moving_axis_verdict_dominates(self):
        """K3 — quantity measured: cell MOVING overriding a non-blocked herdr signal (1 → BLOCKED), a runtime BLOCKED surviving a cell STASIS (1 → still BLOCKED), and a cell STASIS over an unknown herdr status yielding no verdict (1)."""
        moving_over_idle = dominant(
            map_signal("cell", {"axis_verdict": "MOVING"}),
            map_signal("herdr", {"agent_status": "idle"}))
        self.assertTrue(moving_over_idle.is_blocked)
        blocked_survives_stasis = dominant(
            map_signal("cell", {"axis_verdict": "STASIS"}),
            map_signal("herdr", {"agent_status": "blocked"}))
        self.assertTrue(blocked_survives_stasis.is_blocked)
        stasis_over_unknown = dominant(
            map_signal("cell", {"axis_verdict": "STASIS"}),
            map_signal("herdr", {"agent_status": "unknown"}))
        self.assertFalse(stasis_over_unknown.is_blocked)
        self.assertEqual(stasis_over_unknown.name, "no_verdict")

    # -- K4: fuzz never auto-attests; attestation_ref stays null -----------------

    def test_K4_fuzz_never_yields_attested(self):
        """K4 — quantity measured: fuzzed verdicts outside {blocked, no_verdict} across 3000 random payloads × 3 dialects (0) and across cell + unknown dialects (0); a mapper 'attested' concept (0 — it does not exist)."""
        rng = random.Random(0xB1)
        keys_of_interest = [
            "agent_status", "terminate", "ctx", "ui", "confirm", "state",
            "gate_state", "status", "approval", "held", "axis_verdict",
            "verdict", "moving", "pane_id", "workspace_id", "label",
        ]
        values_of_interest = [
            "blocked", "idle", "working", "done", "unknown", "held-pending",
            "MOVING", "STASIS", "recast", "failed", "granted", None,
        ]
        alphabet = string.ascii_letters + string.digits

        def random_string():
            return "".join(rng.choice(alphabet)
                           for _ in range(rng.randrange(8)))

        def random_payload(depth=0):
            if depth > 3 or rng.random() < 0.3:
                return rng.choice(values_of_interest + [
                    True, False, rng.randint(-9, 9), random_string()])
            kind = rng.randrange(3)
            if kind == 0:
                return {rng.choice(keys_of_interest + [random_string()]):
                        random_payload(depth + 1)
                        for _ in range(rng.randrange(6))}
            if kind == 1:
                return [random_payload(depth + 1)
                        for _ in range(rng.randrange(6))]
            return random_string()

        payloads = [random_payload() for _ in range(1000)]
        violations = 0
        trials = 0
        for dialect in ("herdr", "pi", "dsh"):
            for payload in payloads:
                trials += 1
                verdict = map_signal(dialect, payload)
                if verdict.name not in ("blocked", "no_verdict"):
                    violations += 1
        for dialect in ("cell", "esperanto", None, 42):
            for payload in payloads:
                trials += 1
                verdict = map_signal(dialect, payload)
                if verdict.name not in ("blocked", "no_verdict"):
                    violations += 1
        self.assertEqual(violations, 0)
        self.assertGreaterEqual(trials, 3000)

    def test_K4_static_attestation_ref_never_nonnull(self):
        """K4 — quantity measured (static AST + fixture read): attestation_ref assignments in the authored sources with a non-null value (0) and attestation_ref values in the fixtures that are not null (0)."""
        violations = 0
        for module_name in ("instrument.py", "dialects.py", "walker.py",
                            "selftest.py"):
            src = open(os.path.join(HERE, module_name),
                       encoding="utf-8").read()
            tree = ast.parse(src)
            for node in ast.walk(tree):
                if isinstance(node, ast.Dict):
                    for key, value in zip(node.keys, node.values):
                        if (isinstance(key, ast.Constant)
                                and key.value == "attestation_ref"
                                and not (isinstance(value, ast.Constant)
                                         and value.value is None)):
                            violations += 1
                if isinstance(node, ast.keyword) and node.arg == "attestation_ref":
                    if not (isinstance(node.value, ast.Constant)
                            and node.value.value is None):
                        violations += 1
        for fixture_name in sorted(os.listdir(FIXTURES)):
            if not fixture_name.endswith(".json"):
                continue
            fixture = load_fixture(fixture_name)
            stack = [fixture]
            while stack:
                item = stack.pop()
                if isinstance(item, dict):
                    if ("attestation_ref" in item
                            and item["attestation_ref"] is not None):
                        violations += 1
                    stack.extend(item.values())
                elif isinstance(item, list):
                    stack.extend(item)
        self.assertEqual(violations, 0)

    # -- encoding lens ---------------------------------------------------------

    def test_encoding_bytes_survive_every_string_field(self):
        """Encoding — quantity measured: byte differences (0) for the pane text carrying '∞0′ → ‖' round-tripped through the fake socket and the walker's observation; for the pane title 'π - the-cell' through pane.get; and for a ledger record's string fields (payload_ref, axis anchor) round-tripped through B0's writer and tail_record — with chain verification halts (0)."""
        fixture = load_fixture(BLOCKED_FIXTURE)
        self.server.start(arrangement_handler(fixture))
        inst = Instrument(socket_path=self.server.path)
        self.assertIn(NEEDLE, inst.read_pane(pane_id="w8:p3")["text"])
        self.assertEqual(inst.pane_info("w8:p3")["title"], "π - the-cell")
        inst.close()
        walker = Walker(socket_path=self.server.path,
                        ledger_path=self.ledger_path)
        frame = walker.tick()
        walker.close()
        expected_text = fixture["reads"]["w8:p3"]
        for desk_frame in frame["desks"]:
            if desk_frame["desk"] == "G":
                self.assertEqual(desk_frame["output"]["text"], expected_text)
        record = make_record(
            address="G", gate="y", state="held-pending",
            mark="mechanical", payload_ref="ref:" + NEEDLE,
            axis={"field": {"mode": "anchored",
                            "anchor": "ref:" + NEEDLE}, "delta": []},
            axis_verdict=None, corruption=None, tentative=True,
            turn_key=None, block_version="", attestation_ref=None,
            attempt="1")
        with LedgerWriter(self.ledger_path) as writer:
            writer.append(record)
        tail = tail_record(self.ledger_path)
        self.assertEqual(tail["payload_ref"], "ref:" + NEEDLE)
        self.assertEqual(tail["axis"]["field"]["anchor"], "ref:" + NEEDLE)
        self.assertEqual(verify_halts(self.ledger_path), 0)

    # -- absence is never validity (lens 3) -------------------------------------

    def test_absence_unknown_and_truncated_never_read_as_valid(self):
        """C2/K3 (lens 3) — quantity measured: BLOCKED verdicts produced by agent_status 'unknown' (0), by a missing agent_status (0), by a null result payload (0), and desk observations fabricated for a desk absent from the arrangement (0 — it is reported unresolved, never invented)."""
        unknown = map_signal("herdr", {"agent_status": "unknown"})
        self.assertFalse(unknown.is_blocked)
        missing = map_signal("herdr", {})
        self.assertFalse(missing.is_blocked)
        nul = map_signal("herdr", None)
        self.assertFalse(nul.is_blocked)
        fixture = load_fixture(BLOCKED_FIXTURE)
        arrangement = {"panes": [dict(p) for p in fixture["panes"]],
                       "reads": dict(fixture["reads"])}
        arrangement["panes"] = [p for p in arrangement["panes"]
                                if p["pane_id"] != "w8:p4"]
        self.server.start(arrangement_handler(arrangement))
        walker = Walker(socket_path=self.server.path,
                        ledger_path=self.ledger_path)
        frame = walker.tick()
        walker.close()
        observed = {df["desk"] for df in frame["desks"]}
        self.assertNotIn("V", observed)
        self.assertIn("V", frame["unresolved_desks"])


# ---------------------------------------------------------------------------

def main():
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(B1Selftest)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    print("\ncriterion summary — each test names the criterion ID it "
          "exercises and the quantity it measures:")
    for name in unittest.defaultTestLoader.getTestCaseNames(B1Selftest):
        doc = (getattr(B1Selftest, name).__doc__ or "").splitlines()[0]
        print("  %-52s %s" % (name, doc))
    sys.exit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
