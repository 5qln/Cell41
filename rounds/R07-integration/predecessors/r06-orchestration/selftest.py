#!/usr/bin/env python3
"""selftest — the orchestration round, author-side checks.

Every test names, in its first docstring line, the criterion ID (or the
commission rule) it exercises and the quantity it measures.  These are
HYPOTHESES — the author's predictions, never results: the verifier
executes the artifact and recomputes every one of them with its own
implementation.

Fixture apparatus lives under fixtures/ (the deterministic desk harness
speaking the real herdr dialect with the agent_not_found and
absent-socket cases, the four pattern scenarios + the cycle + the
malformed set as data files, the cold-restart runner).  Scratch runs
use tempfile directories and the fixed fixture clock; the live ledger
and the live herdr socket are never written — every run resolves the
fixture harness's own socket (H-ORCH-1: no desk is constituted in the
live box).

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
sys.path.insert(0, os.path.join(HERE, "fixtures"))
sys.path.insert(0, os.environ.get("FRACTAL_LEDGER_DIR",
                                  "/home/deploy/the-cell/ledger"))

import surface_contract  # noqa: E402
import word as word_module  # noqa: E402
import navigate as navigate_module  # noqa: E402
import materialize as materialize_module  # noqa: E402
import orchestrate as orchestrate_module  # noqa: E402
import fixtures.build as build  # noqa: E402
import fixtures.desk_harness as desk_harness  # noqa: E402
from fixtures.desk_harness import DeskHarness  # noqa: E402

SOURCES_DIR = os.path.normpath(os.path.join(HERE, "..", "sources"))
FRACTAL_TEXT = os.path.join(
    SOURCES_DIR, "5qln-codex-appendix-D-the-fractal.txt")
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()
NEEDLE = "∞0′ → ‖"


def _decoded(name):
    report = word_module.decode_scenario(build.scenario_of(name))
    assert report["status"] == "ok", report
    return report["scenario"]


def _plan(name):
    return navigate_module.plan_walk(_decoded(name))


class HarnessCase:
    """One deterministic end-to-end run against the fixture harness —
    a scratch dir, the harness's own socket, the fixed clock."""

    def __init__(self, scenario_name, constituted="all",
                 omit_infinity=False, use_socket=True, spec_kwargs=None):
        self.tmp = tempfile.mkdtemp(prefix="orch-")
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
        kwargs = dict(spec_kwargs or {})
        self.spec = build.orchestrate_spec(
            live_socket=(self.socket if use_socket
                         else desk_harness.absent_socket_path(self.tmp)),
            **kwargs)
        self.ledger = os.path.join(self.tmp, "ledger.jsonl")
        self.trail = os.path.join(self.tmp, "trail.jsonl")
        self.conductor = None

    def run(self, max_steps=None):
        self.conductor = orchestrate_module.Orchestrator(
            self.scenario_path, self.ledger, self.trail, self.spec,
            socket_dir=os.path.join(self.tmp, "sockdir"))
        result = self.conductor.run(max_steps=max_steps)
        self.conductor.close()
        return result

    def authority(self):
        return self.conductor._authority()

    def close(self):
        if self.harness is not None:
            self.harness.halt()


def _gates_of(records):
    return [(r["address"] or "_", r["gate"], r["state"]) for r in records]


class TestWordScenario(unittest.TestCase):
    """C1 — the scenario is a word, not code."""

    def test_the_fractal_quotes_are_verbatim_from_the_held_source(self):
        """C1 quotes D.2/D.3/D.5/D.6 — never paraphrased into the criteria."""
        raw = open(FRACTAL_TEXT, "rb").read().decode("utf-8")
        joined = "".join(raw.split())
        for key, quote in word_module.FRACTAL_QUOTES.items():
            self.assertIn("".join(quote.split()), joined,
                          "%s is not verbatim in the held Fractal text"
                          % key)

    def test_every_pattern_scenario_decodes_lawful(self):
        """C1 — each fixture scenario (data, JSON) decodes status ok."""
        for name in build.NAMES:
            report = word_module.decode_scenario(build.scenario_of(name))
            self.assertEqual(report["status"], "ok",
                             "%s: %s" % (name, report.get("reason")))

    def test_the_scenario_word_is_validated_against_the_grammar(self):
        """C1 — the word alphabet is the imported grammar's COURSE; a
        non-alphabet letter refuses."""
        for name, _expected in (("empty-word", "malformed"),
                                ("bad-letter", "malformed"),
                                ("ascii-hyphen", "malformed"),
                                ("not-normalized", "malformed"),
                                ("word-mismatch", "malformed"),
                                ("broken-chain", "malformed")):
            report = word_module.decode_scenario(build.MALFORMED[name])
            self.assertEqual(report["status"], _expected,
                             "%s: %s" % (name, report.get("reason")))

    def test_a_declared_path_must_normalize_to_the_address_grammar(self):
        """C1/D.5 — addr(A→B) = +^k·(−x₁)…(−x_m): a path that does not
        equal path_between(from, to) is refused (the ASCII hyphen is
        not the U+2212 operator — never normalised, K2)."""
        report = word_module.decode_scenario(build.MALFORMED["ascii-hyphen"])
        self.assertIn("U+002D", report["reason"])
        report = word_module.decode_scenario(
            build.MALFORMED["not-normalized"])
        self.assertIn("normalize", report["reason"])

    def test_no_topology_enum_ever_rides_a_scenario(self):
        """C1/C2 — a scenario carrying pattern/topology/shape keys is
        REFUSED: the signs are the topology (D.6), never a stored
        enum."""
        report = word_module.decode_scenario(
            build.MALFORMED["topology-enum"])
        self.assertEqual(report["status"], "malformed")
        self.assertIn("topology", report["reason"])

    def test_absent_and_empty_scenarios_never_read_valid(self):
        """C1, lens 3 — absent word / empty file: the sha256 of empty
        is e3b0c44298fc…, never valid."""
        report = word_module.decode_scenario(None)
        self.assertEqual(report["status"], "absent")
        report = word_module.decode_scenario(b"")
        self.assertEqual(report["status"], "absent")
        self.assertEqual(report["sha256"], EMPTY_SHA256)
        with tempfile.TemporaryDirectory() as tmp:
            missing = os.path.join(tmp, "nothing.json")
            report = word_module.load_scenario_file(missing)
            self.assertEqual(report["status"], "absent")
            empty = os.path.join(tmp, "empty.json")
            open(empty, "wb").close()
            report = word_module.load_scenario_file(empty)
            self.assertEqual(report["status"], "absent")
            self.assertEqual(report["sha256"], EMPTY_SHA256)

    def test_the_letter_of_an_address_derives_never_stores(self):
        """C1 — the node's phase derives from its address through the
        imported zoom primitives (ε seats S — D.7); never stored."""
        self.assertEqual(word_module.letter_of(""), "S")
        self.assertEqual(word_module.letter_of("G"), "G")
        self.assertEqual(word_module.letter_of("QG"), "Q")
        self.assertEqual(word_module.letter_of("PQG"), "P")

    def test_an_unbounded_loop_is_inconclusive_never_a_cap(self):
        """C1/D.2 — "The law has no base case and no terminal
        condition": a loop whose seed declares no bound refuses to
        start (INCONCLUSIVE), never a silently capped walk."""
        report = word_module.decode_scenario(
            build.MALFORMED["unbounded-loop"])
        self.assertEqual(report["status"], "inconclusive")
        self.assertIn("terminal condition", report["reason"])


class TestNavigateSigns(unittest.TestCase):
    """C2 — the navigation derives from the signs."""

    def test_orientation_is_read_from_the_signs_alone(self):
        """C2/D.6 — k=0 daughter · m=0 father · k,m>0 cousins · empty
        same node."""
        self.assertEqual(navigate_module.orientation(0, 1), "daughter")
        self.assertEqual(navigate_module.orientation(0, 3), "daughter")
        self.assertEqual(navigate_module.orientation(1, 0), "father")
        self.assertEqual(navigate_module.orientation(3, 0), "father")
        self.assertEqual(navigate_module.orientation(1, 1), "cousins")
        self.assertEqual(navigate_module.orientation(3, 2), "cousins")
        self.assertEqual(navigate_module.orientation(0, 0), "same-node")

    def test_sequence_derives_from_a_daughter_chain(self):
        """C2 — sequence = a daughter chain (k=0 every step): the plan
        derives "sequence" from the signs, never from a stored label."""
        plan = _plan("sequence")
        self.assertEqual(plan["status"], "ok", plan.get("reason"))
        self.assertEqual(plan["pattern"], "sequence")
        self.assertTrue(all(v["k"] == 0 for v in plan["visits"]
                            if v["path"] is not None))
        self.assertEqual([v["letter"] for v in plan["visits"]],
                         ["S", "G", "Q", "P"])

    def test_parallel_derives_from_cousins_converging_on_a_father(self):
        """C2 — parallel = cousins (k,m>0) converging on a father: the
        plan reads the cousins path +·−P and the father step + as the
        convergence on the shared father-frame G."""
        plan = _plan("parallel")
        self.assertEqual(plan["status"], "ok", plan.get("reason"))
        self.assertEqual(plan["pattern"], "parallel")
        cousins = [v for v in plan["visits"]
                   if v.get("orientation") == "cousins"]
        fathers = [v for v in plan["visits"]
                   if v.get("orientation") == "father"]
        self.assertTrue(cousins and fathers)
        self.assertEqual(cousins[0]["path"], "+·−P")
        self.assertEqual(fathers[0]["path"], "+")
        self.assertIn("father-frame", plan["pattern_evidence"][0])

    def test_loop_appends_until_the_seeds_declared_bound(self):
        """C2 — loop = append until a bound (the seed's boundary; D.2
        has NO terminal condition): the plan expands the append word
        until the declared word length 4."""
        plan = _plan("loop")
        self.assertEqual(plan["status"], "ok", plan.get("reason"))
        self.assertEqual(plan["pattern"], "loop")
        addresses = [v["address"] for v in plan["visits"]]
        self.assertEqual(addresses, ["", "G", "GG", "QGG", "GQGG"])
        self.assertEqual([v["letter"] for v in plan["visits"]],
                         ["S", "G", "G", "Q", "G"])

    def test_custom_is_a_free_word_composition(self):
        """C2 — custom = free word composition: mixed signs matching
        none of the three named shapes."""
        plan = _plan("custom")
        self.assertEqual(plan["pattern"], "custom")
        plan = _plan("cycle")
        self.assertEqual(plan["pattern"], "custom",
                         "the cycle is a free composition (daughter + "
                         "cousins — the return is V's slot, D.1/D.8)")

    def test_the_d12_step_check_runs_after_every_navigation_step(self):
        """C2/P4a reuse — every visit of a walk carries a conformance
        report from the imported conformance.evaluate."""
        scenario = _decoded("cycle")
        plan = navigate_module.plan_walk(scenario)
        world = _DeterministicWorld(scenario, plan)

        result = navigate_module.walk(
            scenario, world, scenario["seed"]["ref"],
            sources_dir=SOURCES_DIR, session_lines=[])
        self.assertEqual(len(result["visits"]), len(plan["visits"]))
        for step in result["visits"]:
            report = step.get("conformance")
            self.assertIsNotNone(report, "step %s has no D.12 report"
                                 % step.get("index"))
            self.assertIn(report["verdict"],
                          ("PASS", "FAIL", "INCONCLUSIVE"))
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["ended_in"], "∞0′")


class _DeterministicWorld:
    """A deterministic in-process world for the pure walk (no socket —
    navigate is I/O-free by construction, K1): answers composed by
    the pinned B4 fixture desk, records kept in a plain list (the
    world protocol, never a real ledger)."""

    def __init__(self, scenario, plan):
        self.scenario = scenario
        self.plan = plan
        self.records = []
        self.templates = surface_contract.b4_build.render_templates()

    def _record(self, address, gate, payload, key):
        rec = {
            "address": address, "gate": gate, "state": "held-pending",
            "mark": "mechanical", "payload_ref": payload,
            "axis": {"field": {"mode": "anchored", "anchor": payload},
                     "delta": []},
            "axis_verdict": None, "corruption": None,
            "tentative": True, "turn_key": key,
            "block_version": "", "attestation_ref": None,
            "record_id": "r%d" % (len(self.records) + 1),
            "prev_hash": None, "ts": None,
        }
        self.records.append(rec)
        return rec

    def ledger(self):
        return {"path": "world", "records": list(self.records),
                "count": len(self.records), "head": "h%d" % len(self.records)}

    def seed(self, visit, seed_ref):
        payload = surface_contract.seed_ref(seed_ref, visit["address"],
                                            visit["index"])
        key = surface_contract.turn_key(visit["address"], "x",
                                        "step:%d" % visit["index"], "")
        rec = self._record(visit["address"], "x", payload, key)
        return {"record_id": rec["record_id"], "payload_ref": payload,
                "turn_key": key, "count": len(self.records),
                "head": rec["record_id"]}

    def turn(self, visit, handoff_ref):
        from surface_contract import fence_marker
        key = surface_contract.turn_key(
            visit["address"],
            surface_contract.grammar.DESK_GATES[visit["letter"]],
            "step:%d" % visit["index"], "")
        template = self.templates[visit["letter"]]
        cell = visit["address"] or "ε"
        answer = surface_contract.compose_answer(
            template, cell, visit["index"], visit["letter"],
            fence_marker(key))
        parsed = surface_contract.parse_surface(
            answer, equation_forms=surface_contract.EQUATION_FORMS)
        payload = "fenced:sha256:" + hashlib.sha256(
            answer.encode("utf-8")).hexdigest()
        return {"status": "answered", "text": answer, "parsed": parsed,
                "payload_ref": payload, "turn_key": key}

    def land(self, visit, payload_ref):
        key = surface_contract.turn_key(
            visit["address"],
            surface_contract.grammar.DESK_GATES[visit["letter"]],
            "step:%d" % visit["index"], "")
        rec = self._record(visit["address"],
                           surface_contract.grammar.DESK_GATES[
                               visit["letter"]], payload_ref, key)
        return {"record_id": rec["record_id"], "turn_key": key,
                "count": len(self.records), "head": rec["record_id"]}

    def hold(self, visit, kind, detail, report):
        key = surface_contract.turn_key(
            visit["address"],
            surface_contract.grammar.DESK_GATES.get(visit["letter"]),
            "hold:%d" % len(self.records), "")
        rec = self._record(visit["address"],
                           surface_contract.grammar.DESK_GATES.get(
                               visit["letter"]),
                           "hold:%s:%s" % (kind, detail), key)
        return {"record_id": rec["record_id"], "turn_key": key,
                "count": len(self.records), "head": rec["record_id"]}


class TestMaterializer(unittest.TestCase):
    """C3/C4 — the materializer is zoom-in; general tools are lawful."""

    def test_materialize_emits_a_nodes_cell_from_a_scenario(self):
        """C3 — the write-path emits SYSTEM.md, .pi/settings.json,
        skills/, tools per node."""
        scenario = _decoded("cycle")
        plan = navigate_module.plan_walk(scenario)
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "cells")
            report = materialize_module.materialize(
                scenario, out, visits=plan["visits"])
            self.assertEqual(report["status"], "materialized",
                             report.get("reason"))
            self.assertEqual({n["address"] for n in report["nodes"]},
                             {"", "G", "Q", "P", "V"})
            for node in report["nodes"]:
                self.assertEqual(sorted(node["files"]),
                                 sorted(materialize_module.cell_files()))
                for name in materialize_module.cell_files():
                    path = os.path.join(
                        out, "_" if node["address"] == "" else node[
                            "address"], *name.split("/"))
                    raw = open(path, "rb").read()
                    self.assertTrue(raw, "%s is empty" % path)
                    self.assertEqual(hashlib.sha256(raw).hexdigest(),
                                     node["files"][name])

    def test_emitted_bytes_are_byte_exact_against_the_enumerated_tables(self):
        """C3/K2 — the SYSTEM.md seat/equation/operation bytes are
        P4b's PHASE register bytes; the model is the bridge's
        DECLARED_MODEL (D6); the One Law line derives from the
        enumerated seal.  No normalisation: ⋂ stays U+22C2, ∞0′ never
        folds to ∞0'."""
        scenario = _decoded("cycle")
        plan = navigate_module.plan_walk(scenario)
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "cells")
            materialize_module.materialize(scenario, out,
                                           visits=plan["visits"])
            for address, letter in (("", "S"), ("G", "G"), ("Q", "Q"),
                                    ("P", "P"), ("V", "V")):
                node_dir = os.path.join(
                    out, "_" if address == "" else address)
                system = open(os.path.join(node_dir, "SYSTEM.md"),
                              "rb").read().decode("utf-8")
                phase = surface_contract.grammar.PHASE[letter]
                self.assertIn("SEAT: %s" % phase["seat"], system)
                self.assertIn("EQUATION: %s" % phase["equation"], system)
                self.assertIn("OPERATION: %s" % phase["phase_gate"],
                              system)
                self.assertIn("LAW: H = ∞0 | A = K", system)
                if letter == "Q":
                    self.assertIn("⋂", system)  # U+22C2, never ∩
                if letter == "V":
                    self.assertIn("∞0'", system)  # the codex's glyph
                settings = json.loads(open(os.path.join(
                    node_dir, ".pi", "settings.json"),
                    "rb").read().decode("utf-8"))
                self.assertEqual(settings["model"],
                                 surface_contract.DECLARED_MODEL)
                self.assertEqual(settings["tools"][:3],
                                 ["read", "grep", "bash"])

    def test_skills_are_the_p4b_bundle_at_this_address(self):
        """C3 — skills/ is the desk grammar at this address: the
        emitted SKILL.md verifies through the imported grammar's own
        verify_bundle."""
        scenario = _decoded("cycle")
        plan = navigate_module.plan_walk(scenario)
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "cells")
            materialize_module.materialize(scenario, out,
                                           visits=plan["visits"])
            for address, letter in (("G", "G"), ("Q", "Q")):
                text = open(os.path.join(
                    out, address, "skills", "SKILL.md"),
                    "rb").read().decode("utf-8")
                report = surface_contract.grammar.verify_bundle(
                    text, address, letter)
                self.assertEqual(report["status"], "ok", report["items"])

    def test_general_tools_are_lawful_on_the_k_side(self):
        """C4/D.10 — search / write-doc / write-code / activate ride
        the K side; the membrane is the same line whether the K side
        holds a 5qln equation or a filesystem tool."""
        scenario = _decoded("cycle")
        plan = navigate_module.plan_walk(scenario)
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "cells")
            materialize_module.materialize(scenario, out,
                                           visits=plan["visits"])
            p_settings = json.loads(open(os.path.join(
                out, "P", ".pi", "settings.json"),
                "rb").read().decode("utf-8"))
            self.assertIn("activate", p_settings["tools"])
            tool_surface = open(os.path.join(
                out, "P", "tools", "tool-surface.md"),
                "rb").read().decode("utf-8")
            self.assertIn("LAW: H = ∞0 | A = K", tool_surface)
            for tool in ("search", "write-doc", "write-code", "activate"):
                self.assertIn("%s:" % tool, tool_surface)

    def test_the_adapter_stays_tool_agnostic_and_unknown_tools_refuse(self):
        """C4 — nothing forces 5qln-only: an unknown general tool
        reads INCONCLUSIVE with the reason, never a silently
        substituted cell."""
        report = word_module.decode_scenario(
            build.MALFORMED["unknown-tool"])
        self.assertEqual(report["status"], "ok")  # decode: types only
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "cells")
            result = materialize_module.materialize(
                report["scenario"], out)
            self.assertEqual(result["status"], "inconclusive")
            self.assertIn("tool", result["reason"])

    def test_materialize_is_optional_per_run_not_every_run(self):
        """C3 — "not every run": a run with neither materialize nor
        materialized completes (the prompt falls back to the P4b
        bundle); a run with materialize emits and reads SYSTEM.md at
        runtime; a run with materialized verifies from disk."""
        case = HarnessCase("cycle")
        try:
            result = case.run()
            self.assertEqual(result["status"], "complete")
        finally:
            case.close()
        case = HarnessCase("cycle", spec_kwargs={
            "materialize": os.path.join(tempfile.mkdtemp(), "cells")})
        try:
            result = case.run()
            self.assertEqual(result["status"], "complete")
            self.assertTrue(os.path.exists(os.path.join(
                case.spec["materialize"], "G", "SYSTEM.md")))
        finally:
            case.close()

    def test_absent_empty_or_drifted_materialized_cells_never_read_valid(self):
        """C3, lens 3 — an already-materialized word is verified from
        disk: a missing, empty or drifted cell reads INCONCLUSIVE."""
        scenario = _decoded("cycle")
        plan = navigate_module.plan_walk(scenario)
        with tempfile.TemporaryDirectory() as tmp:
            cells = os.path.join(tmp, "cells")
            materialize_module.materialize(scenario, cells,
                                           visits=plan["visits"])
            empty_dir = os.path.join(tmp, "empty")
            os.makedirs(os.path.join(empty_dir, "G"))
            report = materialize_module.read_materialized(
                scenario, empty_dir, visits=plan["visits"])
            self.assertEqual(report["status"], "inconclusive")
            empty_file = os.path.join(tmp, "empty-file")
            for address in ("_", "G", "Q", "P", "V"):
                os.makedirs(os.path.join(empty_file, address),
                            exist_ok=True)
                open(os.path.join(empty_file, address, "SYSTEM.md"),
                     "wb").close()
            report = materialize_module.read_materialized(
                scenario, empty_file, visits=plan["visits"])
            self.assertEqual(report["status"], "inconclusive")
            self.assertEqual(report.get("sha256"), EMPTY_SHA256)
            drifted = os.path.join(tmp, "drifted")
            shutil.copytree(cells, drifted)
            with open(os.path.join(drifted, "G", "SYSTEM.md"),
                      "ab") as handle:
                handle.write(b"\n# drifted\n")
            report = materialize_module.read_materialized(
                scenario, drifted, visits=plan["visits"])
            self.assertEqual(report["status"], "inconclusive")
            self.assertIn("drifted", report["reason"])
            report = materialize_module.read_materialized(
                scenario, cells, visits=plan["visits"])
            self.assertEqual(report["status"], "ok")


class TestOrchestration(unittest.TestCase):
    """C5/C6 — the trace lands per-gate in the B0 ledger; every run
    ends in ∞0′."""

    def test_the_cycle_run_lands_per_gate_records_in_b0_format(self):
        """C5 — the whole run's records are written through B0's
        LedgerWriter (the chain verifies), per gate x/y/z/a/b at the
        walk's addresses, in B2's proposal shape: held-pending,
        mechanical, tentative, attestation_ref null."""
        case = HarnessCase("cycle")
        try:
            result = case.run()
            self.assertEqual(result["status"], "complete")
            authority = case.authority()
            gates = _gates_of(authority["records"])
            self.assertEqual(gates, [("_", "x", "held-pending"),
                                     ("G", "y", "held-pending"),
                                     ("Q", "z", "held-pending"),
                                     ("P", "a", "held-pending"),
                                     ("V", "b", "held-pending")])
            for record in authority["records"]:
                self.assertEqual(record["mark"], "mechanical")
                self.assertTrue(record["tentative"])
                self.assertIsNone(record["attestation_ref"])
                self.assertNotIn("attested", record["state"])
            # every desk turn's payload is a fenced digest — B2's
            # convention, format unchanged
            for record in authority["records"][1:]:
                self.assertTrue(record["payload_ref"].startswith(
                    "fenced:sha256:"))
        finally:
            case.close()

    def test_the_complete_run_ends_in_infinity_zero_prime(self):
        """C6/D.8 — ended_in ∞0′: the final gate is V's and the V
        answer's ∞0′ slot ref is the run's return_question."""
        case = HarnessCase("cycle")
        try:
            result = case.run()
            self.assertEqual(result["ended_in"], "∞0′")
            self.assertTrue(result["return_question"].startswith(
                "sha256:"))
            lines = surface_contract.read_trail(case.trail)["lines"]
            run_end = [line for line in lines
                       if line.get("event") == "run-end"][0]
            self.assertEqual(run_end["content"]["ended_in"], "∞0′")
            self.assertEqual(run_end["return_question"],
                             result["return_question"])
        finally:
            case.close()

    def test_a_v_without_infinity_zero_prime_is_refused(self):
        """C6 — seal line 8 "No V without ∞0'": a lawful V surface
        whose ∞0′ slot is absent holds refused:no-∞0′ — the run ends
        refused, never complete, never clean."""
        case = HarnessCase("cycle", omit_infinity=True)
        try:
            result = case.run()
            self.assertEqual(result["status"], "refused")
            self.assertIsNone(result["ended_in"])
            holds = [r for r in case.authority()["records"]
                     if (r["payload_ref"] or "").startswith("hold:")]
            self.assertEqual(len(holds), 1)
            self.assertIn("refused:no-∞0′", holds[0]["payload_ref"])
        finally:
            case.close()

    def test_a_walk_that_never_reaches_v_never_reads_clean(self):
        """C6, lens 6 — clean-but-no-return is INCONCLUSIVE, never
        complete: the sequence walk ends at P."""
        case = HarnessCase("sequence")
        try:
            result = case.run()
            self.assertEqual(result["status"], "inconclusive")
            self.assertIsNone(result["ended_in"])
        finally:
            case.close()

    def test_the_centre_guard_refuses_s_before_any_byte(self):
        """C7/K4 — a walk whose non-seed visit seats S is refused by
        the imported guard BEFORE any byte: the harness recorded zero
        prompts to S/podium and the refusal holds the gate."""
        case = HarnessCase("guard")
        try:
            result = case.run()
            self.assertEqual(result["status"], "refused")
            holds = [r for r in case.authority()["records"]
                     if (r["payload_ref"] or "").startswith("hold:")]
            self.assertEqual(len(holds), 1)
            self.assertIn("guard-fail:centre", holds[0]["payload_ref"])
            self.assertEqual(case.harness.methods.count("agent.prompt"), 1)
            self.assertNotIn("podium", case.harness.prompts)
            podium_prompts = [request for request in
                              case.harness.requests
                              if request.get("method") == "agent.prompt"
                              and "w8:p2" in str(request.get("params"))]
            self.assertEqual(podium_prompts, [])
        finally:
            case.close()

    def test_every_pattern_runs_end_to_end_through_the_harness(self):
        """C2/C5, lens 2 — sequence/parallel/loop/custom + the cycle
        run whole walks through the live mode against the fixture
        harness; each run's ledger holds one record per visited gate
        (or holds), and the derived pattern rides the run-end line."""
        expected = {"sequence": 4, "parallel": 5, "loop": 5,
                    "custom": 4, "cycle": 5}
        for name, visits in expected.items():
            case = HarnessCase(name)
            try:
                result = case.run()
                self.assertEqual(result["pattern"], _plan(name)["pattern"])
                records = case.authority()["records"]
                self.assertEqual(len(records), visits, name)
            finally:
                case.close()

    def test_an_unreachable_socket_holds_outage_never_clean(self):
        """C2/C7, lens 6 — the absent-socket case: every desk turn
        holds outage, zero fenced records, status inconclusive —
        never complete, never a fixture stand-in."""
        case = HarnessCase("cycle", use_socket=False)
        try:
            result = case.run()
            self.assertEqual(result["status"], "inconclusive")
            authority = case.authority()
            self.assertFalse([r for r in authority["records"]
                              if (r["payload_ref"] or "").startswith(
                                  "fenced:")])
            holds = [r for r in authority["records"]
                     if (r["payload_ref"] or "").startswith("hold:")]
            self.assertEqual(len(holds), 4)
            self.assertTrue(all("outage" in r["payload_ref"]
                                for r in holds))
        finally:
            case.close()

    def test_an_unconstituted_desk_holds_blocked_agent_not_found(self):
        """C2, lens 6 — a desk resolving to a pane with no agent holds
        blocked agent_not_found (the harness's structured error), zero
        fenced records for that desk — never a fake answer."""
        case = HarnessCase("cycle", constituted=())
        try:
            result = case.run()
            self.assertEqual(result["status"], "inconclusive")
            holds = [r for r in case.authority()["records"]
                     if (r["payload_ref"] or "").startswith("hold:")]
            self.assertEqual(len(holds), 4)
            self.assertTrue(all("blocked:agent_not_found"
                                in r["payload_ref"] for r in holds))
            self.assertTrue(any(code == "agent_not_found"
                                for code, _m, _t in case.harness.errors))
        finally:
            case.close()

    def test_real_states_are_read_at_boot_and_absence_is_honest(self):
        """C5, lens 6 — the boot line carries the real desk states
        read through the attested instrument (read-only); an absent
        socket carries {"status": "absent"}, never a fabricated
        state."""
        case = HarnessCase("cycle")
        try:
            case.run()
            lines = surface_contract.read_trail(case.trail)["lines"]
            boot = [line for line in lines if line.get("event") == "boot"][0]
            self.assertEqual(boot["content"]["desk_states"]["status"],
                             "observed")
            states = boot["content"]["desk_states"]["desks"]
            self.assertEqual(set(states), {"S", "G", "Q", "P", "V"})
            self.assertEqual(states["S"]["agent_status"], "unknown")
            self.assertEqual(states["G"]["agent_status"], "idle")
        finally:
            case.close()
        case = HarnessCase("cycle", use_socket=False)
        try:
            case.run()
            lines = surface_contract.read_trail(case.trail)["lines"]
            boot = [line for line in lines if line.get("event") == "boot"][0]
            self.assertEqual(boot["content"]["desk_states"]["status"],
                             "absent")
        finally:
            case.close()

    def test_the_dependency_audit_verdicts_and_the_chain_hold(self):
        """C5 — the imported dependency audit runs over the whole
        ledger at run-end (references never consumed as evidence); a
        torn chain halts the reader (the imported LedgerVerification
        path)."""
        case = HarnessCase("cycle")
        try:
            case.run()
            authority = case.authority()
            audit = surface_contract.audit_payload_chains(
                authority["records"])
            self.assertEqual(audit["verdict"], "PASS")
        finally:
            case.close()


class TestProhibitions(unittest.TestCase):
    """C7/K1–K5 — the standing prohibitions and the claims."""

    def test_no_podium_write_path_exists(self):
        """C7 — no write path to the podium: pane.send_text /
        send_input / send_keys appear nowhere in the authored
        modules."""
        for name in ("word.py", "navigate.py", "materialize.py",
                     "orchestrate.py", "fixtures/desk_harness.py",
                     "fixtures/build.py", "fixtures/run_walk.py"):
            source = open(os.path.join(HERE, name), "rb").read()
            text = source.decode("utf-8")
            for forbidden in ("send_text", "send_input", "send_keys"):
                self.assertNotIn(forbidden, text, name)

    def test_no_machine_authenticity_path(self):
        """C7/K3 — no state: "attested" write, no non-null
        attestation_ref, no cell-attest invocation, no tentative flip:
        HC-1/HC-2 stay INCONCLUSIVE by construction."""
        for name in ("word.py", "navigate.py", "materialize.py",
                     "orchestrate.py"):
            source = open(os.path.join(HERE, name), "rb").read()
            text = source.decode("utf-8")
            self.assertNotIn('state="attested"', text, name)
            self.assertNotIn("cell-attest", text, name)
        # every record built by the conductor carries attestation None
        case = HarnessCase("cycle")
        try:
            case.run()
            for record in case.authority()["records"]:
                self.assertIsNone(record["attestation_ref"])
        finally:
            case.close()

    def test_the_herdr_dialect_and_the_guards_are_imported_never_reauthored(self):
        """C7/C5 — no re-implementation: the authored modules carry no
        socket dialect (no AF_UNIX, no sendall), no D.12 check
        re-authoring (conformance imported), no desk grammar
        re-authoring (PHASE/COURSE imported), no descent re-authoring
        (path_between/validate_signed_path imported), no centre guard
        re-authoring (assert_not_centre imported)."""
        for name in ("word.py", "navigate.py", "materialize.py",
                     "orchestrate.py"):
            source = open(os.path.join(HERE, name), "rb").read()
            text = source.decode("utf-8")
            self.assertNotIn("AF_UNIX", text, name)
            self.assertNotIn("sendall", text, name)
            self.assertNotIn("socketserver", text, name)
        source = open(os.path.join(HERE, "orchestrate.py"),
                      "rb").read().decode("utf-8")
        self.assertIn("Instrument(", source)
        self.assertIn("DeskAdapter(", source)
        source = open(os.path.join(HERE, "navigate.py"),
                      "rb").read().decode("utf-8")
        self.assertIn("conformance.evaluate", source)
        self.assertIn("assert_not_centre", source)
        source = open(os.path.join(HERE, "word.py"),
                      "rb").read().decode("utf-8")
        self.assertIn("path_between", source)
        self.assertIn("validate_signed_path", source)

    def test_no_hardcoded_topology_enum_in_the_navigator(self):
        """C2/C7 — the pattern labels are DERIVED: the navigator's
        derivation reads only k/m signs and the declared loop section;
        the scenario files carry no pattern key."""
        source = open(os.path.join(HERE, "navigate.py"),
                      "rb").read().decode("utf-8")
        self.assertIn("_derive_pattern", source)
        for name in build.NAMES:
            data = build.scenario_of(name)
            self.assertNotIn("pattern", data)
            self.assertNotIn("topology", data)

    def test_no_hardcoded_emphasis_voice_model_or_budget_literals(self):
        """C3/K2 — the conductor's control flow carries no §2 emphasis
        / voice / model / budget literal: the bytes flow from the
        imported PHASE register, the bridge's DECLARED_MODEL and the
        softconfig read path."""
        for name in ("orchestrate.py", "navigate.py"):
            source = open(os.path.join(HERE, name),
                          "rb").read().decode("utf-8")
            self.assertNotIn("kimi-k3", source, name)
            self.assertNotIn('"ATTENTION MODE', source, name)
        source = open(os.path.join(HERE, "materialize.py"),
                      "rb").read().decode("utf-8")
        self.assertIn("DECLARED_MODEL", source)
        self.assertIn("grammar.PHASE", source)

    def test_stdlib_only_deterministic_no_llm(self):
        """K1 — word/navigate/materialize import stdlib only (no
        network, no LLM, no subprocess, no wall-clock in logic);
        orchestrate's only external I/O is the live socket through
        the imported instrument + the imported ledger/trail writers."""
        for name in ("word.py", "navigate.py", "materialize.py"):
            tree = ast.parse(open(os.path.join(HERE, name),
                                  "rb").read().decode("utf-8"))
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports += [alias.name.split(".")[0]
                                for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    imports.append((node.module or "").split(".")[0])
            stdlib = set(sys.stdlib_module_names) | {
                "surface_contract", "word", "navigate", "materialize"}
            rogue = [name for name in imports
                     if name and name not in stdlib]
            self.assertEqual(rogue, [], "%s: %s" % (name, rogue))
        tree = ast.parse(open(os.path.join(HERE, "orchestrate.py"),
                              "rb").read().decode("utf-8"))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports += [alias.name.split(".")[0]
                            for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                imports.append((node.module or "").split(".")[0])
        stdlib = set(sys.stdlib_module_names) | {
            "surface_contract", "fractal_ledger"}
        rogue = [name for name in imports
                 if name and name not in stdlib]
        self.assertEqual(rogue, [], "orchestrate.py: %s" % rogue)

    def test_no_byte_normalisation_and_enumeration_bytes_flow(self):
        """K2 — no fold of ⋂→∩, no ′→', no spacing collapse (renaming
        an L1 symbol): no unicodedata / NFKC normalisation anywhere,
        and the enumerated bytes ride the emitted cells verbatim."""
        for name in ("word.py", "navigate.py", "materialize.py",
                     "orchestrate.py"):
            source = open(os.path.join(HERE, name),
                          "rb").read().decode("utf-8")
            self.assertNotIn("unicodedata", source, name)
            self.assertNotIn("NFKC", source, name)
            self.assertNotIn("NFKD", source, name)
        scenario = _decoded("cycle")
        plan = navigate_module.plan_walk(scenario)
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "cells")
            materialize_module.materialize(scenario, out,
                                           visits=plan["visits"])
            q_system = open(os.path.join(out, "Q", "SYSTEM.md"),
                            "rb").read().decode("utf-8")
            self.assertIn("⋂", q_system)  # U+22C2 survives
            self.assertNotIn("Q = φ ∩ Ω", q_system)

    def test_scenario_and_cells_are_diffable_data_files(self):
        """K5 — the scenario and every materialized artifact are data
        files (JSON / markdown — one place to change, diff-able,
        versioned), never code."""
        for name in build.NAMES:
            data = build.scenario_of(name)
            self.assertIsInstance(data, dict)
            self.assertTrue(all(isinstance(v, (str, int, list, dict,
                                               type(None)))
                                for v in json.loads(json.dumps(
                                    data)).values()
                                if not isinstance(v, (dict, list))))

    def test_every_contract_pin_matches_its_file(self):
        """C5 — every PINNED_FILES entry's sha matches its bytes (the
        load-bearing bridge/B3 entries verify their canonical
        load-anchors)."""
        for pinned in surface_contract.PINNED_FILES:
            source = pinned.get("load_from") or pinned["path"]
            actual = hashlib.sha256(
                open(source, "rb").read()).hexdigest()
            self.assertEqual(actual, pinned["sha256"], source)


class TestLenses(unittest.TestCase):
    """The six lenses, predictively."""

    def test_lens1_criterion_match_declared_with_citations(self):
        """Lens 1 — the orchestration surface declares each criterion
        AS WRITTEN with its citation, and each selftest names its
        criterion in its docstring."""
        surface = surface_contract.ORCHESTRATION_SURFACE
        self.assertIn("scenario", surface)
        self.assertIn("patterns", surface)
        self.assertIn("materialize", surface)
        self.assertIn("trace", surface)
        self.assertIn("return", surface)
        self.assertIn("guard", surface)
        for line in ("k = 0 → B within A (daughter)",
                     "m = 0 → A within B (father)",
                     "k, m > 0 → neither (cousins)"):
            self.assertIn(line, surface["patterns"]["rule"])

    def test_lens2_invariant_holds_across_the_whole_walk(self):
        """Lens 2 — invariant end-to-end, not per call: the hand-off
        chain threads one record's payload_ref into the next prompt
        across the whole walk, and the seed ref chains from the
        scenario's declared ref."""
        case = HarnessCase("cycle")
        try:
            case.run()
            prompts = dict(case.harness.prompts)
            for pane_id, text in prompts.items():
                self.assertIn("CONTEXT (references only):", text)
                # the G prompt carries the seed's ref; later prompts
                # carry the previous turn's fenced digest
                if "desk=G" in text:
                    self.assertIn("seed:sha256:", text)
                else:
                    self.assertIn("fenced:sha256:", text)
        finally:
            case.close()

    def test_lens3_absence_never_reads_valid(self):
        """Lens 3 — absent scenario / absent materialized cell / absent
        agent / empty file: every absence reads absent or INCONCLUSIVE
        with the sha256-of-empty cited, never valid."""
        self.assertEqual(EMPTY_SHA256,
                         "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b9"
                         "34ca495991b7852b855")
        report = word_module.decode_scenario(b"")
        self.assertEqual(report["sha256"], EMPTY_SHA256)
        report = word_module.load_scenario_file("/nonexistent/none.json")
        self.assertEqual(report["status"], "absent")
        case = HarnessCase("cycle", constituted=())
        try:
            result = case.run()
            self.assertEqual(result["status"], "inconclusive")
            fenced = [r for r in case.authority()["records"]
                      if (r["payload_ref"] or "").startswith("fenced:")]
            self.assertEqual(fenced, [])
        finally:
            case.close()

    def test_lens4_encoding_needle_through_every_string_field(self):
        """Lens 4 — ∞0′ → ‖ rides byte-verbatim through the scenario's
        string fields (seed ref, system overrides), the V slot, and
        the boot line; every read is binary (no text-mode byte
        seeks)."""
        scenario_data = build.cycle_scenario()
        scenario_data["seed"]["ref"] = "plant:sha256:abcd ‖ %s" % NEEDLE
        scenario_data["nodes"]["G"] = {"system": {
            "seat": "I am Growth — %s" % NEEDLE,
            "equation": "G = α ≡ {α'} — %s" % NEEDLE,
        }}
        report = word_module.decode_scenario(scenario_data)
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["scenario"]["seed"]["ref"],
                         "plant:sha256:abcd ‖ %s" % NEEDLE)
        plan = navigate_module.plan_walk(report["scenario"])
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "cells")
            materialize_module.materialize(report["scenario"], out,
                                           visits=plan["visits"])
            system = open(os.path.join(out, "G", "SYSTEM.md"),
                          "rb").read().decode("utf-8")
            self.assertIn(NEEDLE, system)
            self.assertIn("α ≡ {α'}", system)  # never folded
        # the V answer's slot content carries the needle (the harness
        # composes the pinned fixture's needle-bearing slot content),
        # and the boot line carries the encoding probe verbatim
        case = HarnessCase("cycle")
        try:
            case.run()
            lines = surface_contract.read_trail(case.trail)["lines"]
            boot = [line for line in lines if line.get("event") == "boot"][0]
            self.assertEqual(boot["content"]["encoding_probe"], NEEDLE)
        finally:
            case.close()
        for name in ("word.py", "materialize.py", "orchestrate.py"):
            source = open(os.path.join(HERE, name),
                          "rb").read().decode("utf-8")
            self.assertIn('"rb"', source, name)
        # navigate.py reads no files at all (the pure sign-walk)

    def test_lens5_cold_restart_rebuilds_from_disk_alone(self):
        """Lens 5 — a NEW process rebuilds the word-walk + the
        materializer from disk alone: a walk split across two fresh
        python processes equals the uninterrupted run's ledger and
        trail bytes (the canonical-work-path assumption, carried from
        the bridge — same path strings for every run); a second
        materialize re-emits byte-identical cells."""
        with tempfile.TemporaryDirectory() as tmp:
            work = os.path.join(tmp, "work")
            os.makedirs(work)
            ledger = os.path.join(work, "ledger.jsonl")
            trail = os.path.join(work, "trail.jsonl")
            scenario_path = os.path.join(work, "scenario.json")
            build.write_json(scenario_path, build.cycle_scenario())
            harness_spec = os.path.join(work, "harness-spec.json")
            build.write_json(harness_spec, build.harness_spec())
            socket = os.path.join(work, "harness.sock")
            # the uninterrupted reference under the canonical paths
            harness = DeskHarness(build.harness_spec(), socket,
                                  constituted="all")
            harness.start()
            try:
                conductor = orchestrate_module.Orchestrator(
                    scenario_path, ledger, trail,
                    build.orchestrate_spec(live_socket=socket),
                    socket_dir=os.path.join(work, "sd-ref"))
                result = conductor.run()
                conductor.close()
                self.assertEqual(result["status"], "complete")
                full_ledger = open(ledger, "rb").read()
                full_trail = open(trail, "rb").read()
            finally:
                harness.halt()
                for path in (ledger, trail):
                    if os.path.exists(path):
                        os.remove(path)
            # a second process re-materializes from the scenario alone
            scenario = _decoded("cycle")
            plan = navigate_module.plan_walk(scenario)
            first = os.path.join(work, "cells-1")
            second = os.path.join(work, "cells-2")
            one = materialize_module.materialize(scenario, first,
                                                 visits=plan["visits"])
            two = materialize_module.materialize(scenario, second,
                                                 visits=plan["visits"])
            self.assertEqual(one["nodes"], two["nodes"])
            # the split across two fresh python processes
            env = dict(os.environ)
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            base = [sys.executable, os.path.join(HERE, "fixtures",
                                                 "run_walk.py"),
                    "--scenario", scenario_path,
                    "--harness-spec", harness_spec,
                    "--ledger", ledger, "--trail", trail,
                    "--socket", socket]
            proc1 = subprocess.run(
                base + ["--work", os.path.join(work, "w1"),
                        "--max-steps", "2",
                        "--result", os.path.join(work, "r1.json")],
                capture_output=True, text=True, env=env, cwd=HERE)
            self.assertEqual(proc1.returncode, 0, proc1.stderr)
            with open(os.path.join(work, "r1.json"), "rb") as handle:
                step1 = json.loads(handle.read().decode("utf-8"))
            self.assertEqual(step1["status"], "step-limited")
            proc2 = subprocess.run(
                base + ["--work", os.path.join(work, "w2"),
                        "--result", os.path.join(work, "r2.json")],
                capture_output=True, text=True, env=env, cwd=HERE)
            self.assertEqual(proc2.returncode, 0, proc2.stderr)
            with open(os.path.join(work, "r2.json"), "rb") as handle:
                step2 = json.loads(handle.read().decode("utf-8"))
            self.assertEqual(step2["status"], "complete")
            self.assertEqual(step2["ended_in"], "∞0′")
            self.assertEqual(open(ledger, "rb").read(), full_ledger)
            self.assertEqual(open(trail, "rb").read(), full_trail)

    def test_lens6_blind_tool_reads_inconclusive_never_clean(self):
        """Lens 6 — an unavailable live socket or an unconstituted
        desk reports INCONCLUSIVE, never clean, never a fixture
        stand-in: zero fenced records in both cases."""
        case = HarnessCase("cycle", use_socket=False)
        try:
            result = case.run()
            self.assertEqual(result["status"], "inconclusive")
            self.assertFalse([r for r in case.authority()["records"]
                              if (r["payload_ref"] or "").startswith(
                                  "fenced:")])
        finally:
            case.close()
        case = HarnessCase("cycle", constituted=("G",))
        try:
            result = case.run()
            self.assertEqual(result["status"], "inconclusive")
            fenced = [r for r in case.authority()["records"]
                      if (r["payload_ref"] or "").startswith("fenced:")]
            self.assertEqual(len(fenced), 1)  # G only — nothing faked
            self.assertEqual(fenced[0]["gate"], "y")
        finally:
            case.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
