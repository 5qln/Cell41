# PHASE CARD — integration · the seam (working handle)

**Round:** integration — the working handle; the phase name and slot are **Amihai's to name** (H-INT-2 /
D4). The integration is W1 + W2 of the SCOPE: a thin, logic-free command surface (`cellctl`) over the
attested engine functions, plus the enforcement suite that makes "no driving logic in the soft layer" a
mechanically-checkable fact.
**Author:** dsh (`deepseek-v4-pro`, ONE generation). **Verifier:** Hermes profile `herdr`, separately,
against a pack written before it judges anything. `builder ≠ verifier`.
**Governing sources:** the commission (`./commission.md`), the SCOPE
(`../sources/SCOPE-integration-engine-to-live-cell.md`), the Codex + Appendix D (held at `../sources/`).
**Codex §1.10 governs every conflict — the source wins**; where this commission and the SCOPE differ,
the SCOPE's citations to the attested files win.

**Every verdict in this card is a PREDICTION.** Nothing here reports that anything ran, passed, or
verified anything. A separate verifier executes the artifact and writes the only record that counts; it
recomputes every verdict with its own implementation, and any divergence — in either direction — is a
FAIL. The committed fixture scenario files under `fixtures/scenarios/` are declared input data for that
recomputation, not a report of an execution.

---

## 0. The integration, in one paragraph (no doctrine)

The integration **binds** the attested engine; it never re-authors it. **(1) The seam CLI**
(`cellctl`): one subcommand per engine module — `word` / `plan` / `walk` / `materialize` / `conduct` /
`config` / `cost` / `states` / `descent` / `decode` / `compile` / `check` / `trail` (candidate names,
D4) — each parsing arguments and making exactly **one** engine call (C1); no socket code, no prompt
assembly, no record-writing, no ledger/trail logic in the wrapper; the write side (`agent.prompt`) is
deliberately **not** a command (C2). The engine is imported **by path, sha-pinned**, through
`surface_contract.py` in the exact pattern of R06 (C7): the R06 contract is itself a pinned entry (loaded
from its canonical round, pinned against the staged bytes — R06's own load-anchor precedent), plus the
R06 `orchestrate.py`, the fixture harness/builder, the Grammar (`codex`/`decoder`/`compiler`/
`corruption`), and the B0 ledger — a drifted or missing pin refuses the import. `conduct` is a binding of
the engine's own `orchestrate.main`; the wrapper resolves the live cell spec (data), takes ONE flock on
the cell's work dir around the whole run (C5 — in the wrapper, never the engine), and forwards. Its
`--plan-only` is the C3 sequence (`word.decode_scenario` + `navigate.plan_walk`) emitted with the
declared serialization — byte-identical to `fixtures/plan_equivalence.py`, the diff-ability lens applied
to the seam itself. **(2) The live cell spec** (`spec.json` + the loader in `surface_contract.py`): the
caller-supplied data — scenario, ledger, trail, socket resolution, materialize dirs, soft-config path,
timeouts-as-data (H-INT-4: provisional, one place to change, diff-able — K5); an unknown field is
REFUSED (INCONCLUSIVE, never silently ignored). **(3) The enforcement suite** (`enforce.py` +
`verify-integration.sh`): three legs — L1 capability scan (no driving write verb, AST-scanned for python,
text-scanned for the rest, the human-TTY allowlist declared), L2 entry-point census (every executable a
declared member of the seam manifest; no soft-layer file imports the pinned modules directly — the CLI
is the only path), L3 config-schema validation (every engine-read soft-layer file validates; unknown
fields = INCONCLUSIVE refuse) — each leg proven to FAIL on a deliberately-injected violation under
`fixtures/enforcement/` (C4). The run lock (C5), fail-closed INCONCLUSIVE (C6), the pinned import
boundary (C7), and the byte-exact forwarding (K2) complete the seam.

---

## 1. Binding — the names this round ships

| binding | real name | where |
|---|---|---|
| `cli_entry` | `cellctl` | one thin CLI; subcommand per module (candidates: `/word /plan /walk /materialize /conduct /config /cost /states /descent /decode /compile /check /trail`); `--plan-only` on `/conduct` (C3); the run lock (C5); no write verb exposed (C2) |
| `spec_data` | `spec.json` | the live cell spec — caller-supplied data (scenario, ledger, trail, socket resolution, materialize dirs, soft-config path, `wait_timeout_ms`/`timeout_s`/`max_steps` as data; every provisional number carries its reason in `notes`) |
| `seam_module` | `surface_contract` | `surface_contract.py` — pins the engine modules by path/sha (importing R06's contract), declares `SEAM_SURFACE` / `SEAM_MANIFEST` / `SPEC_SCHEMA` / `L1_DECLARATION` (the command set + census + scan declaration against them), and holds the spec loader (`load_cell_spec` / `resolve_cell_spec`) |
| `enforce_module` | `enforce` | `enforce.py` + `verify-integration.sh` — the three enforcement legs (capability scan · census · config-schema) + pins + C3 plan-equivalence + gates plant re-check |
| `selftest_module` | `selftest` | `selftest.py` — the author's suite (59 checks), a hypothesis never a result |
| `fixture_desk_harness` | `desk_harness` | `fixtures/desk_harness.py` — a BINDING of the pinned R06 fixture desk harness (deterministic, real herdr dialect, `agent_not_found` + absent-socket cases; no live box) |
| `fixtures` | `fixtures/` | `scenarios/` (pinned-cycle / pinned-guard / pinned-encoding — data, sha-pinned) · `build.py` (the fixture-world + cell-spec builder) · `plan_equivalence.py` (the C3 reference runner) · `restart/run_conduct.py` (the cold-restart/run-lock runner) · `enforcement/` (the injected violations: a write verb, an undeclared bin, a direct engine import, an unknown spec field, an unknown soft-config field) · `soft_config/` (good/empty/malformed/partial/unknown-field) |

The functions are the real surface; the command names are **candidate** (H-INT-2 / SCOPE D4 — his to
name). The verifier's pack may bind different names; the functions are what is checked.

---

## 2. Criteria and claims, by id — with PREDICTIONS

**C1 — the seam is a thin binding, one call each.** Prediction: each subcommand parses arguments and
makes exactly one engine call — `word` → `load_scenario_file`/`decode_scenario`; `plan` →
`plan_walk`; `walk` → `navigate.walk` over the attested `orchestrate._LiveWorld`; `materialize` →
`materialize`/`read_materialize`; `conduct` → the engine's own `orchestrate.main` (a binding, never a
re-implementation); `config` → `load_soft_config`; `cost` → `spend_from_records` (records read through
the B0 `LedgerLoader`, charges through `softconfig.budget_of`); `states` → `Orchestrator.read_states`;
`descent` → one op per invocation (`zoom_in`/`zoom_out`/`path_between`/`validate_signed_path`/
`validate_word`); `decode` → `decoder.decode`; `compile` → `compiler.emit`; `check` →
`compiler.validate`; `trail` → `read_trail`/`audit_payload_chains`. The wrapper's AST imports are
stdlib + the seam (`argparse`/`fcntl`/`hashlib`/`json`/`os`/`sys`/`tempfile` + `surface_contract`);
an AST scan finds no socket client, no subprocess, no unicodedata, no normalization call anywhere in
the wrapper's code (K1/K2 made checkable). The declared exception to one-call is the commission's own:
`conduct --plan-only` is exactly the two calls C3 names.

**C2 — the write side is never exposed as a command.** Prediction: the parser's command set equals the
declared `SEAM_SURFACE["commands"]` exactly — no `prompt` command exists. `/states` over the harness
socket reports `observed` per-desk states with zero write methods on the harness; over an absent
socket it reads `{"status":"absent"}` honestly, exit 1 — never a fixture stand-in.

**C3 — plan-equivalence dry run.** Prediction: `cellctl conduct --plan-only --scenario
fixtures/scenarios/pinned-cycle.json` (sha-pinned `82d5bfa7…`) is **byte-identical** to
`fixtures/plan_equivalence.py` over the same file — same bytes, same exit code; the plan reads
`pattern: custom`, visits S→G→Q→P→V. A second CLI process replans byte-identically (lens 5).

**C4 — the enforcement suite holds as a structural fact (legs 1–3).** Prediction: on the fixture
roots, L1 passes the clean bin and FAILS the injected write verb with the named token; the declared
`cell-plant`/`cell-attest` allowlist is honoured by declaration, never hidden. L2 passes a fully
declared census, FAILS an undeclared executable (`undeclared-executable`), and FAILS a direct pinned
import. L3 passes the clean spec/scenario/soft config and FAILS each of: an unknown spec field, an
unknown soft-config field, a malformed scenario — every refusal carries the INCONCLUSIVE reason, never
a silent ignore. An absent required scan root reads INCONCLUSIVE, never clean (lens 6). **On the live
box (predicted — the enforcement working, not papered over):** L1 FAILs with the real findings the
SCOPE itself names — the plugin's own socket client `plugin/bin/_cell_api.py` (AF_UNIX/connect/
sendall; the pre-integration second client W5 re-points onto `cellctl`) and the five desks'
`.pi/prompts/guide.md` write-verb tool lists (the improvised tooling W3/D8 retires); L2 FAILs with
`plugin/bin/cell-attest` importing the pinned `fractal_ledger` directly (outside the seam); L3 PASSes;
the gates plant re-check PASSes (`6989a742…`, his plant). The suite reports these; it never tunes
around them — that would be exactly the paper-over H-INT-5 forbids.

**C5 — the run lock.** Prediction: the CLI opens `<work_dir>/.cellctl.lock` once and holds an
`fcntl.flock LOCK_EX` across the whole engine call (plan-only takes none — pure). While a test process
holds the flock, a second `/conduct` on the same work dir stays blocked: no ledger record lands and
the process remains alive; on release it completes with five per-gate records. The lock lives in the
wrapper, never the engine. A missing work dir is refused (INCONCLUSIVE), never silently created.

**C6 — fail-closed, INCONCLUSIVE never clean.** Prediction: absent scenario / empty scenario (sha256
of empty `e3b0c44298fc…` cited) / absent spec / unknown spec field / absent socket / unconstituted
desk each read `absent`/`inconclusive` with the reason and exit 1 — never a substituted value, never a
clean verdict. `/conduct` over the live `spec.json` (scenario `null`, D2 open) refuses before any
engine call with the D2 reason. The engine's own run statuses (`inconclusive`/`refused`/
`step-limited`) still exit 0 under the engine's own exit-code contract — the report, not the exit
code, carries the truth (the engine's `orchestrate.main` convention, passed through untouched).

**C7 — the pinned seams stay the import boundary.** Prediction: all 9 pinned entries match their
on-disk shas; a drifted byte, a missing file, and a TBD pin each raise `ImportError` from the
pinned loader. The import itself is the pin check (the verify script's step 2). The census's import
rule mechanically forbids every other soft-layer file from importing a pinned module; the declared
importers are exactly `surface_contract.py`, `cellctl`, `enforce.py`, `selftest.py`.

### Claims (K1–K5), predictively

- **K1 — stdlib, deterministic, no LLM.** `cellctl` and `enforce.py` import stdlib + the seam only
  (AST-checked); no network, no LLM, no wall-clock in their logic, no subprocess in either (the
  verify script and the selftest *invoke* the CLI — that is the verification medium, not the checked
  artifact; the cold-restart lens itself demands a second process). The only socket client on the box
  is the pinned engine's `Instrument` (L1 enforces it).
- **K2 — byte-exact, never normalised.** Every report uses `ensure_ascii=False`; the enumerated
  engine bytes (⋂, ∞0′, `−` vs `-`) pass untouched — the ASCII-hyphen descent path is refused by the
  engine and forwarded un-repaired; `/compile` writes the surface bytes raw; the one declared
  envelope rule (the read-trail report's `raw` field carried as `raw_sha256`) is a JSON-safety
  declaration, never a content transformation; the encoding needle `∞0′ → ‖` rides the scenario ref,
  the system override, the spec scope, the soft-config voice, and a compile slot byte-verbatim
  (lens 4 fixtures).
- **K3 — the click is never a machine verdict.** `/check` over a produced artifact ends INCONCLUSIVE
  (HC-1/HC-2 by design — exit 1, never PASS); a decode claiming arrival at ∞0 reads corruption L3;
  the corruption taxonomy is exactly L1 L2 L3 L4 V∅ (no sixth); every engine record the run writes
  carries `attestation_ref: null`.
- **K4 — the B2 guards hold.** The guard scenario's non-seed S visit holds `guard-fail:centre` with
  ZERO prompts to the podium pane and exactly one (G's) reaching the harness — the imported
  `assert_not_centre`, never re-authored; no `herdr_start_agent`-equivalent authority is added
  (H-INT-3 — D1 deferred, `WRITE_METHODS` frozen).
- **K5 — diff-ability.** The live cell spec, the soft config, the scenarios, and the enforcement
  declarations are data files — one place to change, diff-able, versioned, never code; the node→desk
  map stays the imported `DESK_LABELS` table.

### The six lenses, predictively

1. **Criterion match** — every selftest names its criterion in its first docstring line; the seam
   surface declares each command's engine binding, success statuses, and citation.
2. **Invariant end-to-end** — whole-run artifacts, never per call: the cycle runs plan → walk →
   materialize → conduct in one CLI run (the materialize variant included); the hand-off chain
   threads the seed's ref into G's prompt; boot → seed → four turns → run-end with the audit PASS and
   the spend present.
3. **Absence vs validity** — absent/empty scenario, absent spec, empty soft config (sha256 of empty
   cited), absent socket, absent agent: every absence reads absent/INCONCLUSIVE with the reason,
   never valid.
4. **Encoding** — the needle rides command args, spec fields, scenario strings, soft-config voices,
   compiled slots, and the boot line's declared probe — all byte-verbatim; files are opened
   binary-only.
5. **Cold restart** — a walk split across two fresh CLI processes (the second re-arming from the
   ledger + trail alone) produces the exact ledger + trail bytes of the uninterrupted run; the
   enforcement report rebuilds in a second process with the same verdicts; a second `/conduct`
   honours the run lock; a second process replans byte-identically.
6. **Blind tool** — an unavailable live socket holds outage for every turn with zero fenced records
   and a boot read carried `absent`; an unconstituted desk holds `agent_not_found` with zero fenced
   answers for that desk; both end INCONCLUSIVE — never clean, never a fixture stand-in.

---

## 3. D14 divergence log — everything this artifact adds beyond the source

Per Appendix D's own jacket: declared *derivative* · visibly separate from the decoding · adds **no**
L1 symbol, **no** decoding operation, **no** sixth corruption code · alters no invariant line.
**Summary: the integration adds zero engine logic — it adds the command surface (bindings only), the
live-cell spec (data), and the enforcement suite (scans).  The herdr dialect, the prompt assembly, the
record-writing, the D.12 checks, the desk grammar, the descent, the bridge's live mode, R06's
word/navigate/materialize/orchestrate and the Grammar are the imported ones, byte-identical under
their sha pins.**

| # | Addition | Anchor | Resolution |
|---|---|---|---|
| D-1 | The seam CLI (`cellctl`): one subcommand per engine module, one engine call each; `/conduct` = a binding of `orchestrate.main` (argv forward + the resolved engine spec, the engine prints and exits — codes 0/1/3/4 untouched); `--plan-only` = the C3 two direct calls with the declared serialization; the run lock (a single `flock` on `<work_dir>/.cellctl.lock`, wrapper-only); the exit-code convention (0 = declared success status, 1 = any other — INCONCLUSIVE never clean) | Commission C1/C2/C3/C5; SCOPE §1.1/§3.3 | Binding layer; no socket, no prompt assembly, no records, no ledger/trail logic in the wrapper |
| D-2 | The live cell spec (`spec.json` + the loader): the caller-supplied data schema (scenario/ledger/trail/socket resolution/materialize dirs/soft config/timeouts-as-data + `notes` carrying each provisional number's reason); unknown fields REFUSED (INCONCLUSIVE); a `null` scenario refuses the run with the D2 reason; relative paths resolve against the spec's own directory | Commission §7 + H-INT-4; SCOPE Seam E | Data layer, provisional until the first real run (W4) corrects the numbers — one place to change, never code (K5) |
| D-3 | The enforcement suite (`enforce.py` + `verify-integration.sh`): L1 capability scan (AST for python — docstrings are not driving code; text for the rest; the composite subprocess-to-herdr rule; the declared cell-plant/cell-attest TTY allowlist), L2 entry-point census (executable census + the pinned-import rule — the CLI is the only path), L3 config-schema validation (the seam's spec schema + the engine's own attested softconfig/word readers); the verify script's pin check, C3 diff, and gates-plant re-check | Commission C4; SCOPE §4 legs 1–3 | Enforcement apparatus; zero findings is the rule — the live box's real findings are reported, never tuned away |
| D-4 | The seam declarations (`SEAM_SURFACE` / `SEAM_MANIFEST` / `SPEC_SCHEMA` / `L1_DECLARATION`): the command set + one-call bindings, the scan roots, the forbidden tokens, the allowlist, the census (read from disk — the observed listing), the serialization formula | Commission §4/C7; SCOPE §4 | Declared data, versioned, diff-able — the extension of R06's `ORCHESTRATION_SURFACE` practice |
| D-5 | The fixture apparatus: the pinned R06 desk-harness binding + fixture builder (imported, never re-authored), the sha-pinned scenarios (cycle/guard/encoding), the C3 reference runner, the cold-restart/run-lock runner, the injected-violation fixtures, the soft-config fixtures, the new pins (orchestrate, the harness/builder, the Grammar four, the R06 contract) | H-INT-1; R06's fixture precedent; commission §7 | Test apparatus only; the live box is never written — a real `agent.prompt` to a live desk is Amihai's to authorize (W4), not this round's |

---

## 4. Holds — H-INT-1 … H-INT-5, each with the reading this round ships

* **H-INT-1 (no live `agent.prompt` is sent this round).** Every run resolves the fixture harness's
  own socket through a fixture spec; the live `spec.json` declares `live_socket: null` (the engine's
  own resolution) and `scenario: null`, so `/conduct` over it refuses before any engine call. The
  first real paid turn is Amihai's alone to authorize (SCOPE D6, W4).
* **H-INT-2 (command names and the round's name/slot are provisional).** The working handle is
  `integration`; the subcommand names are candidates (the commission's table); the slash spellings
  are declared per command. The functions are the real surface.
* **H-INT-3 (child-spawn ownership is deferred).** This round adds no `herdr_start_agent`-equivalent
  write; the engine's `WRITE_METHODS` stay frozen; nothing in the wrapper composes a prompt or opens
  a socket (L1 enforces it mechanically).
* **H-INT-4 (the scenario schema and the live spec's numbers are provisional).** The spec schema is
  declared data in `SPEC_SCHEMA`; the live `spec.json` numbers (`wait_timeout_ms: 120000`,
  `timeout_s: 30.0`, `max_steps: null`) are placeholders whose reasons are carried in `notes` —
  corrected only by the first real run (Seam E, W4), never hard-coded in logic.
* **H-INT-5 (the live constitutions do not yet speak the §3.6 surface).** The CLI reports
  `no-surface-announced`/`surface-malformed` exactly as the engine holds them — the harness proves
  the pass path, the live box will prove the hold path at W4; nothing papers over it, and the
  enforcement suite's live findings (the guide.md tool lists, the plugin socket client, the direct
  ledger import) are reported as the W3/W5 work they belong to.

---

## 5. Assumptions and open flags (stated, not hidden)

1. **Load anchors (the R06 precedent, carried).** The R06 contract is loaded from its canonical round
   (`rounds/R06-orchestration/authored/surface_contract.py`, sha `154a6522…`) pinned against the
   staged bytes; the Grammar is read from its canonical round (`rounds/meta-implementation/authored`,
   pinned); the R06 `orchestrate.py` and the fixture modules are loaded from the staged
   `./predecessors/` bytes with their plain-name imports bound to the loaded contract + ledger (the
   `load_bridge_run` pattern). All canonical/staged pairs were verified byte-identical on this box;
   the pins are the contract either way.
2. **Scan roots.** The declared roots are `plugin/bin`, `desks/`, `~/.pi/agent/settings.json`,
   `~/.config/herdr/soft.json` (absent = the engine's defaults, noted), and the authored CLI layer.
   The pi-herdr package and the herdr-managed `extensions/herdr-agent-state.ts` are **consumed
   platform** (SCOPE §6: consumed as-is, never changed) — they are not the cell's soft layer, so they
   are not scan roots; the cell's own extension packages are an empty declared list that W5 populates
   (an undeclared extension bin then FAILs the census by construction).
3. **The live verdict is the enforcement working.** On today's box `verify-integration.sh` predicts
   leg 1 FAIL (the plugin's `_cell_api.py` socket client + the five desks' guide.md write-verb tool
   lists) and leg 2 FAIL (`cell-attest`'s direct `fractal_ledger` import), with L3, the pins, the
   plan-equivalence diff, and the gates plant PASSing. These findings are real pre-integration
   conditions that W3 (constitution retirement, D8) and W5 (plugin re-pointing) fix; the suite never
   tunes around them.
4. **Exit-code convention.** 0 = the report's declared success status; 1 = any other (a blind spot
   never reads clean); `/conduct` passes the engine's own 0/1/3/4 through untouched — an
   `inconclusive` run still exits 0 because the engine's own CLI defines that contract, and the
   report is the truth.
5. **The run-lock file.** The SCOPE's "one flock on the work dir" is realized as
   `<work_dir>/.cellctl.lock` (flock needs a file; the file lives inside the locked dir). A missing
   work dir refuses the run rather than creating one.
6. **K1's subprocess clause.** The CLI and `enforce.py` spawn nothing; `verify-integration.sh` and the
   selftest invoke the CLI as subprocesses because the cold-restart lens itself demands a second
   process — that is the verification medium, declared, never the checked artifact's logic.
7. **Byte-reproducibility of the restart test** holds under the carried canonical-work-path
   assumption: the same ledger/trail/socket path strings across every process, the harness answers
   deterministic fiction over (desk, cell, step), the fixture clock fixed — clearly labelled
   stand-ins, never a claim about any live desk.
8. **The `raw_sha256` envelope rule** (D-1): the read-trail report's `raw` field — the file's own
   bytes, already on disk — is carried as its sha256 in the JSON envelope. A declared JSON-safety
   rule, never a content transformation; the trail's lines ride byte-exact.
9. The verifier's pack may bind different names than §1; the functions are the real surface, the
   names are stable and documented here.
