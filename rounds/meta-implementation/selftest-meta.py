#!/usr/bin/env python3
"""Acceptance selftest — the meta-grammar audit pack, judged BEFORE it judges anything.

Proves the pack is honest by running it against:
  * `good`  = dsh's real authored artifact → every criterion/claim/lens PASS (18/18);
  * `bad-*` = `good` + one surgical defect → the targeted criterion FAILs and is named,
              and nothing cascades.

The defect twins are built by `build_twins_meta.py`. This file re-runs the audit pack
against each twin in a fresh process (no module cache leaks) and asserts the expected
verdicts. Exit 0 = the pack is accepted.

Stdlib only.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = "/opt/data/tmp/proving-meta"
SPEC = os.path.join(HERE, "specs", "meta-grammar.json")
SPEC_TMPL = json.loads(open(SPEC, encoding="utf-8").read())

# the twin → which single criterion/claim id must FAIL (and nothing else)
EXPECT_FAIL = {
    "good": None,
    "bad-c1": "C1",
    "bad-c2": "C2",
    "bad-c3": "C3",
    "bad-c4": "C4",
    "bad-c6": "C6",
    "bad-c7": "C7",
    "bad-k1": "K1",
    "bad-k5": "K5",
}


def _audit(artifact, name):
    spec = dict(SPEC_TMPL)
    spec["artifact"] = artifact
    # rewrite sys_path to the twin's dir so its siblings (and its own codex/…) resolve
    twin_dir = os.path.join(ROOT, name)
    spec["sys_path"] = [twin_dir, os.path.join(ROOT, "ledger")]
    spec["artifact_modules"] = [
        os.path.join(twin_dir, f) for f in
        ("codex.py", "corruption.py", "decoder.py", "compiler.py")]
    path = os.path.join(tempfile.mkdtemp(prefix="meta-selftest-"), "spec.json")
    json.dump(spec, open(path, "w", encoding="utf-8"))
    out = os.path.join(tempfile.mkdtemp(prefix="meta-selftest-"), "evidence.md")
    proc = subprocess.run(
        [sys.executable, "-B", os.path.join(HERE, "audit.py"), "--spec", path,
         "--out", out],
        capture_output=True, text=True, timeout=300)
    # parse the per-line verdicts from stdout (format: "<VERDICT>   <ID>  <title>")
    rows = {}
    known = ("C1", "C2", "C3", "C4", "C5", "C6", "C7",
             "K1", "K2", "K3", "K4", "K5", "L1", "L2", "L3", "L4", "L5", "L6")
    for line in proc.stdout.splitlines():
        toks = line.split()
        if len(toks) >= 2 and toks[1] in known:
            rows[toks[1]] = toks[0]
    return proc.returncode, rows


def main():
    os.environ.setdefault("FRACTAL_LEDGER_DIR", os.path.join(ROOT, "ledger"))
    failures = []

    # 1. good → 18/18 (criteria + claims + lenses all PASS)
    rc, rows = _audit(os.path.join(ROOT, "good", "compiler.py"), "good")
    if rc != 0 or len(rows) != 18 or any(v != "PASS" for v in rows.values()):
        failures.append("good: rc=%d rows=%r (want 18/18 PASS)" % (rc, rows))
    else:
        print("good: 18/18 PASS  ✓")

    # 2. each bad twin → the targeted id FAILs, everything else stays intact
    for name, target in EXPECT_FAIL.items():
        if name == "good":
            continue
        rc, rows = _audit(os.path.join(ROOT, name, "compiler.py"), name)
        if target not in rows or rows[target] != "FAIL":
            failures.append("%s: %s = %r (want FAIL)" % (name, target, rows.get(target)))
            continue
        # non-cascading: no OTHER criterion/claim/lens may FAIL (INCONCLUSIVE/PASS ok)
        cascaded = [cid for cid, v in rows.items() if v == "FAIL" and cid != target]
        if cascaded:
            failures.append("%s: cascading FAILs %r" % (name, cascaded))
        else:
            print("%s: %s FAIL, no cascade  ✓" % (name, target))

    if failures:
        print("\nPACK NOT ACCEPTED:\n  " + "\n  ".join(failures))
        return 1
    print("\nPACK ACCEPTED — good 18/18, every surgical defect caught on its own axis.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
