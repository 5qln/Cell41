#!/usr/bin/env python3
"""walker — the read-only poll loop (R02 · B1, K2, C1, C2).

§4.3 made concrete, without a single pane write and without any gate
advance:

    every TICK:
      1. read the arrangement — desk keys resolved from pane labels       # never cached across restarts
      2. phase truth: fractal_ledger.tail_record() — and nothing else     # the ONLY source of phase truth
      3. observe each desk (agent_status via pane.get / agent.get;
         pane.read for output)
      4. three dialects + the cell's MOVING axis -> one verdict per desk
      5. per blocked EPISODE (commission §2 operational reading): append
         exactly one state=held-pending record through B0's LedgerWriter

Episode open/closed state is derived from the ledger alone (a fresh
LedgerLoader replay each tick — the tail for that address is the
authority), never from RAM: a cold restart mid-episode appends nothing
(C2).  The only records this module ever appends are held-pending holds;
attestation_ref is always null, no code path here advances a gate, and
no gate semantics are re-implemented outside fractal_ledger (T-O2-01).

The 3 s tick and the ×2→30 s backoff live in run() — tick() itself never
sleeps — and the schedule is a pure function, next_delay(), so it can be
asserted without waiting minutes.
"""

from __future__ import annotations

import datetime
import hashlib
import os
import sys
import time

# B0's module is imported, never copied or re-implemented (R01 attested
# and closed).  The ledger directory is a parameter: the env var
# FRACTAL_LEDGER_DIR, defaulting to the canon path.
_LEDGER_DIR = os.environ.get(
    "FRACTAL_LEDGER_DIR", "/home/deploy/the-cell/ledger")
if _LEDGER_DIR not in sys.path:
    sys.path.insert(0, _LEDGER_DIR)

from fractal_ledger import (  # noqa: E402
    DEFAULT_LEDGER_PATH,
    GENESIS,
    LedgerError,
    LedgerLoader,
    LedgerWriter,
    tail_record,
)
from instrument import (  # noqa: E402
    AgentNotFoundError,
    HerdrError,
    Instrument,
    PaneNotFoundError,
)
from dialects import Verdict, dominant, map_signal  # noqa: E402

__all__ = [
    "Walker",
    "next_delay",
    "DESK_GATES",
    "DESK_ADDRESSES",
    "COURSE",
]

# Desk → gate map: Amihai's word, 2026-08-27 (commission §3.6 — hold B1-4
# closed): S:x G:y Q:z P:a V:b.  Data, one place to change.
DESK_GATES = {
    "S": "x",
    "G": "y",
    "Q": "z",
    "P": "a",
    "V": "b",
}

# Desk letter → ledger address word.  S is the centre: its address is the
# empty word "" — matching the attested plant record (gate x, address "").
DESK_ADDRESSES = {
    "S": "",
    "G": "G",
    "Q": "Q",
    "P": "P",
    "V": "V",
}

COURSE = ("S", "G", "Q", "P", "V")


def next_delay(changed, current_delay, base_s=3.0, cap_s=30.0):
    """The §4.3 backoff schedule as a pure function.

    After a tick where something changed, the delay resets to base_s;
    after a tick where nothing changed, it doubles, capped at cap_s
    (3 s → 6 → 12 → 24 → 30 → 30 …).  Pure and assertable without
    waiting."""
    if changed:
        return float(base_s)
    return min(float(current_delay) * 2.0, float(cap_s))


class Walker:
    """The read-only poll loop.

    Walker(socket_path=…, ledger_path=…, …) — both paths are parameters;
    the socket path accepts any AF_UNIX path (how it is tested), and the
    ledger default is fractal_ledger.DEFAULT_LEDGER_PATH (§3.5 — every
    test and demo passes a scratch path explicitly).

    tick() is ONE poll pass with no sleeping inside it; run() owns the
    tick/backoff schedule.  reconstruct() rebuilds, from the accumulated
    poll observations alone, the cycle a human drove at the desks (C1).

    The cell's MOVING axis verdict has no live source on the read-only
    surface this round: it is consumed through an optional axis_provider
    callable (tests inject one).  With no provider, the axis verdict is
    recorded as absent — INCONCLUSIVE, never clean (H-8).
    """

    def __init__(self, socket_path=None, ledger_path=None,
                 desk_labels=None, desk_gates=None, desk_addresses=None,
                 tick_s=3.0, backoff_cap_s=30.0, timeout_s=15.0,
                 axis_provider=None):
        self.ledger_path = (
            ledger_path if ledger_path is not None else DEFAULT_LEDGER_PATH)
        self.desk_gates = dict(
            desk_gates if desk_gates is not None else DESK_GATES)
        self.desk_addresses = dict(
            desk_addresses if desk_addresses is not None else DESK_ADDRESSES)
        self.tick_s = float(tick_s)
        self.backoff_cap_s = float(backoff_cap_s)
        self.axis_provider = axis_provider
        self.instrument = Instrument(
            socket_path=socket_path, timeout_s=timeout_s,
            desk_labels=desk_labels)
        self._observations = []
        self._prev_frame_digest = None
        self._prev_output_digests = {}
        self._run_notes = []

    def close(self):
        self.instrument.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False

    # -- tick -------------------------------------------------------------

    def tick(self):
        """ONE poll pass.  No sleeping anywhere in here — the 3 s tick and
        the ×2→30 s backoff live in run().  Returns the tick frame."""
        tick_no = len(self._observations) + 1
        started = time.monotonic()
        axis = self._axis_observation()
        re_resolved = False
        try:
            snapshot = self.instrument.observe_desks()
        except (PaneNotFoundError, AgentNotFoundError):
            # Pane ids were re-minted under a server restart: resolve the
            # labels again (never reuse a remembered id) and re-observe
            # once (C4).
            snapshot = self.instrument.observe_desks()
            re_resolved = True
        authority = self._ledger_authority()
        phase = self._phase_from_tail(authority)
        desk_frames = []
        for desk in COURSE:
            raw = snapshot["desks"].get(desk)
            if raw is None:
                continue
            herdr_verdict = map_signal("herdr", raw)
            verdict = dominant(axis["verdict"], herdr_verdict)
            episode, appended_id = self._episode(desk, verdict, authority)
            desk_frames.append(self._desk_frame(
                desk, raw, verdict, episode, appended_id))
        unresolved = [desk for desk in COURSE
                      if desk not in snapshot["desks"]]
        frame = {
            "tick": tick_no,
            "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "monotonic_s": time.monotonic() - started,
            "phase": phase,
            "arrangement": snapshot["arrangement"],
            "axis": {"source": axis["source"], "verdict": axis["verdict"]},
            "reresolved_this_tick": re_resolved,
            "desks": desk_frames,
            "unresolved_desks": unresolved,
        }
        frame["digest"] = self._frame_digest(frame)
        self._observations.append(frame)
        return frame

    def _axis_observation(self):
        if self.axis_provider is None:
            return {
                "source": "absent",
                "verdict": Verdict(
                    "no_verdict", (),
                    "cell MOVING axis: no live source this round"),
            }
        payload = self.axis_provider()
        return {"source": "provider", "verdict": map_signal("cell", payload)}

    def _desk_frame(self, desk, raw, verdict, episode, appended_id):
        output = raw.get("read")
        if output is not None and output.get("truncated") is False:
            digest = hashlib.sha256(
                output["text"].encode("utf-8")).hexdigest()
            prev = self._prev_output_digests.get(desk)
            changed = None if prev is None else (digest != prev)
            self._prev_output_digests[desk] = digest
            output_obs = {
                "text": output["text"],
                "truncated": output["truncated"],
                "digest": digest,
                "changed_since_prev": changed,
            }
        else:
            # A truncated read is never treated as a desk's complete
            # output (§3.4); its change status stays unobservable.
            output_obs = {
                "text": output["text"] if output is not None else None,
                "truncated": output["truncated"] if output is not None else None,
                "digest": None,
                "changed_since_prev": None,
            }
        return {
            "desk": desk,
            "pane_id": raw["pane_id"],
            "workspace_id": raw["workspace_id"],
            "label": raw["label"],
            "agent_status": raw["agent_status"],
            "agent_status_source": raw["agent_status_source"],
            "agent": raw["agent"],
            "agent_get_error": raw.get("agent_get_error"),
            "revision_pane_info": raw.get("revision_pane_info"),
            "revision_read": output.get("revision") if output is not None else None,
            "output": output_obs,
            "verdict": {
                "blocked": verdict.is_blocked,
                "signals": list(verdict.signals),
                "detail": verdict.detail,
            },
            "episode": episode,
            "appended_record_id": appended_id,
        }

    # -- episode rule (commission §2 operational reading) ------------------

    def _episode(self, desk, verdict, authority):
        """On a BLOCKED verdict: exactly one held-pending record per
        episode.  The open/closed state comes from the ledger alone —
        the last record for that (address, gate) — never from RAM."""
        if not verdict.is_blocked:
            return "none", None
        address = self.desk_addresses[desk]
        gate = self.desk_gates[desk]
        last = authority["last_per_address_gate"].get((address, gate))
        if last is not None and last.get("state") == "held-pending":
            return "open", None  # episode already open on the ledger
        record = self._hold_record(desk, verdict, authority)
        with LedgerWriter(self.ledger_path) as writer:
            full = writer.append(record)
        return "new", full["record_id"]

    def _hold_record(self, desk, verdict, authority):
        """The twelve caller-supplied §5.1 fields of an observed hold.

        record_id / prev_hash / ts are computed by B0's writer — never
        supplied here.  attestation_ref is always null (K4)."""
        address = self.desk_addresses[desk]
        gate = self.desk_gates[desk]
        signals = tuple(verdict.signals) or ("observed-blocked",)
        payload_ref = "+".join(signals)
        prior = sum(
            1 for record in authority["records"]
            if record["address"] == address and record["gate"] == gate)
        attempt = str(prior + 1)
        # H-2: B1 does not prompt and the read surface exposes no block
        # identity (H-6) — nothing is observed to derive a block id from,
        # and inventing one is forbidden.  The empty string is the honest
        # "no block identity observed" value; turn_key is still computed
        # over the honest tuple (§5.1 formula).
        block_version = ""
        turn_key = hashlib.sha256(
            (address + gate + attempt + block_version).encode("utf-8")
        ).hexdigest()
        # The cell MOVING verdict is the only axis verdict this round can
        # observe; when the hold is purely a runtime-dialect signal the
        # axis is a fresh anchor with no verdict (null — allowed only at
        # anchored mode, per §5.1).
        axis_verdict = "MOVING" if "cell:moving" in signals else None
        return {
            "address": address,
            "gate": gate,
            "state": "held-pending",
            "mark": "mechanical",
            "payload_ref": payload_ref,
            "axis": {
                "field": {"mode": "anchored", "anchor": payload_ref},
                "delta": [],
            },
            "axis_verdict": axis_verdict,
            "corruption": None,
            "tentative": True,
            "turn_key": turn_key,
            "block_version": block_version,
            "attestation_ref": None,
        }

    # -- ledger re-arm (never from RAM) ------------------------------------

    def _ledger_authority(self):
        """Replay the ledger from disk alone: verify the chain, then the
        last record per (address, gate) — the authority for episode
        open/closed state (tail_record() and, when more than the tail is
        needed, LedgerLoader.load(), §2)."""
        loaded = LedgerLoader(self.ledger_path).load(write_index=False)
        last = {}
        for record in loaded.records:
            last[(record["address"], record["gate"])] = record
        return {
            "records": loaded.records,
            "count": loaded.count,
            "head": loaded.head,
            "last_per_address_gate": last,
        }

    def _phase_from_tail(self, authority):
        """Phase truth comes from tail_record() and from nothing else."""
        tail = tail_record(self.ledger_path)
        if tail is None:
            return {
                "source": "tail_record",
                "tail_record_id": GENESIS,
                "chain_records": authority["count"],
                "gate": None,
                "state": None,
                "address": None,
            }
        return {
            "source": "tail_record",
            "tail_record_id": tail.get("record_id"),
            "chain_records": authority["count"],
            "gate": tail.get("gate"),
            "state": tail.get("state"),
            "address": tail.get("address"),
        }

    # -- reconstruction (C1) ------------------------------------------------

    def reconstruct(self):
        """The cycle a human drove at the desks, rebuilt from polling
        alone: per desk, which state in which order (with the tick each
        state was first seen in), the state transitions in tick order,
        the holds appended, and the gate the ledger says the cell stands
        at (the tail's gate — no invented state, no pane write)."""
        frames = self._observations
        if not frames:
            return {
                "ticks": 0,
                "phase_now": None,
                "arrangement_now": None,
                "desk_sequences": {},
                "transitions": [],
                "holds": [],
                "unresolved_desks": [],
                "gate_now": None,
            }
        last = frames[-1]
        desk_sequences = {}
        for desk in COURSE:
            seen = []
            for frame in frames:
                for desk_frame in frame["desks"]:
                    if desk_frame["desk"] != desk:
                        continue
                    status = desk_frame["agent_status"]
                    if not seen or seen[-1]["status"] != status:
                        seen.append({
                            "tick": frame["tick"],
                            "status": status,
                            "output_changed": desk_frame["output"]["changed_since_prev"],
                        })
            desk_sequences[desk] = seen
        transitions = []
        for desk, seq in desk_sequences.items():
            for i in range(1, len(seq)):
                transitions.append({
                    "tick": seq[i]["tick"],
                    "desk": desk,
                    "from": seq[i - 1]["status"],
                    "to": seq[i]["status"],
                })
        transitions.sort(key=lambda t: (t["tick"], COURSE.index(t["desk"])))
        holds = []
        for frame in frames:
            for desk_frame in frame["desks"]:
                if desk_frame["appended_record_id"]:
                    desk = desk_frame["desk"]
                    holds.append({
                        "record_id": desk_frame["appended_record_id"],
                        "tick": frame["tick"],
                        "desk": desk,
                        "address": self.desk_addresses[desk],
                        "gate": self.desk_gates[desk],
                    })
        return {
            "ticks": len(frames),
            "phase_now": last["phase"],
            "arrangement_now": last["arrangement"],
            "desk_sequences": desk_sequences,
            "transitions": transitions,
            "holds": holds,
            "unresolved_desks": last["unresolved_desks"],
            "gate_now": last["phase"]["gate"],
        }

    # -- the loop with the §4.3 schedule ------------------------------------

    def run(self, max_ticks=None, sleep_fn=None, on_frame=None):
        """The §4.3 loop: tick, then sleep per the backoff schedule
        (base tick_s, ×2 to backoff_cap_s when nothing changed, reset on
        change).  Only run() sleeps — tick() never does.  max_ticks bounds
        the run for tests; sleep_fn injects the sleeper so the schedule
        can be asserted without waiting minutes."""
        sleep = time.sleep if sleep_fn is None else sleep_fn
        delay = self.tick_s
        frames = []
        ticks_done = 0
        try:
            while max_ticks is None or ticks_done < max_ticks:
                try:
                    frame = self.tick()
                except (HerdrError, LedgerError) as exc:
                    # Transient transport / ledger-lock errors must not
                    # stall the field; nothing was written on error.
                    self._run_notes.append({
                        "tick_attempt": ticks_done + 1,
                        "error": "%s: %s" % (type(exc).__name__, exc),
                    })
                    sleep(delay)
                    delay = next_delay(
                        False, delay, self.tick_s, self.backoff_cap_s)
                    ticks_done += 1
                    continue
                frames.append(frame)
                if on_frame is not None:
                    on_frame(frame)
                ticks_done += 1
                if max_ticks is not None and ticks_done >= max_ticks:
                    break
                delay = next_delay(
                    self._frame_changed(frame), delay,
                    self.tick_s, self.backoff_cap_s)
                sleep(delay)
        except KeyboardInterrupt:
            pass
        return frames

    def _frame_changed(self, frame):
        changed = (
            self._prev_frame_digest is None
            or frame["digest"] != self._prev_frame_digest)
        self._prev_frame_digest = frame["digest"]
        return changed

    @staticmethod
    def _frame_digest(frame):
        parts = []
        for desk_frame in frame["desks"]:
            out = desk_frame["output"]
            parts.append((
                desk_frame["desk"],
                desk_frame["pane_id"],
                desk_frame["agent_status"],
                out["digest"] if out is not None else None,
                out["truncated"] if out is not None else None,
                desk_frame["episode"],
                desk_frame["appended_record_id"],
            ))
        parts.append(tuple(frame["unresolved_desks"]))
        parts.append(frame["phase"]["tail_record_id"])
        return tuple(parts)
