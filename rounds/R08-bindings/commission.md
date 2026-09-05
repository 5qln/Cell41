# COMMISSION — R08 · the bindings (wire the soft agents to the attested seam)

**Working handle:** "bindings." **The phase name and slot are Amihai's to name** — this document uses
the working handle `bindings` only until he names it (SCOPE D4).

**Author:** dsh (`deepseek-v4-pro`, ONE generation). **Verifier:** Hermes profile `herdr`, separately,
against a pack written before it judges anything. `builder ≠ verifier`.

**Workspace:** `/home/deploy/the-cell/rounds/R08-bindings/` — write **only** inside `./authored/`.
A hash fence outside `authored/` is checked before and after.

**§1.10 of the Codex governs every conflict: where a document diverges from `5qln.com`, the source is
authoritative** — including this commission. The bindings **bind** the attested seam; they never
re-author it. The scope this round continues is
`docs/fractal-herdr/SCOPE-integration-engine-to-live-cell.md` (staged at
`./sources/SCOPE-integration-engine-to-live-cell.md`); where this commission and the SCOPE differ, the
SCOPE's citations to the attested files win, because they were read from disk.

---

## 0. His words and the standing decisions that bind this round

The build so far (all attested and closed): **B0 → B4 · P4a · P4b · B3 · the Grammar · the bridge ·
R06 Orchestration · R07 integration (the seam — `cellctl` + the enforcement suite, canon `992b775`)**.
R07 delivered the **seam**: a thin CLI, one subcommand per engine module, one engine call each. What it
did **not** deliver is the **bindings** — the two callers' surface onto that seam. This round builds
those bindings. It is **not** new engine logic, and it does **not** re-build `cellctl`.

**The governing line (SCOPE §0, verbatim):**

> "the soft layer must never contain driving logic — it only points at the engine. Slash commands are
> the seam. One surface, two callers: the human types `/conduct`, or the conductor S calls the same
> command."

**Amihai's instruction (2026-08-31, verbatim substance):**

> "yes i approve but i want dsh to participate in the design, after all swarm orchestration, and
> fractal loops are highly innovative and we want our lego approach to serve us as we use the system
> and constantly fine tune it."

Consequence, made mechanical: **this commission fixes the CONSTRAINTS (the attested seam, the criteria,
the prohibitions, the LEGO requirement C8); dsh AUTHORS the design** — the module boundaries, the
extension-package contract, the recipe/brick format, and the phase card's predictions. dsh's design is
judged against the criteria and the codex, **never against a pre-ordained shape**. If dsh's design
differs from any candidate named here and still satisfies the criteria, the design wins.

**The boundary (load-bearing): dsh designs the MECHANICS, never the DOCTRINE.** The codex (ASIC), gate
semantics, the corruption codes (L1–L4, V∅), and the ∞0 rule are inherited constraints, never
re-designed. Innovation is channeled to the binding layer, the LEGO brick format, and the
composability of the soft surface — and barred from the doctrine.

**Standing decisions (unchanged):** D12 — success in a phase = contextual DECODE + COMPILE of output
xyzab. D14 — every decode/compile loyal to `5qln.com/codex`. §1.6 — no V without ∞0′. §5.5 — TENTATIVE
is temporal, never epistemic. The conductor is S (§4.8). The human's gate act is a TTY act, never
carried by any channel. The engine's only wire-write is the attested B2 `Instrument.call` chokepoint
(`agent.prompt`); that single chokepoint stays the single chokepoint.

---

## 1. What to build — one paragraph, no doctrine

`cellctl` (R07) already turns every engine module into a callable command. This round gives the **two
callers** a way to reach it, natively, without improvising. (1) The **conductor** — a pi extension
package that registers the `cellctl` subcommands as slash tools, so S's conduction becomes one line:
*conduction = call `/conduct`; I never re-derive the walk.* (2) The **human** — conduction actions in
the herdr plugin manifest, each `command` → `cellctl`, so the human can fire `/conduct` from the cell
UI. (3) The **reconciliation** — re-point the soft layer's three remaining drive/bypass sites (the
plugin's own socket client, the desks' `herdr_start_agent` guide line, `cell-attest`'s unpinned ledger
import) so `verify-integration.sh` reads genuinely clean. (4) The **podium re-point** — the podium
renders `state/trail.jsonl` (the formation trail) instead of `question.md`, becoming the smart ledger.
The LEGO requirement (C8) governs all four: the bindings are a baseplate of independent studs, and the
orchestration *method* stays data the engine reads — never code in the binding.

---

## 2. Acceptance criteria — quoted verbatim

### C1 — the bindings are thin: one tool/action = one `cellctl` call
Each pi slash tool and each plugin action shells out to **exactly one** `cellctl` subcommand. The new
code contains **no socket code, no prompt assembly, no record-writing, no ledger/trail logic, no
engine import** — `cellctl` (R07, attested) already carries all of that; the binding adds nothing on
top (C3 proves it).

### C2 — the write side is never exposed
No tool/action wraps `agent.prompt` or any write verb. The read side (`/states`) is the only
desk-facing surface; an absent socket reads `{"status":"absent"}` honestly, never a fixture stand-in.

### C3 — the binding adds nothing (equivalence on top of R07's plan-equivalence)
`/conduct --plan-only` through the new tool/action is **byte-identical** to `cellctl conduct --plan-only`
directly (which R07 already proved byte-identical to `word.decode_scenario` + `navigate.plan_walk`).
The binding is a transparent pass-through; it re-serializes nothing.

### C4 — the enforcement suite reads clean (the three findings re-pointed, never allowlisted)
`verify-integration.sh` over the live cell returns **zero** findings. The three pre-integration findings
are re-pointed to the seam — not commented out, not allowlisted away, not tuned down: (i) the plugin's
own socket client is reduced to its declared read-only surface or routed through `cellctl states`;
(ii) the desks' `herdr_start_agent` guide line is moved under an explicit *deferred — D1 un-decided*
fence, and conduction is re-pointed to `/conduct`; (iii) `cell-attest`'s ledger write goes through the
declared seam path, never a direct unpinned `fractal_ledger` import.

### C5 — the run lock is honoured, never bypassed
The flock (R07, in `cellctl`) around the cell work dir is the single run lock. The bindings invoke
`cellctl` directly, so they inherit the lock; they add no second path around it. A concurrent human/S
`/conduct` on one trail blocks rather than interleaves.

### C6 — fail-closed, INCONCLUSIVE never clean
Absent `cellctl` / absent socket / drifted pin / malformed surface / `blocked` desk all read
INCONCLUSIVE with a reason — never a substituted value, never a clean verdict, never a fixture
stand-in. A `blocked` desk routes to a human, never retried blind.

### C7 — the pinned seams stay the import boundary
The bindings import **nothing** from the engine directly. Their only reach is a subprocess to `cellctl`
(which is the sole importer of the pinned engine modules). No soft-layer file may import a pinned
module directly; the extension package and the plugin actions contain no `AF_UNIX`/`sendall`/dialect
code.

### C8 — the LEGO requirement (his directive, made a criterion)
The binding layer is a **baseplate of independent studs, never a fixed pipeline**:
1. each of the 13 commands is exposed as an **independent, composable** stud — no orchestration
   *sequence* is hard-coded in the binding;
2. the orchestration **method** (which commands, in what order, under what soft config) is **data the
   engine reads** — never code in the binding — so a new method = a new soft brick snapped on, with
   **zero re-authoring** of the seam or the firmware;
3. a method that closes honestly and returns a live ∞0′ must be **expressible as a new brick** (D8,
   output-is-input) — the binding must not preclude the learning loop feeding winners back into the
   soft layer;
4. the **swarm** (one firmware, many soft configs) is reachable through this layer with **zero firmware
   change** — the binding must not hard-code one orchestration pattern or one cell.

### Claims (K1–K5)

- **K1 — stdlib, deterministic, no LLM.** The extension and the actions add no network, no LLM, no
  wall-clock in logic; their only subprocess is `cellctl`. The only socket client on the box remains
  the pinned `Instrument`.
- **K2 — byte-exact, never normalised.** The bindings forward bytes untouched; no `⋂→∩`, no `′→'`, no
  spacing collapse.
- **K3 — the click is never a machine verdict.** No authenticity verdict; HC-1/HC-2 stay INCONCLUSIVE;
  nothing claims arrival at ∞0.
- **K4 — the B2 guards hold.** The centre guard refuses S/podium before any byte; the write allowlist
  stays frozen (no `herdr_start_agent`-equivalent authority is added this round — D1 is deferred).
- **K5 — diff-ability.** The recipe/method is a **data file** the engine reads — one place to change,
  diff-able, versioned — never code in the binding.

### The six lenses (the verifier runs these; author so they pass, and so a blind spot reads
INCONCLUSIVE, never clean)

1. **Criterion match** — measure each criterion *as written*, not a neighbour of it.
2. **Invariant end-to-end** — the binding behaves identically across a whole run, not per call.
3. **Absence vs validity** — absent `cellctl` / absent socket / empty file must never read valid
   (sha256 of empty = `e3b0c44298fc…`).
4. **Encoding** — push `∞0′ → ‖` through every string field (tool args, action args, config, address);
   text-mode byte seeks break on it.
5. **Cold restart** — a *new* process re-arms from disk alone; a second `/conduct` honours the run lock.
6. **Blind tool** — unavailable live socket / unconstituted desk reports INCONCLUSIVE, never clean,
   never a fixture stand-in.

---

## 3. Verified-facts block (do not re-probe — these were executed)

- **The seam exists and is attested (R07, canon `992b775`).** `cellctl` at
  `rounds/R07-integration/authored/cellctl` — 13 subcommands (`word plan materialize conduct walk config
  cost states descent decode compile check trail`), one engine call each. Exit 0 = declared success; 1 =
  any other; INCONCLUSIVE never reads clean. Its `--help` was re-read 2026-08-31.
- **The enforcement suite exists and its live verdict is FAIL — and it names the three missing links**
  (re-run 2026-08-31, file:line, never tuned away — H-INT-5):
  1. `plugin/bin/_cell_api.py` — `import socket`, `socket.socket(AF_UNIX)`, `sendall` (a second wire).
  2. `desks/{S,G,Q,P,V}/.pi/prompts/guide.md:52` — "I must use `herdr_start_agent`" (spawn authority in
     the soft layer).
  3. `cell-attest` — imports `fractal_ledger` directly (unpinned ledger write).
- **The plugin manifest has no conduction actions.** `plugin/herdr-plugin-v4.toml` declares only
  `begin · plant · attest · zoom` (verified 2026-08-31). The human has no cell-UI path to `cellctl`.
- **The conductor has no slash tool to reach `cellctl`.** S's `desks/S/.pi/prompts/guide.md` describes
  conduction by thought; nothing registers a `/conduct` tool. This is the improvising to eliminate.
- **The native surface (held manual, pi v0.84 × herdr v0.8.2):** pi extensions register tools from a TS
  package under `.pi/extensions/` / `~/.pi/agent/extensions/` (precedent `@andrewjacop/pi-herdr`: tools
  `herdr_delegate · herdr_start_agent · herdr_send_prompt · herdr_wait_agent · herdr_read_agent ·
  herdr_list_agents · herdr_stop_agent · herdr_send_keys`; config env-only `HERDR_BIN`, …). Herdr plugin
  actions: `[[actions]] id/title/command/contexts`. Herdr GUI: `~/.config/herdr/config.toml`
  (`[theme]` 19 tokens · `[ui]` · `[ui.toast]` · `[keys]` with `[[keys.command]] type="plugin_action"` ·
  `$tokens` via `herdr pane report-metadata`). Staged at `./sources/` as the manual text.
- **Live socket is UP** (herdr 0.8.2, protocol 20). Five Pi desks constituted (`desks/{S,G,Q,P,V}/`),
  model `deepseek-v4-pro`. **The authoring pass uses fixtures only, no live box** — no real
  `agent.prompt` is sent this round (H-R08-1).
- **The engine functions `cellctl` already binds** are the attested R06/bridge/B3/Grammar shapes — this
  round does not re-derive them; `cellctl` is the only interface it touches.

---

## 4. The interface to the attested rounds (predecessors — import, never re-author)

The immediate predecessor is **R07-integration**, staged under `./predecessors/r07-integration/`:
`cellctl` (the CLI to bind), `enforce.py` + `verify-integration.sh` (the suite whose findings this round
reconciles), `surface_contract.py` (the pins), `spec.json` (the live spec). **The bindings do not import
these as modules — they shell to `cellctl`** (C7). They read `enforce.py`/`verify-integration.sh`/the
desk `guide.md` files only to re-point them.

The deeper engine modules (b2, p4a, p4b, b3, b4, bridge, r06-orchestration) remain on the box at their
own `rounds/*/authored/` paths, already pinned and imported by `cellctl` via R06's `surface_contract`.
**This round touches none of them** (C6, prohibitions).

---

## 5. Holds — declare, never guess

- **H-R08-1 — no live `agent.prompt` is sent this round.** The bindings are tested against a fixture
  harness only. The first real paid turn is Amihai's alone to authorize (SCOPE D6, W4) — later, not by
  this authoring run.
- **H-R08-2 — command/tool names and the round's name/slot are provisional** (SCOPE D4). The working
  handle is `bindings`; `pi-cell` is a candidate package name. His to name.
- **H-R08-3 — child-spawn ownership is deferred** (SCOPE D1, Seam C/D). The extension adds **no**
  `herdr_start_agent`-equivalent authority; the engine's `WRITE_METHODS` stay frozen. The desks' spawn
  line is re-fenced under *deferred — D1*, never presented as the walk.
- **H-R08-4 — the `pi-herdr` package is consumed as-is, untouched.** The new package is a *sibling*
  that wraps `cellctl`; it does not fork, patch, or depend on `pi-herdr`'s internals.
- **H-R08-5 — the constitution §3.6 surface (W3) is soft-mode, not this round.** G/Q/P/V still do not
  speak their surface (S is wired). The bindings must report `no-surface-announced`/`surface-malformed`
  honestly when the engine holds — never paper over it.
- **H-R08-6 — the look-and-feel is a separate, later round.** This round re-points the podium's
  *content* to the trail (`state/trail.jsonl`) — it does **not** build the theme/sidebar/toasts skin
  (that is the interface round, mapped from the held manual's §07).

---

## 6. Prohibitions

No write path to the podium (`pane.send_text/input/keys` at the centre). No git, no attestation, no
claim that anything ran. No gate semantics re-implemented outside `fractal-engine`. No re-implementation
of `cellctl`, the herdr socket dialect, the prompt assembly, the record-writing, the D.12 checks, the
desk grammar, the descent, the bridge's live mode, or R06. **No write verb exposed as a tool/action
(C2). No new socket/client code — the pinned `Instrument` is the only client (K1).** No new engine
write (`WRITE_METHODS` frozen, H-R08-3). No modification of `pi-herdr` (H-R08-4). **No hard-coded
orchestration sequence in the binding (C8).** No hard-coded §2-emphasis/voice/model/budget literal. No
sixth corruption code, no new L1 symbol, no new decoding operation, no renamed symbol. No byte
normalisation. No authenticity verdict. No tentative node promoted or consumed. The machine never
resolves a hold. Nothing described as attested/decided/verified that this commission does not mark so.

---

## 7. Deliverables — under `./authored/` (layout yours to design; content is what is checked)

- **`pi-cell/` — the conductor binding** (TS extension package): registers the 13 `cellctl` subcommands
  as pi slash tools, each a thin shell to `cellctl` (C1, C3, C7). Env-only config: `CELLCTL_BIN`
  (default `/home/deploy/the-cell/rounds/R07-integration/authored/cellctl`), `HERDR_BIN`. The `conduct`
  tool is the load-bearing one. Registration contract per the held manual §05. The layout/entry points
  are yours to design (C8 governs: composable studs, no fixed sequence).
- **The human binding** — the conduction plugin actions (`conduct · word · plan · materialize · states ·
  trail · descent · config`) as a manifest patch or a new manifest section, each `command` → `cellctl`,
  no TTY guard (free gestures); `plant`/`attest` unchanged.
- **The enforcement reconciliation** — the re-pointed `desks/*/.pi/prompts/guide.md` (conduction → `/conduct`;
  spawn → *deferred — D1*), the reduced `_cell_api.py` (read-only `snapshot`/`schema` only), and the
  re-pointed `cell-attest`. Acceptance: `verify-integration.sh` reads **zero** findings, honestly.
- **The podium re-point** — a small read-only renderer over `state/trail.jsonl` (one event per line,
  human + desk interleaved, `read_trail`'s shape) + the manifest pane re-point from `question.md` to it.
- **`selftest.py`** — the author's own suite (a hypothesis, not a result).
- **`phase-card.md`** — predictions only (never results) + the D14 divergence log + the design
  rationale (why the brick format / module boundaries look the way they do, and how C8 is satisfied).
- **`fixtures/`** — at least: a fake `cellctl` (deterministic, with an absent case and a malformed
  case) · a fixture desk harness with an unconstituted-desk `agent_not_found` and an absent-socket case ·
  enforcement fixtures with the three pre-integration findings, proving the suite flips to clean only
  after the re-pointing · a cold-restart fixture (second process, run-lock honoured) · a byte-round-trip
  fixture pushing `∞0′ → ‖` through the tool/action args.

---

## 8. Budget

**ONE authoring generation.** No exploratory chat. Artifact + phase card in, out. The design is yours;
the criteria and the codex are the judge.
