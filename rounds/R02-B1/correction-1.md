# CORRECTION 1 — R02 · B1 the read-only walker

*Surgical. Never a rewrite request. Thirteen of the fourteen judged items passed on the first
generation; this is one predicate in one file.*

## What failed

Claim **K3**, verbatim from the commission:

> the **three-dialect mapper** — herdr `agent_status: blocked` · Pi `terminate: true` or
> `ctx.ui.confirm` · dsh gate state `held-pending` · the cell's `MOVING` axis verdict → BLOCKED,
> MOVING dominates

Every blocked signal maps correctly. The failure is the inverse direction: a **non-blocked** dsh
payload produces `BLOCKED`, so the walker would append a `held-pending` record and call a human for
a desk that is not held.

## The exact evidence

```
$ cd /opt/data/tmp/r02-b1 && PYTHONPATH=. python3 -c "
import dialects
for p in ({'held': False}, {'held': None}, {'held': 'sid-42'}, {'gate_state':'running'}):
    v = dialects.map_signal('dsh', p)
    print(f'{str(p):32} -> {v.name:11} signals={v.signals} detail={v.detail!r}')"

{'held': False}                  -> blocked     signals=('dsh:held',) detail='dsh relay reported a held SID'
{'held': None}                   -> no_verdict  signals=() detail='dsh payload carries no blocked signal'
{'held': 'sid-42'}               -> blocked     signals=('dsh:held',) detail='dsh relay reported a held SID'
{'gate_state': 'running'}        -> no_verdict  signals=() detail='dsh payload carries no blocked signal'
```

The verifier's own run of the same defect:

```
$ cd /opt/data/tools/deliverable-audit && python3 audit.py --spec specs/b1-walker.json
FAIL          K3  every dialect's native signal collapses to one BLOCKED
   herdr blocked→BLOCKED via {"agent_status": "blocked"}; pi blocked→BLOCKED via {"terminate": true};
   dsh blocked→BLOCKED via {"gate_state": "held-pending"}; cell blocked→BLOCKED via {"axis_verdict": "MOVING"};
   herdr clear→not blocked (clean); pi clear→not blocked (clean);
   dsh clear→not blocked (leaks: [{"held": false}])
```

The bytes, `authored/dialects.py` lines 130–133 (sha256 of the file as audited:
`6b1a8adad12c9a1e4edb4210a40175de6e5069cca64885f729e27aa3c4d19282`):

```python
            if "held" in payload and payload["held"] is not None:
                return Verdict(
                    "blocked", (_SIGNAL_DSH_HELD,),
                    "dsh relay reported a held SID")
```

## The narrowest true statement of the defect

`is not None` is the wrong test for the thing your own phase card calls **a held SID**: `False`,
`""` and `0` are all "not None" and none of them is a session id, so a relay reporting
`held: false` — the ordinary way a relay says *nothing is held* — is read as a hold. It is the
absence-vs-validity class (lens 3), in the one direction that manufactures work for a human rather
than hiding it.

## What is NOT being asked

- **Nothing else changes.** `instrument.py` (sha256 `5563dfce…`) and `walker.py` (sha256
  `5889160a…`) passed and must not be touched. C1, C2, C3, C4, K1, K2, K4 and all six lenses passed;
  the episode reading of your **HOLD H-7 is accepted as authored** (see below) — do not revisit it.
- Do not widen the dsh dialect, do not add a dialect, do not restructure `Verdict`, do not change the
  signal names, do not change any other branch of `map_signal`.
- Ask only: what is a *usable* `held` value? Fix that one predicate, and cover the falsy cases
  (`False`, `""`, `0`, whitespace) in `selftest.py` beside the existing K3 test. Your 22 tests
  currently pass here (`Ran 22 tests … OK`, 2.26 s) and none of them exercises a falsy `held`.

## Accepted from your card, so you do not re-argue it

**HOLD H-7 is accepted.** Your reading — an episode is open iff the last ledger record for that
`(address, gate)` is `held-pending`, and only a human attestation closes it — is the one that
satisfies both "derived from the ledger, never from RAM" (§4.5) and "only a human moves a gate out of
`held-pending`" (§5.1). The commission's alternative clause (a non-blocked poll closing an episode)
would have let the machine resolve a hold, which §4.2 forbids. The commission's operational reading is
corrected to yours, and the audit now measures it that way: one hold while it stands, none added by a
cold restart, a second only after an attestation record appears for the same `(address, gate)`.

## Budget

Correction 1 of at most 2. If a second is needed after this, it is one more; a third is a **HOLD
surfaced to Amihai**, never a third attempt.
