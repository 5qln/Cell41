#!/usr/bin/env bash
# R04-B3 — the descent: his verification block (runs on the box, python 3.12.3).
# Runs the author's own suite (a hypothesis, not a result) plus prints the
# letter-order hold facts dsh gave in phase-card §1. The verifier's independent
# evidence (PASS 18/18) is already written; this block is his hand confirming the
# artifact runs clean in the target environment.
set -u
cd /home/deploy/the-cell/rounds/R04-B3/authored || exit 9
export FRACTAL_LEDGER_DIR=/home/deploy/the-cell/ledger
echo "python: $(python3 -c 'import sys;print(sys.version.split()[0])')"
python3 selftest.py
echo
echo "=== the letter-order hold (dsh, phase-card §1) ==="
python3 - <<'PY'
import sys
sys.path.insert(0, ".")
import descent
print("word order (declared parameter):", descent.grammar.WORD_ORDER,
      "— D.2 inner-first carried; D.3/D.6 outer-first stays HIS to confirm (H-B3-2)")
print("the letter-order touches exactly two spots:")
print("  zoom_in  delegates to grammar.seat_address (the parameter)")
print("  zoom_out is the only WORD_ORDER branch in the module")
print("sealed corruption codes (no sixth):", " ".join(descent.CORRUPTION_CODES))
print("pinned predecessor shas (a drifted predecessor is an ImportError, never a silent substitution)")
print("  grammar:", descent._SHA_GRAMMAR[:16] + "…  block:", descent._SHA_BLOCK[:16]
      + "…  driver:", descent._SHA_DRIVER[:16] + "…")
PY
