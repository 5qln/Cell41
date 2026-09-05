#!/usr/bin/env python3
"""install — the deterministic Pi installer (PRD §6.2 / E1 / E4; C4).

One arrangement always produces the same bytes.  The installer is a pure
function of the arrangement record and the block store: it validates the
arrangement end-to-end, resolves every block, scans every bundle for the
headless anti-pattern, and emits the launch manifest —

  * headless ``--mode rpc`` (PRD §6.2: "Driven headless via `--mode rpc`");
  * the trust gate: ``defaultProjectTrust: "always"`` **and** ``--approve``
    (§6.2: "headless runs need `defaultProjectTrust:\"always\"` or
    `--approve`, else project `.pi/` skills/extensions are ignored");
  * forced skill loading: a ``before_agent_start`` injection carrying
    ``/skill:<name>`` per skill (§6.2: "Skills are not reliably
    auto-loaded → force with `/skill:name` or `before_agent_start`
    injection");
  * no TUI APIs: every bundle is scanned for the headless-forbidden
    ``ctx.ui`` and the install fails closed when it appears (E4.5: "Use
    TUI APIs in headless modes — guard with ctx.mode/ctx.hasUI");
  * tool output honors 50 KB / 2000 lines — the limits ride in the
    manifest and ``truncate_output`` honors them (§6.2 / E4.7);
  * state lives in the ledger, not extension memory: the manifest names
    the arrangement's ledger path and carries a §5.1 record template per
    corner desk, built through B0's ``make_record`` (imported, never
    copied) with ``block_version: ""`` (H-P4b-6) — no template for S,
    because the centre is never prompted and nothing here writes to the
    podium (commission §6).

The runtime differs per desk from the arrangement's own data: ``pi`` for
the corners, the desk-adapter for S in v1 (H-P4b-3 — the grammar is one,
the runtime differs; the all-Pi shape stays a config change).  The
installer never executes anything: it is generated data + command,
structurally checkable (H-P4b-1) — no subprocess, no socket, no LLM, no
wall clock, deterministic.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys

from block import canonical_json, BlockStore
import arrangement
import grammar

# B0's module is imported, never copied (R01 attested and closed).
_LEDGER_DIR = os.environ.get(
    "FRACTAL_LEDGER_DIR", "/home/deploy/the-cell/ledger")
if _LEDGER_DIR not in sys.path:
    sys.path.insert(0, _LEDGER_DIR)

from fractal_ledger import make_record  # noqa: E402

__all__ = [
    "INSTALLER_VERSION",
    "TRUNCATION_LIMITS",
    "InstallError",
    "truncate_output",
    "scan_no_tui",
    "report_install",
    "install",
    "install_to",
]

INSTALLER_VERSION = 1

# PRD §6.2: "Tool output honors 50 KB / 2000 lines."
TRUNCATION_LIMITS = {"max_bytes": 51200, "max_lines": 2000}

# The headless-forbidden TUI needle, built so the scan cannot flag itself
# (P4a §3.7 lesson 4).  PRD §6.2: "No TUI APIs (`ctx.ui`) in headless
# modes."
_TUI_NEEDLE = "ctx" + "." + "ui"

# The runtime specs (data — the arrangement's entry names the runtime;
# the installer never hardcodes which desk runs where):
RUNTIME_SPECS = {
    "pi": {
        "launch": ["pi", "--mode", "rpc", "--approve", "--print"],
        "trust": {"project": {"defaultProjectTrust": "always"},
                  "cli": "--approve"},
        "skill_loading": "before_agent_start injection",
    },
    "hermes-desk-adapter": {
        "launch": None,
        "adapter": "desk-adapter",
        "note": "S is the conductor in v1 — Hermes behind the same "
                "desk-adapter interface as the corners (H-P4b-3)",
    },
}


class InstallError(Exception):
    """The installer refused to emit launch bytes (fail closed)."""


def truncate_output(text):
    """Honor the 50 KB / 2000-line limit (E4.7) — byte length on the UTF-8
    encoding and line count on the text; returns (text, truncated)."""
    if not isinstance(text, str):
        text = str(text)
    truncated = False
    lines = text.split("\n")
    if len(lines) > TRUNCATION_LIMITS["max_lines"]:
        lines = lines[:TRUNCATION_LIMITS["max_lines"]]
        text = "\n".join(lines)
        truncated = True
    blob = text.encode("utf-8")
    if len(blob) > TRUNCATION_LIMITS["max_bytes"]:
        while len(text.encode("utf-8")) > TRUNCATION_LIMITS["max_bytes"] and text:
            text = text[:-1]
        truncated = True
    return text, truncated


def scan_no_tui(text):
    """Count the headless-forbidden TUI occurrences in a bundle's bytes."""
    if isinstance(text, bytes):
        blob = text
    else:
        blob = text.encode("utf-8")
    count = 0
    start = 0
    needle = _TUI_NEEDLE.encode("utf-8")
    while True:
        found = blob.find(needle, start)
        if found == -1:
            return count
        count += 1
        start = found + len(needle)


def _desk_manifest(letter, entry, block_store):
    """One desk's launch spec + record template — deterministic."""
    block_id, version = arrangement.split_ref(entry["instruction"])
    instruction = block_store.read(block_id, version)
    instruction_bytes = instruction["files"].get("instruction.md")
    if instruction_bytes is None:
        return {"letter": letter, "verdict": "FAIL",
                "reason": "the instruction block carries no instruction.md"}
    skills = []
    skill_payloads = {}
    for ref in entry["skills"]:
        skill_id, skill_version = arrangement.split_ref(ref)
        result = block_store.read(skill_id, skill_version)
        blob = result["files"].get("SKILL.md")
        if blob is None:
            return {"letter": letter, "verdict": "FAIL",
                    "reason": "skill block %s carries no SKILL.md" % ref}
        skills.append({
            "block": ref,
            "sha256": result["record"]["sha256"],
            "name": skill_id,
        })
        skill_payloads[skill_id] = blob
    tool_id, tool_version = arrangement.split_ref(entry["tool_surface"])
    tool_surface = block_store.read(tool_id, tool_version)
    tool_blob = tool_surface["files"].get("tool-surface.md")
    if tool_blob is None:
        return {"letter": letter, "verdict": "FAIL",
                "reason": "the tool surface block carries no tool-surface.md"}
    model_id, model_version = arrangement.split_ref(entry["model"])
    model = block_store.read(model_id, model_version)

    # E4.5: no TUI APIs in headless modes — scanned over every bundle byte.
    scanned = {
        "instruction": scan_no_tui(instruction_bytes),
        "tool_surface": scan_no_tui(tool_blob),
    }
    for skill_id, blob in skill_payloads.items():
        scanned["skill:%s" % skill_id] = scan_no_tui(blob)
    tui_hits = [name for name, count in scanned.items() if count]
    if tui_hits:
        return {"letter": letter, "verdict": "FAIL",
                "reason": "headless-forbidden TUI APIs found in: %s"
                          % ", ".join(sorted(tui_hits))}

    runtime = entry["runtime"]
    spec = RUNTIME_SPECS.get(runtime)
    if spec is None:
        return {"letter": letter, "verdict": "INCONCLUSIVE",
                "reason": "runtime %r has no launch spec on this box"
                          % (runtime,)}

    launch = None
    trust = None
    skill_loading = None
    if runtime == "pi":
        launch = spec["launch"]
        trust = spec["trust"]
        skill_loading = spec["skill_loading"]
    adapter = spec.get("adapter")

    desk = {
        "letter": letter,
        "address": entry["address"],
        "gate": grammar.DESK_GATES[letter],
        "runtime": runtime,
        "instruction": {
            "block": entry["instruction"],
            "sha256": instruction["record"]["sha256"],
            "bytes": len(instruction_bytes),
        },
        "skills": skills,
        "tool_surface": {
            "block": entry["tool_surface"],
            "sha256": tool_surface["record"]["sha256"],
        },
        "model": {
            "block": entry["model"],
            "sha256": model["record"]["sha256"],
            "route": entry["model_route"],
        },
        "tars": entry["tars"],
        "launch": {
            "command": launch,
            "adapter": adapter,
            "trust": trust,
            "skill_loading": skill_loading,
            "skill_injection": (
                "\n".join("/skill:%s" % skill["name"] for skill in skills)
                if skills else None),
            "no_tui": {"scan": _TUI_NEEDLE, "occurrences": 0},
            "truncation": TRUNCATION_LIMITS,
            "state": {"authority": "ledger",
                      "path": None},  # filled below, once, from the record
        },
        "record_template": None,
    }
    if letter != "S":
        # §5.1 template through B0's make_record — block_version "" is the
        # carried hold H-P4b-6, never an invented identity.  The template
        # is data, never a write: the ledger writer appends it when the
        # desk's turn is proposed.
        desk["record_template"] = make_record(
            address=entry["address"], gate=grammar.DESK_GATES[letter],
            state="mechanical", mark="mechanical", payload_ref="",
            block_version="", tentative=False)
    else:
        desk["launch"]["note"] = (
            "the centre is never prompted (B2 guards) and no code path "
            "writes to the podium — no record template is emitted for S "
            "(commission §6)")
    return {"letter": letter, "verdict": "OK", "desk": desk}


def report_install(record, block_store):
    """Validate and build the manifest — a REPORT, never a write.  The
    verdicts: OK per desk, FAIL (defective, refused), INCONCLUSIVE
    (unobservable, refused — lens 6: never a guessed clean)."""
    check = arrangement.validate_arrangement(record, block_store)
    items = list(check["items"])
    desks = {}
    problems = 0
    unknowns = 0
    if check["status"] == "ok":
        for letter in grammar.COURSE:
            entry = record["desks"][letter]
            try:
                result = _desk_manifest(letter, entry, block_store)
            except arrangement.ArrangementError as exc:
                result = {"letter": letter, "verdict": "FAIL",
                          "reason": str(exc)}
            except Exception as exc:  # noqa: BLE001 — fail closed, never crash open
                result = {"letter": letter, "verdict": "INCONCLUSIVE",
                          "reason": "unobservable: %s" % exc}
            if result["verdict"] == "FAIL":
                problems += 1
            elif result["verdict"] == "INCONCLUSIVE":
                unknowns += 1
            items.append({
                "id": "IN-%s" % letter,
                "verdict": {"OK": "PASS", "FAIL": "FAIL",
                            "INCONCLUSIVE": "INCONCLUSIVE"}[result["verdict"]],
                "citation": ("PRD §6.2/E1/E4: headless --mode rpc, trust "
                             "gate, forced skills, no TUI APIs, "
                             "50 KB / 2000 lines, state in the ledger"),
                "evidence": result.get("reason")
                or "launch spec and record template built",
            })
            if "desk" in result:
                desks[letter] = result["desk"]
    elif check["status"] == "fail":
        problems += 1
    else:
        unknowns += 1

    status = "fail" if problems else ("inconclusive" if unknowns else "ok")
    manifest = None
    if status == "ok":
        for desk in desks.values():
            desk["launch"]["state"]["path"] = record["state"]["ledger_path"]
        manifest = {
            "installer_version": INSTALLER_VERSION,
            "arrangement": {
                "name": record["name"],
                "version": record["version"],
                "sha256": record["sha256"],
            },
            "runtime_pins": record["runtime_pins"],
            "state": {"authority": "ledger",
                      "path": record["state"]["ledger_path"]},
            "desks": desks,
            "determinism": (
                "a pure function of the arrangement bytes and the resolved "
                "block digests — one arrangement, one byte string"),
        }
        manifest["checksum"] = hashlib.sha256(canonical_json(
            {key: value for key, value in manifest.items()
             if key != "checksum"}).encode("utf-8")).hexdigest()
    return {"status": status, "items": items, "manifest": manifest}


def install(record, block_store):
    """One arrangement → one byte string.  Raises InstallError unless the
    arrangement is fully observable and ok — fail closed, never a partial
    launch."""
    report = report_install(record, block_store)
    if report["status"] != "ok":
        failed = [it["id"] for it in report["items"]
                  if it["verdict"] != "PASS"]
        raise InstallError(
            "refusing to emit launch bytes: install status %s (%s)"
            % (report["status"], ", ".join(failed) if failed else "items"))
    return canonical_json(report["manifest"]).encode("utf-8") + b"\n"


def install_to(record, block_store, path):
    """Write the deterministic launch bytes to ``path`` and return them."""
    payload = install(record, block_store)
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "wb") as handle:
        handle.write(payload)
    return payload
