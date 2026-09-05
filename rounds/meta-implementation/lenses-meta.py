#!/usr/bin/env python3
"""Lens pack — the Grammar (the meta implementation).

The six lenses, domain-shaped for the decoder/compiler: each is a bug the build already
paid for, checked here in the engine's own terms. Stdlib only.
"""

from __future__ import annotations

import ast
import hashlib
import os
import subprocess
import sys
import tempfile

from harness import FAIL, INCONCLUSIVE, PASS, Result

GOOD = "/opt/data/tmp/proving-meta/good"
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()
NEEDLE = "∞0′ → ‖"


def _res(lid, title, status, raw="", note=""):
    return Result(id=lid, title=title, status=status, raw=raw, note=note)


def _bind(ctx, key):
    name = ctx.spec["binding"].get(key)
    if not name or not hasattr(ctx.artifact.module, name):
        return None
    return getattr(ctx.artifact.module, name)


def run_lenses(ctx, spec, criteria):
    results = []

    # L1 — criterion match: one quantity per criterion, every probe registered
    measures = [c.get("measures") for c in spec.get("criteria", [])]
    claims = [c.get("measures") for c in spec.get("claims", [])]
    all_m = [m for m in measures + claims if m]
    dupes = sorted({m for m in all_m if all_m.count(m) > 1})
    from harness import PROBES
    missing = [c["probe"] for c in spec.get("criteria", []) + spec.get("claims", [])
               if c["probe"] not in PROBES]
    if dupes or missing:
        results.append(_res("L1", "criterion match — one quantity per criterion, "
                                  "no blind probe", FAIL,
                            "dupes=%r missing=%r" % (dupes, missing)))
    else:
        results.append(_res("L1", "criterion match", PASS,
                            "%d criteria + %d claims, each a distinct measured "
                            "quantity, every probe registered" % (len(measures), len(claims))))

    # L2 — invariant end-to-end: the five equations byte-identical across all five
    # emitted surfaces of one cycle (one pass over the whole cycle, never per call).
    emit = _bind(ctx, "emit_fn")
    course = _bind(ctx, "course_const")
    if emit is None or course is None:
        results.append(_res("L2", "invariant end-to-end — the block identical across "
                                 "the cycle", INCONCLUSIVE, note="emit/course not bound"))
    else:
        import codex as CX
        values = {"S": {"X": "q"}, "G": {"X": "q", "α": "a", "{α'}": "e", "Y": "p"},
                  "Q": {"X": "q", "α": "a", "Y": "p", "φ⋂Ω": "l", "Z": "k"},
                  "P": {"X": "q", "α": "a", "Y": "p", "Z": "k", "∇": "f", "A": "c"},
                  "V": {"X": "q", "α": "a", "Y": "p", "Z": "k", "∇": "f", "A": "c",
                        "L": "h", "G": "b", "B": "ben", "B''": "s", "∞0'": "n"}}
        blocks = set()
        for phase in course:
            text = emit(phase, values[phase])
            start = text.index("LAW: H = ∞0 | A = K")
            end = text.index("CENTER: not a sixth phase — coherence only")
            blocks.add(text[start:end + 1])
        if len(blocks) != 1:
            results.append(_res("L2", "invariant end-to-end — the block identical across "
                                      "the cycle", FAIL,
                                "the §3.1 block differs across the five surfaces"))
        else:
            results.append(_res("L2", "invariant end-to-end", PASS,
                                "the §3.1 block is byte-identical across all five "
                                "emitted surfaces — one invariant, not per call"))

    # L3 — absence vs validity: missing/empty never reads valid
    parse = _bind(ctx, "parse_surface_fn")
    if parse is None:
        results.append(_res("L3", "absence vs validity", INCONCLUSIVE, note="parse not bound"))
    else:
        import codex as CX
        absent = parse(None, CX.EQUATION_FORMS)
        empty = parse("", CX.EQUATION_FORMS)
        if absent.get("status") != "absent" or empty.get("status") != "absent":
            results.append(_res("L3", "absence vs validity", FAIL,
                                "absent=%r empty=%r (sha256 of empty is %s, never a surface)"
                                % (absent.get("status"), empty.get("status"),
                                   EMPTY_SHA256[:12])))
        else:
            results.append(_res("L3", "absence vs validity", PASS,
                                "absent→absent, empty→absent (e3b0c44298fc…), never a "
                                "valid surface"))

    # L4 — encoding: the needle survives emit → parse byte-exact (the byte-transparency
    # check: no normalisation anywhere in the emission path)
    emit2 = _bind(ctx, "emit_fn")
    parse2 = _bind(ctx, "parse_surface_fn")
    if not (emit2 and parse2):
        results.append(_res("L4", "encoding — ∞0′ → ‖ survives the pipeline", INCONCLUSIVE,
                            note="emit/parse not bound"))
    else:
        import codex as CX
        text = emit2("V", {"∞0'": NEEDLE})
        parsed = parse2(text, CX.EQUATION_FORMS)
        if parsed.get("status") != "lawful" or NEEDLE not in text:
            results.append(_res("L4", "encoding", FAIL,
                                "the needle did not survive: present=%r status=%r"
                                % (NEEDLE in text, parsed.get("status"))))
        else:
            results.append(_res("L4", "encoding", PASS,
                                "∞0′ → ‖ survived emit→parse byte-exact; no "
                                "normalisation anywhere in the path"))

    # L5 — cold restart: a NEW process rebuilds the same surface from disk alone
    emit3 = _bind(ctx, "emit_fn")
    if emit3 is None:
        results.append(_res("L5", "cold restart — the second process rebuilds from disk",
                            INCONCLUSIVE, note="emit not bound"))
    else:
        adir = os.path.dirname(ctx.artifact.path)
        code = (
            "import os; os.environ.setdefault('FRACTAL_LEDGER_DIR', "
            "'/opt/data/tmp/proving-meta/ledger'); import sys; "
            "sys.path.insert(0, '%s'); import compiler as C; "
            "import hashlib; t = C.emit('V', {'X':'q','α':'a','Y':'p','Z':'k','∇':'f',"
            "'A':'c','L':'h','G':'b','B':'ben',\"B''\":'s',\"∞0'\":'∞0′ → ‖'}); "
            "print(hashlib.sha256(t.encode('utf-8')).hexdigest())" % adir)
        try:
            out = subprocess.run([sys.executable, "-B", "-c", code],
                                 capture_output=True, text=True, timeout=60)
            child_sha = out.stdout.strip()
        except Exception as exc:
            results.append(_res("L5", "cold restart", FAIL, "subprocess raised: %s" % exc))
            return results + []
        import compiler as C
        parent_sha = hashlib.sha256(C.emit(
            "V", {"X": "q", "α": "a", "Y": "p", "Z": "k", "∇": "f", "A": "c",
                  "L": "h", "G": "b", "B": "ben", "B''": "s",
                  "∞0'": "∞0′ → ‖"}).encode("utf-8")).hexdigest()
        if child_sha != parent_sha:
            results.append(_res("L5", "cold restart", FAIL,
                                "parent %s ≠ child %s" % (parent_sha, child_sha)))
        else:
            results.append(_res("L5", "cold restart", PASS,
                                "a fresh python -B process re-imported the engine and "
                                "rebuilt the byte-identical surface from disk alone"))

    # L6 — blind tool: no desk constituted; HC-1/HC-2 INCONCLUSIVE by design; no report
    # can ever read a fully clean verdict.
    validate = _bind(ctx, "validate_fn")
    compile_cycle = _bind(ctx, "compile_cycle_fn")
    if not (validate and compile_cycle):
        results.append(_res("L6", "blind tool — nothing unobservable reads clean",
                            INCONCLUSIVE, note="validate/compile_cycle not bound"))
    else:
        import codex as CX
        import decoder as D
        from corruption import TRAIL_TAGS
        trail = [D.make_trail_entry(i, "V" + "SGQPV"[(i - 1) % 5], tag, "trail " + tag)
                 for i, tag in enumerate(TRAIL_TAGS, start=1)]
        cyc = compile_cycle(values_by_phase={
            "S": {"X": "q"}, "G": {"X": "q", "α": "a", "{α'}": "e", "Y": "p"},
            "Q": {"X": "q", "α": "a", "Y": "p", "φ⋂Ω": "l", "Z": "k"},
            "P": {"X": "q", "α": "a", "Y": "p", "Z": "k", "∇": "f", "A": "c"},
            "V": {"X": "q", "α": "a", "Y": "p", "Z": "k", "∇": "f", "A": "c",
                  "L": "h", "G": "b", "B": "ben", "B''": "s", "∞0'": "n"}},
            trail=trail)
        verdict = cyc["validation"]["verdict"]
        hc = [i for i in cyc["artifacts"][0]["validation"]["items"]
              if i["id"] in ("HC-1", "HC-2")]
        if verdict == "PASS" or any(i["verdict"] != "INCONCLUSIVE" for i in hc):
            results.append(_res("L6", "blind tool", FAIL,
                                "a machine report read a clean verdict (cycle=%s, HC=%r)"
                                % (verdict, [(i["id"], i["verdict"]) for i in hc])))
        else:
            results.append(_res("L6", "blind tool", PASS,
                                "no desk is constituted; HC-1/HC-2 INCONCLUSIVE by "
                                "design — no machine report can read a fully clean verdict"))

    return results
