# PHASE CARD — the bridge · the live desk adapter + the runtime config-read (working handle)

**Round:** the bridge — the last firmware round (the working handle; the phase name and slot are
**Amihai's to name**). It closes the gap candidate #2 of the roadmap: the conductor joins the live
herdr socket, and reads the soft layer at runtime.
**Author:** dsh (`deepseek-v4-pro`, one generation). **Verifier:** Hermes profile `herdr`,
separately, against a pack written before it judges anything. `builder ≠ verifier`.
**Governing sources:** the commission (`./commission.md`), the Codex, Appendix D, PRD,
REQUIREMENTS (held at `../sources/`). **Codex §1.10 governs every conflict — the source wins.**

**Every verdict in this card is a PREDICTION.** Nothing here reports that anything ran, passed, or
verified anything. A separate verifier executes the artifact and writes the only record that
counts; it recomputes every verdict with its own implementation, and any divergence — in either
direction — is a FAIL. The committed fixture pins under `fixtures/*/expected/` are declared input
bytes for that recomputation, not a report of an execution.

---

## 0. The bridge, in one paragraph (no doctrine)

The bridge extends the attested B4 unattended run in exactly two ways, importing every predecessor
(never re-implementing). **(1) A live `desk` mode:** `cost.DeskAdapter` gains a third mode
`"live"` beside `sub-process` and `re-prompted`; `open_turn` returns a `TurnContext` on the
resolved live herdr socket (`HERDR_SOCKET_PATH`, else `~/.config/herdr/herdr.sock`) with process
`None` — no fixture `desk_server.py` is ever spawned — and the conductor's existing
`Instrument(socket_path=context.socket_path)` path then speaks the real herdr dialect through the
attested B2 adapter: resolve the desk by pane label on every turn, `agent.prompt` to the resolved
pane, the §4.5 fenced read (`pane.wait_for_output` to `⟦END …⟧`). An unreachable socket holds as
outage; a desk resolving to a pane with no agent holds as blocked `agent_not_found` — never a
fixture stand-in, never a guessed answer, never clean; the centre guard refuses S/podium before
any byte. **(2) A runtime config-read:** a new module `softconfig.py` reads, at runtime, each
desk's codex §2 emphasis, voice, model, and the cycle budget (charges + default mode) from a
soft-layer config file; the conductor's prompt, budget and mode-default paths read through it, so
the hard-coded `DESK_FUNCTION_SPECS` / `COST_MODEL` literals become the DECLARED DEFAULTS, never
the conductor's source of truth. Absent soft config → the declared defaults (B4's exact
bytes/values — the fixture run is byte-identical, nothing attested is un-done). Empty, malformed
or partial soft config → INCONCLUSIVE with the reason — the run refuses to boot, never a silently
substituted value.

## 1. Binding — the names this round ships

| binding | real name | where |
|---|---|---|
| `cost_module` | `cost` | `cost.py` — `COST_MODEL` (now carrying a `"live"` mode entry + live charges), `DeskAdapter` (third mode `"live"`), `TurnContext`, `live_socket_path` |
| `softconfig_module` | `softconfig` | `softconfig.py` — `SOFT_DEFAULTS`, `load_soft_config`, `desk_emphasis`, `desk_voice`, `desk_model`, `budget_of`, `default_mode`, `DECLARED_MODEL` |
| `conductor_module` | `run` | `run.py` — `Conductor` (live mode + runtime config-read), `next_action`, `audit_payload_chains`, `seed_ref` |
| `surface_contract_module` | `surface_contract` | `surface_contract.py` — sha-pins the predecessors by path (now incl. B4's trail/desk/desk_server/build **and** this round's softconfig); declares the bridge surface (`RUN_SURFACE["live_mode"]`, `["soft_config"]`) |
| `selftest_module` | `selftest` | `selftest.py` — the author's suite, a hypothesis never a result |
| `fixture_live_server` | `live_server` | `fixtures/live_server.py` — a server speaking the **real herdr dialect** on its own socket (B2 `FakeHerdrServer` shape), modelled on the probed live pane state, with the `agent_not_found` case and the absent-socket case |
| `fixtures` | `fixtures/` | `live_run/` (the live-mode run, byte-pinned) · `restart/` (the cold-restart harness + soft layer, byte-pinned) · `soft_config/` (the override + the four fail-closed files) · `build.py` (the fixture builder) |

The functions are the real surface; the names are stable and documented here. The verifier's pack
may bind different names — the functions are what is checked.

## 2. Criteria and claims, by id — with PREDICTIONS

**C1 — the live desk mode.** Prediction: `cost.DeskAdapter(spec, socket_dir, mode="live")`
accepts the third mode; `open_turn` returns `TurnContext(live_socket_path(override), None)` —
override > `HERDR_SOCKET_PATH` > `~/.config/herdr/herdr.sock`, resolved fresh per turn — process
`None`, no spawn of any kind (the live branch of `open_turn` contains no `_spawn`, no `Popen`, no
`desk_server`). The conductor's unchanged `Instrument(socket_path=context.socket_path)` path then
speaks the real dialect: the fixture live box receives `pane.list` (label resolution — the
unlabelled `w7:p1` pane is never indexed), `pane.get` (the centre guard's target check and the
§4.3 live-label assertion), `agent.prompt` to the RESOLVED pane id (`w8:p3` for G, never a
remembered id), then `pane.wait_for_output`, whose fenced read carries the `⟦END <turn_key>⟧`
marker. The whole pinned live run completes (constituted-all variant) or stalls (live-box-shaped
variant) through exactly this path. The centre guard raises `CentreWriteError` for S/podium —
before any byte, before any connection (the server records zero connections for that attempt),
and an unresolvable target (`None`) is refused too (K4, T-R3-02).

**C2 — live mode fails closed, never into a fixture (lens 6).** Prediction: an absent/unreachable
live socket → every live turn holds `outage` with detail `SocketTransportError` and the run ends
`stalled` with zero `fenced:` records (no answer was ever read, so nothing was ever valid); a desk
resolving to a pane with no agent → `blocked` hold with detail `agent_not_found` (the B2
`AgentNotFoundError` path — the fixture server answered the structured error, and composed no
stand-in bytes for any pane but the constituted one). Neither case spawns `desk_server.py`,
neither returns a fake answer, neither reads clean, and the pinned box-run ledger holds exactly
two such blocked holds, still `held-pending` at the end.

**C3 — the runtime config-read.** Prediction: `softconfig.load_soft_config(path)` resolves
spec-path > `SOFT_CONFIG_PATH` > `~/.config/herdr/soft.json` and reads the per-desk `emphasis` /
`voice` / `model` and the `budget` (`default_mode` + per-mode `charges`); the conductor's
`_prompt_text` renders `ATTENTION MODE — <voice>` + the emphasis lines through
`softconfig.desk_voice` / `desk_emphasis` (with the model line rendering in live mode and whenever
a soft layer is present — so the model read is observable in the prompt path), the budget path
charges through `softconfig.budget_of` (spend recomputed from the ledger with the soft charges),
and the mode default through `softconfig.default_mode`. The hard-coded `DESK_FUNCTION_SPECS` /
`COST_MODEL` literals are no longer the conductor's source of truth: `run.py`'s control flow
carries none of them (they live in `softconfig.SOFT_DEFAULTS` + `cost.COST_MODEL` + the soft
file). A complete override changes the runtime read end-to-end: the prompt bytes change (the
soft emphasis/voice/model ride it verbatim), the run-end spend equals the soft charges, and —
because the desk answers never depended on the prompt — the LEDGER stays byte-identical to B4's
pins while the trail changes. A soft `default_mode` overrides the mode resolution (the restart
fixture resolves `"live"` from the soft layer with the spec's mode null).

**C4 — declared defaults, fail-closed (lens 3).** Prediction: absent soft config →
`{"status": "defaults", …}` and the conductor resolves B4's exact bytes/values — the three B4
fixture runs (main 20-cycle, hold, budget) under the bridge conductor reproduce B4's pinned
ledgers AND trails byte for byte, and the absent-config prompt equals B4's prompt byte for byte
(no model line ever existed there). Empty / not-UTF-8 / not-JSON / partial (a missing desk) /
wrong-typed / unknown-field soft configs → `{"status": "inconclusive", "reason": …}` — the empty
file's reason carries the sha256 of empty (`e3b0c44298fc…`), every reason names the exact field —
and the conductor REFUSES TO BOOT with a `BootError` carrying `INCONCLUSIVE` and the reason:
nothing runs, nothing is written, never a silently substituted value.

**C5 — import, never re-author (D14 loyalty).** Prediction: B0's ledger (via
`FRACTAL_LEDGER_DIR`, never copied), B2's `dialects/instrument/lens/walker/driver`, P4a's
`surface/conformance/step`, P4b's `block/grammar/arrangement` (+ its canonical contract), B3's
`descent` (+ its canonical contract), B4's `trail/desk/desk_server/build`, and this round's
`softconfig` are all loaded by path under sha pins; a drifted pin raises `ImportError` (never a
substitution); every pin's sha matches its file's bytes. No new decoding operation, no new L1
symbol, no sixth corruption code (`L1 L2 L3 L4 V∅` only), and no re-authored socket dialect
(`run.py`/`softconfig.py` contain no socket imports, no `sendall`, no `AF_UNIX`).

**C6 — nothing attested is un-done.** Prediction: the two fixture modes (`sub-process`,
`re-prompted`) behave exactly as B4 attested — the three pinned B4 runs reproduce byte-identically
under the bridge conductor, the dual-mode ledgers stay equal, the default mode is still
`re-prompted`, and the bridge is additive (a third mode + a read path; no attested code path
changed its bytes on the wire or in the records).

**C7 — cold restart from disk alone (lens 5).** Prediction: a NEW process re-arms the live mode +
config-read from disk alone: the restart harness spawns two fresh python processes over the same
ledger/trail/spec/soft files (the fixture live box stays up as the environment) and the final
ledger and trail equal the uninterrupted pins byte for byte, with the boot line's mode `"live"`
(resolved from the soft layer), the run-end spend equal to the soft live charges, and the needle
bytes riding the trail. A brand-new `Conductor` derives the same next action at every step of the
live run (never from RAM). In live mode the cycle-1 seed carries the previous V turn's
`fenced:sha256:<digest>` payload_ref as its source reference — re-derived from the ledger alone,
never regenerated, never guessed — and a live turn line rebuilt after a kill -9 carries the
digest only (D12: references, never content).

### Claims (K1–K5), predictively

- **K1 — stdlib, deterministic, no LLM.** `run.py`/`softconfig.py` carry no network/LLM imports,
  no wall-clock in logic; `cost.py` keeps only the attested subprocess spawn for the two fixture
  modes; the live socket is the only I/O, and it is the attested instrument's.
- **K2 — byte-exact enumerated forms.** The declared emphasis/voice bytes are the pinned B4
  folded-item bytes; the P4b `PHASE` registers flow byte-exact when configured (`⋂` stays
  `U+22C2`, never `∩`; `∞0′` never folded to `∞0'` — normalising is renaming an L1 symbol).
- **K3 — the click is never a machine verdict.** No `state: "attested"`, no non-null
  `attestation_ref`, no tentative flip anywhere in `run.py`/`cost.py`/`softconfig.py` — HC-1/HC-2
  stay INCONCLUSIVE by construction.
- **K4 — the B2 guards hold.** The centre guard refuses S/podium before any byte; an unresolvable
  write target is refused too (fail closed) — the imported `assert_not_centre`, never re-authored.
- **K5 — diff-ability.** The soft config is a data file (`.json`, one place to change), never
  code; the pane-label → desk map stays the imported config table (`DESK_LABELS`) — no code
  derives meaning from a displayed label.

### The six lenses, predictively

1. **Criterion match** — each criterion's done-when sentence is declared in
   `RUN_SURFACE["live_mode"]` / `["soft_config"]` with its citation, and each selftest names the
   criterion it measures.
2. **Invariant end-to-end** — the byte-pinned live runs (box + all + absent variants), the restart
   run and the three B4 runs are whole-run artifacts compared byte for byte, and the dependency
   audit is predicted to read PASS over each whole live ledger — never per-call readings.
3. **Absence vs validity** — absent socket → outage holds (no `fenced:` record); absent soft
   config → `defaults` (the declared fallback, never a "valid read"); absent agent →
   `agent_not_found`; empty file → `inconclusive` carrying `e3b0c44298fc…`; empty ledger audits
   INCONCLUSIVE; absent plant boots nothing.
4. **Encoding** — `∞0′ → ‖` rides the soft-config voice/emphasis fields into the prompt bytes,
   the fixture soft files carry the raw UTF-8 (no `\u` escapes), `softconfig.py` opens files
   binary-only (no text-mode byte seeks), and the pinned live/restart trails carry the needle
   verbatim.
5. **Cold restart** — the restart harness and the fixture-mode split both run the SECOND process
   as a fresh python rebuilding from disk alone, byte-identical to the uninterrupted pins; the
   derive-at-every-step test re-derives every next action from a brand-new Conductor.
6. **Blind tool** — an unavailable live socket or an unconstituted desk reports INCONCLUSIVE,
   never clean: the box run stalls with its holds, the absent-socket run holds outage, malformed
   configs refuse with the reason, and the read-only live-socket probe skips (INCONCLUSIVE) when
   the box is down.

## 3. D14 divergence log — everything this artifact adds beyond the source

Per Appendix D's own jacket: declared *derivative* · visibly separate from the decoding · adds
**no** L1 symbol, **no** decoding operation, **no** sixth corruption code · alters no invariant
line. **Summary: the bridge adds two interface layers ON the attested rounds — the live desk mode
(a third adapter mode + two new hold details on B4's hold surface) and the runtime config-read (a
data-file read path whose defaults are B4's exact bytes). The herdr dialect, the D.12 checks, the
desk grammar and the descent remain the imported ones; the only new record-level byte is the live
seed's source reference (the previous V turn's own fenced digest — a reference, never content).
One declared reading note: commission §5's table cites `PHASE[desk]["phase_gate"]+["decoding"]` /
`seat` as the emphasis/voice defaults, but C4/C6 pin the absent-config prompt byte-identical to
B4 — so the DECLARED DEFAULTS are B4's actual prompt bytes (the pinned `fixtures/desk.py`
function-specs + attention readings); the PHASE registers remain the enumerated provenance,
exposed through the imported grammar and flowing byte-exact whenever the soft layer configures
them (K2), which the constitution will write.**

| # | Addition | Anchor | Resolution |
|---|---|---|---|
| D-1 | The live desk mode: `COST_MODEL["modes"]["live"]` + live charges (declared stand-ins), `DeskAdapter.open_turn`'s live branch (`TurnContext(live_socket, None)`, no spawn), `live_socket_path()` (override > env > default), the conductor's `agent_not_found` → blocked hold (detail `agent_not_found`) and outage holds for an unreachable socket, the live seed source-reference rule (the previous V turn's fenced payload_ref — the live answer's bytes exist nowhere on disk, D12), and the digest-only live observe-repair line | Commission C1/C2, §3 facts; B2's `Instrument.prompt_desk` (imported, never re-authored); H-B4-2 carried | Additive interface on the attested adapter and conductor; no new dialect byte, no new decoding, no fixture spawn in live mode (fail closed) |
| D-2 | The runtime config-read: `softconfig.py` (the schema, the strict validation, the three statuses defaults/ok/inconclusive), `SOFT_DEFAULTS` (B4's exact bytes: the pinned folded-item specs + attention readings, `DECLARED_MODEL` = `kimi-k3` per D6 / PRD §7 note, `COST_MODEL` charges + default mode), and the conductor's prompt/budget/mode-default paths reading through it (the MODEL line renders in live mode and when a soft layer is present — the model never existed in B4's prompt) | Commission C3/C4, §5; B4's hard-coded tables (which become the declared defaults) | Data-file read path, deterministic and stdlib-only; malformed/partial → INCONCLUSIVE with the reason, the run refuses to boot — never a silently substituted value |
| D-3 | The fixture apparatus and the contract pins: `fixtures/live_server.py` (the real-dialect stand-in box: six panes modelled on the probed live state, `agent_not_found` for the unconstituted desks, `constituted=all` as declared fixture fiction), the byte-pinned `live_run`/`restart` fixtures + soft-config files, and the new sha pins (B4's `trail/desk/desk_server/build` + this round's `softconfig`) | H-BRIDGE-1; B2's FakeHerdrServer precedent; B4's fixture-fiction precedent | Test apparatus only; the live box is never written (the one live touch is a read-only probe that skips when the box is down) |

## 4. Holds — H-BRIDGE-1 … H-BRIDGE-4, each with the reading this round ships

* **H-BRIDGE-1 (no desk is constituted except G).** The live mode is tested two ways, both safe:
  (a) the fixture live server — the full `prompt_desk` path exercised deterministically, with the
  live-box-shaped variant (only G constituted; Q/V/P answer `agent_not_found`) and the
  constituted-all declared fiction (a whole cycle completes through the dialect); (b) the live
  socket, read-only (resolve desks by label, `pane.get`/`agent.get` — zero writes, skip
  INCONCLUSIVE when the box is down). A real `agent.prompt` to the G desk is a paid Pi turn,
  deferred to the constitution. The centre guard refuses S/podium on the live socket too.
* **H-BRIDGE-2 (the soft-config location + schema are provisional).** The bridge ships the read
  path with the declared default location `~/.config/herdr/soft.json` (`SOFT_CONFIG_PATH` and the
  spec's `soft_config` override it); the constitution (S first) writes the real soft files. The
  bridge authors no desk personality and no §2 content — it reads them.
* **H-BRIDGE-3 (the success shape stays inert — carried H-B4-3).** The run reads the desk's
  answer from the fenced read, never from `agent.prompt`'s success shape; the fixture live
  server's success shape is deliberately inert.
* **H-BRIDGE-4 (the human's gate act is untouched — carried H-B4-4).** No podium write, no
  `cell-attest` invocation, no typed word; attestation stays a TTY act, in every mode including
  live.

## 5. Assumptions and open flags (stated, not hidden)

1. The committed byte-pins were generated under the **canonical relative work paths**
   (`fixtures/<case>/work/…`, cwd = `authored/`): the trail lines carry the ledger path as
   observability, so regeneration under a different path string yields identical content with the
   path string (and the chained hashes) differing — the harnesses re-run under the same strings
   and compare byte for byte (B4's stated assumption, carried).
2. The fixture world writes the plant (attested) as the human's TTY stand-in — P4a's
   attest-provider precedent; the run itself never writes attested (assumption #4 of B3, carried).
3. The live charges (`COST_MODEL["charges"]["live"]`) mirror the re-prompted stand-ins — the live
   per-Pi measurement awaits a constituted desk (H-B4-2 carried); they are soft-config-overridable
   like every other charge.
4. The declared model is `kimi-k3` (D6: one model across the four desks; PRD §7 note — "the model
   is a block, swappable, never hardcoded in doctrine"); the constitution's soft files override it.
5. The live-mode observe-repair after a kill -9 rebuilds the turn line from the fenced digest
   alone (`decoded: {}`, `measured: None`) — the live answer's bytes were never retained (D12), so
   a rebuilt line never guesses content; the cold-restart fixture uses the clean max-actions
   split, where every line is written by exactly one process and the bytes stay identical.
6. The spec's `live_socket` is an additive caller-supplied override; absent it, the resolution is
   exactly C1's (`HERDR_SOCKET_PATH` → the declared default), and the conductor's own socket
   never touches the real box in any fixture run.
7. The verifier's pack may bind different names than §1; the functions are the real surface, the
   names are stable and documented here.
