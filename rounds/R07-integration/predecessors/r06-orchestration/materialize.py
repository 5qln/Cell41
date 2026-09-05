#!/usr/bin/env python3
"""materialize — the materializer is zoom-in (R06 · orchestration,
C3/C4): the WRITE-path — the complement of the bridge's softconfig.py
READ-path.  Each node is its own lawful cell with its own ∞0|K
membrane and its own tools on the K side (D.1, D.10).  Emit a node's
cell — SYSTEM.md, .pi/settings.json, skills/, tools — from a scenario.

The Fractal is the spec, quoted — never paraphrased into the criteria:

  D.1:
    "4+1 is the syntax. It is invariant at every depth and every
    height: 1 center (S) + 4 corners (G, Q, P, V), never 3+1, never
    6+1."

  D.10:
    "H = ∞0 | A = K
    The field-question lives on the ∞0 side — unmarked, shared, no
    sign
    The +/− tracker lives on the K side — relations, lineage, known
    paths
    The membrane | is the line a stranger crosses to ask \"whose is
    this?\""

A node's K side may carry GENERAL tools (search / write-doc /
write-code / activate — Amihai, 2026-08-30: \"agents can act with
tools other than 5qln\"): the adapter stays tool-agnostic — nothing
forces 5qln-only, and the membrane is the same line whether the K
side holds a 5qln equation or a filesystem tool.  The materializer
DECLARES tools into the soft layer; whether a live pi loads them is
the constitution/run's concern, never this round's (H-ORCH-3).

Emitted bytes are byte-exact against the enumerated P4b tables (K2):
the seat/equation/operation/hand-off bytes are grammar.PHASE's (the
imported table — ⋂ stays U+22C2, ∞0′ never folded to ∞0', no spacing
collapse = no renaming), the LAW line is derived from the enumerated
seal form, the model is the bridge's DECLARED_MODEL (D6: one model —
read through softconfig, the read path this write path complements).
Every scenario-declared override byte passes through verbatim, never
normalised (lens 4: ∞0′ → ‖ rides them untouched).  A malformed
scenario or an unknown tool reads INCONCLUSIVE with the reason —
never a silently substituted value (C4).

Deterministic and stdlib-only: no network, no LLM, no wall-clock, no
subprocess (K1).  Every emitted artifact is a data file — diff-able,
versioned, never code (K5).
"""

from __future__ import annotations

import hashlib
import json
import os
import sys

sys.dont_write_bytecode = True

from surface_contract import (  # noqa: E402
    DECLARED_MODEL,
    grammar,
)

__all__ = [
    "GENERAL_TOOLS",
    "BASE_TOOLS",
    "MATERIALIZE_DEFAULTS",
    "SYSTEM_KEYS",
    "law_line",
    "node_cell",
    "materialize",
    "read_materialized",
    "cell_files",
    "MaterializeError",
]

# ---------------------------------------------------------------------------
# Declared data — the general-tool vocabulary (the K side is
# tool-agnostic, D.10; nothing forces 5qln-only), the base tools, the
# declared settings defaults.  One place to change, never logic.
# ---------------------------------------------------------------------------

GENERAL_TOOLS = {
    "search": {
        "description": ("search the outside world for what the question "
                        "needs — a general K-side tool, declared never "
                        "executed (H-ORCH-3)"),
    },
    "write-doc": {
        "description": ("write documents — a general K-side tool, "
                        "declared never executed (H-ORCH-3)"),
    },
    "write-code": {
        "description": ("write code — a general K-side tool, declared "
                        "never executed (H-ORCH-3)"),
    },
    "activate": {
        "description": ("activate a declared tool surface — the "
                        "provisional activation declaration (H-ORCH-3: "
                        "the materializer declares, it does not "
                        "execute)"),
    },
}

BASE_TOOLS = ("read", "grep", "bash")

MATERIALIZE_DEFAULTS = {
    "settings": {
        "model": DECLARED_MODEL,   # D6 — one model across the desks
        "thinking": True,          # declared default, caller-overridable
        "tools": list(BASE_TOOLS), # + the scenario's general tools
    },
    "tool_surface_header": ("⟦TOOL SURFACE v1⟧\n"
                            "LAW: H = ∞0 | A = K\n"
                            "5QLN-SIDE: %s\n"
                            "K-SIDE:\n"),
    "tool_surface_footer": "⟦END TOOL SURFACE⟧\n",
}

SYSTEM_KEYS = frozenset(("seat", "equation", "operation",
                         "handoff_in", "handoff_out"))


class MaterializeError(ValueError):
    """The materializer refused — INCONCLUSIVE, never a substituted
    cell."""


def law_line():
    """The One Law line — derived from the enumerated seal form (the
    activation-page seal's first line), never a fresh literal (K2: the
    bytes come from the enumerated table)."""
    form = grammar.SEAL["form"]
    for line in form.split("\n"):
        if line.startswith("1."):
            return line[len("1."):].lstrip()
    raise MaterializeError(
        "the enumerated seal form carries no Law line — the membrane "
        "bytes are INCONCLUSIVE, never substituted")


def node_cell(scenario, address, letter):
    """One node's cell — the four emitted artifacts as byte-exact
    strings (pure, deterministic, no disk): system (SYSTEM.md), the
    settings dict (.pi/settings.json), skills (the P4b bundle at this
    address), tools (the K-side tool-surface declaration)."""
    node = (scenario.get("nodes") or {}).get(address, {})
    phase = grammar.PHASE[letter]
    system_override = dict(node.get("system") or {})
    unknown = sorted(set(system_override) - SYSTEM_KEYS)
    if unknown:  # word.py already refused these — fail closed twice
        raise MaterializeError("unknown system override field(s): %s"
                               % ", ".join(unknown))
    seat = system_override.get("seat", phase["seat"])
    equation = system_override.get("equation", phase["equation"])
    operation = system_override.get("operation", phase["phase_gate"])
    handoff_in = system_override.get("handoff_in", phase["context_in"])
    handoff_out = system_override.get("handoff_out",
                                      phase["context_out"])
    system_text = (
        "⟦SYSTEM v1⟧\n"
        "LAW: %s\n"
        "SEAT: %s\n"
        "EQUATION: %s\n"
        "OPERATION: %s\n"
        "HAND-OFF: CONTEXT IN: %s · CONTEXT OUT: %s\n"
        "⟦END SYSTEM⟧\n"
        % (law_line(), seat, equation, operation, handoff_in,
           handoff_out))
    tools = list(node.get("tools") or BASE_TOOLS)
    general = list(node.get("general_tools") or [])
    for tool_name in general:
        if not isinstance(tool_name, str) or tool_name not in GENERAL_TOOLS:
            raise MaterializeError(
                "the scenario declares an unknown general tool %r — the "
                "K side is tool-agnostic, never silently substituted; "
                "the declared vocabulary is %s (C4)"
                % (tool_name, ", ".join(sorted(GENERAL_TOOLS))))
    settings = dict(MATERIALIZE_DEFAULTS["settings"])
    settings["tools"] = list(tools) + list(general)
    overrides = dict(node.get("settings") or {})
    for key, value in overrides.items():
        # byte-exact passthrough — every override rides verbatim, never
        # normalised (K2, lens 4)
        settings[key] = value
    _check_json_safe(settings, address)
    skills_text = grammar.render_bundle(address, letter)
    tool_lines = [MATERIALIZE_DEFAULTS["tool_surface_header"]
                  % ", ".join(tools)]
    for tool_name in general:
        tool_lines.append("%s: %s\n"
                          % (tool_name,
                             GENERAL_TOOLS[tool_name]["description"]))
    tool_lines.append(MATERIALIZE_DEFAULTS["tool_surface_footer"])
    tools_text = "".join(tool_lines)
    return {
        "system": system_text,
        "settings": settings,
        "skills": skills_text,
        "tools": tools_text,
    }


def _check_json_safe(settings, address):
    try:
        json.dumps(settings, ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise MaterializeError(
            "nodes.%s.settings is not JSON-safe (%s) — the soft layer "
            "is data, never code (K5)" % (address, exc))


def _word_to_disk(address):
    return "_" if address == "" else address


def cell_files():
    """The four emitted files of one node's cell — the declared shape
    (one place to change)."""
    return ("SYSTEM.md", ".pi/settings.json", "skills/SKILL.md",
            "tools/tool-surface.md")


def _canonical_settings(settings):
    return (json.dumps(settings, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"), allow_nan=False) + "\n")


def materialize(scenario, out_dir, visits=None):
    """Emit every node's cell of a DECODED scenario (word.decode_
    scenario's "ok" output) under ``out_dir`` — deterministic,
    byte-exact, data files only.  ``visits`` is the walk's plan
    (navigate.plan_walk's list — the loop-expanded visits included);
    absent it, the seed + the declared paths are covered.  Returns:

      {"status": "materialized", "root", "nodes": [{address, letter,
        files: {name: sha256}}]}
      {"status": "inconclusive", "reason": …}

    A malformed scenario or an unknown tool reads INCONCLUSIVE with the
    reason — never a silently substituted cell (C4, lens 3/6)."""
    if not isinstance(scenario, dict) or scenario.get("word") is None:
        return {"status": "inconclusive",
                "reason": "the scenario is not a decoded scenario "
                          "object — the materializer refuses to emit "
                          "from nothing"}
    try:
        nodes = []
        addresses = []
        from word import letter_of  # noqa: E402 — this round's decoder
        seen = set()
        for visit in _all_addresses(scenario, visits):
            if visit in seen:
                continue
            seen.add(visit)
            addresses.append((visit, letter_of(visit)))
        total = 0
        for address, letter in addresses:
            cell = node_cell(scenario, address, letter)
            node_dir = os.path.join(out_dir, _word_to_disk(address))
            skills_dir = os.path.join(node_dir, "skills")
            tools_dir = os.path.join(node_dir, "tools")
            pi_dir = os.path.join(node_dir, ".pi")
            os.makedirs(skills_dir, exist_ok=True)
            os.makedirs(tools_dir, exist_ok=True)
            os.makedirs(pi_dir, exist_ok=True)
            files = {}
            for name, content in (
                    ("SYSTEM.md", cell["system"]),
                    (".pi/settings.json", _canonical_settings(
                        cell["settings"])),
                    ("skills/SKILL.md", cell["skills"]),
                    ("tools/tool-surface.md", cell["tools"])):
                path = os.path.join(node_dir, *name.split("/"))
                raw = content.encode("utf-8")
                with open(path, "wb") as handle:
                    handle.write(raw)
                files[name] = hashlib.sha256(raw).hexdigest()
                total += len(raw)
            nodes.append({"address": address, "letter": letter,
                          "files": files})
    except MaterializeError as exc:
        return {"status": "inconclusive", "reason": str(exc)}
    return {"status": "materialized", "root": out_dir, "nodes": nodes,
            "bytes": total,
            "reason": "every node emitted as its own ∞0|K cell — data "
                      "files, never code (D.1/D.10)"}


def _all_addresses(scenario, visits=None):
    """Every node address of the scenario — the plan's visits (the
    loop-expanded walk included) when given, else the seed plus every
    declared arrival."""
    if visits:
        for visit in visits:
            yield visit["address"]
        return
    yield scenario["seed"]["address"]
    for path in scenario["paths"]:
        yield path["to"]


def read_materialized(scenario, directory, visits=None):
    """Verify an already-materialized word from disk (the \"not every
    run\" clause, C3): every node's four files must exist, be
    non-empty (the sha256 of empty is e3b0c44298fc… — never valid,
    lens 3), and be byte-equal to the deterministic re-emission — an
    absent, empty or drifted cell reads INCONCLUSIVE, never used
    silently.  Binary reads only — never text-mode byte seeks
    (lens 4)."""
    if not isinstance(scenario, dict) or scenario.get("word") is None:
        return {"status": "inconclusive",
                "reason": "the scenario is not a decoded scenario — "
                          "the materialized word cannot be verified"}
    try:
        from word import letter_of  # noqa: E402
        seen = set()
        nodes = []
        for address in _all_addresses(scenario, visits):
            if address in seen:
                continue
            seen.add(address)
            nodes.append((address, letter_of(address)))
        for address, letter in nodes:
            cell = node_cell(scenario, address, letter)
            expected = {
                "SYSTEM.md": cell["system"].encode("utf-8"),
                ".pi/settings.json": _canonical_settings(
                    cell["settings"]).encode("utf-8"),
                "skills/SKILL.md": cell["skills"].encode("utf-8"),
                "tools/tool-surface.md": cell["tools"].encode("utf-8"),
            }
            node_dir = os.path.join(directory, _word_to_disk(address))
            for name, wanted in expected.items():
                path = os.path.join(node_dir, *name.split("/"))
                try:
                    with open(path, "rb") as handle:
                        raw = handle.read()
                except OSError as exc:
                    return {"status": "inconclusive",
                            "reason": ("the materialized cell %r is "
                                       "missing %s (%s) — an absent "
                                       "cell never reads valid (lens 3)"
                                       % (address, name, exc))}
                if not raw:
                    return {"status": "inconclusive",
                            "sha256": hashlib.sha256(b"").hexdigest(),
                            "reason": ("the materialized cell %r holds "
                                       "an EMPTY %s — the sha256 of "
                                       "empty is e3b0c44298fc…, never "
                                       "valid (lens 3)"
                                       % (address, name))}
                if raw != wanted:
                    return {"status": "inconclusive",
                            "reason": ("the materialized cell %r's %s "
                                       "drifted from the scenario's "
                                       "deterministic re-emission — a "
                                       "drifted cell is not the "
                                       "scenario's cell; never used "
                                       "silently" % (address, name))}
    except MaterializeError as exc:
        return {"status": "inconclusive", "reason": str(exc)}
    return {"status": "ok", "directory": directory, "nodes": nodes,
            "reason": "the materialized word on disk is the scenario's "
                      "cells, byte for byte — a run may use it "
                      "(\"not every run\")"}
