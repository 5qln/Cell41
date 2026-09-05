# COMMISSION — R05 · B4 · The unattended run

**Working handle:** "the unattended run." **The phase name and slot are Amihai's to name** — this
document uses the build-spine slot `B4` (round `R05`) only until he names it.

**Author:** dsh (`deepseek-v4-pro`, ONE generation). **Verifier:** Hermes profile `herdr`, separately,
against a pack written before it judges anything. `builder ≠ verifier`.

**Workspace:** `/home/deploy/the-cell/rounds/R05-B4/` — write **only** inside `./authored/`. A hash
fence outside `authored/` is checked before and after.

**§1.10 of the Codex governs every conflict: where a document diverges from `5qln.com`, the source is
authoritative** — including this commission.

---

## 0. His words and the standing decisions that bind this round

The build so far (all attested and closed): **B0** ledger + record · **B1** read-only walker · **B2**
driver (one cell, sequential) · **P4a** step mode · **P4b** desk bundles · **B3** descent. B4 is the
product's **core claim**: the run that keeps going without him, and now also the **observability
deliverable** — a readable trail *while it runs*, because a seed is received by being observable.

**His attention-mode correction (2026-08-29, his word — reshapes the desk function-specs, folded into
this round):** *"the question is not just given — the whole cell is in attention mode. At S, the human
may bring raw parts of interest, not yet a question; S then suggests, if a question is found, what kind
of question the human is seeking — How? Why? etc. Then SG seeks the core in the yet-not-found question.
All five agents are in attention mode."* → The question is **discovered through the cell, never handed
in finished**; all five desks attend simultaneously, not a linear pipeline waiting for a finished
question.

**His aimless-openness answer (2026-08-27, his word, banked in Hindsight):** *"the bird high in optimal
state does not move — it is carried, not resisting the nature of air; that state is AIMLESS OPENNESS.
Ideally there are not even five phases: there is only infinite-zero announcing itself… The phases appear
only when the hovering begins to navigate toward the manifest."* And the run's whole shape in one
sentence: *"the human gives the challenge, the AI runs the loops, bounded only by resources."*

**Standing decisions (D12/D14, unchanged):** success in a phase = **contextual DECODE of context to
language + COMPILE of output xyzab**; every decoding and compiling **loyal to `5qln.com/codex`**. The
formation trail records **what the context decoded to, never the context itself** (D12). No V without ∞0′
(§1.6). TENTATIVE is temporal, never epistemic (§5.5). The conductor is **S** (§4.8) — not a layer above
the desks.

## 1. What to build — one paragraph, no doctrine

The **unattended run**: a conductor (`run.py`) that drives the attested B2 driver's one-cell cycle
**repeatedly, with zero human keystrokes** — when a gate fails to lock it records a **hold and keeps
other cells moving** instead of stopping; when a cycle returns ∞0′ it **seeds the next S as TENTATIVE**
(never reaching the podium, never consumed as evidence); it **re-arms from the ledger alone** after a
`kill -9` (no duplicate/skipped gate); and it **accounts model spend** so a ceiling surfaces as a held
gate, never a silent kill. Beside the gate ledger it writes an **observability trail** (`trail.py`) —
hash-chained, replayable, readable *while the run runs*, recording what each step decoded to, never
content. Desk invocation supports **both** sub-process (persistent) and re-prompted (stateless) modes
with a per-turn memory/token **cost accounting** (`cost.py`), so the mode decision is measured, not
reasoned. It imports the attested rounds — never re-implements the socket dialect, the D.12 checks, the
desk grammar, or the descent.

## 2. Acceptance criteria — quoted verbatim

### C1 — holds accumulate instead of stopping the run (PRD §B4 + §10.3)
> "Build: holds accumulate instead of stopping the run…" — §10.3: "model/provider outage → hold the
> gate, keep other cells moving."

A held gate does not halt the conductor: it records the hold, keeps other cells/cycles moving, and
surfaces the hold (to the observability trail). A hold is never auto-resolved — the machine never
attests, never closes a hold, never converts a held gate (T-O5-02).

### C2 — TENTATIVE seeding of the next S (PRD §B4 + §5.5)
> "Build: … TENTATIVE seeding of the next S…" — §5.5: "`tentative: true` is temporal, never epistemic. A
> tentative node is **non-data**: no heuristic may promote it, no downstream gate may consume it as
> evidence, and it never reaches the podium. Only a human act converts or discards it."

When a cycle's V returns ∞0′, the machine seeds the next S from it — and that seeded S carries
`tentative: true`, never reaches the podium, and is never consumed by a downstream gate (T-R5-01).

### C3 — restart re-arm from the ledger alone (PRD §B4 + T-E3-01)
> "Build: … restart re-arm…" — *Done when:* "a `kill -9` mid-run restarts with no duplicate/skipped
> gate."

A **fresh process** reads the ledger alone and reconstructs the run's exact next action (from `turn_key`
idempotency + the ledger tail) — no duplicate gate, no skipped gate. No in-memory state is trusted across
the restart. Chain verified from GENESIS; a broken chain halts the conductor, never "repairs" (B0).

### C4 — budget hold: a ceiling surfaces as a hold, never a silent kill (PRD §B4 + §10.3)
> "Build: … budget hold (a spend ceiling surfaces as a hold, never a silent kill)." — *Done when:* "a
> budget stop appears as a held gate."

Model spend is accounted **before** each turn. A ceiling reached → a held gate is **recorded in the
ledger** and the run stops cleanly — it is never killed silently and never spends past the ceiling.

### C5 — no tentative node consumed by a downstream gate (PRD §B4 + T-R5-02)
> *Done when:* "… no tentative node is ever consumed by a downstream gate (dependency audit)."

A dependency audit walks every gate record's `payload_ref` chain; any gate whose evidence chains to a
`tentative: true` record is a FAIL. This holds end-to-end across the whole run, not per call.

### C6 — ≥ 20 cycles with zero human keystrokes (PRD §B4 + T-R5-03)
> *Done when:* "≥ 20 cycles with zero human keystrokes…"

The conductor runs **20 or more full cycles unattended** — no human input, no attestation, no keystroke.
(No desk is constituted on the box, so this runs against fixture desks whose turns are deterministic —
see H-B4-1. "Zero keystrokes" is proven by the absence of any human-gate path in the run: the only
attestation writer is the TTY-guarded `cell-attest`, which the run never invokes.)

### C7 — the observability deliverable: a readable trail while it runs (PLAN-ADDENDUM §B + ANSWERS)
> R05 = B4 is "now also **the observability deliverable**: a readable trail *while it runs*, because
> reception happens by being observable."

The trail is **append-only, hash-chained, replayable from disk**, readable *mid-run* (a reader can tail a
partially-written trail and produce a consistent partial projection), and it records **what the context
decoded to, never the context itself** (D12). **Two trails, never merged:** the formation trail (the
field — everything that happened) and the gate ledger (the chain — only B″ fruits and his attestations).

## 3. Verified-facts block (do not re-probe — `FACTS.md`)

- **Ledger:** B0 module at `/home/deploy/the-cell/ledger/fractal_ledger.py` (import via
  `FRACTAL_LEDGER_DIR`, **never copy**), sha `b291e659…`. `state/gates.jsonl` holds **1 record — his
  plant** (gate `x`, address `""`, `prev_hash=GENESIS`, attested).
- **herdr dialect:** envelope `{id,method,params}` all-required; tagged-union results; desk label key
  `PaneInfo.label`; pane ids volatile; **one request per connection** (reconnect/retry-once is absorbed
  by the B1/B2 adapter — never "optimise" it away). The B2 driver is the only module that speaks it.
- **P4b grammar/arrangement/block** (canon `2a2053a`): one grammar seated at addresses over `{S,G,Q,P,V}`;
  `WORD_ORDER = "inner_first"` (D.2, **settled by Amihai 2026-08-29 "keep"** — no longer open).
  Blocks are write-once, content-addressed; a new version is a new directory.
- **P4a step mode** (canon `898593b`): `step.py` + `surface.py`; the D.12 check after every step.
- **B3 descent** (canon `be30010`): `descent.py` + `surface_contract.py` — the gate-fails-to-lock flow,
  byte-exact axis inheritance, guard pass at every depth, return = artifact + genuine ∞0′.
- **The seal:** the numbered 217-byte nine-line block → `feaa46b4…`. The equations' byte forms are
  enumerated (P4a commission §3.3 / P4b `grammar.py`); **enumerate, never normalise**.
- **No desk is constituted** on the box (H-B4-1). `agent_prompted`'s success shape is still inert; the
  run reads the desk's answer from the fenced read, never from the success shape (H-B4-3, carried).
- **Formation trail** already exists at `/home/deploy/formation-trails/fractal-herder.jsonl` (the
  field side); the gate ledger is `/home/deploy/the-cell/state/gates.jsonl` (the chain side). Two trails,
  never merged.

## 4. The interface to the attested rounds (predecessors — import, never re-author)

Staged under `./predecessors/{b2,p4a,p4b,b3}/`; the B0 ledger is on `FRACTAL_LEDGER_DIR`. dsh imports
and extends; it re-implements none of them.

- **B2 driver** (`predecessors/b2/`): `driver.py`, `instrument.py`, `lens.py`, `walker.py`,
  `dialects.py` — the one-cell walk and the herdr socket surface. B4's run calls it per cycle.
- **P4a step mode** (`predecessors/p4a/`): `step.py`, `surface.py`, `conformance.py` — the D.12 check.
  The run's per-step guard is this check; import, never re-author.
- **P4b desk bundles** (`predecessors/p4b/`): `block.py`, `arrangement.py`, `grammar.py`, `install.py`,
  `surface_contract.py` — the desk grammar seated at addresses.
- **B3 descent** (`predecessors/b3/`): `descent.py`, `surface_contract.py` — the gate-fails-to-lock
  flow the run descends through.

## 5. The desk function-specs — the folded item (codex §2, attention mode)

This is the procedure each desk runs each cycle. It is **not** new doctrine: it is the codex §2
(D1 — the Decoder) decoding operation, run on the **not-yet-found** question, in attention mode. Quote
them byte-faithful; **no new decoding operation, no new L1 symbol, no renamed symbol** (D.12). The
founding sentence is §2.1's success criterion: *"∞0 is not a step to complete — it is a state to hold. →
is not an action to perform — it is an emergence to receive. ? is not a question to formulate — it is a
question to recognize as it arrives."*

| Desk | Codex §2 decoding operation (verbatim) | Attention-mode reading (the question not yet found) |
|---|---|---|
| **S** | `HOLD ∞0` · `RECEIVE →` · `NAME ?` · `VALIDATE X` | receives the human's **raw parts of interest** (not a question); names the question only as it arrives; suggests **what kind** of question (How? Why? …) — his word; validates it is genuine (from ∞0), never manufactured. |
| **G** | `RECEIVE X` · `SEEK α` · `TEST ≡` · `FIND {α′}` · `VALIDATE Y` | seeks the **core hiding in the yet-not-found question** (his word: "SG seeks the core in the yet-not-found question"); α sought *within* X, never invented alongside it. |
| **Q** | `RECEIVE X+α+Y` · `HOLD φ` · `HOLD Ω` · `WATCH FOR ⋂` · `VALIDATE Z` | holds direct perception (φ) and the larger field (Ω) open; **⋂ is not sought — it arrives.** The lock is the human's click; never forced. |
| **P** | `RECEIVE X+α+Y+Z` · `MAP δE` · `MAP δV` · `COMPUTE δE/δV` · `RECEIVE →` · `VALIDATE A` | maps where energy drains and where value stirs; makes the ratio visible; **the gradient reveals itself, never invented.** |
| **V** | `RECEIVE full trace` · `NAME L` · `NAME G` · `FIND ⋂` · `COMPOSE B″` · `NAME B` · `FORM ∞0′` | composes the seed **from the trail, never from nothing**; forms the return question; **never closes without ∞0′.** |

## 6. Holds — declare, never guess

- **H-B4-1 — no desk is constituted on the box.** The run is fixture-driven: fixture desks answer
  deterministically; no real Pi, no real herdr socket, no live pane. A live unattended run (real Pi
  turns) is a later tier, after the desk function-specs are embodied and constituted.
- **H-B4-2 — the sub-process vs re-prompted decision is measured, not yet made live.** `cost.py`
  supports **both** modes and instruments per-turn memory/token cost. The conservative default is
  **declared data**, not hard-coded logic; the live per-Pi measurement awaits a constituted desk (one
  paid Pi turn) and is **not** done here.
- **H-B4-3 — `agent_prompted`'s success shape stays inert (carried from B2).** The run reads the desk's
  answer from the fenced read (`pane.wait_for_output`), never from the success shape.
- **H-B4-4 — the human's gate act is untouched.** The run may seed the *next* S as TENTATIVE, but it
  never writes the podium, never types a word, never invokes `cell-attest`. Attestation stays a TTY act.
- **H-B4-5 — `B″` composition (the candidate seed) is B6, not B4.** The run returns `artifact + genuine
  ∞0′` (B3's return); it does not compose the candidate B″.

## 7. Prohibitions

No write path to the podium (`pane.send_text/input/keys` at the centre). No git, no attestation, no
claim that anything ran. No gate semantics re-implemented outside `fractal-engine`. No sixth corruption
code, no new L1 symbol, no new decoding operation, no renamed symbol. No byte normalisation (⋂→∩ is
renaming). No hard-coded max depth; no code assuming the current cell is the root (Appendix D.2: no
root, no leaf). No tentative node promoted or consumed as evidence. No silent budget kill. No
authenticity verdict (the human's click is the only one). **The machine never resolves a hold** — fuzz
all three dialects → BLOCKED, never auto-attest (T-O5-02). Nothing described as attested/decided/verified
that this commission does not mark so.

## 8. Deliverables — under `./authored/` (layout yours to vary; content is what is checked)

- `run.py` — the unattended run loop: hold accumulation, TENTATIVE S seeding, restart re-arm (derive
  next action from the ledger alone), budget hold, ≥20-cycle fixture run with zero keystrokes.
- `trail.py` — the observability trail: append-only, hash-chained, replayable, readable mid-run,
  decoding-not-transcript, two-trails-never-merged.
- `cost.py` — per-turn memory/token cost accounting + the dual-mode (sub-process / re-prompted) desk
  invocation surface; conservative default as declared data.
- `surface_contract.py` — imports the attested predecessors by path, sha-pinned; declares B4's surface
  against them.
- `selftest.py` — the author's own suite (a hypothesis, not a result).
- `phase-card.md` — predictions only (never results) + the D14 divergence log.
- `fixtures/` — at least: a deterministic fixture desk (attention-mode answers) · a full ≥20-cycle
  unattended run · a `kill -9` at a known mid-run point → clean re-arm with no duplicate/skipped · a
  budget ceiling reached → held gate, no overspend · a tentative S seeded → never promoted, never
  consumed · a hold that does not stop the run · a torn/partial trail → replay still consistent.

## 9. Budget

**ONE authoring generation.** No exploratory chat. Artifact + phase card in, out.
