# Security policy

## What this repository is

Cell41 is a declarative 5QLN orchestration cell: the 4+1 desk layout
(S centre, G/Q/P/V corners), the sealed Nine Invariant Lines, the sign grammar,
the hash-chained formation ledger, the correspondence lock, and a written case
study. It is not a network service and exposes no server or endpoint.

## What is never committed

- `state/` — the live formation ledger (`gates.jsonl`, `trail.jsonl`) is
  runtime state, hash-chained, and human-attested; it is gitignored.
- `__pycache__/`, `*.pyc`, and Python bytecode.
- `.env`, credentials, tokens, and any secret material.
- Backups and deployment snapshots (`.bak*`, `backup-*`, `.guide-backups/`).

If you find a secret or credential in the repository, report it (below) and
treat it as compromised.

## Guard rails that are enforced, not advisory

- **The centre is human-planted.** `bin/cell-plant` and `bin/cell-attest`
  refuse to run without a human TTY (they exit RC=4 off a TTY). No machine can
  type an attestation.
- **The correspondence lock.** `skills/5qln-lock/lock.py` verifies a desk's
  `SYSTEM.md` / `AGENTS.md` against the pinned codex (equations, corruption
  line, course, §3.6 surface) and refuses to operate on drift (exit 1). It
  verifies; it never silently repairs.
- **The ledger is hash-chained.** Each gate record carries the previous
  record's hash, so a tampered or reordered trail fails to verify from a cold
  start.

## Reporting a vulnerability

Use the repository's **Security** tab and GitHub Private Vulnerability Reporting
when available. If a private report cannot be opened, contact
[@5qln](https://github.com/5qln) privately before public disclosure; do not
publish an unpatched vulnerability in a public issue.

Include the commit/version, operating environment, reproduction steps, impact,
and any proposed mitigation. Exclude private source material and credentials.
