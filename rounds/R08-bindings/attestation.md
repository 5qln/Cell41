# ATTESTATION — R08 · the bindings · the hard↔soft link

*Amihai's act. One sentence in his own words, and the sha256 of what he attested. The machine wrote the
material below the line so he knows exactly what he is putting his word to; it never types his word for him.*

---

## What was run, and what it showed

The verifier (Hermes `herdr`, the non-author) executed dsh's artifact independently and recorded the
result in `evidence.md`:

- **Fence clean** — byte-identical before/after; zero files touched outside `authored/`.
- **Author's suite** — 38/38, and it drives the **real** `cellctl` + the **real** R07 `enforce` module
  (not a re-implementation).
- **Enforcement, live cell (pre re-point)** — `verify-integration.sh` reads **FAIL, exactly as the
  diagnosis predicted** (L1 socket-client · L2 census · L3 PASS) — the three findings are real, the suite
  is honest; `gates_plant` PASS and `plan-equivalence` PASS (byte-identical).
- **Independent capability scan** — zero forbidden tokens remain in the re-pointed code; the socket is
  gone, conduction is re-pointed to `/conduct`, the spawn line is fenced *deferred — D1*, `cell-attest`
  writes the ledger through the pinned `surface_contract` (the import IS the pin check).
- **Independent brick decode** — `cellctl word` over `bricks/methods/sgqpv-cycle/word.json` → `status: ok`;
  seed ref = his plant's sha256.
- **His plant** — `6989a742…`, byte-for-byte, untouched.

## What is being attested

That **the bindings — the hard↔soft link — do what they were commissioned to do**, on the evidence of an
execution record written by the non-author (`evidence.md`, **C1–C8 · K1–K5 · six lenses, zero
corrections**):

- the **soft layer only points at the engine through slash commands** — one tool/action = one `cellctl`
  call, no socket, no engine import (C1, C7);
- the **write side is never exposed** (C2), and **the binding adds nothing** — plan-equivalence
  byte-identical (C3);
- the **three findings are re-pointed, never allowlisted** (C4);
- the **run lock is honoured** (C5) and **fail-closed** holds — absent/empty/malformed never read valid,
  never clean (C6);
- **the LEGO requirement** — 13 independent studs, the method is the brick (data the engine reads), a new
  method = a new brick with zero re-authoring, the swarm reachable with zero firmware change (C8);
- stdlib/deterministic/no-LLM (K1) · byte-exact (K2) · the click stays the human's (K3) · the B2 guards
  hold (K4) · method/table/manifest are diff-able data (K5);
- the six lenses, including cold-restart, absence-never-valid, encoding, and blind-tool INCONCLUSIVE.

**What is NOT being attested:** that any live desk was prompted (H-R08-1, fixture-only — the first paid
`/conduct` is Amihai's alone to authorize, W4) · that the re-points are yet *deployed* to the live cell
(recorded as the closing act below) · command/package/round names (D4) · spawn ownership (D1, deferred) ·
the look-and-feel skin (H-R08-6, a later round). The design decision that `cell-begin` refuses the raise
(D14-3) is a declared divergence carried for his attention.

## His word — recorded exactly as he gave it

> **"attest it"** — Amihai Loven, 2026-08-31. (The drafted sentence below was shown to him; he endorsed
> this round's attestation as written and evidenced.)

## The drafted sentence — shown to him, endorsed

> *"I attest the bindings — the soft layer only points at the engine through slash commands, the three
> findings are re-pointed never allowlisted, the method is a brick the engine reads, and the podium shows
> the formation trail. PASS, zero corrections."*

---

- `evidence.md` sha256: `edbf9c52cab265de757c3087020c95bd91a6c233690b2fc4699dacbd1114b492`
- `commission.md` sha256: `7e9a69d478105837ebd820488559286b69c4ae860916721f07f67982fdbd00a7`
- `phase-card.md` sha256: `f7e50aaee766d64910e3c0caed94ec5b5342b95179235c40f7e8969ea92b77d4`
- authored tree manifest sha256: `a7ac593841c26030b70dc1a96479b52544c106449976eee62a6f39250d95bb8f`
- representative authored files: `selftest.py 5b3d1251…` · `tool-table.json 40571d2e…` ·
  `cellctl.mjs bef93da6…` · `addendum.toml 9b463ce5…` · `cell-podium c95e87c5…` ·
  `_cell_api.py 5b2c2274…` · `cell-attest d749fb6f…` · `word.json 2169f311…`
- his box at the moment of attesting: `state/gates.jsonl` — 1 record, his plant (`6989a742…`; the
  bindings are a link, not a gate)
- date: **2026-08-31**
