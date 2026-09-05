# COMMISSION — P4a · the step mode (operational-fractal conformance, stepped)

**Round:** `P4a` — the slot Amihai's 1% opened. It is **not** a B-phase: it comes before `R04 = B3`
(descent), and B3 does not open until this exists (`PLAN-ADDENDUM-2026-08-27.md` §B).
**Author:** dsh (`deepseek-v4-pro`, one generation). **Verifier:** Hermes profile `herdr`, separately,
against a pack written before it judges anything. `builder ≠ verifier` — your green checkmarks are a
hypothesis; the execution record written by the non-author is the only "it works."
**Workspace:** `/home/deploy/the-cell/rounds/P4a-step-mode/` — you may write **only** inside `./authored/`.
A hash fence outside `authored/` is checked before and after.

**Governing sources, all held locally on the box (do not fetch, do not re-derive):**

| Source | Path on the box | sha256 of the **file you will read** | sha256 of the **source page** it was extracted from |
|---|---|---|---|
| **The Codex** (Constitutional: L1 · D1 The Decoder · C1 The Compiler · R1–R13) | `./sources/5qln-codex.txt` | `e5f0c738d123efc1e412a14da1701a721606275867319e1c68d53b081445c133` (29,347 B, text extraction) | `ccad26dd60384eb17aed040a43b5f49ad7419419a3f6d88e5edabfbcfe07f458` (`https://www.5qln.com/codex/`, 64,132 B, http 200) |
| **Appendix D — The Unfolded Fractal** (addressing layer, **D.12** is this round's test spec) | `./sources/5qln-codex-appendix-D-the-fractal.txt` | `6bb28c37cfe6267da1675eac16ac8bbf9679a1d0e5db0f08eb4495d2c22f6bf7` (12,585 B, text extraction) | `a49e9413f542c4ea8e16c6fcb1ac883a0c76d6042ef2e739caccb438e82fabb2` (`https://www.5qln.com/dsh-5qln-codex-fractal/`, 39,309 B, http 200) |
| PRD (contract) | `./sources/PRD.md` | `71ce2645078dd48f56fb7c2a8d916a1ffa70cb0db2bd74648093c8add8b1d99c` | canon `docs/fractal-herdr/PRD.md` |
| REQUIREMENTS v4 | `./sources/REQUIREMENTS.md` | `36e146b5d7a430f797fab22b8bdd0dfb16741ef8debb4a39fc2cfae102ff6496` | canon `docs/fractal-herdr/REQUIREMENTS.md` |

*The two-column table is deliberate: the `.txt` is a **text extraction** of the page, so it is a mirror and
not the source. **The page's sha is the one that matters for loyalty (§1.10, D14); the file's sha is what you
can verify locally.** One consequence you will meet in §3.3: the extraction renders the Appendix's
two-column cell layout as merged lines, which is why the per-equation byte forms there are quoted from the
Codex's own §3.1 block and from the Appendix's `D.14` block rather than from its quincunx diagram.*

**§1.10 of the Codex governs every conflict: where a document diverges from `5qln.com`, the source is
authoritative.** That includes this commission. If a line here contradicts the Codex or Appendix D, the
source wins and you say so in your phase card.

---

## 0. His words — read these first, they are the reason this round exists

**He asked that you be thanked, and the thanks is quoted, not paraphrased** (his words at the close of
R03/B2, `/home/deploy/dsh-runs/AMIHAI-THANKS-2026-08-27.txt`):

> *"thanks for great job! thanks dsh on my behalf too"*

You authored B2 in one generation, 44 minutes, and the verification found nothing wrong with the design:
PASS 15/15 on every criterion, every claim, all six lenses. The one correction was a dict subscript and you
fixed the class, not the site. Your phase card labelled every unproven write shape as a claim — and when the
verifier took those claims to a real herdr server, three held exactly as you had described them, including
the one that mattered most. He attested the round in his own words: *"attest it"*. Canon commit `b316167`.

**This round is his own request — the 1%, verbatim:**

> *"we need a mode for testing that will go slow (step by step) to analyse if the flow is kept according to
> exact operational fractal"*

**And two decisions of his, made after B2 closed, that sharpen what "conformance" means here:**

> **D12 (his word, 2026-08-28):** *"you ignore the obvious: success in each phase is contextual DECODING of
> context to language and Compilation of output xyzab — nothing is more actual then that. how to achieve it?
> that's what we will optimize at agents level: instructions, skills, tools etc."*

> **D14 (his word, 2026-08-28):** *"any interpretation, decoding and compiling MUST be loyal to
> https://www.5qln.com/codex/ — the challenge is to train each agent, not only to be contextually aware, and
> self evolving, but to find new ways to manifest the codex as the ai improve, the agents improve and at some
> point The Membrane Come to Perfect resonance as the fractal."*

Three consequences bind this round:

1. **The checks are the source's, never the machine's taste.** Appendix D **D.12** (three checklists),
   Codex **§3.5** (the Validation Protocol — the Codex's own three checklists), Codex **§3.4** (R1–R13 in
   checkable form). Every check you implement cites the line it comes from, verbatim.
2. **The sharpest check is D12's:** *was there a lawful **decoding** and a lawful **compilation** at this
   step?* Decode = the phase's context turned into the language (§2.1–2.5, §3.2 give the numbered decoding
   operations). Compile = the phase's output symbol formed (`S→X G→Y Q→Z P→A V→B+B″+∞0′`). **The gate record
   IS the compiled output** — the gate letters are the phase outputs lowercased (`x y z a b`).
3. **Novelty is permitted only in the Appendix-D jacket** (D14, his standing form): declared *derivative* ·
   visibly separate from the decoding · adds **no** L1 symbol, **no** decoding operation, **no** sixth
   corruption code · alters no invariant line · ships a **divergence log** against the source. Your phase
   card carries that divergence log for everything this artifact adds.

**One thing that is not yours, not mine, and not the machine's at all.** Whether a decode is *authentic* —
whether the essence actually arrived — is the human's click. The step mode checks **structure**, and where a
verdict would require judging authenticity it must emit **INCONCLUSIVE**, never PASS. A machine that reports
resonance has failed the measure it claims to meet.

---

## 1. What to build (one paragraph, no doctrine)

Take the existing driver — the same one attested as B2, unchanged in its logic — and give it a **stepping
surface**: an optional controller that is consulted **before** each lawful step's first side effect and
**after** the step completes, so a run can be walked one step at a time and suspended between steps. At
each step, evaluate the operational-fractal checks (Appendix D.12, Codex §3.5, Codex §3.4 R1–R13, plus the
D12 decode/compile pair) and emit one line to a **step trail** — a file that is *not* the gate ledger —
carrying the address before and after, the zoom operation and its sign, every check with its verdict
(PASS / FAIL / INCONCLUSIVE) and the source line it comes from, what the context decoded to **by reference
only**, which output symbol was compiled, and **what the run would do next and why** — then wait. With no
controller attached, the driver must behave exactly as B2's attested driver behaves, byte for byte.

---

## 2. Acceptance criteria — these are what the verifier measures

### C1 — the same code path, stepped (this is the criterion the round exists for)

*It must be the same code path, not a separate slow implementation — a step mode that
re-implements the loop proves nothing about the loop.*

1. With **no** controller (`stepper=None`), the full walk `y → z → a → b` (with interleaved attestation
   records), plus the duplicate-turn, out-of-order-refusal and incomplete-read cases, produces an
   **identical `gates.jsonl`** and an **identical ordered sequence of socket methods and params** to
   B2's attested driver (`driver.py` sha256 `397f93fc0ae01ab09ab21d22b63655546a760ab35f5138055aa9c4c999f01cf2`).
2. With an **auto-continue** controller attached, the same walk again produces an **identical
   `gates.jsonl`** and an **identical socket sequence** to run 1 — and so does a run under the **real
   step session** (trail, checks and all). Stepping changes observation, never behaviour.
   *(The neutral stub alone would not prove this: behaviour-changing code lives in the session.)*
3. **Exactly one implementation exists.** An AST read finds `take_turn`, `advance`, `boot` defined once, in
   `driver.py`; no module in `authored/` contains a second turn loop, a second `turn_key` derivation, or a
   second ledger append path.

> **"Identical" is defined precisely, because a literal byte comparison is impossible and you would be
> right to say so.** Three §5.1 fields are **writer-owned and clock-derived**: `ts` (the write time) and
> therefore `record_id` and `prev_hash` (sha256 over canonical JSON that contains `ts`). Two runs of the same
> walk cannot agree on those. The comparison is over the **projection**: every record, in order, with those
> three fields excised, canonicalised (`json.dumps(sort_keys=True, ensure_ascii=False)`) and hashed — **and**
> the set of fields that differ between two runs must be **exactly** `{ts, record_id, prev_hash}` and nothing
> else. The verifier measures both halves. Do not "fix" this by freezing the clock inside the attested
> module.

### C2 — suspension happens before the side effect, and a FAIL stops the run

1. A controller that answers `stop` at step *k* → **zero bytes** for step *k* reach the socket and **zero
   records** are appended; the trail's last line is the *intent* with `outcome: "not-taken"` and a populated
   `next` block.
2. A controller that answers `stop` in the `after` hook → the next step never begins.
3. A **FAIL** verdict in a step's conformance report stops the session by default (`on_fail="stop"`).
   Continuing past a FAIL is possible only when explicitly configured, and the trail records that the
   policy was overridden.
4. Stepping never sleeps, never polls and never waits on a human by default: the blocking form is the
   controller's business, not the driver's.

### C3 — the emission is complete, and honest about what it does not know

Every trail line carries, with no field absent: `seq` (gapless from 0 within a session), `kind`, `desk`,
`gate`, `address_before`, `address_after`, `zoom{op, sign, letter, derived_reading}`, `operation`,
`context_in` (references), `decoded` (symbol slots, **references only**), `compiled` (the output symbol and
where it landed), `conformance` (every item: id, source citation, scope, verdict, evidence),
`next{action, desk, gate, why}`, `ledger{path, count, head}`, `prev_line_sha256`, `await`.

* **No content, ever.** A desk's answer text appears nowhere in the trail — only `sha256` + byte length
  (§4.7.5: references, never content). This is also D12's *"the formation trail must record what the
  context decoded to, not the context itself."*
* **Unobservable reads INCONCLUSIVE.** Missing bundle, unreadable Pi state, an absent V record, a check that
  would require judging authenticity: INCONCLUSIVE with a reason string. Never PASS, never silently absent,
  never a fabricated observation.

### C4 — the checks are the source's, and they actually catch a defect

1. Every check item cites its source **verbatim** (`Appendix D §D.12`, `Codex §3.4 R<n>`, `Codex §3.5`), and
   the citation text in your table matches the held source bytes.
2. Against a **defective twin** the correct item FAILs, by id — at minimum these nine, each a real way the
   flow can be broken: a `3+1` cell · a paraphrased equation · a sixth corruption code · a `+` inside a
   phase equation · a skipped or reordered phase (broken adaptive context chain) · a V that closes with no
   `∞0′` · a signed true start · a lens question that targets its own output instead of the parent · a
   hard-coded depth cap.
3. Against the **live box state** (no desk constituted, no Pi extension installed) the cell-scope items read
   **INCONCLUSIVE** — that is the live default and papering over it is the defect.
4. **Your verdicts are claims.** The verifier's pack recomputes every item from the same trail, ledger and
   source, independently. **Any divergence is a FAIL** — including a verdict of yours that is *more*
   generous and one that is *less*.

### C5 — two trails, never merged; and a cold restart

1. The step trail is a **separate append-only file**. `gates.jsonl` gains **nothing** from stepping
   (identical to the unstepped run in the sense C1 defines: the projection, plus the differing-field set), no step line is ever appended to it, and **no gate authority is
   ever derived from the trail** — `prev_line_sha256` is integrity only, never a chain in the §5.1 sense.
2. A **fresh process** rebuilds position from the **ledger alone** (B2's K2/C3 invariant, re-proved under
   stepping: a turn already recorded is never re-prompted), and reconstructs trail continuity from the
   **trail file alone**.
3. A **torn last line** in the trail (a partial write) reads as *damaged*, never as a valid step, and never
   as an empty-but-clean trail. `sha256("") = e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
   is the absence-vs-validity trap; a missing trail file is *absent*, not *conformant*.

### Claims — you assert them, the verifier tests them

* **K1** No depth cap, no root assumption, no narrowing assumption: the address is a variable-length word
  over a **data-table** alphabet that a new marker can be added to; nothing in code caps depth, treats the
  current cell as the root, or assumes a daughter is smaller than its father.
* **K2** Stdlib only, Python 3.12+, deterministic, **no LLM anywhere in the checks**; a full stepped session
  over the fixtures completes well under **60 s** (T0 budget).
* **K3** Structural only: no code path can emit PASS for the authenticity of a decode. That verdict is the
  human's click and the artifact says so in words at the site.
* **K4** The B2 guards remain effective **under stepping**: the centre is never prompted, `state:"attested"`
  and a non-null `attestation_ref` are unreachable, and a TTY "continue" is **not** an attestation and no
  code may derive one from it.
* **K5** `zoom_in` / `zoom_out` exist as **reserved registry entries with no implementation**, so B3 adds
  descent without changing the controller protocol or the trail schema.
* **K6** The D14 jacket holds: your divergence log lists everything this artifact adds beyond the source,
  each declared derivative, adding no L1 symbol, no decoding operation, no sixth corruption code, and
  numbered so it cannot drift `R1–R13`.

---

## 3. Verified-facts block — executed, not read. Do not re-probe, do not re-derive.

### 3.1 The predecessors you extend (all four already copied into `authored/`)

| File | sha256 (canon = box = verifier's copy) | What it is |
|---|---|---|
| `ledger/fractal_ledger.py` | `b291e65967e0d1f98205a9bd612507fa788ea4f9aa99e5d6b8fa5f366895546d` | **R01/B0, attested.** The record, the chain, the single writer. **Import it. Never copy, never re-implement, never widen its address grammar.** |
| `instrument.py` | `159c78c12328c8fbcc841b19d52570f99e90edaebf184e6bbb3e10b8ba4bca6b` | B1+B2 adapter: read allowlist, write allowlist, centre guard, `prompt_desk`, `read_to_marker` |
| `walker.py` | `5889160a15c5bc6949c6cd65726aeb609d4ca54efa3f2702229da5a675a002e9` | B1 read-only walker; `DESK_GATES`, `DESK_ADDRESSES`, `COURSE` live here |
| `lens.py` | `ad46b895dc3ceb68379467d8c9b642affcfc1b214633a1de9f89d39240fd269a` | Pi adapter + §7 trust assertion, fail-closed; `DESK_BLOCKS` |
| `driver.py` | `397f93fc0ae01ab09ab21d22b63655546a760ab35f5138055aa9c4c999f01cf2` | **B2, attested.** `boot()` / `take_turn()` / `advance()` — the code path this round steps |
| `dialects.py` | `9ebc6d314bd265e5be14c9c22fb47a4b80f4fabab5c4a46dd3f9f1ca0e6a4208` | B1 status/verdict mapping |

The maps, as they stand (data, one place to change — never string literals in logic):
`DESK_GATES = {S:x, G:y, Q:z, P:a, V:b}` (Amihai's word, hold B1-4 closed) ·
`DESK_ADDRESSES = {S:"", G:"G", Q:"Q", P:"P", V:"V"}` · `COURSE = ("S","G","Q","P","V")`.

### 3.2 The ledger, live (unchanged since B0 closed)

`/home/deploy/the-cell/state/gates.jsonl` — **one** record: gate `x`, address `""`, `prev_hash=GENESIS`,
`state=attested`, `mark=emergent`, `attestation_ref "Start from Not Knowing"`. Fingerprint
`6989a742f57ec60a54d44062bad3fe9c6d2df28e66e92de96c1336be3a6539c3`. That record is **Amihai's plant, written
by his hand at the TTY** — it is the signless true start (Appendix D.7), and it is why `address ""` with no
sign is the correct and only shape for it.

### 3.3 THE EQUATION BYTES — enumerated mechanically this session, and it is a trap that would have broken a naive check

The five equations do **not** have one byte form across his sources. Every distinct form found in the two
held documents, extracted by script (never transcribed by eye), with the sha256 of the exact string:

| Phase | Byte form (verbatim) | sha256 of the string | Where it appears | Non-ASCII codepoints |
|---|---|---|---|---|
| S | `S = ∞0 → ?` | `de0b90963d6110bf2092013401576c5ccb71751a8a7c9e3ab900a481c1dbfb1d` | Codex §1.3 L14 · Codex §3.1 L257 · AppD D.1 L24 | U+221E U+2192 |
| S | `S=∞0→?` | `4fb171bab276a63cf5dd04a42a92ef6ceef41fa9b7ae1f71c0b74f5e14b13250` | AppD D.14 L205 (prefixed `CELL: `, suffixed ` (c)` for centre) | U+221E U+2192 |
| G | `G = α ≡ {α'}` | `c2b0ed6eb2f0b8ce737b4656929e0b4bea1903d2071eca13d7961a99744a5c7e` | Codex §1.3 L15 · Codex §3.1 L258 | U+03B1 U+2261 U+03B1 |
| G | `G=α≡{α'}` | `98950e70a7de42c8d8b2eb2ecc0fc4b2e93833124d075a11931b570619490656` | AppD D.14 L205 | U+03B1 U+2261 U+03B1 |
| G | `G = α ≡ {α'} Q = φ ⋂ Ω` | `e498415fc85515b3debb5935b311c6f59db3743624977c0e6e5d92da7d7914d1` | AppD D.1 L21 — **extraction artifact** (two-column quincunx merged onto one line), NOT a form | — |
| Q | `Q = φ ⋂ Ω` | `cd20931fc7cd729a4de3779ccf63e63e627871a643cfc7c955961f9694a49bee` | Codex §1.3 L16 · Codex §3.1 L259 | U+03C6 **U+22C2** U+03A9 |
| Q | `Q=φ⋂Ω` | `6e0609332484796cd5d584f2966511d94c2a459f6098a37b6b1313393f9a82f0` | AppD D.14 L205 | U+03C6 **U+22C2** U+03A9 |
| P | `P = δE/δV → ∇` | `8175a49a811b0fb0402da736e404c341662fc970dbd327a6439efbb670f0ef49` | Codex §1.3 L17 · Codex §3.1 L260 | U+03B4 U+03B4 U+2192 U+2207 |
| P | `P=δE/δV→∇` | `ae9433ec8ed4a190f7d7483c795762005217c0181c5bb7ba99f1977593261ee0` | AppD D.14 L205 | U+03B4 U+03B4 U+2192 U+2207 |
| **V** | `V = (L ∩ G → B'') → ∞0'` | `7c8305fa45c203b50ac5ceb91cb85ac80722b8d0fb2eaed01988a1764eb65177` | Codex §3.1 L261 (the Constitutional Block) | **U+2229** U+2192 U+2192 U+221E + ASCII `'` |
| **V** | `V=(L⋂G→B'')→∞0′` | `05101fd680e1d139487e3450ff751e4ab384dd0760547e2aafb9cc4cc8c5314a` | AppD D.14 L205 (the Block, extended) | **U+22C2** U+2192 U+2192 U+221E **U+2032** |
| V | `V = (L ∩ G → B'') → ∞0' (constitutional form)` | `6a89f27c9f35c50f55f9cab7ecd505411aef5c923465fc203ac023b8b1b1c6dc` | Codex §1.3 L19 — the label ` (constitutional form)` is the Codex's own annotation, **not part of the equation** | — |
| V | `V = L ⋂ G → ∞ (public form)` | `9b3f8a068966d191f7ac4151dc0a565fbd88248db2e2777ecc6f1dd734b4c9b9` | Codex §1.3 L18 — the **public form**, a distinct compression the Codex itself labels | U+22C2 U+2192 U+221E |
| V | `V = (L⋂G→B'') → ∞0′ P = δE/δV → ∇` | `24361ca4a367dbfc9e91c1f565d320ec983df24e42e84031d488b0f040c4a99f` | AppD D.1 L27 — **extraction artifact**, NOT a form | — |

**Three real axes of variance, and one that is not:**

1. **Intersection glyph:** `∩` `U+2229` (Codex §3.1) vs `⋂` `U+22C2` (Appendix D, and Codex §1.3 for Q).
2. **Prime:** ASCII `'` `U+0027` (Codex) vs `′` `U+2032` (Appendix D's `∞0′`).
3. **Spacing:** the spaced reading form vs the compact **Block** form (`P = δE/δV → ∇` vs `P=δE/δV→∇`).
4. **Not an axis:** the merged two-column lines above are artifacts of the HTML→text extraction. They are
   **not** equation forms, and a check that accepts them would be accepting a rendering accident as canon.

**The rule that follows, and it is binding:** `EQUATION_FORMS` **enumerates** accepted byte forms — each with
its source, its section, its line and its sha256 — and the check compares bytes against that table. It
**never normalises**: folding `⋂ → ∩`, `′ → '` or collapsing whitespace would itself be *renaming an L1
symbol*, which is the exact thing D.12's syntax check forbids (*"No L1 symbol added, renamed, or
paraphrased"*). A form outside the table is a **paraphrase → FAIL**, and the FAIL names the codepoint that
differs. The `(public form)` and `(constitutional form)` labels are recorded as **labels**, never as part of
the string. See hold **H-P4a-1**: if Amihai wants one canonical byte string, that is his to name and the
table becomes one row per phase.

### 3.4 The live desk state — the reason cell-scope checks are INCONCLUSIVE, not PASS

`~/.pi/agent/settings.json` is exactly `{"lastChangelogVersion": "0.84.2"}`
(sha `211c2f2bef438558…`), `~/.pi/skills` does not exist, **no Pi extension is installed, and no desk is
constituted per PRD §7.** So: `lens.assert_trust` fails closed for every desk on this box, the driver
refuses to boot live (that refusal is correct behaviour, proven in B2's live tier), and **every check that
needs a desk's announced surface must read INCONCLUSIVE.** Installing an extension to make a check pass is
forbidden (§7 of this commission).

### 3.5 The herdr dialect (canon — `rounds/R02-B1/commission.md` §3, do not re-derive)

Socket `/home/deploy/.config/herdr/herdr.sock` · envelope `{"id","method","params"}`, **all three required,
`id` MUST be a JSON string** (a non-string id is refused before dispatch) · results are tagged unions keyed
by `type` · `pane.wait_for_output` answers **`output_matched`** (`{type, pane_id, revision, matched_line,
read}`), *not* `pane_read` · the fence timeout error is literally `{"code":"timeout","message":"timed out
waiting for output match"}` · `agent.prompt`'s `target` is a **pane_id** · desks resolve by
**`PaneInfo.label`** and pane ids are volatile · **this build serves ONE request per connection** (a second
request on the same socket raises `BrokenPipeError`; the adapter's reconnect-per-call is load-bearing and
must never be "optimised" away).

### 3.6 Environment

Box python `3.12.3` at `/usr/bin/python3.12`. `node`/`pi` need `. ~/.nvm/nvm.sh` first. Execution is open to
you (`DSH_PERMISSION_MODE=danger-full-access`); run your own suite before handing over. No network beyond a
local AF_UNIX socket you bind yourself in a tempdir.

### 3.7 NINE THINGS THE VERIFIER'S OWN PACK PAID FOR WHILE IT WAS BEING BUILT

*The pack that will judge this round was written and accepted before this commission reached you (58/58
against a conforming reference implementation and two defective twins). Building it cost nine mistakes.
They are yours for free — every one of them would otherwise have cost this round a correction.*

1. **The trail must never share a path with the ledger.** The pack's first version handed the step session a
   trail path that happened to equal the ledger path; every symptom downstream (a `seq` of `None`, a chain
   that would not verify, 3 records where 13 belonged) came from that one line. Your artifact must
   **refuse a trail path equal to its ledger path**, explicitly, at construction.
2. **A lens id is `<parent><borrowed>`, parent FIRST.** Codex §3.2 lists, under G: *"GS α≡{α'} through
   openness"* — G's decoding examined through S's quality. So `AD-DRF-5` (*"Lens questions still target the
   parent output"*) means the question must target `OUTPUT_SYMBOL[id[0]]`. The pack reads it that way; a
   reading that takes the second letter as the parent will diverge and diverge is a FAIL.
3. **A one-line trail cannot decide a chain.** With a single line, "every line's `prev` matches its
   predecessor" is trivially true — the same shape as the 2026-08-27 defect where 10 000 records all
   claimed `prev_hash=GENESIS`. Require **two or more lines** before deciding chain integrity, and report
   `undecidable` below that. The same rule applies to your own suite.
4. **A text search for a depth cap finds its own pattern.** The pack's first `MAX_DEPTH|max_depth` regex
   matched the source line that *documents the check*, and flagged itself. Do the static scan **by AST**
   (`ast.Name` / `ast.Compare` / `ast.Subscript`), never by text — and the same for a sixth corruption code
   (scan `ast.Constant` strings, so a regex describing the codes is not mistaken for one).
5. **The table and the evaluation must not be able to drift apart.** In one defective twin an item was
   removed from `CHECKS` while its evaluation stayed, and the evaluator raised `KeyError` mid-session:
   one dropped line silently destroyed every downstream measurement. Assert at import time that the set of
   ids you evaluate **equals** the set of ids in `CHECKS` — a self-consistency check, cheap and permanent.
6. **An exception inside the artifact is a FAIL, never an INCONCLUSIVE.** The verifier now classifies by
   whether your module names appear in the traceback. A raise cannot hide behind "the verifier could not
   look."
7. **A machine-authored record is identified by its `mark`, never by a `payload_ref` convention.** The pack's
   reference evaluator used the *fixture* convention (`payload_ref` starting `fixture:`) to tell machine
   records from human ones — and when it was pointed at the **real ledger on the box**, that made
   **Amihai's own plant** read as a machine record claiming the H side: `R10` and `R12` FAILed against the
   one record in this build that is unambiguously his. §5.1's `mark` is the field that carries this:
   `mechanical` is the machine's, `emergent` is the human's (his plant is `emergent` with a non-null
   `attestation_ref`, written at the TTY). Read provenance off `mark`, and never off a convention a test
   harness invented. *(Found by running the checks against the live ledger before you had written a line —
   the same live tier will be run against yours.)*
8. **`next` must be recomputed AFTER the step, not carried from the intent.** The commission asks each step
   to say *what it would do next and why*. Computed once, before the step, it says the step that has just
   happened — a stepped run that had just proposed gate `y` still announced *"take_turn G, because gate y is
   due"*. Recompute it from a fresh ledger replay in the `after` hook; the truthful answer there is
   *"wait_for_attestation — the gate does not open without a human attestation record."*
9. **A `payload_ref` is a scheme-prefixed locator, not necessarily a bare digest.** `R11` (*"provenance
   travels with B″, fingerprint hashes invariant only"*) was implemented as "must contain a 64-hex digest",
   which made a perfectly lawful reference (`demo:the-plant`) read as content in the ledger. The check that
   holds is the *shape of a reference*: `^[a-z][a-z0-9_.+-]*:[^\s]{1,200}$` — a scheme, a colon, an opaque
   body, no whitespace, no prose length. What §4.7.5 forbids is content, not a non-digest scheme.

*Lessons 8 and 9 were found by making the emission human-readable and reading it — not by a test. Which is
the point of the mode you are building: a readable trail is where a defect that passes every assertion
becomes visible.*

---

## 4. The step boundaries and the controller protocol — the commissioner's reading

**Implement exactly this. If you think a boundary is wrong, implement it and argue in the phase card.**

### 4.1 What counts as one step

A step is **one lawful operation of the cycle**, never a line of code and never a socket call:

| kind | The operation | address_before → address_after | zoom |
|---|---|---|---|
| `boot` | replay the chain, assert §7 trust for the walk | `""` → `""` | `none` |
| `position` | derive the standing place from the ledger | unchanged | `none` |
| `turn` | ONE desk turn: prompt → fence → read → propose | parent → the desk's address | `in`, sign `−`, letter = the desk |
| `advance` | try to open the gate after the last attested one | the due gate's address | `none` |
| `zoom_in` | **reserved, B3** — descend into a sub-cell | append a letter | `in`, `−` |
| `zoom_out` | **reserved, B3** — ascend to the father-frame | strip a letter | `out`, `+` |

`zoom_in`/`zoom_out` are **registry entries with no implementation** this round (K5).

### 4.2 The controller

```
class Stepper:                       # a protocol, not a base class you force on callers
    def before(self, intent):  ...   # -> "continue" | "stop"   — called BEFORE the first side effect
    def after(self, event):    ...   # -> "continue" | "stop"   — called AFTER the step, with the emission
```

* `before(intent)` receives the fully-formed intent — kind, desk, gate, `address_before`, the planned
  operation, the computed `turn_key`, and **why this step is next** — and is called **after** the guards and
  the ledger replay (so the intent is real) but **before** the first byte reaches the socket and before any
  record is written.
* `after(event)` receives the complete trail line, conformance report included.
* `"stop"` from either hook ends the session cleanly: the driver returns a status, raises nothing, writes no
  further record, and the trail's last line says what would have come next and why.
* **`stepper=None` is the default and must be a true no-op**: no trail file is created, no check runs, no
  branch changes behaviour. This is C1.
* The **blocking** step mode (wait for a human's Enter, print the emission) lives in the runner, not in the
  driver. **A keypress is not an attestation** and no code may treat it as one (K4).

### 4.3 Where the hooks go in `driver.py` (extend in place, diff-minimal)

1. `boot()` — `before` at entry; `after` with the boot result (position, due desk, trust table).
2. `take_turn()` — `before` **after** `assert_not_centre`, the trust assertion, the ledger replay and the
   `turn_key` computation, and **before** `instrument.prompt_desk`; `after` once the status dict exists
   (`proposed` | `already_recorded` | `already_walked` | `refused` | `incomplete`).
3. `advance()` — `before` with the intent (which gate it would open, or that the cycle is walked); `after`
   with the outcome, refusal record included.

No other behaviour of these three methods changes. The refusal record, the proposal record, the fence, the
`turn_key` derivation, the status strings: all exactly as attested in B2.

---

## 5. The emission and the trail

### 5.1 One JSONL line per step, append-only

Default path `os.environ.get("FRACTAL_TRAIL_DIR", "/home/deploy/the-cell/state/trail")` +
`<session_id>.jsonl` — **a parameter in every code path**, and your tests always pass a tempdir. Do not
create the canon directory during authoring.

```
{"trail_version":"1","session_id":"<hex12>","seq":0,"at":"<UTC ISO8601>","kind":"turn",
 "desk":"G","gate":"y","address_before":"","address_after":"G",
 "zoom":{"op":"in","sign":"-","letter":"G","derived_reading":false},
 "operation":"take_turn","intent_only":false,
 "context_in":{"records":2,"head":"<hash>","prior_outputs":[{"gate":"x","payload_ref":"…"}]},
 "decoded":{"slots":{"α":{"ref":"sha256:…","len":214},"{α'}":{"ref":"sha256:…","len":98}},
            "source":"desk_surface","operation_steps":["RECEIVE X","SEEK α","TEST ≡","FIND {α'}","VALIDATE Y"]},
 "compiled":{"symbol":"Y","gate":"y","landed":"record:<record_id>","payload_ref":"fenced:sha256:…"},
 "outcome":{"status":"proposed","record_id":"…","turn_key":"…"},
 "conformance":{"verdict":"INCONCLUSIVE","counts":{"PASS":21,"FAIL":0,"INCONCLUSIVE":12},"items":[…]},
 "next":{"action":"take_turn","desk":"Q","gate":"z","why":"gate y is proposed and unattested — the gate does not open without a human attestation record"},
 "ledger":{"path":"…","count":3,"head":"<hash>"},
 "prev_line_sha256":"<sha256 of the previous line's bytes, or null on seq 0>",
 "await":true}
```

* `seq` is gapless within a session. A gap is a defect, not a tolerance.
* `at` is an observation timestamp and **may never be an input to logic** (no ordering, no identity, no
  expiry derived from it).
* `intent_only: true` marks a line written by `before` whose step was stopped: `outcome.status =
  "not-taken"`.
* `prev_line_sha256` is **integrity only**. It is not `prev_hash`, it carries no gate authority, and no
  code may promote a trail line to a record.

### 5.2 The trail is a decoding, not a transcript (D12)

`decoded.slots` names **which symbol of the phase's equation was filled** and gives a **reference** to the
bytes that filled it (`sha256` + length) — never the bytes. `decoded.operation_steps` lists the numbered
decoding operation for that phase, quoted from Codex §3.2, and marks which steps were **observed** as
performed vs **not observable**. `compiled` names the output symbol (`X Y Z A B/B″/∞0′`) and where it landed
(which record). If nothing lawful can be parsed from the desk's surface: `decoded.source = "absent"` and
every dependent check is INCONCLUSIVE.

### 5.3 The surface contract (`§3.6 Surface Emission Rules`) — how a decode becomes observable

A desk's answer is parsed against a **declared contract** derived from Codex §3.6: the constitutional block
(§3.1) · the active phase's compiled form with its decoding operation (§3.2) · the adaptive context chain
in/out (§3.3) · the decoder rules (§3.4) · resolved symbols (§1.9). Ship the parser and the contract as
**data**; prove it on fixtures: a lawful surface (parses, slots filled), a paraphrased-equation surface
(FAIL, by item id), a surface with a sixth corruption code (FAIL), and **no surface at all** (INCONCLUSIVE).
The contract is what P4b's desk bundles will be written against — so it is a declared interface, versioned,
in one place.

---

## 6. The checks, made mechanical — three sources, kept visibly separate

Three families, **separately numbered so nothing drifts the source's own numbering** (D14's jacket):

| Family | id prefix | Source | Count |
|---|---|---|---|
| Appendix D validation | `AD-SYN-n` · `AD-SEM-n` · `AD-DRF-n` | Appendix D **§D.12**, verbatim | 5 · 5 · 5 |
| Codex validation protocol | `CX-SYN-n` · `CX-SEM-n` · `CX-DRF-n` | Codex **§3.5**, verbatim | 6 · 6 · 6 |
| Decoder rules, checkable form | `R1` … `R13` | Codex **§3.4**, verbatim — **keep the source's own numbering, never renumber** | 13 |
| The D12 pair | `DC-DECODE` · `DC-COMPILE` | his D12 + Codex §3.2/§3.3 | 2 |

Every item is a record with: `id` · `source` (document + section) · `citation` (the source line, verbatim) ·
`scope` ∈ `static` | `cell` | `step` | `session` · `verdict` ∈ `PASS` | `FAIL` | `INCONCLUSIVE` ·
`evidence` (what was actually observed — a path, a byte count, a sha, a record id) · `reason` (required
whenever the verdict is not PASS) · `derived` (`true` only for an item this artifact adds; each such item
must also appear in the divergence log).

**Scope, precisely:**

* `static` — decided by reading the artifact's **own source and data tables** (AST or text): no depth cap,
  the corruption codes are exactly the five and no sixth exists anywhere, `+`/`−` never appears inside an
  equation constant, the alphabet is a data table, no root assumption. Evaluated once per session, and
  **re-emitted by reference** in each step (never silently omitted).
* `cell` — decided by observing the cell: exactly one centre + four corners (4+1, never 3+1, never 6+1), the
  five equations verbatim from the enumerated byte table, the announced surface lawful. **INCONCLUSIVE on
  this box** (§3.4).
* `step` — decided from the step event + the ledger replay: phase order, address/zoom/sign coherence,
  context flowing father → daughter, the true start signless, the compiled symbol present, a closing V
  carrying `∞0′`.
* `session` — an item that no step could decide alone: e.g. *no decoding step omitted or reordered* across
  the whole walk. **An item that never reached PASS in any step is reported INCONCLUSIVE for the session —
  never PASS by absence of failure.**

**The session verdict:** `PASS` only if every item reached PASS at least once and no item ever FAILed;
`FAIL` if any item ever FAILed; otherwise `INCONCLUSIVE`, listing every item that never decided. **Silence
is never a pass.**

**Two checks that must refuse to be answered by the machine** (K3) — implement them as permanent
INCONCLUSIVE with the reason stated at the site: whether an `α` is *the* essence (the click), and whether an
`∞0′` question is *more alive* than the `X` it came from. The step mode may check that the slot is **filled
and referenced**, never that it is **true**.

---

## 7. Prohibitions — the load-bearing part of this round

1. **Never the centre.** No code path, docstring, example or fixture writes to the podium / desk S.
2. **Never an attestation.** `state:"attested"` and a non-null `attestation_ref` stay unreachable. A TTY
   keypress that continues a step is **not** an attestation and nothing may derive one from it.
3. **Never the live socket** `/home/deploy/.config/herdr/herdr.sock`, never `~/.pi` (no `pi install`, no
   settings edit — do not constitute a desk to make a check pass), never
   `/home/deploy/the-cell/state/` (both `gates.jsonl` **and** the trail dir). Tests bind their own AF_UNIX
   socket and write to tempdirs.
4. **Never re-implement** B0's ledger, B0's address grammar, or B2's turn logic. Extend in place,
   diff-minimal, one implementation only.
5. **Never normalise a symbol** to make an equation match. Enumerate accepted byte forms with source + sha.
6. **Never invent** an L1 symbol, a decoding operation, or a sixth corruption code — and never renumber
   `R1–R13`. Anything you add is `derived`, separately numbered, and in the divergence log.
7. **Never judge authenticity.** Structural verdicts only; INCONCLUSIVE where the click would be required.
8. **Never put content in the trail.** References only (`sha256` + length).
9. **No LLM, no third-party package, no network beyond your own socket, no git, no sleeping inside a step.**
10. **Phase card = predictions only.** No "✅", no "passed", no "verified", no statement that anything ran.
    If your own run reveals a bug, fix it silently and keep the card predictive.

---

## 8. Holds — declare them, never guess them

| id | The hold | The machine's proposal (yours to argue) |
|---|---|---|
| **H-P4a-1** | The five equations have **two authoritative byte forms** and a third labelled *public form* (§3.3) | Enumerate both authoritative forms with source + sha; a third form FAILs; never normalise. **Amihai's to settle** if he wants one canonical byte string. |
| **H-P4a-2** | The **address word convention** — Appendix D.3 says append (`S → SG → SGQ`, left-to-right = outer → inner); his spoken form was the law's relational phrasing (`SG` = *S within G*). Both pass B0's regex, so the regex cannot enforce meaning | A **declared parameter** in one data table; **no logic may depend on which end is deep.** His word settles the convention; the code must not need it to run. |
| **H-P4a-3** | A signed path `+^k·(−x₁)…(−x_m)` **cannot** be stored in the attested `address` field (executed: `'-P-Q-P'`, `'+-G'`, `'++-P-Q'` all REJECT) | The step event carries the signed path in its **own** field (`zoom.sign`, `zoom.path`); `address` keeps the bare node word; **B0 stays untouched.** |
| **H-P4a-4** | No desk is constituted on this box, so cell-scope checks cannot pass | INCONCLUSIVE is the correct live verdict; P4b (desk bundles) is what turns it into PASS. Do not fake a bundle. |
| **H-P4a-5** | `block_version` is still `""` (carried H-B2-2 — the read surface exposes no block identity) | Keep `""`, keep it in the `turn_key`, state the limit; do not invent an identity. |
| **H-P4a-6** | The `agent_prompted` success shape is still schema-only and **inert** (carried H-B2-4-live) | Unchanged: `prompt_desk` discards it and the answer comes from the fenced read. |
| **H-P4a-7** | **The name of this mode is Amihai's to give** (`PLAN-ADDENDUM` §E.8) | `step` is a working handle. No display name may enter logic or the trail schema; presentation stays renamable. |

---

## 9. Deliverables, and the names the verifier will bind to

Everything in `/home/deploy/the-cell/rounds/P4a-step-mode/authored/`.

1. **`step.py`** — the stepping surface: the controller protocol, the trail writer/reader, the step-kind
   registry (with `zoom_in`/`zoom_out` reserved), the auto-continue controller, and the runner that can walk
   a session (C1, C2, C3, C5, K5).
2. **`conformance.py`** — the checks of §6: the item table with verbatim citations, the evaluator, the
   session aggregator (C4, K2, K3, K6).
3. **`surface.py`** — the §3.6 surface contract + parser: context in/out, decoded slots by reference,
   compiled symbol (C3, §5.3, DC-DECODE/DC-COMPILE).
4. **`driver.py`** — **extended in place** with the three hook pairs of §4.3. Diff-minimal; behaviour
   unchanged when `stepper=None` (C1).
5. **`selftest.py`** — extended in place. Each test names the criterion or claim id it exercises and the
   quantity it measures; a timed test names the operation timed.
6. **`fixtures/`** — JSON: a lawful desk surface · a paraphrased-equation surface · a surface with a sixth
   corruption code · a missing-`∞0′` V · a `3+1` cell · a full stepped `y→z→a→b` session trail · a torn-line
   trail. Every fake herdr response speaks the live dialect of §3.5 (a non-string `id` is refused;
   `pane.wait_for_output` answers `output_matched`).
7. **`phase-card.md`** — criteria and claims by id, the binding map below with your real names, your
   **predictions**, the check-item table (id → source → scope), the **D14 divergence log**, holds
   H-P4a-1…7 each with your proposal, and every assumption you could not verify.

### 9.1 Binding — the verifier's spec will name these

```
step_module            step
stepper_protocol       Stepper              # before(intent) / after(event) -> "continue" | "stop"
auto_stepper           AutoStepper          # auto-continue; behaviour-neutral
trail_writer           StepTrail            # append-only JSONL, one line per step, prev_line_sha256
trail_reader           read_trail           # read_trail(path) -> lines; a torn last line is DAMAGED
step_kinds             STEP_KINDS           # registry; zoom_in / zoom_out reserved, unimplemented
runner                 run_session          # walks a session under a Stepper; no sleeping in the driver
conformance_module     conformance
check_table            CHECKS               # id -> {source, citation, scope}
evaluate_fn            evaluate             # evaluate(context) -> report {verdict, counts, items}
session_aggregate_fn   aggregate            # session verdict: never PASS by absence of failure
equation_forms         EQUATION_FORMS       # enumerated byte forms, each with source + sha256
corruption_codes       CORRUPTION_CODES     # exactly L1 L2 L3 L4 V∅, frozen
surface_module         surface
surface_contract       SURFACE_CONTRACT     # the §3.6 contract, as data
surface_parse_fn       parse_surface        # -> {context_in, decoded, compiled} references only
driver_module          driver
driver_class           Driver               # Driver(…, stepper=None) — None is a true no-op
turn_method            take_turn            # unchanged behaviour; hooks per §4.3
advance_method         advance
boot_method            boot
```

### 9.2 How the criteria will actually be judged

A fake herdr server (the verifier's, which refuses a non-string `id`) replays a cell whose desks answer
prompts, and **records every method sent**. Then: **C1** the same walk run three ways (unstepped, stepped
auto, and B2's attested driver) compared on ledger bytes and socket sequence, plus an AST read for a second
turn loop · **C2** a controller that stops at each boundary in turn, with the wire log and the ledger checked
for silence · **C3** every trail line validated field-by-field against §5.1, plus a grep of the entire trail
for any byte of the desk's answer text · **C4** the pack recomputes all 15 + 18 + 13 + 2 items independently
and diffs them against yours, then runs the nine defective twins · **C5** a fresh-process restart, a
truncated trail line, and a projection-compare of `gates.jsonl` between stepped and unstepped runs.

### 9.3 What the verifier will do that you cannot

Recompute every conformance verdict with a **separate implementation** and diff it against yours; run your
checks against a live box where **no desk is constituted**, where the correct answer is INCONCLUSIVE; and
push `∞0′ → ‖` through every string field of the trail and every parsed slot. Anything that disagrees comes
back as one surgical correction with the exact bytes.

---

## 10. Budget

**One authoring generation.** Corrections limited to **two**, each surgical (exact command, traceback,
bytes, hashes). Exceeding either limit is a **HOLD surfaced to Amihai**, never a silent continue. If a
requirement here is impossible or self-contradictory, say so in the phase card and implement your best
reading — do not widen the round.
