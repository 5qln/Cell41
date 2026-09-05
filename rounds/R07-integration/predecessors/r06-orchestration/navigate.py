#!/usr/bin/env python3
"""navigate — the sign-walk (R06 · orchestration, C2/C6): execute a
word by walking the signed paths; sequence / parallel / loop / custom
derive from the SIGNS (D.6), not from a topology enum.  The D.12 step
check (P4a's conformance.evaluate, imported — never re-authored) runs
after every navigation step.

The Fractal is the spec, quoted — never paraphrased into the criteria:

  D.6:
    "Orientation is read from the signs alone:
    k = 0 → B within A (daughter) A is the father-frame
    m = 0 → A within B (father) B is the father-frame
    k, m > 0 → neither (cousins) shared father, different branch
    empty address → same node"

  D.5:
    "addr(A → B) = +^k · (−x₁)(−x₂)…(−x_m)
    k = steps up to the common father
    m = steps down to the target"

  D.2:
    "The law has no base case and no terminal condition."  — the loop's
    bound is therefore the seed's declared boundary (scenario data),
    never a navigator constant; a loop whose seed declares no bound
    refuses to start (INCONCLUSIVE, never an infinite walk, never a
    silently capped one).

  D.3:
    "zoom in = append a letter S → SG → SGQ → …"  — sequence is a
    daughter chain (k = 0 every step: zoom in = append); parallel is
    cousins (k, m > 0) converging on a father (a later father step,
    m = 0, landing on the cousins' common father); loop appends until
    the declared bound; custom is free word composition — the lawful
    mix of signs that is none of the three.

The pattern label is DERIVED by this module from the walk's (k, m)
signs and the scenario's declared loop section alone — a scenario
carrying a pattern/topology field was already refused by word.py
(the signs are the topology, D.6).  The walk itself never touches a
socket and never writes a ledger record: the injected ``world`` (the
conductor's live wiring — orchestrate, or a deterministic test world)
carries every turn, seed, hold and ledger read; this module stays
pure — deterministic, stdlib-only, no network, no LLM, no subprocess
(K1).

World protocol (the conductor supplies an object with these methods):

  world.seed(visit, seed_ref)  -> {"record_id", "payload_ref"}
  world.turn(visit, handoff)   -> {"status": "answered", "text",
                                    "parsed", "payload_ref"} |
                                  {"status": "blocked"|"outage"|
                                            "guard-fail", "detail"}
  world.land(visit, payload_ref)   -> {"record_id"}
  world.hold(visit, kind, detail, report) -> {"record_id"}
  world.ledger()                -> {"path", "records", "count", "head"}

The per-step order is B4's, carried: pre-check (the imported D.12
guard) BEFORE the record lands — a FAIL in any DESK-FIDELITY item
holds the gate (never lands); after the land, the final report is
evaluated for the trail.  A V turn whose parsed surface carries no
∞0′ slot is REFUSED — "No V without ∞0'" (seal line 8, R6) — and a
walk whose non-seed visit seats S is refused at the imported centre
guard BEFORE any byte reaches the world (K4: zero socket bytes).
"""

from __future__ import annotations

import sys

sys.dont_write_bytecode = True

from surface_contract import (  # noqa: E402
    CentreWriteError,
    DESK_FIDELITY_ITEMS,
    STEP_KINDS,
    assert_not_centre,
    conformance,
    grammar,
    zoom_in,
    zoom_out,
)

from surface_contract import deep_letter  # noqa: E402
from surface_contract import word  # noqa: E402  (the scenario decoder)

__all__ = [
    "ORIENTATIONS",
    "orientation",
    "plan_walk",
    "walk",
    "common_father",
    "slot",
    "WalkError",
]

# ---------------------------------------------------------------------------
# The orientation vocabulary — the signs read as D.6 reads them (data).
# ---------------------------------------------------------------------------

ORIENTATIONS = {
    "daughter": ("k = 0 → B within A (daughter) A is the father-frame — "
                 "zoom in = append (D.3/D.6)"),
    "father": ("m = 0 → A within B (father) B is the father-frame — "
               "zoom out = strip (D.3/D.6)"),
    "cousins": ("k, m > 0 → neither (cousins) shared father, different "
                "branch (D.6)"),
    "same-node": "empty address → same node (D.6)",
}


def orientation(k, m):
    """The D.6 orientation of one signed path, read from the signs
    alone: k = the plus steps, m = the minus steps."""
    if k == 0 and m == 0:
        return "same-node"
    if k == 0:
        return "daughter"
    if m == 0:
        return "father"
    return "cousins"


class WalkError(ValueError):
    """The walk refused to plan or to run — INCONCLUSIVE, never a
    guessed walk."""


def common_father(address, k):
    """The address k frames up from ``address`` — the cousins' common
    father (D.5: k = steps up to the common father)."""
    current = address
    for _ in range(k):
        father = zoom_out(current)
        if father == current:
            break
        current = father
    return current


def slot(parsed, *names):
    """One decoded slot by name — B4's carried pattern (the grammar
    declares the slot \"∞0'\" as the codex writes it; \"∞0′\" is the
    commission table's glyph — both accepted, never normalised, K2)."""
    slots = parsed.get("slots") or {}
    for name in names:
        if name in slots:
            return slots[name]
    return None


# ---------------------------------------------------------------------------
# The plan — the walk's visits, addresses and letters derived from the
# declared paths (and the loop's expansion), the pattern from the signs.
# ---------------------------------------------------------------------------


def plan_walk(scenario):
    """The full walk plan of a decoded scenario:

      {"status": "ok", "pattern": <sequence|parallel|loop|custom>,
       "visits": [{index, address, letter, path, k, letters, m,
                   orientation}], "pattern_evidence": […]}
      {"status": "inconclusive"|"malformed", "reason": …}

    Loop expansion: from the last declared arrival, the loop's append
    letters are appended one at a time (each step the daughter path
    ``−L``) until the seed's declared bound — ``word_length`` (the
    address reaches the bound) or ``passes`` (the append word runs the
    bound times).  A loop whose seed declares no bound was already
    refused by word.decode_scenario; the plan refuses one whose bound
    can never produce a visit (the bound is already met — nothing
    moves).  The word must spell the expanded walk exactly — the plan
    is the word's own validation against the Grammar (C1)."""
    visits = []
    current = scenario["seed"]["address"]
    visits.append({
        "index": 0,
        "address": current,
        "letter": word.letter_of(current),
        "path": None,
        "k": None,
        "letters": None,
        "m": None,
        "orientation": None,
        "from": None,
    })
    for path in scenario["paths"]:
        current = path["to"]
        visits.append({
            "index": len(visits),
            "address": current,
            "letter": word.letter_of(current),
            "path": path["path"],
            "k": path["k"],
            "letters": path["letters"],
            "m": path["m"],
            "orientation": orientation(path["k"], path["m"]),
            "from": path["from"],
        })
    if scenario["loop"] is not None:
        bound = scenario["seed"]["bound"]
        append = scenario["loop"]["append"]
        produced = []
        if bound["kind"] == "word_length":
            produced = _expand_by_length(current, append, bound["value"])
        else:  # "passes"
            for _pass in range(bound["value"]):
                for letter in append:
                    current = _append_letter(current, letter)
                    produced.append((current, letter))
        if not produced:
            return {"status": "inconclusive",
                    "reason": ("the loop's bound is already met at %r — "
                               "append until a bound produces no visit; "
                               "a loop that does not move is not a loop "
                               "(D.2 has no terminal condition, so the "
                               "bound must come from the scenario's "
                               "seed)" % current)}
        for address, letter in produced:
            visits.append({
                "index": len(visits),
                "address": address,
                "letter": letter,
                "path": "−" + letter,
                "k": 0,
                "letters": [letter],
                "m": 1,
                "orientation": "daughter",
                "from": _father_of(address),
            })
    letters = "".join(visit["letter"] for visit in visits)
    if letters != scenario["word"]:
        return {"status": "malformed",
                "reason": ("the word %r does not spell the walk %r — "
                           "the scenario word must be the walk's "
                           "letters in order (D.3: zoom in = append)"
                           % (scenario["word"], letters))}
    pattern, evidence = _derive_pattern(scenario, visits)
    return {"status": "ok", "pattern": pattern, "visits": visits,
            "pattern_evidence": evidence,
            "reason": "the word walks the declared signed paths — the "
                      "pattern is read from the signs (D.6)"}


def _father_of(address):
    father = zoom_out(address)
    return father if father != address else None


def _append_letter(address, letter):
    child = zoom_in(address, letter)
    if child == address:
        raise WalkError("appending %r to %r does not move — the root "
                        "cell's centre S seats at ε itself (P4b's "
                        "declared exception, Appendix D.7); a loop step "
                        "that does not move is not a loop step"
                        % (letter, address))
    return child


def _expand_by_length(address, append, bound):
    """Append the loop's letters until the address reaches the declared
    word length — the bound is the seed's boundary (D.2 has no
    terminal condition; the stop is the scenario's declared data,
    never a constant here)."""
    produced = []
    current = address
    if len(current) >= bound:
        return produced
    index = 0
    while len(current) < bound:
        letter = append[index % len(append)]
        current = _append_letter(current, letter)
        produced.append((current, letter))
        index += 1
    return produced


def _derive_pattern(scenario, visits):
    """The pattern label — derived from the signs alone (data-driven
    precedence from the declared surface: loop > sequence > parallel >
    custom).  Never read from the scenario (word.py refused any
    topology enum key)."""
    steps = [visit for visit in visits if visit["path"] is not None]
    if scenario["loop"] is not None:
        return "loop", ["the scenario declares a loop section — the "
                        "walk appends until the seed's declared bound "
                        "(the seed's boundary; D.2 has no terminal "
                        "condition)"]
    orientations_seen = [step["orientation"] for step in steps]
    if all(item == "daughter" for item in orientations_seen):
        return "sequence", ["every path has k = 0 — a daughter chain "
                            "(zoom in = append, D.3: S → SG → SGQ)"]
    cousins = [step for step in steps if step["orientation"] == "cousins"]
    fathers = [step for step in steps if step["orientation"] == "father"]
    converging = []
    for cousin in cousins:
        frame = common_father(cousin["from"], cousin["k"])
        for father in fathers:
            if father["address"] == frame:
                converging.append((cousin, father, frame))
    if cousins and fathers and converging:
        cousin, father, frame = converging[0]
        return "parallel", [
            ("the cousins path %s (%r → %r, k = %d, m = %d) and the "
             "father step %s (%r → %r, m = 0) converge on the shared "
             "father-frame %r — cousins converging on a father (D.6)"
             % (cousin["path"], cousin["from"], cousin["address"],
                cousin["k"], cousin["m"], father["path"],
                father["from"], father["address"], frame))]
    return "custom", [
        ("a free word composition — the signs (%s) match none of the "
         "three named shapes: the lawful mix is custom (D.3: anything "
         "the word tells it to do)" % ", ".join(orientations_seen))]


# ---------------------------------------------------------------------------
# The walk — one step at a time, the D.12 check after every step.
# ---------------------------------------------------------------------------


def _zoom_of(visit):
    """The step's zoom glyph data — read from P4a's STEP_KINDS registry
    (imported data), never a literal here."""
    if visit["m"] and visit["m"] > 0:
        return {"op": STEP_KINDS["turn"]["zoom_op"],
                "sign": STEP_KINDS["turn"]["zoom_sign"],
                "letter": visit["letter"], "derived_reading": False}
    if visit["k"] and visit["k"] > 0:
        return {"op": STEP_KINDS["zoom_out"]["zoom_op"],
                "sign": STEP_KINDS["zoom_out"]["zoom_sign"],
                "letter": visit["letter"], "derived_reading": True}
    return {"op": "none", "sign": None, "letter": visit["letter"],
            "derived_reading": False}


def _evaluate(ctx):
    return conformance.evaluate(ctx)


def walk(scenario, world, seed_ref, sources_dir=None, session_lines=None,
         max_steps=None):
    """Execute the plan: one visit at a time, the D.12 check
    (conformance.evaluate — P4a, imported) after every navigation step.
    The seed visit is never prompted (the conductor is S — §4.8); a
    non-seed visit seating S is refused at the imported centre guard
    BEFORE any byte reaches the world (K4); a V turn without ∞0′ is
    REFUSED ("No V without ∞0'", seal line 8); a desk-fidelity FAIL
    holds the gate before its record lands (B4's policy, carried).  A
    step whose record already exists on the world's ledger reads
    ``observed`` — a cold restart never re-prompts (turn_key
    idempotency).  ``max_steps`` is the caller's resource budget — a
    step-limited walk ends "step-limited" (the return criterion is
    observed after the loop, never a break condition).

    Returns the assembled trace:

      {"status": "complete"|"inconclusive"|"refused"|"step-limited",
       "pattern", "visits": [per-step results incl. conformance],
       "return_question": <the ∞0′ slot ref or None>,
       "ended_in": "∞0′"|None}

    ``session_lines`` is the trail's line list so far (the context the
    aggregate reads).  Deterministic and stdlib-only — the world is
    the only I/O, and it is the caller's."""
    plan = plan_walk(scenario)
    if plan["status"] != "ok":
        return {"status": plan["status"], "pattern": None, "visits": [],
                "return_question": None, "ended_in": None,
                "reason": plan["reason"]}
    results = []
    handoff_ref = None
    holds = 0
    stepped = 0
    for visit in plan["visits"]:
        if max_steps is not None and stepped >= max_steps:
            break
        if visit["index"] == 0:
            step_result = _seed_step(scenario, world, seed_ref, visit,
                                     sources_dir, session_lines)
            handoff_ref = step_result.get("payload_ref")
        else:
            step_result = _visit_step(scenario, world, visit, handoff_ref,
                                      sources_dir, session_lines)
            if step_result.get("payload_ref"):
                handoff_ref = step_result["payload_ref"]
        if step_result.get("held"):
            holds += 1
        results.append(step_result)
        stepped += 1
    stepped_limit = (max_steps is not None
                     and stepped < len(plan["visits"]))
    if stepped_limit:
        return {"status": "step-limited", "pattern": plan["pattern"],
                "visits": results, "return_question": None,
                "ended_in": None,
                "pattern_evidence": plan["pattern_evidence"],
                "reason": "the caller's step budget ended the walk — "
                          "the return criterion is observed, never a "
                          "break condition"}
    last = results[-1] if results else None
    infinite_prime = (last or {}).get("infinite_prime_ref")
    ended_in = "∞0′" if infinite_prime else None
    status = "complete"
    if holds:
        status = "inconclusive"
    if (last or {}).get("refused"):
        status = "refused"
    if infinite_prime is None and not holds and (last or {}).get(
            "status") not in ("refused", "held"):
        # the walk ran clean but never reached V's ∞0′ — every run ends
        # in ∞0′ (C6): clean-but-no-return is INCONCLUSIVE, never clean
        status = "inconclusive"
    return {"status": status, "pattern": plan["pattern"], "visits": results,
            "return_question": infinite_prime, "ended_in": ended_in,
            "pattern_evidence": plan["pattern_evidence"]}


def _ctx_base(visit, step, parsed, world, sources_dir, session_lines,
              handoff_ref):
    """The conformance context — B4's carried shape (the imported check
    reads exactly this)."""
    authority = world.ledger()
    decoded = (parsed or {}).get("decoding") or {}
    return {
        "step": step,
        "ledger": {"path": authority.get("path"),
                   "records": authority.get("records") or [],
                   "count": authority.get("count", 0),
                   "head": authority.get("head")},
        "cell": {"observed": True,
                 "arrangement": list(grammar.COURSE),
                 "surfaces": ({visit["letter"]: parsed}
                              if parsed is not None else {}),
                 "question_ref": handoff_ref},
        "session": {"lines": list(session_lines or [])},
        "sources_dir": sources_dir,
    }


def _build_turn_step(visit, parsed, outcome, handoff_ref, authority):
    parsed = parsed or {}
    decoded = parsed.get("decoding") or {}
    return {
        "kind": "turn",
        "desk": visit["letter"],
        "gate": grammar.DESK_GATES[visit["letter"]],
        "address_before": visit["from"],
        "address_after": visit["address"],
        "zoom": _zoom_of(visit),
        "operation": ("word-walk step %d — %s %r → %r"
                      % (visit["index"], visit["orientation"],
                         visit["from"], visit["address"])),
        "intent_only": False,
        "outcome": outcome,
        "decoded": {"slots": parsed.get("slots") or {},
                    "source": "desk_surface",
                    "operation_steps": decoded.get("ops") or []},
        "compiled": {"symbol": (parsed.get("compiled") or {}).get(
            "symbol"),
            "gate": grammar.DESK_GATES[visit["letter"]],
            "landed": outcome.get("record_id"),
            "payload_ref": outcome.get("payload_ref")},
        "context_in": {"records": authority.get("count", 0),
                       "head": authority.get("head"),
                       "prior_outputs": []},
        "surface_parse": parsed or None,
    }


def _seed_step(scenario, world, seed_ref, visit, sources_dir,
               session_lines):
    """The seed visit: the world appends the tentative seed record (the
    conductor is S — never prompted, never the podium); the D.12 check
    runs on the seed step.  A seed the world reports ``already`` (a
    cold restart) reads ``observed`` — never re-appended."""
    landed = world.seed(visit, seed_ref)
    authority = world.ledger()
    if landed.get("already"):
        step = {
            "kind": "seed",
            "desk": "S",
            "gate": "x",
            "address_before": None,
            "address_after": visit["address"],
            "zoom": {"op": "none", "sign": None, "letter": "S",
                     "derived_reading": False},
            "operation": ("word-walk seed — already on the ledger; the "
                          "walk re-armed from disk alone and never "
                          "re-appended (turn_key idempotency, C7)"),
            "intent_only": False,
            "outcome": {"status": "observed",
                        "record_id": landed.get("record_id")},
            "decoded": {"slots": {}, "source": "absent",
                        "operation_steps": []},
            "compiled": {"symbol": None, "gate": "x",
                         "landed": landed.get("record_id"),
                         "payload_ref": landed.get("payload_ref")},
            "context_in": {"records": authority.get("count", 0),
                           "head": authority.get("head"),
                           "prior_outputs": []},
            "surface_parse": None,
        }
        report = _evaluate(_ctx_base(visit, step, None, world,
                                     sources_dir, session_lines, None))
        return {"index": visit["index"], "letter": visit["letter"],
                "address": visit["address"], "status": "observed",
                "payload_ref": landed.get("payload_ref"),
                "record_id": landed.get("record_id"),
                "turn_key": landed.get("turn_key"),
                "ledger_count": landed.get("count"),
                "ledger_head": landed.get("head"),
                "held": False, "refused": False,
                "infinite_prime_ref": None, "conformance": report}
    step = {
        "kind": "seed",
        "desk": "S",
        "gate": "x",
        "address_before": None,
        "address_after": visit["address"],
        "zoom": {"op": "none", "sign": None, "letter": "S",
                 "derived_reading": False},
        "operation": ("word-walk seed — the signless true start "
                      "(D.7: S = ∞0 → ?, bare · silent · no prefix · "
                      "no sign)"),
        "intent_only": False,
        "outcome": {"status": "seeded", "record_id": landed.get(
            "record_id")},
        "decoded": {"slots": {}, "source": "absent",
                    "operation_steps": []},
        "compiled": {"symbol": None, "gate": "x",
                     "landed": landed.get("record_id"),
                     "payload_ref": landed.get("payload_ref")},
        "context_in": {"records": authority.get("count", 0),
                       "head": authority.get("head"),
                       "prior_outputs": []},
        "surface_parse": None,
    }
    report = _evaluate(_ctx_base(visit, step, None, world, sources_dir,
                                 session_lines, None))
    return {"index": visit["index"], "letter": visit["letter"],
            "address": visit["address"], "status": "seeded",
            "payload_ref": landed.get("payload_ref"),
            "record_id": landed.get("record_id"),
            "turn_key": landed.get("turn_key"),
            "ledger_count": landed.get("count"),
            "ledger_head": landed.get("head"),
            "held": False, "refused": False,
            "infinite_prime_ref": None, "conformance": report}


def _visit_step(scenario, world, visit, handoff_ref, sources_dir,
                session_lines):
    """One navigation step: the centre guard first (S refused before
    any byte), then the world's turn, then the D.12 pre-check BEFORE
    the record lands (desk-fidelity FAIL → hold, B4's policy), the
    land, the final check — and for V: no ∞0′ → REFUSED (seal line 8,
    R6).  A turn the world reports ``already`` (the record exists — a
    cold restart) reads ``observed``: never re-prompted."""
    if visit["letter"] == "S":
        try:
            assert_not_centre(visit["letter"])
        except CentreWriteError as exc:
            landed = world.hold(visit, "guard-fail", "centre", None)
            result = _hold_result(visit, "guard-fail", "centre", landed,
                                  world, sources_dir, session_lines,
                                  handoff_ref, refused=True,
                                  reason=("the centre guard refused the "
                                          "S visit before any byte — "
                                          "S/podium is the forbidden "
                                          "path (K4, T-R3-02); nothing "
                                          "was sent: %s" % exc))
            result["turn_key"] = landed.get("turn_key")
            result["ledger_count"] = landed.get("count")
            result["ledger_head"] = landed.get("head")
            return result
    event = world.turn(visit, handoff_ref)
    if event.get("status") == "already":
        # the fenced record exists (a cold restart continuing the same
        # walk): observed, never re-prompted; the live answer's bytes
        # are gone (D12 — references, never content), so no decode is
        # guessed and no D.12 surface check is re-evaluated
        authority = world.ledger()
        step = _build_turn_step(
            visit, None,
            outcome={"status": "observed",
                     "record_id": event.get("record_id"),
                     "payload_ref": event.get("payload_ref")},
            handoff_ref=handoff_ref, authority=authority)
        report = _evaluate(_ctx_base(visit, step, None, world,
                                     sources_dir, session_lines,
                                     handoff_ref))
        return {"index": visit["index"], "letter": visit["letter"],
                "address": visit["address"], "status": "observed",
                "payload_ref": event.get("payload_ref"),
                "record_id": event.get("record_id"),
                "turn_key": event.get("turn_key"),
                "ledger_count": authority.get("count"),
                "ledger_head": authority.get("head"),
                "held": False, "refused": False,
                "infinite_prime_ref": None, "conformance": report}
    if event.get("status") != "answered":
        kind = event.get("status") or "blocked"
        detail = event.get("detail") or ""
        landed = world.hold(visit, kind, detail, None)
        result = _hold_result(visit, kind, detail, landed, world,
                              sources_dir, session_lines, handoff_ref,
                              refused=False,
                              reason=event.get("reason", ""))
        result["turn_key"] = landed.get("turn_key")
        result["ledger_count"] = landed.get("count")
        result["ledger_head"] = landed.get("head")
        return result
    parsed = event.get("parsed")
    payload_ref = event.get("payload_ref")
    # the per-step D.12 check, BEFORE the record lands (B4's order)
    authority = world.ledger()
    pre_step = _build_turn_step(
        visit, parsed,
        outcome={"status": "in-progress",
                 "turn_key": event.get("turn_key")},
        handoff_ref=handoff_ref, authority=authority)
    pre_report = _evaluate(_ctx_base(visit, pre_step, parsed, world,
                                     sources_dir, session_lines,
                                     handoff_ref))
    # C6: every run ends in ∞0′ — a V turn whose parsed surface
    # carries no ∞0′ slot is REFUSED first ("No V without ∞0'", seal
    # line 8 — B3's GS-VOID precedent: REFUSED dominates), before the
    # desk-fidelity policy, so the seal's reason rides the hold
    if visit["letter"] == "V":
        infinity = slot(parsed, "∞0′", "∞0'")
        if infinity is None:
            landed = world.hold(visit, "refused", "no-∞0′", pre_report)
            result = _hold_result(
                visit, "refused", "no-∞0′", landed, world, sources_dir,
                session_lines, handoff_ref, refused=True,
                reason=("a V with no ∞0′ is REFUSED — seal line 8: "
                        "\"No V without ∞0'\"; the run never ends clean "
                        "without the return question (C6)"))
            result["conformance"] = pre_report
            result["turn_key"] = landed.get("turn_key")
            result["ledger_count"] = landed.get("count")
            result["ledger_head"] = landed.get("head")
            return result
    failures = [item["id"] for item in pre_report["items"]
                if item["verdict"] == "FAIL"
                and item["id"] in DESK_FIDELITY_ITEMS]
    if failures:
        landed = world.hold(visit, "guard-fail",
                            "+".join(sorted(failures)), pre_report)
        result = _hold_result(visit, "guard-fail",
                              "+".join(sorted(failures)), landed, world,
                              sources_dir, session_lines, handoff_ref,
                              refused=False,
                              reason=("a DESK-FIDELITY FAIL held the "
                                      "gate before its record landed "
                                      "(B4's policy, carried)"))
        result["conformance"] = pre_report
        result["turn_key"] = landed.get("turn_key")
        result["ledger_count"] = landed.get("count")
        result["ledger_head"] = landed.get("head")
        return result
    landed = world.land(visit, payload_ref)
    # the final report for the trail (B4's final ctx)
    authority = world.ledger()
    final_step = _build_turn_step(
        visit, parsed,
        outcome={"status": "proposed",
                 "turn_key": event.get("turn_key"),
                 "record_id": landed.get("record_id"),
                 "payload_ref": payload_ref},
        handoff_ref=handoff_ref, authority=authority)
    final_report = _evaluate(_ctx_base(visit, final_step, parsed, world,
                                       sources_dir, session_lines,
                                       handoff_ref))
    if visit["letter"] == "V":
        # the landed V carries its ∞0′ (the pre-check refused the
        # absence) — the return question may seed the next cycle (D.8)
        infinity = slot(parsed, "∞0′", "∞0'")
        return {"index": visit["index"], "letter": visit["letter"],
                "address": visit["address"], "status": "proposed",
                "payload_ref": payload_ref,
                "record_id": landed.get("record_id"),
                "turn_key": landed.get("turn_key"),
                "ledger_count": landed.get("count"),
                "ledger_head": landed.get("head"),
                "held": False, "refused": False,
                "infinite_prime_ref": (infinity or {}).get("ref"),
                "conformance": final_report}
    return {"index": visit["index"], "letter": visit["letter"],
            "address": visit["address"], "status": "proposed",
            "payload_ref": payload_ref,
            "record_id": landed.get("record_id"),
            "turn_key": landed.get("turn_key"),
            "ledger_count": landed.get("count"),
            "ledger_head": landed.get("head"),
            "held": False, "refused": False,
            "infinite_prime_ref": None, "conformance": final_report}


def _hold_result(visit, kind, detail, landed, world, sources_dir,
                 session_lines, handoff_ref, refused, reason):
    authority = world.ledger()
    step = {
        "kind": "hold",
        "desk": visit["letter"],
        "gate": grammar.DESK_GATES.get(visit["letter"]),
        "address_before": visit["from"],
        "address_after": visit["address"],
        "zoom": _zoom_of(visit),
        "operation": ("word-walk step %d — %s: the gate failed to "
                      "lock; the hold is recorded, the walk keeps "
                      "moving, never auto-resolved (C1)"
                      % (visit["index"], visit["orientation"])),
        "intent_only": False,
        "outcome": {"status": "held", "record_id": landed.get(
            "record_id")},
        "decoded": {"slots": {}, "source": "absent",
                    "operation_steps": []},
        "compiled": {"symbol": None,
                     "gate": grammar.DESK_GATES.get(visit["letter"]),
                     "landed": landed.get("record_id"),
                     "payload_ref": None},
        "context_in": {"records": authority.get("count", 0),
                       "head": authority.get("head"),
                       "prior_outputs": []},
        "surface_parse": None,
    }
    report = _evaluate(_ctx_base(visit, step, None, world, sources_dir,
                                 session_lines, handoff_ref))
    return {"index": visit["index"], "letter": visit["letter"],
            "address": visit["address"], "status": "held",
            "hold_kind": kind, "detail": detail,
            "payload_ref": None,
            "record_id": landed.get("record_id"),
            "held": True, "refused": refused,
            "infinite_prime_ref": None, "reason": reason,
            "conformance": report}
