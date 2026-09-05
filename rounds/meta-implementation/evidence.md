# EVIDENCE — Grammar · the meta implementation — decoder (D1) + compiler (C1) + corruption taxonomy (C2.8), judged by the step mode

*Written by `deliverable-audit` (the verifier side), by **running** the authored artifact. This file is the only place where "it works" may be said, and only next to the command that proved it. "Looks correct" is not a verdict here.*

## Environment

- when: `2026-08-29T17:37:15Z` · harness `deliverable-audit 1.0.0`
- host: `918576e4db0d68` · Linux-6.12.105-fly-x86_64-with-glibc2.41 · python `3.13.5`
- artifact under test: `/opt/data/tmp/proving-meta/good/compiler.py`
- artifact sha256: `ffb5b8d585549be8cf2b29e7a75ac2eaf851c0912a0cde0ed04426af1fa9ff19`
- criteria spec: `/opt/data/tools/deliverable-audit/specs/meta-grammar.json`
- scratch (ledgers written during the run): `/tmp/deliverable-audit-qjpt1g7g`
- criteria quoted from: The criteria are quoted from rounds/meta-implementation/commission.md §2 (staged on the box 2026-08-29, sha c9f3fda1270d440a3cf3fb6bf1b13fcc95ee75da4b54f9a66b7095404c5553ee), which quotes the held Codex (§2.1-2.5, §2.8, §3.1-3.6) and Appendix D (§D.7/D.8/D.12/D.14). The held sources are the Codex (page sha ccad26dd..., extraction e5f0c738...) and Appendix D (page sha a49e9413..., extraction 6bb28c37...).
- total runtime: **0.48 s**  ✅ under the 60 s T0 bar

## Per-criterion result (§9 as written)

| ID | Criterion (verbatim) | Command | Raw output (decisive lines) | Verdict |
|---|---|---|---|---|
| C1 | C1 — The Decoder. §2.1–2.5, the five decoding operations, symbol-by-symbol, over the adaptive context (§2.6 / §3.3). §3.5 (syntax): "Every decoding operation follows D1 symbol-by-symbol"; §3.5 (drift): "No decoding step omitted or reordered." §2.9: "The decoding operations do not change at scale." | — | all five phases decode over the §2.6/§3.3 adaptive context, symbol-by-symbol in order, slots as references; unresolvable contexts fail closed (DecoderError) | **PASS** |
| C2 | C2 — The Compiler. §3.1 "Every compiled surface carries this block exactly". §3.2 the five compiled phases each with EQUATION / OUTPUT / CONTEXT IN / CONTEXT OUT / DECODING / CORRUPTION / LENSES. §3.3 the adaptive context chain: S with ∅ (or ∞0' from prior cycle) → X … V with full trace → B + B'' + ∞0'. | — | block byte-for-byte §3.1 · five §3.2 compiled phases with all seven labels · §3.3 context chain verbatim | **PASS** |
| C3 | C3 — The thirteen decoder rules, checkable. §3.4 R1–R13, enforced as checks: R1 … R13 (verbatim citations, the source's own numbering). | — | R1–R13 carried verbatim from §3.4 and enforced in the 48-item check table | **PASS** |
| C4 | C4 — Corruption taxonomy. §2.8, exactly five, each a named decoding failure: L1 Closing · L2 Generating · L3 Claiming · L4 Performing · V∅ Incomplete. §3.5 (syntax): "Five corruption codes exactly"; §3.5 (drift): "No corruption code added beyond five." | — | exactly five codes, each a named decoding failure, the sixth-code AST scan clean, every detector maps to its code | **PASS** |
| C5 | C5 — Validation protocol. §3.5, all three passes applied to any produced surface — syntax (6), semantic (6), drift (6) — with "B, B'', ∞0' are three distinct things with distinct decoding steps" and "Crystallization reads the formation trail (not generated from nothing)." | — | 48 checks across §3.5 (6/6/6) + D.12 (5/5/5) + R1–R13 + HC; the lawful cycle aggregates with 0 FAIL; HC-1/HC-2 INCONCLUSIVE by design | **PASS** |
| C6 | C6 — Surface emission + the addressing layer. §3.6 "Every emitted surface must carry: Constitutional block (§3.1) — exact · The active phase's compiled form WITH decoding operation (§3.2) · The adaptive context chain (§3.3) · The decoder rules (§3.4) · Resolved symbols for every symbol used (§1.9)" — and "Surfaces may add behavioral, interface, and domain layers — visibly separate from the decoding." Appendix D.12: 4+1 invariant, five equations verbatim, signless true start (AR5), ∞0′ ≡ ∞0 (D.8). | — | all five surfaces parse lawful; block exact; jacket visibly separate; signless start + ∞0′≡∞0 present; 3+1 cells FAIL | **PASS** |
| C7 | C7 — The authenticity prohibition (the load-bearing refusal). The engine never scores, decides, or asserts authenticity. HC-1 ("a machine click is never a verdict") and HC-2 are permanently INCONCLUSIVE. No write path to state:attested; no non-null attestation_ref; a decode that claims to have reached ∞0 is corruption L3, reported as such — never as arrival. | — | no authenticity field; a claim to reach ∞0 is L3 never arrival; no state:attested / cell-attest / input() in the sources | **PASS** |

## Claimed capabilities (asserted by the author, measured here)

| ID | Criterion (verbatim) | Command | Raw output (decisive lines) | Verdict |
|---|---|---|---|---|
| K1 | Stdlib only, deterministic, no LLM in the engine mechanics (the LLM lives at the desk, never in the decoder/compiler). | — | the four modules import only the stdlib and the sanctioned predecessors (codex/decoder/corruption/compiler + attested carriers) | **PASS** |
| K2 | No byte normalisation (⋂→∩ is renaming). The enumerated ∞0′/∞0' and ∩/⋂ forms are accepted as data, never folded into one. | — | every equation form enumerated with a sha that recomputes; the ∩/⋂ V forms are both carried, never folded | **PASS** |
| K3 | Every decoding and compiling loyal to 5qln.com/codex (D14). Anything added beyond the source is declared derivative, visibly separate, no new L1 symbol, no new decoding operation, no sixth corruption code. | — | D14 divergence log present; the AST scan finds no new L1 symbol, no sixth corruption code | **PASS** |
| K4 | No authenticity verdict. The run has no write path to state attested and never types the human's word. | — | no assignment or record key writes an attested state/mark; the engine's mark is mechanical, never attested | **PASS** |
| K5 | No write path to the podium (PRD §2.1, T-R3-02). The engine never writes nodes/*/question.md, never invokes cell-attest, never prompts the centre S. | — | no question.md / nodes/ write path; no cell-attest; the engine never prompts the centre S | **PASS** |

`INCONCLUSIVE` is a legitimate verdict. A blind tool must never report clean.

## Six-lens pass

| Lens | Applied how | Result |
|---|---|---|
| L1 criterion match | 7 criteria + 5 claims, each a distinct measured quantity, every probe registered | **PASS** |
| L2 invariant end-to-end | the §3.1 block is byte-identical across all five emitted surfaces — one invariant, not per call | **PASS** |
| L3 absence vs validity | absent→absent, empty→absent (e3b0c44298fc…), never a valid surface | **PASS** |
| L4 encoding | ∞0′ → ‖ survived emit→parse byte-exact; no normalisation anywhere in the path | **PASS** |
| L5 cold restart | a fresh python -B process re-imported the engine and rebuilt the byte-identical surface from disk alone | **PASS** |
| L6 blind tool | no desk is constituted; HC-1/HC-2 INCONCLUSIVE by design — no machine report can read a fully clean verdict | **PASS** |

## Timings (T0 mechanical)

| Step | Seconds |
|---|---|
| C1 the Decoder — the numbered decoding operation walked symbol-by-symbol, in order, over the adaptive context, fail closed | 0.00 |
| C2 the Compiler — the constitutional block byte-for-byte, the five compiled phases, the context chain verbatim | 0.07 |
| C3 the thirteen decoder rules, checkable — R1–R13 enforced with verbatim citations | 0.00 |
| C4 the corruption taxonomy — exactly five, each a named decoding failure, no sixth | 0.02 |
| C5 the validation protocol — syntax/semantic/drift (§3.5) + D.12 + R1–R13 + HC, applied to any surface | 0.00 |
| C6 surface emission + the addressing layer — block exact, lawful parse, jacket visibly separate, 4+1 / signless start / ∞0′≡∞0 | 0.00 |
| C7 the authenticity prohibition — HC-1/HC-2 permanently INCONCLUSIVE, no authenticity field, a claim to reach ∞0 reads L3 never arrival | 0.00 |
| K1 stdlib-only, deterministic, no LLM in the engine mechanics | 0.02 |
| K2 the equation byte forms enumerated with source + sha, never normalised | 0.00 |
| K3 D14 loyalty + the divergence log — no new L1 symbol, decoding operation, or sixth corruption code | 0.03 |
| K4 no authenticity verdict — the engine never writes state:attested, never sets a machine attestation_ref | 0.03 |
| K5 no write path to the podium — no question.md write, no cell-attest, no input() | 0.00 |
| L1 criterion match | 0.00 |
| L2 invariant end-to-end | 0.00 |
| L3 absence vs validity | 0.00 |
| L4 encoding | 0.00 |
| L5 cold restart | 0.00 |
| L6 blind tool | 0.00 |
| **total** | **0.48** |

## Verdict

**PASS** — PASS 18

A FAIL is not a rewrite request: it is one correction, surgical, with the exact command, the raw output and the bytes that differ.
