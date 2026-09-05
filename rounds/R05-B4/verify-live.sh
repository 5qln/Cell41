#!/usr/bin/env bash
# R05-B4 — the unattended run: Amihai's numbered live block (T3).
# Every check below already passed agent-side; this re-runs them on the box.
set -e
cd /home/deploy/the-cell/rounds/R05-B4/authored
export FRACTAL_LEDGER_DIR=/home/deploy/the-cell/ledger

echo "=== 1. python ==="
python3 --version

echo "=== 2. the author's suite (34 tests: the ≥20-cycle run, kill -9 re-arm, budget hold, holds, tentative, torn trail) ==="
python3 selftest.py 2>&1 | tail -5

echo "=== 3. the gate ledger is still his plant, byte-for-byte ==="
sha256sum /home/deploy/the-cell/state/gates.jsonl
echo "   (expect 6989a742f57ec60a54d44062bad3fe9c6d2df28e66e92de96c1336be3a6539c3)"
