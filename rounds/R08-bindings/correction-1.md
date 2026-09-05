# CORRECTION 1 — R08 · the bindings (the hard↔soft link)

*Surgical. Never a rewrite request. The whole round passed C1–C8 · K1–K5 · six lenses and was
attested + deployed. This is one predicate in one file, found only at the first live activation.*

## What failed

The pi-cell extension's **registration glue** (`index.ts`) fails to load in a live pi session. The
R08 fixtures imported `src/cellctl.mjs` (the runtime) and tested *that* — they never actually loaded
`index.ts` into a pi process, so the defect passed verification and "deploy" (file-level) while the
first real activation crashed.

## The exact evidence

```
$ (S desk boot via boot.sh, extension present)
Failed to load extension: schema.description is not a function
Hint: Start without extensions using "pi -ne".
```

Root cause, verified against the installed library (not guessed): pi ships **TypeBox 1.3.7**, which
removed the fluent `.description()` chainable modifier. `index.ts` was written against TypeBox 0.x
syntax — `Type.String().description("…")`. In 1.x the description is a **constructor option**:

```
$ node --input-type=module -e 'import {Type} from "typebox";
  console.log(JSON.stringify(Type.String({description:"path"})))'
{"type":"string","description":"path"}          # 1.x: option, not method

$ node --input-type=module -e 'import {StringEnum} from "@earendil-works/pi-ai";
  console.log(JSON.stringify(StringEnum(["a","b"],{description:"the op"})))'
{"type":"string","enum":["a","b"],"description":"the op"}   # StringEnum already takes options
```

`Type.Optional` and `Type.Object` exist in 1.x unchanged, so the only broken surface is the
`.description()` chaining in `schemaFor()`.

## The narrowest true statement of the defect

`index.ts` `schemaFor()` (lines 23–41): `KIND_BUILDERS` returned a bare schema and then called
`schema.description(spec.description)` on it — a TypeBox 0.x method that does not exist in the 1.3.7
pi ships. The fix passes `{ description }` (and, for enum rows, `StringEnum(values, { description })`)
into the constructor, and removes the chaining call. Three lines change; nothing else moves.

## What is NOT being asked

- Do NOT touch `src/cellctl.mjs` (the runtime — already exercised by the fixtures, correct).
- Do NOT touch `src/tool-table.json` (DATA — the 13 studs, byte-verbatim).
- Do NOT touch the enforcement suite, the seam (`cellctl`), the podium, or the pinned
  `surface_contract`.
- The governing line is unchanged: *conduction = call `conduct`; the conductor never re-derives the
  walk.*

## The applied fix (sha256)

- before: `06fc3749e80dcf15e99cfa8da14c93a8d2cd2e4cbadff103d50c388c95b2f453` (repo / box round / deployed, all three identical)
- after:  `508ebb843d2fc8983d395dae087f29c023f53cfedaf6e29f91eeb6eb53012d46`

Verified live: S boots with the extension present and **no load error**; the pane lists `pi-cell`
alongside the built-in extension. All five desks on fresh 2026-08-31 sessions, `idle`. Enforcement
`VERDICT: PASS`. His plant untouched (`6989a742…`).

## Budget

Correction 1 of at most 2. If a third is needed → **HOLD surfaced to Amihai**, not a third attempt.
