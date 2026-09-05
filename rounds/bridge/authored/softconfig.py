#!/usr/bin/env python3
"""softconfig — the runtime config-read (the bridge, C3/C4/K1/K2).

The read path the conductor now reads THROUGH: each desk's codex §2
emphasis, its voice, its model, and the cycle budget (the declared
charges + the default mode) come from a soft-layer config file at
runtime.  The file is DATA, never code, never doctrine (K5, H-BRIDGE-2:
the schema is a declared default — the constitution writes the real
soft files; the bridge authors no desk personality and no §2 content,
it reads them).

The declared shape (per desk S/G/Q/P/V, all caller-overridable):

  {
    "desks": {
      "G": {"emphasis": ["…", "…"], "voice": "…", "model": "…"},
      … S Q P V …
    },
    "budget": {"default_mode": "re-prompted",
               "charges": {"re-prompted": {"G": 2600, "Q": 3000,
                                           "P": 3400, "V": 4600},
                           "sub-process": {…}, "live": {…}}}
  }

Resolution of the file path: the caller's path, else the
``SOFT_CONFIG_PATH`` env var, else the declared default
``~/.config/herdr/soft.json``.

The three statuses of a read (lens 3 — absence vs validity):

  * ``defaults`` — NO soft config file exists: the declared defaults —
    B4's exact bytes/values (the pinned fixtures/desk.py codex §2 desk
    function-specs + attention readings, the declared single model
    (D6 / PRD §7 note), and cost.COST_MODEL's charges + default mode).
    The fixture run is unchanged (C4, C6).
  * ``ok`` — a complete soft config was read and validated.
  * ``inconclusive`` — the file is EMPTY, not UTF-8, not JSON, or
    malformed/partial (a missing desk, a wrong type, an unknown field,
    a bad budget entry): the read REFUSES — never a silently
    substituted value (C4); the reason is carried, never guessed.

Every byte of every value is carried verbatim — the encoding-lens
bytes (∞0′ → ‖) and the enumerated glyph forms (⋂, ∞0′ vs ∞0') pass
through untouched, never normalised (K2: normalising is renaming an L1
symbol).  Deterministic and stdlib-only: no network, no LLM, no
wall-clock; the file is read once, in binary, never text-mode byte
sought (lens 4).
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys

# The pinned default table is imported by path — never leave a bytecode
# cache beside a predecessor file (the workspace outside ./authored/
# must stay untouched).
sys.dont_write_bytecode = True

__all__ = [
    "SOFT_DEFAULTS",
    "DEFAULT_SOFT_CONFIG_PATH",
    "SOFT_CONFIG_PATH_ENV",
    "DESK_KEYS",
    "CHARGE_DESKS",
    "MODES",
    "DECLARED_MODEL",
    "load_soft_config",
    "desk_emphasis",
    "desk_voice",
    "desk_model",
    "budget_of",
    "default_mode",
    "SoftConfigError",
]

_HERE = os.path.dirname(os.path.abspath(__file__))
_PRED_B4 = os.path.normpath(os.path.join(
    _HERE, "..", "predecessors", "b4"))

SOFT_CONFIG_PATH_ENV = "SOFT_CONFIG_PATH"
DEFAULT_SOFT_CONFIG_PATH = os.path.expanduser(
    "~/.config/herdr/soft.json")

# The pinned folded-item carrier — B4's fixtures/desk.py (the codex §2
# desk function-specs and his-word attention readings, byte-faithful,
# sha-pinned, never re-authored, never copied — imported by path; lens
# 3: drifted bytes refuse the import, never silently substitute).
_DESK_PIN = {
    "path": os.path.join(_PRED_B4, "fixtures", "desk.py"),
    "sha256": ("0d8c47fd90a69a47107b78c143f4a59c33d4468ee5ce18f"
               "52446f1119303a06d"),
    "role": ("B4 fixtures/desk.py — the codex §2 desk function-specs "
             "and the attention readings (the declared defaults' bytes)"),
}


def _load_pinned_bytes(pinned, module_name):
    """Load one pinned predecessor file by path under ``module_name``,
    refusing (ImportError) when the bytes drift from the pin."""
    try:
        with open(pinned["path"], "rb") as handle:
            raw = handle.read()
    except OSError as exc:
        raise ImportError(
            "softconfig: the pinned file %s is unreadable (%s) — the "
            "declared defaults are INCONCLUSIVE, never substituted"
            % (pinned["path"], exc)) from None
    actual = hashlib.sha256(raw).hexdigest()
    if actual != pinned["sha256"]:
        raise ImportError(
            "softconfig: %s sha256 %s does not match the pinned %s — "
            "refusing to import a drifted default table"
            % (pinned["path"], actual, pinned["sha256"]))
    spec = importlib.util.spec_from_file_location(module_name,
                                                  pinned["path"])
    if spec is None or spec.loader is None:
        raise ImportError(
            "softconfig: cannot build an import spec for %s"
            % pinned["path"])
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_desk = _load_pinned_bytes(_DESK_PIN, "softconfig_b4_desk")

import cost  # noqa: E402  (cost.py is stdlib-only; no import cycle)

# The declared single model — D6: one model across the four desks in
# v1 (PRD §7 note: "Desk model reality today: pi --provider
# kimi-coding --model kimi-k3 … the model is a block, swappable, never
# hardcoded in doctrine").  A declared default, soft-config-overridable.
DECLARED_MODEL = "kimi-k3"

DESK_KEYS = ("S", "G", "Q", "P", "V")
CHARGE_DESKS = ("G", "Q", "P", "V")
MODES = frozenset(cost.COST_MODEL["modes"])


def _defaults():
    """The declared defaults — B4's exact bytes/values (C4): emphasis =
    the codex §2 desk function-specs, voice = his-word attention
    readings (both byte-exact from the pinned fixtures/desk.py), model
    = the declared single model, budget = COST_MODEL's charges +
    default mode (byte-exact).  A fresh deep structure per call — a
    caller mutating a returned view never mutates the declaration."""
    return {
        "desks": {
            desk: {
                "emphasis": tuple(_desk.DESK_FUNCTION_SPECS[desk]),
                "voice": _desk.ATTENTION_READINGS[desk],
                "model": DECLARED_MODEL,
            }
            for desk in DESK_KEYS
        },
        "budget": {
            "default_mode": cost.COST_MODEL["default_mode"],
            "charges": {
                mode: dict(per_desk)
                for mode, per_desk in cost.COST_MODEL["charges"].items()
            },
        },
    }


SOFT_DEFAULTS = _defaults()


class SoftConfigError(Exception):
    """A soft-config read is INCONCLUSIVE and no value was
    substituted."""


# ---------------------------------------------------------------------------
# The strict schema validation — fail closed.  A config that is not a
# complete, correctly-typed object is INCONCLUSIVE with the reason:
# missing a desk, wrong type, bad field, unknown key, empty file —
# never a silently substituted value (C4, lens 3/6).
# ---------------------------------------------------------------------------

_DESK_FIELDS = frozenset(("emphasis", "voice", "model"))
_BUDGET_FIELDS = frozenset(("default_mode", "charges"))
_TOP_FIELDS = frozenset(("desks", "budget"))


def _validate(parsed):
    """(ok, reason) over a parsed JSON value.  Returns (True, "") for a
    complete, correctly-typed soft config."""
    if not isinstance(parsed, dict):
        return (False, "the soft config is not a JSON object (got %s)"
                % type(parsed).__name__)
    unknown = sorted(set(parsed) - _TOP_FIELDS)
    if unknown:
        return (False, "unknown top-level field(s): %s"
                % ", ".join(unknown))
    desks = parsed.get("desks")
    if not isinstance(desks, dict):
        return (False, "'desks' is missing or not an object — the "
                       "per-desk read is incomplete")
    missing = sorted(set(DESK_KEYS) - set(desks))
    if missing:
        return (False, "missing desk(s): %s — a partial soft config "
                       "never reads valid" % ", ".join(missing))
    extra = sorted(set(desks) - set(DESK_KEYS))
    if extra:
        return (False, "unknown desk key(s): %s — no desk beyond "
                       "S/G/Q/P/V" % ", ".join(extra))
    for desk in DESK_KEYS:
        entry = desks[desk]
        if not isinstance(entry, dict):
            return (False, "desks.%s is not an object (got %s)"
                    % (desk, type(entry).__name__))
        unknown = sorted(set(entry) - _DESK_FIELDS)
        if unknown:
            return (False, "desks.%s carries unknown field(s): %s"
                    % (desk, ", ".join(unknown)))
        for field in _DESK_FIELDS:
            if field not in entry:
                return (False, "desks.%s is missing %r — a partial "
                               "soft config never reads valid"
                        % (desk, field))
            value = entry[field]
            if field == "emphasis":
                if (not isinstance(value, list) or not value
                        or not all(isinstance(item, str) and item
                                   for item in value)):
                    return (False, "desks.%s.emphasis must be a "
                                   "non-empty list of non-empty "
                                   "strings (got %s)"
                            % (desk, type(value).__name__))
            else:
                if not isinstance(value, str) or not value:
                    return (False, "desks.%s.%s must be a non-empty "
                                   "string (got %s)"
                            % (desk, field, type(value).__name__))
    budget = parsed.get("budget")
    if budget is not None:
        if not isinstance(budget, dict):
            return (False, "'budget' is not an object (got %s)"
                    % type(budget).__name__)
        unknown = sorted(set(budget) - _BUDGET_FIELDS)
        if unknown:
            return (False, "'budget' carries unknown field(s): %s"
                    % ", ".join(unknown))
        declared = budget.get("default_mode")
        if declared is not None:
            if not isinstance(declared, str) or declared not in MODES:
                return (False, "budget.default_mode %r is not a "
                               "declared mode (%s)"
                        % (declared, ", ".join(sorted(MODES))))
        charges = budget.get("charges")
        if charges is not None:
            if not isinstance(charges, dict):
                return (False, "budget.charges is not an object (got "
                               "%s)" % type(charges).__name__)
            for mode, per_desk in charges.items():
                if not isinstance(mode, str) or mode not in MODES:
                    return (False, "budget.charges.%r is not a "
                                   "declared mode (%s)"
                            % (mode, ", ".join(sorted(MODES))))
                if not isinstance(per_desk, dict):
                    return (False, "budget.charges.%s is not an "
                                   "object" % mode)
                missing_c = sorted(set(CHARGE_DESKS) - set(per_desk))
                if missing_c:
                    return (False, "budget.charges.%s is missing "
                                   "desk(s): %s — a partial budget "
                                   "never reads valid"
                            % (mode, ", ".join(missing_c)))
                extra_c = sorted(set(per_desk) - set(CHARGE_DESKS))
                if extra_c:
                    return (False, "budget.charges.%s carries unknown "
                                   "desk key(s): %s"
                            % (mode, ", ".join(extra_c)))
                for desk, value in per_desk.items():
                    if (not isinstance(value, int)
                            or isinstance(value, bool) or value < 0):
                        return (False, "budget.charges.%s.%s must be a "
                                       "non-negative integer (got %r)"
                                % (mode, desk, value))
    return (True, "")


# ---------------------------------------------------------------------------
# The read.
# ---------------------------------------------------------------------------


def load_soft_config(path=None):
    """Read the soft-layer config and return the SOFT VIEW:

      {"status": "defaults"|"ok"|"inconclusive",
       "path": <the resolved path>,
       "config": <the effective config — the declared defaults when
                  "defaults", the validated read when "ok", None when
                  "inconclusive">,
       "reason": <why — carried, never hidden>}

    Absent file → ``defaults`` (the declared defaults — C4).  Empty /
    malformed / partial file → ``inconclusive`` with the reason — never
    a silently substituted value (lens 3/6: an empty file's sha256 is
    e3b0c44298fc… and reads nothing).  Deterministic and stdlib-only.
    """
    resolved = (path or os.environ.get(SOFT_CONFIG_PATH_ENV)
                or DEFAULT_SOFT_CONFIG_PATH)
    try:
        with open(resolved, "rb") as handle:
            raw = handle.read()
    except OSError:
        return {"status": "defaults", "path": resolved,
                "config": _defaults(),
                "reason": ("no soft config file at %r — the declared "
                           "defaults (B4's exact bytes/values) apply "
                           "(C4)" % resolved)}
    if not raw:
        return {"status": "inconclusive", "path": resolved,
                "config": None,
                "reason": ("the soft config file %r is EMPTY (sha256 "
                           "%s) — an empty file never reads valid; "
                           "INCONCLUSIVE, never a substituted value "
                           "(lens 3)"
                           % (resolved,
                              hashlib.sha256(b"").hexdigest()))}
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        return {"status": "inconclusive", "path": resolved,
                "config": None,
                "reason": ("the soft config file %r is not valid UTF-8 "
                           "(%s) — INCONCLUSIVE, never a substituted "
                           "value" % (resolved, exc))}
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        return {"status": "inconclusive", "path": resolved,
                "config": None,
                "reason": ("the soft config file %r is not valid JSON "
                           "(%s) — INCONCLUSIVE, never a substituted "
                           "value" % (resolved, exc))}
    ok, reason = _validate(parsed)
    if not ok:
        return {"status": "inconclusive", "path": resolved,
                "config": None,
                "reason": "the soft config file %r is malformed: %s — "
                          "INCONCLUSIVE, never a silently substituted "
                          "value" % (resolved, reason)}
    effective = {"desks": parsed["desks"],
                 "budget": dict(_defaults()["budget"])}
    if parsed.get("budget") is not None:
        effective["budget"]["default_mode"] = parsed["budget"].get(
            "default_mode", effective["budget"]["default_mode"])
        effective["budget"]["charges"] = parsed["budget"].get(
            "charges", effective["budget"]["charges"])
    reason = "read from %r" % resolved
    if parsed.get("budget") is None:
        reason += (" — no budget section: the declared budget defaults "
                   "apply (the per-desk read is complete)")
    return {"status": "ok", "path": resolved, "config": effective,
            "reason": reason}


def _view_config(soft):
    """The effective config of a soft view — refusing (SoftConfigError)
    to read an inconclusive or non-view object: never a substituted
    value."""
    if not isinstance(soft, dict) or soft.get("status") not in (
            "ok", "defaults"):
        reason = soft.get("reason") if isinstance(soft, dict) else None
        raise SoftConfigError(
            "the soft view is not readable%s — INCONCLUSIVE, never "
            "substituted" % (": %s" % reason if reason else ""))
    return soft["config"]


def desk_emphasis(soft, desk):
    """-> the desk's codex §2 emphasis lines (a tuple of byte-exact
    strings) — the prompt's function-spec block, read through the soft
    layer."""
    config = _view_config(soft)
    if desk not in DESK_KEYS:
        raise SoftConfigError("unknown desk key %r" % (desk,))
    return tuple(config["desks"][desk]["emphasis"])


def desk_voice(soft, desk):
    """-> the desk's voice / seat (a byte-exact string) — the prompt's
    attention-mode reading, read through the soft layer."""
    config = _view_config(soft)
    if desk not in DESK_KEYS:
        raise SoftConfigError("unknown desk key %r" % (desk,))
    return config["desks"][desk]["voice"]


def desk_model(soft, desk):
    """-> the desk's model (a byte-exact string, D6: the declared
    single model by default), read through the soft layer at runtime."""
    config = _view_config(soft)
    if desk not in DESK_KEYS:
        raise SoftConfigError("unknown desk key %r" % (desk,))
    return config["desks"][desk]["model"]


def budget_of(soft, mode, desk):
    """-> the declared charge of one turn of ``desk`` in ``mode`` —
    the budget path's value, read through the soft layer (defaults =
    cost.COST_MODEL["charges"], byte-exact)."""
    config = _view_config(soft)
    charges = config["budget"]["charges"]
    if mode not in charges:
        raise SoftConfigError("unknown desk mode %r" % (mode,))
    if desk not in charges[mode]:
        raise SoftConfigError(
            "no declared charge for desk %r in mode %r" % (desk, mode))
    return charges[mode][desk]


def default_mode(soft):
    """-> the declared default desk mode, read through the soft layer
    (default = cost.COST_MODEL["default_mode"], byte-exact)."""
    config = _view_config(soft)
    return config["budget"]["default_mode"]
