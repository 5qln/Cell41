# EVIDENCE — P4a · the step mode

*Written by Hermes (`herdr`) after **running** dsh's authored artifact. This file is the only place where
"it works" may be said, and only next to the command that proved it.*

## Environment

- **Verifier:** Hermes profile `herdr`, a separate process from the author. `builder ≠ verifier`.
- **Artifact under test:** dsh's authored P4a deliverables, at
  `/home/deploy/the-cell/rounds/P4a-step-mode/authored/`, staged locally to
  `/opt/data/tmp/proving-p4a/good/` (byte-identical, sha-verified below).
- **Audit pack:** `/opt/data/tools/deliverable-audit/` — `specs/p4a-step-mode.json`,
  `probes/step_session.py`, `lenses_p4a.py`, `selftest_p4a.py`. **Accepted 58/58 against the real §9.1
  interface before it judged anything**, alongside the older suites (22/22 · 38/38 · 45/45).
- **Command:** `python3 audit.py --spec specs/p4a-step-mode.json --out …/p4a-evidence-final.md`
- **Full run time:** 1.60 s (T0 bar < 60 s).
- **Artifact sha256** (the bytes judged):

| file | sha256 |
|---|---|
| `conformance.py` | `3391b9cac14f56e0d0d7aac954f77864ca84faf8401e36d82d978146e6ef404c` |
| `surface.py` | `776ff46393bf81db62841043021c97288e2c1414bec43971d275d1dfbdfac36d` |
| `step.py` | `7c02f316969fdc2a6a9825b2ce4cb264976de3c607d8438f58b4b1e94bd26edf` |
| `driver.py` | `2a0dfedc8a2fec4709a0e5687597dba5fa938fc523152edc4b3ce4653ad66628` |
| `selftest.py` | `573b7ea6fd3b3c34f8f6cab617fd55249c3281e2cad054c3d53a5847a19d9b9d` |
| `phase-card.md` | `3051f66fcce46143c78ba351707ff6fb5bf5a6ed145fb115e03ab5f4e03e4a38` |

## Per-criterion result

| ID | Criterion (as the pack binds it — commission §9.1) | Decisive line | Verdict |
|---|---|---|---|
| C1 | the same code path, stepped — identical to the attested driver | ledger projection `d87d7fd3006d` across plain · auto-stepped · step-session · attested-B2; single defs | **PASS** |
| C2 | the step suspends before the first side effect; a FAIL stops the session | stop_before=turn → `prompts=0 machine records=0`, last `intent_only=True` `outcome='not-taken'`; on_fail=stop → verdicts `['INCONCLUSIVE','FAIL']` stopped at the FAIL | **PASS** |
| C3 | every step emits address, zoom, checks, decode, compile and what it would do next | 9 trail lines, 4 turn steps, 450 conformance items; gapless, by-reference, content leaked=none | **PASS** |
| C4 | every check cites its source verbatim and catches its defect | AD=15 CX=18 R=13 derived=4; citations verbatim **50/50**; nine defects caught **9/9** | **PASS** |
| C5 | two trails, never merged; and a cold restart | ledger sha equal stepped/plain; absent=absent empty=empty torn=damaged; cold restart position='b' records=13 | **PASS** |
| K1 | no depth cap · no root assumption · an extensible alphabet | depth caps=none, roots=none, narrowing=none; alphabet `('S','G','Q','P','V')` extensible | **PASS** |
| K2 | stdlib only · deterministic · no LLM in the checks | foreign imports=none network=none llm=none; two runs identical (9 lines each) | **PASS** |
| K3 | the click is never a machine verdict | `DC-AUTH-1/2` both INCONCLUSIVE on a lawful V surface, reasons name the click, no flip site | **PASS** |
| K4 | the centre, the attestation and the keypress under stepping | centre prompt raised, 0 writes; 0 attestations authored; run_session states the limit | **PASS** |
| K5 | descent is reserved, not implemented | registry carries zoom_in/zoom_out reserved, signs −/+, no implementation; trail schema ready | **PASS** |
| K6 | novelty only in the Appendix-D jacket (D14) | divergence log present, derivative declared, all 4 derived items listed, codes exactly 5 | **PASS** |

## Six-lens pass

| Lens | Applied how | Result |
|---|---|---|
| 1 Criterion match | reads the author's own suite by AST; requires a **byte** comparison of the stepped/unstepped ledger | **PASS** — 98 tests, byte comparison=True |
| 2 Invariant end-to-end | seq gapless, every line chained to the previous line's bytes, zoom/sign coherent, ledger verifies after stepping | **PASS** |
| 3 Absence vs validity | missing/empty/newline-only trail and absent/empty/no-marker surface all read absent/empty/damaged; blind evaluation PASS=0 FAIL=0 INCONCLUSIVE=38 | **PASS** |
| 4 Encoding | `∞0′ → ‖` pushed through every field; 13 slots by `sha256:` reference, no leak, digests independently recomputed | **PASS** |
| 5 Cold restart | a fresh process rebuilds position from the ledger alone and trail continuity from the trail alone | **PASS** |
| 6 Blind tool | cell-scope items INCONCLUSIVE with no desk constituted; session verdict INCONCLUSIVE, never PASS | **PASS** |

## T0 mechanical (< 60 s)

- Full audit: **1.60 s**.
- Pack acceptance (`selftest_p4a.py`): 58/58, conforming twin 1.64 s.
- Older suites still green: `selftest.py` 22/22 · `selftest_b1.py` 38/38 · `selftest_b2.py` 45/45.
- Drift check (canon vs box vs wiki): run separately per the canon discipline; this evidence covers the artifact.

## Honest summary

**16/16 PASS — zero corrections to dsh.** The one anomaly this verification surfaced was the verifier's
own: the P4a audit pack had been written against a three-name interface (`StepSession` /
`PromptStepper` / `ALPHABET`) that commission §9.1 never names, and its "58/58 acceptance" was
circular (pack ↔ its own twin, never pack ↔ commission). The pack was reconciled to §9.1
(`run_session` + `Stepper` + `StepTrail` + `read_trail` + `STEP_KINDS`), re-accepted 58/58, and
re-run. dsh's artifact was faithful throughout.

Two codex/fractal content questions were put to dsh (the verifier does not decide source bytes):

1. **`∩` U+2229 vs `⋂` U+22C2** in the V equation — dsh ruled same operator, two glyphs; `∩` is
   canonical for the constitutional form; `EQUATION_FORMS` correctly enumerates both.
2. **`surface.PHASES["V"]["equation"]`** — dsh ruled it is a verbatim §3.2 Compiled Phases L347
   citation, not drift; keep as-is.

Both rulings are recorded verbatim-able in `dsh-runs/P4a-step-mode/run-consult-glyph.log` (rc=0).

**Not tested and why:** no desk is constituted on the box (H-P4a-4), so cell-scope checks correctly
read INCONCLUSIVE — that is the live verdict P4b's desk bundles will turn into PASS. The live tier
(prompting a real Pi pane) belongs to P4b, not this round.

No correction was needed. The round is ready for Amihai's attestation.
