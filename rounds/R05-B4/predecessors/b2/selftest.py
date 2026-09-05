#!/usr/bin/env python3
"""selftest — R03 · B2 (the driver), author-side checks.

Every test names, in its first docstring line, the criterion ID it
exercises (C1–C4, K1–K5; where a commission rule is the subject the
section is named) and the quantity it measures; a test that timed
something would name the operation timed — none does, on purpose: every
fence answer is scripted, no sleeping anywhere.

The fake herdr server binds its OWN AF_UNIX socket inside a
tempfile-created directory and replays the fixtures/ transcripts — the
live herdr socket is never touched, every ledger path is inside a
tempfile-created directory (never the attested plant), and the Pi home
is a tempfile directory built from the fixture (the real ~/.pi is never
read or written).  The fake server speaks the live dialect (commission
§3.1 / R03 §6.3): string-only request ids — a non-string id is refused
with {"id": "", "error": {"code": "invalid_request", …}} before
dispatch — and the write-response shapes it serves are the fixture's
declared claims (H-B2-4), never reported as observed.

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
