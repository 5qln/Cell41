#!/usr/bin/env python3
"""conductor — the corrected live-turn read-back + the swarm (fan-out + converge).

Bridge-authored ("build it"), NOT an attested round: a thin extension over the
attested engine.  Two things it adds over the pinned conductor:

1. The corrected read-back.  herdr 0.8.2's ``agent.prompt`` writes the answer to
   the agent SESSION, not the pane screen; the old ``pane.wait_for_output`` read
   always timed out and surfaced as a false "HerdrRemoteError" outage.  The fix:
   after the prompt, wait for the turn to settle (``state_change_seq`` advances),
   then read the fenced answer from the session file.

2. The SWARM.  A concurrent walk whose shape is DERIVED from the word's signs
   (not hardcoded): sibling visits (same parent address) fan out concurrently on
   distinct desks, and the terminal desk CONVERGES — it receives the fan-out
   desks' full surfaces as CONTENT (never bare hashes), so it can actually
   crystallize.  The executed topology is recorded and saved as a PRESET — a
   reusable swarm flow ("see what it did, save it as presets").

Everything else (the ledger hash chain, the trail schema, the corruption
discipline) is the attested engine's own, reused by subclassing ``Orchestrator``
— never re-authored, never re-implemented.

Deterministic and stdlib-only; the only I/O is the herdr socket (prompt +
state-read), the agent session files (read-only), and the preset files it writes.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import sys
import time

sys.dont_write_bytecode = True

_AUTHORED = "/home/deploy/the-cell/rounds/R07-integration/authored"
if _AUTHORED not in sys.path:
    sys.path.insert(0, _AUTHORED)

import surface_contract as sc  # noqa: E402  (the sha-pinned seam)

orchestrate = sc.orchestrate

Orchestrator = orchestrate.Orchestrator
Instrument = orchestrate.Instrument
DESK_LABELS = orchestrate.DESK_LABELS
AgentNotFoundError = orchestrate.AgentNotFoundError
CentreWriteError = orchestrate.CentreWriteError
HerdrError = orchestrate.HerdrError
parse_surface = orchestrate.parse_surface
EQUATION_FORMS = orchestrate.EQUATION_FORMS
navigate = orchestrate.navigate


def fence_marker(turn_key):
    """The unique end marker (§4.5): ``⟦END <turn_key>⟧`` — replicated
    byte-for-byte from the instrument's own."""
    return "⟦END %s⟧" % turn_key


_FENCE_INSTRUCTION = (
    "When your answer is complete, emit exactly this end marker on a line "
    "by itself, nothing after it: %s"
)

_CONVERGE_HEADER = (
    "⟦SWARM FAN-OUT — the desks' full surfaces, in full (content, never "
    "references)⟧"
)

# The human's planted word (the podium — human-planted only, TTY-guarded).
# Carried verbatim as CONTENT into every desk's prompt (lesson 9: carry the
# FULL X, never a reduced stone; NP-08: the desks received a hash, not the
# question, and V held).
_PLANTED_WORD_PATH = "/home/deploy/the-cell/nodes/_/question.md"
_PLANTED_HEADER = ("⟦PLANTED WORD — the human's question, carried verbatim "
                   "(content, never a reference)⟧")
_PLANTED_FOOTER = "⟦END PLANTED WORD⟧"


class Conductor(Orchestrator):
    """The attested Orchestrator + the corrected read + the swarm."""

    # ------------------------------------------------------------------ read
    def _read_session_fenced(self, session_path, marker):
        """The last assistant text in the agent's session carrying the marker.
        herdr 0.8.2 writes the answer here; the pane screen never does."""
        last = None
        with open(session_path, "r", encoding="utf-8") as handle:
            for line in handle:
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(obj, dict) or obj.get("type") != "message":
                    continue
                msg = obj.get("message") or {}
                if msg.get("role") != "assistant":
                    continue
                for c in msg.get("content") or []:
                    if (isinstance(c, dict) and c.get("type") == "text"
                            and marker in c["text"]):
                        last = c["text"]
        if last is None:
            raise HerdrError(
                "the fenced answer carrying %r was not found in the session "
                "%r" % (marker, session_path))
        return last

    # -- the corrected turn primitive, split into fire / await / read --------
    def _fire(self, desk, key, prompt):
        """Deliver one prompt (guarded at the instrument chokepoint); return a
        handle for awaiting + reading.  Does NOT wait for the desk."""
        marker = fence_marker(key)
        full_prompt = prompt + "\n" + (_FENCE_INSTRUCTION % marker)
        pane_id = self.instrument.desks().get(desk)
        if pane_id is None:
            raise AgentNotFoundError(
                "desk %r resolves to no live pane" % desk)
        before = self.instrument.call("agent.get", {"target": pane_id})
        self.instrument.call(
            "agent.prompt",
            {"target": pane_id, "text": full_prompt})
        return {"desk": desk, "pane_id": pane_id,
                "before_seq": before.get("state_change_seq"),
                "session_path": before["agent_session"]["value"],
                "marker": marker}

    def _await(self, handle):
        """Wait for the fired turn to settle (a NEW idle, not a stale one)."""
        deadline = time.time() + self.wait_timeout_ms / 1000.0
        while time.time() < deadline:
            agent = self.instrument.call(
                "agent.get", {"target": handle["pane_id"]})
            if (agent.get("agent_status") == "idle"
                    and agent.get("state_change_seq") != handle["before_seq"]):
                return agent["agent_session"]["value"]
            time.sleep(1.0)
        raise HerdrError(
            "timed out waiting for desk %r to settle" % handle["desk"])

    def _prompt_and_read(self, desk, prompt, turn_key):
        """One live turn, corrected (sequential convenience over fire/await/
        read)."""
        handle = self._fire(desk, turn_key, prompt)
        session_path = self._await(handle)
        return {"text": self._read_session_fenced(session_path,
                                                  handle["marker"])}

    def _live_turn(self, visit, handoff_ref):
        """The corrected sequential turn — same contract as the attested one,
        but the answer is read from the session instead of the pane screen."""
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
                read = self._prompt_and_read(visit["letter"], prompt, key)
            finally:
                self.instrument.close()
        except AgentNotFoundError as exc:
            self._desk_adapter().close_turn(context)
            return {"status": "blocked", "detail": "agent_not_found",
                    "reason": ("the live desk resolved by label to a pane "
                               "with no agent — a blocked hold: %s" % exc)}
        except CentreWriteError as exc:
            self._desk_adapter().close_turn(context)
            return {"status": "guard-fail", "detail": "centre",
                    "reason": ("the centre guard refused the write before "
                               "any byte (K4): %s" % exc)}
        except HerdrError as exc:
            self._desk_adapter().close_turn(context)
            return {"status": "outage", "detail": type(exc).__name__,
                    "reason": ("an unreachable socket or a dialect failure — "
                               "an outage hold: %s" % exc)}
        self._desk_adapter().close_turn(context)
        answer = read["text"]
        parsed = parse_surface(answer, equation_forms=EQUATION_FORMS)
        if parsed.get("status") == "absent":
            return {"status": "blocked", "detail": "no-surface-announced",
                    "reason": "the desk announced no §3.6 surface"}
        if parsed.get("status") == "malformed":
            return {"status": "guard-fail", "detail": "surface-malformed",
                    "reason": "the desk's surface does not parse lawful"}
        payload_ref = "fenced:sha256:" + hashlib.sha256(
            answer.encode("utf-8")).hexdigest()
        return {"status": "answered", "text": answer, "parsed": parsed,
                "payload_ref": payload_ref, "turn_key": key}

    # --------------------------------------------- the planted word (D2) -----
    def _planted_word_text(self):
        """The human's planted question (the podium), read from disk —
        carried as CONTENT, never a reference.  Absent/empty reads None and
        the run proceeds on the desk bundle alone (honest, never a
        substituted fixture)."""
        try:
            with open(_PLANTED_WORD_PATH, "r", encoding="utf-8") as handle:
                text = handle.read().strip()
        except OSError:
            return None
        return text or None

    def _prompt_text(self, visit, handoff_ref):
        """The attested prompt + the planted word, carried verbatim as
        content — so every desk asks the SAME question from its own lens
        (the decentralized constitution run)."""
        base = super()._prompt_text(visit, handoff_ref)
        word = self._planted_word_text()
        if word:
            base += ("\n\n" + _PLANTED_HEADER + "\n" + word
                     + "\n" + _PLANTED_FOOTER)
        return base

    # ------------------------------------------------- swarm derivation ------
    def _parent_of(self, visit):
        """The parent address a visit hangs from, read from its signs."""
        orientation = visit.get("orientation")
        if orientation == "daughter":
            return visit.get("from")
        if orientation == "father":
            return visit.get("to")
        if orientation == "cousins":
            k = visit.get("k") or 0
            return navigate.common_father(visit.get("from"), k)
        return visit.get("from")

    def _derive_swarm(self):
        """Derive the swarm structure from the plan alone (D.6 — the signs are
        the topology).  Returns {seed, fanout_groups, converge} where
        fanout_groups is a list of concurrent groups (in dependency order) and
        converge is the terminal visit (the crystallizer / father)."""
        seed = self.plan[0]
        turns = [v for v in self.plan if v["index"] > 0]
        converge = turns[-1] if turns else None
        groups = []
        for v in turns[:-1]:
            parent = self._parent_of(v)
            if groups and self._parent_of(groups[-1][0]) == parent:
                groups[-1].append(v)
            else:
                groups.append([v])
        return {"seed": seed, "fanout_groups": groups, "converge": converge}

    # --------------------------------------------------------- swarm run -----
    def _open_instrument(self):
        context = self._desk_adapter().open_turn("", 0, "S")
        self.instrument = Instrument(
            socket_path=context.socket_path,
            desk_labels=dict(DESK_LABELS),
            timeout_s=self.timeout_s)

    def _hold(self, visit, kind, detail):
        landed = self._hold_record(visit, kind, detail, None)
        return {"visit": visit, "status": "held", "kind": kind,
                "detail": detail, "turn_key": landed.get("turn_key"),
                "payload_ref": None}

    def _finalize_turn(self, visit, text, key):
        parsed = parse_surface(text, equation_forms=EQUATION_FORMS)
        if parsed.get("status") == "absent":
            return self._hold(visit, "blocked", "no-surface-announced")
        if parsed.get("status") == "malformed":
            return self._hold(visit, "guard-fail", "surface-malformed")
        payload_ref = "fenced:sha256:" + hashlib.sha256(
            text.encode("utf-8")).hexdigest()
        landed = self._land_record(visit, payload_ref)
        return {"visit": visit, "status": "answered", "text": text,
                "parsed": parsed, "payload_ref": payload_ref,
                "turn_key": key, "record_id": landed.get("record_id")}

    def _run_group(self, group, handoff_ref):
        """Fan-out one concurrent group: fire all, await all, read all."""
        handles = []
        outcomes = []
        for visit in group:
            key = self._key_for(visit)
            prompt = self._prompt_text(visit, handoff_ref)
            try:
                handles.append((visit, key, self._fire(visit["letter"],
                                                       key, prompt)))
            except (AgentNotFoundError, CentreWriteError) as exc:
                outcomes.append(self._hold(visit, type(exc).__name__,
                                           str(exc)))
        for visit, key, handle in handles:
            try:
                session_path = self._await(handle)
                text = self._read_session_fenced(session_path,
                                                 handle["marker"])
                outcomes.append(self._finalize_turn(visit, text, key))
            except HerdrError as exc:
                outcomes.append(self._hold(visit, "outage",
                                           type(exc).__name__))
        return outcomes

    def _run_converge(self, converge_visit, fanout_results):
        """The terminal desk receives the fan-out desks' full surfaces as
        CONTENT (the fix from the findings) and crystallizes."""
        key = self._key_for(converge_visit)
        parts = [_CONVERGE_HEADER]
        for r in fanout_results:
            if r.get("status") == "answered":
                v = r["visit"]
                parts.append("=== %s (step %d) ===" % (v["letter"],
                                                       v["index"]))
                parts.append(r["text"])
        prompt = (self._prompt_text(converge_visit, None)
                  + "\n" + "\n\n".join(parts))
        try:
            handle = self._fire(converge_visit["letter"], key, prompt)
            session_path = self._await(handle)
            text = self._read_session_fenced(session_path, handle["marker"])
            return self._finalize_turn(converge_visit, text, key)
        except (AgentNotFoundError, CentreWriteError) as exc:
            return self._hold(converge_visit, type(exc).__name__, str(exc))
        except HerdrError as exc:
            return self._hold(converge_visit, "outage", type(exc).__name__)

    def _swarm_line(self, event, phase, cell, signal, content):
        line = self._line_base()
        line.update({"event": event, "phase": phase, "cell": cell,
                     "signal": signal, "content": content,
                     "return_question": None,
                     "ledger": self._ledger_block()})
        return line

    def run_swarm(self, preset_dir=None):
        """The swarm: seed → concurrent fan-out (sign-derived) → converge →
        run-end, recorded to the ledger + trail, and saved as a preset."""
        if any(line.get("event") == "run-end"
               for line in self._read_trail_lines()):
            return {"status": "already-complete", "actions": 0}
        states = self.read_states()
        self._emit_boot(states)
        swarm = self._derive_swarm()
        seed = swarm["seed"]
        seed_rec = self._seed_record(seed, self.scenario["seed"]["ref"])
        handoff_ref = seed_rec["payload_ref"]
        self._open_instrument()
        results = []
        try:
            for group in swarm["fanout_groups"]:
                group_results = self._run_group(group, handoff_ref)
                results.extend(group_results)
                for r in reversed(group_results):
                    if r.get("payload_ref"):
                        handoff_ref = r["payload_ref"]
                        break
            converge = swarm["converge"]
            converge_result = None
            if converge is not None:
                converge_result = self._run_converge(converge, results)
                results.append(converge_result)
        finally:
            self.instrument.close()

        for r in results:
            v = r["visit"]
            self._append_line(self._swarm_line(
                "turn", v["letter"], v["letter"],
                "swarm %s of %s at step %d — attended live" % (
                    "converge" if v is converge else "fan-out",
                    v["letter"], v["index"]),
                {"detail": r.get("status"), "payload_ref": r.get(
                    "payload_ref")}))

        holds = sum(1 for r in results
                    if r.get("status") not in ("answered", "already"))
        ended_in = None
        v_formed = False
        if converge_result and converge_result.get("status") == "answered":
            slots = (converge_result.get("parsed") or {}).get("slots") or {}
            has_slot = "∞0′" in slots or "∞0'" in slots
            # the F7 fix: a slot is "formed" only if V did not hold it — the
            # TRACE carries ":: held" when V refused to compose B″/∞0′.
            v_held = ":: held" in (converge_result.get("text") or "")
            if has_slot and not v_held:
                ended_in = "∞0′"
                v_formed = True
        status = "complete" if (not holds and v_formed) else "inconclusive"

        self._append_line(self._swarm_line(
            "run-end", "NOTE", None,
            "the swarm ended %s — ended_in %s; the topology is the preset" % (
                status, ended_in),
            {"status": status, "ended_in": ended_in,
             "actions": len(results)}))

        preset_path = None
        if preset_dir is not None:
            preset_path = self._save_preset(
                results, swarm, status, ended_in, preset_dir)

        return {"status": status, "ended_in": ended_in, "pattern": self.pattern,
                "actions": len(results),
                "visits": [{v: r.get("status")} for r in results
                           for v in [r["visit"]["letter"]]],
                "preset": preset_path}

    def _save_preset(self, results, swarm, status, ended_in, preset_dir):
        os.makedirs(preset_dir, exist_ok=True)
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y%m%dT%H%M%SZ")
        name = "swarm-%s-%s" % (self.scenario["word"], stamp)
        converge = swarm["converge"]
        preset = {
            "name": name,
            "word": self.scenario["word"],
            "pattern": self.pattern,
            "seed_ref": self.scenario["seed"]["ref"],
            "swarm": {
                "seed": "S",
                "fanout_groups": [[v["letter"] for v in g]
                                  for g in swarm["fanout_groups"]],
                "converge": converge["letter"] if converge else None,
            },
            "results": {
                r["visit"]["letter"]: {
                    "status": r.get("status"),
                    "payload_ref": r.get("payload_ref"),
                    "excerpt": (r.get("text") or "")[:200],
                } for r in results
            },
            "run": {"status": status, "ended_in": ended_in},
        }
        if converge is not None:
            cr = next((r for r in results if r["visit"] is converge), None)
            if cr and cr.get("status") == "answered":
                preset["converge_output"] = cr["text"]
        path = os.path.join(preset_dir, name + ".json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(preset, handle, ensure_ascii=False, indent=2)
        return path


def _run(argv):
    import argparse
    parser = argparse.ArgumentParser(prog="conductor")
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--ledger", required=True)
    parser.add_argument("--trail", required=True)
    parser.add_argument("--spec", default=None)
    parser.add_argument("--max-steps", type=int, default=None)
    parser.add_argument("--swarm", action="store_true",
                        help="run the concurrent swarm (fan-out + converge)")
    parser.add_argument("--preset-dir", default=None,
                        help="save the executed swarm topology as a preset here")
    args = parser.parse_args(argv)

    spec = {}
    if args.spec:
        with open(args.spec, "r", encoding="utf-8") as handle:
            spec = json.load(handle)

    conductor = Conductor(args.scenario, args.ledger, args.trail, spec=spec)
    if args.swarm:
        result = conductor.run_swarm(preset_dir=args.preset_dir)
    else:
        result = conductor.run(max_steps=args.max_steps)
    sys.stdout.write(json.dumps(result, ensure_ascii=False, sort_keys=True,
                                separators=(",", ":")) + "\n")


if __name__ == "__main__":
    _run(sys.argv[1:])
