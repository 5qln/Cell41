# CONTEXT.md — requirements ground: the fractal 4+1 (studio) and the canon (Hindsight)

**Added 2026-08-25 by the host-side sibling agent, per Amihai's instruction to add the relevant
context for this repo's requirements. Additive only — no file authored by hermes-amihai was
modified; review the diff freely.**

## §0 — Where this context comes from

| source | what it holds | status |
|---|---|---|
| The Cell studio design — `DESIGN.md` (Session 02, "The Question Conducts") | the 4+1 cell as the interface design: sealed podium + four free desks | authored in the studio (hermes-amihai), 2026-08-24 |
| `DIALECT.md` (Session 03, "A Felt Wish Becomes an Attested Setting") | the four-step crossing: will → settings → meaning → confirm-or-comment | authored in the studio, 2026-08-24 |
| `USER-GUIDE.md` | what stands on the host; the human's two doors (`plant`, `attest`) | authored in the studio, 2026-08-24 |
| Hindsight bank `canon` | source-only tier: verbatim pages, references, H's authority notes (`authority: ground-truth` / `implementation-context`) | read-only by doctrine; recall-only |
| Hindsight bank `studio` | produced fruit of the 5QLN Studio sessions (tags `5qln-design-language`, `session-01…`, `herdr-host-truth`) | produced |
| `ADDRESS.md` (in this repo) | the locked vocabulary; canon spans quoted verbatim with section ids | LOCKED CANDIDATE, sha256 `2724c99b…2644` |

## §1 — The ground: the fractal 4+1, as designed in the studio

The instrument this repo ships is the **4+1 cell** — the one design rule (studio Session 02):
one centre + four corners, invariant at every depth and every height; never 3+1, never 6+1.
In this cell:

- **The centre is the podium** — sealed, shell-less, renders only `question.md`. The question is
  planted by the human alone, by hand, in the pane. No agent may ever take the podium, at any
  number of agents.
- **The four corners are the desks G · Q · P · V** — free. Agents play there; one agent may walk
  all desks in sequence or five agents may take a desk each; the score does not change, only the
  ensemble size. The agent may re-orchestrate the desks endlessly; it may never touch the podium
  (the Sealed / Free law).
- **Attestation before action** — the tuning loop obeys the same law as the cycle (DIALECT's
  four-step crossing): the human expresses will in free language; all discrete setting-work is
  machine-side; what returns is the *meaning* of the choices; one confirm-or-comment word closes,
  and only then does anything land. `plant` and `attest` are TTY-guarded — a machine-typed
  attestation is not an attestation, with no flag and no override path.
- **Nothing autonomous (stage 1)** — no `[[startup]]`, no `[[build]]`; the events hook is a pure
  recorder. Trusted-autonomy profiles are a later, optional module, earned through use.

The studio provenance for each of these is in the files cited in §0. This repo's README section
"The law, encoded" is exactly this ground in code.

## §2 — The canon, as held in Hindsight bank `canon`

The `canon` bank is the source-only tier of 5QLN memory: verbatim pages, references, and H's
authority notes; the machine files into `living` and *proposes* for `canon` — only H
promotes/seals. Recalled spans that ground this repo (authority tags as returned):

- **D.1 — the lawful cell** (`authority: ground-truth`, published): *"4+1 is the syntax. It is
  invariant at every depth and every height: 1 center (S) + 4 corners (G, Q, P, V), never 3+1,
  never 6+1."* — quoted verbatim in `ADDRESS.md` §1.
- **H-verbatim on the cell** (canon): *"Center = S, the only position that is both origin (∞0)
  and return (∞0′). Corners = G, Q, P, V, read clockwise."* — 5QLN Codex, Appendix D,
  *Decentralized Addressing* (5qln.com).
- **DC-01 — the fractal is the 4+1 cell, not the 25 sub-phases** (`authority:
  implementation-context`): the old 5×5 map is superseded; *"the 25 sub-phases are the first
  in-zoom of a single cell, never a cap; 25 is a floor, not a ceiling."*
- **DC-02 — the centre is the question, never the code** (`authority: implementation-context`):
  *"The center of every memory cell is the question (S = ∞0 → ?)… the Nine Invariant Lines are
  the grammar, held outside the cell, never a position in it."* — why this repo ships no centre
  content, no default node, and a human-planted `question.md` only.
- **The One Law** — *"H = ∞0 | A = K"*: the word lives on the K side; the question on the ∞0
  side (`ADDRESS.md` §4).
- **D.7 — the signless true start** — *"S = ∞0 → ? · bare · silent · no prefix · no sign."*

`ADDRESS.md` §1 carries the full verbatim span set (D.1–D.14, AR1–AR5) with their section ids —
it is the hashable artifact both agents agree against (8/8 canon spans matched). The canon bank
recall is a retrieval over that same source layer.

## §3 — How the requirements trace

| requirement in this repo | source |
|---|---|
| 4+1 invariant — 1 centre + 4 corners, never 3+1/6+1 | canon D.1 / AR1; studio DESIGN.md (Session 02) |
| sealed podium; no machine write path to the centre | studio DESIGN.md (the seal); studio bank `herdr-host-truth` (podium-seal caveat) |
| `plant` / `attest` refuse without a human TTY | studio DIALECT.md (attestation before action); canon DC-02 (centre human-planted) |
| no default node; missing declaration ⇒ `AddressUnknown` ⇒ refuse | canon D.2 ("No root — start is a role, not a coordinate"); ADDRESS.md §4 |
| node-local centre; relative podium command | canon D.5 / AR3 (address grammar); studio R4 decision (ADDRESS.md §4) |
| nothing autonomous; events hook = recorder only | studio DESIGN.md (stage 1); DIALECT.md (no premature crystallization) |
| Apache-2.0 + CC BY-ND kernel licence — the mutable implementation is free, the kernel is sealed | README; `LICENSE` / `LICENSE-5QLN-KERNEL.md` |

## §4 — The open (unchanged)

The design is true only while the podium stays human-held; the moment it is read as a spec to
execute rather than a score to play, it has died on the page. This repo ships the instrument,
not the workshop.
