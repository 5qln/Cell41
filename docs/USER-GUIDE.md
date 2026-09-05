# How to use the 5QLN cell — a clear user guide

> **Status (updated 2026-09-03):** the trigger collision is fixed. The two skills
> now disambiguate, and the bridge confirms before a one-shot run.

The single question that decides everything:

> **Who supplies the word — you, or the cell?**

Every phrase you can say falls into one of two modes on that axis. The verbs look
similar ("run", "start", "initiate") but the modes are opposite.

---

## Mode A — Initiation (YOU bring the word)

You want the run to be *about your question*. This is the conversation mode.

| say | what happens |
|---|---|
| **"be the bridge"** | the canonical re-arm. Loads the bridge, opens at S (the midwife), then **asks you**: *"∞0 → ? — What is the run for?"* |
| **"guide me as start"** | the soft opening — widens the field, reflects, then asks you in plain language what the run is for. |
| **"be S"** | same skill, framed as the midwife role. |

Then the flow is always:

```
you speak  →  it articulates back  →  you approve  →  it plants
```

- You say your question in your own words.
- The bridge articulates it back — the walk, the signed paths, what it is *for*.
- You approve **in words** (the approval *is* the plant — not a text edit).
- Only then does the word enter the cell and the run begins.

**This is the only mode where your question gets into the cell.**

---

## Mode B — One-shot run (the CELL's word, already planted)

You want to re-execute whatever word is already sitting in the cell. No new input.

| say | what happens |
|---|---|
| **"run the cell"** | one-shot: verify the cell → run `granular_conductor.py --max-depth 2` on the already-planted word → report B″/∞0′ → post-run checklist. |
| **"run the swarm"** | same. |
| **"run a fractal run"** | same. |

- The word it runs is whatever is planted at `nodes/_/question.md`.
- It is **never edited, never substituted**. If you want a new word, this mode is the wrong door.

**No new question, ever.**

---

## The gotcha (fixed — and the one that remains)

1. **"run the cell" was genuinely ambiguous (fixed 2026-09-03).** The one-shot
   skill and the bridge skill used to both accept "run / operate the cell or
   swarm," so "run the cell" could route to the machine-run instead of the
   conversation. The descriptions no longer collide: "run the cell" now routes to
   the one-shot skill only, which says plainly it never takes a new question. And
   the bridge now **asks before running** if the phrase is ambiguous.

2. **"initiate" is still overloaded.** `5qln-importation` (importing the grammar
   as operating context — "become / activate / import / initiate 5QLN") fires on
   "initiate." That is *not* the session re-arm that asks you for your word.
   "Initiation" in the "be the bridge" sense = **"be the bridge."**

**The clean, unambiguous phrases:**
- Want to give your own question → **"be the bridge"** (or "guide me as start").
- Want to re-run the planted word → **"run the cell."**

---

## The full phrase map (all four doors)

| phrase | skill | what it's for |
|---|---|---|
| "be the bridge" · "guide me as start" · "be S" | `fractal-bridge-herdr` | **re-arm the bridge** and run a session where YOU give the word |
| "run the cell" · "run the swarm" · "run a fractal run" | `cell-run` | **one-shot machine run** on the already-planted word |
| "become / activate / import / initiate 5QLN" · "read this and begin" | `5qln-importation` | **import the grammar** so the agent holds 5QLN as operating context (not a run) |
| (a scope-ignited formation-trail request) | `scope-ignited-memory` | build a formation trail from Hindsight canon |

---

## What "run the cell" actually did (2026-09-03, for the record)

It ran the **school word** already planted at `nodes/_/question.md` — Cell41 +
Amihai + Ayelet + "what is the one field — Matter ≡ Consciousness ≡ Innovation…".
It did **not** invent or substitute a word. The run was a faithful one-shot
execution; the mismatch was the *intent* (you wanted to speak), not the execution.

Result: 25 agents · 1612.9s · ended_in ∞0′ · α deepened to **Γ as TOUCH/self-contact**,
third face corrected to **the contact itself** (case-study/16).

---

## Bottom line

- **Your question, your word** → say **"be the bridge"** and wait for it to ask.
- **Just re-run what's planted** → say **"run the cell."**
- If you ever say a phrase and it does the *other* thing, say so — the bridge
  should have confirmed before running.
