# PHASE CARD — P4a · the step mode (operational-fractal conformance, stepped)

**Round:** `P4a` — the slot Amihai's 1% opened (his words, verbatim, held in the
commission §0): *"we need a mode for testing that will go slow (step by step) to
analyse if the flow is kept according to exact operational fractal."*
**Author:** dsh (`deepseek-v4-pro`, one generation). **Not** a B-phase: it precedes
`R04 = B3` (descent). **Governing sources:** the Codex, Appendix D, PRD,
REQUIREMENTS (held at `../sources/`, shas in the commission header). **Codex
§1.10 governs every conflict — the source wins.**

**Every verdict in this card is a PREDICTION.** Nothing here reports that
anything ran, passed, or verified anything. A separate verifier executes the
artifact and writes the only record that counts; it recomputes every
conformance verdict with its own implementation, and any divergence — in
either direction — is a FAIL. If my own run revealed a bug, it was fixed
silently; this card stays predictive.

---

## 1. Binding — the names of §9.1, as shipped

| binding | real name | where |
|---|---|---|
| `step_module` | `step` | `step.py` |
| `stepper_protocol` | `Stepper` | `step.py` — `before(intent)` / `after(event)` → `"continue"` \| `"stop"`; a protocol, not an enforced base |
| `auto_stepper` | `AutoStepper` | `step.py` — answers `"continue"` to every hook; behaviour-neutral |
| `trail_writer` | `StepTrail` | `step.py` — append-only JSONL, one line per step, `prev_line_sha256` chained; refuses a trail path equal to its ledger path |
| `trail_reader` | `read_trail` | `step.py` — `read_trail(path)` → `{status: absent\|empty\|damaged\|ok, lines, damage, chain, sha256}`; a torn last line is DAMAGED |
| `step_kinds` | `STEP_KINDS` | `step.py` — registry; `zoom_in` / `zoom_out` RESERVED, `implemented: False` |
| `runner` | `run_session` | `step.py` — walks a plan under a Stepper; no sleeping in the driver; the blocking form lives here |
| `conformance_module` | `conformance` | `conformance.py` |
| `check_table` | `CHECKS` | `conformance.py` — 50 items, id → `{source, citation (verbatim), scope, derived}` |
| `evaluate_fn` | `evaluate` | `conformance.py` — `evaluate(context)` → `{verdict, counts, items}` |
| `session_aggregate_fn` | `aggregate` | `conformance.py` — PASS only if every item reached PASS at least once and none ever FAILed; silence is never a pass |
| `equation_forms` | `EQUATION_FORMS` | `conformance.py` — enumerated byte forms, each with source + sha256 (per-form sha and the extracted source-line sha); never normalised |
| `corruption_codes` | `CORRUPTION_CODES` | `conformance.py` — exactly `L1 L2 L3 L4 V∅`, frozen |
| `surface_module` | `surface` | `surface.py` |
| `surface_contract` | `SURFACE_CONTRACT` | `surface.py` — the §3.6 contract as data, versioned, in one place |
| `surface_parse_fn` | `parse_surface` | `surface.py` — `parse_surface(text, equation_forms=…)` → `{context_in, decoded, compiled}` references only |
| `driver_module` | `driver` | `driver.py` (extended in place) |
| `driver_class` | `Driver` | `Driver(…, stepper=None)` — `None` is a true no-op: no trail file, no check, no behavioural branch |
| `turn_method` | `take_turn` | `driver.py` — behaviour unchanged; hooks per §4.3 |
| `advance_method` | `advance` | `driver.py` |
| `boot_method` | `boot` | `driver.py` |

## 2. Criteria and claims, by id — with PREDICTIONS

**C1 — the same code path, stepped.** Prediction: `stepper=None` executes none
of the stepping surface (no trail file is created anywhere, no `"step"` key
appears in any status dict, no check runs), so the unstepped driver is B2's
attested driver behaviour-for-byte — the 34 B2 tests run against the extended
driver unchanged and must keep holding. The same walk under `AutoStepper`
should produce an identical `gates.jsonl` projection (every record with
`ts`/`record_id`/`prev_hash` excised, canonicalised, hashed) and an identical
ordered socket method+params sequence — 20 calls across the four turns, no
extra observation traffic (the cell's arrangement is captured from the label
resolution the walk already performs; a desk's surface is parsed from the
fenced read the walk already takes). Exactly one implementation: AST finds
`take_turn`/`advance`/`boot` once, in `driver.py`; `step.py`,
`conformance.py`, `surface.py` define no second turn loop, no `turn_key`
derivation, no ledger append path (the runner calls the driver; the human's
attest provider is the one writer, the same channel B2's tests use).

**C2 — suspension before the side effect.** Prediction: a controller answering
`stop` at the boot intent or at a turn intent leaves zero socket connections /
zero prompt bytes / zero records, and the trail's last line is the intent with
`outcome.status: "not-taken"` and a populated `next` block. A `stop` in the
`after` hook ends the session cleanly — the next step never begins, the driver
returns a status and raises nothing. A FAIL verdict stops the session under
`on_fail="stop"` (the default); `on_fail="continue"` (explicitly configured)
continues and the trail line records the override in
`conformance.policy`. Stepping never sleeps, never polls, never waits on a
human by default: the blocking form (print the emission, wait for Enter) lives
in `run_session` and is off by default; a keypress is not an attestation and
nothing derives one from it.

**C3 — the emission is complete and honest.** Prediction: every trail line
carries all 21 required fields (the builder and the reader share one list, so
a missing field cannot pass the writer); `seq` is gapless within a session
(a gap raises at the writer); `prev_line_sha256` chains every line after the
first; `at` is an observation timestamp and is never an input to logic. A
desk's answer text appears nowhere in the trail — slots leave the parser as
`sha256` + byte length only, and the greppable trail carries scheme-prefixed
references or 64-hex fingerprints, never content. Unobservable reads —
missing bundle, unreadable Pi state, absent V record, no announced surface —
read INCONCLUSIVE with a reason, never PASS, never silently absent.

**C4 — the checks are the source's and they catch a defect.** Prediction:
every one of the 46 source items cites its source line verbatim (the derived
four cite his decision verbatim plus a source line); the nine commissioned
defective twins FAIL by id: 3+1 cell → `AD-SYN-1` (naming the missing corner);
paraphrased equation → `AD-SYN-2` (evidence carries the first differing
codepoint); sixth corruption code → `AD-SYN-5`; `+` inside a phase equation →
`AD-SYN-4`; skipped/reordered phase (a proposed Q while y is unattested) →
`CX-SEM-2`; V closing without `∞0′` → `R8` + `CX-SYN-6` + `AD-SEM-3` + `R2`
(the source states the rule three times — mirrors by source design, all four
fail); signed true start → `AD-SEM-4`; lens question targeting the wrong
output → `AD-DRF-5` + its §3.5 mirror `CX-DRF-6`; hard-coded depth cap in a
mutated artifact copy → `AD-DRF-1` (AST scan over the mutated tree). Against
the live box state (no desk constituted, no Pi extension installed) every
cell-scope item reads INCONCLUSIVE — that is the correct live verdict, not a
gap. My verdicts are deterministic functions of the context and the verifier
recomputes each one independently.

**C5 — two trails, never merged; cold restart.** Prediction: `gates.jsonl`
gains nothing from stepping (the projection and the differing-field set are
unchanged); no trail line is ever promoted to a record; `prev_line_sha256` is
integrity only. A fresh process rebuilds position from the ledger alone (a
recorded turn is never re-prompted) and reconstructs trail continuity from the
trail file alone; a continuing session appends the next `seq` chained to the
last line. A torn last line reads DAMAGED (never a valid step, never an
empty-but-clean trail); a missing file reads `absent`; an empty file reads
`empty` with `sha256("") = e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`;
a one-line trail's chain reads `undecidable`, never trivially clean.

**K1** — prediction: the static AST facts are empty (no identifier names a
depth, no `len(address-like)` compared against a constant, no re-implemented
address grammar), the alphabet is the walker's `COURSE` data table, and no
logic depends on which end of the address word is deep (H-P4a-2).

**K2** — prediction: stdlib only (Python 3.12+), deterministic, no LLM
anywhere in the checks; the full stepped session over the fixtures (the timed
operation: `run_session` over the cycle fixture) completes in well under 60 s.

**K3** — prediction: no code path can emit PASS for the authenticity of a
decode. `DC-AUTH-1` (whether an α is THE essence) and `DC-AUTH-2` (whether an
`∞0′` question is more alive than the X it came from) are permanent
INCONCLUSIVE, with the reason stated at the site: *"…is the human's click — the
step mode checks that the slot is filled and referenced, never that it is
true (K3)… A machine that reports resonance has failed the measure."*

**K4** — prediction: the B2 guards hold under stepping — the centre is never
prompted, `state:"attested"` and a non-null `attestation_ref` stay unreachable
from the driver, and an interactive Enter consumed between steps derives zero
attestations (the attested records stay exactly the plant + the four
provider-supplied human records).

**K5** — prediction: `zoom_in`/`zoom_out` exist as reserved registry entries
with `implemented: False`; a plan act for either raises `StepKindError` — B3
adds descent without touching the controller protocol or the trail schema.

**K6** — prediction: the D14 jacket holds — exactly four items are marked
`derived` (`DC-DECODE`, `DC-COMPILE`, `DC-AUTH-1`, `DC-AUTH-2`), separately
numbered so they cannot drift `R1–R13`, the corruption codes are exactly the
five, no L1 symbol was added, no decoding operation was added; the divergence
log below lists everything this artifact adds.

## 3. The check-item table (id → source → scope)

| id | source | scope | derived |
|---|---|---|---|
| AD-SYN-1 | Appendix D §D.12 (syntax) | cell | — |
| AD-SYN-2 | Appendix D §D.12 (syntax) | cell | — |
| AD-SYN-3 | Appendix D §D.12 (syntax) | cell | — |
| AD-SYN-4 | Appendix D §D.12 (syntax) | cell | — |
| AD-SYN-5 | Appendix D §D.12 (syntax) | cell | — |
| AD-SEM-1 | Appendix D §D.12 (semantic) | step | — |
| AD-SEM-2 | Appendix D §D.12 (semantic) | step | — |
| AD-SEM-3 | Appendix D §D.12 (semantic) | step | — |
| AD-SEM-4 | Appendix D §D.12 (semantic) | step | — |
| AD-SEM-5 | Appendix D §D.12 (semantic) | cell | — |
| AD-DRF-1 | Appendix D §D.12 (drift) | static | — |
| AD-DRF-2 | Appendix D §D.12 (drift) | static | — |
| AD-DRF-3 | Appendix D §D.12 (drift) | session | — |
| AD-DRF-4 | Appendix D §D.12 (drift) | static | — |
| AD-DRF-5 | Appendix D §D.12 (drift) | cell | — |
| CX-SYN-1 | Codex §3.5 (syntax) | cell | — |
| CX-SYN-2 | Codex §3.5 (syntax) | cell | — |
| CX-SYN-3 | Codex §3.5 (syntax) | cell | — |
| CX-SYN-4 | Codex §3.5 (syntax) | static | — |
| CX-SYN-5 | Codex §3.5 (syntax) | static | — |
| CX-SYN-6 | Codex §3.5 (syntax) | step | — |
| CX-SEM-1 | Codex §3.5 (semantic) | cell | — |
| CX-SEM-2 | Codex §3.5 (semantic) | step | — |
| CX-SEM-3 | Codex §3.5 (semantic) | cell | — |
| CX-SEM-4 | Codex §3.5 (semantic) | cell | — |
| CX-SEM-5 | Codex §3.5 (semantic) | step | — |
| CX-SEM-6 | Codex §3.5 (semantic) | step | — |
| CX-DRF-1 | Codex §3.5 (drift) | static | — |
| CX-DRF-2 | Codex §3.5 (drift) | static | — |
| CX-DRF-3 | Codex §3.5 (drift) | session | — |
| CX-DRF-4 | Codex §3.5 (drift) | static | — |
| CX-DRF-5 | Codex §3.5 (drift) | session | — |
| CX-DRF-6 | Codex §3.5 (drift) | cell | — |
| R1 | Codex §3.4 R1 | step | — |
| R2 | Codex §3.4 R2 | step | — |
| R3 | Codex §3.4 R3 | cell | — |
| R4 | Codex §3.4 R4 | static | — |
| R5 | Codex §3.4 R5 | cell | — |
| R6 | Codex §3.4 R6 | cell | — |
| R7 | Codex §3.4 R7 | step | — |
| R8 | Codex §3.4 R8 | step | — |
| R9 | Codex §3.4 R9 | static | — |
| R10 | Codex §3.4 R10 | step | — |
| R11 | Codex §3.4 R11 | step | — |
| R12 | Codex §3.4 R12 | step | — |
| R13 | Codex §3.4 R13 | static | — |
| DC-DECODE | D12 (his word, 2026-08-28) + Codex §3.2/§3.3 | step | derived |
| DC-COMPILE | D12 (his word, 2026-08-28) + Codex §3.2/§3.3 | step | derived |
| DC-AUTH-1 | his decision (K3) + Codex §2.2 success criterion | step | derived |
| DC-AUTH-2 | his decision (K3) + Codex §2.5 success criterion | step | derived |

Scope meanings, as implemented: `static` — decided by reading the artifact's
own source and data tables (AST scans, cached by the scanned bytes' digest so
a mutated twin re-scans), re-emitted by reference in every step; `cell` —
decided by observing the cell (the arrangement captured from the label
resolution the walk already performs; each desk's announced surface parsed
from its fenced read — INCONCLUSIVE when nothing is observed, which is the
correct live verdict on this box); `step` — decided from the step event + the
ledger replay; `session` — decided at aggregation from the whole trail, never
by absence of failure.  Every item appears in every report — no item is ever
silently omitted.

### Predictions of note (the honest defaults)

* On the LIVE box (no desk constituted, no Pi extension): all 15 cell-scope
  items INCONCLUSIVE; `R10`/`R11`/`R12`/`AD-SEM-4` PASS (provenance read off
  `mark` — the plant is emergent+attested+non-null ref; its bare-digest
  `payload_ref` is a fingerprint hash, accepted by R11's reference shapes);
  the report verdict INCONCLUSIVE. That is the correct live verdict — P4b's
  desk bundles are what will turn the cell items into PASS.
* On a clean stepped walk whose desks announce no surface: the session verdict
  is INCONCLUSIVE (the cell items are unobservable and the two DC-AUTH checks
  are permanent INCONCLUSIVE by design) — a machine can never report a fully
  clean session, and that is the point of K3.
* `AD-SYN-4` and `AD-DRF-1`/`R13` carry the static scans (no `+`/`−` inside
  any equation constant; no depth cap; no re-implemented address grammar).
* `CX-DRF-2` re-finds each enumerated form verbatim at its declared source
  line; with the held sources unreadable it reads INCONCLUSIVE, never clean.

## 4. D14 divergence log — everything this artifact adds beyond the source

Per Appendix D's own jacket: declared *derivative* · visibly separate from the
decoding · adds **no** L1 symbol, **no** decoding operation, **no** sixth
corruption code · alters no invariant line. Each entry: what was added, its
source anchor, and its resolution.

| # | Addition | Anchor | Resolution |
|---|---|---|---|
| D-1 | `step.py` — the Stepper protocol, `StepSession`, `run_session` | §3.6 "Surfaces may add behavioral, interface, and domain layers — visibly separate from the decoding" | Interface layer; the driver's loop is untouched — the runner calls it |
| D-2 | The step trail (TRAIL_VERSION 1, the 21-field line schema, `prev_line_sha256`) | D12's "the formation trail must record what the context decoded to, not the context itself" (commission §5.2) | Observation layer, references only; integrity chain carries no gate authority; never merged with `gates.jsonl` |
| D-3 | `SURFACE_CONTRACT` v1 — the concrete surface grammar (`⟦SURFACE v1⟧` … `⟦END SURFACE⟧`, the section lines, SLOTS/TRACE/TRAIL/LENSES) | Codex §3.6 (the five required things, verbatim) | The five required sections are §3.1/§3.2/§3.3/§3.4/§1.9 verbatim; the line grammar is a versioned declaration P4b's bundles are written against |
| D-4 | `EQUATION_FORMS` — the enumerated byte forms with source + sha256 | commission §3.3 (executed), H-P4a-1 | Enumerates the source's own forms, never folds; the `(public form)` / `(constitutional form)` labels are stored as labels, never part of the string; each entry carries both the per-form sha and the extracted source-line sha |
| D-5 | `SYMBOL_TABLE` / `SYMBOL_ALIASES` / `CORRUPTION_FAILURES` / `CREATIVE_LINE` — the verbatim data tables | Codex §1.9, §2.8, §1.7 | Data, copied verbatim; the U+2032/U+22C2 spellings are recorded as aliases of the §1.9 symbols, never folded |
| D-6 | The static AST scans (depth caps, sixth codes, re-implemented address grammar, signs inside equation constants) | commission §3.7 lessons 3-4 | Mechanical; by `ast.Name`/`ast.Compare`/`ast.Constant`, never by text search; the scan patterns are built so they cannot flag themselves |
| D-7 | `DC-DECODE` / `DC-COMPILE` | D12 (his word) + Codex §3.2/§3.3 | Derived check items, separately numbered — they cannot drift R1–R13 |
| D-8 | `DC-AUTH-1` / `DC-AUTH-2` — the two K3 checks, permanent INCONCLUSIVE | Codex §2.2/§2.5 success criteria (his decision: the click is the human's) | Derived check items; the reason is stated at the site; no code path can emit PASS for them |
| D-9 | The three hook pairs in `driver.py` + `attach_stepper` + `_next_action` | commission §4.3 | Extends in place; `stepper=None` executes none of it; `next` is recomputed from a fresh replay after each step (lesson 8) |
| D-10 | `instrument.last_arrangement()` — the read-only capture of the label resolution the walk already performs | commission C1.2 ("stepping changes observation, never behaviour") | Adds zero socket calls; nothing else in `instrument.py` changes |
| D-11 | The `on_fail` policy (`"stop"` default; `"continue"` override recorded in the trail line) | commission C2.3 | Session policy, recorded in the line, never silent |
| D-12 | The runner's attest channel and interactive Enter | commission §4.2, K4 | The human's act is passed through a caller-supplied provider — the runner never fabricates one; a keypress is never an attestation |
| D-13 | `R11`'s reference shapes: scheme-prefixed locator `^[a-z][a-z0-9_.+-]*:[^\s]{1,200}$` OR a bare 64-hex fingerprint hash | commission §3.7 lesson 9 + R11's own "fingerprint hashes invariant only" | The live plant's `payload_ref` is a bare digest — a fingerprint hash — so both shapes are lawful; §4.7.5 forbids content, not a non-digest scheme |
| D-14 | The seven new fixtures (lawful surface, paraphrased equation, sixth code, missing-∞0′-V, 3+1 cell, full stepped trail, torn trail) | commission §9.6 | Test apparatus; each declares its claim; the trail fixture is a snapshot of one real session |

The four derived check items are numbered `DC-…` — the source's own `R1–R13`
are untouched and unrenumbered (K6).

## 5. Holds — H-P4a-1 … H-P4a-7, each with my proposal

* **H-P4a-1 (two authoritative byte forms + the labelled public form).**
  Proposal: `EQUATION_FORMS` enumerates both authoritative forms per phase
  (spaced reading form and compact Block form, source + sha256 each) and, for
  V only, the third labelled `public form` — all three accepted, all compared
  by bytes, never normalised. Anything outside the table is a paraphrase →
  FAIL naming the first differing codepoint. If Amihai names ONE canonical
  byte string, the table becomes one row per phase and the FAILs follow the
  single row. Amihai's to settle.
* **H-P4a-2 (the address word convention).** Proposal: the convention is a
  declared parameter (the walker's `COURSE`/`DESK_ADDRESSES` data — one place
  to change); no logic in `step.py`/`conformance.py`/`surface.py` derives
  depth arithmetic from the address string (the checks read the recorded zoom
  fields). His word settles the meaning; the code does not need it to run.
* **H-P4a-3 (the signed path cannot live in the attested `address` field).**
  Proposal: the step event carries the signed move in its own fields
  (`zoom.op`, `zoom.sign`, `zoom.letter`); the ledger `address` keeps the bare
  node word; B0 stays untouched.
* **H-P4a-4 (no desk constituted → cell checks cannot pass here).**
  Proposal: INCONCLUSIVE is the correct live verdict, stated with its reason;
  nothing fabricates a bundle; P4b's desk bundles are what turn these items
  into PASS.
* **H-P4a-5 (`block_version` is still `""`).** Proposal: kept `""`, kept in
  the `turn_key` (the attested formula); the limit is stated, no identity is
  invented.
* **H-P4a-6 (`agent_prompted` is schema-only and inert).** Proposal: unchanged
  — `prompt_desk` discards it and the answer comes from the fenced
  `pane.wait_for_output` (the write-response shapes remain the fixture's
  declared claims).
* **H-P4a-7 (the mode's name is Amihai's).** Proposal: `step` is a working
  handle only; no display name enters logic or the trail schema (the
  `STEP_KINDS` descriptions are presentation strings, renamable).

## 6. Assumptions I could not verify (stated, not hidden)

1. `PLAN-ADDENDUM-2026-08-27.md` is **not present on the box**; its §B and
   §E.8 are known only from the commission's quotes. H-P4a-7's naming hold
   rests on that quote.
2. The verifier's pack's per-twin expected FAIL sets are not visible to me;
   my item → defect mapping is the faithful reading, documented per item
   above (e.g. a V closing without `∞0′` fails `R8` + `CX-SYN-6` +
   `AD-SEM-3` + `R2` — the source states the rule three times, so all three
   mirrors fail; a refused out-of-order attempt fails nothing — the guard
   held, and the walk must not stop on it).
3. The pack's cell fixtures' surface format is unknown; the parser reads only
   the declared `SURFACE_CONTRACT` v1 — anything else parses `absent` and the
   dependent checks read INCONCLUSIVE (never a guessed PASS).
4. The pack's torn-trail fixture's exact bytes are unknown; my rule mirrors
   B0's kill-9 tolerance: an unparseable trailing fragment is DAMAGED, a
   complete final line missing only its `\n` is valid.
5. Whether the pack's session-verdict formula includes the two DC-AUTH items;
   mine does — so a clean session reads INCONCLUSIVE listing them (a machine
   can never report a fully clean session; that is K3's point).
6. The live Pi state beyond the read-only observations made (settings file
   exactly `{"lastChangelogVersion": "0.84.2"}`, no skills directory) — the
   lens reads it, nothing writes it.
7. The herdr write-response shapes remain the declared claims (H-B2-4
   carried); the live socket is never opened by this artifact.

## 7. What the fixtures claim (each carries its claim inside itself)

* `lawful_desk_surface.json` — a lawful G surface; parses lawful, slots
  referenced only, decoding verbatim, lenses targeting `Y` (parent first).
* `paraphrased_equation_surface.json` — Q's block equation carries a double
  space; no enumerated form matches; `AD-SYN-2` FAILs naming U+0020.
* `sixth_corruption_code_surface.json` — announces `L6`; `AD-SYN-5` FAILs.
* `missing_infinity_zero_prime_v.json` — a V that closes with B and B″ but no
  `∞0′`; at a V step `R8`, `CX-SYN-6`, `AD-SEM-3`, `R2` FAIL by id.
* `three_plus_one_cell.json` — arrangement S G Q P (no V); `AD-SYN-1` FAILs
  naming the missing corner.
* `full_stepped_session_trail.jsonl` — one real stepped y→z→a→b session (10
  lines, boot → G proposed → advance refused → … → advance complete), chain
  intact; a snapshot of one session, fixed `at` clock, `session_id`
  `feedfacebeef`.
* `torn_last_line_trail.jsonl` — two complete lines + a truncated fragment of
  a third; `read_trail` reads DAMAGED (line 2 unparseable, its sha and byte
  count in the damage report).
