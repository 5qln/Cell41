# CORRECTION 2 — R02 · B1 the read-only walker

*Surgical, and the last one in this round's budget. One expression in one file. Found only against
the live instrument — the tier neither of our fixtures could reach.*

## What failed

Claim **K1**, verbatim from the commission:

> the `instrument` adapter (**raw socket client, label-resolved desks**)

Against the **live** herdr 0.8.2 socket the adapter cannot complete a single call. Every criterion
that needs the socket therefore reads INCONCLUSIVE — nothing about the walker was measurable.

## The exact evidence

Your adapter, against Amihai's running cell (`~/.config/herdr/herdr.sock`), first call:

```
$ cd /home/deploy/the-cell/rounds/R02-B1/authored && python3 -c "
from walker import Walker; Walker(socket_path='/home/deploy/.config/herdr/herdr.sock',
                                 ledger_path='/tmp/scratch.jsonl').tick()"

Traceback (most recent call last):
  File "walker.py", line 162, in tick
    snapshot = self.instrument.observe_desks()
  File "instrument.py", line 466, in observe_desks
    resolved = self._resolve()
  File "instrument.py", line 404, in _resolve
    panes = self.call("pane.list", {})
  File "instrument.py", line 281, in call
    return self._decode(raw, method, request_id)
  File "instrument.py", line 311, in _decode
    raise HerdrProtocolError(
instrument.HerdrProtocolError: response id '' does not echo request id 1
```

The ground truth, probed read-only on the live server (2026-08-27 16:42 UTC, herdr 0.8.2,
protocol 20) — five requests, the raw first bytes of each response:

```
request id='1'        -> response id='1'        keys=['id','result']   {"id":"1","result":{"type":"pong",…
request id='abc123'   -> response id='abc123'   keys=['id','result']   {"id":"abc123","result":{"type":"pong",…
request id=''         -> response id=''         keys=['id','result']   {"id":"","result":{"type":"pong",…
request id=7          -> response id=''         keys=['error','id']    {"id":"","error":{"code":"invalid_request","message":"invalid request: invalid t…
request id=None       -> response id=''         keys=['error','id']    {"id":"","error":{"code":"invalid_request","message":"invalid request: invalid t…
```

So: **herdr echoes a string id verbatim, and rejects a non-string id** as
`invalid_request`, answering with `id: ""`.

Your bytes, `authored/instrument.py`:

```python
202:        self._ids = itertools.count(1)          # ← an integer counter
270:            request_id = next(self._ids)
274:                envelope = {"id": request_id, "method": method,
275:                            "params": params}
310:        if obj.get("id") != request_id:          # ← this check is CORRECT; keep it
```

`itertools.count(1)` yields `1, 2, 3…` — integers. The server refuses the request before looking at
the method, replies with `id: ""`, and your echo check correctly reports that the response does not
echo the request. The failure surfaced honestly; the cause is the id's **type**.

## The narrowest true statement of the defect

The envelope's `id` must be a JSON **string**; yours is an integer, so the live server rejects every
request as `invalid_request` before dispatch.

## What is NOT being asked

- **The strict echo check at line 310 is right — do not weaken it.** Do not accept `""` as a match,
  do not skip the check, do not "tolerate" a mismatched id. It is what turned a silent wrong-response
  hazard into a clear error, and it must keep doing that.
- Do not restructure `call()`, the allowlist, the retry/reconnect path, the tagged-union unwrapping,
  the typed errors, or anything in `walker.py` / `dialects.py` (both already passed; `dialects.py`
  carries correction 1 and is settled).
- Do not change how the id is *generated* beyond making it a string — a monotonic counter is fine;
  `str(next(self._ids))` is the whole fix if you want it.

## One test-side change, because this is why neither of us saw it

Your fake server — like the verifier's — echoed whatever id it was handed, so an integer id round
tripped happily and all 23 tests passed against a dialect the real server does not speak. Make the
fixture speak the live dialect: **a non-string id must be refused with
`{"id": "", "error": {"code": "invalid_request", …}}`**, exactly as probed above, and add the test that
sends one. The verifier's fixture has already been corrected the same way, and with it every
socket-dependent criterion of this round reads INCONCLUSIVE against your current adapter.

## Budget

Correction **2 of at most 2**. If this does not close K1, the round stops and the state is surfaced to
Amihai as a HOLD — not a third attempt.
