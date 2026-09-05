#!/usr/bin/env python3
"""Build the meta-grammar defective twins — `good` + N surgical defects.

Each defect is a single, named mutation of dsh's real artifact; it must fail exactly
the criterion it targets and nothing else (non-cascading, no import crash). The
acceptance selftest (`selftest_meta.py`) runs the audit pack against `good` (18/18) and
each twin (targeted criterion FAIL, others intact).

Design rule per defect: the mutation must be visible to EXACTLY ONE probe and must not
break the module import (a defect that makes the artifact unimportable reads INCONCLUSIVE
everywhere, not a clean FAIL).
"""

from __future__ import annotations

import os
import shutil

ROOT = "/opt/data/tmp/proving-meta"
GOOD = os.path.join(ROOT, "good")


def _copy(name):
    dst = os.path.join(ROOT, name)
    shutil.rmtree(dst, ignore_errors=True)
    shutil.copytree(GOOD, dst)
    return dst


def _patch(path, old, new):
    src = open(path, encoding="utf-8").read()
    if old not in src:
        raise SystemExit("patch anchor not found in %s: %r" % (path, old[:70]))
    open(path, "w", encoding="utf-8").write(src.replace(old, new, 1))


def bad_c1():
    d = _copy("bad-c1")
    p = os.path.join(d, "decoder.py")
    # drop the last decoding operation of P only — C1 checks the walked op list
    _patch(p,
           "    operations = [\n"
           "        {\"n\": index, \"op\": text}\n"
           "        for index, text in enumerate(DECODING_OPS[phase], start=1)]",
           "    ops_table = list(DECODING_OPS[phase])\n"
           "    if phase == \"P\":\n"
           "        ops_table = ops_table[:-1]\n"
           "    operations = [\n"
           "        {\"n\": index, \"op\": text}\n"
           "        for index, text in enumerate(ops_table, start=1)]")


def bad_c2():
    d = _copy("bad-c2")
    p = os.path.join(d, "compiler.py")
    # the public block constant drifts (the emission still uses BLOCK_LINES directly,
    # so C6's "block exact in the emission" stays intact — C2 alone reads this constant)
    _patch(p, 'CONSTITUTIONAL_BLOCK = "\\n".join(BLOCK_LINES)',
           'CONSTITUTIONAL_BLOCK = "\\n".join(BLOCK_LINES) + "\\nEXTRA LINE"')


def bad_c3():
    d = _copy("bad-c3")
    p = os.path.join(d, "compiler.py")
    # paraphrase one rule citation (key kept, so CHECK_META import-time reads don't crash)
    _patch(p, "RULES = dict(RULE_LINES)",
           'RULES = dict(RULE_LINES)\nRULES["R13"] = "R13 paraphrased (defect)"')


def bad_c4():
    d = _copy("bad-c4")
    p = os.path.join(d, "corruption.py")
    # disable the L2 detector only — classify() then returns None for the L2 signal,
    # but no sixth code exists, so K3's sixth-code scan stays clean
    _patch(p, "    if evidence.get(\"x_generated\"):",
           "    if False and evidence.get(\"x_generated\"):")


def bad_c6():
    d = _copy("bad-c6")
    p = os.path.join(d, "compiler.py")
    # rename the jacket's open-marker — C6 greps for the exact ⟦APPENDIX-D JACKET⟧
    # marker, while the engine's own AD-DRF-2 greps the *words* "Appendix-D jacket"
    # (still present in the DERIVED: line), so validate() does not also fail
    _patch(p, 'lines.append("⟦APPENDIX-D JACKET⟧")',
           'lines.append("⟦JACKET⟧")')


def bad_c7():
    d = _copy("bad-c7")
    p = os.path.join(d, "decoder.py")
    _patch(p,
           '        "corruption_detections": detections,\n    }',
           '        "corruption_detections": detections,\n'
           '        "authentic": False,\n    }')


def bad_k1():
    d = _copy("bad-k1")
    p = os.path.join(d, "decoder.py")
    # a never-called function carrying a third-party import — the K1 AST scan catches
    # it, but the import is never executed, so the module still imports cleanly
    _patch(p, "import re\n",
           "import re\n\n\ndef _unused_foreign():\n    import requests  # third-party (defect)\n")


def bad_k5():
    d = _copy("bad-k5")
    p = os.path.join(d, "compiler.py")
    # a podium write path (never called — K5 greps the source, not the behaviour)
    _patch(p,
           "def emit(phase, slot_texts, lens_ids=(), trail_report=None,",
           "def _write_podium():\n"
           "    open('nodes/_/question.md', 'w').write('q')\n\n\n"
           "def emit(phase, slot_texts, lens_ids=(), trail_report=None,")


def main():
    bad_c1(); bad_c2(); bad_c3(); bad_c4(); bad_c6(); bad_c7(); bad_k1(); bad_k5()
    print("twins built:")
    for name in sorted(os.listdir(ROOT)):
        if name.startswith("bad-"):
            print("  ", name)


if __name__ == "__main__":
    main()
