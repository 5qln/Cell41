# ATTESTATION — R03 · B2 the driver (one cell, sequential)

*Amihai's act. One sentence in his own words, and the sha256 of what he attested. Nothing in this file is
written by the machine except the material below the line, which is here so he knows exactly what he is
putting his word to.*

---

## What he ran, by his own hand

```
bash /home/deploy/b2-block.sh
```

Its output, from his own cell (the machine ran the identical script first — this is what it showed):

```
1. your ledger, before      : 6989a742f57ec60a… (611 bytes)

2. the driver boots against YOUR cell:
   REFUSED  : TrustError
   because  : trust assertion failed for desk 'G' at 'instruction' (missing):
              the instruction block (phase-gate) is not authored for desk 'G'
   stage    : instruction / verdict: missing
   meaning  : no desk on this box is constituted per §7 (no Pi extension is
              installed), so the driver refuses before sending anything.

3. your desks still read by label, through the same adapter (a read):
   {"G": "w8:p3", "P": "w8:p6", "Q": "w8:p5", "S": "w8:p2", "V": "w8:p4"}

4. your ledger, after       : 6989a742f57ec60a…
   your ~/.pi settings      : unchanged

VERDICT: nothing was written — your ledger is byte-identical
```

## What is being attested

That **B2 — the driver — does what B2 was commissioned to do**, on the evidence of an execution record
written by the non-author:

- a full `y → z → a → b` walk, every gate held until *his* attestation record exists (C1);
- no gate opens without one, and **every refusal is recorded** (C2);
- a duplicated prompt yields **one** record, including from a second process (C3);
- the trust assertion **fails the boot** when a desk is not constituted — proven on his own cell, above,
  with zero writes and nothing appended (C4);
- prompt → fence → read → propose, the fence a unique end marker read via `pane.wait_for_output` (K1);
- the `turn_key` formula of §5.1 (K2); the Pi lens fails closed seven ways (K3);
- the driver **never types, implies or infers an attestation** (K4);
- **no machine write path to the podium** — statically, on the wire, and against a live pane really
  labelled `podium` (K5);
- the six lenses, and a live tier that confirmed three schema-derived claims against a real herdr server.

**What is NOT being attested:** that a real desk has ever answered a real prompt (no desk is constituted
yet — that is an un-slotted phase), and nothing about B3–B6.

## The drafted sentence — his to change, delete, or replace

> *"I attest B2: the driver takes a turn and refuses to advance without my word."*

**He may say it differently, or say only "attest it". The machine never types his word for him.**

## His word — recorded exactly as he gave it

> **"attest it"**

*He was shown the drafted sentence and chose his own shorter form. The machine did not type it for him,
and the drafted sentence is left above unchanged so the record shows what he was offered and what he
actually said.*

---

- `evidence.md` sha256: `6bdeb15dae3e66d7fff5cac538b21dff162f43a280f745b070cbf9486e9649c5` (18,252 B)
- `commission.md` sha256: `d35ddfba364601f7e6b585a2027909959309bbd61ec9dee39713c7c1da183626`
- `correction-1.md` sha256: `6728cd0edefb5586e18bfd37c421d537846320d434f23da957816c04b24a7b7e`
- corrected artifact: `instrument.py` `159c78c12328c8fb…` · `driver.py` `397f93fc0ae01ab0…` ·
  `lens.py` `ad46b895dc3ceb68…` · `selftest.py` `e0ac260f5c12e093…` · `phase-card.md` `80be74a35ff17d68…`
- unchanged from R02's attested files: `walker.py` `5889160a15c5bc69…` · `dialects.py` `9ebc6d314bd265e5…`
- his cell at the moment of attesting: `state/gates.jsonl` `6989a742f57ec60a…` — **1 record, his plant,
  byte-identical to before the round**
- date: **2026-08-27**

