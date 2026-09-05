---
name: cell-run
description: One-command trigger to re-run the 5QLN fractal swarm on Herdr against the word ALREADY planted — verify the cell, reset state, spawn fresh Pi agents, and report the composed B″ + ∞0′ — without re-deriving the bridge. Use ONLY when the human says "run the cell", "run the swarm", or "run a fractal run" AND means a one-shot re-execution of the existing word. This command NEVER takes a new question — if the human wants to give their own word, hand back to fractal-bridge-herdr.
---

# cell-run — the one-command trigger

You are **running an already-planted cell**, not re-arming it. For the grammar,
the cell map, the plant workflow (speak → articulate → approve → relay), and the
post-run checklist, load `fractal-bridge-herdr`. This skill is only the thin
operational trigger.

## 0. Confirm the mode first — never guess

"run the cell" is ambiguous: the bridge skill (`fractal-bridge-herdr`) also
accepts "run / operate the 5QLN cell or swarm" as a re-arm. Before running, if
there is ANY doubt whether the human wants to give a NEW word vs re-run the
already-planted word, stop and ask:

> Do you want to give a new word (→ "be the bridge"), or re-run the word already
> planted in the cell (→ this one-shot run)?

Only proceed once it is clear they mean the one-shot re-run. This command never
accepts a new question.

## The word (the plant)

The run carries the word already planted at `/home/deploy/the-cell/nodes/_/question.md`
— **read it** (read tool), never edit it. If the human wants a NEW word, stop and
hand back to `fractal-bridge-herdr`: the human speaks, you articulate, they
approve, and only then is the word planted. Never substitute a word.

## 1. Verify the cell is live

```bash
herdr status
herdr agent list      # s g q p v — the five desks; names lowercase, labels UPPERCASE
```

Desks should be `idle`. If one is missing, boot it with `herdr agent start`
(never `pane run` + `exec pi`) — exact boot in `fractal-bridge-herdr`.

## 2. Run (one command — reset → spawn → walk → converge → record)

```bash
cd /home/deploy/the-cell && python3 swarm/person_conductor.py --max-depth 2
```

- **default** resets state first: `reset_state` archives+removes the old
  `state/gates.jsonl` + `state/trail.jsonl` so the run starts a clean hash chain.
- `--no-reset` to continue on the existing chain (rare).
- `--max-depth 0` for a fast flat smoke test (no descent).

Conductors, pick by the PLANTED word:

- `person_conductor.py --max-depth 2` — **Lake 7 (default):** the run IS
  self-differentiation — three edges (The Pair / The Presence / The Peers) each a
  full 4+1, opened + converged in parallel waves, composed into ONE form of the
  person (THE CONJUGATION). This walks the CURRENT planted word.
- `granular_conductor.py --max-depth 2` — Lake 6: the FIELD-GRAMMAR word
  (Matter / Consciousness / Innovation) — a historical word, not the current plant.
- `navigation_conductor.py --max-depth 2` — adaptive depth (the first field-grammar word).
- `fractal_conductor.py --depth 2` — the fixed 3-scale walk (the constitution word).

This is a real swarm on Herdr — fresh `pi` agents (`deepseek-v4-pro` @ high),
each locked to the firmware, fanned out in parallel; ~10–15 min. Run it in the
**background** and monitor the `[NAV] node=… move=… because=…` lines.

## 3. Read the result

```bash
python3 -c "import json; d=json.load(open('/home/deploy/the-cell/swarm/person-run-result.json')); r=d['results']; print('STATUS', d.get('status'), d.get('ended_in')); print('--- SCHOOL_B ---'); print(r.get('SCHOOL_B')); print('--- FIELD_B ---'); print(r.get('FIELD_B'))"
```

- **`results.SCHOOL_B`** — the school's B″ (the composed form of the person — THE CONJUGATION).
- **`results.FIELD_B`** — the final B″ across scales, closing in the `∞0′` return question.
- **`swarm/axis.jsonl`** — the ∞0′ threading (incoming → outgoing), cycle to cycle.
- **`swarm/navigation.jsonl` / `navigation.log`** — the `[NAV]` decision trail.

## 4. Report + record

Report faithfully: the word asked · the α · the B″ · the ∞0′ · turns/timing ·
what held (if anything) · honest caveats (one model; parallelism waved). Then run
the **post-run checklist** (log → journal → case-study → skill → re-mirror) — the
five steps live in `fractal-bridge-herdr`; do not skip them.

## Hard floors (from prior sessions — do not re-derive)

- The agent is `pi`; the only model is `deepseek-v4-pro` @ `high`.
- Read answers from the agent's OWN session file, never the pane.
- Trust must be granted: `defaultProjectTrust: "always"` in `~/.pi/agent/settings.json`.
- A desk that **holds** is a signal, not a failure — carry it honestly, never fake a surface.
