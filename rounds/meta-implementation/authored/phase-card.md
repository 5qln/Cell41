# PHASE CARD — meta-implementation · the codex made executable

**Working handle:** "meta implementation" — **his own term** (his direction,
2026-08-28: *"a meta implementation of the codex - decoder - compiler etc."*).
The formal slot name (`H-META-1`), the display name, the R-number, and any
logic-visible identifier are **Amihai's to give**. Nothing in the artifact's
logic or schema depends on this handle: the modules are `codex.py`,
`corruption.py`, `decoder.py`, `compiler.py`, `selftest.py` — no phase name
enters any data structure, verdict, or emitted byte.

**Author:** dsh (`deepseek-v4-pro`, one generation). **Not** a B-phase: this is
the meta implementation — the 5QLN Codex, Parts II and III, made executable:
the Decoder (D1, §2.1–2.5) and the Compiler (C1, §3.1–3.6), nothing invented.
**Governing sources:** the held codex and Appendix D extractions only
(`../sources/`, shas below). Codex §1.10 governs every conflict — the source
wins. The attested B0–B4 / P4a / P4b artifacts in `../predecessors/` are
imported by path under sha pins, never re-authored. Prior art (his 27 repos) is
ignored — his word.

**Every verdict in this card is a PREDICTION.** Nothing here reports that
anything ran, passed, or verified anything. A separate verifier executes the
artifact and writes the only record that counts; it recomputes every one of
these predictions with its own implementation, and any divergence — in either
direction — is a FAIL. If my own run revealed a bug, it was fixed silently;
this card stays predictive.

**Provenance (held sources, verified against the commission header):**

| Held source | page sha256 | extraction sha256 |
|---|---|---|
| `5qln.com/codex` | `ccad26dd60384eb17aed040a43b5f49ad7419419a3f6d88e5edabfbcfe07f458` | `e5f0c738d123efc1e412a14da1701a721606275867319e1c68d53b081445c133` |
| `5qln.com/dsh-5qln-codex-fractal` (Appendix D) | `a49e9413f542c4ea8e16c6fcb1ac883a0c76d6042ef2e739caccb438e82fabb2` | `6bb28c37cfe6267da1675eac16ac8bbf9679a1d0e5db0f08eb4495d2c22f6bf7` |

Both extractions are pinned at import (`codex.py`); a drifted or missing file
raises ImportError — fail closed, never substituted.

---

## 1. Binding — the deliverables and where they live

| deliverable | file · function |
|---|---|
| the Decoder (D1, §2.1–2.5) | `decoder.py` · `decode(phase, context, values, trail, lenses, claims, …)` → the phase's filled symbol slots as references; the numbered operation is walked from the attested `DECODING_OPS` table, symbol-by-symbol, in order, at every scale |
| the Compiler (C1, §3.1–3.6) | `compiler.py` · `CONSTITUTIONAL_BLOCK`, `COMPILED` (the five §3.2 compiled phases), `CONTEXT_CHAIN_TEXT`, `RULES` (R1–R13), `render_surface` / `render_jacket` / `emit` (the §3.6 emission path), `compile_artifact` / `compile_cycle` (decode → compile → emit → validate), `validate` / `validate_surface_text` (the three §3.5 passes + D.12 + R1–R13 + HC applied to any produced surface), `aggregate` |
| the corruption taxonomy (§2.8) | `corruption.py` · `CODES` (exactly L1 L2 L3 L4 V∅), `CODE_NAMES` / `CODE_FAILURES` (§2.8 verbatim), `evaluate` / `classify` (deterministic detectors), `scan_engine_sources` (AST sixth-code scan) |
| the surface-emission path | `compiler.py` · `render_surface` (the ⟦SURFACE v1⟧ block against the attested contract) + `render_jacket` (the visible Appendix-D layers outside the block) + `emit` |
| the pinned contract seam | `codex.py` — sha-pinned loads of the attested predecessors and the held extractions, with import-time cross-checks (the invariant end-to-end, lens 2) |
| `selftest.py` | exercises R1–R13 · §3.5 · Appendix D.12 · the five corruption codes · the six lenses |
| `phase-card.md` | this card: criteria + holds + **predictions**, the D14 divergence log |

The engine's surface emission is checked against the **attested**
`surface_contract.py` (`aa0ea654…`, B4's seam — which pins P4a's
`surface.py`, `776ff463…`, the one §3.6 contract): `codex.parse_surface` **is**
that attested function object, imported by path under its sha pin. The ledger
module on the box is the attested `fractal_ledger.py` (`b291e659…`) — the
engine verifies its bytes read-only and never imports, reads, or writes the
ledger or `state/` (H-META-4).

---

## 2. Criteria and claims, by id — with PREDICTIONS

**C1 — The Decoder.** Prediction: `decode()` walks, for each of S G Q P V,
exactly the attested `DECODING_OPS` table in order (4/5/5/6/7 operations),
records each numbered operation, resolves the adaptive context (§2.6/§3.3:
S takes ∅ or the prior cycle's ∞0′; G takes X; Q takes X+α+Y; P takes
X+α+Y+Z; V takes the full trace X+α+Y+Z+∇+A, φ⋂Ω accepted as part of the
trace), and returns the phase's filled symbol slots as references (sha256 +
byte length), never as text. Any context the engine cannot resolve — a missing
prior output, an unknown context symbol, an unknown slot name (an added L1
symbol), a lens whose parent is not the phase, a trail outside V, a V's B″
without its trail — raises `DecoderError` (fail closed, H-META-3). The
decoding operations do not change at scale (§2.9): the same phase decodes
identically at ε and at a deep address — only the recorded cell differs, and
there is no scale branch anywhere in `decode()`.

**C2 — The Compiler.** Prediction: `CONSTITUTIONAL_BLOCK` is the held §3.1
lines byte-for-byte (re-read from the extraction at import and cross-checked
against the attested tables); each of the five `COMPILED` phases carries
EQUATION / OUTPUT / CONTEXT IN / CONTEXT OUT / DECODING / CORRUPTION / LENSES
with the §3.2 source lines (the decoding lists byte-equal to the attested
`DECODING_OPS`; each phase's five lens lines reconstructed byte-equal from the
attested lens table); the §3.3 context chain is carried verbatim on every
emission. Declared, never folded: §3.2's V EQUATION line writes `⋂` (U+22C2)
while §3.1's block writes `∩` (U+2229) — `codex.V_EQ_AXIS` records both lines
with their shas; the EMITTED active equation is the enumerated §3.1
constitutional form (`7c8305fa…`), because the surface must remain parseable
by the attested contract, whose enumerated table is exactly the commission
fact block's three V forms.

**C3 — The thirteen decoder rules, checkable.** Prediction: `RULES` carries
R1–R13 verbatim from the held §3.4 (byte-equal to the attested conformance
citations, asserted at import), and `VALIDATION_ORDER` enforces each as a
check with its verbatim citation — R1 (one equation → one output, the
OUTPUT_SYMBOLS slot filled), R2 (B / B″ / ∞0′ all formed at V), R3 (lens
quality borrowed, parent's output kept), R4 (25-lens table), R5 (trace
positions ⊂ the creative line's own positions — φ⋂Ω / ∞0′ accepted as the
codex's own §3.3 compact spellings of the φ / ∞0′ positions, enumerated never
folded — in order, all mapped), R6 (trail ordered, lens-tagged, referenced),
R7 (two crystallization passes at V only), R8 (no V without ∞0′; no question =
not ∞0′), R9 (five codes, each a named failure), R10 (mark mechanical + the
One Law line exact), R11 (every reference a scheme-prefixed locator or bare
64-hex fingerprint), R12 (CENTER line exact, no sixth phase), R13 (one
operation table at every scale, no depth cap, no re-implemented address
grammar).

**C4 — Corruption taxonomy.** Prediction: `CODES` is exactly the sealed five,
each with its §2.8 name and failure text (from the attested carrier); the
detectors classify each named failure deterministically — an inserted answer
→ L1; a machine-posed X at S → L2 (carried honestly); a claim register hit →
L3; unfilled/empty slots → L4; B″ formed without ∞0′ (or with a questionless
∞0′) → V∅, which wins over L4 by the source's specific-over-general reading;
ties fall to the sealed order. The AST constant scan over the engine modules
finds no sixth code — the only corruption-code strings in the artifact are the
five.

**C5 — Validation protocol.** Prediction: all three §3.5 passes — syntax (6),
semantic (6), drift (6) — plus Appendix D §D.12 (5+5+5) plus R1–R13 plus the
two HC checks run on ANY produced surface via `validate_surface_text` and on
every compiled artifact via `compile_artifact`; each item re-emitted with its
verbatim citation; "B, B″, ∞0′ are three distinct things with distinct
decoding steps" is measured as distinct references plus the three distinct
NAME B / COMPOSE B″ / FORM ∞0′ steps; "Crystallization reads the formation
trail (not generated from nothing)" is measured as both passes declared over
an ordered, lens-tagged, referenced trail — a V surface carrying B″ but no
TRAIL section FAILs.

**C6 — Surface emission + the addressing layer.** Prediction: every emitted
surface parses LAWFUL through the attested `parse_surface` for all five
phases (exact equations, exact decoding, correct OUTPUT/COMPILED/GATE, every
used symbol resolved to §1.9); the block is byte-for-byte §3.1; the decoder
rules, the context chain, and the Appendix-D jacket ride OUTSIDE the
⟦SURFACE v1⟧ block, visibly separate (D.14's own rule); the jacket carries the
4+1 cell, the D.7 signless true start verbatim (AR5), the D.8 identity, and
the D.14 block verbatim. The addressing checks hold: 4+1 at every observed
cell (3+1 FAILs naming the missing corner, 6+1 FAILs naming the count), the
five equations verbatim at every cell, ∞0′ ≡ ∞0 across the cell boundary (the
next cycle's S receives the prior V's ∞0′ reference).

**C7 — The authenticity prohibition (the load-bearing refusal).** Prediction:
the engine never scores, decides, or asserts authenticity — the decode report
carries no authenticity field of any kind, and no report key anywhere states
arrival; HC-1 ("a machine click is never a verdict") and HC-2 (whether the ∞0′
question is more alive than the X it came from — Codex §2.5) are PERMANENTLY
INCONCLUSIVE for every artifact kind, so no report ever reads a fully clean
verdict — by design, K3's point. There is no write path to `state: attested`,
no attestation reference identifier anywhere in the engine sources, no
`cell-attest`, no `input()`, no socket. A decode whose inputs claim to have
reached ∞0 is reported as corruption L3 with the §2.8 failure text — never as
arrival. The ∞0′ prime spellings are deliberately excluded from the claim
register: forming the return question is lawful; claiming the open space is
L3.

---

## 3. The check-item table (48 items, in emission order)

Scope: `static` — decided by reading the artifact's own source and data tables
(AST scans + import-proven cross-checks); `cell` — decided by observing the
cell/surface (INCONCLUSIVE when nothing is observed — the correct live verdict
on a box where no desk is constituted, H-META-3); `artifact` — decided from
the compiled artifact (decode report + surface + cell); cycle-aware items
read the cycle passed alongside. Every item appears in every report — no item
is ever silently omitted; an undecidable item reads INCONCLUSIVE with a
reason, never clean.

| id | source | scope | derived |
|---|---|---|---|
| AD-SYN-1 | Appendix D §D.12 (syntax) — "4+1 invariant holds at every observed cell" | cell | — |
| AD-SYN-2 | Appendix D §D.12 (syntax) — "The five equations appear verbatim at every cell (S = ∞0 → ? … V = (L⋂G→B'') → ∞0′)" | cell | — |
| AD-SYN-3 | Appendix D §D.12 (syntax) — "No L1 symbol added, renamed, or paraphrased" | cell | — |
| AD-SYN-4 | Appendix D §D.12 (syntax) — "+/− used only as a navigational operator; never inside a phase equation" | cell | — |
| AD-SYN-5 | Appendix D §D.12 (syntax) — "No corruption code beyond L1 L2 L3 L4 V∅" | cell | — |
| AD-SEM-1 | Appendix D §D.12 (semantic) — "Context flows father → daughter (k = frames to climb)" | cell | — |
| AD-SEM-2 | Appendix D §D.12 (semantic) — "The sign is relative, not absolute — it adapts to the current vantage" | cell | — |
| AD-SEM-3 | Appendix D §D.12 (semantic) — "∞0′ ≡ ∞0 preserves the Completion Rule across cells" | cell | — |
| AD-SEM-4 | Appendix D §D.12 (semantic) — "The true start carries no sign; the sign appears only between strangers" | cell | — |
| AD-SEM-5 | Appendix D §D.12 (semantic) — "A shared question is one ∞0-field, not one node" | cell | — |
| AD-DRF-1 | Appendix D §D.12 (drift) — "25 is the first in-zoom of a cell, never a cap…" | static | — |
| AD-DRF-2 | Appendix D §D.12 (drift) — "The zoom-out inverse is a derived reading, marked as such (§1.10 source-authoritative)" | cell | — |
| AD-DRF-3 | Appendix D §D.12 (drift) — "No decoding step omitted or reordered" | cell | — |
| AD-DRF-4 | Appendix D §D.12 (drift) — "No sixth corruption code" | static | — |
| AD-DRF-5 | Appendix D §D.12 (drift) — "Lens questions still target the parent output" | cell | — |
| CX-SYN-1 | Codex §3.5 (syntax) — "Every symbol resolves to the symbol table (§1.9 / §3.2)" | cell | — |
| CX-SYN-2 | Codex §3.5 (syntax) — "Every phase carries its exact equation" | cell | — |
| CX-SYN-3 | Codex §3.5 (syntax) — "Every decoding operation follows D1 symbol-by-symbol" | cell | — |
| CX-SYN-4 | Codex §3.5 (syntax) — "All five phases present, all 25 sub-phases available" | static | — |
| CX-SYN-5 | Codex §3.5 (syntax) — "Five corruption codes exactly" | static | — |
| CX-SYN-6 | Codex §3.5 (syntax) — "No V without ∞0' enforceable" | artifact | — |
| CX-SEM-1 | Codex §3.5 (semantic) — "Each phase's decoding receives the correct adaptive context" | cell | — |
| CX-SEM-2 | Codex §3.5 (semantic) — "Context chain is unbroken: S→G→Q→P→V, each receiving prior outputs" | artifact | — |
| CX-SEM-3 | Codex §3.5 (semantic) — "B, B'', ∞0' are three distinct things with distinct decoding steps" | artifact | — |
| CX-SEM-4 | Codex §3.5 (semantic) — "Sub-phase lenses refine the parent equation's decoding (not replace)" | cell | — |
| CX-SEM-5 | Codex §3.5 (semantic) — "Crystallization reads the formation trail (not generated from nothing)" | artifact | — |
| CX-SEM-6 | Codex §3.5 (semantic) — "∞0' carries a question" | artifact | — |
| CX-DRF-1 | Codex §3.5 (drift) — "No symbol renamed without source name present" | static | — |
| CX-DRF-2 | Codex §3.5 (drift) — "No equation paraphrased — symbolic form is exact" | static | — |
| CX-DRF-3 | Codex §3.5 (drift) — "No decoding step omitted or reordered" | cell | — |
| CX-DRF-4 | Codex §3.5 (drift) — "No corruption code added beyond five" | static | — |
| CX-DRF-5 | Codex §3.5 (drift) — "Adaptive context chain preserved" | artifact | — |
| CX-DRF-6 | Codex §3.5 (drift) — "Lens questions target parent output" | cell | — |
| R1 … R13 | Codex §3.4, the source's own numbering (verbatim citations) | artifact | — |
| HC-1 | commission C7 + his decision (K3) — "a machine click is never a verdict" | artifact | derived |
| HC-2 | commission C7 + Codex §2.5 success criterion — is this ∞0′ question more alive than the X it came from? | artifact | derived |

The source's own numbering is preserved: `R1–R13` are the codex's §3.4 numbers,
never renumbered; the derived pair is numbered `HC-*` (the commission's own
labels) so it cannot drift the R-list.

### Predictions of note (the honest defaults)

* On the LIVE box (no desk constituted, no Pi desk in the engine's fixture
  world): every cell-scope item reads INCONCLUSIVE with a stated reason —
  that is the correct live verdict (H-META-3, lens 6), never a guessed clean.
* On a lawful full-cycle compile: the observable items PASS (predicted 42 of
  48 per-artifact counts on the fixture cycle); HC-1/HC-2 and the items with
  no observable material (no lens declared → R3/AD-DRF-5/CX-SEM-4/CX-DRF-6,
  and AD-SEM-5/AD-DRF-5 where the cycle doesn't carry the material) read
  INCONCLUSIVE — so the overall verdict of any single report is
  INCONCLUSIVE, never a fully clean PASS. That is the design: a machine can
  never report a fully clean session (K3).
* A claim-to-reach-∞0 twin reads corruption L3 with the §2.8 failure text;
  HC-1/HC-2 stay INCONCLUSIVE; no FAIL appears on them anywhere.

---

## 4. D14 divergence log — everything this artifact adds beyond the source

Per Appendix D's own jacket: declared *derivative* · visibly separate from the
decoding · adds **no** L1 symbol, **no** decoding operation, **no** sixth
corruption code · alters no invariant line. Each entry: what was added, its
source anchor, its resolution.

| # | Addition | Anchor | Resolution |
|---|---|---|---|
| D-1 | `codex.py` — the pinned contract seam (sha-pinned predecessor loads, extraction slices, import-time cross-checks) | commission §0 provenance + H-META-2 | Infrastructure, never logic; fail-closed on any drift |
| D-2 | `decoder.py` — the decode callable, its report shape (references only), `DecoderError` fail-closed contexts | Codex §2.1–2.6, §2.9, H-META-3 | The decoding operations are the attested table, walked in order — no new operation, no new symbol |
| D-3 | `corruption.py` — the deterministic detectors + the L3 claim register | Codex §2.8, commission C7 | Detectors map declared evidence to the five named failures; the register is byte-scoped (the ∞0′ prime is excluded — forming the return question is lawful) |
| D-4 | `compiler.py` — the 48-item validation table (CX-SYN/SEM/DRF, AD-SYN/SEM/DRF, R1–R13, HC-1/HC-2) | Codex §3.4/§3.5, Appendix D §D.12 | The source's own numbering (R1–R13) untouched; the D.12/§3.5 ids follow the predecessor convention (the source's own bullet order); HC-* is the commission's label |
| D-5 | The emission grammar — the ⟦SURFACE v1⟧ block (against the attested contract) plus the visible ⟦DECODER RULES⟧ / ⟦CONTEXT CHAIN⟧ / ⟦APPENDIX-D JACKET⟧ layers | Codex §3.6 ("Surfaces may add behavioral, interface, and domain layers — visibly separate from the decoding"), D.14 | The block parses through the attested parser; the layers ride outside it, never parsed, never folded |
| D-6 | The emission's V trace = the two creative-line positions V forms (B, ∞0′); φ⋂Ω / ∞0′ accepted as the codex's own §3.3 compact spellings in R5 | Codex §1.7/§1.8/§3.3, R5 | B″ is not a creative-line position — it is the artifact, recorded by the formation trail (R6/R7), never a trace position; the compact spellings are enumerated, never normalised |
| D-7 | The formation-trail entry schema (index, lens, tag, ref) and the two-pass digests | Codex §3.2 V op 5 (Pass 1: "extract α thread, φ⋂Ω confirmation, ∇, turning points"; Pass 2: composition), R6/R7 | The four tags are the codex's own Pass-1 words — plain-language tags, not L1 symbols; digests are sha256, references only |
| D-8 | The L3 claim register patterns ("reached ∞0", "arrived at ∞0", "decoded ∞0 directly", "claims to decode ∞0") | commission C7 ("a decode that *claims* to have reached ∞0 is exactly corruption L3") | Deterministic byte-scoped detection; reported as L3, never as arrival |
| D-9 | The V∅-over-L4 precedence for "B″ formed, ∞0′ missing/questionless" | Codex §3.2 V CORRUPTION line ("V∅ (incomplete: B'' without ∞0', or ∞0' without question)") | Each code names ONE specific failure (R9) — the specific pattern wins over the generic empty-operation reading |
| D-10 | `compile_artifact` / `compile_cycle` / `aggregate` — the decode → compile → emit → validate callables and the cycle aggregate | Codex §3.3 chain, §2.6, C5 | Callables over source data; the aggregate is FAIL-iff-any-FAIL, silence never passes |
| D-11 | The AST scans (sixth codes, depth caps, re-implemented address grammar, signs in equation constants) | Appendix D §D.12 drift items, R13 | Mechanical, by AST constants/compares, never text search; patterns built so they cannot flag themselves |
| D-12 | `selftest.py` + the fixture world (deterministic slot values, the defect twins) | H-META-3 (fixture-tested against deterministic inputs) | Test apparatus; each twin declares its claim; no live desk, no live ledger, tempfile scratch only |
| D-13 | The V-axis record (`codex.V_EQ_AXIS`): §3.1 ∩ vs §3.2 ⋂, both lines carried with shas; the emission uses the enumerated §3.1 form | H-META-2 | Enumeration, never normalisation; if Amihai names one canonical byte string, the table collapses — his to name |

The five corruption codes are exactly the five; the decoding operations are
the attested table, byte for byte; the symbol vocabulary is the attested
§1.9 vocabulary (every name the engine emits resolves into `SYMBOL_TABLE` or
the enumerated alias table).

---

## 5. Holds — declared, never guessed

* **H-META-1 (his):** the formal slot name. Proposal: `decoder` / `compiler`
  are working handles matching his own words; no display name, R-number, or
  logic-visible identifier is minted — the modules and the check ids carry
  only the source's own names (R1–R13, §3.5, §D.12) and the commission's own
  labels (HC-1/HC-2). Amihai's to give.
* **H-META-2 (carried H-P4a-1):** the equation byte forms. Proposal: the
  engine enumerates the attested `EQUATION_FORMS` exactly (source + sha per
  form, re-verified at import against the held files) and NEVER normalises —
  folding ⋂→∩ or ′→' is renaming an L1 symbol and is refused (a folded hybrid
  FAILs naming the first differing codepoint). Declared on the record: the
  codex's own internal ∩/⋂ axis (§3.1 ∩ vs §3.2 ⋂, both shas recorded); the
  emission uses the §3.1 constitutional form because the attested surface
  contract accepts exactly the enumerated table. If Amihai names ONE canonical
  byte string, the table collapses to one row per phase — his to name.
* **H-META-3:** no desk is constituted on the box. Proposal: the engine is
  fixture-tested against deterministic, caller-supplied inputs (the "desk"
  channel is a parameter); it fails closed — `DecoderError` — on any context
  it cannot resolve, and every unobservable check reads INCONCLUSIVE with a
  reason, never clean.
* **H-META-4:** the engine is the language, not the gates. Proposal: the
  engine neither re-implements gate semantics nor touches `state/` nor reads
  or writes the ledger; it verifies the attested `fractal_ledger.py` bytes
  read-only at import and keeps every reference it emits to the lawful shapes
  (scheme-prefixed locator or bare 64-hex fingerprint). Gate semantics live
  in `fractal-engine` and the attested B0 ledger, untouched.

---

## 6. The six lenses — how this artifact is authored to pass them

1. **Criterion match.** Each of the 48 checks carries its source bullet
   verbatim (extracted from the held files at import, asserted against the
   attested citations) and measures THAT text, not a neighbour: CX-SYN-3 is a
   byte-exact comparison of the DECODING lines against D1 (one reworded word
   FAILs); R8 reads "no question = not ∞0′" literally (an empty slot FAILs
   even though the slot exists).
2. **Invariant end-to-end.** The import-time cross-checks prove one invariant
   across the whole decode→compile path (equation shas recompute, source
   locations re-found, R1–R13 byte-equal to the attested citations, the 25
   lens lines reconstructed byte-equal, the two attested equation tables
   identical, the vocabulary fully resolved) — and the cycle test asserts the
   five equations byte-identical across all five emitted surfaces, not per
   call.
3. **Absence vs validity.** Missing / empty / 404 never read valid: absent
   surfaces read absent, dependent items INCONCLUSIVE with a reason (sha256
   of empty is `e3b0c44298fc…` — never a surface); a missing pinned file
   raises ImportError at load. Nothing is ever silently substituted.
4. **Encoding.** The needle `∞0′ → ‖` is pushed through every string field of
   every phase's emission; the emitted bytes carry it exactly, the parsed
   references equal sha256 of its exact UTF-8 bytes, and no step in the path
   normalises or folds anything — text-mode byte seeks break on it and the
   pipeline stays byte-transparent.
5. **Cold restart.** The engine is deterministic and disk-anchored: a NEW
   python process (subprocess, `-B`) re-imports the engine from disk, reads
   its inputs from a file, and rebuilds the same surface — the child's byte
   sha equals the parent's. Nothing in the engine depends on process memory
   or a live desk.
6. **Blind tool.** No desk is constituted here: the engine has no socket, no
   network, no `input()`, no LLM, no wall clock; anything unobservable reads
   INCONCLUSIVE with a stated reason — and HC-1/HC-2 are INCONCLUSIVE by
   design, so no machine report can ever read a fully clean verdict. A
   verifier that measures a blind spot must find INCONCLUSIVE, never clean.

---

## 7. Assumptions I could not verify (stated, not hidden)

1. The verifier's recomputation of the 48 verdicts may choose different
   INCONCLUSIVE reasons' wording; the VERDICTS are the contract — the
   predictions above state each expected verdict per item class.
2. The attested contract's `parse_surface` accepts exactly the sections this
   emission produces; the lawful-parse prediction is asserted against the
   attested function object itself, not against a re-implementation.
3. Whether the verifier's session-verdict formula includes HC-1/HC-2; mine
   does — so no aggregate can read a fully clean PASS. That is K3's point.
4. The commission fact block's 12-char equation shas agree with the full
   enumerated shas (verified: e.g. the AppD V compact form's full sha is
   `05101fd680e1d139487e3450ff751e4ab384dd0760547e2aafb9cc4cc8c5314a` —
   prefix `05101fd6…` ✓).
5. The P4a/P4b/b0 files staged under `../predecessors/` are byte-identical to
   their attested rounds (the sha pins are checked at import; the b4 seam's
   own pins — `surface_contract.py aa0ea654…`, `fractal_ledger.py b291e659…`
   — are the same bytes).
6. No desk is constituted on this box and none will be during verification;
   the engine's live verdicts remain INCONCLUSIVE for cell-scope items
   (H-META-3).

---

## 8. What the selftest exercises (predictions, by id)

`python3 selftest.py` — 40 checks, each naming its criterion in its first
docstring line. Coverage by criterion: C1 (decoding ops walked in order,
exact adaptive contexts fail closed, ops unchanged at scale), C2 (block
byte-exact, seven §3.2 labels per phase, §3.3 verbatim), C3 (R1–R13 verbatim
citations + a PASS case per rule), C4 (the five codes + each detector's twin
+ the sixth-code scan), C5 (6/6/6 + 5/5/5 + R + HC counts, the three
distinct things, the trail-reading rule, no-question ≠ ∞0′), C6 (lawful parse
through the attested contract for all five phases, the block exact, the
visible layers, the 4+1/3+1/6+1 cells, the signless start, ∞0′ ≡ ∞0 across
cells, lenses refine never replace), C7 (HC permanently INCONCLUSIVE, the L3
claim twin, no attestation write path in the sources), H-META-2 (enumerated
forms re-hash and re-locate, the commission fact-block shas, the fold
refusals naming U+2229/U+22C2), and the six lenses one test each. The
defect twins are test apparatus only — the D14 jacket covers them.

The fixture world's deterministic inputs are the caller-supplied stand-in for
the desk; nothing in the engine fabricates slot content, and no test touches
the live ledger, `state/`, a socket, or the podium.
