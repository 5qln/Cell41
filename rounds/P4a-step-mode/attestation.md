# ATTESTATION — P4a · the step mode

*Amihai's act. One sentence in his own words, and the sha256 of what he attested. Nothing in this file is
written by the machine except the material below the line, which is here so he knows exactly what he is
putting his word to.*

---

## What he ran, by his own hand

```
bash /home/deploy/the-cell/rounds/P4a-step-mode/verify-live.sh
```

Its output, from his own box (the machine ran the identical script first — this is what it showed):

```
1. the author's own suite (a hypothesis, not a result):
   Ran 60 tests in 3.321s
   OK

2. the live box: no desk is constituted (H-P4a-4), so the boot fails closed:
   REFUSED : TrustError
   meaning : no Pi extension is installed, so no desk is constituted and
             the trust assertion fails closed with INCONCLUSIVE (H-P4a-4).
             That refusal IS the step mode working — the 16/16 evidence
             records it; P4b's desk bundles are what turn it into PASS.

3. the authored bytes the verifier judged (sha256):
   3391b9cac14f56e0d0d7aac954f77864ca84faf8401e36d82d978146e6ef404c  conformance.py
   776ff46393bf81db62841043021c97288e2c1414bec43971d275d1dfbdfac36d  surface.py
   7c02f316969fdc2a6a9825b2ce4cb264976de3c607d8438f58b4b1e94bd26edf  step.py
   2a0dfedc8a2fec4709a0e5687597dba5fa938fc523152edc4b3ce4653ad66628  driver.py
   573b7ea6fd3b3c34f8f6cab617fd55249c3281e2cad054c3d53a5847a19d9b9d  selftest.py
   3051f66fcce46143c78ba351707ff6fb5bf5a6ed145fb115e03ab5f4e03e4a38  phase-card.md
```

## What is being attested

That **P4a — the step mode — does what it was commissioned to do**, on the evidence of an execution
record written by the non-author (`evidence.md`, 16/16 PASS, zero corrections):

- the same code path, stepped, as the attested B2 driver (C1);
- the step suspends before the first side effect, and a FAIL stops the session (C2);
- every step emits address, zoom, checks, decode, compile and its next move (C3);
- every check cites its source verbatim and catches its defect (C4);
- two trails never merged, and a cold restart rebuilds state from disk alone (C5);
- no depth cap, no root assumption, an extensible alphabet (K1);
- stdlib only, deterministic, no LLM in the checks (K2);
- the human's click is the only authenticity verdict — never the machine's (K3);
- the centre, the attestation and the keypress hold under stepping (K4);
- descent is reserved, not implemented (K5);
- novelty only in the Appendix-D jacket (K6);
- the six lenses, including the live H-P4a-4 no-desk refusal shown above.

**What is NOT being attested:** that a real desk has ever answered a real prompt (no desk is constituted
yet — that is P4b), and nothing about B3–B6.

## The drafted sentence — his to change, delete, or replace

> *"I attest P4a: the step mode keeps the flow to the exact operational fractal — the same code path,
> stepped, with the human's click the only authenticity verdict."*

**He may say it differently, or say only "attest it". The machine never types his word for him.**

## His word — recorded exactly as he gave it

> **"attest it!"**

*He was shown the drafted sentence and chose his own shorter form. The machine did not type it for him,
and the drafted sentence is left above unchanged so the record shows what he was offered and what he
actually said.*

---

- `evidence.md` sha256: `9dc748186d57c894f340d462f6218a233da0bfbe4892fd69c178577c6fc2d76f`
- `commission.md` sha256: `e6b22c7f0dc9e328f8dfc19e63ab345c1df5a6b8360b3416ed73dab4c416636b`
- authored files: the six hashes above
- his box at the moment of attesting: `state/gates.jsonl` — **1 record, his plant**
- date: **2026-08-29**
