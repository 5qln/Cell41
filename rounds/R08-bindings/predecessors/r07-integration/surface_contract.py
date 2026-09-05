#!/usr/bin/env python3
"""surface_contract — the integration round's contract seam: the CLI
binds the attested engine THROUGH this module, never beside it.

The integration is the seam, not new engine logic: the soft layer must
never contain driving logic — it only points at the engine (SCOPE §0,
verbatim).  This module pins every engine file it imports by path and
sha256 and refuses (ImportError) on any drift or absence — exactly the
R06 ``surface_contract.py`` pattern, imported never re-authored:

  * the R06 contract (``predecessors/r06-orchestration/surface_contract.py``)
    is itself a pinned entry, loaded from its canonical round directory
    and pinned against the staged bytes — the same load-anchor note R06
    carried for the bridge/B3 (the staged bytes are identical; the sha
    pins are the contract either way).  Loading it re-runs R06's own
    pin table: B0, B2, P4a, P4b, B3, B4, the bridge, and R06's
    word/navigate/materialize — every one refused on drift.
  * the three modules R06's contract does not pin (``orchestrate.py``,
    the fixture desk harness, the fixture builder) are pinned here and
    loaded with the module environment their own round had (the plain
    names ``surface_contract`` / ``fractal_ledger`` bound during the
    exec — R06's ``load_bridge_run`` pattern).
  * the Grammar (``codex`` / ``decoder`` / ``compiler`` / ``corruption``,
    library-only, no mains) is pinned here and loaded from its canonical
    round (``rounds/meta-implementation/authored``).
  * the B0 ledger is pinned here and loaded by path (FRACTAL_LEDGER_DIR).

Beyond the engine re-exports, this module declares the SEAM SURFACE in
one place, versioned: the command set (candidate names, H-INT-2/D4),
the one-call binding per command, the exit-code convention, the report
serialization formula (the C3 byte-identity contract), the run-lock
declaration (C5), the live-cell spec schema (H-INT-4 — provisional,
declared data), and the enforcement declaration (scan roots, forbidden
tokens, allowlist, entry-point census — SCOPE §4 legs 1-3).  All of it
is DATA — one place to change, diff-able, never logic (K5).

Fail closed: a pinned file that is missing, drifted, or unreadable
raises ImportError at import time — a contract that cannot be verified
is INCONCLUSIVE, never silently substituted (commission lens 6, C7).
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys

# The pinned loads import the predecessors by path — never leave a
# bytecode cache beside a predecessor file (the workspace outside
# ./authored/ must stay untouched).
sys.dont_write_bytecode = True

__all__ = [
    "PINNED_FILES",
    "CONTRACT_VERSION",
    "SEAM_SURFACE",
    "SEAM_MANIFEST",
    "SPEC_SCHEMA",
    "load_cell_spec",
    "resolve_cell_spec",
    "SpecError",
    "ledger",
    "r06_contract",
    "orchestrate",
    "desk_harness",
    "fixtures_build_r06",
    "codex",
    "decoder",
    "compiler",
    "corruption",
]

_HERE = os.path.dirname(os.path.abspath(__file__))
_PRED = os.path.normpath(os.path.join(_HERE, "..", "predecessors"))
_R06_DIR = os.path.join(_PRED, "r06-orchestration")
_LEDGER_DIR = os.environ.get(
    "FRACTAL_LEDGER_DIR", "/home/deploy/the-cell/ledger")
# The canonical load anchors (the R06 precedent, module docstring):
# the R06 contract resolves its own anchors (its ``_HERE`` → word/
# navigate/materialize; its ``_ROUNDS`` → bridge + R04-B3) only from
# inside its own round, so — exactly as R06 reads the bridge/B3 from
# their canonical rounds — this round loads the R06 contract from
# ``rounds/R06-orchestration/authored``, pinned against the staged
# bytes.  The Grammar is read from its canonical round (not staged).
_CELL_ROOT = os.path.dirname(_LEDGER_DIR)
_R06_CANON_DIR = os.path.join(_CELL_ROOT, "rounds",
                              "R06-orchestration", "authored")
_META_CANON_DIR = os.path.join(_CELL_ROOT, "rounds",
                               "meta-implementation", "authored")

# ---------------------------------------------------------------------------
# The pinned files this round adds to R06's own pin table (the R06
# contract re-verifies everything else at load).  Staged bytes are the
# contract; the load anchor for the R06 contract is its canonical round
# (identical bytes, verified on this box).
# ---------------------------------------------------------------------------

PINNED_FILES = (
    {
        "path": os.path.join(_LEDGER_DIR, "fractal_ledger.py"),
        "sha256": "b291e65967e0d1f98205a9bd612507fa788ea4f9aa99e5d6b8fa5f366895546d",
        "role": "B0 ledger and record (the chain — via FRACTAL_LEDGER_DIR, never copied)",
    },
    {
        "path": os.path.join(_R06_DIR, "surface_contract.py"),
        "sha256": "154a6522620ac2ebb7f77503e4143d2984f5e3917c8964ab2c9105fde63e7184",
        "role": "R06's contract seam (the immediate predecessor — imported, never re-authored)",
        "load_from": os.path.join(_R06_CANON_DIR, "surface_contract.py"),
    },
    {
        "path": os.path.join(_R06_DIR, "orchestrate.py"),
        "sha256": "ccc97a38b5353b9b023fa5fbbadc45e5c6f2e7fda13cde6868d034d7e9e5aa1e",
        "role": "R06 orchestrate — the conductor (Orchestrator, BootError, main — bound, never re-implemented)",
    },
    {
        "path": os.path.join(_R06_DIR, "fixtures", "desk_harness.py"),
        "sha256": "2e85c8ecd7df1b7aca23902363dac6504708c538e59bb906270a185fa232e06c",
        "role": "R06 fixture desk harness (deterministic, no live box — fixture apparatus, never the production surface)",
    },
    {
        "path": os.path.join(_R06_DIR, "fixtures", "build.py"),
        "sha256": "ae63f4f61e5aac6725a42c3f1f549ab28c83c0bb7c946cbbdf15232441a76620",
        "role": "R06 fixture builder (the harness spec + the pattern scenarios — fixture apparatus)",
    },
    {
        "path": os.path.join(_META_CANON_DIR, "codex.py"),
        "sha256": "f550457aef1679b1f5127a75942de95572784231e106fe99559fd53f7eedd0f8",
        "role": "the Grammar — codex (the sealed carrier: COURSE, EQUATION_FORMS, PHASE_SLOTS, the §3.6 contract)",
    },
    {
        "path": os.path.join(_META_CANON_DIR, "decoder.py"),
        "sha256": "7ee2ea130b85ecf77827d6c9492b5f736651ad153a061ae1ce1829f9cf6c1ef5",
        "role": "the Grammar — decoder (D1: filled symbol slots as references, never text)",
    },
    {
        "path": os.path.join(_META_CANON_DIR, "compiler.py"),
        "sha256": "ffb5b8d585549be8cf2b29e7a75ac2eaf851c0912a0cde0ed04426af1fa9ff19",
        "role": "the Grammar — compiler (C1: the §3.6 surface + jacket; the 48-item validation; HC-1/HC-2 INCONCLUSIVE by design)",
    },
    {
        "path": os.path.join(_META_CANON_DIR, "corruption.py"),
        "sha256": "0969f646be7f43e3ee4394e1c164f0e390cef213afbcd3a2a19f4034be83b16b",
        "role": "the Grammar — corruption (the five codes L1 L2 L3 L4 V∅ only — no sixth exists)",
    },
)


def _pin_for(path):
    for pinned in PINNED_FILES:
        if os.path.abspath(pinned["path"]) == os.path.abspath(path):
            return pinned
    raise ImportError("surface_contract: no pin entry for %s" % path)


def _load_pinned(pinned, module_name, path_entries=(), bind_names=None,
                 bind_self_as=None):
    """Load one pinned file by path under ``module_name``, refusing
    (ImportError) when the bytes drift from the pin.  ``path_entries``
    is inserted at sys.path[0] for the load only, so the module's
    sibling imports resolve inside its own round.  ``bind_names`` binds
    plain module names in sys.modules for the exec's duration —
    the short-circuit the loaded round's own selftest had (the staged
    orchestrate's ``from surface_contract import …`` resolves against
    the contract, never against a staging copy whose own anchors are
    off).  ``bind_self_as`` binds the module being loaded under a
    plain name too — the R06 contract's own module loads (word /
    navigate / materialize) import ``surface_contract``, which in its
    own round IS the contract: binding it under itself reproduces that
    module environment exactly."""
    if pinned["sha256"].startswith("TBD"):
        raise ImportError(
            "surface_contract: %s has no pin (TBD placeholder) — the "
            "contract is INCONCLUSIVE, never substituted" % pinned["path"])
    source = pinned.get("load_from") or pinned["path"]
    try:
        with open(source, "rb") as handle:
            raw = handle.read()
    except OSError as exc:
        raise ImportError(
            "surface_contract: the pinned file %s is unreadable (%s) — the "
            "attested surface is INCONCLUSIVE, never substituted"
            % (source, exc)) from None
    actual = hashlib.sha256(raw).hexdigest()
    if actual != pinned["sha256"]:
        raise ImportError(
            "surface_contract: %s sha256 %s does not match the pinned %s — "
            "refusing to import a drifted contract"
            % (source, actual, pinned["sha256"]))
    saved = sys.path[:]
    saved_names = {name: sys.modules.get(name)
                   for name in (bind_names or {})}
    if bind_self_as is not None:
        saved_names.setdefault(bind_self_as,
                               sys.modules.get(bind_self_as))
    try:
        for entry in reversed(path_entries):
            sys.path.insert(0, entry)
        for name, module in (bind_names or {}).items():
            sys.modules[name] = module
        spec = importlib.util.spec_from_file_location(module_name, source)
        if spec is None or spec.loader is None:
            raise ImportError(
                "surface_contract: cannot build an import spec for %s"
                % source)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        if bind_self_as is not None:
            sys.modules[bind_self_as] = module
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path[:] = saved
        for name, module in saved_names.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


if _LEDGER_DIR not in sys.path:
    sys.path.insert(0, _LEDGER_DIR)

# -- the B0 ledger (loaded first: the R06 contract and the conductor
#    both resolve ``fractal_ledger`` through this same module object) ----
ledger = _load_pinned(
    _pin_for(os.path.join(_LEDGER_DIR, "fractal_ledger.py")),
    "fractal_ledger", path_entries=(_LEDGER_DIR,))

# -- R06's contract (the immediate predecessor) -----------------------------
# Loaded from its canonical round (the load-anchor note above), pinned
# against the staged bytes.  Its exec re-verifies R06's whole pin table
# and re-exports the attested engine; it also leaves its own module
# registrations (word/navigate/materialize/…) in sys.modules — correct:
# they ARE the engine modules for this process.
r06_contract = _load_pinned(
    _pin_for(os.path.join(_R06_DIR, "surface_contract.py")),
    "r06_contract", path_entries=(_R06_CANON_DIR, _LEDGER_DIR),
    bind_self_as="surface_contract")

# Re-export the attested engine surface — never re-declared, never
# re-implemented: every name below is the loaded R06 contract's own.
# (R06's __all__ carries a few historical names it never bound — only
# names actually present on the loaded module are re-exported; the
# seam's own declarations PINNED_FILES / CONTRACT_VERSION / SEAM_SURFACE
# / SEAM_MANIFEST / SPEC_SCHEMA are never shadowed by a re-export.)
_REEXPORT_GUARD = frozenset((
    "PINNED_FILES", "CONTRACT_VERSION", "SEAM_SURFACE", "SEAM_MANIFEST",
    "SPEC_SCHEMA", "L1_DECLARATION"))
for _name in r06_contract.__all__:
    if _name not in _REEXPORT_GUARD and hasattr(r06_contract, _name):
        globals()[_name] = getattr(r06_contract, _name)
__all__.extend(_name for _name in r06_contract.__all__
               if _name not in _REEXPORT_GUARD
               and hasattr(r06_contract, _name))

# -- R06 orchestrate (bound: its plain-name imports resolve against the
#    contract and the ledger module above — the same module environment
#    its own round had) -----------------------------------------------------
orchestrate = _load_pinned(
    _pin_for(os.path.join(_R06_DIR, "orchestrate.py")), "orchestrate",
    path_entries=(_LEDGER_DIR,),
    bind_names={"surface_contract": r06_contract,
                "fractal_ledger": ledger})

# -- the R06 fixture apparatus (pinned, bound the same way) -----------------
desk_harness = _load_pinned(
    _pin_for(os.path.join(_R06_DIR, "fixtures", "desk_harness.py")),
    "desk_harness", bind_names={"surface_contract": r06_contract})

DeskHarness = desk_harness.DeskHarness
PANES = desk_harness.PANES
absent_socket_path = desk_harness.absent_socket_path

fixtures_build_r06 = _load_pinned(
    _pin_for(os.path.join(_R06_DIR, "fixtures", "build.py")),
    "fixtures_build_r06", bind_names={"surface_contract": r06_contract})

# -- the Grammar (library-only; its plain-name siblings resolve inside
#    its own canonical round) ----------------------------------------------
codex = _load_pinned(_pin_for(os.path.join(_META_CANON_DIR, "codex.py")),
                      "codex", path_entries=(_META_CANON_DIR,))
corruption = _load_pinned(
    _pin_for(os.path.join(_META_CANON_DIR, "corruption.py")), "corruption",
    path_entries=(_META_CANON_DIR,))
decoder = _load_pinned(
    _pin_for(os.path.join(_META_CANON_DIR, "decoder.py")), "decoder",
    path_entries=(_META_CANON_DIR,))
compiler = _load_pinned(
    _pin_for(os.path.join(_META_CANON_DIR, "compiler.py")), "compiler",
    path_entries=(_META_CANON_DIR,))

# -- this round's contract version ------------------------------------------
CONTRACT_VERSION = "integration-1"

# ---------------------------------------------------------------------------
# The spec schema (H-INT-4 — provisional; declared data, one place to
# change).  Every field the engine reads from the soft layer is here;
# an unknown field is REFUSED (INCONCLUSIVE, never silently ignored —
# commission C4/L3, the attested softconfig behavior extended to the
# live cell spec).
# ---------------------------------------------------------------------------

SPEC_SCHEMA = {
    "version": 1,
    "fields": {
        "spec_version": {"required": True, "types": ("int",),
                         "value": 1},
        "round": {"required": False, "types": ("str",)},
        "work_dir": {"required": True, "types": ("str",),
                     "nonempty": True,
                     "doc": "the cell's work dir — the run lock lives here (C5)"},
        "scenario": {"required": True, "types": ("str", "null"),
                     "nonempty": True,
                     "doc": "the scenario file the run decodes; null = no acceptance word declared (D2 open — the run refuses INCONCLUSIVE)"},
        "ledger": {"required": True, "types": ("str",), "nonempty": True,
                   "doc": "the B0 ledger path (the run appends per-gate records)"},
        "trail": {"required": True, "types": ("str",), "nonempty": True,
                  "doc": "the B4 trail path (the run's readable trail)"},
        "live_socket": {"required": False, "types": ("str", "null"),
                        "nonempty": True,
                        "doc": "the resolved herdr socket path; null = the engine's own resolution (HERDR_SOCKET_PATH → ~/.config/herdr/herdr.sock) — never resolved in the wrapper"},
        "socket_dir": {"required": False, "types": ("str", "null")},
        "materialize": {"required": False, "types": ("str", "null"),
                        "nonempty": True,
                        "doc": "the materialize dir (the optional write-path, \"not every run\")"},
        "materialized": {"required": False, "types": ("str", "null"),
                         "nonempty": True,
                         "doc": "an already-materialized word, verified from disk"},
        "soft_config": {"required": False, "types": ("str", "null"),
                        "nonempty": True,
                        "doc": "the soft.json path (the bridge's runtime config-read)"},
        "observe_states": {"required": False, "types": ("bool",)},
        "block_version": {"required": False, "types": ("str",)},
        "scope": {"required": False, "types": ("str",)},
        "clock": {"required": False, "types": ("null", "dict"),
                  "doc": "fixture data only; null = the engine's declared default (the live numbers are W4's, Seam E)"},
        "wait_timeout_ms": {"required": False, "types": ("int",),
                            "doc": "PROVISIONAL (H-INT-4): caller-supplied data, never a wrapper constant"},
        "timeout_s": {"required": False, "types": ("int", "float")},
        "max_steps": {"required": False, "types": ("int", "null"),
                      "doc": "the caller's step budget; null = the word's length is the bound"},
        "notes": {"required": False, "types": ("dict",),
                  "doc": "declared reasons — the provisional numbers carry their provenance here (data, diff-able)"},
    },
}


class SpecError(ValueError):
    """The live cell spec was refused: absent / malformed / unknown
    field — INCONCLUSIVE, never a silently substituted value."""


def _check_type(value, types, field):
    for kind in types:
        if kind == "null" and value is None:
            return
        if kind == "int" and isinstance(value, int) \
                and not isinstance(value, bool):
            return
        if kind == "float" and isinstance(value, (int, float)) \
                and not isinstance(value, bool):
            return
        if kind == "str" and isinstance(value, str):
            return
        if kind == "bool" and isinstance(value, bool):
            return
        if kind == "dict" and isinstance(value, dict):
            return
    raise SpecError("spec field %r must be %s (got %s)"
                    % (field, "|".join(types), type(value).__name__))


def load_cell_spec(path):
    """Read + validate the live cell spec — binary read, UTF-8 decode
    (lens 4: never a text-mode byte seek).  Returns:

      {"status": "ok", "spec": <the validated spec>, "reason": …}
      {"status": "absent"|"inconclusive", "reason": …}

    Absent file, empty file (the sha256 of empty is e3b0c44298fc…),
    bad JSON, wrong types, and — load-bearing — any unknown top-level
    field all REFUSE (C4/L3).  Never a substituted default beyond the
    declared schema."""
    try:
        with open(path, "rb") as handle:
            raw = handle.read()
    except OSError as exc:
        return {"status": "absent", "path": path,
                "reason": "no cell spec at %r (%s) — nothing to read"
                          % (path, exc)}
    if not raw:
        return {"status": "inconclusive", "path": path,
                "sha256": hashlib.sha256(b"").hexdigest(),
                "reason": ("the cell spec %r is EMPTY — the sha256 of "
                           "empty is e3b0c44298fc…, never valid "
                           "(lens 3)" % path)}
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        return {"status": "inconclusive", "path": path,
                "reason": "the cell spec %r is not valid UTF-8 (%s)"
                          % (path, exc)}
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        return {"status": "inconclusive", "path": path,
                "reason": "the cell spec %r is not valid JSON (%s)"
                          % (path, exc)}
    if not isinstance(parsed, dict):
        return {"status": "inconclusive", "path": path,
                "reason": "the cell spec is not a JSON object (got %s)"
                          % type(parsed).__name__}
    try:
        unknown = sorted(set(parsed) - set(SPEC_SCHEMA["fields"]))
        if unknown:
            raise SpecError(
                "the cell spec carries unknown field(s): %s — unknown "
                "fields read INCONCLUSIVE, never ignored (C4/L3)"
                % ", ".join(unknown))
        for field, decl in SPEC_SCHEMA["fields"].items():
            if field not in parsed:
                if decl.get("required"):
                    raise SpecError("the cell spec is missing %r — a "
                                    "partial spec never reads valid"
                                    % field)
                continue
            value = parsed[field]
            _check_type(value, decl["types"], field)
            if decl.get("nonempty") and value is not None \
                    and isinstance(value, str) and not value:
                raise SpecError("spec field %r must be non-empty" % field)
            if "value" in decl and value != decl["value"]:
                raise SpecError("spec field %r must be %r (got %r)"
                                % (field, decl["value"], value))
        if parsed.get("notes") is not None:
            for key, value in parsed["notes"].items():
                if not isinstance(key, str) or not isinstance(value, str):
                    raise SpecError("spec.notes must map strings to "
                                    "strings (declared reasons)")
        if parsed.get("clock") is not None and not isinstance(
                parsed.get("clock"), dict):
            raise SpecError("spec field 'clock' must be null or an object")
    except SpecError as exc:
        return {"status": "inconclusive", "path": path,
                "reason": str(exc)}
    return {"status": "ok", "path": path, "spec": parsed,
            "reason": "the cell spec validates against the declared "
                      "schema (provisional — H-INT-4)"}


def resolve_cell_spec(spec, base_dir):
    """Resolve a validated spec into the caller's declared paths +
    the engine-spec the conductor reads.  Relative paths resolve
    against the spec file's directory (declared, documented).  The
    engine-spec carries ONLY the engine's own keys — the wrapper adds
    no quantity.  A spec with no scenario still resolves (the
    conductor refuses to run with the D2 reason — H-INT-4 honest)."""
    def _resolve(value):
        if not isinstance(value, str) or not value:
            return value
        if os.path.isabs(value):
            return value
        return os.path.normpath(os.path.join(base_dir, value))

    engine_keys = ("scope", "block_version", "wait_timeout_ms",
                   "timeout_s", "observe_states", "materialize",
                   "materialized", "live_socket", "soft_config", "clock")
    engine_spec = {}
    for key in engine_keys:
        if spec.get(key) is not None:
            engine_spec[key] = spec[key]
    for path_key in ("materialize", "materialized", "soft_config"):
        if engine_spec.get(path_key):
            engine_spec[path_key] = _resolve(engine_spec[path_key])
    return {
        "status": "ok",
        "spec": spec,
        "scenario": _resolve(spec.get("scenario")),
        "ledger": _resolve(spec.get("ledger")),
        "trail": _resolve(spec.get("trail")),
        "work_dir": _resolve(spec.get("work_dir")),
        "socket_dir": _resolve(spec.get("socket_dir")),
        "max_steps": spec.get("max_steps"),
        "engine_spec": engine_spec,
        "lock_path": os.path.join(_resolve(spec.get("work_dir")),
                                  ".cellctl.lock"),
    }


# ---------------------------------------------------------------------------
# The seam manifest — the declared entry-point census (SCOPE §4 leg 2)
# and the command set.  Every executable in the soft layer is a
# declared member here; an undeclared bin is a FAIL.  Data, one place
# to change; read from disk (the observed listing), never invented.
# ---------------------------------------------------------------------------

_SEAM_LAYER = os.path.normpath(os.path.join(_HERE, ".."))
_PLUGIN_BIN = os.path.join(_CELL_ROOT, "plugin", "bin")
_DESKS = os.path.join(_CELL_ROOT, "desks")
_PI_AGENT_SETTINGS = os.path.expanduser("~/.pi/agent/settings.json")
_SOFT_JSON = os.path.expanduser("~/.config/herdr/soft.json")
_STATE_GATES = os.path.join(_CELL_ROOT, "state", "gates.jsonl")

# The census, read from disk (the soft layer as it stands; the W5
# bindings extend it — an extension not declared here = FAIL).
SEAM_MANIFEST = {
    "version": 1,
    "entry_points": [
        # -- the seam itself -------------------------------------------------
        {"path": os.path.join(_HERE, "cellctl"),
         "role": "the seam CLI — one subcommand per engine module, one engine call each (the only path to the engine)"},
        {"path": os.path.join(_HERE, "verify-integration.sh"),
         "role": "the enforcement suite runner (pins + legs 1-3 + C3 plan-equivalence)"},
        # -- the live plugin bins (declared, read from disk) ------------------
        {"path": os.path.join(_PLUGIN_BIN, "cell-attest"),
         "role": "human-TTY attestation act (L1 allowlist — unchanged)"},
        {"path": os.path.join(_PLUGIN_BIN, "cell-plant"),
         "role": "human-TTY plant act (L1 allowlist — unchanged)"},
        {"path": os.path.join(_PLUGIN_BIN, "cell-begin"),
         "role": "free-corner gesture (read-only surface act)"},
        {"path": os.path.join(_PLUGIN_BIN, "cell-boot"),
         "role": "desk boot helper (declared bin)"},
        {"path": os.path.join(_PLUGIN_BIN, "cell-zoom"),
         "role": "zoom gesture (declared bin)"},
        {"path": os.path.join(_PLUGIN_BIN, "cell-on-desk-state"),
         "role": "desk state read (declared bin)"},
        {"path": os.path.join(_PLUGIN_BIN, "_cell_api.py"),
         "role": "the plugin's shared api module (declared, read from disk)"},
        {"path": os.path.join(_PLUGIN_BIN, "cell-attest.v1.bak"),
         "role": "retired backup (declared, read from disk)"},
        {"path": os.path.join(_PLUGIN_BIN, "cell-attest.v2.bak"),
         "role": "retired backup (declared, read from disk)"},
        {"path": os.path.join(_PLUGIN_BIN, "cell-plant.v1.bak"),
         "role": "retired backup (declared, read from disk)"},
        # -- the desk boot scripts -------------------------------------------
        {"path": os.path.join(_DESKS, "S", "boot.sh"),
         "role": "the S desk's boot (declared, read from disk)"},
        {"path": os.path.join(_DESKS, "G", "boot.sh"),
         "role": "the G desk's boot (declared, read from disk)"},
        {"path": os.path.join(_DESKS, "Q", "boot.sh"),
         "role": "the Q desk's boot (declared, read from disk)"},
        {"path": os.path.join(_DESKS, "P", "boot.sh"),
         "role": "the P desk's boot (declared, read from disk)"},
        {"path": os.path.join(_DESKS, "V", "boot.sh"),
         "role": "the V desk's boot (declared, read from disk)"},
    ],
    # The import rule (leg 2): the engine's pinned modules are callable
    # ONLY through the CLI.  surface_contract.py is the seam; these
    # files are the declared importers.
    "import_allowed": (
        os.path.join(_HERE, "surface_contract.py"),
        os.path.join(_HERE, "cellctl"),
        os.path.join(_HERE, "enforce.py"),
        os.path.join(_HERE, "selftest.py"),
    ),
    "pinned_module_names": (
        "word", "navigate", "materialize", "orchestrate",
        "surface_contract", "cost", "softconfig", "trail", "run",
        "descent", "instrument", "driver", "walker", "dialects", "lens",
        "grammar", "block", "arrangement", "install", "conformance",
        "step", "surface", "desk", "desk_server", "decoder", "compiler",
        "corruption", "codex", "fractal_ledger",
    ),
}

# The L1 declaration (SCOPE §4 leg 1): the forbidden write verbs, the
# scan roots, the declared allowlist (the human-TTY acts) and the
# declared exclusions (test apparatus — the scanner's own patterns and
# the fixture world).
L1_DECLARATION = {
    "forbidden_patterns": (
        (r"herdr_send_prompt",
         "pi-herdr write verb — a soft-layer drive channel"),
        (r"herdr\s+agent\s+prompt",
         "herdr CLI write verb — a soft-layer drive channel"),
        (r"agent\.prompt",
         "the engine's write method name in soft-layer reach — the single chokepoint stays the engine's"),
        (r"pane\.wait_for_output",
         "wait verb — driving logic in the soft layer"),
        (r"send[-_]keys|send[-_]text|send[-_]input",
         "podium/panes write verbs — no write path to the podium"),
        (r"socket\.AF_UNIX|\.sendall\(|\.connect\(",
         "socket-client code — the pinned Instrument is the only client (K1)"),
    ),
    # a file carrying subprocess + herdr + a prompt/wait verb is a
    # subprocess-to-herdr drive — checked as one composite pattern.
    "composite_patterns": (
        {"parts": (r"subprocess", r"herdr",
                   r"(?:agent\s+prompt|wait_for_output|send_prompt)"),
         "reason": "subprocess-to-herdr with a prompt/wait verb — driving logic in the soft layer"},
    ),
    "allowlist": (
        {"path_suffix": os.path.join("plugin", "bin", "cell-plant"),
         "reason": "the human's TTY plant act — declared, unchanged (H-ORCH-4)"},
        {"path_suffix": os.path.join("plugin", "bin", "cell-attest"),
         "reason": "the human's TTY attest act — declared, unchanged (H-ORCH-4)"},
    ),
    "excluded_paths": (
        os.path.join(_HERE, "enforce.py"),   # the scanner's own patterns
        os.path.join(_HERE, "selftest.py"),  # the author's suite
        os.path.join(_HERE, "fixtures"),     # fixture apparatus (the declared harness + injected violations)
    ),
    "scan_roots": (
        {"name": "plugin-bin", "path": _PLUGIN_BIN,
         "files": None, "executables": True, "required": True,
         "doc": "every plugin bin — tokens + census"},
        {"name": "desks", "path": _DESKS,
         "files": None, "executables": True, "required": True,
         "doc": "the desk constitutions + boot + .pi configs — tokens + census"},
        {"name": "pi-agent-config", "path": _PI_AGENT_SETTINGS,
         "files": None, "executables": False, "required": True,
         "doc": "the pi agent settings (config data — tokens only)"},
        {"name": "soft-config", "path": _SOFT_JSON,
         "files": None, "executables": False, "required": False,
         "doc": "the soft.json (absent = the engine's declared defaults)"},
        {"name": "authored-cli", "path": _HERE,
         "files": ("cellctl", "surface_contract.py",
                   "verify-integration.sh", "spec.json"),
         "executables": True, "required": True,
         "doc": "the seam's own layer — the CLI is the only path to the engine"},
    ),
    # the cell's own extension packages (W5's sibling — currently none;
    # the pi-herdr package and the herdr-managed integration file are
    # consumed platform, never the cell's soft layer — SCOPE §6).
    "extension_roots": (),
    # L3: the files the engine reads from the soft layer (schema-checked).
    "schema_targets": (
        {"name": "cell-spec", "path": os.path.join(_HERE, "spec.json"),
         "kind": "cell-spec"},
        {"name": "soft-config", "path": _SOFT_JSON, "kind": "soft-config"},
    ),
    "gates_plant": {"path": _STATE_GATES,
                    "sha256": "6989a742f57ec60a54d44062bad3fe9c6d2df28e66e92de96c1336be3a6539c3",
                    "citation": "the bridge's verify-live.sh expectation (his plant, byte-for-byte)"},
}

# ---------------------------------------------------------------------------
# The seam surface — the command set and the binding, declared in one
# place.  The command names are CANDIDATES (H-INT-2 / D4 — his to
# name); the functions are the real surface.
# ---------------------------------------------------------------------------

SEAM_SURFACE = {
    "version": 1,
    "contract_version": CONTRACT_VERSION,
    "round": "integration (the seam — wire the engine to the live cell; working handle, his to name)",
    "governing_line": ("the soft layer must never contain driving logic — "
                       "it only points at the engine. Slash commands are "
                       "the seam. One surface, two callers: the human "
                       "types /conduct, or the conductor S calls the "
                       "same command."),
    "what": ("cellctl is a thin, logic-free command surface over the "
             "attested engine functions: each subcommand parses its "
             "arguments and makes exactly one engine call; the wrapper "
             "contains no socket code, no prompt assembly, no "
             "record-writing, no ledger/trail logic (C1).  The write "
             "side (agent.prompt) is deliberately NOT exposed as a "
             "command (C2).  The engine is imported by path, "
             "sha-pinned, through this contract (C7).  /conduct takes "
             "one flock on the cell's work dir around the whole run "
             "(C5 — in the wrapper, never the engine)."),
    "serialization": ("every report is emitted as UTF-8 JSON via "
                      "json.dumps(report, ensure_ascii=False, "
                      "sort_keys=True, separators=(',', ':')) + '\\n' — "
                      "byte-exact, never normalised (K2); /compile "
                      "writes the emitted surface bytes raw; /conduct "
                      "passes the engine CLI's own output through "
                      "untouched.  The one declared envelope rule: the "
                      "read-trail report's ``raw`` field (the file's "
                      "own bytes, already on disk) is carried as its "
                      "sha256 under ``raw_sha256`` — a JSON-safety "
                      "declaration, never a content transformation.  "
                      "The C3 plan-equivalence reference "
                      "(fixtures/plan_equivalence.py) uses the same "
                      "formula over the same two direct calls."),
    "exit_codes": ("0 = the report's declared success status (per "
                   "command below) · 1 = any other status (absent / "
                   "malformed / INCONCLUSIVE — a blind spot never "
                   "reads clean) · /conduct passes the engine's own "
                   "codes through (0/1/3/4, argparse 2)"),
    "run_lock": {
        "path": "<work_dir>/.cellctl.lock",
        "mechanism": ("fcntl.flock LOCK_EX around the whole run — the "
                      "wrapper opens the lock file once, holds it "
                      "across the engine call, releases in a finally. "
                      "A second /conduct on the same work dir BLOCKS "
                      "rather than interleaves (C5)."),
        "plan_only_note": ("--plan-only touches no work dir (decode + "
                           "plan are pure) and takes no lock"),
    },
    "commands": {
        "word": {
            "engine": "word.load_scenario_file / word.decode_scenario",
            "one_call": True,
            "inputs": "a scenario file path (or --stdin raw bytes / --json inline JSON)",
            "outputs": "the decode report: ok + decoded scenario · absent/malformed/inconclusive + reason (never a substituted value)",
            "success": ("ok",),
            "candidate_slash": "/word",
        },
        "plan": {
            "engine": "navigate.plan_walk",
            "one_call": True,
            "inputs": "a DECODED scenario (JSON file — word.decode_scenario's \"scenario\" object)",
            "outputs": "{status, pattern, visits[], pattern_evidence[]} — pure, no socket, no ledger",
            "success": ("ok",),
            "candidate_slash": "/plan",
        },
        "walk": {
            "engine": "navigate.walk (world = orchestrate._LiveWorld — the attested live wiring)",
            "one_call": True,
            "inputs": "a resolved cell spec (scenario + live_socket + …) + optional --max-steps",
            "outputs": "the trace {status: complete|inconclusive|refused|step-limited, ended_in, visits[]} — the low-level surface; /conduct is the composite that also emits boot/steps/run-end",
            "success": ("complete",),
            "candidate_slash": "/walk",
        },
        "materialize": {
            "engine": "materialize.materialize / read_materialize (--verify)",
            "one_call": True,
            "inputs": "a decoded scenario + --out DIR (+ optional --visits plan JSON); --verify reads the materialized word back",
            "outputs": "materialized + per-node file shas · --verify: ok/inconclusive drift report",
            "success": ("materialized", "ok"),
            "candidate_slash": "/materialize",
        },
        "conduct": {
            "engine": "orchestrate.main (the engine's own CLI — a binding, never a re-implementation); --plan-only: word.decode_scenario + navigate.plan_walk (the C3 sequence)",
            "one_call": True,
            "inputs": "a resolved cell spec (--spec spec.json) + optional --max-steps; --plan-only takes --scenario directly",
            "outputs": "the run result + the engine's own exit codes (0/1/3/4); side effects: per-gate B0 records + B4 trail lines (the engine's)",
            "success": ("complete", "inconclusive", "refused", "step-limited", "already-complete"),
            "plan_only": ("byte-identical to word.decode_scenario + "
                          "navigate.plan_walk over the same scenario "
                          "bytes (C3) — the wrapper adds nothing"),
            "candidate_slash": "/conduct",
        },
        "config": {
            "engine": "softconfig.load_soft_config",
            "one_call": True,
            "inputs": "optional --path (soft.json); absent = the declared defaults",
            "outputs": "the soft view: defaults/ok/inconclusive + per-desk emphasis/voice/model + budget — read-only",
            "success": ("ok", "defaults"),
            "candidate_slash": "/config",
        },
        "cost": {
            "engine": "cost.spend_from_records (records read through the B0 LedgerLoader; optional soft charges through softconfig.budget_of)",
            "one_call": True,
            "inputs": "--ledger X --mode <mode> [--soft-config soft.json]",
            "outputs": "the declared spend per desk + the total",
            "success": ("ok",),
            "candidate_slash": "/cost",
        },
        "states": {
            "engine": "orchestrate.Orchestrator.read_states",
            "one_call": True,
            "inputs": "a resolved cell spec (the bootable conductor's own read)",
            "outputs": "per-desk real states (read-only); an absent socket reads {\"status\":\"absent\"} honestly — never a fixture stand-in (C2)",
            "success": ("observed",),
            "candidate_slash": "/states",
        },
        "descent": {
            "engine": "descent zoom_in / zoom_out / path_between / validate_signed_path / validate_word (one op per invocation)",
            "one_call": True,
            "inputs": "one op: path-between --from --to · zoom-in --address --letter · zoom-out --address · validate-path --path · validate-word --address",
            "outputs": "the address-grammar result (the +^k·(−x₁)…(−x_m) normalization)",
            "success": ("ok",),
            "candidate_slash": "/descent",
        },
        "decode": {
            "engine": "decoder.decode (D1: filled symbol slots as references, never text)",
            "one_call": True,
            "inputs": "--phase G + optional --values/--context/--trail/--claims (JSON files or inline) --lenses --cell --inserted-answer",
            "outputs": "the decode report: slots as refs, walked operations, corruption detections — never an authenticity verdict (K3)",
            "success": ("ok",),
            "candidate_slash": "/decode",
        },
        "compile": {
            "engine": "compiler.emit (C1: the §3.6 surface + jacket)",
            "one_call": True,
            "inputs": "--phase G --slots {…} + optional --lenses/--trail/--cell/--surface-only",
            "outputs": "the emitted surface bytes, RAW — byte-exact, never normalised (K2)",
            "success": ("ok",),
            "candidate_slash": "/compile",
        },
        "check": {
            "engine": "compiler.validate (the 48-item table CX/AD SYN/SEM/DRF + R1-R13 + HC-1/HC-2 + the corruption verdict L1..V∅ only)",
            "one_call": True,
            "inputs": "an artifact JSON (any produced surface) + optional --cycle JSON",
            "outputs": "the validation report — HC-1/HC-2 are INCONCLUSIVE by design; a machine can never report a fully clean artifact (K3)",
            "success": ("PASS",),
            "candidate_slash": "/check",
        },
        "trail": {
            "engine": "trail.read_trail (default) / audit_payload_chains over the B0 LedgerLoader's records (--audit)",
            "one_call": True,
            "inputs": "--ledger X --trail Y [--audit]",
            "outputs": "the readable trail (B4) · --audit: the dependency audit",
            "success": ("ok",),
            "candidate_slash": "/trail",
        },
    },
    "holds": {
        "H-INT-1": "no live agent.prompt is sent this round — the CLI is tested against the fixture desk harness only; the first real paid turn is Amihai's alone to authorize (W4)",
        "H-INT-2": "command names and the round's name/slot are provisional (D4) — the working handle is integration; the functions are the real surface",
        "H-INT-3": "child-spawn ownership is deferred (D1) — no herdr_start_agent-equivalent write; the engine's WRITE_METHODS stay frozen",
        "H-INT-4": "the scenario schema stays provisional (carried H-ORCH-2) and the live spec's numbers are unknown until the first real run (Seam E, W4) — they are declared data in spec.json, never hard-coded in logic",
        "H-INT-5": "the live constitutions do not yet speak the §3.6 surface (Seam B) — the CLI reports no-surface-announced/surface-malformed honestly when the engine holds, never papers over it",
    },
    "lenses": {
        "1": "criterion match — each criterion measured AS WRITTEN (C1 one-call binding · C2 no write verb · C3 plan-equivalence · C4 legs 1-3 · C5 run lock · C6 fail-closed · C7 pinned seams); every selftest names its criterion",
        "2": "invariant end-to-end — whole-run artifacts (plan → walk → materialize → conduct), never per call; the hand-off chain threads one record's payload_ref into the next prompt",
        "3": "absence vs validity — absent scenario / absent soft config / absent socket / empty file never read valid (sha256 of empty = e3b0c44298fc…)",
        "4": "encoding — ∞0′ → ‖ rides every string field (command args, spec, address, voice, emphasis) byte-verbatim; files opened binary-only, never text-mode byte sought",
        "5": "cold restart — a NEW process rebuilds the plan + the enforcement scans from disk alone; the second process honours the run lock",
        "6": "blind tool — an unavailable live socket or an unconstituted desk reports INCONCLUSIVE, never clean, never a fixture stand-in",
    },
}
