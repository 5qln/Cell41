# R02 · B1 — phase card (authored by dsh, predictions only)

This card carries **predictions**, not results: it records no outcome of
any execution and no judgment of any criterion. A separate verifier
executes the artifact and writes the only record that counts. Where a
fact could not be established, a HOLD names what would be needed.

---

## 1. Criteria restated by ID

| ID | Criterion, as written (commission §2) | Where the artifact answers it |
|---|---|---|
| **C1** | a human-driven cycle at the desks is **fully reconstructed from polling alone** | `walker.reconstruct()` over accumulated `tick()` observations; driven by `fixtures/cycle_transcript.json` (the §6.2 minimum cycle) |
| **C2** | every `blocked` in **any** dialect appears as **exactly one** `held-pending` record | `walker._episode()`: one append per blocked **episode**, open/closed state re-derived from the ledger each tick; still one record after a cold restart |
| **C3** | **zero pane writes** in the audit | `instrument.READ_ONLY_METHODS` (frozen allowlist) enforced at the single chokepoint `Instrument.call()` before any byte is sent; runtime method log asserted in selftest; static AST single-send-site check in selftest |
| **C4** | on a socket error the adapter **reconnects and re-resolves labels** | `Instrument.call()` reconnect + retry; `desks()` re-resolves by pane label on every use; `walker.tick()` re-resolves and re-observes once when a re-minted id surfaces as `pane_not_found` |
| **K1** | the `instrument` adapter (**raw socket client, label-resolved desks**) | `instrument.py` — envelope `{id, method, params}` over `AF_UNIX`, tagged-union unwrapping, typed errors, `DESK_LABELS` data table |
| **K2** | **the poll loop** as §4.3 specifies it | `walker.tick()` (one pass, no sleeping) + `walker.run()` (3 s tick, ×2→30 s backoff as the pure function `next_delay`) |
| **K3** | the **three-dialect mapper** — all three runtimes of §4.4, plus the cell's `MOVING` | `dialects.map_signal()` + `dialects.dominant()` |
| **K4** | fuzzing all three dialects yields `BLOCKED` / no-verdict and **never** `attested`; no code path sets `attestation_ref` | `dialects.py` has no attested verdict at all; every record this round can produce carries `attestation_ref: null` |

## 2. Binding map (commission §6.1 → what I authored)

| Commission name | My name | Lives in | Notes |
|---|---|---|---|
| `adapter_module` | `instrument` | `instrument.py` | stdlib only, importable |
| `adapter_class` | `Instrument` | `instrument.py` | constructed with a socket path; nothing global |
| `adapter_ctor_param` | `socket_path` | `Instrument.__init__` | first positional + keyword; accepts **any** AF_UNIX path; fallback chain `HERDR_SOCKET_PATH` → `~/.config/herdr/herdr.sock` |
| `call_method` | `call` | `Instrument.call` | the single chokepoint: `call(method, params) -> unwrapped result payload` |
| `allowlist_const` | `READ_ONLY_METHODS` | `instrument.py` | `frozenset` of the 18 read methods of §3.1 |
| `desks_method` | `desks` | `Instrument.desks` | `-> {desk_key: pane_id}`, label-resolved on THIS call |
| `label_map_const` | `DESK_LABELS` | `instrument.py` | the label→desk **config table** (data, not literals in logic); ctor `desk_labels=` override for relabels |
| `read_pane_method` | `read_pane` | `Instrument.read_pane` | `->` the unwrapped `PaneReadResult` dict (all 8 fields validated); `desk=` resolves by label on the call |
| `desk_states_method` | `desk_states` | `Instrument.desk_states` | `-> {desk_key: observed state incl. agent_status}` |
| `dialect_module` | `dialects` | `dialects.py` | pure functions; no I/O, no socket |
| `map_signal_fn` | `map_signal` | `dialects.map_signal` | `map_signal(dialect, payload) -> Verdict`; total — never raises |
| `blocked_const` | `BLOCKED` | `dialects.py` | the one verdict all dialects collapse to; `NO_VERDICT` is its only counterpart |
| `walker_module` | `walker` | `walker.py` | imports `fractal_ledger` (B0 — never re-implemented), `instrument`, `dialects` |
| `walker_class` | `Walker` | `walker.py` | `Walker(socket_path=…, ledger_path=…, …)` — both parameters; ledger default `fractal_ledger.DEFAULT_LEDGER_PATH` per §3.5 |
| `tick_method` | `tick` | `Walker.tick` | ONE poll pass, no sleeping inside, returns the observation frame |
| `reconstruct_method` | `reconstruct` | `Walker.reconstruct` | the cycle rebuilt from polling alone (C1) |
| `run_method` | `run` | `Walker.run` | owns the §4.3 tick/backoff; `sleep_fn` injectable, `max_ticks` bounds it |
| *(schedule)* | `next_delay` | `walker.next_delay` | the ×2→30 s backoff as a **pure function** — assertable without waiting |

Extra data tables (documented, not in the binding): `walker.DESK_GATES`
(`S:x G:y Q:z P:a V:b` — Amihai's word, §3.6), `walker.DESK_ADDRESSES`
(`S` → `""`, the empty address word matching the attested plant record),
`walker.COURSE` (`S,G,Q,P,V`).

## 3. Predictions per criterion

> These are predictions about what the verifier will observe when it
> executes the artifact against its own fake socket and scratch ledger.
> None of them claims that anything already ran.

- **C1 — Prediction:** replaying `fixtures/cycle_transcript.json`
  (plant attested at `gate x` → G `working` → G `idle` with new output
  carrying the bytes `∞0′ → ‖` → Q `blocked` → P `unknown` throughout →
  a human attestation record for `G/y` appearing → Q leaving `blocked`),
  the walker's `reconstruct()` will report, from read calls alone:
  G `working→idle` with the output change flagged at tick 2; Q
  `unknown→blocked` at tick 3 and `blocked→unknown` at tick 6; P with
  zero state transitions over all six ticks; exactly one hold (desk Q,
  gate `z`); and the phase read from `tail_record()` as gate `y`,
  state `attested`, address `G`. No invented state, no pane write.
- **C2 — Prediction:** ten consecutive blocked polls for Q append exactly
  one `held-pending` record; a blocked poll after a human attestation
  record for `(Q, z)` appends a second (a new episode, not a duplicate);
  a further blocked poll appends none; a fresh **subprocess** re-armed
  from disk alone, ticking once mid-episode, appends none (still exactly
  one record); two dialects (herdr `blocked` + cell `MOVING`) firing for
  the same desk in one tick append exactly one record whose `payload_ref`
  carries both dialect references.
- **C3 — Prediction:** the fake server's method log across the full cycle
  run contains only `pane.list`, `pane.get`, `agent.get`, `pane.read` —
  a strict subset of `READ_ONLY_METHODS`; a call to any non-allowlisted
  method raises `MethodNotAllowedError` with zero bytes and zero
  connections reaching the server (also on an already-warm connection);
  the static AST read finds exactly one socket send site in the artifact,
  inside `Instrument.call()`, after the allowlist membership check, and
  none in `walker.py`/`dialects.py`.
- **C4 — Prediction:** when the fake server closes the connection
  mid-tick and returns with re-minted ids (`w2:*` → `w8:*`, same labels),
  the instrument reconnects, the next resolution returns the re-minted
  ids for the same five desk keys, the same tick completes with all
  observations on `w8:*` ids, and the following tick follows the same
  desks again.
- **K1 — Prediction:** the verifier can construct
  `Instrument(socket_path=<any AF_UNIX path>)` and observe the exact
  envelope (all three required fields, `\n`-framed), the method-specific
  payload unwrapping of §3.1, structured `{code,message}` errors mapped
  to typed exceptions, and desk resolution that filters null labels and
  derives the workspace from the labels resolved (never assuming an id).
- **K2 — Prediction:** `tick()` completes without any call to a sleep
  function; `next_delay(False, …)` yields 3→6→12→24→30→30 with a reset
  to 3 on change; `run(max_ticks=4, sleep_fn=…)` sleeps exactly
  `3, 6, 12` seconds-worth of injected calls over four unchanged ticks.
- **K3 — Prediction:** every blocked payload of each §4.4 dialect
  fixture maps to `BLOCKED`; every non-blocked, absent, junk, or unknown
  payload maps to a no-verdict; the cell `MOVING` verdict forces
  `BLOCKED` even when herdr reports idle (dominance), while a cell
  `STASIS`/absent verdict never clears a runtime `BLOCKED`.
- **K4 — Prediction:** the fuzz harness (3000+ random payloads across
  the dialects) observes only `blocked`/`no_verdict` verdicts — never an
  attestation verdict (none exists in the module); the static scan finds
  no assignment of a non-null `attestation_ref` anywhere in the authored
  sources or fixtures.

## 4. The dialect mapping table I implemented (`dialects.map_signal`)

| Dialect | §4.4 native signal | Payload shapes accepted | → Verdict |
|---|---|---|---|
| `herdr` | `agent_status: blocked` (via `agent.get` / `pane.get`, polled) | dict with `agent_status == "blocked"` (a full `PaneInfo`/`AgentInfo` dict is accepted) | `BLOCKED` (`herdr:agent_status`); anything else — `idle`/`working`/`done`/**`unknown`**/missing/non-dict — a **no-verdict** |
| `pi` | tool returns `terminate: true`, or `ctx.ui.confirm` | `{"terminate": true}` or `{"ctx": {"ui": {"confirm": …}}}` | `BLOCKED` (`pi:terminate` / `pi:ctx.ui.confirm`); anything else a no-verdict |
| `dsh` | gate state `held-pending`; approval fails closed | `state`/`gate_state`/`status` == `"held-pending"`, or `approval == "failed"`, or a non-null `held` SID | `BLOCKED` (`dsh:gate_state` / `dsh:approval` / `dsh:held`); anything else a no-verdict |
| `cell` | `MOVING` axis verdict (axis check at a return gate) | `axis_verdict`/`verdict` == `"MOVING"`, or `moving is true` | `BLOCKED` (`cell:moving`); `STASIS`/`recast`/absent a no-verdict |

**Dominance** (`dialects.dominant`): any `BLOCKED` wins — so a cell
`MOVING → BLOCKED` forces `BLOCKED` whatever the runtime dialect says,
and a cell `STASIS`/absent verdict can never clear a runtime `BLOCKED`
(§4.4 "MOVING dominates, stop-and-surface"). Blocked signal references
merge into one verdict, so two dialects reporting blocked for the same
desk in the same tick are **one** hold, with both identities in
`payload_ref` (a reference, never content).

## 5. Holds — raised, with proposals (never guessed)

- **HOLD H-2 — `block_version` for an observed hold.** Proposal: the
  empty string `""`. Derivation: B1 does not prompt, and the read-only
  surface exposes **no block identity** (see H-6) — nothing is observed
  from which a block id could be derived, and inventing a plausible id
  is forbidden. The empty string is the honest "no block identity
  observed" value: §5.1 requires the field to be a string and places no
  charset constraint, and `turn_key` is still computed over the honest
  tuple `sha256(address ‖ gate ‖ attempt ‖ "")`. A downstream reader
  must treat `""` as *nothing observed*, never as a block id (absence is
  not validity). Rejected alternative: `PaneInfo.revision` /
  `PaneReadResult.revision` — the §3.4 trap shows they are inconsistent
  and untrustworthy as identity tokens. **What I would need to close
  it:** a read-only herdr field mapping a pane/desk to a block or
  essence identity, or Amihai's word on the convention — B2 (the driver
  round) inherits this decision as stated, not as an accident.
- **HOLD H-3 — the change token.** Decision, stated: the loop trusts
  **no revision field** as a change token (pane.read `revision: 0` vs
  pane.list `revision: 2` for one pane in one minute, §3.4). "Something
  changed" for the `run()` backoff schedule is the in-process comparison
  of consecutive tick observation digests (per desk: pane_id,
  agent_status, output digest, episode state, appended record id; plus
  the tail record id). It is schedule input only — never phase truth,
  never persisted, never re-armed. Revisions are recorded in the
  observations and never trusted. A cold start has no previous digest:
  the first tick counts as changed and the schedule starts at the base
  tick. **What I would need to close it:** a documented, consistent
  revision/changestamp semantic from the herdr server (the instrument's
  own `state_change_seq` on agents is the plausible candidate).
- **HOLD H-4 — Pi and dsh dialect signals are specified, not live.**
  There is no Pi RPC and no dsh relay running this round.
  `dialects.map_signal("pi", …)` and `("dsh", …)` are **pure functions
  over the §4.4 payload shapes, tested by fixture only**
  (`fixtures/dialect_signals.json`). Their live observation status this
  round is **INCONCLUSIVE** — they are not observed live, and no claim
  of any kind is made about them. **What I would need to close it:** a
  live Pi RPC `get_state` and a live dsh `status`/`held` relay to
  observe against (the verifier's tier, not the author's).
- **HOLD H-5 — `agent.wait --until blocked` is blocking.** It is **not
  used**. §4.3 forbids a sleep-until-done that blocks the whole field,
  and even a `timeout_ms`-bounded wait would stall the one chokepoint —
  and therefore the whole tick — for its timeout on every desk. The
  walker **polls** instead: `agent.get` (with `target` = the pane_id,
  per the §3.1 trap) for panes that carry an agent, `pane.get` (whose
  `agent_status` is a required field) for bare desks — one pass per
  tick, bounded by the per-call socket timeout (15 s default), after
  which the tick moves on to the next desk. `events.wait` /
  `pane.wait_for_output` stay in the allowlist (they are reads) but are
  never called. **What I would need to close it:** a signal from the
  PRD that an event-stream subscription is the sanctioned non-blocking
  path — if so, a later round can subscribe; the loop's structure does
  not depend on it.
- **HOLD H-6 — arrangement, not just labels.** The read surface exposes
  a pane **label** per pane plus `agent_status` and pane text — and **no
  block identity at all** (nothing says which block sits at which desk).
  What the walker reconstructs is therefore: desk letter ← pane label
  (`DESK_LABELS` data), gate ← desk (`DESK_GATES`, Amihai's word),
  pane_id/workspace per tick, agent_status, output text. It does **not**
  fabricate a block registry, and it writes no block identity into any
  record (`block_version` stays `""` per H-2). **Missing for a true
  block-to-desk arrangement:** a read-only herdr field mapping a
  pane/desk to a block or essence identity, or Amihai's word on where
  the block registry lives.
- **HOLD H-7 (raised by me — episode closure by a clear poll).** The
  commissioner's operational reading says an episode "ends at the first
  later poll whose verdict is not BLOCKED, **or** at a human attestation
  record". My implementation derives open/closed **from the ledger
  alone**: an episode is open iff the last ledger record for that
  `(address, gate)` has `state == "held-pending"`; it is closed by any
  later record for that pair (a human attestation) or by absence.
  Consequence, stated: a blocked→clear→blocked sequence with **no
  attestation record between** stays **one** episode (one record),
  because this round may append only `held-pending` holds — a
  poll-side closure is not ledger-representable, and §4.5 forbids
  deriving it from RAM. Argument for this reading: it is the only one
  that satisfies "open/closed state derived from the ledger, never from
  RAM" together with "a cold restart mid-episode must not write a second
  record", and it matches "only a human moves a gate out of
  held-pending" (§5.1): a hold nobody resolved is still one hold. The
  measurable bars (ten blocked polls → one record; re-block after an
  attestation → a second record) hold under it. **What I would need to
  close it:** a ruling that a non-blocked poll may close an episode
  ledger-side, plus a record state/kind this round is permitted to write
  to represent that closure — without one, the ledger-derived reading
  above is the only cold-restart-safe implementation, and I implemented
  exactly it.
- **HOLD H-8 (raised by me — the cell's MOVING axis has no live
  source).** Like Pi and dsh, the cell's `MOVING` axis verdict has no
  live source on the read-only surface this round (no allowlisted method
  returns an axis check). The mapper and the record fields handle it
  (`axis_verdict: "MOVING"` when a cell hold is written; dominance in
  `dialects.dominant`), the walker consumes it through an optional
  `axis_provider` callable, and **with no provider the axis verdict is
  recorded as absent** — INCONCLUSIVE, never clean. Fixture-tested, not
  observed live. **What I would need to close it:** a read-only axis
  check (a herdr method or an attested file the walker may read) that
  returns the cell's current axis verdict.

H-1 is closed by the commission (labels are `PaneInfo.label`; desk→gate
map; event grammars) — accepted as stated, not re-derived, not
contradicted.

## 6. Assumptions I could not verify (and the derivation where there is one)

1. **`podium` ↔ desk S.** The commission gives the desk→gate map
   `S:x G:y Q:z P:a V:b` (Amihai's word) and the plant record `gate x,
   address ""`; the centre pane (labelled `podium` live, relabellable)
   is the only pane consistent with gate `x` — so the default
   `DESK_LABELS` maps `podium → S`. It is **data**, one place to change.
2. **Desk S's address word.** `DESK_ADDRESSES` gives S the empty address
   `""`, matching the attested plant (`gate x, address ""`); G/Q/P/V use
   their own letters. Not established against a live record for desk S.
3. **Workspace selection rule.** When desk labels appear in more than
   one workspace, the workspace holding the **most** desk panes is the
   cell's own (derived from the labels resolved, per §3.2 fact 3); an
   exact tie raises `DeskResolutionError` instead of guessing. Not
   observed against a real multi-workspace arrangement.
4. **Record field choices for an observed hold** (all validator-legal
   under §5.1, none pinned by the commission): `mark: "mechanical"`,
   `tentative: true` (machine-posed; a human converts), `corruption:
   null`, `axis` a fresh anchor anchored at `payload_ref` with
   `axis_verdict: null` for a purely runtime-dialect hold (null is only
   valid at anchored mode) and `"MOVING"` for a cell hold;
   `turn_key = sha256(address ‖ gate ‖ attempt ‖ block_version)` with
   `attempt` = count of prior ledger records for that `(address, gate)`
   + 1 — ledger-derived, so a cold restart re-derives the same key.
5. **`attempt` semantics.** "attempt" is read as the 1-based index of
   the record among that pair's records; not established against any live
   convention beyond the §5.1 formula.
6. **The ledger path default** is `fractal_ledger.DEFAULT_LEDGER_PATH`
   per §3.5; the socket default chain is `HERDR_SOCKET_PATH` →
   `~/.config/herdr/herdr.sock` per §3.1. Both are parameters; nothing
   in this round's tests ever uses either default.
7. **The allowlist is exactly the 18 methods of the §3.1 table**
   (including `events.subscribe`/`events.wait`/`pane.wait_for_output`,
   which the walker never calls). The table was taken as the complete
   read surface for this round.
8. **Simulated human records in tests keep `attestation_ref: null`**
   (the walker keys episode closure on `state == "attested"` for the
   matching `(address, gate)`, never on the ref value) — this keeps the
   artifact free of any non-null `attestation_ref` assignment (K4) while
   the §6.2 cycle still contains the required attestation record.
9. **`run()` sleeps only between ticks**; the first tick always counts
   as "changed" and starts the schedule at the base tick. A socket
   timeout (bounded, 15 s default per call) is transport reality, not a
   sleep-until-done, and is raised as a typed error after which the tick
   continues to the next desk.
10. **`truncated: true`** is forwarded into observations with
    `digest: null` and `changed_since_prev: null` — never treated as a
    desk's complete output (the walker reads full visible text; a
    truncated read is recorded, not trusted).
11. **Agentless desks read `agent_status` from `pane.get`** (a required
    `PaneInfo` field); a pane carrying an agent additionally goes through
    `agent.get` (the §4.4 path), whose value is preferred and whose
    source is recorded. A missing/non-string `agent_status` is a
    protocol error (fail closed), never "clean".
12. **Phase shape.** `tick()` reports the phase exclusively from
    `tail_record()`; at 0 records it reports `{gate: null, state: null,
    tail_record_id: GENESIS}` — an absence, never a fabricated phase.
    Per-(address, gate) episode authority comes from a
    `LedgerLoader.load(write_index=False)` replay of the same disk file.

## 7. INCONCLUSIVE — stated plainly

- **Pi dialect: INCONCLUSIVE** (no live Pi RPC this round; fixture-tested only — HOLD H-4).
- **dsh dialect: INCONCLUSIVE** (no live dsh relay this round; fixture-tested only — HOLD H-4).
- **cell MOVING axis: INCONCLUSIVE** (no live axis source on the read-only surface; provider-injected and fixture-tested only — HOLD H-8).
- **`agent_status: "unknown"`** — the live normal for three of the four
  desks — is mapped to a no-verdict and forwarded as observed; it
  is never read as idle, done, or clean.

## 8. Correction note (2026-08-27)

- The dsh `held` predicate is tightened so that only a usable SID — a
  non-empty, non-whitespace string — counts as a hold, because a falsy
  `held` (`false`, `""`, `0`, whitespace) is the relay's way of
  reporting that nothing is held, not a session id.
- (2026-08-27) The envelope request `id` is a JSON **string** — the
  monotonic counter stringified as `str(next(self._ids))`. Why: live
  herdr 0.8.2 echoes a string id verbatim and refuses a non-string id
  before dispatch with `{"id": "", "error": {"code": "invalid_request",
  …}}`, so an integer id would make every call fail at the socket. The
  strict echo check in `Instrument._decode` is kept as-is — it never
  accepts an empty or mismatched response id. Prediction: the verifier
  will observe every envelope id as a non-empty string, and the
  author-side fake server will refuse a non-string id with exactly the
  live `invalid_request` shape.
