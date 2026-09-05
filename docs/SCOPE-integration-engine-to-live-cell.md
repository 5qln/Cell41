# SCOPE OF WORK — wiring the firmware engine to the live cell

*Consultation document (K-side: structure, citations, candidate requirements — not doctrine).
Prepared 2026-08-30 from the files on disk. Nothing here was built or executed against the live
cell. Names marked “candidate” are proposals; every phase card in this repository says the real
names are Amihai's to give (`rounds/R06-orchestration/authored/phase-card.md:3`).*

**Method note (honesty about sources):** this scope was grounded by reading the attested firmware
under `rounds/*/authored/`, the bridge, the Grammar, the live desk constitutions (`desks/*/`), the
herdr plugin (`plugin/herdr-plugin-v4.toml`, linked as `cell.fiveqln` per
`~/.config/herdr/plugins.json`), the pi-herdr extension
(`~/.pi/agent/npm/node_modules/@andrewjacop/pi-herdr/src/tools/orchestration.ts`), and the on-disk
traces of the 2026-08-30 descent (`nodes/_/*.level1.md`, `nodes/_/*.child.md`, child agents in
`~/.config/herdr/session.json`). Two cited sources were **not found on disk**: the brief's
`docs/fractal-herdr/RECORD-live-descent-2026-08-30.md` (no such path exists under
`/home/deploy/the-cell` — the acceptance record for "re-run the descent through the engine" must be
located or planted, see W0), and the scoped-memory field (`scope_memory.py context --scope
fractal-herdr`) returned an empty pack. Every claim below cites a file and, where useful, a line.

The governing line, as given: **the soft layer must never contain driving logic — it only points
at the engine. Slash commands are the seam. One surface, two callers: the human types `/conduct`,
or the conductor S calls the same command.**

---

## 0. The picture in one paragraph

The engine already contains every moving part of conduction, attested and sha-pinned: the scenario
decoder (`word.py`), the sign-walk (`navigate.py`), the materializer (`materialize.py`), the live
conductor (`orchestrate.py`), the live desk adapter + runtime config-read (bridge `cost.py` /
`softconfig.py` / `run.py`), the ledger (B0), the read-only walker (B1), the herdr dialect (B2),
the descent/address grammar (B3), the unattended run (B4), and the Grammar (decoder D1 + compiler
C1 + the 48-check + HC-1/HC-2). The live cell (five real Pi agents in herdr panes, booted from
`desks/<letter>/boot.sh` with `SYSTEM.md` appended) does not call any of it: on 2026-08-30 S
re-derived conduction by thought, using the pi-herdr tools, and it worked — which proves the cell
can be driven and proves the engine was absent from the drive. The integration is therefore **not
new engine logic**; it is (a) a thin, logic-free command surface over the attested functions,
(b) a live-desk constitution that answers in the shape the engine already refuses anything else
(§3.6 surface + the `⟦END …⟧` fence), and (c) the binding of that one surface to the two callers.
The hard parts are exactly where the fixture world and the live world differ, listed in §5.

---

## 1. The seam inventory — what becomes callable, minimal surface each

One command per module, one thin CLI, **no logic in the wrapper**: each subcommand parses
arguments and makes one engine call. Inputs/outputs below are the attested function shapes
verbatim.

### 1.1 The minimal set (must be callable)

| Engine module (file) | Candidate command | Inputs | Outputs | Notes |
|---|---|---|---|---|
| `word.py` (`rounds/R06-orchestration/authored/word.py`) | `/word` | a scenario file path (or JSON): `{word, seed{address,ref,bound}, paths[{from,to,path}], nodes?, loop?}` | decode report: `ok` + decoded scenario · `malformed`/`absent`/`inconclusive` + reason (never a substituted value) | Wraps `load_scenario_file` / `decode_scenario` (`word.py:331,447`). The schema is **provisional** (H-ORCH-2) — one place to change, already true (`word.py:128-144`). |
| `navigate.py` (`rounds/R06-orchestration/authored/navigate.py`) | `/plan` | a decoded scenario | `{status, pattern: sequence\|parallel\|loop\|custom, visits[], pattern_evidence[]}` — **pure, no socket, no ledger** | Wraps `plan_walk` (`navigate.py:158`). The pattern derives from the signs (D.6); a `pattern`/`topology` field is refused at decode (C1/C2). |
| `navigate.py` | `/walk` | decoded scenario + a world wiring (live spec or a declared dry world) + `max_steps` | trace `{status: complete\|inconclusive\|refused\|step-limited, ended_in: ∞0′\|null, return_question, visits[] with per-step conformance}` | Wraps `walk` (`navigate.py:342`). The world protocol is `seed/turn/land/hold/ledger` (`navigate.py:47-56`); the live wiring already exists as `orchestrate._LiveWorld`. |
| `materialize.py` (`rounds/R06-orchestration/authored/materialize.py`) | `/materialize` (`--verify` for read-back) | decoded scenario + `out_dir` (+ optional plan visits) | `materialized` + per-node file shas (`SYSTEM.md`, `.pi/settings.json`, `skills/SKILL.md`, `tools/tool-surface.md`) · `--verify`: `ok`/`inconclusive` drift report | Wraps `materialize` / `read_materialized` (`materialize.py:227,301`); byte-exact, absent/empty/drifted = INCONCLUSIVE. |
| `orchestrate.py` (`rounds/R06-orchestration/authored/orchestrate.py`) | `/conduct` | scenario + spec (ledger path, trail path, socket resolution, materialize dirs, soft_config, `wait_timeout_ms`, `timeout_s`, `max_steps`) | run result `{status, ended_in, pattern, actions, return_question}`; side effects: per-gate B0 ledger records + B4 trail lines; exit codes 0/1/3/4 (`orchestrate.py:733-737`) | The composite. A CLI already exists (`orchestrate.py main`, `orchestrate.py:728`) — the slash command is a binding of it, not a re-implementation. |
| `softconfig.py` (`rounds/bridge/authored/softconfig.py`) | `/config` | optional soft-config path | read report `defaults`/`ok`/`inconclusive` + per-desk emphasis/voice/model + budget | Wraps `load_soft_config` + `desk_emphasis/voice/model` + `budget_of`. **Read-only** — writing `~/.config/herdr/soft.json` stays the constitution's act (H-BRIDGE-2). |
| `cost.py` (`rounds/bridge/authored/cost.py`) | `/cost` | ledger records + mode (+ optional soft charges) | declared spend, per-desk charges | Wraps `spend_from_records` / `charge_for` (`cost.py:161,202`); the run-end already emits it. Standalone for humans to see the budget. |
| B2 `instrument.py` — read side | `/states` | (resolved live socket from spec) | per-desk real states, read-only; absent socket carried `{"status":"absent"}` honestly | Wraps `Orchestrator.read_states` (`orchestrate.py:467-491`). The **write** side (`agent.prompt`) is deliberately NOT exposed as a command — exposing it would create a second conduction channel in the soft layer (see §4). |
| B3 `descent.py` (`rounds/R04-B3/authored/descent.py`) | `/descent` | address ops: zoom-in letter, zoom-out, or `from→to` | `zoom_in/zoom_out/path_between/validate_signed_path` results (the address grammar, the `+^k·(−x₁)…(−x_m)` normalization) | The "navigation system" of the metaphor, already machine-pure. Also `validate_word` for word lawfulness. |
| Grammar (`rounds/meta-implementation/authored/{decoder,compiler,corruption}.py`) | `/decode`, `/compile`, `/check` | surface text + phase/context (decode) · artifact inputs (compile) · any produced surface (check) | D1 filled symbol slots **as references, never text**; C1 emitted §3.6 surface + jacket; the 48-item validation table (CX/AD SYN/SEM/DRF, R1–R13, HC-1/HC-2) + corruption verdict (`L1 L2 L3 L4 V∅` only) | Library-only today (no mains). HC-1/HC-2 are **INCONCLUSIVE by design** (`compiler.py:1412`) — the "no claim of arrival" the agent re-discovers by thought is this, structurally. |
| B4/bridge `run.py` | (keep the existing CLI) | `--ledger --trail --spec --mode --max-actions …` (`run.py:1435-1449`) | the attested unattended run | Already callable as a CLI; the fixed S→G→Q→P→V cycle is a special case of a scenario word, so `/conduct` subsumes it — the run CLI stays for the attested B4 surface (C6: nothing attested is un-done). |
| `fractal_ledger.py` + B4 `trail.py` | `/trail` | ledger + trail paths | the readable trail (B4 `read_trail`) + dependency audit (`audit_payload_chains`) | The human's window into a running/ended run; required by B4's "readable trail" promise, cheap to wrap. |

### 1.2 Optional (callable, but not on the critical path)

- **B1 walker** (`rounds/R02-B1/authored/walker.py`): `Walker(socket_path, ledger_path).run(...)` —
  the standalone read-only lawfulness pass. The conductor's boot `read_states` covers the live
  need; the walker earns a command only if Amihai wants a standing watch mode. Defer.
- **`/seed`-adjacent human acts** (`plant`/`attest`): already exist as plugin actions
  (`plugin/herdr-plugin-v4.toml` actions `plant`, `attest`) with TTY guards — **unchanged** (the
  gate act stays a human TTY act, H-ORCH-4).

Everything above is a **binding**, never a new function: the wrappers contain no socket code, no
prompt assembly, no records. The sha-pinned `surface_contract.py` seams
(`rounds/R06-orchestration/authored/surface_contract.py:141-200`) are the import boundary and stay
the import boundary.

---

## 2. The bridge gap — fixture adapter vs. the real herdr/Pi desks

**Verdict first: `cost.py`'s live mode is sufficient as the socket adapter — no new adapter is
required.** The evidence:

- The live branch of `DeskAdapter.open_turn` returns `TurnContext(live_socket_path, None)` —
  the **real** socket resolved `override > HERDR_SOCKET_PATH > ~/.config/herdr/herdr.sock`,
  process `None`, no `desk_server.py` spawn of any kind (`cost.py:317-324`, `cost.py:81-90`).
- The dialect that speaks on that socket is the attested B2 `Instrument` — the real herdr
  protocol (`pane.list` → label resolution fresh per turn → `agent.prompt` → `pane.wait_for_output`
  to the `⟦END <turn_key>⟧` fence), which the bridge commission records was
  **"probe-verified against the live box"** (`rounds/bridge/commission.md:31-33`).
- Fail-closed is attested: unreachable socket → `outage` hold; desk resolving to a no-agent pane →
  `agent_not_found`; never a fixture stand-in (bridge C2, R06 lens 6).
- `DESK_LABELS = {podium:S, G, Q, P, V}` (`instrument.py:159-165`) already matches the live layout
  (`cell.layout.5desks.json` pane labels).

What the fixtures were, honestly: the bridge and R06 tested this dialect against
`fixtures/live_server.py` / `fixtures/desk_harness.py` — servers **speaking the real dialect** on
their own sockets, with a declared "constituted-all fiction". H-BRIDGE-1 and H-ORCH-1 both state
it: **no real `agent.prompt` has ever been sent to a live desk** — "a paid Pi turn, deferred to
the constitution." So the adapter is real; its first real use is the acceptance event of this
project. The gap is fourfold, and only one item is even partly adapter-shaped:

1. **The un-proven first cycle (the paid turn).** Prompt→fence→read has never completed against a
   live Pi pane. Fixture-scaled parameters will not survive contact: `orchestrate.py:170-171`
   defaults `wait_timeout_ms=5000`, `timeout_s=10.0` — real Pi thinking turns take minutes. These
   are **caller-supplied spec data**, so the fix is a live spec, not code — but the live spec's
   numbers are unknowns until the first run (they may not even be constants: hold/poll policy is
   soft-config's declared domain, bridge commission candidate #2). Open risks to verify in W4:
   the fence marker actually appearing in the pane's visible stream (Pi renders progress UI),
   output truncation (50 KB / 2000 lines — P4b `install.py` limits), ANSI handling.
2. **The live constitutions do not speak the §3.6 surface.** The engine refuses anything else:
   `parse_surface` absent → hold `no-surface-announced`; malformed → hold `surface-malformed`
   (`orchestrate.py:450-458`; same in bridge `run.py:677-687`). The live desks' `SYSTEM.md` files
   carry the seal and seat but **zero mention of a surface, a fence, or `⟦SURFACE⟧`** (grep over
   `desks/*/SYSTEM.md` returns nothing). The engine's prompt does say "answer through your §3.6
   surface" (`run.py:610-612`), but a desk that has never been shown its §3.6 shape cannot honor
   it. This is **constitution content (soft mode, S first)** — the bridge authors no desk
   personality (H-BRIDGE-2) — and it is the single largest piece of work in this project: aligning
   each desk's `SYSTEM.md`/`AGENTS.md` with the P4b bundle content (`grammar.render_bundle`,
   `grammar.py:541`) and the surface contract the engine parses.
3. **Child spawn ownership (the descent seam).** The engine's attested write allowlist holds
   exactly one write: `agent.prompt` (`instrument.py` — `WRITE_METHODS`, frozen, B1's read-only
   set "is never widened"). The engine **cannot start agents**. The observed 2026-08-30 descent
   spawned five child agents via `herdr_start_agent` — a pi-herdr capability, exercised by S's own
   reasoning (S's spawn notes in `desks/S/.pi/prompts/guide.md` §5). Under the governing line, a
   conducted descent needs one owner: either (i) a new attested firmware write (a new round — it
   touches a sealed, attested module), or (ii) the desk-executed pattern: the engine materializes
   the child cell and **declares** the spawn; the desk executes the declaration with its herdr
   tools — the same declared/executed split the engine already uses for `activate` (H-ORCH-3).
   Genuinely open — see D1 in §5.
4. **Schema drift between emitted cells and real Pi settings.** The materializer's
   `.pi/settings.json` uses `{model, thinking, tools}` (`materialize.py:105-116`); a real desk's
   settings use `{defaultProvider, defaultModel, defaultThinkingLevel, defaultTools}`
   (`desks/*/.pi/settings.json`). The live desks also boot via `boot.sh` with `SYSTEM.md` appended
   and load `AGENTS.md` from cwd — a shape the materializer does not emit (it emits
   `SYSTEM.md/.pi/settings.json/skills/SKILL.md/tools/tool-surface.md`, `materialize.py:215-219`).
   Reconciling the two shapes (adopt the materializer's as the desk format, or map between them)
   is a one-time schema decision with doctrine weight (the constitution's shape is soft mode, S
   first). Mechanically small; canonically significant.

Also carried: the live charges are declared stand-in mirrors of re-prompted
(`COST_MODEL["charges"]["live"]`, `cost.py:143-146`) pending the first real measurement (H-B4-2 /
H-BRIDGE-1) — the first runs supply the data, which is a config change, not a build.

---

## 3. The two callers — one command, human and conductor

**The technical shape: one logic-free CLI, two bindings onto it, both already have working
precedents on this box.**

```
                    ┌── herdr plugin action  ←── the human  (cell UI / herdr plugin action invoke)
cellctl <command> ──┤
  (thin, no logic) └── pi slash tool         ←── conductor S (pi extension package)
                          │
                          ▼
        engine functions (pinned, sha-verified) ── the ONLY wire path: B2 Instrument
```

1. **The human's binding — herdr plugin actions.** The cell plugin is already linked
   (`cell.fiveqln`, manifest `plugin/herdr-plugin-v4.toml`), with the action pattern proven:
   `[[actions]]` whose `command` is an absolute bin path, invocable as
   `herdr plugin action invoke <action> --plugin cell.fiveqln` (verified against the herdr 0.8.2
   CLI) and from the cell UI. Human-only acts (`plant`, `attest`) carry TTY guards and stay;
   conduction commands (`/conduct`, `/word`, `/plan`, `/materialize`, `/descent`, `/config`,
   `/states`, `/trail`) need **no** TTY guard — they are machine-invokable free-corner gestures,
   exactly like the existing `begin`/`zoom` actions. The human's `/conduct` is S's `/conduct`: the
   identical bin, differing only in who invoked it.
2. **The conductor's binding — a pi extension.** Precedent: `@andrewjacop/pi-herdr` is installed
   via pi's `packages` in `~/.pi/agent/settings.json` and registers thin tool wrappers over the
   herdr CLI (`src/tools/orchestration.ts`: `herdr_send_prompt`, `herdr_start_agent`,
   `herdr_wait_agent`, `herdr_read_agent`, `herdr_delegate`, `herdr_list_agents`). A sibling
   package exposes the same command set as pi slash tools — each tool shells to the **same**
   `cellctl`. Then S's constitution's "My conduction" section (`desks/S/SYSTEM.md:48-50`) becomes
   one sentence: *conduction = call `/conduct`; I never re-derive the walk.* The desk's herdr
   tools remain available for what they are — the desk's own level-in spawns (pending decision D1)
   — but **never** for conducting the walk: a conductor composing `herdr_send_prompt` sequences is
   driving logic in the soft layer, which is exactly what the rule forbids.
3. **Safety when both callers exist.** The engine is already re-entrant-safe in the intended way:
   `turn_key` idempotency means a re-invocation re-arms from disk and observes, never re-prompts
   (`navigate.py` `already`/`observed`; `orchestrate.py run` `already-complete`). What it is not
   is concurrent-safe: the B0 `LedgerWriter` holds a single-writer lock per ledger file
   (`ledger/fractal_ledger.py:15` — "single-writer lock", K2; the cell's own lock file
   `state/gates.jsonl.lock` exists), but a simultaneous human `/conduct` and S `/conduct` on the
   same trail/work-dir is still an interleaving hazard (two processes each planning from the same
   trail). The CLI therefore takes one run lock on the cell's work dir (a single flock around the
   whole run) — mechanical, in the wrapper, not in the engine.
4. **The human's terminal.** For the human, `/conduct` runs and returns; the readable trail
   (`/trail`) and `/states` give the window; the ∞0′ return question comes back either to the
   human (S's seat is the human's at the membrane) or seeds the next cycle (D.8) when S calls it.

---

## 4. The firm rule, enforced — "no conduction logic in the soft layer" as a structural fact

The rule is enforceable because the codebase already separates the layers *physically*: the only
socket client on the box is inside the pinned engine modules (attested K1/C7 — "no `AF_UNIX` /
`sendall` / dialect code in the authored modules", R06 phase-card C7; the single chokepoint
`Instrument.call` with its frozen allowlists, `instrument.py:314`). The soft layer (TS tools, bash
bins, markdown, JSON) *cannot* currently reach a desk except by shelling to the herdr CLI or by
importing the engine. Enforcement therefore has four legs, each with an existing precedent:

1. **Capability scan (the soft layer cannot drive).** A mechanical scan over `desks/`,
   `plugin/bin`, `.pi/` configs, and any extension packages: forbidden tokens = herdr **write
   verbs** in the soft layer's reach — `herdr_send_prompt`, `herdr agent prompt`, `agent.prompt`,
   `pane.wait_for_output`, `send-keys`/`send_text`/`send_input`, socket-client code, subprocess to
   `herdr` with a prompt/wait verb. Precedents: the attested invariant scans ("no
   `send_text`/`send_input`/`send_keys` anywhere", R06 phase-card C7) and
   `corruption.scan_engine_sources` (the AST sixth-code scan). Result must be *zero*, except for
   the declared allowlist of human-TTY acts (`cell-plant`/`cell-attest`, which write no desk).
2. **Entry-point census (the soft layer can only point).** Every executable in the soft layer is
   a declared member of the seam manifest — an extension of the existing declared-surface
   practice (`ORCHESTRATION_SURFACE`, `RUN_SURFACE` in the `surface_contract.py` files). An
   undeclared bin, an undeclared tool, an undeclared import of the engine = FAIL. Symmetrically:
   the engine seam functions are callable **only** through the CLI — the census checks that no
   soft-layer file imports the pinned modules directly.
3. **Config-only soft content.** Every file the engine reads from the soft layer validates
   against a declared schema; unknown fields = INCONCLUSIVE refuse — the attested
   `softconfig.load_soft_config` behavior (bridge C4), extended to any new data the integration
   introduces (scenario files already refuse unknown fields, `word.py`). The soft layer's only
   contributions to a conducted run are data: constitutions, settings, skills, tool-surface
   declarations, scenarios, soft.json — all of which the engine **reads**, through its attested
   read paths (`softconfig`, `materialize.read_materialized`).
4. **Runtime sender audit (the proof, not the promise).** Because every wire write already
   crosses the single chokepoint `Instrument.call`, a live run can record its sender provenance:
   the verification asserts that in a full `/conduct` trail, every `agent.prompt` originated from
   the engine's `_live_turn` / `_do_turn` path (the chokepoint is the only caller), and that the
   boot line's `live_socket` (`orchestrate.py:585`) matches the resolved socket. Combined with
   the run lock (§3.3), this makes a soft-layer drive not just a violation but an
   *unrecordable* one — its prompts would appear in no ledger/trail under no turn_key.

**The verification check, concretely** — a `verify-integration.sh` in the pattern of the bridge's
`verify-live.sh` (`rounds/bridge/verify-live.sh`, which already re-checks pins and the read-only
live resolution on the box):

1. sha-pins: all engine files match the attested pins (import of the R06 `surface_contract`);
   `state/gates.jsonl` still his plant, byte-for-byte.
2. Legs 1–3 above (capability scan, census, config-schema validation) — zero findings.
3. **Plan-equivalence dry run:** `/conduct --plan-only` over a pinned scenario (a `null`/dry
   world) must produce byte-identical plan output to calling `word.decode_scenario` +
   `navigate.plan_walk` directly — proving the wrapper adds nothing (the diff-ability lens,
   applied to the seam itself).
4. The live gate (W4): one real `/conduct`; then the sender audit (leg 4) over its trail, and
   the `run-end` dependency audit PASS.

That is the structural fact: **the soft layer is scanned to contain no driving capability, its
executables are a closed declared set, its content is schema-checked data, and every prompt that
ever reaches a desk is provably the engine's.**

---

## 5. Ordering, hard seams, and what is genuinely open

### Dependency order (mechanically determined)

- **W0 — Locate or plant the acceptance record.** `RECORD-live-descent-2026-08-30.md` is cited in
  the brief and absent from the tree; the on-disk evidence is `nodes/_/*.level1.md` /
  `*.child.md` and the child agents in `~/.config/herdr/session.json`. The project's acceptance
  criterion — "the descent S improvised, now executed by the engine" — needs that record (or
  Amihai's re-statement of it) as its spec. Nothing else blocks on it, but nothing can *verify*
  without it.
- **W1 — The seam CLI** (thin bindings over the attested functions, §1) + the **live cell spec**
  (one spec.json: scenario dir, ledger, trail, socket resolution, materialize dirs, soft.json
  location, realistic timeouts-as-data).
- **W2 — The enforcement suite** (`verify-integration.sh`, legs 1–3) — built early, run from day
  one, so the rule is enforced *while* the soft layer changes, not audited after.
- **W3 — The desk constitution upgrade** (soft mode, S first): each live desk's
  `SYSTEM.md`/`AGENTS.md` learns its §3.6 surface shape and fence discipline, aligned with the
  P4b bundle content the engine renders; the materialized-cell ↔ live-desk schema decision
  (bridge gap #4); the first real `~/.config/herdr/soft.json` (emphasis/voice/model/budget —
  H-BRIDGE-2's provisional location, now written by the constitution).
- **W4 — The live acceptance gate:** the first real `/conduct` over the five desks — the deferred
  paid turn (H-BRIDGE-1 / H-ORCH-1), lifted by Amihai's order alone. This is where reality
  diverges from fixture fiction and where the numbers in the live spec get corrected.
- **W5 — The bindings:** herdr plugin actions (human) + the pi extension package (conductor),
  both onto the W1 CLI; S's constitution re-pointed from improvised conduction to `/conduct`.
- **W6 — Descent through the engine:** B3 zoom + materialized child cells + the spawn-ownership
  decision (D1) implemented; re-run of the 2026-08-30 descent as the acceptance, compared against
  the W0 record.
- **W7 — Live charges from the first measurements** (a data update to `COST_MODEL["charges"]
  ["live"]` via soft.json — closes H-B4-2's stand-ins).
- **W8 — Verification + attestation of the integration round** under the standing discipline
  (builder ≠ verifier, prediction cards, evidence record).

### The hard seams (where the fixture world and the live world actually differ)

- **Seam A — the first prompt→fence→read against a live Pi pane.** Everything about the dialect
  is attested against fixture servers speaking the dialect; nothing against a real Pi in a TUI
  pane. Failure modes to hunt in W4: the `⟦END …⟧` fence not appearing in visible output (Pi's
  progress UI), truncation, ANSI, and real thinking latency vs. the 5 s default (`orchestrate.py:170`).
- **Seam B — the surface contract vs. the live constitutions.** The engine refuses answers
  without a parseable §3.6 surface; no live desk constitution mentions one. If W3 is wrong or
  skipped, every live turn holds `no-surface-announced` and the run is INCONCLUSIVE — the engine
  will *prove* the soft layer wrong rather than guess. That is the intended behavior, and it
  makes W3 the critical path.
- **Seam C — the engine structurally forbids part of what the improvised descent did.** The
  centre guard refuses any non-seed S visit before any byte (`navigate.py:561-577`; K4). The
  observed descent spawned an **s-child** (S one level down). A word whose visits include S at
  index > 0 cannot be conducted by the engine as written — the improvised descent crossed a line
  the engine encodes as structure. Either the acceptance word omits child-S (four children), or
  the guard policy is revisited — and the guard is attested, imported, "never re-authored"
  (K4), so revisiting it is a firmware commission, not this project.
- **Seam D — two channels to the same agents.** B2's raw socket (`agent.prompt`) and the
  pi-herdr tools reach the same live panes. Without the ownership rule of §3.2, a conducted run
  and a desk's own descent can double-drive a pane. The run lock + sender audit contain it; the
  ownership rule must be written into the constitutions.
- **Seam E — fixture-scaled cost/time parameters.** Live charges are declared mirrors
  (`cost.py:143-146`); live timeouts are 5 s defaults. Both are data; both are wrong for live;
  both get corrected only by the first real runs (W4 → W7).
- **Seam F — the schema reconciliation** (materializer cells vs. real Pi settings/boot shape,
  bridge gap #4). Small mechanically; it is where the soft layer's shape is settled, so it needs
  Amihai's touch (the constitution is S first by standing decision).

### Genuinely open — needs Amihai (nothing else on this list is)

1. **D1 — Child spawn ownership (Seam C/D):** engine-owned (a new attested firmware write —
   separate round, touches the frozen `WRITE_METHODS`) vs. desk-executed (engine declares, desk
   spawns via its herdr tools — the `activate` pattern). This decides whether the engine ever
   holds `herdr_start_agent`-equivalent authority.
2. **D2 — The acceptance word:** what exactly the first `/conduct` runs (the 2026-08-30 descent
   word, a plain SGQPV cycle, or a new word) — including whether child-S is part of the
   acceptance (Seam C says the engine will refuse it).
3. **D3 — The missing record:** where `RECORD-live-descent-2026-08-30.md` lives, or whether the
   nodes/session evidence on disk is the acceptance record.
4. **D4 — Command names and the round's name/slot** (candidates in §1; every phase card defers
   naming to him).
5. **D5 — The constitution's shape (Seam F):** adopt the materializer's emitted cell format as
   the live desk format, or keep `boot.sh` + `AGENTS.md` and teach surface emission within it.
   Doctrine-adjacent; S first.
6. **D6 — The first paid turn:** H-BRIDGE-1's deferral is lifted only by his order (W4), and he
   certifies the live spec's hold/poll/timeout numbers after the first runs.
7. **D7 — Human UX of `/conduct`:** synchronous with a returned result vs. backgrounded with the
   trail as the surface (the engine supports both: cold-restart + `/trail`).
8. **D8 — What remains of S's improvised tooling** (`desks/S/.pi/prompts/guide.md` §5 spawn
   notes): retire, or keep as the desk-executed descent capability pending D1.

Everything else in §5's order is mechanically determined by the attested surfaces and needs no
decision — only execution.

---

## 6. Out of scope (to keep the project bounded)

- **No new firmware logic.** Any engine change — the agent-start write (D1-i), a centre-guard
  revisit (Seam C), a softconfig schema change — is a separate commissioned round with its own
  builder/verifier and attestation, not part of this integration. This project *binds*; it never
  re-authors (the standing D14 loyalty rule).
- **No touch to the sealed codex (ASIC), no new L1 symbol, no new decoding operation, no sixth
  corruption code** — the D14 jacket governs.
- **No machine attestation path:** `cell-attest` stays human-TTY; the engine never writes
  `state: "attested"`, never a non-null `attestation_ref` (K3, H-ORCH-4).
- **No podium writes, no plant automation** — the centre guard and the TTY guards stand.
- **No changes to B0's record format, B2's dialect bytes, or the P4a discipline** — the engine
  is imported under sha pins and stays byte-identical.
- **No new desks beyond the five, no multi-cell arrangements, no swarm, no "two modes"** — those
  are later soft-mode phases; this project delivers *one* cell driven by its engine.
- **No redesign of the scenario schema or the soft-config schema** (both provisional-but-attested;
  changes there are separate small commissions, H-ORCH-2 / H-BRIDGE-2).
- **No changes to the pi-herdr package itself** — it is consumed as-is (a sibling extension wraps
  `cellctl`; pi-herdr is untouched).
- **No LLM in the loop inside the engine** (K1 holds), and **no GUI/dashboard** beyond the
  existing podium and the `/states`/`/trail` text surfaces.

---

## Attestation needed

The scope above is K: structure, citations, and candidate requirements. The one question whose
answer opens the build:

> **Does this scope match the direction — the seam is the slash commands, the soft layer only
> points at the engine — and is the first real `/conduct` (the paid turn deferred by H-BRIDGE-1 /
> H-ORCH-1) authorized under this project, or does the engine stay harness-tested until the
> constitution (S first) is re-shaped?**

(No trail event was appended to the scoped-memory field for this consultation — a trail event is
appended only on an explicit human signal, per the skill; the field's `fractal-herdr` scope
currently reads empty.)
