# The LEGO bricks — the orchestration method as data (C8, K5)

The binding layer is a baseplate of independent studs; the orchestration **method** —
which commands, in what order, under what soft config — is **data the engine reads**,
never code in the binding.  A brick is exactly that data, in three files:

```
methods/<name>/
├── word.json    the scenario word — decoded by word.decode_scenario (cellctl word)
├── spec.json    the cell spec — read by cellctl conduct / walk / states (SPEC_SCHEMA)
└── soft.json    the soft config — read by softconfig.load_soft_config (cellctl config)
```

All three are validated by the engine's own attested readers (the binding never opens
them; nothing in the binding or the seam parses a brick).  The selftest proves each file
is data the engine reads: `cellctl word` decodes `word.json`, the spec validates against
the declared schema, the absent soft.json reads the engine's declared defaults honestly.

## Why the method is not in the binding (C8.1/C8.2)

The engine's composite (`/conduct`) derives the walk from the word's signs itself
(`navigate.plan_walk`) and reads the spec and the soft config itself.  So "which commands,
in what order, under what soft config" is fully expressed by the brick — and a new method
is a **new brick directory, snapped on with zero re-authoring of the seam or the firmware**
and zero change to the bindings (the tools already take arbitrary paths as arguments).

## The learning loop is not precluded (C8.3, D8 output-is-input)

A method that closes honestly and returns a live ∞0′ IS the brick: the run-end's
`return_question` reference becomes the next word's seed ref (`plant:sha256:…`).  Writing
that next `word.json` is a data act — a file the engine reads — so the learning loop
feeding winners back into the soft layer needs no new code anywhere in this round's
surface.  The binding deliberately hard-codes no scenario, no desk order, no cell.

## The swarm is reachable (C8.4)

One firmware, many soft configs: a second cell is a second brick whose `spec.json`
declares its own `work_dir` / `ledger` / `trail` / `soft_config` paths.  Nothing in the
bindings names a cell — the binary path is env data (`CELLCTL_BIN`) and every tool takes
paths as arguments.  A swarm = N bricks, zero firmware change.

## The example brick — `methods/sgqpv-cycle/` (CANDIDATE — D2/D4, his to name)

The single 4+1 cycle: seed at the centre ε → G → Q → P → V → ∞0′.  Its seed ref is the
plant that actually stands at the centre — `plant:sha256:a5935788…` — read from the live
gates plant record (`/home/deploy/the-cell/state/gates.jsonl`, the attested plant of
`nodes/_/question.md`, byte-for-byte).  The word itself is a **candidate demonstration**:
the acceptance word is Amihai's to choose (D2 open), and the engine refuses to run until
he plants it.  `soft.json` is deliberately **absent** — soft mode is the constitution's
act (W3, H-R08-5); an absent file reads the engine's declared defaults, honestly.
