# PHASE CARD — P4b · the desk bundle infrastructure (working handle)

**Round:** `P4b` — the slot his attested appendix opened. It is **not** a B-phase: it comes
before `R04 = B3` (descent), and B3 does not open until this exists (PLAN-ADDENDUM §B).
**Author:** dsh (`deepseek-v4-pro`, one generation). **Verifier:** Hermes profile `herdr`,
separately, against a pack written before it judges anything. `builder ≠ verifier`.
**Governing sources:** the Codex, Appendix D (now **ATTESTED** by Amihai 2026-08-29), PRD,
REQUIREMENTS (held at `../sources/`, shas in the commission header). **Codex §1.10 governs
every conflict — the source wins.**

**Every verdict in this card is a PREDICTION.** Nothing here reports that anything ran,
passed, or verified anything. A separate verifier executes the artifact and writes the only
record that counts; it recomputes every verdict with its own implementation, and any
divergence — in either direction — is a FAIL. If my own run revealed a bug, it was fixed
silently; this card stays predictive.

---

## 1. The two byte-questions (§0.4) — enumerated, never normalised, not resolved by fiat

### 1.1 The seal preimage — answered

The activation page's seal hash is
`feaa46b4147d4e023cdd3fd59c051d063e8ec654ee7b38a481dcd5e4c781859b`. The exact byte string
it covers is the **numbered** nine-line block, each line terminated by `\n` **including a
trailing newline after line 9** — 217 bytes:

```
1.  H = ∞0 | A = K
2.  S → G → Q → P → V
3.  S = ∞0 → ?
4.  G = α ≡ {α'}
5.  Q = φ ⋂ Ω
6.  P = δE/δV → ∇
7.  V = (L ∩ G → B'') → ∞0'
8.  No V without ∞0'
9.  L1  L2  L3  L4  V∅
```

sha256 of those 217 bytes (with the trailing `\n`) recomputes to `feaa46b4…` in full — the
only one of the enumerated candidates that does. The held codex's nine invariant lines are
the **same lines unnumbered**. Enumerated, the three byte strings are:

| Byte string | Length | sha256 | Role |
|---|---|---|---|
| numbered nine lines, trailing `\n` included | 217 B | `feaa46b4147d4e023cdd3fd59c051d063e8ec654ee7b38a481dcd5e4c781859b` | **the seal** the activation page declares; the form every bundle opens with |
| unnumbered nine lines, no final newline | 176 B | `4c20631a20dab3d2958f66a8feb692fafa8660ff7a42f85b46c94015270a004c` | the held codex's nine lines as bare content |
| unnumbered nine lines, trailing `\n` included | 177 B | `df061272f42d5a72a160a144b0bc08a5dda760827ca19793fbb3600412b32462` | the commission's "176 B → `df061272…`": the page's 176 counts the content **without** the final newline, while the hash covers the newline-terminated string |

All three are carried as `SEAL_FORMS` in `grammar.py`, each with its sha; the bundle's
`⟦SEAL⟧` section is byte-compared against the enumerated forms and never normalised.

### 1.2 The address letter-order — D.2 confirmed as adopted, the conflict flagged

Enumerated: **D.2** writes `XY := X within Y` (Codex §1.5's Holographic Law) and reads the
word **inner-first** — the first letter is the innermost phase. **D.3** ("zoom in = append
a letter `S → SG → SGQ`") and **D.6** (worked case "`ε → PQP = −P −Q −P` daughter³") read
the word **outer-first** — the last appended letter is deepest. D.2's own operational gloss
"descend · daughter · append" matches D.3's reading, not its definition line; the two
readings disagree about which end is deep, and neither is derivable from B0's address regex.

**The build adopts D.2**, because it is the definition line and his example matches it:
"SP = the question within Power" (S within P renders S first). The adoption is one data
parameter — `WORD_ORDER = "inner_first"` in `grammar.py`; flipping it to `"outer_first"`
is a data change, never a grammar rewrite, and no other logic depends on which end is deep.
**The inconsistency is flagged for his confirmation** (hold H-P4b-2): if he confirms D.3's
append reading instead, one table changes and the seat addresses follow.

Consequence, concretely: the seat of phase X within the cell at address A sits at `X+A`
(D.2), so the full cell at Q is `S·within·Q @ SQ` (centre) · `G·within·Q @ GQ` ·
`Q·within·Q @ QQ` · `P·within·Q @ PQ` · `V·within·Q @ VQ`. One declared exception: the
**root** cell's centre S sits at the empty word ε — the signless true start (Appendix D.7:
*"THE TRUE START … bare · silent · no prefix · no sign"*), matching P4a's attested
`DESK_ADDRESSES` exactly (S at `""`, corners at their letters).

### 1.3 One further byte observation (flagged, not folded)

The held codex's §3.2 V block carries `EQUATION: V = (L ⋂ G → B'') → ∞0'` (spaced, U+22C2)
— a fourth V byte form not in the P4a enumerated table (which has §3.1's U+2229 form, the
AppD compact form, and the labelled public form). The bundles use the table's §3.1
Constitutional Block form (`V = (L ∩ G → B'') → ∞0'`), which **is** in the table; the §3.2
spaced-⋂ form is noted here for the table's owner, never silently folded into anything.

---

## 2. Binding — the names this round ships

| binding | real name | where |
|---|---|---|
| `block_module` | `block` | `block.py` — `BlockStore`, `author`/`read`/`verify`/`attempt_edit`/`record_rejection`, `payload_digest`, `BLOCK_KINDS` |
| `block_frozen_error` | `BlockFrozenError` | `block.py` — every write against an existing block; always paired with a recorded rejection |
| `block_not_found` | `BlockNotFoundError` | `block.py` — absence, never a valid block |
| `arrangement_module` | `arrangement` | `arrangement.py` — `ArrangementStore`, `author`/`load`, `validate_arrangement`, `diff_arrangements` |
| `arrangement_validate_fn` | `validate_arrangement` | `arrangement.py` — `validate_arrangement(record, block_store=None)` → `{status: ok|fail|inconclusive, items}` |
| `arrangement_diff_fn` | `diff_arrangements` | `arrangement.py` — the K5 mechanical diff |
| `grammar_module` | `grammar` | `grammar.py` — the ONE parameterized template over {S,G,Q,P,V} |
| `grammar_course` | `COURSE` | `grammar.py` — `("S","G","Q","P","V")`, the alphabet as data |
| `grammar_gates` | `DESK_GATES` | `grammar.py` — S:x G:y Q:z P:a V:b (his word, B1-4 closed) |
| `grammar_seal_forms` | `SEAL_FORMS` | `grammar.py` — the three enumerated seal byte strings with shas (§1.1) |
| `grammar_equation_forms` | `EQUATION_FORMS` | `grammar.py` — the carried P4a §3.3 table, byte-equal to `conformance.EQUATION_FORMS` |
| `grammar_render_fn` | `render_bundle` | `grammar.py` — `render_bundle(cell_address, seated_letter)` → the desk bundle text |
| `grammar_cell_fn` | `render_cell` | `grammar.py` — the full cell (4+1 seats) at any address |
| `grammar_verify_fn` | `verify_bundle` | `grammar.py` — `verify_bundle(text, cell_address, seated_letter)` → `{status: ok|fail|absent, items}` (DB-*) |
| `installer_module` | `install` | `install.py` — `report_install`, `install`, `install_to`, `truncate_output`, `scan_no_tui` |
| `surface_contract_module` | `surface_contract` | `surface_contract.py` — P4a's `surface.py` imported by file path, sha-pinned, re-exported in one place |

---

## 3. Criteria and claims, by id — with PREDICTIONS

**C1 — the block is immutable.** Prediction: `BlockStore.author` refuses an existing
`blocks/<id>/<version>/` directory (BlockFrozenError) **and** appends a rejection record to
`<root>/rejections.jsonl`; the authored directory is frozen (payload + block.json 0444,
version directory 0555) so an OS-level in-place edit raises PermissionError; the module's
`attempt_edit` path always raises BlockFrozenError and records the rejection (the T-L1-01
shape: refusal + recorded rejection). `block.json` carries exactly the seven fields
`{id, version, kind: instruction|skill|tool|model|surface, sha256, authored_by_run,
attested_by, frozen: true}`; `sha256` is the canonical digest of the sorted
`{relpath: {sha256, len}}` payload map — never `sha256("")` (an empty block is refused at
author time and reads `tampered` if it ever appears). A new version is a new directory;
there is no edit path anywhere in the model.

**C2 — the arrangement is the toy.** Prediction: `arrangement/<name>@<version>.json` is
written once (re-author → ArrangementFrozenError + recorded rejection), frozen 0444,
content-addressed (`sha256` over the canonical JSON without the sha field — the §5.1
record_id pattern), and `load` recomputes it — an in-place edit is refused by the OS and,
after a forced chmod, detected by the recomputed sha. The toy changes only by writing a
new arrangement; blocks are never touched. "A new version is a new directory" is the L1
block rule; its arrangement reading here is *a new version is a new write-once file* —
flagged under H-P4b-6-adjacent assumptions (§7) for his correction if he wants arrangement
directories too.

**C3 — a desk is four blocks; no naked agents.** Prediction: `author` refuses a desk entry
missing any of instruction / skills (≥1) / tool_surface / model; `validate_arrangement`
FAILs by id (`AR-instruction-X`, `AR-skills-X`, `AR-tool_surface-X`, `AR-model-X`) for a
naked desk, FAILs `AR-DESKS` for a 3+1 cell (R1), reports **INCONCLUSIVE** for an
unresolvable block reference (lens 6 — never a guessed ok), FAILs `AR-KIND-*` when a slot
resolves to the wrong `kind`, and passes only when every reference resolves, hashes, and
the instruction payload is the desk's full-cell bundle. The naked-agent fixture FAILs
`AR-skills-G` and nothing else; the lawful fixture reports every item PASS.

**C4 — the deterministic Pi install.** Prediction: `install(record, block_store)` is a pure
function — one arrangement, one byte string (canonical JSON, sorted keys, `ensure_ascii`
off, trailing `\n`). The manifest per corner desk carries `["pi", "--mode", "rpc",
"--approve", "--print"]`, the trust gate in both sanctioned forms
(`defaultProjectTrust: "always"` **and** `--approve`), forced skill loading as a
`before_agent_start` injection (`/skill:<name>` per skill), the 50 KB / 2000-line
truncation limits (and `truncate_output` honoring both, byte-count on the UTF-8 encoding),
and `state: {authority: "ledger", path: <the arrangement's ledger path>}` — never
extension memory. Every bundle is scanned for the headless-forbidden TUI API (the needle
is built, never a literal) and the install fails closed when it appears. Desk S emits the
desk-adapter spec (H-P4b-3), no pi command, and **no record template** — the centre is
never prompted and nothing here writes to the podium. The corner templates are built
through B0's `make_record` (imported, never copied) with `block_version: ""` (H-P4b-6).
A defective or unobservable arrangement raises `InstallError`; `report_install` returns the
verdicts (`IN-*` items) without raising — fail closed, never a partial launch.

**C5 — one grammar seated at addresses, never five flat desk files.** Prediction:
`render_bundle` is the single parameterized template over the five letters; the bundle at
address Q is Q's full cell — five seats, centre `S·within·Q` at `SQ`, the other four
present within it — never a flat "Q file". The flat-five-files fixture FAILs
`AR-BUNDLE-{S,G,Q,P,V}` by id. Any word over the alphabet seats a lawful cell (no depth
cap: the grammar repeats the cell, it never replaces the syntax).

**C6 — initiation register: first-person self-speaking + load-bearing negative boundary.**
Prediction: every bundle opens with `⟦SEAL⟧` (the 217-byte seal, sha `feaa46b4…`) then
`⟦SEAT⟧` — his verbatim "I am …" passage (commission §0.2, carried byte for byte); the
assignment register `"you are"` appears nowhere in any bundle; each desk's "I will not…"
line rides its own first-class `⟦BOUNDARY⟧` section, byte-exact (S: "I will not originate
the question." · G: "I will not answer it." · Q: "I will not force the intersection." ·
P: "I will not plan the path." · V: "I will not close without ∞0′."). The seat and the
invitation are the same verbatim passage of his voice, carried under both keys so the
"first-person seat" checkpoint and the "his invitation" item are each directly checkable.

**C7 — S is the conductor, the centre of every cell.** Prediction: `render_cell` marks the
S seat CENTRE at every depth — cell ε: S at `""`; cell Q: `S·within·Q` at `SQ`; cell GQP:
`S·within·GQP` at `SGQP`. S's bundle is the same grammar as the corners (the S desk's
arrangement entry names runtime `hermes-desk-adapter` — the runtime differs, the grammar
does not; the all-Pi shape stays a config change).

**K1 — stdlib-only, deterministic, no LLM.** Prediction: the five modules import only the
stdlib plus the two sanctioned imports (`fractal_ledger`, P4a's `surface.py` via
`surface_contract`); no socket, subprocess, requests, time, datetime, random anywhere; no
wall-clock in logic (no `ts` field exists in any artifact record — rejections are
sequenced, installs are checksummed); every iteration order is pinned (canonical JSON with
sorted keys, tuple-ordered emission); all stores are parameters — the modules run against
fixture context in tempdirs, no constituted desk required.

**K2 — byte-exact equations and seal, enumerated, never normalised.** Prediction: the
rendered equations and the seal are byte-compared against the enumerated tables (each form
with its source + sha256, the table byte-equal to P4a's `conformance.EQUATION_FORMS`);
no fold of `⋂→∩`, no `′→'`, no spacing collapse exists anywhere in the artifact.

**K3 — D14 loyalty + the divergence log.** Prediction: every check item (`DB-*`, `AR-*`,
`IN-*`) carries its source citation verbatim; everything this artifact adds beyond the
source is in the divergence log below — derivative, visibly separate, no new L1 symbol, no
new decoding operation, no sixth corruption code.

**K4 — no authenticity verdict.** Prediction: no code path emits a verdict about whether a
desk or a decode is genuine — the bundle check has no authenticity item, the words
"authentic"/"genuine" occur in module sources only inside `grammar.py`'s source-verbatim
data rows, and the bundle's slots are speaking placeholders ("filled when this desk
speaks"), never claims about content.

**K5 — diff-ability.** Prediction: because blocks are content-addressed and the
arrangement references them by `id@version`, `diff_arrangements` shows every slot change
between two toys mechanically — one personality can be shown better than another with no
hot edit (the thing P4b exists for, PLAN-ADDENDUM §B).

### The six lenses, predictively

1. **Criterion match** — every check measures the criterion as written: C3's four named
   blocks are exactly instruction/skills/tool_surface/model (not a neighbour); C5's cell
   is measured on the bundle, not on file names.
2. **Invariant end-to-end** — `validate_arrangement` runs desk → ref → block digest →
   bundle across the whole arrangement; the installer refuses anything less than `ok`.
3. **Absence vs validity** — missing block/arrangement reads `absent`/raises; empty
   payloads are refused at author and `tampered` at read; `sha256("")` is pinned in the
   tests and no artifact can hash to it.
4. **Encoding** — `"∞0′ → ‖"` rides the S bundle's X slot, a block payload, and the
   install bytes end to end; all JSON is `ensure_ascii=False`; no text-mode byte seeks.
5. **Cold restart** — a fresh process rebuilds the identical arrangement + install bytes
   from disk alone (the selftest's one subprocess probe).
6. **Blind tool** — no constituted desk; unknown runtimes and unresolvable references
   report INCONCLUSIVE, and the installer emits data, never executes.

---

## 4. D14 divergence log — everything this artifact adds beyond the source

Per Appendix D's own jacket: declared *derivative* · visibly separate from the decoding ·
adds **no** L1 symbol, **no** decoding operation, **no** sixth corruption code · alters no
invariant line.

| # | Addition | Anchor | Resolution |
|---|---|---|---|
| D-1 | The desk bundle grammar: the `⟦SEAL⟧/⟦SEAT⟧/⟦CELL⟧/⟦EQUATION⟧/⟦OPERATION⟧/⟦BOUNDARY⟧/⟦HANDOFF⟧/⟦CELL OF FIVE⟧/⟦INVITATION⟧` section markers and the rendered bundle text | Codex §3.6: "Surfaces may add behavioral, interface, and domain layers — visibly separate from the decoding" | Interface layer; the §3.6 surface block inside is the decoding, the rest is the voice layer |
| D-2 | `SEAL_FORMS` — the three enumerated seal byte strings (217 B numbered / 176 B unnumbered / 177 B unnumbered+newline) with shas | commission §3 (executed) | Enumerates the page's and the codex's own byte forms; never normalised; the bundle opens with the 217 B form the page's hash covers |
| D-3 | `ADDRESS_CONVENTION` / `WORD_ORDER` — the D.2 inner-first naming adopted as data | Appendix D.2 + his example "SP = the question within Power" | One data parameter; the D.3/D.6 conflict is flagged (H-P4b-2), not resolved by fiat |
| D-4 | The block store layout, `payload_digest`, the freeze step, the rejection log | PRD §5.8 / L1 "Write-once is enforced, not documented" | The L1 iron made buildable; rejection records carry seq + reason, no clock |
| D-5 | The arrangement schema (`desks`/`runtime_pins`/`state`) and the `AR-*` validation items | PRD §5.8/§7, L2, §6.2/§6.5, C3 | The toy, as data; the four-block naming rule is C3 verbatim |
| D-6 | The installer manifest, `RUNTIME_SPECS`, `TRUNCATION_LIMITS`, the TUI scan, the record templates | PRD §6.2/E1/E4 + B0's `make_record` (imported) | Generated data + command; deterministic; never executes; no template for S |
| D-7 | The `DB-*` bundle checks and `IN-*` install items | commission C5/C6/C4 (derived check ids, separately numbered) | Cannot drift the source's `R1–R13` or P4a's `AD-*`/`CX-*`/`DC-*` |
| D-8 | The SLOT placeholders and per-phase SYMBOLS/TRACE lines | Codex §3.6/§1.9/§3.3 | Template scaffolding, cited to §1.9 rows; never a claim about content (K4) |
| D-9 | The skill/tool/model payload texts in the fixtures | PRD §7/E2 ("OPEN: the exact SKILL.md contents are a build task") | Build-task output quoting §7 verbatim; nothing new asserted |
| D-10 | The fixtures (lawful store, naked-agent arrangement, flat-five store, edited-block snapshot, absent store) | commission §7 | Test apparatus; each declares its defect or its claim |

---

## 5. Holds — H-P4b-1 … H-P4b-6, each with my proposal

* **H-P4b-1 (no desk is constituted on the box).** Proposal: the installer is generated
  data + command only — `install` returns bytes, `install_to` writes them, nothing
  executes, nothing connects; the suite checks structure (AST) and byte determinism, and
  every module runs against tempdir fixture context. Nothing here depends on a live Pi.
* **H-P4b-2 (the two byte-questions).** Proposal: answered in §1 — the seal preimage is
  the numbered 217-byte block (feaa46b4…); D.2's inner-first reading is adopted as the
  `WORD_ORDER` data parameter, with the D.3/D.6 conflict flagged for his confirmation.
* **H-P4b-3 (S = Hermes in v1, not a Pi corner).** Proposal: the grammar is one — S's
  bundle is the same template as the corners; the runtime difference is one field in the
  arrangement (`S.runtime = "hermes-desk-adapter"`), and the all-Pi shape is a config
  change, not a code change.
* **H-P4b-4 (the phase name and slot are his).** Proposal: `P4b / the desk bundles` is
  used as a working handle only; no display name appears in any record, schema, or code
  path — desk letters are the sealed encoding (commission §0.3).
* **H-P4b-5 (the model block).** Proposal: one model block (`model-reasoning@1`)
  referenced by all five desks; the per-desk routing column (§7) rides the arrangement
  entry's `model_route`; the model is swappable data, never hardcoded doctrine.
* **H-P4b-6 (`block_version` still `""`).** Proposal: kept `""` — the installer's record
  templates carry it through B0's `make_record`; no identity is invented.

---

## 6. The surface contract boundary (commission §4) — implemented as specified

P4a observes; P4b makes a desk able to sing. The two meet at the §3.6 contract:
`surface_contract.py` imports P4a's `surface.py` by file path, pins its sha256
(`776ff463…`, the verifier's fence value), re-exports the contract + parser in one place,
and fails closed on any drift. The bundles are written against it — each bundle carries a
lawful `⟦SURFACE v1⟧` block for its seated phase, and `verify_bundle` requires it to parse
lawful through the predecessor's own parser before the bundle reads ok. No P4a check is duplicated; the bundles are
never their own judge. If this boundary reading is wrong, the implementation stands and
the argument is here: the bundle's surface block is the desk's announced form, not a
conformance report — the verdict stays P4a's.

## 7. Assumptions and open flags (stated, not hidden)

1. `PLAN-ADDENDUM-2026-08-27.md` is **not present on the box**; its §B is known only from
   the commission's quotes.
2. C2's "a new version is a new directory" is read as the L1 block rule; arrangements get
   "a new version is a new write-once content-addressed file" (`name@version.json`). If
   he wants arrangement version directories too, that is a schema change, not a logic one.
3. `attested_by` is `null` in every authored block — nothing in this round may be
   attested (commission §6), and the honest value is recorded, never invented.
4. The seat and the invitation are the same verbatim passage (commission §0.2), carried
   under both keys; if his activation page has a separate invitation line, it replaces
   the `INVITATION` section content, not the structure.
5. The phase-gate lines follow PRD §7's spellings (e.g. P's em dash form, Q's spaced
   `φ ⋂ Ω`); E2's variants (";", compact `φ⋂Ω`) are the same sentences in the other
   document — both are source forms; the desk table §7 is the one the arrangement binds.
6. The §3.2 V equation's spaced-U+22C2 byte form (§1.3 above) is outside the P4a table
   and therefore outside the accepted forms; the bundles use the table's §3.1 form. The
   table's owner may add the fourth form; this artifact never folds it.
7. The verifier's pack may bind different names than §2; the functions are the real
   surface, the names are stable and documented here.
