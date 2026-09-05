# ATTESTATION — R02 · B1 the read-only walker

*Amihai's act. The machine prepares the block and a draft sentence; **he** runs it and **he** says the
word. Nothing here is attested until he does.*

## ATTESTED — Amihai Loven, 2026-08-27, after running the block himself

His word: **"attest it"** — the sentence below, approved as written and unchanged.

> I attest that the B1 read-only walker — authored by dsh, corrected twice, and verified PASS across
> all four criteria, all four claims and all six lenses, including against my own live cell — reads
> the instrument faithfully and writes to nothing.

He ran the block on his own machine (17:00 UTC) and read the same bytes the verifier read: the
author's 24 tests `OK`; three ticks at `phase=x/attested` — his own plant — with all five desks
resolved by label; `holds appended: 0`; `gates.jsonl` still `6989a742f5…`, still one record, 611 bytes
before and after; `evidence.md` `89c2206ebafbb827…`.

## Said by him in the same act — his word, recorded, not graded

> "your default essence is that 5qln is operational language and its essence is itself as a fractal"

Recorded as **his statement of essence**, not as a build attestation and not as a finding of this
round. It stands above the round: the machine's default stance toward 5QLN, in his words.

## What it covers — with the hashes

| Artifact | Lines | sha256 | The verdict it rests on |
|---|---|---|---|
| `authored/instrument.py` | 528 | `c511a4840e464b304e7f8de7b1d89db707d0048356d23153eed7844192aeeb3b` | K1 · C3 · C4 — read-only allowlist, labels as data, reconnect by label |
| `authored/walker.py` | 489 | `5889160a15c5bc6949c6cd65726aeb609d4ca54efa3f2702229da5a675a002e9` | C1 · C2 · K2 — the cycle from polling, one hold per episode, phase from the ledger alone |
| `authored/dialects.py` | 171 | `9ebc6d314bd265e5be14c9c22fb47a4b80f4fabab5c4a46dd3f9f1ca0e6a4208` | K3 · K4 — four dialects to one BLOCKED, never an attestation |
| `authored/selftest.py` | 1102 | `1fff9746950f3ce0735b404b4505add8b6819f53755cfc26d0d400443a619421` | executed here: `Ran 24 tests … OK` |
| `authored/phase-card.md` | 314 | `aeaa00fc0e929f279b23d26f49626221166112d5ea58faad7ce51c14b61360ca` | binding map · predictions · holds H-2…H-8 |
| `evidence.md` | 256 | `89c2206ebafbb827ba25825a72d1d0e2acaeb54d1a3d72463ca85294f44a88e0` | **PASS 14/14**, 5.01 s, plus the live tier |

Commission `af54b3de92ce9f12…` · corrections `fdad7e182f3532d9…` and `e9b06394ca5d8d53…` (2 of 2).

## His block (numbered, ≤6 commands, copy-paste, iPad-safe)

What it does, in one clause: **it runs the walker against his own live cell and shows that his plant
and his ledger are untouched.**

```
1) bash /home/deploy/the-cell/rounds/R02-B1/verify-live.sh

2) sha256sum /home/deploy/the-cell/rounds/R02-B1/evidence.md
```

Step 1 already passed on the Hermes side twice (16:49 and 16:52 UTC). What he should see: the author's
24 tests `OK`; three ticks each reading `phase=x/attested` — **his** plant — and all five desks resolved
by label (`S(podium)@w8:p2`, `G(G)@w8:p3 idle`, `Q`, `P`, `V` `unknown`); `holds appended: 0`; and the
same ledger hash `6989a742f5…` with `1` record before and after. Step 2 must print
`89c2206ebafbb827…`. He confirms; he does not debug.

## Why this round writes no ledger record

R01's attestation *was* a ledger record because his plant is the chain's first record. B1 is a
**reader**: it advances no gate, and no gate was reached. Writing a record here would be the machine
moving a gate — forbidden by §4.7 and by the walker's own design. So this round's attestation is a
round attestation only: his sentence, this file, these hashes. The chain still holds exactly one
record — his.

## Status this creates

A **build attestation** — never an attestation of the contract (§0.2). R/O/E/A/L stay candidate. The
episode reading (HOLD H-7, evidence §7) is a **K-side reading** he may overrule. Pi, dsh and the cell's
MOVING axis stay **INCONCLUSIVE** — fixture-tested, not observed live (H-4/H-8). **D8 remains his and
unanswered** unless he answers it here, in his own words.

## Recorded

- his sentence, verbatim, in this file · `attestation.md` + the round committed to canon
  `5qln/5qln-herdr-plugin` · Hindsight bank `herdr` deposit · `STATE.md` ledger row closed · drift check
  re-run green.
