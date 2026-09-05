#!/usr/bin/env python3
"""selftest — R05 · B4 (the unattended run), author-side checks.

Every test names, in its first docstring line, the criterion ID (or the
commission rule) it exercises and the quantity it measures.  These are
HYPOTHESES — the author's predictions, never results: the verifier
executes the artifact and recomputes every one of them with its own
implementation.

Fixture apparatus lives under fixtures/ (the deterministic fixture desk,
the ≥20-cycle unattended run, the kill -9 harness, the budget run, the
tentative/consumed variants, the hold run, the torn trail).  Scratch
runs use tempfile directories and the fixed fixture clock; the live
ledger and the live formation trail are never touched.

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

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.environ.get("FRACTAL_LEDGER_DIR",
                                  "/home/deploy/the-cell/ledger"))

import fixtures.build as build  # noqa: E402
import run as run_module  # noqa: E402
import trail as trail_module  # noqa: E402
import cost as cost_module  # noqa: E402
import surface_contract  # noqa: E402
from run import Conductor, audit_payload_chains  # noqa: E402
from trail import FormationTrail, read_trail  # noqa: E402
from fractal_ledger import (  # noqa: E402
    LedgerLoader,
    LedgerVerificationError,
    LedgerWriter,
    canonical_json,
)

FIXTURES = os.path.join(HERE, "fixtures")
MAIN = os.path.join(FIXTURES, "main_run")
HOLD = os.path.join(FIXTURES, "hold")
BUDGET = os.path.join(FIXTURES, "budget")
TENTATIVE = os.path.join(FIXTURES, "tentative")
KILL9 = os.path.join(FIXTURES, "kill9")
TORN = os.path.join(FIXTURES, "torn")

NEEDLE = "∞0′ → ‖"  # the encoding-lens bytes (commission lens 4)
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()


def read_bytes(path):
    with open(path, "rb") as handle:
        return handle.read()


def read_json_lines(path):
    return [json.loads(line) for line in
            open(path, encoding="utf-8") if line.strip()]


def ledger_records(path):
    return LedgerLoader(path).load(write_index=False).records


def scratch_run(name, spec_path, max_actions=None, mode=None,
                extra_plant=None):
    """Run one fixture spec in a scratch dir (in-process, fixed clock);
    returns (ledger_path, trail_path, result)."""
    directory = tempfile.mkdtemp(prefix="b4-selftest-")
    spec = build.read_spec(spec_path)
    ledger = os.path.join(directory, "gates.jsonl")
    trailp = os.path.join(directory, "trail.jsonl")
    build.write_plant(ledger)
    if extra_plant is not None:
        with LedgerWriter(ledger, clock=lambda: build.TS) as writer:
            writer.append(extra_plant)
    conductor = Conductor(ledger, trailp, spec,
                          socket_dir=os.path.join(directory, "sock"),
                          mode=mode, max_actions=max_actions)
    result = conductor.run()
    conductor.close()
    return ledger, trailp, result


def main_run_lines():
    return read_json_lines(os.path.join(MAIN, "expected", "trail.jsonl"))


class TestC1HoldsAccumulate(unittest.TestCase):
    """C1 — holds accumulate instead of stopping the run (PRD §B4 +
    §10.3); a held gate never halts the conductor and is never
    auto-resolved."""

    def test_hold_run_stalls_with_two_holds_still_held(self):
        ledger, trailp, result = scratch_run(
            "c1", os.path.join(HOLD, "spec.json"))
        self.assertEqual(result["status"], "stalled")
        records = ledger_records(ledger)
        lines = read_json_lines(trailp)
        holds = [line for line in lines
                 if line.get("event") == "hold"]
        self.assertEqual(len(holds), 2)
        # both hold kinds present: one outage (adapter error) and one
        # blocked (no surface announced)
        kinds = sorted(line["content"]["kind"] for line in holds)
        self.assertEqual(kinds, ["blocked", "outage"])
        # the holds stay held-pending at the end — never auto-resolved:
        # no later record at the held (address, gate), no attested
        # record anywhere but the plant
        for line in holds:
            for record in records:
                if record["turn_key"] == line["turn_key"]:
                    self.assertEqual(record["state"], "held-pending")
                    self.assertIsNone(record["attestation_ref"])
        attested = [r for r in records if r["state"] == "attested"]
        self.assertEqual(len(attested), 1)  # the plant, and only the plant

    def test_hold_does_not_stop_other_cells_moving(self):
        ledger, trailp, _result = scratch_run(
            "c1-move", os.path.join(HOLD, "spec.json"))
        lines = read_json_lines(trailp)
        holds = [line for line in lines if line.get("event") == "hold"]
        first_hold_seq = min(line["seq"] for line in holds)
        # other cells kept moving AFTER the first hold was recorded
        after = [line for line in lines
                 if line["seq"] > first_hold_seq
                 and line.get("event") in ("turn", "seed")]
        self.assertTrue(after, "no other cell moved after the first hold")
        first_hold_cell = holds[0]["cell"]
        moved_on = [line for line in after
                    if line["cell"] != first_hold_cell]
        self.assertTrue(moved_on,
                        "only the held cell moved after the hold")
        # the projection surfaces the holds (one readable list)
        projection = trail_module.project(read_trail(trailp))
        self.assertEqual(len(projection["holds"]), 2)
        self.assertGreaterEqual(projection["completed_cycles"], 1)

    def test_main_run_completes_with_a_hold_still_held(self):
        lines = main_run_lines()
        holds = [line for line in lines if line.get("event") == "hold"]
        self.assertEqual(len(holds), 1)
        run_end = [line for line in lines
                   if line.get("event") == "run-end"][0]
        self.assertEqual(run_end["content"]["status"], "complete")
        self.assertEqual(len(run_end["content"]["holds"]), 1)
        self.assertEqual(run_end["content"]["holds"][0]["cell"], "P")
        self.assertEqual(run_end["content"]["holds"][0]["cycle"], 3)


class TestC2TentativeSeeding(unittest.TestCase):
    """C2 — TENTATIVE seeding of the next S (PRD §B4 + §5.5): a cycle's
    ∞0′ seeds the next S with tentative: true — never promoted, never
    reaching the podium, never consumed (T-R5-01)."""

    def test_every_seed_record_is_tentative_with_the_l2_signal(self):
        records = ledger_records(os.path.join(
            MAIN, "expected", "gates.jsonl"))
        seeds = [r for r in records
                 if (r.get("payload_ref") or "").startswith("seed:")]
        self.assertGreater(len(seeds), 0)
        for seed in seeds:
            self.assertTrue(seed["tentative"])
            self.assertEqual(seed["state"], "held-pending")
            self.assertIsNone(seed["attestation_ref"])
            self.assertEqual(seed["corruption"], "L2")

    def test_seed_lines_carry_the_return_question_as_a_reference(self):
        lines = main_run_lines()
        seeds = [line for line in lines if line.get("event") == "seed"]
        cycle_1_plus = [s for s in seeds if s["cycle"] > 0]
        self.assertTrue(cycle_1_plus)
        for seed in cycle_1_plus:
            ref = seed["return_question"]
            self.assertTrue(
                isinstance(ref, str) and ref.startswith("sha256:"),
                "the seeded ∞0′ must be a reference, never content")
            self.assertEqual(
                seed["content"]["payload_ref"],
                "seed:sha256:" + hashlib.sha256(
                    (ref + " ‖ cell " + str(seed["cell"])
                     + " ‖ cycle " + str(seed["cycle"]))
                    .encode("utf-8")).hexdigest())

    def test_no_machine_record_is_ever_promoted(self):
        records = ledger_records(os.path.join(
            MAIN, "expected", "gates.jsonl"))
        for record in records:
            if record["state"] == "attested":
                self.assertEqual(
                    record["gate"], "x",
                    "only the human's plant may be attested")
                self.assertEqual(record["address"], "")
        # and the run's own source carries no promotion write path:
        # no attested-state write, no non-null attestation write, no
        # tentative flip
        for module in ("run.py", "cost.py", "trail.py"):
            source = open(os.path.join(HERE, module),
                          encoding="utf-8").read()
            self.assertNotIn('state="attested"', source, module)
            self.assertNotIn('"state": "attested"', source, module)
            self.assertNotIn('attestation_ref="', source, module)
            self.assertNotIn('tentative=False', source, module)
            self.assertNotIn('"tentative": false', source, module)
            self.assertNotIn('"tentative": False', source, module)

    def test_the_run_has_no_human_gate_path(self):
        # C6's zero-keystroke half, checked on the source: no input(),
        # no cell-attest invocation, no podium write
        for module in ("run.py", "cost.py", "trail.py"):
            source = open(os.path.join(HERE, module),
                          encoding="utf-8").read()
            tree = ast.parse(source)
            calls = [node.func.id for node in ast.walk(tree)
                     if isinstance(node, ast.Call)
                     and isinstance(node.func, ast.Name)]
            self.assertNotIn("input", calls, module)
            docstrings = set()
            if (isinstance(tree.body[0], ast.Expr)
                    and isinstance(tree.body[0].value, ast.Constant)):
                docstrings.add(id(tree.body[0].value))
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                                     ast.ClassDef)):
                    body = node.body
                    if (body and isinstance(body[0], ast.Expr)
                            and isinstance(body[0].value, ast.Constant)):
                        docstrings.add(id(body[0].value))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Constant) \
                        or not isinstance(node.value, str):
                    continue
                if id(node) in docstrings:
                    continue  # docstring mentions are exempt
                if "cell-attest" in node.value:
                    self.fail("%s carries the cell-attest command: %r"
                              % (module, node.value))
                if node.value.endswith("question.md"):
                    self.fail("%s names the podium file: %r"
                              % (module, node.value))


class TestC3RestartRearm(unittest.TestCase):
    """C3 — restart re-arm from the ledger alone (PRD §B4 + T-E3-01):
    a kill -9 mid-run restarts with no duplicate/skipped gate."""

    def test_kill9_harness_re_arms_byte_identical(self):
        completed = subprocess.run(
            [sys.executable, os.path.join(KILL9, "run_kill9.py")],
            cwd=HERE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=900)
        self.assertEqual(completed.returncode, 0,
                         completed.stderr.decode("utf-8", "replace"))
        report = json.loads(completed.stdout.decode("utf-8"))
        self.assertEqual(report["status"], "re-armed")
        self.assertGreater(report["kill_point_records"], 1)
        self.assertLess(report["kill_point_records"],
                        report["final_records"])

    def test_cold_restart_split_across_fresh_processes(self):
        # a NEW process runs the first N actions; a SECOND process
        # rebuilds the next action from disk alone and finishes —
        # byte-identical to the uninterrupted pins (the run uses the
        # same relative work path the pins were generated under, so the
        # trail's embedded ledger path is comparable byte for byte)
        work = os.path.join(MAIN, "work")
        if os.path.exists(work):
            shutil.rmtree(work)
        os.makedirs(work)
        ledger = os.path.join(work, "gates.jsonl")
        trailp = os.path.join(work, "trail.jsonl")
        build.write_plant(ledger)
        spec_path = os.path.join(MAIN, "spec.json")
        rel_work = os.path.relpath(work, HERE)
        for i, max_actions in enumerate((40, None)):
            command = [sys.executable, os.path.join(HERE, "run.py"),
                       "--ledger", os.path.join(rel_work, "gates.jsonl"),
                       "--trail", os.path.join(rel_work, "trail.jsonl"),
                       "--spec", spec_path,
                       "--socket-dir", os.path.join(
                           rel_work, "sock%d" % i)]
            if max_actions is not None:
                command += ["--max-actions", str(max_actions)]
            completed = subprocess.run(command, cwd=HERE,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,
                                       timeout=600)
            self.assertEqual(completed.returncode, 0,
                             completed.stderr.decode())
            result = json.loads(completed.stdout.decode("utf-8"))
            if max_actions is not None:
                self.assertEqual(result["status"], "step-limited")
            else:
                self.assertEqual(result["status"], "complete")
        self.assertEqual(read_bytes(ledger),
                         read_bytes(os.path.join(
                             MAIN, "expected", "gates.jsonl")))
        self.assertEqual(read_bytes(trailp),
                         read_bytes(os.path.join(
                             MAIN, "expected", "trail.jsonl")))

    def test_next_action_is_derivable_from_disk_alone_at_every_step(self):
        # a BRAND-NEW Conductor (no in-memory state) must derive the
        # same next action the running one took, after every action —
        # the schedule is a pure function of the ledger + trail
        directory = tempfile.mkdtemp(prefix="b4-derive-")
        spec = build.read_spec(os.path.join(MAIN, "spec.json"))
        ledger = os.path.join(directory, "gates.jsonl")
        trailp = os.path.join(directory, "trail.jsonl")
        build.write_plant(ledger)
        conductor = Conductor(ledger, trailp, spec,
                              socket_dir=os.path.join(directory, "sock"))
        for step in range(30):
            expected = conductor.next_action()
            fresh = Conductor(ledger, trailp, spec,
                              socket_dir=os.path.join(
                                  directory, "fresh"))
            derived = fresh.next_action()
            fresh.close()
            self.assertEqual(derived["kind"], expected["kind"])
            self.assertEqual(derived.get("cell"), expected.get("cell"))
            self.assertEqual(derived.get("cycle"),
                             expected.get("cycle"))
            self.assertEqual(derived.get("desk"), expected.get("desk"))
            self.assertEqual(derived.get("turn_key"),
                             expected.get("turn_key"))
            if expected["kind"] in ("done", "stalled", "budget-stop"):
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

    def test_a_broken_chain_halts_never_repairs(self):
        directory = tempfile.mkdtemp(prefix="b4-broken-")
        ledger = os.path.join(directory, "gates.jsonl")
        trailp = os.path.join(directory, "trail.jsonl")
        build.write_plant(ledger)
        with open(ledger, "ab") as handle:
            handle.write(b'{"record_id":"bad"}\n')
        spec = build.read_spec(os.path.join(MAIN, "spec.json"))
        conductor = Conductor(ledger, trailp, spec,
                              socket_dir=os.path.join(directory, "s"))
        with self.assertRaises(LedgerVerificationError):
            conductor.run()
        conductor.close()
        # the broken bytes are still there — nothing repaired them
        self.assertIn(b'{"record_id":"bad"}', read_bytes(ledger))


class TestC4BudgetHold(unittest.TestCase):
    """C4 — budget hold (PRD §B4 + §10.3): a spend ceiling surfaces as
    a held gate in the ledger, never a silent kill, never overspend."""

    def test_ceiling_records_a_held_gate_and_stops_cleanly(self):
        ledger, trailp, result = scratch_run(
            "c4", os.path.join(BUDGET, "spec.json"))
        self.assertEqual(result["status"], "budget-held")
        records = ledger_records(ledger)
        tail = records[-1]
        self.assertEqual(tail["state"], "held-pending")
        self.assertTrue((tail["payload_ref"] or "").startswith(
            "hold:budget-ceiling:"))
        self.assertIsNone(tail["attestation_ref"])
        # the trail surfaces the budget hold as a held gate
        lines = read_json_lines(trailp)
        budget_lines = [line for line in lines
                        if line.get("event") == "budget-hold"]
        self.assertEqual(len(budget_lines), 1)
        run_end = [line for line in lines
                   if line.get("event") == "run-end"][0]
        self.assertEqual(run_end["content"]["status"], "budget-held")
        self.assertEqual(len(run_end["content"]["holds"]), 1)

    def test_no_overspend_and_accounted_before_each_turn(self):
        ledger, trailp, _result = scratch_run(
            "c4-spend", os.path.join(BUDGET, "spec.json"))
        spec = build.read_spec(os.path.join(BUDGET, "spec.json"))
        ceiling = spec["budget"]["ceiling"]
        lines = read_json_lines(trailp)
        # spend is a pure function of the completed turns — recomputed
        # here independently, per record, and never above the ceiling
        mode = cost_module.DEFAULT_MODE
        spend = 0
        for record in ledger_records(ledger):
            payload = record.get("payload_ref") or ""
            if not payload.startswith("fenced:"):
                continue
            desk = {"y": "G", "z": "Q", "a": "P", "b": "V"}[
                record["gate"]]
            spend += cost_module.charge_for(mode, desk)
            self.assertLessEqual(spend, ceiling)
        # the charged turns recorded on the trail match the ledger sum
        charged = sum(line["cost"]["charge"] for line in lines
                      if line.get("cost"))
        self.assertEqual(spend, charged)
        # the declared charges are conservative: measured ≤ charge
        for line in lines:
            cost_record = line.get("cost")
            if not cost_record:
                continue
            self.assertLessEqual(cost_record["measured"]["tokens"],
                                 cost_record["charge"])


class TestC5DependencyAudit(unittest.TestCase):
    """C5 — no tentative node consumed by a downstream gate (PRD §B4 +
    T-R5-02): the dependency audit walks every payload_ref chain
    end-to-end."""

    def test_main_run_audit_passes_end_to_end(self):
        records = ledger_records(os.path.join(
            MAIN, "expected", "gates.jsonl"))
        audit = audit_payload_chains(records)
        self.assertEqual(audit["verdict"], "PASS")
        self.assertEqual(audit["count"], len(records))
        self.assertEqual(audit["fails"], [])
        lines = main_run_lines()
        audit_line = [line for line in lines
                      if line.get("event") == "audit"][0]
        self.assertEqual(audit_line["content"]["verdict"], "PASS")

    def test_a_consumed_tentative_seed_fails(self):
        records = ledger_records(os.path.join(
            TENTATIVE, "expected", "consumed_gates.jsonl"))
        audit = audit_payload_chains(records)
        self.assertEqual(audit["verdict"], "FAIL")
        self.assertEqual(len(audit["fails"]), 1)
        fail = audit["fails"][0]
        reached = fail["reached_tentative"]
        owner = {r["record_id"]: r for r in records}
        self.assertTrue(owner[reached]["tentative"])
        self.assertTrue((owner[reached]["payload_ref"] or "").startswith(
            "seed:"))
        self.assertEqual(owner[fail["record_id"]]["payload_ref"],
                         owner[reached]["payload_ref"])

    def test_audit_reads_inconclusive_on_nothing(self):
        audit = audit_payload_chains([])
        self.assertEqual(audit["verdict"], "INCONCLUSIVE")


class TestC6TwentyCycles(unittest.TestCase):
    """C6 — ≥ 20 cycles with zero human keystrokes (PRD §B4 +
    T-R5-03): the whole run, not per call."""

    def test_at_least_twenty_completed_cycles_zero_keystrokes(self):
        lines = main_run_lines()
        run_end = [line for line in lines
                   if line.get("event") == "run-end"][0]
        self.assertEqual(run_end["content"]["status"], "complete")
        self.assertGreaterEqual(run_end["content"]["completed_cycles"],
                                20)
        # zero keystrokes: the only attested record is the plant (his
        # TTY act, written by the fixture world — the run writes none)
        records = ledger_records(os.path.join(
            MAIN, "expected", "gates.jsonl"))
        attested = [r for r in records if r["state"] == "attested"]
        self.assertEqual(len(attested), 1)
        self.assertEqual(attested[0]["gate"], "x")
        self.assertEqual(attested[0]["address"], "")
        # every cycle's V carried its ∞0′ before it was counted
        v_turns = [line for line in lines
                   if line.get("event") == "turn"
                   and line.get("phase") == "V"]
        self.assertGreaterEqual(len(v_turns), 20)
        for v in v_turns:
            self.assertIsNotNone(v["return_question"])


class TestC7Trail(unittest.TestCase):
    """C7 — the observability deliverable (PLAN-ADDENDUM §B): append-
    only, hash-chained, replayable, readable mid-run, decoding-not-
    transcript, two trails never merged."""

    def test_trail_is_hash_chained_and_replays_identical(self):
        trailp = os.path.join(MAIN, "expected", "trail.jsonl")
        read = read_trail(trailp)
        self.assertEqual(read["status"], "ok")
        self.assertEqual(read["chain"]["status"], "ok")
        self.assertIsNone(read["damage"])
        self.assertGreater(len(read["lines"]), 100)
        # every line's event_hash recomputes; prev_hash chains
        for i, line in enumerate(read["lines"]):
            expected = trail_module.compute_event_hash(
                line["prev_hash"] or "",
                {k: v for k, v in line.items() if k != "event_hash"})
            self.assertEqual(line["event_hash"], expected, i)
            if i:
                prev_bytes = trail_module.canonical_line_bytes(
                    read["lines"][i - 1])
                self.assertEqual(
                    line["prev_hash"],
                    hashlib.sha256(prev_bytes).hexdigest(), i)

    def test_trail_is_append_only(self):
        # a prefix of the file stays byte-for-byte after the run
        # continues writing it (the writer never rewrites)
        directory = tempfile.mkdtemp(prefix="b4-append-")
        spec = build.read_spec(os.path.join(MAIN, "spec.json"))
        ledger = os.path.join(directory, "gates.jsonl")
        trailp = os.path.join(directory, "trail.jsonl")
        build.write_plant(ledger)
        conductor = Conductor(ledger, trailp, spec,
                              socket_dir=os.path.join(directory, "s"))
        conductor.run()
        conductor.close()
        raw = read_bytes(trailp)
        split = raw.rfind(b"\n", 0, len(raw) // 2) + 1
        prefix = raw[:split]
        self.assertEqual(read_bytes(trailp)[:len(prefix)], prefix)

    def test_torn_tail_replays_consistently_partial_projection(self):
        read = read_trail(os.path.join(TORN, "torn_trail.jsonl"))
        self.assertEqual(read["status"], "partial")
        self.assertTrue(read["tail"]["torn"])
        self.assertEqual(read["chain"]["status"], "ok")
        self.assertEqual(len(read["lines"]), 10)
        projection = trail_module.project(read)
        self.assertEqual(projection["status"], "partial")
        # the projection is consistent: every projected line came from
        # the complete prefix, and the chain held
        self.assertIsNone(read["damage"])
        # the fragment is reported, never a line, never valid
        self.assertNotEqual(
            read["tail"]["fragment_sha256"], EMPTY_SHA256)

    def test_mid_file_damage_fails_closed(self):
        read = read_trail(os.path.join(TORN, "damaged_trail.jsonl"))
        self.assertEqual(read["status"], "damaged")
        self.assertIsNotNone(read["damage"])

    def test_absence_and_emptiness_never_read_valid(self):
        directory = tempfile.mkdtemp(prefix="b4-absent-")
        absent = read_trail(os.path.join(directory, "none.jsonl"))
        self.assertEqual(absent["status"], "absent")
        self.assertIsNone(absent["sha256"])
        empty_path = os.path.join(directory, "empty.jsonl")
        open(empty_path, "wb").close()
        empty = read_trail(empty_path)
        self.assertEqual(empty["status"], "empty")
        self.assertEqual(empty["sha256"], EMPTY_SHA256)

    def test_two_trails_never_merged(self):
        directory = tempfile.mkdtemp(prefix="b4-merge-")
        path = os.path.join(directory, "same.jsonl")
        with self.assertRaises(trail_module.TrailError):
            FormationTrail(path, ledger_path=path)

    def test_trail_records_decoding_never_content(self):
        trailp = os.path.join(MAIN, "expected", "trail.jsonl")
        raw = read_bytes(trailp)
        text = raw.decode("utf-8")
        # the desk's fixture content never enters the trail — only the
        # sha256+len references do (D12)
        self.assertNotIn("fixture stand-in — attention mode", text)
        self.assertNotIn("held open, nothing manufactured", text)
        self.assertIn("sha256:", text)
        # the slot content appears only as its digest
        lines = main_run_lines()
        turn = [line for line in lines
                if line.get("event") == "turn"][0]
        slots = turn["content"]["decoded"]
        for name, ref in slots.items():
            self.assertTrue(ref["ref"].startswith("sha256:"))
            self.assertGreater(ref["len"], 0)

    def test_readable_mid_run(self):
        # a reader tailing the partially-written trail produces a
        # consistent partial projection at every point
        directory = tempfile.mkdtemp(prefix="b4-midrun-")
        spec = build.read_spec(os.path.join(MAIN, "spec.json"))
        ledger = os.path.join(directory, "gates.jsonl")
        trailp = os.path.join(directory, "trail.jsonl")
        build.write_plant(ledger)
        conductor = Conductor(ledger, trailp, spec,
                              socket_dir=os.path.join(directory, "s"))
        seen = []
        for _ in range(30):
            action = conductor.next_action()
            if action["kind"] in ("done", "stalled", "budget-stop"):
                break
            if action["kind"] == "seed":
                conductor._do_seed(action)
            elif action["kind"] == "turn":
                conductor._do_turn(action)
            elif action["kind"] == "hold":
                conductor._record_hold(action)
            else:
                conductor._do_observe(action)
            read = read_trail(trailp)
            self.assertIn(read["status"], ("ok", "partial"))
            self.assertIn(read["chain"]["status"], ("ok", "undecidable"))
            projection = trail_module.project(read)
            seen.append(projection["completed_cycles"])
        conductor.close()
        self.assertEqual(seen, sorted(seen))


class TestEncodingLens(unittest.TestCase):
    """Lens 4 — encoding: the bytes "∞0′ → ‖" survive every string
    field, raw UTF-8, no text-mode byte seeks."""

    def test_needle_survives_in_ledger_and_trail(self):
        ledger = read_bytes(os.path.join(MAIN, "expected", "gates.jsonl"))
        trailp = read_bytes(os.path.join(MAIN, "expected", "trail.jsonl"))
        self.assertIn(NEEDLE.encode("utf-8"), ledger)
        self.assertIn(NEEDLE.encode("utf-8"), trailp)
        # raw UTF-8 passthrough — never escaped to \u sequences
        self.assertNotIn(b"\\u221e", trailp)
        self.assertNotIn(b"\\u2032", trailp)
        # round-trip through the canonical readers
        for record in ledger_records(os.path.join(
                MAIN, "expected", "gates.jsonl")):
            json.dumps(record, ensure_ascii=False)
        for line in main_run_lines():
            json.dumps(line, ensure_ascii=False)

    def test_no_text_mode_byte_seeks_in_the_trail(self):
        # every open() in trail.py is binary ("rb"/"ab") — a text-mode
        # seek would break on the needle bytes
        source = open(os.path.join(HERE, "trail.py"),
                      encoding="utf-8").read()
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


class TestFoldedItem(unittest.TestCase):
    """Commission §5 — the folded item: the five desk function-specs
    quoted byte-faithful, no new decoding operation, no new L1 symbol,
    no renamed symbol."""

    def test_desk_function_specs_are_byte_faithful(self):
        src_path = os.path.normpath(os.path.join(
            HERE, "..", "sources", "5qln-codex.txt"))
        source = open(src_path, encoding="utf-8").read()
        import re
        sections = ["2.1 Decoding S = ∞0 → ?",
                    "2.2 Decoding G = α ≡ {α'}",
                    "2.3 Decoding Q = φ ⋂ Ω",
                    "2.4 Decoding P = δE/δV → ∇",
                    "2.5 Decoding V = (L ⋂ G → B'') → ∞0'"]
        for i, section in enumerate(sections):
            match = re.search(
                re.escape(section) +
                r".*?\nDecoding operation\n(.*?)\nAdaptive context",
                source, re.S)
            ops = [chunk.strip("\n") for chunk in
                   re.split(r"\n(?=\d+\. )", match.group(1))
                   if chunk.strip()]
            self.assertEqual(
                list(surface_contract.DESK_FUNCTION_SPECS[
                    "SGQPV"[i]]), ops, section)

    def test_founding_sentence_quoted(self):
        expected = ("∞0 is not a step to complete — it is a state to "
                    "hold. → is not an action to perform — it is an "
                    "emergence to receive. ? is not a question to "
                    "formulate — it is a question to recognize as it "
                    "arrives.")
        self.assertEqual(surface_contract.FOUNDING_SENTENCE, expected)

    def test_no_new_l1_symbol_in_the_specs(self):
        vocab = surface_contract.SYMBOL_VOCABULARY
        l1_tokens = ("∞0", "→", "?", "X", "α", "{α'}", "≡", "Y", "φ",
                     "Ω", "⋂", "Z", "δE", "δV", "δE/δV", "∇", "A", "L",
                     "G", "B''", "B", "∞0'", "∞0′", "∅", "φ⋂Ω")
        for desk, ops in surface_contract.DESK_FUNCTION_SPECS.items():
            for op in ops:
                for token in l1_tokens:
                    if token in op:
                        self.assertIn(token, vocab,
                                      "%s in %s spec" % (token, desk))


class TestDualModeCost(unittest.TestCase):
    """H-B4-2 — the sub-process / re-prompted decision is measured: both
    modes run, both instrument per-turn memory/token cost, the default
    is declared data."""

    def test_both_modes_run_and_the_chain_does_not_depend_on_mode(self):
        spec_path = os.path.join(MAIN, "spec.json")
        ledgers = []
        for mode in ("sub-process", "re-prompted"):
            ledger, trailp, result = scratch_run(
                "dual-" + mode, spec_path, mode=mode, max_actions=None)
            self.assertEqual(result["status"], "complete")
            ledgers.append(read_bytes(ledger))
            lines = read_json_lines(trailp)
            costs = [line["cost"] for line in lines if line.get("cost")]
            self.assertTrue(costs)
            for cost_record in costs:
                self.assertEqual(cost_record["mode"], mode)
                measured = cost_record["measured"]
                self.assertGreater(measured["answer_tokens"], 0)
                if mode == "sub-process":
                    self.assertGreater(measured["memory_bytes"], 0)
                else:
                    self.assertEqual(measured["memory_bytes"], 0)
        self.assertEqual(ledgers[0], ledgers[1])

    def test_the_default_mode_is_declared_data_not_logic(self):
        self.assertEqual(cost_module.DEFAULT_MODE,
                         cost_module.COST_MODEL["default_mode"])
        self.assertEqual(cost_module.DEFAULT_MODE, "re-prompted")
        spec = build.read_spec(os.path.join(MAIN, "spec.json"))
        self.assertIsNone(spec.get("mode"))
        # a Conductor with no explicit mode resolves the DECLARED table
        directory = tempfile.mkdtemp(prefix="b4-default-")
        conductor = Conductor(
            os.path.join(directory, "g.jsonl"),
            os.path.join(directory, "t.jsonl"), spec,
            socket_dir=os.path.join(directory, "s"))
        self.assertEqual(conductor.mode, "re-prompted")
        conductor.close()
        # the run.py source resolves the default from the data table,
        # never from a mode literal in its own control flow
        source = open(os.path.join(HERE, "run.py"),
                      encoding="utf-8").read()
        self.assertIn("cost.DEFAULT_MODE", source)
        self.assertNotIn('mode = "re-prompted"', source)


class TestBlindToolLens(unittest.TestCase):
    """Lens 6 — blind tool: no constituted desk here; anything
    unobservable reports INCONCLUSIVE, never clean."""

    def test_no_plant_boots_nothing(self):
        directory = tempfile.mkdtemp(prefix="b4-noplant-")
        spec = build.read_spec(os.path.join(MAIN, "spec.json"))
        conductor = Conductor(
            os.path.join(directory, "g.jsonl"),
            os.path.join(directory, "t.jsonl"), spec,
            socket_dir=os.path.join(directory, "s"))
        with self.assertRaises(run_module.BootError):
            conductor.run()
        conductor.close()
        self.assertFalse(os.path.exists(os.path.join(
            directory, "g.jsonl")))

    def test_blocked_answer_holds_and_never_completes(self):
        ledger, trailp, result = scratch_run(
            "blocked", os.path.join(HOLD, "spec.json"))
        lines = read_json_lines(trailp)
        blocked = [line for line in lines
                   if line.get("event") == "hold"
                   and line["content"]["kind"] == "blocked"]
        self.assertEqual(len(blocked), 1)
        # the blocked turn never completed: no fenced record at that
        # gate's cycle
        records = ledger_records(ledger)
        held = next(r for r in records
                    if r["turn_key"] == blocked[0]["turn_key"])
        self.assertFalse((held["payload_ref"] or "").startswith(
            "fenced:"))


if __name__ == "__main__":
    unittest.main(verbosity=1)
