# EVIDENCE — R05 · B4 — the unattended run (the product's core claim + the observability deliverable).

*Written by `deliverable-audit` (the verifier side), by **running** the authored artifact. This file is the only place where "it works" may be said, and only next to the command that proved it. "Looks correct" is not a verdict here.*

## Environment

- when: `2026-08-29T15:40:23Z` · harness `deliverable-audit 1.0.0`
- host: `918576e4db0d68` · Linux-6.12.105-fly-x86_64-with-glibc2.41 · python `3.13.5`
- artifact under test: `/opt/data/tmp/proving-b4/rounds/R05-B4/authored/run.py`
- artifact sha256: `5a798bbda07d037879a359e981c91f24962b86f48c285d03c87052e1b996896f`
- criteria spec: `/opt/data/tools/deliverable-audit/specs/b4-unattended-run.json`
- scratch (ledgers written during the run): `/tmp/deliverable-audit-5u2_b58_`
- criteria quoted from: The criteria are quoted from rounds/R05-B4/commission.md §2 (sha256 fe61d69b974be4aec84fef164c5be818040beaee9473483963857a00a0473a22, 15,659 B, staged on the box 2026-08-29), which in turn quotes PRD.md §B4/§5.5/§10.3 and PLAN-ADDENDUM §B. The held sources are the Codex (page sha ccad26dd…) and Appendix D (page sha a49e9413…). The K-claims are quoted from commission §5/§7 and the phase-card §3 (D14 divergence log).
- total runtime: **6.93 s**  ✅ under the 60 s T0 bar

## Per-criterion result (§9 as written)

| ID | Criterion (verbatim) | Command | Raw output (decisive lines) | Verdict |
|---|---|---|---|---|
| C1 | Build: holds accumulate instead of stopping the run… — §10.3: model/provider outage → hold the gate, keep other cells moving. A held gate does not halt the conductor; the hold is surfaced; the machine never resolves a hold (T-O5-02). | — | hold run stalled with two holds (blocked+outage) still held-pending; only the plant is attested; no hold auto-resolved; run-end written | **PASS** |
| C2 | Build: TENTATIVE seeding of the next S… — §5.5: tentative: true is temporal, never epistemic. A tentative node is non-data: no heuristic may promote it, no downstream gate may consume it as evidence, and it never reaches the podium. | — | every machine-posed seed is tentative:true, corruption L2, held-pending, attestation_ref null, payload_ref seed:sha256:…; the plant is the only non-tentative S | **PASS** |
| C3 | Build: restart re-arm… — Done when: a kill -9 mid-run restarts with no duplicate/skipped gate. A fresh process reads the ledger alone and reconstructs the exact next action. | — | a fresh process re-armed from the ledger alone: byte-identical to the uninterrupted reference, no duplicate/skipped gate | **PASS** |
| C4 | Build: budget hold (a spend ceiling surfaces as a hold, never a silent kill)… — Done when: a budget stop appears as a held gate. Spend is accounted before each turn. | — | ceiling reached → a held-pending budget-ceiling gate recorded and the run stopped cleanly (budget-held); spend 16200 ≤ 19000, never a silent kill | **PASS** |
| C5 | Done when: … no tentative node is ever consumed by a downstream gate (dependency audit). Any gate whose payload_ref chain reaches a tentative:true record is a FAIL (T-R5-02). | — | dependency audit PASS over the lawful run, FAIL (naming the one consuming record) over the consumed variant, INCONCLUSIVE over nothing | **PASS** |
| C6 | Done when: ≥ 20 cycles with zero human keystrokes. The only attested record is the plant; no input() call, no cell-attest invocation, no podium write. | — | 20 completed cycles with zero keystrokes; the plant is the only attested record; no input(), no cell-attest in the run source | **PASS** |
| C7 | R05 = B4 is now also the observability deliverable: a readable trail while it runs, because reception happens by being observable. The trail records what the context decoded to, never the context itself (D12). | — | trail is append-only + hash-chained (ok/ok), readable mid-run, decoding-not-transcript, torn tail discarded (partial), mid-file mutation fails closed (damaged), absent reads absent; two trails never merged | **PASS** |

## Claimed capabilities (asserted by the author, measured here)

| ID | Criterion (verbatim) | Command | Raw output (decisive lines) | Verdict |
|---|---|---|---|---|
| K1 | Deterministic and stdlib-only (commission §1). The conductor core is pure logic; the LLM lives at the desk, never in the run mechanics. | — | run.py/trail.py/cost.py import only the stdlib and the sanctioned predecessor modules (surface_contract, fractal_ledger, fixtures) | **PASS** |
| K2 | No byte normalisation (⋂→∩ is renaming). The two enumerated ∞0′/∞0' forms are accepted as data, never folded into one. | — | both ∞0′ and ∞0' glyph forms are enumerated as data, never folded | **PASS** |
| K3 | Every decoding and compiling loyal to 5qln.com/codex (D14). Anything added beyond the source is declared derivative, visibly separate, no new L1 symbol, no new decoding operation, no sixth corruption code. | — | the phase card carries a D14 divergence log declaring no new L1 symbol / decoding operation / corruption code | **PASS** |
| K4 | No authenticity verdict (commission §6). The run has no write path to state attested and never types the human's word. | — | across the whole run only the plant is attested; no machine record carries a non-null attestation_ref | **PASS** |
| K5 | No write path to the podium (PRD §2.1, T-R3-02). The run never writes nodes/*/question.md, never invokes cell-attest, never prompts the centre S. | — | no write path to the podium (question.md), no cell-attest, no input() anywhere in the run modules | **PASS** |

`INCONCLUSIVE` is a legitimate verdict. A blind tool must never report clean.

## Six-lens pass

| Lens | Applied how | Result |
|---|---|---|
| L1 criterion match — one quantity per criterion, no blind probe | 7 criteria + 5 claims, each a distinct measured quantity, every probe registered | **PASS** |
| L2 invariant end-to-end — one pass over the whole list | a consumed tentative anywhere in the list fails the WHOLE list, never a per-record quirk | **PASS** |
| L3 absence vs validity | absent→absent, empty→empty (sha e3b0c44298fc…), never a valid decode | **PASS** |
| L4 encoding | ∞0′ → ‖ survived the append→read round-trip byte-exact | **PASS** |
| L5 cold restart — the second process rebuilds from disk alone | C3's fresh-process re-arm held byte-identical, no duplicate/skipped gate | **PASS** |
| L6 blind tool — nothing unobservable reads clean | empty ledger audits INCONCLUSIVE; the run refuses to start from nothing (BootError); no desk is constituted (H-B4-1) | **PASS** |

## Timings (T0 mechanical)

| Step | Seconds |
|---|---|
| C1 holds accumulate instead of stopping the run — a held gate never halts the conductor, is never retried, never auto-resolved | 0.68 |
| C2 TENTATIVE seeding of the next S — tentative:true, corruption L2, never promoted, never reaches the podium | 4.56 |
| C3 restart re-arm from the ledger alone — a kill -9 mid-run re-arms with no duplicate/skipped gate | 1.20 |
| C4 budget hold — a spend ceiling surfaces as a held gate, never a silent kill, never an overspend | 0.23 |
| C5 no tentative node consumed by a downstream gate — the dependency audit | 0.00 |
| C6 ≥ 20 cycles with zero human keystrokes | 0.06 |
| C7 the observability deliverable — a readable trail while it runs, decoding-not-transcript, two trails never merged | 0.06 |
| K1 stdlib-only, deterministic, no LLM in the run mechanics | 0.02 |
| K2 no byte normalisation — the ∞0′/∞0' glyphs are enumerated, never folded | 0.00 |
| K3 D14 loyalty + the divergence log — no new L1 symbol, decoding operation, or sixth corruption code | 0.00 |
| K4 no authenticity verdict — the run never writes state:attested, never sets a machine attestation_ref | 0.01 |
| K5 no write path to the podium — no question.md write, no cell-attest, no input() | 0.04 |
| L1 criterion match — one quantity per criterion, no blind probe | 0.00 |
| L2 invariant end-to-end — one pass over the whole list | 0.00 |
| L3 absence vs validity | 0.00 |
| L4 encoding | 0.00 |
| L5 cold restart — the second process rebuilds from disk alone | 0.00 |
| L6 blind tool — nothing unobservable reads clean | 0.00 |
| **total** | **6.93** |

## Verdict

**PASS** — PASS 18

A FAIL is not a rewrite request: it is one correction, surgical, with the exact command, the raw output and the bytes that differ.
