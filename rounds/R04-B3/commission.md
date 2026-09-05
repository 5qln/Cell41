# COMMISSION — R04 · B3 · Descent (zoom)

**Working handle:** "the descent." **The phase name and slot are Amihai's to name** — this document uses
the build-spine slot `B3` (round `R04`) only until he names it.

**Author:** dsh (`deepseek-v4-pro`, ONE generation). **Verifier:** Hermes profile `herdr`, separately,
against a pack written before it judges anything. `builder ≠ verifier`.

**Workspace:** `/home/deploy/the-cell/rounds/R04-B3/` — write **only** inside `./authored/`. A hash
fence outside `authored/` is checked before and after.

**§1.10 of the Codex governs every conflict: where a document diverges from `5qln.com`, the source is
authoritative** — including this commission.

---

## 0. His words and the standing decisions that bind this round

The build so far (all attested and closed): **B0** the ledger + record · **B1** the read-only walker ·
**B2** the driver (one cell, sequential) · **P4a** the step mode (the check path) · **P4b** the desk
bundles (one grammar seated at addresses over `{S,G,Q,P,V}`, never five flat desks).

His attested clarity (PRD-APPENDIX-DRAFT.md, ATTESTED 2026-08-29): *"S is the conductor — the membrane,
the gate where ∞0 is allowed in by a human start from not-knowing… Every phase contains all five phases —
one grammar seated at addresses, never five flat desks."*

Standing decisions (D12/D14, unchanged): success in a phase = **contextual DECODE of context to language +
COMPILE of output xyzab**; every decoding and compiling **loyal to `5qln.com/codex`**.

## 1. What to build — one paragraph, no doctrine

The **descent**: given a node at an address, when its gate fails to lock, the driver **descends** — it
creates a child node by appending a letter to the address (zoom in), seats an arrangement from the P4b
grammar at that child, carries the axis `field` **byte-exact** from parent to child, runs the guard pass at
every depth, and returns **an artifact + a genuine ∞0′** as the return criterion. Address is *derived, never
stored*; the signed path is a *separate field*; the axis verdicts (MOVING / recast / STASIS) are computed
from byte comparison; and every one of the five quantum-jump commitments holds. This is the module that
makes the one cell *walkable at depth*, on top of the attested B2 driver, the P4a step checks, and the P4b
desk bundles — importing them, never re-implementing them.

## 2. Acceptance criteria — quoted verbatim

### C1 — byte-exact axis inheritance (PRD §B3 + §5.4)
> "Build: gate-fails-to-lock → child node + address append + arrangement; **byte-exact axis
> inheritance**…" — *Done when:* "a 3-deep descent shows byte-identical `axis.field` from root to leaf;
> a manufactured field change yields `MOVING` and a stop-and-surface."

`field` = `{mode: inherited|anchored, anchor: <durable ref>}` — at a continuation **copied byte-exact** from
the parent's handoff; at a fresh start anchored at the field's own birth; **never empty**. Verdicts:
`MOVING` iff fields differ · `recast` iff fields equal and surfaces equal · `STASIS` iff fields equal and
surfaces differ. **MOVING dominates:** stop the descent at the human's level, surface, log, wait.

### C2 — address append/strip + the signed path split (PRD §5.3 + PLAN-ADDENDUM §C)
> "Word over `{S,G,Q,P,V}` with an optional sign for orientation; ε (the root) is written `_` on disk.
> Nodes are directories: `nodes/<word>/{question.md, cell.node.json}`. Zoom in = append a letter; zoom out
> = strip. **Addressing is derived, never stored** as a separate identity, and never derived from herdr
> pane ids (which are re-minted by `layout.apply`)."

> "The signed path (`+^k · −x₁…−x_m`, AR3) gets its own field in B3; `address` keeps the bare node word.
> B0 is attested and stays untouched." — the validator rejects `-P-Q-P` and `+-G`.

### C3 — guard pass at every depth (PRD §5.5)
> "Guard pass at **every** node and depth: `L1 L2 L3 L4 V∅`. No V without ∞0′ (R6)." — *Done when:* "a V
> with no ∞0′ is refused."

### C4 — the return criterion (PRD §B3)
> "return criterion = artifact + genuine ∞0′."

### C5 — TENTATIVE is temporal, never epistemic (PRD §5.5)
> "`tentative: true` is temporal, never epistemic. A tentative node is **non-data**: no heuristic may
> promote it, no downstream gate may consume it as evidence, and it never reaches the podium. Only a human
> act converts or discards it."

### C6 — the gate-fails-to-lock flow (PRD §B3)
> "gate-fails-to-lock → child node + address append + arrangement."

### C7 — the five invariant commitments (PLAN-ADDENDUM §C)
> "no hard-coded maximum depth · the address alphabet stays extensible so a jump marker can exist beside
> `{S,G,Q,P,V}` · the loop stops on **resources**, never on semantic completion · nothing treats descent
> as narrowing (a leap may open a *larger* dimension) · **no code assumes the current cell is the root**
> (Appendix D.2: no root, no leaf)."

## 3. Verified-facts block (do not re-probe — `FACTS.md`)

- **herdr dialect:** envelope `{id,method,params}` all-required; tagged-union results; desk label key
  `PaneInfo.label`; pane ids volatile (`w2:*` vs `w8:*`); one request per connection. The driver (B2) is
  the only module that speaks it.
- **Ledger:** B0 module at `/home/deploy/the-cell/ledger/fractal_ledger.py` (import, **never copy**), sha
  `b291e659…`. `gates.jsonl` holds **1 record — his plant**.
- **P4b grammar/arrangement/block** (attested, canon `2a2053a`): `WORD_ORDER = "inner_first"` (D.2) is a
  **declared parameter** — `seat_address` returns `letter + cell_address`. The seat-address convention is
  the D.2/D.3 flag, still open for **his** confirmation (see H-B3-2). No logic may depend on which end is
  deep.
- **P4a step mode** (attested, canon `898593b`): `step.py` exposes the stepping surface; `surface.py`
  declares the surface contract (sha `776ff463…`).
- **The equations + seal:** byte forms enumerated in P4a commission §3.3 and P4b `grammar.py`
  `EQUATION_FORMS`/`SEAL_FORMS`. Seal = the numbered 217-byte nine-line block → `feaa46b4…`.
- **No desk is constituted** on the box. Descent is a data/state module, tested on fixture node trees,
  never a live run (H-B3-1).

## 4. The interface to the attested rounds

- **B2 driver** (`rounds/R03-B2/authored/driver.py`): the gate walk and the herdr socket surface. B3's
  descent **imports and extends** it; it does not re-implement the socket dialect.
- **P4a step mode** (`rounds/P4a-step-mode/authored/step.py`): the D.12 check after every step. The
  descent's per-depth guard pass is the same class of check; import, never re-author.
- **P4b desk bundles** (`rounds/P4b-desk-bundles/authored/`): `block.py`, `arrangement.py`, `grammar.py`.
  The child node's arrangement is a P4b arrangement — import, never re-author.

## 5. Holds — declare, never guess

- **H-B3-1 — no desk constituted.** The descent runs against fixture node trees; nothing boots, no
  socket, no live pane. A live run is B4, not here.
- **H-B3-2 — the letter-order is open (his).** The convention is a **declared parameter** (`WORD_ORDER`).
  dsh must **not** hard-code inner-first or outer-first; no logic may depend on which end is deep. The
  D.2/D.3 confirmation is his, later, and is a one-table flip — never a rewrite.
- **H-B3-3 — `B″` (B-double-prime) and the run-verdict are B4/B5, not B3.** The descent returns
  `artifact + genuine ∞0′`; it does not yet compose the candidate B″ (that is B6).
- **H-B3-4 — the quantum jump is *planned for*, never implemented.** The five commitments are structural
  constraints on the code, not a jump feature. No jump marker, no jump logic.
- **H-B3-5 — block/arrangement/ledger versions are carried, never invented.**

## 6. Prohibitions

No write path to the podium (`pane.send_text/input/keys` at the centre). No git, no attestation, no claim
anything ran. No gate semantics re-implemented outside `fractal-engine`. No sixth corruption code, no new
L1 symbol, no new decoding operation, no renamed symbol. No byte normalisation (⋂→∩ is renaming). No
hard-coded max depth. No code assuming the current cell is the root. No naked agents. No hand-editing
blocks (write-once). No authenticity verdict (the human's click is the only one). Nothing described as
attested/decided/verified that this commission does not mark so.

## 7. Deliverables — under `./authored/` (layout yours to vary; content is what is checked)

- `descent.py` — the descent module (address ops, axis field/delta/verdicts, guard pass, the
  gate-fails-to-lock flow, the signed-path field).
- `surface_contract.py` — reads P4a/P4b's surface contract by path, sha-pinned; declares the descent
  surface against it.
- `selftest.py` — the author's own suite (a hypothesis, not a result).
- `phase-card.md` — predictions only (never results) + the D14 divergence log.
- `fixtures/` — at least: a lawful 3-deep descent · a manufactured field change → MOVING + stop ·
  a V with no ∞0′ → refused · a tentative node never consumed · the malformed signed paths `-P-Q-P`,
  `+-G` → rejected.

## 8. Budget

**ONE authoring generation.** No exploratory chat. Artifact + phase card in, out.
