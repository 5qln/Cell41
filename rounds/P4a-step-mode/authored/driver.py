#!/usr/bin/env python3
"""driver — the turn machine (R03 · B2, C1, C2, C3, K1, K2, K4).

One cell, sequential.  Given a desk that the ledger says is due, the
driver resolves that desk by LABEL, computes its ``turn_key``, sends ONE
prompt to that desk's pane, fences the answer with the unique end marker
``⟦END <turn_key>⟧``, reads to the marker via ``pane.wait_for_output``,
and appends ONE proposed gate record — then refuses to advance the gate
until a human attestation record for that (address, gate) exists on the
ledger, and RECORDS the refusal (a silent refusal is a bug, §8).

The walk (commission §2.1, the commissioner's reading): gate ``x`` is
Amihai's plant — already on the ledger, already attested, written by his
hand at the TTY — and the driver walks ``y`` (G) → ``z`` (Q) → ``a`` (P)
→ ``b`` (V), each prompted, fenced, proposed, and held until his
attestation record appears.  The driver reads gate ``x`` from the ledger
as its starting position and NEVER prompts the centre: the centre guard
refuses desk S before any byte reaches the socket, and the walk simply
does not contain it.

Invariants, all enforced by this module:

  * phase truth comes from the ledger alone — every method replays B0's
    chain from disk (a cold restart rebuilds position from the ledger
    and never re-prompts a turn already recorded, K2/C3);
  * one record per ``turn_key``: a gate record already bearing the key
    is never re-proposed, and the same turn re-issued (fresh process
    included) sends no second prompt (C3);
  * gate order ``x y z a b``: a prompt is refused — and the refusal
    RECORDED — whenever the desk asked for is not the due gate (C1, C2);
  * no attestation, ever: the driver cannot write ``state: "attested"``
    and cannot set ``attestation_ref`` to anything but null (K4);
  * the boot runs the §7 trust assertion for every desk of the walk
    before any prompt — trust missing means the boot fails closed, with
    zero writes on the wire and zero records (C4, §10.3).

The driver consumes an arrangement and asserts it; it never authors a
desk's instruction block or skill (commission §1, §3.3).  The prompt
text is the caller's; the driver appends only the §4.5 fence
instruction.

P4a adds the STEPPING SURFACE — the same code path, stepped (C1): an
optional controller is consulted BEFORE each step's first side effect
and AFTER the step completes, and each step emits one line to a step
trail (a separate append-only file — never the gate ledger, C5).  The
three hook pairs live here, exactly where commission §4.3 places them:
``boot`` (before at entry, after with the boot result), ``take_turn``
(before after the guards, the trust assertion, the ledger replay and
the turn_key computation — before ``instrument.prompt_desk``; after
once the status dict exists), ``advance`` (before with the intent,
after with the outcome, refusal record included).  ``stepper=None`` is
a true no-op: no trail file is created, no check runs, no branch
changes behaviour — the unstepped driver is B2's attested driver,
byte for byte.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys

# B0's module is imported, never copied or re-implemented (R01 attested
# and closed).  The ledger directory is a parameter: the env var
# FRACTAL_LEDGER_DIR, defaulting to the canon path.
_LEDGER_DIR = os.environ.get(
    "FRACTAL_LEDGER_DIR", "/home/deploy/the-cell/ledger")
if _LEDGER_DIR not in sys.path:
    sys.path.insert(0, _LEDGER_DIR)

from fractal_ledger import (  # noqa: E402
    DEFAULT_LEDGER_PATH,
    LedgerLoader,
    LedgerWriter,
)
from instrument import (  # noqa: E402
    HerdrError,
    Instrument,
    assert_not_centre,
)
from lens import DESK_BLOCKS, Lens  # noqa: E402
from surface import COMPILED_OUTPUTS  # noqa: E402
from walker import COURSE, DESK_ADDRESSES, DESK_GATES  # noqa: E402
from step import STEP_KINDS, StepSession, StepError  # noqa: E402

__all__ = [
    "Driver",
    "turn_key",
    "BootError",
    "PROMPT_ATTEMPT",
    "REFUSAL_ATTEMPT_PREFIX",
]

# The attempt ordinal of every gate's (single) prompt.  In this round's
# walk each gate is prompted at most once, so its prompt is always
# attempt "1" — the re-issued turn recomputes the SAME key and is
# suppressed by the record already bearing it (K2, C3, H-B2-2).
PROMPT_ATTEMPT = "1"

# Refusal records derive their turn_key as sha256(address ‖ gate ‖
# "refusal:<n>" ‖ block_version) where n = the number of records already
# on the ledger for that (address, gate).  Deterministic from the ledger
# alone, never colliding with the prompt key (H-B2-2).
REFUSAL_ATTEMPT_PREFIX = "refusal:"


def turn_key(address, gate, attempt, block_version):
    """turn_key(address, gate, attempt, block_version) -> hex64 (§5.1).

    sha256 over the raw byte concatenation of the four UTF-8 fields, in
    order, with no separator: ``address ‖ gate ‖ attempt ‖
    block_version``.  ``attempt`` is coerced to str so callers may pass a
    number or a labelled attempt slot."""
    return hashlib.sha256(
        (str(address) + str(gate) + str(attempt)
         + str(block_version)).encode("utf-8")).hexdigest()


class BootError(Exception):
    """The boot refused to start: the plant is not attested on the ledger,
    or the chain is broken — nothing was prompted."""


class Driver:
    """The turn machine.

    ``Driver(socket_path=…, ledger_path=…, …)`` — both paths are
    parameters (the socket accepts any AF_UNIX path; the ledger default
    is ``fractal_ledger.DEFAULT_LEDGER_PATH`` — every test and the
    verifier pass scratch paths).  ``blocks`` is the arrangement the
    trust assertion ASSERTS (default ``lens.DESK_BLOCKS``); ``lens`` is
    the Pi lens adapter (default ``Lens()``).  ``block_version`` defaults
    to "" — no block identity is observable on the read surface, and
    inventing one is forbidden (H-B2-2).

    ``take_turn()`` is ONE turn — prompt → fence → read → propose — with
    no sleeping inside it.  ``advance()`` refuses without an attestation
    record and RECORDS the refusal.  ``boot()`` runs the trust assertion
    before any write.  No method keeps phase state in RAM: every method
    replays the ledger from disk alone.

    ``stepper=`` attaches the P4a controller (None = B2 behaviour, byte
    for byte); ``trail_path`` / ``session_id`` / ``on_fail`` /
    ``sources_dir`` / ``cell_provider`` / ``step_clock`` parameterise
    the step session (every path is a parameter — tests pass tempdirs).
    """

    def __init__(self, socket_path=None, ledger_path=None,
                 desk_labels=None, desk_gates=None, desk_addresses=None,
                 course=None, blocks=None, block_version="",
                 wait_timeout_ms=60000, fence_source="visible",
                 timeout_s=15.0, lens=None, pi_home=None, pi_bin=None,
                 stepper=None, trail_path=None, session_id=None,
                 on_fail="stop", sources_dir=None, cell_provider=None,
                 step_clock=None):
        self.ledger_path = (
            ledger_path if ledger_path is not None else DEFAULT_LEDGER_PATH)
        self.desk_gates = dict(
            desk_gates if desk_gates is not None else DESK_GATES)
        self.desk_addresses = dict(
            desk_addresses if desk_addresses is not None else DESK_ADDRESSES)
        self.course = tuple(course if course is not None else COURSE)
        self.blocks = dict(blocks) if blocks is not None else DESK_BLOCKS
        self.block_version = "" if block_version is None else block_version
        self.wait_timeout_ms = wait_timeout_ms
        self.fence_source = fence_source
        self.lens = (
            lens if lens is not None
            else Lens(pi_home=pi_home, pi_bin=pi_bin, blocks=self.blocks))
        self.instrument = Instrument(
            socket_path=socket_path, timeout_s=timeout_s,
            desk_labels=desk_labels)
        self.stepper = None
        self.step_session = None
        if stepper is not None:
            self.attach_stepper(
                stepper, trail_path=trail_path, session_id=session_id,
                on_fail=on_fail, sources_dir=sources_dir,
                cell_provider=cell_provider, clock=step_clock)

    def attach_stepper(self, stepper, trail_path=None, session_id=None,
                       on_fail="stop", sources_dir=None,
                       cell_provider=None, clock=None):
        """Attach (or detach) the controller.  ``stepper=None`` detaches
        and returns to B2 behaviour — a true no-op (C1).  The trail path
        must never equal the ledger path (refused at construction)."""
        if stepper is None:
            if self.step_session is not None:
                self.step_session.close()
            self.stepper = None
            self.step_session = None
            return
        self.stepper = stepper
        self.step_session = StepSession(
            stepper, trail_path=trail_path,
            ledger_path=self.ledger_path, session_id=session_id,
            on_fail=on_fail, sources_dir=sources_dir,
            cell_provider=cell_provider, clock=clock)

    @property
    def _step(self):
        return self.step_session is not None

    def close(self):
        if self.step_session is not None:
            self.step_session.close()
        self.instrument.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False

    # -- ledger replay (the only phase authority) --------------------------

    def _authority(self):
        """Replay and verify the chain from disk alone, then the records
        grouped per (address, gate).  Anything not in the ledger did not
        happen (§4.5)."""
        loaded = LedgerLoader(self.ledger_path).load(write_index=False)
        by_pair = {}
        for record in loaded.records:
            pair = (record["address"], record["gate"])
            by_pair.setdefault(pair, []).append(record)
        return {"records": loaded.records, "count": loaded.count,
                "head": loaded.head, "by_pair": by_pair}

    def _pair_records(self, authority, desk):
        return authority["by_pair"].get(
            (self.desk_addresses[desk], self.desk_gates[desk]), [])

    def _pair_attested(self, authority, desk):
        """A human attestation record exists for the desk's (address,
        gate): state "attested" AND a non-null attestation_ref — an
        attested record with a null ref is not an attestation (lens 3)."""
        for record in self._pair_records(authority, desk):
            if (record.get("state") == "attested"
                    and record.get("attestation_ref") is not None):
                return True
        return False

    def _key_present(self, authority, address, gate, key):
        return any(
            record.get("turn_key") == key
            for record in authority["by_pair"].get((address, gate), []))

    def position_from(self, authority):
        """The standing place, derived from the ledger alone: the last
        attested gate in course order (walking from the front, stopping
        at the first unattested gate — a gap never reads as progress)."""
        index = -1
        for i, desk in enumerate(self.course):
            if self._pair_attested(authority, desk):
                index = i
            else:
                break
        if index < 0:
            return {"index": -1, "desk": None, "gate": None,
                    "records": authority["count"]}
        desk = self.course[index]
        return {"index": index, "desk": desk,
                "gate": self.desk_gates[desk],
                "records": authority["count"]}

    def position(self):
        """position() — the standing place, replayed from the ledger on
        THIS call (never from RAM)."""
        return self.position_from(self._authority())

    # -- the stepping surface (P4a — every line below this marker runs
    #    only under stepping; stepper=None executes none of it) ----------

    def _ledger_block(self, authority):
        return {"path": self.ledger_path,
                "records": authority["records"],
                "count": authority["count"],
                "head": authority["head"]}

    def _turn_intent(self, desk, gate, address, authority, turn_key, why,
                     parent_address):
        """The fully-formed intent of ONE turn — kind, desk, gate,
        addresses, zoom, the planned operation, the computed turn_key,
        and WHY this step is next (§4.2)."""
        return {
            "kind": "turn", "desk": desk, "gate": gate,
            "address_before": parent_address, "address_after": address,
            "zoom": {"op": "in", "sign": "−", "letter": desk,
                     "derived_reading": False},
            "operation": "take_turn", "turn_key": turn_key, "why": why,
            "ledger": self._ledger_block(authority),
            "decoded": {"slots": {}, "source": "absent",
                        "operation_steps": []},
            "compiled": {"symbol": None, "gate": None, "landed": None,
                         "payload_ref": None},
            "surface_parse": None, "await": False,
            "next": {"action": "take_turn", "desk": desk, "gate": gate,
                     "why": why},
        }

    def _boot_intent(self):
        return {
            "kind": "boot", "desk": None, "gate": None,
            "address_before": "", "address_after": "",
            "zoom": {"op": "none", "sign": None, "letter": None,
                     "derived_reading": False},
            "operation": "boot", "turn_key": None,
            "why": "replay the chain and assert §7 trust for the walk "
                   "before any prompt",
            "ledger": {"path": self.ledger_path, "records": [],
                       "count": None, "head": None},
            "decoded": {"slots": {}, "source": "absent",
                        "operation_steps": []},
            "compiled": {"symbol": None, "gate": None, "landed": None,
                         "payload_ref": None},
            "surface_parse": None, "await": False,
            "next": {"action": "boot", "desk": None, "gate": None,
                     "why": "replay the chain and assert §7 trust for "
                            "the walk before any prompt"},
        }

    def _advance_intent(self, desk, gate, address, authority, turn_key,
                        why):
        return {
            "kind": "advance", "desk": desk, "gate": gate,
            "address_before": address, "address_after": address,
            "zoom": {"op": "none", "sign": None, "letter": None,
                     "derived_reading": False},
            "operation": "advance", "turn_key": turn_key, "why": why,
            "ledger": self._ledger_block(authority),
            "decoded": {"slots": {}, "source": "absent",
                        "operation_steps": []},
            "compiled": {"symbol": None, "gate": None, "landed": None,
                         "payload_ref": None},
            "surface_parse": None, "await": False,
            "next": {"action": "advance", "desk": desk, "gate": gate,
                     "why": why},
        }

    @staticmethod
    def _not_taken(kind, desk, gate, turn_key, line):
        """The clean stop: a status, no exception, no record, no bytes —
        the trail's last line is the intent with outcome "not-taken"
        (C2)."""
        return {
            "status": "not-taken", "kind": kind, "desk": desk,
            "gate": gate, "turn_key": turn_key,
            "reason": "the controller stopped the step before its first "
                      "side effect; nothing was sent and nothing was "
                      "appended",
            "step": {"seq": line["seq"], "line": line, "stopped": True},
        }

    def _next_action(self):
        """What the run would do next and why — recomputed from a FRESH
        ledger replay AFTER the step, never carried from the intent
        (commission §3.7 lesson 8)."""
        authority = self._authority()
        pos = self.position_from(authority)
        if pos["index"] < 0:
            return {"action": "boot", "desk": None, "gate": None,
                    "why": "the plant (gate x, address '') is not "
                           "attested on the ledger — the driver refuses "
                           "to start from nothing"}
        if pos["index"] + 1 >= len(self.course):
            desk = self.course[-1]
            return {"action": "complete", "desk": desk,
                    "gate": self.desk_gates[desk],
                    "why": "gate b is attested: the cycle is walked"}
        due = self.course[pos["index"] + 1]
        gate = self.desk_gates[due]
        address = self.desk_addresses[due]
        key = turn_key(address, gate, PROMPT_ATTEMPT, self.block_version)
        if self._key_present(authority, address, gate, key):
            return {"action": "wait_for_attestation", "desk": due,
                    "gate": gate,
                    "why": "gate %r (desk %r) is proposed and unattested "
                           "— the gate does not open without a human "
                           "attestation record" % (gate, due)}
        return {"action": "take_turn", "desk": due, "gate": gate,
                "why": "gate %r (desk %r) is due — no proposal is "
                       "pending for it" % (gate, due)}

    def _line_outcome(self, outcome):
        """The outcome as it enters the trail: the status plus the
        record-level references — never a desk's text, never a full
        record body."""
        record = outcome.get("record") or {}
        trimmed = {
            "status": outcome.get("status"),
            "record_id": (outcome.get("record_id")
                          or outcome.get("refusal_record_id")
                          or record.get("record_id")),
            "turn_key": outcome.get("turn_key"),
            "reason": outcome.get("reason"),
        }
        if outcome.get("records") is not None:
            trimmed["records"] = outcome["records"]
        return trimmed

    def _emit_step(self, kind, desk, gate, address_before, address_after,
                   outcome, authority, read=None, extra_outcome=None,
                   operation=None):
        """The after emission: the complete trail line, conformance
        report included.  Observations come from calls the walk already
        made (the label resolution, the fenced read) — stepping adds no
        socket traffic of its own (C1)."""
        session = self.step_session
        if session is None:
            return None
        entry = STEP_KINDS[kind]
        arrangement = self.instrument.last_arrangement()
        if arrangement:
            session.record_arrangement(list(arrangement))
        parsed = None
        if read is not None:
            parsed = session.record_surface(desk, read.get("text") or "")
        decoded = {"slots": {}, "source": "absent", "operation_steps": []}
        if parsed is not None and parsed.get("status") != "absent":
            if parsed.get("status") == "lawful":
                decoded["source"] = "desk_surface"
                decoded["slots"] = parsed.get("slots") or {}
                names = (parsed.get("decoding") or {}).get("ops") or []
                decoded["operation_steps"] = [
                    {"op": name, "observed": True} for name in names]
            # a malformed announcement parses to nothing lawful:
            # decoded.source stays "absent" (§5.2) and the dependent
            # checks read INCONCLUSIVE; the cell-scope checks still see
            # the announced surface and fail it by id.
        compiled = {"symbol": None, "gate": None, "landed": None,
                    "payload_ref": None}
        record = outcome.get("record") or {}
        if (kind == "turn" and desk
                and outcome.get("status") == "proposed"
                and record.get("record_id")):
            compiled = {
                "symbol": COMPILED_OUTPUTS.get(desk),
                "gate": self.desk_gates.get(desk),
                "landed": "record:%s" % record["record_id"],
                "payload_ref": record.get("payload_ref"),
            }
        line_outcome = self._line_outcome(outcome)
        if extra_outcome:
            line_outcome.update(extra_outcome)
        event = {
            "kind": kind, "desk": desk, "gate": gate,
            "address_before": address_before,
            "address_after": address_after,
            "zoom": {"op": entry["zoom_op"], "sign": entry["zoom_sign"],
                     "letter": desk if kind == "turn" else None,
                     "derived_reading": entry["derived_reading"]},
            "operation": operation or kind, "outcome": line_outcome,
            "ledger": self._ledger_block(authority),
            "next": self._next_action(),
            "await": outcome.get("status") == "proposed",
            "decoded": decoded, "compiled": compiled,
            "surface_parse": parsed,
        }
        line, stopped = session.complete(event)
        return {"seq": line["seq"], "line": line, "stopped": stopped}

    @staticmethod
    def _trust_ref(blocks):
        """The asserted arrangement as a reference (sha256 + byte
        length) — the desk's instruction text never enters the trail."""
        raw = json.dumps(blocks, ensure_ascii=False, sort_keys=True)
        raw = raw.encode("utf-8")
        return {"asserted": True,
                "arrangement_ref": "sha256:" + hashlib.sha256(raw).hexdigest(),
                "len": len(raw)}

    # -- boot ---------------------------------------------------------------

    def boot(self):
        """The trust assertion runs here, before any write (C4, §10.3).

        Replays and verifies the chain (the plant, gate x, address "",
        must be attested — it is Amihai's TTY plant), then asserts §7
        trust for every desk of the walk.  The boot touches the socket
        not at all: on a trust failure zero writes (indeed zero bytes)
        reach the wire and zero records are appended.  Desk S's lens is
        not asserted here — the driver never prompts the centre, and
        where the centre's own lens runs is hold H-B2-1.

        Under stepping: ``before`` at entry (§4.3), ``after`` with the
        boot result (position, due desk, trust table as references).
        """
        if self._step:
            intent = self._boot_intent()
            answer, line = self.step_session.consult(intent)
            if answer == "stop":
                return self._not_taken("boot", None, None, None, line)
        authority = self._authority()
        pos = self.position_from(authority)
        if pos["index"] < 0:
            raise BootError(
                "the plant (gate x, address '') is not attested on the "
                "ledger — the driver refuses to start from nothing")
        trust = {}
        for desk in self.course[1:]:
            trust[desk] = self.lens.assert_trust(desk, self.blocks)
        due = (self.course[pos["index"] + 1]
               if pos["index"] + 1 < len(self.course) else None)
        result = {
            "position": pos,
            "due": due,
            "trust": trust,
            "records": authority["count"],
            "head": authority["head"],
        }
        if self._step:
            outcome = {
                "status": "booted",
                "position": {"index": pos["index"], "desk": pos["desk"],
                             "gate": pos["gate"]},
                "due": due,
                "trust": {desk: self._trust_ref(blocks)
                          for desk, blocks in trust.items()},
                "reason": "the chain replays and §7 trust holds for the "
                          "walk",
            }
            result["step"] = self._emit_step(
                "boot", None, None, "", "", outcome, authority,
                operation="boot",
                extra_outcome={"position": outcome["position"],
                               "due": outcome["due"],
                               "trust": outcome["trust"]})
        return result

    # -- one turn ------------------------------------------------------------

    def take_turn(self, desk, text):
        """ONE turn: prompt → fence → read → propose.  No sleeping.

        The centre guard and the trust assertion run before any byte
        reaches the socket; the desk must be exactly the due gate (per
        the ledger replay) or the turn is refused and the refusal
        RECORDED; a turn already recorded is never re-prompted (C3).
        Returns a status dict:

          * ``proposed``        — the fenced answer was read and ONE
                                  proposed gate record appended;
          * ``already_recorded``— the turn_key is already on the ledger:
                                  no prompt sent, no record appended;
          * ``already_walked``  — the gate's attestation is already on
                                  the ledger: nothing to do;
          * ``refused``         — an out-of-order advance attempt: the
                                  refusal record was appended;
          * ``incomplete``      — the prompt or the fenced read failed
                                  (timeout / empty / truncated / missing
                                  marker): NOT a completed turn, no
                                  record (lens 3).

        ``text`` is the prompt body (the caller's, never invented here);
        the driver appends the §4.5 fence instruction to it."""
        assert_not_centre(desk)          # K5 — before anything else
        if desk not in self.course:
            raise ValueError("unknown desk %r" % (desk,))
        if desk == self.course[0]:
            assert_not_centre(desk)  # unreachable: the guard above already refused S
            raise BootError("the centre desk is never prompted (T-R3-02)")
        self.lens.assert_trust(desk, self.blocks)  # fail closed, pre-write
        if not isinstance(text, str) or not text:
            raise ValueError("take_turn needs the prompt text")
        gate = self.desk_gates[desk]
        address = self.desk_addresses[desk]
        authority = self._authority()
        pos = self.position_from(authority)
        if pos["index"] < 0:
            raise BootError(
                "the plant (gate x, address '') is not attested on the "
                "ledger — there is no position to take a turn from")
        due = (self.course[pos["index"] + 1]
               if pos["index"] + 1 < len(self.course) else None)
        parent_address = self.desk_addresses[self.course[pos["index"]]]
        if desk != due:
            desk_index = self.course.index(desk)
            if desk_index <= pos["index"]:
                outcome = {
                    "status": "already_walked", "desk": desk, "gate": gate,
                    "address": address,
                    "reason": "the gate's attestation is already on the "
                              "ledger; nothing to prompt",
                    "records": [r["record_id"]
                                for r in self._pair_records(authority, desk)],
                }
                if self._step:
                    intent = self._turn_intent(
                        desk, gate, address, authority, None,
                        "the gate's attestation is already on the "
                        "ledger; nothing to prompt", parent_address)
                    answer, line = self.step_session.consult(intent)
                    if answer == "stop":
                        return self._not_taken(
                            "turn", desk, gate, None, line)
                    authority = self._authority()
                    outcome["step"] = self._emit_step(
                        "turn", desk, gate, parent_address, address,
                        outcome, authority, operation="take_turn")
                return outcome
            # The desk sits beyond the due gate: prompting it would be an
            # advance past a gate that no human has attested — refuse and
            # RECORD the refusal (§8, C2).
            refusal_key = None
            if self._step:
                # the refusal key, computed BEFORE the before-hook so the
                # intent carries it (the same deterministic key
                # _record_refusal would derive — nothing is re-derived)
                n = len(self._pair_records(authority, due))
                refusal_key = turn_key(
                    self.desk_addresses[due], self.desk_gates[due],
                    REFUSAL_ATTEMPT_PREFIX + str(n), self.block_version)
                intent = self._turn_intent(
                    desk, gate, address, authority, refusal_key,
                    "desk %r is gate %r but the due gate is %r (desk %r) "
                    "with no attestation record"
                    % (desk, gate, self.desk_gates[due], due),
                    parent_address)
                answer, line = self.step_session.consult(intent)
                if answer == "stop":
                    return self._not_taken(
                        "turn", desk, gate, refusal_key, line)
            refusal = self._record_refusal(authority, due)
            outcome = {
                "status": "refused", "desk": desk, "gate": gate,
                "address": address,
                "reason": ("desk %r is gate %r but the due gate is %r "
                           "(desk %r) with no attestation record"
                           % (desk, gate, self.desk_gates[due], due)),
                "refusal_record_id": refusal["record_id"],
                "refusal": refusal,
            }
            if self._step:
                authority = self._authority()
                outcome["step"] = self._emit_step(
                    "turn", desk, gate, parent_address, address,
                    outcome, authority, operation="take_turn")
            return outcome
        key = turn_key(address, gate, PROMPT_ATTEMPT, self.block_version)
        if self._key_present(authority, address, gate, key):
            # K2 / C3: a gate record already bearing this turn_key exists —
            # the turn is recorded; never re-propose, never re-prompt.
            existing = [r for r in authority["by_pair"].get((address, gate), [])
                        if r.get("turn_key") == key]
            outcome = {
                "status": "already_recorded", "desk": desk, "gate": gate,
                "address": address, "turn_key": key,
                "record_id": existing[0]["record_id"],
                "reason": "a record already bears this turn_key — the "
                          "duplicated turn is suppressed (K2)",
            }
            if self._step:
                intent = self._turn_intent(
                    desk, gate, address, authority, key,
                    "a record already bears this turn_key — the "
                    "duplicated turn is suppressed (K2)",
                    parent_address)
                answer, line = self.step_session.consult(intent)
                if answer == "stop":
                    return self._not_taken("turn", desk, gate, key, line)
                outcome["step"] = self._emit_step(
                    "turn", desk, gate, parent_address, address,
                    outcome, authority, operation="take_turn")
            return outcome
        if self._step:
            # the before hook: after the guards, the trust assertion, the
            # ledger replay and the turn_key computation; BEFORE
            # instrument.prompt_desk — the first side effect (§4.3).
            intent = self._turn_intent(
                desk, gate, address, authority, key,
                "gate %r (desk %r) is due — no proposal is pending for "
                "it" % (gate, desk), parent_address)
            answer, line = self.step_session.consult(intent)
            if answer == "stop":
                return self._not_taken("turn", desk, gate, key, line)
        try:
            read = self.instrument.prompt_desk(
                desk, text, key, source=self.fence_source,
                timeout_ms=self.wait_timeout_ms)
        except HerdrError as exc:
            # A timeout, an empty read, a truncated read, a missing
            # marker, a lost label: none may read as a completed turn or
            # an open gate — nothing is appended (lens 3, H-B2-3).
            outcome = {
                "status": "incomplete", "desk": desk, "gate": gate,
                "address": address, "turn_key": key,
                "reason": "%s: %s" % (type(exc).__name__, exc),
            }
            if self._step:
                outcome["step"] = self._emit_step(
                    "turn", desk, gate, parent_address, address,
                    outcome, authority, operation="take_turn")
            return outcome
        # The literal K2 guard, at propose time: re-read the ledger from
        # disk; if the key appeared meanwhile (another process proposed
        # it first), never re-propose.
        authority = self._authority()
        if self._key_present(authority, address, gate, key):
            outcome = {
                "status": "already_recorded", "desk": desk, "gate": gate,
                "address": address, "turn_key": key,
                "reason": "the turn_key landed on the ledger while the "
                          "fence was being read; never re-proposed (K2)",
            }
            if self._step:
                outcome["step"] = self._emit_step(
                    "turn", desk, gate, parent_address, address,
                    outcome, authority, operation="take_turn")
            return outcome
        record = self._proposal_record(address, gate, key, read["text"])
        with LedgerWriter(self.ledger_path) as writer:
            full = writer.append(record)
        outcome = {
            "status": "proposed", "desk": desk, "gate": gate,
            "address": address, "turn_key": key, "record": full,
            "read": read,
        }
        if self._step:
            authority = self._authority()
            outcome["step"] = self._emit_step(
                "turn", desk, gate, parent_address, address,
                outcome, authority, read=read, operation="take_turn")
        return outcome

    # -- advance ---------------------------------------------------------------

    def advance(self):
        """Try to open the gate after the last attested one.

        With a proposal pending attestation: REFUSE — no attestation
        record for that (address, gate) exists — and RECORD the refusal
        (§8, C2: a silent refusal is indistinguishable from a success and
        is therefore a bug).  With nothing pending: report the due gate
        (nothing was refused — the previous gate IS attested).  After
        gate b is attested the cycle is complete.

        Under stepping: ``before`` with the intent (which gate it would
        open, or that the cycle is walked); ``after`` with the outcome,
        refusal record included (§4.3)."""
        authority = self._authority()
        pos = self.position_from(authority)
        if pos["index"] < 0:
            raise BootError(
                "the plant (gate x, address '') is not attested on the "
                "ledger — there is nothing to advance from")
        if pos["index"] + 1 >= len(self.course):
            desk = self.course[-1]
            gate = self.desk_gates[desk]
            address = self.desk_addresses[desk]
            outcome = {
                "status": "complete", "desk": desk,
                "gate": gate,
                "address": address,
                "reason": "gate b is attested: the cycle is walked",
            }
            if self._step:
                intent = self._advance_intent(
                    desk, gate, address, authority, None,
                    "gate b is attested: the cycle is walked")
                answer, line = self.step_session.consult(intent)
                if answer == "stop":
                    return self._not_taken(
                        "advance", desk, gate, None, line)
                outcome["step"] = self._emit_step(
                    "advance", desk, gate, address, address,
                    outcome, authority)
            return outcome
        due = self.course[pos["index"] + 1]
        gate = self.desk_gates[due]
        address = self.desk_addresses[due]
        key = turn_key(address, gate, PROMPT_ATTEMPT, self.block_version)
        if self._step:
            intent = self._advance_intent(
                due, gate, address, authority, key,
                "attempt to open gate %r (desk %r) — the gate after the "
                "last attested one" % (gate, due))
            answer, line = self.step_session.consult(intent)
            if answer == "stop":
                return self._not_taken("advance", due, gate, key, line)
        if self._key_present(authority, address, gate, key):
            refusal = self._record_refusal(authority, due)
            outcome = {
                "status": "refused", "due_desk": due, "due_gate": gate,
                "address": address, "turn_key": key,
                "reason": ("gate %r (desk %r) is proposed but no "
                           "attestation record for it exists — the "
                           "conductor refuses to advance" % (gate, due)),
                "refusal_record_id": refusal["record_id"],
                "refusal": refusal,
            }
            if self._step:
                authority = self._authority()
                outcome["step"] = self._emit_step(
                    "advance", due, gate, address, address,
                    outcome, authority)
            return outcome
        outcome = {
            "status": "due", "due_desk": due, "due_gate": gate,
            "address": address,
            "reason": "no proposal is pending for the due gate — "
                      "take_turn(%r) first" % (due,),
        }
        if self._step:
            outcome["step"] = self._emit_step(
                "advance", due, gate, address, address,
                outcome, authority)
        return outcome

    # -- records (the only two the driver ever appends) -------------------------

    def _proposal_record(self, address, gate, key, text):
        """The ONE proposed gate record of a turn: state held-pending,
        mark mechanical, tentative — machine-posed, non-data until a
        human converts it (§5.1).  payload_ref is a durable reference,
        never content (§4.7.5): the sha256 of the fenced text.
        attestation_ref is always null (K4)."""
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        payload_ref = "fenced:sha256:" + digest
        return {
            "address": address,
            "gate": gate,
            "state": "held-pending",
            "mark": "mechanical",
            "payload_ref": payload_ref,
            "axis": {"field": {"mode": "anchored", "anchor": payload_ref},
                     "delta": []},
            "axis_verdict": None,
            "corruption": None,
            "tentative": True,
            "turn_key": key,
            "block_version": self.block_version,
            "attestation_ref": None,
        }

    def _record_refusal(self, authority, held_desk):
        """Append the refusal record — on the HELD gate's own (address,
        gate), so the ledger's gate letters keep their x y z a b order
        (C1) — and return the full record.  The refusal never advances
        anything: state held-pending, attestation_ref null (K4).  Its
        turn_key is sha256(address ‖ gate ‖ "refusal:<n>" ‖
        block_version), n = records already on the ledger for the pair:
        deterministic from the ledger alone and never colliding with the
        prompt key (H-B2-2)."""
        address = self.desk_addresses[held_desk]
        gate = self.desk_gates[held_desk]
        n = len(self._pair_records(authority, held_desk))
        attempt = REFUSAL_ATTEMPT_PREFIX + str(n)
        key = turn_key(address, gate, attempt, self.block_version)
        payload_ref = "refusal:no-attestation:%s:%s" % (address, gate)
        record = {
            "address": address,
            "gate": gate,
            "state": "held-pending",
            "mark": "mechanical",
            "payload_ref": payload_ref,
            "axis": {"field": {"mode": "anchored", "anchor": payload_ref},
                     "delta": []},
            "axis_verdict": None,
            "corruption": None,
            "tentative": True,
            "turn_key": key,
            "block_version": self.block_version,
            "attestation_ref": None,
        }
        with LedgerWriter(self.ledger_path) as writer:
            return writer.append(record)
