#!/usr/bin/env python3
"""lens — the Pi lens adapter and the §7 trust assertion (R03 · B2, K3, C4).

One thin adapter, no doctrine inside (§6.5): it does not author any
desk's instruction block or skill, it does not install or remove a Pi
extension, and it never writes to the Pi home.  It CONSUMES an
arrangement (``DESK_BLOCKS`` — data, never invented) and ASSERTS, against
the observed Pi runtime state, that a desk is constituted per §7:

    instruction (phase-gate) + at least one skill + tool surface + model

A desk that is not constituted raises ``TrustError``, and the boot fails
closed before the first prompt (§10.3, C4).

Observation is read-only and everything is a path parameter:

  * the Pi settings file (default ``~/.pi/agent/settings.json``) — the
    installed extensions are looked for under a ``"skills"`` key: a
    declared claim about where `pi install` records them (unproven;
    the live file holds only ``{"lastChangelogVersion": "0.84.2"}``);
  * the skills directory (default ``~/.pi/skills``) — the live box has
    none (commission §3.3); entries here count as installed skill names:
    a declared claim;
  * the ``pi`` binary (NOT invoked unless a path is passed in) — the
    output of ``pi list``, one skill name per line: a declared claim.

An unobservable source is INCONCLUSIVE, never clean (lens 6): when no
source can observe the skills, every named skill fails the assertion.

On today's box no extension is installed at all, and the desk instruction
blocks are an un-slotted phase (commission §3.3).  The shipped
arrangement ``DESK_BLOCKS`` records exactly that live absence — no
instruction authored, no skills — so the assertion fails closed on the
live state, which is the required behaviour: the C4 negative case is the
live default, not a synthetic one.
"""

from __future__ import annotations

import json
import os
import subprocess

__all__ = [
    "Lens",
    "TrustError",
    "assert_trust",
    "DESK_BLOCKS",
]

# The arrangement the trust assertion ASSERTS — data, never invented
# (commission §6.1, §7).  Each entry names the four §7 blocks of a desk.
# These entries record the arrangement as it stands on the live box
# 2026-08-27 (commission §3.3): the desk instruction blocks are a
# separate un-slotted phase (no text authored — recorded here as absence,
# never fabricated), no Pi extension is installed, and the tool surface
# and model are not recorded anywhere the read surface exposes.  Every
# entry therefore fails §7 and the boot assertion fails closed on the
# live state.  Tests and the verifier inject their own arrangement.
#
# Entry shape:
#   "instruction": str | None    — the phase-gate instruction block
#   "skills":      [str]         — at least one; each must be OBSERVED
#                                  installed in the Pi state
#   "tools":       [str] | None  — the tool surface allowlist
#   "model":       {provider, model} | None
DESK_BLOCKS = {
    "S": {"instruction": None, "skills": [], "tools": None, "model": None},
    "G": {"instruction": None, "skills": [], "tools": None, "model": None},
    "Q": {"instruction": None, "skills": [], "tools": None, "model": None},
    "P": {"instruction": None, "skills": [], "tools": None, "model": None},
    "V": {"instruction": None, "skills": [], "tools": None, "model": None},
}

_BLOCK_KEYS = ("instruction", "skills", "tools", "model")

# The settings key under which installed extensions ("skills") are
# expected — a declared claim about the Pi settings file, unproven live.
_SETTINGS_SKILLS_KEY = "skills"


class TrustError(Exception):
    """The §7 trust assertion failed: the desk is not constituted.

    ``stage`` is the block that failed — "arrangement" | "instruction" |
    "skills" | "tools" | "model" — and ``verdict`` is why: "missing" (the
    arrangement does not name it) | "not_loaded" (named but not observed
    installed) | "inconclusive" (the Pi state is unobservable — never
    "clean", lens 6)."""

    def __init__(self, desk, stage, verdict, detail):
        self.desk = desk
        self.stage = stage
        self.verdict = verdict
        self.detail = detail
        super().__init__(
            "trust assertion failed for desk %r at %r (%s): %s"
            % (desk, stage, verdict, detail))


class Lens:
    """The Pi lens adapter: read-only observation of the Pi state plus the
    §7 constitution assertion for one desk.

    ``Lens(pi_home=…)`` — every path is a parameter (tests use tempfile
    directories; the live ~/.pi is never written).  ``pi_bin`` is None by
    default, so the binary is never invoked unless the caller supplies a
    path (and its output shape remains a declared claim).  ``blocks``
    defaults to ``DESK_BLOCKS``.
    """

    def __init__(self, pi_home=None, settings_path=None, skills_dir=None,
                 pi_bin=None, timeout_s=15.0, blocks=None):
        self.pi_home = (
            os.path.expanduser(pi_home) if pi_home is not None
            else os.path.expanduser("~/.pi"))
        self.settings_path = (
            settings_path if settings_path is not None
            else os.path.join(self.pi_home, "agent", "settings.json"))
        self.skills_dir = (
            skills_dir if skills_dir is not None
            else os.path.join(self.pi_home, "skills"))
        self.pi_bin = pi_bin
        self.timeout_s = float(timeout_s)
        self.blocks = dict(blocks) if blocks is not None else DESK_BLOCKS

    # -- observation (read-only, every source a declared claim) -----------

    def observe(self):
        """Observe the Pi state now — fresh every call, never cached.

        Returns per-source observations with their claims, plus the union
        of installed skill names and whether ANY source was observable
        (a source that ran and found nothing IS an observed absence; a
        source that could not be read is not)."""
        settings = self._observe_settings()
        skills_dir = self._observe_skills_dir()
        pi_bin = self._observe_pi_bin()
        names = {}
        if settings["observed"]:
            for name in settings["skills"]:
                names.setdefault(name, "settings.json:skills")
        if skills_dir["observed"]:
            for name in skills_dir["entries"]:
                names.setdefault(name, "skills-dir")
        if pi_bin["observed"]:
            for name in pi_bin["skills"]:
                names.setdefault(name, "pi list")
        any_source_observed = bool(
            settings["observed"] or skills_dir["observed"]
            or pi_bin["observed"])
        return {
            "settings": settings,
            "skills_dir": skills_dir,
            "pi_bin": pi_bin,
            "installed_skills": {
                "names": sorted(names),
                "sources": names,
                "any_source_observed": any_source_observed,
            },
        }

    def _observe_settings(self):
        claim = ("the Pi settings file records installed extensions under "
                 "a %r key — declared claim, unproven live (H-B2-4)"
                 % (_SETTINGS_SKILLS_KEY,))
        obs = {
            "path": self.settings_path,
            "observed": False,
            "exists": False,
            "parseable": False,
            "skills_key_present": False,
            "skills": [],
            "claim": claim,
        }
        try:
            with open(self.settings_path, encoding="utf-8") as handle:
                raw = handle.read()
        except OSError:
            return obs
        obs["exists"] = True
        try:
            data = json.loads(raw)
        except (ValueError, UnicodeDecodeError):
            return obs
        obs["parseable"] = True
        if not isinstance(data, dict):
            return obs
        value = data.get(_SETTINGS_SKILLS_KEY)
        if value is None:
            # The key's absence is NOT proof that no extension is
            # installed — it only means this source does not record it.
            return obs
        obs["skills_key_present"] = True
        obs["observed"] = True
        if isinstance(value, list):
            for entry in value:
                if isinstance(entry, str) and entry:
                    obs["skills"].append(entry)
                elif isinstance(entry, dict) and isinstance(
                        entry.get("name"), str) and entry["name"]:
                    obs["skills"].append(entry["name"])
        return obs

    def _observe_skills_dir(self):
        claim = ("the Pi skills directory lists one installed skill per "
                 "entry — declared claim; the live box has no such "
                 "directory (commission §3.3)")
        obs = {
            "path": self.skills_dir,
            "observed": False,
            "exists": False,
            "entries": [],
            "claim": claim,
        }
        if not os.path.isdir(self.skills_dir):
            return obs
        obs["exists"] = True
        obs["observed"] = True
        try:
            obs["entries"] = sorted(os.listdir(self.skills_dir))
        except OSError:
            obs["observed"] = False
        return obs

    def _observe_pi_bin(self):
        claim = ("`pi list` prints one installed extension per line — "
                 "declared claim, unproven live; the binary is not "
                 "invoked unless a path is passed in")
        obs = {
            "bin": self.pi_bin,
            "observed": False,
            "skills": [],
            "error": None,
            "claim": claim,
        }
        if not self.pi_bin:
            obs["error"] = "not invoked: no pi binary path supplied"
            return obs
        try:
            completed = subprocess.run(
                [self.pi_bin, "list"],
                capture_output=True, text=True,
                timeout=self.timeout_s, check=False)
        except (OSError, subprocess.SubprocessError) as exc:
            obs["error"] = "%s: %s" % (type(exc).__name__, exc)
            return obs
        if completed.returncode != 0:
            obs["error"] = "pi list exited %d" % completed.returncode
            return obs
        obs["observed"] = True
        for line in completed.stdout.splitlines():
            name = line.strip()
            if name:
                obs["skills"].append(name)
        return obs

    # -- the §7 trust assertion -------------------------------------------

    def assert_trust(self, desk, blocks=None):
        """Constitute desk per §7 or raise TrustError (fail closed).

        The four blocks are checked in order; the skills block is
        cross-checked against the OBSERVED Pi state — a named skill that
        no observable source shows as installed fails ("not_loaded"),
        and a Pi state with no observable source at all fails
        ("inconclusive" — absence is not validity, lens 6).  Returns the
        desk's four blocks as asserted on success."""
        if blocks is None:
            blocks = self.blocks
        if not isinstance(blocks, dict) or desk not in blocks:
            raise TrustError(
                desk, "arrangement", "missing",
                "no arrangement entry names desk %r (§7: no naked "
                "desks)" % (desk,))
        entry = blocks[desk]
        if not isinstance(entry, dict):
            raise TrustError(
                desk, "arrangement", "missing",
                "the arrangement entry for desk %r is not an object"
                % (desk,))
        instruction = entry.get("instruction")
        if not isinstance(instruction, str) or not instruction.strip():
            raise TrustError(
                desk, "instruction", "missing",
                "the instruction block (phase-gate) is not authored for "
                "desk %r" % (desk,))
        skills = entry.get("skills")
        if (not isinstance(skills, list) or not skills
                or not all(isinstance(s, str) and s for s in skills)):
            raise TrustError(
                desk, "skills", "missing",
                "desk %r names no skill — §7 requires at least one"
                % (desk,))
        obs = self.observe()
        if not obs["installed_skills"]["any_source_observed"]:
            raise TrustError(
                desk, "skills", "inconclusive",
                "no Pi extension source is observable (settings without "
                "a skills key, no skills directory, no pi binary) — the "
                "skills of desk %r cannot be verified loaded; never "
                "clean (lens 6)" % (desk,))
        installed = obs["installed_skills"]["names"]
        missing = [s for s in skills if s not in installed]
        if missing:
            raise TrustError(
                desk, "skills", "not_loaded",
                "skill(s) named by desk %r are not observed installed: %s"
                % (desk, ", ".join(missing)))
        tools = entry.get("tools")
        if (not isinstance(tools, list) or not tools
                or not all(isinstance(t, str) and t for t in tools)):
            raise TrustError(
                desk, "tools", "missing",
                "the tool surface is not named for desk %r" % (desk,))
        model = entry.get("model")
        if (not isinstance(model, dict) or not model.get("provider")
                or not model.get("model")):
            raise TrustError(
                desk, "model", "missing",
                "the model block (provider/model) is not named for desk "
                "%r" % (desk,))
        return dict(entry)


def assert_trust(desk, blocks=None, lens=None):
    """The boot assertion (§10.3): constitute a desk per §7 or raise
    TrustError — before the first prompt.

    ``blocks`` defaults to ``DESK_BLOCKS`` and ``lens`` defaults to
    ``Lens()`` with the live ~/.pi paths, so with no arrangement authored
    and no extension installed (the live state, commission §3.3) it fails
    closed — the C4 negative case is the default, not a synthetic one."""
    if blocks is None:
        blocks = DESK_BLOCKS
    if lens is None:
        lens = Lens()
    return lens.assert_trust(desk, blocks)
