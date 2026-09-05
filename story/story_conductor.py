#!/usr/bin/env python3
"""story_conductor — Lake 9: the storyteller (Cell 41 tells its own formation).

Four corner agents (Language/Machine/Circle/Persons) each narrate their corner of
the formation trail under the eight fractal laws, then the center (V) composes the
holographic flagship article. Ledger-free and lock-free: the storyteller produces
plain prose, not ⟦SURFACE⟧ boilerplate — it is a notation over the trail, not a walk.
"""
from __future__ import annotations

import json
import os
import sys
import time

sys.dont_write_bytecode = True

_HERE = os.path.dirname(os.path.abspath(__file__))
_SWARM = os.path.join(os.path.dirname(_HERE), "swarm")
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
if _SWARM not in sys.path:
    sys.path.insert(0, _SWARM)

from fractal_conductor import FractalConductor, CELL, HERDR  # noqa: E402

STORY = os.path.join(CELL, "story")
LAWS_MD = os.path.join(STORY, "laws.md")

# (corner, letter-for-pane-split, description, record-pack files)
CORNERS = [
    ("formation", "G", "Language — how Cell 41 formed",
     ["case-study/00-index.md", "case-study/02-the-system.md"]),
    ("evolution", "Q", "Machine — how the fractal evolves, how we work with it",
     ["case-study/01-what-and-why.md", "case-study/03-what-was-developed.md",
      "case-study/04-three-runs.md", "case-study/07-lessons-learned.md",
      "case-study/12-retrospective.md", "case-study/15-self-improvement-plan.md"]),
    ("swarm", "P", "Circle — what we learn about swarms, agents, possibilities",
     ["case-study/08-swarm-assessment.md", "case-study/13-navigation-engine.md",
      "case-study/14-granular-lake6.md", "case-study/16-contact-not-vacancy.md"]),
    ("school", "V", "Persons — the school seeded and sprouted",
     ["case-study/11-session-2026-09-02-school-constitution.md",
      "case-study/17-person-expression.md", "case-study/18-book-ground.md",
      "ground/book-ground.md", "ground/lossless-report.md"]),
]


class StoryConductor(FractalConductor):
    def __init__(self, scenario_path, ledger_path, trail_path, spec=None):
        super().__init__(scenario_path, ledger_path, trail_path, spec=spec)
        self.laws = open(LAWS_MD, encoding="utf-8").read()
        self.axis = ""

    def planted(self):
        return "Lake 9 — the storyteller: Cell 41 tells its own formation trail"

    # -- spawn WITHOUT the lock (storyteller is prose, not a surface) --------
    def spawn(self, letter, panes):
        name = self._name()
        pane = json.loads(self.sh([HERDR, "pane", "split", panes[letter],
                                   "--direction", "right", "--cwd", STORY]).stdout)
        pane_id = pane["result"]["pane"]["pane_id"]
        started = json.loads(self.sh([HERDR, "agent", "start", name, "--kind", "pi",
                                      "--pane", pane_id, "--timeout", "90000"]).stdout)
        agent = started["result"]["agent"]
        if "agent_session" not in agent:
            for _ in range(30):
                time.sleep(2)
                lst = json.loads(self.sh([HERDR, "agent", "list"]).stdout)
                for a in lst["result"]["agents"]:
                    if a.get("name") == name and a.get("agent_session"):
                        agent = a
                        break
                if "agent_session" in agent:
                    break
        if "agent_session" not in agent:
            raise RuntimeError("agent start failed for %s" % name)
        return name, pane_id, agent["agent_session"]["value"]

    def _pack(self, files):
        parts = []
        for rel in files:
            p = os.path.join(CELL, rel)
            if os.path.exists(p):
                txt = open(p, encoding="utf-8").read()
                if len(txt) > 7000:
                    txt = txt[:7000] + "\n…[truncated]…"
                parts.append("### %s\n%s" % (rel, txt))
        return "\n\n".join(parts)

    def build_prompt(self, letter, address, level, handoff):
        if level == "corner":
            corner, _letter, desc, files = next(c for c in CORNERS if c[0] == address)
            return "\n\n".join([
                "⟦LAWS — your charter⟧\n" + self.laws + "\n⟦END LAWS⟧",
                "⟦RECORD — your corner's formation-trail artifacts⟧\n"
                + self._pack(files) + "\n⟦END RECORD⟧",
                ("⟦TASK⟧ You are ONE corner of Cell 41 — the %s corner (%s) — telling "
                 "the story of its own formation. Read the LAWS (your charter) and the "
                 "RECORD (your corner's actual artifacts). Write THIS corner's story, "
                 "obeying the eight laws: cite lineage (L8) — point at real artifacts "
                 "(run ids, holds, lakes, files); mark the membrane (L4) — say what the "
                 "humans attested vs what the machine structured; compress (L2/L5); return "
                 "a question (L3). Plain living prose, 500–900 words. No ⟦SURFACE⟧, no "
                 "equations-as-decoration." % (corner, desc)),
            ])
        # center
        parts = ["⟦LAWS — your charter⟧\n" + self.laws + "\n⟦END LAWS⟧",
                 "⟦THE FOUR CORNER-STORIES⟧"]
        if isinstance(handoff, dict):
            for k, v in handoff.items():
                parts.append("=== %s ===\n%s" % (k, v))
        parts.append("⟦END CORNER-STORIES⟧")
        parts.append(
            "⟦TASK⟧ You are the CENTER of Cell 41, composing the whole. Read the LAWS "
            "and the four corner-stories. Compose ONE flagship article — 'The Formation "
            "Trail' — that holds the whole holographically: the α ('start from not "
            "knowing') carried whole; the four corners woven, not listed; lineage marked "
            "(the real runs, holds, lakes, timings); the membrane marked (the human's word "
            "vs the machine's form); and it must NOT conclude — it must return a question "
            "(∞0′). ~900–1300 words. Plain living prose; no boilerplate, no ⟦SURFACE⟧.")
        return "\n\n".join(parts)

    def _turn(self, letter, address, level, handoff, panes):
        name, pane_id, session = self.spawn(letter, panes)
        try:
            t0 = time.time()
            marker = self.fire(name, self.build_prompt(letter, address, level, handoff))
            answer = self.read_fenced(session, marker)
            self.turns.append({"address": address, "letter": letter,
                               "turn_time_s": round(time.time() - t0, 1)})
            return answer
        finally:
            self.close(pane_id)

    def run_story(self, panes=None):
        panes = panes or self.pane_map()
        assert set(panes) == {"G", "Q", "P", "V"}, panes
        t0 = time.time()

        def log(k):
            print("[%6.1fs] %s" % (time.time() - t0, k), flush=True)

        # four corners, spawned + fired in parallel, read + closed
        log("four corners narrate (parallel, lock-free)")
        spawned = []
        for letter, address, _lvl, _h in [(c[1], c[0], "corner", "") for c in CORNERS]:
            name, pane_id, session = self.spawn(letter, panes)
            t_start = time.time()
            marker = self.fire(name, self.build_prompt(letter, address, "corner", ""))
            spawned.append((address, letter, session, marker, pane_id, t_start))
        corner_out = {}
        for address, letter, session, marker, pane_id, t_start in spawned:
            try:
                corner_out[address] = self.read_fenced(session, marker)
                self.turns.append({"address": address, "letter": letter,
                                   "turn_time_s": round(time.time() - t_start, 1)})
            finally:
                self.close(pane_id)

        for corner, _letter, _desc, _files in CORNERS:
            with open(os.path.join(STORY, "corner-%s.md" % corner), "w",
                      encoding="utf-8") as fh:
                fh.write("# Corner: %s\n\n%s\n" % (corner, corner_out[corner]))

        # center compose
        log("center composes the flagship (with the axis)")
        handoff = {c[2]: corner_out[c[0]] for c in CORNERS}
        axis_path = os.path.join(CELL, "swarm", "axis.jsonl")
        if os.path.exists(axis_path):
            handoff["the axis (∞0′ cycle-to-cycle)"] = open(axis_path, encoding="utf-8").read()[-4000:]
        article = self._turn("V", "center", "center", handoff, panes)

        with open(os.path.join(STORY, "formation-trail-article.md"), "w",
                  encoding="utf-8") as fh:
            fh.write(article + "\n")

        log("DONE")
        total_s = round(time.time() - t0, 1)
        self.log_run_generic("cell-story", "complete", "∞0′", total_s,
                             extra={"article": article[:600]})
        return {"status": "complete", "turns": len(self.turns), "total_s": total_s,
                "saved": os.path.join(STORY, "formation-trail-article.md"),
                "corners": sorted(corner_out)}


def main(argv):
    import argparse
    p = argparse.ArgumentParser(prog="story_conductor")
    p.add_argument("--scenario", default=os.path.join(CELL, "state", "word.json"))
    p.add_argument("--ledger", default=os.path.join(CELL, "state", "gates.jsonl"))
    p.add_argument("--trail", default=os.path.join(CELL, "state", "trail.jsonl"))
    p.add_argument("--spec", default=os.path.join(CELL, "rounds", "R07-integration",
                                                  "authored", "spec.json"))
    args = p.parse_args(argv)
    spec = json.load(open(args.spec)) if os.path.exists(args.spec) else {}
    sc = StoryConductor(args.scenario, args.ledger, args.trail, spec=spec)
    result = sc.run_story()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main(sys.argv[1:])
