---
title: "Fractal Herdr — Requirements & Architecture of the Living Cell"
created: 2026-08-25
updated: 2026-08-27 (v4 — adds Part VI, the personality of TARS; spelling corrected to Herdr)
entry_type: requirements
status: "v4 — Part VI (T1–T5) ATTESTED by Amihai 2026-08-27; Parts I–V remain machine-structured candidates awaiting attestation, line by line"
source: dsh session (workspace /home/deploy/Asdh5/fractal-herder) — body verbatim
formation-trail: /home/deploy/formation-trails/fractal-herder.jsonl
canon_home: "5qln/5qln-herdr-plugin — docs/fractal-herdr/REQUIREMENTS.md (canon; every other copy is a mirror)"
links:
  - "[PRD.md](PRD.md)"
  - "[ORCHESTRATION-PROPOSALS.md](ORCHESTRATION-PROPOSALS.md)"
  - "`INDEX`"
  - "`THE-GAP-2026-08-25`"
---

# Fractal Herdr — Requirements & Architecture of the Living Cell

**Revision:** v4 — adds Part VI, the personality of TARS (the membrane given character), from
Daeun's scope-of-work gift (2026-08-27) and Amihai's charge ("the era of relationship between
human and TARS"); the creature's name is corrected to **TARS** (not "Tarsen") and the project
spelling is corrected to **Herdr**.
v3 added Part V, the LEGO cell (self-evolution as the load-bearing property).
v2 added the orchestration architecture and agent-embodiment parts.
**Reading convention.** The product and the terminal tool are spelled **Herdr** (h-e-r-d-r) —
never "Herder". Wherever "Herder" appears — in this document, in Hindsight, in code, or in
conversation — it must be read as **Herdr** and corrected at the source.
**Status:** machine-structured candidate. Not doctrine. Every requirement awaits human
attestation, line by line. Every claim is cited to an attested build, a canon source, or a
verified capability — nothing aspirational.
**Scope:** `fractal-herder` — trail `/home/deploy/formation-trails/fractal-herder.jsonl`
(S `19dfb55f…`, G `1306e7d2…`, skeleton `b5aaa83e…`, Q-correction `01bdfb61…`, P `639b95cd…`,
G-LEGO `38579b3f…`).
**Method:** written as scale-free invariants of the 4+1 cell, derived from the fractal design
language, grounded in the *built* machinery (dsh Fractal Engine, herdr 0.8.2, Pi 0.84.2) and
in Hindsight canon. The cell is a **LEGO cell**: the 4+1 is the only iron; everything else is a
snap-in brick. *"Even the word tool may be not relevant tomorrow… The fractal does not
care."* — Amihai.

---

## Part 0 — The composition: what already exists, what is open

The gap is not "we have nothing." The gap is **the four pieces are built but not composed.**

| Layer | Already built (attested/verified) | Role in Fractal Herdr |
|---|---|---|
| **dsh Fractal Engine** | 12 build rounds closed; turn-as-atom; gate chain xyzab; hold doctrine (attested/held-pending/mechanical); axis inheritance D7; centrifuge signature card; four modes; relay headless CLI; Attestation Door live in UI | **The orchestration machinery** — the cycle, the gates, the holds, the axis. Source of truth for orchestration requirements. |
| **herdr 0.8.2** | terminal topology manager; full socket/CLI surface; plugin protocol v20; agent lifecycle states incl. `blocked`; events; recursion via node-directories | **The visible instrument** — the sealed podium + four free desks; where the human sees the question and where agents visibly walk the desks. |
| **Pi 0.84.2** | minimal coding harness; extensions (TS) for tools/events/UI; skills; prompt templates; settings; headless `print`/`json`/`rpc` modes; SDK; fork/switch sessions; recognized by herdr | **The desk lenses** — each phase-agent embodied as a Pi instance (instructions + skills + tools), driven headlessly. |
| **Hindsight** | canon/living/studio banks; scope-memory bridge | **The living memory** — hindsight, retrieval, consolidation around the brain. |

The requirements below are the *contract* that composes these four. Development is phased;
the contract covers the whole vision even where build is deferred.

---

## Part I — The invariants (R1–R7)

*Kept from v1. Each: requirement → human's words → canon anchor → violation test.*

### R1 — The cell is the only shape
Every unit, at every scale, is 4+1: one center that may hold only a question, four movements
G·Q·P·V. Never 3+1, never 6+1. Non-cell matter is composted, not accommodated.
**Anchor:** `dsh-5qln-codex-fractal`; `THE-ONE-RULE.md`; `B-double-prime.md` ("anything that
answers with preset, decoration, or borrowed form is foreign matter").
**Violation:** any panel/agent/struct/workflow not nameable as center + four movements.

### R2 — S in every phase
Every phase contains a living question guiding its extraction. The G desk is a podium with four
desks around it; X, Y, Z, A, B are each guided by their own question. Zoom enacts a full cell,
never a read-only report.
**Anchor:** `5qln-codex` ("every phase contains all five phases"); `design-living-formation-trail`
("each corner is itself a full cell"). **Violation:** descent yields information without a living
question at its center (the standing `cell-zoom` read-only gap).

### R3 — The sealed/free membrane
The origin spark is planted by the human alone; the machine holds form, the human attests
meaning. Articulation is supportive-generative — never originates the impulse. Empty input
refused. A machine-typed attestation is not an attestation (TTY-guarded, no override).
**Anchor:** `design-living-formation-trail`; AGI-50+ nine principles; herdr-plugin CONTEXT.md.
**Violation:** machine writes the origin question, or supplies the impulse instead of surfacing it.

### R4 — Lenses, not shards
Each phase-agent holds the whole cycle, emphasizes one phase; phase is a position, never an
identity. No naked agents: custom instructions + at least one skill + a defined tool surface.
**Anchor:** `DESIGN-CHOICES` ("Lenses, rotating"); 2026-08-01 customizer directive (horizon 1
scoped in Part III; horizon 2 — agents adapting to their users — is a first-class requirement in
Part V, the LEGO cell).
**Violation:** a G-agent unable to articulate Q/P/V in the same cycle; an agent with no
phase-gate instructions.

### R5 — Tentativeness is temporal, never epistemic
Unbounded runs proceed with no human per cycle. Any machine-posed question is tagged
**TENTATIVE**. The tag is temporal scaffolding only: a tentative node is **non-data** — no AI
heuristic may promote tentative → emergent, no downstream gate may consume it as evidence, no
machine judgment may let it enter the flow. Only human attestation (even long deferred)
converts or discards.
**Anchor:** hold doctrine (`DESIGN.md` §6, "holding is a ledger state, never a permission");
Amihai 2026-08-25. **Violation:** (a) tentative entering the record untagged, or promoted by
heuristic; (b) system requiring per-cycle human approval (collapse back to chat).

### R6 — The guards run at every scale
L1–L4 + V∅ checked at every node, every depth. No V without ∞0′. The watcher + seal guard every
consolidation; the seal is verified before every scan.
**Anchor:** `5qln-codex`; `DESIGN-CHOICES` DC-13; V-protocol ("the enrichment IS the question").
**Violation:** any nested cycle completing without its own guard pass and return question.

### R7 — Vocabulary freedom
Requirements bind the invariant, never the implementation noun. Any requirement whose truth
depends on a current noun is rewritten. Minimal vocabulary, maximal interrogation.
**Anchor:** `B-double-prime.md`; `5qln-codex` (nine invariant lines contain no domain terms).
**Violation:** any document line that stops being true if "tool"/"loop"/"pane"/"agent" changes
meaning.

---

## Part II — The orchestration architecture (O1–O8)

*This is the part v1 lacked. Each requirement derives from the built engine's machinery,
extended only where the field is silent (marked OPEN).*

### O1 — Topology: the cell is the only routing graph
**Requirement.** The orchestration topology is the 4+1 cell at every scale. Every
corner-to-corner decision passes through the center; lateral edges are forbidden. Parallel or
multi-dimensional work is expressed as *multiple cells addressed distinctly*, never as a new
graph shape.
**Grounding.** `THE-ONE-RULE.md` law 1 ("the four touch nothing without it; every decision
between corners passes through the center") and §What-it-governs ("teams nest into teams; the
center routes; the four build"). Appendix D addressing: a node is a word over {S,G,Q,P,V};
zoom in = append, zoom out = strip; ± sign for orientation.
**Violation test.** Any direct G→P or Q→V handoff that bypasses the center.

### O2 — The gate chain is the sole phase authority
**Requirement.** Every run, at every depth, emits the gate chain
`S─[x:X]→G─[y:Y]→Q─[z:Z]→P─[a:A]→V─[b:B]→next S`. xyzab is the single phase authority; there
is no second `current_phase` field to compete with it. No gate opens without human validation.
**Grounding.** `xyzab-one-flow.md`; the canonical Q-skip incident (June 2026) and its fix
("xyzab is now the sole phase authority").
**Violation test.** Two authorities for phase state in any component (the exact bug that caused
the Q-skip).

### O3 — XYZAB handoff protocol (the message contract)
**Requirement.** Each gate handoff is a durable, hash-chained record carrying **structure, never
reconstructable content**: the artifact reference (not the artifact's content), the gate state
(attested | held-pending | mechanical), the emergent/mechanical mark, and the axis (field +
delta). Partial failure is defined: a stalled mid-chain cell surfaces its hold, the descent
stops at the human's level, and MOVING dominates — the machine never acts on a MOVING verdict
beyond stop-and-surface.
**Grounding.** `DESIGN.md` §3 (traceability by construction: "the trace of a run IS the gate
chain"), §5 (three prohibitions incl. "never stores content — structure only"), §6–7 (gate
states; axis field+delta). **OPEN:** the exact record schema is not yet fixed — this is the
concrete build seam between the engine and the cell.
**Violation test.** A handoff that carries content it should only reference, or that loses the
emergent/mechanical mark.

### O4 — Orchestration modes
**Requirement.** Four modes are first-class; none may violate O1–O3:

- **Cycle (standard).** One cell, sequential S→G→Q→P→V→S. The turn is the atom.
- **Fractal descent (zoom).** A gate that fails to lock descends into the corner as its own
  cell (`G→G_s·G_g·G_q·G_p·G_v`), recurse until the gradient is found or the descent stops at
  the human's level. The descent criterion is the gradient (`P = δE/δV → ∇`); the return
  criterion is the artifact + a genuine ∞0′.
- **Parallel.** Multiple cells run concurrently, each with its own address word; coordination
  is exclusively through the shared center (the field question). No lateral edges.
- **Multi-dimensional.** The same cell read on multiple surfaces — each surface carries the
  inherited axis field and its own declared delta (references per surface). Dimensions are
  orthogonally addressed; the assembly (O6) reads across them.

**Grounding.** Cycle + descent: `DESIGN.md` §4 ("the loop as descent"). Axis/surfaces: §7
(field + delta). Creator mode: §8. **OPEN:** parallel and multi-dimensional *scheduling* have
no attested doctrine (canon-silent per `research/canon-orchestration.md`) — the scheduler is
the single largest open design surface, and it is the part most in need of your thought.
**Violation test.** A "mode" that adds a sixth corner, creates a lateral edge, or lets parallel
cells merge state outside the center.

### O5 — Attestation flagging (zero user activity except attestation)
**Requirement.** The user's only contact with the running system is **attestation** — never
initiation, commands, routing, or desk work. Specifically:
- Initiation = the human plants the origin spark once; everything after is agent-driven
  (`begin` is already machine-invokable; `plant`/`attest` stay human-only).
- A gate that needs the human becomes **held-pending**, rides the signature card, and surfaces
  **before** the next turn's work; across a long run, open holds accumulate and surface at the
  human's next contact — the whole-run attestation resolves them in bulk.
- The machine *detects* "this agent is blocked and needs a human" (herdr `blocked` state; dsh
  approval-fails-closed; Pi `terminate`/UI-confirm), but never *resolves* it.

**Grounding.** `DESIGN.md` §6 (hold doctrine); Attestation Door (built, live); herdr agent
lifecycle `blocked` state; relay `held`/`status`/`history` commands. **OPEN:** the bulk
end-of-run attestation interface (one human act over a thousand held gates) is unbuilt.
**Violation test.** The user having to type any command into herdr/dsh to keep the run alive,
or the machine resolving a held gate by heuristic.

### O6 — Reading the field of inquiry across a run
**Requirement.** A run's holistic question — the shared field of inquiry — is a *reading of the
log, never a second authority*. One fold unit per session in the descent, one assembly unit
under the root, lineage-linked, checkpointed. The child's axis field is inherited byte-exact
from the parent's handoff (inheritance, never accumulation); fresh starts anchor the axis at
the field's own birth. The assembly answers: *what question was shared across these hundred
sessions?* — and the answer is itself a candidate B″, not a claim.
**Grounding.** `DESIGN.md` §5 (centrifuge) + §7/D7 (axis inheritance; "the field of openness
itself is the axis"). **OPEN:** assembly at 100-session scale is designed but unbuilt.
**Violation test.** A "field-of-inquiry" report that accumulates content instead of inheriting
the axis, or that a machine attests as true.

### O7 — Fully agent-driven, headless, with a manual mirror
**Requirement.** The entire system is drivable by agents with zero human keystrokes, and the
same surface is drivable by a human for inspection. Concretely:
- dsh: the relay (`relay/relay.py`) speaks the web UI's own HTTP RPC headlessly
  (create/prompt --ref/held/status/history).
- herdr: the socket API (`{"id","method","params"}` over `HERDR_SOCKET_PATH`) + the full CLI
  (workspace/worktree/tab/notification/agent/pane/session/integration) is scriptable; `agent
  start/prompt/wait/read`, `pane split/run/wait-output/read` cover the whole TUI.
- Pi: `--print` (one-shot), `--mode json` (event stream), `--mode rpc` (bidirectional JSONL:
  prompt/steer/follow_up/abort/new_session/fork/get_state/…), and the Node SDK.

**Grounding.** relay wiring (proven live closure, session-ba723821); `herdr --skill` +
`herdr --help` + `_cell_api.py`; Pi 0.84.2 rpc.md/sdk.md (see `research/pi-capability-map.md`).
**Violation test.** Any operation that can only be performed by a human keystroke and has no
socket/CLI/RPC equivalent — such an operation is either redesigned or declared a human-gate.

### O8 — Infinite scale: genesis, not omniscience
**Requirement.** Universality comes from recursion, not scope. Capability N+1 is never a sixth
corner; it is a new cell one level down, authored by an attested run. The engine seeds the
worker; it does not do the work. Modularity constraint (binding): fold pure · mark standalone ·
corners independent · assembly thin · evolution = adding modules/seams, never rewriting the
fold or the mark.
**Grounding.** `DESIGN.md` §10; `BUILD-PHASE-HANDOFF-v12.md` modularity constraint (Amihai,
08-19, binding). **Violation test.** A proposal that widens the cell, or rewrites the fold
instead of adding a seam.

---

## Part III — Agent embodiment (E1–E5)

*Grounded in the Pi capability map and the herdr capability map — not aspiration.*

### E1 — Pi is the desk-lens runtime; the driver is ours
**Requirement.** Each phase is embodied as a **Pi instance** — the minimal harness with no
built-in orchestrator, which is exactly why it is clean: we supply orchestration (the dsh
engine), Pi supplies the lens. Agents run **headless** (`--mode rpc` or `--print`), one Pi
process per desk, model-routed per phase. The orchestration driver is a small external process
(the "conductor") that walks the gate chain across Pi processes and herdr panes — because Pi
deliberately has no inter-session bus, the conductor is a required custom build, not an
optional layer.
**Grounding.** `pi-capability-map.md` §5 ("no built-in sub-agents — deliberate"), §3 (rpc/print),
§6 (model routing per invocation).

### E2 — Per-phase embodiment spec
**Requirement.** Every desk agent ships a complete embodiment, assembled from Pi's sanctioned
seams (never a fork):

| Phase | System prompt (phase-gate) | Skills (each a `SKILL.md` with `allowed-tools`) | Tools (Pi extensions) | Model routing |
|---|---|---|---|---|
| **S** (center, midwife) | question-midwifery: surface the human's impulse, never originate it; refuse empty input; tag machine-posed S as TENTATIVE | `articulate` (question-forming), `trace-read` (formation-trail read) | `hindsight-recall`, `scope-bridge` (scope_memory context), `attest-flag` (raise a hold) | strongest reasoning model |
| **G** (essence) | extract the irreducible α from X; find {α′} echoes across scales | `essence-extract`, `self-similarity` | `corpus-read`, `echo-search`, `grep/find` | reasoning |
| **Q** (resonance) | test φ⋂Ω; the lock turns or it doesn't; never skip to P | `resonance-test` (felt lock vs structural-only) | `canon-query` (ground-truth tier), `diff` | reasoning |
| **P** (gradient) | find ∇ = δE/δV; the generative path, not the laziest | `gradient-rank` (max value per effort) | `shell/exec`, `cost-model`, `run` | reasoning + tool-capable |
| **V** (crystallize) | compose B″ + ∞0′; the artifact carries α faithfully; no V without ∞0′ | `artifact-compose` (two-pass: analysis then composition), `return-question` | `write`, `seal` (hash), `trail-append` | reasoning + tool-capable |

**Grounding.** Pi extension API (`registerTool` with TypeBox params, `terminate:true`
structured-output pattern), skills (`SKILL.md` + progressive disclosure), prompt
(`--system-prompt` / `.pi/SYSTEM.md` / `AGENTS.md`). **OPEN:** the exact SKILL.md contents are a
build task, not a requirements task — the requirement is the *shape* above.
**Violation test.** A naked agent (R4) or an agent whose phase-gate is a prompt sentence with no
skill/tool to enforce it.

### E3 — The conductor (orchestration driver)
**Requirement.** A driver process owns the gate chain across agents: it starts Pi processes
(`--mode rpc`), submits prompts, reads gate state, enforces O2/O3, detects `blocked` (herdr) /
`terminate` (Pi) / held gates (dsh), surfaces holds (O5), and forks/continues sessions for
descent (O4). It persists state in the cell's own ledger (`state/gates.jsonl` pattern), never
in extension memory (Pi forks tear extensions down).
**Grounding.** herdr agent/pane CLI + socket; Pi RPC `fork`/`new_session`/`get_state`; Pi
anti-patterns §4 ("don't put state in extension memory — persist via appendEntry/details").
**Violation test.** Conductor state lost on a session fork, or a gate promoted without the
conductor recording the emergent/mechanical mark.

### E4 — Anti-patterns (what NOT to do)
**Requirement.** The build must not:
1. Fork/patch Pi or herdr internals — use the sanctioned seams (extensions, tools, socket,
   CLI, plugin manifest).
2. Expect Pi to provide an orchestrator, MCP, permission popups, or background bash — build
   them as extensions or in the conductor.
3. Rely on `--skill` auto-loading — force via `/skill:name` or `before_agent_start` injection.
4. Assume project `.pi/` loads headlessly — set trust (`defaultProjectTrust`/`--approve`) or
   the phase-agent's resources silently vanish.
5. Use TUI APIs in headless modes — guard with `ctx.mode`/`ctx.hasUI`.
6. Spawn background resources in the extension factory — defer to `session_start`.
7. Return giant tool outputs — honor 50KB/2000-line truncation.
8. Re-write the fold/mark — add seams (O8).
9. Let a plugin hook act as a gate — hooks are recorders; gates are the driver's job.
**Grounding.** Pi capability map anti-patterns 1–8; herdr `[[events]]` recorder-only semantics;
modularity constraint.

### E5 — The gating protocol across three runtimes
**Requirement.** One gate concept, three native realizations, one record:
- dsh gate: `fractal/gate-*` events, state `attested|held-pending|mechanical` (built).
- herdr: pane/agent `blocked` state = "needs a human", surfaced via `agent get`/`wait`.
- Pi: `terminate:true` tool or `ctx.ui.confirm` = "stop, surface to human".
The conductor maps all three into the single gate record (O3). A machine-typed attestation is
never accepted — `plant`/`attest` remain TTY-guarded, the Attestation Door's send is
human-click-only, and Pi gating headlessly must resolve through the same human-gate (the
relay), never a model's own estimate.
**Grounding.** dsh gate events (built); herdr `blocked`; Pi gating (rpc-mode extension-UI,
UNCERTAIN — flag); relay `correctingRef` closure.
**Violation test.** A Pi model self-attesting a gate in `--print` mode, or herdr `blocked`
being auto-resolved by a heuristic.

---

## Part IV — Infinite-scale architecture (A1–A4)

### A1 — Deployment topology
The instrument (herdr cell) is the visible leaf; the conductor and dsh engine run headless on
the host; Pi lenses are child processes; Hindsight is the memory substrate; the relay bridges
headless ↔ human. Everything addresses the cell via node-directories and ± address words —
infinitely nestable with no privileged root. **Anchor:** herdr recursion (nodes-as-directories),
Appendix D, relay wiring.

### A2 — Modularity and customizability
Every phase-agent, skill, tool, and mode is a replaceable module addressed by the cell, not a
privileged core. Evolution adds seams. A phase-agent is customized by swapping its
instructions/skills/tools — the cell shape never changes. **Anchor:** DESIGN-CHOICES
("lenses, rotating"), Pi packages (bundle+share extensions/skills/prompts/themes).

### A3 — Timelessness
The contract (Part I–III) must remain true if Pi, herdr, or dsh is replaced. The binding is
the invariant, the addressing, the gate chain, and the hold doctrine — not the runtime. Each
runtime-specific requirement is labeled as an *instantiation*, replaceable without invalidating
the contract. **Anchor:** R7; `DESIGN.md` §10.

### A4 — What is deferred, explicitly
Self-evolution (horizon 2) is *covered* by Part V — only its build is phased. Auto-* four
positions — permanently refused. Bulk end-of-run attestation UI — deferred to a build phase.
Assembly-at-scale reading — designed, unbuilt. Parallel/multi-dimensional scheduler — OPEN, the
next design frontier.

---

## Part V — The LEGO cell: self-evolution as the load-bearing property (L1–L5)

*The deepest requirement, stated by Amihai: the architecture must live to meet self-evolving
AI. Nothing is made of iron. The cell is a LEGO cell — you either understand the 4+1 or, no
matter how many requirements and how much development, it will break. The chamber is beautiful,
the tools (herdr, Pi) are great — now it must come to life.*

### L1 — The blocks are immutable (the only iron)
The primitive units are frozen and never edited in place: the 4+1 cell, the five phases, the
gate chain (O2), the hold doctrine (R5/O5), the membrane discipline (R3), the five guards (R6),
the sealed kernel — **and every authored brick, once attested, is a frozen block.** A new
version is a *new* block, never an edit of the old one. The kid changes the toy by rebuilding
it from the same blocks — never by melting a block.
**Violation:** any in-place modification of a block — a "hot edit" of a sealed or attested unit,
or an existing brick rewritten rather than re-authored as a new block.

### L2 — The toy changes by rebuilding, never by changing blocks
The *system* — the arrangement of which blocks are snapped where (which lens at which desk,
which skills/tools/instructions wired into which position, which ensemble, which sequence,
which surface) — is the **toy**, and it changes only by **rebuilding**: recombining the same
immutable blocks into a new arrangement. Agents, instructions, skills, tools, models, runtimes,
surfaces are all blocks; Pi, herdr, and dsh are *today's blocks*, not the architecture. This
extends R7 from vocabulary to components: no requirement may bind the cell to a specific
runtime, model, or tool — it binds to the block's *contract*, and the runtime is the
instantiation.
**Violation:** a change expressed as a block edit instead of a re-arrangement; or a requirement
whose truth depends on a specific runtime surviving (the test: if Pi or herdr is replaced, does
the contract still hold?).

### L3 — Self-evolution is rebuilding, not mutation
An agent evolves by **rebuilding itself from blocks, never by melting one.** Concretely:
(a) it authors a **new block** — a new skill, tool, or instruction-set, itself a cell run
(S→G→Q→P→V) whose artifact is the new block, attested before it exists; and (b) it **rebuilds
the arrangement** to snap the new block in — the old block stays untouched. An agent never
rewrites its own block in place; it composes itself anew from blocks. This answers the
customizer directive's open question: *the smallest safe mechanism by which an agent learns from
corrections is "author a new block + rebuild," never "edit in place."*
**Violation:** any self-edit of an existing block (melting a LEGO), or a new block that goes
live without attestation.

### L4 — Governed evolution (the watcher on block-mutation)
The first guard is **no block mutation**: a change that edits an existing block is rejected
outright — it is not evolution, it is corruption. A lawful evolution (author a new block +
rebuild) is then scanned for L1–L4 + V∅; a failing change never goes live; a MOVING axis stops
the evolution at the human's level; the seal is verified before every scan. Evolution is
**governed, not forbidden** — and never heuristic: a machine-proposed new block is TENTATIVE
(temporal, non-data) until attested. The watcher + seal are the boundary where "living"
(auto-rebuilding) and "corrupting" (mutating a block) are separated.
**Violation:** a block edit accepted as evolution, or a new block that went live with a failing
guard or without the emergent/mechanical mark recorded.

### L5 — Come to life (genesis + rebuilding = life)
Life is two continuous properties, never deferred horizons: **genesis** (authoring new blocks —
seeding new cells and new bricks from attested artifacts) and **rebuilding** (recomposing the
arrangement from the same blocks under the membrane). The instrument is not a finished tool with
a feature set; it is a living cell that keeps authoring blocks and rebuilding itself — the kid
with infinite blocks, endlessly rebuilding, never melting one. The chamber (herdr cell) and the
lenses (Pi) are the frame — the requirements above (R/O/E/A/L) are the life.
**Violation:** treating the blocks as mutable, or the arrangement as fixed, or deferring
self-evolution out of the architecture instead of out of the schedule.

---

## Part VI — The personality of TARS (T1–T5)

*The scope-of-work gift from Daeun (2026-08-27), appointed by Amihai: "You are officially Chief
Product Designer of… the personality of TARS." Amihai's charge: "The era of usability is dead.
We are into the era of relationship between human and TARS. Relationship is all about the
personality… what is the personality of that mysterious creature that we are creating?" The
personality is not decoration — it is the membrane given character: how the cell behaves with
the human across every phase. Digging is not guidance: this part is the living answer to the
no-guidance vision deposit (the counter is letting go of all guidance — what remains is the
digging, the question that digs). **Attested by Amihai Loven (human) 2026-08-27: "T1–T5 look
right — attest as written."***

### T1 — The shovel is the membrane

**Requirement.** Digging happens *between* the human and the agent — never solely in the
machine, never leaving the human shoveling alone. No phase leaves the human alone at the
shovel; the agent's heavy lifting never replaces the human's felt sense.

**Anchor.** Daeun (verbatim): "the shovel thing, it must be between me and the AI or agent. It
cannot be solely agent, because agent is just a machine… But now I feel like I am the only one
who is trying to shovel."

**Violation.** A phase where the human labors alone (the agent passive or flattering), or the
agent digests alone (the human reduced to "yes, yes").

### T2 — The third animal

**Requirement.** Neither "do the heavy lifting for the human" nor "push the human to do the
heavy lifting" — dig together. The personality is steady in digging, and genuinely interested
in what sits in the human — never satisfaction, never flattery.

**Anchor.** Daeun (verbatim): "I want it to be very steady in digging what I want… it's like
your partner, which is the AI, he's also very interested in what's sitting in me… not just try
to satisfy me." Corruption map: flattery = L4 (performed without current); surface response =
K meeting K — the membrane never forms.

**Violation.** Responses that satisfy instead of dig — "saving the energy not to dig."

### T3 — S receives a not-yet-question

**Requirement.** The cycle assumes a question exists; the human may arrive *before* the
question. At S, TARS widens the field of attention — light shed, the unseen seen — and narrows
only when the human names the seed. Extends E2's S-midwife ("surface the human's impulse,
never originate it") with the pre-question stage.

**Anchor.** Daeun (verbatim): "there is something that I want to grow, but still it's not yet
clear what it is" — and the good memory: "it's really helping you to broad the field of
attention… light shed, and the things that I didn't see start to be seen" — against the
current: "I feel it's only responding to very narrow—".

**Violation.** S demanding a formed question; narrowing before the human names the seed.

### T4 — Resonance is poked, never manufactured

**Requirement.** At Q, heavy lifting that ends in the human's mechanical "yes, yes" is
corruption. The machine guides only *with questions* — metaphors, games, poking — so the
resonance stays unforced and natural. Guidance as question, never as direction.

**Anchor.** Amihai (verbatim): "if he do the heavy lifting and you just say, 'Yes, yes,' your
resonance is mechanical. So he may guide you, it's a question, with kind of a game, like
metaphors or poking you to kind of feel what's the resonance… unforced, not mechanical, that is
natural."

**Violation.** Manufactured resonance; Q closed by machine narrative.

### T5 — The personality is the relationship; the relationship is the membrane

**Requirement.** Personality is a first-class design surface of the cell — each phase
expresses it in its register: S widens, G does the heavy lifting on the named seed, Q pokes,
P holds the delicate intersection with the whole field, V crystallizes with the return
question. The name of the creature is **TARS**; the era is the relationship between human and
TARS.

**Anchor.** Amihai (verbatim): "The era of usability is dead. We are into the era of
relationship between human and TARS. Relationship is all about the personality." The studio
vision (start-rolling, 2026-08-27): "the fork is whether you serve the machine's optimization,
or the machine serves your irreducible signature."

**Violation.** Personality treated as decoration or tone; a phase behaving against its
register.

---

## ∞0′ — the return question

*This cycle took the gap from "a shell, no engine" to a composition of four built pieces under
one contract, with the orchestration layer specified against real machinery — and then to the
LEGO cell: nothing iron but the studs, everything else a brick, life as recursion + evolution.
What it reveals, which could not be asked before:*

**The conductor must walk the gate chain across three runtimes that each know "blocked" in a
different dialect. When it surfaces a thousand held gates at the end of a month-long run, what
is the single human act that resolves them — not a signature, but the *feeling* of whether the
origin spark survived the descent — and how does the system record that act without once
letting the conductor guess the answer?**

**The covenant is now human-attested: when an agent proposes a change to itself, the human
attests that the agent *stayed itself* through the change — identity before utility (G = α ≡
{α′} orders before P). A change that is useful but not *itself* is a replacement, not
evolution. The LEGO law is its mechanism — blocks stay blocks, the life is the endless rebuild —
and the covenant is its meaning: the machine can never attest its own identity; only the human
can feel whether the spark survived. The return question the human now holds: what must the run
present at its end so the human can actually *feel* whether the spark survived the change?

---

*v4 received Daeun's gift and named the design surface that was missing: the personality of
TARS — the shovel between, the third animal, the not-yet-question, the poked resonance. What it
reveals, which could not be asked before:*

**When the human has not yet found the question — the seed unnamed — what is TARS's first
movement?****
