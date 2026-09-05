#!/usr/bin/env python3
"""desk_harness — the fixture desk harness BINDING (the integration
round, H-INT-1): re-exports the pinned R06 fixture desk harness
(``predecessors/r06-orchestration/fixtures/desk_harness.py``) — a
deterministic fake desk box speaking the REAL herdr dialect on its
own socket, with the unconstituted-desk ``agent_not_found`` case, the
absent-socket path, and the no-V-without-∞0′ switch.  Imported by
path, sha-pinned, never re-authored; this file is a binding only
(the deliverable's declared name for the pinned module).
"""

from __future__ import annotations

import sys

sys.dont_write_bytecode = True

from surface_contract import (  # noqa: E402
    desk_harness,
    DeskHarness,
    PANES,
    absent_socket_path,
)

__all__ = ["DeskHarness", "PANES", "absent_socket_path", "desk_harness"]
