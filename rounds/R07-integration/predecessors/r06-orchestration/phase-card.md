# PHASE CARD — orchestration · the executable Fractal (working handle)

**Round:** orchestration — the working handle; the phase name and slot are **Amihai's to name**. The
scenario is a word (D.3); the navigation is the signed path (D.5); the materializer is zoom-in
(D.1/D.10); the trace lands per-gate in the B0 ledger, and every run ends in ∞0′.
**Author:** dsh (`deepseek-v4-pro`, one generation). **Verifier:** Hermes profile `herdr`,
separately, against a pack written before it judges anything. `builder ≠ verifier`.
**Governing sources:** the commission (`./commission.md`), the Codex, Appendix D (held at
`../sources/5qln-codex-appendix-D-the-fractal.txt`). **Codex §1.10 governs every conflict — the
source wins.**

**Every verdict in this card is a PREDICTION.** Nothing here reports that anything ran, passed, or
verified anything. A separate verifier executes the artifact and writes the only record that
counts; it recomputes every verdict with its own implementation, and any divergence — in either
direction — is a FAIL. The committed fixture scenario files under `fixtures/scenarios/` are
declared input data for that recomputation, not a report of an execution.

---

## 0. The orchestration, in one paragraph (no doctrine)

Orchestration extends the attested bridge in exactly three ways, importing every predecessor (never
re-implementing). **(1) The scenario is a word** (`word.py`): a scenario is DATA — a word over
{S,G,Q,P,V} plus the signed paths between its nodes (D.3/D.5) — never code, never a hardcoded
topology enum; any `pattern`/`topology`/`shape` field is REFUSED (the signs are the topology, D.6).
Decode + validate against the Grammar: the alphabet is P4b's imported `COURSE`, the path validator
is B3's imported `validate_signed_path`, and every declared path must NORMALIZE — it must equal
`path_between(from, to)` (`addr(A → B) = +^k · (−x₁)…(−x_m)`, all + first then all −). **(2) The
navigation is the address grammar** (`navigate.py`): the walk derives sequence/parallel/loop/custom
from the SIGNS alone (k=0 daughter chain · cousins k,m>0 converging on a father · append until the
seed's declared bound — D.2 has no terminal condition · free composition otherwise); the D.12 step
check (P4a's `conformance.evaluate`, imported) runs after every navigation step. **(3) The
materializer is zoom-in** (`materialize.py`): the WRITE-path — the complement of the bridge's
`softconfig.py` READ-path. Each node is its own lawful cell with its own ∞0|K membrane and its own
tools on the K side (D.1/D.10): `SYSTEM.md`, `.pi/settings.json`, `skills/`, tools — all bytes from
the enumerated P4b tables; the K side may carry GENERAL tools (search / write-doc / write-code /
activate — declared, never executed, H-ORCH-3). `orchestrate.py` drives a materialized word over
the live desks via the bridge's attested live mode (`DeskAdapter(mode="live")` → the imported
instrument dialect), reads real states, carries hand-offs, assembles the trace — per-gate in the B0
ledger, format unchanged — and refuses any end without ∞0′ ("No V without ∞0′", seal line 8).
*"not every run"*: the materialize step is optional per run.

## 1. Binding — the names this round ships

| binding | real name | where |
|---|---|---|
| `word_module` | `word` | `word.py` — `FRACTAL_QUOTES` (D.2/D.3/D.5/D.6 verbatim), `decode_scenario`, `load_scenario_file`, `letter_of`, `declared_visits` |
| `navigate_module` | `navigate` | `navigate.py` — `orientation`, `plan_walk`, `walk`, `common_father`, `slot`, `ORIENTATIONS` |
| `materialize_module` | `materialize` | `materialize.py` — `GENERAL_TOOLS`, `MATERIALIZE_DEFAULTS`, `law_line`, `node_cell`, `materialize`, `read_materialized`, `cell_files` |
| `orchestrate_module` | `orchestrate` | `orchestrate.py` — `Orchestrator` (the live-desk conductor), `BootError`, `main` |
| `surface_contract_module` | `surface_contract` | `surface_contract.py` — sha-pins every predecessor by path (now incl. word/navigate/materialize); declares `ORCHESTRATION_SURFACE` |
| `selftest_module` | `selftest` | `selftest.py` — the author's suite, a hypothesis never a result |
| `fixture_desk_harness` | `desk_harness` | `fixtures/desk_harness.py` — the deterministic fake desk box (real herdr dialect, `agent_not_found` + absent-socket cases) |
| `fixtures` | `fixtures/` | `scenarios/` (the four patterns + the cycle + the guard + the malformed set + harness specs — data files) · `build.py` (the fixture builder) · `run_walk.py` (the cold-restart runner) |

The functions are the real surface; the names are stable and documented here. The verifier's pack
may bind different names — the functions are what is checked.

## 2. Criteria and claims, by id — with PREDICTIONS

**C1 — the scenario is a word, not code.** Prediction: `word.decode_scenario` accepts the six
fixture scenarios (cycle/sequence/parallel/loop/custom/guard) with status `ok`; refuses the
malformed set with reasons that name the exact field — an ASCII-hyphen path cites U+002D (never
normalised to U+2212, K2), a non-normalized path cites the address grammar, a broken walk chain
cites the continuity rule, a `pattern`-key scenario cites D.6 (the signs are the topology). Absent
(None), empty file (sha256 `e3b0c44298fc…` carried in the reason) and missing file all read
`absent` — never valid. Every scenario artifact under `fixtures/scenarios/` is a JSON data file —
never code. `FRACTAL_QUOTES` carries D.2/D.3/D.5/D.6 verbatim (the selftest proves each byte-run
against the held Fractal text).

**C2 — the navigation derives from the signs.** Prediction: `navigate.orientation` reads D.6
exactly (k=0 daughter · m=0 father · k,m>0 cousins · empty same-node); `plan_walk` derives
`sequence` for the all-daughter chain (ε→G→QG→PQG), `parallel` for the cousins path +·−P
converging with the father step + on the shared father-frame G, `loop` for the append word
expanded to the seed's declared bound (word length 4 → visits "", G, GG, QGG, GQGG), and `custom`
for any other lawful mix — including the cycle (daughter + cousins, the return is V's slot,
D.1/D.8). No scenario field carries a pattern label (the fixtures contain none; the decoder
refuses any). Every walk step carries a conformance report from the imported
`conformance.evaluate` (P4a reuse — the D.12 check after every navigation step).

**C3 — the materializer writes a node's cell.** Prediction: `materialize.materialize` emits, per
node, the four declared files — `SYSTEM.md` (LAW line derived from the enumerated seal form +
SEAT/EQUATION/OPERATION/HAND-OFF from `grammar.PHASE`, byte-exact), `.pi/settings.json` (model =
the bridge's `DECLARED_MODEL`, thinking true, tools = `["read","grep","bash"]` + the scenario's
general tools), `skills/SKILL.md` (the P4b bundle at this address — the grammar's own
`verify_bundle` reads it `ok`), `tools/tool-surface.md` (the K-side declaration). The
materialize step is optional per run: a run with neither `materialize` nor `materialized` completes
(the prompt falls back to the P4b bundle — "not every run"); a run with `materialize` emits and
reads `SYSTEM.md` from disk at runtime (the READ side of the write path — the complement of the
bridge's `softconfig`); a run with `materialized` verifies the already-materialized word from disk
— absent, empty (sha256 of empty cited) or drifted cells read INCONCLUSIVE, never used silently.

**C4 — general tools are lawful on the K side.** Prediction: search / write-doc / write-code /
activate ride `GENERAL_TOOLS` (declared data); the emitted settings and tool-surface carry them
with the One Law line — the membrane | is the same line whether the K side holds a 5qln equation
or a filesystem tool (D.10); the adapter hardcodes no 5qln-only gate — an unknown general tool
reads INCONCLUSIVE with the reason, never a silently substituted cell. `activate` is DECLARED into
the soft layer, never executed (H-ORCH-3).

**C5 — the trace lands per-gate in the ledger (B0 unchanged).** Prediction: the cycle run's ledger
holds exactly five records — gate x at ε (the tentative L2 seed), gates y/z/a/b at G/Q/P/V —
written through B0's `LedgerWriter` (the chain verifies), in B2's proposal shape (held-pending,
mechanical, tentative, `attestation_ref` null, `fenced:sha256:<hex>` payloads, B2's `turn_key`
with attempt `step:<i>`), and the imported dependency audit reads PASS. The observability trail is
B4's imported `FormationTrail` — boot, seed, four turns, run-end — hash-chained and replayable.

**C6 — every run ends in ∞0′.** Prediction: the complete run reports `status: complete`,
`ended_in: "∞0′"`, and its `return_question` is the V answer's ∞0′ slot ref (which may seed the
next cycle — D.8); a lawful V surface whose ∞0′ slot is absent (the harness's omit-infinity
variant) holds `refused:no-∞0′` and the run ends `refused` — never complete; a walk that never
reaches V (the sequence walk ends at P) ends INCONCLUSIVE — never clean.

**C7 — the invariants hold.** Prediction: no `send_text`/`send_input`/`send_keys` anywhere (no
podium write); no `state: "attested"` write, no non-null `attestation_ref`, no `cell-attest`
invocation (no machine authenticity path); the herdr dialect, the D.12 checks, the desk grammar,
the descent and the bridge's live mode + softconfig read-path are the IMPORTED ones (no AF_UNIX /
sendall / dialect code in the authored modules); no hardcoded topology enum; no hardcoded
emphasis/voice/model/budget literal in the conductor's flow (no `kimi-k3` literal — the model
flows from the bridge's `DECLARED_MODEL`).

### Claims (K1–K5), predictively

- **K1 — stdlib, deterministic, no LLM.** word/navigate/materialize import stdlib only; the AST
  scan lists their imports against `sys.stdlib_module_names` (+ the pinned seam names);
  orchestrate's imports are stdlib + `fractal_ledger` + `surface_contract`; no subprocess, no
  network, no wall-clock in logic — the live socket is the only I/O, and it is the attested
  instrument's.
- **K2 — byte-exact enumerated forms.** The emitted SYSTEM.md bytes equal `grammar.PHASE[letter]`
  registers byte for byte (⋂ stays U+22C2 — never ∩; the V equation's ∞0' stays U+0027 — the
  codex's glyph, never folded to the commission table's ∞0′); no unicodedata/NFKC/NFKD anywhere;
  the One Law line derives from the enumerated seal form, never a fresh literal.
- **K3 — the click is never a machine verdict.** No record the conductor writes carries state
  attested or a non-null attestation_ref — HC-1/HC-2 stay INCONCLUSIVE by construction; the
  machine never claims arrival at ∞0 (the ∞0′ slot is a reference carried, never a verdict).
- **K4 — the B2 guards hold.** The centre guard refuses S/podium BEFORE any byte: the guard
  scenario's second S visit holds `guard-fail:centre` with exactly one `agent.prompt` reaching the
  harness and ZERO prompts to the podium pane; the imported `assert_not_centre`, never re-authored.
- **K5 — diff-ability.** The scenario and the materialized soft config are data files (JSON /
  markdown — one place to change, diff-able, versioned), never code; the node→desk map stays the
  imported `DESK_LABELS` config table.

### The six lenses, predictively

1. **Criterion match** — `ORCHESTRATION_SURFACE` declares scenario/patterns/materialize/trace/
   return/guard each with the criterion AS WRITTEN and its citation; every selftest names its
   criterion in its docstring.
2. **Invariant end-to-end** — whole-run artifacts, never per call: the five whole walks (the four
   patterns + the cycle) run end-to-end through the live mode; the hand-off chain threads one
   record's payload_ref into the next prompt across the whole walk (G receives the seed's ref,
   each later desk the previous fenced digest); the restart test compares whole ledger + trail
   bytes across the full walk.
3. **Absence vs validity** — absent scenario, empty scenario, absent materialized cell, empty
   materialized file (sha256 of empty `e3b0c44298fc…` cited), absent agent (`agent_not_found`),
   absent socket (outage): every absence reads absent/INCONCLUSIVE with the reason, never valid.
4. **Encoding** — `∞0′ → ‖` rides the scenario's seed ref and system overrides byte-verbatim into
   the emitted SYSTEM.md; the V slot content carries the needle (the pinned fixture's
   needle-bearing slot fiction); the boot line carries the encoding probe verbatim; every file
   read is binary-only (no text-mode byte seeks).
5. **Cold restart** — a walk split across TWO fresh python processes (the second re-planning,
   re-materializing and continuing from the ledger + trail alone, never re-prompting the steps
   already recorded) equals the uninterrupted run's ledger AND trail bytes; a second materialize
   re-emits byte-identical cells.
6. **Blind tool** — an unavailable live socket holds outage for every desk turn with ZERO fenced
   records; an unconstituted desk holds blocked `agent_not_found` with zero fenced records for
   that desk; both end INCONCLUSIVE — never clean, never a fixture stand-in. A boot state read
   against an absent socket is carried `{"status": "absent"}` — never fabricated.

## 3. D14 divergence log — everything this artifact adds beyond the source

Per Appendix D's own jacket: declared *derivative* · visibly separate from the decoding · adds
**no** L1 symbol, **no** decoding operation, **no** sixth corruption code · alters no invariant
line. **Summary: orchestration adds three interface layers ON the attested rounds — the scenario
(the word + signed paths as data), the sign-walk (patterns derived from the signs), and the
materializer (the write-path, whose defaults are the imported P4b bytes + the bridge's declared
model). The herdr dialect, the D.12 checks, the desk grammar, the descent and the bridge's live
mode + softconfig read-path remain the imported ones; the record bytes are B2/B4's conventions.**
One declared load-anchor note: the bridge's and B3's contract files resolve their sibling imports
inside their own round directories, so — exactly as the bridge reads B3 from B3's canonical round
("the staged bytes are identical — the sha pins below are the contract either way") — this round
reads the bridge's four files from `rounds/bridge/authored/` and B3's two from
`rounds/R04-B3/authored/`, pinned against the staged `./predecessors/` bytes (verified identical).

| # | Addition | Anchor | Resolution |
|---|---|---|---|
| D-1 | The scenario schema (`word.py`): `{word, seed {address, ref, bound?}, paths [{from, to, path}], nodes?, loop?}` — the word over {S,G,Q,P,V} + the signed paths as DATA; decode + validate against the imported Grammar (COURSE alphabet, B3's path validator, `path_between` normalization); the no-topology-enum scan (pattern/topology/shape keys refused) | Commission C1/C2, H-ORCH-2; D.3/D.5/D.6 quoted verbatim | Data layer, provisional until Amihai touches it (H-ORCH-2); no new decoding, no new symbol |
| D-2 | The sign-walk (`navigate.py`): the plan (loop expansion included — append until the seed's declared bound; an unbounded loop refuses to start, D.2), the pattern derivation from the (k, m) signs alone (loop > sequence > parallel > custom, declared data), the per-step D.12 check (imported conformance) in B4's order (pre-check before the record lands, desk-fidelity FAIL holds), the centre-guard refusal of a non-seed S visit before any byte, and the no-∞0′-V REFUSAL (seal line 8 — B3's GS-VOID precedent: REFUSED dominates) | Commission C2/C6; D.6/D.2/D.3 quoted; B4's guard policy carried | Interface layer; REFUSED + hold bytes are B4's hold surface extended with `no-∞0′` |
| D-3 | The materializer (`materialize.py`): the four-file cell (SYSTEM.md / .pi/settings.json / skills/SKILL.md / tools/tool-surface.md); defaults = the imported PHASE bytes + `DECLARED_MODEL` + `["read","grep","bash"]` + scenario general tools; `GENERAL_TOOLS` (search/write-doc/write-code/activate — declarations, never executions, H-ORCH-3); the read-back verifier (`read_materialized` — absent/empty/drifted INCONCLUSIVE) | Commission C3/C4, §5 table; D.1/D.10 quoted; H-ORCH-3 | Write-path data emitter — the complement of the bridge's softconfig read-path; every artifact a data file |
| D-4 | The conductor (`orchestrate.py`): the live-desk walk over the bridge's `DeskAdapter(mode="live")` + the imported instrument (label-resolve, agent.prompt, fenced read), the real-states boot read (read-only; absent socket carried honestly), the per-gate B0 records (B2's proposal shape, attempt `step:<i>`, `seed:sha256:`/`fenced:sha256:`/`hold:` payloads — the bridge's `seed_ref` imported), the B4-format trail, the run-end (audit + spend through the softconfig read path), `already`/`observe` re-arm (turn_key idempotency — never re-prompted), and the ∞0′-only completion (complete iff the final gate is V's with the ∞0′ slot) | Commission C5/C6; bridge's live mode imported; B0 format unchanged | Conductor layer; no dialect byte, no attested state, no podium path |
| D-5 | The fixture apparatus: `desk_harness.py` (the deterministic desk box on its own socket — the real dialect's fixture shape, `agent_not_found` for unconstituted desks, the absent-socket path, the omit-infinity variant), the scenario data files under `fixtures/scenarios/`, the cold-restart runner (`run_walk.py`), the new sha pins (the bridge's four + B3's two + this round's three modules) | H-ORCH-1; the bridge's fixture live-server shape; B4's fixture-fiction precedent | Test apparatus only; the live box is never written — a real agent.prompt to a live desk is the constitution's work |

## 4. Holds — H-ORCH-1 … H-ORCH-4, each with the reading this round ships

* **H-ORCH-1 (no desk is constituted in the live box).** The word-walk and the materializer are
  tested against the fixture desk harness (deterministic, no live box; the conductor resolves the
  harness's own socket through the spec). A real `agent.prompt` to a live desk is the
  constitution's work, not this round's. The centre guard refuses S/podium (zero podium prompts
  recorded by the harness).
* **H-ORCH-2 (the scenario schema is provisional).** The word + signed-path encoding is this
  round's engineering proposal, judged against the Fractal (D.3/D.5 — quoted, never paraphrased);
  it is candidate until Amihai renames or re-shapes it. Every schema constant is declared data in
  `word.py` / `ORCHESTRATION_SURFACE` — one place to change.
* **H-ORCH-3 ("activate tools" is provisional).** The materializer emits the tool DECLARATION into
  the soft layer; whether a live pi actually loads it is the constitution/run's concern — the
  materializer declares, it does not execute.
* **H-ORCH-4 (the human's gate act is untouched — carried H-B4-4).** No podium write, no
  `cell-attest` invocation, no typed word; attestation stays a TTY act. The conductor writes no
  record with state attested and no non-null attestation_ref.

## 5. Assumptions and open flags (stated, not hidden)

1. The letter-order question (H-B3-2 carried) is untouched: this round derives every address and
   every path through B3's imported zoom primitives and P4b's declared `WORD_ORDER` parameter —
   the fixture paths (`−Q`, `+·−P`, `++·−V`, …) are the grammar's own outputs under the declared
   D.2 inner-first reading; flipping the parameter is a data change, never a rewrite.
2. The flat cycle's derived pattern label is `custom` (a free composition: daughter + cousins
   steps, the return is V's slot — D.1/D.8); `sequence` names the daughter chain (zoom in =
   append, D.3), `parallel` the cousins-converging-on-a-father shape, `loop` the append-until-
   a-bound shape. The labels are the navigator's vocabulary, never the scenario's.
3. The byte-reproducibility of the restart test holds under the canonical-work-path assumption
   (carried from the bridge): the same ledger/trail/socket path strings across every process; the
   harness answers are deterministic fiction over (desk, cell, step) — clearly labelled stand-ins,
   never a claim about any live desk.
4. The seed's declared `ref` in the fixture scenarios is fixture data (`plant:sha256:…`); the
   conductor's seed record derives its own `seed:sha256:` payload through the bridge's imported
   `seed_ref` — references, never content (D12).
5. The run-end spend reads the bridge's softconfig budget defaults (absent soft config → the
   declared charges) — the constitution's soft files override them at runtime, same as the bridge.
6. The verifier's pack may bind different names than §1; the functions are the real surface, the
   names are stable and documented here.
