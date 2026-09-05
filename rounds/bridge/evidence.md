# EVIDENCE — the bridge — the live desk adapter + the runtime config-read (the last firmware round).

*Written by `deliverable-audit` (the verifier side), by **running** the authored artifact. This file is the only place where "it works" may be said, and only next to the command that proved it. "Looks correct" is not a verdict here.*

## Environment

- when: `2026-08-30T07:05:25Z` · harness `deliverable-audit 1.0.0`
- host: `918576e4db0d68` · Linux-6.12.105-fly-x86_64-with-glibc2.41 · python `3.13.5`
- artifact under test: `/opt/data/tmp/proving-bridge/rounds/bridge/authored/run.py`
- artifact sha256: `4d550f889bf56090dbfee68929a5243caeae3e7832e8a5fb72ab7429caaa8637`
- criteria spec: `/opt/data/tools/deliverable-audit/specs/bridge.json`
- scratch (ledgers written during the run): `/tmp/deliverable-audit-zk3wnsqc`
- criteria quoted from: The criteria are quoted from rounds/bridge/commission.md §2 (staged on the box 2026-08-30, sha256 844705640475f7912f89406483e3f6031dffbc43a6587a242a7342045095de63), which in turn quotes Amihai's instruction (2026-08-30), FACTS.md (the B4 DeskAdapter fixture-only reading), and REVERSE-ENGINEERING.md §4.2 candidate #2. The held sources are the Codex (page sha ccad26dd…) and Appendix D (page sha a49e9413…). The K-claims are quoted from commission §2 and the phase-card §3 (D14 divergence log).
- total runtime: **6.37 s**  ✅ under the 60 s T0 bar

## Per-criterion result (§9 as written)

| ID | Criterion (verbatim) | Command | Raw output (decisive lines) | Verdict |
|---|---|---|---|---|
| C1 | …join the conductor to the live herdr socket via the attested B2 instrument.py (a live desk mode)… cost.DeskAdapter supports a third mode "live"; in it a turn speaks the real herdr dialect through the imported B2 Instrument — resolve by pane label, agent.prompt to the resolved pane, fenced read. No fixture process is spawned. | — | live mode returns TurnContext(override, None); the live branch never spawns; a whole live run completed through the real dialect (the server saw agent.prompt on resolved panes, 16 fenced turns) | **PASS** |
| C2 | …both spawn the fixture desk_server.py — never the live herdr socket… an unreachable live socket → outage hold (INCONCLUSIVE); a desk resolving to a pane with no agent (agent_not_found) → blocked hold. Neither spawns desk_server.py, neither returns a fake answer, neither reads clean. The centre guard refuses S/podium before any byte. | — | box run stalled with agent_not_found blocked holds on Q/V/P and G's fenced turns; absent socket stalled with outage holds and zero fenced records — neither spawned a fixture, neither read clean | **PASS** |
| C3 | …the conductor reads, at runtime, from Pi's settings.json + AGENTS.md + skills + prompts: the cycle budget/hold/poll, each desk's codex §2 emphasis, its voice, its model. A softconfig module reads each desk's §2 emphasis / voice / model and the budget from a soft-layer config file; the prompt and budget paths read through it. | — | good config reads ok; the soft voice/emphasis/model ride through byte-exact; the soft default_mode resolves the conductor's mode | **PASS** |
| C4 | …a guess that reads as a fact is the failure this whole flow exists to prevent. Absent soft config → the declared defaults (B4's exact bytes/values). Empty / malformed / partial soft config → INCONCLUSIVE with the reason; the run refuses to boot, never a silently substituted value. | — | absent config resolves B4's exact folded-spec bytes; empty/malformed/partial/wrong-typed configs read INCONCLUSIVE with the reason (empty carries e3b0c44298fc…); the conductor refuses to boot on a malformed config | **PASS** |
| C5 | …any interpretation, decoding and compiling MUST be loyal to 5qln.com/codex (D14). The B2 instrument, P4a's surface/conformance/step, P4b's block/arrangement/grammar, B3's descent, B0's ledger are imported by path, sha-pinned, never re-implemented. No new decoding operation, no new L1 symbol, no sixth corruption code. | — | run.py/softconfig.py carry no socket surface; every contract pin matches its bytes; corruption codes stay L1 L2 L3 L4 V∅ | **PASS** |
| C6 | Nothing attested is un-done; the triage uses B0–B4. The two fixture modes (sub-process, re-prompted) behave exactly as B4 attested — the pinned B4 runs reproduce byte-identically under the bridge conductor; the default mode is still re-prompted. | — | default mode still re-prompted; the two fixture modes' charges are B4's exact bytes (only 'live' added); a re-prompted run of B4's main_run completes with a chain-verified ledger and only the plant attested | **PASS** |
| C7 | …a new process must rebuild state from disk alone; test the second process. A fresh process re-arms the live mode and the config-read from disk alone (soft-layer files + ledger + the attested predecessors) with byte-identical next-action behaviour. | — | a second fresh Conductor re-armed the live mode from the ledger and soft files alone, byte-identical to the uninterrupted reference | **PASS** |

## Claimed capabilities (asserted by the author, measured here)

| ID | Criterion (verbatim) | Command | Raw output (decisive lines) | Verdict |
|---|---|---|---|---|
| K1 | K1 — stdlib, deterministic, no LLM. The bridge adds no network, no subprocess-beyond-the-attested, no LLM, no wall-clock in logic. The live socket is the only I/O, and it is the attested instrument's. | — | run.py/softconfig.py/cost.py import only the stdlib and the sanctioned predecessor modules | **PASS** |
| K2 | K2 — byte-exact enumerated forms. The §2-emphasis and voice bytes come from the enumerated tables (P4b PHASE/EQUATION_FORMS), never normalised (⋂→∩, ′→', spacing collapse = renaming an L1 symbol). | — | the declared defaults carry the enumerated glyph forms byte-exact; the needle ∞0′ → ‖ survives the soft read | **PASS** |
| K3 | K3 — the click is never a machine verdict. No authenticity verdict; the machine never claims arrival at ∞0 (HC-1/HC-2 permanently INCONCLUSIVE). | — | no module writes state='attested' or a non-null attestation_ref — the click stays the human's | **PASS** |
| K4 | K4 — the B2 guards hold. The centre guard refuses S/podium before any byte; an unresolvable write target is refused too (fail closed). | — | the centre guard refuses S/podium/None before any byte and lets a real desk pass | **PASS** |
| K5 | K5 — diff-ability. The soft config is a data file (one place to change, diff-able, versioned), never code. The pane-label → desk map stays a config table; no code derives meaning from a displayed label. | — | the soft config is a JSON data file and the label→desk map stays the imported DESK_LABELS table | **PASS** |

`INCONCLUSIVE` is a legitimate verdict. A blind tool must never report clean.

## Six-lens pass

| Lens | Applied how | Result |
|---|---|---|
| L1 criterion match — one quantity per criterion, no blind probe | 7 criteria + 5 claims, each a distinct measured quantity, every probe registered | **PASS** |
| L2 invariant end-to-end — one pass over the whole list | a consumed tentative anywhere fails the WHOLE list; the live runs are whole-run artifacts | **PASS** |
| L3 absence vs validity | absent config → defaults (never valid); empty config → inconclusive carrying e3b0c44298fc…; empty ledger audits INCONCLUSIVE | **PASS** |
| L4 encoding — ∞0′ → ‖ survives the soft read | the needle rode the soft config's voice field byte-exact, never folded | **PASS** |
| L5 cold restart — the second process rebuilds from disk alone | C7's fresh-process re-arm held byte-identical | **PASS** |
| L6 blind tool — nothing unobservable reads clean | the box run stalls with holds, the absent socket holds outage, a malformed config refuses to boot (C2 PASS) | **PASS** |

## Timings (T0 mechanical)

| Step | Seconds |
|---|---|
| C1 the live desk mode — a third mode joined to the live herdr socket through the imported B2 instrument, label-resolved, never a fixture spawn | 0.51 |
| C2 live mode fails closed, never into a fixture — absent socket → outage hold; no-agent desk → blocked hold; never a fake answer, never clean | 0.24 |
| C3 the runtime config-read — §2 emphasis / voice / model / budget read from the soft layer at runtime, replacing the hard-coded specs/charges | 0.00 |
| C4 declared defaults + fail-closed — absent config → B4's exact bytes; empty/malformed/partial → INCONCLUSIVE with the reason, never silently substituted | 0.00 |
| C5 import, never re-author (D14 loyalty) — the dialect, the D.12 checks, the grammar, the descent are imported sha-pinned, never re-implemented | 0.04 |
| C6 nothing attested is un-done — the two fixture modes reproduce B4's pinned bytes; the bridge is additive | 4.90 |
| C7 cold restart from disk alone — a fresh process re-arms the live mode + config-read from the ledger + soft files, byte-identical | 0.55 |
| K1 stdlib-only, deterministic, no LLM — no network/socket imports in the conductor's own modules; the live socket is the attested instrument's | 0.02 |
| K2 byte-exact enumerated forms — the §2-emphasis/voice bytes come from the enumerated tables, never normalised | 0.00 |
| K3 the click is never a machine verdict — no state:attested, no non-null attestation_ref, no tentative flip | 0.02 |
| K4 the B2 guards hold — the centre guard refuses S/podium before any byte; an unresolvable write target is refused too | 0.00 |
| K5 diff-ability — the soft config is a data file (one place to change), never code; no code derives meaning from a displayed label | 0.00 |
| L1 criterion match — one quantity per criterion, no blind probe | 0.00 |
| L2 invariant end-to-end — one pass over the whole list | 0.00 |
| L3 absence vs validity | 0.00 |
| L4 encoding — ∞0′ → ‖ survives the soft read | 0.00 |
| L5 cold restart — the second process rebuilds from disk alone | 0.00 |
| L6 blind tool — nothing unobservable reads clean | 0.00 |
| **total** | **6.37** |

## Verdict

**PASS** — PASS 18

A FAIL is not a rewrite request: it is one correction, surgical, with the exact command, the raw output and the bytes that differ.
