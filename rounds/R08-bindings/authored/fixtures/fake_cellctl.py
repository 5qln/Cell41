#!/usr/bin/env python3
"""fake_cellctl — the bindings round's deterministic seam stand-in
(declared fixture apparatus, never the production surface).

A fixture twin of the R07 attested `cellctl` surface: the same 13
subcommands, the same declared serialization (UTF-8 JSON,
ensure_ascii=False, sort_keys=True, compact separators, one line), the
same exit-code convention (0 = the declared success status · 1 = any
other status — absent / malformed / INCONCLUSIVE never reads clean),
and the same fail-closed honesty for absent/empty/malformed inputs.
It writes NOTHING except (a) its invocation journal — one line per
process call, when CELLCTL_JOURNAL is set — and (b) the fixture
fiction of a /conduct run (a declared trail + ledger scratch), which
is labelled fixture fiction and never the engine's bytes.

What it emulates, and why (each emulation is DECLARED here, never
claimed as the engine):
  * the run lock — /conduct takes an fcntl.flock on
    <work_dir>/.cellctl.lock around the whole run, exactly the seam's
    declared C5 mechanism, so the binding-layer tests can prove a
    second process BLOCKS rather than interleaves without loading the
    engine (H-R08-1 — fixtures only);
  * turn_key idempotency — a second /conduct over the same spec
    re-arms from disk alone and reports observed (the seam's
    already-complete shape), so the cold-restart lens is provable;
  * the absent/malformed cases — word/plan/trail/config/decode/check
    refuse absent and malformed inputs honestly, with the sha256 of
    empty = e3b0c44298fc… named for empty files (lens 3);
  * byte-exact passthrough — every string field a caller handed over
    (including the ∞0′ → ‖ needle) is echoed verbatim in the report,
    so the byte-round-trip lens has a deterministic oracle (lens 4).

The reference runner for C3 (plan-equivalence) is built INTO the fake:
`conduct --plan-only --scenario X` composes word + plan with the
declared serialization — the binding's run and the direct run go
through the same bytes, so any difference is the binding's, never the
oracle's.  The fake is stdlib-only and deterministic (no network, no
wall-clock in logic; the lock hold duration is caller-supplied data).

Environment:
  CELLCTL_JOURNAL   a file path — one JSON line per invocation:
                    {"argv": [...], "pid": N}
  FAKE_HOLD_MS      /conduct only: how long the lock is held (data,
                    fixture-only; default 250)
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import sys
import time

sys.dont_write_bytecode = True

EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()

# The five-corner walk the fake declares for an ok word "SGQPV" — the
# same shape a navigate.plan_walk report carries (fixture fiction).
_VISITS = [
    {"index": 0, "letter": "S", "address": "", "orientation": "seed"},
    {"index": 1, "letter": "G", "address": "G", "orientation": "down"},
    {"index": 2, "letter": "Q", "address": "Q", "orientation": "cousin"},
    {"index": 3, "letter": "P", "address": "P", "orientation": "cousin"},
    {"index": 4, "letter": "V", "address": "V", "orientation": "cousin"},
]


def _emit(report):
    sys.stdout.write(json.dumps(report, ensure_ascii=False,
                                sort_keys=True,
                                separators=(",", ":")) + "\n")


def _refuse(reason, status="inconclusive", code=1):
    _emit({"status": status, "reason": reason})
    return code


def _journal():
    """One invocation journal line (fixture apparatus)."""
    path = os.environ.get("CELLCTL_JOURNAL")
    if not path:
        return
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps({"argv": sys.argv[1:],
                                 "pid": os.getpid()},
                                separators=(",", ":")) + "\n")


def _read_binary(path):
    """Binary read — absent / empty / bytes, honestly classified
    (lens 3: the sha256 of empty is e3b0c44298fc…, never valid)."""
    try:
        with open(path, "rb") as handle:
            raw = handle.read()
    except OSError as exc:
        return {"status": "absent", "path": path,
                "reason": "no file at %r (%s) — nothing to read"
                          % (path, exc)}
    if not raw:
        return {"status": "inconclusive", "path": path,
                "sha256": EMPTY_SHA256,
                "reason": ("the file %r is EMPTY — the sha256 of empty "
                           "is %s…, never valid (lens 3)"
                           % (path, EMPTY_SHA256[:16]))}
    return {"status": "bytes", "path": path, "raw": raw}


def _read_json_arg(value, what):
    """An inline JSON string or a JSON file — the seam's declared
    input convention, mirrored (parsing inputs is the wrapper's job)."""
    if value is None:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        pass
    try:
        with open(value, "rb") as handle:
            raw = handle.read()
    except OSError as exc:
        raise SystemExit(_refuse(
            "%s: %r is neither inline JSON nor a readable file (%s)"
            % (what, value, exc)))
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SystemExit(_refuse(
            "%s: the file %r is not valid UTF-8 JSON (%s)"
            % (what, value, exc)))


def _decode_scenario(raw):
    """The fake's scenario decode: the word over {S,G,Q,P,V}, the seed,
    the signed paths — malformed reads malformed with the reason,
    never a substituted value (fixture mirror of word.decode_scenario's
    refusal surface, never the engine's logic)."""
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {"status": "malformed",
                "reason": "the scenario is not valid UTF-8 JSON (%s)"
                          % exc}
    if not isinstance(data, dict):
        return {"status": "malformed",
                "reason": "the scenario is not a JSON object"}
    for field in ("word", "seed", "paths"):
        if field not in data:
            return {"status": "malformed",
                    "reason": "the scenario is missing %r" % field}
    word = data["word"]
    if not isinstance(word, str) or not word or \
            any(ch not in "SGQPV" for ch in word):
        return {"status": "malformed",
                "reason": ("the word %r is not a non-empty string over "
                           "{S,G,Q,P,V}" % word)}
    seed = data["seed"]
    if not isinstance(seed, dict) or not isinstance(
            seed.get("ref"), str) or not seed["ref"]:
        return {"status": "malformed",
                "reason": "the seed's ref must be a non-empty string"}
    paths = data["paths"]
    if not isinstance(paths, list):
        return {"status": "malformed",
                "reason": "'paths' must be a list"}
    for path in paths:
        if not isinstance(path, dict) or "from" not in path \
                or "to" not in path or "path" not in path:
            return {"status": "malformed",
                    "reason": ("each path must carry from/to/path "
                               "(got %r)" % (path,))}
    return {"status": "ok", "scenario": data}


# -- the subcommands ---------------------------------------------------------

def cmd_word(args):
    if args.json is not None:
        report = _decode_scenario(args.json.encode("utf-8"))
        report.setdefault("source", "inline-json")
        # the needle rides verbatim (lens 4): echo what the caller sent
        if report["status"] == "ok":
            report["needle_echo"] = args.json
    else:
        read = _read_binary(args.scenario)
        if read["status"] != "bytes":
            _emit(read)
            return 1
        report = _decode_scenario(read["raw"])
        if report["status"] == "ok":
            report["word"] = report["scenario"]["word"]
            report["seed_ref"] = report["scenario"]["seed"]["ref"]
            report["scenario_sha256"] = hashlib.sha256(
                read["raw"]).hexdigest()
    _emit(report)
    return 0 if report.get("status") == "ok" else 1


def cmd_plan(args):
    read = _read_binary(args.scenario)
    if read["status"] != "bytes":
        _emit(read)
        return 1
    report = _decode_scenario(read["raw"])
    if report["status"] != "ok":
        _emit(report)
        return 1
    scenario = report["scenario"]
    word = scenario["word"]
    visits = []
    for index, letter in enumerate(word):
        visit = dict(_VISITS[index % len(_VISITS)])
        visit["letter"] = letter
        visits.append(visit)
    plan = {"status": "ok",
            "pattern": "sequence",
            "visits": visits,
            "pattern_evidence": [
                "the signs chain one continuous walk (fixture oracle)"
            ]}
    _emit(plan)
    return 0


def cmd_materialize(args):
    read = _read_binary(args.scenario)
    if read["status"] != "bytes":
        _emit(read)
        return 1
    report = _decode_scenario(read["raw"])
    if report["status"] != "ok":
        _emit(report)
        return 1
    if args.verify:
        out = {"status": "ok", "verified": True,
               "reason": "the materialized word reads back unchanged "
                         "(fixture oracle)"}
    else:
        out = {"status": "materialized", "out": args.out,
               "cells": ["_", "G", "Q", "P", "V"],
               "reason": "the child cells are emitted (fixture "
                         "oracle — declared fixture fiction, never "
                         "the engine's bytes)"}
    _emit(out)
    return 0


def _conduct_plan_only(args):
    """C3 — the fake's reference composite: word + plan over the same
    bytes, emitted with the declared serialization.  The binding's
    conduct --plan-only run and the direct run must land the same
    bytes THROUGH THIS oracle — any difference is the binding's."""
    read = _read_binary(args.scenario)
    if read["status"] != "bytes":
        _emit(read)
        return 1
    decode = _decode_scenario(read["raw"])
    if decode["status"] != "ok":
        _emit({"status": decode["status"],
               "reason": decode["reason"]})
        return 1
    word = decode["scenario"]["word"]
    visits = []
    for index, letter in enumerate(word):
        visit = dict(_VISITS[index % len(_VISITS)])
        visit["letter"] = letter
        visits.append(visit)
    _emit({"status": "ok", "pattern": "sequence", "visits": visits,
           "pattern_evidence": [
               "decode + plan composed by the fixture oracle (C3)"]})
    return 0


def _acquire_lock(work_dir):
    if not os.path.isdir(work_dir):
        raise SystemExit(_refuse(
            "the spec's work_dir %r does not exist — the run lock has "
            "nowhere to live; INCONCLUSIVE, never a silently created "
            "dir" % work_dir))
    lock_path = os.path.join(work_dir, ".cellctl.lock")
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o644)
    fcntl.flock(fd, fcntl.LOCK_EX)  # blocks — never interleaves (C5)
    return fd


def _release_lock(fd):
    try:
        fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)


def _load_spec(path):
    read = _read_binary(path)
    if read["status"] != "bytes":
        return read, None
    try:
        spec = json.loads(read["raw"].decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {"status": "malformed",
                "reason": "the spec %r is not valid UTF-8 JSON (%s)"
                          % (path, exc)}, None
    if not isinstance(spec, dict):
        return {"status": "malformed",
                "reason": "the spec is not a JSON object"}, None
    for field in ("work_dir", "scenario", "ledger", "trail"):
        if field not in spec or not isinstance(spec[field], (str, type(None))):
            return {"status": "malformed",
                    "reason": "the spec is missing %r" % field}, None
    return None, spec


def cmd_conduct(args):
    if args.plan_only:
        return _conduct_plan_only(args)
    refused, spec = _load_spec(args.spec)
    if refused is not None:
        _emit(refused)
        return 1
    if spec.get("scenario") is None:
        return _refuse(
            "the cell spec declares no scenario (D2 open — the "
            "acceptance word is Amihai's to choose): /conduct refuses, "
            "INCONCLUSIVE — never a fixture stand-in")
    hold_ms = int(os.environ.get("FAKE_HOLD_MS", "250"))
    fd = _acquire_lock(spec["work_dir"])
    try:
        # the declared C5 mechanism: the whole run holds the lock.
        # a second process BLOCKS here until this one releases.
        if hold_ms > 0:
            time.sleep(hold_ms / 1000.0)  # fixture apparatus only
        # turn_key idempotency (the cold-restart lens): re-arm from disk.
        turn_key = "fake:" + hashlib.sha256(
            json.dumps({"scenario": spec.get("scenario"),
                        "ledger": spec.get("ledger")},
                       sort_keys=True).encode("utf-8")).hexdigest()[:16]
        marker = os.path.join(spec["work_dir"],
                              ".fake-ran-" + turn_key)
        observed = os.path.isfile(marker)
        if not observed:
            with open(marker, "w", encoding="utf-8") as handle:
                handle.write("ran\n")
            status = "complete"
            reason = ("the run completed (fixture oracle — declared "
                      "fixture fiction, never the engine's bytes)")
        else:
            status = "already-complete"
            reason = ("the run re-armed from disk alone and observed "
                      "the same turn_key — never re-run (fixture "
                      "oracle)")
        _emit({"status": status,
               "ended_in": "∞0′",
               "return_question": "plant:sha256:" + "ab" * 32,
               "pattern": "sequence",
               "turn_key": turn_key,
               "reason": reason})
        return 0
    finally:
        _release_lock(fd)


def cmd_walk(args):
    refused, spec = _load_spec(args.spec)
    if refused is not None:
        _emit(refused)
        return 1
    if spec.get("scenario") is None:
        return _refuse("the cell spec declares no scenario (D2 open) — "
                       "the walk cannot boot; INCONCLUSIVE")
    _emit({"status": "complete", "ended_in": None,
           "visits": list(_VISITS),
           "reason": "the raw sign-walk completed (fixture oracle)"})
    return 0


def cmd_config(args):
    if args.path is None:
        _emit({"status": "defaults", "path": None,
               "config": {"desks": {}},
               "reason": ("no soft config path — the declared defaults "
                          "apply (fixture oracle)")})
        return 0
    read = _read_binary(args.path)
    if read["status"] != "bytes":
        _emit({"status": read["status"], "path": args.path,
               "reason": read["reason"]})
        return 1
    try:
        config = json.loads(read["raw"].decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return _refuse("the soft config is not valid JSON (%s)" % exc)
    if not isinstance(config, dict) or "desks" not in config:
        return _refuse("the soft config carries no 'desks' object")
    _emit({"status": "ok", "path": args.path, "config": config,
           "reason": "the soft view (fixture oracle)"})
    return 0


def cmd_cost(args):
    read = _read_binary(args.ledger)
    if read["status"] != "bytes":
        _emit({"status": "inconclusive",
               "reason": ("the ledger %r cannot be read (%s) — the "
                          "spend is INCONCLUSIVE, never guessed"
                          % (args.ledger, read["reason"]))})
        return 1
    count = sum(1 for line in read["raw"].split(b"\n")
                if line.strip())
    spend = {"S": 1, "G": count, "Q": count, "P": count, "V": count}
    _emit({"status": "ok", "mode": args.mode, "spend": spend,
           "total": sum(spend.values()),
           "reason": "the declared spend (fixture oracle)"})
    return 0


def cmd_states(args):
    refused, spec = _load_spec(args.spec)
    if refused is not None:
        _emit(refused)
        return 1
    if spec.get("scenario") is None:
        return _refuse("the cell spec declares no scenario (D2 open) — "
                       "the conductor cannot boot, the state read is "
                       "INCONCLUSIVE, never a stand-in")
    if not spec.get("live_socket"):
        _emit({"status": "absent",
               "reason": "no live socket — the state read is absent, "
                         "honestly (fixture oracle)"})
        return 1
    _emit({"status": "observed",
           "desks": {letter: {"state": "idle",
                              "surface": "no-surface-announced"}
                     for letter in "SGQPV"},
           "reason": "the desks' real states (fixture oracle)"})
    return 0


def cmd_descent(args):
    op = args.op
    try:
        if op == "path-between":
            if not isinstance(args.from_address, str) or \
                    not isinstance(args.to_address, str):
                raise ValueError("path-between needs --from and --to")
            if any(ch not in "SGQPV" for ch in
                   (args.from_address + args.to_address)):
                raise ValueError("an address carries letters outside "
                                 "{S,G,Q,P,V}")
            from_word = args.from_address
            to_word = args.to_address
            # the fake's trivial address grammar: the path is the
            # signed route — "+" per frame climbed, "−x" per descent
            out = ""
            for _ in from_word[1:]:
                out += "+"
            for ch in to_word:
                out += "−" + ch
            result = out
        elif op == "zoom-in":
            if args.address is None or args.letter is None:
                raise ValueError("zoom-in needs --address and --letter")
            if args.letter not in "SGQPV":
                raise ValueError("the letter is outside {S,G,Q,P,V}")
            result = args.address + args.letter
        elif op == "zoom-out":
            if args.address is None:
                raise ValueError("zoom-out needs --address")
            result = args.address[:-1] if args.address else ""
        elif op == "validate-path":
            if args.path is None:
                raise ValueError("validate-path needs --path")
            if args.path == "":
                result = {"k": 0, "letters": []}
            elif any(ch not in "+−·SGQPV" for ch in args.path):
                raise ValueError("a signed-path character is outside "
                                 "the notation")
            else:
                result = {"k": args.path.count("+"), "letters":
                          [ch for ch in args.path if ch in "SGQPV"]}
        elif op == "validate-word":
            if args.address is None:
                raise ValueError("validate-word needs --address")
            result = all(ch in "SGQPV" for ch in args.address)
        else:
            raise ValueError("unknown descent op %r" % op)
    except ValueError as exc:
        return _refuse("the address grammar refused: %s" % exc)
    _emit({"status": "ok", "result": result,
           "reason": "the address grammar's result (fixture oracle)"})
    return 0


def cmd_decode(args):
    if args.phase not in "SGQPV":
        return _refuse("the phase must be one of S,G,Q,P,V")
    values = _read_json_arg(args.values, "the values")
    if args.values is not None and values is None:
        return 1
    if args.values is not None and not isinstance(values, dict):
        return _refuse("the values must be a JSON object")
    report = {"status": "ok", "mark": "mechanical", "phase": args.phase,
              "slots": {},
              "corruption": None,
              "reason": ("the decode report (fixture oracle) — "
                         "references, never text; never an "
                         "authenticity verdict")}
    if values:
        report["needle_echo"] = values  # byte-exact passthrough (lens 4)
    _emit(report)
    return 0


def cmd_compile(args):
    if args.phase not in "SGQPV":
        return _refuse("the phase must be one of S,G,Q,P,V")
    slots = _read_json_arg(args.slots, "the slot texts")
    if slots is None or not isinstance(slots, dict):
        return _refuse("the slots must be a JSON object")
    # emit the slot bytes RAW — the needle rides untouched (lens 4)
    text = "\n".join(str(value) for value in slots.values())
    sys.stdout.write(text)
    if not text.endswith("\n"):
        sys.stdout.write("\n")
    return 0


def cmd_check(args):
    artifact = _read_json_arg(args.artifact, "the artifact")
    if artifact is None:
        return 1
    if not isinstance(artifact, dict) or "surface" not in artifact:
        return _refuse("the artifact is malformed — the check refused, "
                       "INCONCLUSIVE, never clean")
    if artifact.get("surface") == "INCONCLUSIVE-fixture":
        _emit({"verdict": "INCONCLUSIVE",
               "reason": ("HC-1/HC-2 are INCONCLUSIVE by design — a "
                          "machine never reports a fully clean "
                          "artifact (fixture oracle)")})
        return 1
    _emit({"verdict": "PASS",
           "checks": {"R1": "ok"},
           "reason": "the 48-item validation (fixture oracle) — exit "
                     "0 means PASS only"})
    return 0


def cmd_trail(args):
    read = _read_binary(args.trail)
    if read["status"] != "bytes":
        report = {"status": read["status"], "lines": [],
                  "chain": {"status": "undecidable",
                            "first_break": None},
                  "tail": {"torn": False},
                  "sha256": read.get("sha256"),
                  "reason": read["reason"]}
        _emit(report)
        return 1
    raw = read["raw"]
    body = raw.rstrip(b"\r\n")
    lines = []
    damage = None
    for index, piece in enumerate(body.split(b"\n") if body else []):
        try:
            entry = json.loads(piece.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            damage = {"kind": "unparseable", "line": index,
                      "detail": str(exc)}
            break
        if not isinstance(entry, dict):
            damage = {"kind": "not-an-object", "line": index,
                      "detail": ""}
            break
        lines.append(entry)
    if damage is not None:
        _emit({"status": "damaged", "lines": lines, "damage": damage,
               "chain": {"status": "undecidable",
                         "first_break": None},
               "tail": {"torn": False},
               "sha256": hashlib.sha256(raw).hexdigest(),
               "reason": ("a complete line fails to parse — the trail "
                          "reads damaged, never clean (fixture "
                          "oracle)")})
        return 1
    _emit({"status": "ok", "lines": lines,
           "chain": {"status": "undecidable" if len(lines) < 2
                     else "ok", "first_break": None},
           "tail": {"torn": False},
           "sha256": hashlib.sha256(raw).hexdigest(),
           "reason": "the readable trail (fixture oracle)"})
    return 0


def build_parser():
    parser = argparse.ArgumentParser(prog="fake-cellctl")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("word")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--scenario")
    group.add_argument("--json")
    p.set_defaults(func=cmd_word)

    p = sub.add_parser("plan")
    p.add_argument("scenario")
    p.set_defaults(func=cmd_plan)

    p = sub.add_parser("materialize")
    p.add_argument("scenario")
    p.add_argument("--out", required=True)
    p.add_argument("--visits")
    p.add_argument("--verify", action="store_true")
    p.set_defaults(func=cmd_materialize)

    p = sub.add_parser("conduct")
    p.add_argument("--spec")
    p.add_argument("--max-steps", type=int)
    p.add_argument("--plan-only", action="store_true")
    p.add_argument("--scenario")
    p.set_defaults(func=cmd_conduct)

    p = sub.add_parser("walk")
    p.add_argument("--spec", required=True)
    p.add_argument("--max-steps", type=int)
    p.set_defaults(func=cmd_walk)

    p = sub.add_parser("config")
    p.add_argument("--path")
    p.set_defaults(func=cmd_config)

    p = sub.add_parser("cost")
    p.add_argument("--ledger", required=True)
    p.add_argument("--mode", required=True)
    p.add_argument("--soft-config")
    p.set_defaults(func=cmd_cost)

    p = sub.add_parser("states")
    p.add_argument("--spec", required=True)
    p.set_defaults(func=cmd_states)

    p = sub.add_parser("descent")
    p.add_argument("op", choices=["path-between", "zoom-in",
                                  "zoom-out", "validate-path",
                                  "validate-word"])
    p.add_argument("--from", dest="from_address")
    p.add_argument("--to", dest="to_address")
    p.add_argument("--address")
    p.add_argument("--letter")
    p.add_argument("--path")
    p.set_defaults(func=cmd_descent)

    p = sub.add_parser("decode")
    p.add_argument("--phase", required=True, choices=list("SGQPV"))
    p.add_argument("--context")
    p.add_argument("--values")
    p.add_argument("--trail")
    p.add_argument("--lenses")
    p.add_argument("--claims")
    p.add_argument("--cell")
    p.add_argument("--inserted-answer", action="store_true")
    p.set_defaults(func=cmd_decode)

    p = sub.add_parser("compile")
    p.add_argument("--phase", required=True, choices=list("SGQPV"))
    p.add_argument("--slots", required=True)
    p.add_argument("--lenses")
    p.add_argument("--trail")
    p.add_argument("--cell")
    p.add_argument("--surface-only", action="store_true")
    p.set_defaults(func=cmd_compile)

    p = sub.add_parser("check")
    p.add_argument("artifact")
    p.add_argument("--cycle")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("trail")
    p.add_argument("--ledger", required=True)
    p.add_argument("--trail", required=True)
    p.add_argument("--audit", action="store_true")
    p.set_defaults(func=cmd_trail)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    _journal()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
