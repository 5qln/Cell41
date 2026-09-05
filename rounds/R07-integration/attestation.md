# ATTESTATION — R07 · integration · the seam

*Amihai's act. One sentence in his own words, and the sha256 of what he attested. The machine wrote the
material below the line so he knows exactly what he is putting his word to; it never types his word for him.*

---

## What was run, and what it showed

The verifier (Hermes `herdr`, the non-author) executed dsh's artifact independently — not the author's
suite — and recorded the result in `evidence.md`:

- **Fence clean** — nothing outside `authored/` touched across authoring (the only delta is the
  verifier's own `fence-before.txt`).
- **Pins (C7):** 9 pinned files, `contract: integration-1` — `pins: PASS` (the import IS the pin check;
  a drifted/missing pin refuses the import).
- **Plan-equivalence (C3):** `cellctl conduct --plan-only` **byte-identical** to the direct engine calls
  (`word.decode_scenario` + `navigate.plan_walk`) — the wrapper adds nothing.
- **Enforcement legs (C4), verifier's own probes:** L1 injected `herdr_send_prompt` → FAIL · L2
  `from word import` → FAIL + `undeclared-executable` → FAIL · L3 unknown spec field → INCONCLUSIVE,
  clean → `ok`.
- **Thin binding (C1/C2/K1), verifier's own AST audit:** `cellctl` imports stdlib + the seam only — no
  socket, no subprocess, no LLM; 13 subcommands, **no `prompt`** (the write side is never a command).
- **Fail-closed (C6):** absent / empty (sha256 of empty cited) / malformed scenario each read
  `absent`/`malformed`, exit 1 — never clean.
- **Run lock (C5):** `flock LOCK_EX` on `<work_dir>/.cellctl.lock`, in the wrapper, never the engine.
- **His plant (gates_plant):** `6989a742…`, byte-for-byte — untouched.

**The live enforcement verdict is FAIL — and that is the suite working, not a defect.** It found exactly
the pre-integration conditions the SCOPE names: `plugin/bin/_cell_api.py` socket client (AF_UNIX/connect/
sendall), the five desks' `.pi/prompts/guide.md` `herdr_send_prompt`, and `cell-attest` importing the
pinned `fractal_ledger` directly. Those are W3 (constitution) and W5 (bindings) work — reported with
file:line:token, never tuned away.

## What is being attested

That **the integration — the seam — does what it was commissioned to do**, on the evidence of an
execution record written by the non-author (`evidence.md`, **C1–C7 · K1–K5 · six lenses, zero
corrections**):

- the **slash commands are the seam**: a thin, logic-free `cellctl` over the attested engine — one
  subcommand, one engine call, no socket code, no prompt assembly, no record-writing (C1);
- the **write side is never exposed** as a command (C2);
- the **wrapper adds nothing** — plan-equivalence byte-identical (C3);
- the **enforcement suite makes "no driving logic in the soft layer" a structural, mechanically-checkable
  fact** — each leg proven to FAIL on a deliberately-injected violation (C4);
- the **run lock** holds — a second `/conduct` blocks, never interleaves (C5);
- **fail-closed**: absent/empty/malformed never read valid, never clean (C6);
- the **pinned seams stay the import boundary** (C7);
- stdlib/deterministic/no-LLM (K1) · byte-exact, never normalised (K2) · the click stays the human's
  (K3) · the centre guard holds (K4) · spec/scenario/config are diff-able data (K5);
- the six lenses, including cold-restart, absence-never-valid, and blind-tool INCONCLUSIVE.

**What is NOT being attested:** that any live desk was prompted — the round is fixture-only (H-INT-1);
the first paid `/conduct` is Amihai's alone to authorize (W4); command + round names are candidate (D4);
spawn ownership is deferred (H-INT-3); the scenario schema and the live-spec numbers are provisional
(H-INT-4); and the constitutions do not yet speak the §3.6 surface (H-INT-5 — W3's work).

## His word — recorded exactly as he gave it

> **"attest it"** — Amihai Loven, 2026-08-31. (The drafted sentence below was shown to him; he endorsed
> this round's attestation as written and evidenced.)

## The drafted sentence — shown to him, endorsed

> *"I attest the integration — the slash commands are the seam; the soft layer only points at the
> engine; the enforcement suite proves it structurally."*

---

- `evidence.md` sha256: `c2f0a9555f09d894eaa739902505e9576801fd822fee58b64e26b098b2f382f1`
- `commission.md` sha256: `bd6d88d8fa0411d0667a81c1c0af8156ba0ab86ab7fb8efa0c4eb443bded591c`
- `phase-card.md` sha256: `4ae26cdb1c1e83adcefd2a5f011fc4acb3456dd96f0aab170b9f8ab1a8f2b94a`
- authored files (sha256): `cellctl 75f1d1cc…` · `enforce.py 4368fb63…` · `surface_contract.py 06773af8…` ·
  `spec.json eb812a88…` · `verify-integration.sh 2e523279…`
- his box at the moment of attesting: `state/gates.jsonl` — 1 record, his plant (`6989a742…`; the
  integration is firmware/binding, not a gate)
- date: **2026-08-31**
