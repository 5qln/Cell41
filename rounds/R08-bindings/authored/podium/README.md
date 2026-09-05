# The podium re-point — the smart ledger (content only, H-R08-6)

The podium pane stops rendering `question.md` and renders `state/trail.jsonl` — the
formation trail, the cell's smart ledger.  Two artifacts:

| file | role |
|---|---|
| `cell-podium` | the read-only renderer: shells `cellctl trail --ledger … --trail …` (one seam call per refresh), prints one display line per trail event — human and desk interleaved, read_trail's field shape, references only (D12: never the desk's text) |
| `manifest-pane-repoint.toml` | the replacement `[[panes]]` block — `watch -n 2 cell-podium --ledger … --trail …`, argv-only, no shell (the seal property unchanged) |

## Honesty on the glass (C6, lens 3, lens 6)

* **absent trail** → `no trail yet — no /conduct has run on this cell; INCONCLUSIVE, never a stand-in`
* **empty trail** → `EMPTY — sha256 e3b0c44298fc… — an empty file never reads valid`
* **damaged / broken chain** → INCONCLUSIVE banner + the complete prefix, shown as-is
* **mid-run torn tail** → flagged, discarded, never a line
* **unreachable seam** → `status: UNREACHABLE … INCONCLUSIVE, never a stand-in` + the raw stderr tail

The renderer contains no trail logic, no ledger logic, no socket code, no record-writing,
no engine import (C7) — the classification is the engine's, delivered through the seam, and
printed, never re-derived.  It writes nothing: no write path to the podium exists anywhere
in this round.

## What is NOT in this round

The theme, sidebar, toasts and the pane title's final wording are the interface round's
(H-R08-6) — this round only re-points the content.  `question.md` itself is untouched: the
human's plant still writes it; where the planted question is displayed alongside the trail
is the skin round's layout decision.
