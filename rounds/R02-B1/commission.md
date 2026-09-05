# COMMISSION — R02 · B1 the read-only walker

*Written by Hermes (`herdr`) on 2026-08-27 before anything is authored. A file, never chat. This
document is dsh's whole world for this round. Nothing outside it is required, and nothing inside it
may be widened.*

- **Canon this commission quotes:** `5qln/5qln-herdr-plugin` → `docs/fractal-herdr/PRD.md`,
  sha256 `71ce2645078dd48f56fb7c2a8d916a1ffa70cb0db2bd74648093c8add8b1d99c` (commit `e50eb25`).
  The box copy at `/home/deploy/Asdh5/fractal-herder/PRD.md` is byte-identical — drift check
  *in sync* 2026-08-27 15:18 UTC. Quote from either; they are the same bytes.
- **Round budget:** one authoring generation. Exceeding it is a HOLD surfaced to Amihai, never a
  silent continue.
- **Author:** dsh. **Verifier:** Hermes (`herdr`) with `/opt/data/tools/deliverable-audit/`.
  **Attester:** Amihai, at a TTY, at the end.
- **Predecessor:** R01 (B0) is **attested and closed**. Its module is canon and this round *imports*
  it — B1 never re-implements a chain, a validator, or a writer.

---

## 1. What to build (one paragraph, no doctrine)

Three modules and their selftests: (a) an **`instrument` adapter** — a raw herdr unix-socket client
whose every call goes through one chokepoint with a **read-only method allowlist**, which resolves
desks by **pane label** on every use (never by remembered `pane_id`) and reconnects and re-resolves
after a socket error; (b) a **three-dialect mapper** — pure functions that turn each runtime's native
"needs a human" signal into one `BLOCKED` verdict, with the cell's `MOVING` axis verdict dominating;
(c) a **read-only poll loop** that, tick by tick, reads the arrangement, asks B0's `tail_record()` for
the phase, observes each desk, reconstructs the cycle a human drove at the desks, and appends exactly
one `held-pending` record per blocked episode through B0's writer. Nothing else: no prompting, no
`agent.start`, no pane writes of any kind, no gate advance, no attestation, no descent, no Pi process,
no dsh relay, no scheduling daemon, no network beyond the local unix socket.

---

## 2. Acceptance criteria — quoted verbatim from the PRD

> ### B1 — The read-only walker
> Build: the `instrument` adapter (raw socket client, label-resolved desks); the poll loop; the
> three-dialect mapper — **no writes to any pane**.
> **Done when:** a human-driven cycle at the desks is fully reconstructed from polling alone; every
> `blocked` in any dialect appears as exactly one `held-pending` record; zero pane writes in the
> audit.

| ID | Criterion, as written | The dimension it is judged in |
|---|---|---|
| **C1** | a human-driven cycle at the desks is **fully reconstructed from polling alone** | completeness of the *reconstruction* — the sequence of desk states and the cycle it implies — from read calls only; not "the loop ran without crashing" |
| **C2** | every `blocked` in **any** dialect appears as **exactly one** `held-pending` record | one record per blocked **episode**, in **all three** dialects, and still exactly one **after a cold restart** (§4.5: re-arm from the ledger, never from RAM) |
| **C3** | **zero pane writes** in the audit | the *set of methods actually sent to the socket* during a full run, plus a static read of the artifact — not a promise in a docstring |

The §9 build list names three components; each is a first-class deliverable and is judged as a claim:

| ID | Requirement, as written | Where |
|---|---|---|
| **K1** | "the `instrument` adapter (**raw socket client, label-resolved desks**)" | §9 B1 build list |
| **K2** | "**the poll loop**" — as §4.3 specifies it, quoted below | §9 B1, §4.3 |
| **K3** | "the **three-dialect mapper**" — all three runtimes of §4.4, plus the cell's `MOVING` | §9 B1, §4.4 |

One row of the failure-mode table is assigned to **B1 by the PRD itself**, so it is a criterion here:

> | herdr server restart | socket error | reconnect; `live_handoff` preserves panes; re-resolve labels | B1 |

| ID | Criterion | The dimension it is judged in |
|---|---|---|
| **C4** | on a socket error the adapter **reconnects and re-resolves labels** | a desk followed by *label* across a server restart that re-mints pane ids — proven against changed ids, not against a reconnect that happens to see the same ids |

And one conformance test of §10.1 has this round's mapper as its subject:

> | T-O5-02 | O5 | the machine never resolves a hold | fuzz all three dialects → BLOCKED, never auto-attest |

| ID | Claim | Judged as |
|---|---|---|
| **K4** | fuzzing all three dialects yields `BLOCKED` / no-verdict and **never** `attested`, and no code path this round can set `attestation_ref` | exhaustive fuzz of the mapper + a static audit that `attestation_ref` is never assigned a non-null value anywhere in the artifact |

### Supporting text, also verbatim — the code must satisfy all of it

> **§4.2** | `BLOCKED` | any dialect says "needs a human" (§4.4) | records `state: held-pending`,
> surfaces, **moves on to other work** | one held record | `ATTESTED` on the human's word |

> **§4.3 The poll loop (concrete)**
> ```
> every TICK (default 3s, backoff ×2 to 30s when nothing changes):
>   1. read the arrangement (which block sits at which desk)      # never cached across restarts
>   2. for each active cell (address word):
>        a. ledger.tail()        -> current gate, current state   # the ONLY source of phase truth
>        b. if awaiting desk:    agent.get(pane) / pane.read      # heuristic state, fenced (§4.5)
>        c. if desk done:        read output -> propose gate record
>        d. if any dialect says blocked -> BLOCKED (one record, then continue)
>   3. flush: append-only write + fsync, single writer process
> ```
> **Never:** a sleep-until-done that blocks the whole field; a prompt sent without first asserting
> the target pane's **label** (§6.1 pitfall); a gate advanced from memory rather than from the
> ledger.

> **§4.4 Three dialects → one `BLOCKED` (E5, made operational)**
>
> | Runtime | Native signal | How the conductor sees it | Mapped to |
> |---|---|---|---|
> | **herdr** | `agent_status: blocked` | `agent.get` / `agent.wait --until blocked` (polled) | `BLOCKED` + record `state: held-pending` |
> | **Pi** | tool returns `terminate: true`, or `ctx.ui.confirm` | RPC `get_state` / turn end with terminate | same |
> | **dsh** | gate state `held-pending`; approval fails closed | relay `held SID` / `status SID` | same |
> | **the cell** | `MOVING` axis verdict | axis check at a return gate | `BLOCKED` — **MOVING dominates**, stop-and-surface |

> **§4.5** Re-arm from the ledger, never from RAM. On boot the conductor replays the ledger, verifies
> the hash chain, and reconstructs its state; **anything not in the ledger did not happen.**

> **§4.7 What the conductor may never do.** 1. Write to the podium pane (`pane.send_text/input/keys`
> at the centre is the forbidden path). 2. Type, imply, or infer an attestation — or convert a
> run-verdict into per-gate truth. 3. Promote a `TENTATIVE` node… 5. Store reconstructable content in
> the ledger (references only).

> **§10.2 Red-team list.** …Can a hook trigger `agent.prompt`? …Can a re-minted pane id send a G
> prompt to the V desk? …

> **§5.1** | `state` | `attested` \| `held-pending` \| `mechanical` | ✔ | three-valued; **only a human
> moves a gate out of `held-pending`** |

### The commissioner's operational reading of "exactly one" — implement exactly this

"Every `blocked` … appears as exactly one `held-pending` record" is judged per **episode**, defined
here so the criterion is measurable as written:

- An **episode** for a desk begins at the first poll whose dialect verdict is `BLOCKED` and ends at
  the first later poll for that same desk whose verdict is not `BLOCKED`, **or** at a human
  attestation record for that address+gate. Ten consecutive polls that all see `blocked` are **one**
  episode ⇒ **one** record.
- A new `BLOCKED` after the episode closed is a **new** episode ⇒ a second record. That is not a
  duplicate.
- **The open/closed state of an episode is derived from the ledger, never from RAM.** A cold restart
  mid-episode must not write a second record. The ledger's own tail for that address is the authority
  (`tail_record()` and, if you need more than the tail, `LedgerLoader.load()`).
- Two dialects reporting blocked for the **same desk at the same episode** is one hold, not two.
  Dialect identity belongs in `payload_ref` (a reference, never content).

If you judge this reading wrong, do **not** silently implement something else: implement it and raise
`HOLD` with your argument. The criterion match is what this round is measured on (lens 1).

---

## 3. Verified-facts block — executed on the live box today. Do not re-derive, do not re-probe.

Everything in this section was executed against the running instrument on 2026-08-27 between 15:19
and 15:34 UTC, read-only. It cost this round's probing budget; spending it again is spending twice.

### 3.1 Transport (this closes hold **B1-1**)

| Fact | Value | Probed |
|---|---|---|
| Socket | `/home/deploy/.config/herdr/herdr.sock` (`srw-------`, `deploy:deploy`) | live `ls` 15:19 UTC |
| Socket path env var | `HERDR_SOCKET_PATH`, injected into every plugin invocation; fall back to `~/.config/herdr/herdr.sock` | `_cell_api.py` (in service) |
| Request envelope | `{"id", "method", "params"}` — **all three required** (`request.required = [id, method, params]`), one JSON object per line, `\n`-framed | schema + live |
| Response | one `\n`-framed line; success carries `result`, failure carries `error` | live |
| `ping` result | `{"type":"pong","version":"0.8.2","protocol":20,"capabilities":{"live_handoff":true,"detached_server_daemon":true}}` | live 15:26 UTC |
| **Every result is a tagged union** keyed by `type`, and the payload sits under a **method-specific key** | `pane_list`→`panes[]` · `pane_info`→`pane` · **`pane_read`→`read`** (nested `PaneReadResult`) · `agent_list`→`agents[]` · `agent_info`→`agent` · `pane_current`→`pane` · `session_snapshot`→`snapshot` · `pane_process_info`→`process_info` | live + schema |
| Errors are structured | `{"code":"pane_not_found","message":"pane w2:p3 not found"}` · `{"code":"agent_not_found","message":"agent target pi not found"}` | live 15:34 UTC |
| Existing minimal client (the transport is solved — read it, do not depend on it) | `/home/deploy/the-cell/plugin/bin/_cell_api.py`, 4 360 B: `call(method, params) -> result`, `CellApiError`, `socket_path()`, 15 s timeout | read 15:19 UTC |

**Read-only methods and their exact parameter names** (`*` = required; the whole surface is 91
methods — these are the ones this round may touch):

| Method | Params | Result |
|---|---|---|
| `ping` | `{}` | `pong` |
| `pane.list` | `{workspace_id?: string\|null}` | `pane_list.panes[] : PaneInfo` |
| `pane.get` | `{pane_id*}` | `pane_info.pane : PaneInfo` |
| `pane.read` | `{pane_id*, source*, format?: "text"\|"ansi", lines?: int\|null, strip_ansi?: bool}` | `pane_read.read : PaneReadResult` |
| `pane.process_info` | `{pane_id?}` | `pane_process_info.process_info` |
| `pane.current` | `{caller_pane_id?}` | `pane_current.pane` |
| `pane.layout` \| `pane.edges` \| `pane.neighbor` | geometry, read-only | — |
| `agent.list` | `{}` | `agent_list.agents[] : AgentInfo` |
| `agent.get` | `{target*}` | `agent_info.agent : AgentInfo` |
| `agent.read` | `{target*, source*, format?, lines?, strip_ansi?}` | read result |
| `tab.list` `{workspace_id?}` · `workspace.list` `{}` · `session.snapshot` `{}` | inventory | — |
| `events.subscribe` | `{subscriptions*: [Subscription]}` | subscription stream |
| `events.wait` | `{match_event*: EventMatch, timeout_ms?}` | one event |
| `pane.wait_for_output` | `{pane_id*, source*, match*: {type:"substring"\|"regex", value*}, lines?, strip_ansi?=true, timeout_ms?}` | matched read |

`ReadSource` enum: `visible` · `recent` · `recent_unwrapped` · `detection`. `ReadFormat`: `text` ·
`ansi`. `AgentStatus`: `idle` · `working` · `blocked` · `done` · `unknown`.

**`PaneReadResult`** — all eight fields required: `pane_id`, `workspace_id`, `tab_id`, `source`,
`format`, `text`, `truncated`, `revision`.

**`PaneInfo`** — required: `pane_id`, `workspace_id`, `tab_id`, `terminal_id`, `agent_status`,
`focused`, `revision`. Optional/nullable: `label`, `title`, `terminal_title`,
`terminal_title_stripped`, `agent`, `display_agent`, `agent_session`, `cwd`, `foreground_cwd`,
`scroll`, `state_labels` (map string→string), `tokens`.

**`AgentInfo`** = `PaneInfo`'s fields plus `name`, `interactive_ready`, `launch_pending`,
`screen_detection_skipped`, `state_change_seq` (default 0).
**`AgentSessionInfo`** = `{source, agent, kind, value}`; live: `{"source":"herdr:pi","agent":"pi",
"kind":"path","value":"/home/deploy/.pi/agent/sessions/--home-deploy-the-cell--/2026-08-25T12-49-40-544Z_01a038f8-….jsonl"}`.

**Trap, executed:** `agent.get` / `agent.read` take `target` — and **`target` is a `pane_id`**.
`{"target":"w8:p3"}` returns the agent; `{"target":"pi"}`, `{"target":"term_659dc5a4b9c8f10"}` and
`{"target":"G"}` all fail `agent_not_found`. The obvious guess (the agent's name) is wrong.

### 3.2 The desks, live — this closes hold **B1-2**

`pane.list` at 15:26 UTC, the whole live surface (six panes, two workspaces):

| pane_id | label | agent | agent_status | terminal_title | revision |
|---|---|---|---|---|---|
| `w7:p1` | **`null`** | null | `unknown` | `deploy@srv1707555: ~` | 1 |
| `w8:p2` | `podium` | null | `unknown` | null | 0 |
| `w8:p3` | `G` | `pi` | `idle` | `π - the-cell` | 2 |
| `w8:p5` | `Q` | null | `unknown` | `deploy@srv1707555: ~/the-cell` | 1 |
| `w8:p4` | `V` | null | `unknown` | `deploy@srv1707555: ~/the-cell` | 1 |
| `w8:p6` | `P` | null | `unknown` | `deploy@srv1707555: ~/the-cell` | 1 |

1. **The desk label key is `PaneInfo.label`** (`string|null`). Not `title` (null on every live pane),
   not `terminal_title` (the shell prompt, or the agent's own title `π - the-cell`), not
   `display_agent` (null everywhere), not `state_labels`/`tokens` (**null on every live pane — do not
   build on them**).
2. **Pane ids are volatile.** `cell.layout.export.json` on disk records these same desks as
   `w2:p3 (G) · w2:p5 (Q) · w2:p4 (V) · w2:p6 (P)`; **live they are `w8:*`**. A remembered id is
   already wrong on this box: `pane.get {"pane_id":"w2:p3"}` → `pane_not_found` (executed). The label
   is the only stable handle — resolve it every tick (K1, C4, and §10.2's re-minted-id question).
3. **A pane with `label: null` exists and is not a desk** (`w7:p1`, Amihai's own shell, another
   workspace). Filter by resolved label **within the cell's own workspace**; never index a null label,
   never assume workspace `w2`, never assume a fixed workspace id at all — derive it from the labels
   you resolve.
4. **Labels are presentation and may be renamed at will** (Amihai's standing direction, recorded in
   `STATE.md`): `cell.layout.export.post-swap.json` labels the centre `THE QUESTION` where the live
   cell says `podium`. Therefore the **label → desk map is data — one config table, one place to
   change — never a string literal in logic.** The ledger keeps the codex letters `x y z a b` and the
   address alphabet `{S,G,Q,P,V}` no matter what a pane is called. A relabelled pane must not be able
   to change what a record means.
5. **`agent_status: "unknown"` is the live normal for a bare desk** — three of the four desks report
   it right now. It must never read as `idle`, `done`, or "clean" (lens 3: absence is not validity).
   Only `w8:p3` carries an agent (`pi`, `idle`).
6. The centre is `w8:p2`, label `podium`. **It is read-only forever** (§4.7.1). Reading it is allowed;
   any write path to it is the forbidden path.

### 3.3 The two event grammars — this closes hold **B1-3**

herdr 0.8.2 speaks **two** event-name dialects, and mixing them fails **silently**:

| Where | Grammar | Example | Count |
|---|---|---|---|
| manifest `[[events]] on = …` **and** `events.subscribe` (`Subscription.type`) | **DOTTED** | `pane.agent_status_changed` | 27 subscribable types |
| the push event stream (`EventKind`) **and** `events.wait` (`EventMatch.event`) | **UNDERSCORED** | `pane_agent_status_changed` | 26 kinds |

- Only **three** subscriptions carry parameters and emit a `subscription_event`:
  `pane.output_matched {pane_id*, source*, match*, lines?, strip_ansi?}` ·
  `pane.agent_status_changed {pane_id*, agent_status?}` · `pane.scroll_changed {pane_id*}`.
  The other 24 are bare `{type}`.
- `subscription_event` envelope: `{event: <dotted kind>, data: SubscriptionEventData}`.
  Push-stream envelope: `{event: <underscored kind>, data: EventData}` where `data.type` repeats the
  kind in **underscored** form.
- Status payload fields (both grammars): `{pane_id*, workspace_id*, agent_status*, agent?,
  display_agent?, state_labels?, title?}`.
- `events.wait` `EventMatch` for the status event: `{event:"pane_agent_status_changed", pane_id*,
  agent_status*}`; for output: `{event:"pane_output_changed", pane_id*, min_revision?}`.
- **An unknown event name is a NON-FATAL warning** quoting the value (`unknown event '…'`) at link /
  registry-load time. A typo therefore produces a hook that never fires and no error (lens 3). The
  cell's manifest already carries `[[events]] on = "pane.agent_status_changed"` →
  `plugin/bin/cell-on-desk-state`; **hooks are recorders, gates are the driver's job** (§4.1) — B1
  must not depend on that hook for anything.

### 3.4 Read-side observations that are traps (executed, not reasoned)

- `pane.read {"pane_id":"w8:p3","source":"visible","lines":5,"strip_ansi":true}` returned
  `truncated: true` **and** `revision: 0`, while `pane.list` reported `revision: 2` for that same
  pane in the same minute. **Do not assume `PaneReadResult.revision` is the change token.** If your
  loop uses a revision for change detection, name which field, from which call, and why — or raise a
  HOLD.
- A **`truncated: true`** read must never be treated as a desk's complete output.
- The live pane text is already non-ASCII: `"π - the-cell"`, `"↑6.0k ↓2.9k R9.7k CH5…"`. The encoding
  lens is live here, not theoretical: `∞0′ → ‖` must survive every string field you touch, and any
  byte-offset arithmetic must be byte-honest.

### 3.5 The ledger this round writes through (R01, attested — never re-implement it)

| Fact | Value |
|---|---|
| B0 module | `/home/deploy/the-cell/ledger/fractal_ledger.py`, sha256 `b291e65967e0d1f98205a9bd612507fa788ea4f9aa99e5d6b8fa5f366895546d` — byte-identical to canon `ledger/fractal_ledger.py`. Import it via `sys.path` (the `ledger/` dir sits beside `plugin/bin/`). |
| Public API | `LedgerWriter` (`append(record)` → the full 15-field record; **single-writer lock taken in the constructor**, `fsync` per append, `close()`), `LedgerVerifier(.verify())`, `LedgerLoader(.load())` → `LoadedLedger{records, head, count, index}`, `tail_record(ledger_path)`, `tail_record_id`, `RecordValidator`, `make_record(...)`, `GENESIS`, `DEFAULT_LEDGER_PATH`, exceptions `LedgerError`, `RecordValidationError`, `LedgerVerificationError`, `LedgerLockedError` |
| `append()` contract | exactly the **twelve** caller-supplied fields: `address, gate, state, mark, payload_ref, axis, axis_verdict, corruption, tentative, turn_key, block_version, attestation_ref`. The writer computes `prev_hash`, `ts`, `record_id` itself — supplying any of them is a violation. |
| `tail_record()` | reads the tail **from disk alone** at the 0/1/n-record boundaries (binary, 64 KiB window). This is your phase authority; there is no `current_phase` field anywhere. |
| The live ledger | `/home/deploy/the-cell/state/gates.jsonl` — **one** record: `gate x`, `address ""`, `prev_hash GENESIS`, `state attested`, `mark emergent`, `attestation_ref "Start from Not Knowing"`. Amihai's plant, by his hand at the TTY, 15:02 UTC. Fingerprint `6989a742f57ec60a…`. |
| **This round must not append to it** | the live chain is sacred this round. Take the ledger path as a parameter, default to `DEFAULT_LEDGER_PATH`, and let every test and demo use a scratch path. See prohibition 7. |

### 3.6 Host facts

| Fact | Value |
|---|---|
| Python | box `python3` **3.12.3**; the verifier host runs 3.13.5 → write for **3.12+, stdlib only** |
| herdr / Pi / node | herdr **0.8.2** (protocol **20**) · Pi 0.84.2 · node v22.23.2 |
| Attestation binaries | `plugin/bin/cell-plant`, `plugin/bin/cell-attest` refuse non-TTY with **RC=4** — the seal working, never to be routed around |
| Canon PRD sha256 | `71ce2645078dd48f56fb7c2a8d916a1ffa70cb0db2bd74648093c8add8b1d99c` (repo = box = wiki) |
| Desk→gate map | **Amihai's word, 2026-08-27:** `S:x G:y Q:z P:a V:b` (a gate letter *is* the phase's own validated output, `5qln.com/codex` §1.9). Hold **B1-4 is closed** — use it; do not re-derive it. |

---

## 4. Holds — declare, never guess

Write `HOLD <id>: <what you would need>` in the phase card for anything you cannot verify. A guess
that reads as a fact is the failure this whole flow exists to prevent. Carried into this round:

- **H-1 (closed, stated so you do not re-open it):** the desk labels are `PaneInfo.label`; the
  desk→gate map is `S:x G:y Q:z P:a V:b`; the event grammars are as §3.3. All three were probed or
  are Amihai's word. Do not re-derive them and do not contradict them.
- **H-2 — `block_version` for an *observed* hold.** §5.1 requires `block_version` ("which block sat
  at this desk") and `turn_key = sha256(address ‖ gate ‖ attempt ‖ block_version)`. B1 does not prompt,
  so it does not know a block version. **Do not invent a plausible block id.** Choose a value derived
  only from what you actually observed, state the derivation, and raise `HOLD H-2` with your proposal
  so the driver round (B2) inherits a decision rather than an accident.
- **H-3 — the change token.** See §3.4: two different `revision` values for one pane in one minute.
  State which field your loop trusts for "something changed", or raise the hold.
- **H-4 — Pi and dsh dialect signals are specified, not live.** There is no Pi RPC and no dsh relay
  running for this round. Their mappers must therefore be **pure functions over the signal payloads
  named in §4.4**, tested by fixture, and the phase card must say plainly that they are fixture-tested
  and not observed live. Claiming otherwise is the exact failure lens 6 exists for: an unavailable
  runtime is **INCONCLUSIVE**, never "clean".
- **H-5 — `agent.wait --until blocked` is blocking.** §4.4 names it; §4.3 forbids "a sleep-until-done
  that blocks the whole field". If you use `agent.wait`, bound it (`timeout_ms`) and say why it cannot
  stall the field — or poll `agent_status` instead and say so.
- **H-6 — arrangement, not just labels.** §4.3 step 1 says "read the arrangement (which block sits at
  which desk)". The live cell exposes a *label* per pane, and no block identity at all. Reconstruct
  what the instrument actually offers, and raise a HOLD naming what is missing for a true
  block-to-desk arrangement. Do not fabricate a block registry.

---

## 5. Prohibitions for this round

1. **No writes to any pane, by any method, anywhere in the artifact.** Forbidden literals include
   `pane.send_text`, `pane.send_input`, `pane.send_keys`, `pane.input.set`, `pane.split`,
   `pane.close`, `pane.rename`, `pane.resize`, `pane.move`, `pane.swap`, `pane.zoom`, `pane.focus`,
   `pane.graphics.*`, `pane.report_*`, `pane.release_agent`, `pane.clear_agent_authority`,
   `agent.prompt`, `agent.start`, `agent.send_keys`, `agent.rename`, `agent.focus`, `agent.view.*`,
   `layout.apply`, `layout.set_split_ratio`, `tab.*` (create/close/rename/move/focus),
   `workspace.*` (create/close/rename/move/focus/report_metadata), `worktree.*`, `plugin.*`,
   `integration.*`, `notification.show`, `popup.close`, `client.window_title.*`, `server.stop`,
   `server.reload_config`, `server.reload_agent_manifests`, `server.live_handoff`.
   **The adapter must enforce this in code**: one chokepoint, one read-only allowlist, and a call to
   anything else raises before a byte reaches the socket. C3 is judged on the methods actually sent.
2. **No write path to the podium**, in code or in an example or in a docstring (§4.7.1).
3. **No attestation, and no claim that anything ran.** The phase card carries **predictions**, never
   results. Do not write "✅", "passed", "verified", "tests green", "works". `attestation_ref` is
   `null` in every record this round can produce (K4).
4. **No gate advance.** B1 observes; it never moves a gate, never writes `state: attested`, never
   converts an observation into phase truth. The only records it appends are `held-pending` holds.
5. **No gate semantics re-implemented outside `fractal-engine`**, and no second phase/state store:
   `tail_record()` is the only source of phase truth (§10.1 T-O2-01).
6. **No re-implementation of B0.** Import `fractal_ledger`; do not copy it, wrap its chain, or write
   JSONL by hand.
7. **No writes anywhere outside** `/home/deploy/the-cell/rounds/R02-B1/authored/` and paths passed to
   your own code as parameters. **Never append to `/home/deploy/the-cell/state/gates.jsonl`** — not in
   a test, not in a demo, not "just once to check". It holds Amihai's attested plant.
8. **No git, no network beyond the local unix socket, no third-party package.** Stdlib only,
   importable as modules and runnable with `python3`.
9. **Nothing may be described as attested, decided, or verified** that this commission does not
   already mark so. `TENTATIVE` is temporal, never epistemic.

---

## 6. Deliverables, and the names the verifier will bind to

Everything goes in `/home/deploy/the-cell/rounds/R02-B1/authored/`.

1. **`instrument.py`** — the adapter (K1, C3, C4).
2. **`dialects.py`** — the three-dialect mapper (K3, K4). Pure functions, no I/O, no socket.
3. **`walker.py`** — the read-only poll loop (K2, C1, C2). Imports `fractal_ledger` and `instrument`
   and `dialects`; owns no chain logic of its own.
4. **`selftest.py`** — your tests. Each test names **which criterion ID** it exercises and **which
   quantity** it measures. A test that times something must name the operation timed.
5. **`fixtures/`** — the transcripts (see 6.2). Plain JSON, checked in as files.
6. **`phase-card.md`** — criteria by ID, the binding map below filled in with your real names,
   your **predictions** per criterion, the dialect mapping table you implemented, holds raised
   (H-2…H-6 at minimum, with your proposals), and every assumption you could not verify.
   Predictions only. No results.

### 6.1 Binding — the verifier's spec will name these; keep them or state the mapping

```
adapter_module      instrument
adapter_class       Instrument            # constructed with a socket path, nothing global
adapter_ctor_param  socket_path           # must accept ANY AF_UNIX path (this is how it is tested)
call_method         call                  # the single chokepoint: call(method, params) -> result payload
allowlist_const     READ_ONLY_METHODS     # the frozen set of permitted methods
desks_method        desks                 # -> {desk_key: pane_id}, label-resolved THIS CALL
label_map_const     DESK_LABELS           # the label -> desk config table (data, not literals in logic)
read_pane_method    read_pane             # -> the unwrapped PaneReadResult dict
desk_states_method  desk_states           # -> {desk_key: <observed state incl. agent_status>}
dialect_module      dialects
map_signal_fn       map_signal            # map_signal(dialect, payload) -> Verdict
blocked_const       BLOCKED               # the one verdict all three dialects collapse to
walker_module       walker
walker_class        Walker                # Walker(socket_path=…, ledger_path=…, …) — both parameters
tick_method         tick                  # ONE poll pass, no sleeping inside it, returns observations
reconstruct_method  reconstruct           # the cycle rebuilt from polling alone (C1)
run_method          run                   # the loop with the §4.3 tick/backoff, used only by you
```

`tick()` must be callable in a test without any sleeping: put the 3 s tick and the ×2→30 s backoff in
`run()`, and expose the schedule as a pure function or a parameter so the backoff can be asserted
without waiting minutes.

### 6.2 The fake-socket contract — how C1/C2/C3/C4 are actually judged

The verifier binds a **fake herdr server** to a scratch `AF_UNIX` path, hands it a transcript, and
points your `Instrument` at it. It replays this contract:

- reads one `\n`-framed JSON request `{"id","method","params"}`;
- **records the method name** (this log is C3's evidence — zero pane writes means this log contains
  only allowlisted read methods);
- answers with one `\n`-framed `{"id": <echoed>, "result": {…}}` from the transcript, or
  `{"id": <echoed>, "error": {"code":…, "message":…}}`;
- for C4 it **closes the connection mid-run** and comes back with **re-minted pane ids** (`w2:*` →
  `w8:*`, the real observed shift), same labels. Your adapter must reconnect, re-resolve by label, and
  keep following the same desks.

Your own `selftest.py` should carry its own fake server of the same shape — write it so a test can
drive a full human-driven cycle deterministically, with **no sleeping and no live socket**. Your tests
must not require the live cell; the live cell is the verifier's tier, not the author's.

The transcript of the human-driven cycle to reconstruct (C1) must at minimum contain: the plant
already in the ledger (`gate x`, `address ""`, attested) → a desk going `working` → the same desk
going `idle` with new output → a second desk reporting `blocked` → a third desk reporting `unknown`
throughout → an attestation record appearing in the ledger → the blocked desk leaving `blocked`.
Reconstruction means: from polls alone, your walker can state which desk was in which state in which
order, and which gate the ledger says the cell stands at — with no pane write and no invented state.

---

## 7. Budget

One authoring generation for this round. Corrections after the evidence record are limited to two,
each surgical (exact command, traceback, bytes, hashes). Exceeding either limit is a HOLD surfaced to
Amihai, never a silent continue.
