# PHASE CARD — R05-B4 · the unattended run (working handle)

**Round:** `R05 · B4` — the product's core claim, plus the observability deliverable. The phase
name and slot are **Amihai's to name** — this card uses the build-spine slot `B4` only until he
names it.
**Author:** dsh (`deepseek-v4-pro`, one generation). **Verifier:** Hermes profile `herdr`,
separately, against a pack written before it judges anything. `builder ≠ verifier`.
**Governing sources:** the commission (`./commission.md`), the Codex, Appendix D, PRD,
REQUIREMENTS (held at `../sources/`). **Codex §1.10 governs every conflict — the source wins.**

**Every verdict in this card is a PREDICTION.** Nothing here reports that anything ran, passed,
or verified anything. A separate verifier executes the artifact and writes the only record that
counts; it recomputes every verdict with its own implementation, and any divergence — in either
direction — is a FAIL.

---

## 0. The folded item — carried, never authored

The five desk function-specs are the **codex §2 decoding operations, run in attention mode on
the not-yet-found question** — quoted byte-faithful in `fixtures/desk.py`
(`DESK_FUNCTION_SPECS`), re-exported through `surface_contract` (sha-pinned), and carried into
every prompt the run sends. The founding sentence (§2.1) is quoted byte-faithful
(`FOUNDING_SENTENCE`). No new decoding operation, no new L1 symbol, no renamed symbol (D.12) —
including the glyph discipline: the codex's own `∞0'` (U+0027, §2.5 op 7) and the commission
table's `∞0′` (U+2032) are two enumerated byte forms, never folded.

## 1. Binding — the names this round ships

| binding | real name | where |
|---|---|---|
| `conductor_module` | `run` | `run.py` — `Conductor`, `next_action`, `audit_payload_chains`, `seed_ref` |
| `trail_module` | `trail` | `trail.py` — `FormationTrail`, `read_trail`, `project`, `compute_event_hash` |
| `cost_module` | `cost` | `cost.py` — `COST_MODEL`, `DeskAdapter`, `charge_for`, `measured_cost`, `spend_from_records` |
| `surface_contract_module` | `surface_contract` | `surface_contract.py` — 15 sha-pinned predecessor loads; `RUN_SURFACE` declared against the imported contract |
| `selftest_module` | `selftest` | `selftest.py` — the author's suite, a hypothesis never a result |
| `fixture_desk` | `desk` / `desk_server` | `fixtures/desk.py` (the folded specs + deterministic attention-mode answers) · `fixtures/desk_server.py` (the herdr-dialect stand-in pane server, B2's FakeHerdrServer shape) |
| `fixture_builder` | `build` | `fixtures/build.py` — renders the §3.6 surface templates from P4b's imported grammar, plants the human's record, pins the expected bytes |
| `fixtures` | `fixtures/{main_run,hold,budget,tentative,kill9,torn}/` | the seven named cases, byte-pinned |

## 2. Criteria and claims, by id — with PREDICTIONS

**C1 — holds accumulate instead of stopping the run.** Prediction: when a gate fails to lock
(the fixture desk dies mid-turn — the PRD §10.3 outage — or answers `⟦BLOCKED⟧` with no surface)
the conductor records ONE held record at the gate's own (address, gate) in the ledger, surfaces
it to the trail, and **keeps the other cells moving** — the hold never halts the run, is never
retried, and is never auto-resolved (no code path in `run.py`/`cost.py`/`trail.py` writes
`state: "attested"` or a non-null `attestation_ref`). The main 20-cycle run carries one outage
hold (cell `P`, cycle 3, Q-gate) and still ends `complete`; the hold fixture stalls with **two**
holds (one outage, one blocked) still held at the end, surfaced as one list in the run-end
projection.

**C2 — TENTATIVE seeding of the next S.** Prediction: when a cycle's V answer carries its ∞0′
slot, the run seeds the cell's next S with `tentative: true`, `corruption: "L2"` (the
machine-posed signal, carried honestly — B3's precedent), `state: held-pending`,
`attestation_ref: null`, `block_version: ""`; the seed record's `payload_ref` is
`seed:sha256:…` (a durable reference binding the carried ∞0′ to the seeding place, unique per
cell+cycle); the seed is never promoted, never reaches the podium (the run has no `question.md`
write path and never invokes `cell-attest`), and no downstream gate consumes it (C5's audit).
The seeded S is never prompted (T-R3-02: the inherited centre guard refuses S).

**C3 — restart re-arm from the ledger alone.** Prediction: `next_action` is a pure function of
the ledger (its chain verified by B0's loader on every replay) and the trail's line index — a fresh process rebuilds the
exact next action from disk alone, with no duplicate or skipped gate. The kill -9 fixture kills
the conductor at 60 records mid-run and the **second process** re-arms to a final ledger and
trail **byte-identical** to the uninterrupted pins (turn_key idempotency: every due turn's key
is `sha256(address ‖ gate ‖ "cycle:<c>" ‖ block_version)`, recomputed from the ledger alone;
the observe-repair rebuilds a trail line whose record landed while its line did not — the kill
order invariant is ledger-record-first, trail-line-second). A broken chain halts the conductor
(B0's verifier, exit 4) — never repairs.

**C4 — budget hold.** Prediction: spend is accounted BEFORE each turn as a pure function of the
completed turn records (`cost.spend_from_records` — re-armable from the ledger alone), charged
from the declared per-desk table (`COST_MODEL["charges"]`, conservative: each charge ≥ the
measured turn cost). A ceiling reached records `hold:budget-ceiling:…` at the due (address,
gate) in the ledger and the run stops cleanly (status `budget-held`, exit 0) — never a silent
kill, never a spend past the ceiling (the budget fixture charges 6 turns to 16200 ≤ ceiling
19000 and holds the 7th).

**C5 — no tentative node consumed by a downstream gate.** Prediction: the dependency audit
walks every gate record's payload_ref chain — each payload_ref resolves to the FIRST record in
chain order carrying that reference (the producer: every run record anchors its axis at its own
payload_ref); a gate whose evidence chain reaches a `tentative: true` record is a FAIL. The
audit runs once, end-to-end over the whole ledger: PASS over the full main run, FAIL (exactly
one consuming record) over the injected consumed variant, INCONCLUSIVE over an empty ledger —
never clean on nothing (lens 6).

**C6 — ≥ 20 cycles with zero human keystrokes.** Prediction: the main fixture completes 20
cycles (103 ledger records: his plant + 102 machine records, 105 trail lines) with zero
keystrokes — the only attested record in the ledger is the plant (the fixture world's TTY
stand-in, P4a's attest-provider precedent); the run's source carries no `input()` call, no
cell-attest invocation, no podium write, and every counted cycle's V carried its ∞0′ reference
first.

**C7 — the observability deliverable.** Prediction: the trail is append-only (O_APPEND + fsync
per line, a mid-run prefix stays byte-for-byte), hash-chained (`prev_hash` = sha256 of the
previous line's exact bytes; `event_hash` = sha256(prev_hash ‖ canonical(line − event_hash)) —
the field-side chaining the existing formation trail uses), replayable from disk, and readable
MID-RUN: a reader replays the complete prefix (a torn tail is flagged and discarded — never a
line, never valid), the chain verifies, and the partial projection is consistent at every
point. It records what the context decoded TO — slot references (sha256 + byte length), never
the desk's text, never the context (D12). Two trails, never merged: the formation trail refuses
a path equal to the ledger path, and the gate ledger is written through `fractal_ledger` only,
never by hand.

### The six lenses, predictively

1. **Criterion match** — each criterion's done-when sentence is quoted at the measuring site
   (the run's docstrings carry the §B4 build sentences; the guard policy, the audit rule and
   the schedule are declared in `RUN_SURFACE` with citations), and each selftest names the
   criterion it measures.
2. **Invariant end-to-end** — the dependency audit and the zero-keystroke run hold across the
   whole 20+ cycles at once (not per call): one audit over all 103 records, one
   completed-cycle count from the whole trail, the byte-pinned ledgers and trails.
3. **Absence vs validity** — an absent trail reads `absent`, an empty one reads `empty` with
   sha256 `e3b0c44298fc…` (never valid); an absent plant boots nothing (BootError, zero
   records); an empty ledger audits INCONCLUSIVE; a torn fragment is discarded, never a line.
4. **Encoding** — `∞0′ → ‖` rides the plant's `attestation_ref` (a ledger string field), the
   trail's boot line, and every fixture slot the desk speaks; all JSON is UTF-8 passthrough
   (`ensure_ascii=False`), the trail opens only binary modes, and no text-mode byte seek
   exists.
5. **Cold restart** — the kill -9 harness and the max-actions split both run the SECOND
   process as a fresh python (subprocess) rebuilding from disk alone, byte-identical to the
   uninterrupted pins; the derive-at-every-step test re-derives every next action from a
   brand-new Conductor.
6. **Blind tool** — no desk is constituted (H-B4-1): the fixture desks are declared stand-ins,
   a blocked answer holds and never completes, an empty ledger audits INCONCLUSIVE, and a
   missing plant boots nothing — nothing unobservable ever reads clean.

## 3. D14 divergence log — everything this artifact adds beyond the source

Per Appendix D's own jacket: declared *derivative* · visibly separate from the decoding · adds
**no** L1 symbol, **no** decoding operation, **no** sixth corruption code · alters no invariant
line. **Summary: the conductor layer (schedule, holds, TENTATIVE seeding, budget, audit, trail)
sits ON the attested driver — the attestation-gated walk gating is not used (T-R5-03: nothing
is attested by design), the D.12 check is the imported one with a declared turn-validity
policy, and the RUN-FLOW item reads the D.12 semantic flow on the unattended record surface,
separately numbered (B3's GS-* precedent). No L1 symbol, decoding operation or corruption code
is added; the folded desk function-specs are quoted byte-faithful.**

| # | Addition | Anchor | Resolution |
|---|---|---|---|
| D-1 | The conductor layer: `Conductor` (extends B2's `Driver`), the round-robin schedule (cells in declared order, cycles ascending — the next action is a pure function of the ledger), the hold records (outage / blocked / guard-fail / budget-ceiling), the TENTATIVE seeding, the budget accounting, the run-end audit | PRD §B4, §10.3; B2's `Driver`, `turn_key`, `Instrument.prompt_desk` imported | Interface layer on the attested driver — the herdr dialect, the D.12 checks, the desk grammar and the descent are never re-implemented. B2's attestation-gated gating (`position_from`/`advance`) is not called: an unattended run has no attestations by definition |
| D-2 | The record conventions (payload_ref kinds `fenced:sha256:` / `seed:sha256:` / `hold:<kind>:…`, the `cycle:<c>` attempt slot, the B2 proposal shape, the hold never-resolved rule) | §5.1, B2's proposal record, B3's seed precedent | Data declared in `RUN_SURFACE`; every append through B0's `LedgerWriter`, never by hand |
| D-3 | The trail schema (`TRAIL_FIELDS`, the prev_hash/event_hash chaining, the torn-tail rule, the projection) and the two-trails refusal | PLAN-ADDENDUM §B; the existing formation trail's field-side chaining; P4a's step-trail precedents | The formation trail is the field side; the gate ledger is the chain side — never merged |
| D-4 | The guard policy: the imported D.12 check (`conformance.evaluate`) runs after every step; `DESK_FIDELITY_ITEMS` FAILs hold the gate; `GUARD_FLOW_ITEMS` FAILs (P4a's attestation-based reading of "context flows father → daughter") are the unattended world's own truth, carried beside the RUN-FLOW schedule invariant | Appendix D §D.12; P4a's `conformance.py` (imported, never re-authored); T-R5-03 | The check is P4a's; only the turn-validity POLICY is B4's declared data — never a re-numbering of P4a's AD-*/CX-*/DC-* items |
| D-5 | The cost model (`COST_MODEL` — the declared default mode, the per-desk charges, the dual-mode adapter with measured RSS/token instrumentation) | H-B4-2: the sub-process vs re-prompted decision is measured, not yet made live | Declared data; the live per-Pi measurement awaits a constituted desk |
| D-6 | The fixture apparatus (the deterministic fixture desk, the desk server, the spec builder, the seven pinned cases, the fixed clock, the kill harness) | H-B4-1; B2's FakeHerdrServer precedent; B3's fixture-fiction precedent | Test apparatus only; the run itself never writes `state: "attested"` — the plant is the fixture world's TTY stand-in |
| D-7 | The folded item carrier (`fixtures/desk.py`: the codex §2 desk function-specs byte-faithful, the founding sentence, the attention readings) | Commission §5 (not new doctrine — quoted) | Quoted, never authored; the specs' glyphs are enumerated, never normalised |

## 4. Holds — H-B4-1 … H-B4-5, each with the reading this round ships

* **H-B4-1 (no desk is constituted).** The run is fixture-driven: `fixtures/desk.py` is the
  deterministic attention-mode desk (clearly labelled stand-in fiction), served by
  `fixtures/desk_server.py` over its OWN AF_UNIX socket — no real Pi, no live herdr socket, no
  live pane. The inherited B2 trust assertion sits behind a neutral stand-in.
* **H-B4-2 (the mode decision is measured, not yet made live).** `cost.py` supports BOTH modes
  and instruments per-turn memory/token cost; the conservative default is DECLARED DATA —
  `cost.py:65` (`COST_MODEL["default_mode"]`) — and the conductor resolves it from that table
  at `run.py:155`, never from a mode literal in its control flow.
* **H-B4-3 (the success shape stays inert).** The run reads the desk's answer from the fenced
  read (`Instrument.prompt_desk`), never from the `agent.prompt` success shape — the fixture
  server's success shape is deliberately inert.
* **H-B4-4 (the human's gate act is untouched).** The run seeds the next S as TENTATIVE, but
  never writes the podium, never types a word, never invokes `cell-attest` — attestation stays
  a TTY act.
* **H-B4-5 (B″ composition is B6, not B4).** The run returns the V's artifact + ∞0′ as
  references (the fixture desk's own B″ — the run composes no candidate).

## 5. Assumptions and open flags (stated, not hidden)

1. The committed byte-pins are the bytes generated under the **canonical relative work path**
   (`fixtures/<case>/work/…`, run with cwd = `authored/`): the trail lines carry the ledger
   path as observability, so regeneration under a different path string yields identical
   content with the path string (and therefore the chained hashes) differing — the kill -9 and
   cold-restart proofs run under the canonical path and compare byte for byte.
2. The fixture world writes the plant (attested) as the human's TTY stand-in — P4a's
   attest-provider precedent; the run itself never writes attested (assumption #4 of B3,
   carried).
3. "Genuine ∞0′" is operationalized as presence — the run records the ∞0′ reference and the
   tentative marker; genuineness is the human's click, never a machine verdict (commission §6).
4. The run's clock is the fixed fixture clock (B0's `clock=` parameter, the spec's declared
   data) so the pins are byte-exact; the default clock stays B0's own.
5. `block_version` stays `""` (H-B3-5 carried) — no block identity is observable on the read
   surface, and inventing one is forbidden.
6. The cycle target, the cells, the ceiling and the mode are caller-supplied spec data — the
   run hard-codes no cap, no cell list, no ceiling, and assumes no root (the plant's role is
   read from the ledger, Appendix D.2).
7. `PLAN-ADDENDUM` is not present on the box; its §B is known only from the commission's
   quotes (P4b's precedent, carried).
8. The verifier's pack may bind different names than §1; the functions are the real surface,
   the names are stable and documented here.
