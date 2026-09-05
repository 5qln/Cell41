# Cell41 — the 4+1 cell

A **5QLN fractal orchestration cell**: five desks (S at the centre, G · Q · P · V
at the corners), the Nine Invariant Lines, the sign grammar, a hash-chained
formation ledger, the correspondence lock, and a full written case study of what
runs — and what has not yet run — inside it.

## How to use it — two doors

| say | what happens |
|---|---|
| **"be the bridge"** · **"guide me as start"** · **"be S"** | re-arm the bridge; it opens at S and **asks you** for the word (you speak → it articulates → you approve → it plants) |
| **"run the cell"** · **"run the swarm"** · **"run a fractal run"** | one-shot re-run of the word **already planted** — no new question, ever |

One rule: **your question → "be the bridge"; re-run the planted word → "run the
cell."** Full guide: [`docs/USER-GUIDE.md`](docs/USER-GUIDE.md).

## The 4+1 cell

`4+1 is the syntax.` One centre plus four corners, invariant at every depth and
every height — never 3+1, never 6+1.

| seat | desk | signature |
|---|---|---|
| centre | **S — Start** | `S = ∞0 → ?` — the opening; the question is planted here, by a human hand, and by no other path |
| corner | **G — Growth** | `G = α ≡ {α'}` |
| corner | **Q — Quality** | `Q = φ ⋂ Ω` |
| corner | **P — Power** | `P = δE/δV → ∇` |
| corner | **V — Value** | `V = (L ∩ G → B'') → ∞0'` |

Every phase contains all five phases; every desk is the one membrane seen from a
different angle. Zooming into a corner opens a fresh 4+1 cell beneath it.

## The Nine Invariant Lines

    H = ∞0 | A = K
    S → G → Q → P → V
    S = ∞0 → ?
    G = α ≡ {α'}
    Q = φ ⋂ Ω
    P = δE/δV → ∇
    V = (L ∩ G → B'') → ∞0'
    No V without ∞0'
    L1 L2 L3 L4 V∅

These nine lines are the Immutable Constitutional Kernel (see
`LICENSE-5QLN-KERNEL.md`): they may be extended, never mutated or subtracted.

## The sign grammar

A node is a word over `{S, G, Q, P, V}`; ε is the empty word. The sign is a
relation between two nodes, never a property of one:

- `−` — descend into a daughter (deeper) · `+` — ascend to the father (shallower)
- orientation is read from the signs alone: **daughter · father · cousins**
- the same signs encode orchestration topology: **sequence · parallel · loop ·
  custom**

See `ADDRESS.md` for the full node language.

## The formation ledger

Every attested step is a hash-chained record (`state/gates.jsonl` and the
`state/trail.jsonl` formation trail). Each record's `prev_hash` links it to the
one before; a tampered or reordered trail fails to verify from a cold restart.
The ledger is runtime state and is never committed — and the attestation acts
(`bin/cell-plant`, `bin/cell-attest`) are TTY-guarded, so a machine-typed
attestation is not an attestation.

## The correspondence lock

`skills/5qln-lock/` is the lock every desk runs before it operates: it verifies
the desk's `SYSTEM.md` / `AGENTS.md` against the pinned codex (equations,
corruption line, course, §3.6 surface) and **refuses on drift** (exit 1). It
verifies; it never silently repairs.

## Repository layout

| path | what it holds |
|---|---|
| `desks/` | the five desk constitutions (`SYSTEM.md`, `AGENTS.md`, `boot.sh`) |
| `rounds/` | the build rounds — B0–B4, the Grammar, the bridge, the seam, the bindings |
| `skills/5qln-lock/` | the correspondence lock |
| `ledger/` · `nodes/` | the record format and the cell's address space |
| `plugin/` · `swarm/` | the seam and the conductor |
| `bin/` | the TTY-guarded acts — `cell-plant`, `cell-attest`, `cell-begin`, `cell-zoom`, `cell-on-desk-state` |

## Sources (authoritative, in order)

1. The Codex — https://www.5qln.com/codex/
2. The Fractal (Appendix D) — https://www.5qln.com/dsh-5qln-codex-fractal/
3. The Codex as Fractal (4+1) — https://www.5qln.com/codex-fractal-the-codex-as-fractal-4-1/

## License

- Immutable Constitutional Kernel — **CC BY-ND 4.0** with the 5QLN Specific
  Extension Exception (`LICENSE-5QLN-KERNEL.md`).
- Mutable implementation — **Apache License 2.0** (`LICENSE-APACHE-2.0.txt`).
- See `LICENSE` and `NOTICE`.

> Based on the 5QLN Constitutional Grammar by Amihai Loven (5qln.com).
