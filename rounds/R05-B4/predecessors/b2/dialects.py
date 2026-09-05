#!/usr/bin/env python3
"""dialects — the three-dialect mapper (R02 · B1, K3, K4).

Pure functions only: no I/O, no socket, no import of anything beyond the
dataclass machinery.  Each runtime's native "needs a human" signal
(commission §4.4) maps to the one verdict BLOCKED; anything else — a
non-blocked signal, an absent field, an unknown payload, ``agent_status
"unknown"`` — maps to NO_VERDICT.  The mapper can never produce an
attestation verdict: there is no such verdict here, and no code path in
this module can invent one (K4).

The cell's MOVING axis verdict DOMINATES: a cell verdict of MOVING forces
BLOCKED no matter what the runtime dialect says, and a cell verdict of
STASIS/absent contributes nothing — it can never clear a runtime BLOCKED
(§4.4: "MOVING dominates, stop-and-surface").

Verdicts carry ``signals`` — reference strings naming the dialect signal
that said blocked (a reference, never content) — so the walker can put
dialect identity into a record's payload_ref without copying any pane
content.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "Verdict",
    "BLOCKED",
    "NO_VERDICT",
    "DIALECTS",
    "map_signal",
    "dominant",
]

# Reference strings (references only — never content, §4.7.5).
_SIGNAL_HERDR = "herdr:agent_status"
_SIGNAL_PI_TERMINATE = "pi:terminate"
_SIGNAL_PI_CONFIRM = "pi:ctx.ui.confirm"
_SIGNAL_DSH_STATE = "dsh:gate_state"
_SIGNAL_DSH_APPROVAL = "dsh:approval"
_SIGNAL_DSH_HELD = "dsh:held"
_SIGNAL_CELL = "cell:moving"


@dataclass(frozen=True)
class Verdict:
    """The one result shape of map_signal.

    name:   "blocked" | "no_verdict" — nothing else exists.
    signals: reference strings naming the dialect signal(s) that said
             blocked (empty for no_verdict).
    detail:  a human-readable reason (e.g. the raw agent_status seen),
             never pane content."""

    name: str
    signals: tuple = ()
    detail: str = ""

    @property
    def is_blocked(self):
        return self.name == "blocked"


# The one verdict all three dialects collapse to (§4.2, §4.4).
BLOCKED = Verdict("blocked")

# "No signal says blocked" — the honest non-verdict.  It is NOT "clean":
# absence, "unknown", and truncated payloads land here too (lens 3).
NO_VERDICT = Verdict("no_verdict")

DIALECTS = frozenset(("herdr", "pi", "dsh", "cell"))


def _no_verdict(detail):
    return Verdict("no_verdict", (), detail)


def map_signal(dialect, payload):
    """map_signal(dialect, payload) -> Verdict.

    Total and pure: it never raises, never touches I/O, and never returns
    anything but BLOCKED or a no_verdict (K4: fuzz-robust).  Payloads are
    the §4.4 signal shapes of each runtime.

    herdr: agent_status == "blocked" (as seen via agent.get / pane.get).
    pi:    terminate is True, or a ctx.ui.confirm is present.
    dsh:   gate state "held-pending", or approval "failed" (fails closed),
           or a held SID.
    cell:  the MOVING axis verdict: axis_verdict/verdict == "MOVING" or
           moving is True.
    """
    if dialect == "herdr":
        if isinstance(payload, dict):
            status = payload.get("agent_status")
            if status == "blocked":
                return Verdict(
                    "blocked", (_SIGNAL_HERDR,),
                    "herdr agent_status == 'blocked'")
            return _no_verdict(
                "herdr agent_status %r is not 'blocked'" % (status,))
        return _no_verdict("herdr payload is not an object")
    if dialect == "pi":
        if isinstance(payload, dict):
            if payload.get("terminate") is True:
                return Verdict(
                    "blocked", (_SIGNAL_PI_TERMINATE,),
                    "pi tool returned terminate: true")
            ctx = payload.get("ctx")
            if isinstance(ctx, dict):
                ui = ctx.get("ui")
                if isinstance(ui, dict) and "confirm" in ui:
                    return Verdict(
                        "blocked", (_SIGNAL_PI_CONFIRM,),
                        "pi asked ctx.ui.confirm")
            return _no_verdict("pi payload carries no blocked signal")
        return _no_verdict("pi payload is not an object")
    if dialect == "dsh":
        if isinstance(payload, dict):
            if (payload.get("state") == "held-pending"
                    or payload.get("gate_state") == "held-pending"
                    or payload.get("status") == "held-pending"):
                return Verdict(
                    "blocked", (_SIGNAL_DSH_STATE,),
                    "dsh gate state is held-pending")
            if payload.get("approval") == "failed":
                return Verdict(
                    "blocked", (_SIGNAL_DSH_APPROVAL,),
                    "dsh approval failed closed")
            held = payload.get("held")
            if isinstance(held, str) and held.strip():
                return Verdict(
                    "blocked", (_SIGNAL_DSH_HELD,),
                    "dsh relay reported a held SID")
            return _no_verdict("dsh payload carries no blocked signal")
        return _no_verdict("dsh payload is not an object")
    if dialect == "cell":
        if isinstance(payload, dict):
            if (payload.get("axis_verdict") == "MOVING"
                    or payload.get("verdict") == "MOVING"
                    or payload.get("moving") is True):
                return Verdict(
                    "blocked", (_SIGNAL_CELL,),
                    "cell axis verdict is MOVING")
            return _no_verdict(
                "cell axis verdict %r is not MOVING"
                % (payload.get("axis_verdict"),))
        return _no_verdict("cell payload is not an object")
    return _no_verdict("unknown dialect %r" % (dialect,))


def dominant(*verdicts):
    """Combine verdicts with the cell's MOVING axis dominating.

    Any BLOCKED wins — so a cell MOVING→BLOCKED forces BLOCKED whatever
    the runtime dialect says, and a cell STASIS/absent verdict can never
    clear a runtime BLOCKED (§4.4).  Blocked signal references are merged,
    so two dialects reporting blocked for the same desk in the same tick
    collapse to ONE verdict (one hold, not two — §2 episode rule)."""
    blocked = [v for v in verdicts if isinstance(v, Verdict) and v.is_blocked]
    if blocked:
        signals = []
        details = []
        for v in blocked:
            signals.extend(v.signals)
            if v.detail:
                details.append(v.detail)
        return Verdict("blocked", tuple(signals), " | ".join(details))
    details = [v.detail for v in verdicts
               if isinstance(v, Verdict) and v.detail]
    return Verdict("no_verdict", (), " | ".join(details) or "no signal")
