#!/usr/bin/env python3
"""person_conductor — Lake 7: the person as expression of the fractal.

The third pillar (after the constitution and the field): X asks what the
STUDENT (or facilitator) is, as an expression of the same fractal that already
expressed the school, the constitution, and the field. X self-differentiates
into three edges — the AI pair (human ↔ K co-creation), the online/offline
presence boundary, and the global decentralized peers — each opened as a full
4+1 cell, then composed back into ONE coherent form of the person.

Inherits GranularConductor (→ NavigationConductor → FractalConductor): robust
spawn, fan_out_parallel, semantic classify, [NAV] logging, the ∞0′ axis,
adaptive descent (descend only where a surface is unformed), unified log.
"""
from __future__ import annotations

import json
import os
import sys
import time

sys.dont_write_bytecode = True

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from granular_conductor import GranularConductor  # noqa: E402
from fractal_conductor import CELL, AUTHORED, reset_state  # noqa: E402


class PersonConductor(GranularConductor):
    def run_person(self, panes=None, max_depth=2, axis=""):
        self.axis = axis or self.load_axis()
        panes = panes or self.pane_map()
        assert set(panes) == {"G", "Q", "P", "V"}, panes
        results = {}
        t0 = time.time()

        def log(k):
            print("[%6.1fs] %s" % (time.time() - t0, k), flush=True)

        self._emit_boot(self.read_states())
        self._seed_record({"address": "", "index": 0}, self.scenario["seed"]["ref"])

        faces = [("The Pair", "GG", "G"),
                 ("The Presence", "GQ", "Q"),
                 ("The Peers", "GP", "P")]

        lens = {"G": "essence (α)", "Q": "resonance (φ⋂Ω)", "P": "gradient (δE/δV→∇)"}

        # L0 — anchor: G names α of X
        log("L0 · anchor (G names α)")
        self.nav_line("anchor", "GG (α)", "L0", "—",
                      "G names the irreducible α of X (the person as expression "
                      "of the fractal)")
        alpha = self.ask(
            "G", "GG",
            "L0 · G — name the irreducible α of the person as an expression of the "
            "fractal: the student (or facilitator) is one tense of the field that "
            "already expressed the school, the constitution, and the field. Read α "
            "as an operator, not a relation, and show its three edges (the AI pair, "
            "the online/offline presence, the global peers) as ONE thing.",
            "", panes)
        results["ALPHA"] = alpha

        # L1 — the three edges, each opened as a full 4+1 (9 corners in parallel)
        log("L1 · three edges fan-out (9 corners in parallel)")
        self.nav_line("fanout", "3 edges × G/Q/P", "L1", "—",
                      "X self-differentiates: The Pair / The Presence / The Peers, "
                      "each opened as its own 4+1 — 9 corners in parallel")
        w1 = []
        for name, cell, _f in faces:
            for L in "GQP":
                w1.append((L, cell + L,
                           "L1 · %s · %s — read this edge of the person-as-expression"
                           % (name, lens[L]), ""))
        surfaces = dict(self.fan_out_parallel(w1, panes))

        # classify all 9; adaptive descent waves (parallel, only where unformed)
        descended = set()
        frontier = [(L, cell + L) for _n, cell, _f in faces for L in "GQP"]
        for depth in range(1, max_depth + 1):
            to_descend = []
            for (L, addr) in frontier:
                if addr in descended:
                    continue
                klass, reason = self.classify(L, surfaces[addr])
                if klass == "unformed":
                    to_descend.append((L, addr, reason))
                else:
                    self.nav_line("stay", addr, "L%d" % (depth - 1), klass, reason)
            if not to_descend:
                break
            log("L%d · descent wave (%d corners unformed)"
                % (depth + 1, len(to_descend)))
            for (L, addr, reason) in to_descend:
                self.nav_line("descend", addr, "L%d" % (depth + 1), "unformed", reason)
            # open every unformed corner's cell in ONE parallel wave
            w = []
            for (L, addr, _r) in to_descend:
                for SL in "GQP":
                    w.append((SL, addr + SL,
                              "L%d · within %s · %s" % (depth + 1, addr, lens[SL]), ""))
            sub = self.fan_out_parallel(w, panes)
            surfaces.update(sub)
            # converge every descended corner's V in ONE parallel wave
            conv = []
            for (L, addr, _r) in to_descend:
                handoff = {"G": sub[addr + "G"], "Q": sub[addr + "Q"],
                           "P": sub[addr + "P"]}
                conv.append(("V", addr + "V",
                             "L%d · converge %s (its own B″)" % (depth + 1, addr), handoff))
            cv = self.fan_out_parallel(conv, panes)
            next_frontier = []
            for (L, addr, _r) in to_descend:
                surfaces[addr] = cv[addr + "V"]
                descended.add(addr)
                self.nav_line("converge", addr + "V", "L%d" % (depth + 1), "—",
                              "descended corner replaced by its own B″")
                next_frontier.extend([(SL, addr + SL) for SL in "GQP"])
            frontier = next_frontier

        # converge the three edges in parallel
        log("converge · three edges (3 V in parallel)")
        self.nav_line("converge", "3 edges", "L1", "—",
                      "each edge's V composes its own B″ — 3 in parallel")
        conv = []
        for name, cell, _f in faces:
            handoff = {"G": surfaces[cell + "G"], "Q": surfaces[cell + "Q"],
                       "P": surfaces[cell + "P"]}
            conv.append(("V", cell + "V", "converge %s (its own B″)" % name, handoff))
        fv = self.fan_out_parallel(conv, panes)
        face_b = {name: fv[cell + "V"] for name, cell, _f in faces}
        for name in face_b:
            results["FACE_" + name.replace(" ", "_").upper()] = face_b[name]

        # compose — the school V reduces the three edges + α into ONE form
        log("compose · school V (ONE form of the person)")
        self.nav_line("converge", "GV (school)", "compose", "—",
                      "school V composes ONE form of the person from α + three edges "
                      "— reduce, not list")
        school_b = self.ask(
            "V", "GV",
            "compose — reduce α and the three edge-readings into ONE coherent form "
            "of the person as expression of the fractal (a single artifact, not a "
            "report of three). Carry α faithfully.",
            {"α (the one)": alpha,
             "The Pair": face_b["The Pair"],
             "The Presence": face_b["The Presence"],
             "The Peers": face_b["The Peers"]},
            panes)
        results["SCHOOL_B"] = school_b
        ended_in, status = self._semantic_end(school_b)
        log("school B″ composed (%s / %s)" % (ended_in, status))

        # +1 — the field: ascend and close across scales
        log("+1 · field fan-out + converge (the ascent)")
        self.nav_line("ascend", "ε (field)", "L+1", "—",
                      "ascend to the field — close across scales (person / school / cell)")
        r = {"G (the school)": school_b}
        r.update(self.fan_out_parallel([
            ("Q", "Q", "L+1 · Q — what does the field hold that meets the person's one form?", ""),
            ("P", "P", "L+1 · P — where does the person's energy flow in the wider field?", ""),
        ], panes))
        r["V"] = self.ask("V", "V",
                           "L+1 · V — compose the final B″ across the scales", r, panes)
        results["FIELD_B"] = r["V"]

        axis_rec = self.close_axis(ended_in, r["V"])
        log("DONE")
        total_s = round(time.time() - t0, 1)
        self._append_line(self._swarm_line(
            "run-end", "NOTE", None,
            "the person swarm ended — %d turns, %.1fs total, ended_in %s"
            % (len(self.turns), total_s, ended_in),
            {"status": status, "ended_in": ended_in,
             "actions": len(self.turns), "total_s": total_s,
             "navigation": self.nav, "axis": axis_rec}))

        out = os.path.join(CELL, "swarm", "person-run-result.json")
        with open(out, "w", encoding="utf-8") as fh:
            json.dump({"results": results, "turns": self.turns,
                       "navigation": self.nav, "axis": axis_rec,
                       "max_depth": max_depth, "total_s": total_s,
                       "status": status, "ended_in": ended_in},
                      fh, ensure_ascii=False, indent=2)
        self.log_run_generic("person-expression", status, ended_in, total_s,
                             extra={"alpha": alpha[:400],
                                    "bpp": school_b[:600],
                                    "axis": axis_rec,
                                    "navigation": self.nav})
        return {"status": status, "ended_in": ended_in,
                "turns": len(self.turns), "total_s": total_s,
                "saved": out, "navigation": self.nav, "axis": axis_rec,
                "results": results}


def main(argv):
    import argparse
    p = argparse.ArgumentParser(prog="person_conductor")
    p.add_argument("--scenario", default=os.path.join(CELL, "state", "word.json"))
    p.add_argument("--ledger", default=os.path.join(CELL, "state", "gates.jsonl"))
    p.add_argument("--trail", default=os.path.join(CELL, "state", "trail.jsonl"))
    p.add_argument("--spec", default=os.path.join(AUTHORED, "spec.json"))
    p.add_argument("--max-depth", type=int, default=2)
    p.add_argument("--axis", default="")
    p.add_argument("--no-reset", action="store_true",
                   help="skip the state reset (continue on the existing chain)")
    args = p.parse_args(argv)
    spec = json.load(open(args.spec)) if os.path.exists(args.spec) else {}
    if not args.no_reset:
        reset_state(args.ledger, args.trail)
    pc = PersonConductor(args.scenario, args.ledger, args.trail, spec=spec)
    result = pc.run_person(max_depth=args.max_depth, axis=args.axis)
    result["reset"] = not args.no_reset
    print(json.dumps({"status": result["status"], "ended_in": result["ended_in"],
                      "turns": result["turns"], "total_s": result["total_s"],
                      "saved": result["saved"], "reset": result["reset"],
                      "axis": result["axis"], "navigation": result["navigation"]},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main(sys.argv[1:])
