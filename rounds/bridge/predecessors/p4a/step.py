#!/usr/bin/env python3
"""step — the stepping surface (P4a): the controller protocol, the step
trail, the step-kind registry, the auto-continue controller and the
session runner.

One implementation of the loop exists — ``driver.Driver.take_turn`` /
``advance`` / ``boot`` — and this module never re-implements any of
them: the driver consults a ``StepSession`` before each step's first
side effect and after the step completes; the runner only CALLS the
driver's methods and plays the human's attestation acts through the
caller-supplied provider.

The step trail is NOT the gate ledger: it is a separate append-only
JSONL file, one line per step, ``prev_line_sha256`` chained line to
line.  The chain is integrity only — it carries no gate authority, no
trail line is ever promoted to a record, and ``gates.jsonl`` gains
nothing from stepping.  A trail path equal to its ledger path is
refused explicitly at construction (commission §3.7 lesson 1).

Stepping never sleeps, never polls, never waits on a human by default:
the blocking form (print the emission, wait for Enter) lives in
``run_session`` — and a keypress is NOT an attestation; nothing in this
module derives one from it (K4).

``zoom_in`` / ``zoom_out`` exist in ``STEP_KINDS`` as RESERVED registry
entries with no implementation — B3 adds descent without changing the
controller protocol or the trail schema (K5).
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import secrets

import conformance
import surface

__all__ = [
    "Stepper",
    "AutoStepper",
    "StepTrail",
    "read_trail",
    "STEP_KINDS",
    "run_session",
    "StepSession",
    "StepError",
    "StepKindError",
    "StepProtocolError",
    "StepTrailError",
    "TRAIL_VERSION",
    "REQUIRED_TRAIL_FIELDS",
    "DEFAULT_TRAIL_DIR",
]

TRAIL_VERSION = "1"

DEFAULT_TRAIL_DIR = os.environ.get(
    "FRACTAL_TRAIL_DIR", "/home/deploy/the-cell/state/trail")

# Every field a trail line must carry (commission P4a C3): no field
# absent, ever.  The builder and the reader share this one list.
REQUIRED_TRAIL_FIELDS = (
    "trail_version", "session_id", "seq", "at", "kind", "desk", "gate",
    "address_before", "address_after", "zoom", "operation",
    "intent_only", "context_in", "decoded", "compiled", "outcome",
    "conformance", "next", "ledger", "prev_line_sha256", "await",
)

# The step-kind registry (§4.1).  zoom_in / zoom_out are RESERVED with no
# implementation this round (K5): the schema and the protocol are fixed
# now so B3 adds descent without touching either.  zoom_out's inverse
# reading is marked derived (Appendix D §D.12 drift: "The zoom-out
# inverse is a derived reading, marked as such").
STEP_KINDS = {
    "boot": {
        "zoom_op": "none", "zoom_sign": None, "implemented": True,
        "reserved": False, "derived_reading": False,
        "description": "replay the chain, assert §7 trust for the walk",
    },
    "position": {
        "zoom_op": "none", "zoom_sign": None, "implemented": True,
        "reserved": False, "derived_reading": False,
        "description": "derive the standing place from the ledger",
    },
    "turn": {
        "zoom_op": "in", "zoom_sign": "−", "implemented": True,
        "reserved": False, "derived_reading": False,
        "description": "ONE desk turn: prompt → fence → read → propose",
    },
    "advance": {
        "zoom_op": "none", "zoom_sign": None, "implemented": True,
        "reserved": False, "derived_reading": False,
        "description": "try to open the gate after the last attested one",
    },
    "zoom_in": {
        "zoom_op": "in", "zoom_sign": "−", "implemented": False,
        "reserved": True, "derived_reading": False,
        "description": "RESERVED for B3 — descend into a sub-cell",
    },
    "zoom_out": {
        "zoom_op": "out", "zoom_sign": "+", "implemented": False,
        "reserved": True, "derived_reading": True,
        "description": "RESERVED for B3 — ascend to the father-frame",
    },
}


class StepError(Exception):
    """Base class for every stepping error.  Errors are loud, never
    silent."""


class StepKindError(StepError):
    """A reserved step kind was asked to run — no implementation exists
    this round (K5)."""


class StepProtocolError(StepError):
    """A controller returned something other than \"continue\"|\"stop\"."""


class StepTrailError(StepError):
    """The trail refused an operation: path collision with the ledger, a
    seq gap, or an append to a damaged trail."""


class Stepper:
    """The controller protocol — a protocol, not a base class callers are
    forced to inherit.  Any object with these two methods conforms:

        before(intent) -> "continue" | "stop"
        after(event)   -> "continue" | "stop"

    ``before`` receives the fully-formed intent — kind, desk, gate,
    address_before/after, zoom, the planned operation, the computed
    turn_key, and WHY this step is next — after the guards and the
    ledger replay (so the intent is real), before the first byte reaches
    the socket and before any record is written.  ``after`` receives the
    complete trail line, conformance report included.

    "stop" from either hook ends the session cleanly: the driver returns
    a status, raises nothing, writes no further record, and the trail's
    last line says what would have come next and why.  A keypress that
    continues a step is NOT an attestation and nothing may derive one
    from it (K4)."""

    def before(self, intent):
        return "continue"

    def after(self, event):
        return "continue"


class AutoStepper:
    """The auto-continue controller: answers "continue" to every hook —
    behaviour-neutral, so a stepped run walks exactly the same code path
    as an unstepped one (C1)."""

    def before(self, intent):
        return "continue"

    def after(self, event):
        return "continue"


def _canonical_line_bytes(line):
    """The exact bytes a trail line occupies on disk: canonical JSON
    (sorted keys, compact separators, UTF-8 passthrough, no NaN) plus
    the trailing newline.  ``prev_line_sha256`` hashes THESE bytes."""
    return json.dumps(
        line, ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False).encode("utf-8") + b"\n"


class StepTrail:
    """The append-only step trail — one JSONL line per step.

    ``StepTrail(path, ledger_path=…)`` — every path is a parameter.
    Construction REFUSES a trail path equal to its ledger path
    (commission §3.7 lesson 1) and, when the file already exists (a cold
    restart continuing the same session), rebuilds the seq counter from
    the TRAIL ALONE and refuses to append to a damaged trail.

    The writer owns ``seq`` (gapless — a gap raises, never tolerated)
    and ``prev_line_sha256`` (the sha256 of the previous line's bytes,
    null on seq 0): integrity only, never gate authority (C5).
    """

    def __init__(self, path, ledger_path=None):
        if ledger_path is not None and os.path.abspath(path) == \
                os.path.abspath(ledger_path):
            raise StepTrailError(
                "the trail path equals the ledger path — the step trail "
                "is never the gate ledger (two trails, never merged)")
        self.path = path
        self._count = 0
        self._last_bytes = None
        parent = os.path.dirname(path) or "."
        os.makedirs(parent, exist_ok=True)
        if os.path.exists(path):
            read = read_trail(path)
            if read["status"] == "damaged":
                raise StepTrailError(
                    "the existing trail is damaged — refusing to append "
                    "to it (fail closed): %s" % (read.get("damage"),))
            if read["status"] == "ok":
                self._count = len(read["lines"])
                raw = self._raw_bytes()
                if raw:
                    if raw.endswith(b"\n"):
                        # the last line's bytes as written, newline
                        # included — what the next line chains to
                        self._last_bytes = raw[
                            raw.rfind(b"\n", 0, len(raw) - 1) + 1:]
                    else:
                        # a complete final line missing only its '\n'
                        # (the torn kill -9 boundary): chain to its bytes
                        body = raw.rstrip(b"\n")
                        nl = body.rfind(b"\n")
                        self._last_bytes = body[nl + 1:] if nl != -1 else body
        self._fd = None

    @property
    def count(self):
        """How many lines the trail holds — the writer's seq counter."""
        return self._count

    def _raw_bytes(self):
        try:
            with open(self.path, "rb") as handle:
                return handle.read()
        except FileNotFoundError:
            return b""

    def append(self, line):
        """Append one line.  The line must carry every REQUIRED field
        with ``seq`` == the writer's counter and ``prev_line_sha256`` ==
        None; the writer fills the chain field, fsyncs, and returns the
        line as written."""
        missing = [field for field in REQUIRED_TRAIL_FIELDS
                   if field not in line]
        if missing:
            raise StepTrailError(
                "trail line is missing required field(s): %s"
                % ", ".join(missing))
        if line.get("prev_line_sha256") is not None:
            raise StepTrailError(
                "the writer owns prev_line_sha256 — the builder must "
                "leave it null")
        if line.get("seq") != self._count:
            raise StepTrailError(
                "seq gap: line carries seq %r, the session is at %d — a "
                "gap is a defect, never a tolerance"
                % (line.get("seq"), self._count))
        line["prev_line_sha256"] = (
            None if self._last_bytes is None
            else hashlib.sha256(self._last_bytes).hexdigest())
        payload = _canonical_line_bytes(line)
        if self._fd is None:
            self._fd = open(self.path, "ab")
            # a complete final line missing only its '\n' (the torn
            # kill -9 boundary) gets its separator back before the
            # append — never splice two lines together
            raw = self._raw_bytes()
            if raw and not raw.endswith(b"\n"):
                self._fd.write(b"\n")
        self._fd.write(payload)
        self._fd.flush()
        os.fsync(self._fd.fileno())
        self._last_bytes = payload
        self._count += 1
        return line

    def close(self):
        if self._fd is not None:
            self._fd.close()
            self._fd = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False


def read_trail(path):
    """read_trail(path) -> the trail's lines, honestly classified.

    status: ``absent`` (no file — not conformant) | ``empty`` (zero
    bytes — sha256 of empty is e3b0c44298fc… — not conformant) |
    ``damaged`` (a torn last line, an invalid line, a missing field, or
    a broken prev_line_sha256 chain) | ``ok``.  A torn last line is
    DAMAGED, never a valid step, never an empty-but-clean trail (C5).
    The chain verdict needs two or more lines; below that it reads
    ``undecidable``, never trivially clean (commission §3.7 lesson 3).
    """
    try:
        with open(path, "rb") as handle:
            raw = handle.read()
    except FileNotFoundError:
        return {"status": "absent", "lines": [], "damage": None,
                "chain": {"status": "undecidable", "first_break": None},
                "sha256": None}
    if not raw:
        return {"status": "empty", "lines": [], "damage": None,
                "chain": {"status": "undecidable", "first_break": None},
                "sha256": hashlib.sha256(b"").hexdigest()}
    damage = None
    lines = []
    pieces = raw.split(b"\n")
    # the writer always ends a line with '\n', so the final piece is the
    # empty string; a non-empty final piece is the (possibly torn) tail
    pieces = pieces[:-1] if pieces and pieces[-1] == b"" else pieces
    for index, piece in enumerate(pieces):
        try:
            obj = json.loads(piece.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            damage = {"line": index, "kind": "unparseable",
                      "detail": str(exc),
                      "bytes_sha256": hashlib.sha256(piece).hexdigest(),
                      "byte_count": len(piece)}
            break
        if not isinstance(obj, dict):
            damage = {"line": index, "kind": "not-an-object", "detail": ""}
            break
        missing = [field for field in REQUIRED_TRAIL_FIELDS
                   if field not in obj]
        if missing:
            damage = {"line": index, "kind": "missing-fields",
                      "detail": ", ".join(missing)}
            break
        lines.append(obj)
    if damage is not None:
        return {"status": "damaged", "lines": lines, "damage": damage,
                "chain": {"status": "undecidable", "first_break": None},
                "sha256": hashlib.sha256(raw).hexdigest()}
    # chain integrity over the exact on-disk bytes (each line's bytes
    # as written, trailing newline included)
    terminated = [piece + b"\n" for piece in pieces]
    if not raw.endswith(b"\n") and terminated:
        terminated[-1] = pieces[-1]  # the final line lost only its '\n'
    chain = {"status": "ok", "first_break": None}
    if len(lines) < 2:
        chain["status"] = "undecidable"
    else:
        for index, line in enumerate(lines):
            if index == 0:
                if line.get("prev_line_sha256") is not None:
                    chain = {"status": "broken", "first_break": 0}
                    break
            else:
                expected = hashlib.sha256(terminated[index - 1]).hexdigest()
                if line.get("prev_line_sha256") != expected:
                    chain = {"status": "broken", "first_break": index}
                    break
    status = "ok" if chain["status"] != "broken" else "damaged"
    if status == "damaged" and damage is None:
        damage = {"kind": "broken-chain",
                  "line": chain["first_break"],
                  "detail": "prev_line_sha256 does not match the previous "
                            "line's bytes"}
    return {"status": status, "lines": lines, "damage": damage,
            "chain": chain, "sha256": hashlib.sha256(raw).hexdigest()}


def _validate_controller_answer(answer, hook):
    if answer not in ("continue", "stop"):
        raise StepProtocolError(
            "Stepper.%s must return \"continue\" or \"stop\", got %r"
            % (hook, answer))
    return answer


class StepSession:
    """The emission engine the driver consults before and after each
    step.  Owns the trail writer, the session id, the seq counter, the
    observed-cell state (arrangement + per-desk surface parse results —
    references only, never the desk's text) and the conformance
    evaluation.

    ``on_fail="stop"`` (the default): a FAIL verdict in a step's
    conformance report stops the session; continuing past a FAIL is
    possible only with ``on_fail="continue"``, and the trail line then
    records that the policy was overridden (C2).
    """

    def __init__(self, stepper, trail_path, ledger_path=None,
                 session_id=None, on_fail="stop", sources_dir=None,
                 cell_provider=None, clock=None):
        if stepper is None:
            raise StepError("StepSession needs a controller (stepper)")
        self.stepper = stepper
        self.on_fail = "continue" if on_fail == "continue" else "stop"
        self.session_id = session_id if session_id else secrets.token_hex(6)
        if trail_path is None:
            trail_path = os.path.join(
                DEFAULT_TRAIL_DIR, self.session_id + ".jsonl")
        self.trail_path = trail_path
        self.ledger_path = ledger_path
        self.sources_dir = sources_dir
        self.cell_provider = cell_provider
        self._clock = clock if clock is not None else _utcnow
        self.trail = StepTrail(trail_path, ledger_path=ledger_path)
        # a cold restart continuing the SAME session: the seq counter and
        # the in-memory history rebuild from the TRAIL alone (C5)
        self.seq = self.trail.count
        self._lines = []
        if self.trail.count:
            existing = read_trail(trail_path)
            if existing["status"] == "ok":
                self._lines = list(existing["lines"])
        self._cell = {"observed": False, "arrangement": None,
                      "surfaces": {}, "question_ref": None}

    def close(self):
        self.trail.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False

    # -- cell observation (references only, from calls the walk already
    #    made — stepping never adds socket traffic of its own) ----------

    def record_arrangement(self, arrangement):
        if arrangement:
            self._cell["arrangement"] = sorted(set(arrangement))
            self._cell["observed"] = True

    def record_surface(self, desk, text):
        parsed = surface.parse_surface(
            text, equation_forms=conformance.EQUATION_FORMS)
        if parsed.get("status") != "absent":
            self._cell["surfaces"][desk] = parsed
            self._cell["observed"] = True
        return parsed

    def _refresh_question_ref(self, records):
        for record in records or []:
            if (record.get("gate") == "x" and record.get("address") == ""
                    and isinstance(record.get("payload_ref"), str)):
                self._cell["question_ref"] = record["payload_ref"]
                return

    # -- the two hook points ---------------------------------------------

    def consult(self, intent):
        """before(intent): the controller's chance to stop the step
        before its first side effect.  Returns ("continue", None) or
        ("stop", line) — on "stop" the intent line is written
        (intent_only, outcome "not-taken")."""
        answer = _validate_controller_answer(self.stepper.before(intent),
                                             "before")
        if answer == "continue":
            return "continue", None
        line = self._build_line(
            intent, intent_only=True,
            outcome={"status": "not-taken",
                     "turn_key": intent.get("turn_key"),
                     "reason": "the controller stopped the step before "
                               "its first side effect"})
        self._emit(line)
        return "stop", line

    def complete(self, event):
        """after(event): build the full line (conformance report
        included), append it, then consult the controller's after hook.
        Returns (line, stopped).  The ``next`` block is recomputed by
        the DRIVER from a fresh ledger replay after the step — never
        carried from the intent (commission §3.7 lesson 8)."""
        line = self._build_line(event, intent_only=False,
                                outcome=event.get("outcome") or {})
        stopped = self._emit(line)
        return line, stopped

    # -- the line ----------------------------------------------------------

    def _build_line(self, event, intent_only, outcome):
        step = {
            "kind": event.get("kind"),
            "desk": event.get("desk"),
            "gate": event.get("gate"),
            "address_before": event.get("address_before"),
            "address_after": event.get("address_after"),
            "zoom": event.get("zoom") or {"op": "none", "sign": None,
                                          "letter": None,
                                          "derived_reading": False},
            "operation": event.get("operation"),
            "intent_only": intent_only,
            "outcome": outcome,
            "decoded": event.get("decoded") or {
                "slots": {}, "source": "absent", "operation_steps": []},
            "compiled": event.get("compiled") or {
                "symbol": None, "gate": None, "landed": None,
                "payload_ref": None},
            "context_in": self._context_in(event),
            "surface_parse": event.get("surface_parse"),
        }
        ledger = event.get("ledger") or {}
        records = ledger.get("records") or []
        self._refresh_question_ref(records)
        if self.cell_provider is not None:
            provided = self.cell_provider()
            if provided:
                for key in ("arrangement", "surfaces", "observed"):
                    if key in provided:
                        self._cell[key] = provided[key]
        line = {
            "trail_version": TRAIL_VERSION,
            "session_id": self.session_id,
            "seq": self.seq,
            "at": self._clock().isoformat(),
            "kind": step["kind"],
            "desk": step["desk"],
            "gate": step["gate"],
            "address_before": step["address_before"],
            "address_after": step["address_after"],
            "zoom": step["zoom"],
            "operation": step["operation"],
            "intent_only": intent_only,
            "context_in": step["context_in"],
            "decoded": step["decoded"],
            "compiled": step["compiled"],
            "outcome": outcome,
            "conformance": None,
            "next": event.get("next") or {},
            "ledger": {"path": ledger.get("path"),
                       "count": ledger.get("count"),
                       "head": ledger.get("head")},
            "prev_line_sha256": None,
            "await": bool(event.get("await")),
        }
        ctx = {
            "step": step,
            "ledger": {"path": ledger.get("path"),
                       "records": records,
                       "count": ledger.get("count"),
                       "head": ledger.get("head")},
            "cell": self._cell,
            "session": {"lines": self._lines + [line]},
            "sources_dir": self.sources_dir,
        }
        report = conformance.evaluate(ctx)
        report["policy"] = self._policy_label(report["verdict"])
        line["conformance"] = report
        return line

    def _policy_label(self, verdict):
        if verdict == "FAIL" and self.on_fail == "continue":
            return ("continue-on-fail (explicitly configured — the "
                    "stop-on-fail default was overridden; the trail "
                    "records the override)")
        if verdict == "FAIL":
            return "stop-on-fail (triggered)"
        return "stop-on-fail"

    def _context_in(self, event):
        ledger = event.get("ledger") or {}
        records = ledger.get("records") or []
        prior = []
        for record in records:
            if (record.get("state") == "attested"
                    and record.get("attestation_ref") is not None
                    and isinstance(record.get("gate"), str)):
                prior.append({"gate": record["gate"],
                              "payload_ref": record.get("payload_ref")})
        return {"records": ledger.get("count"),
                "head": ledger.get("head"),
                "prior_outputs": prior}

    def _emit(self, line):
        """Append the line (writer owns seq + prev_line_sha256) and
        consult the after hook; a FAIL verdict with on_fail="stop"
        forces the stop."""
        self.trail.append(line)
        self.seq += 1
        self._lines.append(line)
        answer = _validate_controller_answer(self.stepper.after(line),
                                             "after")
        if line["conformance"]["verdict"] == "FAIL" and self.on_fail == "stop":
            answer = "stop"
        return answer == "stop"


def _utcnow():
    return datetime.datetime.now(datetime.timezone.utc)


# ---------------------------------------------------------------------------
# The session runner — walks a plan under the driver (which owns the one
# implementation of the loop).  No sleeping in the driver; the blocking
# form lives here, and a keypress is NOT an attestation (K4).
# ---------------------------------------------------------------------------

def run_session(driver, plan, attest=None, stepper=None, trail_path=None,
                session_id=None, on_fail="stop", sources_dir=None,
                cell_provider=None, interactive=False, printer=None,
                input_fn=None, max_steps=None):
    """run_session(driver, plan, …) -> the session result.

    Boots the driver (the boot is a step — the controller may stop it),
    then walks ``plan`` act by act: {"act": "take_turn", "desk": "G"} |
    {"act": "advance"} | {"act": "position"} | {"act": "attest", "desk":
    "G"}.  The attestation act is the HUMAN's channel: ``attest`` is the
    caller-supplied provider (a TTY stand-in in tests) — the runner
    plays it through and never fabricates one.  zoom_in / zoom_out are
    reserved and raise StepKindError (K5).

    With ``interactive=True`` the emission is printed and Enter awaited
    between steps — the blocking form lives HERE, not in the driver; a
    keypress continues a step and no code may derive an attestation
    from it.  The default never waits (stepping never sleeps, never
    polls, never waits on a human by default).

    Returns {"status": "complete"|"stopped", "reason", "steps",
    "trail_path", "lines", "session_verdict"}.
    """
    if driver.step_session is None:
        if stepper is None:
            raise StepError(
                "run_session needs a controller: the driver has no "
                "stepper attached and none was passed")
        driver.attach_stepper(stepper, trail_path=trail_path,
                              session_id=session_id, on_fail=on_fail,
                              sources_dir=sources_dir,
                              cell_provider=cell_provider)
    elif stepper is not None and stepper is not driver.stepper:
        raise StepError("the driver already has a different controller "
                        "attached")
    session = driver.step_session
    printer = printer if printer is not None else _print_line
    steps = []
    acts = list(plan or [])

    def _run_boot():
        result = driver.boot()
        steps.append(result)
        return result

    def _act(act):
        name = act.get("act")
        if name == "take_turn":
            desk = act.get("desk")
            text = act.get("text")
            if text is None:
                prompts = act.get("prompts") or {}
                text = prompts.get(desk)
            return driver.take_turn(desk, text)
        if name == "advance":
            return driver.advance()
        if name == "position":
            return driver.position()
        if name == "attest":
            if attest is None:
                raise StepError(
                    "the plan asks for a human attestation but no "
                    "attest provider was supplied — the runner never "
                    "fabricates one (K4)")
            return attest(act)
        if name in ("zoom_in", "zoom_out"):
            raise StepKindError(
                "%s is RESERVED for B3 — no implementation exists this "
                "round (K5)" % name)
        raise StepError("unknown plan act %r" % (name,))

    def _await_enter():
        if interactive and input_fn is not None:
            input_fn("step %d — press Enter to continue" % session.seq)

    boot = _run_boot()
    stopped = bool((boot.get("step") or {}).get("stopped"))
    if not stopped:
        _await_enter()
        for act in acts:
            if max_steps is not None and len(steps) >= max_steps:
                stopped = True
                break
            result = _act(act)
            steps.append(result)
            if isinstance(result, dict) and (result.get("step") or {}).get(
                    "stopped"):
                stopped = True
                break
            if (isinstance(result, dict)
                    and result.get("step") is not None):
                _await_enter()

    lines = session._lines
    context = {"step": None,
               "ledger": None,
               "cell": session._cell,
               "session": {"lines": lines},
               "sources_dir": session.sources_dir}
    verdict = conformance.aggregate(context)
    return {
        "status": "stopped" if stopped else "complete",
        "reason": ("the controller stopped the session" if stopped
                   else "the plan was walked"),
        "steps": steps,
        "trail_path": session.trail_path,
        "session_id": session.session_id,
        "lines": lines,
        "session_verdict": verdict,
    }


def _print_line(line):
    print(json.dumps(line, ensure_ascii=False))
