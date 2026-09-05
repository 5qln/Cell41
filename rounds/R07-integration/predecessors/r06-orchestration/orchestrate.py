#!/usr/bin/env python3
"""orchestrate — the conductor (R06 · orchestration, C5/C6): drive a
materialized word over the live desks via the bridge's attested live
mode (the imported instrument socket dialect — never re-authored),
read real states, carry hand-offs, assemble the trace.  The trace
lands per-gate in the B0 ledger, format unchanged; every run ends in
∞0′ — no V without ∞0′.

The Fractal is the spec, quoted — never paraphrased into the criteria:

  D.1:
    "The Cycle is the clockwise read of the cell — the Creative Line
    closed into a ring that returns to center:
    S → G → Q → P → V → ∞0′"

  D.8:
    "∞0′ = ∞0 deepened by the question (the enrichment IS the
    question)
    ∞0′ may seed the next cycle as new ∞0"

  Seal line 8:
    "No V without ∞0'"

One run, one paragraph: boot loads the scenario (the word + the
signed paths — data, never code) from disk alone; the materialize
step is OPTIONAL per run (\"not every run\": the spec may declare a
materialize directory to emit the word's cells, or a materialized
directory whose cells are verified from disk — absent/empty/drifted
cells read INCONCLUSIVE, never valid); the walk then executes the
plan (navigate — the sign-walk, D.6) over the live desks through the
bridge's live mode: ``cost.DeskAdapter(mode=\"live\")`` →
``TurnContext(live_socket, None)`` — NO desk_server.py spawn of any
kind — then the imported B2 ``Instrument`` speaks the real herdr
dialect (label-resolve every turn, ``agent.prompt`` to the resolved
pane, the fenced read to ⟦END …⟧).  An unreachable socket holds
outage; a desk resolving to a pane with no agent holds blocked
``agent_not_found`` — never a fixture stand-in, never a guessed
answer, never clean (lens 6).  The centre guard refuses S/podium
before any byte (the imported B2 assert_not_centre — the seed visit
is never prompted: the conductor is S, §4.8).  Real states are read
at boot through the attested instrument (read-only); an absent socket
is carried honestly.  Every record lands per-gate in the B0 ledger
through ``LedgerWriter`` in B2's proposal shape (held-pending,
mechanical, tentative, attestation null — the run has NO write path
to state attested), keyed by B2's turn_key; beside it, the
observability trail is B4's FormationTrail (imported).  A V turn
whose parsed surface carries no ∞0′ is REFUSED (seal line 8); the
run reports complete ONLY when its final gate is V's and the ∞0′
slot is carried — the return question may seed the next cycle (D.8).

Deterministic and stdlib-only: the live socket is the only I/O, and
it is the attested instrument's (K1).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

sys.dont_write_bytecode = True

from fractal_ledger import (  # noqa: E402
    LedgerLoader,
    LedgerWriter,
    make_record,
)

from surface_contract import (  # noqa: E402
    AgentNotFoundError,
    CentreWriteError,
    DESK_LABELS,
    DeskAdapter,
    EQUATION_FORMS,
    HerdrError,
    Instrument,
    FormationTrail,
    TRAIL_VERSION,
    audit_payload_chains,
    conformance,
    cost,
    grammar,
    materialize,
    navigate,
    parse_surface,
    read_trail,
    seed_ref,
    softconfig,
    turn_key,
    word,
)

__all__ = [
    "Orchestrator",
    "BootError",
    "main",
]

DESKS_WALKED = ("G", "Q", "P", "V")

_GATE_LETTERS = {"x": "S", "y": "G", "z": "Q", "a": "P", "b": "V"}


class BootError(Exception):
    """The run refused to start: the scenario is absent/malformed/
    INCONCLUSIVE, the materialized word is not verifiable, or the
    ledger chain is broken — nothing ran, never a substituted value."""


def _slot(parsed, *names):
    """One decoded slot by name — B4's carried pattern (\"∞0'\" as the
    codex writes it; \"∞0′\" the commission table's glyph — both
    accepted, never normalised, K2)."""
    for name in names:
        if name in (parsed.get("slots") or {}):
            return (parsed.get("slots") or {})[name]
    return None


class _LiveWorld:
    """The walk's world — the conductor's live wiring behind
    navigate's protocol (seed / turn / land / hold / ledger).  Every
    ledger append goes through B0's LedgerWriter (never by hand);
    every desk turn goes through the bridge's live mode + the
    imported instrument (never a fixture desk_server spawn); a step
    whose turn_key already has a fenced record on the ledger is
    reported ``already`` (cold restart — never re-prompted)."""

    def __init__(self, orchestrator):
        self.orchestrator = orchestrator

    def ledger(self):
        return self.orchestrator._authority()

    def seed(self, visit, declared_ref):
        return self.orchestrator._seed_record(visit, declared_ref)

    def turn(self, visit, handoff_ref):
        return self.orchestrator._live_turn(visit, handoff_ref)

    def land(self, visit, payload_ref):
        return self.orchestrator._land_record(visit, payload_ref)

    def hold(self, visit, kind, detail, report):
        return self.orchestrator._hold_record(visit, kind, detail,
                                              report)


class Orchestrator:
    """The orchestration run.  Every path, socket and quantity is a
    caller-supplied parameter (the spec — data); the walk's plan is
    the scenario's word + signed paths (navigate), never a hardcoded
    topology (Appendix D.2/D.6).  A fresh process re-arms from the
    ledger, the trail, the scenario and the materialized directory —
    disk alone (C7, lens 5)."""

    def __init__(self, scenario_path, ledger_path, trail_path,
                 spec=None, clock=None, sources_dir=None,
                 socket_dir=None):
        spec = dict(spec or {})
        self.spec = spec
        self.scenario_path = scenario_path
        self.ledger_path = ledger_path
        self.trail_path = trail_path
        self.socket_dir = socket_dir or (trail_path + ".sockdir")
        self.scope = spec.get("scope") or "orchestration-walk"
        self.block_version = spec.get("block_version") or ""
        self.wait_timeout_ms = spec.get("wait_timeout_ms") or 5000
        self.timeout_s = float(spec.get("timeout_s") or 10.0)
        self.observe_states = bool(spec.get("observe_states", True))
        self.sources_dir = sources_dir or os.path.normpath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "..", "sources"))
        self._clock = self._make_clock(spec.get("clock") or {},
                                       clock)
        self._adapter = None
        # the scenario — data, from disk alone (binary read; absent /
        # empty / malformed never reads valid, lens 3)
        self.scenario_report = word.load_scenario_file(scenario_path)
        if self.scenario_report.get("status") != "ok":
            raise BootError(
                "the scenario %r is %s — never a silently substituted "
                "word: %s" % (scenario_path,
                              self.scenario_report.get("status"),
                              self.scenario_report.get("reason")))
        self.scenario = self.scenario_report["scenario"]
        # the plan — the sign-walk, derived from the signs (D.6)
        self.plan_report = navigate.plan_walk(self.scenario)
        if self.plan_report.get("status") != "ok":
            raise BootError(
                "the walk plan is %s — the word does not walk: %s"
                % (self.plan_report.get("status"),
                   self.plan_report.get("reason")))
        self.plan = self.plan_report["visits"]
        self.pattern = self.plan_report["pattern"]
        # the write path — OPTIONAL per run ("not every run"): emit the
        # word's cells, or verify an already-materialized word from
        # disk; absent/empty/drifted cells read INCONCLUSIVE, never
        # valid (lens 3)
        self.materialize_dir = spec.get("materialize")
        self.materialized_dir = spec.get("materialized")
        self.materialized = None
        if self.materialize_dir is not None:
            report = materialize.materialize(
                self.scenario, self.materialize_dir, visits=self.plan)
            if report.get("status") != "materialized":
                raise BootError(
                    "the materializer refused (INCONCLUSIVE, never a "
                    "substituted cell): %s" % report.get("reason"))
            self.materialized = report
        if self.materialized_dir is not None:
            report = materialize.read_materialized(
                self.scenario, self.materialized_dir, visits=self.plan)
            if report.get("status") != "ok":
                raise BootError(
                    "the materialized word %r is not verifiable — "
                    "INCONCLUSIVE, never used silently: %s"
                    % (self.materialized_dir, report.get("reason")))
            self.materialized = report
        # the ledger — replay + verify the chain (broken halts, exit 4)
        try:
            self._authority()
        except Exception as exc:
            raise BootError("the ledger chain cannot be read: %s" % exc)
        # the trail — B4's apparatus, imported
        self.trail = FormationTrail(trail_path, ledger_path=ledger_path,
                                    clock=self._clock)
        self._trail_key_index = self.trail.turn_key_index()

    # -- clock (declared fixture data) -------------------------------------

    @staticmethod
    def _make_clock(clock_spec, clock):
        if clock is not None:
            return clock
        kind = clock_spec.get("kind") or "fixed"
        if kind == "fixed":
            ts = clock_spec.get("ts") or "2026-08-30T12:00:00.000000Z"
            return lambda: ts
        raise BootError("unknown clock kind %r" % (kind,))

    # -- ledger ------------------------------------------------------------

    def _authority(self):
        loaded = LedgerLoader(self.ledger_path).load(write_index=False)
        by_pair = {}
        for record in loaded.records:
            pair = (record["address"], record["gate"])
            by_pair.setdefault(pair, []).append(record)
        return {"path": self.ledger_path, "records": loaded.records,
                "count": loaded.count, "head": loaded.head,
                "by_pair": by_pair}

    def _append(self, record):
        with LedgerWriter(self.ledger_path, clock=self._clock) as writer:
            return writer.append(record)

    # -- the world's record ops --------------------------------------------

    def _seed_record(self, visit, declared_ref):
        key = turn_key(visit["address"], "x",
                       "step:%d" % visit["index"], self.block_version)
        # cold restart: a seed record already on the ledger is never
        # re-appended (turn_key idempotency — the kill order invariant)
        authority = self._authority()
        for record in authority["records"]:
            if record.get("turn_key") == key:
                return {"record_id": record["record_id"],
                        "payload_ref": record["payload_ref"],
                        "turn_key": key, "count": authority["count"],
                        "head": authority["head"], "already": True}
        payload = seed_ref(declared_ref, visit["address"], visit["index"])
        record = make_record(
            address=visit["address"], gate="x", state="held-pending",
            mark="mechanical", payload_ref=payload,
            axis={"field": {"mode": "anchored", "anchor": payload},
                  "delta": []},
            axis_verdict=None, corruption="L2", tentative=True,
            turn_key=key, block_version=self.block_version,
            attestation_ref=None)
        full = self._append(record)
        authority = self._authority()
        return {"record_id": full["record_id"], "payload_ref": payload,
                "turn_key": key, "count": authority["count"],
                "head": authority["head"]}

    def _land_record(self, visit, payload_ref):
        key = turn_key(visit["address"],
                       grammar.DESK_GATES[visit["letter"]],
                       "step:%d" % visit["index"], self.block_version)
        record = make_record(
            address=visit["address"],
            gate=grammar.DESK_GATES[visit["letter"]],
            state="held-pending", mark="mechanical",
            payload_ref=payload_ref,
            axis={"field": {"mode": "anchored", "anchor": payload_ref},
                  "delta": []},
            axis_verdict=None, corruption=None, tentative=True,
            turn_key=key, block_version=self.block_version,
            attestation_ref=None)
        full = self._append(record)
        authority = self._authority()
        return {"record_id": full["record_id"], "turn_key": key,
                "count": authority["count"],
                "head": authority["head"]}

    def _hold_record(self, visit, kind, detail, report):
        authority = self._authority()
        n = len(authority.get("by_pair", {}).get(
            (visit["address"], grammar.DESK_GATES.get(visit["letter"])),
            []))
        key = turn_key(visit["address"],
                       grammar.DESK_GATES.get(visit["letter"]),
                       "hold:%d" % n, self.block_version)
        payload = "hold:%s:%s:%s:step:%d" % (
            kind, detail, visit["address"] or "eps", visit["index"])
        record = make_record(
            address=visit["address"],
            gate=grammar.DESK_GATES.get(visit["letter"]),
            state="held-pending", mark="mechanical",
            payload_ref=payload,
            axis={"field": {"mode": "anchored", "anchor": payload},
                  "delta": []},
            axis_verdict=None, corruption=None, tentative=True,
            turn_key=key, block_version=self.block_version,
            attestation_ref=None)
        full = self._append(record)
        authority = self._authority()
        return {"record_id": full["record_id"], "turn_key": key,
                "count": authority["count"],
                "head": authority["head"]}

    # -- the live turn (the bridge's attested live mode) -------------------

    def _desk_adapter(self):
        if self._adapter is None:
            self._adapter = DeskAdapter(
                self.spec, self.socket_dir, mode="live",
                live_socket=self.spec.get("live_socket"))
        return self._adapter

    def _key_for(self, visit):
        return turn_key(visit["address"],
                        grammar.DESK_GATES[visit["letter"]],
                        "step:%d" % visit["index"], self.block_version)

    def _existing_fenced(self, visit):
        key = self._key_for(visit)
        authority = self._authority()
        for record in authority["records"]:
            if record.get("turn_key") == key and (record.get(
                    "payload_ref") or "").startswith("fenced:"):
                return record
        return None

    def _prompt_text(self, visit, handoff_ref):
        if self.materialized is not None and self.materialize_dir:
            root = self.materialize_dir
        elif self.materialized is not None:
            root = self.materialized_dir
        else:
            root = None
        if root is not None:
            # the read side of the write path: the materialized cell is
            # read from disk at RUNTIME (binary-only, never text-mode
            # byte seeks — lens 4), the complement of softconfig's
            # runtime config-read
            path = os.path.join(
                root, "_" if visit["address"] == "" else visit[
                    "address"], "SYSTEM.md")
            try:
                with open(path, "rb") as handle:
                    raw = handle.read()
            except OSError as exc:
                raise BootError(
                    "the materialized cell %r is unreadable at run "
                    "time (%s) — INCONCLUSIVE, never substituted"
                    % (path, exc))
            cell_text = raw.decode("utf-8", "replace")
        else:
            # "not every run": without materialization the prompt is
            # the desk grammar at this address (the P4b bundle)
            cell_text = grammar.render_bundle(visit["address"],
                                              visit["letter"])
        name = visit["address"] if visit["address"] else "ε"
        lines = ["⟦TURN cell=%s step=%d desk=%s⟧"
                 % (name, visit["index"], visit["letter"]),
                 "⟦DESK CELL — the materialized node (or the P4b "
                 "bundle)⟧"]
        lines.append(cell_text.rstrip("\n"))
        lines.append("CONTEXT (references only): %s"
                     % (handoff_ref or "∅"))
        return "\n".join(lines)

    def _live_turn(self, visit, handoff_ref):
        """One desk turn through the bridge's live mode — the attested
        instrument dialect, imported, never re-authored.  A step whose
        fenced record already exists (a cold restart continuing the
        same walk) reports ``already`` — never re-prompted (turn_key
        idempotency)."""
        existing = self._existing_fenced(visit)
        if existing is not None:
            return {"status": "already",
                    "payload_ref": existing["payload_ref"],
                    "record_id": existing["record_id"],
                    "turn_key": existing["turn_key"],
                    "detail": "recorded"}
        key = self._key_for(visit)
        prompt = self._prompt_text(visit, handoff_ref)
        context = self._desk_adapter().open_turn(
            visit["address"], visit["index"], visit["letter"])
        try:
            self.instrument = Instrument(
                socket_path=context.socket_path,
                desk_labels=dict(DESK_LABELS),
                timeout_s=self.timeout_s)
            try:
                read = self.instrument.prompt_desk(
                    visit["letter"], prompt, key,
                    timeout_ms=self.wait_timeout_ms)
            finally:
                self.instrument.close()
        except AgentNotFoundError as exc:
            self._desk_adapter().close_turn(context)
            return {"status": "blocked", "detail": "agent_not_found",
                    "reason": ("the live desk resolved by label to a "
                               "pane with no agent — a blocked hold, "
                               "never a fixture stand-in, never a "
                               "guessed answer (lens 6): %s" % exc)}
        except CentreWriteError as exc:
            # caught BEFORE the general HerdrError (the guard error is
            # its subclass): the centre guard refused the write before
            # any byte (K4) — never an outage
            self._desk_adapter().close_turn(context)
            return {"status": "guard-fail", "detail": "centre",
                    "reason": ("the centre guard refused the write "
                               "before any byte (K4): %s" % exc)}
        except HerdrError as exc:
            self._desk_adapter().close_turn(context)
            return {"status": "outage",
                    "detail": type(exc).__name__,
                    "reason": ("an unreachable live socket or a dialect "
                               "failure — an outage hold, never a "
                               "fixture stand-in, never clean (lens 6): "
                               "%s" % exc)}
        self._desk_adapter().close_turn(context)
        answer = read["text"]
        parsed = parse_surface(answer, equation_forms=EQUATION_FORMS)
        if parsed.get("status") == "absent":
            return {"status": "blocked", "detail": "no-surface-announced",
                    "reason": "the desk announced no §3.6 surface — "
                              "nothing valid was read"}
        if parsed.get("status") == "malformed":
            return {"status": "guard-fail",
                    "detail": "surface-malformed",
                    "reason": "the desk's surface does not parse "
                              "lawful — nothing valid was read"}
        payload_ref = "fenced:sha256:" + hashlib.sha256(
            answer.encode("utf-8")).hexdigest()
        return {"status": "answered", "text": answer, "parsed": parsed,
                "payload_ref": payload_ref, "turn_key": key}

    # -- real states (read-only, through the attested instrument) ----------

    def read_states(self):
        """The desks' real states at boot — read-only through the
        imported instrument (label-resolve + pane.get + agent.get).
        An absent/unreachable socket is carried honestly:
        {"status": "absent"} — never a fabricated state (lens 6)."""
        if not self.observe_states:
            return {"status": "not-observed",
                    "reason": "observe_states is off (the caller's "
                              "declared spec)"}
        try:
            instrument = Instrument(
                socket_path=self.spec.get("live_socket"),
                desk_labels=dict(DESK_LABELS),
                timeout_s=self.timeout_s)
            try:
                return {"status": "observed",
                        "desks": instrument.desk_states()}
            finally:
                instrument.close()
        except HerdrError as exc:
            return {"status": "absent",
                    "reason": ("no live socket is reachable at %r — the "
                               "state read is INCONCLUSIVE, never a "
                               "fabricated state (lens 6): %s"
                               % (self.spec.get("live_socket"), exc))}

    # -- the run -----------------------------------------------------------

    def run(self, max_steps=None):
        """The walk: seed → the planned visits over the live desks, the
        D.12 check after every step (navigate — the imported
        conformance), every record per-gate in the B0 ledger, the
        trail beside it.  Ends in ∞0′ or reports why not — never
        clean on nothing.  A re-armed run whose run-end already exists
        on the trail reports ``already-complete`` — nothing is
        re-written, never re-run."""
        if any(line.get("event") == "run-end"
               for line in self._read_trail_lines()):
            return {"status": "already-complete", "ended_in": None,
                    "pattern": self.pattern, "actions": 0}
        states = self.read_states()
        self._emit_boot(states)
        world = _LiveWorld(self)
        result = navigate.walk(
            self.scenario, world, self.scenario["seed"]["ref"],
            sources_dir=self.sources_dir,
            session_lines=self._session_lines(),
            max_steps=max_steps)
        self._emit_steps(result)
        status = result.get("status")
        if max_steps is not None and status == "step-limited":
            return {"status": status, "ended_in": result.get("ended_in"),
                    "pattern": result.get("pattern"),
                    "actions": len(result.get("visits") or [])}
        self._run_end(result)
        return {"status": status, "ended_in": result.get("ended_in"),
                "pattern": result.get("pattern"),
                "actions": len(result.get("visits") or []),
                "return_question": result.get("return_question")}

    # -- trail lines (B4's schema, imported) -------------------------------

    def _session_lines(self):
        return [line for line in self._read_trail_lines()
                if isinstance(line, dict)]

    def _read_trail_lines(self):
        read = read_trail(self.trail_path)
        return read.get("lines") or []

    def _append_line(self, line):
        written = self.trail.append(line)
        key = written.get("turn_key")
        if isinstance(key, str):
            self._trail_key_index.setdefault(key, written["seq"])
        return written

    def _line_base(self):
        return {
            "trail_version": TRAIL_VERSION,
            "scope": self.scope,
            "seq": self.trail.count,
            "ts": None,
            "source": "machine",
            "turn_key": None,
            "cell": None,
            "cycle": None,
            "ledger": None,
            "conformance": None,
            "cost": None,
            "prev_hash": None,
            "event_hash": None,
        }

    def _ledger_block(self):
        authority = self._authority()
        return {"path": self.ledger_path, "count": authority["count"],
                "head": authority["head"]}

    def _emit_boot(self, states):
        if any(line.get("event") == "boot"
               for line in self._read_trail_lines()):
            return  # the restart re-arms — the boot line exists
        line = self._line_base()
        line.update({
            "phase": "NOTE",
            "event": "boot",
            "signal": ("the orchestration boots from the scenario alone: "
                       "the word %r + its signed paths; the pattern is "
                       "read from the signs (D.6); the ledger chain is "
                       "replayed from GENESIS"
                       % (self.scenario["word"],)),
            "content": {
                "word": self.scenario["word"],
                "pattern": self.pattern,
                "seed_address": self.scenario["seed"]["address"],
                "materialize_dir": self.materialize_dir,
                "materialized_dir": self.materialized_dir,
                "live_socket": self.spec.get("live_socket"),
                "desk_states": states,
                "encoding_probe": "∞0′ → ‖",
            },
            "return_question": None,
            "ledger": self._ledger_block(),
        })
        self._append_line(line)

    def _emit_steps(self, result):
        """Append the per-step trail lines from the walk's results, in
        visit order (the writer owns seq + the hash chain).  A step
        whose line already exists (a clean restart boundary) appends
        nothing; a step whose record landed without its line (kill -9
        between the ledger fsync and the trail append) is repaired
        honestly — the live answer's bytes are gone, so the repaired
        line carries the digest only, never a guessed decode (D12)."""
        existing = {line.get("turn_key"): line
                    for line in self._read_trail_lines()
                    if line.get("turn_key")}
        for step in result.get("visits") or []:
            key = step.get("turn_key")
            if key is None:
                continue
            if key in existing or key in self._trail_key_index:
                continue
            self._append_line(self._step_line(step))

    def _step_line(self, step):
        line = self._line_base()
        letter = step.get("letter") or "S"
        turn_key_value = step.get("turn_key")
        if step.get("status") == "seeded":
            event, phase, signal = "seed", "S", (
                "the seed at %r is TENTATIVE (L2 — machine-posed, the "
                "signal carried honestly) and never prompted: the "
                "conductor is S (§4.8); the human's gate act stays a "
                "TTY act (H-ORCH-4)" % (step.get("address"),))
        elif step.get("status") == "observed":
            event, phase, signal = "observe", letter, (
                "the step's record was already on the ledger — the "
                "walk re-armed from disk alone and never re-prompted "
                "(turn_key idempotency, C7)")
        elif step.get("status") == "held":
            event, phase, signal = "hold", letter, (
                "%s: %s — the gate failed to lock; the hold is "
                "recorded and the walk keeps moving (C1, never "
                "auto-resolved)" % (step.get("hold_kind"),
                                    step.get("detail")))
        else:
            event, phase, signal = "turn", letter, (
                "turn of %s at step %d — attended through the live "
                "mode, decoded, compiled" % (letter, step.get("index")))
        content = {"status": step.get("status"),
                   "payload_ref": step.get("payload_ref")}
        if step.get("hold_kind"):
            content["kind"] = step["hold_kind"]
            content["detail"] = step["detail"]
        ledger_block = {"path": self.ledger_path,
                        "count": step.get("ledger_count"),
                        "head": step.get("ledger_head")}
        line.update({
            "phase": phase,
            "event": event,
            "signal": signal,
            "content": content,
            "return_question": step.get("infinite_prime_ref"),
            "turn_key": turn_key_value,
            "cell": step.get("address"),
            "cycle": step.get("index"),
            "ledger": ledger_block,
            "conformance": step.get("conformance"),
        })
        return line

    def _run_end(self, result):
        authority = self._authority()
        audit = audit_payload_chains(authority["records"])
        read = self._read_trail_lines()
        reports = [step.get("conformance")
                   for step in result.get("visits") or []
                   if step.get("conformance")]
        aggregate = conformance.aggregate(
            {"session": {"lines": read},
             "sources_dir": self.sources_dir},
            reports=reports)
        line = self._line_base()
        line.update({
            "phase": "NOTE",
            "event": "run-end",
            "signal": ("the walk ended %s — ended_in %s; every held "
                       "gate is still held, none auto-resolved (C1); "
                       "the dependency audit verdict is %s"
                       % (result.get("status"), result.get("ended_in"),
                          audit["verdict"])),
            "content": {
                "status": result.get("status"),
                "ended_in": result.get("ended_in"),
                "pattern": result.get("pattern"),
                "word": self.scenario["word"],
                "holds": [{"index": step.get("index"),
                           "kind": step.get("hold_kind"),
                           "detail": step.get("detail")}
                          for step in result.get("visits") or []
                          if step.get("hold_kind")],
                "audit_verdict": audit["verdict"],
                "aggregate_conformance": aggregate["verdict"],
                "spend": cost.spend_from_records(
                    authority["records"], "live",
                    charge_for=self._soft_charge),
            },
            "return_question": result.get("return_question"),
            "ledger": self._ledger_block(),
        })
        self._append_line(line)

    def _soft_charge(self, mode, desk):
        """The budget path's charge resolver — the soft layer's value
        (the bridge's read path, imported), never a literal here."""
        return softconfig.budget_of(
            softconfig.load_soft_config(
                self.spec.get("soft_config")), mode, desk)

    def close(self):
        try:
            if self._adapter is not None:
                self._adapter.close()
        finally:
            self.trail.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False


def _load_spec(path):
    with open(path, "rb") as handle:
        return json.loads(handle.read().decode("utf-8"))


def main(argv=None):
    from fractal_ledger import LedgerVerificationError
    parser = argparse.ArgumentParser(prog="orchestrate", description=(
        "the orchestration run: drive a materialized word over the "
        "live desks via the bridge's live mode; the trace lands "
        "per-gate in the B0 ledger.  Exit codes: 0 the run ended on "
        "its declared resources (complete / inconclusive / refused / "
        "step-limited) or the audit passed · 1 config/boot error · 3 "
        "the audit FAILed · 4 the ledger chain broke (halt — never "
        "repair)"))
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--ledger", required=True)
    parser.add_argument("--trail", default=None)
    parser.add_argument("--spec", default=None)
    parser.add_argument("--socket-dir", default=None)
    parser.add_argument("--max-steps", type=int, default=None)
    parser.add_argument("--sources-dir", default=None)
    args = parser.parse_args(argv)
    try:
        if args.trail is None or args.spec is None:
            parser.error("--trail and --spec are required")
        orchestrator = Orchestrator(
            args.scenario, args.ledger, args.trail,
            _load_spec(args.spec), socket_dir=args.socket_dir,
            sources_dir=args.sources_dir)
        result = orchestrator.run(max_steps=args.max_steps)
        orchestrator.close()
        authority = orchestrator._authority()
        audit = audit_payload_chains(authority["records"])
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 3 if audit["verdict"] == "FAIL" else 0
    except LedgerVerificationError as exc:
        print("error: the ledger chain is broken — halt, never "
              "repair: %s" % exc, file=sys.stderr)
        return 4
    except BootError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
