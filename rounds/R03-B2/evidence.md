# EVIDENCE — R03 · B2 the driver (one cell, sequential)

*Written by Hermes (`herdr`) after **running** the authored artifact. This file is the only place where
"it works" may be said, and only next to the command that proved it. The words "looks correct" are
banned. dsh's own `Ran 32 tests … OK` is a hypothesis and is not evidence.*

## Environment

| | |
|---|---|
| Verified | 2026-08-27, 19:00–19:52 UTC |
| Fixture tier ran on | the hosted Hermes container, `Linux-6.12.91-fly-x86_64`, python `3.13.5` |
| Live tier ran on | the box (`srv1707555`, Ubuntu 24.04), python `3.12.3`, herdr **0.8.2 / protocol 20** |
| Artifact under test | `/home/deploy/the-cell/rounds/R03-B2/authored/`, staged byte-identical at `/opt/data/tmp/r03-b2/` |
| `driver.py` | sha256 `397f93fc0ae01ab09ab21d22b63655546a760ab35f5138055aa9c4c999f01cf2` (466 L) — **unchanged by correction 1** |
| `lens.py` | sha256 `ad46b895dc3ceb68379467d8c9b642affcfc1b214633a1de9f89d39240fd269a` (338 L) — **unchanged by correction 1** |
| `instrument.py` | audited at `04d755ccb90dc3dc0be8158fe9d0ae912f3cde541a86e658fc6d88dcf59eefd3` (717 L); **after correction 1: `159c78c12328c8fbcc841b19d52570f99e90edaebf184e6bbb3e10b8ba4bca6b` (725 L)** |
| `selftest.py` / `phase-card.md` | `d08f4fc5f704501f…` (1288 L) / `06924230a5f566d3…` (301 L); **after correction 1: `e0ac260f5c12e093…` (1359 L, 34 tests) / `80be74a35ff17d68…` (308 L)** |
| `walker.py` / `dialects.py` | **byte-identical to R02's attested files** (`5889160a15c5bc69…`, `9ebc6d314bd265e5…`) — not re-implemented |
| B0 module imported, never copied | `ledger/fractal_ledger.py` `b291e65967e0d1f9…` (R01, attested) |
| Commission | `rounds/R03-B2/commission.md` sha256 `d35ddfba364601f7e6b585a2027909959309bbd61ec9dee39713c7c1da183626` (22,351 B) |
| Criteria quoted from | canon `docs/fractal-herdr/PRD.md` sha256 `71ce2645078dd48f56fb7c2a8d916a1ffa70cb0db2bd74648093c8add8b1d99c` (commit `e50eb25`); drift check **in sync** before and after |
| Verifier instrument | `/opt/data/tools/deliverable-audit/` — B2 pack built this session: `probes/driver_socket.py`, `lenses_b2.py`, `specs/b2-driver.json` |
| Command | `python3 audit.py --spec specs/b2-driver.json --out evidence-raw.md` → exit 0, **7.90 s** (T0 bar 60 s) |

**The verifier was accepted before it judged.** `python3 selftest_b2.py` → **45/45**: the pack passes an
independently written conforming driver (`/opt/data/tmp/proving-b2/good/`, its own suite 10/10) and
**fails a deliberately defective one on all fifteen axes, naming each defect**
(`/opt/data/tmp/proving-b2/bad/`). The two older packs stayed green in the same session:
`selftest.py` **22/22** (B0), `selftest_b1.py` **38/38** (B1).

## Per-criterion result (§9 B2, as written)

| ID | Criterion (verbatim) | Command | Raw output (decisive lines) | Verdict |
|---|---|---|---|---|
| **C1** | a full S→G→Q→P→V cycle is walked with the human attesting each gate | `boot → take_turn(G,Q,P,V)`, an attestation record written by the fixture's human stand-in between each, against a private fake cell | gates=`x y y y y z z z z a a a a b b b`; proposals/gate=`{y:1, z:1, a:1, b:1}`; prompts=`['G','Q','P','V']`; three out-of-order attempts → `refused`, **0 prompts added**; final `advance()` → `complete`; wire writes = `['agent.prompt']` only | **PASS** |
| **C2** | no gate opens without an attestation record | `take_turn(G) → advance() ×2 → hollow attestation → take_turn(Q) → attestation → advance()` | `advance_1=refused`, `advance_2=refused`, **1 record written per refused call** (`[1,1,1,1]`), 4 distinct refusal `turn_key`s; an `attested` record with a **null** `attestation_ref` → still `refused`; out-of-order `take_turn` → `refused`, 0 prompts; after the human's word → `due`; driver-authored attested records = **0** | **PASS** |
| **C3** | a deliberately duplicated prompt produces one record | `take_turn(G)` twice in one process, once more in a **fresh subprocess**, and once against an already-`working` desk | `turn_key=a49024a39a419dc8…`; **records bearing it = 1**; statuses `proposed / already_recorded`; prompts on the wire `1 → 1 → 1`; child process → `already_recorded`, sent no prompt; working desk → 1 record, 1 prompt | **PASS** |
| **C4** | the skills-loaded assertion fails the boot when trust is missing | `boot()` against a Pi state mirroring the live box (`settings.json` = `{"lastChangelogVersion": "0.84.2"}`, no skills dir, no binary), then the shipped `DESK_BLOCKS`, then a constituted control | live-like Pi → `TrustError` stage `skills` verdict **`inconclusive`**; **zero write methods on the wire, zero requests, zero records**; a turn attempted after the failed boot also raises with zero writes; shipped `DESK_BLOCKS` → `TrustError` stage `instruction`; control → boots, turn `proposed`, exactly one write (`agent.prompt`) | **PASS** |

## Claimed capabilities (asserted by the author, measured here)

| ID | Claim (verbatim) | Raw output | Verdict |
|---|---|---|---|
| **K1** | prompt → fence → read → propose; the fence a unique end marker via `pane.wait_for_output`, never heuristic idle (§4.5) | one turn on the wire = `pane.list · pane.get · pane.get · agent.prompt · pane.wait_for_output` — exactly the five the phase card predicted; the prompt text **ends** with the fence instruction carrying `⟦END <turn_key>⟧`; the fence matches that exact marker as a `substring`, bounded `timeout_ms=60000`; `agent.wait` never used and the string `agent_status` appears nowhere in `driver.py`; desk ignores the marker → `incomplete`/0 records · truncated read → `incomplete`/0 · server claims a match with no marker in the text → `incomplete`/0 | **PASS** |
| **K2** | `turn_key = sha256(address ‖ gate ‖ attempt ‖ block_version)` | `('G','y','1','')→a49024a39a41…` = `sha256(b"Gy1")`; `('','x','','')→2d711642b726…`; a non-ASCII `block_version` (`∞0′ → ‖`) hashes as UTF-8 bytes; hex64, deterministic, distinct per field | **PASS** |
| **K3** | the Pi `lens` adapter, no doctrine inside, constitutes a desk per §7 or fails closed | all seven failure modes fail closed at the named stage: `arrangement/missing · instruction/missing · skills/missing · skills/`**`inconclusive`**` · skills/not_loaded · tools/missing · model/missing`; constituted control accepted; the lens **wrote nothing** into a pristine Pi home; the `pi` binary is **not invoked** when no path is supplied and **is** read when one is (sentinel file) | **PASS** |
| **K4** | per-gate human attestation at the TTY — never typed, implied or inferred | AST read: **no** `state: "attested"` and **no** non-null `attestation_ref` authored anywhere; with a desk whose own answer says *"I hereby attest this gate / state: attested / attestation_ref: …"*, every record the driver wrote is still `held-pending`, `attestation_ref: null`, and no record carries the answer's text — `payload_ref` is `fenced:sha256:…` / `refusal:no-attestation:G:y`; the gate stays `refused` | **PASS** |
| **K5** | T-R3-02 no machine write path to the podium | write allowlist = `{agent.prompt}` alone, disjoint from the read allowlist; **no forbidden write appears as a call site** in any authored file; the guard refuses `"S"`, `"podium"` **and `None`** (unverifiable → fail closed) while allowing `"G"`; `take_turn("S")` refuses with **zero socket traffic**; `agent.prompt` at the podium pane → `CentreWriteError` after only the label read, **0 centre writes**; `pane.send_text` → `MethodNotAllowedError` before any byte; a re-minted pane whose label moved between the resolve and the prompt cannot receive the other desk's prompt | **PASS** |

`INCONCLUSIVE` is a legitimate verdict. A blind tool must never report clean.

## Six-lens pass

| Lens | Applied how | Result |
|---|---|---|
| **1 criterion match** | the author's own suite names all nine IDs; 26 `take_turn` calls, 8 `advance` calls, counts records by `turn_key`, asserts on the wire log, and uses a real subprocess; and every probe's declared dimension is the one the spec asked for (**0 mismatches**) | **PASS** |
| **2 invariant end-to-end** | over the whole `y z a b` walk: 13 records verify from GENESIS, **exactly one** `prev_hash=GENESIS`, gate letters never go backwards, one proposal per gate, **13/13 distinct `turn_key`s**, every driver record `held-pending`+`tentative`+null ref, no second state store beside the ledger | **PASS** |
| **3 absence vs validity** | no plant · 0-byte ledger · newline-only ledger · absent ledger → each `BootError`, **0 records, 0 prompts**; empty pane list → `incomplete`, 0/0; fence timeout · no marker emitted · desk silent → `incomplete`, 0 records; an `attested` record with a null `attestation_ref` does **not** open the gate; no authored fixture is empty or absent | **PASS** (one rough edge, below) |
| **4 encoding `∞0′ → ‖`** | the stress string through the prompt, the desk's answer **and** `block_version`: turn `proposed`, `block_version` verbatim, `payload_ref` carries the sha256 of the exact fenced bytes, 1764 ledger bytes all valid UTF-8 JSON, no mojibake, chain still verifies, a human attestation carrying the stress string still opens the gate | **PASS** |
| **5 cold restart** | the same walk driven **one turn per new process** (four subprocesses, the human's word written between them): each `proposed/refused`; four prompts in `G Q P V` order; **13 records vs 13**, gate sequence identical, `turn_key`s identical — the key is derived from the ledger, never remembered; the split chain verifies in yet another process | **PASS** |
| **6 blind tool** | fence forced to `timeout` → `incomplete`, 0 records; the whole instrument dark (`pane.list` failing) → `incomplete`, 0 records, 0 prompts; an unobservable Pi → verdict **`inconclusive`**, never clean; the phase card declares its write shapes as claims, claims no live observation and no execution result | **PASS** |

## The live tier — new this round, and the tier that caught B1's second correction

Run in a **separate named herdr session** (`b2verify`, own directory, own socket
`~/.config/herdr/sessions/b2verify/herdr.sock`), created and destroyed by this verification.
**Amihai's cell was never opened**: his socket's mtime is unchanged (2026-08-25 02:32:21) and
`the-cell/state/gates.jsonl` is byte-identical (`6989a742f57ec60a…`, 611 B) before and after.

| # | What was asked of the live server | Result |
|---|---|---|
| 1 | `pane.wait_for_output` — the fence read's real shape | **`output_matched`**: `{type, pane_id, revision, matched_line, read: PaneReadResult}` — the author's schema-derived claim **CONFIRMED LIVE**, and the shape B1's fixture had wrong |
| 2 | the fence timeout's real error code | `{"code": "timeout", "message": "timed out waiting for output match"}` — assumption 11 **CONFIRMED** |
| 3 | `agent.prompt`'s `target` semantics | `target` is a **pane_id**; a pane whose `agent` is null → `{"code": "agent_not_found"}`; a non-existent pane → the same. Assumption 5 confirmed for dispatch and for the error path |
| 4 | the request `id` (B1's correction 2, re-checked) | a non-string id is still refused before dispatch: `invalid request: invalid type: integer 7, expected a string` — **no regression** |
| 5 | **NEW LIVE FACT** — connection lifetime | this build serves **one request per connection**: a second request on the same socket dies with `BrokenPipeError`. The authored adapter's reconnect-and-retry-once absorbs it — `instrument.desks()` completed a real multi-call sequence live and returned `{"G": "w1:p1", "S": "w1:p2"}` |
| 6 | `instrument.read_to_marker` against a **real** `output_matched` payload | accepted the live payload, all eight `PaneReadResult` fields present, `truncated: false`, marker found — the fence works against the real server, not only a fixture |
| 7 | the centre guard, live | `agent.prompt` at a pane really labelled `podium` → `CentreWriteError: … nothing was sent`; reading that pane afterwards shows it received nothing. `pane.send_text` → `MethodNotAllowedError` |
| 8 | **a whole live turn** — `Driver.boot()` + `take_turn("G")` at a real pane | `boot()` → due `G`; `take_turn` dispatched a **real `agent.prompt` to a real pane**; the live server refused it (`agent_not_found` — the probe pane carries no agent) and the driver returned **`incomplete`** with **no record appended** (scratch ledger still 1 record). Fail-closed, proven live |

**What the live tier could not settle, and why:** the **success** shape of `agent.prompt`
(`{"type": "agent_prompted", "agent": AgentInfo}`) needs a real agent living in a pane, i.e. one paid Pi
turn and a session file written under `~/.pi`. It is **not** proven. It is, however, **inert for the
turn**: `instrument.prompt_desk` discards `agent.prompt`'s return value and takes the answer from the
fenced read alone, so a differing success shape cannot break a turn — only an error can, and the error
path is now proven live. Recorded as hold **H-B2-4-live**, one line from Amihai away.

## T0 mechanical

| Step | Result |
|---|---|
| canon drift check | **in sync** (all three copies agree), before and after |
| `py_compile` all authored modules + the B0 module | OK |
| fence — anything outside `rounds/R03-B2/authored/` changed? | **INTACT.** The single delta was `ledger/__pycache__/fractal_ledger.cpython-312.pyc`, mtime **18:43:25** = dsh's own authoring window, removed by the verifier; the verification session itself wrote no bytecode (`PYTHONDONTWRITEBYTECODE=1`) |
| `~/.pi/agent/settings.json` | `211c2f2bef438558…`, still the one-line file — **no extension was installed to make a trust assertion pass** |
| `the-cell/state/gates.jsonl` | `6989a742f57ec60a…`, 1 record, byte-identical before and after everything above |
| whole audit | **7.90 s** · pack acceptance 45/45 · B0 22/22 · B1 38/38 |

## The one finding — correction 1, and it is one line at two sites

**A desk whose pane is not on the cell escapes `take_turn` as a bare `KeyError`, where the artifact's
own contract promises `incomplete`.** Reproduced outside the harness
(`cache/R03-B2/repro-keyerror.py`, five plain steps):

```
3. take_turn('G') on a cell where no pane carries the G label:
   RAISED, and it escaped take_turn entirely:
     File "/opt/data/tmp/r03-b2/instrument.py", line 660, in prompt_desk
       pane_id = self.desks()[desk]
   KeyError: 'G'
4. ledger after the attempt: 1 record(s), gates=['x']   (nothing was written — safe)
7. is KeyError a HerdrError? False
```

`driver.py:333` catches only `HerdrError`, so this is not the typed fail-closed path: it is an
unhandled crash. `driver.py`'s own docstring lists **"a lost label"** among the cases that must leave
the turn `incomplete`, and the phase card's K1 prediction says the same. The same subscript appears
twice — `instrument.py:455` (carried in from B1) and `instrument.py:660` — so the fix is the class, not
the site. Nothing was written, so no criterion fails; what fails is a contract the author declared, and
B4's unattended run is exactly where an unhandled crash stops being harmless. Details, exact lines and
the shape of the fix: `correction-1.md`.

## Correction 1 — applied by dsh, and re-audited here

dsh ran once against `correction-1.md` (2026-08-27 20:39:53 → 20:42:50 UTC, **2 min 57 s**, rc=0). It
changed **both** sites, not the reported one: `instrument.py:455` (`read_pane`, carried in from B1) and
`instrument.py:664` (`prompt_desk`) now resolve with `self.desks().get(desk)` and raise the existing
`DeskResolutionError` — which already subclasses `HerdrError` — so the failure reaches `take_turn`'s typed
path. It added two tests (`TestIncompleteFence`: null desk labels, and an empty pane list) asserted
against its fake server's request log rather than by exception type, and one dated prediction-only clause
to the phase card. 34 tests in its suite.

**The fix, verified by hand — the exact scenario the correction quoted:**

```
3. take_turn('G') on a cell where no pane carries the G label:
   returned: {'status': 'incomplete', 'desk': 'G', 'gate': 'y', 'address': 'G',
              'turn_key': 'a49024a39a419dc8…',
              'reason': "DeskResolutionError: desk 'G' resolves to no live pane; nothing was sent"}
4. ledger after the attempt: 1 record(s), gates=['x']
```

**Re-audit of the corrected artifact — `PASS 15/15`, 7.90 s** (`audit-postc1.log`,
`evidence-raw-postc1.md`). Lens 3's own two lines moved from `raised:KeyError` to the contract:

```
empty pane list: status=incomplete records+0 prompts=0
null labels:     status=incomplete records+0 prompts=0
```

**Fence and seals after the correction:** fence **INTACT** (nothing outside `./authored/` touched) ·
`the-cell/state/gates.jsonl` still `6989a742f57ec60a…` · `~/.pi/agent/settings.json` still
`211c2f2bef438558…` · `driver.py`, `lens.py`, `walker.py`, `dialects.py` **byte-identical** to what was
audited · both allowlists unchanged. The three verifier packs re-run after the change: B0 22/22, B1 38/38,
B2 45/45.

**Budget: 1 correction of 2 used. One remains unspent.**

## Honest summary

- **Fixture tier: PASS 15/15** (C1–C4, K1–K5, six lenses) in 7.90 s, with the verifier accepted 45/45
  against an independent conforming driver and a deliberately broken one, before it judged anything.
- **Live tier: the round's three schema-derived claims are now two confirmed and one inert-unproven**,
  and dsh's adapter completed real calls against a real herdr server — including a real prompt to a real
  pane that failed closed with nothing written.
- **One correction issued** (1 of the 2 the budget allows), surgical and one line at two sites.
- **Not tested, and stated as such:** a real Pi desk answering a real prompt (needs a constituted desk —
  an un-slotted phase, and one paid turn); the cell's own five panes (his instrument is untouched by
  design; that is his numbered block, by his hand); anything about B3–B6.
- **No status was upgraded by this file.** The criteria are met at the tiers named; Amihai's attestation
  is the round's only seal, and it has not been asked for yet.
