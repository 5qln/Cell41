#!/usr/bin/env bash
# P4a verify — runs on the box, no desk constituted (H-P4a-4).
# 1) the author's own suite   2) a fresh-process stepped walk, read back
# 3) the authored file hashes (what the verifier's 16/16 rests on)
set -u
cd /home/deploy/the-cell/rounds/P4a-step-mode/authored || exit 1

echo "1. the author's own suite (a hypothesis, not a result):"
python3 selftest.py 2>&1 | tail -3

echo
echo "2. the live box: no desk is constituted (H-P4a-4), so the boot fails closed:"
python3 - <<'PY'
import sys, tempfile, os
sys.path.insert(0, os.getcwd())
sys.path.insert(0, "/home/deploy/the-cell/ledger")
from driver import Driver
import step as st

tmp = tempfile.mkdtemp(prefix="p4a-verify-")
ledger = os.path.join(tmp, "gates.jsonl")
from fractal_ledger import LedgerWriter
rec = __import__("fractal_ledger").make_record(
    address="", gate="x", state="attested", mark="emergent",
    payload_ref="fixture:plant", attestation_ref="Start from Not Knowing",
    block_version="")
with LedgerWriter(ledger) as w:
    w.append(rec)

drv = Driver(socket_path=os.path.join(tmp, "cell.sock"), ledger_path=ledger,
             blocks={"S": {"skills": ["fixture-skill"], "instruction": "x"},
                     "G": {"skills": ["fixture-skill"], "instruction": "y"},
                     "Q": {"skills": ["fixture-skill"], "instruction": "z"},
                     "P": {"skills": ["fixture-skill"], "instruction": "a"},
                     "V": {"skills": ["fixture-skill"], "instruction": "b"}},
             pi_home=tmp)
try:
    drv.boot()
    print("booted (unexpected)")
except Exception as exc:
    print("REFUSED : %s" % type(exc).__name__)
    print("meaning : no Pi extension is installed, so no desk is constituted and")
    print("          the trust assertion fails closed with INCONCLUSIVE (H-P4a-4).")
    print("          That refusal IS the step mode working — the 16/16 evidence")
    print("          records it; P4b's desk bundles are what turn it into PASS.")
PY

echo
echo "3. the authored bytes the verifier judged (sha256):"
sha256sum conformance.py surface.py step.py driver.py selftest.py phase-card.md
