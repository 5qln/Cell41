#!/usr/bin/env python3
"""run — the conductor of the unattended run (R05 · B4, C1–C7).

The unattended run, one paragraph: a conductor that drives the attested
B2 driver's one-cell cycle repeatedly, with zero human keystrokes — when
a gate fails to lock it records a HOLD and keeps other cells moving
instead of stopping (C1); when a cycle returns ∞0′ it seeds the next S
as TENTATIVE — never promoted, never reaching the podium, never
consumed as evidence (C2, C5); it re-arms from the ledger alone after a
kill -9 (turn_key idempotency + the ledger tail — no duplicate, no
skipped gate, C3); and it accounts model spend BEFORE each turn, so a
ceiling reached records a held gate in the ledger and stops cleanly —
never a silent kill, never an overspend (C4).  Beside the gate ledger it
writes the observability trail (trail.py): append-only, hash-chained,
replayable, readable mid-run, decoding-not-transcript (C7).

Imports — the attested rounds, never re-authored (commission §4),
through this round's surface_contract (by path, sha-pinned):
B0's ledger via FRACTAL_LEDGER_DIR (every append through LedgerWriter,
never by hand); B2's driver (this module EXTENDS Driver — the attested
prompt→fence→read runs through the imported Instrument.prompt_desk, and
the turn_key idempotency is the imported turn_key); P4a's D.12 check
(conformance.evaluate — the run's per-step guard, with the declared
turn-validity policy in surface_contract); P4a's STEP_KINDS (the zoom
glyph data); P4b's grammar (COURSE / DESK_GATES / EQUATION_FORMS — the
run carries no five-letter literal); B3's descent (cell_desk_addresses —
the seating convention).  The herdr socket dialect, the D.12 checks, the
desk grammar and the descent are never re-implemented here.

What B2's walk gating was, this run cannot use: B2's Driver walks by
attestation (position_from reads attested records only), and an
unattended run has no attestations by definition (T-R5-03 — the only
attestation writer is the TTY-guarded cell-attest, which this run never
invokes).  The conductor's schedule is therefore its own layer ON the
attested driver: the next action is a pure function of the ledger alone
(RUN_SURFACE["schedule"]), each turn still runs the attested
prompt→fence→read→propose mechanics, and every record keeps B2's
proposal shape (held-pending, mechanical, tentative, attestation null —
the run has NO write path to state "attested").

The conductor never prompts the centre S (T-R3-02: the inherited centre
guard refuses it, and the course walked is G Q P V); the seeded S is a
ledger record, tentative, and the podium (question.md / his plant) has
no machine path (H-B4-4).

Every path, cell list, cycle target and ceiling is a caller-supplied
parameter (the spec — data), never a hard-coded cap (Appendix D.2: no
root, no leaf).  Deterministic and stdlib-only.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import surface_contract  # noqa: E402  (the sha-pinned seam)
from surface_contract import (  # noqa: E402
    ATTENTION_READINGS,
    DESK_FIDELITY_ITEMS,
    DESK_FUNCTION_SPECS,
    FOUNDING_SENTENCE,
    HerdrError,
    Instrument,
    STEP_KINDS,
    Driver,
    conformance,
    fence_marker,
    grammar,
    parse_surface,
    turn_key,
)
from fractal_ledger import (  # noqa: E402
    LedgerLoader,
    LedgerWriter,
    LedgerVerificationError,
    make_record,
)
import cost  # noqa: E402
import trail  # noqa: E402
from trail import FormationTrail, TRAIL_VERSION, read_trail  # noqa: E402

__all__ = [
    "Conductor",
    "audit_payload_chains",
    "seed_ref",
    "main",
    "BootError",
]

DESKS_WALKED = ("G", "Q", "P", "V")

def _slot(slots, *names):
    """One decoded slot by name — the source's enumerated forms (the
    grammar declares the slot "∞0'" as the codex writes it; "∞0′" is the
    commission table's glyph — both accepted, never normalised, K2)."""
    for name in names:
        if name in (slots or {}):
            return (slots or {})[name]
    return None

_GATE_LETTERS = {"x": "S", "y": "G", "z": "Q", "a": "P", "b": "V"}
_LETTER_GATES = {"S": "x", "G": "y", "Q": "z", "P": "a", "V": "b"}


class BootError(Exception):
    """The run refused to start: the plant is not attested on the ledger,
    the chain is broken, or the spec is not lawful — nothing ran."""


class Conductor(Driver):
    """The unattended run.  Extends B2's Driver (the attested ledger
    replay, the fence conventions, the centre guard) and adds the
    conductor layer: the schedule, the holds, the seeding, the budget,
    the audit and the trail.

    Every action is derived from the ledger alone (``next_action`` is a
    pure function of the ledger + the trail's line index — never of
    in-process memory), and every record is appended through B0's
    LedgerWriter with the injected clock, so a fresh process re-arms to
    the same bytes.
    """

    def __init__(self, ledger_path, trail_path, spec, socket_dir=None,
                 mode=None, clock=None, max_actions=None,
                 sources_dir=None):
        if not isinstance(spec, dict):
            raise BootError("the run needs a spec object (declared data)")
        self.spec = dict(spec)
        self.cells = tuple(spec.get("cells") or ())
        if not self.cells:
            raise BootError("the spec declares no cells")
        self.scope = spec.get("scope") or "unattended-run"
        self.cycle_target = spec.get("cycle_target")
        if not isinstance(self.cycle_target, int) or self.cycle_target < 0:
            raise BootError("the spec must declare a non-negative cycle "
                            "target (a caller-supplied budget, never a "
                            "hard-coded cap)")
        ceiling = spec.get("budget", {}).get("ceiling")
        self.ceiling = ceiling
        if ceiling is not None and not isinstance(ceiling, int):
            raise BootError("the spec's ceiling must be an integer or null")
        # the mode default is DECLARED DATA — resolved from the cost
        # model's table (cost.COST_MODEL["default_mode"]), never
        # re-literalised here (H-B4-2; the spec may override per run)
        declared_mode = spec.get("mode")
        self.mode = mode if mode is not None else (
            declared_mode if declared_mode in cost.COST_MODEL["modes"]
            else cost.DEFAULT_MODE)
        if self.mode not in cost.COST_MODEL["modes"]:
            raise BootError("unknown desk mode %r" % (self.mode,))
        self.max_actions = max_actions
        self.sources_dir = sources_dir or os.path.normpath(
            os.path.join(_HERE, "..", "sources"))
        self._clock = self._make_clock(spec.get("clock") or {})
        self.socket_dir = socket_dir or (trail_path + ".sockdir")
        self.trail_path = trail_path
        self.block_version = spec.get("block_version") or ""
        self.wait_timeout_ms = spec.get("wait_timeout_ms") or 5000
        self.timeout_s = float(spec.get("timeout_s") or 10.0)
        self._adapter = None
        super().__init__(
            ledger_path=ledger_path,
            socket_path=os.path.join(self.socket_dir,
                                     "never-connected.sock"),
            desk_gates=grammar.DESK_GATES,
            desk_addresses={},  # per-turn, per-cell — never a remembered desk
            course=grammar.COURSE,
            blocks={},
            block_version=self.block_version,
            lens=_NeutralLens(),
            wait_timeout_ms=self.wait_timeout_ms,
            timeout_s=self.timeout_s,
        )
        self.trail = FormationTrail(trail_path, ledger_path=ledger_path,
                                    clock=self._clock)
        # the observe-repair index, rebuilt from the TRAIL alone (a fresh
        # process re-derives it from disk; within one process the appends
        # below keep it exact)
        self._trail_key_index = self.trail.turn_key_index()
        self._descent = surface_contract.load_descent()

    # -- clock (declared fixture data) -------------------------------------

    @staticmethod
    def _make_clock(clock_spec):
        kind = clock_spec.get("kind") or "fixed"
        if kind == "fixed":
            ts = clock_spec.get("ts") or "2026-08-29T12:00:00.000000Z"
            return lambda: ts
        raise BootError("unknown clock kind %r" % (kind,))

    # -- the plant (B2's boot invariant, read from the ledger alone) --------

    def _plant_record(self, authority):
        for record in authority["records"]:
            if (record.get("gate") == "x" and record.get("address") == ""
                    and record.get("state") == "attested"
                    and record.get("attestation_ref") is not None):
                return record
        return None

    def _seats(self, cell):
        return self._descent.cell_desk_addresses(cell)

    def _desks_adapter(self):
        if self._adapter is None:
            self._adapter = cost.DeskAdapter(
                self.spec, self.socket_dir, mode=self.mode)
        return self._adapter

    def close(self):
        try:
            if self._adapter is not None:
                self._adapter.close()
        finally:
            super().close()
            self.trail.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False

    # -- ledger helpers (all pure over the replayed records) ---------------

    @staticmethod
    def _pair_records(authority, address, gate):
        return authority["by_pair"].get((address, gate), [])

    @classmethod
    def _keyed(cls, authority, address, gate, attempt, block_version=""):
        key = turn_key(address, gate, attempt, block_version)
        for record in cls._pair_records(authority, address, gate):
            if record.get("turn_key") == key:
                return record
        return None

    @classmethod
    def _turn_record(cls, authority, address, gate, attempt,
                     block_version=""):
        record = cls._keyed(authority, address, gate, attempt,
                            block_version)
        if record is not None and (record.get("payload_ref") or ""
                                   ).startswith("fenced:"):
            return record
        return None

    @classmethod
    def _hold_for_cycle(cls, authority, address, gate, cycle):
        marker = "cycle:%d" % cycle
        for record in cls._pair_records(authority, address, gate):
            payload = record.get("payload_ref") or ""
            if payload.startswith("hold:") and payload.endswith(marker):
                return record
        return None

    @staticmethod
    def _attested_at(authority, address, gate):
        for record in Conductor._pair_records(authority, address, gate):
            if record.get("state") == "attested" \
                    and record.get("attestation_ref") is not None:
                return record
        return None

    @classmethod
    def _source_ref_for_seed(cls, spec, authority, cell, cycle, plant,
                             seats):
        """The reference the cycle's seed carries: the plant's field
        anchor for a cycle 0 (the human's origin), or the previous
        cycle's V answer's ∞0′ slot ref (regenerated deterministically
        from the spec's template — the same bytes the desk answered)."""
        if cycle == 0:
            return plant["payload_ref"]
        answer = cls._regenerate_answer(spec, cell, cycle - 1, "V")
        parsed = parse_surface(answer, equation_forms=grammar.EQUATION_FORMS)
        slot = _slot(parsed.get("slots"), "∞0′", "∞0'")
        if slot is None:
            raise BootError("the V answer of cycle %d carries no ∞0′ "
                            "reference to seed from" % (cycle - 1,))
        return slot["ref"]

    @classmethod
    def _regenerate_answer(cls, spec, cell, cycle, desk):
        """The fixture desk's answer for (cell, cycle, desk) — a pure
        function of the spec's surface template (the same bytes the desk
        server answered)."""
        import fixtures.desk as desk_module
        template = (spec or {}).get("surface_templates", {}).get(desk)
        if template is None:
            raise BootError("the spec carries no surface template for "
                            "desk %r" % (desk,))
        seat = surface_contract.load_descent().cell_desk_addresses(
            cell)[desk]
        marker = fence_marker(turn_key(
            seat, grammar.DESK_GATES[desk], "cycle:%d" % cycle, ""))
        return desk_module.compose_answer(template, cell, cycle, desk,
                                          marker)

    # -- the schedule (the next action, from the ledger alone) -------------

    def next_action(self, authority=None):
        """The run's exact next action — a pure function of the ledger
        (verified chain + records) and the trail's line index.  No
        in-memory state is consulted (C3).

        The schedule (RUN_SURFACE["schedule"]): rounds of one cycle per
        cell — cells in declared order, cycles ascending.  Within a
        round, a cell's cycle runs seed first, then G Q P V in course
        order; the FIRST due action in that order is the next action.
        A cell whose previous cycle never completed (a held gate, an
        incomplete father) contributes nothing to later rounds — its
        cycle is suspended forever (never retried, never resolved)
        while the other cells keep moving (C1)."""
        authority = authority if authority is not None else self._authority()
        records = authority["records"]
        trail_index = self._trail_key_index
        plant = self._plant_record(authority)
        if plant is None:
            raise BootError(
                "the plant (gate x, address '') is not attested on the "
                "ledger — the run refuses to start from nothing (B2's "
                "boot invariant)")
        # a budget stop already recorded? — derive the stop from the
        # ledger, never from RAM (a kill mid-budget-hold re-arms here)
        for record in records:
            payload = record.get("payload_ref") or ""
            if payload.startswith("hold:budget-ceiling:"):
                if record["turn_key"] not in trail_index:
                    return self._observe_action(record, "hold")
                return {"kind": "budget-stop",
                        "record_id": record["record_id"]}
        completed_cycles = 0
        for cycle in itertools.count():
            for cell in self.cells:
                seats = self._seats(cell)
                # the cycle's S: the human's attested record at the S
                # seat (his act — cycle 0 only), or the machine seed —
                # data-driven, no root assumption (Appendix D.2)
                seed = self._keyed(authority, seats["S"], "x",
                                   "cycle:%d" % cycle,
                                   self.block_version)
                if seed is None:
                    if cycle == 0:
                        attested = self._attested_at(
                            authority, seats["S"], "x")
                        if attested is None:
                            return self._seed_action(
                                cell, 0, plant["payload_ref"], seats["S"])
                        seed_ok = attested  # the human's act — nothing to write
                    else:
                        prev_v = self._turn_record(
                            authority, seats["V"], "b",
                            "cycle:%d" % (cycle - 1), self.block_version)
                        if prev_v is None:
                            continue  # suspended / no material — next cell
                        source = self._source_ref_for_seed(
                            self.spec, authority, cell, cycle, plant,
                            seats)
                        return self._seed_action(cell, cycle, source,
                                                 seats["S"])
                else:
                    if seed["turn_key"] not in trail_index:
                        return self._observe_action(seed, "seed")
                    seed_ok = seed
                suspended = False
                for desk in DESKS_WALKED:
                    addr = seats[desk]
                    gate = grammar.DESK_GATES[desk]
                    attempt = "cycle:%d" % cycle
                    done = self._turn_record(
                        authority, addr, gate, attempt, self.block_version)
                    if done is not None:
                        if done["turn_key"] not in trail_index:
                            return self._observe_action(done, "turn")
                        if desk == "V":
                            completed_cycles += 1
                            if completed_cycles >= self.cycle_target:
                                return {"kind": "done",
                                        "completed_cycles":
                                            completed_cycles,
                                        "cycle_target": self.cycle_target}
                        continue
                    if self._hold_for_cycle(authority, addr, gate, cycle):
                        suspended = True  # the gate failed to lock —
                        break               # never retried, never resolved
                    if desk == "G":
                        father_ok = seed_ok is not None
                    else:
                        prev_desk = DESKS_WALKED[
                            DESKS_WALKED.index(desk) - 1]
                        father_ok = self._turn_record(
                            authority, seats[prev_desk],
                            grammar.DESK_GATES[prev_desk], attempt,
                            self.block_version) is not None
                    if not father_ok:
                        suspended = True
                        break
                    spend = cost.spend_from_records(records, self.mode)
                    charge = cost.charge_for(self.mode, desk)
                    if self.ceiling is not None \
                            and spend + charge > self.ceiling:
                        return self._budget_action(
                            cell, cycle, desk, addr, gate, spend, charge)
                    return self._turn_action(
                        cell, cycle, desk, addr, gate, attempt, spend,
                        charge, seats, plant, authority)
            # the round ended with no due action: when at least one cell
            # completed this cycle, the next round has material (the
            # completed cells' next seeds); when NO cell completed and
            # none has pending work, every gate is held — nothing can
            # ever run again
            any_completed = False
            for cell in self.cells:
                if self._turn_record(
                        authority, self._seats(cell)["V"], "b",
                        "cycle:%d" % cycle, self.block_version) is not None:
                    any_completed = True
                    break
            if any_completed:
                continue
            return {"kind": "stalled",
                    "completed_cycles": completed_cycles,
                    "cycle_target": self.cycle_target}

    # -- action builders ---------------------------------------------------

    def _seed_action(self, cell, cycle, source_ref, seat_s):
        payload_ref = seed_ref(source_ref, cell, cycle)
        key = turn_key(seat_s, "x", "cycle:%d" % cycle, self.block_version)
        record = make_record(
            address=seat_s, gate="x", state="held-pending",
            mark="mechanical", payload_ref=payload_ref,
            axis={"field": {"mode": "anchored", "anchor": payload_ref},
                  "delta": []},
            axis_verdict=None, corruption="L2", tentative=True,
            turn_key=key, block_version=self.block_version,
            attestation_ref=None)
        return {"kind": "seed", "cell": cell, "cycle": cycle,
                "desk": "S", "address": seat_s, "gate": "x",
                "turn_key": key, "record": record,
                "payload_ref": payload_ref, "source_ref": source_ref}

    def _turn_action(self, cell, cycle, desk, addr, gate, attempt, spend,
                     charge, seats, plant, authority):
        key = turn_key(addr, gate, attempt, self.block_version)
        question_ref = self._question_ref(authority, cell, cycle, seats,
                                          plant)
        return {"kind": "turn", "cell": cell, "cycle": cycle, "desk": desk,
                "address": addr, "gate": gate, "turn_key": key,
                "attempt": attempt, "spend": spend, "charge": charge,
                "question_ref": question_ref}

    def _budget_action(self, cell, cycle, desk, addr, gate, spend, charge):
        key = self._hold_key(addr, gate)
        detail = "spend%d:ceiling%d:charge%d" % (spend, self.ceiling,
                                                 charge)
        return self._hold_action(cell, cycle, desk, addr, gate, key,
                                 "budget-ceiling", detail, None)

    def _hold_key(self, addr, gate):
        authority = self._authority()
        n = len(self._pair_records(authority, addr, gate))
        return turn_key(addr, gate, "hold:" + str(n), self.block_version)

    def _hold_action(self, cell, cycle, desk, addr, gate, key, kind,
                     detail, report):
        payload_ref = "hold:%s:%s:%s:%s:cycle:%d" % (
            kind, detail, cell if cell else "eps", gate, cycle)
        record = make_record(
            address=addr, gate=gate, state="held-pending",
            mark="mechanical", payload_ref=payload_ref,
            axis={"field": {"mode": "anchored", "anchor": payload_ref},
                  "delta": []},
            axis_verdict=None, corruption=None, tentative=True,
            turn_key=key, block_version=self.block_version,
            attestation_ref=None)
        return {"kind": "hold", "hold_kind": kind, "detail": detail,
                "cell": cell, "cycle": cycle, "desk": desk,
                "address": addr, "gate": gate, "turn_key": key,
                "record": record, "payload_ref": payload_ref,
                "report": report}

    def _observe_action(self, record, subkind):
        return {"kind": "observe", "subkind": subkind, "record": record}

    @staticmethod
    def _question_ref(authority, cell, cycle, seats, plant):
        seed = Conductor._keyed(authority, seats["S"], "x",
                                "cycle:%d" % cycle)
        if seed is not None:
            return seed["payload_ref"]
        return plant["payload_ref"]

    # -- the prompt (the caller's text: the folded spec + context refs) ----

    def _prompt_text(self, cell, cycle, desk, question_ref, key):
        lines = ["⟦TURN cell=%s cycle=%d desk=%s⟧" % (cell, cycle, desk),
                 "⟦DESK FUNCTION-SPEC — codex §2, attention mode⟧",
                 FOUNDING_SENTENCE,
                 "ATTENTION MODE — %s" % ATTENTION_READINGS[desk]]
        lines.extend(DESK_FUNCTION_SPECS[desk])
        lines.append("CONTEXT (references only): %s" % question_ref)
        lines.append("answer through your §3.6 surface; emit exactly the "
                     "end marker the fence instruction names: %s"
                     % fence_marker(key))
        return "\n".join(lines)

    # -- one turn (the attested prompt→fence→read, then the D.12 guard) ----

    def _do_turn(self, action):
        cell = action["cell"]
        cycle = action["cycle"]
        desk = action["desk"]
        addr = action["address"]
        gate = action["gate"]
        key = action["turn_key"]
        prompt = self._prompt_text(cell, cycle, desk,
                                   action["question_ref"], key)
        context = self._desks_adapter().open_turn(cell, cycle, desk)
        try:
            self.instrument = Instrument(
                socket_path=context.socket_path,
                desk_labels=dict(surface_contract.DESK_LABELS),
                timeout_s=self.timeout_s)
            try:
                read = self.instrument.prompt_desk(
                    desk, prompt, key, source=self.fence_source,
                    timeout_ms=self.wait_timeout_ms)
            finally:
                self.instrument.close()
        except HerdrError as exc:
            self._desks_adapter().close_turn(context)
            hold_action = self._hold_action(
                cell, cycle, desk, addr, gate, self._hold_key(addr, gate),
                "outage", type(exc).__name__, None)
            return self._record_hold(hold_action)
        self._desks_adapter().close_turn(context)
        memory_bytes = context.memory_bytes()
        # H-B4-3: the answer is the fenced read — never the success shape.
        answer = read["text"]
        parsed = parse_surface(answer, equation_forms=grammar.EQUATION_FORMS)
        if parsed.get("status") == "absent":
            hold_action = self._hold_action(
                cell, cycle, desk, addr, gate, self._hold_key(addr, gate),
                "blocked", "no-surface-announced", None)
            return self._record_hold(hold_action)
        if parsed.get("status") == "malformed":
            hold_action = self._hold_action(
                cell, cycle, desk, addr, gate, self._hold_key(addr, gate),
                "guard-fail", "surface-malformed", None)
            return self._record_hold(hold_action)
        # the per-step D.12 check, BEFORE any record (the declared
        # turn-validity policy: DESK_FIDELITY_ITEMS — a FAIL holds the
        # gate; the run keeps other cells moving)
        pre_ctx = self._conformance_ctx(
            cell, cycle, desk, addr, gate, key, parsed,
            outcome={"status": "in-progress", "turn_key": key},
            landed=None, payload_ref=None,
            question_ref=action["question_ref"], ledger=None)
        pre_report = conformance.evaluate(pre_ctx)
        failures = [item["id"] for item in pre_report["items"]
                    if item["verdict"] == "FAIL"
                    and item["id"] in DESK_FIDELITY_ITEMS]
        if failures:
            hold_action = self._hold_action(
                cell, cycle, desk, addr, gate, self._hold_key(addr, gate),
                "guard-fail", "+".join(sorted(failures)), pre_report)
            return self._record_hold(hold_action)
        digest = hashlib.sha256(answer.encode("utf-8")).hexdigest()
        payload_ref = "fenced:sha256:" + digest
        record = make_record(
            address=addr, gate=gate, state="held-pending",
            mark="mechanical", payload_ref=payload_ref,
            axis={"field": {"mode": "anchored", "anchor": payload_ref},
                  "delta": []},
            axis_verdict=None, corruption=None, tentative=True,
            turn_key=key, block_version=self.block_version,
            attestation_ref=None)
        full = self._append(record)  # the ledger record FIRST — the kill
                                     # order invariant (C3)
        authority = self._authority()
        final_ctx = self._conformance_ctx(
            cell, cycle, desk, addr, gate, key, parsed,
            outcome={"status": "proposed", "turn_key": key,
                     "record_id": full["record_id"]},
            landed=full["record_id"], payload_ref=payload_ref,
            question_ref=action["question_ref"], ledger=authority)
        report = conformance.evaluate(final_ctx)
        measured = cost.measured_cost(
            self.mode, desk, len(prompt.encode("utf-8")),
            len(answer.encode("utf-8")),
            bundle_bytes=self._bundle_bytes(desk),
            memory_bytes=memory_bytes)
        cost_record = {"mode": self.mode,
                       "charge": action["charge"],
                       "measured": measured,
                       "spend_before": action["spend"],
                       "spend_after": action["spend"] + action["charge"],
                       "ceiling": self.ceiling}
        return_question = _slot(parsed.get("slots"), "∞0′", "∞0'") \
            if desk == "V" else None
        line = self._turn_line(
            cell, cycle, desk, addr, gate, key, parsed, full, report,
            cost_record, authority, return_question,
            "turn of %s at cycle %d — attended, decoded, compiled"
            % (desk, cycle))
        self._append_line(line)
        return {"status": "proposed", "desk": desk, "cell": cell,
                "cycle": cycle, "record_id": full["record_id"],
                "return_question": return_question}

    def _bundle_bytes(self, desk):
        template = (self.spec.get("surface_templates") or {}).get(desk)
        return len((template or "").encode("utf-8"))

    # -- the seed / the hold / the observe ---------------------------------

    def _do_seed(self, action):
        full = self._append(action["record"])
        authority = self._authority()
        content = {"payload_ref": action["payload_ref"],
                   "tentative": True, "corruption": "L2",
                   "source_ref": action["source_ref"]}
        line = {
            "trail_version": TRAIL_VERSION,
            "scope": self.scope,
            "seq": self.trail.count,
            "ts": None,
            "phase": "S",
            "source": "machine",
            "event": "seed",
            "signal": self._seed_signal(action["cycle"]),
            "content": content,
            "return_question": (action["source_ref"]
                                if action["cycle"] > 0 else None),
            "turn_key": action["turn_key"],
            "cell": action["cell"],
            "cycle": action["cycle"],
            "ledger": {"path": self.ledger_path,
                       "count": authority["count"],
                       "head": authority["head"]},
            "conformance": None,
            "cost": None,
            "prev_hash": None,
            "event_hash": None,
        }
        self._append_line(line)
        return {"status": "seeded", "cell": action["cell"],
                "cycle": action["cycle"], "record_id": full["record_id"]}

    @staticmethod
    def _seed_signal(cycle):
        if cycle > 0:
            return ("the cycle %d ∞0′ seeds the next S as TENTATIVE — "
                    "never promoted, never the podium (C2)" % cycle)
        return ("the plant's field anchor seeds cycle 0 as TENTATIVE "
                "(the human's origin, carried)")

    def _record_hold(self, action):
        """Record the hold in the LEDGER first (the kill order
        invariant), then surface it to the trail.  The hold is never
        auto-resolved: this module has no code path to state attested."""
        full = self._append(action["record"])
        authority = self._authority()
        line = {
            "trail_version": TRAIL_VERSION,
            "scope": self.scope,
            "seq": self.trail.count,
            "ts": None,
            "phase": action["desk"],
            "source": "machine",
            "event": "hold" if action["hold_kind"] != "budget-ceiling"
            else "budget-hold",
            "signal": self._hold_signal(action["hold_kind"],
                                        action["detail"]),
            "content": {"kind": action["hold_kind"],
                        "detail": action["detail"],
                        "payload_ref": action["payload_ref"],
                        "tentative": True},
            "return_question": None,
            "turn_key": action["turn_key"],
            "cell": action["cell"],
            "cycle": action["cycle"],
            "ledger": {"path": self.ledger_path,
                       "count": authority["count"],
                       "head": authority["head"]},
            "conformance": action.get("report"),
            "cost": None,
            "prev_hash": None,
            "event_hash": None,
        }
        self._append_line(line)
        return {"status": "held", "hold_kind": action["hold_kind"],
                "cell": action["cell"], "cycle": action["cycle"],
                "record_id": full["record_id"]}

    @staticmethod
    def _hold_signal(kind, detail):
        return ("%s: %s — the gate failed to lock; the hold is recorded "
                "and the run keeps other cells moving (C1, never "
                "auto-resolved)" % (kind, detail))

    def _do_observe(self, action):
        """The trail-repair action (C3): the turn/seed/hold is already on
        the ledger but its trail line is missing (a kill -9 landed
        between the ledger fsync and the trail append).  Rebuild the
        exact line from the ledger + the deterministic fixture — never
        re-prompt, never re-append a ledger record."""
        record = action["record"]
        subkind = action["subkind"]
        if subkind == "seed":
            line = self._rebuild_seed_line(record)
        elif subkind == "hold":
            line = self._rebuild_hold_line(record)
        else:
            line = self._rebuild_turn_line(record)
        self._append_line(line)
        return {"status": "observed", "subkind": subkind,
                "record_id": record["record_id"]}

    # -- (cell, cycle, desk) recovery from a record (deterministic) --------

    def _record_place(self, record):
        """The place of one run record, derived from the ledger alone:
        the cell from the imported seating of the record's address
        (address = seat(cell, letter) under the D.2 convention), the
        cycle from the hold payload's cycle marker or from the record's
        ordinal among its pair's same-kind records in chain order
        (seeds/turns), shifted by one when the pair holds an attested
        record first (the human's act takes cycle 0)."""
        authority = self._authority()
        address = record["address"]
        gate = record["gate"]
        payload = record.get("payload_ref") or ""
        letter = _GATE_LETTERS.get(gate, "S")
        cell = self._cell_of(address, letter)
        if "cycle:" in payload:
            return cell, int(payload.rsplit("cycle:", 1)[1]), letter
        kind = "seed:" if payload.startswith("seed:") else "fenced:"
        index = 0
        for other in self._pair_records(authority, address, gate):
            other_payload = other.get("payload_ref") or ""
            if not other_payload.startswith(kind):
                continue
            if other.get("record_id") == record.get("record_id"):
                shift = 1 if self._attested_at(
                    authority, address, gate) is not None \
                    and kind == "seed:" else 0
                return cell, index + shift, letter
            index += 1
        return cell, 0, letter

    def _cell_of(self, address, letter):
        for cell in self.cells:
            if self._seats(cell)[letter] == address:
                return cell
        return ""

    @staticmethod
    def _cell_of_hold(payload):
        parts = payload.split(":")
        if len(parts) >= 5:
            cell = parts[3]
            return "" if cell == "eps" else cell
        return ""

    # -- line rebuilds (the same bytes the interrupted process wrote or
    #    would have written) -----------------------------------------------

    def _rebuild_seed_line(self, record):
        authority = self._authority()
        cell, cycle, _letter = self._record_place(record)
        plant = self._plant_record(authority)
        seats = self._seats(cell)
        source_ref = self._source_ref_for_seed(
            self.spec, authority, cell, cycle, plant, seats)
        content = {"payload_ref": record["payload_ref"],
                   "tentative": True, "corruption": "L2",
                   "source_ref": source_ref}
        return {
            "trail_version": TRAIL_VERSION,
            "scope": self.scope,
            "seq": self.trail.count,
            "ts": None,
            "phase": "S",
            "source": "machine",
            "event": "seed",
            "signal": self._seed_signal(cycle),
            "content": content,
            "return_question": source_ref if cycle > 0 else None,
            "turn_key": record["turn_key"],
            "cell": cell,
            "cycle": cycle,
            "ledger": {"path": self.ledger_path,
                       "count": authority["count"],
                       "head": authority["head"]},
            "conformance": None,
            "cost": None,
            "prev_hash": None,
            "event_hash": None,
        }

    def _rebuild_hold_line(self, record):
        authority = self._authority()
        payload = record["payload_ref"]
        parts = payload.split(":")
        hold_kind = parts[1] if len(parts) > 1 else "hold"
        detail = parts[2] if len(parts) > 2 else ""
        cell = self._cell_of_hold(payload)
        cycle = int(payload.rsplit("cycle:", 1)[1]) \
            if "cycle:" in payload else 0
        letter = _GATE_LETTERS.get(record["gate"], "S")
        report = None
        if hold_kind == "guard-fail" and detail != "surface-malformed":
            report = self._rebuild_guard_report(record, cell, cycle,
                                                letter, authority)
        return {
            "trail_version": TRAIL_VERSION,
            "scope": self.scope,
            "seq": self.trail.count,
            "ts": None,
            "phase": letter,
            "source": "machine",
            "event": "hold" if hold_kind != "budget-ceiling"
            else "budget-hold",
            "signal": self._hold_signal(hold_kind, detail),
            "content": {"kind": hold_kind, "detail": detail,
                        "payload_ref": payload, "tentative": True},
            "return_question": None,
            "turn_key": record["turn_key"],
            "cell": cell,
            "cycle": cycle,
            "ledger": {"path": self.ledger_path,
                       "count": authority["count"],
                       "head": authority["head"]},
            "conformance": report,
            "cost": None,
            "prev_hash": None,
            "event_hash": None,
        }

    def _rebuild_guard_report(self, record, cell, cycle, desk, authority):
        key = turn_key(record["address"], record["gate"],
                       "cycle:%d" % cycle, self.block_version)
        answer = self._regenerate_answer(self.spec, cell, cycle, desk)
        parsed = parse_surface(answer, equation_forms=grammar.EQUATION_FORMS)
        pre_ctx = self._conformance_ctx(
            cell, cycle, desk, record["address"], record["gate"], key,
            parsed, outcome={"status": "in-progress", "turn_key": key},
            landed=None, payload_ref=None,
            question_ref=self._question_ref(
                authority, cell, cycle, self._seats(cell),
                self._plant_record(authority)),
            ledger=None)
        return conformance.evaluate(pre_ctx)

    def _rebuild_turn_line(self, record):
        authority = self._authority()
        cell, cycle, desk = self._record_place(record)
        key = record["turn_key"]
        seats = self._seats(cell)
        plant = self._plant_record(authority)
        question_ref = self._question_ref(authority, cell, cycle, seats,
                                          plant)
        prompt = self._prompt_text(cell, cycle, desk, question_ref, key)
        answer = self._regenerate_answer(self.spec, cell, cycle, desk)
        parsed = parse_surface(answer, equation_forms=grammar.EQUATION_FORMS)
        final_ctx = self._conformance_ctx(
            cell, cycle, desk, record["address"], record["gate"], key,
            parsed,
            outcome={"status": "proposed", "turn_key": key,
                     "record_id": record["record_id"]},
            landed=record["record_id"], payload_ref=record["payload_ref"],
            question_ref=question_ref, ledger=authority)
        report = conformance.evaluate(final_ctx)
        spend_after = cost.spend_from_records(authority["records"],
                                              self.mode)
        charge = cost.charge_for(self.mode, desk)
        cost_record = {"mode": self.mode, "charge": charge,
                       "measured": cost.measured_cost(
                           self.mode, desk,
                           len(prompt.encode("utf-8")),
                           len(answer.encode("utf-8")),
                           bundle_bytes=self._bundle_bytes(desk),
                           memory_bytes=0),
                       "spend_before": spend_after - charge,
                       "spend_after": spend_after,
                       "ceiling": self.ceiling}
        return_question = _slot(parsed.get("slots"), "∞0′", "∞0'") \
            if desk == "V" else None
        return self._turn_line(
            cell, cycle, desk, record["address"], record["gate"], key,
            parsed, record, report, cost_record, authority,
            return_question,
            "turn of %s at cycle %d — attended, decoded, compiled"
            % (desk, cycle))

    # -- the conformance context (the D.12 check's input, P4a's contract) --

    def _conformance_ctx(self, cell, cycle, desk, addr, gate, key, parsed,
                         outcome, landed, payload_ref, question_ref,
                         ledger):
        authority = ledger if ledger is not None else self._authority()
        decoded = parsed.get("decoding") or {}
        step = {
            "kind": "turn",
            "desk": desk,
            "gate": gate,
            "address_before": cell,
            "address_after": addr,
            "zoom": {"op": STEP_KINDS["turn"]["zoom_op"],
                     "sign": STEP_KINDS["turn"]["zoom_sign"],
                     "letter": desk,
                     "derived_reading": False},
            "operation": "unattended run turn — cycle %d" % cycle,
            "intent_only": False,
            "outcome": outcome,
            "decoded": {"slots": parsed.get("slots") or {},
                        "source": "desk_surface",
                        "operation_steps": decoded.get("ops") or []},
            "compiled": {"symbol": (parsed.get("compiled") or {}).get(
                "symbol"),
                "gate": gate,
                "landed": landed,
                "payload_ref": payload_ref},
            "context_in": {"records": authority["count"],
                           "head": authority["head"],
                           "prior_outputs": []},
            "surface_parse": parsed,
        }
        return {
            "step": step,
            "ledger": {"path": self.ledger_path,
                       "records": authority["records"],
                       "count": authority["count"],
                       "head": authority["head"]},
            "cell": {"observed": True,
                     "arrangement": list(grammar.COURSE),
                     "surfaces": {desk: parsed},
                     "question_ref": question_ref},
            "session": {"lines": []},
            "sources_dir": self.sources_dir,
        }

    def _turn_line(self, cell, cycle, desk, addr, gate, key, parsed, full,
                   report, cost_record, authority, return_question,
                   signal):
        return {
            "trail_version": TRAIL_VERSION,
            "scope": self.scope,
            "seq": self.trail.count,
            "ts": None,
            "phase": desk,
            "source": "machine",
            "event": "turn",
            "signal": signal,
            "content": {
                "decoded": parsed.get("slots") or {},
                "compiled": {"symbol": (parsed.get("compiled") or {}).get(
                    "symbol"),
                    "gate": gate,
                    "payload_ref": full["payload_ref"]},
                "outcome": {"status": "proposed",
                            "record_id": full["record_id"],
                            "turn_key": key},
            },
            "return_question": return_question,
            "turn_key": key,
            "cell": cell,
            "cycle": cycle,
            "ledger": {"path": self.ledger_path,
                       "count": authority["count"],
                       "head": authority["head"]},
            "conformance": report,
            "cost": cost_record,
            "prev_hash": None,
            "event_hash": None,
        }

    def _append(self, record):
        with LedgerWriter(self.ledger_path, clock=self._clock) as writer:
            return writer.append(record)

    def _append_line(self, line):
        """Append one trail line, keeping the observe-repair index exact."""
        written = self.trail.append(line)
        key = written.get("turn_key")
        if isinstance(key, str):
            self._trail_key_index.setdefault(key, written["seq"])
        return written

    # -- the loop ----------------------------------------------------------

    def run(self):
        """The unattended loop: derive → execute, until a resource ends
        it — the caller-supplied cycle target, the spend ceiling (a
        recorded hold), a step limit, or a stall (no runnable material —
        every gate held or complete).  The run-end audit and the
        held-gate surface are written only at a natural end."""
        authority = self._authority()  # verifies the chain — broken halts
        plant = self._plant_record(authority)
        if plant is None:
            raise BootError(
                "the plant (gate x, address '') is not attested on the "
                "ledger — the run refuses to start from nothing (B2's "
                "boot invariant)")
        self._emit_boot()
        actions_done = 0
        status = None
        while True:
            action = self.next_action()
            if action["kind"] == "done":
                status = "complete"
                break
            if action["kind"] == "stalled":
                status = "stalled"
                break
            if action["kind"] == "budget-stop":
                status = "budget-held"
                break
            if self.max_actions is not None \
                    and actions_done >= self.max_actions:
                status = "step-limited"
                break
            if action["kind"] == "seed":
                self._do_seed(action)
            elif action["kind"] == "turn":
                self._do_turn(action)
            elif action["kind"] == "hold":
                self._record_hold(action)
            elif action["kind"] == "observe":
                self._do_observe(action)
            else:  # pragma: no cover — the schedule builds only the four
                raise BootError("unknown action kind %r" % action["kind"])
            actions_done += 1
        if status != "step-limited":
            self._run_end(status)
        return {"status": status, "actions": actions_done}

    def _emit_boot(self):
        read = read_trail(self.trail_path)
        if any(line.get("event") == "boot" for line in read["lines"]):
            return  # the restart re-arms — the boot line exists
        authority = self._authority()
        plant = self._plant_record(authority)
        line = {
            "trail_version": TRAIL_VERSION,
            "scope": self.scope,
            "seq": self.trail.count,
            "ts": None,
            "phase": "NOTE",
            "source": "machine",
            "event": "boot",
            "signal": ("the chain verified from GENESIS; the plant "
                       "(gate x, address '') is his attested record — "
                       "the run starts from nothing else"),
            "content": {"cells": list(self.cells),
                        "cycle_target": self.cycle_target,
                        "mode": self.mode,
                        "ceiling": self.ceiling,
                        "plant_record_id": plant["record_id"],
                        "plant_payload_ref": plant["payload_ref"],
                        "encoding_probe": "∞0′ → ‖"},
            "return_question": None,
            "turn_key": None,
            "cell": None,
            "cycle": None,
            "ledger": {"path": self.ledger_path,
                       "count": authority["count"],
                       "head": authority["head"]},
            "conformance": None,
            "cost": None,
            "prev_hash": None,
            "event_hash": None,
        }
        self._append_line(line)

    def _run_end(self, status):
        authority = self._authority()
        audit = audit_payload_chains(authority["records"])
        read = read_trail(self.trail_path)
        reports = [line.get("conformance") for line in read["lines"]
                   if line.get("conformance")]
        aggregate = conformance.aggregate(
            {"session": {"lines": read["lines"]},
             "sources_dir": self.sources_dir},
            reports=reports)
        self.trail.append({
            "trail_version": TRAIL_VERSION,
            "scope": self.scope,
            "seq": self.trail.count,
            "ts": None,
            "phase": "NOTE",
            "source": "machine",
            "event": "audit",
            "signal": ("the dependency audit walks every gate record's "
                       "payload_ref chain — any gate whose evidence "
                       "chains to a tentative: true record is a FAIL "
                       "(C5, T-R5-02)"),
            "content": {"verdict": audit["verdict"],
                        "records": audit["count"],
                        "fails": audit["fails"],
                        "aggregate_conformance": aggregate["verdict"]},
            "return_question": None,
            "turn_key": None,
            "cell": None,
            "cycle": None,
            "ledger": {"path": self.ledger_path,
                       "count": authority["count"],
                       "head": authority["head"]},
            "conformance": None,
            "cost": None,
            "prev_hash": None,
            "event_hash": None,
        })
        projection = trail.project(read)
        spend = cost.spend_from_records(authority["records"], self.mode)
        self.trail.append({
            "trail_version": TRAIL_VERSION,
            "scope": self.scope,
            "seq": self.trail.count,
            "ts": None,
            "phase": "NOTE",
            "source": "machine",
            "event": "run-end",
            "signal": ("the run ended on a resource — %s; every held "
                       "gate is still held, none auto-resolved (C1)"
                       % status),
            "content": {"status": status,
                        "completed_cycles": projection[
                            "completed_cycles"],
                        "cycle_target": self.cycle_target,
                        "holds": projection["holds"],
                        "spend": spend,
                        "ceiling": self.ceiling,
                        "audit_verdict": audit["verdict"]},
            "return_question": None,
            "turn_key": None,
            "cell": None,
            "cycle": None,
            "ledger": {"path": self.ledger_path,
                       "count": authority["count"],
                       "head": authority["head"]},
            "conformance": None,
            "cost": None,
            "prev_hash": None,
            "event_hash": None,
        })


class _NeutralLens:
    """The run's fixture desk world (H-B4-1): the inherited B2 trust
    assertion sits behind this stand-in — the fixture desks are the
    caller's deterministic stand-ins, never a live Pi."""

    def assert_trust(self, desk, blocks):
        return {"desk": desk, "ok": True,
                "reason": "the unattended run prompts fixture desks "
                          "only (H-B4-1)"}


# ---------------------------------------------------------------------------
# The dependency audit (C5 / T-R5-02) — end-to-end over the whole ledger.
# ---------------------------------------------------------------------------


def audit_payload_chains(records):
    """Walk every gate record's payload_ref chain.  Each payload_ref
    resolves to the FIRST record in chain order carrying that reference
    — the producer (the run's convention anchors every record's axis at
    its own payload_ref); a later record carrying the same reference
    consumed it as evidence.  A gate whose evidence chain reaches a
    tentative: true record is a FAIL.  A record's own tentative flag is
    its honesty signal, never its own evidence.  Verdict: PASS | FAIL
    (with the consuming record and the tentative record reached) |
    INCONCLUSIVE (no records — nothing is observable, lens 6)."""
    if not records:
        return {"verdict": "INCONCLUSIVE", "count": 0, "fails": [],
                "reason": "the ledger holds no records — the dependency "
                          "audit has nothing to observe"}
    first_owner = {}
    for record in records:
        payload = record.get("payload_ref")
        if isinstance(payload, str):
            first_owner.setdefault(payload, record)
    fails = []
    for record in records:
        chain = [record["record_id"]]
        seen = {record["record_id"]}
        current = record
        reached = None
        while True:
            nxt = first_owner.get(current.get("payload_ref"))
            if nxt is None or nxt.get("record_id") in seen:
                break
            seen.add(nxt["record_id"])
            chain.append(nxt["record_id"])
            if nxt.get("tentative") is True:
                reached = nxt
                break
            current = nxt
        if reached is not None:
            fails.append({
                "record_id": record["record_id"],
                "address": record.get("address"),
                "gate": record.get("gate"),
                "chain": chain,
                "reached_tentative": reached["record_id"],
            })
    verdict = "FAIL" if fails else "PASS"
    return {"verdict": verdict, "count": len(records), "fails": fails}


# ---------------------------------------------------------------------------
# The seed reference (declared in RUN_SURFACE["records"]["payload_ref"]).
# ---------------------------------------------------------------------------


def seed_ref(source_ref, cell, cycle):
    """A durable reference binding the carried field content (the ∞0′ or
    the plant anchor's source ref) to the seeding place — unique per
    (cell, cycle), so no two seeds share a payload_ref and the audit's
    chain stays exact."""
    material = source_ref + " ‖ cell " + cell + " ‖ cycle " + str(cycle)
    return "seed:sha256:" + hashlib.sha256(
        material.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# The CLI.
# ---------------------------------------------------------------------------


def _load_spec(path):
    with open(path, "rb") as handle:
        return json.loads(handle.read().decode("utf-8"))


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(prog="run", description=(
        "the unattended run conductor.  Exit codes: 0 the run ended on a "
        "declared resource (complete / budget-held / stalled / "
        "step-limited) or the audit passed · 1 config/boot error · 3 the "
        "audit FAILed · 4 the ledger chain broke (halt — never repair)"))
    parser.add_argument("--ledger", required=True)
    parser.add_argument("--trail", default=None)
    parser.add_argument("--spec", default=None)
    parser.add_argument("--socket-dir", default=None)
    parser.add_argument("--mode", default=None)
    parser.add_argument("--max-actions", type=int, default=None)
    parser.add_argument("--sources-dir", default=None)
    parser.add_argument("--audit", action="store_true",
                        help="run the dependency audit over --ledger and "
                             "print it; exit 0 PASS / 3 FAIL")
    args = parser.parse_args(argv)
    try:
        if args.audit:
            loaded = LedgerLoader(args.ledger).load(write_index=False)
            result = audit_payload_chains(loaded.records)
            print(json.dumps(result, ensure_ascii=False, sort_keys=True))
            return 3 if result["verdict"] == "FAIL" else 0
        if args.trail is None or args.spec is None:
            parser.error("--trail and --spec are required for a run "
                         "(not for --audit)")
        conductor = Conductor(
            args.ledger, args.trail, _load_spec(args.spec),
            socket_dir=args.socket_dir, mode=args.mode,
            max_actions=args.max_actions, sources_dir=args.sources_dir)
        result = conductor.run()
        conductor.close()
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except LedgerVerificationError as exc:
        print("error: the ledger chain is broken — halt, never repair: %s"
              % exc, file=sys.stderr)
        return 4
    except BootError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
