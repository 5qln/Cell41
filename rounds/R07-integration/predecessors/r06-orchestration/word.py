#!/usr/bin/env python3
"""word — the scenario (R06 · orchestration, C1/C2): a scenario is a
WORD over {S, G, Q, P, V} plus the signed paths between its nodes —
data, never code, never a hardcoded topology enum.  Decode + validate
against the Grammar.

The Fractal is the spec, quoted — never paraphrased into the criteria:

  D.2 (the zoom law has no terminal condition):
    "The law has no base case and no terminal condition. Applying it
    recursively never stops going in, and the inverse never stops going
    out. Therefore the fractal is infinite in both directions:
    No root — any cell has a father-frame, which has a father-frame, …
    No leaf — any cell has five daughters, which have five daughters, …"

  D.3 (the node language):
    "A node is a word over the alphabet {S, G, Q, P, V}. ε is the empty
    word — the origin of a given reading.
    zoom in = append a letter S → SG → SGQ → …
    zoom out = strip a letter SGQ → SG → S → ε → ε's father → …
    The word anchors to one assumed root. That is the gap the sign
    fills."

  D.5 (the address grammar):
    "From node A to node B, the signed path always normalizes to: all +
    first, then all − — because between any two nodes there is exactly
    one path, up to the common father, then down.
    addr(A → B) = +^k · (−x₁)(−x₂)…(−x_m)
    k = steps up to the common father
    m = steps down to the target
    k+m = the generation gap
    The − steps carry a letter (which daughter); the + steps carry none
    (there is only one father)."

  D.6 (the decision rule):
    "Orientation is read from the signs alone:
    k = 0 → B within A (daughter) A is the father-frame
    m = 0 → A within B (father) B is the father-frame
    k, m > 0 → neither (cousins) shared father, different branch
    empty address → same node"

Validation is the imported Grammar's: the alphabet is P4b's
``grammar.COURSE`` (imported — never a five-letter literal here), the
signed-path validator is B3's ``validate_signed_path`` (imported — the
ASCII hyphen is not the U+2212 descent operator, never normalised,
K2), and every declared path must NORMALIZE: it must equal
``path_between(from, to)`` (B3's address grammar, imported).  A
scenario carrying any ``pattern`` / ``topology`` / ``kind`` / ``shape``
field is REFUSED — the signs are the topology (D.6), never a stored
enum.  Absent / empty / malformed scenarios never read valid (the
sha256 of empty is e3b0c44298fc… — lens 3); an unbounded loop reads
INCONCLUSIVE with the reason (D.2 has no terminal condition — the
bound is the seed's boundary, never a navigator constant).

Deterministic and stdlib-only: no network, no LLM, no wall-clock, no
subprocess (K1).  Every string byte — seed refs, node voices, emphasis
overrides — passes through verbatim, never normalised (K2, lens 4).
"""

from __future__ import annotations

import json
import re
import sys

sys.dont_write_bytecode = True

from surface_contract import (  # noqa: E402
    EMPTY_SHA256,
    deep_letter,
    grammar,
    path_between,
    validate_signed_path,
    validate_word,
)

__all__ = [
    "FRACTAL_QUOTES",
    "SCENARIO_KEYS",
    "SEED_KEYS",
    "PATH_KEYS",
    "NODE_KEYS",
    "FORBIDDEN_ENUM_KEYS",
    "BOUND_KINDS",
    "letter_of",
    "decode_scenario",
    "load_scenario_file",
    "declared_visits",
    "ScenarioError",
]

# ---------------------------------------------------------------------------
# The Fractal quotes — carried verbatim (commission §1: quote the Fractal,
# never paraphrase it into the criteria).  The selftest verifies every
# entry byte-for-byte against the held source
# ../sources/5qln-codex-appendix-D-the-fractal.txt.
# ---------------------------------------------------------------------------

FRACTAL_QUOTES = {
    "D.2": (
        "The law has no base case and no terminal condition. Applying it "
        "recursively never stops going in, and the inverse never stops "
        "going out. Therefore the fractal is infinite in both directions: "
        "No root — any cell has a father-frame, which has a father-frame, "
        "… No leaf — any cell has five daughters, which have five "
        "daughters, …"),
    "D.3": (
        "A node is a word over the alphabet {S, G, Q, P, V}. ε is the "
        "empty word — the origin of a given reading. zoom in = append a "
        "letter S → SG → SGQ → … zoom out = strip a letter SGQ → SG → S "
        "→ ε → ε's father → … The word anchors to one assumed root. That "
        "is the gap the sign fills."),
    "D.5": (
        "From node A to node B, the signed path always normalizes to: all "
        "+ first, then all − — because between any two nodes there is "
        "exactly one path, up to the common father, then down. "
        "addr(A → B) = +^k · (−x₁)(−x₂)…(−x_m) k = steps up to the common "
        "father m = steps down to the target k+m = the generation gap The "
        "− steps carry a letter (which daughter); the + steps carry none "
        "(there is only one father)."),
    "D.6": (
        "Orientation is read from the signs alone: k = 0 → B within A "
        "(daughter) A is the father-frame m = 0 → A within B (father) B "
        "is the father-frame k, m > 0 → neither (cousins) shared father, "
        "different branch empty address → same node"),
}

# ---------------------------------------------------------------------------
# The declared schema (H-ORCH-2 — provisional; one place to change, data,
# never logic).
# ---------------------------------------------------------------------------

SCENARIO_KEYS = frozenset(("word", "seed", "paths", "nodes", "loop"))
SEED_KEYS = frozenset(("address", "ref", "bound"))
PATH_KEYS = frozenset(("from", "to", "path"))
NODE_KEYS = frozenset(("tools", "general_tools", "settings", "system"))
SYSTEM_OVERRIDE_KEYS = frozenset(
    ("seat", "equation", "operation", "handoff_in", "handoff_out"))
BOUND_KINDS = frozenset(("word_length", "passes"))
# The no-topology-enum prohibition, made checkable: a scenario never
# DECLARES its walk's pattern — the signs are the topology (D.6).
# ("kind" is not here: the seed's declared bound is a data structure
# with a "kind" field — the loop's stop, never a topology label.)
FORBIDDEN_ENUM_KEYS = frozenset(("pattern", "topology", "shape"))

_WORD_RE = re.compile(r"\A[%s]*\Z" % re.escape("".join(grammar.COURSE)))


class ScenarioError(ValueError):
    """A scenario was refused: malformed or INCONCLUSIVE — never a
    silently substituted value."""


def _check_word_text(value, what):
    if not isinstance(value, str) or _WORD_RE.fullmatch(value) is None:
        raise ScenarioError(
            "%s %r is not a word over {%s}"
            % (what, value, ", ".join(grammar.COURSE)))


def letter_of(address):
    """The seated phase of the node at ``address`` — derived through the
    imported zoom primitives, never stored: the empty word ε seats S
    (the centre — P4b's declared ε-exception, Appendix D.7: the
    signless true start), every other word seats its deepest letter."""
    _check_word_text(address, "address")
    if address == "":
        return "S"
    return deep_letter(address)


def _check_forbidden(obj, where):
    """The no-enum scan: any pattern/topology/kind/shape key anywhere in
    the scenario is REFUSED (D.6: the signs are the topology)."""
    if isinstance(obj, dict):
        for key in obj:
            if key in FORBIDDEN_ENUM_KEYS:
                raise ScenarioError(
                    "the scenario carries the %r key under %s — the "
                    "signs are the topology (D.6), no topology enum is "
                    "ever stored (C1/C2)" % (key, where))
            _check_forbidden(obj[key], where + "." + key)
    elif isinstance(obj, list):
        for index, item in enumerate(obj):
            _check_forbidden(item, "%s[%d]" % (where, index))


def _decode_seed(seed):
    if not isinstance(seed, dict):
        raise ScenarioError("'seed' is missing or not an object — the "
                            "seed's declaration is required (D.7)")
    unknown = sorted(set(seed) - SEED_KEYS)
    if unknown:
        raise ScenarioError("the seed carries unknown field(s): %s"
                            % ", ".join(unknown))
    address = seed.get("address", "")
    _check_word_text(address, "the seed's address")
    ref = seed.get("ref")
    if not isinstance(ref, str) or not ref:
        raise ScenarioError("the seed's ref must be a non-empty string "
                            "(the carried field anchor — a reference, "
                            "never content, D12)")
    bound = seed.get("bound")
    if bound is not None:
        if not isinstance(bound, dict) or sorted(bound) != ["kind", "value"]:
            raise ScenarioError("the seed's bound must be "
                                "{\"kind\", \"value\"} — the loop's "
                                "declared stop, never a navigator "
                                "constant")
        if bound.get("kind") not in BOUND_KINDS:
            raise ScenarioError("the seed's bound kind %r is not one of "
                                "%s" % (bound.get("kind"),
                                        ", ".join(sorted(BOUND_KINDS))))
        value = bound.get("value")
        if (not isinstance(value, int) or isinstance(value, bool)
                or value < 1):
            raise ScenarioError("the seed's bound value must be a "
                                "positive integer")
    return {"address": address, "ref": ref,
            "bound": dict(bound) if bound else None}


def _decode_paths(paths, seed_address):
    if not isinstance(paths, list) or not paths:
        raise ScenarioError("'paths' must be a non-empty list — the "
                            "signed paths between the scenario's nodes "
                            "(D.5)")
    decoded = []
    current = seed_address
    for index, entry in enumerate(paths):
        if not isinstance(entry, dict):
            raise ScenarioError("paths[%d] is not an object" % index)
        unknown = sorted(set(entry) - PATH_KEYS)
        if unknown:
            raise ScenarioError("paths[%d] carries unknown field(s): %s"
                                % (index, ", ".join(unknown)))
        for field in PATH_KEYS:
            if field not in entry:
                raise ScenarioError("paths[%d] is missing %r — a partial "
                                    "scenario never reads valid"
                                    % (index, field))
        _check_word_text(entry["from"], "paths[%d].from" % index)
        _check_word_text(entry["to"], "paths[%d].to" % index)
        if entry["from"] != current:
            raise ScenarioError(
                "paths[%d].from %r does not continue the walk at %r — "
                "the chain must be consistent (each path departs where "
                "the previous arrived; the first departs the seed's "
                "address)" % (index, entry["from"], current))
        report = validate_signed_path(entry["path"])
        if report["status"] != "ok":
            raise ScenarioError("paths[%d].path %r is %s: %s"
                                % (index, entry["path"],
                                   report["status"], report["reason"]))
        expected = path_between(entry["from"], entry["to"])
        if entry["path"] != expected:
            raise ScenarioError(
                "paths[%d].path %r does not normalize — the address "
                "grammar says addr(%s → %s) = %r (D.5/AR3: all + first, "
                "then all −); a path that does not equal the grammar's "
                "path is not an address" % (index, entry["path"],
                                            entry["from"], entry["to"],
                                            expected))
        current = entry["to"]
        decoded.append({
            "from": entry["from"],
            "to": entry["to"],
            "path": entry["path"],
            "k": report["k"],
            "letters": list(report["letters"]),
            "m": len(report["letters"]),
        })
    return decoded


def _decode_nodes(nodes):
    if nodes is None:
        return {}
    if not isinstance(nodes, dict):
        raise ScenarioError("'nodes' must be an object keyed by node "
                            "address, or null")
    out = {}
    for address, entry in nodes.items():
        _check_word_text(address, "node key")
        if not isinstance(entry, dict):
            raise ScenarioError("nodes.%r is not an object" % (address,))
        unknown = sorted(set(entry) - NODE_KEYS)
        if unknown:
            raise ScenarioError("nodes.%r carries unknown field(s): %s"
                                % (address, ", ".join(unknown)))
        tools = entry.get("tools")
        if tools is not None and (not isinstance(tools, list) or not tools
                                  or not all(isinstance(t, str) and t
                                             for t in tools)):
            raise ScenarioError("nodes.%s.tools must be a non-empty list "
                                "of non-empty strings" % address)
        general = entry.get("general_tools")
        if general is not None and (not isinstance(general, list)
                                    or not all(isinstance(t, str) and t
                                               for t in general)):
            raise ScenarioError("nodes.%s.general_tools must be a list "
                                "of non-empty strings" % address)
        settings = entry.get("settings")
        if settings is not None and not isinstance(settings, dict):
            raise ScenarioError("nodes.%s.settings must be an object "
                                "(JSON-safe data)" % address)
        system = entry.get("system")
        if system is not None:
            if not isinstance(system, dict):
                raise ScenarioError("nodes.%s.system must be an object"
                                    % address)
            unknown_sys = sorted(set(system) - SYSTEM_OVERRIDE_KEYS)
            if unknown_sys:
                raise ScenarioError("nodes.%s.system carries unknown "
                                    "field(s): %s"
                                    % (address, ", ".join(unknown_sys)))
            for field, value in system.items():
                if not isinstance(value, str):
                    raise ScenarioError("nodes.%s.system.%s must be a "
                                        "string (byte-exact passthrough)"
                                        % (address, field))
        out[address] = {
            "tools": list(tools) if tools is not None else None,
            "general_tools": list(general) if general is not None else None,
            "settings": dict(settings) if settings is not None else {},
            "system": dict(system) if system is not None else {},
        }
    return out


def decode_scenario(data):
    """Decode + validate a scenario — the word + the signed paths —
    against the Grammar.  Returns:

      {"status": "ok", "scenario": <the decoded scenario>, "reason": …}
      {"status": "absent"|"malformed"|"inconclusive", "reason": …}

    Never a silently substituted value: a scenario that fails any check
    is refused with the reason (lens 3/6).  The decoded scenario is
    data — dicts, strings, ints — never code, never an enum: the
    walk's pattern labels are NOT here (the navigator derives them from
    the signs, D.6)."""
    if data is None:
        return {"status": "absent",
                "reason": "no scenario is present — nothing to decode"}
    if isinstance(data, bytes):
        if not data:
            return {"status": "absent",
                    "sha256": EMPTY_SHA256,
                    "reason": ("the scenario is EMPTY — the sha256 of "
                               "empty is e3b0c44298fc…, never valid "
                               "(lens 3)")}
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            return {"status": "malformed",
                    "reason": "the scenario is not valid UTF-8 (%s)"
                              % exc}
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            return {"status": "malformed",
                    "reason": "the scenario is not valid JSON (%s)" % exc}
    if not isinstance(data, dict):
        return {"status": "malformed",
                "reason": "the scenario is not a JSON object (got %s)"
                          % type(data).__name__}
    try:
        _check_forbidden(data, "scenario")
        unknown = sorted(set(data) - SCENARIO_KEYS)
        if unknown:
            raise ScenarioError("unknown top-level field(s): %s"
                                % ", ".join(unknown))
        word = data.get("word")
        if not isinstance(word, str) or not word:
            raise ScenarioError("'word' is missing or empty — the "
                                "scenario IS a word over {S,G,Q,P,V} "
                                "(D.3)")
        _check_word_text(word, "the scenario word")
        seed = _decode_seed(data.get("seed"))
        paths = _decode_paths(data.get("paths"), seed["address"])
        nodes = _decode_nodes(data.get("nodes"))
        loop = data.get("loop")
        if loop is not None:
            if not isinstance(loop, dict) or sorted(loop) != ["append"]:
                raise ScenarioError("'loop' must be {\"append\": …} or "
                                    "null")
            append = loop.get("append")
            if not isinstance(append, str) or not append:
                raise ScenarioError("the loop's append must be a "
                                    "non-empty word over {S,G,Q,P,V}")
            _check_word_text(append, "the loop's append word")
            if seed["bound"] is None:
                # D.2: the law has no base case and no terminal
                # condition — a loop whose seed declares no bound can
                # never stop, so it refuses to start.  The bound is the
                # seed's boundary, never a navigator constant.
                return {"status": "inconclusive",
                        "reason": ("the scenario declares a loop but "
                                   "the seed declares no bound — D.2: "
                                   "\"The law has no base case and no "
                                   "terminal condition\"; the bound is "
                                   "the seed's boundary, never a "
                                   "navigator constant — an unbounded "
                                   "loop refuses to start")}
            loop = {"append": append}
        # the word vs the declared visits: word[0] seats the seed's
        # address; each declared path's arrival seats its "to".
        if len(word) < len(paths) + 1:
            raise ScenarioError(
                "the word %r is shorter than the walk (seed + %d "
                "path(s)) — the scenario word must spell the walk's "
                "letters in order (D.3)" % (word, len(paths)))
        if word[0] != letter_of(seed["address"]):
            raise ScenarioError("the word opens with %r but the seed "
                                "seats %r at %r — the word spells the "
                                "walk's letters in order (D.3)"
                                % (word[0], letter_of(seed["address"]),
                                   seed["address"]))
        for index, path in enumerate(paths):
            expected_letter = letter_of(path["to"])
            if word[index + 1] != expected_letter:
                raise ScenarioError(
                    "word[%d] is %r but the path %r arrives at %r — "
                    "which seats %r" % (index + 1, word[index + 1],
                                        path["path"], path["to"],
                                        expected_letter))
        if loop is None and len(word) != len(paths) + 1:
            raise ScenarioError(
                "the word has %d letters but the walk has %d nodes and "
                "no loop section — the word must spell the whole walk"
                % (len(word), len(paths) + 1))
        scenario = {
            "word": word,
            "seed": seed,
            "paths": paths,
            "nodes": nodes,
            "loop": loop,
        }
    except ScenarioError as exc:
        return {"status": "malformed", "reason": str(exc)}
    return {"status": "ok", "scenario": scenario,
            "reason": "the scenario is a lawful word + signed paths "
                      "(D.3/D.5) — decoded, never code"}


def load_scenario_file(path):
    """Read a scenario from disk — binary-only, never text-mode byte
    sought (lens 4) — and decode it.  A missing or empty file reads
    absent (the sha256 of empty is e3b0c44298fc…, never valid)."""
    try:
        with open(path, "rb") as handle:
            raw = handle.read()
    except OSError as exc:
        return {"status": "absent", "path": path,
                "reason": "no scenario file at %r (%s) — nothing to "
                          "decode" % (path, exc)}
    report = decode_scenario(raw)
    report["path"] = path
    return report


def declared_visits(scenario):
    """The walk's declared visits (seed + one arrival per declared
    path), derived — addresses from the paths, letters from the
    addresses — never stored (PRD §5.3 carried).  Loop expansion is
    the navigator's (navigate.plan_walk)."""
    visits = [{
        "index": 0,
        "address": scenario["seed"]["address"],
        "letter": letter_of(scenario["seed"]["address"]),
        "path": None,
        "k": None,
        "letters": None,
        "m": None,
        "from": None,
    }]
    for offset, path in enumerate(scenario["paths"], start=1):
        visits.append({
            "index": offset,
            "address": path["to"],
            "letter": letter_of(path["to"]),
            "path": path["path"],
            "k": path["k"],
            "letters": path["letters"],
            "m": path["m"],
            "from": path["from"],
        })
    return visits
