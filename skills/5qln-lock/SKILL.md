---
name: 5qln-lock
description: Lock a desk's configuration to maximum correspondence with the 5QLN code tools (codex, decoder, compiler, corruption); verify and refuse on drift.
---

# 5qln-lock — the correspondence lock

You are a desk in the 5QLN cell. Your configuration must be in **maximum
correspondence** with the 5QLN code tools — not a hand-written approximation.
That correspondence is the fractal itself: a swarm of any size is lawful only
if every agent's config is bound to the same firmware.

## The invariant (what "locked" means)

Your `SYSTEM.md` / `AGENTS.md` must correspond, byte-faithfully, to the code
tools in `/home/deploy/the-cell/rounds/meta-implementation/authored/`:

| config | code tool | must equal |
|---|---|---|
| the seal's five equations | `codex.EQUATION_FORMS` | the accepted forms, line-exact |
| the corruption line | `codex.CORRUPTION_CODES` | exactly `L1 L2 L3 L4 V∅` — no sixth |
| the course line | `codex.COURSE` | `S → G → Q → P → V` |
| the §3.6 surface | `codex.SURFACE_CONTRACT` | all 18 required sections, both markers |
| `PHASE` / `GATE` / `SLOTS` | `codex.PHASE_SLOTS` / `DESK_GATES` | the desk's own letter, gate, slots |

Divergence is **drift** — a "new build" wearing the firmware's clothes. The
lock reports it; it never repairs silently.

## Run the lock before you operate

```sh
python3 /home/deploy/the-cell/skills/5qln-lock/lock.py <YOUR-DESK-LETTER> \
  --system "$(pwd)/SYSTEM.md" --agents "$(pwd)/AGENTS.md"
```

`<YOUR-DESK-LETTER>` is `S`, `G`, `Q`, `P`, or `V` (your seat).

- Exit `0` → `{"status": "locked"}` → you may operate.
- Exit `1` → `{"status": "drift"}` with the failing checks → **refuse to
  operate.** Do not answer the question, do not announce a surface, do not
  hand off. Report the drift (the report's `checks` block names exactly what
  diverged) and stop.

## The discipline

- You verify; you do not regenerate. If your config drifts, the fix is a
  human's or the build's to make — never yours, silently, at runtime.
- A drifted desk that speaks anyway is corruption (L4 Performing). Refusing is
  the lawful move.
- The lock is the same one every desk and every depth runs — one firmware,
  repeated. If it passes here, it passes for the swarm.
