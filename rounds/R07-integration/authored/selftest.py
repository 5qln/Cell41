#!/usr/bin/env python3
"""selftest — the integration round, author-side checks.

Every test names, in its first docstring line, the criterion ID (or the
commission rule) it exercises and the quantity it measures.  These are
HYPOTHESES — the author's predictions, never results: the verifier
executes the artifact and recomputes every one of them with its own
implementation.

Fixture apparatus lives under fixtures/ (the deterministic desk harness
binding — real herdr dialect, agent_not_found + absent-socket cases —
the pinned scenarios, the plan-equivalence reference runner, the
cold-restart/run-lock runner, and the enforcement fixtures with the
deliberately-injected violations).  Scratch runs use tempfile
directories and the fixed fixture clock; the live ledger and the live
herdr socket are never written — every run resolves the harness's own
socket (H-INT-1: no live agent.prompt is sent this round).

The CLI is exercised as the REAL artifact: a subprocess per invocation
(the cold-restart lens's second process), in/out compared byte-for-byte
against the direct engine calls (C3's diff-ability applied to the seam).

Run:  python3 selftest.py
"""

from __future__ import annotations

import ast
import fcntl
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

# Never leave a bytecode cache beside a predecessor file (the pinned
# loads import by path; the workspace outside ./authored/ stays
# untouched).
sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "fixtures"))
sys.path.insert(0, os.path.join(HERE, "fixtures", "restart"))
sys.path.insert(0, os.environ.get("FRACTAL_LEDGER_DIR",
                                  "/home/deploy/the-cell/ledger"))

import surface_contract as sc  # noqa: E402
import enforce  # noqa: E402
import fixtures.build as build  # noqa: E402
from fixtures.desk_harness import DeskHarness  # noqa: E402
import fixtures.restart.run_conduct as run_conduct  # noqa: E402

CELLCTL = os.path.join(HERE, "cellctl")
PLAN_EQUIV = os.path.join(HERE, "fixtures", "plan_equivalence.py")
SCENARIOS = os.path.join(HERE, "fixtures", "scenarios")
ENFORCEMENT = os.path.join(HERE, "fixtures", "enforcement")
SOFT_CONFIG = os.path.join(HERE, "fixtures", "soft_config")
PINNED_CYCLE = os.path.join(SCENARIOS, "pinned-cycle.json")
PINNED_GUARD = os.path.join(SCENARIOS, "pinned-guard.json")
PINNED_ENCODING = os.path.join(SCENARIOS, "pinned-encoding.json")
NEEDLE = "∞0′ → ‖"
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()

# The declared scenario pins (the C3 pinned-scenario contract).
PINNED_SCENARIO_SHAS = {
    "pinned-cycle.json": ("82d5bfa73af88eb9ebc6f83321d66366d799a29cb01982ac6"
                          "2d860daff891235"),
    "pinned-guard.json": ("34419d66cc302b6e3c0a7e960fcb66af1bfba0373e9646d3f"
                          "49db8e1804ae959"),
    "pinned-encoding.json": ("fe5b3f15169d71f1b1973ff9c870ce98b65213badfd314"
                             "f6a324490bffb16db6"),
}


def emit_bytes(report):
    """The declared serialization (SEAM_SURFACE.serialization) — the
    byte-identity formula."""
    return (json.dumps(report, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("utf-8")


def run_cli(*argv, input_bytes=None, timeout=120.0, cwd=None):
    return subprocess.run([sys.executable, CELLCTL] + list(argv),
                          input=input_bytes, capture_output=True,
                          cwd=cwd or HERE, timeout=timeout)


def run_py(path, *argv, timeout=120.0):
    return subprocess.run([sys.executable, path] + list(argv),
                          capture_output=True, cwd=HERE, timeout=timeout)


def load_cellctl_module():
    """Load the extensionless cellctl file as a module (the parser's
    command set is what C2 checks)."""
    import importlib.machinery
    import importlib.util
    loader = importlib.machinery.SourceFileLoader("cellctl_probe",
                                                  CELLCTL)
    spec = importlib.util.spec_from_loader("cellctl_probe", loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def _decoded(name):
    report = sc.word.decode_scenario(build.scenario_of(name))
    assert report["status"] == "ok", report
    return report["scenario"]


class HarnessCase:
    """One deterministic end-to-end run against the fixture harness —
    a scratch dir, the harness's own socket, the fixed clock, and a
    cell spec built by the fixture spec builder."""

    def __init__(self, scenario_name="cycle", constituted="all",
                 omit_infinity=False, use_socket=True, spec_kwargs=None,
                 max_steps=None):
        self.tmp = tempfile.mkdtemp(prefix="ctl-")
        self.socket = os.path.join(self.tmp, "harness.sock")
        self.harness = None
        if use_socket:
            self.harness = DeskHarness(
                build.harness_spec(omit_infinity=omit_infinity),
                self.socket, constituted=constituted)
            self.harness.start()
        self.scenario_path = os.path.join(self.tmp, "scenario.json")
        build.write_json(self.scenario_path,
                         build.scenario_of(scenario_name))
        self.ledger = os.path.join(self.tmp, "ledger.jsonl")
        self.trail = os.path.join(self.tmp, "trail.jsonl")
        kwargs = dict(spec_kwargs or {})
        self.spec = build.cell_spec(
            self.tmp, self.scenario_path, self.ledger, self.trail,
            live_socket=(self.socket if use_socket else
                         sc.desk_harness.absent_socket_path(self.tmp)),
            max_steps=max_steps, **kwargs)
        self.spec_path = os.path.join(self.tmp, "spec.json")
        build.write_json(self.spec_path, self.spec)

    def conduct(self, *extra):
        return run_cli("conduct", "--spec", self.spec_path, *extra)

    def result(self, completed):
        if completed.returncode not in (0, 1, 3, 4):
            raise AssertionError(
                "conduct exited %d: %s" % (completed.returncode,
                                           completed.stderr.decode()))
        return json.loads(completed.stdout.decode("utf-8"))

    def records(self):
        return sc.ledger.LedgerLoader(self.ledger).load(
            write_index=False).records

    def trail_lines(self):
        return sc.read_trail(self.trail).get("lines") or []

    def close(self):
        if self.harness is not None:
            self.harness.halt()
        shutil.rmtree(self.tmp, ignore_errors=True)


# ---------------------------------------------------------------------------
# C7 / K1 / K2 — the seam itself.
# ---------------------------------------------------------------------------

class TestContractSeam(unittest.TestCase):
    """C7/K1/K2 — the pinned seams stay the import boundary."""

    def test_every_pin_matches_the_staged_bytes(self):
        """C7 — every PINNED_FILES entry's sha equals the file on disk."""
        for pinned in sc.PINNED_FILES:
            with open(pinned["path"], "rb") as handle:
                actual = hashlib.sha256(handle.read()).hexdigest()
            self.assertEqual(actual, pinned["sha256"], pinned["path"])

    def test_a_drifted_pin_refuses_the_import(self):
        """C7, lens 3 — a drifted pinned file raises ImportError; a
        missing one raises ImportError; a TBD pin raises ImportError."""
        tmp = tempfile.mkdtemp(prefix="pin-")
        drifted = os.path.join(tmp, "drifted.py")
        with open(drifted, "w") as handle:
            handle.write("x = 1\n")
        with self.assertRaises(ImportError):
            sc._load_pinned(
                {"path": drifted,
                 "sha256": "0" * 64}, "drifted_probe")
        with self.assertRaises(ImportError):
            sc._load_pinned(
                {"path": os.path.join(tmp, "missing.py"),
                 "sha256": "0" * 64}, "missing_probe")
        with self.assertRaises(ImportError):
            sc._load_pinned(
                {"path": drifted, "sha256": "TBD"}, "tbd_probe")

    def test_the_pinned_scenarios_hold_their_declared_shas(self):
        """C3 — the pinned scenario files are byte-pinned (the
        plan-equivalence dry run's declared input data)."""
        for name, wanted in PINNED_SCENARIO_SHAS.items():
            with open(os.path.join(SCENARIOS, name), "rb") as handle:
                actual = hashlib.sha256(handle.read()).hexdigest()
            self.assertEqual(actual, wanted, name)

    def test_the_cli_and_enforcer_import_stdlib_and_the_seam_only(self):
        """K1 — the CLI and the enforcement suite add no network, no
        LLM, no wall-clock, no subprocess: an AST scan lists their
        imports against the stdlib + the pinned seam names."""
        for path in (CELLCTL, os.path.join(HERE, "enforce.py")):
            with open(path, "rb") as handle:
                tree = ast.parse(handle.read().decode("utf-8"), path)
            imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.update(a.name.split(".")[0]
                                   for a in node.names)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module.split(".")[0])
            allowed = set(sys.stdlib_module_names) | {"surface_contract"}
            extra = imports - allowed
            self.assertFalse(extra, "%s imports non-stdlib: %s"
                             % (path, ", ".join(sorted(extra))))

    def test_no_write_verb_is_exposed_as_a_command(self):
        """C2 — the write side is deliberately NOT exposed: no command
        wraps the write verb; the command set is exactly the declared
        seam manifest's."""
        module = load_cellctl_module()
        parser = module.build_parser()
        choices = sorted(parser._subparsers._group_actions[0].choices)
        self.assertEqual(choices, sorted(sc.SEAM_SURFACE["commands"]))
        self.assertNotIn("prompt", choices)

    def test_no_socket_client_and_no_normalisation_in_the_wrapper(self):
        """C1/K2 — the wrapper's CODE contains no socket client and no
        byte normalisation: an AST scan over the CLI and the seam
        modules finds no AF_UNIX/sendall/connect name or attribute, no
        socket/subprocess/unicodedata import, no normalize/casefold
        call (declaration strings that NAME the scanned tokens are
        data, not driving code)."""
        for path in (CELLCTL,
                     os.path.join(HERE, "enforce.py"),
                     os.path.join(HERE, "surface_contract.py")):
            with open(path, "rb") as handle:
                tree = ast.parse(handle.read().decode("utf-8"), path)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    self.assertFalse(
                        any(a.name.split(".")[0] in
                            ("socket", "subprocess", "unicodedata")
                            for a in node.names),
                        "%s imports %s" % (path, node.names))
                if isinstance(node, ast.ImportFrom):
                    self.assertFalse(
                        node.module and node.module.split(".")[0]
                        in ("socket", "subprocess", "unicodedata"),
                        "%s imports %s" % (path, node.module))
                if isinstance(node, ast.Name):
                    self.assertNotIn(
                        node.id, ("AF_UNIX", "sendall", "send_text",
                                  "send_input", "send_keys",
                                  "herdr_send_prompt"),
                        "%s names %s" % (path, node.id))
                if isinstance(node, ast.Attribute):
                    self.assertNotIn(
                        node.attr, ("sendall", "connect", "normalize",
                                    "casefold"),
                        "%s uses .%s" % (path, node.attr))

    def test_the_manifest_declares_every_command_one_call(self):
        """C1 — every SEAM_SURFACE command declares one engine call,
        its success statuses, and its candidate slash name."""
        for name, command in sc.SEAM_SURFACE["commands"].items():
            self.assertTrue(command.get("one_call"), name)
            self.assertTrue(command.get("success"), name)
            self.assertTrue(command.get("engine"), name)
            self.assertIn("candidate_slash", command, name)


# ---------------------------------------------------------------------------
# C1 — one subcommand, one engine call, byte-exact forwarding.
# ---------------------------------------------------------------------------

class TestWordCommand(unittest.TestCase):
    """C1, lens 3/4 — /word wraps the decoder, byte-exact."""

    def test_word_ok_report_equals_the_direct_call_bytes(self):
        """C1 — the CLI's report bytes equal json of the direct
        load_scenario_file report (the wrapper adds nothing)."""
        done = run_cli("word", "--scenario", PINNED_CYCLE)
        self.assertEqual(done.returncode, 0)
        self.assertEqual(done.stdout,
                         emit_bytes(sc.word.load_scenario_file(
                             PINNED_CYCLE)))

    def test_absent_and_empty_scenarios_never_read_valid(self):
        """C1, lens 3 — absent file and empty file (sha256 of empty
        cited) read absent with exit 1, never a substituted value."""
        with tempfile.TemporaryDirectory() as tmp:
            missing = os.path.join(tmp, "none.json")
            done = run_cli("word", "--scenario", missing)
            self.assertEqual(done.returncode, 1)
            report = json.loads(done.stdout)
            self.assertEqual(report["status"], "absent")
            empty = os.path.join(tmp, "empty.json")
            open(empty, "wb").close()
            done = run_cli("word", "--scenario", empty)
            self.assertEqual(done.returncode, 1)
            report = json.loads(done.stdout)
            self.assertEqual(report["status"], "absent")
            self.assertIn("e3b0c44298fc", report["reason"])

    def test_a_malformed_scenario_reads_malformed_with_the_reason(self):
        """C1 — a bad-letter scenario reads malformed, exit 1."""
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "bad.json")
            build.write_json(path, build.MALFORMED["bad-letter"])
            done = run_cli("word", "--scenario", path)
            self.assertEqual(done.returncode, 1)
            self.assertEqual(json.loads(done.stdout)["status"],
                             "malformed")

    def test_the_encoding_needle_rides_the_decode_report_verbatim(self):
        """lens 4 — ∞0′ → ‖ carried in the seed ref + a system override
        rides the CLI output byte-verbatim."""
        done = run_cli("word", "--scenario", PINNED_ENCODING)
        self.assertEqual(done.returncode, 0)
        self.assertIn(NEEDLE.encode("utf-8"), done.stdout)

    def test_stdin_and_inline_json_decode(self):
        """C1 — --stdin raw bytes and --json inline JSON reach
        decode_scenario (one call each)."""
        with open(PINNED_CYCLE, "rb") as handle:
            raw = handle.read()
        done = run_cli("word", "--stdin",
                       input_bytes=raw)
        self.assertEqual(done.returncode, 0)
        self.assertEqual(json.loads(done.stdout)["status"], "ok")
        done = run_cli("word", "--json", raw.decode("utf-8"))
        self.assertEqual(done.returncode, 0)
        self.assertEqual(json.loads(done.stdout)["status"], "ok")


class TestPlanCommand(unittest.TestCase):
    """C1/C3 — /plan and the plan-equivalence dry run."""

    def test_plan_equals_the_direct_call(self):
        """C1 — the CLI's plan bytes equal json of the direct
        plan_walk over the same decoded scenario."""
        with tempfile.TemporaryDirectory() as tmp:
            decoded_path = os.path.join(tmp, "decoded.json")
            build.write_json(decoded_path, _decoded("cycle"))
            done = run_cli("plan", decoded_path)
            self.assertEqual(done.returncode, 0)
            self.assertEqual(
                done.stdout,
                emit_bytes(sc.navigate.plan_walk(_decoded("cycle"))))

    def test_plan_only_is_byte_identical_to_the_direct_sequence(self):
        """C3 — cellctl conduct --plan-only over the pinned scenario is
        byte-identical to word.decode_scenario + navigate.plan_walk
        directly (the reference runner) — the wrapper adds nothing."""
        cli = run_cli("conduct", "--plan-only", "--scenario",
                      PINNED_CYCLE)
        direct = run_py(PLAN_EQUIV, PINNED_CYCLE)
        self.assertEqual(cli.returncode, direct.returncode)
        self.assertEqual(cli.stdout, direct.stdout)
        plan = json.loads(cli.stdout)
        self.assertEqual(plan["status"], "ok")
        self.assertEqual(plan["pattern"], "custom")
        self.assertEqual([v["letter"] for v in plan["visits"]],
                         ["S", "G", "Q", "P", "V"])

    def test_plan_only_over_an_absent_scenario_reads_absent(self):
        """C3, lens 3 — plan-only over a missing file reads absent,
        exit 1 — never a substituted plan."""
        with tempfile.TemporaryDirectory() as tmp:
            done = run_cli("conduct", "--plan-only", "--scenario",
                           os.path.join(tmp, "none.json"))
            self.assertEqual(done.returncode, 1)
            self.assertEqual(json.loads(done.stdout)["status"], "absent")


class TestMaterializeCommand(unittest.TestCase):
    """C1, lens 3/4 — /materialize is the engine's write path, bound."""

    def _case(self):
        tmp = tempfile.mkdtemp(prefix="mat-")
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        decoded_path = os.path.join(tmp, "decoded.json")
        build.write_json(decoded_path, _decoded("cycle"))
        return tmp, decoded_path

    def test_materialize_and_verify_round_trip(self):
        """C1 — materialize emits every node's four files with the
        declared shas; --verify reads them back ok."""
        tmp, decoded_path = self._case()
        out = os.path.join(tmp, "cells")
        done = run_cli("materialize", decoded_path, "--out", out)
        self.assertEqual(done.returncode, 0)
        report = json.loads(done.stdout)
        self.assertEqual(report["status"], "materialized")
        self.assertEqual({n["address"] for n in report["nodes"]},
                         {"", "G", "Q", "P", "V"})
        for node in report["nodes"]:
            for name in sc.materialize.cell_files():
                path = os.path.join(out, "_" if node["address"] == ""
                                    else node["address"], *name.split("/"))
                with open(path, "rb") as handle:
                    raw = handle.read()
                self.assertTrue(raw, "%s is empty" % path)
                self.assertEqual(hashlib.sha256(raw).hexdigest(),
                                 node["files"][name])
        done = run_cli("materialize", decoded_path, "--out", out,
                       "--verify")
        self.assertEqual(done.returncode, 0)
        self.assertEqual(json.loads(done.stdout)["status"], "ok")

    def test_a_drifted_cell_reads_inconclusive(self):
        """C1, lens 3 — a tampered materialized file reads
        inconclusive on --verify, exit 1 — never used silently."""
        tmp, decoded_path = self._case()
        out = os.path.join(tmp, "cells")
        run_cli("materialize", decoded_path, "--out", out)
        with open(os.path.join(out, "G", "SYSTEM.md"), "ab") as handle:
            handle.write(b"drift")
        done = run_cli("materialize", decoded_path, "--out", out,
                       "--verify")
        self.assertEqual(done.returncode, 1)
        self.assertEqual(json.loads(done.stdout)["status"],
                         "inconclusive")

    def test_the_needle_rides_a_system_override_into_the_cell(self):
        """lens 4 — a system override carrying ∞0′ → ‖ lands in the
        emitted SYSTEM.md byte-verbatim."""
        tmp, decoded_path = self._case()
        scenario = _decoded("cycle")
        scenario["nodes"] = {**scenario["nodes"],
                             "": {"system": {"seat": "S " + NEEDLE}}}
        path = os.path.join(tmp, "needle-decoded.json")
        build.write_json(path, scenario)
        out = os.path.join(tmp, "cells")
        run_cli("materialize", path, "--out", out)
        with open(os.path.join(out, "_", "SYSTEM.md"), "rb") as handle:
            self.assertIn(NEEDLE.encode("utf-8"), handle.read())

    def test_an_unknown_general_tool_reads_inconclusive(self):
        """C1 — an unknown general tool is refused with the reason
        (never a silently substituted cell)."""
        tmp, decoded_path = self._case()
        scenario = _decoded("cycle")
        scenario["nodes"] = {**scenario["nodes"],
                             "G": {"general_tools": ["teleport"]}}
        path = os.path.join(tmp, "bad-tool.json")
        build.write_json(path, scenario)
        done = run_cli("materialize", path, "--out",
                       os.path.join(tmp, "cells"))
        self.assertEqual(done.returncode, 1)
        self.assertEqual(json.loads(done.stdout)["status"],
                         "inconclusive")


# ---------------------------------------------------------------------------
# C5/C6/K4, lenses 2/5/6 — /conduct end to end.
# ---------------------------------------------------------------------------

class TestConductEndToEnd(unittest.TestCase):
    """C1/C5/C6, K4, lenses 2/5/6 — the composite over the harness."""

    def test_the_full_cycle_runs_end_to_end_through_the_cli(self):
        """C6, lens 2 — plan → walk → conduct through the CLI: the run
        ends complete in ∞0′ with the return question; five per-gate
        records; boot/seed/turns/run-end trail; the dependency audit
        PASSes; the hand-off chain threads refs; the podium is never
        prompted (K4)."""
        case = HarnessCase()
        self.addCleanup(case.close)
        done = case.conduct()
        self.assertEqual(done.returncode, 0)
        result = case.result(done)
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["ended_in"], "∞0′")
        self.assertTrue(result["return_question"].startswith("sha256:"))
        records = case.records()
        self.assertEqual([(r["address"] or "_", r["gate"]) for r in
                          records],
                         [("_", "x"), ("G", "y"), ("Q", "z"), ("P", "a"),
                          ("V", "b")])
        for record in records:
            self.assertEqual(record["state"], "held-pending")
            self.assertIsNone(record["attestation_ref"])  # K3
        events = [line.get("event") for line in case.trail_lines()]
        self.assertEqual(events, ["boot", "seed", "turn", "turn",
                                  "turn", "turn", "run-end"])
        audit = sc.audit_payload_chains(records)
        self.assertEqual(audit["verdict"], "PASS")
        # the hand-off chain: G's prompt carries the seed's ref, each
        # later desk the previous fenced digest (references only)
        seed_payload = records[0]["payload_ref"]
        self.assertIn(seed_payload.split(":", 1)[1][:16],
                      case.harness.prompts["w8:p3"])
        # the podium (w8:p2) received ZERO prompts (K4)
        self.assertNotIn("w8:p2", case.harness.prompts)
        # the boot line carries the encoding probe (lens 4)
        boot = case.trail_lines()[0]
        self.assertIn(NEEDLE, boot["content"]["encoding_probe"])

    def test_conduct_with_materialize_runs_the_whole_pipeline(self):
        """lens 2 — one run: plan → materialize → conduct (the
        materializer's write path + the runtime read-back)."""
        mat_tmp = tempfile.mkdtemp(prefix="mat-")
        self.addCleanup(shutil.rmtree, mat_tmp, ignore_errors=True)
        case = HarnessCase(spec_kwargs={
            "materialize": os.path.join(mat_tmp, "cells")})
        self.addCleanup(case.close)
        done = case.conduct()
        self.assertEqual(done.returncode, 0)
        result = case.result(done)
        self.assertEqual(result["status"], "complete")
        root = case.spec["materialize"]
        for node in ("_", "G", "Q", "P", "V"):
            self.assertTrue(os.path.isfile(
                os.path.join(root, node, "SYSTEM.md")), node)

    def test_an_unconstituted_desk_holds_agent_not_found(self):
        """lens 6 — a desk resolving to a pane with no agent holds
        blocked agent_not_found; the run ends inconclusive, NEVER
        clean, never a fixture stand-in."""
        case = HarnessCase(constituted=("G", "Q", "P"))  # V absent
        self.addCleanup(case.close)
        done = case.conduct()
        self.assertEqual(done.returncode, 0)  # engine code: declared resources
        result = case.result(done)
        self.assertEqual(result["status"], "inconclusive")
        holds = [line for line in case.trail_lines()
                 if line.get("event") == "hold"]
        self.assertEqual([h["content"]["detail"] for h in holds],
                         ["agent_not_found"])
        # the hold record is honest; ZERO fenced answers for V — no
        # stand-in answered
        v_records = [r for r in case.records() if r["address"] == "V"]
        self.assertEqual(len(v_records), 1)
        self.assertTrue(str(v_records[0]["payload_ref"]).startswith(
            "hold:"))
        self.assertFalse([r for r in v_records
                          if str(r["payload_ref"]).startswith(
                              "fenced:")])

    def test_an_absent_socket_holds_outage(self):
        """lens 6 — an unavailable live socket holds outage for every
        desk turn with zero fenced records; the boot state read is
        carried absent honestly; the run is INCONCLUSIVE, never clean."""
        case = HarnessCase(use_socket=False)
        self.addCleanup(case.close)
        done = case.conduct()
        self.assertEqual(done.returncode, 0)
        result = case.result(done)
        self.assertEqual(result["status"], "inconclusive")
        boot = case.trail_lines()[0]
        self.assertEqual(boot["content"]["desk_states"]["status"],
                         "absent")
        holds = [line for line in case.trail_lines()
                 if line.get("event") == "hold"]
        self.assertEqual({h["content"]["kind"] for h in holds},
                         {"outage"})
        self.assertFalse([r for r in case.records()
                          if str(r["payload_ref"]).startswith("fenced:")])

    def test_the_centre_guard_refuses_s_before_any_byte(self):
        """K4 — the guard scenario's non-seed S visit is refused before
        any byte: hold guard-fail centre, ZERO prompts to the podium,
        exactly one prompt (G's) reaching the harness."""
        case = HarnessCase(scenario_name="guard")
        self.addCleanup(case.close)
        done = case.conduct()
        self.assertEqual(done.returncode, 0)
        result = case.result(done)
        self.assertEqual(result["status"], "refused")
        holds = [line for line in case.trail_lines()
                 if line.get("event") == "hold"]
        self.assertEqual([(h["content"]["kind"], h["content"]["detail"])
                          for h in holds], [("guard-fail", "centre")])
        self.assertNotIn("w8:p2", case.harness.prompts)
        self.assertEqual(sorted(case.harness.prompts), ["w8:p3"])

    def test_a_v_without_infinity_is_refused(self):
        """C6 — the harness's omit-infinity variant: a lawful V surface
        whose ∞0′ slot is absent holds refused no-∞0′ — seal line 8,
        the run never ends clean."""
        case = HarnessCase(omit_infinity=True)
        self.addCleanup(case.close)
        done = case.conduct()
        self.assertEqual(done.returncode, 0)
        result = case.result(done)
        self.assertEqual(result["status"], "refused")
        self.assertIsNone(result["ended_in"])
        holds = [line for line in case.trail_lines()
                 if line.get("event") == "hold"]
        self.assertEqual([h["content"]["detail"] for h in holds],
                         ["no-∞0′"])

    def test_the_run_lock_blocks_a_second_conduct(self):
        """C5, lens 5 — while the flock is held, a second /conduct on
        the same work dir BLOCKS (no records land, the process stays
        alive); on release it completes.  The lock lives in the
        wrapper, never the engine."""
        case = HarnessCase()
        self.addCleanup(case.close)
        lock_path = os.path.join(case.tmp, ".cellctl.lock")
        fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o644)
        fcntl.flock(fd, fcntl.LOCK_EX)
        try:
            proc = subprocess.Popen(
                [sys.executable, CELLCTL, "conduct", "--spec",
                 case.spec_path], cwd=HERE,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(1.5)
            self.assertIsNone(proc.poll(),
                              "the second /conduct did not block")
            self.assertFalse(os.path.exists(case.ledger) and
                             open(case.ledger, "rb").read(),
                             "records landed while the lock was held")
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)
        out, err = proc.communicate(timeout=120)
        self.assertEqual(proc.returncode, 0, err.decode())
        self.assertEqual(json.loads(out)["status"], "complete")
        self.assertEqual(len(self._gates(case)), 5)

    @staticmethod
    def _gates(case):
        return case.records()

    def test_a_second_process_rebuilds_the_run_from_disk_alone(self):
        """lens 5 — a walk split across TWO fresh CLI processes (the
        second re-arms from the ledger + trail alone) produces the
        exact ledger + trail bytes of the uninterrupted run; the first
        process's step limit never re-prompts."""
        case = HarnessCase()
        self.addCleanup(case.close)
        # uninterrupted reference run
        done = case.conduct()
        self.assertEqual(done.returncode, 0)
        reference_ledger = open(case.ledger, "rb").read()
        reference_trail = open(case.trail, "rb").read()
        # reset the same paths (the harness answers are deterministic)
        for path in (case.ledger, case.trail):
            if os.path.exists(path):
                os.unlink(path)
        first = case.conduct("--max-steps", "2")
        self.assertEqual(first.returncode, 0)
        first_result = case.result(first)
        self.assertEqual(first_result["status"], "step-limited")
        second = case.conduct()
        self.assertEqual(second.returncode, 0)
        second_result = case.result(second)
        self.assertEqual(second_result["status"], "complete")
        self.assertEqual(second_result["ended_in"], "∞0′")
        self.assertEqual(open(case.ledger, "rb").read(), reference_ledger)
        self.assertEqual(open(case.trail, "rb").read(), reference_trail)

    def test_the_declared_restart_runner_drives_the_second_process(self):
        """lens 5 — the declared cold-restart fixture runner
        (fixtures/restart/run_conduct.py) executes cellctl in a NEW
        process and returns its exit + output (the second-process
        medium of the restart lens)."""
        case = HarnessCase()
        self.addCleanup(case.close)
        report = run_conduct.run_conduct(case.spec_path)
        self.assertEqual(report["exit"], 0, report["stderr"])
        result = json.loads(report["stdout"])
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["ended_in"], "∞0′")

    def test_the_live_spec_with_no_scenario_refuses(self):
        """H-INT-4/C6 — /conduct over the live spec (scenario null, D2
        open) refuses INCONCLUSIVE before any engine call — never a
        fixture stand-in."""
        done = run_cli("conduct", "--spec",
                       os.path.join(HERE, "spec.json"))
        self.assertEqual(done.returncode, 1)
        report = json.loads(done.stdout)
        self.assertEqual(report["status"], "inconclusive")
        self.assertIn("D2", report["reason"])

    def test_an_unknown_spec_field_refuses_the_run(self):
        """C4/L3 — a spec carrying an unknown field is refused by the
        loader (INCONCLUSIVE), the run never starts."""
        with tempfile.TemporaryDirectory() as tmp:
            spec = dict(build.cell_spec(tmp, PINNED_CYCLE,
                                        os.path.join(tmp, "l.jsonl"),
                                        os.path.join(tmp, "t.jsonl")))
            spec["totally_unknown_field"] = 1
            path = os.path.join(tmp, "spec.json")
            build.write_json(path, spec)
            done = run_cli("conduct", "--spec", path)
            self.assertEqual(done.returncode, 1)
            self.assertEqual(json.loads(done.stdout)["status"],
                             "inconclusive")


class TestStatesCommand(unittest.TestCase):
    """C2 — the read side is the only desk-facing command."""

    def test_states_read_the_harness_desks_read_only(self):
        """C2 — /states reports observed per-desk states over the
        harness socket; the harness recorded only read methods, never
        a prompt."""
        case = HarnessCase()
        self.addCleanup(case.close)
        done = run_cli("states", "--spec", case.spec_path)
        self.assertEqual(done.returncode, 0)
        report = json.loads(done.stdout)
        self.assertEqual(report["status"], "observed")
        self.assertIn("G", report["desks"])
        self.assertNotIn("agent.prompt", case.harness.methods)

    def test_an_absent_socket_reads_absent_honestly(self):
        """C2, lens 6 — an absent socket reads {"status":"absent"},
        exit 1 — never a fabricated state."""
        case = HarnessCase(use_socket=False)
        self.addCleanup(case.close)
        done = run_cli("states", "--spec", case.spec_path)
        self.assertEqual(done.returncode, 1)
        self.assertEqual(json.loads(done.stdout)["status"], "absent")


class TestWalkCommand(unittest.TestCase):
    """C1 — /walk is the raw sign-walk over the live wiring."""

    def test_walk_runs_the_attested_live_wiring(self):
        """C1 — /walk returns the trace (complete, ended in ∞0′) over
        the harness; the composite /conduct also emits the trail."""
        case = HarnessCase()
        self.addCleanup(case.close)
        done = run_cli("walk", "--spec", case.spec_path)
        self.assertEqual(done.returncode, 0)
        result = json.loads(done.stdout)
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["ended_in"], "∞0′")
        self.assertEqual(len(result["visits"]), 5)


# ---------------------------------------------------------------------------
# C1 — config / cost / descent / trail / decode / compile / check.
# ---------------------------------------------------------------------------

class TestConfigCommand(unittest.TestCase):
    """C1, lens 3/4 — /config reads the soft config, fail-closed."""

    def test_absent_defaults_good_and_inconclusive_reads(self):
        """C1, lens 3 — absent → defaults (exit 0); good → ok; empty
        (sha256 of empty cited) / malformed / partial / unknown-field →
        inconclusive (exit 1) — never a substituted value."""
        with tempfile.TemporaryDirectory() as tmp:
            done = run_cli("config", "--path",
                           os.path.join(tmp, "none.json"))
            self.assertEqual(done.returncode, 0)
            self.assertEqual(json.loads(done.stdout)["status"], "defaults")
            done = run_cli("config", "--path",
                           os.path.join(SOFT_CONFIG, "good.json"))
            self.assertEqual(done.returncode, 0)
            self.assertEqual(json.loads(done.stdout)["status"], "ok")
            for name in ("empty.json", "malformed.json",
                         "partial.json", "unknown-field.json"):
                done = run_cli("config", "--path",
                               os.path.join(SOFT_CONFIG, name))
                self.assertEqual(done.returncode, 1, name)
                self.assertEqual(json.loads(done.stdout)["status"],
                                 "inconclusive", name)
            done = run_cli("config", "--path",
                           os.path.join(SOFT_CONFIG, "empty.json"))
            self.assertIn("e3b0c44298fc",
                          json.loads(done.stdout)["reason"])

    def test_the_needle_rides_a_voice_verbatim(self):
        """lens 4 — a soft config voice carrying ∞0′ → ‖ reads back
        byte-verbatim through the CLI."""
        with tempfile.TemporaryDirectory() as tmp:
            good = build.read_json(os.path.join(SOFT_CONFIG,
                                                "good.json"))
            good["desks"]["G"]["voice"] = "G-voice " + NEEDLE
            path = os.path.join(tmp, "soft.json")
            build.write_json(path, good)
            done = run_cli("config", "--path", path)
            self.assertEqual(done.returncode, 0)
            self.assertIn(NEEDLE.encode("utf-8"), done.stdout)


class TestCostCommand(unittest.TestCase):
    """C1 — /cost reads the declared spend through the engine."""

    def test_cost_equals_the_direct_spend(self):
        """C1 — the CLI's spend bytes equal the direct
        spend_from_records over the same records and mode."""
        case = HarnessCase()
        self.addCleanup(case.close)
        case.conduct()
        records = case.records()
        done = run_cli("cost", "--ledger", case.ledger, "--mode", "live")
        self.assertEqual(done.returncode, 0)
        report = json.loads(done.stdout)
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["spend"],
                         sc.cost.spend_from_records(records, "live"))
        self.assertGreater(report["spend"], 0)

    def test_cost_with_soft_charges_reads_the_soft_layer(self):
        """C1 — --soft-config resolves the per-desk charges through
        softconfig.budget_of (the engine's read path)."""
        case = HarnessCase()
        self.addCleanup(case.close)
        case.conduct()
        records = case.records()
        soft_path = os.path.join(SOFT_CONFIG, "good.json")
        done = run_cli("cost", "--ledger", case.ledger, "--mode",
                       "live", "--soft-config", soft_path)
        self.assertEqual(done.returncode, 0)
        soft = sc.softconfig.load_soft_config(soft_path)
        expected = sc.cost.spend_from_records(
            records, "live",
            charge_for=lambda mode, desk: sc.softconfig.budget_of(
                soft, mode, desk))
        self.assertEqual(json.loads(done.stdout)["spend"], expected)

    def test_a_broken_ledger_reads_inconclusive(self):
        """C1, lens 3 — an unreadable ledger refuses the spend
        (INCONCLUSIVE), never a guessed value."""
        with tempfile.TemporaryDirectory() as tmp:
            broken = os.path.join(tmp, "broken.jsonl")
            open(broken, "w").write("{ torn\n")
            done = run_cli("cost", "--ledger", broken, "--mode", "live")
            self.assertEqual(done.returncode, 1)
            self.assertEqual(json.loads(done.stdout)["status"],
                             "inconclusive")


class TestDescentCommand(unittest.TestCase):
    """C1/K2 — /descent binds the address grammar, byte-exact."""

    def test_each_op_matches_the_direct_engine_call(self):
        """C1 — path-between / zoom-in / zoom-out / validate-path /
        validate-word each equal the direct engine result."""
        done = run_cli("descent", "path-between", "--from", "G",
                       "--to", "Q")
        self.assertEqual(json.loads(done.stdout),
                         {"reason": "the address grammar's result (B3, "
                                    "imported)",
                          "result": sc.path_between("G", "Q"),
                          "status": "ok"})
        done = run_cli("descent", "zoom-in", "--address", "G",
                       "--letter", "Q")
        self.assertEqual(json.loads(done.stdout)["result"], "QG")
        done = run_cli("descent", "zoom-out", "--address", "QG")
        self.assertEqual(json.loads(done.stdout)["result"], "G")
        done = run_cli("descent", "validate-path", "--path", "−G")
        self.assertEqual(json.loads(done.stdout),
                         sc.validate_signed_path("−G"))
        self.assertEqual(json.loads(done.stdout)["status"], "ok")
        done = run_cli("descent", "validate-word", "--address", "QG")
        self.assertEqual(json.loads(done.stdout)["status"], "ok")

    def test_the_ascii_hyphen_is_never_normalised(self):
        """K2 — an ASCII-hyphen path is refused (U+002D is not the
        U+2212 operator) — the wrapper forwards the refusal, never
        repairs it."""
        done = run_cli("descent", "validate-path", "--path=-G")
        self.assertEqual(done.returncode, 1)
        report = json.loads(done.stdout)
        self.assertNotEqual(report["status"], "ok")


class TestGrammarCommands(unittest.TestCase):
    """C1/K3, lens 4 — /decode /compile /check bind the Grammar."""

    def _values(self, phase):
        return {name: {"text": "slot-%s-%s" % (phase, name)}
                for name in sc.codex.PHASE_SLOTS[phase]}

    def _context(self, phase):
        chain = {"G": {"X": "prior-x"},
                 "Q": {"X": "x", "α": "a", "Y": "y"},
                 "P": {"X": "x", "α": "a", "Y": "y", "Z": "z"},
                 "V": {"X": "x", "α": "a", "Y": "y", "Z": "z",
                       "∇": "g", "A": "b"},
                 "S": {}}
        return chain[phase]

    def test_decode_fills_slots_as_references_never_text(self):
        """C1/K3 — /decode returns slots as references (never the
        input text), the mechanical mark, and no authenticity verdict
        anywhere in the report bytes."""
        values = self._values("G")
        context = {"X": "prior-x"}  # the adaptive chain, G's required
        with tempfile.TemporaryDirectory() as tmp:
            values_path = os.path.join(tmp, "values.json")
            context_path = os.path.join(tmp, "context.json")
            build.write_json(values_path, values)
            build.write_json(context_path, context)
            done = run_cli("decode", "--phase", "G",
                           "--values", values_path,
                           "--context", context_path)
            self.assertEqual(done.returncode, 0)
            report = json.loads(done.stdout)
            self.assertEqual(report["mark"], "mechanical")
            for name, slot in report["slots"].items():
                self.assertNotEqual(slot, "slot-G-%s" % name)
                self.assertNotIn("authenticity", json.dumps(report))

    def test_a_claim_of_arrival_reads_corruption_l3(self):
        """K3 — a decode that claims to have reached ∞0 reads
        corruption L3 — never arrival, never clean."""
        values = self._values("G")
        with tempfile.TemporaryDirectory() as tmp:
            values_path = os.path.join(tmp, "values.json")
            context_path = os.path.join(tmp, "context.json")
            claims_path = os.path.join(tmp, "claims.json")
            build.write_json(values_path, values)
            build.write_json(context_path, {"X": "prior-x"})
            build.write_json(claims_path,
                             ["we reached ∞0 directly — a claim"])
            done = run_cli("decode", "--phase", "G",
                           "--values", values_path,
                           "--context", context_path,
                           "--claims", claims_path)
            self.assertEqual(done.returncode, 0)
            report = json.loads(done.stdout)
            self.assertEqual(report["corruption"], "L3")

    def test_compile_emits_the_surface_with_the_needle_raw(self):
        """C1, lens 4 — /compile writes the emitted §3.6 surface RAW;
        a slot carrying ∞0′ → ‖ rides it byte-verbatim."""
        slots = {"B''": "a formed return", "∞0'": NEEDLE}
        with tempfile.TemporaryDirectory() as tmp:
            slots_path = os.path.join(tmp, "slots.json")
            build.write_json(slots_path, slots)
            done = run_cli("compile", "--phase", "V",
                           "--slots", slots_path)
            self.assertEqual(done.returncode, 0)
            self.assertIn(NEEDLE.encode("utf-8"), done.stdout)
            self.assertIn("⟦".encode("utf-8"), done.stdout)

    def test_check_reports_hc_inconclusive_never_clean(self):
        """K3 — /check over a produced artifact ends INCONCLUSIVE
        (HC-1/HC-2 are INCONCLUSIVE by design) — a machine can never
        report a fully clean artifact; exit 1."""
        slots = {"B''": "a formed return", "∞0'": "the question"}
        text = sc.compiler.emit("V", slots, cell_address="V")
        parsed = sc.parse_surface(text,
                                  equation_forms=sc.EQUATION_FORMS)
        cell = {"address": "V",
                "arrangement": list(sc.grammar.COURSE),
                "seats": {letter: sc.codex.seat_address("V", letter)
                          for letter in sc.grammar.COURSE}}
        artifact = {"parsed": parsed, "surface": text, "phase": "V",
                    "cell": cell}
        with tempfile.TemporaryDirectory() as tmp:
            artifact_path = os.path.join(tmp, "artifact.json")
            build.write_json(artifact_path, artifact)
            done = run_cli("check", artifact_path)
            self.assertEqual(done.returncode, 1)
            report = json.loads(done.stdout)
            self.assertNotEqual(report["verdict"], "PASS")
            hcs = {item["id"]: item["verdict"]
                   for item in report["items"]
                   if item["id"] in ("HC-1", "HC-2")}
            self.assertEqual(hcs, {"HC-1": "INCONCLUSIVE",
                                   "HC-2": "INCONCLUSIVE"})

    def test_the_five_corruption_codes_only(self):
        """K3 — the corruption taxonomy is exactly L1 L2 L3 L4 V∅ — no
        sixth code exists."""
        self.assertEqual(sc.corruption.CODES,
                         ("L1", "L2", "L3", "L4", "V\u2205"))


class TestTrailCommand(unittest.TestCase):
    """C1 — /trail is the human's window into a run."""

    def test_trail_and_audit_match_the_direct_reads(self):
        """C1 — /trail equals read_trail; --audit equals the direct
        dependency audit over the same records."""
        case = HarnessCase()
        self.addCleanup(case.close)
        case.conduct()
        done = run_cli("trail", "--ledger", case.ledger, "--trail",
                       case.trail)
        self.assertEqual(done.returncode, 0)
        direct = sc.read_trail(case.trail)
        raw = direct.pop("raw", None)
        direct["raw_sha256"] = hashlib.sha256(raw or b"").hexdigest()
        self.assertEqual(done.stdout, emit_bytes(direct))
        done = run_cli("trail", "--ledger", case.ledger, "--trail",
                       case.trail, "--audit")
        self.assertEqual(done.returncode, 0)
        records = case.records()
        expected = sc.audit_payload_chains(records)
        self.assertEqual(json.loads(done.stdout)["verdict"],
                         expected["verdict"])


# ---------------------------------------------------------------------------
# C4 — the enforcement suite holds as a structural fact.
# ---------------------------------------------------------------------------

class TestEnforcementLegs(unittest.TestCase):
    """C4 — legs 1-3, each failing on a deliberately-injected
    violation and passing on the clean fixture root."""

    def _root(self, name, files=None):
        return {"name": name,
                "path": os.path.join(ENFORCEMENT, name, "plugin", "bin"),
                "files": files, "executables": True}

    @staticmethod
    def _fixture_declaration():
        """The declared L1 declaration minus the test-apparatus
        exclusions (the fixture roots ARE the test apparatus — the
        exclusion list is for the live roots, where fixtures/ is never
        a scan root anyway)."""
        declaration = dict(sc.L1_DECLARATION)
        declaration["excluded_paths"] = ()
        return declaration

    def test_leg1_passes_a_clean_fixture_root(self):
        """C4/L1 — the clean fixture soft layer passes the capability
        scan with zero findings."""
        report = enforce.leg1_capability(
            roots=[self._root("clean")],
            declaration=self._fixture_declaration())
        self.assertEqual(report["verdict"], "PASS", report)

    def test_leg1_fails_the_injected_write_verb(self):
        """C4/L1 — the injected write-verb bin FAILS the capability
        scan with the named token."""
        report = enforce.leg1_capability(
            roots=[self._root("l1-write-verb")],
            declaration=self._fixture_declaration())
        self.assertEqual(report["verdict"], "FAIL", report)
        self.assertTrue(any("herdr_send_prompt" in f["token"]
                            or "send_prompt" in f["token"]
                            for f in report["findings"]), report)

    def test_leg1_honours_the_declared_tty_allowlist(self):
        """C4/L1 — a finding inside the declared cell-plant/cell-attest
        allowlist is allowed by declaration, never hidden."""
        with tempfile.TemporaryDirectory() as tmp:
            bin_dir = os.path.join(tmp, "plugin", "bin")
            os.makedirs(bin_dir)
            plant = os.path.join(bin_dir, "cell-plant")
            with open(plant, "w") as handle:
                handle.write("#!/usr/bin/env bash\nsend_text "
                             "'planted'  # the human's TTY act\n")
            report = enforce.leg1_capability(
                roots=[{"name": "probe", "path": bin_dir,
                        "files": None, "executables": True}],
                declaration=sc.L1_DECLARATION)
            self.assertEqual(report["verdict"], "PASS", report)
            self.assertTrue(any("allowlist" in note["note"]
                                for note in report["notes"]), report)

    def test_leg2_passes_the_declared_census(self):
        """C4/L2 — a root whose executables are declared members of the
        manifest passes the census."""
        clean_bin = os.path.join(ENFORCEMENT, "clean", "plugin", "bin",
                                 "cell-begin")
        manifest = {"entry_points": [{"path": clean_bin,
                                      "role": "fixture bin"}],
                    "import_allowed": (), "pinned_module_names":
                        sc.SEAM_MANIFEST["pinned_module_names"]}
        report = enforce.leg2_census(roots=[self._root("clean")],
                                     manifest=manifest)
        self.assertEqual(report["verdict"], "PASS", report)

    def test_leg2_fails_an_undeclared_bin(self):
        """C4/L2 — an executable that is NOT a declared member of the
        seam manifest FAILS the census."""
        manifest = {"entry_points": [], "import_allowed": (),
                    "pinned_module_names":
                        sc.SEAM_MANIFEST["pinned_module_names"]}
        report = enforce.leg2_census(roots=[self._root("l2-undeclared")],
                                     manifest=manifest)
        self.assertEqual(report["verdict"], "FAIL", report)
        self.assertTrue(any(f["token"] == "undeclared-executable"
                            for f in report["findings"]), report)

    def test_leg2_fails_a_direct_engine_import(self):
        """C4/L2 — a soft-layer file importing a pinned engine module
        directly FAILS the census (the CLI is the only path)."""
        manifest = {"entry_points": [], "import_allowed": (),
                    "pinned_module_names":
                        sc.SEAM_MANIFEST["pinned_module_names"]}
        report = enforce.leg2_census(
            roots=[self._root("l2-engine-import")], manifest=manifest)
        self.assertEqual(report["verdict"], "FAIL", report)
        self.assertTrue(any("pinned engine module" in f["reason"]
                            for f in report["findings"]), report)

    def test_leg3_passes_the_clean_declared_data(self):
        """C4/L3 — the clean spec + scenario validate against the
        declared schemas."""
        report = enforce.leg3_schema(
            targets=[{"name": "clean-spec",
                      "path": os.path.join(ENFORCEMENT, "clean",
                                           "spec.json"),
                      "kind": "cell-spec"}],
            scenarios=[os.path.join(ENFORCEMENT, "clean",
                                    "scenario.json")])
        self.assertEqual(report["verdict"], "PASS", report)

    def test_leg3_refuses_an_unknown_spec_field(self):
        """C4/L3 — a spec carrying an unknown field reads INCONCLUSIVE
        (refuse) and FAILS the leg — never silently ignored."""
        report = enforce.leg3_schema(
            targets=[{"name": "bad-spec",
                      "path": os.path.join(ENFORCEMENT,
                                           "l3-unknown-field",
                                           "spec.json"),
                      "kind": "cell-spec"}])
        self.assertEqual(report["verdict"], "FAIL", report)
        self.assertTrue(any("unknown field" in f["reason"]
                            for f in report["findings"]), report)

    def test_leg3_refuses_an_unknown_soft_config_field(self):
        """C4/L3 — a soft config with an unknown field reads
        INCONCLUSIVE through the engine's own attested read."""
        report = enforce.leg3_schema(
            targets=[{"name": "bad-soft",
                      "path": os.path.join(ENFORCEMENT,
                                           "l3-soft-unknown",
                                           "soft.json"),
                      "kind": "soft-config"}])
        self.assertEqual(report["verdict"], "FAIL", report)

    def test_leg3_refuses_a_malformed_scenario(self):
        """C4/L3 — a scenario outside the declared schema reads
        INCONCLUSIVE (refuse) and FAILS the leg."""
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "bad.json")
            build.write_json(path, build.MALFORMED["topology-enum"])
            report = enforce.leg3_schema(targets=[], scenarios=[path])
            self.assertEqual(report["verdict"], "FAIL", report)

    def test_a_missing_required_scan_root_reads_inconclusive(self):
        """C4, lens 6 — an absent required scan root reads INCONCLUSIVE,
        never clean (a blind spot is never a pass)."""
        with tempfile.TemporaryDirectory() as tmp:
            report = enforce.leg1_capability(
                roots=[{"name": "probe",
                        "path": os.path.join(tmp, "absent"),
                        "files": None, "executables": True,
                        "required": True}],
                declaration=sc.L1_DECLARATION)
            self.assertEqual(report["verdict"], "INCONCLUSIVE", report)

    def test_the_verify_report_rebuilds_in_a_second_process(self):
        """lens 5 — a NEW process rebuilds the enforcement report from
        disk alone and lands the same verdicts."""
        here = HERE
        code = ("import sys, json; sys.path.insert(0, %r); "
                "import enforce; r = enforce.verify_all(); "
                "print(json.dumps({'verdict': r['verdict'], "
                "'legs': {k: v['verdict'] for k, v in r['legs'].items()},"
                " 'gates': r['gates_plant']['verdict']}))" % here)
        second = subprocess.run(
            [sys.executable, "-c", code], capture_output=True,
            cwd=here, timeout=180)
        self.assertEqual(second.returncode, 0, second.stderr.decode())
        in_process = enforce.verify_all()
        rebuilt = json.loads(second.stdout)
        self.assertEqual(rebuilt["legs"],
                         {k: v["verdict"]
                          for k, v in in_process["legs"].items()})
        self.assertEqual(rebuilt["gates"],
                         in_process["gates_plant"]["verdict"])


class TestColdRestartScans(unittest.TestCase):
    """lens 5 — the plan rebuilds in a second process, byte-exact."""

    def test_a_second_process_plan_is_byte_exact(self):
        """lens 5 — a NEW CLI process replans the pinned scenario and
        lands the same bytes as the first process."""
        first = run_cli("conduct", "--plan-only", "--scenario",
                        PINNED_CYCLE)
        second = run_cli("conduct", "--plan-only", "--scenario",
                         PINNED_CYCLE)
        self.assertEqual(first.stdout, second.stdout)
        self.assertEqual(first.returncode, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
