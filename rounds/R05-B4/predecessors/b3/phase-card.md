# PHASE CARD — R04-B3 · the descent (working handle)

**Round:** `R04 · B3` — the slot the attested appendix opened ("the descent"). The phase name and
slot are **Amihai's to name** — this card uses the build-spine slot `B3` only until he names it
(H-B3-4-adjacent: no display name appears in any record, schema, or code path).
**Author:** dsh (`deepseek-v4-pro`, one generation). **Verifier:** Hermes profile `herdr`,
separately, against a pack written before it judges anything. `builder ≠ verifier`.
**Governing sources:** the commission (`./commission.md`), the Codex, Appendix D (ATTESTED
2026-08-29), PRD, REQUIREMENTS (held at `../sources/`). **Codex §1.10 governs every conflict —
the source wins.**

**Every verdict in this card is a PREDICTION.** Nothing here reports that anything ran, passed,
or verified anything. A separate verifier executes the artifact and writes the only record that
counts; it recomputes every verdict with its own implementation, and any divergence — in either
direction — is a FAIL. If my own authoring-time run revealed a bug, it was fixed silently; this
card stays predictive.

---

## 1. The load-bearing hold — H-B3-2 (the letter-order stays open)

D.2's definition line reads the word **inner-first** (`XY := X within Y` — the first letter is
the innermost phase); D.3's append chain (`S → SG → SGQ`) and D.6's worked case
(`ε → PQP = −P −Q −P`) read it **outer-first**. The two readings disagree about which end is
deep, and the commission makes the answer **his to confirm, later**.

The convention therefore is a **DECLARED PARAMETER**, never a decision: P4b already carries
`WORD_ORDER = "inner_first"` in its attested `grammar.py`, and the descent imports it — it does
not hard-code either convention, and **no logic depends on which end is deep**. The
letter-order touches the descent in exactly **two spots**, both delegating to the parameter:

| spot | where | what it does |
|---|---|---|
| 1 — the append side | `descent.py:300` | `zoom_in` returns the imported `grammar.seat_address(address, letter)` — P4b's parameterized seat convention, never a literal |
| 2 — the strip side | `descent.py:317` | `zoom_out` carries the only `WORD_ORDER` branch in the file — it strips the deep-end letter, whichever end the parameter says is deep |

Everything else (`deep_letter`, ancestor chains, `path_between`, `apply_signed_path`) is built
from those two primitives alone, so the signed path is **convention-independent** (it records
the descent steps in chronological order; the address carries the convention). Prediction:
flipping `WORD_ORDER` to `"outer_first"` flips the addresses and leaves every mechanism intact —
a one-table change, never a rewrite (the selftest's flip probe exercises exactly this). The two
byte-questions from P4b stay closed: the seal is the numbered 217-byte nine-line block →
`feaa46b4…`, and D.2 is the carried parameter — neither is reopened here.

## 2. Binding — the names this round ships

| binding | real name | where |
|---|---|---|
| `descent_module` | `descent` | `descent.py` — `Descent`, `walk`, `descend`, `guard_pass`, `evaluate_return`, `seat_arrangement`, `read_node` |
| `zoom_in_fn` | `zoom_in` | `descent.py:285` — the append side (spot 1 of H-B3-2) |
| `zoom_out_fn` | `zoom_out` | `descent.py:303` — the strip side (spot 2 of H-B3-2) |
| `signed_path_validator` | `validate_signed_path` | `descent.py` — the AR3 field validator; rejects `-P-Q-P` and `+-G` |
| `signed_path_build` / `apply` | `path_between` / `apply_signed_path` | `descent.py` — built from the zoom primitives alone |
| `axis_fn` | `field_handoff` / `axis_verdict` / `field_bytes` | `descent.py` — byte-exact carry and the three §5.4 verdicts |
| `surface_contract_module` | `surface_contract` | `surface_contract.py` — P4a/P4b's contract read by path, sha-pinned; `DESCENT_SURFACE` declared against it |
| `selftest_module` | `selftest` | `selftest.py` — the author's suite, a hypothesis never a result |
| `fixtures` | `fixtures/` | the five named cases + the byte-pinned expected trees and ledgers |

## 3. Criteria and claims, by id — with PREDICTIONS

**C1 — byte-exact axis inheritance.** Prediction: the 3-deep descent fixture walks ε → Q → PQ →
GPQ with `axis.field` byte-identical from root to leaf — one invariant, compared on the
canonical JSON bytes of the field across the WHOLE descent, never per call (lens 2). The
handoff re-stamps provenance (`anchored → inherited`) and carries the anchor byte-exact; the
field is never empty (an empty anchor is refused). The manufactured-change fixture yields
`MOVING` and a stop-and-surface: the child exists with the drifted field as the world's truth
(the engine never repairs a drift), the stop is logged as a record, and nothing descends past
it — MOVING dominates (PRD §5.4).

**C2 — address append/strip + the signed path split.** Prediction: `zoom_in`/`zoom_out`
round-trip under the declared parameter and under the flipped value; the node record carries
**no address field** (a record storing one is refused — addressing is derived from the
directory, ε = `_`); the signed path is a separate field validated against AR3 — the descent
operator is U+2212 `−` (P4a's `STEP_KINDS` glyph, imported), and the ASCII hyphen is not part
of the notation, so `-P-Q-P` and `+-G` are rejected (no byte normalisation, K2 — and the
rejection is letter-order-independent, as H-B3-2 requires).

**C3 — guard pass at every depth.** Prediction: `guard_pass` runs at every node the walk
visits and reports `GS-L1 · GS-L2 · GS-L3 · GS-L4 · GS-VOID` with citations; each machine-posed
seed honestly carries its L2 signal; a skipped arrow flags L1; a claimed surface outside the
§1.9 vocabulary (checked through P4a's own imported parser) flags L3; an unfilled payload
flags L4; a V with no ∞0′ is REFUSED and the refusal is recorded (B2's refusal keying,
imported). Anything unobservable reads INCONCLUSIVE, never clean (lens 6).

**C4 — the return criterion.** Prediction: `evaluate_return` observes (never fabricates):
an attested V with artifact + ∞0′ → `returned` (references and byte facts, never content);
an unattested V → `held` (the human's click is the only authenticity authority — presence is
reported, genuineness is never judged, commission §6); a V with no ∞0′ → `refused` (V∅) with a
recorded refusal; an attested V missing its artifact → `refused` (half a return is not a
return).

**C5 — TENTATIVE is temporal, never epistemic.** Prediction: every engine-created node is
`tentative: true`; the seed lives in the node's own file (`seed.md`), never on the podium; the
engine has no `question.md` write path at all; a downstream gate whose payload chains to the
tentative seed is REFUSED (the T-R5-02 dependency audit) with the refusal recorded; no
heuristic ever flips `tentative` to false.

**C6 — the gate-fails-to-lock flow.** Prediction: `descend` requires a REAL trigger (the
parent's (address, gate) record held-pending with no attestation), then creates the child
directory, appends the address through the declared convention, seats a full P4b arrangement
(five desks at the child's seat addresses, each instruction block the desk's full-cell bundle
at its own address, four blocks per desk — validated through P4b's own `validate_arrangement`
and `verify_bundle`, status `ok`), and writes the child's seed record.

**C7 — the five invariant commitments, as structural constraints (never a feature, H-B3-4).**
Prediction: (1) no depth constant exists anywhere — the walk's only bound is a
caller-supplied step budget, and a five-deep walk completes; (2) the alphabet is imported data
(P4b's `COURSE`) — no five-letter literal exists in the module and the signed-path letter
class follows the data, so a jump marker can exist beside `{S,G,Q,P,V}`; (3) the walk loop's
only exits are resources (the budget, the descent material, the no-trigger node) and mandated
stops (MOVING / refusal / unobservable) — the return criterion is observed AFTER the loop and
is never a break condition; (4) nothing compares sizes to prune a child — the deeper cell's
bundle is LARGER and accepted; (5) every function takes the address as a parameter, a descent
started at a non-ε cell walks identically, and ε is a coordinate anchor, never a privileged
root (Appendix D.2: no root, no leaf).

### The six lenses, predictively

1. **Criterion match** — the criteria are carried verbatim where they are measured (the §B3
   done-when sentences appear in `descent.py` at the measuring sites), and each selftest check
   names the criterion it measures.
2. **Invariant end-to-end** — the field bytes are one invariant compared across all four
   nodes of the descent at once, and the rebuilt tree + ledger are byte-pinned in
   `fixtures/*/expected/`.
3. **Absence vs validity** — a missing node reads `absent`; an empty node record reads
   `absent` with the empty-sha trap named (e3b0c44298fc… never a valid ref); an empty field is
   refused; a missing ∞0′ is refused.
4. **Encoding** — `∞0′ → ‖` rides the plant question, the artifact and the ∞0′ end to end;
   every JSON is UTF-8 passthrough (`ensure_ascii=False`, the imported canonical forms), and
   no text-mode byte seek exists in the module.
5. **Cold restart** — a NEW process (the suite's one subprocess) rebuilds the same node tree
   and ledger from the static fixture on disk alone, byte-identical to the pins and to the
   first process's rebuild.
6. **Blind tool** — an unobservable parent reads INCONCLUSIVE; a node with unobservable
   evidence reads INCONCLUSIVE; a walk with no fixture world fabricates nothing and ends
   INCONCLUSIVE — never clean (H-B3-1).

## 4. D14 divergence log — everything this artifact adds beyond the source

Per Appendix D's own jacket: declared *derivative* · visibly separate from the decoding ·
adds **no** L1 symbol, **no** decoding operation, **no** sixth corruption code · alters no
invariant line.

| # | Addition | Anchor | Resolution |
|---|---|---|---|
| D-1 | The descent walk + `descend` (trigger-checked child creation, seed records, refusal records, the MOVING stop record) | PRD §4.2 DESCENDING / §B3; B2's `Driver`, `turn_key`, `REFUSAL_ATTEMPT_PREFIX` imported | Interface layer on the attested driver — the socket dialect is never re-implemented and never touched (H-B3-1) |
| D-2 | The node record schema (`axis` / `signed_path` / `tentative` / refs — no address key) and the node layout (`seed.md`, `artifact.md`, `return.md`) | PRD §5.3/§5.4/§13.1-D7; PLAN-ADDENDUM §C | Derived node state; the podium (`question.md`) has no machine path |
| D-3 | The signed-path field grammar (AR3 glyphs, `+^k·−x₁…−x_m`, the U+2212 operator; `-P-Q-P` and `+-G` rejected) | Appendix D.5/AR3; commission §7 | Interface layer; the glyphs are P4a's `STEP_KINDS` data, imported — and the rejection rule is letter-order-independent (H-B3-2) |
| D-4 | The descent guard items `GS-L1…GS-VOID` (the D.12-class check, separately numbered) | PRD §5.5, R6, the seal line 9 | Cannot drift P4a's `AD-*`/`CX-*`/`DC-*` or the source's R1–R13; the §1.9 symbol check runs through P4a's imported parser |
| D-5 | The fixture apparatus (the start states, the world provider, the walk scripts, the byte-pinned expected trees/ledgers, the fixed ledger clock) | commission §7; P4a's attest-provider pattern | Test apparatus only; each fixture declares its case and its prediction; the engine never writes `state: "attested"` |
| D-6 | `DESCENT_SURFACE` in `surface_contract.py` — the descent's declared surface, versioned | Codex §3.6; P4a/P4b surface contract (sha-pinned: 776ff463… / fb166569… / d7ab814c…) | A declaration, not a fork: the contract is imported, the descent surface is declared against it |

## 5. Holds — H-B3-1 … H-B3-5, each with the reading this round ships

* **H-B3-1 (no desk constituted).** The descent runs against fixture node trees; nothing
  boots, no socket, no live pane. The inherited B2 driver keeps its trust assertion behind a
  neutral stand-in and the instrument is never exercised — the socket surface is imported,
  never used, never re-implemented.
* **H-B3-2 (the letter-order is open — his).** §1 above: a declared parameter, the two spots
  `descent.py:300` and `descent.py:317`, nothing else. His confirmation is a one-table flip.
* **H-B3-3 (B″ and the run-verdict are B4/B5/B6).** The descent returns `artifact + genuine
  ∞0′` as references and byte facts; it composes no candidate B″ and writes no run-verdict.
* **H-B3-4 (the quantum jump is planned for, never implemented).** C7 is encoded as
  structural constraints — no jump marker, no jump logic; the word "jump" appears only in
  docstrings/comments, and the selftest asserts exactly that.
* **H-B3-5 (versions carried, never invented).** `block_version` stays `""` (H-P4b-6
  carried); block/arrangement versions are `1` (P4b's own); runtime pins are the PRD §3.2
  probe pins; nothing in a record or store is an invented identity.

## 6. Assumptions and open flags (stated, not hidden)

1. `PLAN-ADDENDUM` is **not present on the box**; its §B/§C are known only from the
   commission's quotes (P4b's precedent, carried).
2. The two malformed signed paths `-P-Q-P` and `+-G` are read as **ASCII-hyphen** forms: the
   commission's own bytes write them with U+002D while the AR3 operator is U+2212 — the only
   reading that rejects both without resolving the D.2/D.3 letter-order question (H-B3-2),
   and the one the selftest pins.
3. "Genuine ∞0′" is operationalized as *the V record carries the human's act* (non-null
   attestation_ref) — the human's click is the only authenticity authority; the engine reports
   presence, never genuineness (commission §6).
4. The fixture fiction: attested records in the fixtures are written by the fixture world
   (the caller-supplied provider, P4a's attest-provider pattern) — the descent engine itself
   never writes `state: "attested"` and never writes `question.md`.
5. Fixture ledgers use a fixed injected clock (B0's `clock=` parameter) so the expected pins
   are byte-exact; the default clock stays B0's own.
6. The anchor (`""`) is the reading's coordinate, not a root: a node at ε stores the
   `inherited` form of the field (the reading is itself a continuation — no root, D.2), while
   the `anchored` form lives at the field's birth record (the plant, gate x) on the ledger.
7. The verifier's pack may bind different names than §2; the functions are the real surface,
   the names are stable and documented here.
