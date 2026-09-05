# 02 · The Five Lakes — how not to build a swarm

Before the swarm was real, it was four ways of being wrong. The record keeps all four,
because the trail is the title.

**Lake 1** was a drawing — `cellctl --plan-only`, zero agents. A shape catalog derived
from signs, but no one walked it.

**Lake 2** was a relay — one desk at a time, sequential. Fan-out without parallelism.

**Lake 3** was four solo prompts, fired concurrently — one model, four role-prompts, no
shared trace. The V desk held: it refused to compose a return it could not trace. No
convergence.

**Lake 4** was a flat `SGQPV` spin — reused idle desks, no fractal descent. More prompts,
still no movement.

Each lake taught something that cost real time to learn. The timeout was learned as data,
not assumed: 30 seconds killed every turn; 180 was ten seconds short of V's ~190; 300
cleared it. The answers were always there — fenced in the desk *session* files — but the
conductor read the pane *screen*, which the runtime never wrote, and recorded four
`outage: HerdrRemoteError` holds for turns that had succeeded. The fix was one override:
read the session, not the screen.

And a gate crystallized, the test for the word "swarm": **distinct spawned agents · genuine
parallelism · the fractal descent actually walked · a converge that reduces** — a B″ that
says something no single desk said. Four lakes failed that gate. The fifth would not.

This chapter is the least glamorous and the most load-bearing. The cell's engineering is
not decoration; it is the trail. Every future article rests on the fact that these
mistakes were recorded, not smoothed over.

**The question this chapter opens:** if a swarm is defined by fan-out *and* converge, what
had to be true before four solo answers could become one?

*Lineage: `case-study/03-what-was-developed.md` · `case-study/04-three-runs.md` · `case-study/07-lessons-learned.md` · `case-study/08-swarm-assessment.md`.*
