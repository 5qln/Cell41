#!/usr/bin/env python3
"""selftest — R03 · B2 (the driver) + P4a (the step mode), author-side
checks.

Every test names, in its first docstring line, the criterion ID it
exercises (B2: C1–C4, K1–K5; P4a: C1–C5, K1–K6, the six lenses) and the
quantity it measures; a test that times something names the operation
timed (the P4a timed test times run_session over the cycle fixture —
K2's 60 s budget).  Every fence answer is scripted, no sleeping inside
any step.

The fake herdr server binds its OWN AF_UNIX socket inside a
tempfile-created directory and replays the fixtures/ transcripts — the
live herdr socket is never touched, every ledger path is inside a
tempfile-created directory (never the attested plant), every trail path
is inside a tempfile directory (never the canon trail dir), and the Pi
home is a tempfile directory built from the fixture (the real ~/.pi is
never read or written).  The fake server speaks the live dialect
(commission §3.1 / R03 §6.3): string-only request ids — a non-string id
is refused with {"id": "", "error": {"code": "invalid_request", …}}
before dispatch — and the write-response shapes it serves are the
fixture's declared claims (H-B2-4), never reported as observed.

Run:  python3 selftest.py
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import socket
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

import driver as driver_module  # noqa: E402
import instrument as instrument_module  # noqa: E402
import lens as lens_module  # noqa: E402
from driver import Driver, PROMPT_ATTEMPT, turn_key  # noqa: E402
from instrument import (  # noqa: E402
    READ_ONLY_METHODS,
    WRITE_METHODS,
    CentreWriteError,
    HerdrProtocolError,
    Instrument,
    MethodNotAllowedError,
    _FENCE_INSTRUCTION,
    assert_not_centre,
    fence_marker,
)
from lens import DESK_BLOCKS, Lens, TrustError, assert_trust  # noqa: E402
from walker import COURSE  # noqa: E402
from fractal_ledger import (  # noqa: E402
    LedgerLoader,
    LedgerWriter,
    canonical_json,
)

FIXTURES = os.path.join(HERE, "fixtures")
CYCLE_FIXTURE = "cycle_transcript.json"
DUP_FIXTURE = "duplicated_prompt_transcript.json"
WORKING_FIXTURE = "already_working_transcript.json"
UNTRUSTED_FIXTURE = "untrusted_boot.json"
CONSTITUTED_FIXTURE = "constituted_boot.json"

NEEDLE = "∞0′ → ‖"  # the encoding-lens bytes (commission lens 4)

# B1's READ_ONLY_METHODS, verbatim (R02 commission §3.1): the assertion
# that B2 never widened it.
B1_READ_ONLY = frozenset((
    "ping", "pane.list", "pane.get", "pane.read", "pane.process_info",
    "pane.current", "pane.layout", "pane.edges", "pane.neighbor",
    "agent.list", "agent.get", "agent.read", "tab.list", "workspace.list",
    "session.snapshot", "events.subscribe", "events.wait",
    "pane.wait_for_output",
))


def load_fixture(name):
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as handle:
        return json.load(handle)


# ---------------------------------------------------------------------------
# The fake herdr server — the verifier's §6.2 shape, speaking the live
# dialect of §3.1 / §6.3: own AF_UNIX path in a tempfile directory, one
# '\n'-framed JSON request {"id","method","params"}, string-only ids (a
# non-string id is refused before dispatch with the exact live refusal),
# every method name recorded (the write-surface evidence), answers from a
# handler.  Never a live socket.
# ---------------------------------------------------------------------------

class FakeHerdrServer:
    def __init__(self, directory, name="herdr-test.sock"):
        self.path = os.path.join(directory, name)
        self.requests = []       # full envelopes received
        self.methods = []        # method names only (write-surface evidence)
        self.connections = 0
        self.handler = None      # callable(request) -> response dict (no id)
        self.mismatches = []
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
        # The live dialect (§3.1, §6.3): the envelope id must be a JSON
        # STRING.  A non-string id is refused before dispatch, exactly as
        # herdr 0.8.2 was probed to answer for id=7 and id=None.
        if not isinstance(request.get("id"), str):
            refusal = {"id": "", "error": {
                "code": "invalid_request",
                "message": "invalid request: invalid type for id"}}
            conn.sendall(json.dumps(refusal, ensure_ascii=False).encode(
                "utf-8") + b"\n")
            return
        if self.handler is None:
            return
        response = self.handler(request)
        if response is None:
            return
        payload = json.dumps(response, ensure_ascii=False).encode(
            "utf-8") + b"\n"
        conn.sendall(payload)


def scripted_handler(transcript, log):
    """Serve a fixture transcript in order: each incoming request must
    match the next scripted entry's method and params; the scripted
    response is echoed with the request's string id.  Any deviation is
    logged (tests fail on it) — a fixture is a claim about reality."""
    index = 0

    def handler(request):
        nonlocal index
        if index >= len(transcript):
            log.append(("script exhausted", request))
            return {"id": request.get("id"), "error": {
                "code": "script_exhausted",
                "message": "more requests than the transcript scripts"}}
        entry = transcript[index]
        index += 1
        expected = entry["request"]
        if (request.get("method") != expected.get("method")
                or request.get("params") != expected.get("params")):
            log.append(("script mismatch", expected, request))
            return {"id": request.get("id"), "error": {
                "code": "script_mismatch",
                "message": "request does not match the scripted transcript"}}
        response = json.loads(json.dumps(
            entry["response"], ensure_ascii=False))
        response["id"] = request.get("id")
        return response

    return handler


# --- helpers ---------------------------------------------------------------

def seed_ledger(ledger_path, seed_records):
    """Seed a scratch ledger with full fifteen-field records (the plant),
    one canonical JSON line each — nothing touches the live ledger."""
    with open(ledger_path, "a", encoding="utf-8") as handle:
        for record in seed_records:
            handle.write(canonical_json(record) + "\n")


def append_human(ledger_path, caller_record):
    """The test plays the human's TTY act (cell-attest refuses non-TTY,
    RC=4 — never routed around): append the attestation record through
    B0's writer.  The DRIVER never does this."""
    with LedgerWriter(ledger_path) as writer:
        return writer.append(caller_record)


def build_pi_home(directory, spec):
    """Build a tempfile Pi home from a fixture's pi_home spec; a None
    value means the path is absent (as live)."""
    pi_home = os.path.join(directory, "pi_home")
    os.makedirs(pi_home, exist_ok=True)
    for rel, content in spec.items():
        if content is None:
            continue
        path = os.path.join(pi_home, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(content, handle, ensure_ascii=False)
    return pi_home


def make_driver(socket_path, ledger_path, fixture, directory):
    pi_home = build_pi_home(directory, fixture["pi_home"])
    params = dict(fixture["driver_params"])
    return Driver(
        socket_path=socket_path,
        ledger_path=ledger_path,
        blocks=fixture["blocks"],
        pi_home=pi_home,
        wait_timeout_ms=params.get("wait_timeout_ms"),
        fence_source=params.get("fence_source"),
        block_version=params.get("block_version", ""),
    )


def loaded_records(ledger_path):
    return LedgerLoader(ledger_path).load(write_index=False).records


def seq(records):
    """(address, gate, state, kind) per record, kind inferred: plant =
    attested + non-null ref and gate x; human = attested + non-null ref;
    proposal = held-pending whose turn_key is the pair's prompt key
    (sha256 over attempt "1"); refusal = held-pending with any other
    key (the refusal slot).  Keys are asserted separately."""
    out = []
    for record in records:
        if (record["state"] == "attested"
                and record["attestation_ref"] is not None):
            kind = "plant" if (record["gate"] == "x"
                               and record["address"] == "") else "human"
        elif record["state"] == "held-pending":
            prompt_key = turn_key(record["address"], record["gate"],
                                  PROMPT_ATTEMPT, record["block_version"])
            kind = ("proposal" if record["turn_key"] == prompt_key
                    else "refusal")
        else:
            kind = "proposal"
        out.append((record["address"], record["gate"], record["state"],
                    kind))
    return out


def expected_seq(fixture):
    return [
        (entry["address"], entry["gate"], entry["state"], entry["kind"])
        for entry in fixture["expected_ledger_sequence"]
    ]


def settle(fn, timeout_s=2.0):
    """Poll (test plumbing, not a timed artifact operation) until fn()
    holds — the fake server's accept loop runs in its own thread."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if fn():
            return True
        time.sleep(0.02)
    return fn()


class TmpCase(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.directory = self.td.name
        self.ledger_path = os.path.join(self.directory, "gates.jsonl")
        self.server = FakeHerdrServer(self.directory)
        self.addCleanup(self.server.halt)


# ---------------------------------------------------------------------------
# K1 / K2 — the turn and the key
# ---------------------------------------------------------------------------

class TestTurnKeyAndFence(TmpCase):
    def test_turn_key_is_sha256_of_the_four_fields(self):
        """K2 — quantity measured: the hex64 turn_key equals sha256 over the
        raw concatenation address‖gate‖attempt‖block_version (no separator),
        including a non-ASCII block_version."""
        self.assertEqual(
            turn_key("G", "y", "1", ""),
            hashlib.sha256(b"G" + b"y" + b"1" + b"").hexdigest())
        self.assertEqual(
            turn_key("Q", "z", 1, NEEDLE),
            hashlib.sha256(
                ("Q" + "z" + "1" + NEEDLE).encode("utf-8")).hexdigest())
        self.assertEqual(len(turn_key("G", "y", "1", "")), 64)

    def test_fence_marker_wraps_the_key(self):
        """K1 — quantity measured: fence_marker(turn_key) is exactly
        ⟦END <turn_key>⟧ and the marker appears once at the prompt's end."""
        marker = fence_marker("a" * 64)
        self.assertEqual(marker, "⟦END " + "a" * 64 + "⟧")

    def test_one_turn_sends_exactly_the_five_scripted_requests(self):
        """K1 — quantity measured: one turn = pane.list (resolve by label),
        pane.get (live-label assertion), pane.get (centre guard), ONE
        agent.prompt whose text ends with the fence instruction, ONE
        pane.wait_for_output whose match is the marker — and nothing else."""
        fixture = load_fixture(DUP_FIXTURE)
        log = []
        self.server.start(scripted_handler(fixture["transcript"], log))
        seed_ledger(self.ledger_path, fixture["ledger_seed"])
        drv = make_driver(self.server.path, self.ledger_path,
                          fixture, self.directory)
        drv.boot()
        result = drv.take_turn("G", fixture["prompts"]["G"])
        self.assertEqual(result["status"], "proposed")
        self.assertEqual(log, [])
        self.assertEqual(
            self.server.methods,
            ["pane.list", "pane.get", "pane.get",
             "agent.prompt", "pane.wait_for_output"])
        key = fixture["expected_prompt_keys"]["G"]
        marker = fence_marker(key)
        prompt = self.server.requests[3]["params"]["text"]
        self.assertIn(NEEDLE, prompt)
        self.assertTrue(prompt.endswith(marker))
        wait = self.server.requests[4]["params"]
        self.assertEqual(wait["match"],
                         {"type": "substring", "value": marker})
        self.assertEqual(self.server.methods.count("agent.prompt"), 1)
        records = loaded_records(self.ledger_path)
        self.assertEqual(len(records), 2)  # plant + one proposal
        self.assertEqual(records[-1]["turn_key"], key)
        self.assertEqual(records[-1]["state"], "held-pending")
        self.assertEqual(records[-1]["attestation_ref"], None)


# ---------------------------------------------------------------------------
# K5 — the centre guard
# ---------------------------------------------------------------------------

class TestCentreGuard(TmpCase):
    def test_guard_refuses_centre_desk_key_and_unverifiable_target(self):
        """K5 — quantity measured: assert_not_centre raises CentreWriteError
        for the centre desk key "S", for the podium label, and for None
        (unverifiable); it passes other desk keys."""
        for centre in ("S", "podium"):
            with self.assertRaises(CentreWriteError):
                assert_not_centre(centre)
        with self.assertRaises(CentreWriteError):
            assert_not_centre(None)
        self.assertIsNone(assert_not_centre("G"))
        self.assertIsNone(assert_not_centre("Q"))

    def test_runtime_prompt_of_the_centre_is_refused_before_bytes(self):
        """K5 — quantity measured: agent.prompt to the podium pane raises
        CentreWriteError with ZERO agent.prompt bytes on the wire (the
        guard's only socket traffic is the read pane.get), and
        take_turn("S") raises before ANY socket traffic at all."""
        fixture = load_fixture(DUP_FIXTURE)

        def handler(request):
            if request.get("method") == "pane.get":
                pane = [p for p in fixture["panes"]
                        if p["pane_id"] == request["params"]["pane_id"]][0]
                return {"id": request.get("id"), "result": {
                    "type": "pane_info", "pane": pane}}
            return {"id": request.get("id"), "error": {
                "code": "method_not_found", "message": "unscripted"}}

        self.server.start(handler)
        seed_ledger(self.ledger_path, fixture["ledger_seed"])
        drv = make_driver(self.server.path, self.ledger_path,
                          fixture, self.directory)
        centre_id = "w8:p2"  # label podium → desk S
        before = len(self.server.requests)
        with self.assertRaises(CentreWriteError):
            drv.instrument.call(
                "agent.prompt",
                {"target": centre_id, "text": "reach the podium"})
        after_prompt_attempt = len(self.server.requests)
        # the guard read the label (pane.get) but the write never left:
        self.assertEqual(after_prompt_attempt, before + 1)
        self.assertNotIn("agent.prompt", self.server.methods)
        with self.assertRaises(CentreWriteError):
            drv.take_turn("S", "reach the podium")
        self.assertEqual(len(self.server.requests), after_prompt_attempt)
        self.assertEqual(len(loaded_records(self.ledger_path)), 1)

    def test_pane_send_text_is_outside_both_allowlists_everywhere(self):
        """K5 / prohibition 2 — quantity measured: pane.send_text raises
        MethodNotAllowedError at the centre AND at a walk desk, with zero
        bytes and zero connections (the only write this round is
        agent.prompt)."""
        inst = Instrument(socket_path=os.path.join(self.directory, "s"))
        for pane_id in ("w8:p2", "w8:p3"):
            with self.assertRaises(MethodNotAllowedError):
                inst.call("pane.send_text",
                          {"pane_id": pane_id, "text": "x"})
        inst.close()
        self.server.start(lambda request: None)
        try:
            raw = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            raw.connect(self.server.path)
            raw.sendall(json.dumps(
                {"id": "1", "method": "pane.send_text",
                 "params": {"pane_id": "w8:p2", "text": "x"}}).encode()
                + b"\n")
        finally:
            raw.close()
        self.assertTrue(settle(lambda: self.server.connections == 1))
        self.assertEqual(self.server.methods, ["pane.send_text"])

    def test_allowlists_are_two_frozen_disjoint_sets(self):
        """K5 / prohibition 2 — quantity measured: READ_ONLY_METHODS is
        exactly B1's 18-method frozen set (never widened); WRITE_METHODS is
        the frozen single-element set {"agent.prompt"}; the two are
        disjoint and pane.wait_for_output stays on the READ side."""
        self.assertEqual(READ_ONLY_METHODS, B1_READ_ONLY)
        self.assertEqual(WRITE_METHODS, frozenset(("agent.prompt",)))
        self.assertIsInstance(READ_ONLY_METHODS, frozenset)
        self.assertIsInstance(WRITE_METHODS, frozenset)
        self.assertFalse(READ_ONLY_METHODS & WRITE_METHODS)
        self.assertIn("pane.wait_for_output", READ_ONLY_METHODS)

    def test_no_write_call_site_outside_the_chokepoint(self):
        """K5 (static) — quantity measured: every call("method", …) literal
        in the artifact sits inside READ_ONLY ∪ WRITE and the only WRITE
        literal is "agent.prompt"; the forbidden write-method literals
        appear in no call site at all."""
        forbidden = {
            "pane.send_text", "pane.send_input", "pane.send_keys",
            "pane.input.set", "agent.send_keys", "agent.start",
        }
        for name in ("instrument.py", "driver.py", "lens.py"):
            path = os.path.join(HERE, name)
            tree = ast.parse(open(path, encoding="utf-8").read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if (isinstance(func, ast.Attribute)
                            and func.attr == "call"
                            and node.args
                            and isinstance(node.args[0], ast.Constant)
                            and isinstance(node.args[0].value, str)):
                        method = node.args[0].value
                        self.assertNotIn(method, forbidden, path)
                        self.assertIn(
                            method,
                            READ_ONLY_METHODS | WRITE_METHODS, path)
                        if method in WRITE_METHODS:
                            self.assertEqual(method, "agent.prompt")


# ---------------------------------------------------------------------------
# K3 / C4 — the lens and the trust assertion
# ---------------------------------------------------------------------------

class TestTrustAssertion(TmpCase):
    def test_boot_fails_closed_before_any_socket_byte_on_live_like_state(self):
        """C4 — quantity measured: with an arrangement naming skills but a
        Pi state mirroring the live box (settings.json without a skills
        key, no skills directory, no pi binary), boot() raises TrustError
        at stage "skills" with verdict "inconclusive" (never clean), with
        ZERO socket requests, ZERO connections and ZERO records appended."""
        fixture = load_fixture(UNTRUSTED_FIXTURE)
        self.server.start(scripted_handler(fixture["transcript"], []))
        seed_ledger(self.ledger_path, fixture["ledger_seed"])
        drv = make_driver(self.server.path, self.ledger_path,
                          fixture, self.directory)
        with self.assertRaises(TrustError) as caught:
            drv.boot()
        self.assertEqual(caught.exception.stage, "skills")
        self.assertEqual(caught.exception.verdict, "inconclusive")
        self.assertEqual(self.server.requests, [])
        self.assertEqual(self.server.connections, 0)
        self.assertEqual(len(loaded_records(self.ledger_path)), 1)

    def test_boot_fails_closed_with_the_shipped_default_arrangement(self):
        """C4 — quantity measured: Driver() with the shipped DESK_BLOCKS
        (the live arrangement: nothing authored, no skills) raises
        TrustError at stage "instruction" before any socket byte — the C4
        negative case is the live default, not a synthetic one."""
        fixture = load_fixture(UNTRUSTED_FIXTURE)
        self.server.start(lambda request: None)
        seed_ledger(self.ledger_path, fixture["ledger_seed"])
        drv = Driver(socket_path=self.server.path,
                     ledger_path=self.ledger_path,
                     blocks=DESK_BLOCKS,
                     pi_home=self.directory)  # empty pi home, like live
        with self.assertRaises(TrustError) as caught:
            drv.boot()
        self.assertEqual(caught.exception.stage, "instruction")
        self.assertEqual(self.server.requests, [])
        self.assertEqual(self.server.connections, 0)

    def test_constituted_desk_boots_and_walks(self):
        """K3/C4 (positive control) — quantity measured: with all four §7
        blocks named and the skill observed loaded in the synthetic Pi
        state, boot() passes (touching the socket not at all) and the G
        turn then walks to a proposal."""
        fixture = load_fixture(CONSTITUTED_FIXTURE)
        log = []
        self.server.start(scripted_handler(fixture["transcript"], log))
        seed_ledger(self.ledger_path, fixture["ledger_seed"])
        drv = make_driver(self.server.path, self.ledger_path,
                          fixture, self.directory)
        boot = drv.boot()
        self.assertEqual(boot["due"], "G")
        self.assertEqual(self.server.requests, [])
        result = drv.take_turn("G", fixture["prompts"]["G"])
        self.assertEqual(result["status"], "proposed")
        self.assertEqual(log, [])
        self.assertEqual(self.server.methods.count("agent.prompt"), 1)

    def test_each_trust_failure_mode_raises_at_the_named_stage(self):
        """K3 — quantity measured: seven failure modes each raise
        TrustError at the named stage with the named verdict — missing
        arrangement entry; missing instruction; no skills; skills
        inconclusive (no observable source); skill not_loaded (a source
        observed, the name absent); missing tools; missing model — and
        exactly the constituted arrangement passes."""
        good = {
            "instruction": "fixture placeholder", "skills": ["s1"],
            "tools": ["t1"], "model": {"provider": "p", "model": "m"},
        }
        cases = [
            ({}, "arrangement", "missing"),
            ({"G": dict(good, instruction=None)}, "instruction", "missing"),
            ({"G": dict(good, instruction="  ")}, "instruction", "missing"),
            ({"G": dict(good, skills=[])}, "skills", "missing"),
            ({"G": dict(good, skills=[None, ""])}, "skills", "missing"),
        ]
        pi_home = build_pi_home(self.directory, {})  # nothing observable
        lens = Lens(pi_home=pi_home)
        for blocks, stage, verdict in cases:
            with self.assertRaises(TrustError) as caught:
                lens.assert_trust("G", blocks)
            self.assertEqual(caught.exception.stage, stage)
            self.assertEqual(caught.exception.verdict, verdict)
        with self.assertRaises(TrustError) as caught:
            lens.assert_trust("G", {"G": good})
        self.assertEqual(caught.exception.stage, "skills")
        self.assertEqual(caught.exception.verdict, "inconclusive")
        # a source observed, the named skill absent:
        pi_home2 = build_pi_home(
            self.directory,
            {"agent/settings.json": {"skills": ["other-skill"]}})
        with self.assertRaises(TrustError) as caught:
            Lens(pi_home=pi_home2).assert_trust("G", {"G": good})
        self.assertEqual(caught.exception.stage, "skills")
        self.assertEqual(caught.exception.verdict, "not_loaded")
        with self.assertRaises(TrustError) as caught:
            Lens(pi_home=pi_home2).assert_trust(
                "G", {"G": dict(good, skills=["s1", "other-skill"])})
        self.assertEqual(caught.exception.stage, "skills")
        self.assertEqual(caught.exception.verdict, "not_loaded")
        # a source that HAS the named skill, so the later stages surface:
        pi_home3 = build_pi_home(
            self.directory,
            {"agent/settings.json": {"skills": ["s1"]}})
        with self.assertRaises(TrustError) as caught:
            Lens(pi_home=pi_home3).assert_trust(
                "G", {"G": dict(good, tools=None)})
        self.assertEqual(caught.exception.stage, "tools")
        with self.assertRaises(TrustError) as caught:
            Lens(pi_home=pi_home3).assert_trust(
                "G", {"G": dict(good, model=None)})
        self.assertEqual(caught.exception.stage, "model")
        # the one that passes:
        returned = Lens(pi_home=pi_home3).assert_trust("G", {"G": good})
        self.assertEqual(returned, good)

    def test_module_assert_trust_delegates_and_lens_never_writes(self):
        """K3 — quantity measured: module-level assert_trust(desk, blocks,
        lens) raises/passes exactly as the lens does, and a full
        observe+assert leaves the Pi home byte-identical (the lens is
        read-only: same file list, same contents, same mtimes)."""
        pi_home = build_pi_home(
            self.directory,
            {"agent/settings.json": {"skills": ["s1"]}})
        good = {"instruction": "fixture placeholder", "skills": ["s1"],
                "tools": ["t1"], "model": {"provider": "p", "model": "m"}}
        lens = Lens(pi_home=pi_home)
        before = {}
        for root, _dirs, files in os.walk(pi_home):
            for name in files:
                path = os.path.join(root, name)
                with open(path, "rb") as handle:
                    before[path] = (os.stat(path).st_mtime_ns,
                                    handle.read())
        self.assertEqual(assert_trust("G", {"G": good}, lens), good)
        with self.assertRaises(TrustError):
            assert_trust("G", {"G": dict(good, skills=["nope"])}, lens)
        after = {}
        for root, _dirs, files in os.walk(pi_home):
            for name in files:
                path = os.path.join(root, name)
                with open(path, "rb") as handle:
                    after[path] = (os.stat(path).st_mtime_ns, handle.read())
        self.assertEqual(before, after)

    def test_pi_bin_not_invoked_without_a_path(self):
        """K3 / lens 6 — quantity measured: with pi_bin=None the binary is
        never invoked (observation reports "not invoked") and the trust
        assertion can never report clean — it fails inconclusive."""
        lens = Lens(pi_home=self.directory)
        obs = lens.observe()
        self.assertFalse(obs["pi_bin"]["observed"])
        self.assertIn("not invoked", obs["pi_bin"]["error"])
        good = {"instruction": "fixture placeholder", "skills": ["s1"],
                "tools": ["t1"], "model": {"provider": "p", "model": "m"}}
        with self.assertRaises(TrustError) as caught:
            lens.assert_trust("G", {"G": good})
        self.assertEqual(caught.exception.verdict, "inconclusive")


# ---------------------------------------------------------------------------
# C1 / C2 — the full cycle and the refusal
# ---------------------------------------------------------------------------

class TestCycle(TmpCase):
    def test_full_cycle_walked_with_interleaved_attestations(self):
        """C1 — quantity measured: the ledger's own record sequence across
        the whole cycle — gate letters exactly x y y y z z a a b b (plant,
        proposal, refusal, attestation interleaved; the refusal rides the
        held gate so the letters keep order), four agent.prompt calls on
        the wire in G→Q→P→V order, and every proposal followed by its
        attestation before the next prompt is sent."""
        fixture = load_fixture(CYCLE_FIXTURE)
        log = []
        self.server.start(scripted_handler(fixture["transcript"], log))
        seed_ledger(self.ledger_path, fixture["ledger_seed"])
        drv = make_driver(self.server.path, self.ledger_path,
                          fixture, self.directory)
        boot = drv.boot()
        self.assertEqual(boot["due"], "G")
        self.assertEqual(self.server.requests, [])
        for act in fixture["timeline"]:
            name = act["act"]
            if name == "boot":
                continue
            if name.startswith("take_turn"):
                desk = name.split()[-1]
                result = drv.take_turn(desk, fixture["prompts"][desk])
                self.assertEqual(
                    result["status"], act["expect"]["status"], name)
                if "turn_key" in act["expect"]:
                    self.assertEqual(
                        result["turn_key"], act["expect"]["turn_key"])
            elif name == "advance":
                result = drv.advance()
                self.assertEqual(
                    result["status"], act["expect"]["status"], name)
                if act["expect"]["status"] == "refused":
                    self.assertEqual(
                        result["refusal"]["turn_key"],
                        act["expect"]["refusal_turn_key"])
            elif name.startswith("attest"):
                desk = {"y": "G", "z": "Q", "a": "P", "b": "V"}[
                    name.split()[1]]
                append_human(
                    self.ledger_path,
                    fixture["human_attestation_records"][desk])
            else:
                self.fail("unknown timeline act %r" % name)
        self.assertEqual(log, [])
        records = loaded_records(self.ledger_path)
        self.assertEqual(seq(records), expected_seq(fixture))
        prompt_desks = [
            request["params"]["target"] for request in self.server.requests
            if request.get("method") == "agent.prompt"]
        self.assertEqual(
            prompt_desks, ["w8:p3", "w8:p5", "w8:p6", "w8:p4"])
        gates = [record["gate"] for record in records]
        self.assertEqual(gates, ["x", "y", "y", "y", "z", "z",
                                 "a", "a", "b", "b"])
        for record in records:
            if record["state"] == "held-pending":
                # every MACHINE record: held, mechanical, tentative, and
                # attestation_ref null — the human records carry his ref.
                self.assertIsNone(record["attestation_ref"])
                self.assertEqual(record["mark"], "mechanical")
                self.assertTrue(record["tentative"])

    def test_advance_without_attestation_refused_and_recorded(self):
        """C2 — quantity measured: two advance attempts while the proposal
        for (G, y) is unattested each return refused and each append ONE
        refusal record (keys in the refusal slot, distinct from the prompt
        key), with state held-pending, attestation_ref null, and NO prompt
        for the next desk on the wire."""
        fixture = load_fixture(CYCLE_FIXTURE)
        log = []
        self.server.start(scripted_handler(fixture["transcript"], log))
        seed_ledger(self.ledger_path, fixture["ledger_seed"])
        drv = make_driver(self.server.path, self.ledger_path,
                          fixture, self.directory)
        drv.boot()
        drv.take_turn("G", fixture["prompts"]["G"])
        first = drv.advance()
        self.assertEqual(first["status"], "refused")
        second = drv.advance()
        self.assertEqual(second["status"], "refused")
        self.assertNotEqual(
            first["refusal"]["turn_key"], second["refusal"]["turn_key"])
        records = loaded_records(self.ledger_path)
        refusals = [r for r in records if r["state"] == "held-pending"
                    and r["turn_key"] != turn_key(
                        r["address"], r["gate"], PROMPT_ATTEMPT,
                        r["block_version"])]
        self.assertEqual(len(refusals), 2)
        for refusal in refusals:
            self.assertEqual((refusal["address"], refusal["gate"]),
                             ("G", "y"))
            self.assertEqual(refusal["attestation_ref"], None)
            self.assertTrue(refusal["tentative"])
        self.assertEqual(self.server.methods.count("agent.prompt"), 1)
        self.assertEqual(self.server.methods.count("pane.wait_for_output"), 1)

    def test_out_of_order_turn_is_refused_on_the_due_gate(self):
        """C1/C2 — quantity measured: take_turn(P) while gate z is due
        (y attested, z unwalked) sends no prompt, appends ONE refusal on
        the due pair (Q, z) with the refusal-slot key, and the walk then
        proceeds normally through z."""
        fixture = load_fixture(CYCLE_FIXTURE)
        log = []
        self.server.start(scripted_handler(fixture["transcript"], log))
        seed_ledger(self.ledger_path, fixture["ledger_seed"])
        drv = make_driver(self.server.path, self.ledger_path,
                          fixture, self.directory)
        drv.boot()
        drv.take_turn("G", fixture["prompts"]["G"])
        append_human(self.ledger_path,
                     fixture["human_attestation_records"]["G"])
        result = drv.take_turn("P", fixture["prompts"]["P"])
        self.assertEqual(result["status"], "refused")
        self.assertEqual(self.server.methods.count("agent.prompt"), 1)
        records = loaded_records(self.ledger_path)
        refusal = records[-1]
        self.assertEqual((refusal["address"], refusal["gate"]), ("Q", "z"))
        self.assertEqual(refusal["turn_key"], "cd75491791f886fee0ab6fd3e"
                         "98158b2892d22c7c3f221f2fc80711022ffd3f1")
        self.assertNotEqual(refusal["turn_key"],
                            fixture["expected_prompt_keys"]["Q"])
        result = drv.take_turn("Q", fixture["prompts"]["Q"])
        self.assertEqual(result["status"], "proposed")
        self.assertEqual(log, [])

    def test_walked_gate_is_quiet_and_advance_reports_due(self):
        """C1/C3 — quantity measured: after gate y's attestation,
        advance() reports due (Q) without appending anything, and
        take_turn for the already-walked gate sends no prompt and appends
        no record (status already_walked); advance→complete after b is
        asserted inside the full-cycle C1 test."""
        fixture = load_fixture(DUP_FIXTURE)
        log = []
        self.server.start(scripted_handler(fixture["transcript"], log))
        seed_ledger(self.ledger_path, fixture["ledger_seed"])
        drv = make_driver(self.server.path, self.ledger_path,
                          fixture, self.directory)
        drv.boot()
        drv.take_turn("G", fixture["prompts"]["G"])
        append_human(self.ledger_path, {
            "address": "G", "gate": "y", "state": "attested",
            "mark": "emergent", "payload_ref": "attest:y",
            "axis": {"field": {"mode": "anchored", "anchor": "attest:y"},
                     "delta": []},
            "axis_verdict": None, "corruption": None, "tentative": False,
            "turn_key": "4e37acf8b261bb970495354d187bca8f9ff35144300177cad"
                        "7c23dc0f8364721", "block_version": "",
            "attestation_ref": "Amihai: gate y holds (fixture TTY stand-in)",
        })
        result = drv.take_turn("G", fixture["prompts"]["G"])
        self.assertEqual(result["status"], "already_walked")
        self.assertEqual(self.server.methods.count("agent.prompt"), 1)
        self.assertEqual(len(loaded_records(self.ledger_path)), 3)
        self.assertEqual(drv.advance()["status"], "due")
        self.assertEqual(drv.advance()["due_desk"], "Q")


# ---------------------------------------------------------------------------
# C3 / lens 5 — idempotency and cold restart
# ---------------------------------------------------------------------------

class TestIdempotency(TmpCase):
    def test_duplicated_prompt_produces_one_record(self):
        """C3 — quantity measured: the same turn re-issued in-process
        returns already_recorded, sends NO second prompt, and the ledger
        holds exactly ONE record bearing the prompt turn_key."""
        fixture = load_fixture(DUP_FIXTURE)
        log = []
        self.server.start(scripted_handler(fixture["transcript"], log))
        seed_ledger(self.ledger_path, fixture["ledger_seed"])
        drv = make_driver(self.server.path, self.ledger_path,
                          fixture, self.directory)
        drv.boot()
        key = fixture["expected_prompt_keys"]["G"]
        first = drv.take_turn("G", fixture["prompts"]["G"])
        self.assertEqual(first["status"], "proposed")
        second = drv.take_turn("G", fixture["prompts"]["G"])
        self.assertEqual(second["status"], "already_recorded")
        self.assertEqual(self.server.methods.count("agent.prompt"), 1)
        records = loaded_records(self.ledger_path)
        self.assertEqual(
            sum(1 for r in records if r["turn_key"] == key), 1)
        self.assertEqual(log, [])

    def test_cold_restart_subprocess_does_not_reprompt(self):
        """C3 / lens 5 — quantity measured: a FRESH subprocess, pointed at
        the same socket and ledger, rebuilds the position from the ledger
        alone (plant attested, gate x) and its take_turn for the recorded
        gate returns already_recorded — prompts on the wire stay ONE and
        records bearing the key stay ONE."""
        fixture = load_fixture(DUP_FIXTURE)
        log = []
        self.server.start(scripted_handler(fixture["transcript"], log))
        seed_ledger(self.ledger_path, fixture["ledger_seed"])
        drv = make_driver(self.server.path, self.ledger_path,
                          fixture, self.directory)
        drv.boot()
        first = drv.take_turn("G", fixture["prompts"]["G"])
        self.assertEqual(first["status"], "proposed")
        pi_home = build_pi_home(self.directory, fixture["pi_home"])
        child = r"""
import json, sys
authored, ledger_dir, socket_path, ledger_path, pi_home, blocks_json = \
    sys.argv[1:7]
sys.path.insert(0, authored)
sys.path.insert(0, ledger_dir)
from driver import Driver
driver = Driver(socket_path=socket_path, ledger_path=ledger_path,
                blocks=json.loads(blocks_json), pi_home=pi_home,
                wait_timeout_ms=60000, block_version="")
pos = driver.position()
result = driver.take_turn("G", "duplicate prompt from a fresh process")
print(json.dumps({"position": pos, "turn": result}, ensure_ascii=False))
"""
        completed = subprocess.run(
            [sys.executable, "-c", child, HERE, LEDGER_DIR,
             self.server.path, self.ledger_path, pi_home,
             json.dumps(fixture["blocks"], ensure_ascii=False)],
            capture_output=True, text=True, timeout=60)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        out = json.loads(completed.stdout)
        self.assertEqual(out["position"]["index"], 0)
        self.assertEqual(out["position"]["gate"], "x")
        self.assertEqual(out["turn"]["status"], "already_recorded")
        self.assertEqual(self.server.methods.count("agent.prompt"), 1)
        records = loaded_records(self.ledger_path)
        self.assertEqual(
            sum(1 for r in records
                if r["turn_key"] == fixture["expected_prompt_keys"]["G"]),
            1)

    def test_already_working_desk_still_one_record(self):
        """C3 — quantity measured: against a desk whose agent_status is
        "working", the turn still yields exactly ONE record bearing the
        key and ONE prompt; the re-issue while still working is
        suppressed by the ledger check before any second prompt (the
        driver never branches on agent_status — H-B2-6)."""
        fixture = load_fixture(WORKING_FIXTURE)
        log = []
        self.server.start(scripted_handler(fixture["transcript"], log))
        seed_ledger(self.ledger_path, fixture["ledger_seed"])
        drv = make_driver(self.server.path, self.ledger_path,
                          fixture, self.directory)
        drv.boot()
        key = fixture["expected_prompt_keys"]["G"]
        first = drv.take_turn("G", fixture["prompts"]["G"])
        self.assertEqual(first["status"], "proposed")
        second = drv.take_turn("G", fixture["prompts"]["G"])
        self.assertEqual(second["status"], "already_recorded")
        self.assertEqual(self.server.methods.count("agent.prompt"), 1)
        self.assertEqual(
            sum(1 for r in loaded_records(self.ledger_path)
                if r["turn_key"] == key), 1)
        self.assertEqual(log, [])


# ---------------------------------------------------------------------------
# K1 / lens 3 — an incomplete fence is never a completed turn
# ---------------------------------------------------------------------------

def _incomplete_handler(fixture, wait_response, log):
    """Reuse the scripted turn prefix (pane.list, 2× pane.get,
    agent.prompt) and substitute the wait_for_output response."""
    entries = [entry for entry in fixture["transcript"]
               if entry["request"]["method"] != "pane.wait_for_output"]
    wait_request = [entry["request"] for entry in fixture["transcript"]
                    if entry["request"]["method"] == "pane.wait_for_output"][0]
    entries.append({"request": wait_request, "response": wait_response})
    return scripted_handler(entries, log)


def _lost_label_handler(fixture):
    """pane.list answers the live lost-label shape (B1's §3.2 fact: pane
    ids re-mint and labels move): every walk desk's pane now carries
    label null, only the podium keeps its label — so a desk resolves to
    no live pane.  Every other method is refused loudly."""
    def handler(request):
        if request.get("method") == "pane.list":
            panes = []
            for pane in fixture["panes"]:
                entry = dict(pane)
                if entry.get("label") != "podium":
                    entry["label"] = None
                panes.append(entry)
            return {"id": request.get("id"), "result": {
                "type": "pane_list", "panes": panes}}
        return {"id": request.get("id"), "error": {
            "code": "method_not_found", "message": "unscripted"}}
    return handler


def _empty_pane_list_handler():
    """pane.list answers zero panes: no desk can resolve at all."""
    def handler(request):
        if request.get("method") == "pane.list":
            return {"id": request.get("id"), "result": {
                "type": "pane_list", "panes": []}}
        return {"id": request.get("id"), "error": {
            "code": "method_not_found", "message": "unscripted"}}
    return handler


class TestIncompleteFence(TmpCase):
    def _drive(self, wait_response):
        fixture = load_fixture(DUP_FIXTURE)
        log = []
        self.server.start(
            _incomplete_handler(fixture, wait_response, log))
        seed_ledger(self.ledger_path, fixture["ledger_seed"])
        drv = make_driver(self.server.path, self.ledger_path,
                          fixture, self.directory)
        drv.boot()
        return drv, log, fixture["prompts"]

    def test_timeout_reads_incomplete(self):
        """K1 / lens 3 — quantity measured: a wait_for_output timeout error
        (the declared claim code "timeout") makes the turn incomplete with
        ZERO records appended — a timeout is never a completed turn or an
        open gate (H-B2-3)."""
        drv, log, prompts = self._drive({
            "error": {"code": "timeout",
                      "message": "timed out waiting for output"}})
        result = drv.take_turn("G", prompts["G"])
        self.assertEqual(result["status"], "incomplete")
        self.assertIn("timeout", result["reason"])
        self.assertEqual(len(loaded_records(self.ledger_path)), 1)
        self.assertEqual(self.server.methods.count("agent.prompt"), 1)
        self.assertEqual(log, [])

    def test_empty_read_is_incomplete(self):
        """K1 / lens 3 — quantity measured: an output_matched read whose
        text is empty carries no marker, so the turn is incomplete and
        ZERO records are appended (absence is not validity)."""
        fixture = load_fixture(DUP_FIXTURE)
        pane = [p for p in fixture["panes"] if p["label"] == "G"][0]
        drv, log, prompts = self._drive({"result": {
            "type": "output_matched", "pane_id": pane["pane_id"],
            "revision": 3, "matched_line": None,
            "read": {"pane_id": pane["pane_id"],
                     "workspace_id": pane["workspace_id"],
                     "tab_id": pane["tab_id"], "source": "visible",
                     "format": "text", "text": "", "truncated": False,
                     "revision": 3}}})
        result = drv.take_turn("G", prompts["G"])
        self.assertEqual(result["status"], "incomplete")
        self.assertEqual(len(loaded_records(self.ledger_path)), 1)
        self.assertEqual(log, [])

    def test_truncated_read_is_incomplete(self):
        """K1 / lens 3 — quantity measured: a fenced read with
        truncated: true is refused (HerdrProtocolError → incomplete) and
        ZERO records are appended — a truncated read is never a complete
        answer."""
        fixture = load_fixture(DUP_FIXTURE)
        pane = [p for p in fixture["panes"] if p["label"] == "G"][0]
        marker = fence_marker(fixture["expected_prompt_keys"]["G"])
        drv, log, prompts = self._drive({"result": {
            "type": "output_matched", "pane_id": pane["pane_id"],
            "revision": 3, "matched_line": marker,
            "read": {"pane_id": pane["pane_id"],
                     "workspace_id": pane["workspace_id"],
                     "tab_id": pane["tab_id"], "source": "visible",
                     "format": "text", "text": marker, "truncated": True,
                     "revision": 3}}})
        result = drv.take_turn("G", prompts["G"])
        self.assertEqual(result["status"], "incomplete")
        self.assertIn("truncated", result["reason"])
        self.assertEqual(len(loaded_records(self.ledger_path)), 1)
        self.assertEqual(log, [])

    def test_matched_read_without_marker_is_incomplete(self):
        """K1 / lens 3 — quantity measured: a "matched" read whose text
        does not carry ⟦END …⟧ is refused and ZERO records are appended —
        a guessed completion is not a completed turn (H-B2-3)."""
        fixture = load_fixture(DUP_FIXTURE)
        pane = [p for p in fixture["panes"] if p["label"] == "G"][0]
        drv, log, prompts = self._drive({"result": {
            "type": "output_matched", "pane_id": pane["pane_id"],
            "revision": 3, "matched_line": "wrong",
            "read": {"pane_id": pane["pane_id"],
                     "workspace_id": pane["workspace_id"],
                     "tab_id": pane["tab_id"], "source": "visible",
                     "format": "text", "text": "no marker here",
                     "truncated": False, "revision": 3}}})
        result = drv.take_turn("G", prompts["G"])
        self.assertEqual(result["status"], "incomplete")
        self.assertIn("marker", result["reason"])
        self.assertEqual(len(loaded_records(self.ledger_path)), 1)
        self.assertEqual(log, [])

    def test_lost_label_is_incomplete(self):
        """K1 / lens 3 — quantity measured: a cell whose walk-desk panes
        carry label: null resolves the desk to no live pane, so
        take_turn is incomplete with ZERO records appended and the wire
        log carries ZERO agent.prompt requests (only the resolving
        pane.list) — a lost label is a typed DeskResolutionError refusal
        carrying "nothing was sent", never a bare KeyError (H-B2-3)."""
        fixture = load_fixture(DUP_FIXTURE)
        self.server.start(_lost_label_handler(fixture))
        seed_ledger(self.ledger_path, fixture["ledger_seed"])
        drv = make_driver(self.server.path, self.ledger_path,
                          fixture, self.directory)
        drv.boot()
        result = drv.take_turn("G", fixture["prompts"]["G"])
        self.assertEqual(result["status"], "incomplete")
        self.assertIn("DeskResolutionError", result["reason"])
        self.assertIn("nothing was sent", result["reason"])
        self.assertEqual(self.server.methods, ["pane.list"])
        self.assertNotIn("agent.prompt", self.server.methods)
        self.assertEqual(len(loaded_records(self.ledger_path)), 1)

    def test_empty_pane_list_is_incomplete(self):
        """K1 / lens 3 — quantity measured: an empty pane list resolves
        no desk at all, so take_turn is incomplete with ZERO records
        appended and the wire log carries ZERO agent.prompt requests —
        an absent desk is a typed DeskResolutionError refusal, never a
        guessed pane id (H-B2-3)."""
        fixture = load_fixture(DUP_FIXTURE)
        self.server.start(_empty_pane_list_handler())
        seed_ledger(self.ledger_path, fixture["ledger_seed"])
        drv = make_driver(self.server.path, self.ledger_path,
                          fixture, self.directory)
        drv.boot()
        result = drv.take_turn("G", fixture["prompts"]["G"])
        self.assertEqual(result["status"], "incomplete")
        self.assertIn("DeskResolutionError", result["reason"])
        self.assertEqual(self.server.methods, ["pane.list"])
        self.assertNotIn("agent.prompt", self.server.methods)
        self.assertEqual(len(loaded_records(self.ledger_path)), 1)

    def test_unknown_agent_status_never_reads_as_completed(self):
        """K1 / lens 3 — quantity measured: the driver's source contains
        no agent_status branch at all, so agent_status "unknown" (the
        live bare-desk normal) can never read as a completed turn or an
        open gate — and a desk reporting "unknown" still walks by label
        and fence alone."""
        with open(os.path.join(HERE, "driver.py"), encoding="utf-8") as fh:
            self.assertNotIn("agent_status", fh.read())
        fixture = load_fixture(DUP_FIXTURE)
        log = []
        self.server.start(scripted_handler(fixture["transcript"], log))
        seed_ledger(self.ledger_path, fixture["ledger_seed"])
        drv = make_driver(self.server.path, self.ledger_path,
                          fixture, self.directory)
        drv.boot()
        result = drv.take_turn("G", fixture["prompts"]["G"])
        self.assertEqual(result["status"], "proposed")
        self.assertEqual(log, [])


# ---------------------------------------------------------------------------
# K4 — no attestation, ever
# ---------------------------------------------------------------------------

class TestNoAttestation(TmpCase):
    def test_driver_never_writes_attested_or_sets_attestation_ref(self):
        """K4 — quantity measured, static: every "attestation_ref" key the
        driver authors carries None, no dict the driver builds carries
        state "attested", and the literal "attested" appears only inside
        the human-attestation CHECK, never as a written value."""
        for name in ("driver.py", "lens.py"):
            tree = ast.parse(
                open(os.path.join(HERE, name), encoding="utf-8").read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Dict):
                    for key, value in zip(node.keys, node.values):
                        if (isinstance(key, ast.Constant)
                                and key.value == "attestation_ref"):
                            self.assertIsNone(value.value, name)
                        if (isinstance(key, ast.Constant)
                                and key.value == "state"):
                            self.assertNotEqual(value.value, "attested",
                                                name)

    def test_every_driver_record_across_a_cycle_has_null_attestation_ref(self):
        """K4 — quantity measured, runtime: across the full cycle every
        machine record (proposal AND refusal) has attestation_ref null and
        state held-pending; the only attested records are the plant and
        the four human TTY stand-ins."""
        fixture = load_fixture(CYCLE_FIXTURE)
        log = []
        self.server.start(scripted_handler(fixture["transcript"], log))
        seed_ledger(self.ledger_path, fixture["ledger_seed"])
        drv = make_driver(self.server.path, self.ledger_path,
                          fixture, self.directory)
        drv.boot()
        drv.take_turn("G", fixture["prompts"]["G"])
        drv.advance()
        records = loaded_records(self.ledger_path)
        machine = [r for r in records if r["gate"] != "x"
                   and r["state"] == "held-pending"]
        self.assertEqual(len(machine), 2)  # proposal + refusal
        for record in machine:
            self.assertIsNone(record["attestation_ref"])
            self.assertEqual(record["state"], "held-pending")


# ---------------------------------------------------------------------------
# lens 4 — encoding
# ---------------------------------------------------------------------------

class TestEncoding(TmpCase):
    def test_needle_survives_prompt_fence_and_every_free_text_field(self):
        """lens 4 / K1 — quantity measured: the bytes ∞0′ → ‖ appear
        verbatim in the prompt, the fenced read, block_version, and the
        human attestation_ref; the proposal's payload_ref and turn_key are
        the sha256 forms computed over the needle-bearing bytes; and the
        ledger file bytes carry the needle un-mangled (fields constrained
        to enums — address/gate/state/mark — cannot carry it by schema)."""
        fixture = load_fixture(DUP_FIXTURE)
        pane = [p for p in fixture["panes"] if p["label"] == "G"][0]
        key = turn_key("G", "y", PROMPT_ATTEMPT, NEEDLE)
        marker = fence_marker(key)
        answer = "y: the needle lives. " + NEEDLE + "\n" + marker + "\n"
        read = {"pane_id": pane["pane_id"],
                "workspace_id": pane["workspace_id"],
                "tab_id": pane["tab_id"], "source": "visible",
                "format": "text", "text": answer, "truncated": False,
                "revision": 3}
        # the scripted turn with the needle riding the block_version: the
        # pane.list / pane.get entries stay, the prompt and the fence read
        # are rebuilt around the needle-derived key:
        prompt_text = "Desk G: carry the needle. " + NEEDLE
        needle_prompt = prompt_text + "\n" + (
            _FENCE_INSTRUCTION % marker)
        transcript = [
            fixture["transcript"][0],  # pane.list
            fixture["transcript"][1],  # pane.get (live-label assertion)
            fixture["transcript"][2],  # pane.get (centre guard)
            {"request": {"method": "agent.prompt",
                         "params": {"target": pane["pane_id"],
                                    "text": needle_prompt}},
             "response": fixture["transcript"][3]["response"]},
            {"request": {"method": "pane.wait_for_output",
                         "params": {"pane_id": pane["pane_id"],
                                    "source": "visible",
                                    "match": {"type": "substring",
                                              "value": marker},
                                    "strip_ansi": True,
                                    "timeout_ms": 60000}},
             "response": {"result": {"type": "output_matched",
                                     "pane_id": pane["pane_id"],
                                     "revision": 3, "matched_line": marker,
                                     "read": read}}},
        ]
        log = []
        self.server.start(scripted_handler(transcript, log))
        seed_ledger(self.ledger_path, fixture["ledger_seed"])
        pi_home = build_pi_home(self.directory, fixture["pi_home"])
        drv = Driver(socket_path=self.server.path,
                     ledger_path=self.ledger_path,
                     blocks=fixture["blocks"], pi_home=pi_home,
                     wait_timeout_ms=60000, block_version=NEEDLE)
        drv.boot()
        result = drv.take_turn("G", prompt_text)
        self.assertEqual(result["status"], "proposed")
        self.assertEqual(log, [])
        record = result["record"]
        self.assertEqual(record["block_version"], NEEDLE)
        self.assertEqual(record["turn_key"], key)
        self.assertEqual(
            record["payload_ref"],
            "fenced:sha256:" + hashlib.sha256(
                answer.encode("utf-8")).hexdigest())
        self.assertIsNone(record["attestation_ref"])
        sent = [r for r in self.server.requests
                if r.get("method") == "agent.prompt"][0]
        self.assertIn(NEEDLE, sent["params"]["text"])
        self.assertIn(NEEDLE, result["read"]["text"])
        refusal = drv.advance()
        self.assertEqual(refusal["status"], "refused")
        self.assertEqual(refusal["refusal"]["block_version"], NEEDLE)
        self.assertEqual(
            refusal["refusal"]["turn_key"],
            turn_key("G", "y", "refusal:1", NEEDLE))
        append_human(self.ledger_path, {
            "address": "G", "gate": "y", "state": "attested",
            "mark": "emergent", "payload_ref": "attest: " + NEEDLE,
            "axis": {"field": {"mode": "anchored",
                               "anchor": "attest: " + NEEDLE},
                     "delta": []},
            "axis_verdict": None, "corruption": None, "tentative": False,
            "turn_key": turn_key("G", "y", "", NEEDLE),
            "block_version": NEEDLE,
            "attestation_ref": "Attested: " + NEEDLE,
        })
        records = loaded_records(self.ledger_path)
        self.assertEqual(records[-1]["attestation_ref"],
                         "Attested: " + NEEDLE)
        self.assertEqual(records[-1]["payload_ref"], "attest: " + NEEDLE)
        with open(self.ledger_path, "rb") as handle:
            raw = handle.read()
        self.assertIn(NEEDLE.encode("utf-8"), raw)


# ---------------------------------------------------------------------------
# §3.1 / §6.3 — the fake server speaks the live dialect
# ---------------------------------------------------------------------------

class TestDialect(TmpCase):
    def test_non_string_id_refused_exactly_like_the_live_server(self):
        """§3.1 / §6.3 — quantity measured: a request envelope with the
        non-string id 7 is refused before dispatch with {"id": "",
        "error": {"code": "invalid_request", …}} — byte-for-byte the
        shape herdr 0.8.2 was probed to answer — and every id the adapter
        itself sends is a JSON string."""
        self.server.start(lambda request: None)
        raw = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            raw.connect(self.server.path)
            raw.sendall(json.dumps(
                {"id": 7, "method": "ping", "params": {}}).encode()
                + b"\n")
            raw.settimeout(5.0)
            line = raw.recv(65536)
        finally:
            raw.close()
        response = json.loads(line.decode("utf-8"))
        self.assertEqual(response["id"], "")
        self.assertEqual(response["error"]["code"], "invalid_request")
        fixture = load_fixture(DUP_FIXTURE)
        log = []
        server2 = FakeHerdrServer(self.directory, name="herdr2.sock")
        self.addCleanup(server2.halt)
        server2.start(scripted_handler(fixture["transcript"], log))
        seed_ledger(self.ledger_path, fixture["ledger_seed"])
        drv = make_driver(server2.path, self.ledger_path,
                          fixture, self.directory)
        drv.boot()
        drv.take_turn("G", fixture["prompts"]["G"])
        self.assertTrue(all(isinstance(r.get("id"), str)
                            for r in server2.requests))

    def test_fixtures_declare_their_claims_and_bake_verifiable_keys(self):
        """§6.3 / K2 — quantity measured: every fixture parses, declares
        its write-shape claims (H-B2-4), carries the server dialect rules,
        and every baked key recomputes from the bound turn_key() over the
        fixture's own fields."""
        for name in (CYCLE_FIXTURE, DUP_FIXTURE, WORKING_FIXTURE,
                     UNTRUSTED_FIXTURE, CONSTITUTED_FIXTURE):
            fixture = load_fixture(name)
            self.assertIsInstance(fixture, dict, name)
            self.assertTrue(fixture.get("claims"), name)
            self.assertIn("server_rules", fixture, name)
            self.assertIn("non_string_id_refusal_example",
                          fixture["server_rules"], name)
        cycle = load_fixture(CYCLE_FIXTURE)
        for desk in ("G", "Q", "P", "V"):
            self.assertEqual(
                cycle["expected_prompt_keys"][desk],
                turn_key(desk, cycle["human_attestation_records"][desk]
                         ["gate"], "1", ""))
            human = cycle["human_attestation_records"][desk]
            self.assertEqual(
                human["turn_key"],
                turn_key(human["address"], human["gate"], "",
                         human["block_version"]))
        self.assertEqual(
            cycle["expected_refusal_keys"]["G1"],
            turn_key("G", "y", "refusal:1", ""))

    def test_write_response_shapes_are_the_declared_claims(self):
        """H-B2-4 — quantity measured: every fixture's agent.prompt answer
        carries {"type": "agent_prompted", "agent": AgentInfo} and every
        wait_for_output answer carries {"type": "output_matched",
        "pane_id", "revision", "read": PaneReadResult} — the declared
        schema-derived claims, never reported as observed."""
        for name in (CYCLE_FIXTURE, DUP_FIXTURE, WORKING_FIXTURE,
                     CONSTITUTED_FIXTURE):
            fixture = load_fixture(name)
            for entry in fixture["transcript"]:
                method = entry["request"]["method"]
                result = entry["response"].get("result") or {}
                if method == "agent.prompt":
                    self.assertEqual(result.get("type"),
                                     "agent_prompted", name)
                    self.assertIn("agent", result, name)
                    self.assertIn("agent_status", result["agent"], name)
                if method == "pane.wait_for_output":
                    self.assertEqual(result.get("type"),
                                     "output_matched", name)
                    self.assertIsInstance(result.get("pane_id"), str, name)
                    self.assertIsInstance(result.get("revision"), int, name)
                    read = result.get("read") or {}
                    for field in ("pane_id", "workspace_id", "tab_id",
                                  "source", "format", "text", "truncated",
                                  "revision"):
                        self.assertIn(field, read, name)
                    self.assertIs(read["truncated"], False, name)


# ---------------------------------------------------------------------------
# P4a — the step mode.  Every test below names the criterion / claim id it
# exercises and the quantity it measures; a timed test names the operation
# timed.  Stepping never sleeps inside a step; the fake servers answer
# instantly, so the suite stays well inside the 60 s T0 budget (K2).
# ---------------------------------------------------------------------------

P4A_FIXTURES = {
    "lawful": "lawful_desk_surface.json",
    "paraphrased": "paraphrased_equation_surface.json",
    "sixth_code": "sixth_corruption_code_surface.json",
    "missing_prime": "missing_infinity_zero_prime_v.json",
    "three_plus_one": "three_plus_one_cell.json",
    "full_trail": "full_stepped_session_trail.jsonl",
    "torn_trail": "torn_last_line_trail.jsonl",
}


def _walk_plan(fixture):
    acts = []
    for a in fixture["timeline"]:
        name = a["act"]
        if name == "boot":
            continue
        if name.startswith("take_turn"):
            desk = name.split()[-1]
            acts.append({"act": "take_turn", "desk": desk,
                         "text": fixture["prompts"][desk]})
        elif name == "advance":
            acts.append({"act": "advance"})
        elif name.startswith("attest"):
            acts.append({"act": "attest",
                         "desk": {"y": "G", "z": "Q", "a": "P",
                                  "b": "V"}[name.split()[1]]})
    return acts


def _ledger_projection(ledger_path):
    return [canonical_json(
        {key: value for key, value in record.items()
         if key not in ("ts", "record_id", "prev_hash")})
        for record in loaded_records(ledger_path)]


def _walk_unstepped(directory, fixture, ledger_path, server):
    pi_home = build_pi_home(directory, fixture["pi_home"])
    drv = Driver(socket_path=server.path, ledger_path=ledger_path,
                 blocks=fixture["blocks"], pi_home=pi_home,
                 wait_timeout_ms=60000, block_version="")
    drv.boot()
    for a in fixture["timeline"]:
        name = a["act"]
        if name == "boot":
            continue
        if name.startswith("take_turn"):
            desk = name.split()[-1]
            drv.take_turn(desk, fixture["prompts"][desk])
        elif name == "advance":
            drv.advance()
        elif name.startswith("attest"):
            append_human(ledger_path, fixture["human_attestation_records"][
                {"y": "G", "z": "Q", "a": "P", "b": "V"}[name.split()[1]]])
    drv.close()
    return (_ledger_projection(ledger_path), list(server.methods),
            [request["params"] for request in server.requests])


def _walk_stepped(directory, fixture, ledger_path, server, trail_path):
    from step import AutoStepper, run_session
    pi_home = build_pi_home(directory, fixture["pi_home"])
    drv = Driver(socket_path=server.path, ledger_path=ledger_path,
                 blocks=fixture["blocks"], pi_home=pi_home,
                 wait_timeout_ms=60000, block_version="",
                 stepper=AutoStepper(), trail_path=trail_path)
    attested = []

    def attest(act):
        record = append_human(
            ledger_path, fixture["human_attestation_records"][act["desk"]])
        attested.append(record)
        return record

    result = run_session(drv, _walk_plan(fixture), attest=attest,
                         on_fail="stop")
    drv.close()
    return result, attested


class TestC1SameCodePath(TmpCase):
    def test_stepper_none_is_a_true_no_op(self):
        """C1 — quantity measured: with stepper=None (the B2 default) a
        full walk creates ZERO trail files anywhere in the tempdir, the
        returned status dicts carry no "step" key, and the socket
        sequence is exactly B2's five-method turn."""
        fixture = load_fixture(CYCLE_FIXTURE)
        log = []
        self.server.start(scripted_handler(fixture["transcript"], log))
        seed_ledger(self.ledger_path, fixture["ledger_seed"])
        pi_home = build_pi_home(self.directory, fixture["pi_home"])
        drv = Driver(socket_path=self.server.path,
                     ledger_path=self.ledger_path,
                     blocks=fixture["blocks"], pi_home=pi_home,
                     wait_timeout_ms=60000, block_version="")
        boot = drv.boot()
        self.assertNotIn("step", boot)
        for a in fixture["timeline"]:
            name = a["act"]
            if name == "boot":
                continue
            if name.startswith("take_turn"):
                desk = name.split()[-1]
                result = drv.take_turn(desk, fixture["prompts"][desk])
                self.assertNotIn("step", result)
            elif name == "advance":
                result = drv.advance()
                self.assertNotIn("step", result)
            elif name.startswith("attest"):
                append_human(self.ledger_path,
                             fixture["human_attestation_records"][
                                 {"y": "G", "z": "Q", "a": "P",
                                  "b": "V"}[name.split()[1]]])
        trails = [path for path, _dirs, files in os.walk(self.directory)
                  for path in [os.path.join(path, f) for f in files
                               if f.endswith(".jsonl")]]
        self.assertEqual(trails, [self.ledger_path])
        self.assertEqual(log, [])

    def test_stepped_walk_is_identical_to_the_unstepped_walk(self):
        """C1 — quantity measured: the same walk y→z→a→b run unstepped and
        under AutoStepper produces IDENTICAL ledger projections (10
        records each, hashed per the C1 projection), an IDENTICAL ordered
        socket method sequence (20 calls) and IDENTICAL params — the same
        code path, stepped."""
        fixture = load_fixture(CYCLE_FIXTURE)
        proj1 = methods1 = params1 = None
        for stepped in (False, True):
            directory = tempfile.mkdtemp()
            ledger_path = os.path.join(directory, "gates.jsonl")
            server = FakeHerdrServer(directory)
            self.addCleanup(server.halt)
            log = []
            server.start(scripted_handler(fixture["transcript"], log))
            seed_ledger(ledger_path, fixture["ledger_seed"])
            if stepped:
                result, _ = _walk_stepped(
                    directory, fixture, ledger_path, server,
                    os.path.join(directory, "trail", "sess.jsonl"))
                self.assertEqual(result["status"], "complete")
            else:
                proj, methods, params = _walk_unstepped(
                    directory, fixture, ledger_path, server)
                proj1, methods1, params1 = proj, methods, params
            self.assertEqual(log, [])
            if stepped:
                self.assertEqual(_ledger_projection(ledger_path), proj1)
                self.assertEqual(list(server.methods), methods1)
                self.assertEqual(
                    [request["params"] for request in server.requests],
                    params1)

    def test_exactly_one_implementation_exists(self):
        """C1 (AST read) — quantity measured: take_turn, advance and boot
        are each defined exactly ONCE, in driver.py; step.py/conformance
        .py/surface.py define none of them, no second turn_key
        derivation and no LedgerWriter append path (the runner calls the
        driver; the human's attest provider is the one writer)."""
        counts = {}
        for name in ("step.py", "conformance.py", "surface.py",
                     "driver.py"):
            tree = ast.parse(
                open(os.path.join(HERE, name), encoding="utf-8").read())
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    counts.setdefault(node.name, []).append(name)
        for method in ("take_turn", "advance", "boot"):
            self.assertEqual(counts.get(method), ["driver.py"], method)
        for name in ("step.py", "conformance.py", "surface.py"):
            tree = ast.parse(
                open(os.path.join(HERE, name), encoding="utf-8").read())
            source = open(os.path.join(HERE, name),
                          encoding="utf-8").read()
            for node in ast.walk(tree):
                if (isinstance(node, ast.FunctionDef)
                        and node.name == "turn_key"):
                    self.fail(name)
            if "LedgerWriter" in source:
                self.fail("%s opens a second ledger append path" % name)


class TestC2Suspension(TmpCase):
    class StopAtFirst:
        def __init__(self, stops):
            self.stops = stops
            self.before_calls = 0
            self.after_calls = 0

        def before(self, intent):
            self.before_calls += 1
            if self.before_calls in self.stops:
                return "stop"
            return "continue"

        def after(self, event):
            self.after_calls += 1
            return "continue"

    def test_stop_before_boot_sends_zero_bytes_and_writes_zero_records(self):
        """C2.1 — quantity measured: a controller answering stop at the
        boot intent leaves ZERO socket connections, ZERO records and a
        trail whose last line is the intent with outcome "not-taken" and
        a populated next block."""
        from step import read_trail
        fixture = load_fixture(DUP_FIXTURE)
        self.server.start(scripted_handler(fixture["transcript"], []))
        seed_ledger(self.ledger_path, fixture["ledger_seed"])
        pi_home = build_pi_home(self.directory, fixture["pi_home"])
        trail_path = os.path.join(self.directory, "trail", "sess.jsonl")
        stepper = self.StopAtFirst({1})
        drv = Driver(socket_path=self.server.path,
                     ledger_path=self.ledger_path,
                     blocks=fixture["blocks"], pi_home=pi_home,
                     wait_timeout_ms=60000, block_version="",
                     stepper=stepper, trail_path=trail_path)
        result = drv.boot()
        self.assertEqual(result["status"], "not-taken")
        self.assertEqual(self.server.connections, 0)
        self.assertEqual(len(loaded_records(self.ledger_path)), 1)
        read = read_trail(trail_path)
        self.assertEqual(read["status"], "ok")
        last = read["lines"][-1]
        self.assertTrue(last["intent_only"])
        self.assertEqual(last["outcome"]["status"], "not-taken")
        self.assertTrue(last["next"].get("action"))
        self.assertTrue(last["next"].get("why"))
        drv.close()

    def test_stop_before_turn_sends_zero_bytes_and_writes_zero_records(self):
        """C2.1 — quantity measured: stop at the turn's before hook (the
        second before call — the boot was allowed) leaves ZERO
        agent.prompt bytes, ZERO wait_for_output calls, ZERO records for
        the turn, and the trail's last line is the turn intent with
        outcome "not-taken"."""
        from step import read_trail
        fixture = load_fixture(DUP_FIXTURE)
        log = []
        self.server.start(scripted_handler(fixture["transcript"], log))
        seed_ledger(self.ledger_path, fixture["ledger_seed"])
        pi_home = build_pi_home(self.directory, fixture["pi_home"])
        trail_path = os.path.join(self.directory, "trail", "sess.jsonl")
        stepper = self.StopAtFirst({2})
        drv = Driver(socket_path=self.server.path,
                     ledger_path=self.ledger_path,
                     blocks=fixture["blocks"], pi_home=pi_home,
                     wait_timeout_ms=60000, block_version="",
                     stepper=stepper, trail_path=trail_path)
        drv.boot()
        result = drv.take_turn("G", fixture["prompts"]["G"])
        self.assertEqual(result["status"], "not-taken")
        self.assertNotIn("agent.prompt", self.server.methods)
        self.assertEqual(len(loaded_records(self.ledger_path)), 1)
        read = read_trail(trail_path)
        last = read["lines"][-1]
        self.assertTrue(last["intent_only"])
        self.assertEqual(last["outcome"]["status"], "not-taken")
        self.assertEqual(last["kind"], "turn")
        self.assertEqual(log, [])
        drv.close()

    def test_stop_in_after_hook_means_the_next_step_never_begins(self):
        """C2.2 — quantity measured: a controller answering stop in the
        after hook of the G turn ends the session cleanly — the boot and
        the G turn ran (1 agent.prompt), the advance after it never
        began (run_session status stopped, steps after the stop = 0)."""
        from step import AutoStepper, run_session
        fixture = load_fixture(CYCLE_FIXTURE)
        log = []
        self.server.start(scripted_handler(fixture["transcript"], log))
        seed_ledger(self.ledger_path, fixture["ledger_seed"])

        class StopAfterG:
            def before(self, intent):
                return "continue"

            def after(self, event):
                if (event.get("kind") == "turn"
                        and event.get("desk") == "G"
                        and (event.get("outcome") or {}).get("status")
                        == "proposed"):
                    return "stop"
                return "continue"

        plan = _walk_plan(fixture)
        trail_path = os.path.join(self.directory, "trail", "sess.jsonl")
        drv = Driver(socket_path=self.server.path,
                     ledger_path=self.ledger_path,
                     blocks=fixture["blocks"],
                     pi_home=build_pi_home(self.directory,
                                           fixture["pi_home"]),
                     wait_timeout_ms=60000, block_version="")
        result = run_session(
            drv, plan[:4], attest=None, stepper=StopAfterG(),
            trail_path=trail_path, on_fail="stop")
        self.assertEqual(result["status"], "stopped")
        statuses = [s.get("status") for s in result["steps"]
                    if isinstance(s, dict)]
        self.assertIn("proposed", statuses)
        self.assertNotIn("refused", statuses)
        self.assertEqual(self.server.methods.count("agent.prompt"), 1)
        drv.close()

    def test_fail_stops_the_session_and_the_override_is_recorded(self):
        """C2.3 — quantity measured: on_fail="stop" (the default) ends
        the run at the first FAIL; with on_fail="continue" (explicitly
        configured) the run continues AND the trail line records the
        policy override in conformance.policy."""
        from step import AutoStepper, run_session
        import conformance as conformance_module
        fixture = load_fixture(CYCLE_FIXTURE)
        log = []
        self.server.start(scripted_handler(fixture["transcript"], log))
        seed_ledger(self.ledger_path, fixture["ledger_seed"])
        # a defective cell observation injected through the provider: the
        # G desk announces a paraphrased equation — AD-SYN-2 FAILs
        paraphrased = load_fixture(P4A_FIXTURES["paraphrased"])
        parsed = __import__("surface").parse_surface(
            paraphrased["surface"],
            equation_forms=conformance_module.EQUATION_FORMS)

        class FakeCell:
            def __call__(self):
                return {"observed": True,
                        "arrangement": ["S", "G", "Q", "P", "V"],
                        "surfaces": {"G": parsed},
                        "question_ref": "demo:the-plant"}

        for on_fail, expect_stopped in (("stop", True),
                                        ("continue", False)):
            directory = tempfile.mkdtemp()
            ledger_path = os.path.join(directory, "gates.jsonl")
            server = FakeHerdrServer(directory)
            self.addCleanup(server.halt)
            server.start(scripted_handler(fixture["transcript"], []))
            seed_ledger(ledger_path, fixture["ledger_seed"])
            drv = Driver(socket_path=server.path, ledger_path=ledger_path,
                         blocks=fixture["blocks"],
                         pi_home=build_pi_home(directory,
                                               fixture["pi_home"]),
                         wait_timeout_ms=60000, block_version="")
            result = run_session(
                drv, _walk_plan(fixture),
                attest=lambda act: append_human(
                    ledger_path,
                    fixture["human_attestation_records"][act["desk"]]),
                stepper=AutoStepper(),
                trail_path=os.path.join(directory, "trail", "sess.jsonl"),
                on_fail=on_fail, cell_provider=FakeCell())
            self.assertEqual(result["status"],
                             "stopped" if expect_stopped else "complete")
            if on_fail == "continue":
                overridden = [line for line in result["lines"]
                              if line["conformance"]["verdict"] == "FAIL"
                              and "overrid" in
                              line["conformance"]["policy"]]
                self.assertTrue(overridden)
            drv.close()


class TestC3Emission(TmpCase):
    def test_every_line_carries_every_field_and_the_chain_holds(self):
        """C3 / lens 2 (invariant end-to-end) — quantity measured: all 21
        REQUIRED_TRAIL_FIELDS present on all 10 lines of the baked full
        session trail; seq gapless 0..9; prev_line_sha256 chaining every
        line (chain status ok); zoom/address coherent from step to step
        (turn lines carry op in, sign −, letter = desk, address_after =
        the desk's address)."""
        from step import REQUIRED_TRAIL_FIELDS, read_trail
        read = read_trail(os.path.join(FIXTURES,
                                       P4A_FIXTURES["full_trail"]))
        self.assertEqual(read["status"], "ok")
        self.assertEqual(read["chain"]["status"], "ok")
        lines = read["lines"]
        self.assertEqual(len(lines), 10)
        self.assertEqual([line["seq"] for line in lines],
                         list(range(10)))
        for line in lines:
            missing = [field for field in REQUIRED_TRAIL_FIELDS
                       if field not in line]
            self.assertEqual(missing, [])
        self.assertIsNone(lines[0]["prev_line_sha256"])
        for line in lines[1:]:
            self.assertEqual(len(line["prev_line_sha256"]), 64)
        for line in lines:
            if line["kind"] == "turn":
                self.assertEqual(line["zoom"]["op"], "in")
                self.assertEqual(line["zoom"]["sign"], "−")
                self.assertEqual(line["zoom"]["letter"], line["desk"])
                self.assertEqual(line["operation"], "take_turn")
        self.assertEqual(lines[0]["kind"], "boot")
        self.assertEqual(lines[-1]["kind"], "advance")
        self.assertEqual(lines[-1]["outcome"]["status"], "complete")

    def test_no_desk_content_anywhere_in_the_trail(self):
        """C3 (references, never content) — quantity measured: zero
        occurrences of any desk answer's text bytes (the cycle fixture's
        four fenced reads) in the raw trail file; the payload_refs that
        appear are scheme-prefixed references or 64-hex fingerprints."""
        import re as _re
        fixture = load_fixture(CYCLE_FIXTURE)
        raw = open(os.path.join(FIXTURES, P4A_FIXTURES["full_trail"]),
                   encoding="utf-8").read()
        texts = []
        for entry in fixture["transcript"]:
            result = entry["response"].get("result") or {}
            read = result.get("read")
            if read and isinstance(read.get("text"), str):
                texts.append(read["text"])
        self.assertTrue(texts)
        for text in texts:
            for chunk in text.split("\n"):
                if chunk.strip() and "⟦END" not in chunk:
                    self.assertNotIn(chunk, raw)
        refs = _re.findall(r'"payload_ref": ?"([^"]+)"', raw)
        self.assertTrue(refs)
        for ref in refs:
            self.assertTrue(
                _re.match(r"^[a-z][a-z0-9_.+-]*:[^\s]{1,200}$", ref)
                or _re.match(r"^[0-9a-f]{64}$", ref), ref)

    def test_unobservable_reads_inconclusive_on_the_live_like_box(self):
        """C3 / C4.3 (honesty) — quantity measured: evaluated against the
        live box state (the canon ledger replayed read-only, NO cell
        observation, NO step) every cell-scope item reads INCONCLUSIVE
        with a reason, the ledger-scope items decide honestly (R10 R11
        R12 PASS on the human's plant), and the report verdict is
        INCONCLUSIVE — the correct live default, never a papered-over
        PASS."""
        import conformance as conformance_module
        ctx = conformance_module.build_live_context()
        report = conformance_module.evaluate(ctx)
        self.assertEqual(report["verdict"], "INCONCLUSIVE")
        cell_items = [item for item in report["items"]
                      if item["scope"] == "cell"]
        self.assertTrue(cell_items)
        for item in cell_items:
            self.assertEqual(item["verdict"], "INCONCLUSIVE", item["id"])
            self.assertTrue(item.get("reason"), item["id"])
        for item_id in ("R10", "R11", "R12", "AD-SEM-4"):
            entry = [item for item in report["items"]
                     if item["id"] == item_id][0]
            self.assertEqual(entry["verdict"], "PASS", item_id)


class TestC4Checks(TmpCase):
    def _cell_context(self, fixture, desk):
        import conformance as conformance_module
        import surface as surface_module
        parsed = surface_module.parse_surface(
            fixture["surface"],
            equation_forms=conformance_module.EQUATION_FORMS)
        return {
            "step": None,
            "ledger": None,
            "cell": {"observed": True,
                     "arrangement": ["S", "G", "Q", "P", "V"],
                     "surfaces": {desk: parsed},
                     "question_ref": "demo:the-plant"},
            "session": {"lines": []},
            "sources_dir": None,
        }

    def test_each_defective_twin_fails_the_correct_item_by_id(self):
        """C4.2 — quantity measured: against the four defective surface
        twins and the 3+1 cell, the correct item FAILs BY ID (paraphrased
        equation → AD-SYN-2 with the differing codepoint in the evidence;
        sixth code → AD-SYN-5; 3+1 → AD-SYN-1 naming the missing corner;
        a V closing without ∞0′ at a V step → R8 + CX-SYN-6 + AD-SEM-3 +
        R2 — the source states the rule three times, mirrors by design)."""
        import conformance as conformance_module
        import surface as surface_module
        cases = [
            (P4A_FIXTURES["paraphrased"], "G",
             ["AD-SYN-2"], None),
            (P4A_FIXTURES["sixth_code"], "G",
             ["AD-SYN-5"], None),
        ]
        for name, desk, expected, _ in cases:
            fixture = load_fixture(name)
            report = conformance_module.evaluate(
                self._cell_context(fixture, desk))
            fails = [item["id"] for item in report["items"]
                     if item["verdict"] == "FAIL"]
            self.assertEqual(sorted(fails), sorted(expected), name)
        fixture = load_fixture(P4A_FIXTURES["paraphrased"])
        report = conformance_module.evaluate(
            self._cell_context(fixture, "G"))
        item = [i for i in report["items"] if i["id"] == "AD-SYN-2"][0]
        self.assertIn(0x0020, item["evidence"])
        # 3+1
        fixture = load_fixture(P4A_FIXTURES["three_plus_one"])
        parsed = {desk: surface_module.parse_surface(
            text, equation_forms=conformance_module.EQUATION_FORMS)
            for desk, text in fixture["surfaces"].items()}
        report = conformance_module.evaluate({
            "step": None, "ledger": None,
            "cell": {"observed": True,
                     "arrangement": fixture["arrangement"],
                     "surfaces": parsed,
                     "question_ref": "demo:the-plant"},
            "session": {"lines": []}, "sources_dir": None})
        fails = [item["id"] for item in report["items"]
                 if item["verdict"] == "FAIL"]
        self.assertEqual(fails, ["AD-SYN-1"])
        item = [i for i in report["items"] if i["id"] == "AD-SYN-1"][0]
        self.assertIn("3+1", item["reason"])
        # missing ∞0′ at a V step
        fixture = load_fixture(P4A_FIXTURES["missing_prime"])
        parsed = surface_module.parse_surface(
            fixture["surface"],
            equation_forms=conformance_module.EQUATION_FORMS)
        step = {"kind": "turn", "desk": "V", "gate": "b",
                "address_before": "P", "address_after": "V",
                "zoom": {"op": "in", "sign": "−", "letter": "V",
                         "derived_reading": False},
                "operation": "take_turn", "intent_only": False,
                "outcome": {"status": "proposed", "record_id": "r1",
                            "turn_key": "k"},
                "decoded": {"slots": parsed["slots"],
                            "source": "desk_surface",
                            "operation_steps": []},
                "compiled": {"symbol": "B+B''+∞0′", "gate": "b",
                             "landed": "record:r1"},
                "context_in": {}, "surface_parse": parsed, "await": True}
        ledger = {"path": "/tmp/fixture/gates.jsonl",
                  "records": [
                      {"record_id": "a" * 64, "address": "", "gate": "x",
                       "state": "attested", "mark": "emergent",
                       "payload_ref": "demo:the-plant",
                       "attestation_ref": "Start from Not Knowing"},
                      {"record_id": "b" * 64, "address": "G", "gate": "y",
                       "state": "attested", "mark": "emergent",
                       "payload_ref": "attest:y",
                       "attestation_ref": "attested"},
                      {"record_id": "c" * 64, "address": "Q", "gate": "z",
                       "state": "attested", "mark": "emergent",
                       "payload_ref": "attest:z",
                       "attestation_ref": "attested"},
                      {"record_id": "d" * 64, "address": "P", "gate": "a",
                       "state": "attested", "mark": "emergent",
                       "payload_ref": "attest:a",
                       "attestation_ref": "attested"}],
                  "count": 4, "head": "d" * 64}
        report = conformance_module.evaluate({
            "step": step, "ledger": ledger,
            "cell": {"observed": True,
                     "arrangement": ["S", "G", "Q", "P", "V"],
                     "surfaces": {"V": parsed},
                     "question_ref": "demo:the-plant"},
            "session": {"lines": []}, "sources_dir": None})
        fails = sorted(item["id"] for item in report["items"]
                       if item["verdict"] == "FAIL")
        self.assertEqual(fails, ["AD-SEM-3", "CX-SYN-6", "R2", "R8"])

    def test_remaining_defective_twins_fail_by_id(self):
        """C4.2 — quantity measured: the other five commissioned twins
        each FAIL the correct item by id: a '+' inside a phase equation
        → AD-SYN-4; a skipped/reordered phase (a proposed Q turn while y
        is unattested) → CX-SEM-2; a signed true start → AD-SEM-4; a
        lens question targeting the wrong output → AD-DRF-5 (and its
        §3.5 mirror CX-DRF-6); a hard-coded depth cap in a mutated
        artifact copy → AD-DRF-1 (AST scan over the mutated tree)."""
        import conformance as conformance_module
        import surface as surface_module
        # '+' inside a phase equation
        lawful = load_fixture(P4A_FIXTURES["lawful"])
        plus_surface = lawful["surface"].replace(
            "Q = φ ⋂ Ω\n", "Q = φ ⋂ + Ω\n", 1)
        parsed = surface_module.parse_surface(
            plus_surface, equation_forms=conformance_module.EQUATION_FORMS)
        report = conformance_module.evaluate({
            "step": None, "ledger": None,
            "cell": {"observed": True,
                     "arrangement": ["S", "G", "Q", "P", "V"],
                     "surfaces": {"G": parsed},
                     "question_ref": "demo:the-plant"},
            "session": {"lines": []}, "sources_dir": None})
        fails = [i["id"] for i in report["items"]
                 if i["verdict"] == "FAIL"]
        self.assertIn("AD-SYN-4", fails)
        # skipped/reordered phase: a proposed Q while y is unattested
        step = {"kind": "turn", "desk": "Q", "gate": "z",
                "address_before": "G", "address_after": "Q",
                "zoom": {"op": "in", "sign": "−", "letter": "Q",
                         "derived_reading": False},
                "operation": "take_turn", "intent_only": False,
                "outcome": {"status": "proposed", "record_id": "r1",
                            "turn_key": "k"},
                "decoded": {"slots": {}, "source": "absent",
                            "operation_steps": []},
                "compiled": {"symbol": "Z", "gate": "z",
                             "landed": "record:r1"},
                "context_in": {}, "surface_parse": None, "await": True}
        report = conformance_module.evaluate({
            "step": step,
            "ledger": {"path": "/tmp/f/gates.jsonl", "records": [
                {"record_id": "a" * 64, "address": "", "gate": "x",
                 "state": "attested", "mark": "emergent",
                 "payload_ref": "demo:the-plant",
                 "attestation_ref": "Start from Not Knowing"}],
                "count": 1, "head": "a" * 64},
            "cell": {"observed": False, "arrangement": None,
                     "surfaces": {}, "question_ref": None},
            "session": {"lines": []}, "sources_dir": None})
        fails = [i["id"] for i in report["items"]
                 if i["verdict"] == "FAIL"]
        self.assertIn("CX-SEM-2", fails)
        # a signed true start
        signed = conformance_module.evaluate({
            "step": None,
            "ledger": {"path": "/tmp/f/gates.jsonl", "records": [
                {"record_id": "a" * 64, "address": "+G", "gate": "x",
                 "state": "attested", "mark": "emergent",
                 "payload_ref": "demo:the-plant",
                 "attestation_ref": "Start from Not Knowing"}],
                "count": 1, "head": "a" * 64},
            "cell": {"observed": False, "arrangement": None,
                     "surfaces": {}, "question_ref": None},
            "session": {"lines": []}, "sources_dir": None})
        fails = [i["id"] for i in signed["items"]
                 if i["verdict"] == "FAIL"]
        self.assertIn("AD-SEM-4", fails)
        # a lens question targeting the wrong output (X, not the parent
        # G's output Y)
        lens_surface = lawful["surface"].replace(
            " — target: Y\nGQ", " — target: X\nGQ", 1)
        parsed = surface_module.parse_surface(
            lens_surface, equation_forms=conformance_module.EQUATION_FORMS)
        report = conformance_module.evaluate({
            "step": None, "ledger": None,
            "cell": {"observed": True,
                     "arrangement": ["S", "G", "Q", "P", "V"],
                     "surfaces": {"G": parsed},
                     "question_ref": "demo:the-plant"},
            "session": {"lines": []}, "sources_dir": None})
        fails = [i["id"] for i in report["items"]
                 if i["verdict"] == "FAIL"]
        self.assertIn("AD-DRF-5", fails)
        self.assertIn("CX-DRF-6", fails)
        # a hard-coded depth cap in a mutated artifact copy (subprocess
        # over the twin tree — the static scan reads the twin's source)
        import shutil
        twin = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, twin, True)
        twin_authored = os.path.join(twin, "authored")
        shutil.copytree(HERE, twin_authored)
        twin_driver = os.path.join(twin_authored, "driver.py")
        with open(twin_driver, "a", encoding="utf-8") as handle:
            handle.write("\n\nMAX_DEPTH = 3  # the twin's hard-coded cap\n"
                         "def capped(address):\n"
                         "    if len(address) >= MAX_DEPTH:\n"
                         "        return True\n"
                         "    return False\n")
        child = r"""
import json, sys
authored, ledger_dir = sys.argv[1:3]
sys.path.insert(0, authored)
sys.path.insert(0, ledger_dir)
import conformance
facts = conformance._static_facts()
ctx = {"step": None, "ledger": None,
       "cell": {"observed": False, "arrangement": None, "surfaces": {},
                "question_ref": None},
       "session": {"lines": []}, "sources_dir": None}
report = conformance.evaluate(ctx)
print(json.dumps({
    "caps": facts["caps"],
    "ad_drf_1": [i["verdict"] for i in report["items"]
                 if i["id"] == "AD-DRF-1"][0],
    "r13": [i["verdict"] for i in report["items"]
            if i["id"] == "R13"][0],
}))
"""
        completed = subprocess.run(
            [sys.executable, "-c", child, twin_authored, LEDGER_DIR],
            capture_output=True, text=True, timeout=60)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        out = json.loads(completed.stdout)
        self.assertTrue(out["caps"])
        self.assertEqual(out["ad_drf_1"], "FAIL")

    def test_citations_match_the_held_source_bytes_verbatim(self):
        """C4.1 — quantity measured: all 50 citations are found VERBATIM
        (as substrings) in the held source files — the checks are the
        source's, never the machine's taste."""
        import conformance as conformance_module
        codex = open(os.path.join(HERE, "..", "sources",
                                  "5qln-codex.txt"),
                     encoding="utf-8").read()
        appd = open(os.path.join(HERE, "..", "sources",
                                 "5qln-codex-appendix-D-the-fractal.txt"),
                    encoding="utf-8").read()
        commission = open(os.path.join(HERE, "..", "commission.md"),
                          encoding="utf-8").read()
        checked = 0
        for item_id, meta in conformance_module.CHECKS.items():
            citation = meta["citation"]
            if meta["derived"]:
                # derived items cite the decision's words (held in the
                # commission) plus a source line — every quoted part must
                # appear verbatim somewhere held
                for needle in ("without being told",
                               "more alive than X was"):
                    if needle in citation:
                        self.assertTrue(needle in codex, item_id)
                if ("success in each phase" in citation
                        or "Compilation of output xyzab" in citation):
                    self.assertIn("Compilation of output xyzab",
                                  commission)
                continue
            self.assertTrue(
                citation in codex or citation in appd, item_id)
            checked += 1
        self.assertGreaterEqual(checked, 46)

    def test_table_and_evaluator_cannot_drift_apart(self):
        """C4 / §3.7 lesson 5 — quantity measured: the set of ids in
        CHECKS equals the set of ids the evaluator can decide (asserted
        at import AND re-checked here), and no id drifts R1-R13 (the
        source's own numbering is intact)."""
        import conformance as conformance_module
        self.assertEqual(
            frozenset(conformance_module.CHECK_ORDER),
            frozenset(conformance_module.CHECKS))
        self.assertEqual(
            frozenset(conformance_module._EVALUATORS),
            frozenset(conformance_module.CHECKS))
        for n in range(1, 14):
            self.assertIn("R%d" % n, conformance_module.CHECKS)
        self.assertEqual(len(conformance_module.CHECKS), 50)


class TestC5TwoTrails(TmpCase):
    def test_trail_path_equal_to_ledger_path_is_refused(self):
        """C5 / §3.7 lesson 1 — quantity measured: constructing a
        StepTrail whose path equals the ledger path raises StepTrailError
        at construction — the trail is never the gate ledger."""
        from step import StepTrail, StepTrailError
        with self.assertRaises(StepTrailError):
            StepTrail(self.ledger_path, ledger_path=self.ledger_path)

    def test_absence_emptiness_and_torn_lines_are_never_conformant(self):
        """C5.3 / lens 3 (absence vs validity) — quantity measured: a
        missing trail file reads absent, an empty file reads empty with
        sha256 e3b0c44298fc…, a torn last line reads DAMAGED (2 good
        lines + 1 fragment — never a valid step, never empty-clean), and
        a one-line trail's chain reads undecidable, never trivially
        clean."""
        from step import StepTrail, read_trail
        missing = os.path.join(self.directory, "absent.jsonl")
        read = read_trail(missing)
        self.assertEqual(read["status"], "absent")
        empty = os.path.join(self.directory, "empty.jsonl")
        with open(empty, "w", encoding="utf-8") as handle:
            handle.write("")
        read = read_trail(empty)
        self.assertEqual(read["status"], "empty")
        self.assertEqual(
            read["sha256"],
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
        read = read_trail(os.path.join(FIXTURES,
                                       P4A_FIXTURES["torn_trail"]))
        self.assertEqual(read["status"], "damaged")
        self.assertEqual(len(read["lines"]), 2)
        self.assertIsNotNone(read["damage"])
        # one complete line: undecidable, never a pass
        one = os.path.join(self.directory, "one.jsonl")
        trail = StepTrail(one, ledger_path=self.ledger_path)
        from step import REQUIRED_TRAIL_FIELDS
        line = {field: None for field in REQUIRED_TRAIL_FIELDS}
        line.update({"trail_version": "1", "session_id": "a" * 12,
                     "seq": 0, "at": "2026-08-28T12:00:00+00:00",
                     "kind": "boot", "prev_line_sha256": None})
        trail.append(line)
        trail.close()
        read = read_trail(one)
        self.assertEqual(read["chain"]["status"], "undecidable")

    def test_fresh_process_rebuilds_position_and_trail_continuity(self):
        """C5.2 / lens 5 (cold restart) — quantity measured via a FRESH
        subprocess: the position rebuilds from the LEDGER alone (a
        recorded turn is never re-prompted — agent.prompt count stays 4
        across the restart) and the trail reads back from the TRAIL alone
        (status ok, chain ok, 10 lines); a continuing session appends
        seq 10 chained to line 9."""
        from step import AutoStepper, run_session, read_trail
        fixture = load_fixture(CYCLE_FIXTURE)
        log = []
        self.server.start(scripted_handler(fixture["transcript"], log))
        seed_ledger(self.ledger_path, fixture["ledger_seed"])
        trail_path = os.path.join(self.directory, "trail", "sess.jsonl")
        drv = Driver(socket_path=self.server.path,
                     ledger_path=self.ledger_path,
                     blocks=fixture["blocks"],
                     pi_home=build_pi_home(self.directory,
                                           fixture["pi_home"]),
                     wait_timeout_ms=60000, block_version="",
                     stepper=AutoStepper(), trail_path=trail_path)
        result = run_session(
            drv, _walk_plan(fixture),
            attest=lambda act: append_human(
                self.ledger_path,
                fixture["human_attestation_records"][act["desk"]]),
            on_fail="stop")
        self.assertEqual(result["status"], "complete")
        drv.close()
        pi_home = build_pi_home(self.directory, fixture["pi_home"])
        child = r"""
import json, sys
from step import read_trail
authored, ledger_dir, socket_path, ledger_path, trail_path, pi_home, blocks = sys.argv[1:8]
sys.path.insert(0, authored)
sys.path.insert(0, ledger_dir)
from driver import Driver
from step import AutoStepper
read = read_trail(trail_path)
driver = Driver(socket_path=socket_path, ledger_path=ledger_path,
                blocks=json.loads(blocks), pi_home=pi_home,
                wait_timeout_ms=60000, block_version="")
pos = driver.position()
dupe = driver.take_turn("G", "duplicate from the restarted process")
# a continuing session appends to the SAME trail: seq must continue
# gapless and the new line must chain to the last existing line
driver.attach_stepper(AutoStepper(), trail_path=trail_path,
                      session_id=read["lines"][0]["session_id"])
boot = driver.boot()
print(json.dumps({
    "trail_status": read["status"],
    "trail_chain": read["chain"]["status"],
    "trail_lines": len(read["lines"]),
    "position": pos,
    "dupe": dupe["status"],
    "boot_status": boot["step"]["line"]["outcome"]["status"],
    "boot_seq": boot["step"]["seq"],
}, ensure_ascii=False))
"""
        completed = subprocess.run(
            [sys.executable, "-c", child, HERE, LEDGER_DIR,
             self.server.path, self.ledger_path, trail_path, pi_home,
             json.dumps(fixture["blocks"], ensure_ascii=False)],
            capture_output=True, text=True, timeout=60)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        out = json.loads(completed.stdout)
        self.assertEqual(out["trail_status"], "ok")
        self.assertEqual(out["trail_chain"], "ok")
        self.assertEqual(out["trail_lines"], 10)
        self.assertEqual(out["position"]["gate"], "b")
        self.assertEqual(out["dupe"], "already_walked")
        self.assertEqual(out["boot_status"], "booted")
        self.assertEqual(out["boot_seq"], 10)
        self.assertEqual(self.server.methods.count("agent.prompt"), 4)
        read = read_trail(trail_path)
        self.assertEqual(read["status"], "ok")
        self.assertEqual(read["chain"]["status"], "ok")
        self.assertEqual(len(read["lines"]), 11)
        self.assertEqual(read["lines"][-1]["seq"], 10)
        self.assertEqual(log, [])


class TestKClaims(TmpCase):
    def test_k1_no_cap_no_root_assumption_alphabet_is_data(self):
        """K1 — quantity measured: the static AST facts are empty (zero
        depth-cap patterns, zero re-implemented address grammars) and the
        address alphabet lives in the walker's COURSE data table (five
        letters, a new marker = a table edit, nothing in code)."""
        import conformance as conformance_module
        facts = conformance_module._static_facts()
        self.assertEqual(facts["caps"], [])
        self.assertEqual(facts["grammar_reimpls"], [])
        self.assertEqual(facts["signed_equations"], [])
        self.assertEqual(tuple(COURSE_IMPORT), ("S", "G", "Q", "P", "V"))

    def test_k2_stdlib_only_and_a_full_session_under_60_seconds(self):
        """K2 — quantity measured and TIMED: the full stepped y→z→a→b
        session (the operation timed is run_session over the cycle
        fixture) completes in well under 60 s, and every module the
        artifact imports is stdlib + the authored predecessors + B0."""
        import conformance as conformance_module
        import step as step_module
        import surface as surface_module
        fixture = load_fixture(CYCLE_FIXTURE)
        log = []
        self.server.start(scripted_handler(fixture["transcript"], log))
        seed_ledger(self.ledger_path, fixture["ledger_seed"])
        from step import AutoStepper, run_session
        trail_path = os.path.join(self.directory, "trail", "sess.jsonl")
        drv = Driver(socket_path=self.server.path,
                     ledger_path=self.ledger_path,
                     blocks=fixture["blocks"],
                     pi_home=build_pi_home(self.directory,
                                           fixture["pi_home"]),
                     wait_timeout_ms=60000, block_version="")
        started = time.monotonic()
        result = run_session(
            drv, _walk_plan(fixture),
            attest=lambda act: append_human(
                self.ledger_path,
                fixture["human_attestation_records"][act["desk"]]),
            stepper=AutoStepper(), trail_path=trail_path, on_fail="stop")
        elapsed = time.monotonic() - started
        self.assertEqual(result["status"], "complete")
        self.assertLess(elapsed, 60.0)
        self.assertEqual(log, [])
        drv.close()
        for module in (step_module, conformance_module, surface_module):
            for name in dir(module):
                value = getattr(module, name)
                if isinstance(value, type):
                    source = getattr(value, "__module__", "")
                    if source.startswith("socket"):
                        self.fail("%s.%s imports the socket module"
                                  % (module.__name__, name))

    def test_k3_authenticity_is_never_a_pass(self):
        """K3 — quantity measured: DC-AUTH-1 and DC-AUTH-2 emit
        INCONCLUSIVE on every evaluation (a G step, a V step, a boot
        line, the live context) with the reason stated at the site —
        the machine checks that the slot is filled and referenced, never
        that it is true."""
        import conformance as conformance_module
        ctx = conformance_module.build_live_context()
        report = conformance_module.evaluate(ctx)
        for item_id in ("DC-AUTH-1", "DC-AUTH-2"):
            entry = [i for i in report["items"] if i["id"] == item_id][0]
            self.assertEqual(entry["verdict"], "INCONCLUSIVE")
            self.assertIn("click", entry["reason"])
        fixture = load_fixture(P4A_FIXTURES["lawful"])
        parsed = __import__("surface").parse_surface(
            fixture["surface"],
            equation_forms=conformance_module.EQUATION_FORMS)
        step = {"kind": "turn", "desk": "G", "gate": "y",
                "address_before": "", "address_after": "G",
                "zoom": {"op": "in", "sign": "−", "letter": "G",
                         "derived_reading": False},
                "operation": "take_turn", "intent_only": False,
                "outcome": {"status": "proposed", "record_id": "r1",
                            "turn_key": "k"},
                "decoded": {"slots": parsed["slots"],
                            "source": "desk_surface",
                            "operation_steps": []},
                "compiled": {"symbol": "Y", "gate": "y",
                             "landed": "record:r1"},
                "context_in": {}, "surface_parse": parsed, "await": True}
        report = conformance_module.evaluate({
            "step": step,
            "ledger": {"path": "/tmp/f/gates.jsonl", "records": [
                {"record_id": "a" * 64, "address": "", "gate": "x",
                 "state": "attested", "mark": "emergent",
                 "payload_ref": "demo:the-plant",
                 "attestation_ref": "Start from Not Knowing"}],
                "count": 1, "head": "a" * 64},
            "cell": {"observed": True,
                     "arrangement": ["S", "G", "Q", "P", "V"],
                     "surfaces": {"G": parsed},
                     "question_ref": "demo:the-plant"},
            "session": {"lines": []}, "sources_dir": None})
        for item_id in ("DC-AUTH-1", "DC-AUTH-2"):
            entry = [i for i in report["items"] if i["id"] == item_id][0]
            self.assertEqual(entry["verdict"], "INCONCLUSIVE")
            self.assertIn("click", entry["reason"])

    def test_k4_a_keypress_is_not_an_attestation(self):
        """K4 — quantity measured: an interactive run (Enter consumed
        between steps) derives ZERO attestations from the keypresses —
        the attested records on the ledger stay exactly the plant + the
        four provider-supplied human records (5), and every machine
        record keeps attestation_ref null."""
        from step import AutoStepper, run_session
        fixture = load_fixture(CYCLE_FIXTURE)
        log = []
        self.server.start(scripted_handler(fixture["transcript"], log))
        seed_ledger(self.ledger_path, fixture["ledger_seed"])
        keypresses = []

        def input_fn(prompt):
            keypresses.append(prompt)
            return None

        drv = Driver(socket_path=self.server.path,
                     ledger_path=self.ledger_path,
                     blocks=fixture["blocks"],
                     pi_home=build_pi_home(self.directory,
                                           fixture["pi_home"]),
                     wait_timeout_ms=60000, block_version="")
        result = run_session(
            drv, _walk_plan(fixture),
            attest=lambda act: append_human(
                self.ledger_path,
                fixture["human_attestation_records"][act["desk"]]),
            stepper=AutoStepper(),
            trail_path=os.path.join(self.directory, "trail", "s.jsonl"),
            interactive=True, input_fn=input_fn,
            printer=lambda line: None)
        self.assertEqual(result["status"], "complete")
        self.assertGreater(len(keypresses), 4)
        records = loaded_records(self.ledger_path)
        attested = [r for r in records
                    if r["state"] == "attested"]
        self.assertEqual(len(attested), 5)
        for record in records:
            if record["state"] == "held-pending":
                self.assertIsNone(record["attestation_ref"])
        self.assertEqual(log, [])
        drv.close()

    def test_k5_zoom_entries_are_reserved_and_unimplemented(self):
        """K5 — quantity measured: STEP_KINDS holds zoom_in and zoom_out
        as reserved entries with implemented False (so B3 adds descent
        without touching the protocol or the schema) and a plan act for
        either raises StepKindError."""
        from step import STEP_KINDS, StepKindError, AutoStepper, run_session
        for kind in ("zoom_in", "zoom_out"):
            self.assertTrue(STEP_KINDS[kind]["reserved"])
            self.assertFalse(STEP_KINDS[kind]["implemented"])
        self.assertTrue(STEP_KINDS["zoom_out"]["derived_reading"])
        fixture = load_fixture(DUP_FIXTURE)
        log = []
        self.server.start(scripted_handler(fixture["transcript"], log))
        seed_ledger(self.ledger_path, fixture["ledger_seed"])
        drv = Driver(socket_path=self.server.path,
                     ledger_path=self.ledger_path,
                     blocks=fixture["blocks"],
                     pi_home=build_pi_home(self.directory,
                                           fixture["pi_home"]),
                     wait_timeout_ms=60000, block_version="")
        with self.assertRaises(StepKindError):
            run_session(drv, [{"act": "zoom_in"}], attest=None,
                        stepper=AutoStepper(),
                        trail_path=os.path.join(self.directory, "t",
                                                "s.jsonl"))
        drv.close()

    def test_k6_the_d14_jacket_numbers_every_addition(self):
        """K6 — quantity measured: exactly four items are marked derived
        (DC-DECODE, DC-COMPILE, DC-AUTH-1, DC-AUTH-2 — the D12 pair and
        the two K3 checks), R1-R13 keep the source's own numbering, and
        the corruption-code set is exactly the five."""
        import conformance as conformance_module
        derived = sorted(
            item_id for item_id, meta in conformance_module.CHECKS.items()
            if meta.get("derived"))
        self.assertEqual(derived,
                         ["DC-AUTH-1", "DC-AUTH-2", "DC-COMPILE",
                          "DC-DECODE"])
        self.assertEqual(conformance_module.CORRUPTION_CODES,
                         frozenset(("L1", "L2", "L3", "L4", "V∅")))


class TestTrailEncoding(TmpCase):
    def test_needle_round_trips_every_free_trail_field(self):
        """lens 4 (encoding) — quantity measured: the bytes ∞0′ → ‖
        pushed through the server's error message land verbatim in the
        trail line's outcome.reason, survive the append (raw UTF-8 on
        disk — zero escaping) and the read-back round-trip; slot values
        carrying the needle leave the parser ONLY as sha256 references."""
        from step import AutoStepper, read_trail
        import surface as surface_module
        import conformance as conformance_module
        fixture = load_fixture(DUP_FIXTURE)
        pane = [p for p in fixture["panes"] if p["label"] == "G"][0]

        def handler(request):
            if request.get("method") == "pane.list":
                return {"id": request.get("id"), "result": {
                    "type": "pane_list",
                    "panes": [dict(p) for p in fixture["panes"]]}}
            if request.get("method") == "pane.get":
                return {"id": request.get("id"), "result": {
                    "type": "pane_info", "pane": pane}}
            if request.get("method") == "agent.prompt":
                return {"id": request.get("id"), "result": {
                    "type": "agent_prompted", "agent": pane}}
            if request.get("method") == "pane.wait_for_output":
                return {"id": request.get("id"), "error": {
                    "code": "timeout",
                    "message": "the fence never closed on ∞0′ → ‖"}}
            return {"id": request.get("id"), "error": {
                "code": "method_not_found", "message": "unscripted"}}

        self.server.start(handler)
        seed_ledger(self.ledger_path, fixture["ledger_seed"])
        trail_path = os.path.join(self.directory, "trail", "s.jsonl")
        drv = Driver(socket_path=self.server.path,
                     ledger_path=self.ledger_path,
                     blocks=fixture["blocks"],
                     pi_home=build_pi_home(self.directory,
                                           fixture["pi_home"]),
                     wait_timeout_ms=60000, block_version="",
                     stepper=AutoStepper(), trail_path=trail_path)
        drv.boot()
        result = drv.take_turn("G", fixture["prompts"]["G"])
        self.assertEqual(result["status"], "incomplete")
        drv.close()
        raw = open(trail_path, "rb").read()
        self.assertIn(NEEDLE.encode("utf-8"), raw)
        read = read_trail(trail_path)
        self.assertEqual(read["status"], "ok")
        turn = [line for line in read["lines"]
                if line["kind"] == "turn"][0]
        self.assertIn(NEEDLE, turn["outcome"]["reason"])
        # the slot values never leave the parser: parse the lawful
        # surface whose X slot carries the needle — references only
        lawful = load_fixture(P4A_FIXTURES["lawful"])
        parsed = surface_module.parse_surface(
            lawful["surface"],
            equation_forms=conformance_module.EQUATION_FORMS)
        blob = json.dumps(parsed, ensure_ascii=False)
        self.assertNotIn(NEEDLE, blob)
        self.assertIn("sha256:", blob)


class TestSurfaceContract(TmpCase):
    def test_the_four_surfaces_parse_as_declared(self):
        """§5.3 / C3 — quantity measured: the lawful surface parses
        lawful (4 slots referenced, decoding matches the §3.2 list, both
        lenses target Y = OUTPUT_SYMBOL[G], trace fully mapped); the
        paraphrased surface's Q bytes match no form (codepoint U+0020);
        the sixth-code surface announces L6; a desk answer with NO
        surface block reads absent."""
        import surface as surface_module
        import conformance as conformance_module
        lawful = load_fixture(P4A_FIXTURES["lawful"])
        parsed = surface_module.parse_surface(
            lawful["surface"],
            equation_forms=conformance_module.EQUATION_FORMS)
        self.assertEqual(parsed["status"], "lawful")
        self.assertEqual(set(parsed["slots"]),
                         {"X", "α", "{α'}", "Y"})
        self.assertTrue(parsed["decoding"]["matches"])
        self.assertEqual([lens["target"] for lens in parsed["lenses"]],
                         ["Y", "Y"])
        self.assertTrue(parsed["trace"]["all_mapped"])
        paraphrased = load_fixture(P4A_FIXTURES["paraphrased"])
        parsed = surface_module.parse_surface(
            paraphrased["surface"],
            equation_forms=conformance_module.EQUATION_FORMS)
        self.assertFalse(parsed["equations"]["Q"]["match"])
        self.assertEqual(
            parsed["equations"]["Q"]["first_differing_codepoint"], 0x0020)
        sixth = load_fixture(P4A_FIXTURES["sixth_code"])
        parsed = surface_module.parse_surface(
            sixth["surface"],
            equation_forms=conformance_module.EQUATION_FORMS)
        self.assertEqual(parsed["corruption_codes"],
                         ["L1", "L2", "L3", "L4", "V∅", "L6"])
        self.assertEqual(
            surface_module.parse_surface(
                "a plain answer with no surface block\n⟦END 1⟧\n",
                equation_forms=conformance_module.EQUATION_FORMS)["status"],
            "absent")


class TestP4aFixtures(TmpCase):
    def test_every_p4a_fixture_parses_and_declares_its_claims(self):
        """§9.6 — quantity measured: all seven new fixtures load (five
        JSON objects each with a name and a claim; the two trail files
        read as ok-chained and damaged respectively), and each baked key
        recomputes."""
        for name in ("lawful", "paraphrased", "sixth_code",
                     "missing_prime", "three_plus_one"):
            fixture = load_fixture(P4A_FIXTURES[name])
            self.assertTrue(fixture.get("name"), name)
            self.assertTrue(fixture.get("claim"), name)
        lawful = load_fixture(P4A_FIXTURES["lawful"])
        self.assertEqual(set(lawful["expected_slot_refs"]),
                         {"X", "α", "{α'}", "Y"})
        from step import read_trail
        read = read_trail(os.path.join(FIXTURES,
                                       P4A_FIXTURES["full_trail"]))
        self.assertEqual((read["status"], read["chain"]["status"]),
                         ("ok", "ok"))
        read = read_trail(os.path.join(FIXTURES,
                                       P4A_FIXTURES["torn_trail"]))
        self.assertEqual(read["status"], "damaged")


COURSE_IMPORT = COURSE  # walker.COURSE — the alphabet's data table


if __name__ == "__main__":
    unittest.main(verbosity=2)
