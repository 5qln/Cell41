# EVIDENCE — R04 · B3 — the descent (zoom). Byte-exact axis inheritance · address append/strip + signed-path split · guard pass at every depth · return criterion = artifact + genuine ∞0′ · five quantum-jump commitments (structural, never implemented).

*Written by `deliverable-audit` (the verifier side), by **running** the authored artifact. This file is the only place where "it works" may be said, and only next to the command that proved it. "Looks correct" is not a verdict here.*

## Environment

- when: `2026-08-29T11:44:07Z` · harness `deliverable-audit 1.0.0`
- host: `918576e4db0d68` · Linux-6.12.105-fly-x86_64-with-glibc2.41 · python `3.13.5`
- artifact under test: `/opt/data/tmp/proving-b3/rounds/R04-B3/authored/descent.py`
- artifact sha256: `ccf33cbf5d2910393076eb076030475721b80229a8fcbeb04e4854043515828e`
- criteria spec: `/opt/data/tools/deliverable-audit/specs/b3-descent.json`
- scratch (ledgers written during the run): `/tmp/deliverable-audit-4k79fakg`
- criteria quoted from: The criteria are quoted from rounds/R04-B3/commission.md §2 (sha256 1c897c718e4edc6fc4381c9d4d752fe6f241e1a68ebf8f965b6427a444e693a6, 9,275 B, staged on the box 2026-08-29), which in turn quotes PRD.md §B3/§5.3/§5.4/§5.5 and PLAN-ADDENDUM §C. The held sources are the Codex (page sha ccad26dd…, extraction e5f0c738…) and Appendix D (page sha a49e9413…, extraction 6bb28c37…). The K-claims are quoted from commission §6 (prohibitions) and phase-card §4 (D14 divergence log) — B3's commission carries criteria C1–C7 only; the K-claims are the binding prohibitions, promoted to measured claims so they are not asserted in prose.
- total runtime: **0.79 s**  ✅ under the 60 s T0 bar

## Per-criterion result (§9 as written)

| ID | Criterion (verbatim) | Command | Raw output (decisive lines) | Verdict |
|---|---|---|---|---|
| C1 | byte-exact axis inheritance… a 3-deep descent shows byte-identical axis.field from root to leaf; a manufactured field change yields MOVING and a stop-and-surface. | — | handoff byte-exact + never-empty; MOVING/recast/STASIS computed; 3-deep field byte-identical; manufactured change → MOVING + stop | **PASS** |
| C2 | Word over {S,G,Q,P,V} … Zoom in = append a letter; zoom out = strip. Addressing is derived, never stored… The signed path (+^k · −x₁…−x_m, AR3) gets its own field in B3; address keeps the bare node word… the validator rejects -P-Q-P and +-G. | — | append/strip round-trip + parameter flip; address derived never stored; signed path split with ASCII-hyphen rejection | **PASS** |
| C3 | Guard pass at every node and depth: L1 L2 L3 L4 V∅. No V without ∞0′ (R6). — a V with no ∞0′ is refused. | — | guard ran at every depth with the five GS-* items; the leaf's V carries ∞0′ (PASS) and the seed is honestly flagged L2; a V with no ∞0′ is refused as V∅ | **PASS** |
| C4 | return criterion = artifact + genuine ∞0′. | — | returned = attested V + artifact + ∞0′ (byte facts, never content); V-without-∞0′ refused; unattested V held | **PASS** |
| C5 | tentative: true is temporal, never epistemic. A tentative node is non-data: no heuristic may promote it, no downstream gate may consume it as evidence, and it never reaches the podium. Only a human act converts or discards it. | — | tentative seed consumed by a downstream gate → refused; no heuristic promotes tentative; no podium write path | **PASS** |
| C6 | gate-fails-to-lock → child node + address append + arrangement. | — | a locked gate is no-trigger (no descent material); a failing gate descends to a child with an appended address and a seated arrangement | **PASS** |
| C7 | no hard-coded maximum depth · the address alphabet stays extensible so a jump marker can exist beside {S,G,Q,P,V} · the loop stops on resources, never on semantic completion · nothing treats descent as narrowing … · no code assumes the current cell is the root. | — | no depth constant + five-deep walk completes; alphabet is data; the loop stops on budget (resources); no size comparison prunes a child | **PASS** |

## Claimed capabilities (asserted by the author, measured here)

| ID | Criterion (verbatim) | Command | Raw output (decisive lines) | Verdict |
|---|---|---|---|---|
| K1 | Deterministic and stdlib-only (commission §6: no gate semantics re-implemented outside fractal-engine, no new L1 symbol, no new decoding operation). The module imports nothing outside the standard library plus the sanctioned predecessor modules, each loaded by path and sha-pinned. | — | descent + surface_contract import stdlib + sanctioned predecessors only | **PASS** |
| K2 | No byte normalisation (⋂→∩ is renaming). The descent operator is U+2212 −; ASCII - is not part of the notation and no byte normalisation maps it — -P-Q-P and +-G are rejected. | — | ASCII-hyphen signed paths rejected; no L1-glyph normalisation | **PASS** |
| K3 | every decoding and compiling loyal to 5qln.com/codex (D14). Anything this artifact adds that is not in the source is declared in a divergence log: derivative, visibly separate, no new L1 symbol, no new decoding operation, no sixth corruption code. | — | divergence log present with the Appendix-D jacket; the five sealed codes only | **PASS** |
| K4 | No authenticity verdict (commission §6). The engine never writes state: attested and never judges genuineness — an unattested V is held, presence is reported, genuineness is never claimed. | — | no state: attested write, no genuineness verdict — the human's click is the only authority | **PASS** |
| K5 | No write path to the podium (PRD §2.1, T-R3-02). Addressing is derived, never stored as a separate identity — the node record carries no address field, and the descent has no write path to question.md. | — | address field refused in the record; no podium write path | **PASS** |

`INCONCLUSIVE` is a legitimate verdict. A blind tool must never report clean.

## Six-lens pass

| Lens | Applied how | Result |
|---|---|---|
| L1 criterion match — the suite measures, not prose | selftest exercises 11 measurement markers | **PASS** |
| L2 invariant end-to-end — one field + a verifying chain | field byte-identical across 4 nodes; chain verifies (14 records) | **PASS** |
| L3 absence vs validity | missing + empty node read absent; empty field refused | **PASS** |
| L4 encoding — ∞0′ → ‖ survives every field | stress anchor round-trips byte-exact; U+2212 operator intact | **PASS** |
| L5 cold restart — a new process rebuilds the same bytes | fresh process digest matches (617afe39dc2d…) | **PASS** |
| L6 blind tool — unobservable reads INCONCLUSIVE | bare node + worldless walk both refuse to fabricate a clean | **PASS** |

## Timings (T0 mechanical)

| Step | Seconds |
|---|---|
| C1 byte-exact axis inheritance + MOVING dominates (the §5.4 verdicts) | 0.07 |
| C2 address append/strip + the signed path split (derived, never stored) | 0.00 |
| C3 guard pass at every depth — L1 L2 L3 L4 V∅ · no V without ∞0′ | 0.06 |
| C4 the return criterion — artifact + genuine ∞0′ | 0.07 |
| C5 TENTATIVE is temporal, never epistemic — non-data, never consumed | 0.03 |
| C6 the gate-fails-to-lock flow — child node + address append + arrangement | 0.05 |
| C7 the five quantum-jump commitments, as structural constraints | 0.13 |
| K1 stdlib-only, deterministic, no LLM, no network | 0.01 |
| K2 no byte normalisation — the ASCII hyphen is not the U+2212 operator | 0.00 |
| K3 D14 loyalty + the divergence log (zero silent novelty) | 0.00 |
| K4 no authenticity verdict — the human's click is the only one | 0.00 |
| K5 address derived never stored · no machine write path to the podium | 0.01 |
| L1 criterion match — the suite measures, not prose | 0.00 |
| L2 invariant end-to-end — one field + a verifying chain | 0.00 |
| L3 absence vs validity | 0.00 |
| L4 encoding — ∞0′ → ‖ survives every field | 0.00 |
| L5 cold restart — a new process rebuilds the same bytes | 0.00 |
| L6 blind tool — unobservable reads INCONCLUSIVE | 0.00 |
| **total** | **0.79** |

## Verdict

**PASS** — PASS 18

A FAIL is not a rewrite request: it is one correction, surgical, with the exact command, the raw output and the bytes that differ.
