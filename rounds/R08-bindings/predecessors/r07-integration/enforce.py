#!/usr/bin/env python3
"""enforce — the enforcement suite (the integration round, C4): the
three legs of SCOPE §4 made mechanically checkable, each proven to
FAIL on a deliberately-injected violation (see selftest.py +
fixtures/enforcement/).

  L1 capability scan — the soft layer contains no driving write verb
     (herdr_send_prompt, herdr agent prompt, agent.prompt,
     pane.wait_for_output, send-keys/send_text/send_input, socket-
     client code, subprocess-to-herdr with a prompt/wait verb), except
     the declared human-TTY allowlist (cell-plant/cell-attest).  For
     python files the scan walks the AST (call sites, attribute
     chains, the subprocess composite — docstrings are not driving
     code); for every other soft-layer file it scans the text (their
     content IS the surface).  Zero findings = PASS.

  L2 entry-point census — every executable in the soft layer is a
     declared member of the seam manifest, and no soft-layer file
     imports the pinned engine modules directly (the CLI is the only
     path; surface_contract.py is the seam).  An undeclared bin, an
     undeclared tool, an undeclared engine import = FAIL.

  L3 config-schema validation — every file the engine reads from the
     soft layer validates against a declared schema; unknown fields =
     INCONCLUSIVE refuse (the attested softconfig + word behavior,
     extended to the cell spec).  Absent/empty/malformed/unknown never
     read valid.

Every leg's report is a dict; the overall verdict is FAIL if any leg
FAILs, INCONCLUSIVE if any leg is INCONCLUSIVE (an unreadable scan
target is never claimed clean — lens 6), else PASS.  Deterministic
and stdlib-only: no network, no LLM, no wall-clock, no subprocess
(K1).  The declarations (roots, tokens, allowlist, census) live in
``surface_contract`` — data, one place to change (K5).
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import stat
import sys

sys.dont_write_bytecode = True

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import surface_contract as sc  # noqa: E402

__all__ = ["leg1_capability", "leg2_census", "leg3_schema", "verify_all"]


def _read_text(path):
    with open(path, "rb") as handle:
        raw = handle.read()
    return raw.decode("utf-8", "replace")


def _is_python(path, text):
    """Python files by extension OR by shebang (the extensionless CLI
    and plugin bins are python too — their docstrings are not driving
    code, so they get the AST scan)."""
    if path.endswith(".py"):
        return True
    first_line = text.split("\n", 1)[0]
    return first_line.startswith("#!") and "python" in first_line


def _is_executable(path):
    try:
        mode = os.stat(path).st_mode
    except OSError:
        return False
    return bool(mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH))


def _skip_path(path, excluded):
    normalized = os.path.abspath(path)
    for entry in excluded:
        if normalized.startswith(os.path.abspath(entry) + os.sep):
            return True
    return False


def _root_files(root):
    """The files of one scan root: a declared file list (basename or
    subpath prefix), or every regular file.  Bytecode caches are
    skipped (declared: caches are not source)."""
    base = root["path"]
    if not os.path.isdir(base):
        return []
    out = []
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for name in filenames:
            path = os.path.join(dirpath, name)
            if not os.path.isfile(path):
                continue
            declared = root.get("files")
            if declared:
                relative = os.path.relpath(path, base)
                if not any(relative == item
                           or relative.startswith(item + os.sep)
                           or os.path.basename(relative) == item
                           for item in declared):
                    continue
            out.append(path)
    return sorted(out)


def _root_file_paths(root):
    """The files of a root whose path is itself a FILE (the config
    roots) — one entry or none."""
    path = root["path"]
    if os.path.isfile(path):
        return [path]
    return []


# ---------------------------------------------------------------------------
# L1 — the capability scan.
# ---------------------------------------------------------------------------

# Attribute chains flagged as driving write verbs (AST + text).
_WRITE_CHAINS = (
    (("agent",), "prompt"),
    (("pane",), "wait_for_output"),
    (("pane", "wait_for_output"), None),
)
_WRITE_NAMES = (
    "herdr_send_prompt",
    "send_text", "send_input", "send_keys",
    "send-keys",
)
_SOCKET_NAMES = ("AF_UNIX", "sendall", "connect")
_TEXT_PATTERNS = (
    (re.compile(r"herdr_send_prompt"),
     "pi-herdr write verb — a soft-layer drive channel"),
    (re.compile(r"herdr\s+agent\s+prompt"),
     "herdr CLI write verb — a soft-layer drive channel"),
    (re.compile(r"agent\.prompt"),
     "the engine's write method name in soft-layer reach — the single chokepoint stays the engine's"),
    (re.compile(r"pane\.wait_for_output"),
     "wait verb — driving logic in the soft layer"),
    (re.compile(r"send[-_]keys|send[-_]text|send[-_]input"),
     "podium/panes write verbs — no write path to the podium"),
    (re.compile(r"socket\.AF_UNIX|\.sendall\(|\.connect\("),
     "socket-client code — the pinned Instrument is the only client (K1)"),
)
_COMPOSITE_REASON = ("subprocess-to-herdr with a prompt/wait verb — "
                     "driving logic in the soft layer")


def _ast_findings(path, text):
    """AST scan of one python file: write-verb call sites, attribute
    chains, socket-client code, and the subprocess composite.  The
    module docstring is not code; string constants are only evidence
    for the composite (a string alone drives nothing)."""
    findings = []
    try:
        tree = ast.parse(text, filename=path)
    except SyntaxError as exc:
        return [{"file": path, "line": exc.lineno or 0,
                 "token": "unparseable",
                 "reason": "the soft-layer file does not parse (%s) — "
                           "INCONCLUSIVE, never skipped" % exc}]
    string_consts = []
    has_subprocess = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            string_consts.append(node.value)
        if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if (alias.name or "").split(".")[0] == "subprocess":
                    has_subprocess = True
        if isinstance(node, ast.Name) and node.id in _WRITE_NAMES:
            findings.append({
                "file": path, "line": node.lineno, "token": node.id,
                "reason": "a driving write verb name in the soft layer"})
        if isinstance(node, ast.Attribute):
            chain = _attr_chain(node)
            for prefix, attr in _WRITE_CHAINS:
                if tuple(chain[-len(prefix) - 1:-1]) == prefix \
                        and chain[-1] == attr:
                    findings.append({
                        "file": path, "line": node.lineno,
                        "token": ".".join(chain[-len(prefix) - 1:]),
                        "reason": ("a driving write verb in the soft "
                                   "layer — the single chokepoint stays "
                                   "the engine's")})
        if isinstance(node, ast.Attribute) and node.attr in _SOCKET_NAMES:
            findings.append({
                "file": path, "line": node.lineno,
                "token": "socket.%s" % node.attr,
                "reason": "socket-client code — the pinned Instrument "
                          "is the only client (K1)"})
        if isinstance(node, ast.Name) and node.id == "AF_UNIX":
            findings.append({
                "file": path, "line": node.lineno, "token": "AF_UNIX",
                "reason": "socket-client code — the pinned Instrument "
                          "is the only client (K1)"})
    if has_subprocess:
        joined = "\n".join(string_consts)
        if re.search(r"herdr", joined) and re.search(
                r"agent\s+prompt|wait_for_output|send_prompt", joined):
            findings.append({
                "file": path, "line": 1, "token": "subprocess→herdr",
                "reason": _COMPOSITE_REASON})
    return findings


def _attr_chain(node):
    chain = []
    current = node
    while isinstance(current, ast.Attribute):
        chain.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        chain.append(current.id)
    return list(reversed(chain))


def _text_findings(path, text):
    """Text scan of one non-python soft-layer file — its content IS
    the surface (markdown constitutions, bash bins, configs)."""
    findings = []
    for line_no, line in enumerate(text.split("\n"), start=1):
        for pattern, reason in _TEXT_PATTERNS:
            if pattern.search(line):
                findings.append({
                    "file": path, "line": line_no,
                    "token": pattern.pattern,
                    "reason": reason})
    if (re.search(r"subprocess", text) and re.search(r"herdr", text)
            and re.search(r"agent\s+prompt|wait_for_output|send_prompt",
                          text)):
        findings.append({
            "file": path, "line": 1, "token": "subprocess→herdr",
            "reason": _COMPOSITE_REASON})
    return findings


def leg1_capability(roots=None, declaration=None):
    """L1 — the capability scan.  ``roots`` defaults to the declared
    scan roots (SEAM_SURFACE data); each root is {name, path, files}.
    Absent scan targets are reported honestly: a missing REQUIRED root
    reads INCONCLUSIVE (never claimed clean — lens 6)."""
    declaration = declaration or sc.L1_DECLARATION
    roots = roots if roots is not None else declaration["scan_roots"]
    findings = []
    notes = []
    scanned = []
    for root in roots:
        path = root["path"]
        files = (_root_files(root) if os.path.isdir(path)
                 else _root_file_paths(root))
        if not files:
            notes.append({
                "root": root["name"], "path": path,
                "note": ("absent or empty — not scanned; a required "
                         "root that is absent reads INCONCLUSIVE, "
                         "never clean" if root.get("required")
                         else "absent — the declared read is the "
                              "engine's defaults (soft config)")})
            if root.get("required"):
                return {
                    "leg": "L1-capability", "verdict": "INCONCLUSIVE",
                    "findings": [], "notes": notes, "scanned": [],
                    "reason": "a required scan root is absent (%r at "
                              "%r) — the capability scan cannot claim "
                              "clean (lens 6)" % (root["name"], path)}
            continue
        for file_path in files:
            if _skip_path(file_path, declaration["excluded_paths"]):
                continue
            allowed = any(
                os.path.abspath(file_path).endswith(
                    entry["path_suffix"])
                for entry in declaration["allowlist"])
            text = _read_text(file_path)
            if _is_python(file_path, text):
                found = _ast_findings(file_path, text)
            else:
                found = _text_findings(file_path, text)
            if allowed and found:
                notes.append({
                    "root": root["name"], "file": file_path,
                    "note": ("declared human-TTY allowlist "
                             "(cell-plant/cell-attest) — the finding "
                             "is allowed by declaration, never "
                             "hidden")})
                continue
            findings.extend(found)
            scanned.append(file_path)
    verdict = "FAIL" if findings else "PASS"
    return {"leg": "L1-capability", "verdict": verdict,
            "findings": findings, "notes": notes, "scanned": scanned,
            "reason": ("zero findings — the soft layer carries no "
                       "driving write verb" if not findings
                       else "%d finding(s) — the soft layer carries a "
                             "driving write verb" % len(findings))}


# ---------------------------------------------------------------------------
# L2 — the entry-point census.
# ---------------------------------------------------------------------------

_PINNED_NAMES = sc.SEAM_MANIFEST["pinned_module_names"]
_IMPORT_TEXT_RE = re.compile(
    r"^\s*(?:from\s+(%s)\s+import|import\s+(%s)\b)"
    % ("|".join(_PINNED_NAMES), "|".join(_PINNED_NAMES)))


def _ast_import_findings(path, text):
    findings = []
    try:
        tree = ast.parse(text, filename=path)
    except SyntaxError:
        return findings
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in _PINNED_NAMES:
                    findings.append({
                        "file": path, "line": node.lineno,
                        "token": "import %s" % alias.name,
                        "reason": "a pinned engine module imported "
                                  "directly — the CLI is the only "
                                  "path (C7)"})
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.split(".")[0] in _PINNED_NAMES:
                findings.append({
                    "file": path, "line": node.lineno,
                    "token": "from %s import" % node.module,
                    "reason": "a pinned engine module imported "
                              "directly — the CLI is the only "
                              "path (C7)"})
    return findings


def leg2_census(roots=None, manifest=None, excluded=()):
    """L2 — the entry-point census: every executable in the scan roots
    is a declared member of the seam manifest, and no scanned file
    imports the pinned engine modules directly (surface_contract.py is
    the seam; the CLI is the only path)."""
    manifest = manifest or sc.SEAM_MANIFEST
    roots = roots if roots is not None else sc.L1_DECLARATION["scan_roots"]
    declared = [os.path.abspath(entry["path"])
                for entry in manifest["entry_points"]]
    import_allowed = [os.path.abspath(p) for p in manifest[
        "import_allowed"]] + [os.path.abspath(p) for p in excluded]
    findings = []
    scanned = []
    for root in roots:
        path = root["path"]
        files = (_root_files(root) if os.path.isdir(path)
                 else _root_file_paths(root))
        for file_path in files:
            text = _read_text(file_path)
            allowed_importer = os.path.abspath(file_path) in import_allowed
            if _is_python(file_path, text):
                for finding in _ast_import_findings(file_path, text):
                    if allowed_importer:
                        continue
                    findings.append(finding)
            else:
                for finding in _text_import_findings(file_path, text):
                    if allowed_importer:
                        continue
                    findings.append(finding)
            if root.get("executables") and _is_executable(file_path):
                scanned.append(file_path)
                if os.path.abspath(file_path) not in declared:
                    findings.append({
                        "file": file_path, "line": 0,
                        "token": "undeclared-executable",
                        "reason": "an undeclared bin/tool in the soft "
                                  "layer — every executable is a "
                                  "declared member of the seam "
                                  "manifest (SCOPE §4 leg 2)"})
    verdict = "FAIL" if findings else "PASS"
    return {"leg": "L2-census", "verdict": verdict,
            "findings": findings, "scanned": scanned,
            "reason": ("every executable is declared and no soft-layer "
                       "file imports the engine directly" if not findings
                       else "%d census finding(s)" % len(findings))}


def _text_import_findings(path, text):
    findings = []
    for line_no, line in enumerate(text.split("\n"), start=1):
        match = _IMPORT_TEXT_RE.search(line)
        if match:
            findings.append({
                "file": path, "line": line_no,
                "token": match.group(0).strip(),
                "reason": "a pinned engine module imported directly — "
                          "the CLI is the only path (C7)"})
    return findings


# ---------------------------------------------------------------------------
# L3 — config-schema validation.
# ---------------------------------------------------------------------------

def leg3_schema(targets=None, scenarios=()):
    """L3 — every file the engine reads from the soft layer validates
    against a declared schema.  Unknown fields read INCONCLUSIVE
    (refuse), never silently ignored — the cell spec through the
    seam's declared schema, the soft config through the engine's own
    attested read, the scenarios through the engine's own decoder."""
    targets = targets if targets is not None \
        else sc.L1_DECLARATION["schema_targets"]
    findings = []
    notes = []
    checked = []
    for target in targets:
        path = target["path"]
        kind = target["kind"]
        if kind == "cell-spec":
            report = sc.load_cell_spec(path)
            checked.append({"name": target["name"], "path": path,
                            "status": report.get("status")})
            if report.get("status") != "ok":
                findings.append({
                    "file": path, "line": 0, "token": "schema-refusal",
                    "reason": ("the cell spec %r reads %s — an "
                               "absent/empty/malformed/unknown-field "
                               "spec is INCONCLUSIVE, never used: %s"
                               % (path, report.get("status"),
                                  report.get("reason")))})
        elif kind == "soft-config":
            if not os.path.isfile(path):
                notes.append({"name": target["name"], "path": path,
                              "note": "absent — the engine's declared "
                                      "defaults apply (the attested "
                                      "read, C4)"})
                continue
            report = sc.softconfig.load_soft_config(path)
            checked.append({"name": target["name"], "path": path,
                            "status": report.get("status")})
            if report.get("status") not in ("ok", "defaults"):
                findings.append({
                    "file": path, "line": 0, "token": "schema-refusal",
                    "reason": ("the soft config %r reads %s — unknown "
                               "fields are INCONCLUSIVE, never used: %s"
                               % (path, report.get("status"),
                                  report.get("reason")))})
        else:
            findings.append({"file": path, "line": 0,
                             "token": "unknown-target",
                             "reason": "unknown schema target kind %r"
                                       % (kind,)})
    for path in scenarios:
        report = sc.word.load_scenario_file(path)
        checked.append({"name": os.path.basename(path), "path": path,
                        "status": report.get("status")})
        if report.get("status") != "ok":
            findings.append({
                "file": path, "line": 0, "token": "schema-refusal",
                "reason": ("the scenario %r reads %s — a scenario "
                           "outside the declared schema is "
                           "INCONCLUSIVE, never run: %s"
                           % (path, report.get("status"),
                              report.get("reason")))})
    verdict = "FAIL" if findings else "PASS"
    return {"leg": "L3-config-schema", "verdict": verdict,
            "findings": findings, "notes": notes, "checked": checked,
            "reason": ("every engine-read soft-layer file validates "
                       "against a declared schema" if not findings
                       else "%d schema finding(s) — unknown fields "
                             "read INCONCLUSIVE, never ignored"
                             % len(findings))}


# ---------------------------------------------------------------------------
# The whole verification (pins are the import itself; legs 1-3; the
# gates plant; the C3 plan-equivalence runs in verify-integration.sh,
# which executes the CLI as the second process).
# ---------------------------------------------------------------------------

def verify_all():
    report = {
        "round": "integration",
        "contract_version": sc.CONTRACT_VERSION,
        "pins": {
            "pinned_files": len(sc.PINNED_FILES),
            "note": ("the import above IS the pin check — a drifted or "
                     "missing pinned file refused the import "
                     "(ImportError, C7)"),
        },
        "legs": {},
        "gates_plant": None,
    }
    report["legs"]["L1"] = leg1_capability()
    report["legs"]["L2"] = leg2_census()
    report["legs"]["L3"] = leg3_schema(
        scenarios=[os.path.join(sc._HERE, "fixtures", "scenarios",
                                name)
                   for name in ("pinned-cycle.json",
                                "pinned-guard.json",
                                "pinned-encoding.json")])
    gates = sc.L1_DECLARATION["gates_plant"]
    try:
        with open(gates["path"], "rb") as handle:
            actual = hashlib.sha256(handle.read()).hexdigest()
    except OSError as exc:
        report["gates_plant"] = {"verdict": "INCONCLUSIVE",
                                 "reason": "the plant %r is unreadable "
                                           "(%s) — never claimed intact"
                                           % (gates["path"], exc)}
    else:
        report["gates_plant"] = {
            "verdict": "PASS" if actual == gates["sha256"] else "FAIL",
            "path": gates["path"], "actual_sha256": actual,
            "expected_sha256": gates["sha256"],
            "citation": gates["citation"]}
    verdicts = [leg["verdict"] for leg in report["legs"].values()]
    if report["gates_plant"]["verdict"] != "PASS":
        verdicts.append(report["gates_plant"]["verdict"])
    if "FAIL" in verdicts:
        report["verdict"] = "FAIL"
    elif "INCONCLUSIVE" in verdicts:
        report["verdict"] = "INCONCLUSIVE"
    else:
        report["verdict"] = "PASS"
    return report


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(
        prog="enforce",
        description="the enforcement suite (legs 1-3 + pins + gates "
                    "plant) — exit 0 PASS, 1 FAIL, 2 INCONCLUSIVE")
    parser.add_argument("--verify-all", action="store_true",
                        help="run the whole declared verification")
    args = parser.parse_args(argv)
    report = verify_all() if args.verify_all else verify_all()
    sys.stdout.write(json.dumps(report, ensure_ascii=False,
                                sort_keys=True, separators=(",", ":"))
                     + "\n")
    return {"PASS": 0, "FAIL": 1, "INCONCLUSIVE": 2}[report["verdict"]]


if __name__ == "__main__":
    sys.exit(main())
