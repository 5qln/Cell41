# The fixture desk harness (the blind-tool lens, lens 6)

`desk_bind.py` binds the pinned R06 desk harness **through the seam** (never re-authored): a
deterministic fake desk box that speaks the real herdr dialect on its own socket.  The two
named cases:

* **unconstituted desk** — `unconstituted_case()`: one desk holds no agent; the engine
  (via the real `cellctl`, invoked with the binding's exact argv) reports the
  `agent_not_found` hold — never a fixture stand-in.
* **absent socket** — `absent_socket_case(work_dir)`: `cellctl states --spec …` over a
  spec whose `live_socket` points nowhere reads `{"status":"absent"}` honestly (C2).

No live desk is ever prompted (H-R08-1): the harness's own socket receives every
fixture turn; the live box is never touched.
