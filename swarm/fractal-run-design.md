# The 3-scale fractal swarm — build design (bound B)

The real throw: the school's constitution stone, walked at **three scales** of the
4+1 — one level **up** (the father-frame), the **root** (the school cell), and
**two levels down** (each desk's own 4+1, then one representative branch to the
floor). All agents are **Pi · deepseek-v4-pro · high**, spawned as needed, each
bound to the same firmware by `5qln-lock` before it speaks.

## The topology (the address grammar, school anchored at `G`)

`ε` is the empty word; the school sits at `G` — the essence-corner of its field —
so "one level up" (the field) is representable as `ε`, the school's father.

| scale | role | addresses |
|---|---|---|
| **+1 · father-frame (the field)** | centre `S` + 4 corners | `ε`(S) · `G`(the school) · `Q` · `P` · `V` |
| **0 · root (the school)** | centre `G` + 4 desks | `G`(S-role) · `GG` · `GQ` · `GP` · `GV` |
| **−1 · one down** | each desk opens its own 4+1 | `GG`→`GGG,GGQ,GGP,GGV` · `GQ`→`GQG,GQQ,GQP,GQV` · `GP`→`GPG,GPQ,GPP,GPV` · `GV`→`GVG,GVQ,GVP,GVV` (16) |
| **−2 · two down (one branch)** | `GGG` opens its own 4+1 | `GGGG` · `GGGQ` · `GGGP` · `GGGV` (4) |

Distinct nodes ≈ 29 (`ε,G,Q,P,V` = 5 · `GG,GQ,GP,GV` = 4 · 16 · 4). "Father 5 +
root 5 + 16 + 4", `G` counted once.

## Run semantics (one stone, three scales)

The same attested word is thrown at every cell, at every scale:

1. **Descent (top-down).** The field seeds `ε` and fans out to `G,Q,P,V` (the
   school as the field's α). The school seeds `G` and fans out to `GG,GQ,GP,GV`
   (the four lenses). Each desk descends into its own 4+1; one branch (`GGG`)
   descends again.
2. **Fan-out.** Within each cell, the four corners run **in parallel** — distinct
   spawned agents, distinct sessions, each locked to the firmware.
3. **Converge (bottom-up).** The leaves feed their fathers; each father collects
   its daughters' full surfaces (content, never hashes) into one artifact; the
   chain rises `−2 → −1 → 0 → +1`.
4. **The B″.** The school's `GV` (Value) crystallizes the constitution — the
   seed enriched by the descent (its own α/φ⋂Ω/∇ recursed) and the ascent (the
   field that contains it). `No V without ∞0′`.

## Spawn plan (as needed, not reused)

- One **fresh Pi agent per node**, booted with `herdr agent start <name> --kind
  pi --pane <pane> -- --skill 5qln-lock`, charter auto-loaded from the desk's
  `.pi/APPEND_SYSTEM.md`.
- Each agent runs `lock.py <letter> --system SYSTEM.md` and **refuses on drift**
  (exit 1) before it answers.
- Panes: the cell workspace holds the podium + 5 desk panes; split more panes as
  the fan-out needs them. Peak fan-out = 16 (scale −1), but the walk can wave it
  (4 per cell) if pane capacity binds — bound B keeps the structure, not a fixed
  pane count.
- Parallelism is **within a fan-out group**; descent/ascent is sequential by
  scale. The swarm-ness is the many distinct spawned agents converging, not one
  model prompted four times.

## What must hold for this to be a real swarm (the gate)

- ≥ 2 distinct spawned agents ran **in parallel** (not serialized) — observable
  on the server.
- The descent was actually walked (addresses at scale −1 and −2 produced real
  surfaces), not flattened.
- The converge **reduced** — the school's B″ says something none of the 29 parts
  said alone (case-study `08` criterion).

## Build order

1. `swarm/fractal_conductor.py` — the multi-scale walk: spawn → lock → fan-out →
   descend → converge → record (reusing `orchestrate.Orchestrator` + the corrected
   session read, never re-authoring the engine).
2. Re-arm the ledger/trail; plant the stone (already planted: `nodes/_/question.md`).
3. Spawn + lock + run + converge.
4. Read B″/∞0′, log the run, correct the record.
