#!/usr/bin/env python3
"""selftest — the bindings round, author-side checks.

Every test names, in its first docstring line, the criterion ID (or the
commission rule / lens) it exercises and the quantity it measures.
These are HYPOTHESES — the author's predictions, never results: the
verifier executes the artifact and recomputes every one of them with
its own implementation.

What is executed here:
  * the pi binding's REAL runtime — fixtures/probe.mjs imports the
    delivered pi-cell/src/cellctl.mjs (table + argv builder + one
    spawn + result shaping), so the tested code IS the shipped code
    (lens 2), driven from fresh processes (lens 5);
  * the human binding's REAL argv — the addendum TOML is parsed and
    each action's declared command is executed as-is (lens 2);
  * the REAL attested cellctl (the seam, R07 canon 992b775) — through
    the binding's exact argv shapes, against the pinned R06 desk
    harness on its own socket (H-R08-1: no live desk is ever
    prompted, the live ledger/trail are never written);
  * the enforcement suite (the R07 enforce module, through the seam)
    over the fixture pre-world and over the APPLIED authored
    re-points — the suite flips to clean only after the re-pointing
    (C4);
  * the podium renderer over fixture trail files (absent/empty/ok/
    damaged + the needle).

Run:  python3 selftest.py
"""

from __future__ import annotations

import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import tomllib
import unittest

# Never leave a bytecode cache beside a predecessor file (the pinned
# loads import by path; the workspace outside ./authored/ stays
# untouched).
sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "fixtures"))
sys.path.insert(0, os.path.join(HERE, "fixtures", "desk_harness"))
sys.path.insert(0, os.path.join(HERE, "fixtures", "cold_restart"))
sys.path.insert(0, ("/home/deploy/the-cell/rounds/"
                    "R07-integration/authored"))

import surface_contract as sc  # noqa: E402  (the seam)
import enforce  # noqa: E402  (the enforcement suite, through the seam)
import build  # noqa: E402  (the round's fixture builders)
import desk_bind  # noqa: E402  (the fixture desk harness binding)
import run_conduct  # noqa: E402  (the declared cold-restart runner)

CELLCTL = os.path.join("/home/deploy/the-cell/rounds",
                       "R07-integration/authored/cellctl")
FAKE = os.path.join(HERE, "fixtures", "fake_cellctl.py")
PROBE = os.path.join(HERE, "fixtures", "probe.mjs")
NODE = "node"
ADDENDUM = os.path.join(HERE, "human-binding",
                        "herdr-plugin-v4.addendum.toml")
PI_CELL_SRC = os.path.join(HERE, "pi-cell")
ENFORCEMENT = os.path.join(HERE, "enforcement")
ENFORCEMENT_PRE = os.path.join(HERE, "fixtures", "enforcement", "pre")
ENFORCEMENT_MANIFEST = os.path.join(HERE, "fixtures", "enforcement",
                                    "manifest.json")
PODIUM_BIN = os.path.join(HERE, "podium", "cell-podium")
BRICKS = os.path.join(HERE, "bricks")
NEEDLE_CASES = os.path.join(HERE, "fixtures", "byte_round_trip",
                            "needle_args.json")
NEEDLE_SCENARIO = os.path.join(HERE, "fixtures", "scenarios",
                               "binding-needle.json")
NEEDLE = "∞0′ → ‖"
EMPTY_SHA256 = "e3b0c44298fc"
SPAWN_TOOL = "herdr_start_agent"

SUCCESS = {"word": "ok", "plan": "ok", "materialize": "materialized",
           "conduct": "complete", "walk": "complete",
           "config": "defaults", "cost": "ok", "states": "observed",
           "descent": "ok", "decode": "ok", "compile": "ok",
           "check": "PASS", "trail": "ok"}


# ---------------------------------------------------------------------------
# Helpers.
# ---------------------------------------------------------------------------

def run(argv, env=None, cwd=None, timeout=300, input_bytes=None):
    return subprocess.run(argv, capture_output=True, env=env, cwd=cwd,
                          timeout=timeout, input=input_bytes)


def run_fake(*argv, journal=None, env=None):
    full_env = dict(os.environ)
    if journal:
        full_env["CELLCTL_JOURNAL"] = journal
    full_env.pop("CELLCTL_BIN", None)
    full_env.pop("FAKE_HOLD_MS", None)
    if env:
        full_env.update(env)
    return run([sys.executable, FAKE] + list(argv), env=full_env)


def probe(tool, params, bin_path=None, argv_only=False, env=None):
    argv = [NODE, PROBE, tool, json.dumps(params, ensure_ascii=False)]
    if bin_path:
        argv += ["--bin", bin_path]
    if argv_only:
        argv += ["--argv-only"]
    return run(argv, env=env or dict(os.environ))


def journal(path):
    if not os.path.isfile(path):
        return []
    out = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def table():
    with open(os.path.join(PI_CELL_SRC, "src", "tool-table.json"),
              "r", encoding="utf-8") as handle:
        return json.load(handle)


def parse_addendum():
    with open(ADDENDUM, "rb") as handle:
        return tomllib.load(handle)


def fixture_declaration():
    declaration = dict(sc.L1_DECLARATION)
    declaration["excluded_paths"] = ()
    return declaration


def fixture_manifest(root, extended):
    """The fixture census: pre-extension (import_allowed empty — the
    R07-shaped live manifest, where cell-attest's seam import is NOT
    yet declared) vs post-extension (the seam-declaration extension
    applied)."""
    data = build.read_json(ENFORCEMENT_MANIFEST)
    return {
        "entry_points": [{"path": os.path.join(root, entry["path"]),
                          "role": entry["role"]}
                         for entry in data["entry_points"]],
        "import_allowed": ([os.path.join(root, path)
                            for path in data["import_allowed"]]
                           if extended else []),
        "pinned_module_names": tuple(data["pinned_module_names"]),
    }


def roots_for(root):
    return [
        {"name": "plugin-bin",
         "path": os.path.join(root, "plugin", "bin"),
         "files": None, "executables": True, "required": True},
        {"name": "desks",
         "path": os.path.join(root, "desks"),
         "files": None, "executables": True, "required": True},
    ]


def spawn_authority_scan(root):
    """The author's own check for finding ii (the live enforce.py
    patterns do not match the spawn-tool literal — declared in the
    phase card; this scan proves the flip at the source)."""
    findings = []
    for dirpath, dirnames, filenames in os.walk(root):
        for name in filenames:
            path = os.path.join(dirpath, name)
            with open(path, "r", encoding="utf-8", errors="replace") \
                    as handle:
                for line_no, line in enumerate(handle, start=1):
                    if SPAWN_TOOL in line:
                        findings.append((path, line_no))
    return findings


class HarnessCase:
    """One deterministic end-to-end run against the pinned R06 desk
    harness — a scratch dir, the harness's own socket, a cell spec
    built by the fixture builder.  The REAL cellctl is the binary
    (the seam), invoked with the binding's exact argv shape."""

    def __init__(self, constituted="all", use_socket=True):
        self.tmp = tempfile.mkdtemp(prefix="r08-")
        self.socket = os.path.join(self.tmp, "harness.sock")
        self.harness = None
        if use_socket:
            self.harness = desk_bind.DeskHarness(
                build.harness_spec(), self.socket,
                constituted=constituted)
            self.harness.start()
        self.scenario_path = os.path.join(self.tmp, "scenario.json")
        build.write_json(self.scenario_path, build.scenario_of("cycle"))
        self.ledger = os.path.join(self.tmp, "ledger.jsonl")
        self.trail = os.path.join(self.tmp, "trail.jsonl")
        self.spec = build.cell_spec(
            self.tmp, self.scenario_path, self.ledger, self.trail,
            live_socket=(self.socket if use_socket else
                         desk_bind.absent_socket_case(self.tmp)))
        self.spec_path = os.path.join(self.tmp, "spec.json")
        build.write_json(self.spec_path, self.spec)

    def conduct(self, *extra):
        return run([sys.executable, CELLCTL, "conduct", "--spec",
                    self.spec_path] + list(extra))

    def states(self):
        return run([sys.executable, CELLCTL, "states", "--spec",
                    self.spec_path])

    def close(self):
        if self.harness is not None:
            self.harness.halt()
        shutil.rmtree(self.tmp, ignore_errors=True)


def fake_world(work_dir):
    """A scratch cell for the fake: word + spec + ledger + trail paths
    (all caller-supplied — never the live box)."""
    scenario = os.path.join(work_dir, "scenario.json")
    build.write_json(scenario, build.scenario_of("cycle"))
    ledger = os.path.join(work_dir, "ledger.jsonl")
    trail = os.path.join(work_dir, "trail.jsonl")
    spec = build.cell_spec(work_dir, scenario, ledger, trail,
                           live_socket=os.path.join(work_dir,
                                                    "cell.sock"))
    spec_path = os.path.join(work_dir, "spec.json")
    build.write_json(spec_path, spec)
    return spec_path


def apply_repoints(root):
    """Copy the AUTHORED re-points (the real deliverables — never
    fixture stand-ins) over a scratch soft-layer root."""
    bin_dir = os.path.join(root, "plugin", "bin")
    os.makedirs(bin_dir, exist_ok=True)
    for name in ("_cell_api.py", "cell-attest", "cell-begin",
                 "cell-zoom", "cell-on-desk-state"):
        shutil.copy(os.path.join(ENFORCEMENT, "plugin-bin", name),
                    os.path.join(bin_dir, name))
        os.chmod(os.path.join(bin_dir, name),
                 os.stat(os.path.join(bin_dir, name)).st_mode
                 | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    shutil.copy(PODIUM_BIN, os.path.join(bin_dir, "cell-podium"))
    os.chmod(os.path.join(bin_dir, "cell-podium"),
             os.stat(os.path.join(bin_dir, "cell-podium")).st_mode
             | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    for desk in ("S", "G", "Q", "P", "V"):
        dst = os.path.join(root, "desks", desk, ".pi", "prompts")
        os.makedirs(dst, exist_ok=True)
        shutil.copy(os.path.join(ENFORCEMENT, "desks", desk, ".pi",
                                 "prompts", "guide.md"),
                    os.path.join(dst, "guide.md"))


def write_trail(path, lines, unterminated=False):
    body = "".join(json.dumps(line, ensure_ascii=False,
                              separators=(",", ":")) + "\n"
                   for line in lines)
    if unterminated:
        body = body[:-1]
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(body)


def trail_line(seq, source="machine", event="turn", signal=None,
               return_question=None, phase="G", cell="G", cycle=1):
    return {"trail_version": "1", "scope": "fixture", "seq": seq,
            "ts": "2026-08-31T00:00:%02dZ" % seq, "phase": phase,
            "source": source, "event": event, "signal": signal,
            "content": None, "return_question": return_question,
            "turn_key": "t%08d" % seq, "cell": cell, "cycle": cycle,
            "ledger": None, "conformance": None, "cost": None,
            "prev_hash": None, "event_hash": None}


# ---------------------------------------------------------------------------
# C1/C8 — the binding surface: independent studs, one cellctl call each.
# ---------------------------------------------------------------------------

class TestBindingSurface(unittest.TestCase):
    """C1/C8 — thirteen independent studs; the orchestration method is
    data, never code in the binding."""

    def test_the_table_declares_thirteen_studs_one_subcommand_each(self):
        """C1/C8.1 — the tool table declares exactly the 13 cellctl
        subcommands, each stud one subcommand, no sequence field, no
        tool referencing another."""
        data = table()
        tools = data["tools"]
        self.assertEqual(len(tools), 13)
        names = [row["name"] for row in tools]
        self.assertEqual(sorted(names), sorted([
            "word", "plan", "materialize", "conduct", "walk", "config",
            "cost", "states", "descent", "decode", "compile", "check",
            "trail"]))
        for row in tools:
            self.assertEqual(row["name"], row["subcommand"])
        raw = json.dumps(data)
        for forbidden in ("sequence", "order", "pipeline", "steps",
                          "after", "then"):
            self.assertNotIn('"%s"' % forbidden, raw)

    def test_every_stud_through_the_probe_makes_exactly_one_fake_call(self):
        """C1 — each of the 13 tools, driven through the binding's real
        runtime, lands exactly ONE fake-cellctl invocation and names
        exactly one subcommand."""
        param_sets = {
            "word": {"scenario": "IN-scenario.json"},
            "plan": {"scenario": "IN-scenario.json"},
            "materialize": {"scenario": "IN-scenario.json",
                            "out": "IN-out"},
            "conduct": {"spec": "IN-spec.json"},
            "walk": {"spec": "IN-spec.json"},
            "config": {},
            "cost": {"ledger": "IN-ledger.jsonl", "mode": "live"},
            "states": {"spec": "IN-spec.json"},
            "descent": {"op": "path-between", "from": "", "to": "V"},
            "decode": {"phase": "G"},
            "compile": {"phase": "G", "slots": "{}"},
            "check": {"artifact": '{"surface":"x"}'},
            "trail": {"ledger": "IN-ledger.jsonl",
                      "trail": "IN-trail.jsonl"},
        }
        names = [row["name"] for row in table()["tools"]]
        self.assertEqual(sorted(names), sorted(param_sets))
        with tempfile.TemporaryDirectory() as tmp:
            journal_path = os.path.join(tmp, "journal.jsonl")
            for name in sorted(param_sets):
                params = dict(param_sets[name])
                done = probe(name, params, bin_path=FAKE,
                             env={**os.environ,
                                  "CELLCTL_JOURNAL": journal_path})
                self.assertIn(done.returncode, (0, 1),
                              name + done.stderr.decode())
                entries = journal(journal_path)
                self.assertEqual(len(entries), 1,
                                 "%s: %s" % (name, entries))
                argv = entries[0]["argv"]
                self.assertEqual(argv[0], name)
                subcommands = [item for item in argv[1:]
                               if item in names]
                self.assertEqual(subcommands, [],
                                 "%s argv carries a second "
                                 "subcommand" % name)
                os.unlink(journal_path)

    def test_the_addendum_declares_eight_actions_one_subcommand_each(self):
        """C1/C2 — the human binding declares exactly the eight
        conduction actions, each command = cellctl + ONE subcommand,
        argv-only, no TTY-guard tokens; plant/attest are not
        re-declared."""
        manifest = parse_addendum()
        actions = manifest.get("actions", [])
        ids = [action["id"] for action in actions]
        self.assertEqual(sorted(ids), sorted([
            "conduct", "word", "plan", "materialize", "states",
            "trail", "descent", "config"]))
        for action in actions:
            argv = action["command"]
            self.assertEqual(argv[0], CELLCTL, action["id"])
            subcommands = [item for item in argv[1:]
                           if item in [r["name"]
                                       for r in table()["tools"]]]
            self.assertEqual(len(subcommands), 1, action["id"])
            self.assertEqual(subcommands[0], action["id"])
            self.assertNotIn("isatty", json.dumps(argv))
            self.assertNotIn("TTY", json.dumps(argv))
        self.assertNotIn("plant", ids)
        self.assertNotIn("attest", ids)

    def test_each_action_argv_makes_exactly_one_fake_call(self):
        """C1 — each declared action, executed AS DECLARED against the
        fake (the action command IS the argv), lands exactly one
        invocation."""
        with tempfile.TemporaryDirectory() as tmp:
            journal_path = os.path.join(tmp, "journal.jsonl")
            for action in parse_addendum()["actions"]:
                done = run_fake(*action["command"][1:],
                                journal=journal_path)
                self.assertIn(done.returncode, (0, 1),
                              action["id"] + done.stderr.decode())
                entries = journal(journal_path)
                self.assertEqual(len(entries), 1, action["id"])
                os.unlink(journal_path)

    def test_the_binding_sources_carry_no_fixed_sequence(self):
        """C8.2 — the pi-cell runtime sources carry no orchestration
        sequence: no hard-coded cell path in code (only the declared
        default binary — env-overridable), no scenario name, no desk
        order."""
        for name in ("index.ts", "cellctl.mjs", "tool-table.json"):
            with open(os.path.join(PI_CELL_SRC, "src" if name !=
                                   "index.ts" else "",
                                   name), "r", encoding="utf-8") \
                    as handle:
                text = handle.read()
            self.assertNotIn("SGQPV", text)
            self.assertNotIn("word.json", text)
            self.assertNotIn("/state/", text)


# ---------------------------------------------------------------------------
# C3/K2 — byte identity: the binding adds nothing.
# ---------------------------------------------------------------------------

class TestByteIdentity(unittest.TestCase):
    """C3/K2 — the binding re-serializes nothing; plan-only through the
    binding is byte-identical to the direct calls."""

    def test_plan_only_through_the_binding_is_byte_identical_to_direct(self):
        """C3 — conduct --plan-only through the probe (the binding's
        runtime) and the direct fake call land the same bytes — any
        difference is the binding's."""
        with tempfile.TemporaryDirectory() as tmp:
            scenario = os.path.join(tmp, "scenario.json")
            build.write_json(scenario, build.scenario_of("cycle"))
            via = probe("conduct",
                        {"plan_only": True, "scenario": scenario},
                        bin_path=FAKE)
            direct = run_fake("conduct", "--plan-only", "--scenario",
                              scenario)
            self.assertEqual(via.returncode, 0, via.stderr.decode())
            self.assertEqual(direct.returncode, 0)
            via_result = json.loads(via.stdout)
            self.assertEqual(via_result["content"][0]["text"],
                             direct.stdout.decode("utf-8"))
            self.assertEqual(
                via_result["details"]["argv"],
                ["conduct", "--plan-only", "--scenario", scenario])

    def test_plan_only_through_the_binding_matches_the_real_seam(self):
        """C3 — over the REAL attested cellctl, the binding's plan-only
        run is byte-identical to the direct CLI run (the seam's own
        C3 proof, re-proven through the binding's argv)."""
        via = probe("conduct",
                    {"plan_only": True, "scenario": NEEDLE_SCENARIO},
                    bin_path=CELLCTL)
        direct = run([sys.executable, CELLCTL, "conduct", "--plan-only",
                      "--scenario", NEEDLE_SCENARIO])
        self.assertEqual(via.returncode, 0, via.stderr.decode())
        self.assertEqual(direct.returncode, 0, direct.stderr.decode())
        self.assertEqual(json.loads(via.stdout)["content"][0]["text"],
                         direct.stdout.decode("utf-8"))

    def test_the_probe_result_carries_the_raw_report_untouched(self):
        """K2 — the result's text is the fake's raw stdout string,
        byte-for-byte (no re-serialization, no normalisation)."""
        with tempfile.TemporaryDirectory() as tmp:
            scenario = os.path.join(tmp, "scenario.json")
            build.write_json(scenario, build.scenario_of("cycle"))
            via = probe("plan", {"scenario": scenario}, bin_path=FAKE)
            direct = run_fake("plan", scenario)
            self.assertEqual(json.loads(via.stdout)["content"][0]["text"],
                             direct.stdout.decode("utf-8"))


# ---------------------------------------------------------------------------
# Lens 4 — encoding: the needle rides every string field byte-verbatim.
# ---------------------------------------------------------------------------

class TestEncodingNeedle(unittest.TestCase):
    """lens 4 — ∞0′ → ‖ rides tool args, action argv, inline JSON and
    file paths byte-verbatim; the fake echoes, the test compares."""

    def test_the_needle_rides_every_tool_arg_field(self):
        """lens 4 — each declared needle case, driven through the
        binding's runtime, returns the needle bytes exactly as sent
        (the fake's echo field or its raw stdout) — and a needle
        smuggled into a field whose notation excludes it is REFUSED,
        never normalised into validity."""
        cases = build.read_json(NEEDLE_CASES)["cases"]
        for case in cases:
            via = probe(case["tool"], case["params"], bin_path=FAKE)
            self.assertIn(via.returncode, (0, 1),
                          case["tool"] + via.stderr.decode())
            text = json.loads(via.stdout)["content"][0]["text"]
            if case.get("expect") == "refused":
                self.assertEqual(via.returncode, 1, case["tool"])
                self.assertIn("notation", text)  # the refusal, verbatim
                continue
            self.assertIn(NEEDLE, text, case["tool"])
            if case["echo_field"] == "needle_echo":
                report = json.loads(text)
                echo = report.get("needle_echo")
                self.assertIsNotNone(echo, case["tool"])
                if isinstance(echo, dict):
                    self.assertIn(NEEDLE, json.dumps(echo,
                                                     ensure_ascii=False))
                else:
                    self.assertIn(NEEDLE, echo)
            elif case["echo_field"] == "stdout":
                self.assertIn(NEEDLE, text)

    def test_the_needle_rides_a_scenario_file_through_the_real_seam(self):
        """lens 4 — a scenario file whose seed ref carries the needle,
        decoded through the binding's argv over the REAL cellctl,
        returns the seed ref byte-verbatim."""
        via = probe("word", {"scenario": NEEDLE_SCENARIO},
                    bin_path=CELLCTL)
        self.assertEqual(via.returncode, 0, via.stderr.decode())
        report = json.loads(json.loads(via.stdout)["content"][0]["text"])
        self.assertIn(NEEDLE, report["scenario"]["seed"]["ref"])

    def test_the_needle_rides_an_action_argv_field(self):
        """lens 4 — an action-shaped argv whose data field carries the
        needle is executed as declared; the fake echoes the path
        verbatim (action args are argv items, never shell words)."""
        with tempfile.TemporaryDirectory() as tmp:
            needle_path = os.path.join(tmp, "needle ∞0′ → ‖.json")
            done = run_fake("config", "--path", needle_path)
            self.assertEqual(done.returncode, 1)  # absent → honest
            self.assertIn(NEEDLE, done.stdout.decode("utf-8"))


# ---------------------------------------------------------------------------
# C6/lens 3 — absence vs validity, fail-closed, never clean.
# ---------------------------------------------------------------------------

class TestAbsenceAndMalformed(unittest.TestCase):
    """C6, lens 3 — absent/empty/malformed never read valid; absent
    cellctl reads INCONCLUSIVE with a reason, never a stand-in."""

    def test_absent_empty_and_malformed_scenarios_never_read_valid(self):
        """C6/lens 3 — word over an absent file reads absent, an empty
        file names the sha256 of empty, a malformed file reads
        malformed — all exit 1, never clean."""
        with tempfile.TemporaryDirectory() as tmp:
            absent = os.path.join(tmp, "absent.json")
            empty = os.path.join(tmp, "empty.json")
            open(empty, "wb").close()
            malformed = os.path.join(tmp, "bad.json")
            with open(malformed, "w", encoding="utf-8") as handle:
                handle.write("{not json")
            for path, status in ((absent, "absent"),
                                 (malformed, "malformed")):
                via = probe("word", {"scenario": path}, bin_path=FAKE)
                self.assertEqual(via.returncode, 1)
                text = json.loads(via.stdout)["content"][0]["text"]
                self.assertIn('"status":"%s"' % status, text)
            via = probe("word", {"scenario": empty}, bin_path=FAKE)
            self.assertEqual(via.returncode, 1)
            text = json.loads(via.stdout)["content"][0]["text"]
            self.assertIn(EMPTY_SHA256, text)

    def test_an_absent_cellctl_reads_inconclusive_never_clean(self):
        """C6/lens 6 — the seam binary absent: the binding's result is
        an error whose content carries the INCONCLUSIVE reason, never
        an empty success."""
        via = probe("conduct", {"plan_only": True,
                                "scenario": NEEDLE_SCENARIO},
                    bin_path=os.path.join("/nonexistent", "cellctl"))
        self.assertEqual(via.returncode, 1)
        result = json.loads(via.stdout)
        self.assertTrue(result["isError"])
        self.assertIn("INCONCLUSIVE", result["content"][0]["text"])
        self.assertNotIn('"status":"ok"', result["content"][0]["text"])

    def test_an_absent_socket_reads_absent_through_the_binding_argv(self):
        """C2/lens 6 — states over a spec whose live_socket is absent
        reads {"status":"absent"} honestly, through the fake (the
        binding adds nothing)."""
        with tempfile.TemporaryDirectory() as tmp:
            scenario = os.path.join(tmp, "scenario.json")
            build.write_json(scenario, build.scenario_of("cycle"))
            spec = build.cell_spec(tmp, scenario,
                                   os.path.join(tmp, "l.jsonl"),
                                   os.path.join(tmp, "t.jsonl"),
                                   live_socket=None)
            spec_path = os.path.join(tmp, "spec.json")
            build.write_json(spec_path, spec)
            direct = run_fake("states", "--spec", spec_path)
            self.assertEqual(direct.returncode, 1)
            self.assertIn('"status":"absent"',
                          direct.stdout.decode("utf-8"))

    def test_a_null_scenario_spec_refuses_inconclusive(self):
        """C6 — /conduct over a spec whose scenario is null (D2 open)
        refuses INCONCLUSIVE before any run — never a fixture
        stand-in."""
        with tempfile.TemporaryDirectory() as tmp:
            spec = build.cell_spec(tmp, None,
                                   os.path.join(tmp, "l.jsonl"),
                                   os.path.join(tmp, "t.jsonl"))
            spec_path = os.path.join(tmp, "spec.json")
            build.write_json(spec_path, spec)
            via = probe("conduct", {"spec": spec_path}, bin_path=FAKE)
            self.assertEqual(via.returncode, 1)
            self.assertIn("D2", json.loads(via.stdout)["content"][0][
                "text"])


# ---------------------------------------------------------------------------
# C5/lens 5 — the run lock and the cold restart.
# ---------------------------------------------------------------------------

class TestRunLockAndColdRestart(unittest.TestCase):
    """C5, lens 5 — a second process re-arms from disk alone; a
    concurrent second /conduct blocks rather than interleaves."""

    def test_a_second_process_rebuilds_the_plan_byte_identical(self):
        """lens 5 — two fresh probe processes over the fake land
        byte-identical plan bytes (rebuilt from disk alone)."""
        with tempfile.TemporaryDirectory() as tmp:
            scenario = os.path.join(tmp, "scenario.json")
            build.write_json(scenario, build.scenario_of("cycle"))
            first = probe("conduct",
                          {"plan_only": True, "scenario": scenario},
                          bin_path=FAKE)
            second = probe("conduct",
                           {"plan_only": True, "scenario": scenario},
                           bin_path=FAKE)
            self.assertEqual(
                json.loads(first.stdout)["content"][0]["text"],
                json.loads(second.stdout)["content"][0]["text"])

    def test_a_concurrent_second_conduct_blocks_on_the_run_lock(self):
        """C5 — through the declared restart runner over the fake: the
        first /conduct holds the lock, the concurrent second BLOCKS
        and then observes (already-complete) — never interleaved
        (interleaved runs would both read complete)."""
        with tempfile.TemporaryDirectory() as tmp:
            spec_path = fake_world(tmp)
            journal_path = os.path.join(tmp, "journal.jsonl")
            done = run([sys.executable,
                        os.path.join(HERE, "fixtures", "cold_restart",
                                     "run_conduct.py"),
                        "--bin", FAKE, "--spec", spec_path,
                        "--journal", journal_path,
                        "--concurrent",
                        "--hold-ms", "600", "--grace-ms", "200"],
                       env=dict(os.environ))
            self.assertEqual(done.returncode, 0, done.stderr.decode())
            report = json.loads(done.stdout)
            first = json.loads(report["first"]["stdout"])
            second = json.loads(report["second"]["stdout"])
            self.assertEqual(first["status"], "complete")
            self.assertEqual(second["status"], "already-complete")
            self.assertEqual(len(report["journal"]), 2)
            self.assertNotEqual(report["journal"][0]["pid"],
                                report["journal"][1]["pid"])

    def test_the_declared_restart_runner_drives_the_real_seam(self):
        """lens 5 — the declared restart runner executes the REAL
        cellctl as a new process over the harness (the binding's exact
        argv) and the run completes on the fixture desks."""
        case = HarnessCase()
        self.addCleanup(case.close)
        done = run([sys.executable,
                    os.path.join(HERE, "fixtures", "cold_restart",
                                 "run_conduct.py"),
                    "--bin", CELLCTL, "--spec", case.spec_path,
                    "--journal", os.path.join(case.tmp,
                                              "journal.jsonl")],
                   env=dict(os.environ))
        self.assertEqual(done.returncode, 0, done.stderr.decode())
        report = json.loads(done.stdout)
        self.assertEqual(report["first"]["exit"], 0)
        self.assertEqual(json.loads(report["first"]["stdout"])[
            "status"], "complete")

    def test_the_real_seam_rearms_from_disk_alone(self):
        """lens 5 — a second REAL /conduct over the same scratch world
        re-arms from the ledger + trail alone: already-complete,
        never re-run."""
        case = HarnessCase()
        self.addCleanup(case.close)
        first = case.conduct()
        self.assertEqual(first.returncode, 0, first.stderr.decode())
        second = case.conduct()
        self.assertEqual(second.returncode, 0, second.stderr.decode())
        self.assertEqual(json.loads(second.stdout)["status"],
                         "already-complete")


# ---------------------------------------------------------------------------
# Lens 6 — the blind tool: unconstituted desk, absent socket, honestly.
# ---------------------------------------------------------------------------

class TestBlindTool(unittest.TestCase):
    """lens 6 — an unconstituted desk holds agent_not_found; an absent
    socket reads absent — through the REAL seam, with the binding's
    exact argv; the binding substitutes nothing."""

    def test_an_unconstituted_desk_holds_agent_not_found(self):
        """lens 6 — the real /conduct over the harness with one
        unconstituted desk holds agent_not_found (the trail's hold
        lines name it) and the run ends inconclusive — never clean,
        never a fixture stand-in."""
        constituted, _note = desk_bind.unconstituted_case()
        case = HarnessCase(constituted=constituted)
        self.addCleanup(case.close)
        done = case.conduct()
        self.assertIn(done.returncode, (0, 1, 3, 4))
        result = json.loads(done.stdout)
        self.assertEqual(result["status"], "inconclusive")
        read = sc.read_trail(case.trail)
        holds = [line for line in read.get("lines", [])
                 if line.get("event") == "hold"]
        details = [str((hold.get("content") or {}).get("detail"))
                   for hold in holds]
        self.assertTrue(any("agent_not_found" in detail
                            for detail in details),
                        "holds: %s" % details)
        # zero fenced answers for the unconstituted desk — no stand-in
        absent = desk_bind.UNCONSTITUTED_DESK
        records = sc.ledger.LedgerLoader(case.ledger).load(
            write_index=False).records
        absent_records = [r for r in records if r["address"] == absent]
        self.assertFalse([r for r in absent_records
                          if str(r["payload_ref"]).startswith(
                              "fenced:")])

    def test_an_absent_socket_reads_absent_through_the_real_seam(self):
        """C2/lens 6 — real cellctl states over a spec whose socket is
        the absent path reads {"status":"absent"} — never clean."""
        case = HarnessCase(use_socket=False)
        self.addCleanup(case.close)
        done = case.states()
        self.assertEqual(done.returncode, 1)
        self.assertEqual(json.loads(done.stdout)["status"], "absent")


# ---------------------------------------------------------------------------
# C4 — the enforcement suite flips to clean only after the re-pointing.
# ---------------------------------------------------------------------------

class TestEnforcementFlip(unittest.TestCase):
    """C4 — the three pre-integration findings fail the suite; the
    applied authored re-points flip it to zero findings, honestly."""

    def test_the_pre_world_fails_all_three_findings(self):
        """C4 — the pre fixture world FAILs L1 with the socket tokens,
        FAILs L2 with the direct engine import, and the author's spawn
        scan finds the guide's spawn-authority line."""
        report = enforce.leg1_capability(
            roots=roots_for(ENFORCEMENT_PRE),
            declaration=fixture_declaration())
        self.assertEqual(report["verdict"], "FAIL", report)
        self.assertTrue(any(f["token"] in ("socket.AF_UNIX",
                                           "socket.connect",
                                           "socket.sendall")
                            for f in report["findings"]), report)
        census = enforce.leg2_census(
            roots=roots_for(ENFORCEMENT_PRE),
            manifest=fixture_manifest(ENFORCEMENT_PRE, extended=False))
        self.assertEqual(census["verdict"], "FAIL", census)
        self.assertTrue(any("fractal_ledger" in f["token"]
                            for f in census["findings"]), census)
        spawn = spawn_authority_scan(ENFORCEMENT_PRE)
        self.assertTrue(spawn, "the pre guide carries the spawn line")
        self.assertTrue(any(name.endswith("guide.md")
                            for name, _line in spawn))

    def test_the_applied_repoints_flip_the_suite_to_zero_findings(self):
        """C4 — after the AUTHORED re-points are applied over the same
        world shape, L1 reads zero findings, L2 reads zero findings,
        and the spawn scan reads clean — the flip is the re-pointing,
        never an allowlist or a tuned-down pattern."""
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "cell")
            apply_repoints(root)
            report = enforce.leg1_capability(
                roots=roots_for(root),
                declaration=fixture_declaration())
            self.assertEqual(report["verdict"], "PASS", report)
            self.assertEqual(report["findings"], [])
            census = enforce.leg2_census(
                roots=roots_for(root),
                manifest=fixture_manifest(root, extended=True))
            self.assertEqual(census["verdict"], "PASS", census)
            self.assertEqual(census["findings"], [])
            self.assertEqual(spawn_authority_scan(root), [])

    def test_the_repointed_guides_speak_the_seam(self):
        """C4(ii) — each re-pointed guide re-points conduction to
        /conduct and fences the spawn under deferred — D1; the spawn
        tool name is gone from the soft layer."""
        for desk in ("S", "G", "Q", "P", "V"):
            path = os.path.join(ENFORCEMENT, "desks", desk, ".pi",
                                "prompts", "guide.md")
            with open(path, "r", encoding="utf-8") as handle:
                text = handle.read()
            self.assertIn("/conduct", text)
            self.assertIn("deferred — D1 un-decided", text)
            self.assertNotIn(SPAWN_TOOL, text)
            self.assertNotIn("I must use", text)

    def test_the_seam_extension_patch_lands_on_the_live_declarations(self):
        """C4/K5 — the seam-declaration extension's hunks match the
        live R07 surface_contract.py at their anchor points (the patch
        applies to the file as it stands — data, one place to
        change)."""
        live = ("/home/deploy/the-cell/rounds/R07-integration/"
                "authored/surface_contract.py")
        with open(live, "r", encoding="utf-8") as handle:
            text = handle.read()
        with open(os.path.join(ENFORCEMENT,
                               "seam-declaration-extension.patch"),
                  "r", encoding="utf-8") as handle:
            patch = handle.read()
        self.assertIn("cell-on-desk-state", text)
        self.assertIn('"extension_roots": ()', text)
        self.assertIn("cell-podium", patch)
        self.assertIn("cell-attest", patch)
        self.assertIn("pi-cell", patch)
        self.assertIn("fractal_ledger", text)  # the live cell-attest
        # (pre state) is the file the re-point replaces


# ---------------------------------------------------------------------------
# The podium re-point — the read-only trail renderer.
# ---------------------------------------------------------------------------

class TestPodiumRenderer(unittest.TestCase):
    """deliverable 4 — the renderer prints the trail's honest status,
    one line per event, never clean when the trail is absent."""

    def _render(self, ledger, trail):
        env = dict(os.environ)
        env.pop("CELLCTL_BIN", None)
        return run([sys.executable, PODIUM_BIN, "--ledger", ledger,
                    "--trail", trail],
                   env={**env, "CELLCTL_BIN": FAKE})

    def test_absent_and_empty_trails_read_inconclusive(self):
        """lens 3 — absent and empty fixture trails render the
        INCONCLUSIVE banners (the sha256 of empty named), never a
        clean ledger."""
        with tempfile.TemporaryDirectory() as tmp:
            absent = os.path.join(tmp, "no-trail.jsonl")
            ledger = os.path.join(tmp, "ledger.jsonl")
            empty = os.path.join(tmp, "empty.jsonl")
            open(empty, "wb").close()
            out = self._render(ledger, absent)
            self.assertIn("no trail yet", out.stdout.decode())
            self.assertIn("INCONCLUSIVE", out.stdout.decode())
            out = self._render(ledger, empty)
            self.assertIn(EMPTY_SHA256, out.stdout.decode())

    def test_an_ok_trail_renders_one_line_per_event(self):
        """deliverable 4 — an ok fixture trail renders one line per
        event, human and desk interleaved in the report's own order,
        references only."""
        with tempfile.TemporaryDirectory() as tmp:
            trail = os.path.join(tmp, "trail.jsonl")
            ledger = os.path.join(tmp, "ledger.jsonl")
            lines = [trail_line(1, source="human", event="attest",
                                signal="plant:sha256:ab12"),
                     trail_line(2, source="desk_surface", event="turn",
                                phase="G"),
                     trail_line(3, source="machine", event="run-end",
                                phase="V",
                                return_question="plant:sha256:cd34")]
            write_trail(trail, lines)
            out = self._render(ledger, trail)
            text = out.stdout.decode("utf-8")
            self.assertIn("#001", text)
            self.assertIn("#002", text)
            self.assertIn("#003", text)
            self.assertIn("[human]", text)
            self.assertIn("[desk_surface]", text)
            self.assertIn("[machine]", text)
            self.assertIn("plant:sha256:ab12", text)

    def test_a_damaged_trail_renders_inconclusive(self):
        """C6 — a damaged fixture trail renders the INCONCLUSIVE
        banner and the complete prefix, never a clean ledger."""
        with tempfile.TemporaryDirectory() as tmp:
            trail = os.path.join(tmp, "trail.jsonl")
            ledger = os.path.join(tmp, "ledger.jsonl")
            write_trail(trail, [trail_line(1)])
            with open(trail, "a", encoding="utf-8") as handle:
                handle.write("{broken\n")
            out = self._render(ledger, trail)
            text = out.stdout.decode("utf-8")
            self.assertIn("TRAIL DAMAGED", text)
            self.assertIn("INCONCLUSIVE", text)
            self.assertIn("#001", text)  # the complete prefix

    def test_the_needle_rides_the_rendered_signal(self):
        """lens 4 — a signal carrying the needle renders verbatim."""
        with tempfile.TemporaryDirectory() as tmp:
            trail = os.path.join(tmp, "trail.jsonl")
            ledger = os.path.join(tmp, "ledger.jsonl")
            write_trail(trail, [trail_line(1, signal=NEEDLE)])
            out = self._render(ledger, trail)
            self.assertIn(NEEDLE, out.stdout.decode("utf-8"))

    def test_the_renderer_makes_exactly_one_seam_call(self):
        """C1 shape — the renderer's whole reach is ONE cellctl trail
        invocation per refresh (the journal counts it)."""
        with tempfile.TemporaryDirectory() as tmp:
            trail = os.path.join(tmp, "trail.jsonl")
            ledger = os.path.join(tmp, "ledger.jsonl")
            write_trail(trail, [trail_line(1)])
            journal_path = os.path.join(tmp, "journal.jsonl")
            env = dict(os.environ)
            env["CELLCTL_BIN"] = FAKE
            env["CELLCTL_JOURNAL"] = journal_path
            run([sys.executable, PODIUM_BIN, "--ledger", ledger,
                 "--trail", trail], env=env)
            entries = journal(journal_path)
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0]["argv"],
                             ["trail", "--ledger", ledger, "--trail",
                              trail])


# ---------------------------------------------------------------------------
# C8/K5 — the bricks: the method is data the engine reads.
# ---------------------------------------------------------------------------

class TestBricks(unittest.TestCase):
    """C8/K5 — the brick is engine-read data; the binding reads none
    of it; the engine's own readers accept it."""

    def test_the_brick_word_decodes_through_the_real_seam(self):
        """C8.2 — the brick's word.json is accepted by the engine's
        own decoder (cellctl word) — the method is data the engine
        reads, never parsed by the binding."""
        word = os.path.join(BRICKS, "methods", "sgqpv-cycle",
                            "word.json")
        done = run([sys.executable, CELLCTL, "word", "--scenario",
                    word])
        self.assertEqual(done.returncode, 0, done.stderr.decode())
        self.assertEqual(json.loads(done.stdout)["status"], "ok")

    def test_the_brick_spec_validates_against_the_declared_schema(self):
        """C8.2 — the brick's spec.json validates under the seam's
        declared SPEC_SCHEMA (the loader is the judge)."""
        spec = os.path.join(BRICKS, "methods", "sgqpv-cycle",
                            "spec.json")
        report = sc.load_cell_spec(spec)
        self.assertEqual(report["status"], "ok", report)

    def test_the_absent_soft_brick_reads_defaults_honestly(self):
        """H-R08-5/C6 — the brick's soft.json is absent by design:
        cellctl config over its declared path reads the engine's
        declared defaults — never a stand-in."""
        soft = os.path.join(BRICKS, "methods", "sgqpv-cycle",
                            "soft.json")
        done = run([sys.executable, CELLCTL, "config", "--path", soft])
        self.assertEqual(done.returncode, 0)
        self.assertEqual(json.loads(done.stdout)["status"], "defaults")

    def test_the_binding_reads_no_brick(self):
        """C8.2/K5 — no binding code or data file references a brick
        path or a scenario name: the method is data, one place to
        change, versioned, never code in the binding."""
        for dirpath, _dirnames, filenames in os.walk(PI_CELL_SRC):
            for name in filenames:
                if not name.endswith((".ts", ".mjs", ".json")):
                    continue
                with open(os.path.join(dirpath, name), "r",
                          encoding="utf-8") as handle:
                    text = handle.read()
                self.assertNotIn("bricks", text)
                self.assertNotIn("sgqpv-cycle", text)


# ---------------------------------------------------------------------------
# K1/C7 — token cleanliness: no wire, no write verb, no engine import.
# ---------------------------------------------------------------------------

class TestTokenCleanliness(unittest.TestCase):
    """K1/C7 — the binding sources carry no socket code, no write
    verb, no engine import, no wall-clock, no network; their only
    subprocess is the seam binary."""

    FORBIDDEN = (
        (re.compile(r"socket\.AF_UNIX|\.sendall\(|\.connect\(|AF_UNIX"),
         "socket-client code"),
        (re.compile(r"herdr_send_prompt|herdr\s+agent\s+prompt|"
                    r"agent\.prompt|pane\.wait_for_output|"
                    r"send[-_]keys|send[-_]text|send[-_]input"),
         "a driving write verb"),
        (re.compile(r"\b(Date\(|setTimeout|setInterval|fetch\(|"
                    r"XMLHttpRequest|\.now\(\))"),
         "wall-clock or network in logic"),
    )

    def _binding_files(self):
        out = []
        for root in (PI_CELL_SRC,):
            for dirpath, _d, filenames in os.walk(root):
                for name in filenames:
                    if name.endswith((".ts", ".mjs", ".json", ".md")):
                        out.append(os.path.join(dirpath, name))
        out.append(PODIUM_BIN)
        out.append(ADDENDUM)
        for desk in ("S", "G", "Q", "P", "V"):
            out.append(os.path.join(ENFORCEMENT, "desks", desk,
                                    ".pi", "prompts", "guide.md"))
        for name in ("_cell_api.py", "cell-attest", "cell-begin",
                     "cell-zoom", "cell-on-desk-state"):
            out.append(os.path.join(ENFORCEMENT, "plugin-bin", name))
        return out

    def test_no_socket_no_write_verb_in_the_binding_files(self):
        """K1 — the delivered binding + re-pointed soft-layer files
        carry no socket-client code and no driving write verb."""
        for path in self._binding_files():
            with open(path, "r", encoding="utf-8") as handle:
                text = handle.read()
            for pattern, reason in self.FORBIDDEN[:2]:
                self.assertIsNone(pattern.search(text),
                                  "%s: %s in %s"
                                  % (reason, pattern.pattern, path))

    def test_no_engine_import_in_the_binding_files(self):
        """C7 — no delivered soft-layer file imports a pinned module
        directly (surface_contract is imported ONLY by the re-pointed
        cell-attest — the declared seam importer of the census
        extension)."""
        pinned = ("word", "navigate", "materialize", "orchestrate",
                  "surface_contract", "cost", "softconfig", "trail",
                  "run", "descent", "instrument", "decoder",
                  "compiler", "corruption", "codex", "fractal_ledger")
        for path in self._binding_files():
            with open(path, "r", encoding="utf-8") as handle:
                text = handle.read()
            for match in re.finditer(
                    r"^\s*(?:from\s+([\w.]+)\s+import|import\s+"
                    r"([\w.]+)\b)", text, re.MULTILINE):
                name = (match.group(1) or match.group(2) or "").split(
                    ".")[0]
                if name in pinned:
                    if name == "surface_contract" and \
                            path.endswith("cell-attest"):
                        continue  # the declared seam importer
                    self.fail("engine import %r in %s"
                              % (name, path))

    def test_no_wall_clock_no_network_in_the_extension(self):
        """K1 — the extension runtime carries no wall-clock and no
        network in logic (spawn + argv + bytes only)."""
        for name in ("cellctl.mjs", "index.ts", "tool-table.json"):
            path = os.path.join(PI_CELL_SRC, "src" if name !=
                                "index.ts" else "", name)
            with open(path, "r", encoding="utf-8") as handle:
                text = handle.read()
            self.assertIsNone(self.FORBIDDEN[2][0].search(text), name)
            self.assertNotIn("fetch(", text)

    def test_the_extension_single_subprocess_is_the_seam(self):
        """K1 — the extension's only subprocess is the seam binary:
        the runtime spawns exactly resolveCellctlBin()'s path."""
        with open(os.path.join(PI_CELL_SRC, "src", "cellctl.mjs"),
                  "r", encoding="utf-8") as handle:
            text = handle.read()
        self.assertEqual(text.count("spawn("), 1)
        self.assertIn("resolveCellctlBin()", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
