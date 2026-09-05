# The enforcement fixtures — the three pre-integration findings, and the flip (C4)

The pre world (`pre/`) carries the three pre-integration findings the live suite names,
in minimal fixture form (fixture apparatus, clearly labelled — never the production
surface):

| file | finding |
|---|---|
| `pre/plugin/bin/_cell_api.py` | **i** — the plugin's own socket client: `import socket`, `socket.socket(AF_UNIX)`, `sendall` — the second wire |
| `pre/desks/S/.pi/prompts/guide.md` | **ii** — the spawn-authority line: "I must use the spawn tool …" in the soft layer |
| `pre/plugin/bin/cell-attest` | **iii** — `import fractal_ledger` directly (unpinned ledger write) |

`manifest.json` is the fixture census — the mirror of the **extended** seam manifest
(the seam-declaration extension applied): every fixture executable declared, the
re-pointed `cell-attest` declared as a seam importer, the pinned module names from the
seam's own list.

The flip is proven by the selftest, which:
1. runs the enforcement legs over the **pre** world → L1 FAIL (socket tokens), L2 FAIL
   (direct engine import), and the author's spawn-authority scan FAILs the guide line;
2. copies the **authored re-points** (`authored/enforcement/…` — the real deliverables,
   never fixture stand-ins) over the world → L1 zero findings, L2 zero findings, the
   spawn scan clean — **the suite flips to clean only after the re-pointing**.
