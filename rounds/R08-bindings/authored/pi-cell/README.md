# pi-cell — the conductor binding (candidate package name, D4 — his to name)

The pi extension package that registers the thirteen `cellctl` subcommands as pi slash
tools — **each stud is one thin shell to the seam, one `cellctl` call each** (C1, C3, C7).
This is the conductor S's surface: *conduction = call `/conduct`; the conductor never
re-derives the walk.*

## Layout

| file | role |
|---|---|
| `index.ts` | the pi entry point — registration glue only: TypeBox schemas generated from the table, every invocation forwarded to the shared runtime |
| `src/tool-table.json` | **DATA** — the whole stud surface: 13 tools, each exactly one `cellctl` subcommand, params byte-verbatim (a new stud = a new row, zero re-authoring; K5) |
| `src/cellctl.mjs` | the ONE executable runtime: table load + argv build + one spawn of the seam binary + result shaping. Pure node ESM — the fixture probe imports this same module, so the code the tests execute IS the code the extension runs |

## Config — env-only (the declared surface)

* `CELLCTL_BIN` — the seam binary; default `/home/deploy/the-cell/rounds/R07-integration/authored/cellctl` (R07, attested).
* `HERDR_BIN` — declared for parity with the sibling package's env-only pattern; **read by no code path** (this package never shells to the platform CLI — its only subprocess is `cellctl`, K1).

## What the binding refuses to be (C1, C2, C5, C7, C8)

* no socket code, no record-writing, no ledger/trail logic, no engine import — the seam carries all of that;
* the write side is never exposed (no write verb exists in the table; `/states` is the only desk-facing read);
* no orchestration *sequence* — each tool is an independent, composable stud; the orchestration **method** (which commands, in what order, under what soft config) is **data the engine reads** (the brick: scenario + spec + soft config, see `../bricks/`);
* the run lock is inherited by construction: the binding adds no second path around the seam's flock (C5);
* exit 0 = the declared success status; any other exit is returned as an error carrying the raw report — INCONCLUSIVE never reads clean, absent `cellctl` reads the same honest shape (C6);
* argv items ride as separate strings, byte-for-byte — `∞0′ → ‖` survives untouched, nothing is re-encoded (K2, lens 4).

## Install (data — the declared location)

`desks/S/.pi/extensions/pi-cell/` — the S desk's project extension dir (the manual's
`.pi/extensions/` convention; pi discovers `*/index.ts`). Restart S's pi session or `/reload`.
The location is declared data in the enforcement reconciliation's seam-declaration extension
(`../enforcement/seam-declaration-extension.patch`).

## The swarm (C8.4)

Nothing here names a cell, a desk, a scenario, or an orchestration pattern: the binary path is
env data and every tool takes its paths as arguments. One firmware, many soft configs — a second
cell is a second spec/scenario/soft brick, reachable with zero firmware change and zero change
to this package.
