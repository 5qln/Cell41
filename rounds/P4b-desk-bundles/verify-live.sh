#!/usr/bin/env bash
# P4b — the desk bundles: his verification block (runs on the box, python 3.12.3).
# Runs the author's own suite (a hypothesis, not a result) plus prints the two
# byte-answers dsh gave in phase-card §1. The verifier's independent evidence
# (PASS 18/18) is already written; this block is his hand confirming the artifact
# runs clean in the target environment.
set -u
cd /home/deploy/the-cell/rounds/P4b-desk-bundles/authored || exit 9
export FRACTAL_LEDGER_DIR=/home/deploy/the-cell/ledger
echo "python: $(python3 -c 'import sys;print(sys.version.split()[0])')"
python3 selftest.py
echo
echo "=== the two byte-answers (dsh, phase-card §1) ==="
python3 - <<'PY'
import sys
sys.path.insert(0, ".")
import grammar
print("seal (activation page):", grammar.SEAL_FORMS[0]["sha256"])
print("  -> the NUMBERED 217-byte nine-line block (each line 'N.  …', trailing newline)")
print("word order adopted:", grammar.WORD_ORDER, "(D.2 inner-first; D.3/D.6 flagged for his confirmation)")
print("V canonical form:", grammar.PHASE["V"]["equation"])
PY
