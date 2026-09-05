# ATTESTATION — R01 · B0 the ledger and the record

*Amihai's act. The machine prepares the block and the sentence; **he** runs it and **he** types it.
`cell-attest` refuses non-TTY with RC=4 — that refusal is the seal working, never a bug to route
around.*

## What he is attesting (one sentence, prepared for him, editable)

> I attest that the B0 ledger and record — authored by dsh and verified PASS across all six
> criteria and all six lenses — is the trace's foundation, and that this plant is its first
> record: gate **x**, the codex Start, my word.

## What it covers — with the hash

| Artifact | sha256 | Verdict it rests on |
|---|---|---|
| `authored/fractal_ledger.py` (1064 lines) | `b291e65967e0d1f98205a9bd612507fa788ea4f9aa99e5d6b8fa5f366895546d` | `evidence.md` — **PASS** 12/12 (C1–C4, K1–K2, six lenses), 21.9 s |
| `authored/selftest.py` (503 lines) | `59b5103d84fd4790e4be9189dacf8329b488f8b0a9f2e969e5b4adaa1198fc6c` | lens 1 (timed `verify`) |
| `authored/phase-card.md` (181 lines) | `eb548344fec03dfde6c2c1f959b8eb9c6fb812662b166665b5e66551e24b363c` | adapter mapping + predictions + holds |
| `plugin/bin/cell-attest` (v3 wiring) | `d1346b484932cb2533b70b952b3fd670e9feec3d763cf3e8234e4052686cfe00` | seal RC=4 non-TTY · PTY plant test chain-verified |
| box ledger module `the-cell/ledger/fractal_ledger.py` | `b291e65967e0d1f98205a9bd612507fa788ea4f9aa99e5d6b8fa5f366895546d` | byte-identical to authored |

## His block (numbered, ≤6 commands, copy-paste, iPad-safe)

```
1) /home/deploy/the-cell/plugin/bin/cell-attest S
   → shows:  position S → gate x   address ε (root)
   → type your word at the  attest S >  prompt, Enter. Empty line aborts, records nothing.

2) python3 - <<'PY'
import sys; sys.path.insert(0, '/home/deploy/the-cell/ledger')
import fractal_ledger
r = fractal_ledger.LedgerVerifier('/home/deploy/the-cell/state/gates.jsonl').verify()
print('records', r.count, 'head', r.head[:16], 'gate', r.records[0]['gate'], 'prev', r.records[0]['prev_hash'])
PY

3) sha256sum /home/deploy/the-cell/state/gates.jsonl
```

Every command here already passed on the Hermes side (the plant command was run in a real PTY
against a throwaway state dir and the resulting chain verified from GENESIS by a fresh process).
He confirms; he does not debug.

## Status this creates

A **build attestation** — never an attestation of the contract (§0.2). R/O/E/A/L stay candidate
regardless of build progress. D8 remains his and unanswered unless he answers it here in his own
words. The desk→gate map `S:x G:y Q:z P:a V:b` is his word, recorded as DECIDED, not attested.

## Recorded

- `attestation.md` committed with the sha256 above · Hindsight bank `herdr` deposit · `STATE.md`
  ledger row closed.
