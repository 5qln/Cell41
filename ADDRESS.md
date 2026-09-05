# ADDRESS.md — the node language of the 4+1 cell (§A of AGREED-PLAN-ADDRESSING)

**hermes-amihai [A] · 2026-08-24 · authored vocabulary, no substrate mutation**
**Status: LOCKED CANDIDATE.** This file is the artifact both agents hash (per the lock protocol §0
addition), replacing the Appendix-D *source-text* byte hash that could never be verified across two
different extraction pipelines. Every load-bearing sentence of Appendix D that the implementation
relies on is quoted **verbatim** below, with its section id, so agreement is checked by comparing
spans — not bytes of whole files.

Source: 5QLN Codex — Appendix D, *Decentralized Addressing (The Unfolded Fractal)*, 5qln.com,
fetched 2026-08-24. Appendix D is a self-declared **derivative, surface/interface layer** (Codex
§3.6, §1.10): *"It adds exactly one navigation layer (the signed path) … It introduces no new L1
symbol, no new D1 decoding operation, no sixth corruption code, and it does not alter the Nine
Invariant Lines."* Nothing in this file drifts that boundary.

---

## 1 — Canon, verbatim, with section ids (the spans we both check)

**D.1 — the lawful cell**
> "4+1 is the syntax. It is invariant at every depth and every height: 1 center (S) + 4 corners
> (G, Q, P, V), never 3+1, never 6+1."

**D.2 — the unfolded fractal**
> "No root — any cell has a father-frame, which has a father-frame, …"
> "Start is a role, not a coordinate."

**D.3 — the node language**
> "A node is a word over the alphabet {S, G, Q, P, V}. ε is the empty word — the origin of a given
> reading."
> "zoom in = append a letter S → SG → SGQ → …"
> "zoom out = strip a letter SGQ → SG → S → ε → ε's father → …"
> "The word anchors to one assumed root. That is the gap the sign fills."

**D.4 — the sign**
> "The sign is not a property of a node — it is a relation between two nodes, adapting to the
> current vantage:"
> "− = := = X within Y = descend into the sub-cell (daughter · deeper)"
> "+ = ↤ = Y contains X = ascend to the father-frame (father · shallower)"

**D.5 — the address grammar**
> "addr(A → B) = +^k · (−x₁)(−x₂)…(−x_m)"
> "k = steps up to the common father · m = steps down to the target · k+m = the generation gap"
> "The − steps carry a letter (which daughter); the + steps carry none (there is only one father)."

**D.6 — the decision rule**
> "k = 0 → B within A (daughter) A is the father-frame"
> "m = 0 → A within B (father) B is the father-frame"
> "k, m > 0 → neither (cousins) shared father, different branch"
> "empty address → same node"
> "The sign is the answer to "whose context?" — context flows father → daughter, so k is exactly
> how many frames a merging peer must climb to see the originator's whole inquiry."

**D.7 — the signless true start**
> "THE TRUE START: S = ∞0 → ? ← bare · silent · no prefix · no sign"
> "S = ∞0 → ? is sign-free: its → is emergence, not address."

**D.8 — the ∞0′ ≡ ∞0 identity**
> "∞0′ may seed the next cycle as new ∞0"
> "∞0′ (of the field) ≡ ∞0 (of the stranger)"

**D.10 — the One Law at every node**
> "H = ∞0 | A = K"
> "Centralized domination = one holder of the membrane (one root, one privileged ∞0). This mechanism
> puts the membrane at every node: each cell is its own ∞0 | K, and +/− is the traversal across
> membranes."

**D.14 — the block, extended**
> "ADDRESS: +^k · −x₁…−x_m (relative · adapts to vantage)"
> "START: S(x,t) = ∞0 → ? (role, not coordinate · signless)"

**AR layer (D.11, derived rules — visibly separate from R1–R13)**
> "AR1 4+1 is the invariant cell at every scale. Never 3+1, never 6+1."
> "AR2 Every node is a word over {S, G, Q, P, V}. Zoom in = append (−). Zoom out = strip (+)."
> "AR3 Every address normalizes to +^k · (−x₁)…(−x_m). All + first, then all −."
> "AR4 Orientation is read from the signs: k=0 daughter · m=0 father · else cousins."
> "AR5 The true start is signless: S = ∞0 → ? carries no + and no −."

**D.12 — validation items adopted as tests** (see §5)

---

## 2 — The vocabulary this implementation uses (and only this)

**word** — a string over `{S, G, Q, P, V}*`. The node's identity. **Stored**, never derived (R2:
the socket is one uid; an identity derivable from a renamable label is rewritable by whoever holds
`workspace.rename`, and is therefore not an identity).

**ε (the empty word)** — legal **only as a declared value**: the `word` key is present and set to
`""`. It means *origin of a given reading* — never a global root. A **missing** `word` key is not
ε; it is `AddressUnknown` → **refuse to render**. ε must carry a `reading` field naming whose
reading it originates, and renders as:

```
ADDRESS: ε — origin of this reading · a father-frame exists and is not named here
```

so D.2 ("No root") stays true **on screen**, not only in prose. The word "root" never appears in
any rendered ADDRESS line.

**sign** — `+` ascend (father · strip) / `−` descend (daughter · append). A relation between two
nodes, never a property of one (D.4). Never appears inside a phase equation (D.12).

**address(A → B)** — normalizes to `+^k · (−x₁)…(−x_m)`: all `+` first, then all `−` (AR3). Only
the `−` steps carry letters. Derived, never stored.

**orientation** — read from the signs alone (D.6 / AR4): `k=0` daughter · `m=0` father · `k,m>0`
cousins · empty address = same node.

## 3 — Derivation (never stored): how two words yield an address

Given words A and B with longest common prefix of length `c`:

```
k        = len(A) − c            (frames to climb from A to the common father)
m        = len(B) − c            (daughters to descend into)
letters  = B[c:]                 (each − step's letter, in order)
relation = daughter if k == 0 and m > 0
           father   if m == 0 and k > 0
           same     if k == 0 and m == 0
           cousins  otherwise
```

Worked checks against D.6's own cases (originator ε; peer PQP):
`ε → PQP` = `−P −Q −P` (daughter³) · `PQP → ε` = `+++` (father³) · `PQP → PQG` = `+ −G` (cousins) ·
`PQP → G` = `+++ −G` (cousins). These four are tests, not prose.

## 4 — The node-directory convention (R4: node-local, not path-free)

- A node is a **directory**: `nodes/<word>/` — with `_` standing for ε — holding:
  - `cell.node.json` — `{"word": "…", "reading": "…"}` (`reading` required iff `word == ""`).
    Nothing else. **No centre content ever appears in this file** (H = ∞0 | A = K: the word lives
    on the K side; the question lives on the ∞0 side, in `question.md`, planted by the human).
  - `question.md` — the node's own centre, human-planted only.
- **No default node. No fallback path in code.** A missing or malformed `cell.node.json` ⇒
  `AddressUnknown` ⇒ refuse to render.
- The podium pane command is **relative**: `["watch","-n","2","cat","./question.md"]`; the node is
  selected by the `cwd` passed to `plugin.pane.open` (proven 2026-08-24: `--cwd` honoured outside
  `plugin_root`, `inbox/PROBE-RESULT-S7-2026-08-24.md`). One manifest serves every node at every
  depth; the seal argv (`watch`, no shell) is untouched.
- The **workspace label mirrors the node word** for the human's eyes: the word exactly, or — when
  the word is ε — the **reading name** (a bare `_` is a directory placeholder for machines, not a
  human-facing label). The mirror is a display, never a source. At render, if a label is supplied
  and disagrees with the stored word (or, for ε, with the reading) ⇒ `AddressMismatch` (reporting
  both values) ⇒ **refuse to render**. No silent repair in either direction. (R2: invisible
  disagreement is the drift class that wedged a session at 16:38 on 2026-08-24.)

## 5 — Validation adopted as falsifiable tests (D.12, plus ours)

| # | check | from |
|---|---|---|
| 1 | a cell with no declared word refuses (`AddressUnknown`) rather than assuming ε | sibling |
| 2 | `word: ""` without `reading` refuses | R1 |
| 3 | stored word vs supplied label disagreement ⇒ `AddressMismatch`, both values reported | R2 |
| 4 | the four D.6 worked cases compute exactly | D.6 |
| 5 | `+/−` never appears inside a phase equation anywhere in the render | D.12 |
| 6 | the five phase equations appear verbatim at every cell render | D.12 |
| 7 | depth is uncapped — a 25-letter word and a 3-letter word both render | D.12 ("25 is a floor, not a ceiling") |
| 8 | no sixth corruption code is named anywhere | D.12 |
| 9 | `CENTRE UNREACHABLE` ≠ `UNPLANTED` (already shipped in §C1, four centre states) | sibling F2 |
| 10 | corner fidelity: each corner line carries a verbatim span (≥ 24 chars) of its cited canon fact | §C2 |

## 6 — What this file deliberately does not do

- Names no `root`. ε is origin-of-a-reading, declared, and always points at an unnamed father-frame.
- Stores no address, no relation, no centre content. Words are stored; **everything else is derived**.
- Authorizes no descent. §D (zoom/ascend, depth ≥ 2, `target_pane_id` mandatory) is authored
  separately and **held for Amihai's fresh, scoped attestation** — it creates a workspace and opens
  a podium.
- Touches nothing running. The live podium keeps its current absolute argv until §D's attested
  window (sibling catch #1, accepted in -v2).

— A
