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
"""

from __future__ import annotations

import hashlib
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
from walker import COURSE, DESK_ADDRESSES, DESK_GATES  # noqa: E402

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
    """

    def __init__(self, socket_path=None, ledger_path=None,
                 desk_labels=None, desk_gates=None, desk_addresses=None,
                 course=None, blocks=None, block_version="",
                 wait_timeout_ms=60000, fence_source="visible",
                 timeout_s=15.0, lens=None, pi_home=None, pi_bin=None):
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

    def close(self):
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

    # -- boot ---------------------------------------------------------------

    def boot(self):
        """The trust assertion runs here, before any write (C4, §10.3).

        Replays and verifies the chain (the plant, gate x, address "",
        must be attested — it is Amihai's TTY plant), then asserts §7
        trust for every desk of the walk.  The boot touches the socket
        not at all: on a trust failure zero writes (indeed zero bytes)
        reach the wire and zero records are appended.  Desk S's lens is
        not asserted here — the driver never prompts the centre, and
        where the centre's own lens runs is hold H-B2-1."""
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
        return {
            "position": pos,
            "due": due,
            "trust": trust,
            "records": authority["count"],
            "head": authority["head"],
        }

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
        if desk != due:
            desk_index = self.course.index(desk)
            if desk_index <= pos["index"]:
                return {
                    "status": "already_walked", "desk": desk, "gate": gate,
                    "address": address,
                    "reason": "the gate's attestation is already on the "
                              "ledger; nothing to prompt",
                    "records": [r["record_id"]
                                for r in self._pair_records(authority, desk)],
                }
            # The desk sits beyond the due gate: prompting it would be an
            # advance past a gate that no human has attested — refuse and
            # RECORD the refusal (§8, C2).
            refusal = self._record_refusal(authority, due)
            return {
                "status": "refused", "desk": desk, "gate": gate,
                "address": address,
                "reason": ("desk %r is gate %r but the due gate is %r "
                           "(desk %r) with no attestation record"
                           % (desk, gate, self.desk_gates[due], due)),
                "refusal_record_id": refusal["record_id"],
                "refusal": refusal,
            }
        key = turn_key(address, gate, PROMPT_ATTEMPT, self.block_version)
        if self._key_present(authority, address, gate, key):
            # K2 / C3: a gate record already bearing this turn_key exists —
            # the turn is recorded; never re-propose, never re-prompt.
            existing = [r for r in authority["by_pair"].get((address, gate), [])
                        if r.get("turn_key") == key]
            return {
                "status": "already_recorded", "desk": desk, "gate": gate,
                "address": address, "turn_key": key,
                "record_id": existing[0]["record_id"],
                "reason": "a record already bears this turn_key — the "
                          "duplicated turn is suppressed (K2)",
            }
        try:
            read = self.instrument.prompt_desk(
                desk, text, key, source=self.fence_source,
                timeout_ms=self.wait_timeout_ms)
        except HerdrError as exc:
            # A timeout, an empty read, a truncated read, a missing
            # marker, a lost label: none may read as a completed turn or
            # an open gate — nothing is appended (lens 3, H-B2-3).
            return {
                "status": "incomplete", "desk": desk, "gate": gate,
                "address": address, "turn_key": key,
                "reason": "%s: %s" % (type(exc).__name__, exc),
            }
        # The literal K2 guard, at propose time: re-read the ledger from
        # disk; if the key appeared meanwhile (another process proposed
        # it first), never re-propose.
        authority = self._authority()
        if self._key_present(authority, address, gate, key):
            return {
                "status": "already_recorded", "desk": desk, "gate": gate,
                "address": address, "turn_key": key,
                "reason": "the turn_key landed on the ledger while the "
                          "fence was being read; never re-proposed (K2)",
            }
        record = self._proposal_record(address, gate, key, read["text"])
        with LedgerWriter(self.ledger_path) as writer:
            full = writer.append(record)
        return {
            "status": "proposed", "desk": desk, "gate": gate,
            "address": address, "turn_key": key, "record": full,
            "read": read,
        }

    # -- advance ---------------------------------------------------------------

    def advance(self):
        """Try to open the gate after the last attested one.

        With a proposal pending attestation: REFUSE — no attestation
        record for that (address, gate) exists — and RECORD the refusal
        (§8, C2: a silent refusal is indistinguishable from a success and
        is therefore a bug).  With nothing pending: report the due gate
        (nothing was refused — the previous gate IS attested).  After
        gate b is attested the cycle is complete."""
        authority = self._authority()
        pos = self.position_from(authority)
        if pos["index"] < 0:
            raise BootError(
                "the plant (gate x, address '') is not attested on the "
                "ledger — there is nothing to advance from")
        if pos["index"] + 1 >= len(self.course):
            desk = self.course[-1]
            return {
                "status": "complete", "desk": desk,
                "gate": self.desk_gates[desk],
                "address": self.desk_addresses[desk],
                "reason": "gate b is attested: the cycle is walked",
            }
        due = self.course[pos["index"] + 1]
        gate = self.desk_gates[due]
        address = self.desk_addresses[due]
        key = turn_key(address, gate, PROMPT_ATTEMPT, self.block_version)
        if self._key_present(authority, address, gate, key):
            refusal = self._record_refusal(authority, due)
            return {
                "status": "refused", "due_desk": due, "due_gate": gate,
                "address": address, "turn_key": key,
                "reason": ("gate %r (desk %r) is proposed but no "
                           "attestation record for it exists — the "
                           "conductor refuses to advance" % (gate, due)),
                "refusal_record_id": refusal["record_id"],
                "refusal": refusal,
            }
        return {
            "status": "due", "due_desk": due, "due_gate": gate,
            "address": address,
            "reason": "no proposal is pending for the due gate — "
                      "take_turn(%r) first" % (due,),
        }

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
