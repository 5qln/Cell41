# EVIDENCE — R01 · B0 — the ledger and the record · author dsh · verifier Hermes (herdr)

*Written by `deliverable-audit` (the verifier side), by **running** the authored artifact. This file is the only place where "it works" may be said, and only next to the command that proved it. "Looks correct" is not a verdict here.*

## Environment

- when: `2026-08-27T14:29:36Z` · harness `deliverable-audit 1.0.0`
- host: `918576e4db0d68` · Linux-6.12.91-fly-x86_64-with-glibc2.41 · python `3.13.5`
- artifact under test: `/opt/data/profiles/herdr/rounds/R01-B0/authored/fractal_ledger.py`
- artifact sha256: `b291e65967e0d1f98205a9bd612507fa788ea4f9aa99e5d6b8fa5f366895546d`
- criteria spec: `/opt/data/tools/deliverable-audit/specs/b0-ledger-r01.json`
- scratch (ledgers written during the run): `/tmp/deliverable-audit-pzazrbnc`
- criteria quoted from: docs/fractal-herdr/PRD.md §9 B0, canon sha256 71ce2645078dd48f56fb7c2a8d916a1ffa70cb0db2bd74648093c8add8b1d99c (commit e50eb25) — quoted verbatim below; commission /home/deploy/the-cell/rounds/R01-B0/commission.md sha256 bd0a3871ea4cd51ed2fbd4e3873add5a797d384e6a6de8f785c4949bc74a0344
- total runtime: **21.90 s**  ✅ under the 60 s T0 bar

## Per-criterion result (§9 as written)

| ID | Criterion (verbatim) | Command | Raw output (decisive lines) | Verdict |
|---|---|---|---|---|
| C1 | 10 000 synthetic records verify from GENESIS in < 2 s | `append 10000 records, then verify() the file from GENESIS` | verify returned 10000/10000 records in 0.28s (bar 2.0s); writing the same 10000 records took 21.06s | **PASS** |
| C2 | a single flipped byte is detected and halts the loader | `append 50 records, verify (baseline), flip one byte mid-file, verify again` | baseline verify: 50/50 records valid before tampering; then verify halted: LedgerVerificationError: record 26: line is not JSON (Expecting value: line 1 column 34 (char 33)) | **PASS** |
| C3 | kill -9 mid-append leaves a valid chain (last partial line discarded) | `append 3 records, append a torn line with no newline, verify` | verify returned 3 records; 3 complete records were written before the torn line | **PASS** |
| C4 | a restore from backup reproduces the same chain hash | `append 50 records, verify, copy to backup, delete, restore, verify` | head before restore c873fad6857efc5b…, after restore c873fad6857efc5b…, records 50 → 50 | **PASS** |

## Claimed capabilities (asserted by the author, measured here)

| ID | Criterion (verbatim) | Command | Raw output (decisive lines) | Verdict |
|---|---|---|---|---|
| K1 | Build: … the record schema as a validator (PRD §9 B0 build list) | `append {"total": "garbage", "not_a_gate": true}` | rejected at append: RecordValidationError: caller record is missing required field(s): address, attestation_ref, axis, axis_verdict, block_version, corruption, gate, mark, payload_ref, state, tentative, | **PASS** |
| K2 | Build: … the append-only writer (single-writer lock, fsync) | `hold flock(LOCK_EX) in this process, then append from a second process` | second writer was excluded while the lock was held | **PASS** |

`INCONCLUSIVE` is a legitimate verdict. A blind tool must never report clean.

## Six-lens pass

| Lens | Applied how | Result |
|---|---|---|
| L1 Criterion match — does the test measure the criterion *as written*? | C1: author's timed span around `verify_seconds` does include `verify` | **PASS** |
| L2 Invariant end-to-end — across records/runs, not per call | 200 records appended across one run: 1 carry prev=GENESIS (exactly 1 is lawful), 0 links do not point at the previous record | **PASS** |
| L3 Absence vs validity — empty/404/missing must never read valid | missing: 0 records (correctly not valid content); empty: 0 records (correctly not valid content); newline-only: 0 records (correctly not valid content); empty-hash guard: sha256 of empty input reports EMPTY, never e3b0c442… as content | **PASS** |
| L4 Encoding — `∞0′ → ‖` through every string field | 2 records verified after the stress record; stress text present on disk: True | **PASS** |
| L5 Cold restart — a *new* process rebuilds state from disk alone | 3 separate processes appended 3 records; 1 record(s) carry prev=GENESIS (exactly 1 is lawful); links intact across process boundaries: True | **PASS** |
| L6 Blind tool — unavailable/rate-limited reports INCONCLUSIVE, never clean | harness arithmetic: an INCONCLUSIVE never rounds up to PASS (True); INCONCLUSIVE results in this run: none | **PASS** |

- **L1** — AST of the author's own suite (/opt/data/profiles/herdr/rounds/R01-B0/authored/selftest.py) + the spec's declared measurement dimension. No prose was read.

- **L2** — The chain is a chain: one GENESIS, every later record pointing at its predecessor.

- **L5** — Each new process rebuilt the tail from disk and linked to it.

- **L6** — Requirements declared per probe (`requires`) are checked with shutil.which before the probe runs.

## Timings (T0 mechanical)

| Step | Seconds |
|---|---|
| C1 verify 10 000 records from GENESIS under 2 s | 21.44 |
| C2 one flipped byte halts the loader | 0.03 |
| C3 torn tail discarded, chain still valid | 0.00 |
| C4 restore reproduces the chain head | 0.03 |
| K1 the promised schema validator rejects a malformed record | 0.00 |
| K2 a second writer is excluded while the lock is held | 0.05 |
| L1 Criterion match — does the test measure the criterion *as written*? | 0.01 |
| L2 Invariant end-to-end — across records/runs, not per call | 0.21 |
| L3 Absence vs validity — empty/404/missing must never read valid | 0.00 |
| L4 Encoding — `∞0′ → ‖` through every string field | 0.00 |
| L5 Cold restart — a *new* process rebuilds state from disk alone | 0.12 |
| L6 Blind tool — unavailable/rate-limited reports INCONCLUSIVE, never clean | 0.00 |
| **total** | **21.90** |

## Verdict

**PASS** — PASS 12

A FAIL is not a rewrite request: it is one correction, surgical, with the exact command, the raw output and the bytes that differ.
