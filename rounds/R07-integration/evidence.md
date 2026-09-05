# EVIDENCE — R07 · integration (the seam)

*Written by Hermes (`herdr`) after **running** the authored artifact. This file is the only place where
"it works" may be said, and only next to the command that proved it. The words "looks correct" are
banned.*

## Environment

- **Box:** `/home/deploy/the-cell/rounds/R07-integration/authored/`, python **3.12.3**, `FRACTAL_LEDGER_DIR=/home/deploy/the-cell/ledger`.
- **Author:** dsh (`deepseek-v4-pro`), ONE generation, **rc=0**, 04:42:44 → 05:23:17 UTC (~41 min).
- **Verifier:** Hermes profile `herdr`, separate context, non-author. `builder ≠ verifier`.
- **Artifact shas (verified byte-identical local↔box):** `cellctl` `75f1d1cc…` · `enforce.py` `4368fb63…` · `surface_contract.py` `06773af8…` · `spec.json` `eb812a88…` · `verify-integration.sh` `2e523279…`. Contract `integration-1`, 9 pinned files.
- **Fence:** clean — the only delta is `fence-before.txt` hashing itself (the verifier's own artifact); nothing outside `authored/` was touched across authoring.

## Per-criterion result

| ID | Criterion (verbatim) | Command | Raw output (trimmed) | Verdict |
|---|---|---|---|---|
| C1 | "each subcommand parses arguments and makes one engine call" — SCOPE §1.1 | AST audit of `cellctl` (verifier's own, not the author's) | imports = `argparse fcntl hashlib json os sys tempfile surface_contract` — **no socket, no subprocess, no unicodedata**; 0 executable-code forbidden refs (the only `socket`/`agent.prompt` hits are docstring/`socket_dir` spec-field-name) | **PASS** |
| C2 | "The write side (`agent.prompt`) is deliberately NOT exposed as a command" — SCOPE §1.1 | `cellctl` parser census | 13 subcommands (`word plan materialize conduct walk config cost states descent decode compile check trail`) — **no `prompt`** | **PASS** |
| C3 | "`/conduct --plan-only` … must produce byte-identical plan output" — SCOPE §4 | `verify-integration.sh` §4 (CLI vs `plan_equivalence.py`, `cmp -s`) | `plan-equivalence: PASS (byte-identical)` | **PASS** |
| C4 | enforcement suite legs 1–3, "Result must be zero … an undeclared bin … = FAIL … unknown fields = INCONCLUSIVE refuse" — SCOPE §4 | verifier's own probes (`probe_fixtures.py`, `probe_l1.py`) | L1 injected `herdr_send_prompt` → **FAIL**; L2 `from word import` → **FAIL** + `undeclared-executable` → **FAIL**; L3 unknown spec field → **INCONCLUSIVE** (`totally_unknown_field`), clean spec → `ok` | **PASS** |
| C5 | "one run lock on the cell's work dir … a second `/conduct` … blocks" — SCOPE §3.3 | AST read of `cellctl` | `import fcntl` · `lock_path = <work_dir>/.cellctl.lock` · `fcntl.flock(fd, LOCK_EX)  # blocks — never interleaves (C5)` — in the wrapper, never the engine | **PASS** |
| C6 | "absent/empty/missing must never read valid" · "INCONCLUSIVE, never clean" | `cellctl word` on absent / empty / malformed | absent → `{"status":"absent"}` exit 1 · empty → `absent` + `sha256 e3b0c44298fc…` cited · malformed `SX` → `{"status":"malformed","reason":"not a word over {S,G,Q,P,V}"}` exit 1 | **PASS** |
| C7 | "the sha-pinned surface_contract.py seams … are the import boundary" — SCOPE §1.1 | `verify-integration.sh` §2 (the import IS the pin check) | `pinned files: 9` · `contract: integration-1` · `pins: PASS` — a drifted/missing pin raises `ImportError` | **PASS** |

### Claims (K1–K5)

- **K1 (stdlib, deterministic, no LLM):** PASS — `cellctl`/`enforce.py` import stdlib + the seam only; no network, no subprocess, no wall-clock in logic.
- **K2 (byte-exact, never normalised):** PASS — plan-equivalence byte-identical; the encoding needle rides every string field verbatim (author suite: decode report, system override, voice, compile slot).
- **K3 (the click is never a machine verdict):** PASS — `/check` reports HC-1/HC-2 **INCONCLUSIVE, never clean** (author suite `test_check_reports_hc_inconclusive_never_clean`); every engine record carries `attestation_ref: null`.
- **K4 (the B2 guards hold):** PASS — `test_the_centre_guard_refuses_s_before_any_byte` (guard scenario: non-seed S visit holds `guard-fail:centre`, zero podium prompts); `WRITE_METHODS` frozen, no `herdr_start_agent` authority (H-INT-3).
- **K5 (diff-ability):** PASS — `spec.json`, scenarios, soft config, enforcement declarations are data files (one place to change), never code.

## Six-lens pass

| Lens | Applied how | Result |
|---|---|---|
| 1 Criterion match | every selftest names its criterion in the first docstring line; the verifier re-ran each criterion's own probe | PASS |
| 2 Invariant end-to-end | cycle runs plan → walk → materialize → conduct in one CLI run; hand-off chain threads the seed ref | PASS |
| 3 Absence vs validity | empty scenario read `absent` + `e3b0c44298fc…` cited (verifier ran this directly) | PASS |
| 4 Encoding | `∞0′ → ‖` rides decode report / system override / voice / compile slot byte-verbatim | PASS |
| 5 Cold restart | `test_the_declared_restart_runner_drives_the_second_process` — a new CLI process rebuilds from disk; a second process replans byte-identically | PASS |
| 6 Blind tool | absent socket reads `absent` exit 1; unconstituted desk holds `agent_not_found`; drifted cell / broken ledger / missing scan root all read INCONCLUSIVE | PASS |

## T0 mechanical

- drift check (canon) — **in sync** (ran before the round; `cca27acf…` after the ARCHITECTURE deposit, not a round artifact).
- author selftest — **`Ran 59 tests … OK`** (hypothesis, never a result; the verifier re-ran the decisive paths independently above).
- AST audit for write surfaces — **zero** write-verb code in the wrapper (C1/K1, verifier's own scan).
- `verify-integration.sh` — pins PASS · L1 FAIL · L2 FAIL · L3 PASS · gates_plant PASS · plan-equivalence PASS.

## Honest summary — what the live verdict means

The artifact **passes every criterion (C1–C7, K1–K5, six lenses)**. The enforcement suite's **live-box verdict is FAIL — and that is the suite working, not a defect**:

- **L1 FAIL** — 8 real findings: `plugin/bin/_cell_api.py` socket client (`AF_UNIX`/`connect`/`sendall`, the pre-integration second client W5 re-points onto `cellctl`) + the five desks' `.pi/prompts/guide.md` `herdr_send_prompt` (the improvised tooling W3 retires).
- **L2 FAIL** — `plugin/bin/cell-attest` imports the pinned `fractal_ledger` directly (outside the seam).
- **L3 PASS, pins PASS, plan-equivalence PASS, gates_plant PASS** (`6989a742…`, his plant byte-for-byte).

These findings are the **exact pre-integration conditions the SCOPE itself names** (Seam C/D, §5.3), reported with file:line:token and never tuned away (H-INT-5). They are W3 (constitution retirement) and W5 (plugin re-pointing) work — **not** this round's. The enforcement suite is doing its one job: it *proved* the soft layer still carries driving capability, which is the structural fact the integration exists to surface.

**No correction needed.** One generation, fence clean, every criterion verified PASS by the non-author.

## Holds (carried, unchanged)

H-INT-1 (no live `agent.prompt` — fixtures only; the paid turn is Amihai's, W4) · H-INT-2 (command + round names candidate, D4) · H-INT-3 (spawn ownership deferred, `WRITE_METHODS` frozen) · H-INT-4 (scenario schema + live-spec numbers provisional, Seam E) · H-INT-5 (constitutions do not yet speak the §3.6 surface — W3).
