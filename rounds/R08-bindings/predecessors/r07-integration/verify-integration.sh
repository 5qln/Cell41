#!/usr/bin/env bash
# verify-integration — the integration round's enforcement runner (W2):
# re-runs the pin check, the three enforcement legs (capability scan ·
# entry-point census · config-schema validation), the plan-equivalence
# dry run (C3), and the gates-plant re-check.  The live verdict is
# reported honestly — findings are the enforcement working, never
# papered over (H-INT-5).
#
# Exit: 0 all PASS · 1 any FAIL · 2 INCONCLUSIVE.
# No check here prompts a real desk (H-INT-1 — fixtures only).
set -u
cd "$(dirname "$0")"
export FRACTAL_LEDGER_DIR="${FRACTAL_LEDGER_DIR:-/home/deploy/the-cell/ledger}"
PYTHON="${PYTHON:-python3}"
FAIL=0
INC=0

echo "=== 1. python ==="
"$PYTHON" --version

echo "=== 2. sha-pins (the import IS the pin check — a drifted pin refuses) ==="
if "$PYTHON" -c 'import sys; sys.path.insert(0, "."); import surface_contract as sc; print("pinned files:", len(sc.PINNED_FILES)); print("contract:", sc.CONTRACT_VERSION)'; then
  echo "   pins: PASS"
else
  echo "   pins: FAIL (import refused)"
  FAIL=1
fi

echo "=== 3. enforcement legs 1-3 + gates plant ==="
LEGS_OUTPUT=$("$PYTHON" enforce.py --verify-all)
echo "$LEGS_OUTPUT" | "$PYTHON" -c 'import json,sys; r=json.load(sys.stdin); [print("   %s: %s" % (k, v.get("verdict"))) for k, v in r["legs"].items()]; print("   gates_plant:", r["gates_plant"].get("verdict")); print("   overall:", r["verdict"])'
case "$(echo "$LEGS_OUTPUT" | "$PYTHON" -c 'import json,sys; print(json.load(sys.stdin)["verdict"])')" in
  PASS) ;;
  INCONCLUSIVE) INC=1 ;;
  *) FAIL=1 ;;
esac

echo "=== 4. plan-equivalence dry run (C3 — the wrapper adds nothing) ==="
TMPDIR_VERIFY=$(mktemp -d)
"$PYTHON" cellctl conduct --plan-only \
  --scenario fixtures/scenarios/pinned-cycle.json > "$TMPDIR_VERIFY/cli.json" 2> "$TMPDIR_VERIFY/cli.err"
CLI_CODE=$?
"$PYTHON" fixtures/plan_equivalence.py \
  fixtures/scenarios/pinned-cycle.json > "$TMPDIR_VERIFY/direct.json" 2> "$TMPDIR_VERIFY/direct.err"
DIRECT_CODE=$?
if [ "$CLI_CODE" -ne "$DIRECT_CODE" ]; then
  echo "   plan-equivalence: FAIL (exit codes differ: cli=$CLI_CODE direct=$DIRECT_CODE)"
  FAIL=1
elif ! cmp -s "$TMPDIR_VERIFY/cli.json" "$TMPDIR_VERIFY/direct.json"; then
  echo "   plan-equivalence: FAIL (bytes differ)"
  FAIL=1
else
  echo "   plan-equivalence: PASS (byte-identical)"
fi
rm -rf "$TMPDIR_VERIFY"

echo "=== 5. gates.jsonl — his plant, byte-for-byte ==="
sha256sum /home/deploy/the-cell/state/gates.jsonl 2>/dev/null \
  || { echo "   gates plant: absent — FAIL"; FAIL=1; }
echo "   (expect 6989a742f57ec60a54d44062bad3fe9c6d2df28e66e92de96c1336be3a6539c3)"

if [ "$FAIL" -ne 0 ]; then
  echo "VERDICT: FAIL"; exit 1
elif [ "$INC" -ne 0 ]; then
  echo "VERDICT: INCONCLUSIVE"; exit 2
fi
echo "VERDICT: PASS"; exit 0
