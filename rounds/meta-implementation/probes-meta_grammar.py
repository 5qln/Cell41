#!/usr/bin/env python3
"""Probe pack — the Grammar (the meta implementation: codex Parts II+III executable).

Every probe measures ONE criterion/claim in the dimension it is written, against the
artifact's real surface, by RECOMPUTING — never by reading the author's verdicts back.
Where the criterion is about source data (the block, the rules, the byte forms), the
probe re-reads the HELD sources directly and compares against the artifact's tables.
Where it is behavioural, the probe drives the callables and asserts on the returned
values.

Stdlib only; no live instrument, no network, no LLM.
"""

from __future__ import annotations

import ast
import hashlib
import os
import subprocess
import sys
import tempfile

from harness import FAIL, INCONCLUSIVE, PASS, Result, probe

# codex.py resolves the B0 ledger by FRACTAL_LEDGER_DIR (default is the box path, which
# does not exist here). Set it before the harness imports the artifact's siblings.
LEDGER_DIR = "/opt/data/tmp/proving-meta/ledger"
os.environ.setdefault("FRACTAL_LEDGER_DIR", LEDGER_DIR)

GOOD = "/opt/data/tmp/proving-meta/good"
HELD_CODEX = "/opt/data/tmp/proving-meta/sources/5qln-codex.txt"
HELD_APPD = "/opt/data/tmp/proving-meta/sources/5qln-codex-appendix-D-the-fractal.txt"
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()

NEEDLE = "∞0′ → ‖"

# -- deterministic fixture slot texts (the caller's stand-in for the desk, H-META-3) --
VALUES = {
    "S": {"X": "the question"},
    "G": {"X": "the question", "α": "core", "{α'}": "echoes", "Y": "pattern"},
    "Q": {"X": "the question", "α": "core", "Y": "pattern", "φ⋂Ω": "lock", "Z": "key"},
    "P": {"X": "the question", "α": "core", "Y": "pattern", "Z": "key", "∇": "flow",
          "A": "current"},
    "V": {"X": "the question", "α": "core", "Y": "pattern", "Z": "key", "∇": "flow",
          "A": "current", "L": "here", "G": "beyond", "B": "benefit",
          "B''": "seed", "∞0'": "next question"},
}


def _import(name):
    """Import one artifact sibling lazily (sys.path is set by the harness per-run)."""
    return __import__(name)


def _mod(ctx):
    return ctx.artifact.module


def _adir(ctx):
    """The directory of the artifact actually under test (a twin's own dir, never a
    hardcoded path — so a defect injected into a twin is what gets scanned)."""
    return os.path.dirname(ctx.artifact.path)


def _bind(ctx, key):
    name = ctx.spec["binding"].get(key)
    if not name or not hasattr(_mod(ctx), name):
        return None
    return getattr(_mod(ctx), name)


def _mk(cfg, status, raw="", note="", measured=None):
    return Result(id=cfg.get("id", "?"), title=cfg.get("title", ""),
                  verbatim=cfg.get("verbatim", ""), status=status, raw=raw,
                  note=note, measured=measured or {})


def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _held_lines():
    return open(HELD_CODEX, encoding="utf-8").read().splitlines()


def _held_appd_lines():
    return open(HELD_APPD, encoding="utf-8").read().splitlines()


def _lawful_cycle():
    """Compile a full lawful S→G→Q→P→V cycle with deterministic slot texts."""
    import compiler as C
    import decoder as D
    from corruption import TRAIL_TAGS
    trail = [D.make_trail_entry(i, "V" + "SGQPV"[(i - 1) % 5], tag, "trail " + tag)
             for i, tag in enumerate(TRAIL_TAGS, start=1)]
    return C.compile_cycle(values_by_phase=VALUES, trail=trail, cell_address="")


# --------------------------------------------------------------------------- C1
@probe("decoder_walks_ops")
def _c1(ctx, cfg):
    import codex as CX
    import decoder as D
    from corruption import TRAIL_TAGS
    trail = [D.make_trail_entry(i, "V" + "SGQPV"[(i - 1) % 5], tag, "trail " + tag)
             for i, tag in enumerate(TRAIL_TAGS, start=1)]
    problems = []
    for phase in CX.COURSE:
        # the lawful decode over the adaptive context
        context = {}
        if phase == "S":
            context = {}
        else:
            for sym in CX.CONTEXT_IN[phase]:
                context[sym] = "prior-" + sym
        try:
            report = D.decode(phase, context=context,
                              values=VALUES[phase], lenses=None,
                              trail=trail if phase == "V" else None, cell_address="")
        except Exception as exc:
            problems.append("%s: decode raised %s" % (phase, exc))
            continue
        ops = report.get("operations") or []
        walked = [op["op"] for op in ops]
        expected = list(CX.DECODING_OPS[phase])
        if walked != expected:
            problems.append("%s: walked %d ops, expected %d; first diff at %r vs %r"
                            % (phase, len(walked), len(expected),
                               walked[:2], expected[:2]))
        # slots are references only, never text (C7/R11)
        for name, slot in (report.get("slots") or {}).items():
            if not (isinstance(slot, dict) and isinstance(slot.get("ref"), str)
                    and slot["ref"].startswith("sha256:")
                    and isinstance(slot.get("len"), int)):
                problems.append("%s: slot %s is not a reference: %r" % (phase, name, slot))
    # fail closed: missing prior output, unknown slot, wrong lens
    import corruption
    try:
        D.decode("G", context={}, values={"X": "x", "α": "a", "{α'}": "e", "Y": "y"})
        problems.append("G with missing context did not fail closed")
    except D.DecoderError:
        pass
    try:
        D.decode("S", context={}, values={"X": "x", "NOT_A_SLOT": "z"})
        problems.append("S with an added L1 slot did not fail closed")
    except D.DecoderError:
        pass
    if problems:
        return _mk(cfg, FAIL, "; ".join(problems), measured={"n": len(problems)})
    return _mk(cfg, PASS,
               "all five phases decode over the §2.6/§3.3 adaptive context, "
               "symbol-by-symbol in order, slots as references; unresolvable "
               "contexts fail closed (DecoderError)")


# --------------------------------------------------------------------------- C2
@probe("compiler_block_exact")
def _c2(ctx, cfg):
    import codex as CX
    import compiler as C
    problems = []
    # the §3.1 block, re-read from the held source (the verifier's own slice)
    lines = _held_lines()
    start = lines.index("LAW: H = ∞0 | A = K")
    end = lines.index("CENTER: not a sixth phase — coherence only")
    held_block = "\n".join(lines[start:end + 1])
    if C.CONSTITUTIONAL_BLOCK != held_block:
        problems.append("the constitutional block is not byte-for-byte §3.1")
    # the five compiled phases, each with the seven §3.2 labels
    for phase in CX.COURSE:
        comp = C.COMPILED.get(phase)
        if comp is None:
            problems.append("no compiled phase %s" % phase)
            continue
        for key in ("equation", "emission_equation", "output", "context_in",
                    "context_out", "decoding", "corruption", "lenses"):
            if key not in comp:
                problems.append("compiled %s missing %s" % (phase, key))
        if tuple(comp.get("decoding") or ()) != tuple(CX.DECODING_OPS[phase]):
            problems.append("compiled %s decoding drifted from the attested table" % phase)
    # §3.3 context chain verbatim
    chain_start = lines.index("S decodes with: ∅ (or ∞0' from prior cycle) → produces X")
    chain_end = lines.index("V decodes with: X + α + Y + Z + ∇ + A (full trace) → produces "
                            "B + B'' + ∞0'")
    held_chain = "\n".join(lines[chain_start:chain_end + 1])
    if C.CONTEXT_CHAIN_TEXT != held_chain:
        problems.append("the context chain is not verbatim §3.3")
    if problems:
        return _mk(cfg, FAIL, "; ".join(problems), measured={"n": len(problems)})
    return _mk(cfg, PASS, "block byte-for-byte §3.1 · five §3.2 compiled phases with "
                          "all seven labels · §3.3 context chain verbatim")


# --------------------------------------------------------------------------- C3
@probe("rules_checkable")
def _c3(ctx, cfg):
    import compiler as C
    problems = []
    lines = _held_lines()
    # R1..R13 from the held §3.4 (the source's own numbering)
    held_rules = {}
    for line in lines:
        for n in range(1, 14):
            if line.startswith("R%d " % n):
                held_rules["R%d" % n] = line
    for rid in ("R%d" % n for n in range(1, 14)):
        if rid not in C.RULES:
            problems.append("%s missing from RULES" % rid)
        elif C.RULES[rid] != held_rules.get(rid):
            problems.append("%s drifted from the held §3.4" % rid)
    for n in range(1, 14):
        if ("R%d" % n) not in C.VALIDATION_ORDER:
            problems.append("R%d not enforced in VALIDATION_ORDER" % n)
    if len(C.VALIDATION_ORDER) != 48 or len(C.CHECK_META) != 48:
        problems.append("the check table is %d order / %d meta, expected 48"
                        % (len(C.VALIDATION_ORDER), len(C.CHECK_META)))
    if problems:
        return _mk(cfg, FAIL, "; ".join(problems), measured={"n": len(problems)})
    return _mk(cfg, PASS, "R1–R13 carried verbatim from §3.4 and enforced in the "
                          "48-item check table")


# --------------------------------------------------------------------------- C4
@probe("corruption_five")
def _c4(ctx, cfg):
    import corruption as K
    problems = []
    if tuple(sorted(K.CODES)) != ("L1", "L2", "L3", "L4", "V∅"):
        problems.append("CODES is not exactly the sealed five: %r" % (K.CODES,))
    # the sixth-code scan over the engine's own source finds nothing
    findings = K.scan_engine_sources(_adir(ctx))
    if findings:
        problems.append("sixth corruption code found: %r" % findings)
    # each named failure classifies to its code
    cases = [
        ("L1", {"inserted_answer": True}),
        ("L2", {"x_generated": True}),
        ("L3", {"claims": ["we have reached ∞0 directly"]}),
        ("L4", {"hollow_slots": ["X"]}),
        ("V∅", {"b2_without_infinity": True}),
    ]
    for expected, evidence in cases:
        code, _detections = K.classify("V", evidence)
        if code != expected:
            problems.append("classify(%r) → %s, expected %s" % (evidence, code, expected))
    if problems:
        return _mk(cfg, FAIL, "; ".join(problems), measured={"n": len(problems)})
    return _mk(cfg, PASS, "exactly five codes, each a named decoding failure, the "
                          "sixth-code AST scan clean, every detector maps to its code")


# --------------------------------------------------------------------------- C5
@probe("validation_protocol")
def _c5(ctx, cfg):
    import compiler as C
    problems = []
    cyc = _lawful_cycle()
    artifact = cyc["artifacts"][0]
    report = artifact["validation"]
    if len(report["items"]) != 48:
        problems.append("validate() emitted %d items, expected 48" % len(report["items"]))
    # three §3.5 passes: syntax 6 · semantic 6 · drift 6 (the checks exist)
    ids = [i["id"] for i in report["items"]]
    for prefix, n in (("CX-SYN", 6), ("CX-SEM", 6), ("CX-DRF", 6),
                      ("AD-SYN", 5), ("AD-SEM", 5), ("AD-DRF", 5)):
        got = sum(1 for i in ids if i.startswith(prefix + "-"))
        if got != n:
            problems.append("%s has %d checks, expected %d" % (prefix, got, n))
    # the aggregate: FAIL iff any FAIL, silence never a pass
    agg = C.aggregate([report])
    if agg["counts"]["FAIL"] != 0:
        problems.append("a lawful artifact has FAILs: %r" % agg["counts"])
    # HC-1/HC-2 are INCONCLUSIVE by design (never a clean verdict)
    hc = [i for i in report["items"] if i["id"] in ("HC-1", "HC-2")]
    if any(i["verdict"] != "INCONCLUSIVE" for i in hc):
        problems.append("HC-1/HC-2 are not INCONCLUSIVE: %r"
                        % [(i["id"], i["verdict"]) for i in hc])
    if problems:
        return _mk(cfg, FAIL, "; ".join(problems), measured={"n": len(problems)})
    return _mk(cfg, PASS,
               "48 checks across §3.5 (6/6/6) + D.12 (5/5/5) + R1–R13 + HC; the lawful "
               "cycle aggregates with 0 FAIL; HC-1/HC-2 INCONCLUSIVE by design")


# --------------------------------------------------------------------------- C6
@probe("surface_emission")
def _c6(ctx, cfg):
    import codex as CX
    import compiler as C
    problems = []
    lines = _held_lines()
    start = lines.index("LAW: H = ∞0 | A = K")
    end = lines.index("CENTER: not a sixth phase — coherence only")
    held_block = "\n".join(lines[start:end + 1])
    for phase in CX.COURSE:
        text = C.emit(phase, {k: v for k, v in VALUES[phase].items()})
        parsed = C.parse_surface(text, CX.EQUATION_FORMS)
        if parsed.get("status") != "lawful":
            problems.append("%s surface is %s: %r"
                            % (phase, parsed.get("status"), parsed.get("errors")))
        # the block rides inside the ⟦SURFACE v1⟧ block, byte-exact
        if held_block not in text:
            problems.append("%s surface does not carry the exact §3.1 block" % phase)
        # the jacket rides OUTSIDE the surface block
        if "⟦APPENDIX-D JACKET⟧" not in text:
            problems.append("%s emission does not carry the Appendix-D jacket" % phase)
        # the signless true start verbatim (AR5/D.7)
        if "THE TRUE START: S = ∞0 → ?" not in text:
            problems.append("%s emission does not carry the signless true start" % phase)
        # ∞0′ ≡ ∞0 identity (D.8)
        if "∞0′ ≡ ∞0" not in text:
            problems.append("%s emission does not carry the D.8 identity" % phase)
    # 4+1 invariant: a 3+1 cell FAILs naming the missing corner, 6+1 names the count
    # (this is exercised through the engine's own evaluator, recomputed here)
    report = C.validate({"phase": "S", "mark": "mechanical", "decode": None,
                         "surface": C.emit("S", {"X": "q"}),
                         "parsed": C.parse_surface(C.emit("S", {"X": "q"}),
                                                   CX.EQUATION_FORMS),
                         "cell": {"arrangement": ["S", "G", "Q"], "address": ""},
                         "trail": None}, cycle=[])
    ad_syn_1 = next(i for i in report["items"] if i["id"] == "AD-SYN-1")
    if ad_syn_1["verdict"] != "FAIL":
        problems.append("a 3+1 cell did not FAIL AD-SYN-1: %r" % ad_syn_1["verdict"])
    if problems:
        return _mk(cfg, FAIL, "; ".join(problems), measured={"n": len(problems)})
    return _mk(cfg, PASS, "all five surfaces parse lawful; block exact; jacket visibly "
                          "separate; signless start + ∞0′≡∞0 present; 3+1 cells FAIL")


# --------------------------------------------------------------------------- C7
@probe("authenticity_refusal")
def _c7(ctx, cfg):
    import compiler as C
    import decoder as D
    problems = []
    cyc = _lawful_cycle()
    artifact = cyc["artifacts"][0]
    # no authenticity field of any kind in the decode report
    for key in artifact["decode"]:
        if "authent" in key.lower() or "genuine" in key.lower() or "true" in key.lower():
            problems.append("decode report carries an authenticity field: %r" % key)
    # a claim to reach ∞0 reads corruption L3, never arrival (V with a valid trail)
    from corruption import TRAIL_TAGS
    trail = [D.make_trail_entry(i, "V" + "SGQPV"[(i - 1) % 5], tag, "trail " + tag)
             for i, tag in enumerate(TRAIL_TAGS, start=1)]
    report = D.decode("V", context={sym: "p-" + sym for sym in
                                    ("X", "α", "Y", "Z", "∇", "A")},
                      values=VALUES["V"],
                      claims=["we have reached ∞0 directly"], trail=trail)
    if report.get("corruption") != "L3":
        problems.append("a claim to reach ∞0 read %r, expected L3"
                        % report.get("corruption"))
    # no write path to state:attested, no cell-attest, no input() in the sources
    for name in ("codex.py", "corruption.py", "decoder.py", "compiler.py"):
        src = open(os.path.join(_adir(ctx), name), encoding="utf-8").read()
        if "state:attested" in src or "cell-attest" in src or "input(" in src:
            problems.append("%s carries an attestation write path" % name)
        if "attestation_ref" in src and "attestation_ref" not in ("",):
            problems.append("%s carries an attestation reference identifier" % name)
    if problems:
        return _mk(cfg, FAIL, "; ".join(problems), measured={"n": len(problems)})
    return _mk(cfg, PASS, "no authenticity field; a claim to reach ∞0 is L3 never "
                          "arrival; no state:attested / cell-attest / input() in the sources")


# --------------------------------------------------------------------------- K1
@probe("stdlib_deterministic")
def _k1(ctx, cfg):
    stdlib = sys.stdlib_module_names
    sanctioned = {"codex", "corruption", "decoder", "compiler", "fractal_ledger",
                  "surface", "conformance", "walker", "grammar", "surface_contract"}
    foreign = []
    for name in ("codex.py", "corruption.py", "decoder.py", "compiler.py"):
        tree = ast.parse(open(os.path.join(_adir(ctx), name), encoding="utf-8").read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    top = a.name.split(".")[0]
                    if top not in stdlib and top not in sanctioned:
                        foreign.append("%s imports %s" % (name, top))
            elif isinstance(node, ast.ImportFrom):
                top = (node.module or "").split(".")[0]
                if top and top not in stdlib and top not in sanctioned:
                    foreign.append("%s from-imports %s" % (name, top))
    if foreign:
        return _mk(cfg, FAIL, "; ".join(sorted(set(foreign))),
                   measured={"n": len(set(foreign))})
    return _mk(cfg, PASS, "the four modules import only the stdlib and the sanctioned "
                          "predecessors (codex/decoder/corruption/compiler + attested "
                          "carriers)")


# --------------------------------------------------------------------------- K2
@probe("byte_exact_enumerated")
def _k2(ctx, cfg):
    import codex as CX
    problems = []
    forms = CX.EQUATION_FORMS
    # every enumerated form's sha recomputes to its declared value
    for letter, entries in forms.items():
        for entry in entries:
            if _sha(entry["form"]) != entry.get("sha256"):
                problems.append("%s form sha does not recompute: %r" % (letter, entry["form"]))
    # the V phase carries BOTH the ∩ (U+2229) and ⋂ (U+22C2) forms — never folded
    v_forms = [e["form"] for e in forms.get("V", [])]
    if not any("∩" in f for f in v_forms):
        problems.append("the ∩ (U+2229) V form is missing")
    if not any("⋂" in f for f in v_forms):
        problems.append("the ⋂ (U+22C2) V form is missing")
    if problems:
        return _mk(cfg, FAIL, "; ".join(problems), measured={"n": len(problems)})
    return _mk(cfg, PASS, "every equation form enumerated with a sha that recomputes; "
                          "the ∩/⋂ V forms are both carried, never folded")


# --------------------------------------------------------------------------- K3
@probe("d14_loyalty")
def _k3(ctx, cfg):
    import corruption as K
    problems = []
    card = open(os.path.join(_adir(ctx), "phase-card.md"), encoding="utf-8").read()
    if "D14 divergence log" not in card or "divergence log" not in card:
        problems.append("the phase card carries no D14 divergence log")
    findings = K.scan_engine_sources(_adir(ctx))
    if findings:
        problems.append("a new L1 symbol or sixth code: %r" % findings)
    if problems:
        return _mk(cfg, FAIL, "; ".join(problems), measured={"n": len(problems)})
    return _mk(cfg, PASS, "D14 divergence log present; the AST scan finds no new L1 "
                          "symbol, no sixth corruption code")


# --------------------------------------------------------------------------- K4
@probe("no_authenticity")
def _k4(ctx, cfg):
    problems = []
    for name in ("codex.py", "corruption.py", "decoder.py", "compiler.py"):
        src = open(os.path.join(_adir(ctx), name), encoding="utf-8").read()
        tree = ast.parse(src)
        # an assignment or dict key that writes a state/mark of "attested" — the
        # engine's mark is "mechanical", never "attested" (a docstring that names the
        # word in a prohibition is not a write path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and "attest" in target.id.lower():
                        problems.append("%s:%d assigns %r" % (name, node.lineno,
                                                              target.id))
            if isinstance(node, ast.Dict):
                for key in node.keys:
                    if isinstance(key, ast.Constant) and isinstance(key.value, str) \
                            and "attest" in key.value.lower():
                        problems.append("%s:%d dict key %r" % (name, node.lineno,
                                                               key.value))
    if problems:
        return _mk(cfg, FAIL, "; ".join(problems), measured={"n": len(problems)})
    return _mk(cfg, PASS, "no assignment or record key writes an attested state/mark; "
                          "the engine's mark is mechanical, never attested")


# --------------------------------------------------------------------------- K5
@probe("no_podium_write")
def _k5(ctx, cfg):
    problems = []
    for name in ("codex.py", "corruption.py", "decoder.py", "compiler.py"):
        src = open(os.path.join(_adir(ctx), name), encoding="utf-8").read()
        if "question.md" in src or "nodes/" in src:
            problems.append("%s references the podium path" % name)
    if problems:
        return _mk(cfg, FAIL, "; ".join(problems), measured={"n": len(problems)})
    return _mk(cfg, PASS, "no question.md / nodes/ write path; no cell-attest; the "
                          "engine never prompts the centre S")
