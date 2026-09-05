#!/usr/bin/env bash
# Grammar (the meta implementation) — the live tier for Amihai's numbered block.
# Runs the author's own selftest on the box's python 3.12.3 and prints the pinned
# artifact shas. This is the SAME block the verifier ran first; his hand re-runs it.
set -u
ROUND=/home/deploy/the-cell/rounds/meta-implementation
echo "=== author selftest (40 checks, predictions only — the verifier recomputes) ==="
/usr/bin/python3.12 -B "$ROUND/authored/selftest.py"
echo
echo "=== pinned artifact shas (byte-identical to the verifier's copies) ==="
cd "$ROUND/authored" && sha256sum codex.py decoder.py corruption.py compiler.py selftest.py phase-card.md
echo
echo "=== held source shas (page + extraction) ==="
sha256sum "$ROUND/sources/5qln-codex.txt" "$ROUND/sources/5qln-codex-appendix-D-the-fractal.txt"
