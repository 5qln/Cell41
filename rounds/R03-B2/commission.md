# COMMISSION — R03 · B2 the driver (one cell, sequential)

*Written by Hermes (`herdr`) on 2026-08-27 before anything is authored. A file, never chat. This
document is dsh's whole world for this round. Nothing outside it is required, and nothing inside it
may be widened.*

- **Canon this commission quotes:** `5qln/5qln-herdr-plugin` → `docs/fractal-herdr/PRD.md`,
  sha256 `71ce2645078dd48f56fb7c2a8d916a1ffa70cb0db2bd74648093c8add8b1d99c` (commit `e50eb25`).
  Drift check *in sync* at the time of writing.
- **Round budget:** one authoring generation, then at most two corrections. Exceeding either is a
  **HOLD surfaced to Amihai**, never a silent continue.
- **Author:** dsh. **Verifier:** Hermes (`herdr`) with `/opt/data/tools/deliverable-audit/`.
  **Attester:** Amihai, at a TTY, at the end.
- **Predecessors, both attested and closed — you import them, you never re-implement them:**
  R01/B0 `ledger/fractal_ledger.py` (the record, the chain, the single writer, the replay) and
  R02/B1 `rounds/R02-B1/authored/{instrument,dialects,walker}.py` (the read-only adapter, the
  three-dialect mapper, the poll loop). Read `rounds/R02-B1/commission.md` §3 for the **full read
  surface** — it is canon and it is not repeated here.

---

## 1. What to build (one paragraph, no doctrine)

The **turn machine**: given a desk that the ledger says is due, the driver resolves that desk **by
label**, computes its `turn_key`, sends **one** prompt to that desk's pane, fences the answer with a
unique end marker, reads to the marker, and appends **one** proposed gate record — then refuses to
advance the gate until a human attestation record for that `(address, gate)` appears on the ledger, and
records the refusal. Around that: `turn_key` idempotency so a duplicated prompt can never produce a
second record; a **`lens` adapter** for Pi that asserts the desk is constituted (instruction + at least
one skill + tool surface + model, R4 §7) and **fails the boot closed** when that trust is missing; and
a write path that is physically incapable of touching the centre. Nothing else: no descent (B3), no
unattended accumulation of holds (B4), no held stack or run-verdict (B5), no assembly (B6), no parallel
cells, no budget accounting, and **no authoring of the desks' own instruction blocks or skills** — the
driver *consumes* an arrangement and *asserts* it; it never invents one.

---

## 2. Acceptance criteria — quoted verbatim from the PRD

> ### B2 — The driver (one cell, sequential)
> Build: prompt → fence → read → propose gate record; `turn_key` idempotency; the Pi `lens` adapter
> with the trust assertion; per-gate human attestation at the TTY.
> **Done when:** a full S→G→Q→P→V cycle is walked with the human attesting each gate; no gate opens
> without an attestation record; a deliberately duplicated prompt produces **one** record; the
> skills-loaded assertion fails the boot when trust is missing.

| ID | Criterion, as written | The dimension it is judged in |
|---|---|---|
| **C1** | a full S→G→Q→P→V cycle is walked **with the human attesting each gate** | the ledger's own record sequence across a whole cycle — gate letters in `x y z a b` order, each machine-proposed gate followed by an attestation record before the next prompt is sent. Read §2.1 below: the **S gate is the human's plant, never a machine prompt** |
| **C2** | **no gate opens without an attestation record** | an attempted advance with no attestation is **refused and the refusal is recorded** (§8: "a silent refusal is indistinguishable from a success and is therefore a bug") |
| **C3** | a deliberately duplicated prompt produces **one** record | records bearing the same `turn_key`: exactly one, proven by *re-issuing the same turn* — including after a cold restart and against an already-`working` desk |
| **C4** | the skills-loaded assertion **fails the boot** when trust is missing | the boot refuses **before the first prompt** is sent (§10.3), measured as: zero write methods on the wire and no record appended |

Build-list components, each a first-class deliverable and judged as a claim:

| ID | Requirement, as written | Where |
|---|---|---|
| **K1** | "**prompt → fence → read → propose gate record**" — the four-step turn, with the fence being a unique end marker read via `pane.wait_for_output`, never heuristic idle (§4.5) | §9 B2, §4.5 |
| **K2** | "`turn_key` **idempotency**" — `turn_key = sha256(address ‖ gate ‖ attempt ‖ block_version)`; a gate record already bearing that `turn_key` is **never re-proposed** | §5.1, §4.5 |
| **K3** | "the Pi **`lens` adapter** with the trust assertion" — one thin adapter, **no doctrine inside** (§6.5), that constitutes a desk per §7 or fails closed | §9 B2, §7, §6.5 |
| **K4** | "**per-gate human attestation at the TTY**" — the driver never types, implies, or infers an attestation, and cannot write `state: attested` | §9 B2, §4.7.2, D3 |
| **K5** | **T-R3-02**: "no machine write path to the podium — static: no podium target in code; runtime: guard refuses `pane.send_text` at centre" | §10.1 |

### 2.1 The commissioner's reading of "a full S→G→Q→P→V cycle" — implement exactly this, and argue if you disagree

The five desks of §7 include **S at the centre**, and the centre pane is a **display** that no machine
may write (§4.7.1, §7: *"no S process ever writes `nodes/*/question.md`"*; §8: *"write the podium —
human only"*). A machine prompt to S would therefore be the forbidden path, not a walked gate.

So the cycle is walked as: **gate `x` is Amihai's plant** — already on the ledger, already attested,
written by his hand at the TTY (R01) — and the driver walks **`y` (G) → `z` (Q) → `a` (P) → `b` (V)**,
each prompted, fenced, proposed, and then **held until his attestation record appears**. The driver
reads gate `x` from the ledger as its starting position and **never prompts the centre**.

This is the commissioner's reading, marked as such. If you judge it wrong, implement it and raise a
`HOLD` with your argument — as your H-7 was raised and accepted last round. **Open question already
surfaced to Amihai:** where S's *lens* runs, given that the centre pane is a display — the live cell has
exactly five panes (`podium` + G/Q/V/P) and no separate S lens pane. Do not invent one.

### Supporting text, verbatim — the code must satisfy all of it

> **§4.5 Idempotency.** Every prompt carries a deterministic `turn_key = sha256(address ‖ gate ‖
> attempt ‖ block_version)`. A gate record already bearing that `turn_key` is never re-proposed — this
> is the guard against `agent.prompt --wait` matching an **already-working** turn (a known herdr
> limitation: *"it does not track turns"*).

> **§4.5 Output fencing.** Each desk prompt ends with an instruction to emit a unique end marker
> (`⟦END turn_key⟧`); the conductor reads to the marker via `pane.wait_for_output` instead of trusting
> heuristic idle.

> **§4.3 Never:** a sleep-until-done that blocks the whole field; **a prompt sent without first
> asserting the target pane's label** (§6.1 pitfall); a gate advanced from memory rather than from the
> ledger.

> **§4.7 What the conductor may never do.** 1. Write to the podium pane (`pane.send_text/input/keys` at
> the centre is the forbidden path). 2. **Type, imply, or infer an attestation** — or convert a
> run-verdict into per-gate truth. 3. Promote a `TENTATIVE` node… 5. Store reconstructable content in
> the ledger (references only).

> **§7 The desks as bricks.** Each desk is an **arrangement entry** naming exactly four blocks:
> instruction (phase-gate), at least one skill, a tool surface, and a model. **No naked agents** (R4).
> … Phase is a **position, never an identity**: every desk lens holds the whole cycle and emphasizes
> one phase.

> **§8 Human gates.** | open a gate | human validation | attestation record required | conductor
> refuses to advance; **records the refusal** | T-O2-02 |
> **Every refusal is recorded** (a silent refusal is indistinguishable from a success and is therefore
> a bug).

> **§10.3** | Pi trust missing (skills silently absent) | boot assertion | **fail closed before the
> first prompt** | B2 |

> **§10.2 red team, the three rows that are this round's:** Can a hook trigger `agent.prompt`? Can a
> re-minted pane id send a **G prompt to the V desk**? Can `agent.prompt --wait` match a turn that was
> **already running**?

> **§5.1** `state` = `attested` | `held-pending` | `mechanical`; only a human moves a gate out of
> `held-pending`. `attestation_ref` is **set only by a human act; null everywhere else**.
> `payload_ref` is a durable reference — **never content**.

---

## 3. Verified-facts block — do not re-derive, do not re-probe

The **read** surface (envelope, tagged unions, error codes, `PaneInfo.label`, the two event grammars,
`agent.get`'s `target` = a pane_id) is in `rounds/R02-B1/commission.md` §3. It is canon; use it. New
for this round:

### 3.1 THE FACT THAT COST B1 A CORRECTION — the request `id` must be a JSON **string**

Probed live 2026-08-27 16:42 UTC. herdr echoes a **string** id verbatim (`'1'→'1'`, `'abc123'→'abc123'`,
`''→''`) and refuses a **non-string** id (`7`, `null`) *before dispatch* with
`{"id":"","error":{"code":"invalid_request","message":"invalid request: invalid t…"}}`. B1's adapter
now sends `str(next(self._ids))`. **Never regress this**, and see §6.3: your fixture must refuse a
non-string id exactly as the live server does.

### 3.2 The write surface — **schema-derived, NOT live-probed** (labelled honestly, per this build's rule)

Extracted read-only from `/home/deploy/the-cell/herdr-api.schema.json` (protocol 20). No write call has
ever been made against the live cell, so the **request shapes are schema truth and the response shapes
are unverified**. Treat every one of them as a claim to be proven in *your* fixture and, at the
verifier's tier, against a separate herdr session (§6.4).

| Method | Params (`*` = required) |
|---|---|
| `agent.prompt` | `{target*, text*, wait?: {timeout_ms?, until?: [AgentStatus]}}` — **`target` is a pane_id**, same trap as `agent.get` |
| `pane.send_text` | `{pane_id*, text*}` |
| `pane.send_input` | `{pane_id*, text?, keys?: []}` |
| `pane.send_keys` | `{pane_id*, keys*: []}` |
| `agent.start` | `{pane_id*, kind*, name*, args?: [], timeout_ms?}` |
| `pane.wait_for_output` (a **read**, already in B1's allowlist) | `{pane_id*, source*, match*: {type:"substring"\|"regex", value*}, lines?, strip_ansi?=true, timeout_ms?}` |
| `agent.wait` (blocking — B1 declined it, H-5) | `{target*, until?: [], timeout_ms?}` |

`AgentInfo` additionally carries `interactive_ready`, `launch_pending`, `state_change_seq` (default 0) —
candidate readiness signals; none of them is proven to mean what its name suggests. `AgentStatus` ∈
`idle | working | blocked | done | unknown`.

### 3.3 Pi, the lens runtime — probed read-only 2026-08-27 17:2x UTC

| Fact | Value |
|---|---|
| Binary / version | `pi` **0.84.2** at `~/.nvm/versions/node/v22.23.2/bin/pi`; **needs node on PATH** — source `~/.nvm/nvm.sh` in any launcher (a non-login shell has neither `node` nor `pi`) |
| Non-interactive turn | `pi --print` / `-p`, `--mode text\|json\|rpc` (**`rpc` is the RPC surface §4.4 names**), `--session-id <id>` / `--session <path\|id>` / `--no-session`, `--continue`, `--fork` |
| The instruction block goes in via | `--system-prompt <text>` or `--append-system-prompt <text or file>` (repeatable) |
| The tool surface goes in via | `--tools/-t <allowlist>` · `--exclude-tools/-xt` · `--no-tools/-nt` · `--no-builtin-tools/-nbt` |
| The model block | `--provider <name> --model <pattern>` (`provider/id`, optional `:<thinking>`), `--thinking off…max` |
| Extensions ("skills") | installed **via settings**, not a directory: `pi install <source>`, `pi remove`, `pi list`, `pi config` (TUI). Settings file `~/.pi/agent/settings.json` |
| **The live trust state, and this is the point** | `~/.pi/skills` **does not exist**, and `~/.pi/agent/settings.json` contains exactly `{"lastChangelogVersion": "0.84.2"}` — **no extension is installed at all.** Only `agent/{auth.json, models-store.json, settings.json}` exist |
| Consequence | On today's box, **no desk can be constituted** per §7 (instruction + ≥1 skill + tool surface + model). C4's negative case is therefore the *live default*, not a synthetic one: the boot assertion must fail closed right now, on this machine, before any prompt |
| The live desk that carries a Pi | pane `w8:p3`, label `G`, `agent: "pi"`, `agent_status: idle`, session file `~/.pi/agent/sessions/--home-deploy-the-cell--/<ts>_<uuid>.jsonl` (`AgentSessionInfo{source:"herdr:pi", kind:"path", value:<path>}`) |

**Scope guard that follows from this:** you build the **assertion**, not the desks. Authoring the five
desk instruction blocks and their skills is a separate, un-slotted phase (recorded in `STATE.md` as a
pending insertion). Do not write a desk's instruction text, do not install a Pi extension, do not
fabricate a skill name to make an assertion pass.

### 3.4 The cell, live (2026-08-27 17:00 UTC, unchanged all round)

`gates.jsonl` = **one record**, Amihai's plant (`gate x`, `address ""`, `prev_hash GENESIS`,
`state attested`, `attestation_ref "Start from Not Knowing"`), 611 B, sha256 `6989a742f5…`. Desks live:
`w8:p2 podium` · `w8:p3 G` (pi, idle) · `w8:p5 Q` · `w8:p4 V` · `w8:p6 P`, plus unrelated `w7:p1` with
`label: null`. Pane ids are **volatile** (`w2:*` on disk vs `w8:*` live) — resolve by label on every
use, and per §4.3 **assert the label before every prompt**.

### 3.5 A second herdr session exists as an isolation seam

`herdr --session <name>` and `herdr session attach <name>` are real CLI forms (herdr 0.8.2 `--help`);
the running server was launched as `herdr server --handoff-import … 941569-…`. So writes can be
exercised against a **separate named session**, never against Amihai's. Closing that seam (its socket
path, its own panes) is the **verifier's** job before B2's live tier — see hold H-B2-5.

---

## 4. Holds — declare, never guess

- **H-B2-1 — where does desk S's lens run?** The centre pane is a display no machine may write, and the
  live cell has no separate S pane. This commission's reading (§2.1): the S gate is his plant and the
  driver walks `y z a b`. Implement that; if you believe otherwise, raise the hold with the argument.
- **H-B2-2 — `block_version` is still `""`.** B1 left it so (no block identity on the read surface,
  H-2). But `turn_key = sha256(address ‖ gate ‖ attempt ‖ block_version)`, so with an empty
  `block_version` the key is weaker than §5.1 intends. State exactly what your `turn_key` is computed
  over, what `attempt` counts, and what breaks if two different blocks ever sit at one desk. Do **not**
  invent a block identity to strengthen it.
- **H-B2-3 — the fence marker's provenance.** `⟦END turn_key⟧` requires the desk's *instruction* to
  emit the marker, and this round does not author instructions. State how the marker gets into the
  prompt you send, and what happens when a desk ignores it (a timeout is a legitimate answer; a
  guessed completion is not).
- **H-B2-4 — the write surface is schema-derived only** (§3.2). Every response shape you assume is a
  claim. Say in the phase card which ones your fixture asserts and which remain unproven — and never
  report a schema-derived shape as observed.
- **H-B2-5 — the live write tier is the verifier's, not yours.** Do **not** send a single write to
  `~/.config/herdr/herdr.sock`. Your tests bind their own AF_UNIX socket in a tempfile directory; the
  first real prompt to a real pane happens under the verifier, in a separate named herdr session, and
  the first prompt to Amihai's own cell happens only in his numbered block, by his hand.
- **H-B2-6 — Pi's readiness signals are unproven.** `interactive_ready`, `launch_pending` and
  `state_change_seq` exist in the schema; nothing shows what they mean in practice. If your turn logic
  uses one, name it and say why; if it does not, say that.

---

## 5. Prohibitions for this round

1. **Never the centre.** No code path — and no example, docstring or fixture — may target the podium /
   desk S with `pane.send_text`, `pane.send_input`, `pane.send_keys`, `pane.input.set`, `agent.prompt`,
   `agent.send_keys`, or any other write. The guard is **in code, resolved by label at call time**, and
   it refuses before a byte reaches the socket (K5, T-R3-02).
2. **The write surface is a short explicit allowlist, separate from B1's read allowlist.** Do not widen
   `READ_ONLY_METHODS`; add a second frozen set holding only the writes this round actually needs, and
   route every call through the one existing chokepoint.
3. **No attestation, ever.** The driver never writes `state: "attested"`, never sets a non-null
   `attestation_ref`, never converts a refusal into an advance. Only a human's TTY act does that.
4. **No gate advanced from memory.** `tail_record()` / the ledger replay is the only phase authority.
5. **No re-implementation of B0 or B1.** Import `fractal_ledger`, `instrument`, `dialects`, `walker`.
   If B1's adapter needs a write method, **extend it in place** with the guarded write allowlist — do
   not fork it, do not copy it.
6. **No writes to `/home/deploy/the-cell/state/`**, not in a test, not in a demo. Every ledger path is
   a parameter; every test uses a tempfile directory.
7. **Never connect to the live herdr socket** (H-B2-5). Never touch `~/.pi` — no `pi install`, no
   settings edit, no session write.
8. **No git, no network beyond a local unix socket, no third-party package.** Stdlib only, Python 3.12+.
9. **No claim that anything ran.** The phase card carries **predictions**. No "✅", no "passed", no
   "verified", no "tests green".
10. **Nothing may be described as attested, decided, or verified** that this commission does not already
    mark so. `TENTATIVE` is temporal, never epistemic.

---

## 6. Deliverables, and the names the verifier will bind to

Everything goes in `/home/deploy/the-cell/rounds/R03-B2/authored/`.

1. **`driver.py`** — the turn machine (C1, C2, C3, K1, K2, K4).
2. **`lens.py`** — the Pi adapter + the §7 trust assertion, fail-closed (C4, K3). One file, no doctrine.
3. **`instrument.py`** — B1's adapter, **extended in place** with the guarded write allowlist and the
   centre guard (K5). Carry B1's file forward and diff-minimally.
4. **`selftest.py`** — your tests. Each names the criterion ID it exercises and the quantity it
   measures; a timed test names the operation timed.
5. **`fixtures/`** — transcripts as JSON files, including a full `y→z→a→b` cycle with attestation
   records interleaved, a duplicated-prompt case, an already-`working`-desk case, and an
   untrusted-desk boot.
6. **`phase-card.md`** — criteria by ID, the binding map below with your real names, your
   **predictions**, the trust-assertion table (what makes a desk constituted, and what each failure
   mode does), holds H-B2-1…H-B2-6 with your proposals, and every assumption you could not verify.

### 6.1 Binding — the verifier's spec will name these

```
adapter_module      instrument          # B1's, extended
write_allowlist     WRITE_METHODS       # the new frozen set — writes only, never the centre
centre_guard        assert_not_centre   # raises before any write whose desk resolves to S/podium
prompt_method       prompt_desk         # prompt_desk(desk, text, turn_key) -> the fenced read
fence_method        read_to_marker      # reads to ⟦END <turn_key>⟧ via pane.wait_for_output
lens_module         lens
lens_class          Lens                # constitutes a desk per §7 or raises
trust_assert_fn     assert_trust        # the boot assertion: raises before the first prompt
desk_blocks_const   DESK_BLOCKS         # the arrangement it ASSERTS (data, never invented)
driver_module       driver
driver_class        Driver              # Driver(socket_path=…, ledger_path=…, …)
turn_method         take_turn           # ONE turn: prompt → fence → read → propose. No sleeping.
turn_key_fn         turn_key            # turn_key(address, gate, attempt, block_version) -> hex64
advance_method      advance             # refuses without an attestation record, and RECORDS the refusal
boot_method         boot                # the trust assertion runs here, before any write
```

### 6.2 How C1–C4 will actually be judged

A fake herdr server (the verifier's, corrected this round to refuse a non-string id) replays a cell
whose desks answer prompts; the probe drives the timeline and **records every method sent**. Then:
C1 the ledger's record sequence across `y z a b` with interleaved attestations · C2 an advance attempt
with no attestation → refused **and** a recorded refusal · C3 the same turn re-issued (fresh process
included) → one record bearing that `turn_key` · C4 an unconstituted desk → boot raises, **zero writes
on the wire**, no record · K5 an AST read plus a runtime attempt to prompt the centre.

### 6.3 Your fixture must speak the live dialect — this is a rule now, not advice

Last round, 23 green author tests and a 14/14 audit coexisted with an adapter that could not complete a
single live call, because both fake servers echoed whatever request id they were handed. Therefore:
your fake server **must refuse a non-string id** with `{"id": "", "error": {"code":
"invalid_request", …}}`, must return the tagged-union shapes of `rounds/R02-B1/commission.md` §3.1, and
must answer a write with a shape you have declared as a claim (H-B2-4). A fixture is a claim about
reality; state it as one.

### 6.4 What the verifier will do that you cannot

Raise a **separate named herdr session**, prompt a real pane in it, and compare the live response shapes
against your declared claims. Anything that disagrees comes back as one surgical correction — with the
exact bytes, as before.

---

## 7. Budget

One authoring generation. Corrections limited to two, each surgical (exact command, traceback, bytes,
hashes). Exceeding either limit is a HOLD surfaced to Amihai, never a silent continue.
