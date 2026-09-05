#!/usr/bin/env python3
"""desk_harness — the bindings round's fixture desk harness BINDING
(declared fixture apparatus, H-R08-1): the pinned R06 desk harness
through the seam — a deterministic fake desk box speaking the REAL
herdr dialect on its own socket, with the unconstituted-desk
``agent_not_found`` case and the absent-socket path.  Imported by the
seam, never re-authored; this file binds the two cases the commission
names as fixture deliverables.
"""

from __future__ import annotations

import sys

sys.dont_write_bytecode = True

from surface_contract import (  # noqa: E402
    DeskHarness,
    PANES,
    absent_socket_path,
)

__all__ = ["DeskHarness", "PANES", "absent_socket_path",
           "DESK_LABELS", "unconstituted_case", "absent_socket_case"]

# The four desk letters, read from the pinned harness's own pane list
# (data, never a hard-coded set beyond the harness's own labels).
DESK_LABELS = tuple(sorted(
    pane["label"] for pane in PANES
    if (pane.get("label") or "") in ("G", "Q", "P", "V")))

# The two named cases (the commission's fixture list):
#   unconstituted — one desk holds no agent: the engine reports
#                   agent_not_found (a hold), never a stand-in;
#   absent socket — live_socket points nowhere: /states reads
#                   {"status":"absent"} honestly (C2).
UNCONSTITUTED_DESK = "G"


def unconstituted_case():
    """(constituted set, note) — the unconstituted-desk case: every
    desk except UNCONSTITUTED_DESK is constituted."""
    return (tuple(letter for letter in DESK_LABELS
                  if letter != UNCONSTITUTED_DESK),
            "one desk holds no agent — the engine holds agent_not_found")


def absent_socket_case(work_dir):
    """The absent-socket path for a scratch work dir."""
    return absent_socket_path(work_dir)
