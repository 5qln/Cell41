# Phase card — R08 · the bindings (working handle — the round's name and slot are Amihai's to name, SCOPE D4)

**Author:** dsh (`deepseek-v4-pro`, ONE authoring generation) · **Verifier:** Hermes profile `herdr`,
separately, against a pack written before it judges anything. `builder ≠ verifier`.

**This card carries PREDICTIONS ONLY — never results.** Nothing below claims that anything ran,
passed, or was verified; the author's suite (`selftest.py`) is a hypothesis set, and its outcomes
are what the verifier will recompute with its own implementation. No git, no attestation, no claim
of execution is made anywhere in this round.

---

## 1. What was authored (the deliverables map)

```
authored/
├── phase-card.md                      ← this card
├── selftest.py                        the author's suite (hypotheses, every test names its criterion/lens)
├── pi-cell/                           (1) THE CONDUCTOR BINDING — a pi extension package
│   ├── index.ts                       registration glue: TypeBox schemas generated from the table
│   ├── src/tool-table.json            DATA — the whole stud surface: 13 tools, one cellctl subcommand each
│   ├── src/cellctl.mjs                the ONE runtime: table load + argv build + one spawn + result shape
│   ├── package.json                   the "pi" package manifest (extensions → ./index.ts)
│   └── README.md
├── human-binding/                     (2) THE HUMAN BINDING — plugin actions, manifest addendum
│   ├── herdr-plugin-v4.addendum.toml  conduct·word·plan·materialize·states·trail·descent·config
│   └── README.md                      each command = cellctl + ONE subcommand, argv-only, no TTY guard
├── podium/                            (4) THE PODIUM RE-POINT — content only (H-R08-6)
│   ├── cell-podium                    read-only renderer: one cellctl trail call per refresh
│   ├── manifest-pane-repoint.toml     the replacement [[panes]] block (question.md → the trail)
│   └── README.md
├── enforcement/                       (3) THE ENFORCEMENT RECONCILIATION — the three findings re-pointed
│   ├── plugin-bin/_cell_api.py        reduced: no socket, read-only platform-CLI read verbs only
│   ├── plugin-bin/cell-attest         re-pointed: ledger through the seam contract (the pin IS the check)
│   ├── plugin-bin/cell-begin          re-pointed reads; the raise refuses honestly (see D14-3)
│   ├── plugin-bin/cell-zoom          re-pointed reads (pure read before, pure read after)
│   ├── plugin-bin/cell-on-desk-state re-pointed reads (pure recorder before and after)
│   ├── desks/{S,G,Q,P,V}/.pi/prompts/guide.md   conduction → /conduct · spawn → *deferred — D1*
│   ├── seam-declaration-extension.patch         the census/roots DATA extension (R07's "W5 extends it")
│   └── README.md
├── bricks/                            (C8) THE METHOD AS DATA — the LEGO bricks
│   ├── README.md                      the brick format: three engine-read files, never parsed by the binding
│   └── methods/sgqpv-cycle/           a CANDIDATE method (D2/D4 open): word.json + spec.json; soft.json
│                                      deliberately ABSENT (W3's act — absence reads defaults honestly)
└── fixtures/                          the commission's fixture list — see fixtures/README.md
    ├── fake_cellctl.py                deterministic 13-subcommand stand-in: absent + malformed cases,
    │                                  declared flock + turn_key emulation, invocation journal
    ├── probe.mjs                      the executable twin of the binding (imports the shipped cellctl.mjs)
    ├── build.py · desk_harness/ · enforcement/ · cold_restart/ · byte_round_trip/ · scenarios/
```

## 2. The design rationale (why it looks like this — judged against the criteria, never a pre-ordained shape)

**The tool table is DATA, and the runtime is one shared module.** `pi-cell/src/tool-table.json`
declares the whole stud surface — 13 rows, each exactly one `cellctl` subcommand, params
byte-verbatim; `pi-cell/src/cellctl.mjs` is the single executable path (table load + argv build +
ONE spawn of the seam binary + result shaping). `index.ts` is registration glue only. Three
consequences: (a) a new stud is a new table row — **zero re-authoring** (K5, C8.1); (b) the
fixture probe imports the *same* `.mjs`, so the code the tests execute **is** the code the
extension ships — C3's byte-identity is proven on the delivered artifact, not a transliteration
(lens 2); (c) nothing in the runtime can hold a sequence: there is no chaining construct at all —
the composite is `/conduct`, which is the *engine's* composite, one call away (C8.1/C8.2).

**The orchestration method is the brick — data the engine already reads.** The engine's own
composite derives the walk from the word's signs (`navigate.plan_walk`), reads the spec, and reads
the soft config. A brick (`word.json` + `spec.json` + `soft.json`) is therefore the complete
"which commands, in what order, under what soft config" — and a **new method = a new brick
directory, snapped on with zero re-authoring of the seam or the firmware** (C8.2). The binding
never opens a brick (asserted by test); each file is validated by the engine's own attested
readers. A method that closes honestly and returns a live ∞0′ *is* a brick: the run-end's
`return_question` reference becomes the next word's seed ref — the D8 learning loop is a file
write of data, and nothing in this round precludes it (C8.3). One firmware, many soft configs:
a second cell is a second brick whose spec names its own paths — no binding change (C8.4).

**Why the reconciliation re-points the consumer bins, not just the client.** Finding (i) is the
wire in `_cell_api.py`; removing the wire retires the plugin's write-by-wire path, so every
consumer bin is re-pointed in the same edit — reads re-served over the platform CLI's declared
read verbs (`workspace list` · `pane list` · `api snapshot` · `api schema`), and the one write
behind the wire (`cell-begin`'s raise: workspace.create + layout.apply) **refuses out loud**
instead of improvising a second wire. A working cell, not just a clean scan — see D14-3.

**Why the podium renderer shells `cellctl trail` instead of parsing the file.** The trail's
classification (absent/empty/ok/partial/damaged, the chain verdict, the torn tail) is engine logic;
the renderer holds none of it — one seam call per refresh, the report printed, never re-derived
(C7, the round's whole architecture: the soft layer only points at the engine). Absent trail reads
`no trail yet … INCONCLUSIVE, never a stand-in` on the glass (C6, lens 3, lens 6).

**Why the census extension exists.** R07's own seam declares the extension point: "the W5
bindings extend it — an extension not declared here = FAIL". The patch adds the new podium
renderer to the entry-point census, declares the re-pointed `cell-attest` as a seam importer (its
ledger now arrives through the pinned contract — the import IS the pin check), and declares the
`pi-cell` extension root. Data, diff-able, never logic (K5) — and it is what makes the suite read
the re-pointed world as *declared*, never hidden.

## 3. The D14 divergence log (every place this design reads the commission its own way — declared, never silent)

| # | The candidate/spec line | The design's reading | Why |
|---|---|---|---|
| D14-1 | §7: the reduced `_cell_api.py` is "read-only `snapshot`/`schema` only" | The module's surface is the **read-only verbs the platform CLI declares** — `api snapshot`, `api schema`, plus the three read-only layout helpers (`workspace list`, `pane list`, `pane get`) the consumer bins already used. No socket, no arbitrary-method path, no write verb. | The literal reading (two metadata verbs only) leaves the four consumer bins with no read transport at all and the live cell's begin/zoom/attest/hook broken at import time. C4(i)'s own wording — "reduced to its **declared read-only surface** or routed through cellctl states" — is satisfied by re-serving the module's existing read-only methods over the platform's own read verbs; the wire work now happens inside the platform binary, which is the platform, not the soft layer. |
| D14-2 | §7 lists only guide.md + `_cell_api.py` + `cell-attest` as the reconciliation | The reconciliation also re-points `cell-begin` / `cell-zoom` / `cell-on-desk-state` | They import the removed surface; leaving them broken would be a live regression. The commission's layout clause ("layout yours to design; content is what is checked") covers the extension, and C4's acceptance (zero findings) is met with them declared. |
| D14-3 | `cell-begin`'s raise was never named a finding | The re-pointed `cell-begin` keeps its read-only standing-check and **refuses the raise (exit 9)** — the raise rode the removed wire and is a layout write the soft layer may not carry | The governing line (soft layer only points at the engine) and K1 (one wire, the pinned Instrument) leave no honest path for a plugin-held layout write. The cell is already standing; re-raising was always a human's decision. |
| D14-4 | §7 names the action set but not the descent op | The `descent` action is one fixed gesture: `path-between --from "" --to V` — the signed path from the centre to Value (verified output: `−V`) | Plugin actions are fixed argv (the manual: no runtime args); the op is manifest DATA, changeable in one place (K5). The conductor's `descent` tool takes all ops as arguments. |
| D14-5 | D2 open — no acceptance word | The scenario-bearing actions point at declared data paths (`state/word.json`, `state/decoded-scenario.json`) that are **absent until D2 lands** — the actions read `absent` honestly | Never a fixture stand-in; the engine refuses nothing, the files are just not there yet (C6, lens 3). When Amihai plants the word, it appears at the declared path or the manifest data changes — either way, zero re-authoring. |
| D14-6 | C4(ii): "the spawn line is moved under a *deferred — D1* fence" | The fenced §5 keeps the 2026-08-30 operational notes (cwd-only, never pass the constitution on the command line) **without the spawn tool's name and without any imperative** | H-R08-3 says re-fence, never present as the walk; D8 asks what remains of the improvised tooling. The knowledge survives as recorded data for D1's decision; the authority is gone from the soft layer. |
| D14-7 | §6: no re-authoring of the seam | The census/roots patch edits R07's `surface_contract.py` **declarations only** | The seam's own comment anticipates it ("the W5 bindings extend it — an extension not declared here = FAIL"); K5 designates the declarations as data, one place to change. No seam logic, no engine module, no pin table touched. |
| D14-8 | The suite "names the three missing links" (verified-facts) | The current enforce.py patterns (hard-coded in the attested file, untouched this round) do **not** match the spawn-tool literal — finding ii is therefore re-pointed **at its source** (the guides), and the author's suite carries its own spawn-authority scan to prove the flip | Honest mechanical observation (re-observed while authoring). The declaration data already carries the intent; wiring the scanner to consume `L1_DECLARATION.forbidden_patterns` is a small future enforcement edit, recommended here, not performed (the file is attested). |
| D14-9 | H-R08-6: skin is a later round | The pane title moves to "THE TRAIL" alongside the content re-point; everything else (theme/sidebar/toasts/layout of the question display) is untouched | A truthful title is content, not skin; the visual layer stays for the interface round. |
| D14-10 | §7: env-only config `CELLCTL_BIN`, `HERDR_BIN` | `HERDR_BIN` is declared in the config surface and read by **no code path** — the package's only subprocess is `cellctl` (K1) | Declared-for-parity is honest only if it says so; it says so in the module header and the README. (The reduced `_cell_api.py`, the plugin's own module, does read `HERDR_BIN` for its platform-CLI reads — that is the reconciliation, not the binding.) |

## 4. The predictions (hypotheses — what the verifier will recompute, criterion by criterion)

- **P-C1** — each of the 13 pi tools and each of the 8 plugin actions shells to **exactly one**
  `cellctl` subcommand: the probe's journal will read one entry per invocation, argv naming exactly
  one subcommand; the addendum's 8 commands will each name `cellctl` + one subcommand.
- **P-C2** — no tool/action wraps any write verb; `/states` is the only desk-facing surface; an
  absent socket reads `{"status":"absent"}` through the binding's argv — never a stand-in.
- **P-C3** — `conduct --plan-only` through the binding is byte-identical to the direct call, over
  both the fixture oracle and the REAL attested `cellctl` (the seam's own plan-equivalence proof
  re-proven through the binding's argv).
- **P-C4** — the enforcement legs over the pre fixture world FAIL with the three findings'
  shapes (socket tokens; direct engine import; spawn-authority line) and read **zero findings**
  only after the authored re-points are applied — the census extension declares, never hides.
- **P-C5** — the run lock is inherited by construction (no second lock path exists in any binding
  source); a concurrent second `/conduct` BLOCKS — proven through the fixture fake's declared
  lock emulation (first run `complete`, second `already-complete`, never interleaved) and the
  REAL seam's re-arm-from-disk (`already-complete` on the second process).
- **P-C6** — absent cellctl, absent files, empty files (the sha256 of empty named), malformed
  inputs, and a null-scenario spec all read INCONCLUSIVE with a reason — never clean, never a
  substituted value; the podium's glass says `no trail yet … INCONCLUSIVE` while the trail is
  absent.
- **P-C7** — no soft-layer file imports a pinned engine module directly, except the re-pointed
  `cell-attest` importing `surface_contract` — the declared seam importer of the census extension;
  the binding sources contain no socket code and no dialect code.
- **P-C8** — 13 independent studs with no sequence field, no chaining construct, no hard-coded
  cell/scenario/desk-order in the binding; the method is the brick (data the engine reads — the
  engine's own decoder accepts the brick word, the spec validates under the declared schema, the
  absent soft.json reads defaults); a new method is a new brick directory with zero re-authoring;
  the swarm is reachable with zero firmware change (nothing in the binding names a cell).
- **P-K1** — the extension/actions add no network, no LLM, no wall-clock in logic; the only
  subprocess is the seam binary; the only socket client on the box remains the pinned Instrument
  (the plugin's reads ride the platform CLI's read verbs, inside the platform binary).
- **P-K2** — bytes forwarded untouched: no `⋂→∩`, no `′→'`, no spacing collapse — the needle
  `∞0′ → ‖` rides tool args, inline JSON, and file paths byte-verbatim, and a needle smuggled
  into a field whose notation excludes it is REFUSED, never normalised into validity.
- **P-K3** — no authenticity verdict anywhere: HC-1/HC-2 stay INCONCLUSIVE by design; nothing in
  the binding claims arrival at ∞0 (the fake's `check` reports PASS only, and INCONCLUSIVE never
  reads clean).
- **P-K4** — the B2 guards hold: no `herdr_start_agent`-equivalent authority is added (the
  guides' spawn line is fenced *deferred — D1*); the engine's `WRITE_METHODS` stay frozen; the
  centre guard is the engine's, untouched.
- **P-K5** — the method is a data file the engine reads, diff-able and versioned: the tool table,
  the addendum's data constants, the brick files, and the census extension are all data, one
  place to change; the binding's code reads none of the method.

**The six lenses, predicted:**

1. *Criterion match* — every selftest names its criterion in its first docstring line and measures
   the criterion as written, not a neighbour of it.
2. *Invariant end-to-end* — the binding behaves identically across a whole run: the probe's
   per-call result is the raw cellctl bytes every time; a full conducted cycle through the
   binding's argv over the fixture harness completes (`complete`, `ended_in ∞0′`) with the same
   shape as the direct CLI (predicted, never claimed).
3. *Absence vs validity* — absent cellctl / absent files / empty files / a null-scenario spec
   never read valid; the sha256 of empty is named.
4. *Encoding* — the needle rides every string field (tool args, action argv, inline JSON, file
   paths, the brick seed ref, the podium's rendered signal) byte-verbatim; files are read binary
   in the fixture oracle; no text-mode byte seek exists in the binding.
5. *Cold restart* — a NEW process re-arms from disk alone: fresh probe processes land identical
   plan bytes; the restart runner drives the second process; the second `/conduct` honours the
   run lock (blocks, then observes).
6. *Blind tool* — an unavailable socket reads `absent`; an unconstituted desk holds
   `agent_not_found` (the trail's hold lines name it) with zero fenced stand-in answers; the
   podium reports INCONCLUSIVE, never clean.

## 5. The holds — carried, never guessed

- **H-R08-1** — no live `agent.prompt` was sent anywhere: every engine turn went to the pinned
  fixture desk harness on its own socket; the live ledger/trail were never written.
- **H-R08-2** — `pi-cell` is a candidate package name; all command names are candidates (D4).
- **H-R08-3** — no spawn authority added; the desks' spawn line is fenced *deferred — D1*;
  `WRITE_METHODS` untouched.
- **H-R08-4** — the `pi-herdr` package is consumed as-is: the new package is a sibling and does
  not depend on its internals (the sibling's spawn pattern was read as precedent only).
- **H-R08-5** — G/Q/P/V surfaces are the constitution's act: the brick ships no soft.json; the
  engine's `no-surface-announced` holds are never papered over.
- **H-R08-6** — the podium re-point is content-only: the theme/sidebar/toasts skin stays a later
  round.

## 6. Residual risks the verifier is invited to probe (never hidden)

1. **The pi runtime's jiti** — the extension's TS→`.mjs` import was smoke-tested against the
   harness's jiti 2.7.0 (loads clean, needle rides argv); the pi runtime's bundled jiti is the
   same loader family but was not exercised with the full extension (the pi-coupled part —
   typebox/StringEnum — cannot run without pi's bundled dependencies, and no pi session was
   started this round: H-R08-1).
2. **The platform CLI read verbs** — `workspace list` / `pane list` / `api snapshot` / `api
   schema` were verified present on the live herdr 0.8.2 binary and their output shapes read from
   the live session; the reduced `_cell_api.py` pins itself to those four verbs and refuses
   anything else.
3. **The census patch's application** — the patch hunks were matched against the live
   `surface_contract.py` (data anchors verified); application is the human's, and the fixture
   world already mirrors the extended manifest, so the suite's flip is provable with or without
   the live application.
4. **Enforce.py's hard-coded pattern lists** — see D14-8: the spawn-authority literal is not in
   the current scanner's patterns; the re-point removes the authority at the source, and the
   author's suite carries its own scan. Recommended follow-up: consume
   `L1_DECLARATION.forbidden_patterns` in the next enforcement edit.
