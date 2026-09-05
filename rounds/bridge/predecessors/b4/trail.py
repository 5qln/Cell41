#!/usr/bin/env python3
"""trail — the observability deliverable: the formation trail of the
unattended run (R05 · B4, C7).

The trail is the FIELD side — everything that happened, beside the gate
ledger (the CHAIN side — only B″ fruits and his attestations).  Two
trails, never merged: construction refuses a trail path equal to the
ledger path, and the gate ledger is written through fractal_ledger only,
never here, never by hand.

What the trail is:

  * append-only — the writer opens O_APPEND, never rewrites, never
    rotates; a line is canonical JSON (UTF-8 passthrough — the bytes
    "∞0′ → ‖" survive verbatim) plus one newline, fsynced per line;
  * hash-chained — each line carries ``prev_hash`` (the sha256 of the
    previous line's exact on-disk bytes) and ``event_hash``
    (sha256(prev_hash ‖ canonical(line − event_hash)) — the same
    chaining the existing formation trail of the field uses), so a torn
    or mutated file is detected, never repaired (fail closed);
  * replayable from disk — ``read_trail`` / ``project`` rebuild the
    whole picture from the file alone, never from RAM;
  * readable MID-RUN — a reader may open the file while the run is
    writing: the complete prefix replays and projects consistently, and
    a torn trailing fragment is flagged and discarded — never a line,
    never valid (sha256 of empty is e3b0c44298fc…, never a decode);
  * decoding-not-transcript (D12) — every content field is a reference
    (sha256 + byte length); the desk's text and the context it received
    never enter the trail.

Statuses of ``read_trail``: ``absent`` (no file — not valid) | ``empty``
(zero bytes — not valid) | ``ok`` (every line parses, the chain
verifies) | ``partial`` (a torn tail was discarded; the complete prefix
parses and its chain verifies — the mid-run state) | ``damaged`` (a
COMPLETE line fails to parse or the chain breaks — fail closed, never a
guess).  A chain verdict below two lines reads ``undecidable``, never
trivially clean.

Deterministic and stdlib-only.
"""

from __future__ import annotations

import hashlib
import json
import os

__all__ = [
    "TRAIL_VERSION",
    "TRAIL_FIELDS",
    "FormationTrail",
    "read_trail",
    "project",
    "canonical_line_bytes",
    "EMPTY_SHA256",
    "EVENT_KINDS",
]

TRAIL_VERSION = "1"

EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()

# Every field a trail line carries — the builder and the reader share
# this one list (P4a's REQUIRED_TRAIL_FIELDS pattern).
TRAIL_FIELDS = (
    "trail_version", "scope", "seq", "ts", "phase", "source", "event",
    "signal", "content", "return_question", "turn_key", "cell", "cycle",
    "ledger", "conformance", "cost", "prev_hash", "event_hash",
)

# The event kinds the run writes (data — the reader never guesses).
EVENT_KINDS = frozenset((
    "boot", "seed", "turn", "hold", "budget-hold", "observe", "audit",
    "run-end",
))


def canonical_line_bytes(line):
    """The exact bytes a trail line occupies on disk: canonical JSON
    (sorted keys, compact separators, UTF-8 passthrough, no NaN) plus
    the trailing newline.  ``prev_hash`` chains THESE bytes."""
    return json.dumps(
        line, ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False).encode("utf-8") + b"\n"


def compute_event_hash(prev_hash, line_without_event_hash):
    """event_hash = sha256(prev_hash ‖ canonical(line − event_hash)) —
    the field-side chaining (the existing formation trail's formula:
    prev_hash rides the ASCII hex, then the canonical line bytes follow,
    no separator)."""
    payload = prev_hash + json.dumps(
        line_without_event_hash, ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class TrailError(Exception):
    """The trail refused an operation: a path collision with the ledger,
    a seq gap, or an append to a damaged trail."""


class FormationTrail:
    """The append-only, hash-chained formation trail.

    ``FormationTrail(path, ledger_path=None, clock=None)`` — every path
    is a parameter.  Construction REFUSES a trail path equal to the
    ledger path (two trails, never merged) and, when the file already
    exists (a cold restart continuing the same run), rebuilds the seq
    counter and the last line's bytes from the TRAIL ALONE and refuses
    to append to a damaged trail.

    The writer owns ``seq`` (gapless — a gap raises, never tolerated),
    ``ts`` (the injected clock), ``prev_hash`` and ``event_hash``.  The
    builder supplies the remaining fields with ``prev_hash`` and
    ``event_hash`` null — supplying them is a violation like any
    unknown field.
    """

    def __init__(self, path, ledger_path=None, clock=None):
        if ledger_path is not None and os.path.abspath(path) == \
                os.path.abspath(ledger_path):
            raise TrailError(
                "the trail path equals the ledger path — the formation "
                "trail is never the gate ledger (two trails, never "
                "merged)")
        self.path = path
        self.clock = clock
        self._count = 0
        self._last_bytes = None
        parent = os.path.dirname(path) or "."
        os.makedirs(parent, exist_ok=True)
        if os.path.exists(path):
            read = read_trail(path)
            if read["status"] == "damaged":
                raise TrailError(
                    "the existing trail is damaged — refusing to append "
                    "to it (fail closed): %s" % (read.get("damage"),))
            if read["status"] in ("ok", "partial"):
                self._count = len(read["lines"])
                raw = read["raw"]
                if raw:
                    # the last complete line's bytes AS WRITTEN — the
                    # trailing newline included (the append path chains
                    # the same form); a torn tail is discarded here and
                    # truncated at the next append (never spliced)
                    if raw.endswith(b"\n"):
                        prefix = raw[:-1]
                    else:
                        nl = raw.rfind(b"\n")
                        prefix = raw[:nl + 1] if nl != -1 else b""
                    inner = prefix
                    nl = inner.rfind(b"\n")
                    self._last_bytes = inner[nl + 1:] + b"\n"
        self._fd = None

    @property
    def count(self):
        """How many lines the trail holds — the writer's seq counter."""
        return self._count

    def append(self, line):
        """Append one line.  The line must carry every TRAIL_FIELDS field
        except the writer-owned trio (``seq`` is checked against the
        counter; ``prev_hash``/``event_hash`` must be null; ``ts`` is the
        injected clock when the line carries none), then the writer fills
        the chain fields, fsyncs, and returns the line as written."""
        if not isinstance(line, dict):
            raise TrailError("a trail line is a JSON object")
        unknown = set(line) - set(TRAIL_FIELDS)
        if unknown:
            raise TrailError(
                "trail line carries unknown field(s): %s"
                % ", ".join(sorted(unknown)))
        missing = [field for field in TRAIL_FIELDS
                   if field not in line
                   and field not in ("seq", "prev_hash", "event_hash")]
        if missing:
            raise TrailError(
                "trail line is missing required field(s): %s"
                % ", ".join(missing))
        if line.get("prev_hash") is not None:
            raise TrailError("the writer owns prev_hash — the builder "
                             "must leave it null")
        if line.get("event_hash") is not None:
            raise TrailError("the writer owns event_hash — the builder "
                             "must leave it null")
        if line.get("seq") != self._count:
            raise TrailError(
                "seq gap: line carries seq %r, the trail is at %d — a "
                "gap is a defect, never a tolerance"
                % (line.get("seq"), self._count))
        if line.get("ts") is None and self.clock is not None:
            line["ts"] = self._ts_string()
        line["prev_hash"] = (
            None if self._last_bytes is None
            else hashlib.sha256(self._last_bytes).hexdigest())
        line["event_hash"] = compute_event_hash(
            line["prev_hash"] or "",
            {key: value for key, value in line.items()
             if key != "event_hash"})
        payload = canonical_line_bytes(line)
        if self._fd is None:
            self._fd = open(self.path, "ab")
            raw = self._raw_bytes()
            if raw and not raw.endswith(b"\n"):
                # the torn boundary (a kill -9 mid-append): discard the
                # fragment at the last newline boundary, then append on
                # a fresh line — never splice two lines together
                os.ftruncate(self._fd.fileno(), raw.rfind(b"\n") + 1)
        self._fd.write(payload)
        self._fd.flush()
        os.fsync(self._fd.fileno())
        self._last_bytes = payload
        self._count += 1
        return line

    def _ts_string(self):
        value = self.clock()
        if isinstance(value, str):
            return value
        import datetime
        if isinstance(value, datetime.datetime):
            return value.isoformat()
        raise TrailError("the trail clock must return an RFC3339 UTC "
                         "string or a datetime: %r" % (value,))

    def _raw_bytes(self):
        try:
            with open(self.path, "rb") as handle:
                return handle.read()
        except FileNotFoundError:
            return b""

    def turn_key_index(self):
        """{turn_key: seq} for every recorded line — replayed from the
        trail alone (the restart's observe-repair map)."""
        index = {}
        for line in read_trail(self.path)["lines"]:
            key = line.get("turn_key")
            if isinstance(key, str):
                index.setdefault(key, line["seq"])
        return index

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

    status: absent | empty | ok | partial | damaged, as documented in
    the module header.  A torn final fragment is DISCARDED from the
    projection and reported — it is never a line, never valid (lens 3).
    The chain verdict needs two or more lines; below that it reads
    ``undecidable``, never trivially clean.
    """
    try:
        with open(path, "rb") as handle:
            raw = handle.read()
    except FileNotFoundError:
        return {"status": "absent", "lines": [], "damage": None,
                "chain": {"status": "undecidable", "first_break": None},
                "tail": None, "sha256": None, "raw": b""}
    if not raw:
        return {"status": "empty", "lines": [], "damage": None,
                "chain": {"status": "undecidable", "first_break": None},
                "tail": None, "sha256": EMPTY_SHA256, "raw": raw}
    torn = None
    body = raw.rstrip(b"\r\n")
    pieces = body.split(b"\n") if body else []
    complete = list(pieces)
    if not raw.endswith(b"\n") and pieces:
        # the last piece is unterminated: a complete final line missing
        # only its '\n' (the kill -9 boundary — the writer's fsync lost
        # the separator) still counts as a line; anything else is the
        # torn tail, discarded and reported
        candidate = pieces[-1]
        try:
            obj = json.loads(candidate.decode("utf-8"))
            looks_complete = isinstance(obj, dict) and not (
                set(TRAIL_FIELDS) - set(obj))
        except (UnicodeDecodeError, json.JSONDecodeError):
            looks_complete = False
        if looks_complete:
            pass  # complete = pieces, torn = None
        else:
            complete = pieces[:-1]
            torn = candidate
    damage = None
    lines = []
    for index, piece in enumerate(complete):
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
        missing = [field for field in TRAIL_FIELDS
                   if field not in obj]
        if missing:
            damage = {"line": index, "kind": "missing-fields",
                      "detail": ", ".join(missing)}
            break
        lines.append(obj)
    if damage is not None:
        return {"status": "damaged", "lines": lines, "damage": damage,
                "chain": {"status": "undecidable", "first_break": None},
                "tail": {"torn": torn is not None, "fragment_sha256":
                         hashlib.sha256(torn).hexdigest() if torn is not
                         None else None},
                "sha256": hashlib.sha256(raw).hexdigest(), "raw": raw}
    # chain integrity over the exact on-disk bytes (each line's bytes as
    # written, trailing newline included)
    terminated = [piece + b"\n" for piece in complete]
    chain = {"status": "ok", "first_break": None}
    if len(lines) < 2:
        chain["status"] = "undecidable"
    else:
        for index, line in enumerate(lines):
            if index == 0:
                if line.get("prev_hash") is not None:
                    chain = {"status": "broken", "first_break": 0}
                    break
                continue
            expected_prev = hashlib.sha256(
                terminated[index - 1]).hexdigest()
            if line.get("prev_hash") != expected_prev:
                chain = {"status": "broken", "first_break": index}
                break
            expected_event = compute_event_hash(
                line["prev_hash"],
                {key: value for key, value in line.items()
                 if key != "event_hash"})
            if line.get("event_hash") != expected_event:
                chain = {"status": "broken", "first_break": index}
                break
    if chain["status"] == "broken":
        damage = {"kind": "broken-chain", "line": chain["first_break"],
                  "detail": "prev_hash or event_hash does not match the "
                            "previous line's bytes"}
        return {"status": "damaged", "lines": lines, "damage": damage,
                "chain": chain,
                "tail": {"torn": torn is not None,
                         "fragment_sha256": hashlib.sha256(
                             torn).hexdigest() if torn is not None else
                         None},
                "sha256": hashlib.sha256(raw).hexdigest(), "raw": raw}
    status = "partial" if torn is not None else "ok"
    return {"status": status, "lines": lines, "damage": None,
            "chain": chain,
            "tail": {"torn": torn is not None,
                     "fragment_sha256": hashlib.sha256(
                         torn).hexdigest() if torn is not None else None},
            "sha256": hashlib.sha256(raw).hexdigest(), "raw": raw}


def project(read):
    """project(read_trail(path)) -> the consistent partial projection —
    readable mid-run, built from the complete prefix alone.

    The projection is per-cell, per-cycle: what formed (seed → turns →
    V's return question), which gates hold (and why), the budget state,
    the audit verdict when recorded, and the run-end status when
    recorded.  References only — the same D12 rule as the lines."""
    lines = read.get("lines") or []
    cells = {}
    holds = []
    audit = None
    run_end = None
    for line in lines:
        event = line.get("event")
        cell = line.get("cell")
        if event in ("seed", "turn", "hold", "budget-hold", "observe") \
                and cell is not None:
            entry = cells.setdefault(str(cell), {})
            cycle = line.get("cycle")
            bucket = entry.setdefault(cycle, {"events": []})
            bucket["events"].append({
                "seq": line["seq"], "event": event,
                "phase": line.get("phase"), "turn_key": line.get(
                    "turn_key"),
                "signal": line.get("signal"),
                "return_question": line.get("return_question"),
            })
            if event in ("hold", "budget-hold"):
                holds.append({
                    "cell": cell, "cycle": cycle, "phase": line.get(
                        "phase"),
                    "turn_key": line.get("turn_key"),
                    "seq": line["seq"], "signal": line.get("signal"),
                })
        elif event == "audit":
            audit = line.get("content")
        elif event == "run-end":
            run_end = line.get("content")
    completed = 0
    for cell_entries in cells.values():
        for cycle, bucket in cell_entries.items():
            if any(e["event"] == "turn" and e["phase"] == "V"
                   and e["return_question"] for e in bucket["events"]):
                completed += 1
    return {
        "status": read["status"],
        "chain": read["chain"],
        "tail": read["tail"],
        "cells": cells,
        "completed_cycles": completed,
        "holds": holds,
        "audit": audit,
        "run_end": run_end,
    }
