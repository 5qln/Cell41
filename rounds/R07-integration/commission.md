# COMMISSION — R07 · integration (the seam — wire the engine to the live cell)

**Working handle:** "integration." **The phase name and slot are Amihai's to name** — this document
uses the working handle `integration` only until he names it (SCOPE D4).

**Author:** dsh (`deepseek-v4-pro`, ONE generation). **Verifier:** Hermes profile `herdr`, separately,
against a pack written before it judges anything. `builder ≠ verifier`.

**Workspace:** `/home/deploy/the-cell/rounds/R07-integration/` — write **only** inside `./authored/`.
A hash fence outside `authored/` is checked before and after.

**§1.10 of the Codex governs every conflict: where a document diverges from `5qln.com`, the source is
authoritative** — including this commission. The integration **binds** the attested engine; it never
re-authors it. The scope this commission implements is `docs/fractal-herdr/SCOPE-integration-engine-to-live-cell.md`
(staged at `./sources/SCOPE-integration-engine-to-live-cell.md`); where this commission and the SCOPE
differ, the SCOPE's citations to the attested files win, because they were read from disk.

---

## 0. His words and the standing decisions that bind this round

The build so far (all attested and closed): **B0** ledger + record · **B1** read-only walker · **B2**
driver · **P4a** step mode · **P4b** desk bundles · **B3** descent · **B4** the unattended run · **the
Grammar** · **the bridge** · **R06 Orchestration**. Everything after R06 is **soft mode**; this round
is the seam that connects the finished engine to the live cell — **not** new engine logic.

**The governing line (SCOPE §0, verbatim):**

> "the soft layer must never contain driving logic — it only points at the engine. Slash commands are
> the seam. One surface, two callers: the human types `/conduct`, or the conductor S calls the same
> command."

**Amihai's instruction (2026-08-31, verbatim substance):**

> "use as much native tools from herdr and pi [as possible]" — the bridge is between the hard-coded
> framework (ASIC / firmware — never touched during use) and the soft coding (the agents' configs, the
> macros and recipes for orchestration). The seam must *bind* the native herdr/pi tool surface, never
> re-implement it.

**Standing decisions (unchanged):** D12 — success in a phase = contextual DECODE + COMPILE of output
xyzab. D14 — every decode/compile loyal to `5qln.com/codex`. §1.6 — no V without ∞0′. §5.5 — TENTATIVE
is temporal, never epistemic. The conductor is S (§4.8). The human's gate act is a TTY act, never
carried by any channel. **The R06 engine is the immediate predecessor — the integration *binds* it,
never re-implements it.** The engine's only wire-write is the attested B2 `Instrument.call` chokepoint
(`agent.prompt`), speaking the native herdr socket dialect; that single chokepoint stays the single
chokepoint.

---

## 1. What to build — one paragraph, no doctrine

**The integration** = W1 + W2 of the SCOPE, in one artifact: (a) a **thin, logic-free command surface**
(`cellctl`) over the attested engine functions — one subcommand per module, each parsing arguments and
making exactly **one** engine call, containing **no** socket code, no prompt assembly, no record-writing
— plus a **live cell spec** (`spec.json`, the caller-supplied data: scenario/ledger/trail/socket
resolution/materialize dirs/soft-config/timeouts-as-data); and (b) the **enforcement suite**
(`verify-integration.sh` + its scans) that makes "no driving logic in the soft layer" a structural,
mechanically-checkable fact (SCOPE §4, legs 1–3). The bindings to the two callers (herdr plugin actions
for the human, the pi extension for the conductor) are **later work** (SCOPE W5), not this round; the
CLI is what they will both shell to. The engine functions are imported **by path, sha-pinned**, through
a `surface_contract.py` in the exact pattern of R06 — never re-declared, never re-implemented.

---

## 2. Acceptance criteria — quoted verbatim

### C1 — the seam is a thin binding, one call each
> "each subcommand parses arguments and makes one engine call" — SCOPE §1.1.

Each subcommand of the CLI parses its arguments and makes **exactly one** engine call. The wrapper
contains **no socket code, no prompt assembly, no record-writing, no ledger/trail logic** — the only
socket client on the box remains the pinned engine's `Instrument.call` (R06 C7 precedent).

### C2 — the write side is never exposed as a command
> "The **write** side (`agent.prompt`) is deliberately NOT exposed as a command — exposing it would
> create a second conduction channel in the soft layer" — SCOPE §1.1.

No command wraps `agent.prompt` or any write verb. The read side (`/states`, via
`Orchestrator.read_states`) is the only desk-facing command; an absent socket reads `{"status":"absent"}`
honestly, never a fixture stand-in.

### C3 — plan-equivalence dry run (the wrapper adds nothing)
> "`/conduct --plan-only` over a pinned scenario … must produce byte-identical plan output to calling
> `word.decode_scenario` + `navigate.plan_walk` directly — proving the wrapper adds nothing" — SCOPE §4
> (verification check 3).

A `--plan-only` run over a pinned scenario produces **byte-identical** output to the direct engine calls
(diff-ability lens applied to the seam itself).

### C4 — the enforcement suite holds as a structural fact (legs 1–3)
> "a mechanical scan over `desks/`, `plugin/bin`, `.pi/` configs, and any extension packages: forbidden
> tokens = herdr **write verbs** … Result must be zero … an undeclared bin, an undeclared tool, an
> undeclared import of the engine = FAIL … unknown fields = INCONCLUSIVE refuse" — SCOPE §4, legs 1–3.

The suite implements three legs, each mechanically checkable and each failing on a deliberately-injected
violation: **(L1) capability scan** — the soft layer contains no driving write verb (`herdr_send_prompt`,
`herdr agent prompt`, `agent.prompt`, `pane.wait_for_output`, `send-keys`/`send_text`/`send_input`,
socket-client code, subprocess-to-`herdr` with a prompt/wait verb), except the declared human-TTY
allowlist (`cell-plant`/`cell-attest`); **(L2) entry-point census** — every executable in the soft layer
is a declared member of the seam manifest, and no soft-layer file imports the pinned engine modules
directly (the CLI is the only path); **(L3) config-schema validation** — every file the engine reads
from the soft layer validates against a declared schema, unknown fields = INCONCLUSIVE refuse.

### C5 — the run lock (concurrent safety at the seam)
> "a simultaneous human `/conduct` and S `/conduct` on the same trail/work-dir is still an interleaving
> hazard … The CLI therefore takes one run lock on the cell's work dir (a single flock around the whole
> run)" — SCOPE §3.3.

The CLI takes a single flock on the cell's work dir around the whole run; a second `/conduct` on the
same dir blocks rather than interleaves. The lock lives in the wrapper, not the engine.

### C6 — fail-closed, INCONCLUSIVE never clean
> "absent/empty/missing must never read valid" · "unavailable/rate-limited must report INCONCLUSIVE,
> never 'clean'" — six lenses 3 and 6.

Absent scenario / absent soft-config / absent socket / drifted pin / malformed surface all read
INCONCLUSIVE with a reason — never a substituted value, never a clean verdict, never a fixture stand-in.

### C7 — the pinned seams stay the import boundary
> "the sha-pinned `surface_contract.py` seams … are the import boundary and stay the import boundary" —
> SCOPE §1.1.

The engine modules are imported by path under sha pins; a drifted or missing pinned file refuses the
import (ImportError), exactly as R06's `surface_contract.py` does. No soft-layer file may import a
pinned module directly.

### Claims (K1–K5)

- **K1 — stdlib, deterministic, no LLM.** The CLI and the enforcement suite add no network, no LLM, no
  wall-clock in logic, no new subprocess beyond the attested engine's own. The only socket client is the
  pinned `Instrument`.
- **K2 — byte-exact, never normalised.** The CLI forwards the engine's byte-exact enumerated forms
  (equations, §2-emphasis/voice bytes) untouched; no `⋂→∩`, no `′→'`, no spacing collapse.
- **K3 — the click is never a machine verdict.** No authenticity verdict; HC-1/HC-2 stay INCONCLUSIVE;
  nothing claims arrival at ∞0.
- **K4 — the B2 guards hold.** The centre guard refuses S/podium before any byte; an unresolvable write
  target is refused (fail closed). The write allowlist stays frozen (no `herdr_start_agent`-equivalent
  authority is added this round — D1 is deferred).
- **K5 — diff-ability.** The live cell spec (`spec.json`) and the soft config are **data files** — one
  place to change, diff-able, versioned — never code. The node→desk map stays a config table.

### The six lenses (the verifier runs these; author so they pass, and so a blind spot reads
INCONCLUSIVE, never clean)

1. **Criterion match** — measure each criterion *as written*, not a neighbour of it.
2. **Invariant end-to-end** — plan → walk → materialize → conduct behaviour holds across a whole run,
   not per call.
3. **Absence vs validity** — absent word / absent soft config / absent socket / empty file must never
   read valid (sha256 of empty = `e3b0c44298fc…`).
4. **Encoding** — push `∞0′ → ‖` through every string field (command args, spec, address, voice,
   emphasis); text-mode byte seeks break on it.
5. **Cold restart** — a *new* process rebuilds the plan + the enforcement scans from disk alone; test the
   second process (and that a second `/conduct` honours the run lock).
6. **Blind tool** — an unavailable live socket or an unconstituted desk reports INCONCLUSIVE, never
   clean, never a fixture stand-in.

---

## 3. Verified-facts block (do not re-probe — these were executed)

- **Live socket is UP** (re-probed 2026-08-31): herdr 0.8.2, protocol 20. Five Pi desks constituted
  (`desks/{S,G,Q,P,V}/`), all idle, model `deepseek-v4-pro`. **The authoring pass uses fixtures only,
  no live box** — no real `agent.prompt` is sent this round (H-INT-1).
- **The engine functions the CLI binds** (per SCOPE §1.1, read from disk by dsh 2026-08-30):
  `word.py` `load_scenario_file`/`decode_scenario` · `navigate.py` `plan_walk`/`walk` · `materialize.py`
  `materialize`/`read_materialized` · `orchestrate.py` `main`/`Orchestrator.read_states` · `softconfig.py`
  `load_soft_config`/`desk_emphasis`/`voice`/`model`/`budget_of` · `cost.py` `spend_from_records`/
  `charge_for` · `descent.py` `zoom_in`/`zoom_out`/`path_between`/`validate_signed_path`/`validate_word` ·
  Grammar `decoder`/`compiler`/`corruption`. These are the attested shapes; the CLI wraps them, it does
  not re-derive them.
- **The engine's only wire-write is `agent.prompt`** (B2 `Instrument`, `WRITE_METHODS` frozen). The
  socket dialect, the prompt assembly, the record-writing, and the `⟦END …⟧` fence all live inside the
  pinned engine — the CLI must not duplicate any of them.
- **The predecessors are staged under `./predecessors/`** — b2, p4a, p4b, b3, b4, bridge,
  r06-orchestration — and the B0 ledger is on `FRACTAL_LEDGER_DIR`
  (`/home/deploy/the-cell/ledger/fractal_ledger.py`).
- **The held texts are staged under `./sources/`** — `5qln-codex.txt`, `5qln-codex-appendix-D-the-fractal.txt`,
  and the SCOPE itself.

---

## 4. The interface to the attested rounds (predecessors — import, never re-author)

Staged under `./predecessors/{b2,p4a,p4b,b3,b4,bridge,r06-orchestration}/`. The CLI imports the engine
through the R06 `surface_contract.py` (which already pins and re-exports `word`, `navigate`,
`materialize`, `orchestrate`, `softconfig`, `cost`, `descent`, and the B2 `Instrument`), sha-pinned by
path — **never** by copying engine logic into the wrapper.

- **B2** — the herdr socket surface; `Instrument` is the single wire chokepoint (native herdr dialect).
- **P4a / P4b** — the step check and the desk grammar (the source of the enumerated §2 bytes).
- **B3** — `descent.py` (the address grammar: zoom, signed path, `validate_word`).
- **B4** — `run.py` / `trail.py` (the unattended run + readable trail).
- **bridge** — `cost.py` live desk mode + `softconfig.py` (the runtime config-read).
- **r06-orchestration** — `word.py` / `navigate.py` / `materialize.py` / `orchestrate.py` /
  `surface_contract.py` — the immediate predecessor; the CLI is a binding over exactly these.

### Binding — the names this round ships

| binding | real name | where |
|---|---|---|
| `cli_entry` | `cellctl` | one thin CLI; subcommand per module (candidates: `/word /plan /walk /materialize /conduct /config /cost /states /descent /decode /compile /check /trail`) |
| `spec_data` | `spec.json` | the live cell spec — caller-supplied data (scenario, ledger, trail, socket resolution, materialize dirs, soft-config path, `wait_timeout_ms`/`timeout_s`/`max_steps` as data) |
| `seam_module` | `surface_contract` | `surface_contract.py` — pins the engine modules + declares the seam manifest (command set + census) against them |
| `enforce_module` | `enforce` | `enforce.py` + `verify-integration.sh` — the three enforcement legs (capability scan · census · config-schema) |
| `selftest_module` | `selftest` | `selftest.py` — the author's suite, a hypothesis never a result |
| `fixture_desk_harness` | `desk_harness` | `fixtures/desk_harness.py` — a fake desk harness (deterministic, no live box) for the authoring pass |

The functions are the real surface; the command names are **candidate** (SCOPE D4 — his to name). The
verifier's pack may bind different names; the functions are what is checked.

---

## 5. Holds — declare, never guess

- **H-INT-1 — no live `agent.prompt` is sent this round.** The CLI is tested against a fixture desk
  harness only. The first real paid turn is Amihai's alone to authorize (SCOPE D6, W4) — later, and not
  by this authoring run.
- **H-INT-2 — command names and the round's name/slot are provisional** (SCOPE D4). The working handle is
  `integration`; the subcommand names above are candidates. His to name.
- **H-INT-3 — child-spawn ownership is deferred** (SCOPE D1, Seam C/D). This round adds no
  `herdr_start_agent`-equivalent write; the engine's `WRITE_METHODS` stay frozen. The desk-executed
  pattern (engine declares, desk spawns via its native pi-herdr tools) is a candidate for W6, not this
  round.
- **H-INT-4 — the scenario schema stays provisional** (carried H-ORCH-2) and the live spec's numbers
  (timeouts, hold/poll) are **unknown until the first real run** (SCOPE Seam E, W4). They are declared
  data in `spec.json`, never hard-coded in logic.
- **H-INT-5 — the live constitutions do not yet speak the §3.6 surface** (SCOPE Seam B). This round
  authors the CLI + enforcement; the constitution upgrade is W3, soft-mode work done with Amihai, not
  this round. The CLI must therefore report `no-surface-announced`/`surface-malformed` honestly when the
  engine holds — never paper over it.

---

## 6. Prohibitions

No write path to the podium (`pane.send_text/input/keys` at the centre). No git, no attestation, no
claim that anything ran. No gate semantics re-implemented outside `fractal-engine`. No re-implementation
of the herdr socket dialect, the prompt assembly, the record-writing, the D.12 checks, the desk grammar,
the descent, the bridge's live mode, or R06's word/navigate/materialize/orchestrate. **No write verb
exposed as a command (C2). No new socket/client code — the pinned `Instrument` is the only client (K1).**
No new engine write (`WRITE_METHODS` frozen, H-INT-3). No hardcoded topology enum. No hard-coded
§2-emphasis/voice/model/budget literal in the wrapper. No sixth corruption code, no new L1 symbol, no
new decoding operation, no renamed symbol. No byte normalisation. No authenticity verdict. No tentative
node promoted or consumed. The machine never resolves a hold. Nothing described as
attested/decided/verified that this commission does not mark so.

---

## 7. Deliverables — under `./authored/` (layout yours to vary; content is what is checked)

- `cellctl` (or equivalent entry module) — the thin CLI: one subcommand per engine module, each making
  exactly one engine call; `--plan-only` support on `/conduct` (C3); the run lock (C5); no write verb
  exposed (C2).
- `spec.json` (+ a loader) — the live cell spec as declared data (H-INT-4).
- `surface_contract.py` — pins the engine modules by path/sha (importing R06's contract), declares the
  seam manifest (command set + entry-point census) against them; drifted/missing pin → ImportError (C7).
- `enforce.py` + `verify-integration.sh` — the three legs (capability scan · census · config-schema),
  each with a deliberately-injected violation case in fixtures that must FAIL (C4).
- `selftest.py` — the author's own suite (a hypothesis, not a result).
- `phase-card.md` — predictions only (never results) + the D14 divergence log.
- `fixtures/` — at least: a fake desk harness (deterministic, with an unconstituted-desk
  `agent_not_found` case and an absent-socket case) · a pinned scenario for the plan-equivalence dry run
  (C3) · enforcement fixtures with injected violations (a forbidden write verb, an undeclared bin, an
  unknown config field) that the suite must each catch · a cold-restart fixture (second process, run-lock
  honoured).

---

## 8. Budget

**ONE authoring generation.** No exploratory chat. Artifact + phase card in, out.
