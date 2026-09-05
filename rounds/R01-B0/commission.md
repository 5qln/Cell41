# COMMISSION — R01 · B0 the ledger and the record

*Written by Hermes (`herdr`) on 2026-08-27 before anything is authored. A file, never chat. This
document is dsh's whole world for this round. Nothing outside it is required, and nothing inside it
may be widened.*

- **Canon this commission quotes:** `5qln/5qln-herdr-plugin` → `docs/fractal-herdr/PRD.md`,
  sha256 `71ce2645078dd48f56fb7c2a8d916a1ffa70cb0db2bd74648093c8add8b1d99c` (commit `e50eb25`,
  2026-08-27). The box copy at `/home/deploy/Asdh5/fractal-herder/PRD.md` is byte-identical to it —
  verified, same sha256. Quote from either; they are the same bytes.
- **Round budget:** one authoring generation. Exceeding it is a HOLD surfaced to Amihai, never a
  silent continue.
- **Author:** dsh. **Verifier:** Hermes (`herdr`), with `/opt/data/tools/deliverable-audit/`.
  **Attester:** Amihai, at a TTY, at the end.

---

## 1. What to build (one paragraph, no doctrine)

A standalone Python module (stdlib only) that creates `state/`, defines the gate record of §5.1 **as
an enforcing validator**, appends records to a single append-only hash-chained JSONL ledger with one
writer and `fsync` per record, verifies the whole chain from `GENESIS`, replays it to re-arm state
from disk alone, and maintains a derived, disposable index sidecar. Nothing else: no conductor, no
herdr socket, no Pi, no gate semantics, no pane, no scheduling. B0 is the trace's foundation — the
one thing that must never be lost — and this round is only that foundation.

---

## 2. Acceptance criteria — quoted verbatim from the PRD

> **§9 B0 — The ledger and the record *(blocked by D2)*.** Build: `state/` created; the record schema
> as a validator; the append-only writer (single-writer lock, fsync); the chain verifier; the
> replay/re-arm loader; the disposable index.
> **Done when:** (1) 10 000 synthetic records verify from GENESIS in < 2 s; (2) a single flipped byte
> is detected and halts the loader; (3) `kill -9` mid-append leaves a valid chain (last partial line
> discarded); (4) a restore from backup reproduces the same chain hash.

| ID | Criterion, as written | The dimension it is judged in |
|---|---|---|
| **C1** | 10 000 synthetic records **verify** from GENESIS in < 2 s | time of **verification**, not of writing (see §4 hold H-1) |
| **C2** | a single flipped byte is detected and **halts** the loader | detection, proven against a chain that verified clean *before* the flip |
| **C3** | `kill -9` mid-append leaves a **valid chain** (last partial line discarded) | number of complete records still valid, with **more than one** record written |
| **C4** | a restore from backup reproduces the **same chain hash** | equality of the chain head before and after restore |

Two further requirements of the same §9 build list are commissioned as first-class deliverables,
because the previous attempt at B0 claimed them and did not have them:

| ID | Requirement, as written | Where |
|---|---|---|
| **K1** | "the record schema as a validator" — a record that violates §5.1 must be **rejected at append**, never chained | §9 B0 build list, §5.1 |
| **K2** | "the append-only writer (**single-writer lock**, fsync)" — a second writer must be excluded, and per §10.3 "second exits non-zero, records nothing" | §9 B0 build list, §10.3 |

Supporting text, also verbatim, that the code must satisfy:

> **§5.2 The ledger.** Path (proposal → decision D2): `/home/deploy/the-cell/state/gates.jsonl` …
> Append-only, `fsync` per record, single writer, never rewritten, never rotated (it is the trace).
> Recovery = replay + chain verify. A broken chain halts the conductor (**fail closed**) and
> surfaces; it never "repairs" itself. Sidecar `state/gates.index.json` (derived, disposable): last
> record per address, open holds, cycle counts. **Deleting it must change nothing.**

> **§4.x Re-arm from the ledger, never from RAM.** On boot the conductor replays the ledger, verifies
> the hash chain, and reconstructs its state; anything not in the ledger did not happen.

> **§10.3** ledger chain break → detected by loader verify → required behaviour: **halt** the
> conductor, surface, never repair.

> **§11.4 Durability.** B0's acceptance includes a **restore-and-verify** (same chain hash).

### The record — §5.1, verbatim field rules (the validator's specification)

| Field | Type | Req | Rule |
|---|---|---|---|
| `record_id` | hex64 | ✔ | `sha256(prev_hash ‖ canonical_json(record − record_id))` |
| `prev_hash` | hex64 \| `"GENESIS"` | ✔ | the previous record's `record_id` — the chain |
| `ts` | RFC3339 UTC | ✔ | writer clock; **monotonic non-decreasing per file** |
| `address` | `^[+-]?[SGQPV]*$` (`""` = ε/root) | ✔ | word over {S,G,Q,P,V} + sign; zoom in = append, out = strip |
| `gate` | `x` \| `y` \| `z` \| `a` \| `b` | ✔ | the only phase authority — no `current_phase` field exists anywhere |
| `state` | `attested` \| `held-pending` \| `mechanical` | ✔ | three-valued; only a human moves a gate out of `held-pending` |
| `mark` | `emergent` \| `mechanical` | ✔ | mandatory at every gate |
| `payload_ref` | string | ✔ | durable reference — **never content** |
| `axis` | object | ✔ | `{field:{mode:"inherited"\|"anchored", anchor:<ref>}, delta:[<ref>…]}` |
| `axis_verdict` | `STASIS` \| `MOVING` \| `recast` \| `null` | ✔ | null only at a fresh anchor |
| `corruption` | `L1`…`L4` \| `V∅` \| `null` | ✔ | the guard pass result at this node |
| `tentative` | bool | ✔ | true ⇒ machine-posed; non-data until a human converts it |
| `turn_key` | hex64 | ✔ | `sha256(address ‖ gate ‖ attempt ‖ block_version)` |
| `block_version` | string | ✔ | which block sat at this desk (`g-essence@3`) |
| `attestation_ref` | string \| null | ✔ | set **only** by a human act; null everywhere else |

`record_id` is computed by the writer, never supplied by a caller. All fifteen fields are required:
absence is a violation, and an unknown extra field is a violation.

---

## 3. Verified-facts block (executed on this host — do not re-derive, do not re-probe)

| Fact | Value | Probed |
|---|---|---|
| Ledger path (D2, decided by Amihai) | `/home/deploy/the-cell/state/gates.jsonl` | PRD §5.2 / §13.1 |
| Index sidecar path | `/home/deploy/the-cell/state/gates.index.json` | PRD §5.2 |
| `state/` directory | **ABSENT** — B0 creates it. Nothing has ever been recorded or attested on the cell | box probe 2026-08-27 12:39 UTC |
| `/home/deploy/the-cell` | **not** a git checkout; hand-deployed | box probe 2026-08-27 |
| Cell root question | `/home/deploy/the-cell/question.md` is a symlink → `nodes/_/question.md` (83 B) | box probe 2026-08-27 12:37 UTC |
| Loaded herdr plugin manifest | `/home/deploy/the-cell/plugin/herdr-plugin-v4.toml`, sha256 `11b9b53c8390…`, 14 249 B, `plugin_id cell.fiveqln`; pinned as `manifest_path` in `~/.config/herdr/plugins.json`. The sibling `herdr-plugin.toml` (11 788 B) is **inert** | box probe 2026-08-27 12:33 UTC |
| herdr / Pi / node versions | herdr 0.8.2 (protocol 20) · Pi 0.84.2 · node v22.23.2 | 2026-08-27 |
| Python on the box | `python3` 3.12 (Ubuntu 24.04); Python on the verifier host: 3.13.5 — **write for 3.12+, stdlib only** | 2026-08-27 |
| Attestation binaries | `plugin/bin/cell-plant`, `plugin/bin/cell-attest` refuse non-TTY with **RC=4** — that is the seal working, not a bug to route around | 2026-08-27 |
| Canon PRD sha256 | `71ce2645078dd48f56fb7c2a8d916a1ffa70cb0db2bd74648093c8add8b1d99c` (repo = box = wiki, all three byte-identical) | drift check 2026-08-27 12:39 UTC |
| Verifier harness that will judge this round | `/opt/data/tools/deliverable-audit/` — spec `specs/b0-ledger.json` quotes C1–C4 and K1–K2 above; accepted 2026-08-27 (22/22 self-checks) | 2026-08-27 13:05 UTC |

**What the verifier will run** (so nothing about the judging is a surprise): the four criteria exactly
as quoted, the two claims K1/K2, and the six lenses — criterion match (including an AST read of your
own selftest's timed assertions), invariant end-to-end, absence vs validity, encoding `∞0′ → ‖`
through every string field, **cold restart in a new process**, and blind-tool handling. Adapter names
are declared in the spec's `binding` block: `writer_class`, `verifier_class`, `append_method`,
`verify_method`, `genesis_const`, `id_field`, `prev_field` — name your classes as you like and state
the mapping in the phase card.

### Findings from the previous B0 attempt (a different author, executed 2026-08-27 — this is why the round exists)

1. **The chain was not a chain.** `_get_tail_hash()` returned `GENESIS` for every append: 10 000 of
   10 000 records carried `prev_hash=GENESIS`, and the verifier died at record 2. Cause: a backward
   byte scan in **text mode** that started on the trailing newline, read an empty tail, and silently
   fell back to `GENESIS`.
2. **The criterion was met in the wrong dimension.** Its suite asserted `< 2 s` on a timer wrapped
   around **writing** 10 000 records (19.9–20.8 s measured here). C1 is about **verification**
   (0.15 s once the chain was repaired).
3. **The promised schema validator did not exist.** `{"total":"garbage"}` was accepted and chained.
4. **New, found by the verifier harness on 2026-08-27 and not by any author suite:** after the
   4-line repair, a **second process** cannot rebuild the tail when the ledger holds **exactly one
   record** — it dies with `json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)`.
   The repair only worked because the tail was cached in memory within one process. **The first
   restart after the very first gate record is the failure point** — which is B0's first real moment
   in the live cell. Reproduced with three plain `python3 -c` processes.

Therefore this round's tail recovery must be **specified and tested at the 0-record, 1-record and
n-record boundaries, reading only from disk**, with no dependence on in-process state. State the
boundary behaviour in the phase card as predictions.

---

## 4. Holds — declare, never guess

If you cannot verify something here, write `HOLD <id>: <what you would need>` in the phase card. A
guess that reads as a fact is the failure this whole flow exists to prevent. Open holds carried into
this round:

- **H-1 (closed, stated so you do not re-open it):** C1 measures verification, not writing. Writing
  10 000 records may take as long as it takes; there is no written bar on write time. Do not optimise
  writing at the cost of the chain, and do not report a write timing as if it answered C1.
- **H-2:** `fsync` per record on this VPS costs milliseconds per append. If you believe the criteria
  cannot be met with `fsync` per record, do **not** weaken durability — raise
  `HOLD H-2: <measurement + what you propose>`.
- **H-3:** the monotonic-`ts` rule (§5.1) is per file. If two appends land inside the same clock tick,
  state in the phase card what your writer does (equal timestamps are allowed by
  "non-decreasing" — say so explicitly rather than leaving it implied).
- **H-4:** `state/` does not exist yet. Create it **only** under a path passed in as a parameter, and
  default to the D2 path. Do not create anything under `/home/deploy/the-cell/state/` during
  authoring — the live directory is created in the verified run, not by the author.

---

## 5. Prohibitions for this round

- **No write path to the podium.** `pane.send_text` / `pane.input` / `pane.keys` at the centre is the
  forbidden path, in code and in examples.
- **No git.** You do not commit, branch, tag or push. Publishing is Hermes's act.
- **No attestation, and no claim that anything ran.** Your phase card carries **predictions**, never
  results. Do not write "✅", "passed", "verified", "sound", or "tests green".
- **No gate semantics re-implemented outside `fractal-engine`.** B0 stores records; it does not
  decide what a gate *means*.
- **No herdr socket, no Pi, no network, no third-party package.** Stdlib only, importable as a module
  and runnable as `python3 -m` / `python3 <file>`.
- **Nothing may be described as attested, decided, or verified** that this commission does not
  already mark so. `TENTATIVE` is temporal, never epistemic.
- **No writes anywhere outside** `/home/deploy/the-cell/rounds/R01-B0/authored/` and paths passed to
  your own code as parameters.

---

## 6. Deliverables and where they go

`/home/deploy/the-cell/rounds/R01-B0/authored/`

1. `fractal_ledger.py` (or your chosen name) — validator, writer, verifier, replay/re-arm loader,
   index builder. Stdlib only, Python 3.12+.
2. `selftest.py` — your own tests. Each test states **which criterion ID** it exercises and **which
   quantity** it measures. A test that times an operation must name that operation.
3. `phase-card.md` — criteria restated by ID, the adapter name mapping for the verifier's `binding`,
   your **predictions** per criterion (what you expect the measured numbers to be), the boundary
   behaviour for tail recovery at 0/1/n records, holds raised, and every assumption you could not
   verify. Predictions only. No results.

---

## 7. Budget

One authoring generation for this round. Corrections after the evidence record are limited to two,
each surgical (exact command, traceback, bytes, hashes). Exceeding either limit is a HOLD surfaced to
Amihai, never a silent continue.
