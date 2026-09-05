# COMMISSION — the bridge · the live desk adapter + the runtime config-read

**Working handle:** "the bridge." **The phase name and slot are Amihai's to name** — this document
uses the working handle `bridge` (the last firmware round) only until he names it.

**Author:** dsh (`deepseek-v4-pro`, ONE generation). **Verifier:** Hermes profile `herdr`, separately,
against a pack written before it judges anything. `builder ≠ verifier`.

**Workspace:** `/home/deploy/the-cell/rounds/bridge/` — write **only** inside `./authored/`. A hash
fence outside `authored/` is checked before and after.

**§1.10 of the Codex governs every conflict: where a document diverges from `5qln.com`, the source is
authoritative** — including this commission.

---

## 0. His words and the standing decisions that bind this round

The build so far (all attested and closed): **B0** ledger + record · **B1** read-only walker · **B2**
driver · **P4a** step mode · **P4b** desk bundles · **B3** descent · **B4** the unattended run · **the
Grammar** (the meta implementation). The bridge is the **last firmware round** — after it, everything is
soft mode (constitution, S first → settings surface → two modes → swarm), and no further dsh generation
touches the firmware.

**The crystallization (2026-08-29, his word — the chip framing, canon
`docs/fractal-herdr/REVERSE-ENGINEERING.md` `55c77f0`):**

> **ASIC = the Codex** (sealed, held) · **firmware = everything we built** · **soft layer = Pi/Hermes
> native customization** (`settings.json`, `AGENTS.md`, skills, prompts) that **activates the firmware,
> never modifies it**.

The gap the bridge closes is named in that document's roadmap (candidate #2 — **the settings surface**):

> "The conductor reads, at runtime, from Pi's `settings.json` + `AGENTS.md` + skills + prompts: the cycle
> budget/hold/poll, each desk's codex §2 emphasis, its voice, its model."

**The specific missing piece (verified by reading the code, 2026-08-30 — `FACTS.md`, not inferred):**

> "B4's `cost.DeskAdapter` has exactly two modes, `sub-process` and `re-prompted`, and **both spawn the
> fixture `desk_server.py` — never the live herdr socket**… The B2 `instrument.py` speaks the real herdr
> dialect over `~/.config/herdr/herdr.sock` (live, running) and was probe-verified against the live box,
> but the **conductor was never joined to it**."

**The bridge, in one sentence (Amihai's instruction, 2026-08-30, "sure"):** join the conductor to the
live herdr socket via the attested B2 `instrument.py` (a live `desk` mode), **and** read each desk's
§2-emphasis / voice / model / budget from the soft layer at runtime — replacing the hard-coded
`DESK_FUNCTION_SPECS` / `COST_MODEL`. ONE dsh generation, judged by the P4a discipline.

**Standing decisions (unchanged):** D12 — success in a phase = contextual DECODE + COMPILE of output
xyzab; the trail records what the context decoded **to**, never the context. D14 — every decode/compile
**loyal to `5qln.com/codex`**. §1.6 — no V without ∞0′. §5.5 — TENTATIVE is temporal, never epistemic.
The conductor is **S** (§4.8). The human's gate act is a TTY act, never carried by any channel.

---

## 1. What to build — one paragraph, no doctrine

The **bridge** extends the attested B4 unattended run in exactly two ways, importing every predecessor
(never re-implementing):

1. **A live `desk` mode.** `cost.DeskAdapter` gains a third mode, `"live"`, beside `sub-process` and
   `re-prompted`. In live mode `open_turn` returns a `TurnContext` whose socket is the **live herdr
   socket** (resolved from `HERDR_SOCKET_PATH`, else `~/.config/herdr/herdr.sock`) and whose process is
   **`None`** — no fixture `desk_server.py` is ever spawned. The conductor's existing
   `Instrument(socket_path=context.socket_path)` path then speaks the **real herdr dialect** through the
   attested B2 adapter: resolve the desk by pane **label**, `agent.prompt` to the resolved pane, then the
   §4.5 fenced read (`pane.wait_for_output` to the `⟦END …⟧` marker). An unreachable live socket, or a
   desk resolving to a pane with no agent (`agent_not_found`), surfaces as an **outage / blocked hold** —
   INCONCLUSIVE, never a fixture stand-in, never a guessed answer.

2. **A runtime config-read.** A new module (`softconfig.py`) reads, at runtime, from a soft-layer config
   file the values the run currently hard-codes: each desk's **codex §2 emphasis**, **voice**, **model**,
   and the **cycle budget / hold / poll** (the `DESK_FUNCTION_SPECS` table and `COST_MODEL` charges +
   default mode). The conductor reads through it. **Absent soft config → the declared defaults** (B4's
   exact bytes/values — nothing attested is un-done; the fixture run's behaviour is unchanged).
   **Malformed or partial soft config → INCONCLUSIVE**, never silently substituted (lens 3/6).

Everything else is out of scope. The constitution (real desks into the seats) is **not** this round — the
bridge only provides the *code path* to a live desk and the *read path* to its soft config, so that the
constitution (soft mode, S first) can follow without any further firmware change.

---

## 2. Acceptance criteria — quoted verbatim

### C1 — the live desk mode (join the conductor to the live herdr socket)
> "…join the conductor to the live herdr socket via the attested B2 `instrument.py` (a live `desk` mode)…"
> — Amihai's instruction, 2026-08-30.

`cost.DeskAdapter` supports a third mode `"live"`; in it, a turn speaks the **real herdr dialect** through
the imported B2 `Instrument` — resolve the desk by pane **label** on every turn, `agent.prompt` to the
resolved pane, fenced read via `pane.wait_for_output`. No fixture process is spawned (the mode is joined
to the live socket, not a stand-in).

### C2 — live mode fails closed, never into a fixture (lens 6)
> "…**both spawn the fixture `desk_server.py` — never the live herdr socket**…" — `FACTS.md`, 2026-08-30.

In live mode: an absent/unreachable live socket → an outage hold (INCONCLUSIVE); a desk resolving to a
pane with no agent (`agent_not_found`) → a blocked hold. Neither case spawns `desk_server.py`, neither
returns a fake answer, neither reads clean. The centre guard (S / podium) refuses before any byte
(K4, T-R3-02).

### C3 — the runtime config-read (the soft layer at runtime)
> "…the conductor reads, at runtime, from Pi's `settings.json` + `AGENTS.md` + skills + prompts: the
> cycle budget/hold/poll, each desk's codex §2 emphasis, its voice, its model." — REVERSE-ENGINEERING.md
> §4.2 (candidate #2), 2026-08-29.

A `softconfig` module reads, at runtime, each desk's **§2 emphasis**, **voice**, **model**, and the
**cycle budget / hold / poll** from a soft-layer config file; the conductor's prompt and budget paths read
through it — the hard-coded `DESK_FUNCTION_SPECS` / `COST_MODEL` literals are no longer the conductor's
source of truth (they become the **declared defaults**).

### C4 — declared defaults, fail-closed (lens 3)
> "…a guess that reads as a fact is the failure this whole flow exists to prevent." — commission template
> §4 (the standing rule).

Absent soft config → the conductor resolves exactly B4's declared values (byte-identical prompt/budget
behaviour — the fixture run is unchanged, nothing attested is un-done). Malformed / partial soft config
(missing a desk, wrong type, bad field) → **INCONCLUSIVE**, never a silently substituted value; the run
records the reason.

### C5 — import, never re-author (D14 loyalty)
> "…any interpretation, decoding and compiling MUST be loyal to `5qln.com/codex`." — D14.

The B2 `instrument.py`, P4a's `surface.py`/`conformance.py`/`step.py`, P4b's `block.py`/`arrangement.py`/
`grammar.py`, B3's `descent.py`, and B0's ledger are imported by path, **sha-pinned**, never re-implemented.
No new decoding operation, no new L1 symbol, no sixth corruption code, no re-authored socket dialect.

### C6 — nothing attested is un-done
> "Nothing attested is un-done; the triage *uses* B0–B4." — STATE.md, 2026-08-29.

The two fixture modes (`sub-process`, `re-prompted`) and every attested predecessor's suite stay green.
The bridge is **additive**: it adds a third mode and a read path; it does not change the behaviour of any
attested code path.

### C7 — cold restart from disk alone (lens 5)
> "…a *new process* must rebuild state from disk alone; test the second process." — the six lenses.

A fresh process re-arms the live mode and the config-read from disk alone (soft-layer files + ledger +
the attested predecessors) with byte-identical next-action behaviour — no in-memory state is trusted
across a restart.

### Claims (K1–K5)

- **K1 — stdlib, deterministic, no LLM.** The bridge adds no network, no subprocess-beyond-the-attested,
  no LLM, no wall-clock in logic. The live socket is the only I/O, and it is the attested instrument's.
- **K2 — byte-exact enumerated forms.** The §2-emphasis and voice bytes come from the enumerated tables
  (P4b `PHASE`/`EQUATION_FORMS`), never normalised (`⋂→∩`, `′→'`, spacing collapse = renaming an L1
  symbol).
- **K3 — the click is never a machine verdict.** No authenticity verdict; the machine never claims
  arrival at ∞0 (HC-1/HC-2 permanently INCONCLUSIVE).
- **K4 — the B2 guards hold.** The centre guard refuses S/podium before any byte; an unresolvable write
  target is refused too (fail closed).
- **K5 — diff-ability.** The soft config is a **data file** (one place to change, diff-able, versioned),
  never code. The pane-label → desk map stays a config table; no code derives meaning from a displayed
  label.

### The six lenses (the verifier runs these; author so they pass, and so a blind spot reads
INCONCLUSIVE, never clean)

1. **Criterion match** — measure each criterion *as written*, not a neighbour of it.
2. **Invariant end-to-end** — the live-mode + config-read behaviour holds across a whole run, not per call.
3. **Absence vs validity** — absent socket / absent soft config / absent agent / empty file must never
   read valid (sha256 of empty = `e3b0c44298fc…`).
4. **Encoding** — push `∞0′ → ‖` through every string field (soft-config voice/emphasis values included);
   text-mode byte seeks break on it.
5. **Cold restart** — a *new* process rebuilds the live mode + config-read from disk alone; test the
   second process.
6. **Blind tool** — an unavailable live socket or an unconstituted desk reports INCONCLUSIVE, never clean,
   never a fixture stand-in.

---

## 3. Verified-facts block (do not re-probe — `FACTS.md`, executed 2026-08-30)

- **Live socket is UP, live desk state probed 2026-08-30 (executed, read-only):** `ping` →
  `{"type":"pong","version":"0.8.2","protocol":20,…}`. `pane.list` resolves six panes; the desk labels
  are `podium` (S, `w8:p2`), `G` (`w8:p3`, **agent `pi`, idle** — the one constituted desk), `Q`
  (`w8:p5`, `agent_status: unknown`), `V` (`w8:p4`, unknown), `P` (`w8:p6`, unknown), plus unrelated
  `w7:p1` (label null). Only **G** carries a live Pi agent; the other four desks are bare panes — so a
  live `agent.prompt` to G/Q/V/P resolves G (real, paid turn) and Q/V/P as `agent_not_found` (fail
  closed). **The centre guard must refuse S/podium; no prompt to `w8:p2`.**
- **One request per connection** (carried): a second request on the same socket dies
  (`BrokenPipeError`); the B2 adapter already reconnects/retries-once — never "optimise" that away.
- **The live socket path:** `~/.config/herdr/herdr.sock`, env `HERDR_SOCKET_PATH` (empty on the box —
  the default is resolved). `srw------- deploy`.
- **B4 `cost.py` (read, 2026-08-30):** `DeskAdapter.__init__(spec, socket_dir, mode=None, python=None)`;
  `mode` defaults from `COST_MODEL["default_mode"]` (`"re-prompted"`); `open_turn` returns
  `TurnContext(socket_path, process)` where the socket is the **fixture** `desk_server.py`'s own socket;
  both modes call `_spawn`. The `"live"` mode is the addition: `open_turn` returns
  `TurnContext(live_socket_path, None)` and `close_turn`/`memory_bytes` treat `process is None` as
  no-op / 0 (the stateless path already handles this).
- **B4 `run.py` (read, 2026-08-30):** `Conductor.__init__` resolves the mode from `spec["mode"]` vs
  `cost.DEFAULT_MODE`; `_desks_adapter()` builds `cost.DeskAdapter(self.spec, self.socket_dir,
  mode=self.mode)`; `_do_turn` opens a turn, builds `Instrument(socket_path=context.socket_path, …)` and
  calls `instrument.prompt_desk(desk, prompt, key, …)`. The prompt is built by `_prompt_text` from
  `FOUNDING_SENTENCE` + `ATTENTION_READINGS[desk]` + `DESK_FUNCTION_SPECS[desk]` (all hard-coded via
  `surface_contract` → `fixtures/desk.py`). The bridge makes these soft-config-driven with declared
  defaults.
- **B2 `instrument.py` (read):** `prompt_desk(desk, text, turn_key, …)` already does the full live
  dialect — centre guard → label-resolve → `_assert_live_label` → append the `⟦END …⟧` fence instruction
  → `agent.prompt` → `read_to_marker`. It is the attested path; the bridge does not re-implement it.
- **`agent.prompt`'s success shape stays inert** (H-B4-3 carried): the run reads the fenced read, never
  the success shape.
- **No desk is constituted except G** (H-B4-1 partially lifted by the bridge, but the constitution is
  still the *next* round — see H-BRIDGE-1).

---

## 4. The interface to the attested rounds (predecessors — import, never re-author)

Staged under `./predecessors/{b2,p4a,p4b,b3}/`; the B0 ledger is on `FRACTAL_LEDGER_DIR`. dsh imports and
extends; it re-implements none of them.

- **B2** (`predecessors/b2/`): `driver.py`, `instrument.py`, `lens.py`, `walker.py`, `dialects.py` — the
  one-cell walk and the herdr socket surface (the live-desk path is `instrument.prompt_desk`).
- **P4a** (`predecessors/p4a/`): `step.py`, `surface.py`, `conformance.py` — the D.12 check.
- **P4b** (`predecessors/p4b/`): `block.py`, `arrangement.py`, `grammar.py`, `install.py`,
  `surface_contract.py` — the desk grammar seated at addresses (the source of the enumerated §2
  emphasis / voice bytes, `PHASE` and `EQUATION_FORMS`).
- **B3** (`predecessors/b3/`): `descent.py`, `surface_contract.py` — the descent the run derives cells from.
- **B4** (the immediate predecessor, carried in `./predecessors/b4/`): `run.py`, `cost.py`, `trail.py`,
  `surface_contract.py` — the unattended run the bridge extends.

### Binding — the names this round ships

| binding | real name | where |
|---|---|---|
| `cost_module` | `cost` | `cost.py` — `COST_MODEL` (now carrying a `"live"` mode entry), `DeskAdapter`, `TurnContext` |
| `softconfig_module` | `softconfig` | `softconfig.py` — `SOFT_DEFAULTS`, `load_soft_config`, `desk_emphasis`, `desk_voice`, `desk_model`, `budget_of` |
| `conductor_module` | `run` | `run.py` — `Conductor` (live mode + runtime config-read) |
| `surface_contract_module` | `surface_contract` | `surface_contract.py` — pins the new module; declares the bridge surface against the imported contract |
| `selftest_module` | `selftest` | `selftest.py` — the author's suite, a hypothesis never a result |
| `fixture_live_server` | `live_server` | `fixtures/live_server.py` — a server speaking the **real herdr dialect** on its own socket (B2 `FakeHerdrServer` shape) for the live-mode test |

The functions are the real surface; the names are stable and documented here. The verifier's pack may bind
different names than this table — the functions are what is checked.

---

## 5. The runtime config-read — the soft layer (read, never author)

The soft config is **data**, not code, and not doctrine. Its schema is a **declared default** (H-BRIDGE-2:
the constitution will write the real soft files). The read path is the bridge's deliverable; the *content*
the constitution writes is the next round's.

Minimum shape the read must support (per desk `S/G/Q/P/V`), all caller-overridable, all with a declared
default equal to B4's current hard-coded value:

| key | meaning | declared default (B4's exact value) |
|---|---|---|
| `emphasis` | the desk's codex §2 emphasis (its `phase_gate` + decoding ops) | P4b `PHASE[desk]["phase_gate"]` + `["decoding"]` |
| `voice` | the desk's voice / seat (the instruction block register) | P4b `PHASE[desk]["seat"]` |
| `model` | the desk's model | D6 (one model across four desks — the single value, declared) |
| `budget` | the cycle budget / hold / poll / spend ceiling | B4 `COST_MODEL["charges"]` + `spec["budget"]` |

The read must be **deterministic, stdlib-only, no network, no LLM** (K1), and its values must be
**byte-exact against the enumerated tables** (K2). Absent file → defaults; malformed/partial → INCONCLUSIVE
with the reason (C4).

---

## 6. Holds — declare, never guess

- **H-BRIDGE-1 — no desk is constituted except G.** The live mode is tested two ways, both safe: (a) a
  fixture live-server speaking the real herdr dialect on its own socket (B2 `FakeHerdrServer` shape) —
  this exercises the full live `prompt_desk` path deterministically; (b) the **live socket, read-only**
  (resolve desks by label, `pane.get`/`agent.get`) — proving the live dialect is reached. A real
  `agent.prompt` to the G desk is a **paid Pi turn**, deferred to the constitution. The centre guard must
  refuse S/podium on the live socket too.
- **H-BRIDGE-2 — the soft-config file location + schema are provisional.** The bridge ships the read path
  with a declared default location; the constitution (S first) writes the real soft files. The bridge
  authors no desk personality and no §2 content — it reads them.
- **H-BRIDGE-3 — `agent_prompted`'s success shape stays inert (carried H-B4-3).** The fenced read is the
  answer, never the success shape.
- **H-BRIDGE-4 — the human's gate act is untouched (carried H-B4-4).** No podium write, no `cell-attest`
  invocation, no typed word. Attestation stays a TTY act.

---

## 7. Prohibitions

No write path to the podium (`pane.send_text/input/keys` at the centre). No git, no attestation, no claim
that anything ran. No gate semantics re-implemented outside `fractal-engine`. No re-implementation of the
herdr socket dialect, the D.12 checks, the desk grammar, or the descent. **No fixture `desk_server.py`
spawn in live mode.** No hard-coded §2-emphasis / voice / model / budget literal in the conductor's control
flow (they live in declared defaults + the soft config). No sixth corruption code, no new L1 symbol, no
new decoding operation, no renamed symbol. No byte normalisation (`⋂→∩` is renaming). No authenticity
verdict. No tentative node promoted or consumed. The machine never resolves a hold. Nothing described as
attested/decided/verified that this commission does not mark so.

---

## 8. Deliverables — under `./authored/` (layout yours to vary; content is what is checked)

- `cost.py` — the dual-mode adapter **extended with `"live"`**: live mode returns a `TurnContext` on the
  live socket with no process; the two fixture modes unchanged.
- `softconfig.py` — the runtime config-read (per-desk §2 emphasis / voice / model + budget, declared
  defaults, fail-closed on malformed).
- `run.py` — the conductor extended: resolve `"live"` mode; prompt + budget read through `softconfig`.
- `surface_contract.py` — imports the attested predecessors by path, sha-pinned (now including
  `softconfig`); declares the bridge surface against them.
- `selftest.py` — the author's own suite (a hypothesis, not a result).
- `phase-card.md` — predictions only (never results) + the D14 divergence log.
- `fixtures/` — at least: a fixture live-server speaking the real herdr dialect (deterministic, with an
  unconstituted-desk `agent_not_found` case and an absent-socket case) · a live-mode run that resolves
  desks and reads the fence · a soft-config override that changes the runtime read (and a malformed one
  that reads INCONCLUSIVE) · a cold-restart fixture that re-arms the live mode + config-read from disk
  alone.

---

## 9. Budget

**ONE authoring generation.** No exploratory chat. Artifact + phase card in, out.
