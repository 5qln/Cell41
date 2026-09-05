#!/usr/bin/env bash
# the bridge — the live desk adapter + the runtime config-read: Amihai's numbered
# live block (T3). Every check below already passed agent-side; this re-runs them
# on the box. No check here touches the real live socket or prompts a real desk.
set -e
cd /home/deploy/the-cell/rounds/bridge/authored
export FRACTAL_LEDGER_DIR=/home/deploy/the-cell/ledger

echo "=== 1. python ==="
python3 --version

echo "=== 2. the author's suite (44 tests: live mode, fail-closed, config-read, defaults, cold restart, B4-pins) ==="
python3 selftest.py 2>&1 | tail -3

echo "=== 3. the gate ledger is still his plant, byte-for-byte ==="
sha256sum /home/deploy/the-cell/state/gates.jsonl
echo "   (expect 6989a742f57ec60a54d44062bad3fe9c6d2df28e66e92de96c1336be3a6539c3)"

echo "=== 4. the live desk mode resolves the real desks, read-only (zero writes) ==="
python3 - <<'PY'
import sys
sys.path.insert(0, ".")
sys.path.insert(0, "/home/deploy/the-cell/ledger")
import cost
# live mode returns a turn on the live socket with no process — never a spawn
adapter = cost.DeskAdapter({"cells": [""]}, "/tmp/bridge-live-check", mode="live")
turn = adapter.open_turn("", 0, "G")
print("live turn process:", turn.process, "| socket:", turn.socket_path)
adapter.close()
PY
