#!/usr/bin/env python3
"""arrangement — the arrangement model (PRD §5.8 + REQUIREMENTS L2; C2/C3).

    "`arrangement/<name>@<version>.json` — which block sits at which desk,
    + runtime pins"
    "A new version is a new directory. There is no edit path. The toy —
    which block sits where — changes by writing a new arrangement, which
    is itself a block."  ·  "The toy changes by rebuilding, never by
    changing blocks." (L2)
    "Each desk is an arrangement entry naming exactly four blocks:
    instruction (phase-gate), at least one skill, a tool surface, and a
    model. No naked agents (R4)." (PRD §7)

The toy is this file: which block id@version sits at which desk, plus the
runtime pins (§6.5: version pins live in the arrangement, never hardcoded)
and the state location (§6.2: state lives in the ledger, not extension
memory).  A new version is a new ``<name>@<version>.json`` file — write-once,
content-addressed (``sha256`` over the canonical JSON without the sha
field, the §5.1 record_id pattern), frozen, refused when it already exists,
with the refusal recorded.  Changing the toy is writing a new arrangement;
blocks are never edited by it.

Validation enforces the criteria end-to-end (invariant, not per call):
the five desks (4+1, never 3+1 — R1), each desk's four blocks (C3 — a
missing instruction/skill/tool-surface/model is a FAIL), each referenced
block resolves (an unresolvable ref is INCONCLUSIVE, never silently ok —
lens 6), each block's kind matches its slot, and each instruction block's
payload is the desk's full-cell bundle per the grammar (C5/C6).  Two
arrangements diff mechanically (K5) because every reference is an
id@version content address.

Deterministic, stdlib-only (plus the sanctioned B0 import — imported,
never copied), no wall clock, no network, no LLM.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys

from block import canonical_json, BlockStore  # noqa: F401  (re-exported)
import grammar

# B0's module is imported, never copied, never re-implemented (R01
# attested and closed).  The ledger directory is a parameter.
_LEDGER_DIR = os.environ.get(
    "FRACTAL_LEDGER_DIR", "/home/deploy/the-cell/ledger")
if _LEDGER_DIR not in sys.path:
    sys.path.insert(0, _LEDGER_DIR)

from fractal_ledger import make_record, RecordValidationError, RecordValidator  # noqa: E402

__all__ = [
    "DESK_SLOTS",
    "ArrangementError",
    "ArrangementValidationError",
    "ArrangementFrozenError",
    "ArrangementNotFoundError",
    "ArrangementStore",
    "author_arrangement",
    "load_arrangement",
    "validate_arrangement",
    "diff_arrangements",
    "split_ref",
]

# The four slots a desk entry names (C3) and the block kind each requires.
DESK_SLOTS = (
    ("instruction", "instruction", True),
    ("skills", "skill", False),
    ("tool_surface", "surface", True),
    ("model", "model", True),
)

_DESK_FIELDS = frozenset((
    "address", "runtime", "instruction", "skills", "tool_surface", "model",
    "model_route", "tars",
))
_ARRANGEMENT_FIELDS = frozenset((
    "name", "version", "sha256", "frozen", "desks", "runtime_pins", "state",
))
_PIN_KEYS = ("python", "herdr", "pi", "node")
_REF_RE = re.compile(r"\A[a-z0-9][a-z0-9._-]*@[a-z0-9][a-z0-9._-]*\Z")


class ArrangementError(Exception):
    """Base class for arrangement-store errors."""


class ArrangementValidationError(ArrangementError, ValueError):
    """The arrangement violates the shape and was refused before any byte
    was written."""


class ArrangementFrozenError(ArrangementError):
    """A new arrangement with an existing name@version was attempted — the
    toy changes by writing a NEW arrangement, never by editing one."""


class ArrangementNotFoundError(ArrangementError):
    """No such arrangement — absence, never a valid arrangement."""


def split_ref(ref):
    """Split an id@version reference into (id, version); raise on a
    non-reference (the reference grammar is the diff-ability guarantee)."""
    if type(ref) is not str or _REF_RE.fullmatch(ref) is None:
        raise ArrangementValidationError(
            "%r is not an id@version block reference" % (ref,))
    block_id, _, version = ref.partition("@")
    return block_id, version


def _check_handle(value, what):
    if type(value) is not str or re.fullmatch(r"[a-z0-9][a-z0-9._-]*",
                                              value) is None:
        raise ArrangementValidationError(
            "%s %r violates the handle grammar [a-z0-9][a-z0-9._-]*"
            % (what, value))


def _check_address(address):
    """The address must be a word over {S,G,Q,P,V} with an optional sign —
    enforced through B0's own RecordValidator (imported, never copied)."""
    record = make_record(address=address, gate="x", state="mechanical",
                         mark="mechanical", payload_ref="", block_version="")
    try:
        RecordValidator().validate_call(record)
    except RecordValidationError as exc:
        raise ArrangementValidationError(
            "desk address %r violates the §5.1 address grammar "
            "^[+-]?[SGQPV]*$: %s" % (address, exc)) from None


class ArrangementStore:
    """An arrangement store rooted at ``root`` (a parameter)."""

    def __init__(self, root):
        self.root = root
        self.rejections_path = os.path.join(root, "rejections.jsonl")

    def path(self, name, version):
        return os.path.join(self.root, "%s@%s.json" % (name, version))

    def exists(self, name, version):
        return os.path.isfile(self.path(name, version))

    # -- authoring ---------------------------------------------------------

    def author(self, name, version, desks, runtime_pins, state):
        """Write one arrangement.  Validates the whole shape first (nothing
        defective is ever written), refuses an existing name@version and
        records the refusal, then freezes the file 0444."""
        _check_handle(name, "arrangement name")
        _check_handle(version, "version")
        if type(desks) is not dict or set(desks.keys()) != set(grammar.COURSE):
            raise ArrangementValidationError(
                "an arrangement names exactly the five desks S G Q P V "
                "(4+1, never 3+1, never 6+1 — R1); got %r"
                % sorted(desks.keys()))
        for letter in grammar.COURSE:
            entry = desks[letter]
            if type(entry) is not dict:
                raise ArrangementValidationError(
                    "desk %s entry is not an object" % letter)
            extra = set(entry.keys()) - _DESK_FIELDS
            if extra:
                raise ArrangementValidationError(
                    "desk %s carries unknown field(s): %s"
                    % (letter, ", ".join(sorted(extra))))
            missing = _DESK_FIELDS - set(entry.keys())
            if missing:
                raise ArrangementValidationError(
                    "desk %s is missing field(s): %s"
                    % (letter, ", ".join(sorted(missing))))
            _check_address(entry["address"])
            if type(entry["runtime"]) is not str or not entry["runtime"]:
                raise ArrangementValidationError(
                    "desk %s runtime must be a non-empty string" % letter)
            split_ref(entry["instruction"])
            if (type(entry["skills"]) is not list
                    or len(entry["skills"]) < 1):
                raise ArrangementValidationError(
                    "desk %s must name at least one skill (no naked "
                    "agents — R4/C3)" % letter)
            for ref in entry["skills"]:
                split_ref(ref)
            split_ref(entry["tool_surface"])
            split_ref(entry["model"])
            for field in ("model_route", "tars"):
                if type(entry[field]) is not str:
                    raise ArrangementValidationError(
                        "desk %s %s must be a string" % (letter, field))
        if type(runtime_pins) is not dict or set(runtime_pins.keys()) != set(
                _PIN_KEYS):
            raise ArrangementValidationError(
                "runtime_pins must name exactly python herdr pi node "
                "(§6.5 — pins live in the arrangement)")
        for key in _PIN_KEYS:
            if type(runtime_pins[key]) is not str:
                raise ArrangementValidationError(
                    "runtime pin %s must be a string" % key)
        if (type(state) is not dict
                or set(state.keys()) != {"ledger_path"}
                or type(state.get("ledger_path")) is not str):
            raise ArrangementValidationError(
                "state must be {ledger_path: <string>} — state lives in the "
                "ledger, not extension memory (§6.2/E3)")

        path = self.path(name, version)
        if os.path.isfile(path):
            self.record_rejection(
                "%s@%s" % (name, version), "re-author",
                "the toy changes by writing a NEW arrangement, never by "
                "editing one (L2/C2)")
            raise ArrangementFrozenError(
                "arrangement %s@%s already exists — the toy changes by "
                "writing a new arrangement, never by editing one"
                % (name, version))

        record = {
            "name": name,
            "version": version,
            "desks": desks,
            "runtime_pins": runtime_pins,
            "state": state,
            "frozen": True,
        }
        record["sha256"] = hashlib.sha256(
            canonical_json(record).encode("utf-8")).hexdigest()
        os.makedirs(self.root, exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(canonical_json(record) + "\n")
        os.chmod(path, 0o444)
        return record

    # -- reading -----------------------------------------------------------

    def load(self, name, version):
        """Read an arrangement back; absence raises; a drifted sha or an
        unfrozen file raises ArrangementValidationError."""
        path = self.path(name, version)
        try:
            with open(path, "r", encoding="utf-8") as handle:
                raw = handle.read()
        except FileNotFoundError:
            raise ArrangementNotFoundError(
                "arrangement %s@%s does not exist — absence, never a valid "
                "arrangement" % (name, version)) from None
        try:
            record = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ArrangementValidationError(
                "arrangement %s@%s is not JSON (%s)"
                % (name, version, exc)) from None
        if (type(record) is not dict
                or set(record.keys()) != _ARRANGEMENT_FIELDS):
            raise ArrangementValidationError(
                "arrangement %s@%s does not carry exactly the fields "
                "{name, version, sha256, frozen, desks, runtime_pins, state}"
                % (name, version))
        if record["name"] != name or record["version"] != version:
            raise ArrangementValidationError(
                "arrangement %s@%s names %s@%s"
                % (name, version, record["name"], record["version"]))
        if record["frozen"] is not True:
            raise ArrangementValidationError(
                "arrangement %s@%s frozen is not true" % (name, version))
        expected = hashlib.sha256(canonical_json(
            {key: value for key, value in record.items()
             if key != "sha256"}).encode("utf-8")).hexdigest()
        if record["sha256"] != expected:
            raise ArrangementValidationError(
                "arrangement %s@%s sha256 %s does not match the recomputed "
                "%s — the arrangement was edited in place"
                % (name, version, record["sha256"], expected))
        return record

    # -- the write-once refusal, recorded ----------------------------------

    def record_rejection(self, target, attempt, reason):
        os.makedirs(self.root, exist_ok=True)
        seq = 1
        if os.path.isfile(self.rejections_path):
            with open(self.rejections_path, "r", encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(obj, dict) and isinstance(obj.get("seq"), int):
                        seq = max(seq, obj["seq"] + 1)
        record = {"seq": seq, "target": target, "attempt": attempt,
                  "reason": reason}
        with open(self.rejections_path, "a", encoding="utf-8") as handle:
            handle.write(canonical_json(record) + "\n")
        os.chmod(self.rejections_path, 0o644)
        return record

    def rejections(self):
        if not os.path.isfile(self.rejections_path):
            return []
        out = []
        with open(self.rejections_path, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(obj, dict):
                    out.append(obj)
        return out


def author_arrangement(store, name, version, desks, runtime_pins, state):
    return store.author(name, version, desks, runtime_pins, state)


def load_arrangement(store, name, version):
    return store.load(name, version)


def validate_arrangement(record, block_store=None):
    """The end-to-end check (lens 2): every desk names all four blocks
    (C3 — a missing skill/tool/model is a FAIL), every reference resolves
    to the right kind of block, and every instruction payload is the
    desk's full-cell bundle per the grammar (C5/C6).  An unresolvable
    reference is INCONCLUSIVE, never a guessed ok (lens 6)."""
    items = []
    problems = 0
    unknowns = 0

    def item(item_id, verdict, citation, evidence):
        nonlocal problems, unknowns
        if verdict == "FAIL":
            problems += 1
        elif verdict == "INCONCLUSIVE":
            unknowns += 1
        items.append({"id": item_id, "verdict": verdict,
                      "citation": citation, "evidence": evidence})

    if type(record) is not dict or "desks" not in record:
        return {"status": "fail", "items": [{
            "id": "AR-RECORD",
            "verdict": "FAIL",
            "citation": "PRD §5.8: \"arrangement/<name>@<version>.json — "
                        "which block sits at which desk, + runtime pins\"",
            "evidence": "the arrangement is not a record object"}]}

    desks = record.get("desks")
    if type(desks) is not dict or set(desks.keys()) != set(grammar.COURSE):
        item(
            "AR-DESKS", "FAIL",
            "REQUIREMENTS R1: \"Every unit, at every scale, is 4+1: one "
            "center that may hold only a question, four movements G·Q·P·V. "
            "Never 3+1, never 6+1.\"",
            "desks = %r, expected exactly S G Q P V"
            % (sorted(desks.keys()) if isinstance(desks, dict) else desks))
        return {"status": "fail", "items": items}

    for letter in grammar.COURSE:
        entry = desks.get(letter)
        if type(entry) is not dict:
            item("AR-DESK-%s" % letter, "FAIL",
                 "PRD §7: \"Each desk is an arrangement entry naming "
                 "exactly four blocks\"",
                 "desk %s is not an entry object" % letter)
            continue
        # -- the four blocks: named or FAIL (C3) ----------------------------
        named_ok = True
        for slot, kind, single in DESK_SLOTS:
            if single:
                ref = entry.get(slot)
                if type(ref) is not str or not ref:
                    named_ok = False
                    item("AR-%s-%s" % (slot, letter), "FAIL",
                         "PRD §7: \"Each desk is an arrangement entry "
                         "naming exactly four blocks: instruction "
                         "(phase-gate), at least one skill, a tool "
                         "surface, and a model. **No naked agents** "
                         "(R4).\"",
                         "desk %s names no %s block" % (letter, slot))
                    continue
            else:
                refs = entry.get(slot)
                if type(refs) is not list or len(refs) < 1:
                    named_ok = False
                    item("AR-%s-%s" % (slot, letter), "FAIL",
                         "PRD §7: \"…at least one skill…\" · commission "
                         "C3: \"a missing skill/tool/model is a FAIL\"",
                         "desk %s names no skills" % letter)
                    continue
            item("AR-%s-%s" % (slot, letter), "PASS",
                 "PRD §7: \"Each desk is an arrangement entry naming "
                 "exactly four blocks: instruction (phase-gate), at least "
                 "one skill, a tool surface, and a model. **No naked "
                 "agents** (R4).\"",
                 "desk %s names %s: %s"
                 % (letter, slot, ref if single else ", ".join(refs)))
        if not named_ok or type(entry.get("instruction")) is not str:
            continue
        # -- resolution and kind (INCONCLUSIVE when unobservable) -----------
        for slot, kind, single in DESK_SLOTS:
            refs = ([entry.get(slot)] if single else entry.get(slot)) or []
            if not refs:
                continue  # already FAILed above
            for ref in refs:
                if block_store is None:
                    item("AR-RESOLVE-%s-%s" % (slot, letter), "INCONCLUSIVE",
                         "commission C3 / lens 6: an unresolvable block "
                         "reference must never read valid",
                         "no block store supplied; %s %s unobservable"
                         % (letter, ref))
                    continue
                try:
                    block_id, version = split_ref(ref)
                except ArrangementValidationError as exc:
                    item("AR-REF-%s-%s" % (slot, letter), "FAIL",
                         "commission K5: \"the arrangement references them "
                         "by id@version\"",
                         str(exc))
                    continue
                report = block_store.verify(block_id, version)
                if report["status"] == "absent":
                    item("AR-RESOLVE-%s-%s" % (slot, letter), "INCONCLUSIVE",
                         "commission lens 6: \"anything unobservable "
                         "reports INCONCLUSIVE, never clean\"",
                         "%s %s is absent from the block store"
                         % (letter, ref))
                    continue
                if report["status"] != "ok":
                    item("AR-RESOLVE-%s-%s" % (slot, letter), "FAIL",
                         "PRD §5.8: blocks are content-addressed and "
                         "frozen",
                         "%s %s: %s" % (letter, ref, report["reason"]))
                    continue
                if report["kind"] != kind:
                    item("AR-KIND-%s-%s" % (slot, letter), "FAIL",
                         "PRD §5.8: \"kind: instruction|skill|tool|model|"
                         "surface\" — the slot names the kind",
                         "desk %s %s block %s has kind %r, expected %r"
                         % (letter, slot, ref, report["kind"], kind))
                    continue
                item("AR-RESOLVE-%s-%s" % (slot, letter), "PASS",
                     "PRD §5.8: \"block.json = {id, version, kind…, "
                     "sha256…, frozen: true}\" — resolved and content-"
                     "addressed",
                     "%s %s resolves: kind %s, sha256 %s"
                     % (letter, ref, report["kind"],
                        report["sha256"][:12]))
                if slot == "instruction":
                    # -- C5/C6: the payload is the desk's full-cell bundle --
                    try:
                        result = block_store.read(block_id, version)
                    except Exception as exc:  # noqa: BLE001 — any read failure is unobservable
                        item("AR-BUNDLE-%s" % letter, "INCONCLUSIVE",
                             "commission C5: a desk at address Q is Q's "
                             "full cell, never a flat per-desk file",
                             "instruction payload unreadable: %s" % exc)
                        continue
                    payload = result["files"].get("instruction.md")
                    if payload is None:
                        item("AR-BUNDLE-%s" % letter, "FAIL",
                             "commission C5: a desk at address Q is Q's "
                             "full cell, never a flat per-desk file",
                             "the instruction block carries no "
                             "instruction.md payload")
                        continue
                    report = grammar.verify_bundle(
                        payload.decode("utf-8"),
                        cell_address=entry.get("address", ""),
                        seated_letter=letter)
                    if report["status"] == "absent":
                        item("AR-BUNDLE-%s" % letter, "INCONCLUSIVE",
                             "commission lens 3: missing/empty/404 must "
                             "never read valid",
                             "instruction payload is absent/empty")
                    elif report["status"] == "fail":
                        bad = [it["id"] for it in report["items"]
                               if it["verdict"] == "FAIL"]
                        item("AR-BUNDLE-%s" % letter, "FAIL",
                             "commission C5/C6: one grammar seated at "
                             "addresses; the seal + first-person seat + "
                             "boundary are first-class content",
                             "the bundle for desk %s fails: %s"
                             % (letter, ", ".join(bad)))
                    else:
                        item("AR-BUNDLE-%s" % letter, "PASS",
                             "commission C5: \"the bundle at address Q is "
                             "Q's full cell with centre S·within·Q, never "
                             "a flat 'Q file'\"",
                             "the instruction payload is the desk's "
                             "full-cell bundle (seal, seat, 4+1, boundary, "
                             "hand-off, invitation, lawful §3.6 surface)")

    status = "fail" if problems else ("inconclusive" if unknowns else "ok")
    return {"status": status, "items": items}


def diff_arrangements(a, b):
    """The mechanical diff of two arrangements (K5): every desk slot and
    pin is compared by its id@version reference — one personality can be
    shown better than another with no hot edit."""
    changed = []
    for letter in grammar.COURSE:
        ea = a["desks"].get(letter, {})
        eb = b["desks"].get(letter, {})
        for slot in ("address", "runtime", "instruction", "skills",
                     "tool_surface", "model", "model_route", "tars"):
            va, vb = ea.get(slot), eb.get(slot)
            if va != vb:
                changed.append(
                    {"desk": letter, "slot": slot, "a": va, "b": vb})
    for key in _PIN_KEYS:
        if a["runtime_pins"].get(key) != b["runtime_pins"].get(key):
            changed.append({"desk": "*", "slot": "pin:%s" % key,
                            "a": a["runtime_pins"].get(key),
                            "b": b["runtime_pins"].get(key)})
    return {"identical": not changed, "changed": changed}
