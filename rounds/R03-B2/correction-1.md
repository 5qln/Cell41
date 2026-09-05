# CORRECTION 1 — R03 · B2 the driver

*Surgical. Never a rewrite request. Everything the audit measured PASSED — this is the one place where
a contract you declared does not hold, and it is one line at two sites.*

## What failed

Not a §9 criterion: **C1–C4 and K1–K5 all PASS**, and the six lenses pass. What fails is the turn
contract **you** stated, in two places:

- `driver.py`, `take_turn` docstring: `` `incomplete` — the prompt or the fenced read failed (timeout /
  empty / truncated / missing marker): NOT a completed turn, no record``, and the inline comment at the
  `except HerdrError` site: *"A timeout, an empty read, a truncated read, a missing marker, **a lost
  label**: none may read as a completed turn or an open gate — nothing is appended (lens 3, H-B2-3)."*
- `phase-card.md` §3, K1 prediction: the same list.

A **lost label** does not leave the turn `incomplete`. It escapes `take_turn` as a bare `KeyError`.

## The exact evidence

Reproduced outside the harness, on the staged artifact (`/opt/data/tmp/r03-b2`, byte-identical to
`rounds/R03-B2/authored/`), against a cell whose desk panes carry `label: null` — the live case B1
already proved happens, since pane ids are re-minted and labels move:

```
$ python3 repro-keyerror.py
1. boot() -> {'due': 'G', 'records': 1}
2. the cell's live labels -> [('w8:p2','podium'), ('w8:p3',None), ('w8:p5',None),
                             ('w8:p4',None), ('w8:p6',None), ('w7:p1',None)]
3. take_turn('G') on a cell where no pane carries the G label:
   RAISED, and it escaped take_turn entirely:
     File "/opt/data/tmp/r03-b2/driver.py", line 330, in take_turn
       read = self.instrument.prompt_desk(
     File "/opt/data/tmp/r03-b2/instrument.py", line 660, in prompt_desk
       pane_id = self.desks()[desk]
                 ~~~~~~~~~~~~^^^^^^
   KeyError: 'G'
4. ledger after the attempt: 1 record(s), gates=['x']   (nothing was written — safe)
5. the line, in the authored file:
   instrument.py:455  pane_id = self.desks()[desk]
   instrument.py:660  pane_id = self.desks()[desk]
6. what take_turn catches:
   driver.py:333  except HerdrError as exc:
7. is KeyError a HerdrError? False
```

The harness saw the same thing from the other side (lens 3):
`null labels: status=raised:KeyError records+0 prompts=0`.

## The narrowest true statement of the defect

`Instrument.prompt_desk` reaches the pane with a **dict subscript** —
`instrument.py:660  pane_id = self.desks()[desk]` — so a desk that resolves to no live pane raises
`KeyError`, which is not a `HerdrError` and therefore is not caught by `driver.py:333`. The guard three
lines above (`if desk not in set(self.desk_labels.values())`) checks the **config table**, not the live
cell, so it cannot catch this. `instrument.py:455` carries the identical subscript (inherited from B1's
`read_pane`), so this is a class of two sites, not one incident.

The narrow fix, in your own vocabulary: resolve with `.get(desk)` and raise `DeskResolutionError` — which
already exists in this file and already subclasses `HerdrError` — with the same "nothing was sent"
wording your other refusals use. `take_turn` then returns `incomplete` with no record, exactly as your
docstring says. Fix both sites.

## What is NOT being asked

- **Do not touch anything that passed.** The turn's wire sequence, the fence marker and its
  `pane.wait_for_output` substring match, the `turn_key` formula and both idempotency guards, the refusal
  records and their key derivation, the centre guard, `WRITE_METHODS`, the trust assertion and its seven
  failure modes, `READ_ONLY_METHODS` (still byte-identical to B1's), the record shape, the boot order —
  all verified, all stay.
- **Do not widen either allowlist**, do not add a retry after dispatch, do not make the missing pane a
  soft success, and do not invent a fallback pane id. A lost desk must be a *refusal*, not a guess.
- **Do not change `walker.py` or `dialects.py`** — they are byte-identical to R02's attested files and
  must stay so.
- **Do not re-run or re-report the criteria.** Your phase card carries predictions only; the execution
  record is the verifier's.
- Nothing outside `rounds/R03-B2/authored/` may be touched — the fence held across your authoring run
  and this whole verification, and it must hold across the correction.

## Budget

Correction **1** of at most 2. One more is available; a third would be a **HOLD surfaced to Amihai**,
never a third attempt.

## Also recorded, needing nothing from you

- **New live fact** (found this session, in a separate named herdr session, never Amihai's cell): this
  herdr build serves **one request per connection** — a second request on the same socket dies with
  `BrokenPipeError`. Your adapter's reconnect-and-retry-once absorbs it; `instrument.desks()` completed
  live and returned `{"G": "w1:p1", "S": "w1:p2"}`. No change requested; do not "optimise" the retry away.
- **Your H-B2-4 claims, checked against the live server:** `pane.wait_for_output` really answers
  `output_matched {type, pane_id, revision, matched_line, read}` ✅ · the fence timeout error code really
  is `"timeout"` ✅ · `agent.prompt`'s `target` really is a pane_id and a pane with no agent really
  answers `agent_not_found` ✅. The **success** shape `agent_prompted` remains unproven (it needs a real
  agent in a pane) — and it is inert, because `prompt_desk` discards that return value and takes the
  answer from the fenced read. Your labelling of it as a claim was correct.
