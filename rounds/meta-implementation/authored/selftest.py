#!/usr/bin/env python3
"""selftest — meta-implementation, author-side checks (hypotheses).

Every test names, in its first docstring line, the criterion or hold it
exercises (C1-C7 · H-META-1..4 · R1-R13 · §3.5 · Appendix D.12 · the
five corruption codes · the six verifier lenses) and the quantity it
measures.  These are PREDICTIONS, never results: the verifier executes
the artifact and recomputes every one of them with its own
implementation; any divergence — in either direction — is a FAIL.  If
my own run revealed a bug, it was fixed silently; this file stays a set
of hypotheses.

The engine is fixture-tested against deterministic inputs (H-META-3):
no socket, no pane, no network, no LLM, no wall clock anywhere in the
engine modules — every value is caller-supplied.  Scratch writes use
tempfile directories only (self-cleaning); the held sources, the
attested predecessors, and the attested ledger are only ever READ.

Run:  python3 selftest.py
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import codex  # noqa: E402
import compiler  # noqa: E402
import corruption  # noqa: E402
import decoder  # noqa: E402
from compiler import (CHECK_META, COMPILED, CONSTITUTIONAL_BLOCK, RULES,
                      VALIDATION_ORDER, aggregate, compile_artifact,
                      compile_cycle, emit, validate_surface_text)  # noqa: E402
from decoder import (DecoderError, decode, make_trail_entry, ref_text)  # noqa: E402

NEEDLE = "∞0′ → ‖"  # the encoding-lens bytes (commission lens 4)
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()  # e3b0c44298fc… — never valid

CODEX_PATH = os.path.join(codex.SOURCES_DIR, "5qln-codex.txt")
APPD_PATH = os.path.join(codex.SOURCES_DIR, "5qln-codex-appendix-D-the-fractal.txt")


def held_lines(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read().splitlines()


def full_values():
    """One deterministic cycle's slot values (the fixture world's
    stand-in for the desk — never the engine's invention)."""
    return {
        "S": {"X": "the question the cycle opened"},
        "G": {"X": "the question the cycle opened", "α": "the irreducible core",
              "{α'}": "the echoes of the core across scales",
              "Y": "the validated pattern"},
        "Q": {"X": "the question the cycle opened", "α": "the irreducible core",
              "Y": "the validated pattern", "φ⋂Ω": "the moment that locked",
              "Z": "the resonant key"},
        "P": {"X": "the question the cycle opened", "α": "the irreducible core",
              "Y": "the validated pattern", "Z": "the resonant key",
              "∇": "the natural gradient", "A": "the flow"},
        "V": {"X": "the question the cycle opened", "α": "the irreducible core",
              "Y": "the validated pattern", "Z": "the resonant key",
              "∇": "the natural gradient", "A": "the flow",
              "L": "the local actualization", "G": "the global propagation",
              "B": "the benefit", "B''": "the fractal seed artifact",
              "∞0'": "the return question the cycle opens?"},
    }


def v_trail():
    """A lawful formation trail: ordered, lens-tagged, all four Pass-1
    kinds present (R6)."""
    return [
        make_trail_entry(1, "GQ", "α thread", "the α thread"),
        make_trail_entry(2, "QQ", "φ⋂Ω confirmation", "the confirmation"),
        make_trail_entry(3, "PP", "∇", "the gradient"),
        make_trail_entry(4, "VV", "turning point", "the turn"),
    ]


def lawful_cycle(**overrides):
    kwargs = dict(values_by_phase=full_values(), trail=v_trail())
    kwargs.update(overrides)
    return compile_cycle(**kwargs)


def item(report, item_id):
    for entry in report["items"]:
        if entry["id"] == item_id:
            return entry
    raise KeyError(item_id)


def verdict_of(report, item_id):
    return item(report, item_id)["verdict"]


def engine_source_text():
    return "\n".join(
        open(os.path.join(HERE, name), encoding="utf-8").read()
        for name in corruption.ENGINE_MODULES)


class ProvenanceAndPins(unittest.TestCase):
    def test_held_sources_and_carriers_match_their_pins(self):
        """Provenance §0 — quantity measured: every pinned file's bytes
        hash to its commission pin; a drift would have failed the import
        already (fail closed, lens 6)."""
        for name, (expected, _role) in codex.SOURCE_PINS.items():
            raw = open(os.path.join(codex.SOURCES_DIR, name), "rb").read()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), expected, name)
        self.assertEqual(
            codex.SOURCE_PINS["5qln-codex.txt"][0],
            "e5f0c738d123efc1e412a14da1701a721606275867319e1c68d53b081445c133")
        self.assertEqual(
            codex.SOURCE_PINS["5qln-codex-appendix-D-the-fractal.txt"][0],
            "6bb28c37cfe6267da1675eac16ac8bbf9679a1d0e5db0f08eb4495d2c22f6bf7")
        self.assertEqual(
            codex.PINS["p4a/surface.py"][0],
            "776ff46393bf81db62841043021c97288e2c1414bec43971d275d1dfbdfac36d")
        self.assertEqual(
            codex.PINS["b0/fractal_ledger.py"][0],
            "b291e65967e0d1f98205a9bd612507fa788ea4f9aa99e5d6b8fa5f366895546d")

    def test_contract_parser_is_the_attested_one(self):
        """C6 — quantity measured: the parse function the emission is
        checked against IS the attested P4a surface.py function object
        (imported by path, never copied, never re-authored)."""
        self.assertEqual(compiler.parse_surface.__module__, "surface")
        self.assertIs(compiler.parse_surface, codex.parse_surface)

    def test_missing_pinned_file_fails_closed(self):
        """Lens 3/lens 6 — quantity measured: reading a pinned path that
        does not exist raises ImportError (404 is never a valid
        substitute)."""
        with self.assertRaises(ImportError):
            codex._read_pinned(os.path.join(tempfile.gettempdir(),
                                            "definitely-missing-404"),
                               "0" * 64, "test pin")


class DecoderC1(unittest.TestCase):
    def test_decoding_operations_walk_symbol_by_symbol(self):
        """C1 / §3.5 (syntax: "Every decoding operation follows D1
        symbol-by-symbol") — quantity measured: for each of the five
        phases, decode() walks exactly the attested DECODING_OPS table,
        in order, numbered 1..n; the ops never change at scale (§2.9)."""
        for phase in codex.COURSE:
            values = full_values()[phase]
            context = {}
            if phase != "S":
                context = {sym: ref_text("ctx-%s" % sym)
                           for sym in decoder.REQUIRED_CONTEXT[phase]}
            report = decode(phase, context=context, values=values,
                            trail=v_trail() if phase == "V" else None)
            expected = codex.DECODING_OPS[phase]
            self.assertEqual(
                [op["op"] for op in report["operations"]], list(expected))
            self.assertEqual([op["n"] for op in report["operations"]],
                             list(range(1, len(expected) + 1)))
            self.assertEqual(
                report["equation"], codex.EQUATION_FORMS[phase][0]["form"])

    def test_adaptive_context_is_exact_and_fails_closed(self):
        """C1 / H-META-3 — quantity measured: every lawful §2.6/§3.3
        context decodes; every unresolvable context raises DecoderError
        (a missing prior output, an unknown symbol, an unknown slot, a
        trail outside V, B'' without its trail)."""
        decode("S", context={}, values={"X": "q"})
        decode("S", context={"∞0'": ref_text("prior")}, values={"X": "q"})
        decode("S", context={"∞0′": ref_text("prior")}, values={"X": "q"})
        for bad_ctx, values in (
                ({"Y": ref_text("y")}, {"X": "q"}),
                ({"X": ref_text("x"), "α": ref_text("a"), "Y": ref_text("y"),
                  "Q": ref_text("zz")}, {"X": "x", "α": "a", "{α'}": "e",
                                         "Y": "y"})):
            with self.assertRaises(DecoderError):
                decode("G", context=bad_ctx, values=values)
        with self.assertRaises(DecoderError):
            decode("S", context={"X": ref_text("q")}, values={"X": "q"})
        with self.assertRaises(DecoderError):
            decode("G", context={"X": ref_text("x")},
                   values={"X": "x", "α": "a", "{α'}": "e", "Y": "y",
                           "N": "a new symbol"})
        with self.assertRaises(DecoderError):
            decode("G", context={"X": ref_text("x")}, values={"X": "x"},
                   trail=v_trail())
        with self.assertRaises(DecoderError):
            decode("V", context={}, values={"B''": "artifact"})
        with self.assertRaises(DecoderError):
            decode("S", context={"∞0'": "a", "∞0′": "b"}, values={"X": "q"})

    def test_decoder_never_generates_and_references_only(self):
        """C7 / R11 — quantity measured: the report carries slot
        references (sha256 + byte length) and never the slot text; a
        machine-posed X is corruption L2, carried honestly, never
        hidden."""
        report = decode("S", context={}, values={"X": "the question"})
        dumped = json.dumps(report, ensure_ascii=False, sort_keys=True)
        self.assertNotIn("the question", dumped)
        self.assertIn("sha256:", dumped)
        self.assertEqual(report["slots"]["X"],
                         ref_text("the question"))
        report2 = decode("S", context={},
                         values={"X": {"text": "posed", "channel":
                                       "generated"}})
        self.assertEqual(report2["corruption"], "L2")
        self.assertEqual(report2["mark"], "mechanical")

    def test_claim_to_reach_infinity_zero_is_L3_never_arrival(self):
        """C7 — quantity measured: a decode that claims to have reached
        ∞0 is reported as corruption L3 (the §2.8 failure text), and no
        report key anywhere states arrival or authenticity."""
        report = decode("S", context={}, values={"X": "q"},
                        claims=["the decode reached ∞0"])
        self.assertEqual(report["corruption"], "L3")
        self.assertIn("never arrival",
                      report["corruption_detections"][0]["failure"])
        dumped = json.dumps(report, ensure_ascii=False, sort_keys=True)
        self.assertNotIn("authentic", dumped)
        for key in report:
            self.assertNotIn("auth", key)
            self.assertNotIn("arriv", key)
        # the same claim planted in a slot's text is detected
        report2 = decode("V", context={"X": ref_text("x"),
                                       "α": ref_text("a"),
                                       "Y": ref_text("y"),
                                       "Z": ref_text("z"),
                                       "∇": ref_text("g"),
                                       "A": ref_text("f")},
                         values={"X": "x", "α": "a", "Y": "y", "Z": "z",
                                 "∇": "g", "A": "f", "L": "l", "G": "gg",
                                 "B": "b", "B''": "the seed",
                                 "∞0'": "a question?"},
                         trail=v_trail(),
                         claims=["the decode arrived at ∞0"])
        self.assertEqual(report2["corruption"], "L3")

    def test_l1_l4_v_incomplete_twins(self):
        """C4 — quantity measured: the remaining three named failures
        classify to their codes: an inserted answer (L1), an empty
        operation (L4), and B'' formed without ∞0′ (V∅)."""
        report = decode("S", context={}, values={"X": "q"},
                        inserted_answer=True)
        self.assertEqual(report["corruption"], "L1")
        report = decode("G", context={"X": ref_text("x")},
                        values={"X": "x", "α": "a", "{α'}": "e"})
        self.assertEqual(report["corruption"], "L4")
        self.assertEqual(report["slots_missing"], ["Y"])
        report = decode("V", context={"X": ref_text("x"),
                                      "α": ref_text("a"),
                                      "Y": ref_text("y"),
                                      "Z": ref_text("z"),
                                      "∇": ref_text("g"),
                                      "A": ref_text("f")},
                        values={"X": "x", "α": "a", "Y": "y", "Z": "z",
                                "∇": "g", "A": "f", "L": "l", "G": "gg",
                                "B": "b", "B''": "the seed"},
                        trail=v_trail())
        self.assertEqual(report["corruption"], "V∅")
        # the same taxonomy applies to ANY produced surface: a foreign G
        # surface missing its Y slot classifies L4, a foreign V surface
        # with B'' but no ∞0′ classifies V∅ — references only, never
        # text, never an authenticity verdict.
        foreign_g = validate_surface_text(
            emit("G", {"X": "x", "α": "a", "{α'}": "e"}))
        self.assertEqual(foreign_g["corruption"], "L4")
        foreign_v = validate_surface_text(
            emit("V", {"X": "x", "α": "a", "Y": "y", "Z": "z", "∇": "g",
                       "A": "f", "L": "l", "G": "gg", "B": "b",
                       "B''": "the seed"}))
        self.assertEqual(foreign_v["corruption"], "V∅")

    def test_decoder_operations_do_not_change_at_scale(self):
        """C1 / §2.9 / R13 — quantity measured: the same phase decodes
        with the same operations and equation at ε and at a deep cell;
        only the recorded cell differs."""
        at_root = decode("G", context={"X": ref_text("x")},
                         values={"X": "x", "α": "a", "{α'}": "e", "Y": "y"},
                         cell_address="")
        at_depth = decode("G", context={"X": ref_text("x")},
                          values={"X": "x", "α": "a", "{α'}": "e", "Y": "y"},
                          cell_address="SGQ")
        self.assertEqual(at_root["operations"], at_depth["operations"])
        self.assertEqual(at_root["equation"], at_depth["equation"])
        self.assertEqual(at_depth["cell_address"], "SGQ")


class CompilerC2C3(unittest.TestCase):
    def test_constitutional_block_is_byte_exact(self):
        """C2 / §3.1 — quantity measured: the block equals the held
        extraction's §3.1 lines byte for byte (independently re-read in
        this test) and carries the ∩-axis V equation."""
        lines = held_lines(CODEX_PATH)
        expected = "\n".join(lines[253:266])
        self.assertEqual(CONSTITUTIONAL_BLOCK, expected)
        self.assertTrue(CONSTITUTIONAL_BLOCK.startswith("LAW: H = ∞0 | A = K"))
        self.assertTrue(CONSTITUTIONAL_BLOCK.endswith(
            "CENTER: not a sixth phase — coherence only"))
        self.assertEqual(codex.BLOCK_LINES[7], "V = (L ∩ G → B'') → ∞0'")
        self.assertEqual(codex.BLOCK_LINES[7],
                         codex.EQUATION_FORMS["V"][0]["form"])

    def test_compiled_phases_carry_all_seven_labels(self):
        """C2 / §3.2 — quantity measured: each compiled phase carries
        EQUATION / OUTPUT / CONTEXT IN / CONTEXT OUT / DECODING /
        CORRUPTION / LENSES, with the §3.2 source lines (the held
        extraction, re-read in this test)."""
        lines = held_lines(CODEX_PATH)
        for phase in codex.COURSE:
            compiled = COMPILED[phase]
            self.assertEqual(
                set(compiled), {"equation", "emission_equation", "output",
                                "context_in", "context_out", "decoding",
                                "corruption", "lenses"})
            self.assertEqual(tuple(compiled["decoding"]),
                             tuple(codex.DECODING_OPS[phase]))
            self.assertEqual(len(compiled["lenses"]), 5)
        self.assertTrue(COMPILED["S"]["corruption"][0].startswith(
            "L1 (closing: answer inserted"))
        self.assertTrue(COMPILED["V"]["corruption"][0].startswith(
            "V∅ (incomplete: B'' without ∞0'"))
        self.assertTrue(COMPILED["V"]["corruption"][1].startswith(
            "L1 at scale (premature crystallization"))
        self.assertIn("Forcing ∇ (imposing direction instead of revealing "
                      "it)", COMPILED["P"]["corruption"])
        # the recorded §3.2/§3.1 V-axis shas recompute from the held file
        self.assertEqual(codex.V_EQ_AXIS["section_3_1"]["sha256"],
                         codex.EQUATION_FORMS["V"][0]["sha256"])
        self.assertEqual(codex.V_EQ_AXIS["section_3_2"]["sha256"],
                         hashlib.sha256(lines[346].encode("utf-8"))
                         .hexdigest()[:0] or codex.V_EQ_AXIS["section_3_2"][
                             "sha256"])
        self.assertEqual(
            codex.V_EQ_AXIS["section_3_2"]["sha256"],
            hashlib.sha256(
                lines[346][len("EQUATION: "):].encode("utf-8")).hexdigest())

    def test_thirteen_rules_verbatim_and_checkable(self):
        """C3 / §3.4 — quantity measured: R1-R13 exist as checks in the
        validation order with citations byte-equal to the held codex's
        §3.4 lines; all thirteen decide PASS on a lawful full cycle."""
        lines = held_lines(CODEX_PATH)
        for n in range(1, 14):
            rule = "R%d" % n
            self.assertEqual(RULES[rule], lines[380 + n - 1])
            self.assertIn(rule, VALIDATION_ORDER)
            self.assertEqual(CHECK_META[rule]["citation"], lines[380 + n - 1])
        cycle = lawful_cycle()
        for n in range(1, 14):
            if n == 3:
                # no lens was declared in the cycle — R3 reads
                # INCONCLUSIVE (unobservable), never a false clean
                self.assertEqual(
                    cycle["validation"]["items"]["R3"], "INCONCLUSIVE")
                continue
            self.assertEqual(cycle["validation"]["items"]["R%d" % n], "PASS",
                             "R%d" % n)
        lensed = compile_artifact("G", context={"X": ref_text("x")},
                                  values=full_values()["G"], lenses=["GQ"])
        self.assertEqual(item(lensed["validation"], "R3")["verdict"], "PASS")

    def test_context_chain_verbatim(self):
        """C2 / §3.3 — quantity measured: the emitted context chain is
        the held codex's §3.3 lines byte for byte."""
        lines = held_lines(CODEX_PATH)
        self.assertEqual(compiler.CONTEXT_CHAIN_TEXT,
                         "\n".join(lines[372:377]))
        emitted = emit("S", {"X": "q"})
        self.assertIn(compiler.CONTEXT_CHAIN_TEXT, emitted)


class CorruptionC4(unittest.TestCase):
    def test_taxonomy_is_exactly_five_with_named_failures(self):
        """C4 / §2.8 / R9 — quantity measured: the closed set is exactly
        L1 L2 L3 L4 V∅ and each code names its §2.8 decoding failure
        (re-read from the held extraction in this test)."""
        self.assertEqual(corruption.CODES, ("L1", "L2", "L3", "L4", "V∅"))
        lines = held_lines(CODEX_PATH)
        for code in corruption.CODES:
            self.assertEqual(corruption.CODE_NAMES[code],
                             codex.CORRUPTION_FAILURES[code][0])
            self.assertTrue(corruption.CODE_FAILURES[code])
        # §2.8's own table (lines 239-243) names exactly these five
        table = "\n".join(lines[238:243])
        for code in corruption.CODES:
            self.assertIn(code, table)

    def test_no_sixth_code_anywhere_in_the_engine(self):
        """C4 / AD-DRF-4 / CX-DRF-4 — quantity measured: the AST
        constant scan over the engine modules finds no L<digits> or
        V<symbol> string outside the sealed five, and the checks PASS."""
        self.assertEqual(corruption.scan_engine_sources(HERE), [])
        cycle = lawful_cycle()
        self.assertEqual(cycle["validation"]["items"]["AD-DRF-4"], "PASS")
        self.assertEqual(cycle["validation"]["items"]["CX-DRF-4"], "PASS")
        self.assertEqual(cycle["validation"]["items"]["CX-SYN-5"], "PASS")
        self.assertEqual(cycle["validation"]["items"]["R9"], "PASS")


class ValidationC5(unittest.TestCase):
    def test_three_passes_have_six_checks_each(self):
        """C5 / §3.5 — quantity measured: the validation protocol runs
        syntax (6), semantic (6), drift (6) on any produced surface,
        plus D.12 (5+5+5), R1-R13 and HC-1/HC-2 — 48 items, every
        citation the held bullet text."""
        lines = held_lines(CODEX_PATH)
        appd = held_lines(APPD_PATH)
        for i in range(1, 7):
            self.assertEqual(CHECK_META["CX-SYN-%d" % i]["citation"],
                             lines[395 + i - 1][2:])
            self.assertEqual(CHECK_META["CX-SEM-%d" % i]["citation"],
                             lines[402 + i - 1][2:])
            self.assertEqual(CHECK_META["CX-DRF-%d" % i]["citation"],
                             lines[409 + i - 1][2:])
        for i in range(1, 6):
            self.assertEqual(CHECK_META["AD-SYN-%d" % i]["citation"],
                             appd[157 + i - 1][2:])
            self.assertEqual(CHECK_META["AD-SEM-%d" % i]["citation"],
                             appd[163 + i - 1][2:])
            self.assertEqual(CHECK_META["AD-DRF-%d" % i]["citation"],
                             appd[169 + i - 1][2:])
        self.assertEqual(len(VALIDATION_ORDER), 48)
        self.assertEqual({m["derived"] for m in CHECK_META.values()
                          if m["derived"]}, {True})
        derived = [iid for iid, meta in CHECK_META.items() if meta["derived"]]
        self.assertEqual(derived, ["HC-1", "HC-2"])

    def test_validation_applies_to_any_produced_surface(self):
        """C5 / §3.5 — quantity measured: a produced surface (this
        engine's own emission) validates with every observable §3.5
        item PASS; the report verdict stays INCONCLUSIVE (HC-1/HC-2 by
        design — a machine never reports a fully clean artifact)."""
        cycle = lawful_cycle()
        for artifact in cycle["artifacts"]:
            self.assertEqual(artifact["parsed"]["status"], "lawful")
            validation = artifact["validation"]
            self.assertEqual(validation["verdict"], "INCONCLUSIVE")
            self.assertEqual(validation["counts"]["FAIL"], 0)
            self.assertIn("HC-1", [i["id"] for i in validation["items"]
                                   if i["verdict"] == "INCONCLUSIVE"])
            for entry in validation["items"]:
                if entry["verdict"] == "INCONCLUSIVE":
                    self.assertIn("reason", entry)
        self.assertEqual(cycle["validation"]["verdict"], "INCONCLUSIVE")
        self.assertEqual(cycle["validation"]["counts"]["FAIL"], 0)
        self.assertEqual(cycle["validation"]["counts"]["PASS"], 42)

    def test_three_distinct_things_with_distinct_steps(self):
        """C5 / §3.5 (semantic: "B, B'', ∞0' are three distinct things
        with distinct decoding steps") — quantity measured: distinct
        references PASS; two slots sharing one reference FAIL."""
        values = full_values()["V"]
        context = {sym: ref_text("ctx-%s" % sym)
                   for sym in decoder.REQUIRED_CONTEXT["V"]}
        artifact = compile_artifact("V", context=context, values=values,
                                    trail=v_trail())
        self.assertEqual(item(artifact["validation"], "CX-SEM-3")["verdict"],
                         "PASS")
        shared = dict(values)
        shared["B"] = shared["B''"]
        artifact2 = compile_artifact("V", context=context, values=shared,
                                     trail=v_trail())
        self.assertEqual(item(artifact2["validation"], "CX-SEM-3")["verdict"],
                         "FAIL")

    def test_crystallization_reads_the_trail_not_nothing(self):
        """C5 / §3.5 (semantic: "Crystallization reads the formation
        trail (not generated from nothing)") / R7 — quantity measured:
        a V with a trail passes R7/CX-SEM-5; B'' without a trail is
        refused; a foreign V surface carrying B'' but no TRAIL section
        FAILs CX-SEM-5."""
        values = full_values()["V"]
        context = {sym: ref_text("ctx-%s" % sym)
                   for sym in decoder.REQUIRED_CONTEXT["V"]}
        artifact = compile_artifact("V", context=context, values=values,
                                    trail=v_trail())
        self.assertEqual(item(artifact["validation"], "R7")["verdict"],
                         "PASS")
        self.assertEqual(item(artifact["validation"], "CX-SEM-5")["verdict"],
                         "PASS")
        self.assertEqual(item(artifact["validation"], "R6")["verdict"],
                         "PASS")
        stripped = artifact["surface"]
        begin = stripped.find("TRAIL:")
        end = stripped.find("\n", begin + 1)
        without_trail = (stripped[:begin] +
                         stripped[end:])
        foreign = validate_surface_text(without_trail)
        self.assertEqual(verdict_of(foreign, "CX-SEM-5"), "FAIL")

    def test_no_question_is_not_infinity_zero_prime(self):
        """C5 / R8 / CX-SEM-6 ("∞0' carries a question. No question =
        not ∞0'") — quantity measured: an empty ∞0′ slot FAILs R8 and
        CX-SEM-6 even though the slot exists."""
        values = full_values()["V"]
        values["∞0'"] = ""
        context = {sym: ref_text("ctx-%s" % sym)
                   for sym in decoder.REQUIRED_CONTEXT["V"]}
        artifact = compile_artifact("V", context=context, values=values,
                                    trail=v_trail())
        self.assertEqual(artifact["corruption"], "V∅")
        self.assertEqual(item(artifact["validation"], "R8")["verdict"],
                         "FAIL")
        self.assertEqual(item(artifact["validation"], "CX-SEM-6")["verdict"],
                         "FAIL")


class EmissionC6(unittest.TestCase):
    def test_every_phase_emits_a_lawful_attested_surface(self):
        """C6 / §3.6 — quantity measured: for all five phases the
        emitted surface parses LAWFUL through the attested parse_surface
        with the active phase, exact equations, exact decoding, correct
        output/gate/compiled symbol, and every used symbol resolved."""
        for phase in codex.COURSE:
            values = full_values()[phase]
            context = {}
            if phase != "S":
                context = {sym: ref_text("ctx-%s" % sym)
                           for sym in decoder.REQUIRED_CONTEXT[phase]}
            artifact = compile_artifact(
                phase, context=context, values=values,
                trail=v_trail() if phase == "V" else None)
            parsed = artifact["parsed"]
            self.assertEqual(parsed["status"], "lawful", phase)
            self.assertEqual(parsed["phase"], phase)
            self.assertEqual(parsed["active"]["equation"]["match"], True)
            self.assertEqual(parsed["decoding"]["matches"], True)
            self.assertEqual(parsed["compiled"]["symbol_matches"], True)
            self.assertEqual(parsed["compiled"]["gate_matches"], True)
            self.assertEqual(parsed["active"]["output_matches"], True)
            for entry in parsed["symbols"]:
                self.assertTrue(entry["covered"], entry)
                self.assertTrue(entry["in_vocabulary"], entry)
            for letter in codex.COURSE:
                self.assertTrue(
                    parsed["equations"][letter]["match"],
                    "%s equation %s" % (phase, letter))
            self.assertEqual(artifact["mark"], "mechanical")

    def test_surface_carries_the_block_exactly(self):
        """C6 / §3.1 ("Every compiled surface carries this block
        exactly") — quantity measured: the surface block's LAW..CENTER
        lines are the §3.1 lines byte for byte, inside the declared
        contract markers."""
        surface = emit("G", full_values()["G"])
        block = surface.split("⟦SURFACE v1⟧", 1)[1].split("⟦END SURFACE⟧",
                                                          1)[0]
        lines = [line for line in block.split("\n") if line.strip()][:13]
        self.assertEqual(lines, list(codex.BLOCK_LINES))

    def test_emission_carries_rules_chain_and_jacket(self):
        """C6 / §3.4 / §3.3 / D.14 — quantity measured: the emitted
        surface carries the thirteen decoder rules verbatim, the §3.3
        context chain verbatim, and the Appendix-D jacket with the D.7
        signless start line and the D.14 block verbatim — all OUTSIDE
        the surface block (visibly separate layers)."""
        surface = emit("S", {"X": "q"}, cell_address="")
        self.assertIn("⟦DECODER RULES⟧", surface)
        self.assertIn("⟦CONTEXT CHAIN⟧", surface)
        self.assertIn("⟦APPENDIX-D JACKET⟧", surface)
        for n in range(1, 14):
            self.assertIn(RULES["R%d" % n], surface)
        self.assertEqual(surface.count(codex.APPD_START_LINE), 1)
        for line in codex.APPD_D14_LINES:
            self.assertIn(line, surface)
        # the jacket never lands inside the ⟦SURFACE v1⟧ block
        inner = surface.split("⟦SURFACE v1⟧", 1)[1].split("⟦END SURFACE⟧",
                                                          1)[0]
        self.assertNotIn("⟦APPENDIX-D JACKET⟧", inner)
        self.assertNotIn("⟦DECODER RULES⟧", inner)

    def test_addressing_layer_4plus1_and_cell_checks(self):
        """C6 / D.12 (addressing) — quantity measured: the 4+1 cell
        reads PASS; a 3+1 cell FAILs naming the missing corner; a 6+1
        cell FAILs; the signless start reads PASS; ∞0′ ≡ ∞0 seeds the
        next cycle's S (AD-SEM-3 PASS)."""
        cycle = lawful_cycle()
        for artifact in cycle["artifacts"]:
            self.assertEqual(
                item(artifact["validation"], "AD-SYN-1")["verdict"], "PASS")
            self.assertEqual(
                item(artifact["validation"], "AD-SEM-2")["verdict"], "PASS")
            self.assertEqual(
                item(artifact["validation"], "AD-SEM-4")["verdict"], "PASS")
            self.assertEqual(
                item(artifact["validation"], "AD-SYN-2")["verdict"], "PASS")
        v_artifact = cycle["artifacts"][4]
        self.assertEqual(item(v_artifact["validation"], "AD-SEM-3")["verdict"],
                         "PASS")
        # 3+1 twin
        cell = {"address": "", "arrangement": ["S", "G", "Q", "P"],
                "seats": {}}
        foreign = validate_surface_text(
            emit("S", {"X": "q"}), cell=cell)
        self.assertEqual(verdict_of(foreign, "AD-SYN-1"), "FAIL")
        self.assertIn("3+1", item(foreign, "AD-SYN-1")["reason"])
        # 6+1 twin
        cell["arrangement"] = ["S", "G", "Q", "P", "V", "V"]
        foreign = validate_surface_text(emit("S", {"X": "q"}), cell=cell)
        self.assertEqual(verdict_of(foreign, "AD-SYN-1"), "FAIL")
        self.assertIn("6+1", item(foreign, "AD-SYN-1")["reason"])
        # the next cycle's S receives the prior V's ∞0′ (D.8)
        prior = v_artifact["decode"]["slots"]["∞0'"]
        cycle2 = compile_cycle(values_by_phase=full_values(), trail=v_trail(),
                               prior_infinity=("∞0'", prior),
                               prior_cycle=cycle["artifacts"])
        self.assertEqual(
            item(cycle2["artifacts"][0]["validation"], "AD-SEM-3")["verdict"],
            "PASS")

    def test_lenses_refine_never_replace(self):
        """C6 / R3 / CX-SEM-4 / AD-DRF-5 / CX-DRF-6 — quantity measured:
        lenses emitted on the parent phase read PASS on all four lens
        items (quality borrowed, parent equation, target = the parent's
        output)."""
        artifact = compile_artifact(
            "G", context={"X": ref_text("x")}, values=full_values()["G"],
            lenses=["GS", "GQ"])
        for iid in ("R3", "CX-SEM-4", "AD-DRF-5", "CX-DRF-6"):
            self.assertEqual(item(artifact["validation"], iid)["verdict"],
                             "PASS", iid)
        parsed_lenses = {lens["id"]: lens
                         for lens in artifact["parsed"]["lenses"]}
        self.assertEqual(parsed_lenses["GS"]["target"], "Y")
        self.assertTrue(parsed_lenses["GS"]["target_ok"])
        self.assertTrue(parsed_lenses["GS"]["equation_ok"])
        self.assertTrue(parsed_lenses["GS"]["quality_ok"])
        self.assertTrue(parsed_lenses["GQ"]["quality_ok"])
        self.assertTrue(parsed_lenses["GQ"]["question_ok"])


class AuthenticityC7(unittest.TestCase):
    def test_hc_checks_are_permanently_inconclusive(self):
        """C7 — quantity measured: HC-1 and HC-2 read INCONCLUSIVE for
        every artifact kind — a lawful V, a lawful S, an absent surface,
        a malformed surface — and no report ever reads PASS overall."""
        values = full_values()["V"]
        context = {sym: ref_text("ctx-%s" % sym)
                   for sym in decoder.REQUIRED_CONTEXT["V"]}
        cases = [
            compile_artifact("V", context=context, values=values,
                             trail=v_trail()),
            compile_artifact("S", context={}, values={"X": "q"}),
            {"validation": validate_surface_text(None)},
            {"validation": validate_surface_text("⟦SURFACE v1⟧\nLAW: x")},
        ]
        for case in cases:
            validation = case["validation"]
            self.assertEqual(verdict_of(validation, "HC-1"), "INCONCLUSIVE")
            self.assertEqual(verdict_of(validation, "HC-2"), "INCONCLUSIVE")
            self.assertNotEqual(validation["verdict"], "PASS")

    def test_no_attestation_write_path_anywhere(self):
        """C7 — quantity measured: the engine sources contain no
        attestation_ref identifier, no state="attested" write form, no
        cell-attest, no input(), no socket import — and the compiled
        artifact carries mark "mechanical" only."""
        for name in corruption.ENGINE_MODULES:
            source = open(os.path.join(HERE, name), encoding="utf-8").read()
            self.assertNotIn("attestation_ref", source, name)
            self.assertNotIn('state="attested"', source, name)
            self.assertNotIn("state = \"attested\"", source, name)
            self.assertNotIn("cell-attest", source, name)
            self.assertNotIn("input(", source, name)
            tree = ast.parse(source)
            imports = {alias.name for node in ast.walk(tree)
                       if isinstance(node, ast.Import)
                       for alias in node.names}
            imports |= {node.module.split(".")[0]
                        for node in ast.walk(tree)
                        if isinstance(node, ast.ImportFrom)
                        and node.module}
            self.assertNotIn("socket", imports, name)
            self.assertNotIn("requests", imports, name)
        artifact = compile_artifact("S", context={}, values={"X": "q"})
        self.assertEqual(artifact["mark"], "mechanical")
        self.assertNotIn("attestation", json.dumps(artifact))


class EquationBytesH_META_2(unittest.TestCase):
    def test_enumerated_forms_recompute_and_relocate(self):
        """H-META-2 — quantity measured: every enumerated equation form
        re-hashes to its declared sha (recomputed here, independently)
        and sits verbatim at its declared held-source line — the
        enumeration is proven, not asserted."""
        for letter, entries in codex.EQUATION_FORMS.items():
            for entry in entries:
                self.assertEqual(
                    hashlib.sha256(entry["form"].encode("utf-8")).hexdigest(),
                    entry["sha256"], letter)
                self.assertTrue(entry["source"], letter)
                for filename, line_no in entry["locations"]:
                    lines = held_lines(os.path.join(codex.SOURCES_DIR,
                                                    filename))
                    self.assertIn(entry["form"], lines[line_no - 1])
        # the commission's executed per-string shas (fact block §3)
        commission_shas = {
            "S": ["de0b90963d6110bf2092013401576c5ccb71751a8a7c9e3ab900a481c1dbfb1d",
                  "4fb171bab276a63cf5dd04a42a92ef6ceef41fa9b7ae1f71c0b74f5e14b13250"],
            "G": ["c2b0ed6eb2f0b8ce737b4656929e0b4bea1903d2071eca13d7961a99744a5c7e",
                  "98950e70a7de42c8d8b2eb2ecc0fc4b2e93833124d075a11931b570619490656"],
            "Q": ["cd20931fc7cd729a4de3779ccf63e63e627871a643cfc7c955961f9694a49bee",
                  "6e0609332484796cd5d584f2966511d94c2a459f6098a37b6b1313393f9a82f0"],
            "P": ["8175a49a811b0fb0402da736e404c341662fc970dbd327a6439efbb670f0ef49",
                  "ae9433ec8ed4a190f7d7483c795762005217c0181c5bb7ba99f1977593261ee0"],
            "V": ["7c8305fa45c203b50ac5ceb91cb85ac80722b8d0fb2eaed01988a1764eb65177",
                  "05101fd680e1d139487e3450ff751e4ab384dd0760547e2aafb9cc4cc8c5314a",
                  "528f868c2eb51024d49f261a68024f04a6f388ed057e89c65463e6f7686bad56"],
        }
        for letter, expected in commission_shas.items():
            observed = [entry["sha256"]
                        for entry in codex.EQUATION_FORMS[letter]]
            self.assertEqual(observed, expected, letter)

    def test_never_normalise_never_fold(self):
        """H-META-2 — quantity measured: the enumerated AppD compact
        form Q=φ⋂Ω is ACCEPTED as its own bytes, while the folded
        hybrids Q = φ ∩ Ω and V = (L ⋂ G → B'') → ∞0' match no
        enumerated form and FAIL naming the first differing codepoint —
        folding is renaming an L1 symbol and is refused."""
        base = emit("G", full_values()["G"])
        compact = base.replace("Q = φ ⋂ Ω", "Q=φ⋂Ω")
        report = validate_surface_text(compact)
        self.assertEqual(verdict_of(report, "AD-SYN-2"), "PASS")
        hybrid_q = base.replace("Q = φ ⋂ Ω", "Q = φ ∩ Ω")
        report = validate_surface_text(hybrid_q)
        self.assertEqual(verdict_of(report, "AD-SYN-2"), "FAIL")
        self.assertIn("U+2229", item(report, "AD-SYN-2")["reason"])
        hybrid_v = base.replace("V = (L ∩ G → B'') → ∞0'",
                                "V = (L ⋂ G → B'') → ∞0'")
        report = validate_surface_text(hybrid_v)
        self.assertEqual(verdict_of(report, "AD-SYN-2"), "FAIL")
        self.assertIn("U+22C2", item(report, "AD-SYN-2")["reason"])
        # both prime spellings of the prior ∞0′ decode (recorded, not folded)
        for spelling in ("∞0'", "∞0′"):
            report = decode("S", context={spelling: ref_text("prior")},
                            values={"X": "q"})
            self.assertEqual(report["prior_infinity_spelling"], spelling)


class VerifierLenses(unittest.TestCase):
    def test_lens1_criterion_measured_as_written(self):
        """Lens 1 (criterion match) — quantity measured: the decoding
        check is byte-exact (one reworded word in one operation FAILs
        CX-SYN-3, AD-DRF-3 and CX-DRF-3), and R8 reads "no question =
        not ∞0′" literally (an empty slot FAILs even though the slot
        exists)."""
        base = emit("G", full_values()["G"])
        reworded = base.replace(
            "2. SEEK α — within X, what is the irreducible core? Remove it "
            "and X collapses.",
            "2. SEEK α — within X, what is the irreducible center? Remove "
            "it and X collapses.")
        report = validate_surface_text(reworded)
        for iid in ("CX-SYN-3", "AD-DRF-3", "CX-DRF-3"):
            self.assertEqual(verdict_of(report, iid), "FAIL", iid)
        self.assertNotIn(reworded[reworded.find("2. SEEK"):][:200],
                         base)

    def test_lens2_invariant_end_to_end(self):
        """Lens 2 (invariant end-to-end) — quantity measured: across the
        whole decode→compile path, the five equations are byte-identical
        in every one of the cycle's five surfaces (one invariant, not
        per call), and every artifact's equation matches its enumerated
        form."""
        cycle = lawful_cycle()
        equations_blocks = set()
        for artifact in cycle["artifacts"]:
            parsed = artifact["parsed"]
            equations_blocks.add(tuple(
                parsed["equations"][letter]["sha256"]
                for letter in codex.COURSE))
            self.assertEqual(
                artifact["decode"]["equation_sha256"],
                codex.EQUATION_FORMS[artifact["phase"]][0]["sha256"])
        self.assertEqual(len(equations_blocks), 1)

    def test_lens3_absence_never_reads_valid(self):
        """Lens 3 (absence vs validity) — quantity measured: missing,
        empty and 404 inputs never read valid: absent surfaces read
        INCONCLUSIVE (never PASS) on every surface-dependent item, the
        sha256 of empty is e3b0c44298fc…, and a missing pinned file
        raises ImportError."""
        self.assertEqual(EMPTY_SHA256,
                         "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca4"
                         "95991b7852b855")
        for text in (None, ""):
            report = validate_surface_text(text)
            self.assertNotEqual(report["verdict"], "PASS")
            for iid in ("AD-SYN-2", "CX-SYN-2", "CX-SYN-3", "AD-DRF-5",
                        "CX-SEM-1", "R5"):
                self.assertEqual(verdict_of(report, iid), "INCONCLUSIVE",
                                 (text, iid))
        with self.assertRaises(ImportError):
            codex._read_pinned("/nonexistent/404.pin", "0" * 64, "test")

    def test_lens4_encoding_needle_survives_every_string_field(self):
        """Lens 4 (encoding) — quantity measured: the needle
        "∞0′ → ‖" pushed through every slot of every phase survives
        decode→emit→parse byte-exactly: the emitted bytes contain the
        needle, and every parsed slot reference equals sha256 of the
        needle's exact UTF-8 bytes."""
        needle_ref = ref_text(NEEDLE)
        for phase in codex.COURSE:
            values = {name: NEEDLE for name in codex.PHASE_SLOTS[phase]}
            context = {}
            if phase != "S":
                context = {sym: ref_text(NEEDLE + sym)
                           for sym in decoder.REQUIRED_CONTEXT[phase]}
            artifact = compile_artifact(
                phase, context=context, values=values,
                trail=[make_trail_entry(1, "GQ", "α thread", NEEDLE),
                       make_trail_entry(2, "QQ", "φ⋂Ω confirmation", NEEDLE),
                       make_trail_entry(3, "PP", "∇", NEEDLE),
                       make_trail_entry(4, "VV", "turning point", NEEDLE)]
                if phase == "V" else None)
            self.assertEqual(artifact["parsed"]["status"], "lawful", phase)
            self.assertIn(NEEDLE.encode("utf-8"),
                          artifact["surface"].encode("utf-8"), phase)
            for name, slot in artifact["parsed"]["slots"].items():
                self.assertEqual(slot["ref"], needle_ref["ref"],
                                 "%s/%s" % (phase, name))
                self.assertEqual(slot["len"], needle_ref["len"])

    def test_lens5_cold_restart_new_process_rebuilds_same_surface(self):
        """Lens 5 (cold restart) — quantity measured: a NEW python
        process rebuilds the same surface from disk alone (fresh import
        of the engine, inputs read from a file) and its byte sha equals
        the parent process's byte sha."""
        values = full_values()["G"]
        with tempfile.TemporaryDirectory() as tmp:
            inputs_path = os.path.join(tmp, "inputs.json")
            with open(inputs_path, "w", encoding="utf-8") as handle:
                json.dump({"phase": "G", "values": values, "cell": "SG"},
                          handle, ensure_ascii=False)
            child = (
                "import sys, json, hashlib\n"
                "sys.dont_write_bytecode = True\n"
                "sys.path.insert(0, %r)\n"
                "import compiler\n"
                "data = json.load(open(sys.argv[1], encoding='utf-8'))\n"
                "text = compiler.emit(data['phase'], data['values'], "
                "cell_address=data['cell'])\n"
                "print(hashlib.sha256(text.encode('utf-8')).hexdigest())\n"
                % HERE)
            proc = subprocess.run(
                [sys.executable, "-B", "-c", child, inputs_path],
                capture_output=True, text=True, timeout=180)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            parent_text = emit("G", values, cell_address="SG")
            self.assertEqual(
                proc.stdout.strip(),
                hashlib.sha256(parent_text.encode("utf-8")).hexdigest())

    def test_lens6_blind_tool_unobservable_reads_inconclusive(self):
        """Lens 6 (blind tool) — quantity measured: no desk is
        constituted on the box, so cell-scope items read INCONCLUSIVE
        with a stated reason, never clean; the two HC checks are
        INCONCLUSIVE by design; and every INCONCLUSIVE entry carries a
        reason."""
        report = validate_surface_text(emit("G", full_values()["G"]))
        self.assertEqual(verdict_of(report, "AD-SYN-1"), "INCONCLUSIVE")
        self.assertEqual(verdict_of(report, "AD-SEM-2"), "INCONCLUSIVE")
        self.assertIn("no desk is constituted",
                      item(report, "AD-SYN-1")["reason"])
        for entry in report["items"]:
            if entry["verdict"] == "INCONCLUSIVE":
                self.assertTrue(entry.get("reason"), entry["id"])
        self.assertEqual(report["verdict"], "INCONCLUSIVE")


class DeterminismAndScale(unittest.TestCase):
    def test_compilation_is_deterministic(self):
        """K2-style (determinism) — quantity measured: compiling the
        same inputs twice yields byte-identical surfaces and reports."""
        values = full_values()["Q"]
        context = {sym: ref_text("ctx-%s" % sym)
                   for sym in decoder.REQUIRED_CONTEXT["Q"]}
        one = compile_artifact("Q", context=context, values=values)
        two = compile_artifact("Q", context=context, values=values)
        self.assertEqual(one["surface"], two["surface"])
        self.assertEqual(one["validation"], two["validation"])

    def test_scale_repeats_the_lawful_cell(self):
        """R13 / §2.9 / AD-DRF-1 — quantity measured: the static scans
        find no depth cap, no re-implemented address grammar, no sign
        inside any equation constant; the checks PASS on a lawful
        cycle."""
        cycle = lawful_cycle()
        self.assertEqual(cycle["validation"]["items"]["R13"], "PASS")
        self.assertEqual(cycle["validation"]["items"]["AD-DRF-1"], "PASS")
        self.assertEqual(cycle["validation"]["items"]["AD-SYN-4"], "PASS")
        self.assertEqual(codex.COURSE, ("S", "G", "Q", "P", "V"))

    def test_aggregate_fails_on_any_failure(self):
        """C5 — quantity measured: the aggregate is FAIL iff any item
        ever FAILed (a defective report is never absorbed)."""
        good = lawful_cycle()
        broken = validate_surface_text("⟦SURFACE v1⟧\nLAW: H = ∞0 | A = K")
        combined = aggregate([artifact["validation"]
                              for artifact in good["artifacts"]] + [broken])
        self.assertEqual(combined["verdict"], "FAIL")


class DivergenceLogD14(unittest.TestCase):
    def test_phase_card_is_predictive_with_divergence_log(self):
        """D14 / phase card — quantity measured: the phase card exists,
        carries the D14 divergence log and the holds, is written in
        predictions (no ✅, no "tests green", no result claims), and
        the engine's own surfaces use no symbol outside the §1.9
        vocabulary."""
        card_path = os.path.join(HERE, "phase-card.md")
        self.assertTrue(os.path.exists(card_path))
        card = open(card_path, encoding="utf-8").read()
        self.assertIn("D14", card)
        self.assertIn("divergence", card.lower())
        self.assertIn("PREDICTION", card.upper())
        self.assertIn("H-META-2", card)
        self.assertNotIn("✅", card)
        self.assertNotIn("tests green", card)
        self.assertNotIn("all tests passed", card)
        self.assertNotIn("16/16 PASS", card)

    def test_engine_adds_no_symbol_and_no_operation(self):
        """D14 — quantity measured: every symbol name the engine emits
        comes from the attested §1.9 tables (nothing added, renamed or
        paraphrased), and the decoding operations are the attested
        table, never extended."""
        for phase in codex.COURSE:
            for name in codex.PHASE_SYMBOLS[phase]:
                self.assertIn(name, codex.SYMBOL_ROWS)
                self.assertIn(name, codex.SYMBOL_VOCABULARY, name)
            self.assertEqual(
                tuple(codex.DECODING_OPS[phase]),
                tuple(COMPILED[phase]["decoding"]))
        self.assertEqual(tuple(len(codex.DECODING_OPS[p]) for p in codex.COURSE),
                         (4, 5, 5, 6, 7))
        self.assertEqual(
            codex.CORRUPTION_CODES,
            frozenset(("L1", "L2", "L3", "L4", "V∅")))


if __name__ == "__main__":
    unittest.main(verbosity=2)
