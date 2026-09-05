#!/usr/bin/env python3
"""lock.py — the 5qln-lock verifier (one firmware, repeated).

Prove that ONE desk's configuration is in maximum correspondence with the
5QLN code tools: the codex's sealed carrier (COURSE, DESK_GATES), the
conformance table (EQUATION_FORMS, CORRUPTION_CODES), and the §3.6
surface contract (SURFACE_CONTRACT / PHASE_SLOTS).

This is the fractal invariant, made executable: a swarm of any size is
lawful iff every agent's config passes this lock. Divergence is reported
as drift — never repaired silently (a write path is a bigger claim; this
skill verifies, and the human/agent decides what to do on drift).

Deterministic, stdlib-only (plus the pinned codex): no network, no LLM,
no wall-clock in logic. Exit 0 = locked; exit 1 = drift.

Usage:
    python3 lock.py [DESK] [--system PATH] [--agents PATH]

    DESK      S|G|Q|P|V  (default: inferred from the current directory name)
    --system  path to the desk's SYSTEM.md  (default: <desk-dir>/SYSTEM.md)
    --agents  path to the desk's AGENTS.md  (default: <desk-dir>/AGENTS.md)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_AUTHORED = os.path.normpath(os.path.join(
    _HERE, "..", "..", "rounds", "meta-implementation", "authored"))

sys.path.insert(0, _AUTHORED)
import codex  # noqa: E402  (the sealed carrier; sha-pinned on import)

COURSE = list(codex.COURSE)
DESK_GATES = dict(codex.DESK_GATES)
CORRUPTION_CODES = set(codex.CORRUPTION_CODES)
EQUATION_FORMS = {k: [f["form"] for f in v]
                  for k, v in codex.EQUATION_FORMS.items()}
PHASE_SLOTS = {k: list(v) for k, v in codex.PHASE_SLOTS.items()}
CONTRACT = codex.SURFACE_CONTRACT
OPEN = CONTRACT["open_marker"]        # ⟦SURFACE v1⟧
CLOSE = CONTRACT["close_marker"]      # ⟦END SURFACE⟧
REQUIRED = list(CONTRACT["required_sections"])


def _desk_from(path):
    base = os.path.basename(os.path.normpath(path))
    if base.upper() in COURSE:
        return base.upper()
    return None


def _read(path):
    try:
        with open(path, "rb") as handle:
            return handle.read().decode("utf-8")
    except OSError as exc:
        return None


def _check_seal(text, desk):
    """The constitutional block: course, completion, five corruption codes,
    and the five equations (each an accepted form)."""
    out = {}
    m = re.search(r"## The seal.*?```\n(.*?)```", text, re.S)
    seal = m.group(1) if m else ""
    out["course"] = ("S → G → Q → P → V" in seal) and \
        (COURSE == ["S", "G", "Q", "P", "V"])
    out["completion"] = "No V without ∞0'" in seal
    codes_line = [ln for ln in seal.splitlines()
                  if ln.strip().startswith("L1")]
    out["corruption"] = bool(codes_line) and \
        set(codes_line[0].split()) == CORRUPTION_CODES
    eqs = []
    seal_lines = [ln.strip() for ln in seal.splitlines()]
    for letter in COURSE:
        present = any(ln in EQUATION_FORMS[letter] for ln in seal_lines)
        eqs.append((letter, present))
    out["equations"] = eqs
    out["equations_ok"] = all(p for _, p in eqs)
    return out, seal


def _check_surface(text, desk):
    """The §3.6 surface: both markers, all required sections, PHASE == desk,
    GATE == the desk's gate, EQUATION == an accepted form, SLOTS == the
    phase slots."""
    out = {}
    start = text.find(OPEN)
    end = text.find(CLOSE, start + len(OPEN)) if start != -1 else -1
    out["markers"] = (start != -1 and end != -1)
    body = text[start + len(OPEN):end] if out["markers"] else ""
    lines = [ln.rstrip("\r") for ln in body.split("\n")]
    headers = set()
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        for req in REQUIRED:
            if s == req or s.startswith(req + ":"):
                headers.add(req)
                break
    out["missing_sections"] = sorted(set(REQUIRED) - headers)
    out["sections_ok"] = not out["missing_sections"]
    m = re.search(r"^PHASE:\s*([SGPQV])$", body, re.M)
    out["phase"] = m.group(1) if m else None
    out["phase_ok"] = out["phase"] == desk
    m = re.search(r"^GATE:\s*(\w+)$", body, re.M)
    out["gate"] = m.group(1) if m else None
    out["gate_ok"] = out["gate"] == DESK_GATES.get(desk)
    m = re.search(r"^EQUATION:\s*(.+)$", body, re.M)
    eq = m.group(1).strip() if m else ""
    out["equation_ok"] = any(eq == f for f in EQUATION_FORMS[desk])
    # SLOTS: each declared phase slot is named in the SLOTS section.  The
    # section runs from the SLOTS header to the next required-section header
    # (or the close marker).  A slot line like "Y:" is a single capital
    # letter, not a section header — it must not terminate the section.
    slots_body_lines = []
    in_slots = False
    for ln in lines:
        s = ln.strip()
        if in_slots:
            if s == CLOSE or any(s == r or s.startswith(r + ":")
                                 for r in REQUIRED):
                break
            slots_body_lines.append(s)
        elif s == "SLOTS" or s.startswith("SLOTS:"):
            in_slots = True
    slots_body = "\n".join(slots_body_lines)
    out["slots_ok"] = all(sym in slots_body for sym in PHASE_SLOTS[desk])
    return out


def _check_compact(text, desk):
    """A materialized child cell's compact SYSTEM.md (⟦SYSTEM v1⟧): LAW,
    EQUATION (line-exact against the firmware), SEAT / OPERATION / HAND-OFF
    present.  These cells are emitted from grammar.PHASE, so the check is a
    self-consistency lock — the same firmware, verified the same way."""
    out = {}
    out["markers"] = "⟦SYSTEM v1⟧" in text and "⟦END SYSTEM⟧" in text
    out["law"] = "LAW: H = ∞0 | A = K" in text
    m = re.search(r"^EQUATION:\s*(.+)$", text, re.M)
    eq = m.group(1).strip() if m else ""
    out["equation"] = eq
    out["equation_ok"] = eq in EQUATION_FORMS[desk]
    out["seat"] = "SEAT:" in text
    out["operation"] = "OPERATION:" in text
    out["handoff"] = "HAND-OFF:" in text
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("desk", nargs="?")
    ap.add_argument("--system")
    ap.add_argument("--agents")
    args = ap.parse_args()

    desk = (args.desk or _desk_from(os.getcwd()) or "").upper()
    if desk not in COURSE:
        print(json.dumps({"status": "drift", "reason":
                          "desk %r is not one of S G Q P V" % desk}))
        return 1

    system_path = args.system or os.path.join(os.getcwd(), "SYSTEM.md")
    system = _read(system_path)
    if system is None:
        print(json.dumps({"status": "drift", "reason":
                          "SYSTEM.md unreadable at %r" % system_path}))
        return 1

    if "⟦SYSTEM v1⟧" in system and "⟦SURFACE v1⟧" not in system:
        # materialized child cell — compact form, no §3.6 surface
        compact = _check_compact(system, desk)
        locked = all([compact["markers"], compact["law"],
                      compact["equation_ok"], compact["seat"],
                      compact["operation"], compact["handoff"]])
        report = {
            "status": "locked" if locked else "drift",
            "desk": desk,
            "form": "compact",
            "firmware": {
                "course": COURSE,
                "gates": DESK_GATES,
                "corruption": sorted(CORRUPTION_CODES),
            },
            "checks": {"compact": compact},
        }
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        return 0 if locked else 1

    seal_out, _ = _check_seal(system, desk)
    surf_out = _check_surface(system, desk)

    checks = dict(seal_out)
    checks["surface"] = surf_out
    locked = all([
        seal_out["course"], seal_out["completion"],
        seal_out["corruption"], seal_out["equations_ok"],
        surf_out["markers"], surf_out["sections_ok"],
        surf_out["phase_ok"], surf_out["gate_ok"],
        surf_out["equation_ok"], surf_out["slots_ok"],
    ])
    report = {
        "status": "locked" if locked else "drift",
        "desk": desk,
        "firmware": {
            "course": COURSE,
            "gates": DESK_GATES,
            "corruption": sorted(CORRUPTION_CODES),
        },
        "checks": checks,
    }
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if locked else 1


if __name__ == "__main__":
    sys.exit(main())
