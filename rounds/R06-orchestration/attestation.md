# ATTESTATION — R06 · Orchestration · the executable Fractal

*Amihai's act. One sentence in his own words, and the sha256 of what he attested. The machine wrote the
material below the line so he knows exactly what he is putting his word to; it never types his word for him.*

---

## What was run, and what it showed

The verifier (Hermes `herdr`, the non-author) executed dsh's artifact against the fixture desk harness
(no live box — H-ORCH-1) and recorded the result in `evidence.md`:

- **46/46 selftests** in 6.113 s (Python 3.12.3), RC=0.
- **Cycle run** (`SGQPV`): complete, `ended_in ∞0′`, return-question `sha256:eeb4857b…`, 5 per-gate
  ledger records `x y z a b`.
- **Materializer**: per node (G, Q, P, V, center `_`) emits `SYSTEM.md` + `.pi/settings.json` +
  `skills/SKILL.md` + `tools/tool-surface.md` — a reloadable, 5QLN-dedicated config layer.
- **Cold restart** (lens 5): a fresh process rebuilds from disk alone to **byte-identical ledger
  (`1d23d444…`) and trail (`b9be4bf1…`)**, both ending ∞0′.
- **Loop run** (`SGGQG`): a 7-entry per-iteration trail (seq · cycle · cell · cost · ts · full D.12
  conformance) — the optimization log specified.
- **Podium guard**: refused, zero fenced records.
- **Hash fence**: clean — nothing outside `authored/` touched.

## What is being attested

That **Orchestration — the executable Fractal — does what it was commissioned to do**, on the evidence of
an execution record written by the non-author (`evidence.md`, **18/18 named checks — C1–C7, K1–K5, the
two addendum requirements — plus six lenses, zero corrections**):

- the scenario is a **word** over {S,G,Q,P,V} + signed paths — data, never code, never a topology enum (C1);
- the navigation **derives from the signs** — sequence / parallel / loop / custom fall out of D.6, no
  hardcoded topology (C2);
- the materializer is **zoom-in** — each node its own ∞0|K cell, the write-path complementing the
  bridge's softconfig read-path, reloadable at runtime (C3 + addendum 1);
- **general tools** are lawful on the K side — search / write-doc / write-code / activate, tool-agnostic
  (C4);
- the trace lands **per-gate** in the B0 ledger, format unchanged (C5);
- every run reaching V **ends in ∞0′**; words not reaching V end inconclusive — the seal's "no V without
  ∞0′" (C6);
- the podium is never written; nothing is attested by the machine (C7);
- stdlib/deterministic/no-LLM (K1) · byte-exact forms, never normalised (K2) · the click stays the
  human's (K3) · the centre guard holds (K4) · scenario + config are diff-able data (K5);
- **session logs, especially loops** — a loop run leaves per-iteration, analyzable trail entries
  (addendum 2);
- the six lenses, including cold-restart and absence-never-valid.

**What is NOT being attested:** that any real desk has booted or answered a prompt — no desk is
constituted in the live box for this round (H-ORCH-1); the scenario schema and "activate" are provisional
until Amihai touches them (H-ORCH-2/3); and nothing about the constitution, the settings surface, the two
modes, or the swarm — those are soft mode, not this round.

## His word — recorded exactly as he gave it

> **"i attest."** — Amihai Loven, 2026-08-30. (He endorsed the attestation of this round as written and
> evidenced, after the machine's drafted sentence below was shown to him.)

## The drafted sentence — shown to him, endorsed

> *"I attest R06 Orchestration — the executable Fractal — as written and evidenced."*

---

- `evidence.md` sha256: `62ad3a10bac3a0fad017c1752968ba67764290095d7acbb836b781d6cfb00289`
- `commission.md` sha256: `98f2d098431d618648172176176455277aec1dd7af4dbc499dec6bcbc5e49dcd`
- authored files (sha256): `word.py 4ecde1fe…` · `navigate.py e9d0aa1b…` · `materialize.py 52730dbd…` ·
  `orchestrate.py ccc97a38…` · `surface_contract.py 154a6522…` · `selftest.py ff82d806…` ·
  `phase-card.md 7a29b028…`
- his box at the moment of attesting: `state/gates.jsonl` — 1 record, his plant (`6989a742…`; orchestration
  is firmware, not a gate)
- date: **2026-08-30**
