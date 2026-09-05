# R03 · B2 — phase card (authored by dsh, predictions only)

This card carries **predictions**, not results. It records no outcome of
any execution and no judgment of any criterion — no success marks, no
outcome claims, no execution statements. A separate verifier executes the
artifact against its own fake socket and scratch ledger and writes the
only record that counts. Where a fact could not be established, a HOLD
names what would be needed.

The commissioner's §2.1 reading of "a full S→G→Q→P→V cycle" is
implemented **exactly as written**, with no disagreement to raise: gate
`x` is Amihai's plant — already on the ledger, already attested, by his
hand at the TTY — and the driver walks `y` (G) → `z` (Q) → `a` (P) →
`b` (V). The driver reads gate `x` from the ledger as its starting
position and **never prompts the centre**; the centre guard refuses desk
S before any byte reaches the socket.

---

## 1. Criteria restated by ID

| ID | Criterion, as written (commission §2) | Where the artifact answers it |
|---|---|---|
| **C1** | a full S→G→Q→P→V cycle is walked **with the human attesting each gate** | `driver.take_turn` / `driver.advance` over `fixtures/cycle_transcript.json`: the ledger's own record sequence `x y y y z z a a b b` (plant, proposal, refusal, attestation interleaved; the refusal rides the held gate so the letters keep order), four prompts in G→Q→P→V order, each proposal followed by its attestation before the next prompt |
| **C2** | **no gate opens without an attestation record** | `driver.advance` and the out-of-order branch of `driver.take_turn`: refused **and the refusal recorded** through B0's writer (§8 — a silent refusal is a bug) |
| **C3** | a deliberately duplicated prompt produces **one** record | `driver.turn_key` + the never-re-propose guards in `take_turn`: the re-issued turn (fresh process included, working desk included) sends no second prompt |
| **C4** | the skills-loaded assertion **fails the boot** when trust is missing | `lens.assert_trust` run inside `driver.boot` before any write: zero write methods on the wire, zero records appended; the shipped `DESK_BLOCKS` records the live absence, so the negative case is the live default |
| **K1** | "**prompt → fence → read → propose gate record**" | `instrument.prompt_desk` (one `agent.prompt` whose text ends with the fence instruction) + `instrument.read_to_marker` (`pane.wait_for_output`, substring match on `⟦END <turn_key>⟧`, never heuristic idle) + `driver.take_turn` (ONE proposal through `LedgerWriter`) |
| **K2** | "`turn_key` **idempotency**" | `driver.turn_key(address, gate, attempt, block_version)` = sha256 over the raw concatenation; a gate record already bearing the key is never re-proposed (checked before the prompt and again before the append) |
| **K3** | "the Pi **`lens` adapter** with the trust assertion" | `lens.py` — one thin adapter, no doctrine inside; constitutes a desk per §7 or raises `TrustError` |
| **K4** | "**per-gate human attestation at the TTY**" | the driver cannot write `state: "attested"` and cannot set `attestation_ref` to anything but null — every record it authors is `held-pending` / `attestation_ref: null` (static + runtime evidence) |
| **K5** | **T-R3-02**: no machine write path to the podium | `instrument.WRITE_METHODS` (the one write: `agent.prompt`), `instrument.assert_not_centre` resolved by pane LABEL at call time inside the single chokepoint, refusing before a byte reaches the socket; every other write method stays outside both allowlists |

## 2. Binding map (commission §6.1 → what I authored)

| Commission name | My name | Lives in | Notes |
|---|---|---|---|
| `adapter_module` | `instrument` | `instrument.py` | B1's adapter, extended in place (diff is additions + two touch points: the allowlist line and one `_RESULT_KEYS` entry) |
| `write_allowlist` | `WRITE_METHODS` | `instrument.py` | the new frozen set: `frozenset({"agent.prompt"})` — the only write this round sends; `READ_ONLY_METHODS` is byte-identical to B1's |
| `centre_guard` | `assert_not_centre` | `instrument.py` | module-level: `assert_not_centre(desk)` raises `CentreWriteError` for the centre desk key `"S"`, the podium label, and for `None` (unverifiable → fail closed); returns None for other desk keys |
| `prompt_method` | `prompt_desk` | `Instrument.prompt_desk` | `prompt_desk(desk, text, turn_key, …) -> the fenced read`; label-resolved on THIS call, live label asserted (§4.3), one `agent.prompt`, then the fence read; no retry after dispatch |
| `fence_method` | `read_to_marker` | `Instrument.read_to_marker` | reads to `⟦END <turn_key>⟧` via `pane.wait_for_output` (substring match); refuses a truncated / empty / marker-less read |
| `lens_module` | `lens` | `lens.py` | stdlib only, importable |
| `lens_class` | `Lens` | `lens.py` | `Lens(pi_home=…, settings_path=…, skills_dir=…, pi_bin=…, blocks=…)` — every path a parameter; read-only; the binary is never invoked unless a path was supplied |
| `trust_assert_fn` | `assert_trust` | `lens.py` | module-level `assert_trust(desk, blocks=None, lens=None)` (defaults: `DESK_BLOCKS`, `Lens()` with live paths → fails closed on the live state) and `Lens.assert_trust(desk, blocks=None)` |
| `desk_blocks_const` | `DESK_BLOCKS` | `lens.py` | the arrangement the assertion ASSERTS — data recording the live absence (no instruction authored, no skills), never invented |
| `driver_module` | `driver` | `driver.py` | imports `fractal_ledger`, `instrument`, `lens`, `walker` — never re-implements B0/B1 |
| `driver_class` | `Driver` | `driver.py` | `Driver(socket_path=…, ledger_path=…, …)` — both paths parameters; ledger default `fractal_ledger.DEFAULT_LEDGER_PATH` (every test supplies a scratch path) |
| `turn_method` | `take_turn` | `Driver.take_turn` | ONE turn: prompt → fence → read → propose; no sleeping; returns a status dict (`proposed` / `already_recorded` / `already_walked` / `refused` / `incomplete`) |
| `turn_key_fn` | `turn_key` | `driver.turn_key` | `turn_key(address, gate, attempt, block_version) -> hex64`; attempt coerced to str |
| `advance_method` | `advance` | `Driver.advance` | refuses without an attestation record and RECORDS the refusal; reports the due gate when nothing is pending; `complete` after gate b |
| `boot_method` | `boot` | `Driver.boot` | replays/verifies the chain, demands the attested plant, then runs the trust assertion for the four walk desks — before any write, touching the socket not at all |

Data tables reused from B1 (imported, not re-implemented): `walker.DESK_GATES`
(`S:x G:y Q:z P:a V:b` — Amihai's word), `walker.DESK_ADDRESSES`
(`S → ""`, the empty address word of the attested plant), `walker.COURSE`
(`S,G,Q,P,V`), `instrument.DESK_LABELS` (the label→desk config table).

## 3. Predictions per criterion

> Predictions about what the verifier will observe when it executes the
> artifact against its own fake socket and scratch ledger. None of them
> claims that anything already ran.

- **C1 — Prediction.** Replaying `fixtures/cycle_transcript.json`
  (boot → take_turn G → advance refused → human attestation y →
  advance → take_turn Q → attestation z → take_turn P → attestation a →
  take_turn V → attestation b → advance), the verifier will observe: the
  ledger's record sequence in gate-letter order `x y y y z z a a b b`;
  exactly four `agent.prompt` methods on the wire, targeted at the G, Q,
  P, V panes in that order; every machine proposal (`held-pending`,
  `mark mechanical`, `tentative true`, `attestation_ref null`) followed
  by a human attestation record before the next prompt is sent; the one
  refusal record sitting on the held gate `(G, y)` between the proposal
  and the attestation; and `advance()` reporting `complete` after gate b.
- **C2 — Prediction.** After a proposal exists and before any
  attestation, each `advance()` attempt will return `refused` and append
  one refusal record on the held gate's own (address, gate) — repeated
  attempts append one record each, with distinct refusal-slot turn keys;
  an out-of-order `take_turn` (any desk beyond the due gate) will return
  `refused`, append its refusal on the due pair, and send no prompt. No
  refusal is ever silent: a refusal always yields a record, and a
  refusal record never reads as an advance (`held-pending`,
  `attestation_ref null`).
- **C3 — Prediction.** The same turn re-issued after completion will
  return `already_recorded` with no second prompt on the wire; a FRESH
  subprocess pointed at the same socket and ledger will rebuild the
  position from the ledger alone (plant attested, gate x) and return
  `already_recorded`; against a desk whose `agent_status` is `working`
  the turn still yields exactly one record bearing the prompt key and
  one prompt — the driver never branches on `agent_status`, so the §4.5
  hazard is contained by the fence and the key. In every variant:
  records bearing the prompt `turn_key` = exactly one.
- **C4 — Prediction.** With an arrangement that names skills but a Pi
  state mirroring the live box (settings.json holding only
  `{"lastChangelogVersion": "0.84.2"}`, no skills directory, no pi
  binary), `boot()` will raise `TrustError` at stage `skills` with
  verdict `inconclusive` — and the verifier will measure zero requests
  on the wire (zero connections), zero write methods, zero records
  appended. With the shipped `DESK_BLOCKS` (the live arrangement:
  nothing authored) the same boot raises at stage `instruction`. The
  constituted positive control (skill observed installed in a synthetic
  Pi home) is accepted by the boot and the turn walks.
- **K1 — Prediction.** One turn will appear on the wire as exactly five
  requests, in order: `pane.list` (resolve by label), `pane.get`
  (live-label assertion), `pane.get` (the centre guard resolving the
  write target's label at call time), `agent.prompt` (the single write,
  whose text ends with the fence instruction naming `⟦END <turn_key>⟧`),
  `pane.wait_for_output` (substring match on the marker). A timeout
  error, an empty read, a `truncated: true` read, or a matched read
  without the marker will each leave the turn `incomplete` with zero
  records appended.
- **K2 — Prediction.** `turn_key("G","y","1","")` will equal
  sha256 over the raw bytes `G‖y‖1‖""` (hex64), including with a
  non-ASCII block_version; and a gate record already bearing that key
  is never re-proposed — the verifier will establish this by re-issuing
  the turn, including from a fresh process.
- **K3 — Prediction.** Seven failure modes each raise `TrustError` at
  the named stage with the named verdict (missing arrangement entry;
  missing instruction; no skills; skills `inconclusive` when no source
  is observable; a named skill `not_loaded` when a source was observed
  without it; missing tools; missing model); an unobservable Pi can
  never read as clean; the lens writes nothing to the Pi home; the pi
  binary is never invoked unless a path was supplied.
- **K4 — Prediction.** A static read of the artifact will find every
  `attestation_ref` value the driver authors to be `null` and no
  `state: "attested"` value written anywhere; across a whole cycle every
  machine record is `held-pending` with `attestation_ref: null`, and the
  only attested records are the plant and the human TTY stand-ins.
- **K5 — Prediction.** A static AST read will find exactly one write
  literal routed through the chokepoint — `agent.prompt` — and no call
  site for `pane.send_text` / `pane.send_input` / `pane.send_keys` /
  `agent.send_keys` / `agent.start`; a runtime `agent.prompt` at the
  podium pane will raise `CentreWriteError` after exactly one read
  (`pane.get`, resolving the label) and with zero write bytes on the
  wire; `take_turn("S", …)` will raise before any socket traffic at all;
  `pane.send_text` is refused by the allowlist at any target, before any
  byte.

## 4. Trust-assertion table (what constitutes a desk, and what each failure mode does)

| Block (§7) | Constituted when | Failure mode | What happens |
|---|---|---|---|
| arrangement | an entry names the desk | entry missing / not an object | `TrustError(stage="arrangement", verdict="missing")` — boot fails closed |
| instruction | a non-empty string (the phase-gate block, authored in its own un-slotted phase) | `None` / empty / whitespace | `TrustError("instruction", "missing")` |
| skills | at least one name, AND every named skill **observed installed** in the Pi state | zero names named | `TrustError("skills", "missing")` |
| skills | as above | no Pi source observable (settings without a skills key, no skills dir, no pi binary) | `TrustError("skills", "inconclusive")` — absence is not validity; never clean (lens 6) |
| skills | as above | a source was observed and the name is absent | `TrustError("skills", "not_loaded")` — the C4 subject: skills named but not loaded |
| tool surface | a non-empty list of tool names | `None` / empty | `TrustError("tools", "missing")` |
| model | `{provider, model}` both non-empty strings | `None` / incomplete | `TrustError("model", "missing")` |

Only the **skills** block is cross-checked against the observed Pi
runtime; instruction/tools/model are arrangement-completeness checks (no
live source for them is observable). Observation sources, each a
declared claim: settings.json key `"skills"`; the skills directory
entries; `pi list` stdout lines (only when a binary path was supplied). On
the live box (commission §3.3) no extension is installed and no
instruction is authored, so the boot assertion fails closed **right
now, on this machine, before any prompt** — the C4 negative case is the
live default, not a synthetic one.

## 5. The commissioner's §2.1 reading — implemented as written

The centre pane is a display no machine may write (§4.7.1, §7, §8), so a
machine prompt to S is the forbidden path, not a walked gate. Implemented
exactly so: gate `x` is the plant (read from the ledger as the starting
position), the walk is `y z a b`, and `take_turn("S")` /
`assert_not_centre("S")` refuse before any byte. No disagreement is
raised. Where desk S's *lens* runs remains open — see H-B2-1.

## 6. Holds — declared, never guessed

- **H-B2-1 — where does desk S's lens run?** The centre pane is a
  display and the live cell has no separate S pane. **Proposal:** the
  driver never prompts the centre and never asserts the centre's lens;
  boot asserts §7 trust for the four walk desks (G Q P V) only. The
  question of where the centre's own lens runs (an un-slotted assembly
  concern, no pane invented) stays open for the assembly round — the
  driver's contract is simply that no machine write resolves to S.
- **H-B2-2 — `block_version` is still `""`.** No block identity exists
  on the read surface, and inventing one is forbidden. **Proposal:**
  every machine record carries `block_version = ""` (a parameter, not a
  literal in logic). The PROMPT's `turn_key` is computed over
  `(address, gate, attempt="1", block_version="")` — each gate is
  prompted at most once in this round's walk, so its single prompt
  always carries attempt `"1"`, and the re-issued turn recomputes the
  SAME key and is suppressed by the record bearing it. **What
  `attempt` counts:** the ordinal of the prompt for that (address,
  gate) — always 1 here; there is no rejection-driven re-prompt in
  B2's scope. Refusal records derive their key as
  sha256(address ‖ gate ‖ `"refusal:"+n` ‖ block_version) with `n` = the
  number of records already on the ledger for that pair — deterministic
  from the ledger alone and never colliding with the prompt key. **What
  breaks:** with an empty block_version the key cannot distinguish two
  different blocks that ever sit at one desk — across a second cycle the
  same pair would recompute the same prompt key and a later turn would
  read as a duplicate; that weakening is contained (one cycle this
  round) and stated, not papered over.
- **H-B2-3 — the fence marker's provenance.** `⟦END turn_key⟧` requires
  the desk's own instruction to emit the marker, and this round does not
  author instructions. **Proposal:** the DRIVER builds the marker
  (`fence_marker(turn_key)`) and appends the §4.5 fence instruction to
  every prompt it sends — the mechanism itself, not desk doctrine; the
  desk's authored instruction block (an un-slotted phase) must teach the
  desk to obey it. When a desk ignores the marker, the bounded
  `pane.wait_for_output` (timeout_ms parameter, 60000 default) times out
  or the read fails the marker check: the turn is `incomplete`, nothing
  is proposed, nothing recorded — a timeout is a legitimate answer, a
  guessed completion is not.
- **H-B2-4 — the write surface is schema-derived only.** Every
  write-response shape this round assumes is a claim. **Proposal:** the
  adapter enforces exactly these declared shapes and refuses to guess:
  `agent.prompt` success `{"type": "agent_prompted", "agent":
  AgentInfo}`; `pane.wait_for_output` success `{"type":
  "output_matched", "pane_id", "revision", "read": PaneReadResult,
  "matched_line"?}`; a fence timeout error `{"code": "timeout", …}`.
  The fixtures ASSERT these shapes and carry a `claims` block saying so;
  none is reported as observed. The live tier (a separate named herdr
  session) is the verifier's — a disagreement there comes back as one
  surgical correction.
- **H-B2-5 — the live write tier is the verifier's, not mine.** No
  write and no connection to `~/.config/herdr/herdr.sock` exists anywhere
  in the artifact or its tests; every test binds its own AF_UNIX socket
  in a tempfile directory and every ledger path is a tempfile path. The
  first real prompt to a real pane happens under the verifier, in a
  separate named session; the first prompt to Amihai's own cell happens
  only in his numbered block, by his hand.
- **H-B2-6 — Pi's readiness signals are unproven.** `interactive_ready`,
  `launch_pending`, `state_change_seq` exist in the schema; nothing shows
  what they mean. **Proposal:** my turn logic uses NONE of them, and it
  does not branch on `agent_status` at all — a desk is prompted on the
  strength of its LABEL, the ledger position, and the fence. Therefore
  `agent_status: "unknown"` (the live bare-desk normal) and
  `"working"` can never read as a completed turn or an open gate, and
  the already-working hazard of §4.5 is contained by the turn_key fence,
  exactly as the PRD prescribes.

## 7. Assumptions I could not verify

1. The three write-response shapes of H-B2-4 (schema-derived, never
   live-probed).
2. The settings.json key `"skills"` is where `pi install` records
   installed extensions (the live file has no such key — the claim is
   untested either way).
3. The output shape of `pi list` (never invoked by the lens unless a
   binary path was supplied; on this box none is).
4. `pane.wait_for_output` semantics: it waits for output matching the
   substring and respects `timeout_ms` (per the schema's parameter
   list).
5. `agent.prompt` accepts `target = pane_id` for panes whose `agent`
   field is non-null and dispatches to that agent; the live Q/P/V panes
   carry `agent: null` (B1 §3.2), so the live write path for them is
   unproven — the fixture cells are declared synthetic (their Q/P/V
   carry answering agents).
6. `source: "visible"` is the right `ReadSource` for the fence read (B1
   used it for `pane.read`; the fence uses the same value).
7. The fixture's human attestation records follow the plant's TTY
   convention (turn_key computed with attempt `""`) — Amihai's
   demonstrated convention, used only by the test's human stand-in.
8. The operational reading of `advance()`: "open a gate" requires the
   PREVIOUS gate's attestation, so `advance` refuses (and records) only
   when a proposal is pending attestation; with nothing pending it
   reports the due gate — nothing was refused there, because the gate
   before it IS attested (§2.1's flow). If the verifier's probe intends
   a different `advance` contract, this is the one assumption most
   likely to need a surgical correction.
9. The refusal record rides the HELD (due) pair rather than the
   attempted target, to keep the ledger's gate letters in `x y z a b`
   order — a design choice, stated, not checked against the PRD's
   letter.
10. Boot asserting trust for all four walk desks (G Q P V) is the right
    scope of §7 "no naked agents" for this round; S's lens is H-B2-1.
11. The fence timeout error code name `"timeout"` (schema's error codes
    are free strings).
12. `wait_timeout_ms` default 60000 is sane live pacing (a parameter,
    never a hard promise).
13. The fixture desk-block strings ("fixture placeholder — not a real
    desk instruction") are synthetic test data, not the desks' authored
    instruction blocks; the desks' instruction text and skills are an
    un-slotted phase and are authored by no part of this round.
14. The adapter's reconnect-retry (B1 behaviour) may re-send a prompt
    whose first send's fate is unknown; the turn_key fence absorbs the
    duplicate (one record), which is the PRD's own guard for exactly
    this.

## 8. Key derivations, stated once (H-B2-2 / H-B2-3 machinery)

- `fence_marker(turn_key)` = `"⟦END " + turn_key + "⟧"`; appended to
  every prompt as the §4.5 instruction (the instruction references the
  marker verbatim — it never re-wraps it).
- Prompt key: `turn_key(address, gate, "1", block_version)`.
- Refusal key: `turn_key(address, gate, "refusal:" + str(n),
  block_version)` where `n` = records already on the ledger for that
  (address, gate).
- Proposal record: `state held-pending`, `mark mechanical`,
  `tentative true`, `payload_ref "fenced:sha256:<hex of the fenced
  text>"` (a durable reference, never content), `attestation_ref null`.
- Refusal record: same shape with `payload_ref
  "refusal:no-attestation:<address>:<gate>"` and the refusal-slot key.
- The driver never writes `state: "attested"` and never sets
  `attestation_ref` — only a human's TTY act does that.

## 9. Correction note — 2026-08-27

Desk resolution now refuses through the typed `DeskResolutionError` (a
`HerdrError`) when a desk resolves to no live pane, so a lost label
reaches the `incomplete` path with nothing sent and nothing appended —
prediction only.
