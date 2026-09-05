# The human binding — conduction plugin actions (manifest addendum)

Eight conduction actions appended to `plugin/herdr-plugin-v4.toml`
(`herdr-plugin-v4.addendum.toml`): `conduct · word · plan · materialize · states · trail ·
descent · config`.  **Each `command` is `cellctl` itself with fixed argv — one seam call per
action, argv-only, never through a shell, no TTY guard** (free gestures, exactly like the
existing `begin`/`zoom`).  `plant`/`attest` are unchanged and are deliberately **not**
re-declared here.

## The two caller surfaces are now one surface (SCOPE §0)

| caller | surface | what fires |
|---|---|---|
| the human | plugin action (cell UI / `plugin.action.invoke`) | fixed-argv `cellctl <subcommand>` — the manifest data constants |
| the conductor S | pi slash tool (`pi-cell`) | the same `cellctl <subcommand>`, args from the tool call |

The human's `/conduct` is S's `/conduct`: the identical seam binary, differing only in who
invoked it.  The run lock (C5) is inherited by construction — both callers reach the seam,
and the seam's flock serializes concurrent `/conduct`s on one trail.

## Why fixed argv (the honest mechanics)

Plugin actions are manifest-declared, argv-only — no runtime arguments, no synchronous
stdout (the manual, "Actions don't return output synchronously").  So the scenario-bearing
gestures read their input from **declared data paths** (`state/word.json` — D2, the
acceptance word he plants; `state/decoded-scenario.json` — the declared handoff an operator
saves from `/word`'s logged output).  While D2 is open those paths are **absent**, and the
actions forward the seam's honest `absent` report — INCONCLUSIVE, never a fixture stand-in
(lens 3, lens 6).  The conductor's tools take their paths as arguments, so the pi side has
no such limit; that asymmetry is the platform's, declared here rather than papered over.
`/conduct --plan-only` (decode + plan, byte-identical to the direct calls — C3) remains
reachable on the pi side through the `conduct` tool's `plan_only` parameter.

## Application (data edit, one place — K5)

Append `herdr-plugin-v4.addendum.toml` to `plugin/herdr-plugin-v4.toml`, then re-link the
plugin.  The data constants live in the addendum's header comment — change a path there,
never in code.  A new gesture = a new `[[actions]]` block naming one `cellctl` subcommand.
