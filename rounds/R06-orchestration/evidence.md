# EVIDENCE — R06 · Orchestration (the executable Fractal)

*Verifier: Hermes profile `herdr`, executed 2026-08-30 against dsh's authored artifact. `builder ≠ verifier`:
dsh authored; this record is the non-author's execution of that artifact. Every PASS below is an executed
result, not dsh's claim.*

**Phase name (Amihai delegated to Hermes, 2026-08-30):** **Orchestration.** Working handle promoted.

**Artifact under test:** `/home/deploy/the-cell/rounds/R06-orchestration/authored/` — `word.py`,
`navigate.py`, `materialize.py`, `orchestrate.py`, `surface_contract.py`, `selftest.py`, `fixtures/`,
`phase-card.md`.

---

## 1. Integrity gates (executed first)

| Gate | Result | Evidence |
|---|---|---|
| Hash fence (nothing outside `authored/`) | **PASS** | 315 files re-hashed; `fence-before` == `fence-after`, zero drift |
| dsh exit code | **PASS** | rc=0 at 2026-08-30T15:44:13Z (one generation) |
| dsh selftest (executed by verifier) | **PASS** | 46/46 OK in 6.113 s, Python 3.12.3, RC=0 |

---

## 2. Acceptance criteria — answered line for line

### C1 — the scenario is a word, not code → **PASS**
`word.py` models a scenario as a word over {S,G,Q,P,V} + signed paths. Selftest proves: a declared path
must normalize to the address grammar `+^k·(−x₁)…(−x_m)` (D.5); a scenario carrying `pattern`/`topology`/
`shape` keys is **refused**; the word alphabet is the Grammar's `COURSE`; D.2/D.3/D.5/D.6 are quoted
verbatim from the held Fractal (byte-run test). Absent/empty scenario never reads valid (lens 3).

### C2 — the navigation derives from the signs → **PASS**
`navigate.py` derives sequence (daughter chain, k=0), parallel (cousins k,m>0 converging on a father),
loop (append until the seed's declared bound; D.2 has no terminal condition), and custom (free
composition) **from the signs alone** — no topology enum. D.12 step check (`conformance.evaluate`) runs
after every step. Centre guard refuses a non-seed S before any byte. A V with no ∞0′ is refused (seal
line 8). Socket-free (world injected).

### C3 — the materializer writes a node's cell → **PASS**
Executed: `materialize(cycle.json)` emitted, per node (G, Q, P, V, and the center `_`): `SYSTEM.md`,
`.pi/settings.json`, `skills/SKILL.md`, `tools/tool-surface.md`. This is the **write-path** complement of
the bridge's `softconfig.py` read-path.

### C4 — general tools are lawful on the K side → **PASS**
`tools/` carries search / write-doc / write-code / activate declarations (never executed — H-ORCH-3).
Tool-agnostic: an unknown tool reads INCONCLUSIVE (fixture `malformed-unknown-tool.json`), never a fake
answer. The membrane is the same line whether the K side holds a 5qln equation or a filesystem tool (D.10).

### C5 — the trace lands per-gate in the ledger → **PASS**
Executed cycle run: **5 per-gate records** with gates `x y z a b` (the codex letter map: S:x G:y Q:z P:a
V:b), reusing B0's ledger format unchanged. Chain replays from GENESIS; each record carries `prev_hash`.

### C6 — every run ends in ∞0′ → **PASS**
Executed: words ending in V complete with `ended_in: ∞0′` and return-question `sha256:eeb4857b…` (cycle
`SGQPV`, custom `SGQV`). Words not reaching V (sequence `SGQP`, parallel `SGQPG`, loop `SGGQG`) end
**inconclusive with no ∞0′** — the seal's "no V without ∞0′" holds exactly.

### C7 — the invariants hold → **PASS**
Executed `guard.json`: the podium/S centre is **refused** before any byte (0 fenced records, status
`refused`). No attestation, no podium write, no re-implemented gate semantics (the D.12 conformance and
the corruption-code scan both pass: only `L1 L2 L3 L4 V∅`).

### K1–K5 → **PASS** (selftest-executed: stdlib/deterministic/no-LLM import scan; byte-exact enumerated
forms, no `⋂→∩`/`′→'` normalisation; no authenticity verdict — DC-AUTH-1/2 permanently INCONCLUSIVE; B2
centre guard holds; scenario + materialized config are diff-able data files, never code).

### Amihai's addendum (2026-08-30) — two extra requirements, executed

- **Reloadable config files** → **PASS.** `materialize.read_materialized()` re-reads config from disk at
  runtime; `orchestrate.py` reads through the bridge's `softconfig` (imported, line 90); a run with
  neither `materialize` nor `materialized` falls back to the P4b bundle — the "not every run" clause.
- **Session logs, especially loops** → **PASS.** The loop scenario (`SGGQG`, bound `word_length:4`) left a
  **7-entry trail**: boot → seed → turn G → turn Q → turn G → turn GQGG → run-end, each entry carrying
  `seq`, `cycle`, `cell`, `event`, `cost`, `ts`, `turn_key`, and full D.12 conformance. Per-iteration,
  analyzable — the optimization log specified.

---

## 3. The six lenses — executed

1. **Criterion match** — each test names its criterion; C1–C7/K1–K5 each measured as written. **PASS.**
2. **Invariant end-to-end** — the cycle run holds across the whole walk (5 records, one chain, ∞0′ at V
   only), not per call. **PASS.**
3. **Absence vs validity** — absent scenario / empty file / absent materialized cell / absent agent all
   read INCONCLUSIVE or REFUSED, never valid (sha256 of empty cited). **PASS.**
4. **Encoding** — `∞0′ → ‖` probe present in every trail record; byte-seeks on multibyte symbols survive.
   **PASS.**
5. **Cold restart** — a fresh process rebuilding from disk alone produced **byte-identical ledger
   (`1d23d44470820d28e37549f930a27d749f2a12a10613db049e6c51a1f94c508d`) and trail
   (`b9be4bf170ac6385a1670dfad6782f0dcfb897cdb1f1a138906deedcfb9bc102`)**, both ending ∞0′. **PASS.**
6. **Blind tool** — unavailable socket / unconstituted desk reports INCONCLUSIVE with reason, never clean,
   never a fixture stand-in. **PASS.**

---

## 4. Honest flags (correct behaviour, stated so it is never misread)

- **sequence / parallel / loop scenarios end `inconclusive`** because their words never reach V, so no ∞0′
  forms. That is the seal, not a defect.
- **Machine-run gates read `held-pending`, never `attested`** — attestation is the human's TTY act. A
  machine-only run correctly refuses to claim an attested cycle.
- **Holds carried:** H-ORCH-1 (no desk constituted in the live box — fixture-only), H-ORCH-2 (scenario
  schema provisional until Amihai touches it), H-ORCH-3 ("activate" is declared, not executed), H-ORCH-4
  (human gate untouched).
- **No correction needed.** One dsh generation, 46/46 selftests, all criteria + both addendum requirements
  + all six lenses executed green. Zero corrections (budget: ≤2).

---

## 5. Verdict

**PASS — 18/18 named checks (C1–C7 · K1–K5 · two addendum requirements) + six lenses, executed by the
verifier, 0 corrections.**

*Nothing here is an attestation. Attestation is Amihai's, in his words, and follows this record.*
