# COMMISSION — R06 · Orchestration (the executable Fractal)

**Working handle:** "orchestration." **The phase name and slot are Amihai's to name** — this document
uses the working handle `orchestration` only until he names it.

**Author:** dsh (`deepseek-v4-pro`, ONE generation). **Verifier:** Hermes profile `herdr`, separately,
against a pack written before it judges anything. `builder ≠ verifier`.

**Workspace:** `/home/deploy/the-cell/rounds/R06-orchestration/` — write **only** inside `./authored/`.
A hash fence outside `authored/` is checked before and after.

**§1.10 of the Codex governs every conflict: where a document diverges from `5qln.com`, the source is
authoritative** — including this commission. **The Fractal (Codex Appendix D) is the spec; quote it,
never paraphrase it into the criteria.**

---

## 0. His words and the standing decisions that bind this round

The build so far (all attested and closed): **B0** ledger + record · **B1** read-only walker · **B2**
driver · **P4a** step mode · **P4b** desk bundles · **B3** descent · **B4** the unattended run · **the
Grammar** (the meta implementation) · **the bridge** (the live desk adapter + the runtime config-read —
the last firmware round). After the bridge, everything is soft mode.

**Amihai's instruction (2026-08-30, verbatim substance):**

> "the lego attitude of experimenting endless options of fractal navigation, from sequence, to parallel,
> to loops to anything we tell it to do"

> "the orchestrator should be able to configure the agents configuration files, skills and tools (not
> every run but it should be able to build scenarios and implement them and orchestrate their run)"

> "agents can act with tools other than 5qln, such as search, write documents/code, activate tools"

> "keep the spirit of the great design and architecture from all the work we did and add this in a way
> that registers well with the work"

**His deeper word (2026-08-30):** *"now, in infinite modularity of orchestration, the Fractal comes to
be."* The build reads orchestration **as the executable form of the Fractal's address algebra** — not a
new scheduler bolted beside it. The scenario is a **word** over {S,G,Q,P,V} (D.3); the navigation is the
**signed path** `+^k · (−x₁)…(−x_m)` (D.5); sequence/parallel/loop/custom all fall out of the **signs**
(D.6); the materializer is **zoom-in** — each node its own `∞0 | K` cell with its own tools (D.1, D.10).

**Standing decisions (unchanged):** D12 — success in a phase = contextual DECODE + COMPILE of output
xyzab; the trail records what the context decoded **to**, never the context. D14 — every decode/compile
**loyal to `5qln.com/codex`**. §1.6 — no V without ∞0′. §5.5 — TENTATIVE is temporal, never epistemic.
The conductor is **S** (§4.8). The human's gate act is a TTY act, never carried by any channel. D6 — one
model across four desks. **The bridge's live `desk` mode and `softconfig` read-path are the immediate
predecessors — orchestration extends them, never re-implements them.**

---

## 1. What to build — one paragraph, no doctrine

**Orchestration** extends the attested bridge in exactly three ways, importing every predecessor (never
re-implementing):

1. **The scenario is a word** (`word.py`). A node is a word over {S,G,Q,P,V}; zoom in = append, zoom out
   = strip (D.3). A scenario is *data* — a word + the signed paths between its nodes (D.5) — never code,
   never a hardcoded topology enum. Decode + validate against the Grammar.

2. **The navigation is the address grammar** (`navigate.py`). Execute a word by walking the signed
   paths; sequence/parallel/loop/custom **derive from the signs** (D.6), not from an enum. The D.12 step
   check runs after every navigation step (P4a reuse).

3. **The materializer is zoom-in** (`materialize.py`). Each node is its own lawful cell — its own
   `∞0 | K` membrane, its own tools on the K side (D.1, D.10). Materialize a node's cell by writing its
   `SYSTEM.md`, `.pi/settings.json`, `skills/`, tools. This is the **write-path** — the complement of the
   bridge's `softconfig.py` read-path. A node's K side may carry **general tools** (search / write-doc /
   write-code / activate) — the adapter stays tool-agnostic; nothing forces 5qln-only.

`orchestrate.py` drives a materialized word over the live desks via the bridge's attested live mode
(instrument socket dialect), reads real states, carries hand-offs, assembles the trace. *"not every
run"*: a run may use an already-materialized word; the materialize step is optional per run.

Everything else is out of scope. The constitution (real desks into the seats) is **not** this round — as
the bridge provided the code path and read path, orchestration provides the **word, the sign-walk, and
the write path**, so that the constitution (soft mode, S first) can follow without any further firmware
change.

---

## 2. Acceptance criteria — quoted verbatim

### C1 — the scenario is a word, not code
> "Every node is a word over {S, G, Q, P, V}. zoom in = append · zoom out = strip." — Fractal D.3.

A scenario is a **word** over {S,G,Q,P,V} + signed paths (D.3, D.5) — data, not code. No hardcoded
topology enum. The decode validates the word against the Grammar.

### C2 — the navigation derives from the signs
> "Orientation is read from the signs alone: k = 0 daughter · m = 0 father · k, m > 0 cousins." — D.6.

The navigator executes sequence, parallel, loop, and custom **from the signs** — not from a topology
enum. Sequence = a daughter chain (k=0); parallel = cousins (k,m>0) converging on a father; loop = append
until a bound (the bound is the seed's boundary; D.2 has no terminal condition); custom = free word
composition.

### C3 — the materializer writes a node's cell
> "the orchestrator should be able to configure the agents configuration files, skills and tools … build
> scenarios and implement them and orchestrate their run." — Amihai, 2026-08-30.

The materializer emits a node's cell (`SYSTEM.md`, `.pi/settings.json`, `skills/`, tools) from a
scenario, and a run **can** use an already-materialized word (the "not every run" clause). The
write-path complements the bridge's `softconfig.py` read-path.

### C4 — general tools are lawful on the K side
> "agents can act with tools other than 5qln, such as search, write documents/code, activate tools." —
> Amihai, 2026-08-30. "H = ∞0 | A = K … the membrane | is the line a stranger crosses …" — D.10.

A node's K side may carry **general tools** (search / write-doc / write-code / activate); the adapter
does not hardcode 5qln-only. The membrane is the same line whether the K side holds a 5qln equation or a
filesystem tool.

### C5 — the trace lands per-gate in the ledger (B0 unchanged)
> The ledger and record format is B0's, attested; the trace still lands per-gate.

Orchestration reuses the B0 ledger unchanged; the trace lands per-gate in the same format.

### C6 — every run ends in ∞0′
> "∞0′ ≡ ∞0 … enriched return · open start." — D.8. "no V without ∞0′." — the seal.

Every run ends in the return-question ∞0′; the cycle is the clockwise read returning to center (D.1).

### C7 — the invariants hold
> No write path to the podium · no attestation · no re-implemented gate semantics — the standing
> prohibitions.

The podium is never written; nothing is attested; no gate semantics are re-implemented outside
`fractal-engine`.

### Claims (K1–K5)

- **K1 — stdlib, deterministic, no LLM.** Orchestration adds no network, no subprocess-beyond-the-attested,
  no LLM, no wall-clock in logic. The live socket is the only I/O, and it is the attested instrument's.
- **K2 — byte-exact enumerated forms.** The five equations and the §2-emphasis/voice bytes come from the
  enumerated P4b tables (`PHASE`/`EQUATION_FORMS`), byte-exact, never normalised (`⋂→∩`, `′→'`, spacing
  collapse = renaming an L1 symbol).
- **K3 — the click is never a machine verdict.** No authenticity verdict; the machine never claims
  arrival at ∞0 (HC-1/HC-2 permanently INCONCLUSIVE).
- **K4 — the B2 guards hold.** The centre guard refuses S/podium before any byte; an unresolvable write
  target is refused too (fail closed).
- **K5 — diff-ability.** The scenario and the materialized soft config are **data files** (one place to
  change, diff-able, versioned), never code. The node→desk map stays a config table.

### The six lenses (the verifier runs these; author so they pass, and so a blind spot reads
INCONCLUSIVE, never clean)

1. **Criterion match** — measure each criterion *as written*, not a neighbour of it.
2. **Invariant end-to-end** — the word-walk + materialize + orchestrate behaviour holds across a whole
   run, not per call.
3. **Absence vs validity** — absent word / absent soft config / absent agent / empty file must never
   read valid (sha256 of empty = `e3b0c44298fc…`).
4. **Encoding** — push `∞0′ → ‖` through every string field (word, address, voice, emphasis); text-mode
   byte seeks break on it.
5. **Cold restart** — a *new* process rebuilds the word-walk + materializer from disk alone; test the
   second process.
6. **Blind tool** — an unavailable live socket or an unconstituted desk reports INCONCLUSIVE, never clean,
   never a fixture stand-in.

---

## 3. Verified-facts block (do not re-probe — executed 2026-08-30)

- **Live socket is UP** (carried from the bridge, re-probed 2026-08-30): herdr 0.8.2, protocol 20. The
  desks are now **five** Pi agents (S, G, Q, V, P) in the `the-cell` workspace, all idle, model
  `deepseek-v4-pro` — **but the constitution is still the NEXT round's work; the authoring pass uses
  fixtures only, no live box.**
- **The bridge is the immediate predecessor** (staged at `./predecessors/bridge/`): `cost.py` (live desk
  mode), `softconfig.py` (runtime config-read), `run.py`, `surface_contract.py`. Orchestration imports
  these, never re-authors them.
- **The Fractal (Codex Appendix D) is the spec** — local text `sources/5qln-codex-appendix-D-the-fractal.txt`
  (the held copy). D.3/D.5 (word + signed path), D.6 (signs = orientation), D.2 (unrooted, leafless, no
  terminal condition), D.10 (membrane at every node, `H = ∞0 | A = K`), D.1 (4+1, center = S), D.8
  (∞0′ ≡ ∞0), D.12 (validation). Quote them; never paraphrase into the criteria.
- **The predecessor code is staged under `./predecessors/`** — B2, P4a, P4b, B3, B4, bridge — and the B0
  ledger is on `FRACTAL_LEDGER_DIR` (`/home/deploy/the-cell/ledger/fractal_ledger.py`).

---

## 4. The interface to the attested rounds (predecessors — import, never re-author)

Staged under `./predecessors/{b2,p4a,p4b,b3,b4,bridge}/`; the B0 ledger is on `FRACTAL_LEDGER_DIR`. dsh
imports and extends; it re-implements none of them.

- **B2** (`predecessors/b2/`): `driver.py`, `instrument.py`, `lens.py`, `walker.py`, `dialects.py` — the
  herdr socket surface (the live-desk path is `instrument.prompt_desk`).
- **P4a** (`predecessors/p4a/`): `step.py`, `surface.py`, `conformance.py` — the D.12 check.
- **P4b** (`predecessors/p4b/`): `block.py`, `arrangement.py`, `grammar.py`, `install.py`,
  `surface_contract.py` — the desk grammar seated at addresses (the source of the enumerated §2
  emphasis/voice bytes, `PHASE` and `EQUATION_FORMS`).
- **B3** (`predecessors/b3/`): `descent.py`, `surface_contract.py` — the descent (zoom).
- **B4** (`predecessors/b4/`): `run.py`, `cost.py`, `trail.py`, `surface_contract.py` — the unattended run.
- **bridge** (`predecessors/bridge/`): `cost.py` (live desk mode), `softconfig.py` (runtime config-read),
  `run.py`, `surface_contract.py` — the immediate predecessor; the write-path (materializer) is the
  complement of its read-path (softconfig).

### Binding — the names this round ships

| binding | real name | where |
|---|---|---|
| `word_module` | `word` | `word.py` — the scenario: a word over {S,G,Q,P,V} + signed paths; decode + validate |
| `navigate_module` | `navigate` | `navigate.py` — the sign-walk: sequence/parallel/loop/custom derive from signs (D.6); D.12 step check |
| `materialize_module` | `materialize` | `materialize.py` — the write-path: emit a node's cell (SYSTEM.md, settings, skills, tools) |
| `orchestrate_module` | `orchestrate` | `orchestrate.py` — drive a materialized word over live desks via the bridge's live mode |
| `surface_contract_module` | `surface_contract` | `surface_contract.py` — pins the new modules; declares the surface against the imported contract |
| `selftest_module` | `selftest` | `selftest.py` — the author's suite, a hypothesis never a result |
| `fixture_desk_harness` | `desk_harness` | `fixtures/desk_harness.py` — a fake desk harness (deterministic, no live box) for the authoring pass |

The functions are the real surface; the names are stable and documented here. The verifier's pack may bind
different names than this table — the functions are what is checked.

---

## 5. The materializer — the write-path (write, never author doctrine)

The materializer writes **data**, not code, and not doctrine. Its output is the soft layer the
constitution will later live in — the materializer emits it from a scenario. The schema is a **declared
default** (carried H-BRIDGE-2: the constitution writes the real soft files; orchestration *builds* them
per scenario, which is exactly Amihai's "build scenarios and implement them").

Minimum shape the write must emit, per node (word over {S,G,Q,P,V}), all caller-overridable:

| key | meaning | declared default |
|---|---|---|
| `system` | the node's `SYSTEM.md` — seat, equation, operation, hand-off (P4b seat + equation bytes) | P4b `PHASE[node]["seat"]` + `["phase_gate"]` |
| `settings` | the node's `.pi/settings.json` — model, thinking, tools | D6 model + `["read","grep","bash"]` + any scenario-declared general tools |
| `skills` | the node's `skills/` — the desk grammar at this address | P4b bundle |
| `tools` | the node's tools, including **general** (search / write-doc / write-code / activate) | scenario-declared; K side is tool-agnostic (D.10) |

The write must be **deterministic, stdlib-only, no network, no LLM** (K1), and its emitted bytes must be
**byte-exact against the enumerated tables** (K2). Malformed scenario → INCONCLUSIVE with the reason
(C4), never silently substituted.

---

## 6. Holds — declare, never guess

- **H-ORCH-1 — no desk is constituted in the live box for this round.** The word-walk and materializer
  are tested against a **fixture desk harness** (deterministic, no live box). A real `agent.prompt` to a
  live desk is the constitution's work, not this round's. The centre guard must refuse S/podium.
- **H-ORCH-2 — the scenario schema is provisional.** The word + signed-path encoding is dsh's engineering
  proposal, judged against the Fractal (D.3/D.5). Amihai may rename or re-shape it — it is candidate
  until he touches it.
- **H-ORCH-3 — "activate tools" is provisional.** The materializer emits a tool declaration into the
  soft layer; whether a live pi actually loads it is the constitution/run's concern, not the authoring
  round's. The materializer declares, it does not execute.
- **H-ORCH-4 — the human's gate act is untouched (carried H-B4-4).** No podium write, no `cell-attest`
  invocation, no typed word. Attestation stays a TTY act.

---

## 7. Prohibitions

No write path to the podium (`pane.send_text/input/keys` at the centre). No git, no attestation, no claim
that anything ran. No gate semantics re-implemented outside `fractal-engine`. No re-implementation of the
herdr socket dialect, the D.12 checks, the desk grammar, the descent, or the bridge's live mode and
softconfig read-path. **No hardcoded topology enum — the signs are the topology (D.6).** No hard-coded
§2-emphasis/voice/model/budget literal in the conductor's control flow. No sixth corruption code, no new
L1 symbol, no new decoding operation, no renamed symbol. No byte normalisation (`⋂→∩` is renaming). No
authenticity verdict. No tentative node promoted or consumed. The machine never resolves a hold. Nothing
described as attested/decided/verified that this commission does not mark so.

---

## 8. Deliverables — under `./authored/` (layout yours to vary; content is what is checked)

- `word.py` — the scenario: a word over {S,G,Q,P,V} + signed paths; decode + validate (D.3, D.5).
- `navigate.py` — the sign-walk: sequence/parallel/loop/custom derive from signs (D.6); D.12 step check.
- `materialize.py` — the write-path: emit a node's cell (SYSTEM.md, settings, skills, tools).
- `orchestrate.py` — drive a materialized word over live desks via the bridge's live mode.
- `surface_contract.py` — imports the attested predecessors by path, sha-pinned (now including word,
  navigate, materialize); declares the orchestration surface against them.
- `selftest.py` — the author's own suite (a hypothesis, not a result).
- `phase-card.md` — predictions only (never results) + the D14 divergence log.
- `fixtures/` — at least: a fake desk harness (deterministic, with an unconstituted-desk `agent_not_found`
  case and an absent-socket case) · a word-walk that runs each pattern (sequence/parallel/loop/custom)
  · a materialize that emits a node's cell (and a malformed scenario that reads INCONCLUSIVE) · a
  cold-restart fixture that re-arms the word-walk + materializer from disk alone.

---

## 9. Budget

**ONE authoring generation.** No exploratory chat. Artifact + phase card in, out.
