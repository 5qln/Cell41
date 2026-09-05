#!/usr/bin/env bash
# R02/B1 — the tier only Amihai can authorize: the read-only walker polling the LIVE cell.
# Read-only by construction (C3 proved zero pane writes); every record goes to a scratch
# ledger in a temp dir, never to state/gates.jsonl.
set -u
cd /home/deploy/the-cell/rounds/R02-B1/authored || exit 9
export FRACTAL_LEDGER_DIR=/home/deploy/the-cell/ledger
export HERDR_SOCKET_PATH="${HERDR_SOCKET_PATH:-$HOME/.config/herdr/herdr.sock}"
SCRATCH="$(mktemp -d)"
# a COPY of the real ledger: the walker reads Amihai's own plant, and writes only to the copy
cp /home/deploy/the-cell/state/gates.jsonl "$SCRATCH/scratch.jsonl"

echo "=== 1. the author's own tests, run here on the box ==="
python3 selftest.py 2>&1 | grep -E "^(Ran|OK|FAILED)"

echo
echo "=== 2. your plant, before (this hash must not change) ==="
sha256sum /home/deploy/the-cell/state/gates.jsonl

echo
echo "=== 3. the walker polling YOUR live cell — 3 ticks, reads only ==="
SCRATCH="$SCRATCH" python3 - <<'PY'
import datetime, json, os, sys
sys.path[:0] = [os.getcwd(), os.environ["FRACTAL_LEDGER_DIR"]]
from walker import Walker

ledger = os.path.join(os.environ["SCRATCH"], "scratch.jsonl")
w = Walker(socket_path=os.environ["HERDR_SOCKET_PATH"], ledger_path=ledger)
for i in range(3):
    f = w.tick()
    line = []
    for d in f["desks"]:
        mark = "BLOCKED" if d["verdict"]["blocked"] else "-"
        line.append(f'{d["desk"]}({d["label"]})@{d["pane_id"]} {d["agent_status"]} {mark}')
    print(f'tick {f["tick"]}  phase={f["phase"].get("gate")}/{f["phase"].get("state")}  ' + " | ".join(line))
    if f["unresolved_desks"]:
        print("           unresolved:", f["unresolved_desks"])
rec = w.reconstruct()
print("\nreconstructed from polling alone:")
print("  ticks:", rec.get("ticks"), " holds appended:", len(rec.get("appended_records", []) or []))
for desk, seq in (rec.get("desk_sequences") or {}).items():
    print(f"  {desk}: {seq}")
w.close()
PY

echo
echo "=== 4. your plant, after (must be the same hash, still 1 record) ==="
sha256sum /home/deploy/the-cell/state/gates.jsonl
wc -l < /home/deploy/the-cell/state/gates.jsonl
echo
echo "=== 5. what the walker wrote (a scratch file, not your ledger) ==="
ls -la "$SCRATCH"
rm -rf "$SCRATCH"
