#!/usr/bin/env python3
"""block — the block model (PRD §5.8 + REQUIREMENTS L1; criterion C1).

    "`block.json` = `{id, version, kind: instruction|skill|tool|model|surface,
    sha256, authored_by_run: <address+run ref>, attested_by: <attestation
    record_id>, frozen: true}`"
    "Write-once is enforced, not documented: a build step sets the directory
    read-only and the conformance test (T-L1-01) attempts an in-place edit
    and requires refusal + a recorded rejection."
    "A new version is a new block, never an edit of the old one."

Layout: ``<root>/blocks/<block-id>/<version>/block.json`` +
``payload/<relpath>``, one directory per version.  Write-once is enforced
three ways, in this order:

  1. ``author`` refuses a version directory that already exists — a new
     version is a new block (BlockFrozenError + a recorded rejection);
  2. the authored directory is frozen: files 0444, directory 0555 — an
     in-place edit is refused by the operating system too;
  3. ``attempt_edit`` is the module's edit path: it always refuses
     (BlockFrozenError) and appends a rejection record to
     ``<root>/rejections.jsonl`` — the refusal is recorded, never silent.

Content addressing: ``block.json.sha256`` is the sha256 of the canonical
JSON of ``{"files": {relpath: {"sha256": <hex>, "len": <bytes>}}}`` over
the sorted relpath map — so the digest is independent of write order and
never the sha256 of an empty string (sha256("") =
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 is the
absence trap; an empty payload is refused at author time and reads
``tampered`` if it ever appears).

Deterministic, stdlib-only: no wall clock, no network, no subprocess, no
LLM.  ``attested_by`` is null in this round — nothing here is attested
(prohibition §6), and the honest value is recorded, never invented.
"""

from __future__ import annotations

import hashlib
import json
import os
import re

__all__ = [
    "BLOCK_KINDS",
    "canonical_json",
    "payload_digest",
    "BlockError",
    "BlockValidationError",
    "BlockFrozenError",
    "BlockNotFoundError",
    "BlockTamperedError",
    "BlockStore",
    "author_block",
    "read_block",
    "verify_block",
    "attempt_edit",
]

BLOCK_KINDS = ("instruction", "skill", "tool", "model", "surface")

_BLOCK_FIELDS = frozenset((
    "id", "version", "kind", "sha256", "authored_by_run", "attested_by",
    "frozen",
))
_ID_RE = re.compile(r"\A[a-z0-9][a-z0-9._-]*\Z")


def canonical_json(obj):
    """The one canonical JSON form for everything this module writes or
    hashes: sorted keys, compact separators, UTF-8 passthrough (the bytes
    "∞0′ → ‖" stay raw), no NaN/Infinity."""
    return json.dumps(
        obj, ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False)


def payload_digest(files):
    """sha256 over the canonical JSON of the sorted
    ``{relpath: {sha256, len}}`` map — the block's content address."""
    mapping = {
        relpath: {
            "sha256": hashlib.sha256(blob).hexdigest(),
            "len": len(blob),
        }
        for relpath, blob in files.items()
    }
    return hashlib.sha256(
        canonical_json({"files": mapping}).encode("utf-8")).hexdigest()


class BlockError(Exception):
    """Base class for block-store errors."""


class BlockValidationError(BlockError, ValueError):
    """The authored input violates the block shape and was refused before
    any byte was written."""


class BlockFrozenError(BlockError):
    """A write was attempted against an existing block.  Write-once: a new
    version is a new block, never an edit of the old one."""


class BlockNotFoundError(BlockError):
    """No such block exists — absence, never a valid block."""


class BlockTamperedError(BlockError):
    """The block's payload no longer hashes to its declared sha256."""


def _check_id(value, what):
    if type(value) is not str or _ID_RE.fullmatch(value) is None:
        raise BlockValidationError(
            "%s %r violates the handle grammar [a-z0-9][a-z0-9._-]*"
            % (what, value))


def _check_relpath(relpath):
    if type(relpath) is not str or not relpath:
        raise BlockValidationError("payload relpath must be a non-empty string")
    if relpath.startswith("/") or "\\" in relpath:
        raise BlockValidationError("payload relpath %r is not relative" % relpath)
    norm = os.path.normpath(relpath)
    if norm != relpath or relpath == ".." or relpath.startswith("../"):
        raise BlockValidationError("payload relpath %r escapes the payload dir"
                                   % relpath)


def _check_files(files):
    if type(files) is not dict or not files:
        raise BlockValidationError(
            "a block carries at least one payload file — an empty block is "
            "refused, never authored")
    checked = {}
    for relpath, content in sorted(files.items()):
        _check_relpath(relpath)
        if isinstance(content, str):
            content = content.encode("utf-8")
        if not isinstance(content, (bytes, bytearray)) or len(content) == 0:
            raise BlockValidationError(
                "payload file %r is empty — an empty payload never reads "
                "valid (sha256 of empty is e3b0c44298fc…)" % relpath)
        checked[relpath] = bytes(content)
    return checked


class BlockStore:
    """A block store rooted at ``root`` (a parameter — never a live path)."""

    def __init__(self, root):
        self.root = root
        self.blocks_dir = os.path.join(root, "blocks")
        self.rejections_path = os.path.join(root, "rejections.jsonl")

    def block_dir(self, block_id, version):
        return os.path.join(self.blocks_dir, block_id, version)

    def exists(self, block_id, version):
        return os.path.isdir(self.block_dir(block_id, version))

    # -- authoring ---------------------------------------------------------

    def author(self, block_id, version, kind, files,
               authored_by_run, attested_by=None):
        """Author one block.  Refuses an existing version directory
        (write-once) and records the refusal; writes the payload, the
        seven-field block.json, then freezes the directory."""
        _check_id(block_id, "block id")
        _check_id(version, "version")
        if kind not in BLOCK_KINDS:
            raise BlockValidationError(
                "kind %r is not one of instruction|skill|tool|model|surface"
                % (kind,))
        if type(authored_by_run) is not str or not authored_by_run:
            raise BlockValidationError(
                "authored_by_run must be a non-empty <address+run ref> string")
        if attested_by is not None and type(attested_by) is not str:
            raise BlockValidationError(
                "attested_by must be an attestation record_id string or null")
        checked = _check_files(files)

        block_dir = self.block_dir(block_id, version)
        if os.path.isdir(block_dir):
            self.record_rejection(
                "%s@%s" % (block_id, version), "re-author",
                "write-once (C1, L1): a new version is a new block, never "
                "an edit of the old one")
            raise BlockFrozenError(
                "block %s@%s already exists — a new version is a new block, "
                "never an edit of the old one" % (block_id, version))

        record = {
            "id": block_id,
            "version": version,
            "kind": kind,
            "sha256": payload_digest(checked),
            "authored_by_run": authored_by_run,
            "attested_by": attested_by,
            "frozen": True,
        }
        payload_dir = os.path.join(block_dir, "payload")
        os.makedirs(payload_dir, exist_ok=False)
        try:
            for relpath, content in sorted(checked.items()):
                path = os.path.join(payload_dir, relpath)
                parent = os.path.dirname(path)
                if parent != payload_dir:
                    os.makedirs(parent, exist_ok=True)
                with open(path, "wb") as handle:
                    handle.write(content)
                os.chmod(path, 0o444)
            with open(os.path.join(block_dir, "block.json"), "w",
                      encoding="utf-8") as handle:
                handle.write(canonical_json(record) + "\n")
            os.chmod(os.path.join(block_dir, "block.json"), 0o444)
        except Exception:
            # never leave a half-authored block behind
            for dirpath, dirnames, filenames in os.walk(block_dir, topdown=False):
                for name in filenames:
                    try:
                        os.chmod(os.path.join(dirpath, name), 0o644)
                    except OSError:
                        pass
                try:
                    os.rmdir(dirpath)
                except OSError:
                    pass
            raise
        # the build step sets the directory read-only — enforced, not
        # documented (C1)
        os.chmod(block_dir, 0o555)
        return record

    # -- reading -----------------------------------------------------------

    def read(self, block_id, version):
        """Read a block back: the seven-field record plus the payload bytes,
        with the digest recomputed from disk.  Absence raises; an altered
        payload raises BlockTamperedError; a bad block.json shape raises
        BlockValidationError."""
        block_dir = self.block_dir(block_id, version)
        record_path = os.path.join(block_dir, "block.json")
        try:
            with open(record_path, "r", encoding="utf-8") as handle:
                raw = handle.read()
        except FileNotFoundError:
            raise BlockNotFoundError(
                "block %s@%s does not exist — absence, never a valid block"
                % (block_id, version)) from None
        try:
            record = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise BlockValidationError(
                "block %s@%s block.json is not JSON (%s)"
                % (block_id, version, exc)) from None
        if type(record) is not dict or set(record.keys()) != _BLOCK_FIELDS:
            raise BlockValidationError(
                "block %s@%s block.json does not carry exactly the fields "
                "{id, version, kind, sha256, authored_by_run, attested_by, "
                "frozen}" % (block_id, version))
        if record["id"] != block_id or record["version"] != version:
            raise BlockValidationError(
                "block %s@%s block.json names %s@%s"
                % (block_id, version, record["id"], record["version"]))
        if record["kind"] not in BLOCK_KINDS:
            raise BlockValidationError(
                "block %s@%s kind %r is not one of the five kinds"
                % (block_id, version, record["kind"]))
        if record["frozen"] is not True:
            raise BlockValidationError(
                "block %s@%s frozen is not true — an unfrozen block reads "
                "invalid" % (block_id, version))

        payload_dir = os.path.join(block_dir, "payload")
        try:
            names = os.listdir(payload_dir)
        except FileNotFoundError:
            raise BlockTamperedError(
                "block %s@%s has no payload/ directory — absence, never "
                "valid" % (block_id, version)) from None
        files = {}
        for relpath in sorted(names):
            path = os.path.join(payload_dir, relpath)
            if not os.path.isfile(path):
                continue
            with open(path, "rb") as handle:
                files[relpath] = handle.read()
        if not files:
            raise BlockTamperedError(
                "block %s@%s holds no payload files — empty, never valid"
                % (block_id, version))
        actual = payload_digest(files)
        if actual != record["sha256"]:
            raise BlockTamperedError(
                "block %s@%s payload sha256 %s does not match the declared "
                "%s — the block was altered in place"
                % (block_id, version, actual, record["sha256"]))
        return {"record": record, "files": files}

    def verify(self, block_id, version):
        """A status report instead of an exception: ok | absent | tampered
        | invalid.  Anything unobservable reads its own status, never ok."""
        try:
            result = self.read(block_id, version)
        except BlockNotFoundError as exc:
            return {"status": "absent", "ref": "%s@%s" % (block_id, version),
                    "reason": str(exc)}
        except BlockTamperedError as exc:
            return {"status": "tampered", "ref": "%s@%s" % (block_id, version),
                    "reason": str(exc)}
        except BlockValidationError as exc:
            return {"status": "invalid", "ref": "%s@%s" % (block_id, version),
                    "reason": str(exc)}
        except OSError as exc:
            # unreadable is unobservable — never a guessed ok (lens 3/6)
            return {"status": "invalid", "ref": "%s@%s" % (block_id, version),
                    "reason": "unreadable block: %s" % exc}
        record = result["record"]
        return {"status": "ok",
                "ref": "%s@%s" % (block_id, version),
                "kind": record["kind"],
                "sha256": record["sha256"],
                "bytes": sum(len(blob) for blob in result["files"].values()),
                "record": record}

    # -- the edit path: always refused, always recorded --------------------

    def attempt_edit(self, block_id, version, relpath, content):
        """The module's in-place edit path.  For an existing block it always
        raises BlockFrozenError and records the rejection (C1 / T-L1-01);
        for an absent block it raises BlockNotFoundError (nothing to edit)."""
        if not self.exists(block_id, version):
            raise BlockNotFoundError(
                "block %s@%s does not exist — there is nothing to edit"
                % (block_id, version))
        target = "%s@%s/%s" % (block_id, version, relpath)
        self.record_rejection(
            target, "in-place edit",
            "write-once (C1, L1): the block is frozen; a new version is a "
            "new block, never an edit of the old one")
        raise BlockFrozenError(
            "refusing the in-place edit of %s: the block is frozen — a new "
            "version is a new block, never an edit of the old one" % target)

    def record_rejection(self, target, attempt, reason):
        """Append one rejection record to <root>/rejections.jsonl.  The seq
        is the count of recorded rejections plus one — deterministic, no
        wall clock, no ts field (no wall-clock in logic, K1)."""
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
        """The recorded rejections, in order (the written record, read back)."""
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


def author_block(store, block_id, version, kind, files,
                 authored_by_run, attested_by=None):
    return store.author(block_id, version, kind, files,
                        authored_by_run, attested_by)


def read_block(store, block_id, version):
    return store.read(block_id, version)


def verify_block(store, block_id, version):
    return store.verify(block_id, version)


def attempt_edit(store, block_id, version, relpath, content):
    return store.attempt_edit(block_id, version, relpath, content)
