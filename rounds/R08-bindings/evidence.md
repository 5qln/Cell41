# EVIDENCE — R08 · the bindings (verifier: Hermes profile `herdr`)

**Verdict: PASS — 0 corrections.** dsh authored in one generation (rc=0, 53.5 min); Hermes verified
independently against C1–C8 · K1–K5 · six lenses. `builder ≠ verifier` held: the author's own green
checkmarks were treated as a hypothesis and re-computed from a separate reading.

---

## 1. What was executed (this is the record, not a claim)

| Check | Command / source | Result |
|---|---|---|
| **Hash fence** | `find … ! -path '*/authored/*' \| sha256sum` before vs after | **byte-identical** — zero files touched outside `authored/` |
| **Author's suite** | `python3 selftest.py` (box, nvm-sourced for node) | **38/38 OK** in 7.76 s; every test names its criterion + lens; imports the **real** R07 `enforce` module + drives the **real** `cellctl` |
| **Enforcement, live cell (pre re-point)** | `bash verify-integration.sh` (R07, over the live un-re-pointed cell) | **FAIL, exactly as the diagnosis predicted**: L1 FAIL · L2 FAIL · L3 PASS · `gates_plant` PASS · `plan-equivalence` **PASS (byte-identical)** — the three findings are real, and the suite is honest |
| **Independent capability scan** | grep of the authored re-points for `herdr_send_prompt · herdr_start_agent · agent.prompt · send_text/input/keys · AF_UNIX · socket.socket · fractal_ledger` | **clean** — no socket, no drive verb; the only `fractal_ledger` is `fractal_ledger = sc.ledger` (the declared pinned-contract re-point) |
| **Independent brick decode** | `cellctl word --scenario bricks/methods/sgqpv-cycle/word.json` | `status: ok` — the word `SGQPV` + signed paths decode through the **real** engine; seed ref = the plant's sha256 |
| **Plant** | `verify-integration.sh` gates check | byte-identical `6989a742f5…` — his plant untouched |

---

## 2. Per-criterion verdict

| Criterion | Verdict | The evidence |
|---|---|---|
| **C1** thin binding, one call each | **PASS** | 13 studs (tool-table.json), each exactly one `cellctl` subcommand; `cellctl.mjs` makes one `spawn(bin, argv, {shell:false})`; the 8 addendum actions each `command = [cellctl, subcommand, …]`; plan-equivalence byte-identical |
| **C2** write side never exposed | **PASS** | no tool/action wraps `agent.prompt`; `/states` is the only desk-facing read; absent socket reads `{"status":"absent"}` |
| **C3** binding adds nothing | **PASS** | `verify-integration.sh` over the real cellctl: `plan-equivalence: PASS (byte-identical)`; author's test re-proves it through the binding's argv |
| **C4** enforcement reads clean after re-point | **PASS (authoring) · live flip = deployment step** | the re-points remove the three findings (verified by independent grep + full read); the author's suite proves the flip to zero using the **real** `enforce.leg1_capability`/`leg2_census`; the live flip awaits the deployment below |
| **C5** run lock honoured | **PASS** | no second lock path exists in any binding source; concurrent second `/conduct` blocks → `already-complete` |
| **C6** fail-closed | **PASS** | absent cellctl/socket/files/malformed/null-spec → INCONCLUSIVE with reason; empty named (`e3b0c44298fc…`); never clean, never a stand-in |
| **C7** pinned seams, no engine import | **PASS** | no soft-layer file imports the engine directly except `cell-attest`'s **declared** `import surface_contract` (the import IS the pin check — a drifted pin refuses at ImportError) |
| **C8** the LEGO requirement | **PASS** | 13 independent studs, no sequence field, no chaining construct; the method is the brick (`word.json`+`spec.json`+`soft.json`, data the engine reads — the brick decodes through the real engine); a new method = a new brick directory, zero re-authoring; nothing in the binding names a cell (swarm reachable with zero firmware change) |
| **K1** stdlib, deterministic, no LLM | **PASS** | the extension's only subprocess is the seam binary; no network, no wall-clock in logic |
| **K2** byte-exact, never normalised | **PASS** | bytes forwarded untouched; the `∞0′ → ‖` needle rides tool args / action argv / inline JSON / file paths / the podium signal; a needle smuggled into an excluded notation is REFUSED, never normalised |
| **K3** no machine verdict | **PASS** | HC-1/HC-2 stay INCONCLUSIVE by design; `check` reports PASS only; nothing claims ∞0 |
| **K4** B2 guards hold | **PASS** | no `herdr_start_agent`-equivalent authority; `WRITE_METHODS` frozen; the desks' spawn line fenced *deferred — D1* |
| **K5** diff-ability | **PASS** | tool table, addendum constants, brick files, census extension are all data, one place to change |

## 3. The six lenses

1. **Criterion match** — every author test names its criterion in the first line; each was re-read against the criterion *as written*. PASS.
2. **Invariant end-to-end** — the binding's per-call result is the raw `cellctl` bytes every time; a full cycle through the binding completes with the same shape as the direct CLI. PASS.
3. **Absence vs validity** — absent cellctl / absent files / empty files / null-spec never read valid; sha256 of empty named. PASS.
4. **Encoding** — the needle rides every string field byte-verbatim; files read binary; no text-mode byte seek in the binding. PASS.
5. **Cold restart** — a fresh process re-arms from disk alone; the second `/conduct` honours the run lock. PASS.
6. **Blind tool** — unavailable socket reads `absent`; unconstituted desk holds `agent_not_found`; the podium reports INCONCLUSIVE, never clean. PASS.

---

## 4. Honest limits (what this evidence does NOT yet claim)

- **The live flip is not yet applied.** `verify-integration.sh` over the live cell still reads FAIL because
  the re-points are authored but **not deployed** to the live plugin/desks. Deployment is the
  post-attestation act; the final acceptance is a re-run of `verify-integration.sh` reading **zero**
  findings after the re-points land on the live cell. The author's suite already proves the flip on a
  fixture world with the real enforce module; this evidence verifies the re-points are correct and the
  suite is honest, and records the deployment as the closing step.
- **No live `agent.prompt` was sent** (H-R08-1) — the paid turn is W4, Amihai's alone.
- **The pi runtime's jiti** (loading `index.ts`) is smoke-tested against the harness's jiti, not the
  live pi session (H-R08-1: no pi session started this round). The extension's TS import is the one
  live-coupling deferred to W4.

## 5. Residual flags for Amihai's attention (declared, never hidden)

1. **D14-3 — `cell-begin` now refuses to raise the cell (exit 9).** The raise (workspace.create +
   layout.apply) rode the removed socket; dsh removed it rather than re-wire it, because a
   plugin-held layout write violates the governing line (soft layer only points). The cell is already
   standing today, so nothing breaks now — but raising a *fresh* cell will need a different path. This
   is a genuine behavior change; the design is sound, but it is his to accept or redirect.
2. **D14-8 — `enforce.py`'s hard-coded forbidden-pattern list** does not contain the spawn-tool
   literal; finding ii is re-pointed at its source (the guides) and the author's suite carries its own
   spawn-authority scan. Recommended follow-up: consume `L1_DECLARATION.forbidden_patterns` in a future
   enforcement edit (the file is attested; not touched this round).
3. **Names are candidates** — `pi-cell`, the command names, and the round's name/slot are his (D4).

## 6. Verdict

**PASS.** One dsh generation, 0 corrections. The bindings connect the two callers to the attested seam,
the three enforcement findings are re-pointed (never allowlisted), the LEGO brick format is data the
engine reads, and the podium is re-pointed to the formation trail. The sole remaining act before the
live cell is honest is deployment + the re-run of `verify-integration.sh` (recorded above).
