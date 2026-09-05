#!/usr/bin/env bash
# boot.sh — boot this desk's pi agent (canonical: herdr agent start).
# usage: boot.sh [S|G|Q|P|V]  (default: the desk whose directory holds this script)
#
# The charter (seal, seat, §3.6 surface) auto-loads from .pi/APPEND_SYSTEM.md;
# model/thinking/tools auto-load from .pi/settings.json (trust: always on this host).
# Only the shared 5qln-lock skill is passed explicitly.
set -euo pipefail

DESK="${1:-$(basename "$(cd "$(dirname "$0")" && pwd)")}"
case "$DESK" in
  S|G|Q|P|V) ;;
  *) echo "desk must be S, G, Q, P or V" >&2; exit 2 ;;
esac

pane=$(herdr pane list 2>/dev/null | python3 -c "
import json, sys
for p in json.load(sys.stdin)['result']['panes']:
    if p.get('label', '').upper() == '${DESK}':
        print(p['pane_id']); break
")
[ -z "$pane" ] && { echo "no pane labelled ${DESK}" >&2; exit 3; }

herdr agent start "$(printf '%s' "$DESK" | tr 'A-Z' 'a-z')" --kind pi --pane "$pane" \
  --timeout 60000 -- --skill /home/deploy/the-cell/skills/5qln-lock
