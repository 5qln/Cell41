# The fixtures (the commission's fixture list, one per deliverable)

All fixture apparatus here is **declared fixture fiction** — deterministic, stdlib-only,
never the production surface, never the live box, never the live ledger (H-R08-1).

| deliverable | fixture |
|---|---|
| fake `cellctl` | `fake_cellctl.py` — the 13 subcommands, the declared serialization, the exit-code convention, the flock run lock and turn_key idempotency emulated (declared in its header), **absent + malformed cases** honest (the sha256 of empty named for empty files). Journals every invocation (`CELLCTL_JOURNAL`). |
| fixture desk harness | `desk_harness/` — the pinned R06 harness through the seam: the **unconstituted-desk `agent_not_found`** case and the **absent-socket** case, driven through the REAL `cellctl` with the binding's exact argv. |
| enforcement fixtures | `enforcement/` — the **three pre-integration findings** in `pre/`, the extended census in `manifest.json`; the selftest proves the suite **flips to clean only after** the authored re-points are applied. |
| cold restart | `cold_restart/run_conduct.py` — a NEW process re-arms from disk alone (the second run observes the same turn_key, never re-runs) and a concurrent second `/conduct` **blocks on the run lock** rather than interleaving (C5). |
| byte round-trip | `byte_round_trip/needle_args.json` — `∞0′ → ‖` pushed through tool/action string fields (tool args, inline JSON, file paths); the fake echoes verbatim and the selftest asserts byte equality. |

Plus: `probe.mjs` (the executable twin of the pi binding — imports the same
`pi-cell/src/cellctl.mjs` the extension runs, so the tested code IS the delivered code),
`build.py` (the scratch-world builders), `scenarios/binding-needle.json` (a needle-bearing
scenario file).
