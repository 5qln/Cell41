#!/usr/bin/env python3
"""selftest — the bridge (live desk adapter + runtime config-read),
author-side checks.

Every test names, in its first docstring line, the criterion ID (or the
commission rule) it exercises and the quantity it measures.  These are
HYPOTHESES — the author's predictions, never results: the verifier
executes the artifact and recomputes every one of them with its own
implementation.

Fixture apparatus lives under fixtures/ (the fixture live-server
speaking the real herdr dialect, the byte-pinned live-mode runs, the
soft-config override and the malformed/partial/empty/wrong-type files,
the cold-restart harness).  Scratch runs use tempfile directories and
the fixed fixture clock; the live ledger, the live formation trail and
the live herdr socket are never written (the one live-socket touch is a
READ-ONLY probe that skips — INCONCLUSIVE — when the box is down).

Run:  python3 selftest.py
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

# Never leave a bytecode cache beside a predecessor file (the pinned
# loads import by path; the workspace outside ./authored/ stays
# untouched).
sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.environ.get("FRACTAL_LEDGER_DIR",
                                  "/home/deploy/the-cell/ledger"))

import fixtures.build as build  # noqa: E402
import fixtures.live_server as live_server_module  # noqa: E402
import run as run_module  # noqa: E402
import cost as cost_module  # noqa: E402
import softconfig as softconfig_module  # noqa: E402
import surface_contract  # noqa: E402
from run import Conductor, audit_payload_chains  # noqa: E402
from surface_contract import (  # noqa: E402
    AgentNotFoundError,
    CentreWriteError,
    DeskResolutionError,
    HerdrError,
    Instrument,
    assert_not_centre,
    compose_answer,
    fence_marker,
    grammar,
    parse_surface,
    turn_key,
)
from fractal_ledger import (  # noqa: E402
    LedgerLoader,
    LedgerVerificationError,
    LedgerWriter,
)

FIXTURES = os.path.join(HERE, "fixtures")
LIVE_RUN = os.path.join(FIXTURES, "live_run")
RESTART = os.path.join(FIXTURES, "restart")
SOFT_CONFIG = os.path.join(FIXTURES, "soft_config")
B4 = os.path.normpath(os.path.join(HERE, "..", "predecessors", "b4"))

NEEDLE = "∞0′ → ‖"  # the encoding-lens bytes (commission lens 4)
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()


def read_bytes(path):
    with open(path, "rb") as handle:
        return handle.read()


def read_json_lines(path):
    with open(path, encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def ledger_records(path):
    return LedgerLoader(path).load(write_index=False).records


def scratch_dir(prefix):
    return tempfile.mkdtemp(prefix=prefix)


def b4_case(case, mode=None, max_actions=None, soft_config=None):
    """Run one B4 fixture spec with the bridge conductor under B4's
    canonical relative work path (the trail bytes carry the ledger path
    string — byte-comparability needs the same string) and return
    (ledger_path, trail_path, result)."""
    work = os.path.join("fixtures", case, "work")
    if os.path.exists(work):
        shutil.rmtree(work)
    os.makedirs(work)
    spec = build.read_spec(os.path.join(
        B4, "fixtures", case, "spec.json"))
    if soft_config is not None:
        spec["soft_config"] = soft_config
    ledger = os.path.join(work, "gates.jsonl")
    trailp = os.path.join(work, "trail.jsonl")
    build.b4_build.write_plant(ledger)
    conductor = Conductor(ledger, trailp, spec,
                          socket_dir=os.path.join(work, "sock"),
                          mode=mode, max_actions=max_actions)
    result = conductor.run()
    conductor.close()
    return ledger, trailp, result


def non_docstring_strings(path):
    """Every string constant in the module OUTSIDE docstrings — the
    control-flow bytes (docstring mentions are commentary, exempt —
    B4's precedent)."""
    with open(path, encoding="utf-8") as handle:
        source = handle.read()
    tree = ast.parse(source)
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef,
                             ast.AsyncFunctionDef, ast.ClassDef)):
            body = getattr(node, "body", [])
            if (body and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                docstrings.add(id(body[0].value))
    strings = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) \
                and id(node) not in docstrings:
            strings.append(node.value)
    return strings


class TestC1LiveDeskMode(unittest.TestCase):
    """C1 — the live desk mode: a turn speaks the REAL herdr dialect
    through the imported B2 Instrument — resolve by pane label,
    agent.prompt to the resolved pane, fenced read; no fixture process
    is spawned."""

    def test_live_open_turn_returns_the_live_socket_with_no_process(self):
        directory = scratch_dir("bridge-livectx-")
        try:
            adapter = cost_module.DeskAdapter(
                {"cells": ["G"]}, os.path.join(directory, "sock"),
                mode="live", live_socket="/tmp/none-here.sock")
            context = adapter.open_turn("G", 0, "G")
            self.assertEqual(context.socket_path, "/tmp/none-here.sock")
            self.assertIsNone(context.process)
            self.assertEqual(context.memory_bytes(), 0)
            adapter.close_turn(context)  # a no-op — nothing to stop
            # no fixture process, no fixture socket: the socket dir holds
            # only the spec scratch file
            names = sorted(os.listdir(os.path.join(directory, "sock")))
            self.assertEqual(names, ["desk-spec.json"])
            adapter.close()
        finally:
            shutil.rmtree(directory, ignore_errors=True)

    def test_live_socket_path_resolution_order(self):
        # override > HERDR_SOCKET_PATH > the declared default (C1,
        # commission §3)
        saved = os.environ.get("HERDR_SOCKET_PATH")
        try:
            os.environ["HERDR_SOCKET_PATH"] = "/tmp/env-herdr.sock"
            self.assertEqual(
                cost_module.live_socket_path(), "/tmp/env-herdr.sock")
            self.assertEqual(
                cost_module.live_socket_path("/tmp/arg-herdr.sock"),
                "/tmp/arg-herdr.sock")
            os.environ["HERDR_SOCKET_PATH"] = ""
            self.assertEqual(
                cost_module.live_socket_path(),
                os.path.expanduser("~/.config/herdr/herdr.sock"))
        finally:
            if saved is None:
                os.environ.pop("HERDR_SOCKET_PATH", None)
            else:
                os.environ["HERDR_SOCKET_PATH"] = saved

    def test_live_turn_speaks_the_real_dialect_through_the_instrument(self):
        # one prompt to G on the fixture live box: label resolution
        # (pane.list), the centre guard's pane.get, the §4.3 label
        # assertion, agent.prompt to w8:p3, then the fenced read —
        # exactly the imported B2 path, never re-implemented
        directory = scratch_dir("bridge-dialect-")
        try:
            spec = build.read_spec(os.path.join(LIVE_RUN, "spec.json"))
            path = os.path.join(directory, "live.sock")
            server = live_server_module.LiveServer(spec, path)
            server.start()
            try:
                instrument = Instrument(socket_path=path)
                key = turn_key("GQ", "y", "cycle:0", "")
                read = instrument.prompt_desk(
                    "G",
                    "⟦TURN cell=G cycle=0 desk=G⟧\nprobe prompt",
                    key, timeout_ms=5000)
                instrument.close()
            finally:
                server.halt()
            self.assertIn(fence_marker(key), read["text"])
            self.assertTrue(read["text"].startswith(
                "⟦ATTENTION MODE — fixture stand-in"))
            methods = server.methods
            self.assertEqual(methods[0], "pane.list")
            self.assertEqual(methods[-1], "pane.wait_for_output")
            prompt = next(r for r in server.requests
                          if r.get("method") == "agent.prompt")
            self.assertEqual(prompt["params"]["target"], "w8:p3")
            self.assertIn("probe prompt",
                          server.prompts["w8:p3"])
            self.assertIn(fence_marker(key),
                          server.prompts["w8:p3"])
        finally:
            shutil.rmtree(directory, ignore_errors=True)

    def test_desk_resolution_by_label_skips_unlabelled_panes(self):
        directory = scratch_dir("bridge-resolve-")
        try:
            spec = build.read_spec(os.path.join(LIVE_RUN, "spec.json"))
            path = os.path.join(directory, "live.sock")
            server = live_server_module.LiveServer(spec, path)
            server.start()
            try:
                instrument = Instrument(socket_path=path)
                desks = instrument.desks()
                instrument.close()
            finally:
                server.halt()
            self.assertEqual(desks, {"S": "w8:p2", "G": "w8:p3",
                                     "Q": "w8:p5", "P": "w8:p6",
                                     "V": "w8:p4"})
            # the unrelated w7:p1 pane was never indexed (label null)
            self.assertNotIn("w7:p1", desks.values())
        finally:
            shutil.rmtree(directory, ignore_errors=True)

    def test_centre_guard_refuses_s_before_any_byte(self):
        # K4 / T-R3-02: prompt_desk to S raises BEFORE any byte reaches
        # the socket — the server never even sees a connection
        directory = scratch_dir("bridge-guard-")
        try:
            spec = build.read_spec(os.path.join(LIVE_RUN, "spec.json"))
            path = os.path.join(directory, "live.sock")
            server = live_server_module.LiveServer(spec, path)
            server.start()
            try:
                instrument = Instrument(socket_path=path)
                with self.assertRaises(CentreWriteError):
                    instrument.prompt_desk(
                        "S", "probe", turn_key("GS", "x", "c", ""))
                instrument.close()
            finally:
                server.halt()
            self.assertEqual(server.connections, 0)
            self.assertEqual(server.requests, [])
            with self.assertRaises(CentreWriteError):
                assert_not_centre(None)  # unresolvable target refused too
        finally:
            shutil.rmtree(directory, ignore_errors=True)

    def test_no_desk_server_spawn_in_live_mode(self):
        # the live branch of cost.open_turn contains no spawn, and a
        # whole live run leaves no fixture .sock behind (C2)
        source = open(os.path.join(HERE, "cost.py"),
                      encoding="utf-8").read()
        tree = ast.parse(source)
        live_branch = None
        for node in ast.walk(tree):
            if (isinstance(node, ast.If)
                    and isinstance(node.test, ast.Compare)
                    and isinstance(node.test.left, ast.Attribute)):
                if (node.test.left.attr == "mode"
                        and any(isinstance(c, ast.Constant)
                                and c.value == "live"
                                for c in node.test.comparators)):
                    live_branch = node
        self.assertIsNotNone(live_branch)
        branch_src = ast.get_source_segment(source, live_branch)
        self.assertNotIn("_spawn", branch_src)
        self.assertNotIn("desk_server", branch_src)
        self.assertNotIn("Popen", branch_src)
        # runtime: the pinned live run leaves only its own socket files
        report = subprocess.run(
            [sys.executable, os.path.join(LIVE_RUN, "run_live.py")],
            cwd=HERE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=900)
        self.assertEqual(report.returncode, 0,
                         report.stderr.decode("utf-8", "replace"))
        payload = json.loads(report.stdout.decode("utf-8"))
        self.assertEqual(payload["status"], "pinned")
        shutil.rmtree(os.path.join(LIVE_RUN, "work-box"),
                      ignore_errors=True)
        shutil.rmtree(os.path.join(LIVE_RUN, "work-all"),
                      ignore_errors=True)
        shutil.rmtree(os.path.join(LIVE_RUN, "work-absent"),
                      ignore_errors=True)


class TestC2LiveFailsClosed(unittest.TestCase):
    """C2 — live mode fails closed, never into a fixture (lens 6): an
    absent socket holds as outage, a no-agent desk holds as blocked —
    never a fake answer, never clean."""

    def test_absent_socket_holds_outage_and_never_completes(self):
        directory = scratch_dir("bridge-absent-")
        try:
            spec = build.read_spec(os.path.join(LIVE_RUN, "spec.json"))
            spec["live_socket"] = live_server_module.absent_socket_path(
                directory)
            ledger = os.path.join(directory, "gates.jsonl")
            trailp = os.path.join(directory, "trail.jsonl")
            build.b4_build.write_plant(ledger)
            conductor = Conductor(ledger, trailp, spec,
                                  socket_dir=os.path.join(directory, "s"))
            result = conductor.run()
            conductor.close()
            self.assertEqual(result["status"], "stalled")  # never clean
            records = ledger_records(ledger)
            fenced = [r for r in records
                      if (r.get("payload_ref") or "").startswith(
                          "fenced:")]
            self.assertEqual(fenced, [])  # never a fake answer
            holds = [r for r in records
                     if (r.get("payload_ref") or "").startswith(
                         "hold:outage:SocketTransportError:")]
            self.assertTrue(holds)
            for hold in holds:
                self.assertEqual(hold["state"], "held-pending")
                self.assertIsNone(hold["attestation_ref"])
            # the absence never read valid: no fenced digest, no clean
            # verdict — and the fixture desk server never spawned
            self.assertFalse(os.path.exists(os.path.join(
                directory, "s", "turn-1-G.sock")))
            # the same scenario is the pinned absent variant of the
            # live-run fixture (C2's other half, byte for byte)
            with open(os.path.join(
                    LIVE_RUN, "expected", "run-result-absent.json"),
                    encoding="utf-8") as handle:
                absent = json.loads(handle.read())
            self.assertEqual(absent["result"]["status"], "stalled")
            pinned_records = ledger_records(os.path.join(
                LIVE_RUN, "expected", "gates-absent.jsonl"))
            pinned_fenced = [r for r in pinned_records
                             if (r.get("payload_ref") or "").startswith(
                                 "fenced:")]
            self.assertEqual(pinned_fenced, [])
            self.assertTrue(any(
                (r.get("payload_ref") or "").startswith(
                    "hold:outage:SocketTransportError:")
                for r in pinned_records))
        finally:
            shutil.rmtree(directory, ignore_errors=True)

    def test_no_agent_desk_holds_blocked_with_agent_not_found(self):
        # the live-box-shaped fixture: G answers (the fence read), Q
        # holds blocked agent_not_found — exactly the pinned bytes
        lines = read_json_lines(os.path.join(
            LIVE_RUN, "expected", "trail-box.jsonl"))
        holds = [line for line in lines
                 if line.get("event") == "hold"]
        self.assertEqual(len(holds), 2)
        for hold in holds:
            self.assertEqual(hold["content"]["kind"], "blocked")
            self.assertEqual(hold["content"]["detail"],
                             "agent_not_found")
        turns = [line for line in lines
                 if line.get("event") == "turn"]
        self.assertEqual(len(turns), 2)  # G's two fenced reads
        for turn in turns:
            self.assertEqual(turn["phase"], "G")
        records = ledger_records(os.path.join(
            LIVE_RUN, "expected", "gates-box.jsonl"))
        blocked = [r for r in records
                   if (r.get("payload_ref") or "").startswith(
                       "hold:blocked:agent_not_found:")]
        self.assertEqual(len(blocked), 2)
        # the agent_not_found turns never produced a stand-in answer:
        # the fixture server answered agent_not_found, and no composed
        # answer bytes exist for any pane but G
        with open(os.path.join(
                LIVE_RUN, "expected", "run-result-box.json"),
                encoding="utf-8") as handle:
            summary = json.loads(handle.read())
        self.assertGreaterEqual(
            summary["server"]["agent_not_found_errors"], 2)
        self.assertEqual(summary["server"]["prompt_targets"], ["w8:p3"])

    def test_the_whole_live_run_holds_end_to_end(self):
        # lens 2 over the live run: the pinned box run ends STALLED with
        # the holds still held — the invariant holds across the whole
        # run, not per call
        run_end = [line for line in read_json_lines(os.path.join(
            LIVE_RUN, "expected", "trail-box.jsonl"))
            if line.get("event") == "run-end"][0]
        self.assertEqual(run_end["content"]["status"], "stalled")
        self.assertEqual(len(run_end["content"]["holds"]), 2)
        self.assertEqual(run_end["content"]["completed_cycles"], 0)
        with open(os.path.join(
                LIVE_RUN, "expected", "run-result-box.json"),
                encoding="utf-8") as handle:
            result = json.loads(handle.read())
        self.assertEqual(result["result"]["status"], "stalled")

    def test_fully_constituted_fixture_completes_through_the_dialect(self):
        # the declared fixture fiction: every walked desk answers — the
        # whole live path completes, V's ∞0′ seeds the next S through
        # the live source-reference rule (the seed carries the previous
        # V turn's fenced payload_ref — re-derived from the ledger
        # alone, C7)
        with open(os.path.join(
                LIVE_RUN, "expected", "run-result-all.json"),
                encoding="utf-8") as handle:
            result = json.loads(handle.read())
        self.assertEqual(result["result"]["status"], "complete")
        self.assertEqual(
            sorted(result["server"]["prompt_targets"]),
            ["w8:p3", "w8:p4", "w8:p5", "w8:p6"])
        lines = read_json_lines(os.path.join(
            LIVE_RUN, "expected", "trail-all.jsonl"))
        seeds = [line for line in lines
                 if line.get("event") == "seed" and line["cycle"] > 0]
        self.assertTrue(seeds)
        for seed in seeds:
            self.assertTrue(seed["return_question"].startswith(
                "fenced:sha256:"))
            self.assertTrue(seed["content"]["source_ref"].startswith(
                "fenced:sha256:"))
        run_end = [line for line in lines
                   if line.get("event") == "run-end"][0]
        self.assertEqual(run_end["content"]["completed_cycles"],
                         run_end["content"]["cycle_target"])


class TestC3RuntimeConfigRead(unittest.TestCase):
    """C3 — the runtime config-read: each desk's §2 emphasis, voice,
    model and the budget read from the soft layer at runtime; the
    conductor's prompt and budget paths read through it."""

    def test_softconfig_reads_defaults_when_absent(self):
        view = softconfig_module.load_soft_config(
            os.path.join(scratch_dir("bridge-none-"), "none.json"))
        self.assertEqual(view["status"], "defaults")
        self.assertIsNotNone(view["config"])
        self.assertIn("no soft config file", view["reason"])

    def test_softconfig_reads_a_complete_override(self):
        view = softconfig_module.load_soft_config(
            os.path.join(SOFT_CONFIG, "good.json"))
        self.assertEqual(view["status"], "ok")
        self.assertEqual(
            softconfig_module.desk_voice(view, "G"),
            "SOFT LAYER (fixture) voice G — " + NEEDLE)
        self.assertEqual(
            softconfig_module.desk_model(view, "G"),
            "SOFT LAYER (fixture) model G")
        emphasis = softconfig_module.desk_emphasis(view, "G")
        self.assertTrue(all(NEEDLE in line for line in emphasis))
        self.assertEqual(softconfig_module.budget_of(
            view, "re-prompted", "G"), 1234)
        self.assertEqual(softconfig_module.default_mode(view),
                         "re-prompted")

    def test_softconfig_defaults_are_b4s_exact_bytes(self):
        # C4's declared-defaults half, byte-exact: the softconfig
        # defaults ARE the pinned B4 folded-item bytes and the
        # COST_MODEL values — never re-authored, never normalised (K2)
        for desk in "SGQPV":
            self.assertEqual(
                tuple(softconfig_module.SOFT_DEFAULTS["desks"][desk][
                    "emphasis"]),
                surface_contract.DESK_FUNCTION_SPECS[desk])
            self.assertEqual(
                softconfig_module.SOFT_DEFAULTS["desks"][desk]["voice"],
                surface_contract.ATTENTION_READINGS[desk])
        self.assertEqual(
            softconfig_module.SOFT_DEFAULTS["budget"]["default_mode"],
            cost_module.COST_MODEL["default_mode"])
        self.assertEqual(
            softconfig_module.SOFT_DEFAULTS["budget"]["charges"],
            cost_module.COST_MODEL["charges"])
        self.assertEqual(
            softconfig_module.SOFT_DEFAULTS["desks"]["G"]["model"],
            softconfig_module.DECLARED_MODEL)

    def test_the_override_changes_the_runtime_read_end_to_end(self):
        # the B4 main spec + the soft override: the prompt reads the
        # soft emphasis/voice/model, the budget reads the soft charges —
        # the LEDGER stays byte-identical to B4's pins (the desk
        # answers never depended on the prompt), while the trail's
        # spend reflects the override and the trail bytes changed
        ledger, trailp, result = b4_case(
            "main_run", soft_config=os.path.join(
                SOFT_CONFIG, "good.json"))
        self.assertEqual(result["status"], "complete")
        with open(os.path.join(B4, "fixtures", "main_run", "expected",
                               "gates.jsonl"), "rb") as handle:
            pinned_ledger = handle.read()
        with open(os.path.join(B4, "fixtures", "main_run", "expected",
                               "trail.jsonl"), "rb") as handle:
            pinned_trail = handle.read()
        self.assertEqual(read_bytes(ledger), pinned_ledger)
        lines = read_json_lines(trailp)
        actual_trail = read_bytes(trailp)
        records = ledger_records(ledger)
        run_end = [line for line in lines
                   if line.get("event") == "run-end"][0]
        shutil.rmtree(os.path.join("fixtures", "main_run", "work"),
                      ignore_errors=True)
        soft_charges = build.good_soft_config()["budget"]["charges"][
            "re-prompted"]
        spend = 0
        for record in records:
            payload = record.get("payload_ref") or ""
            if not payload.startswith("fenced:"):
                continue
            desk = {"y": "G", "z": "Q", "a": "P", "b": "V"}[
                record["gate"]]
            spend += soft_charges[desk]
        self.assertEqual(run_end["content"]["spend"], spend)
        self.assertNotEqual(actual_trail, pinned_trail)

    def test_the_prompt_reads_through_softconfig(self):
        directory = scratch_dir("bridge-prompt-")
        try:
            spec = build.read_spec(os.path.join(
                B4, "fixtures", "main_run", "spec.json"))
            spec["soft_config"] = os.path.join(SOFT_CONFIG, "good.json")
            conductor = Conductor(
                os.path.join(directory, "g.jsonl"),
                os.path.join(directory, "t.jsonl"), spec,
                socket_dir=os.path.join(directory, "s"))
            key = turn_key("GG", "y", "cycle:0", "")
            prompt = conductor._prompt_text("", 0, "G",
                                            "sha256:probe", key)
            conductor.close()
            for fragment in (
                    "SOFT LAYER (fixture) voice G — " + NEEDLE,
                    "SOFT LAYER (fixture) emphasis G op 1 — " + NEEDLE,
                    "MODEL — SOFT LAYER (fixture) model G"):
                self.assertIn(fragment, prompt)
            # the needle rides the raw prompt bytes (lens 4)
            self.assertIn(NEEDLE.encode("utf-8"),
                          prompt.encode("utf-8"))
            # absent soft config + fixture mode: B4's exact prompt — no
            # model line ever existed there (C4/C6)
            spec2 = build.read_spec(os.path.join(
                B4, "fixtures", "main_run", "spec.json"))
            conductor2 = Conductor(
                os.path.join(directory, "g2.jsonl"),
                os.path.join(directory, "t2.jsonl"), spec2,
                socket_dir=os.path.join(directory, "s2"))
            default_prompt = conductor2._prompt_text(
                "", 0, "G", "sha256:probe", key)
            conductor2.close()
            self.assertNotIn("MODEL —", default_prompt)
        finally:
            shutil.rmtree(directory, ignore_errors=True)

    def test_the_mode_default_reads_through_softconfig(self):
        directory = scratch_dir("bridge-mode-")
        try:
            config_path = os.path.join(directory, "soft.json")
            config = build.good_soft_config()
            config["budget"]["default_mode"] = "sub-process"
            with open(config_path, "w", encoding="utf-8") as handle:
                handle.write(json.dumps(config, ensure_ascii=False,
                                        sort_keys=True))
            spec = build.read_spec(os.path.join(
                B4, "fixtures", "main_run", "spec.json"))
            spec["soft_config"] = config_path
            conductor = Conductor(
                os.path.join(directory, "g.jsonl"),
                os.path.join(directory, "t.jsonl"), spec,
                socket_dir=os.path.join(directory, "s"))
            self.assertEqual(conductor.mode, "sub-process")
            conductor.close()
            # live mode resolves the same way in the restart fixture:
            # the spec declares none, the soft default_mode is "live"
            restart_spec = build.read_spec(os.path.join(
                RESTART, "spec.json"))
            self.assertIsNone(restart_spec["mode"])
            view = softconfig_module.load_soft_config(
                restart_spec["soft_config"])
            self.assertEqual(softconfig_module.default_mode(view),
                             "live")
        finally:
            shutil.rmtree(directory, ignore_errors=True)

    def test_the_live_prompt_carries_the_model(self):
        # in live mode the model read is observable in the prompt (a
        # new mode — no attested bytes to preserve); absent soft config
        # the declared single model rides it
        directory = scratch_dir("bridge-livemodel-")
        try:
            spec = build.read_spec(os.path.join(LIVE_RUN, "spec.json"))
            spec["live_socket"] = os.path.join(directory, "x.sock")
            conductor = Conductor(
                os.path.join(directory, "g.jsonl"),
                os.path.join(directory, "t.jsonl"), spec,
                socket_dir=os.path.join(directory, "s"))
            key = turn_key("GG", "y", "cycle:0", "")
            prompt = conductor._prompt_text("", 0, "G",
                                            "sha256:probe", key)
            conductor.close()
            self.assertIn("MODEL — " + softconfig_module.DECLARED_MODEL,
                          prompt)
        finally:
            shutil.rmtree(directory, ignore_errors=True)

    def test_phase_table_bytes_flow_byte_exact(self):
        # K2: the enumerated P4b PHASE bytes ride the soft layer
        # verbatim — the Natural Intersection stays ⋂ (U+22C2), never
        # normalised to ∩ (renaming an L1 symbol)
        directory = scratch_dir("bridge-k2-")
        try:
            config = build.good_soft_config()
            config["desks"]["Q"]["voice"] = grammar.PHASE["Q"]["seat"]
            config["desks"]["Q"]["emphasis"] = [
                grammar.PHASE["Q"]["phase_gate"]] + list(
                    grammar.PHASE["Q"]["decoding"])
            config_path = os.path.join(directory, "soft.json")
            with open(config_path, "w", encoding="utf-8") as handle:
                handle.write(json.dumps(config, ensure_ascii=False,
                                        sort_keys=True))
            spec = build.read_spec(os.path.join(
                B4, "fixtures", "main_run", "spec.json"))
            spec["soft_config"] = config_path
            conductor = Conductor(
                os.path.join(directory, "g.jsonl"),
                os.path.join(directory, "t.jsonl"), spec,
                socket_dir=os.path.join(directory, "s"))
            key = turn_key("GQ", "z", "cycle:0", "")
            prompt = conductor._prompt_text("", 0, "Q",
                                            "sha256:probe", key)
            conductor.close()
            self.assertIn(grammar.PHASE["Q"]["seat"], prompt)
            self.assertIn(grammar.PHASE["Q"]["phase_gate"], prompt)
            self.assertIn("⋂", prompt)  # U+22C2, byte-exact
            self.assertNotIn("∩", prompt)  # U+2229 — never normalised
        finally:
            shutil.rmtree(directory, ignore_errors=True)


class TestC4DefaultsFailClosed(unittest.TestCase):
    """C4 — declared defaults, fail-closed (lens 3): absent soft config
    resolves B4's exact bytes; empty / malformed / partial / wrong-typed
    reads INCONCLUSIVE with the reason, never a silently substituted
    value."""

    def test_absent_config_fixture_run_is_b4_byte_identical(self):
        # the strongest C4/C6 measure: B4's three fixture runs under the
        # bridge conductor, byte for byte, absent any soft config
        for case, wanted in (("main_run", "complete"),
                             ("hold", "stalled"),
                             ("budget", "budget-held")):
            ledger, trailp, result = b4_case(case)
            self.assertEqual(result["status"], wanted, case)
            self.assertEqual(
                read_bytes(ledger),
                read_bytes(os.path.join(B4, "fixtures", case,
                                        "expected", "gates.jsonl")),
                case)
            self.assertEqual(
                read_bytes(trailp),
                read_bytes(os.path.join(B4, "fixtures", case,
                                        "expected", "trail.jsonl")),
                case)
            shutil.rmtree(os.path.join("fixtures", case, "work"),
                          ignore_errors=True)

    def test_empty_config_reads_inconclusive_never_valid(self):
        view = softconfig_module.load_soft_config(
            os.path.join(SOFT_CONFIG, "empty.json"))
        self.assertEqual(view["status"], "inconclusive")
        self.assertIsNone(view["config"])
        self.assertIn("EMPTY", view["reason"])
        self.assertIn(EMPTY_SHA256, view["reason"])  # sha256 of empty
        self.assertNotEqual(view["reason"], "")

    def test_malformed_and_partial_and_wrong_typed_read_inconclusive(self):
        for name, fragment in (
                ("malformed.json", "not valid JSON"),
                ("partial.json", "missing desk(s): V"),
                ("wrong_type.json", "desks.G.voice")):
            view = softconfig_module.load_soft_config(
                os.path.join(SOFT_CONFIG, name))
            self.assertEqual(view["status"], "inconclusive", name)
            self.assertIsNone(view["config"], name)
            self.assertIn(fragment, view["reason"], name)
            self.assertIn("INCONCLUSIVE", view["reason"], name)

    def test_inconclusive_config_refuses_the_run_with_the_reason(self):
        # the conductor refuses to boot on an inconclusive soft config —
        # the reason is recorded in the error, never a substitution
        directory = scratch_dir("bridge-boot-")
        try:
            for name in ("malformed.json", "partial.json", "empty.json",
                         "wrong_type.json"):
                spec = build.read_spec(os.path.join(
                    B4, "fixtures", "main_run", "spec.json"))
                spec["soft_config"] = os.path.join(SOFT_CONFIG, name)
                with self.assertRaises(run_module.BootError) as caught:
                    Conductor(
                        os.path.join(directory, "g.jsonl"),
                        os.path.join(directory, "t.jsonl"), spec,
                        socket_dir=os.path.join(directory, "s"))
                self.assertIn("INCONCLUSIVE", str(caught.exception))
                self.assertIn("never a silently substituted value",
                              str(caught.exception))
            # nothing ran, nothing was written
            self.assertFalse(os.path.exists(os.path.join(
                directory, "g.jsonl")))
        finally:
            shutil.rmtree(directory, ignore_errors=True)

    def test_non_utf8_config_reads_inconclusive(self):
        directory = scratch_dir("bridge-utf8-")
        try:
            path = os.path.join(directory, "soft.json")
            with open(path, "wb") as handle:
                handle.write(b"\xff\xfe\x00{")
            view = softconfig_module.load_soft_config(path)
            self.assertEqual(view["status"], "inconclusive")
            self.assertIn("not valid UTF-8", view["reason"])
        finally:
            shutil.rmtree(directory, ignore_errors=True)

    def test_budget_defaults_and_charges_match_b4(self):
        view = softconfig_module.load_soft_config(
            os.path.join(scratch_dir("bridge-b4-"), "none.json"))
        self.assertEqual(view["status"], "defaults")
        self.assertEqual(
            softconfig_module.default_mode(view),
            cost_module.DEFAULT_MODE)
        for mode in ("sub-process", "re-prompted", "live"):
            for desk in "GQPV":
                self.assertEqual(
                    softconfig_module.budget_of(view, mode, desk),
                    cost_module.charge_for(mode, desk))


class TestC5ImportNeverReauthor(unittest.TestCase):
    """C5 — import, never re-author (D14 loyalty): the predecessors are
    imported by path, sha-pinned; no re-implemented dialect, no new
    corruption code."""

    def test_every_pin_matches_its_file(self):
        for pinned in surface_contract.PINNED_FILES:
            actual = hashlib.sha256(
                read_bytes(pinned["path"])).hexdigest()
            self.assertEqual(actual, pinned["sha256"],
                             pinned["path"])
            self.assertFalse(pinned["sha256"].startswith("TBD"))

    def test_a_drifted_pin_refuses_the_import(self):
        # the loader's fail-closed behaviour, exercised on a scratch
        # file: drifted bytes raise, never silently substitute (lens 6)
        directory = scratch_dir("bridge-pindrift-")
        try:
            path = os.path.join(directory, "drift.py")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("X = 1\n")
            pinned = {"path": path, "sha256": EMPTY_SHA256}
            with self.assertRaises(ImportError):
                surface_contract._load_pinned(pinned, "drift_mod")
        finally:
            shutil.rmtree(directory, ignore_errors=True)

    def test_ledger_imported_via_fractal_ledger_dir_never_copied(self):
        import fractal_ledger
        ledger_dir = os.environ.get(
            "FRACTAL_LEDGER_DIR", "/home/deploy/the-cell/ledger")
        self.assertTrue(os.path.abspath(fractal_ledger.__file__)
                        .startswith(os.path.abspath(ledger_dir)))
        self.assertFalse(os.path.exists(os.path.join(
            HERE, "fractal_ledger.py")))

    def test_no_reimplemented_dialect_or_new_corruption_codes(self):
        # the conductor and the config-read never touch a socket or a
        # corruption table: the dialect and the D.12 checks are the
        # imported ones (K1 / D14)
        for module in ("run.py", "softconfig.py"):
            with open(os.path.join(HERE, module),
                      encoding="utf-8") as handle:
                source = handle.read()
            self.assertNotIn("import socket", source, module)
            self.assertNotIn("sendall", source, module)
            self.assertNotIn("recv(", source, module)
            self.assertNotIn("AF_UNIX", source, module)
        self.assertEqual(tuple(surface_contract.CORRUPTION_CODES),
                         ("L1", "L2", "L3", "L4", "V∅"))
        for strings in (non_docstring_strings(os.path.join(
                HERE, "run.py")),
                non_docstring_strings(os.path.join(
                    HERE, "softconfig.py"))):
            for text in strings:
                if text.strip().startswith("L6"):
                    self.fail("a sixth corruption code appeared: %r"
                              % (text,))


class TestC6AttestedUnchanged(unittest.TestCase):
    """C6 — nothing attested is un-done: the two fixture modes and the
    attested B4 suites stay green; the bridge is additive."""

    def test_both_fixture_modes_still_complete_byte_identically(self):
        ledgers = []
        for mode in ("sub-process", "re-prompted"):
            ledger, trailp, result = b4_case("main_run", mode=mode)
            self.assertEqual(result["status"], "complete", mode)
            self.assertEqual(
                read_bytes(ledger),
                read_bytes(os.path.join(B4, "fixtures", "main_run",
                                        "expected", "gates.jsonl")),
                mode)
            ledgers.append(read_bytes(ledger))
            shutil.rmtree(os.path.join("fixtures", "main_run", "work"),
                          ignore_errors=True)
        self.assertEqual(ledgers[0], ledgers[1])

    def test_the_prompt_and_budget_literals_are_not_hard_coded(self):
        # the conductor's control flow carries no §2-emphasis / voice /
        # model / budget literal — they live in the declared defaults
        # (softconfig / cost) + the soft layer (C3, the prohibition)
        with open(os.path.join(HERE, "run.py"),
                  encoding="utf-8") as handle:
            source = handle.read()
        self.assertIn("softconfig.default_mode", source)
        self.assertIn("softconfig.budget_of", source)
        self.assertIn("softconfig.desk_emphasis", source)
        self.assertIn("softconfig.desk_voice", source)
        self.assertIn("softconfig.desk_model", source)
        self.assertNotIn("cost.DEFAULT_MODE", source)
        for text in non_docstring_strings(os.path.join(HERE, "run.py")):
            self.assertNotIn("DESK_FUNCTION_SPECS[", text)
            self.assertNotIn("ATTENTION_READINGS[", text)
            self.assertNotIn("COST_MODEL[\"charges\"]", text)

    def test_no_machine_authenticity_path(self):
        # K3: no authenticity verdict — no attested-state write, no
        # non-null attestation write, no tentative flip (HC-1/HC-2 stay
        # INCONCLUSIVE by construction)
        for module in ("run.py", "cost.py", "softconfig.py"):
            with open(os.path.join(HERE, module),
                      encoding="utf-8") as handle:
                source = handle.read()
            self.assertNotIn('state="attested"', source, module)
            self.assertNotIn('"state": "attested"', source, module)
            self.assertNotIn('attestation_ref="', source, module)
            self.assertNotIn('tentative=False', source, module)
            self.assertNotIn('"tentative": false', source, module)
            self.assertNotIn('"tentative": False', source, module)

    def test_stdlib_only_no_network_no_llm(self):
        # K1: the bridge adds no network, no LLM, no wall-clock logic;
        # the only socket I/O is the attested instrument's (and the
        # fixture apparatus's own server)
        for module in ("run.py", "softconfig.py"):
            with open(os.path.join(HERE, module),
                      encoding="utf-8") as handle:
                source = handle.read()
            for banned in ("requests", "urllib", "http", "openai",
                           "anthropic", "websocket"):
                self.assertNotIn(banned, source, module)
            self.assertNotIn("time.monotonic", source, module)
            self.assertNotIn("time.sleep", source, module)
        with open(os.path.join(HERE, "cost.py"),
                  encoding="utf-8") as handle:
            cost_source = handle.read()
        self.assertNotIn("import socket", cost_source)
        self.assertIn("import subprocess", cost_source)  # the attested
        # fixture spawn — never widened

    def test_no_human_gate_path_and_no_podium_write(self):
        # H-B4-4 carried: no input(), no cell-attest, no podium write
        for module in ("run.py", "cost.py", "softconfig.py"):
            with open(os.path.join(HERE, module),
                      encoding="utf-8") as handle:
                source = handle.read()
            tree = ast.parse(source)
            calls = [node.func.id for node in ast.walk(tree)
                     if isinstance(node, ast.Call)
                     and isinstance(node.func, ast.Name)]
            self.assertNotIn("input", calls, module)
            for text in non_docstring_strings(os.path.join(
                    HERE, module)):
                if "cell-attest" in text or text.endswith("question.md"):
                    self.fail("%s carries a human-gate path: %r"
                              % (module, text))


class TestC7ColdRestart(unittest.TestCase):
    """C7 — cold restart from disk alone (lens 5): a NEW process
    rebuilds the live mode + config-read from disk alone, byte-identical
    next-action behaviour."""

    def test_restart_harness_re_arms_from_disk_alone(self):
        # the harness spawns TWO fresh conductor processes over the live
        # mode + the soft layer; the final ledger and trail equal the
        # uninterrupted pins byte for byte
        completed = subprocess.run(
            [sys.executable, os.path.join(RESTART, "run_restart.py")],
            cwd=HERE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=900)
        self.assertEqual(completed.returncode, 0,
                         completed.stderr.decode("utf-8", "replace"))
        report = json.loads(completed.stdout.decode("utf-8"))
        self.assertEqual(report["status"], "re-armed")
        self.assertEqual(report["final_result"], "complete")
        self.assertEqual(report["mode_from_soft"], "live")
        self.assertEqual(report["spend"], 44800)  # the soft live charges
        shutil.rmtree(os.path.join(RESTART, "work"),
                      ignore_errors=True)

    def test_fixture_mode_split_stays_b4_byte_identical(self):
        # B4's cold-restart split under the bridge conductor (a NEW
        # process runs the first 40 actions; a SECOND finishes) —
        # byte-identical to B4's pins: the bridge did not break the
        # attested restart path (C6/C7)
        work = os.path.join("fixtures", "main_run", "work")
        if os.path.exists(work):
            shutil.rmtree(work)
        os.makedirs(work)
        try:
            ledger = os.path.join(work, "gates.jsonl")
            trailp = os.path.join(work, "trail.jsonl")
            build.b4_build.write_plant(ledger)
            spec_path = os.path.join(B4, "fixtures", "main_run",
                                     "spec.json")
            for i, max_actions in enumerate((40, None)):
                command = [sys.executable, os.path.join(HERE, "run.py"),
                           "--ledger", ledger, "--trail", trailp,
                           "--spec", spec_path,
                           "--socket-dir", os.path.join(work,
                                                        "sock%d" % i)]
                if max_actions is not None:
                    command += ["--max-actions", str(max_actions)]
                completed = subprocess.run(
                    command, cwd=HERE, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE, timeout=900)
                self.assertEqual(completed.returncode, 0,
                                 completed.stderr.decode())
                result = json.loads(completed.stdout.decode("utf-8"))
                if max_actions is not None:
                    self.assertEqual(result["status"], "step-limited")
                else:
                    self.assertEqual(result["status"], "complete")
            self.assertEqual(
                read_bytes(ledger),
                read_bytes(os.path.join(B4, "fixtures", "main_run",
                                        "expected", "gates.jsonl")))
            self.assertEqual(
                read_bytes(trailp),
                read_bytes(os.path.join(B4, "fixtures", "main_run",
                                        "expected", "trail.jsonl")))
        finally:
            shutil.rmtree(work, ignore_errors=True)

    def test_fresh_conductor_derives_every_next_action_from_disk(self):
        # a BRAND-NEW Conductor (no in-memory state) derives the same
        # next action the running one took, at every step of the LIVE
        # run (live socket + soft config re-read from disk, C7)
        directory = scratch_dir("bridge-derive-")
        try:
            spec = build.read_spec(os.path.join(RESTART, "spec.json"))
            ledger = os.path.join(directory, "gates.jsonl")
            trailp = os.path.join(directory, "trail.jsonl")
            build.b4_build.write_plant(ledger)
            socket_path = os.path.join(directory, "live.sock")
            spec["live_socket"] = socket_path
            server = live_server_module.LiveServer(
                spec, socket_path, constituted="all")
            server.start()
            try:
                conductor = Conductor(ledger, trailp, spec,
                                      socket_dir=os.path.join(
                                          directory, "s"))
                for step in range(24):
                    expected = conductor.next_action()
                    fresh = Conductor(ledger, trailp, spec,
                                      socket_dir=os.path.join(
                                          directory, "fresh"))
                    derived = fresh.next_action()
                    fresh.close()
                    self.assertEqual(derived["kind"], expected["kind"])
                    self.assertEqual(derived.get("cell"),
                                     expected.get("cell"))
                    self.assertEqual(derived.get("cycle"),
                                     expected.get("cycle"))
                    self.assertEqual(derived.get("desk"),
                                     expected.get("desk"))
                    self.assertEqual(derived.get("turn_key"),
                                     expected.get("turn_key"))
                    if expected["kind"] in ("done", "stalled",
                                            "budget-stop"):
                        break
                    if expected["kind"] == "seed":
                        conductor._do_seed(expected)
                    elif expected["kind"] == "turn":
                        conductor._do_turn(expected)
                    elif expected["kind"] == "hold":
                        conductor._record_hold(expected)
                    else:
                        conductor._do_observe(expected)
                conductor.close()
            finally:
                server.halt()
        finally:
            shutil.rmtree(directory, ignore_errors=True)

    def test_absent_plant_boots_nothing(self):
        directory = scratch_dir("bridge-noplant-")
        spec = build.read_spec(os.path.join(LIVE_RUN, "spec.json"))
        conductor = Conductor(
            os.path.join(directory, "g.jsonl"),
            os.path.join(directory, "t.jsonl"), spec,
            socket_dir=os.path.join(directory, "s"))
        with self.assertRaises(run_module.BootError):
            conductor.run()
        conductor.close()
        self.assertFalse(os.path.exists(os.path.join(
            directory, "g.jsonl")))


class TestSixLenses(unittest.TestCase):
    """The six lenses, predictively — each named and measured."""

    def test_lens1_criterion_match_declared_with_citations(self):
        # lens 1: the bridge surface declares the criteria as written —
        # the live mode and the soft config sections carry the C1/C2 and
        # C3/C4 done-when sentences
        surface = surface_contract.RUN_SURFACE
        self.assertIn("live_mode", surface)
        self.assertIn("soft_config", surface)
        self.assertIn("agent_not_found", surface["live_mode"][
            "fail_closed"])
        self.assertIn("never a silently substituted value",
                      surface["soft_config"]["statuses"])

    def test_lens2_invariant_end_to_end_pinned_whole_runs(self):
        # lens 2: the byte-pins are whole-run artifacts (not per call) —
        # the live runs and the restart run exist as complete pinned
        # ledgers + trails, and the audit passed over each whole ledger
        for path in (os.path.join(LIVE_RUN, "expected",
                                  "gates-box.jsonl"),
                     os.path.join(LIVE_RUN, "expected",
                                  "gates-all.jsonl"),
                     os.path.join(RESTART, "expected", "gates.jsonl")):
            audit = audit_payload_chains(ledger_records(path))
            self.assertEqual(audit["verdict"], "PASS", path)

    def test_lens3_absence_never_reads_valid(self):
        # lens 3: absent socket → outage holds (C2 test above); absent
        # soft config → the declared defaults (never a "valid read");
        # absent agent → agent_not_found; empty file → INCONCLUSIVE
        # carrying the empty sha256 (C4 test above); empty ledger →
        # INCONCLUSIVE audit
        audit = audit_payload_chains([])
        self.assertEqual(audit["verdict"], "INCONCLUSIVE")
        view = softconfig_module.load_soft_config(
            os.path.join(scratch_dir("bridge-l3-"), "absent.json"))
        self.assertEqual(view["status"], "defaults")
        self.assertIsNone(
            softconfig_module.load_soft_config(
                os.path.join(SOFT_CONFIG, "empty.json"))["config"])

    def test_lens4_encoding_needle_through_every_string_field(self):
        # lens 4: "∞0′ → ‖" rides the soft-config voice/emphasis/model
        # fields into the prompt, the soft files carry the raw bytes
        # (no \u escapes), and softconfig reads binary-only (no
        # text-mode byte seeks)
        raw = read_bytes(os.path.join(SOFT_CONFIG, "good.json"))
        self.assertIn(NEEDLE.encode("utf-8"), raw)
        self.assertNotIn(b"\\u221e", raw)
        self.assertNotIn(b"\\u2032", raw)
        view = softconfig_module.load_soft_config(
            os.path.join(SOFT_CONFIG, "good.json"))
        for desk in "SGQPV":
            self.assertIn(NEEDLE,
                          softconfig_module.desk_voice(view, desk))
            for line in softconfig_module.desk_emphasis(view, desk):
                self.assertIn(NEEDLE, line)
        with open(os.path.join(HERE, "softconfig.py"),
                  encoding="utf-8") as handle:
            source = handle.read()
        tree = ast.parse(source)
        opens = [node for node in ast.walk(tree)
                 if isinstance(node, ast.Call)
                 and isinstance(node.func, ast.Name)
                 and node.func.id == "open"]
        self.assertTrue(opens)
        for node in opens:
            mode = node.args[1] if len(node.args) > 1 else None
            self.assertIsInstance(mode, ast.Constant, node.lineno)
            self.assertIn("b", mode.value, node.lineno)
        # the pinned live/restart trails carry the needle verbatim
        for path in (os.path.join(LIVE_RUN, "expected",
                                  "trail-all.jsonl"),
                     os.path.join(RESTART, "expected", "trail.jsonl")):
            self.assertIn(NEEDLE.encode("utf-8"), read_bytes(path))

    def test_lens5_cold_restart_second_process(self):
        # lens 5: the harness spawns the SECOND process as a fresh
        # python over disk alone (C7 tests above); the restart pins
        # were generated under the same canonical relative paths the
        # harness re-runs, and the harness itself verifies the re-arm
        with open(os.path.join(RESTART, "run_restart.py"),
                  encoding="utf-8") as handle:
            harness = handle.read()
        self.assertIn("subprocess.Popen", harness)
        self.assertIn("--max-actions", harness)
        self.assertIn("expected", harness)
        self.assertTrue(read_bytes(os.path.join(
            RESTART, "expected", "gates.jsonl")))
        self.assertTrue(read_bytes(os.path.join(
            RESTART, "expected", "trail.jsonl")))

    def test_lens6_blind_tool_inconclusive_never_clean(self):
        # lens 6: an unavailable live socket or an unconstituted desk
        # reports INCONCLUSIVE, never clean — the box run stalled with
        # its holds; the absent-socket run held outage; a malformed
        # config refuses with INCONCLUSIVE; and the live-socket probe
        # (below) skips INCONCLUSIVE when the box is down
        run_end = [line for line in read_json_lines(os.path.join(
            LIVE_RUN, "expected", "trail-box.jsonl"))
            if line.get("event") == "run-end"][0]
        self.assertNotEqual(run_end["content"]["status"], "complete")
        for name in ("malformed.json", "partial.json", "empty.json"):
            view = softconfig_module.load_soft_config(
                os.path.join(SOFT_CONFIG, name))
            self.assertEqual(view["status"], "inconclusive", name)


class TestLiveSocketProbe(unittest.TestCase):
    """H-BRIDGE-1(b) — the live socket, READ-ONLY: resolve desks by
    label, pane.get / agent.get — proving the live dialect is reached.
    ZERO writes (no agent.prompt).  An unreachable live box skips —
    INCONCLUSIVE, never clean on nothing (lens 6)."""

    def test_live_socket_read_only_probe(self):
        instrument = Instrument(timeout_s=5.0)
        try:
            try:
                pong = instrument.ping()
            except HerdrError as exc:
                self.skipTest(
                    "INCONCLUSIVE — the live herdr socket is "
                    "unreachable, nothing was read, never clean: %s"
                    % exc)
            self.assertEqual(pong.get("type"), "pong")
            desks = instrument.desks()
            self.assertTrue(desks)
            observed = instrument.observe_desks(include_output=False)
            for desk, state in observed["desks"].items():
                self.assertIsInstance(state["pane_id"], str)
                self.assertIsInstance(state["agent_status"], str)
        finally:
            instrument.close()


if __name__ == "__main__":
    unittest.main(verbosity=1)
