# The enforcement reconciliation — the three findings, re-pointed (C4)

The live suite's verdict (re-run before authoring) names exactly these findings —
they are re-pointed here, never commented out, never allowlisted away, never tuned down:

| # | live finding | the re-point |
|---|---|---|
| i | `plugin/bin/_cell_api.py` — `import socket`, `socket.socket(AF_UNIX)`, `sendall` (a second wire) | `plugin/bin/_cell_api.py` reduced: the socket client is GONE. The plugin's reads are re-served over the platform CLI's declared READ verbs (`workspace list · pane list · api snapshot · api schema`) — the wire work happens inside the platform binary, which is the platform, not the soft layer. No arbitrary-method path, no write verb reach: the module's whole surface is the fixed read verbs. The four consumer bins are re-pointed to it (below). |
| ii | `desks/{S,G,Q,P,V}/.pi/prompts/guide.md` — "I must use the spawn tool" (spawn authority in the soft layer) | `desks/*/.pi/prompts/guide.md` §5 re-fenced: conduction is `/conduct` (§2/§3, unchanged — they already say the conductor never re-derives the walk), and the spawn line is moved under an explicit **deferred — D1 un-decided** fence (H-R08-3): no desk spawns, a spawn request holds, the 2026-08-30 notes are recorded as data for D1's decision, never presented as the walk. |
| iii | `plugin/bin/cell-attest` — `import fractal_ledger` directly (unpinned ledger write) | `plugin/bin/cell-attest` re-pointed: the ledger now arrives **through the declared seam path** — `import surface_contract` (the sha-pinned R07 contract; the import IS the pin check, a drifted pin refuses before any byte) and `fractal_ledger = sc.ledger`. The TTY guard, the seal, the exit codes, and the record fields are unchanged. |

## The consequence the reduction forces, handled honestly

Removing the wire retires the plugin's write-by-wire path, so every consumer bin is
re-pointed in the same reconciliation (a working cell, not just a clean scan):

* `cell-attest` — reads re-served; ledger via the seam contract (finding iii above).
* `cell-zoom` — pure read before, pure read after: reads re-served, nothing else changed.
* `cell-on-desk-state` — pure recorder before, pure recorder after: reads re-served.
* `cell-begin` — its standing-check (read-only) is re-served and still protects a live
  cell; its RAISE (workspace.create + layout.apply) was a write behind the removed wire —
  a drive capability the soft layer may not carry — so the raise now REFUSES out loud
  (exit 9) and points to the platform's own verbs for a human to use.  The cell is
  already standing; re-raising was always a human's decision.

## The census extension (declared data, never hidden)

`seam-declaration-extension.patch` extends R07's seam DECLARATIONS — the census entry for
the new podium renderer (`cell-podium`), the declared-importer entry for the re-pointed
`cell-attest` (its seam import), and the declared extension root for the `pi-cell` package.
This is the extension R07's own seam comment anticipates ("the W5 bindings extend it — an
extension not declared here = FAIL").  It re-authorizes no logic.

## Noted gap (recorded, not worked around)

The current enforce.py pattern lists (hard-coded in R07's attested file, which this round
does not edit) do not match the spawn-tool literal; the re-point therefore removes the
spawn authority at its source (the guides) rather than papering over the scanner.  The
declaration data (`L1_DECLARATION.forbidden_patterns`) already carries the intent; wiring
the scanner to consume that data is a small future enforcement edit, recommended in the
phase card.
