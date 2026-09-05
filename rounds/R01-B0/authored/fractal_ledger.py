#!/usr/bin/env python3
"""fractal_ledger — the B0 ledger and the record (R01 · B0, author: dsh).

A standalone, stdlib-only (Python 3.12+) module.  B0 is the trace's
foundation — the one thing that must never be lost — and this module is
only that foundation.  Nothing else: no conductor, no herdr socket, no Pi,
no gate semantics, no pane write path, no scheduling.  B0 stores records;
it does not decide what a gate means.

The five pieces:

  1. RecordValidator  — the §5.1 gate record schema as an enforcing
     validator.  All fifteen fields are required; absence of any of them
     is a violation, and an unknown extra field is a violation.
  2. LedgerWriter     — the append-only writer: single-writer lock,
     os.fsync per record, never rewritten, never rotated.  record_id is
     computed by the writer, never supplied by a caller; prev_hash is the
     tail record's record_id read from disk (the chain); ts is the writer
     clock (RFC3339 UTC, monotonic non-decreasing per file, equality
     allowed).
  3. LedgerVerifier   — verifies the whole chain from GENESIS and halts
     (LedgerVerificationError, CLI exit 4) at the first broken byte or
     record.  Fail closed: it never repairs, never skips, never truncates.
     The one tolerated case is the torn final line left by kill -9
     mid-append (no trailing newline, unparseable): it is discarded.
  4. LedgerLoader     — replay / re-arm from the ledger, never from RAM
     (§4.x): verify the chain, then rebuild the derived state maps (last
     record per address, open holds, cycle counts) from the replayed
     records, and write the disposable index sidecar.
  5. LedgerIndexBuilder — builds the derived, disposable index.  Deleting
     the sidecar (state/gates.index.json) must change nothing: replay
     rebuilds it and never reads it.

Record id definition (taken literally from §5.1):

    record_id = sha256(prev_hash ‖ canonical_json(record − record_id))

where ‖ is raw byte concatenation of the ASCII prev_hash and the UTF-8
canonical JSON of the record without its record_id field (no separator is
inserted), and canonical_json is one fixed form shared by writer and
verifier: json.dumps(sort_keys=True, ensure_ascii=False,
separators=(",", ":"), allow_nan=False).  ensure_ascii=False keeps every
string field — including the bytes "∞0′ → ‖" — as raw UTF-8 on disk.

Tail recovery boundary behaviour (0 / 1 / n records), always read from
disk alone, never from in-process state:

  * 0 records — the ledger file is absent or empty: tail_record() returns
    None and tail_record_id() returns GENESIS; verify() reports count 0
    and head GENESIS.
  * 1 record  — the sole record is the tail, whether its line ends with a
    trailing newline or not (a kill -9 can leave a complete line without
    the newline; that line still counts).  A second, fresh process reads
    it back correctly from disk alone.
  * n records — the tail is the last line that parses as a JSON object
    carrying record_id and prev_hash; a torn trailing fragment (no
    trailing newline, unparseable) is walked past, never a silent
    fall-back to GENESIS while records exist.  The scan reads the last
    64 KiB window and grows it backwards only if no record-shaped line is
    inside it.

CLI (python3 -m fractal_ledger / python3 fractal_ledger.py) subcommands:
verify, append --record JSON, tail, index.  Exit codes: 0 ok · 1 general
ledger error · 2 single-writer lock conflict (K2) · 3 record validation
(K1) · 4 chain verification halt (C2).
"""

import argparse
import datetime
import hashlib
import json
import os
import re
import sys

try:
    import fcntl
except ImportError:  # non-POSIX fallback path below
    fcntl = None


GENESIS = "GENESIS"

# Path defaults are the D2 paths (§5.2).  Every path this module touches is
# a parameter; the defaults exist for the live cell and for nothing else.
DEFAULT_LEDGER_PATH = "/home/deploy/the-cell/state/gates.jsonl"
DEFAULT_INDEX_PATH = "/home/deploy/the-cell/state/gates.index.json"

_TAIL_WINDOW = 65536

_HEX64_RE = re.compile(r"\A[0-9a-f]{64}\Z")
_ADDRESS_RE = re.compile(r"\A[+-]?[SGQPV]*\Z")

_GATES = ("x", "y", "z", "a", "b")
_STATES = ("attested", "held-pending", "mechanical")
_MARKS = ("emergent", "mechanical")
_VERDICTS = ("STASIS", "MOVING", "recast")
_CORRUPTIONS = ("L1", "L2", "L3", "L4", "V\u2205")
_AXIS_MODES = ("inherited", "anchored")


class LedgerError(Exception):
    """Base class for all ledger errors.  Errors halt; nothing continues
    silently."""


class RecordValidationError(LedgerError, ValueError):
    """A record violates §5.1 and was rejected before any byte was written
    (K1: rejected at append, never chained)."""


class LedgerVerificationError(LedgerError):
    """The chain on disk is broken.  Verification halts (fail closed, §10.3);
    the ledger is never repaired."""


class LedgerLockedError(LedgerError):
    """A second writer tried to open a ledger that already has a writer
    (K2: single-writer lock; the second records nothing)."""


def canonical_json(obj):
    """The one canonical JSON form used for everything the module writes or
    hashes: sorted keys, compact separators, UTF-8 passthrough, no NaN or
    Infinity."""
    return json.dumps(
        obj,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def compute_record_id(prev_hash, record_without_id):
    """record_id = sha256(prev_hash ‖ canonical_json(record − record_id)).

    The §5.1 formula taken literally: raw byte concatenation of the ASCII
    prev_hash and the UTF-8 canonical JSON of the record with its record_id
    field removed.  Returns a 64-char lowercase hex string."""
    payload = prev_hash + canonical_json(record_without_id)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def parse_utc_ts(value):
    """Parse an RFC3339 UTC timestamp and return a tz-aware datetime.

    Accepts the 'Z' or '+00:00' suffix, 'T' (or lowercase 't') separator,
    optional fractional seconds.  Raises ValueError for anything that is
    not a tz-aware UTC instant."""
    if type(value) is not str or not value:
        raise ValueError("ts must be an RFC3339 UTC string")
    if "T" not in value and "t" not in value:
        raise ValueError("ts must carry an RFC3339 T separator")
    s = value.replace("t", "T").replace("z", "Z")
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.datetime.fromisoformat(s)
    if dt.tzinfo is None:
        raise ValueError("ts must be timezone-aware")
    if dt.utcoffset() != datetime.timedelta(0):
        raise ValueError("ts must be UTC (offset zero)")
    return dt


def default_index_path(ledger_path):
    """Sidecar path derived from the ledger path: '.jsonl' is replaced by
    '.index.json' (matches §5.2 for the D2 path: gates.jsonl ->
    gates.index.json); any other ledger path gets '.index.json' appended."""
    base, ext = os.path.splitext(ledger_path)
    if ext == ".jsonl":
        return base + ".index.json"
    return ledger_path + ".index.json"


class RecordValidator:
    """The §5.1 gate record schema as an enforcing validator.

    All fifteen fields are required; absence of any of them is a violation
    and an unknown extra field is a violation.  The fifteen fields:

        record_id      hex64 — sha256(prev_hash ‖ canonical_json(record − record_id))
        prev_hash      hex64 | "GENESIS" — the previous record's record_id
        ts             RFC3339 UTC — monotonic non-decreasing per file
        address        ^[+-]?[SGQPV]*$  ("" = ε/root)
        gate           x | y | z | a | b
        state          attested | held-pending | mechanical
        mark           emergent | mechanical
        payload_ref    string — a durable reference, never content
        axis           {field:{mode:"inherited"|"anchored", anchor:<ref>}, delta:[<ref>…]}
        axis_verdict   STASIS | MOVING | recast | null (null only at a fresh anchor)
        corruption     L1…L4 | V∅ | null
        tentative      bool
        turn_key       hex64 — sha256(address ‖ gate ‖ attempt ‖ block_version)
        block_version  string — which block sat at this desk (g-essence@3)
        attestation_ref string | null — set only by a human act

    validate_full(record) checks a complete fifteen-field record (used at
    append before any byte is written, and by the verifier on every line).
    validate_call(record) checks the twelve caller-supplied fields; the
    writer-owned fields (record_id, prev_hash, ts) must not be supplied by
    a caller — supplying them is a violation like any unknown field.

    Notes on rules the schema quotes but cannot be enforced mechanically,
    so the validator does not over-reach (no gate semantics): "only a
    human moves a gate out of held-pending", "set only by a human act",
    "machine-posed; non-data until a human converts it" — these are
    semantic, not field-type rules.  The one cross-field rule that IS
    mechanical is enforced: axis_verdict null only at a fresh anchor
    (null ⇒ axis.field.mode == "anchored"; the converse is not implied by
    the quoted wording)."""

    FULL_FIELDS = frozenset((
        "record_id", "prev_hash", "ts", "address", "gate", "state", "mark",
        "payload_ref", "axis", "axis_verdict", "corruption", "tentative",
        "turn_key", "block_version", "attestation_ref",
    ))
    CALLER_FIELDS = frozenset((
        "address", "gate", "state", "mark", "payload_ref", "axis",
        "axis_verdict", "corruption", "tentative", "turn_key",
        "block_version", "attestation_ref",
    ))

    def validate_full(self, record, preparsed_ts=None):
        """Validate a complete fifteen-field record.  preparsed_ts, when a
        datetime is given, skips the ts re-parse (verifier fast path)."""
        self._require_exactly(record, self.FULL_FIELDS, "record")
        self._check_fields(record, full=True, preparsed_ts=preparsed_ts)

    def validate_call(self, record):
        """Validate the twelve caller-supplied fields of an append."""
        self._require_exactly(record, self.CALLER_FIELDS, "caller record")
        self._check_fields(record, full=False)

    @staticmethod
    def _require_exactly(record, allowed, what):
        if type(record) is not dict:
            raise RecordValidationError("%s is not a JSON object" % what)
        if not all(type(key) is str for key in record):
            raise RecordValidationError("%s carries a non-string key" % what)
        keys = set(record)
        missing = allowed - keys
        if missing:
            raise RecordValidationError(
                "%s is missing required field(s): %s"
                % (what, ", ".join(sorted(missing))))
        extra = keys - allowed
        if extra:
            raise RecordValidationError(
                "%s carries unknown field(s): %s"
                % (what, ", ".join(sorted(extra))))

    def _check_fields(self, record, full, preparsed_ts=None):
        if full:
            self._hex64(record["record_id"], "record_id")
            self._prev_hash(record["prev_hash"])
            if preparsed_ts is None:
                self._ts(record["ts"])
        self._address(record["address"])
        self._gate(record["gate"])
        self._state(record["state"])
        self._mark(record["mark"])
        self._string(record["payload_ref"], "payload_ref")
        self._axis(record["axis"])
        self._axis_verdict(record["axis_verdict"], record["axis"])
        self._corruption(record["corruption"])
        self._boolean(record["tentative"], "tentative")
        self._hex64(record["turn_key"], "turn_key")
        self._string(record["block_version"], "block_version")
        self._string_or_none(record["attestation_ref"], "attestation_ref")

    @staticmethod
    def _fail(field, value, rule):
        raise RecordValidationError(
            "field %r violates §5.1 (%s): %r" % (field, rule, value))

    def _hex64(self, value, field):
        if type(value) is not str or _HEX64_RE.fullmatch(value) is None:
            self._fail(field, value, "hex64 (64 lowercase hex chars)")

    def _prev_hash(self, value):
        if value != GENESIS and (
                type(value) is not str or _HEX64_RE.fullmatch(value) is None):
            self._fail("prev_hash", value, 'hex64 or "GENESIS"')

    def _ts(self, value):
        try:
            parse_utc_ts(value)
        except (ValueError, TypeError):
            self._fail("ts", value, "RFC3339 UTC")

    def _string(self, value, field):
        if type(value) is not str:
            self._fail(field, value, "string")

    def _string_or_none(self, value, field):
        if value is not None and type(value) is not str:
            self._fail(field, value, "string or null")

    def _boolean(self, value, field):
        if type(value) is not bool:
            self._fail(field, value, "bool")

    def _address(self, value):
        if type(value) is not str or _ADDRESS_RE.fullmatch(value) is None:
            self._fail("address", value, "^[+-]?[SGQPV]*$")

    def _gate(self, value):
        if value not in _GATES:
            self._fail("gate", value, "x|y|z|a|b")

    def _state(self, value):
        if value not in _STATES:
            self._fail("state", value, "attested|held-pending|mechanical")

    def _mark(self, value):
        if value not in _MARKS:
            self._fail("mark", value, "emergent|mechanical")

    def _corruption(self, value):
        if value is not None and value not in _CORRUPTIONS:
            self._fail("corruption", value, "L1…L4|V∅|null")

    def _axis(self, value):
        if type(value) is not dict:
            self._fail(
                "axis", value,
                '{field:{mode:"inherited"|"anchored", anchor:<ref>}, delta:[<ref>…]}')
        if set(value.keys()) != {"field", "delta"}:
            self._fail("axis", value, 'exactly the keys "field" and "delta"')
        field = value["field"]
        if type(field) is not dict or set(field.keys()) != {"mode", "anchor"}:
            self._fail("axis.field", field, '{mode, anchor}')
        if field["mode"] not in _AXIS_MODES:
            self._fail("axis.field.mode", field["mode"], "inherited|anchored")
        if type(field["anchor"]) is not str:
            self._fail("axis.field.anchor", field["anchor"], "string ref")
        delta = value["delta"]
        if type(delta) is not list or not all(
                type(item) is str for item in delta):
            self._fail("axis.delta", delta, "list of string refs")

    def _axis_verdict(self, value, axis):
        if value is not None and value not in _VERDICTS:
            self._fail("axis_verdict", value, "STASIS|MOVING|recast|null")
        if value is None and axis.get("field", {}).get("mode") != "anchored":
            self._fail(
                "axis_verdict", value,
                "null only at a fresh anchor (axis.field.mode must be 'anchored')")


def _utcnow():
    return datetime.datetime.now(datetime.timezone.utc)


def _write_all_fd(fd, data):
    view = memoryview(data)
    while view:
        written = os.write(fd, view)
        view = view[written:]


def _fsync_dir_best_effort(path):
    """Best-effort directory fsync so a freshly created file survives a
    crash (POSIX).  Never raises."""
    try:
        dfd = os.open(os.path.dirname(path) or ".", os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(dfd)
    except OSError:
        pass
    finally:
        os.close(dfd)


class _FileLock:
    """Single-writer lock: fcntl.flock(LOCK_EX | LOCK_NB) on POSIX.  The
    kernel releases the lock when the owning process dies (kill -9
    included), so the next writer can take over.  A non-POSIX fallback uses
    an O_EXCL owner file with pid-liveness checks."""

    def __init__(self, path):
        self.path = path
        self._fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o644)
        self._held = False
        self._owner_path = None

    def acquire(self):
        if fcntl is not None:
            try:
                fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                os.close(self._fd)
                self._fd = -1
                raise LedgerLockedError(
                    "ledger already has a writer (single-writer lock): %s"
                    % self.path) from None
            self._held = True
            return
        # Non-POSIX fallback: O_EXCL owner file, stale-pid recovery.
        owner = self.path + ".owner"
        while True:
            try:
                ofd = os.open(owner, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
            except FileExistsError:
                stale = False
                try:
                    with open(owner, "r", encoding="utf-8") as handle:
                        pid = int(handle.read().strip() or "0")
                    try:
                        os.kill(pid, 0)
                    except ProcessLookupError:
                        stale = True
                    except PermissionError:
                        stale = False
                except (OSError, ValueError):
                    stale = True
                if stale:
                    try:
                        os.unlink(owner)
                    except OSError:
                        pass
                    continue
                os.close(self._fd)
                self._fd = -1
                raise LedgerLockedError(
                    "ledger already has a writer (single-writer lock): %s"
                    % self.path)
            else:
                os.write(ofd, ("%d\n" % os.getpid()).encode("ascii"))
                os.close(ofd)
                self._owner_path = owner
                self._held = True
                return

    def release(self):
        if not self._held:
            return
        if fcntl is not None:
            fcntl.flock(self._fd, fcntl.LOCK_UN)
            os.close(self._fd)
            self._fd = -1
        else:
            os.close(self._fd)
            self._fd = -1
            try:
                os.unlink(self._owner_path)
            except OSError:
                pass
        self._held = False


def _parse_record_shaped(line):
    """Parse one line as a record-shaped JSON object (a dict carrying
    record_id and prev_hash); return the object or None."""
    try:
        obj = json.loads(line.decode("utf-8"))
    except Exception:
        return None
    if isinstance(obj, dict) and "record_id" in obj and "prev_hash" in obj:
        return obj
    return None


def _last_record_shaped_line(window):
    """Walk the window's lines backwards and return the last record-shaped
    object; None when the window holds none (the caller may grow it)."""
    body = window.rstrip(b"\r\n")
    while body:
        nl = body.rfind(b"\n")
        line = body[nl + 1:] if nl != -1 else body
        obj = _parse_record_shaped(line)
        if obj is not None:
            return obj
        if nl == -1:
            return None
        body = body[:nl]
    return None


def tail_record(ledger_path):
    """Read the last complete record-shaped line from disk alone.

    Boundary behaviour (0 / 1 / n records), never consulting in-process
    state:

      * 0 records — the file is absent or empty: returns None (the tail id
        is GENESIS).
      * 1 record  — the sole record is the tail, whether or not its line
        ends with a trailing newline (a kill -9 can leave a complete line
        without the newline; that line still counts).
      * n records — the last line that parses as a JSON object carrying
        record_id and prev_hash; a torn trailing fragment (no trailing
        newline, unparseable) is walked past.  There is no silent fall-back
        to GENESIS while records exist.

    Reads the last 64 KiB window and grows it backwards only if no
    record-shaped line sits inside it.  A permission or I/O error
    propagates (fail closed) rather than reading as "no records"."""
    try:
        size = os.path.getsize(ledger_path)
    except FileNotFoundError:
        return None
    if size == 0:
        return None
    window_start = size
    with open(ledger_path, "rb") as handle:
        while True:
            window_start = max(0, window_start - _TAIL_WINDOW)
            handle.seek(window_start)
            window = handle.read(size - window_start)
            record = _last_record_shaped_line(window)
            if record is not None:
                return record
            if window_start == 0:
                return None


def tail_record_id(ledger_path):
    """The tail record id read from disk alone: the last record's record_id,
    or GENESIS when the ledger holds zero complete records."""
    record = tail_record(ledger_path)
    return GENESIS if record is None else record["record_id"]


def _iter_lines(raw):
    """Yield (line_bytes, is_last, is_newline_terminated) for the ledger
    content.  Trailing blank newlines are trimmed; a final line without a
    trailing newline is the (possibly torn) tail line."""
    if not raw:
        return
    had_nl = raw.endswith(b"\n")
    body = raw.rstrip(b"\r\n")
    if not body:
        return
    lines = body.split(b"\n")
    last = len(lines) - 1
    for i, line in enumerate(lines):
        yield line, i == last, (i != last) or had_nl


class LedgerWriter:
    """The append-only writer.  Single-writer lock, fsync per record, never
    rewritten, never rotated (it is the trace).

    Append contract — append(record) requires EXACTLY the twelve
    caller-supplied fields:

        address, gate, state, mark, payload_ref, axis, axis_verdict,
        corruption, tentative, turn_key, block_version, attestation_ref

    The writer computes the other three fields itself, never from the
    caller:

      * prev_hash — the tail record's record_id read from disk (the
        chain); GENESIS for the first record.  Reading the tail from disk
        before every append means nothing depends on in-process state.
      * ts — the writer clock (clock= callable in the constructor, default
        UTC now), RFC3339 UTC, monotonic non-decreasing per file.  Equal
        timestamps are allowed ("non-decreasing" permits equality — H-3);
        on a backwards clock step the writer holds the previous ts instead
        of decreasing it.
      * record_id — sha256(prev_hash ‖ canonical_json(record − record_id)),
        computed by the writer, never supplied by a caller (supplying it is
        a violation, like any unknown field — K1).

    A record that violates §5.1 is rejected before any byte is written
    (RecordValidationError).  Every append is followed by os.fsync on the
    ledger file.  append returns the full fifteen-field record as written.

    The single-writer lock is taken in the constructor and held until
    close(); a second LedgerWriter on the same ledger raises
    LedgerLockedError and records nothing (K2, §10.3).  The lock file is
    "<ledger>.lock" next to the ledger (derived from the path parameter).

    Before every append the writer restores the file's final line boundary
    if a kill -9 tore it: a complete final record missing only its '\n'
    gets the separator back, and a torn trailing fragment is discarded
    (truncated at the last newline boundary) — so a fresh append after a
    torn append can never splice lines together and break the chain."""

    def __init__(self, ledger_path=None, lock_path=None, clock=None):
        self.ledger_path = (
            ledger_path if ledger_path is not None else DEFAULT_LEDGER_PATH)
        self.lock_path = (
            lock_path if lock_path is not None else (self.ledger_path + ".lock"))
        self._clock = clock if clock is not None else _utcnow
        self._closed = False
        self._fd = -1
        parent = os.path.dirname(self.ledger_path) or "."
        # state/ is created only under the path passed in as a parameter.
        os.makedirs(parent, exist_ok=True)
        self._lock = _FileLock(self.lock_path)
        self._lock.acquire()
        try:
            self._fd = os.open(
                self.ledger_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
        except Exception:
            self._lock.release()
            raise
        _fsync_dir_best_effort(self.ledger_path)

    def append(self, record):
        """Append one record.  Returns the full fifteen-field record as
        written (including the writer-computed record_id, prev_hash, ts)."""
        if self._closed:
            raise LedgerError("writer is closed")
        RecordValidator().validate_call(record)
        tail = tail_record(self.ledger_path)
        if tail is None:
            prev_hash = GENESIS
            last_ts = None
        else:
            prev_hash = tail.get("record_id")
            if type(prev_hash) is not str or _HEX64_RE.fullmatch(prev_hash) is None:
                raise LedgerError(
                    "the tail record on disk has no hex64 record_id; the chain "
                    "is broken — refusing to extend it (never repair)")
            try:
                last_ts = parse_utc_ts(tail.get("ts"))
            except (ValueError, TypeError):
                raise LedgerError(
                    "the tail record on disk has an invalid ts; the chain is "
                    "broken — refusing to extend it (never repair)")
        full = dict(record)
        full["ts"] = self._next_ts(last_ts)
        full["prev_hash"] = prev_hash
        full["record_id"] = compute_record_id(
            prev_hash,
            {key: value for key, value in full.items() if key != "record_id"})
        # K1: the complete record must satisfy §5.1 before any byte is written.
        RecordValidator().validate_full(full)
        line = canonical_json(full).encode("utf-8") + b"\n"
        self._restore_line_boundary()
        _write_all_fd(self._fd, line)
        os.fsync(self._fd)  # fsync per record — never weakened
        return full

    def _restore_line_boundary(self):
        """Recover the file's final line boundary before an append (C3),
        reading from disk alone, never from in-process state.

        A kill -9 mid-append can leave the ledger without its trailing
        newline: either a complete final record (the torn write lost only
        the '\\n') or a torn fragment of a record line.  Appending raw bytes
        after either would splice the new line onto the old one and break
        the chain, so the boundary is restored first:

          * the file ends with '\\n' (or is empty/absent): nothing to do;
          * the trailing bytes parse as a complete record line: write the
            missing '\\n' separator, keeping the record;
          * otherwise the trailing fragment is a torn partial line: it is
            discarded (the file is truncated at the last newline boundary,
            or to zero length when no complete line exists) and the append
            proceeds on a fresh line.

        A complete record is never modified; anything else the verifier
        still halts on (fail closed)."""
        try:
            size = os.fstat(self._fd).st_size
        except OSError:
            return
        if size == 0:
            return
        with open(self.ledger_path, "rb") as handle:
            handle.seek(size - 1)
            if handle.read(1) == b"\n":
                return
            start = size
            while True:
                start = max(0, start - _TAIL_WINDOW)
                handle.seek(start)
                window = handle.read(size - start)
                nl = window.rfind(b"\n")
                if nl != -1 or start == 0:
                    break
        boundary = start + nl + 1 if nl != -1 else 0
        tail = window[nl + 1:] if nl != -1 else window
        if _parse_record_shaped(tail) is not None:
            _write_all_fd(self._fd, b"\n")  # complete the missing separator
        else:
            os.ftruncate(self._fd, boundary)  # discard the torn fragment

    def _next_ts(self, last_ts):
        candidate = self._clock()
        if isinstance(candidate, str):
            try:
                candidate = parse_utc_ts(candidate)
            except ValueError:
                raise LedgerError(
                    "clock returned an unparseable ts: %r" % (candidate,))
        if not isinstance(candidate, datetime.datetime):
            raise LedgerError(
                "clock must return an RFC3339 UTC string or a datetime: %r"
                % (candidate,))
        if candidate.tzinfo is None:
            candidate = candidate.replace(tzinfo=datetime.timezone.utc)
        else:
            candidate = candidate.astimezone(datetime.timezone.utc)
        if last_ts is not None and candidate < last_ts:
            candidate = last_ts  # never decrease; equality is allowed (H-3)
        return candidate.strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"

    def close(self):
        if self._closed:
            return
        try:
            os.close(self._fd)
            self._fd = -1
        finally:
            self._closed = True
            self._lock.release()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return False

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass


class VerifyResult:
    """Outcome of a successful verify(): the replayed records, their count,
    and the chain head — the last record's record_id, or GENESIS when the
    ledger holds zero records."""

    __slots__ = ("records", "count", "head")

    def __init__(self, records, count, head):
        self.records = records
        self.count = count
        self.head = head

    def __repr__(self):
        return "VerifyResult(count=%d, head=%r)" % (self.count, self.head)


class LedgerVerifier:
    """Verifies the whole chain from GENESIS.  Halts — raises
    LedgerVerificationError (CLI exit 4) — at the first broken byte or
    record: fail closed, never repair, never skip, never truncate.

    Per line, in order: JSON parse (a newline-terminated line that does not
    parse halts; an unparseable FINAL line with no trailing newline is the
    one tolerated case — the torn tail of a kill -9 mid-append, discarded);
    full §5.1 validation (all fifteen fields, no extras); prev_hash chaining
    (GENESIS for the first record); record_id recomputation from the
    canonical JSON; ts monotonic non-decreasing per file."""

    def __init__(self, ledger_path=None):
        self.ledger_path = (
            ledger_path if ledger_path is not None else DEFAULT_LEDGER_PATH)

    def verify(self):
        try:
            with open(self.ledger_path, "rb") as handle:
                raw = handle.read()
        except FileNotFoundError:
            return VerifyResult([], 0, GENESIS)
        validator = RecordValidator()
        records = []
        prev_id = GENESIS
        last_ts = None
        index = 0
        for line, is_last, has_nl in _iter_lines(raw):
            try:
                obj = json.loads(line.decode("utf-8"))
            except Exception as exc:
                if is_last and not has_nl:
                    break  # torn final append (kill -9): discarded, never repaired
                raise LedgerVerificationError(
                    "record %d: line is not JSON (%s)" % (index + 1, exc)) from None
            if type(obj) is not dict:
                raise LedgerVerificationError(
                    "record %d: line is not a record object" % (index + 1))
            try:
                ts = parse_utc_ts(obj.get("ts"))
            except (ValueError, TypeError):
                ts = None
            try:
                validator.validate_full(obj, preparsed_ts=ts)
            except RecordValidationError as exc:
                raise LedgerVerificationError(
                    "record %d: %s" % (index + 1, exc)) from None
            if index == 0 and obj["prev_hash"] != GENESIS:
                raise LedgerVerificationError(
                    "record 1: prev_hash %r, expected %r"
                    % (obj["prev_hash"], GENESIS))
            if index > 0 and obj["prev_hash"] != prev_id:
                raise LedgerVerificationError(
                    "record %d: prev_hash %r, expected previous record_id %r"
                    % (index + 1, obj["prev_hash"], prev_id))
            expected_id = compute_record_id(
                obj["prev_hash"],
                {key: value for key, value in obj.items() if key != "record_id"})
            if obj["record_id"] != expected_id:
                raise LedgerVerificationError(
                    "record %d: record_id %r does not match recomputed %r"
                    % (index + 1, obj["record_id"], expected_id))
            if ts is not None:
                if last_ts is not None and ts < last_ts:
                    raise LedgerVerificationError(
                        "record %d: ts %r is earlier than the previous record's "
                        "ts (monotonic non-decreasing per file)"
                        % (index + 1, obj["ts"]))
                last_ts = ts
            records.append(obj)
            prev_id = obj["record_id"]
            index += 1
        return VerifyResult(records, len(records), prev_id if records else GENESIS)


def verify_ledger(ledger_path):
    """Convenience: verify a ledger path and return the VerifyResult."""
    return LedgerVerifier(ledger_path).verify()


def _cycle_count(address):
    """Mechanical cycle count for an address word: greedy left-to-right
    count of complete S→G→Q→P→V subsequences (sign ignored)."""
    stages = "SGQPV"
    stage = 0
    cycles = 0
    for ch in address:
        if ch == stages[stage]:
            stage += 1
            if stage == len(stages):
                cycles += 1
                stage = 0
    return cycles


class LedgerIndexBuilder:
    """Builds the derived, disposable index from replayed records.

    The sidecar is derived and disposable: deleting it must change nothing
    — replay rebuilds it and never reads it.  Mechanical definitions (no
    gate semantics are re-implemented here):

      * last_record_per_address — address -> record_id of the last record
        in chain order carrying that address;
      * open_holds — address -> record_id of a held-pending record that is
        the last record in chain order for its address (a later record at
        the same address supersedes it);
      * cycle_counts — address word -> number of complete S→G→Q→P→V cycles
        in that word (greedy left-to-right, sign ignored).
    """

    @staticmethod
    def build(records):
        last_record = {}
        open_holds = {}
        for record in records:
            address = record["address"]
            last_record[address] = record["record_id"]
            if record["state"] == "held-pending":
                open_holds[address] = record["record_id"]
            else:
                open_holds.pop(address, None)
        cycle_counts = {
            address: _cycle_count(address) for address in sorted(last_record)}
        return {
            "last_record_per_address": last_record,
            "open_holds": open_holds,
            "cycle_counts": cycle_counts,
        }


def write_index_file(index_path, index):
    """Atomically write the disposable index sidecar: tmp file + fsync +
    rename (the sidecar is derived; it is never read back)."""
    parent = os.path.dirname(index_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    tmp = index_path + ".tmp"
    payload = canonical_json(index).encode("utf-8")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
    try:
        _write_all_fd(fd, payload)
        os.fsync(fd)
    finally:
        os.close(fd)
    os.replace(tmp, index_path)
    _fsync_dir_best_effort(index_path)


class LoadedLedger:
    """What replay re-arms: the verified records, the chain head, the count,
    and the rebuilt derived index — from the ledger alone, never from RAM
    (§4.x: anything not in the ledger did not happen)."""

    __slots__ = ("records", "head", "count", "index", "index_path")

    def __init__(self, records, head, count, index, index_path):
        self.records = records
        self.head = head
        self.count = count
        self.index = index
        self.index_path = index_path

    def __repr__(self):
        return "LoadedLedger(count=%d, head=%r)" % (self.count, self.head)


class LedgerLoader:
    """Replay / re-arm from the ledger, never from RAM.

    load() verifies the whole chain (a broken chain halts — fail closed,
    §10.3, never repair), rebuilds the derived state maps from the replayed
    records, and — unless write_index=False — writes the disposable index
    sidecar (atomic tmp + fsync + rename).  The sidecar is never read
    back; deleting it changes nothing."""

    def __init__(self, ledger_path=None, index_path=None):
        self.ledger_path = (
            ledger_path if ledger_path is not None else DEFAULT_LEDGER_PATH)
        self.index_path = (
            default_index_path(self.ledger_path)
            if index_path is None else index_path)

    def load(self, write_index=True):
        result = LedgerVerifier(self.ledger_path).verify()
        index = LedgerIndexBuilder.build(result.records)
        if write_index and self.index_path is not None:
            write_index_file(self.index_path, index)
        return LoadedLedger(
            result.records, result.head, result.count, index, self.index_path)


def make_record(address="", gate="x", state="mechanical", mark="mechanical",
                payload_ref="", axis=None, axis_verdict=None, corruption=None,
                tentative=False, turn_key=None, block_version="g-essence@3",
                attestation_ref=None, attempt=""):
    """Convenience template of the twelve caller-supplied fields of a
    synthetic §5.1 record.  The writer computes record_id, prev_hash and ts
    — do not add them.  turn_key defaults to the quoted §5.1 formula
    sha256(address ‖ gate ‖ attempt ‖ block_version) with attempt=""; the
    axis defaults to a fresh anchor (mode anchored, verdict null)."""
    if axis is None:
        anchor = payload_ref if payload_ref else "anchor-0"
        axis = {"field": {"mode": "anchored", "anchor": anchor}, "delta": []}
    if turn_key is None:
        turn_key = hashlib.sha256(
            (address + gate + attempt + block_version).encode("utf-8")
        ).hexdigest()
    return {
        "address": address,
        "gate": gate,
        "state": state,
        "mark": mark,
        "payload_ref": payload_ref,
        "axis": axis,
        "axis_verdict": axis_verdict,
        "corruption": corruption,
        "tentative": tentative,
        "turn_key": turn_key,
        "block_version": block_version,
        "attestation_ref": attestation_ref,
    }


def main(argv=None):
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument(
        "--ledger", default=argparse.SUPPRESS,
        help="ledger path (default: %s)" % DEFAULT_LEDGER_PATH)
    parser = argparse.ArgumentParser(
        prog="fractal_ledger",
        description=(
            "B0 ledger tool: append / verify / tail / index.  Exit codes: "
            "0 ok · 1 general ledger error · 2 single-writer lock conflict "
            "(K2) · 3 record validation (K1) · 4 chain verification halt (C2)."),
        parents=[shared])
    parser.set_defaults(ledger=DEFAULT_LEDGER_PATH)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser(
        "verify", parents=[shared],
        help="verify the whole chain from GENESIS; exit 4 on a break")
    append_parser = sub.add_parser(
        "append", parents=[shared],
        help="append one record (single writer)")
    append_parser.add_argument(
        "--record", required=True, metavar="JSON",
        help="JSON object with the twelve caller-supplied §5.1 fields")
    sub.add_parser(
        "tail", parents=[shared],
        help="print the tail record id (GENESIS when the ledger holds no records)")
    index_parser = sub.add_parser(
        "index", parents=[shared],
        help="replay, verify and rebuild the disposable index sidecar")
    index_parser.add_argument(
        "--index", default=None,
        help="sidecar path (default: derived from --ledger)")

    args = parser.parse_args(argv)
    try:
        if args.command == "verify":
            result = LedgerVerifier(args.ledger).verify()
            print("head=%s count=%d" % (result.head, result.count))
            return 0
        if args.command == "append":
            try:
                record = json.loads(args.record)
            except json.JSONDecodeError as exc:
                print("error: --record is not JSON: %s" % exc, file=sys.stderr)
                return 3
            writer = LedgerWriter(args.ledger)
            try:
                full = writer.append(record)
            finally:
                writer.close()
            print(full["record_id"])
            return 0
        if args.command == "tail":
            print(tail_record_id(args.ledger))
            return 0
        if args.command == "index":
            loaded = LedgerLoader(args.ledger, args.index).load()
            idx = loaded.index
            print(
                "head=%s count=%d last_addresses=%d open_holds=%d cycle_counts=%d"
                % (loaded.head, loaded.count,
                   len(idx["last_record_per_address"]),
                   len(idx["open_holds"]),
                   len(idx["cycle_counts"])))
            return 0
    except LedgerLockedError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2
    except LedgerVerificationError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 4
    except RecordValidationError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 3
    except LedgerError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 1
    return 0


__all__ = [
    "GENESIS", "DEFAULT_LEDGER_PATH", "DEFAULT_INDEX_PATH",
    "LedgerError", "RecordValidationError", "LedgerVerificationError",
    "LedgerLockedError",
    "canonical_json", "compute_record_id", "parse_utc_ts",
    "RecordValidator", "LedgerWriter", "LedgerVerifier", "VerifyResult",
    "verify_ledger", "LedgerLoader", "LoadedLedger", "LedgerIndexBuilder",
    "write_index_file", "default_index_path",
    "tail_record", "tail_record_id", "make_record", "main",
]


if __name__ == "__main__":
    sys.exit(main())
