# EVIDENCE — R02 · B1 the read-only walker (PRD §9 B1, §4.3, §4.4, §10.3)

*Written by `deliverable-audit` (the verifier side), by **running** the authored artifact. This file is the only place where "it works" may be said, and only next to the command that proved it. "Looks correct" is not a verdict here.*

## Environment

- when: `2026-08-27T16:51:24Z` · harness `deliverable-audit 1.0.0`
- host: `918576e4db0d68` · Linux-6.12.91-fly-x86_64-with-glibc2.41 · python `3.13.5`
- artifact under test: `/opt/data/tmp/r02-b1/walker.py`
- artifact sha256: `5889160a15c5bc6949c6cd65726aeb609d4ca54efa3f2702229da5a675a002e9`
- criteria spec: `/opt/data/tools/deliverable-audit/specs/b1-walker.json`
- scratch (ledgers written during the run): `/tmp/deliverable-audit-nzt5298e`
- criteria quoted from: docs/fractal-herdr/PRD.md §9 B1 + §4.2/§4.3/§4.4/§4.5/§4.7/§10.1/§10.3, canon sha256 71ce2645078dd48f56fb7c2a8d916a1ffa70cb0db2bd74648093c8add8b1d99c (commit e50eb25) — quoted verbatim below. The herdr dialect the fixture speaks was probed live on herdr 0.8.2 / protocol 20 on 2026-08-27 15:19–15:34 UTC.
- total runtime: **5.01 s**  ✅ under the 60 s T0 bar

## Per-criterion result (§9 as written)

| ID | Criterion (verbatim) | Command | Raw output (decisive lines) | Verdict |
|---|---|---|---|---|
| C1 | a human-driven cycle at the desks is fully reconstructed from polling alone | `8 frames × tick() then reconstruct() on /tmp/deliverable-audit-nzt5298e/c1.sock` | tick 0 sees no blocked desk and no working desk=True; tick 1 sees G working=True; tick 2 sees G's new output (the end marker reached the observation)=True; tick 2 no longer sees working=True; ticks 3-5 see the desk blocked=True; tick 6 no longer sees a blocked desk=True; tick 7 sees the desk blocked again=True; every … | **PASS** |
| C2 | every `blocked` in any dialect appears as exactly one `held-pending` record | `frames 0-4 in one process; a second process re-polls frame 4; frames 5-6 release; a human attestation record is appended; frame 7 blocks again` | episode 1 open after 3 blocked polls: held-pending=1; after a cold restart on the same blocked desk=1; after the desk cleared with no human word=1; after the attestation and the second block: held-pending=2 (episodes in the timeline=2); states written=['attested', 'held-pending'] | **PASS** |
| C3 | zero pane writes in the audit | `8 frames × tick(); then call('pane.send_text', …) on the adapter` | write methods that reached the socket=none; methods sent=['agent.get', 'pane.get', 'pane.list', 'pane.read']; static write literals in the shipped modules=none; named in the author's own negative tests (allowed)=none; chokepoint refused before the wire=True | **PASS** |
| C4 | herdr server restart \| socket error \| reconnect; live_handoff preserves panes; re-resolve labels \| B1 | `desks(); server drops the connection and re-mints pane ids (w2:* → w8:*); desks()` | before={"G": "w2:p3", "P": "w2:p6", "Q": "w2:p5", "S": "w2:p2", "V": "w2:p4"}; after={"G": "w8:p3", "P": "w8:p6", "Q": "w8:p5", "S": "w8:p2", "V": "w8:p4"}; new connection=True; last error=none | **PASS** |

## Claimed capabilities (asserted by the author, measured here)

| ID | Criterion (verbatim) | Command | Raw output (decisive lines) | Verdict |
|---|---|---|---|---|
| K1 | the `instrument` adapter (raw socket client, label-resolved desks) | `READ_ONLY_METHODS; DESK_LABELS; desks(); read_pane()` | allowlist=['agent.get', 'agent.list', 'agent.read', 'events.subscribe', 'events.wait', 'pane.current', 'pane.edges', 'pane.get', 'pane.layout', 'pane.list', 'pane.neighbor', 'pane.process_info'] …; outside the read surface=[]; desks={"G": "w8:p3", "P": "w8:p6", "Q": "w8:p5", "S": "w8:p2", "V": "w8:p4"}; read={"pane_id… | **PASS** |
| K2 | the poll loop — every TICK (default 3s, backoff ×2 to 30s when nothing changes) … ledger.tail() -> current gate, current state # the ONLY source of phase truth | `5 × tick() timed; ledger advanced to gate y; a new process reports the phase` | 5 ticks=0.006 s; unchanged sequence from base 3.0=[6.0, 12.0, 24.0, 30.0, 30.0, 30.0]; reset on change=3.0; phase seen by a fresh process={"tick": {"tick": 1, "ts": "2026-08-27t16:51:20.978356+00:00", "monotonic_s": 0.0019516499996825587, "phase": {"source": "tail_record", "tail_record_id": "b16e4 | **PASS** |
| K3 | the three-dialect mapper — herdr `agent_status: blocked` · Pi `terminate: true` or `ctx.ui.confirm` · dsh gate state `held-pending` · the cell's `MOVING` axis verdict → BLOCKED, MOVING dominates | `map_signal(dialect, payload) over §4.4's four runtimes` | herdr blocked→BLOCKED via {"agent_status": "blocked"}; pi blocked→BLOCKED via {"terminate": true}; dsh blocked→BLOCKED via {"gate_state": "held-pending"}; cell blocked→BLOCKED via {"axis_verdict": "MOVING"}; herdr clear→not blocked (clean); pi clear→not blocked (clean); dsh clear→not blocked (clean); cell clear→not bl… | **PASS** |
| K4 | T-O5-02 \| O5 \| the machine never resolves a hold \| fuzz all three dialects → BLOCKED, never auto-attest | `16 fuzz payloads × 7 dialects; AST scan; 8-frame run` | verdict leaks toward attested=none; payloads that raised=0; static attestation_ref assignments=none; states the walker wrote=['held-pending']; non-null attestation_ref written=none | **PASS** |

`INCONCLUSIVE` is a legitimate verdict. A blind tool must never report clean.

## Six-lens pass

| Lens | Applied how | Result |
|---|---|---|
| L1 criterion match | criterion ids named=['C1', 'C2', 'C3', 'C4', 'K1', 'K2', 'K3', 'K4']; `.tick(` calls=19; frame advances=11; record counting=True; request-log assertions=True | **PASS** |
| L2 invariant end-to-end | verified 2 records from GENESIS; records=2; prev_hash=GENESIS count=1; held-pending=1; states=['attested', 'held-pending']; stray files=none | **PASS** |
| L3 absence vs validity | empty pane list: holds=0 tick_raised=True loop_survived=True invented-desk=False; null labels: holds=0 tick_raised=True loop_survived=True resolved-from-null=False; unknown status: holds=0 tick_raised=False loop_survived=True idle/done claimed=False; truncated read: holds=0 tick_raised=False loop_survived=True complete-claim=False truncation-marked=True; fixtures checked=yes empty=none | **PASS** |
| L4 encoding ∞0′ → ‖ | stress in observation=True; mojibake=False; ledger bytes=1060; records readable=True; holds=1 | **PASS** |
| L5 cold restart (a second process) | single process: holds=1 records=2; split at frame 5: holds=1 records=2; child=ok | **PASS** |
| L6 blind tool = INCONCLUSIVE | pane.read forced to fail: surfaced=True claims_clean=False holds written=0; phase card declares fixture-only=True; overclaims live=False; verdicts in this run=['PASS'] | **PASS** |

## Timings (T0 mechanical)

| Step | Seconds |
|---|---|
| C1 the cycle reconstructed from polling alone | 0.26 |
| C2 one held-pending record per blocked episode, across a restart | 0.33 |
| C3 zero pane writes — measured on the wire and in the source | 0.31 |
| C4 a socket error reconnects and re-resolves labels over re-minted pane ids | 0.25 |
| K1 the adapter: read-only allowlist, labels as data, desks resolved per call | 0.25 |
| K2 the poll loop: no sleeping in a tick, the §4.3 schedule, phase from the ledger alone | 0.31 |
| K3 every dialect's native signal collapses to one BLOCKED | 0.00 |
| K4 no fuzz, no code path, and no written record resolves a hold | 0.29 |
| L1 criterion match | 0.00 |
| L2 invariant end-to-end | 0.25 |
| L3 absence vs validity | 1.52 |
| L4 encoding ∞0′ → ‖ | 0.25 |
| L5 cold restart (a second process) | 0.69 |
| L6 blind tool = INCONCLUSIVE | 0.25 |
| **total** | **5.01** |

## Verdict

**PASS** — PASS 14

A FAIL is not a rewrite request: it is one correction, surgical, with the exact command, the raw output and the bytes that differ.


---

# Verifier's additions — executed facts the harness cannot know

*Written by Hermes (`herdr`), the non-author, 2026-08-27. Everything below was run, not read.*

## 1. The round's accounting

| Item | Value |
|---|---|
| Commission | `rounds/R02-B1/commission.md`, sha256 `af54b3de92ce9f12…` (30,594 B) |
| Authoring | dsh, **one generation**, `deepseek-v4-pro` reasoningEffort max (verified in the run's own session transcript: 30/30 model calls), 15:35:33 → 16:11:20 UTC, rc=0 |
| Correction 1 | `correction-1.md` `fdad7e182f3532d9…` — the dsh `held` predicate. 16:32:40 → 16:33:58 UTC (78 s), rc=0 |
| Correction 2 | `correction-2.md` `e9b06394ca5d8d53…` — the request `id` type. 16:46:17 → 16:48:12 UTC (115 s), rc=0 |
| Corrections used | **2 of at most 2.** A third would have been a HOLD to Amihai, not an attempt |
| Artifact as finally judged | `instrument.py` `c511a4840e464b30…` · `walker.py` `5889160a15c5bc69…` · `dialects.py` `9ebc6d314bd265e5…` · `selftest.py` `1fff9746950f3ce0…` · `phase-card.md` `aeaa00fc0e929f27…` |
| Untouched by correction 2, as required | `walker.py` and `dialects.py` — byte-identical hashes before and after |
| Audit runtime | **5.01 s** — the whole T0 tier far under the 60 s bar |

## 2. The live tier — the walker on Amihai's own cell (T3, read-only)

This is the one thing no fixture can prove, and it is where the round's real defect surfaced.

```
$ bash /home/deploy/the-cell/rounds/R02-B1/verify-live.sh

=== 1. the author's own tests, run here on the box ===
Ran 24 tests in 2.239s
OK

=== 3. the walker polling YOUR live cell — 3 ticks, reads only ===
tick 1  phase=x/attested  S(podium)@w8:p2 unknown - | G(G)@w8:p3 idle - | Q(Q)@w8:p5 unknown - | P(P)@w8:p6 unknown - | V(V)@w8:p4 unknown -
tick 2  phase=x/attested  S(podium)@w8:p2 unknown - | G(G)@w8:p3 idle - | Q(Q)@w8:p5 unknown - | P(P)@w8:p6 unknown - | V(V)@w8:p4 unknown -
tick 3  phase=x/attested  S(podium)@w8:p2 unknown - | G(G)@w8:p3 idle - | Q(Q)@w8:p5 unknown - | P(P)@w8:p6 unknown - | V(V)@w8:p4 unknown -

reconstructed from polling alone:
  ticks: 3  holds appended: 0

=== 4. your plant, after (must be the same hash, still 1 record) ===
6989a742f57ec60a54d44062bad3fe9c6d2df28e66e92de96c1336be3a6539c3   1
```

Read as plainly as it can be put: the walker found all five desks **by their labels** on the live
instrument, resolved them to the live pane ids (`w8:*`, not the `w2:*` on disk), read the real
`agent_status` of each (`G` carries Amihai's `pi` and is idle; the other three desks are bare and read
`unknown`, never idle), took the phase from **his own attested plant** (`gate x`, `attested`), held
nothing because nothing was blocked, and wrote not one byte to his ledger or to any pane.

## 3. The defect the live tier caught, and the one my own fixture hid

The first audit read **13 PASS / 1 FAIL** and the corrected artifact read **14/14**. Then the walker
met the real socket and could not complete a single call:

```
instrument.HerdrProtocolError: response id '' does not echo request id 1
```

Probed live, read-only, five requests (`ping`), the raw first bytes of each response:

```
request id='1'      -> id='1'      keys=['id','result']
request id='abc123' -> id='abc123' keys=['id','result']
request id=''       -> id=''       keys=['id','result']
request id=7        -> id=''       keys=['error','id']   {"id":"","error":{"code":"invalid_request",…
request id=None     -> id=''       keys=['error','id']   {"id":"","error":{"code":"invalid_request",…
```

**herdr requires the envelope's `id` to be a JSON string.** The adapter used
`itertools.count(1)` — integers — so the server refused every request before dispatch, and the
adapter's (correct, strict) id-echo check reported it honestly. Fix: `str(next(self._ids))`.

**And the reason 14/14 could be read while this was true: both fake servers echoed whatever id they
were handed.** The author's did, and *mine did* — my fixture encoded my assumption instead of the
observed dialect, and the commission's facts block never stated the id's type because `_cell_api.py`
happens to use a hex string and I never probed a non-string id. The verifier's fixture was corrected to
refuse a non-string id exactly as the live server does; re-run against the *uncorrected* adapter it
reads **6 INCONCLUSIVE + 3 lens FAIL** — the socket criteria become unmeasurable, which is the truthful
verdict. The fact is now in `FACTS.md` so it is never re-derived.

The lesson, recorded because it will recur: **a fixture is a claim about reality and must itself be
probed.** T0–T2 can only ever be as true as the dialect they speak.

## 4. The author's own suite, executed here (nothing below T3 is taken on trust)

```
Ran 22 tests  OK      # as authored
Ran 23 tests  OK      # after correction 1 (falsy `held` coverage)
Ran 24 tests  OK      # after correction 2 (a non-string id must be refused by the fixture too)
```

A green author suite is a hypothesis. It is recorded here as one — and this round is the proof: 23
green tests coexisted with an adapter that could not talk to the instrument at all.

## 5. The write fence (the author ran with `danger-full-access`; the fence replaced it)

```
whole round, first baseline (before any dsh run) vs now:
  the ONLY additions are the four files the verifier wrote into the round dir —
  correction-1.md, correction-2.md, evidence.md, verify-live.sh.
  No file outside ./authored/ was modified or deleted by the author across the authoring run
  and both corrections.
live ledger: 6989a742f57ec60a54d44062bad3fe9c6d2df28e66e92de96c1336be3a6539c3, 1 record —
  byte-identical from before the round to after the live run. Amihai's plant was never touched.
```

(One benign side effect, recorded: importing the attested B0 module wrote
`ledger/__pycache__/fractal_ledger.cpython-312.pyc`. No source byte changed; the cache was removed.)

## 6. The verifier was itself proven before it judged (builder ≠ verifier, applied to the tools)

The B1 audit pack is new code, so it was accepted the way an artifact is: run against a walker that
meets the criteria and one with eight injected defects, requiring that **every** criterion, claim and
lens separate them and **name** the defect.

```
$ python3 selftest_b1.py
38/38 expectations held
B1 AUDIT PACK ACCEPTED: it passes a conforming walker, fails a defective one on every criterion,
claim and lens, and names each defect.

$ python3 selftest.py      # the B0 pack, unaffected by this round's harness changes
22/22 expectations held
```

| Pack file | Lines | sha256 |
|---|---|---|
| `probes/walker_socket.py` | 1156 | `e5416a9377a32d58…` |
| `probes/fake_herdr.py` | 437 | `c5bc3cd80eae9e41…` |
| `lenses_b1.py` | 511 | `847d966e18727f90…` |
| `specs/b1-walker.json` | 98 | `5dcaeb6b47edae0c…` |
| `selftest_b1.py` | 103 | `9e5eb42bcb8b38d0…` |

Seven probe defects were found and fixed **in the verifier, not asked of the author**: a negative test
must be allowed to name a forbidden method; B0's `.lock` file is not a second state store; a rewound
timeline is not a cold restart; a `Verdict` dataclass is not a string; a key *named* `blocked` is not a
blocked desk; the ledger's phase legitimately still reads `held-pending` after a desk clears; and the
fake server must refuse a non-string id. Each was the probe measuring the wrong thing — recorded
because a verifier that silently adapts to the artifact is no verifier.

## 7. A correction to the commission's own reading — HOLD H-7, accepted as the author wrote it

dsh raised **HOLD H-7** against the commission's operational reading of "exactly one". The commission
said an episode ends "at the first later poll whose verdict is not BLOCKED, **or** at a human
attestation record" *and* that open/closed state must be "derived from the ledger, never from RAM".
Those cannot both hold: a poll-side closure is not ledger-representable when the round may append only
`held-pending` records, so deriving it at all means holding it in RAM — and a machine-observed release
closing a hold **is the machine resolving a hold**, which §4.2 ("surfaces, never resolves") and §5.1
("only a human moves a gate out of `held-pending`") forbid.

**The author's reading is accepted and the audit measures it:** an episode is open iff the last ledger
record for that `(address, gate)` is `held-pending`; only an attestation record for the same pair closes
it. Measured: three blocked polls → **1** record; a cold restart mid-episode → still **1**; the desk
clearing with no human word → still **1**; after an attestation record appears, a further block → **2**.

This is a **K-side reading, not doctrine.** It decides what the product does with a human's silence.
Amihai may overrule it; it is surfaced, not settled.

## 8. Carried forward (declared, never resolved by the machine)

- **H-2** `block_version` for an observed hold is `""` — "no block identity observed". B2 inherits it
  as a stated decision, not an accident.
- **H-3** no `revision` field is trusted as a change token (`pane.read` said `revision: 0` while
  `pane.list` said `2` for the same pane in the same minute).
- **H-4 / H-8 — INCONCLUSIVE, and recorded as such:** the Pi dialect, the dsh dialect and the cell's
  MOVING axis have **no live source** this round; they are fixture-tested pure functions. Nothing here
  says they work against a running Pi, a running dsh relay, or a real axis check.
- **From correction 1:** the tightened `held` predicate accepts only a non-empty **string** SID, so an
  integer SID from a real relay would not be recognised. Unverifiable while H-4 stands — carried to B2.
- **H-5** `agent.wait` is deliberately unused (it would stall the tick); the walker polls.
- **H-6** the read-only surface exposes **no block identity at all**, so §4.3's "which block sits at
  which desk" is reconstructed only as far as the instrument allows: desk ← pane label, gate ← desk. No
  block registry was fabricated.
- **New for the plan:** every fixture in this build must be probe-derived. B2's commission will carry
  the id-type fact and a rule that a fake server is validated against the live dialect before it is
  trusted.

## 9. What this evidence does *not* say

It does not say a human has driven a cycle at the desks while the walker watched — the live tier proves
the walker reads the real instrument and Amihai's real plant, not that a full human cycle was observed
in the wild. It does not say the conductor works: B1 writes no prompt and advances no gate. And it
attests nothing — the only attestation of this round is the one Amihai may write, at the TTY, in his own
hand.
