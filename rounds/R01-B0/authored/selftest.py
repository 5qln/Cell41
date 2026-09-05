#!/usr/bin/env python3
"""selftest — dsh's own tests for fractal_ledger (R01 · B0).

Run:  python3 selftest.py        (Python 3.12+, stdlib only)

House rules honoured here:

  * Every test names the criterion ID it exercises (C1, C2, C3, C4, K1, K2)
    and the quantity it measures.
  * A test that times an operation names the operation it timed.  C1 times
    VERIFICATION of 10 000 records from GENESIS — never the writing.
  * Tail recovery is exercised at the 0-record, 1-record and n-record
    boundaries in FRESH processes (subprocess), reading from disk alone —
    never from in-process state.  The 1-record boundary is the defect that
    killed the previous B0 attempt.
  * The encoding lens pushes the bytes "\u221e0\u2032 \u2192 \u2016" ("∞0′ → ‖")
    through every §5.1 string field, written, read back and verified.
  * Every ledger path in every test is a tempfile-created directory.
    Nothing is written anywhere except those temp dirs (and the module
    file, which is only read).
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

import fractal_ledger as fl

MODULE_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "fractal_ledger.py")

# The encoding lens bytes:  "∞0′ → ‖"
ENCODING = "\u221e0\u2032 \u2192 \u2016"

FRESH_TIMEOUT = 120


def fresh(*args):
    """Run the module CLI in a FRESH python process (cold start).  The
    subprocess reads the ledger from disk alone; it never receives state
    from this process."""
    return subprocess.run(
        [sys.executable, MODULE_FILE] + [str(arg) for arg in args],
        capture_output=True, text=True, timeout=FRESH_TIMEOUT)


def fresh_tail(ledger):
    """Tail record id read by a fresh process from disk alone."""
    proc = fresh("tail", "--ledger", ledger)
    assert proc.returncode == 0, proc.stderr
    return proc.stdout.strip()


def fresh_verify(ledger):
    """(head, count) verified by a fresh process from disk alone."""
    proc = fresh("verify", "--ledger", ledger)
    assert proc.returncode == 0, proc.stderr
    tokens = proc.stdout.strip().split()
    head = tokens[0].split("=", 1)[1]
    count = int(tokens[1].split("=", 1)[1])
    return head, count


def _torn_fragment(ledger, index=-2):
    """A genuine torn partial line, as kill -9 mid-append would leave it:
    a true byte prefix of a complete record line, no trailing newline.
    index selects which complete line the prefix is cut from (-2 = the
    last complete line of a newline-terminated file)."""
    with open(ledger, "rb") as handle:
        raw = handle.read()
    line = raw.split(b"\n")[index]
    fragment = line[:40]
    try:
        json.loads(fragment.decode("utf-8"))
    except ValueError:
        pass
    else:
        raise AssertionError(
            "test helper: the torn fragment must be unparseable JSON")
    return fragment


def test_C1_verification_of_10000_records_from_GENESIS_under_2s():
    """C1 — quantity measured: wall time of VERIFICATION of 10 000 records
    from GENESIS, in seconds; the timed operation is LedgerVerifier.verify
    and writing is never timed."""
    with tempfile.TemporaryDirectory(prefix="b0-c1-") as tmp:
        ledger = os.path.join(tmp, "state", "gates.jsonl")
        # Build the 10 000-record chain.  This writing is NOT timed and no
        # assertion is made about its duration (commission H-1).
        with fl.LedgerWriter(ledger) as writer:
            for i in range(10000):
                writer.append(fl.make_record(
                    address="S" * (i % 5), payload_ref="payload-%05d" % i))
        head_after_build = fl.tail_record_id(ledger)
        # The timed operation: VERIFICATION of 10 000 records from GENESIS.
        start = time.perf_counter()
        result = fl.LedgerVerifier(ledger).verify()
        verify_seconds = time.perf_counter() - start
        assert result.count == 10000
        assert result.head == head_after_build and result.head != fl.GENESIS
        assert verify_seconds < 2.0, (
            "C1: VERIFICATION of 10 000 records from GENESIS took %.3f s — "
            "must be < 2 s (timed operation: LedgerVerifier.verify; the "
            "writing above was never timed)" % verify_seconds)
        # Untimed cold-restart cross-check of the same ledger: a fresh
        # process verifies the same chain from disk alone.
        head_fresh, count_fresh = fresh_verify(ledger)
        assert count_fresh == 10000 and head_fresh == head_after_build


def test_C2_single_flipped_byte_halts_the_loader():
    """C2 — quantity measured: whether a single flipped byte raises
    LedgerVerificationError from the loader and makes CLI verify exit 4,
    against a chain that verified clean before the flip."""
    with tempfile.TemporaryDirectory(prefix="b0-c2-") as tmp:
        ledger = os.path.join(tmp, "state", "gates.jsonl")
        with fl.LedgerWriter(ledger) as writer:
            for i in range(5):
                writer.append(fl.make_record(payload_ref="payload-%d" % i))
        # Precondition: the chain verifies clean BEFORE the flip.
        before = fl.LedgerVerifier(ledger).verify()
        assert before.count == 5
        with open(ledger, "rb") as handle:
            raw = bytearray(handle.read())
        position = bytes(raw).find(b"payload-1")
        assert position > 0, "C2: expected a marker byte position in record 2"
        raw[position + 4] ^= 0x01  # flip exactly one byte inside record 2
        with open(ledger, "wb") as handle:
            handle.write(bytes(raw))
        try:
            fl.LedgerLoader(ledger).load()
        except fl.LedgerVerificationError:
            halted = True
        else:
            halted = False
        assert halted, "C2: a single flipped byte must halt the loader"
        proc = fresh("verify", "--ledger", ledger)
        assert proc.returncode == 4, (
            "C2: CLI verify must exit 4 on the flipped byte, got %d"
            % proc.returncode)


def test_C3_mid_append_truncation_discards_the_partial_line():
    """C3 — quantity measured: the number of complete records that remain
    valid after a torn mid-append (a partial last line, as kill -9 would
    leave) — must equal the records written (more than one) — and that the
    next append chains onto the last complete record, never the fragment."""
    with tempfile.TemporaryDirectory(prefix="b0-c3-") as tmp:
        ledger = os.path.join(tmp, "state", "gates.jsonl")
        with fl.LedgerWriter(ledger) as writer:
            for i in range(5):
                writer.append(fl.make_record(
                    address="S" * (i % 3), payload_ref="rec-%d" % i))
        head5 = fl.tail_record_id(ledger)
        # A torn append of the would-be record 6: a true byte prefix of its
        # line, no trailing newline — exactly what kill -9 mid-append leaves.
        with open(ledger, "ab") as handle:
            handle.write(_torn_fragment(ledger))
        # A fresh process reads disk alone: all 5 complete records remain
        # valid and the partial line is discarded.
        head, count = fresh_verify(ledger)
        assert count == 5, "C3: 5 complete records must remain valid"
        assert head == head5
        assert count > 1, "C3: the truncation case must keep more than one record"
        # A fresh process appends the next record: it must chain onto the
        # last complete record, never onto the fragment, never GENESIS.
        next_record = json.dumps(fl.make_record(address="SGQPV", payload_ref="rec-5"))
        proc = fresh("append", "--ledger", ledger, "--record", next_record)
        assert proc.returncode == 0, proc.stderr
        head6, count6 = fresh_verify(ledger)
        assert count6 == 6
        with open(ledger, "rb") as handle:
            record6 = json.loads(handle.read().decode("utf-8").split("\n")[-2])
        assert record6["prev_hash"] == head5, (
            "C3: the append after a torn tail must chain onto the last "
            "complete record — never GENESIS, never the fragment")
        assert head6 == record6["record_id"]


def test_C4_restore_from_backup_reproduces_the_same_chain_head():
    """C4 — quantity measured: equality of the chain head hash (the last
    record's record_id) before and after a restore from a backup copy."""
    with tempfile.TemporaryDirectory(prefix="b0-c4-") as tmp:
        ledger = os.path.join(tmp, "state", "gates.jsonl")
        backup = os.path.join(tmp, "backup", "gates.jsonl")
        with fl.LedgerWriter(ledger) as writer:
            for i in range(8):
                writer.append(fl.make_record(payload_ref="base-%d" % i))
        head_before, count_before = fresh_verify(ledger)
        assert count_before == 8
        os.makedirs(os.path.dirname(backup), exist_ok=True)
        shutil.copyfile(ledger, backup)
        # The live chain moves on past the backup point...
        with fl.LedgerWriter(ledger) as writer:
            for i in range(3):
                writer.append(fl.make_record(payload_ref="extra-%d" % i))
        head_extended, count_extended = fresh_verify(ledger)
        assert count_extended == 11 and head_extended != head_before
        # ...and the restore brings it back to the backed-up state.
        shutil.copyfile(backup, ledger)
        head_after, count_after = fresh_verify(ledger)
        assert head_after == head_before, (
            "C4: restore from backup must reproduce the same chain head hash")
        assert count_after == count_before == 8


def test_K1_violating_records_are_rejected_at_append_never_chained():
    """K1 — quantity measured: every §5.1-violating record is rejected at
    append (RecordValidationError; CLI exit 3) and the number of records
    the ledger gained from all the rejected appends — must be zero."""
    with tempfile.TemporaryDirectory(prefix="b0-k1-") as tmp:
        ledger = os.path.join(tmp, "state", "gates.jsonl")
        good = fl.make_record(payload_ref="good")
        violations = [
            ("absent schema (the previous attempt's garbage)",
             {"total": "garbage"}),
            ("missing field (absence)", {k: v for k, v in good.items()
                                         if k != "mark"}),
            ("unknown extra field", {**good, "extra": 1}),
            ("invalid enum: gate", {**good, "gate": "q"}),
            ("invalid regex: address", {**good, "address": "S" + ENCODING}),
            ("invalid enum: state", {**good, "state": "attested-typo"}),
            ("non-string mark", {**good, "mark": 1}),
            ("invalid corruption level", {**good, "corruption": "L5"}),
            ("axis_verdict null without a fresh anchor",
             {**good, "axis": {"field": {"mode": "inherited", "anchor": "a"},
                               "delta": []}, "axis_verdict": None}),
            ("malformed axis", {**good, "axis": {"nope": {}}}),
            ("non-bool tentative", {**good, "tentative": 1}),
            ("non-string payload_ref", {**good, "payload_ref": 7}),
            ("writer-owned field supplied by a caller",
             {**good, "record_id": "0" * 64}),
        ]
        with fl.LedgerWriter(ledger) as writer:
            for label, record in violations:
                try:
                    writer.append(record)
                except fl.RecordValidationError:
                    pass
                else:
                    raise AssertionError("K1: %s was accepted" % label)
        result = fl.LedgerVerifier(ledger).verify()
        assert result.count == 0 and result.head == fl.GENESIS, (
            "K1: rejected records must never be chained (count must stay 0)")
        # The CLI also rejects a violating append with exit code 3.
        proc = fresh("append", "--ledger", ledger, "--record",
                     json.dumps({"total": "garbage"}))
        assert proc.returncode == 3, (
            "K1: CLI append must exit 3 on a violating record, got %d"
            % proc.returncode)
        # The ledger is untouched: the first VALID record still chains from
        # GENESIS as record 1.
        with fl.LedgerWriter(ledger) as writer:
            first = writer.append(good)
        assert first["prev_hash"] == fl.GENESIS
        assert fl.LedgerVerifier(ledger).verify().count == 1


def test_K2_second_writer_is_excluded_exits_nonzero_records_nothing():
    """K2 — quantity measured: the exit code of a second writer (must be
    non-zero: 2) and the number of records it added to the ledger (must be
    zero) while the first writer holds the single-writer lock."""
    with tempfile.TemporaryDirectory(prefix="b0-k2-") as tmp:
        ledger = os.path.join(tmp, "state", "gates.jsonl")
        first = fl.LedgerWriter(ledger)
        try:
            first.append(fl.make_record(payload_ref="one"))
            first.append(fl.make_record(payload_ref="two"))
            # In-process: a second writer on the same ledger is excluded.
            try:
                fl.LedgerWriter(ledger)
            except fl.LedgerLockedError:
                pass
            else:
                raise AssertionError(
                    "K2: a second writer must be excluded in-process")
            # Fresh process: the CLI append must exit non-zero (2) and
            # record nothing while the lock is held.
            intruder = json.dumps(fl.make_record(payload_ref="intruder"))
            proc = fresh("append", "--ledger", ledger, "--record", intruder)
            assert proc.returncode == 2, (
                "K2: the second writer must exit non-zero (2), got %d"
                % proc.returncode)
            head, count = fresh_verify(ledger)
            assert count == 2, "K2: the second writer must record nothing"
            assert head == fl.tail_record_id(ledger)
        finally:
            first.close()
        # Once the first writer releases, a new writer may take over.
        with fl.LedgerWriter(ledger) as writer:
            writer.append(fl.make_record(payload_ref="three"))
        assert fl.LedgerVerifier(ledger).verify().count == 3


def test_T0_tail_recovery_zero_records_in_a_fresh_process():
    """Tail-recovery boundary 0 (commission §3, the previous B0 defect's
    family) — quantity measured: the tail record id (must be GENESIS) and
    the verify count (must be 0) read by FRESH processes from disk alone,
    for an absent file and for an empty file."""
    with tempfile.TemporaryDirectory(prefix="b0-t0-") as tmp:
        ledger = os.path.join(tmp, "state", "gates.jsonl")
        # Absent file.
        assert fresh_tail(ledger) == fl.GENESIS
        head, count = fresh_verify(ledger)
        assert count == 0 and head == fl.GENESIS
        # Empty file.
        os.makedirs(os.path.dirname(ledger), exist_ok=True)
        with open(ledger, "wb"):
            pass
        assert fresh_tail(ledger) == fl.GENESIS
        head, count = fresh_verify(ledger)
        assert count == 0 and head == fl.GENESIS


def test_T1_tail_recovery_one_record_in_a_fresh_process():
    """Tail-recovery boundary 1 (the exact defect that killed the previous
    B0 attempt) — quantity measured: the tail record id and the verify
    count read by FRESH processes from a ledger holding exactly one record
    — with and without a trailing newline — and the prev_hash of a fresh
    append, which must chain onto that sole record from disk alone."""
    with tempfile.TemporaryDirectory(prefix="b0-t1-") as tmp:
        ledger = os.path.join(tmp, "state", "gates.jsonl")
        with fl.LedgerWriter(ledger) as writer:
            only = writer.append(fl.make_record(address="S", payload_ref="sole"))
        # 1 record, trailing newline present.
        assert fresh_tail(ledger) == only["record_id"]
        head, count = fresh_verify(ledger)
        assert count == 1 and head == only["record_id"]
        # 1 record, trailing newline lost (kill -9 after the record bytes,
        # before the newline).  A complete line without the newline still
        # counts as the tail.
        with open(ledger, "rb") as handle:
            raw = handle.read()
        assert raw.endswith(b"\n")
        with open(ledger, "wb") as handle:
            handle.write(raw[:-1])
        assert fresh_tail(ledger) == only["record_id"]
        head, count = fresh_verify(ledger)
        assert count == 1 and head == only["record_id"]
        # The first restart after the very first record: a FRESH process
        # appends and must chain onto the sole record, never GENESIS.
        second = json.dumps(fl.make_record(address="SG", payload_ref="second"))
        proc = fresh("append", "--ledger", ledger, "--record", second)
        assert proc.returncode == 0, proc.stderr
        head, count = fresh_verify(ledger)
        assert count == 2
        with open(ledger, "rb") as handle:
            record2 = json.loads(handle.read().decode("utf-8").split("\n")[-2])
        assert record2["prev_hash"] == only["record_id"], (
            "T1: the fresh append must chain onto the sole record — never a "
            "silent GENESIS fall-back")
        assert head == record2["record_id"]
        # A torn FIRST append (fragment only, no complete record): fresh
        # processes see 0 records, and the next fresh append becomes record
        # 1 chaining from GENESIS.
        torn = os.path.join(tmp, "torn.jsonl")
        with open(torn, "wb") as handle:
            handle.write(_torn_fragment(ledger, index=-3))
        head, count = fresh_verify(torn)
        assert count == 0 and head == fl.GENESIS
        proc = fresh("append", "--ledger", torn, "--record",
                     json.dumps(fl.make_record(payload_ref="after-torn-first")))
        assert proc.returncode == 0, proc.stderr
        head, count = fresh_verify(torn)
        assert count == 1 and head == proc.stdout.strip()
        with open(torn, "rb") as handle:
            first_real = json.loads(handle.read().decode("utf-8").split("\n")[-2])
        assert first_real["prev_hash"] == fl.GENESIS


def test_Tn_tail_recovery_n_records_in_a_fresh_process():
    """Tail-recovery boundary n — quantity measured: the tail record id and
    the verify count read by FRESH processes from a ledger of n=7 records,
    and the count after a torn trailing fragment is appended (must stay 7,
    with the partial line discarded)."""
    with tempfile.TemporaryDirectory(prefix="b0-tn-") as tmp:
        ledger = os.path.join(tmp, "state", "gates.jsonl")
        with fl.LedgerWriter(ledger) as writer:
            for i in range(7):
                writer.append(fl.make_record(
                    address="S" * (i % 4), payload_ref="n-%d" % i))
        # n records, newline-terminated: a fresh process reads the tail.
        head7, count = fresh_verify(ledger)
        assert count == 7
        assert fresh_tail(ledger) == head7 and head7 != fl.GENESIS
        # n records plus a torn trailing fragment: the fragment is walked
        # past and the 7 complete records remain the chain.
        with open(ledger, "ab") as handle:
            handle.write(_torn_fragment(ledger))
        head, count = fresh_verify(ledger)
        assert count == 7 and head == head7
        assert fresh_tail(ledger) == head7, (
            "Tn: the torn fragment must be walked past — never a silent "
            "GENESIS fall-back while records exist")


def test_encoding_roundtrip_through_every_string_field():
    """Encoding lens (commission §2) — quantity measured: byte-exact
    equality of the string "∞0′ → ‖" in every §5.1 string field after
    write → read back → verify in a fresh process.  The §5.1 fields whose
    rule is plain 'string' are payload_ref, block_version,
    attestation_ref, and the string refs inside axis (field.anchor, delta
    items).  The hex64 / regex / enum fields cannot carry arbitrary bytes
    by §5.1 and the validator rejects them (K1 exercises that side)."""
    with tempfile.TemporaryDirectory(prefix="b0-enc-") as tmp:
        ledger = os.path.join(tmp, "state", "gates.jsonl")
        s = ENCODING
        with fl.LedgerWriter(ledger) as writer:
            full = writer.append(fl.make_record(
                payload_ref=s, block_version=s, attestation_ref=s,
                axis={"field": {"mode": "anchored", "anchor": s},
                      "delta": [s, s]}))
        # Read back and verify from disk (a fresh process re-verifies the
        # chain, recomputing record_id from the same canonical bytes).
        head, count = fresh_verify(ledger)
        assert count == 1 and head == full["record_id"]
        with open(ledger, "rb") as handle:
            raw = handle.read()
        assert s.encode("utf-8") in raw, (
            "the encoding bytes must be on disk as raw UTF-8")
        assert b"\\u221e" not in raw, (
            "the encoding bytes must not be ASCII-escaped on disk")
        record = json.loads(raw.decode("utf-8").split("\n")[0])
        expected_axis = {"field": {"mode": "anchored", "anchor": s},
                         "delta": [s, s]}
        for field, value in (
                ("payload_ref", s), ("block_version", s),
                ("attestation_ref", s), ("axis", expected_axis)):
            assert record[field] == value, (
                "encoding round-trip mismatch in field %r" % field)
        # A second record chaining onto it proves the canonical form that
        # carried the bytes is stable across the chain boundary.
        with fl.LedgerWriter(ledger) as writer:
            writer.append(fl.make_record(payload_ref=s))
        head, count = fresh_verify(ledger)
        assert count == 2


def test_index_sidecar_deleting_it_changes_nothing():
    """Index lens (§9 build list, §5.2) — quantity measured: equality of
    chain head, record count and the rebuilt index maps before and after
    deleting the disposable sidecar (deleting it must change nothing)."""
    with tempfile.TemporaryDirectory(prefix="b0-idx-") as tmp:
        ledger = os.path.join(tmp, "state", "gates.jsonl")
        index_path = fl.default_index_path(ledger)
        with fl.LedgerWriter(ledger) as writer:
            writer.append(fl.make_record(address="S", payload_ref="a"))
            writer.append(fl.make_record(address="SGQPV", payload_ref="b"))
            writer.append(fl.make_record(address="SGQPVSGQPV", payload_ref="c"))
            writer.append(fl.make_record(
                address="S", state="held-pending", payload_ref="d"))
        first = fl.LedgerLoader(ledger).load()
        assert os.path.exists(index_path), "load must rebuild the sidecar"
        assert first.count == 4
        assert first.index["last_record_per_address"]["SGQPVSGQPV"] == \
            first.records[2]["record_id"]
        assert first.index["cycle_counts"]["SGQPVSGQPV"] == 2
        assert first.index["cycle_counts"]["SGQPV"] == 1
        assert first.index["cycle_counts"]["S"] == 0
        assert first.index["open_holds"]["S"] == first.records[3]["record_id"]
        # Delete the sidecar: replay rebuilds it and changes nothing.
        os.unlink(index_path)
        assert not os.path.exists(index_path)
        second = fl.LedgerLoader(ledger).load()
        assert second.head == first.head
        assert second.count == first.count
        assert second.records == first.records
        assert second.index == first.index, (
            "deleting the sidecar must change nothing about the replay")
        assert os.path.exists(index_path), "replay must rebuild the sidecar"
        # Cold restart: the index subcommand re-arms from disk in a fresh
        # process.
        proc = fresh("index", "--ledger", ledger)
        assert proc.returncode == 0, proc.stderr
        assert "count=4" in proc.stdout


def main():
    tests = sorted(
        (name, func) for name, func in globals().items()
        if name.startswith("test_") and callable(func))
    failures = []
    for name, func in tests:
        first_line = (func.__doc__ or "").strip().splitlines()[0]
        try:
            func()
        except Exception as exc:  # noqa: BLE001 — report every failure
            failures.append((name, exc))
            print("FAIL  %-58s %s: %s" % (name, type(exc).__name__, exc))
        else:
            print("ok    %-58s %s" % (name, first_line))
    print("-" * 100)
    print("%d tests, %d failed" % (len(tests), len(failures)))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
