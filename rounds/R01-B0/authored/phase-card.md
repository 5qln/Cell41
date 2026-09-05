# phase-card — R01 · B0 — author dsh

Predictions only, per the round's rules: this card reports no results and no
run of anything. A separate verifier executes the code and writes the only
record that counts.

## 1. Criteria restated by ID

| ID | Criterion | Judged dimension |
|---|---|---|
| **C1** | 10 000 synthetic records **verify** from GENESIS in < 2 s | time of VERIFICATION, never of writing (H-1 closed: no bar on write time) |
| **C2** | a single flipped byte is detected and **halts** the loader | detection, against a chain that was clean before the flip |
| **C3** | `kill -9` mid-append leaves a **valid chain** (last partial line discarded) | number of complete records still valid, with **more than one** record written |
| **C4** | a restore from backup reproduces the **same chain hash** | equality of the chain head before and after restore |
| **K1** | the record schema as a validator — a record that violates §5.1 is **rejected at append**, never chained | §9 B0 build list, §5.1 |
| **K2** | the append-only writer (**single-writer lock**, fsync) — a second writer is excluded; per §10.3 the second **exits non-zero, records nothing** | §9 B0 build list, §10.3 |

fsync per record is kept, unweakened (H-2).

## 2. Adapter mapping for the verifier's binding block

| binding name | module symbol in `fractal_ledger.py` |
|---|---|
| `writer_class` | `LedgerWriter` |
| `verifier_class` | `LedgerVerifier` |
| `append_method` | `LedgerWriter.append` |
| `verify_method` | `LedgerVerifier.verify` |
| `genesis_const` | `GENESIS` (the string `"GENESIS"`) |
| `id_field` | `record_id` |
| `prev_field` | `prev_hash` |

Supporting API the binding may touch: `LedgerVerifier(path).verify()` returns
a `VerifyResult` with `.records` (list of the fifteen-field dicts), `.count`
(int) and `.head` (last `record_id`, or `GENESIS` at zero records);
`LedgerWriter(path, lock_path=None, clock=None).append(record)` takes exactly
the twelve caller-supplied fields and returns the full fifteen-field record
as written; `LedgerLoader(path, index_path=None).load(write_index=True)`
returns a `LoadedLedger` with `.records`, `.head`, `.count`, `.index`,
`.index_path`; module-level `verify_ledger(path)`, `tail_record_id(path)`,
`tail_record(path)`, `RecordValidator` (`validate_full`, `validate_call`),
`make_record(...)` exist. CLI exit codes: 0 ok · 1 general ledger error ·
2 single-writer lock conflict (K2) · 3 record validation (K1) · 4 chain
verification halt (C2).

## 3. Predictions per criterion

- **C1** — verification of the 10 000-record chain completes in **< 2 s**;
  predicted ≈ **0.3 s** (range 0.15–0.6 s) on a host of this box's class.
  Basis: the commission itself records 0.15 s for the previous attempt's
  repaired chain on this host, and the module's verify is a single read pass
  — one JSON parse, one §5.1 validation and one sha256 recomputation per
  record, with no fsync and no second read.
- **C2** — the flipped byte is detected at the first record whose bytes
  changed (the record carrying the flipped byte): `LedgerLoader.load()`
  raises `LedgerVerificationError`, re-arms nothing, and the CLI exits **4**.
  Predicted every time: `record_id` is a sha256 over the record's canonical
  bytes, so any flipped byte changes the recomputed id and halts the pass.
- **C3** — with *k* complete records (*k* > 1) plus one torn partial last
  line, verification counts exactly ***k*** valid records and the head equals
  the *k*-th record's `record_id`; the partial line contributes **zero**
  records. A subsequent append chains with `prev_hash` equal to that last
  complete `record_id` — never `GENESIS`, never the fragment.
- **C4** — `head_after == head_before`: the two 64-hex strings are
  byte-identical, and the restored ledger is accepted by the chain check
  with the backed-up record count. The chain is content-addressed, so
  identical bytes reproduce the identical head.
- **K1** — every §5.1-violating shape (missing field, unknown extra field,
  bad enum, bad address, malformed axis, `axis_verdict` null without a fresh
  anchor, non-bool `tentative`, caller-supplied `record_id`, and the bare
  `{"total":"garbage"}` of the previous attempt) is rejected with
  `RecordValidationError` before any byte is written (CLI exit **3**), and
  the ledger's record count after all rejected appends is exactly unchanged:
  **0** violations chained. The first valid record afterwards still chains
  from `GENESIS`.
- **K2** — while the first writer holds the lock, the second writer gets
  `LedgerLockedError` in-process and exit code **2** as a CLI process, and
  adds exactly **0** records; once the first releases, a new writer acquires
  the lock and appends normally.

## 4. Tail-recovery boundary behaviour — 0 / 1 / n records

Always read from disk alone, never from in-process state:

- **0 records** — the ledger file is absent or empty: `tail_record()`
  returns `None`, `tail_record_id()` returns `GENESIS`, verify reports
  count 0 and head `GENESIS`; a first append writes record 1 with
  `prev_hash` = `GENESIS`.
- **1 record** — the sole record is the tail **whether or not its line ends
  with a trailing newline**: a `kill -9` can leave a complete record line
  without the newline, and that line still counts as the tail. A fresh
  process reads it from disk alone (no memory cache); a fresh append onto a
  1-record ledger chains with `prev_hash` equal to the sole record's
  `record_id` — this is the boundary that killed the previous B0 attempt. A
  torn *first* append (a fragment with no complete record) reads as 0
  records, and the next append becomes record 1 from `GENESIS`.
- **n records** — the tail is the last line that parses as a record-shaped
  JSON object carrying `record_id` and `prev_hash`. A torn trailing fragment
  (no trailing newline, unparseable) is walked past and discarded; there is
  no silent fall-back to `GENESIS` while records exist. Before each append
  the writer restores the file's final line boundary: a complete final
  record missing only its newline gets the separator back; a torn fragment
  is discarded at the last newline boundary. An append after a torn append
  therefore yields a ledger whose lines are exactly the complete records, in
  order, and the new record chains onto the last complete one.

Module revision note (one clause): `fractal_ledger.py` was revised once this
round — the append path now restores the file's final line boundary after a
torn append (completing a missing trailing newline, or discarding a torn
trailing fragment), because appending raw bytes after a torn append would
splice the new line onto the previous line and break the chain.

## 5. Holds

- **HOLD H-0:** the first run of this round had **no execution channel** —
  the sandbox blocked all execution — so nothing authored in that run could
  be executed there; what I would need is an execution channel, and the
  second run of this round received one.
- **HOLD H-V1:** I could not read the verifier harness spec at
  `/opt/data/tools/deliverable-audit/specs/b0-ledger.json` beyond what the
  commission quotes; what I would need is the spec's full binding contract
  (result-object shapes, CLI expectations, lens mechanics) to conform to
  anything beyond the seven binding names declared in §3.
- **HOLD H-V2:** the exact definition of the "encoding `∞0′ → ‖` through
  every string field" lens; what I would need is the lens's field list. My
  assumption is in §6 item 2.
- **HOLD H-V3:** whether the verifier measures C1 in-process or across a
  cold start; what I would need is the lens's timing harness. The prediction
  holds under both readings at this scale (one read pass; a cold start adds
  only interpreter startup).
- **HOLD H-V4:** whether the verifier's "chain hash" for C4 means the chain
  head (the last record's `record_id` — the thing §5.1 chains on) or a hash
  of the whole file; what I would need is the lens's definition. The module
  exposes the head (`VerifyResult.head`), and a byte-identical restore
  reproduces it identically under either reading.

Closed holds, stated so they are not re-opened: **H-2** not raised — fsync
per record is kept unweakened and C1 bounds verification only. **H-3**
closed — `ts` is monotonic non-decreasing per file with **equality
allowed**: two appends landing inside the same clock tick carry equal
timestamps, and a backwards clock step holds the previous `ts` instead of
decreasing. **H-4** closed — `state/` is created only under a path supplied
as a parameter (defaulting to the D2 path); nothing under
`/home/deploy/the-cell/state/` is created during authoring.

## 6. Assumptions I could not verify

1. The binding expects exactly the seven adapter names quoted in §3; the
   mapping in §2 declares them against the real names, and the harness's
   expectations for append/verify return values follow the module's
   documented API.
2. "Every string field" in the encoding lens = every field whose §5.1 rule
   is plain `string`: `payload_ref`, `block_version`, `attestation_ref`, and
   the string refs inside `axis` (`field.anchor` and each `delta` item). The
   hex64 fields (`record_id`, `prev_hash`, `turn_key`), the regex field
   (`address`) and the enum fields (`gate`, `state`, `mark`, `axis_verdict`,
   `corruption`) cannot carry arbitrary bytes under §5.1 and reject them —
   that is the validator enforcing, not a round-trip failure.
3. The verifier host is POSIX with `fcntl` available (both hosts in the
   facts block are Linux); the `flock`-based single-writer lock relies on
   that. The module carries a non-POSIX `O_EXCL` owner-file fallback, which
   I could not exercise on a non-POSIX host.
4. Python 3.13.5 on the verifier host behaves like the commissioned 3.12
   floor: the module is stdlib-only and uses no version-specific feature
   beyond 3.12; I could not execute on 3.13.
5. The §5.1 semantic rules ("only a human moves a gate out of
   `held-pending`", "set only by a human act", "machine-posed; non-data
   until a human converts it") are not mechanical field rules; the validator
   enforces the mechanical rules only (fifteen required fields, no extras,
   types, enums, regexes, hex64, axis shape, `axis_verdict` null only at a
   fresh anchor) and re-implements no gate semantics.
6. The torn-tail tolerance boundary: a final line without a trailing newline
   that parses as a complete record is a complete record (kept); one that
   does not parse is a torn fragment (discarded); a newline-terminated line
   that does not parse, anywhere, halts. I assume the verifier's C3 lens
   accepts exactly this reading of "last partial line discarded".
7. The live `state/` directory remains absent until the verifier's run; the
   module never touches it unless the exact D2 paths are supplied as
   parameters.
8. C1's predicted timing assumes the verifier host is of the same class as
   the box in the commission's facts; the 0.15 s figure quoted as the basis
   is the commission's own measurement, not mine.
