# COMMISSION — meta-implementation · the codex made executable

*Written by Hermes (`herdr`) before dsh authors anything. A file, never chat. dsh's whole world for
this round is this document.*

## 0. Provenance

- Held source: `5qln.com/codex` — page sha256 `ccad26dd60384eb17aed040a43b5f49ad7419419a3f6d88e5edabfbcfe07f458` (64,132 B, http 200), extraction `cache/canon/5qln-codex.txt` sha256 `e5f0c738d123efc1e412a14da1701a721606275867319e1c68d53b081445c133`.
- Held source: `5qln.com/dsh-5qln-codex-fractal` (Codex Appendix D) — page sha256 `a49e9413f542c4ea8e16c6fcb1ac883a0c76d6042ef2e739caccb438e82fabb2`, extraction `cache/canon/dsh-5qln-codex-fractal.txt` sha256 `6bb28c37cfe6267da1675eac16ac8bbf9679a1d0e5db0f08eb4495d2c22f6bf7`.
- **A `.txt` is an extraction, never the source.** The page sha is the one loyalty is owed to (§1.10).
  dsh works from the held extractions, which carry the source page shas in their own commission header.
- **This is a working handle.** The formal slot name is Amihai's to give (`H-META-1`). The word
  "meta implementation" is *his own term* (his direction, 2026-08-28): *"a meta implementation of the
  codex - decoder - compiler etc."* Nothing in the artifact's logic or schema may depend on this handle.

## 1. What to build (one paragraph, no doctrine)

The **5QLN Codex, Parts II and III, as executable modules** — nothing invented. The Decoder (D1,
§2.1–2.5) becomes a set of callables: each phase's numbered decoding operation takes the adaptive
context (§2.6 / §3.3) and returns the phase's filled symbol slots. The Compiler (C1, §3.1–3.6) emits the
constitutional block exactly, the compiled phase forms with their decoding operations, the adaptive
context chain, the thirteen decoder rules in checkable form, and the validation protocol — and checks
any produced surface against all three (syntax · semantic · drift). The corruption taxonomy (§2.8) is a
closed set of exactly five. **What the engine must never do is decide whether a decode is *authentic*** —
that is the human's click, and the step mode's `HC-1`/`HC-2` are permanently INCONCLUSIVE for exactly
that reason. This is a *surface an agent emits and is checked against* — which is why the step mode (P4a)
had to exist first.

## 2. Acceptance criteria — quoted verbatim from the held codex

> The criteria below are the codex's own validation material, quoted verbatim. dsh builds to them; the
> verifier (P4a, the step mode) checks against them. Each gets an ID so `evidence.md` answers line for line.

**C1 — The Decoder.** §2.1–2.5, the five decoding operations, symbol-by-symbol, over the adaptive context (§2.6 / §3.3). §3.5 (syntax): *"Every decoding operation follows D1 symbol-by-symbol"*; §3.5 (drift): *"No decoding step omitted or reordered."* §2.9: *"The decoding operations do not change at scale."*

**C2 — The Compiler.** §3.1 *"Every compiled surface carries this block exactly"* — the constitutional block byte-for-byte (`LAW: H = ∞0 | A = K` … `CENTER: not a sixth phase — coherence only`). §3.2 the five compiled phases each with `EQUATION / OUTPUT / CONTEXT IN / CONTEXT OUT / DECODING / CORRUPTION / LENSES`. §3.3 the adaptive context chain: `S` with `∅ (or ∞0' from prior cycle) → X` … `V` with `full trace → B + B'' + ∞0'`.

**C3 — The thirteen decoder rules, checkable.** §3.4 R1–R13, enforced as checks:
`R1` Each phase decodes one equation to form one output · `R2` B = decoded output (fulfillment + propagation), B'' = artifact, ∞0' = return with question · `R3` Sub-phases refine the decoding through borrowed qualities — they never replace the output · `R4` 25 lenses: each applies one equation's quality to another equation's decoding · `R5` Cycle trace maps creative line positions to actual content as it forms · `R6` Formation trail: per-output ordered record, lens-tagged — what B'' reads · `R7` Crystallization at V only — two passes · `R8` No V without ∞0'. ∞0' carries a question. No question = not ∞0' · `R9` Five corruption codes: L1 L2 L3 L4 V∅. Each names a specific decoding failure · `R10` H = ∞0 | A = K defines the asymmetry · `R11` Attestation: provenance travels with B'', fingerprint hashes invariant only · `R12` Center is coherence only · `R13` Scale by repeating the lawful cell.

**C4 — Corruption taxonomy.** §2.8, exactly five, each a named decoding failure:
`L1` Closing · `L2` Generating · `L3` Claiming · `L4` Performing · `V∅` Incomplete. §3.5 (syntax): *"Five corruption codes exactly"*; §3.5 (drift): *"No corruption code added beyond five."*

**C5 — Validation protocol.** §3.5, all three passes applied to any produced surface — syntax (6), semantic (6), drift (6) — with §3.5 (semantic): *"B, B'', ∞0' are three distinct things with distinct decoding steps"* and *"Crystallization reads the formation trail (not generated from nothing)."*

**C6 — Surface emission + the addressing layer.** §3.6 *"Every emitted surface must carry: Constitutional block (§3.1) — exact · The active phase's compiled form WITH decoding operation (§3.2) · The adaptive context chain (§3.3) · The decoder rules (§3.4) · Resolved symbols for every symbol used (§1.9)"* — and *"Surfaces may add behavioral, interface, and domain layers — visibly separate from the decoding."* Appendix D.12 (addressing) held: the 4+1 invariant, the five equations verbatim at every cell, the signless true start (`AR5`), `∞0′ ≡ ∞0` (`D.8`).

**C7 — The authenticity prohibition (the load-bearing refusal).** The engine never scores, decides, or asserts authenticity. The step mode's `HC-1` (a machine click is never a verdict) and `HC-2` are permanently INCONCLUSIVE. No write path to `state:attested`; no non-null `attestation_ref`; a decode that *claims* to have reached ∞0 is exactly corruption `L3` and must be reported as such — never as arrival.

## 3. Verified-facts block (do not re-derive; these were executed)

| Fact | Value | Probed |
|---|---|---|
| Codex page sha | `ccad26dd6038…` | 2026-08-28 |
| Appendix D page sha | `a49e9413f542…` | 2026-08-27 |
| Equation byte axes | `∩` U+2229 (Codex) vs `⋂` U+22C2 (Appendix D) · ASCII `'` vs `′` U+2032 · spaced vs compact | 2026-08-28 |
| Per-string equation shas | S spaced `de0b9096…`/compact `4fb171ba…` · G `c2b0ed6e…`/`98950e70…` · Q `cd20931f…`/`6e060933…` · P `8175a49a…`/`ae9433ec…` · V Codex `7c8305fa…`/AppD `05101fd6…` · V public `9b3f8a06…` | 2026-08-28 |
| Step mode (P4a) | attested, canon `898593b`, 16/16 PASS, pack 58/58 | 2026-08-29 |
| Desk bundles (P4b) | attested, canon `2a2053a`, 18/18 PASS — `surface_contract.py` is the surface the engine emits | 2026-08-29 |
| Descent (B3) | attested, canon `be30010` | 2026-08-29 |
| Unattended run (B4) | attested, canon `50668ca`, 18/18 PASS | 2026-08-29 |
| Predecessor modules on the box | `surface_contract.py` `aa0ea654…` · `fractal_ledger.py` `b291e659…` (B0) | 2026-08-29 |
| Letter-order | inner-first (`XY := X within Y`) — DECIDED, his word "keep" | 2026-08-29 |
| Box python | `3.12.3` (`/usr/bin/python3.12`); targets 3.12+, stdlib only | 2026-08-27 |
| Prior art (his 27 repos) | IGNORED — his word "ignore them" (2026-08-28); entire math = codex + Appendix D alone | 2026-08-28 |
| dsh invocation | `node ~/.dsh/profiles/node_modules/@deepseek-ai/dsh/lib/bin.js --profile headless "<task>"`; source `~/.nvm/nvm.sh`; `DSH_PERMISSION_MODE=danger-full-access` | 2026-08-27 |

## 4. Holds — declare, never guess

- **`H-META-1` (his):** the formal slot name of this phase. "meta implementation" is his own term and a working handle; the display name, the R-number, and any logic-visible identifier are his to give. No code or schema may depend on the handle.
- **`H-META-2` (carried H-P4a-1):** the equation byte forms. Three real axes of variance across his own two sources (`∩`/`⋂` · `'`/`′` · spaced/compact). The engine **enumerates** accepted byte forms with source + sha and **never normalises** — folding `⋂→∩` or `′→'` is itself renaming an L1 symbol (D.12 syntax check forbids it). If he names one canonical byte string, the table collapses; that is his to name.
- **`H-META-3`:** no desk is constituted on the box. The engine is fixture-tested against deterministic inputs, never a live Pi desk. It must fail closed on any context it cannot resolve.
- **`H-META-4`:** the engine is the *language*, not the *gates*. Gate semantics live in `fractal-engine` and the attested B0 ledger; the engine neither re-implements them nor touches `state/`.

## 5. Prohibitions for this round

- No write path to the podium (`pane.send_text/input/keys` at the centre is forbidden). No `nodes/*/question.md` write. No `cell-attest`. No `input()`.
- No git. No attestation. No claim that anything ran — the phase card carries **predictions**, never results.
- No gate semantics re-implemented outside `fractal-engine` (`H-META-4`).
- **No authenticity verdict** — the engine never decides a decode is authentic (`C7`, `HC-1`/`HC-2` INCONCLUSIVE).
- **No new L1 symbol, no new decoding operation, no sixth corruption code** (D14). Novelty is permitted only in the declared Appendix-D jacket: visibly separate, with a divergence log.
- No prior-art repo is read (his word "ignore them"); the entire math is the held codex + Appendix D alone.
- Stdlib only, deterministic, no LLM in the engine mechanics (the LLM lives at the desk, never in the decoder/compiler).

## 6. Deliverables and where they go

`/home/deploy/the-cell/rounds/meta-implementation/authored/` — the decoder, the compiler, the corruption
taxonomy, the surface-emission path, a `selftest.py` that exercises the codex's own checks (R1–R13 ·
§3.5 · Appendix D.12 · the five corruption codes), and a `phase-card.md` (criteria + holds +
**predictions**, never results; includes the D14 divergence log).

## 7. Budget

One authoring generation. Exceeding it is a HOLD surfaced to Amihai, never a silent continue.
