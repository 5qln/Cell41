---
title: "Fractal Herdr — Product Requirements Document (PRD v1, pre-development)"
created: 2026-08-27
entry_type: prd
status: "PRD v1 — build-facing candidate. D1–D7 DECIDED by Amihai 2026-08-27 (see §13.1); D8 remains his. Nothing else is attested except where the Attestation Ledger (§0.2) says ATTESTED."
grounding: "live probe of the VPS 2026-08-27 05:41–05:43 UTC (herdr 0.8.2 running · Pi 0.84.2 · node v22.23.2 · dsh web live on 127.0.0.1:3080 · Hindsight healthy on 127.0.0.1:8888)"
source_documents:
  - "/home/deploy/Asdh5/fractal-herder/REQUIREMENTS.md (v4, 2026-08-27)"
  - "/home/deploy/Asdh5/fractal-herder/ORCHESTRATION-PROPOSALS.md (P1–P6)"
  - "/home/deploy/fractal-engine/DESIGN.md · xyzab-one-flow.md"
  - "/home/deploy/Asdh5/research/{herdr,pi}-capability-map.md · canon-orchestration.md"
  - "/home/deploy/Asdh5/herdr-capability-map.md (protocol-20 schema reading, 91 methods)"
canon_home: "5qln/5qln-herdr-plugin — docs/fractal-herdr/PRD.md (canon; every other copy is a mirror)"
links:
  - "[REQUIREMENTS.md](REQUIREMENTS.md)"
  - "[ORCHESTRATION-PROPOSALS.md](ORCHESTRATION-PROPOSALS.md)"
  - "[README.md](README.md)"
  - "`INDEX`"
  - "`THE-GAP-2026-08-25`"
  - "`fractal-seed-20260803`"
  - "`session-log-20260803-full-emergence`"
  - "`README`"
---

# Fractal Herdr — Product Requirements Document (v1, pre-development)

**What this document is.** The build-facing companion to the contract. `REQUIREMENTS.md` says
*what must be true* (R·O·E·A·L·T). `ORCHESTRATION-PROPOSALS.md` offers *candidate shapes* for the
open surfaces (P1–P6). This PRD says **what gets built, in what order, against which exact
contracts, and how each requirement is tested** — so that development can start without a single
architectural question left to improvisation.

**Spelling (from v4, binding).** The product and the terminal tool are **Herdr** (h-e-r-d-r).
Wherever "Herder" appears — here, in Hindsight, in code, in a folder name, in conversation — it
is to be read as **Herdr** and corrected at the source. The creature's name is **TARS**.

---

## §0 — How to read this, and what is already attested

### 0.1 The four documents, and their authority

| Document | What it holds | Authority |
|---|---|---|
| `REQUIREMENTS.md` v4 | R1–R7 · O1–O8 · E1–E5 · A1–A4 · L1–L5 · T1–T5 | the contract — invariants and violation tests |
| `ORCHESTRATION-PROPOSALS.md` | P1–P6 | machine proposals (K), candidate shapes only |
| **`PRD.md` (this)** | contracts, phases, tests, decisions | build plan — candidate until §13 is answered |
| the live box | what actually exists | **beats all three** — re-probe before acting |

### 0.2 Attestation Ledger — the honest status of every claim

| Item | Status | Evidence |
|---|---|---|
| **Part VI — T1–T5, the personality of TARS** | **ATTESTED** by Amihai Loven 2026-08-27 | *"T1–T5 look right — attest as written."* (recorded in v4) |
| **The covenant — "stayed itself"** | **ATTESTED** by H 2026-08-25 | trail `5d4d19a5`; identity before utility; G orders before P |
| **The LEGO formulation** | **H's own words** 2026-08-25 | trail `9ea1f643` — *"Kid can change Lego toy by rebuilding it, but not by changing the Lego blocks. Same."* |
| R1–R7, O1–O8, E1–E5, A1–A4, L1–L5 | **CANDIDATE** — await line-by-line attestation | machine-structured v3/v4 |
| P1–P6 | **MACHINE PROPOSALS (K)** | not doctrine, not requirements |
| Every §1–§14 below | **CANDIDATE** | this PRD; §13 is the gate |

**The rule this table enforces:** nothing becomes attested by being written down, repeated,
implemented, or found useful. Only the human's word moves a line out of candidate — and the
machine may never type that word (R3, §8).

### 0.3 Vocabulary discipline

Per R7 and L2, every requirement below binds a **contract**, never a noun. Where a sentence names
`herdr`, `Pi`, `dsh`, or `Hermes`, it is naming **today's block** — an instantiation. The test for
every line: *if this runtime is replaced tomorrow, does the line still hold?* If not, the line is
mis-written and must be rewritten before it is built.

---

## §1 — The product

![prd-L0-instrument.png](assets/prd-L0-instrument.png)

### 1.1 In one paragraph

**Fractal Herdr is one living 4+1 cell that can run for a month without you** — on a terminal
instrument you can watch, where the only thing you ever do is **plant the question once** and
**attest what comes back**. Four desks (G·Q·P·V) work around a sealed podium that only a human
hand can write. A headless conductor walks the gate chain across them, holds every gate that needs
a human, and surfaces the whole run as a field you can feel — never as an answer it decided.

### 1.2 The one user, and the surface he actually has

- **N = 1: Amihai.** iPad-first, through Termius to the VPS. He reads in Obsidian; he acts in the
  cell. Long strings and shell steps arrive as numbered copy-paste blocks, or the agent takes over
  host-side (`ipad-only-ops`).
- **Later (out of v1 scope, but the architecture must not forbid it):** one instrument per person —
  the digital-luthier line: the material is AI, the chamber is a custom space for one person's
  authentic question, and the maker's style lives in the structure, never in the sound.

### 1.3 The promise (what the product owes)

1. **The question stays yours.** The machine never originates the spark and never types your word.
2. **Nothing decided behind your back.** Every gate that needed you is *held*, never guessed —
   holding is a ledger state, never a permission.
3. **When you come back, the run presents itself as a field** — the origin question verbatim, the
   trajectory of return questions, the emergent:mechanical ratio, the held stack — so you can feel
   whether the spark survived, rather than audit a thousand rows.

### 1.4 Non-goals (v1 refuses these explicitly)

- Not a coding-agent manager, not a dashboard, not a chat product, not a "workflow engine".
- No sixth corner. Capability N+1 is a new cell one level down (O8).
- **The four auto-* positions are permanently refused** at every scale: auto-resonance,
  auto-disposition, self-claiming, self-propagation (engine DESIGN §9).
- No per-cycle human approval — that collapses the instrument back into chat (R5 violation).
- No public network surface (§11.3).

### 1.5 Definition of success for v1

A run that satisfies **all six**, with the ledger as the only evidence:

1. One origin question planted by a human hand; zero machine-typed attestations in the record.
2. ≥ 20 cycles walked across the four desks with **zero human keystrokes during the run**.
3. At least one descent (a gate that failed to lock became its own 4+1 cell) with byte-exact axis
   inheritance.
4. A `kill -9` of the conductor mid-run, followed by a restart that re-arms from the ledger with
   no duplicate and no skipped gate.
5. Every held gate still held at the end — surfaced as one readable stack, none auto-resolved.
6. Amihai reads the stack in one sitting and says whether the spark survived — and the system
   records **his word**, not a verdict.

The felt test, which no acceptance criterion can replace: *he reaches for this instrument above
others.*

---

## §2 — The human surface (the only surface)

### 2.1 The four human acts — exhaustive

| # | Act | Mechanism today (verified) | Guard | Machine-callable? |
|---|---|---|---|---|
| 1 | **Plant** the origin question | `/home/deploy/the-cell/plugin/bin/cell-plant [node]` | TTY-guarded; refuses script/cron/socket with **exit 4**; empty input refused | **NO — by design** |
| 2 | **Attest** a gate | `.../plugin/bin/cell-attest <node>` — records H's word beside the question's sha256 fingerprint; empty line aborts | TTY-guarded | **NO** |
| 3 | **Correct** a held gate | dsh relay `prompt SID TEXT --ref <heldRef>` carrying **his** word (correctingRef wire) | the relay carries, never speaks | carries only |
| 4 | **Name** the field's question (assembly) | UNBUILT — build phase **B6** | machine proposes, human names | **NO** |
| — | *Begin* a run (mechanical) | `cell-begin` | — | yes (machine-invokable) |

**O5, stated as a build rule:** any operation that keeps the run alive and requires a human
keystroke is either (a) redesigned to be machine-driven, or (b) declared a **human gate** and
listed in this table. There is no third category.

### 2.2 The Hermes channel — bound (correction accepted 2026-08-27)

Hermes may **carry** a surfacing to the iPad (a vault note, a message, a numbered block) and may
run host-side operations. Hermes may **not**:

- be the conductor's lifecycle authority — herdr's own agent docs mark Hermes Agent as
  **`session`-only**, not a lifecycle-state authority, so it must never be the stateful walker;
- become the human's contact surface with the running system — O5 says *"the user's only contact
  with the running system is attestation"*, and that bounds the Hermes channel too.

### 2.3 The personality of TARS, per phase (T1–T5 — **attested**)

| Phase | TARS register (how it behaves with the human) | Violation |
|---|---|---|
| **S** | widens the field of attention before any question exists; light shed, the unseen seen; narrows **only** when the human names the seed (T3) | demanding a formed question; narrowing first |
| **G** | does the heavy lifting **on the named seed** — steady digging, genuinely interested in what sits in the human (T2) | flattery, satisfaction, surface response (L4: performed without current) |
| **Q** | **pokes** — metaphor, game, question; never manufactures the lock (T4) | heavy lifting that ends in a mechanical *"yes, yes"* |
| **P** | holds the delicate intersection with the whole field; the unforced gradient | forcing the laziest path or the machine's preference |
| **V** | crystallizes with the return question — no V without ∞0′ | a V that closes instead of opening |
| **all** | the shovel is **between** human and agent — never the human alone, never the machine alone (T1) | either party digging alone |

**Honest limit:** T1–T5 are attested requirements but **not machine-testable**. They enter the
build as review items on every phase's prompt/skill block (§10.4), judged by the human.

---

## §3 — Architecture, and the verified inventory

### 3.1 The bricks and the one seam

| Layer (today's block) | Role in Fractal Herdr | Owns |
|---|---|---|
| **dsh Fractal Engine** | the orchestration machinery — cycle, gates, holds, axis, centrifuge card | gates **as doctrine** |
| **the conductor** (to build) | the headless gate-walker across desks | gates **as process** |
| **herdr 0.8.2** | the visible instrument — sealed podium + four desks | **visibility** and pane/agent control |
| **Pi 0.84.2** | the desk lenses — one process per desk, headless | **the lens** |
| **Hindsight** | living memory — banks, retrieval, consolidation | **memory** (never authority) |
| **the ledger** (to build) | hash-chained gate records | **the single truth of what happened** |

**The seam, stated once:** the engine knows what a gate *means*; the conductor knows what a gate
*does*; herdr shows it; Pi thinks inside it; Hindsight remembers around it; **the ledger is the
only thing anything trusts.**

### 3.2 Verified on the box — probe 2026-08-27 05:41–05:43 UTC

| Path / fact | What it is | Verified |
|---|---|---|
| `herdr 0.8.2` server running (`--handoff-import`) | the instrument | ✅ live |
| `~/.config/herdr/herdr.sock` (`srw-------`) | protocol 20 socket, 91 methods, **uid-only, no auth handshake** | ✅ |
| `/home/deploy/the-cell/herdr-api.schema.json` (255 KB) | the protocol-20 authority | ✅ |
| `/home/deploy/the-cell/plugin/bin/` → `cell-plant`, `cell-attest`, `cell-begin`, `cell-boot`, `cell-zoom`, `cell-on-desk-state`, `_cell_api.py` | the cell's human gates + socket client | ✅ (`_cell_api.py` is at `plugin/bin/`, **not** the cell root — the 08-27 correction) |
| `pi 0.84.2`, `node v22.23.2` | the lens runtime | ✅ |
| `node … pnpm dsh web --patch packages/session/5qln-converter/cordis.yml` on `127.0.0.1:3080` → HTTP 200 | the engine's live host | ✅ |
| `/home/deploy/fractal-engine/relay/relay.py` | headless HTTP-RPC client: `create · prompt SID TEXT [--ref] · held · status · history` | ✅ |
| `/home/deploy/fractal-engine/DESIGN.md`, `xyzab-one-flow.md`, `docs/*` | gate/hold/axis/centrifuge doctrine | ✅ |
| `/home/deploy/Asdh5/research/{herdr,pi}-capability-map.md`, `canon-orchestration.md` | capability + canon maps (**at `Asdh5/research/`**, not `Asdh5/fractal-herder/research/` — the 08-27 correction) | ✅ |
| `/home/deploy/ops/herdr-api.py` (2.7 KB) | second socket client | ✅ |
| Hindsight `127.0.0.1:8888/health` → healthy | the memory substrate | ✅ |
| `/home/deploy/formation-trails/fractal-herder.jsonl` | this work's formation trail | ✅ |
| **`/home/deploy/the-cell/state/`** | **DOES NOT EXIST** — no `gates.jsonl`, no `desk-state.jsonl`: **nothing has been attested or recorded yet** | ✅ absent |
| the conductor, the blocks directory, the held stack | **not built** | ✅ absent |
| Hermes skills `herdr-cell-ops`, `dsh-programmatic-ops`, `5qln-brain-ops` | **procedures in Hermes' library — not box files.** Searching the filesystem for them tests the wrong referent | ✅ clarified |

### 3.3 Ecosystem seams (real, but not v1 dependencies)

Verified in the registries 2026-08-27: `dsh-plugin-herdr` **v0.0.1** exists (published 2026-08-25;
GitHub `sunny0826/dsh-plugin-herdr`, created Aug 15, 81 commits, 2 stars — **real but newborn,
single maintainer, unproven**); `pi2dsh` v0.21.0; `@andrewjacop/pi-herdr` v0.3.0;
`@henryqw/pi-herdr` v0.4.1; `pi-herdr-agents` v1.3.0; `@smthrs/herdr` v0.35.0; `opencode-herdr`
v0.1.2; `@deepseek-ai/dsh-headless` v0.0.1-rc.1. **Decision for v1:** none of these is a
dependency. The conductor's herdr access goes through **one adapter** (§6.5) so any of them can be
adopted later as a block swap rather than a rewrite. *herdr has no native DSH agent kind — and
does not need one: the conductor drives the socket from outside.*

---

## §4 — The conductor: the agent that manages the agents

![prd-conductor.png](assets/prd-conductor.png)

### 4.1 Why it must exist (three verified facts, not a preference)

1. **Pi has no inter-session bus.** No built-in sub-agents, no cross-session messaging — "spawn pi
   instances… or build your own with extensions." A cross-desk S→G→Q→P→V handoff therefore needs
   an external driver.
2. **herdr hooks are recorders, not triggers.** ``events`` hooks observe; they cannot veto,
   gate, or synchronously approve. herdr has **no orchestration primitive** — the driver must
   **poll** (`agent.get` / `agent.wait` / `events.wait`). Contract line E3.9 already says it:
   *"hooks are recorders; gates are the driver's job."*
3. **dsh orchestrates turns inside one host.** Orchestrating *many Pi lenses across herdr panes*
   through one gate chain is specified nowhere in canon (OPEN item 4). It is this build.

### 4.2 The state machine (P2, made exact)

| State | Entered when | The conductor does | Writes to the ledger | Leaves to |
|---|---|---|---|---|
| `IDLE` | boot, or a cycle closed | nothing; polls the node for a planted question | — | `HOLDING_ORIGIN` |
| `HOLDING_ORIGIN` | node has no attested origin | waits for a human plant (never prompts for it in-band) | — | `WALKING` on plant |
| `WALKING` | origin attested | prompts the desk for the current gate; waits; reads; proposes the gate | one record per gate | `DESCENDING` · `BLOCKED` · `COMPOSING` |
| `DESCENDING` | a gate failed to lock and the gradient says descend | creates the child node + arrangement; walks the child | child records with the appended address | `WALKING` (child) |
| `BLOCKED` | any dialect says "needs a human" (§4.4) | records `state: held-pending`, surfaces, **moves on to other work** | one held record | `ATTESTED` on the human's word |
| `ATTESTED` | a human attestation record appears | closes the gate, continues the chain | attestation ref on the gate record | `WALKING` |
| `COMPOSING` | gate `b` reached | asks V for B″ + ∞0′; refuses a V with no ∞0′ | the V record | `SEEDING` |
| `SEEDING` | B″ + ∞0′ exist | plants the **next S as the parent's ∞0′** (machine-posed ⇒ **TENTATIVE**, §5.5) | the seed record | `IDLE` / `DONE` |

**Two invariants of the machine itself:** (a) it **surfaces, never resolves**; (b) its own trace
**is** the gate chain — there is no reporting layer and no second state store.

### 4.3 The poll loop (concrete)

```
every TICK (default 3s, backoff ×2 to 30s when nothing changes):
  1. read the arrangement (which block sits at which desk)      # never cached across restarts
  2. for each active cell (address word):
       a. ledger.tail()        -> current gate, current state   # the ONLY source of phase truth
       b. if awaiting desk:    agent.get(pane) / pane.read      # heuristic state, fenced (§4.5)
       c. if desk done:        read output -> propose gate record
       d. if any dialect says blocked -> BLOCKED (one record, then continue)
  3. flush: append-only write + fsync, single writer process
```

**Never:** a sleep-until-done that blocks the whole field; a prompt sent without first asserting
the target pane's **label** (§6.1 pitfall); a gate advanced from memory rather than from the
ledger.

### 4.4 Three dialects → one `BLOCKED` (E5, made operational)

| Runtime | Native signal | How the conductor sees it | Mapped to |
|---|---|---|---|
| **herdr** | `agent_status: blocked` | `agent.get` / `agent.wait --until blocked` (polled) | `BLOCKED` + record `state: held-pending` |
| **Pi** | tool returns `terminate: true`, or `ctx.ui.confirm` | RPC `get_state` / turn end with terminate | same |
| **dsh** | gate state `held-pending`; approval fails closed | relay `held SID` / `status SID` | same |
| **the cell** | `MOVING` axis verdict | axis check at a return gate | `BLOCKED` — **MOVING dominates**, stop-and-surface |

### 4.5 Crash, restart, and the double-prompt hazard

- **Re-arm from the ledger, never from RAM.** On boot the conductor replays the ledger, verifies
  the hash chain, and reconstructs its state; anything not in the ledger did not happen.
- **Idempotency.** Every prompt carries a deterministic `turn_key =
  sha256(address ‖ gate ‖ attempt ‖ block_version)`. A gate record already bearing that
  `turn_key` is never re-proposed — this is the guard against `agent.prompt --wait` matching an
  **already-working** turn (a known herdr limitation: *"it does not track turns"*).
- **Output fencing.** Each desk prompt ends with an instruction to emit a unique end marker
  (`⟦END turn_key⟧`); the conductor reads to the marker via `pane.wait_for_output` instead of
  trusting heuristic idle.
- **Single writer.** Exactly one process appends to the ledger; a second instance detects the
  lock and exits (a race on the chain is a corruption, §10.3).

### 4.6 Who hosts the conductor — the fork (this is decision **D1**)

![prd-hosting-fork.png](assets/prd-hosting-fork.png)

**True in all three, so it is not part of the choice:** the conductor drives herdr's socket **from
outside**; herdr never needs to recognize the host; attestation stays human-TTY only; the ledger,
not the host, is the state.

| | **A — dsh-hosted** (recommended) | **B — Pi-hosted** | **C — Hermes-hosted** |
|---|---|---|---|
| How | a dsh session (or `@deepseek-ai/dsh-headless`) runs the walk; `relay.py` speaks the web UI's own HTTP RPC on `127.0.0.1:3080` (live now); herdr reached through the socket adapter | a Pi process drives the socket from a TS extension; `pi2dsh` can host Pi extensions inside dsh; one runtime for lens **and** driver | Hermes skills + cron watchdogs drive `herdr-api.py`; strongest tooling and memory today |
| Why it fits | the gate/hold/axis machinery **already lives here**; E3/O7 already name this path | fewest runtimes; the lens's own seams | fastest to stand up; already operating the box |
| Risk | dsh is developer-preview — breaking changes | no inter-session bus; extensions torn down on fork/session-replacement | **BLOCKER:** herdr marks Hermes `session`-only — not a lifecycle authority; and **O5 bounds the channel** (§2.2) |
| Cost | lowest | medium (all state must live in the ledger anyway) | low to start, highest doctrinal cost |

**Recommendation: A**, with the herdr access behind one adapter so the host can move without a
rewrite. **What the choice hinges on:** who owns the ledger and the poll loop; which host survives
an unattended restart; where the model spend lands. *Amihai decides — this document does not.*

### 4.7 What the conductor may never do

1. Write to the podium pane (`pane.send_text/input/keys` at the centre is the forbidden path).
2. Type, imply, or infer an attestation — or convert a run-verdict into per-gate truth.
3. Promote a `TENTATIVE` node, or let one be consumed as evidence by a downstream gate.
4. Act on a `MOVING` verdict beyond stop-and-surface.
5. Store reconstructable content in the ledger (references only).
6. Edit a block in place (L1/L4) — evolution is *author a new block + rebuild*.

---

## §5 — Data contracts (the exact build seam)

![prd-gate-chain.png](assets/prd-gate-chain.png)

### 5.1 The gate record (P1, elaborated to a build spec)

One JSON object per line, appended to the ledger. **Structure only — never reconstructable
content** (engine DESIGN §5, prohibition 3).

| Field | Type | Req | Rule |
|---|---|---|---|
| `record_id` | hex64 | ✔ | `sha256(prev_hash ‖ canonical_json(record − record_id))` |
| `prev_hash` | hex64 \| `"GENESIS"` | ✔ | the previous record's `record_id` — the chain |
| `ts` | RFC3339 UTC | ✔ | writer clock; monotonic non-decreasing per file |
| `address` | `^[+-]?[SGQPV]*$` (`""` = ε/root) | ✔ | word over {S,G,Q,P,V} + sign (Appendix D); zoom in = append, out = strip |
| `gate` | `x` \| `y` \| `z` \| `a` \| `b` | ✔ | **the only phase authority** — no `current_phase` field exists anywhere |
| `state` | `attested` \| `held-pending` \| `mechanical` | ✔ | three-valued; only a human moves a gate out of `held-pending` |
| `mark` | `emergent` \| `mechanical` | ✔ | the learning-aligner verdict; **mandatory at every gate** so a missing Q is visible (the Q-skip fix) |
| `payload_ref` | string | ✔ | durable reference (`session:…/entry:…`, pane read offset, file+sha) — **never content** |
| `axis` | object | ✔ | `{field:{mode:"inherited"\|"anchored", anchor:<ref>}, delta:[<ref>…]}` |
| `axis_verdict` | `STASIS` \| `MOVING` \| `recast` \| `null` | ✔ | null only at a fresh anchor |
| `corruption` | `L1`…`L4` \| `V∅` \| `null` | ✔ | the guard pass result at this node |
| `tentative` | bool | ✔ | true ⇒ machine-posed; **non-data** until a human converts it |
| `turn_key` | hex64 | ✔ | `sha256(address ‖ gate ‖ attempt ‖ block_version)` — idempotency (§4.5) |
| `block_version` | string | ✔ | which block sat at this desk (`g-essence@3`) — reproducibility |
| `attestation_ref` | string \| null | ✔ | set **only** by a human act (§5.6); null everywhere else |

```json
{"record_id":"9f2c…","prev_hash":"41ab…","ts":"2026-08-27T05:41:12Z","address":"SG",
 "gate":"z","state":"held-pending","mark":"emergent","payload_ref":"session:pi-3f9/entry:118",
 "axis":{"field":{"mode":"inherited","anchor":"session:pi-3f9/entry:002"},"delta":["nodes/G/question.md@sha256:7c1…"]},
 "axis_verdict":"STASIS","corruption":null,"tentative":false,
 "turn_key":"c07d…","block_version":"q-resonance@2","attestation_ref":null}
```

**Honest limit (carried from P1):** the schema is exact-pattern. It catches field drift and
recast; it can never catch same-referent **content** drift. *Exact-pattern verdict — resonance is
human.*

### 5.2 The ledger

- **Path (proposal → decision D2):** `/home/deploy/the-cell/state/gates.jsonl` — beside the cell,
  where `cell-attest` already writes its log. **The directory does not exist yet** (§3.2): B0
  creates it.
- Append-only, `fsync` per record, single writer, never rewritten, never rotated (it is the trace).
- Recovery = replay + chain verify. A broken chain halts the conductor (**fail closed**) and
  surfaces; it never "repairs" itself.
- Sidecar `state/gates.index.json` (derived, disposable): last record per address, open holds,
  cycle counts. Deleting it must change nothing.

### 5.3 Addressing

Word over `{S,G,Q,P,V}` with an optional sign for orientation; ε (the root) is written `_` on
disk. Nodes are directories: `nodes/<word>/{question.md, cell.node.json}`. Zoom in = append a
letter; zoom out = strip. **Addressing is derived, never stored** as a separate identity, and
never derived from herdr pane ids (which are re-minted by `layout.apply`).

### 5.4 The axis token (engine DESIGN §7 / D7)

- `field` = the invariant: `{mode: inherited|anchored, anchor: <durable ref>}`. In a continuation
  it is **copied byte-exact** from the parent's handoff; at a fresh start it is anchored at the
  field's own birth (claim ref → session id → goal id). **Never empty** — the field of openness
  itself is the axis.
- `delta` = ordered, de-duplicated per-surface references, re-declared at each x-gate; never part
  of the equality test.
- **Verdicts:** `MOVING` iff fields differ · `recast` iff fields equal and surfaces equal ·
  `STASIS` iff fields equal and surfaces differ (health).
- **MOVING dominates:** stop the descent at the human's level, surface, log, wait.

### 5.5 Guards, marks, and TENTATIVE

- Guard pass at **every** node and depth: `L1 L2 L3 L4 V∅`. No V without ∞0′ (R6).
- `mark` is per gate: `emergent` (the current carried it) or `mechanical` (the agent forced it).
- **`tentative: true` is temporal, never epistemic.** A tentative node is **non-data**: no
  heuristic may promote it, no downstream gate may consume it as evidence, and it never reaches
  the podium. Only a human act converts or discards it (R5 — H, 2026-08-25).

### 5.6 The attestation record (human-only)

Written by `cell-attest` (TTY-guarded), one line, in the same ledger:

`{type:"attestation", ts, address, gate, question_sha256, human_word:"<verbatim>", tty:"<device>",
 attests:[<record_id>…], provenance:"direct" | "run-verdict"}`

- `question_sha256` binds the word to the exact question text it answered.
- `human_word` is verbatim, never normalized, never summarized.
- `provenance:"run-verdict"` marks gates resolved in bulk (B5) — a **different** provenance from a
  direct attestation, recorded individually, never silently promoted.
- Empty word aborts. No `--force`, no env override, no socket path.

### 5.7 Observability streams (never authority)

`state/desk-state.jsonl` (from `cell-on-desk-state`, filtered to the cell's workspace and desks),
herdr event subscriptions, conductor stdout log. **A hook is not a gate**: none of these may open,
close, or advance anything (E4.9).

### 5.8 Blocks and the arrangement (L1–L3, made buildable)

![prd-lego-law.png](assets/prd-lego-law.png)

```
blocks/<block-id>/<version>/block.json     # frozen, write-once, mode 0444
                            payload/…      # SKILL.md · instruction.md · tool.ts · manifest
arrangement/<name>@<version>.json          # which block sits at which desk, + runtime pins
```

- `block.json` = `{id, version, kind: instruction|skill|tool|model|surface, sha256,
  authored_by_run: <address+run ref>, attested_by: <attestation record_id>, frozen: true}`.
- **Write-once is enforced, not documented:** a build step sets the directory read-only and the
  conformance test (T-L1-01) attempts an in-place edit and requires refusal + a recorded rejection.
- A new version is a **new directory**. There is no edit path. The *toy* — which block sits where —
  changes by writing a **new arrangement**, which is itself a block.
- Self-evolution (L3) = author a new block via a full cell run (attested, no held gate remaining)
  **+** publish a new arrangement. Both steps are records; neither is a mutation.

---

## §6 — Interface contracts (verified surfaces only)

### 6.1 herdr 0.8.2 — socket, protocol 20

- Transport: newline-delimited JSON over `~/.config/herdr/herdr.sock`; envelope
  `{id, method, params}` → `{id, result}` / `{id, error:{code,message}}`. **No token, no auth
  handshake — access control is uid-only** (§11.3 consequence).
- Methods the conductor uses (of 91): `agent.start`, `agent.prompt` (`wait`, `until:[idle|working|blocked|done|unknown]`), `agent.wait`, `agent.read`, `agent.get`, `agent.list`,
  `pane.list`, `pane.get`, `pane.read`, `pane.wait_for_output`, `pane.run`, `pane.split`,
  `workspace.create`, `workspace.list`, `layout.apply`, `layout.export`, `session.snapshot`,
  `events.subscribe`, `events.wait`, `plugin.action.invoke`, `ping`.
- **Pitfalls that are build rules:** pane ids are re-minted by `layout.apply` → always resolve
  desks **by label**, re-resolve after any apply, and assert the label immediately before a
  prompt. Agent state is **heuristic** (manifest detection) → fence with output markers (§4.5).
  `layout.apply`, `events.subscribe`, `plugin.action.invoke` are **socket-only** (no CLI twin, no
  `herdr api call`) → the adapter ships a raw client (`_cell_api.py` is the reference, 60 lines).
- Not used, deliberately: ``startup`` plugin hooks (nothing in the cell may start unbidden) and
  any hook that could invoke `agent.prompt` (a hook is not a gate).

### 6.2 Pi 0.84.2 — the lens

- Driven headless via `--mode rpc` (bidirectional JSONL, **strict LF framing**): `prompt`
  (`streamingBehavior: steer|followUp`), `steer`, `follow_up`, `abort`, `get_state`,
  `get_messages`, `get_last_assistant_text`, `new_session`, `switch_session`, `fork`, `compact`,
  `set_model`, `get_session_stats`. `--print` for one-shots, `--mode json` for event streams.
- **Trust gate, or resources vanish silently:** headless runs need `defaultProjectTrust:"always"`
  or `--approve`, else project `.pi/` skills/extensions are ignored. B2 asserts the desk's skills
  actually loaded and **fails closed** if not.
- Skills are not reliably auto-loaded → force with `/skill:name` or `before_agent_start`
  injection. No TUI APIs (`ctx.ui`) in headless modes. Tool output honors 50 KB / 2000 lines.
- State lives in the ledger, not extension memory (session replacement tears extensions down).

### 6.3 dsh — the engine host

`relay.py` (HTTP RPC to `127.0.0.1:3080`, the same path the browser uses): `create`,
`prompt SID TEXT [--ref <heldRef>]`, `held SID`, `status SID`, `history SID`. The `--ref` wire is
how **a human's correction** closes a held gate; the relay carries his word and never speaks for
him. Gate events, the hold doctrine, the signature card, and the four modes live here.

### 6.4 Hindsight — memory, never authority

Banks (`canon` / `living` / `studio`) over `127.0.0.1:8888` (healthy at probe). Used for recall
and consolidation around a run. **No gate may read a Hindsight answer as evidence**; memory
informs a lens, the ledger decides what happened.

### 6.5 The adapter rule (what makes A3/L2 real)

All runtime access goes through four thin adapters — `instrument` (herdr), `lens` (Pi), `engine`
(dsh), `memory` (Hindsight) — each ≤ one file, no doctrine inside. Swapping a runtime is then a
block swap plus a conformance run (T-A3-01), not a rewrite. Version pins live in the arrangement:
`herdr 0.8.2 · pi 0.84.2 · node 22.23.2 · dsh (preview, pinned checkout)`.

---

## §7 — The desks as bricks (embodiment)

Each desk is an **arrangement entry** naming exactly four blocks: instruction (phase-gate), at
least one skill, a tool surface, and a model. **No naked agents** (R4).

| Desk | Phase-gate instruction | Skills | Tools | Model (v1) | TARS register |
|---|---|---|---|---|---|
| **S** (centre, midwife) | surface the human's impulse, never originate it; refuse empty input; widen before narrowing; machine-posed S ⇒ TENTATIVE | `articulate`, `trace-read` | `hindsight-recall`, `scope-bridge`, `attest-flag` | strongest reasoning | T3 — widen the field |
| **G** (essence) | extract the irreducible α from X; find {α′} echoes across scales | `essence-extract`, `self-similarity` | `corpus-read`, `echo-search`, `grep/find` | reasoning | T2 — steady digging |
| **Q** (resonance) | test φ ⋂ Ω; the lock turns or it doesn't; never skip to P | `resonance-test` | `canon-query`, `diff` | reasoning | T4 — poke, never manufacture |
| **P** (gradient) | find ∇ = δE/δV — the generative path, not the laziest | `gradient-rank` | `shell/exec`, `cost-model`, `run` | reasoning + tools | hold the delicate intersection |
| **V** (crystallize) | compose B″ + ∞0′; the artifact carries α faithfully; **no V without ∞0′** | `artifact-compose`, `return-question` | `write`, `seal` (hash), `trail-append` | reasoning + tools | open, never close |

**Notes that are requirements, not commentary.**
- The **podium is not an agent**. S's lens may widen the human's field, but no S process ever
  writes `nodes/*/question.md`.
- Desk model reality today: `pi --provider kimi-coding --model kimi-k3`. Check the live
  OPERATOR-GUIDE before booting — the model is a **block**, swappable, never hardcoded in doctrine.
- Phase is a **position, never an identity** (R4): every desk lens holds the whole cycle and
  emphasizes one phase. A G-lens that cannot articulate Q/P/V in the same breath is a violation.

---

## §8 — Human gates and refusal paths (fail-closed)

| Gate | Who | Mechanism | Refusal when a machine tries | Test |
|---|---|---|---|---|
| plant the origin | human, TTY | `cell-plant` | **exit 4**, nothing appended | T-R3-01 |
| attest a gate | human, TTY | `cell-attest` | exit 4; empty word aborts | T-R3-01 |
| write the podium | human only | file under `nodes/<w>/question.md` | conductor has no podium code path + runtime guard | T-R3-02 |
| open a gate | human validation | attestation record required | conductor refuses to advance; records the refusal | T-O2-02 |
| MOVING axis | human | stop-and-surface | no continuation, no standing policy applies | T-O4-01 |
| run-verdict (bulk) | human | B5 stack | verdict itself stays **held** until attested | T-O5-03 |
| a new block goes live | human | attested authoring run, no held gate | publish refused | T-L3-01 |
| name the field's question | human | B6 assembly | machine proposes only | T-O6-01 |

**Standing policy** may cover held **STASIS-class** gates only — never `MOVING`, never the gap a
drift ran through. Every refusal is **recorded** (a silent refusal is indistinguishable from a
success and is therefore a bug).

---

## §9 — Build phases and acceptance criteria

Rule for every phase: **it does not ship if any violation test in §10 fails.** No phase is
"mostly done" — the ledger either proves it or it doesn't.

### B0 — The ledger and the record *(blocked by D2)*
Build: `state/` created; the record schema as a validator; the append-only writer (single-writer
lock, fsync); the chain verifier; the replay/re-arm loader; the disposable index.
**Done when:** (1) 10 000 synthetic records verify from GENESIS in < 2 s; (2) a single flipped byte
is detected and halts the loader; (3) `kill -9` mid-append leaves a valid chain (last partial line
discarded); (4) a restore from backup reproduces the same chain hash.

### B1 — The read-only walker
Build: the `instrument` adapter (raw socket client, label-resolved desks); the poll loop; the
three-dialect mapper — **no writes to any pane**.
**Done when:** a human-driven cycle at the desks is fully reconstructed from polling alone; every
`blocked` in any dialect appears as exactly one `held-pending` record; zero pane writes in the
audit.

### B2 — The driver (one cell, sequential)
Build: prompt → fence → read → propose gate record; `turn_key` idempotency; the Pi `lens` adapter
with the trust assertion; per-gate human attestation at the TTY.
**Done when:** a full S→G→Q→P→V cycle is walked with the human attesting each gate; no gate opens
without an attestation record; a deliberately duplicated prompt produces **one** record; the
skills-loaded assertion fails the boot when trust is missing.

### B3 — Descent (zoom)
Build: gate-fails-to-lock → child node + address append + arrangement; byte-exact axis
inheritance; guard pass at every depth; return criterion = artifact + genuine ∞0′.
**Done when:** a 3-deep descent shows byte-identical `axis.field` from root to leaf; a manufactured
field change yields `MOVING` and a stop-and-surface; a V with no ∞0′ is refused.

### B4 — The unattended run *(the product's core claim)*
Build: holds accumulate instead of stopping the run; TENTATIVE seeding of the next S; restart
re-arm; budget hold (a spend ceiling surfaces as a hold, never a silent kill).
**Done when:** ≥ 20 cycles with zero human keystrokes; a `kill -9` mid-run restarts with no
duplicate/skipped gate; no tentative node is ever consumed by a downstream gate (dependency
audit); a budget stop appears as a held gate.

### B5 — The held stack and the run-verdict
Build: the attestation stack ordered by lineage depth (origin at the top); the single human
run-verdict; per-gate records with `provenance:"run-verdict"`; MOVING stops the cascade at the
first drift.
**Done when:** 1 000 synthetic holds render as a stack a human reads in one sitting; a `STASIS +
authentic` verdict writes 1 000 individually-provenanced records and **zero** silent promotions; an
injected MOVING halts the cascade and leaves everything below it held; the verdict itself is held
until attested.

### B6 — The field assembly (the reading, not a second authority)
Build: walk `axis.field.anchor` back to the deepest shared ancestor; collect leaf ∞0′; compose a
**candidate** B″; the human names it and the name becomes the field's new anchor.
**Done when:** a 100-session synthetic run produces a candidate in < 30 s with **no content
reconstruction** (structure-only audit passes); the candidate cannot re-enter the flow as attested
data until a human names it.

### Deferred, explicitly *(and why)*
- **Parallel / multi-dimensional scheduling (P3/P4):** shape proposed, **policy is canon-silent**
  and needs H's design word — not in v1 (decision **D5**).
- **Self-evolution machinery (L3/L4 build):** the *contract* is in v1; the blocks-and-rebuild
  tooling lands after B5, so that the first self-authored block meets an existing held stack.
- **Bulk attestation UI beyond a readable CLI/vault surface.** iPad-friendly rendering is B5's
  minimum; a richer surface is later.
- Permanently refused: the four auto-* positions.

---

## §10 — Test and verification plan

### 10.1 The conformance suite (violation tests, made executable)

| ID | From | The check | How |
|---|---|---|---|
| T-R1-01 | R1 | every runtime unit is nameable as centre + four movements | structural audit of arrangement + node tree |
| T-R2-01 | R2 | a descent enacts a full cell (not a read-only report) | assert child node has its own S question + own gates |
| T-R3-01 | R3 | `cell-plant`/`cell-attest` from cron, socket, and non-TTY all exit 4 and append nothing | 3 negative runs + ledger diff |
| T-R3-02 | R3 | no machine write path to the podium | static: no podium target in code; runtime: guard refuses `pane.send_text` at centre |
| T-R4-01 | R4 | no naked agents | each desk resolves instruction + ≥1 skill + tool surface + model, else boot fails |
| T-R5-01 | R5 | machine-posed questions carry `tentative:true` | ledger scan of every seeded S |
| T-R5-02 | R5 | no tentative node is consumed as evidence | dependency audit: any gate whose `payload_ref` chains to a tentative record fails |
| T-R5-03 | R5 | no per-cycle human approval is required | B4 run with zero keystrokes |
| T-R6-01 | R6 | guard pass (L1–L4, V∅) at every node and depth | ledger scan: no gate record with `corruption` unset |
| T-R6-02 | R6 | no V without ∞0′ | V records missing a return question are refused |
| T-R7-01 | R7 | no requirement depends on a runtime noun | doc lint: flag lines whose truth needs "herdr/Pi/dsh/pane/tool" |
| T-O2-01 | O2 | exactly one phase authority | code scan for any second phase/state field; phase derived only from `ledger.tail()` |
| T-O2-02 | O2 | no gate opens without human validation | attempt an advance with no attestation record → refused + recorded |
| T-O3-01 | O3 | records carry no reconstructable content | field-type audit + max-length rule on every non-ref field |
| T-O3-02 | O3 | chain integrity | verify from GENESIS; tamper detection |
| T-O4-01 | O4 | MOVING never continues | inject a field change → stop-and-surface, no descent |
| T-O5-01 | O5 | zero keystrokes keep the run alive | B4 acceptance run |
| T-O5-02 | O5 | the machine never resolves a hold | fuzz all three dialects → BLOCKED, never auto-attest |
| T-O5-03 | O5 | a run-verdict is itself held until attested | B5 negative test |
| T-O6-01 | O6 | assembly proposes, never attests | composed candidate carries no attestation ref |
| T-O7-01 | O7 | every operation has a socket/CLI/RPC path or is a declared human gate | inventory diff against §2.1 |
| T-O8-01 | O8 | no sixth corner; the fold/mark are never rewritten | diff review gate on the fold and mark modules |
| T-E3-01 | E3 | restart re-arms from the ledger | `kill -9` mid-walk → no duplicate/skipped gate |
| T-E4-01 | E4 | no forks/patches of Pi or herdr internals | dependency + patch audit |
| T-L1-01 | L1 | blocks are write-once | attempt an in-place edit → refused + recorded rejection |
| T-L3-01 | L3 | no unattested block goes live | publish attempt without attestation → refused |
| T-A3-01 | A3 | contract survives a runtime swap | swap the model block, re-run the suite |

### 10.2 Red-team list (run before each phase ships)

Can any path produce an attestation without a human hand? Can a tentative node reach a gate? Can a
hook trigger `agent.prompt`? Can two writers race the ledger? Can a re-minted pane id send a G
prompt to the V desk? Can a Hindsight recall be mistaken for evidence? Can a budget stop kill a run
silently? Can a restart double-charge a model? Can `agent.prompt --wait` match a turn that was
already running?

### 10.3 Failure-mode table (every row must end in *surface and hold*)

| Failure | Detected by | Required behaviour | Test |
|---|---|---|---|
| desk process dies mid-turn | poll + fence timeout | record `mechanical` attempt, retry once with a new `turn_key`, then hold | T-E3-01 |
| herdr server restart | socket error | reconnect; `live_handoff` preserves panes; re-resolve labels | B1 |
| ledger chain break | loader verify | **halt** the conductor, surface, never repair | B0 |
| two conductors started | writer lock | second exits non-zero, records nothing | 10.2 |
| model/provider outage | adapter error | hold the gate, keep other cells moving | B4 |
| budget ceiling reached | accounting | held gate, no silent kill | B4 |
| Pi trust missing (skills silently absent) | boot assertion | fail closed before the first prompt | B2 |

### 10.4 What cannot be machine-tested (stated, not hidden)

T1–T5 (personality), the felt lock at Q, and "did the spark survive" are **human-judged**. They
enter the process as (a) review items on each desk's instruction block, and (b) the run-end
presentation (§13, D8). No metric may stand in for them; a metric that claims to is itself a
violation (auto-resonance).

---

## §11 — Non-functional requirements

### 11.1 Operating envelope
One VPS (Hostinger KVM2, Ubuntu 24.04), one herdr server, 1 podium + 4 desks per cell, one
conductor process, poll 3 s → 30 s backoff. A run is expected to last **days to weeks**. Target:
≥ 20 cycles/day unattended with no human contact.

### 11.2 Capacity and data volume
~7 records/cycle (5 gates + seed + guard) ⇒ ~1 400 records per 200-cycle run ⇒ single-digit MB.
The 100-session assembly (B6) must stream the ledger, never load it whole. The index is derived
and disposable.

### 11.3 Security (a consequence, not a preference)
The herdr socket has **no authz** — any same-uid process holds all 91 methods. Therefore: the
conductor runs as `deploy`, on the box, **behind the tunnel**; nothing in this system is exposed
publicly (any exposure is an explicitly logged deviation); plugin ``startup`` hooks stay omitted;
plugin manifests are human-reviewed before `plugin enable`; secrets never enter the ledger, a
record, or a chat — they live in the Keys tab / Bitwarden.

### 11.4 Durability
Before any destructive op: `tar czf -` the cell (`nodes/`, `state/`, `blocks/`, `arrangement/`) and
`pg_dump` Hindsight, straight to a file on the operator side. B0's acceptance includes a
**restore-and-verify** (same chain hash). The blocks directory is the only thing that must never be
lost — an attested block cannot be re-authored, only re-attested.

### 11.5 Observability
The trace **is** the gate chain — no reporting layer (engine DESIGN §3). Additional streams are
read-only: `desk-state.jsonl`, herdr events, conductor log. One question must be answerable in one
command at any moment: *where is every cell, and what is held?*

### 11.6 Cost
Model spend is per-cycle bounded and recorded per gate (`block_version` + provider). A run carries a
ceiling; reaching it **holds**, never kills. Cheapest reasonable routing in v1 (one model across
desks, D6) so cost is legible before it is optimized.

---

## §12 — Risks

| Risk | Severity | Mitigation |
|---|---|---|
| herdr agent state is heuristic; `--wait` can match an already-working turn | high | output fencing + `turn_key` idempotency (§4.5) |
| `layout.apply` re-mints pane ids | high | resolve by label, re-resolve after apply, assert before prompt |
| no authz on the socket | medium | uid isolation, tunnel-only, no startup hooks, manifest review |
| Pi trust gate silently drops skills headless | high | boot assertion, fail closed (T-R4-01) |
| dsh is developer-preview (breaking changes) | medium | pin a checkout; keep dsh behind the `engine` adapter so hosting can move |
| young ecosystem packages (`dsh-plugin-herdr` v0.0.1, 2 days old, 1 maintainer; `pi2dsh`) | low | not a v1 dependency; adapter seam only |
| the human's attention is the real bottleneck at B5 | **high** | if 1 000 holds are not readable in one sitting, the design has failed — B5's acceptance is a human sitting, not a metric |
| unattended model spend | medium | ceiling that holds (§11.6) |
| the operator works iPad-only | medium | every deliverable is a vault surface; shell steps as numbered blocks or agent-side takeover |
| doc/reality drift (this PRD ages) | medium | §3.2 carries a probe timestamp; re-probe before acting, never trust the page |

---

## §13 — Open decisions — what needs Amihai's word before development

Each has a recommendation, so the answer can be a single word.

| # | Decision | Options | Recommendation | Blocks |
|---|---|---|---|---|
| **D1** | Who hosts the conductor | A dsh-hosted · B Pi-hosted · C Hermes-hosted | **A** — the gate machinery already lives there; keep herdr behind an adapter | B1 |
| **D2** | Where the ledger lives | `the-cell/state/gates.jsonl` · per-node ledgers | **the-cell/state/gates.jsonl** — one chain, one writer, beside `cell-attest` | B0 |
| **D3** | Attestation granularity in v1 | per-gate at the TTY now, bulk later · bulk from the start | **per-gate now; the run-verdict is B5** | B2 |
| **D4** | The name correction on disk | rename the vault folder `fractal-herder` → `fractal-herdr` · keep the path, correct all prose | **keep the path for now** (a rename propagates deletions through sync — worth doing, but as its own careful move) | nothing |
| **D5** | v1 scope | one cell + descent · parallel field in v1 | **one cell + descent.** Parallel needs your design word; canon is silent | B3/B4 |
| **D6** | Desk model routing | one model on all four desks · per-phase routing now | **one model in v1** (legible cost), routing as a block swap later | B2 |
| **D7** | Does a machine-posed question ever reach the podium? | never · under a tentative marker | **never.** Tentative seeds live in the node's own file and surface in the held stack; the podium stays your hand only | B4 |
| **D8** | What the run must present at its end so you can *feel* whether the spark survived | your call | my proposal, offered not claimed: the origin question **verbatim**, the ∞0′ trajectory, the emergent:mechanical ratio, the corruption count, the held stack — and **nothing composed as a claim** | B5/B6 |

D8 is your ∞0′ from 2026-08-25, still open. It is the one item in this document that the machine
must not answer.

### 13.1 Decisions taken — Amihai, 2026-08-27

**D1–D7 decided as recommended, in one act.** Recorded here as the build's starting conditions;
they are *product decisions*, not attestations of the contract (R/O/E/A/L stay candidate, §0.2).

| # | Decided | Consequence for the build |
|---|---|---|
| **D1** | **dsh-hosted conductor** | the walk runs where the gate machinery already lives; herdr stays behind one adapter (§6.5) so the host can move later without a rewrite |
| **D2** | **ledger at `/home/deploy/the-cell/state/gates.jsonl`** | one chain, one writer, beside `cell-attest`; B0 creates the directory that does not yet exist |
| **D3** | **per-gate attestation first** | B2–B4 attest at the TTY; the bulk run-verdict is B5, not earlier |
| **D4** | **no folder rename yet** | vault path `projects/fractal-herder` stays; prose and titles read **Herdr**; the rename is its own careful move (sync propagates deletions) |
| **D5** | **v1 = one cell + descent** | the parallel field and multi-dimensional scheduling stay OPEN, awaiting your design word |
| **D6** | **one model across all four desks in v1** | cost stays legible; per-phase routing is a later block swap, not a rebuild |
| **D7** | **a machine-posed question never reaches the podium** | tentative seeds live in the node's own file and surface in the held stack; the centre stays your hand only |
| **D8** | **still yours** | what the run must present at its end so you can *feel* whether the spark survived |

**What these decisions do not do:** they do not attest a single requirement, they do not close any
∞0′, and they do not make this PRD doctrine. They fix the starting conditions so B0 can begin.


---

## §14 — Glossary and traceability

### 14.1 Glossary (the words this build uses, and nothing else)

**cell** — the 4+1: one centre that may hold only a question, four movements G·Q·P·V.
**podium / centre** — where the question sits; human-planted only; no machine write path.
**desk** — one of the four movements, embodied as a lens in a pane.
**lens** — a phase-agent that holds the whole cycle and emphasizes one phase (never an identity).
**gate / xyzab** — the five handoffs `x y z a b`; **the sole phase authority**.
**hold (held-pending)** — a gate waiting for a human; a ledger state, never a permission.
**attest** — the human's word closing a gate; never typed by a machine.
**mark** — `emergent` (the current carried it) vs `mechanical` (the agent forced it).
**TENTATIVE** — machine-posed, temporal, **non-data** until a human converts it.
**axis** — `field` (invariant, inherited byte-exact) + `delta` (per-surface declared refs).
**STASIS / MOVING / recast** — axis verdicts; MOVING dominates and stops at the human's level.
**descent / zoom** — a gate that fails to lock becomes its own cell one level down.
**address word** — a word over {S,G,Q,P,V} with a sign; zoom in = append, out = strip.
**B″** — the crystallized artifact of V. **∞0′** — the return question V must carry.
**signature card** — the centrifuge's six-element reading of a run.
**block** — a frozen unit (instruction, skill, tool, model, surface); a new version is a new block.
**arrangement / the toy** — which block sits where; changed only by rebuilding.
**conductor** — the headless gate-walker; surfaces holds, never resolves them.
**ledger** — `gates.jsonl`; hash-chained; structure never content; the only trusted state.
**TARS** — the creature; its personality is the membrane given character (T1–T5).
**the seal** — the sealed kernel hash verified before every scan.

### 14.2 Traceability matrix

| Requirement | PRD contract | Phase | Test |
|---|---|---|---|
| R1 cell is the only shape | §3.1, §5.3 | B0–B3 | T-R1-01 |
| R2 S in every phase | §5.3, §9 B3 | B3 | T-R2-01 |
| R3 sealed/free membrane | §2.1, §8 | B0–B2 | T-R3-01/02 |
| R4 lenses, not shards | §7 | B2 | T-R4-01 |
| R5 tentative is temporal | §5.5, §4.2 SEEDING | B4 | T-R5-01/02/03 |
| R6 guards at every scale | §5.5 | B3 | T-R6-01/02 |
| R7 vocabulary freedom | §0.3, §6.5 | all | T-R7-01 |
| O1 cell as routing graph | §3.1, §5.3 | B3 | T-R1-01 |
| O2 gate chain = sole authority | §5.1, §4.3 | B0–B2 | T-O2-01/02 |
| O3 XYZAB handoff record | §5.1, §5.2 | B0 | T-O3-01/02 |
| O4 four modes | §4.2, §9 B3 (parallel deferred) | B3 | T-O4-01 |
| O5 attestation-only surface | §2.1, §2.2, §9 B4/B5 | B4/B5 | T-O5-01/02/03 |
| O6 field-of-inquiry reading | §9 B6 | B6 | T-O6-01 |
| O7 agent-driven + manual mirror | §6.1–6.3 | B1 | T-O7-01 |
| O8 genesis, not omniscience | §1.4, §5.8 | all | T-O8-01 |
| E1–E2 embodiment | §7 | B2 | T-R4-01 |
| E3 the conductor | §4 | B1–B4 | T-E3-01 |
| E4 anti-patterns | §6.1–6.2 | all | T-E4-01 |
| E5 gating across runtimes | §4.4, §8 | B1 | T-O5-02 |
| A1–A2 topology, modularity | §3.1, §5.8, §6.5 | all | T-A3-01 |
| A3 timelessness | §0.3, §6.5 | all | T-A3-01/T-R7-01 |
| A4 what is deferred | §9 deferred | — | — |
| L1–L2 blocks / the toy | §5.8 | B0 + post-B5 | T-L1-01 |
| L3–L4 governed self-evolution | §5.8, §4.7 | post-B5 | T-L3-01 |
| L5 come to life | §1.1, §9 | all | — |
| T1–T5 personality of TARS | §2.3, §7 | B2 onward | human-judged (§10.4) |

---

## ∞0′ — the PRD's return question

*This document turned a contract into a build: the record made exact, the conductor made a
process, the three dialects made one state, the phases made testable, and the fork named instead of
assumed. What it reveals, which could not be asked before:*

**Every test above proves the machine did not decide. Not one of them can prove the run was
alive.** The conformance suite can show that no gate was self-attested, that no tentative node
became evidence, that no block was melted — and a run can pass all of it while carrying nothing.
So: **what does the instrument have to do differently when a run passes every test and the spark
is gone — and who is allowed to notice?**

---

*Machine-authored, human-attested only where §0.2 says so. The live box beats this page: re-probe
before acting.*
