#!/usr/bin/env python3
"""navigation_conductor — the adaptive fractal walk with a navigation decision engine.

Inherits the shared primitives from FractalConductor (robust spawn,
fan_out_parallel, semantic classify, [NAV] logging, the ∞0′ axis). The walk:

    start at S (the school, scale 0) → fan out G/Q/P in parallel
    classify each surface: formed | unformed (fragmented → the ascent)
      unformed → DESCEND into that desk's own 4+1, all unformed in ONE parallel wave
      formed   → STAY (logged)
    converge V at the school → B″
    ascend +1 to the field (ε) → Q/P fan-out → V → final B″

The descent is now parallelised: all siblings are classified first, then every
unformed corner is descended in a single wave (this fixes the old sequential
descent where one desk's descent blocked the next sibling's classification).
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

from fractal_conductor import FractalConductor, CELL, AUTHORED, reset_state  # noqa: E402


class NavigationConductor(FractalConductor):
    def ask(self, letter, cell, level, handoff, panes):
        return self._turn(letter, cell, level, handoff, panes)

    def run_navigation(self, panes=None, max_depth=2, axis=""):
        self.axis = axis or self.load_axis()
        panes = panes or self.pane_map()
        assert set(panes) == {"G", "Q", "P", "V"}, panes
        results = {}
        t0 = time.time()

        def log(k):
            print("[%6.1fs] %s" % (time.time() - t0, k), flush=True)

        self._emit_boot(self.read_states())
        self._seed_record({"address": "", "index": 0}, self.scenario["seed"]["ref"])

        # scale 0 — the school: fan out G/Q/P in parallel
        log("scale 0 · school fan-out (G/Q/P in parallel)")
        self.nav_line("fanout", "G (school)", "scale 0", "—",
                      "school fan-out: G/Q/P in parallel")
        r0 = self.fan_out([
            ("G", "GG", "scale 0 · G — name the irreducible α of the one field "
                        "(Matter ≡ Consciousness ≡ Innovation) and its self-similar echoes"),
            ("Q", "GQ", "scale 0 · Q — the resonance φ⋂Ω: where the child's touch "
                        "of matter meets the child's experience of consciousness, without forcing"),
            ("P", "GP", "scale 0 · P — the gradient δE/δV→∇: the flow touch → experience "
                        "→ self-inquiry that brings to life the New, the Authentic, the Original"),
        ], panes)
        surfaces = dict(r0)

        # adaptive descent — classify all siblings, descend all unformed in waves
        descended = set()
        frontier = [("G", "GG", "scale 0"), ("Q", "GQ", "scale 0"),
                    ("P", "GP", "scale 0")]
        for depth in range(1, max_depth + 1):
            to_descend = []
            for (L, addr, lvl) in frontier:
                if addr in descended:
                    continue
                klass, reason = self.classify(L, surfaces[addr])
                if klass == "unformed":
                    to_descend.append((L, addr, reason))
                else:
                    self.nav_line("stay", addr, lvl, klass, reason)
            if not to_descend:
                break
            log("scale −%d · descent wave (%d corners unformed)"
                % (depth, len(to_descend)))
            for (L, addr, reason) in to_descend:
                self.nav_line("descend", addr, "scale −%d" % depth,
                              "unformed", reason)
            # open every unformed corner's cell in ONE parallel wave
            w = []
            for (L, addr, _r) in to_descend:
                for SL in "GQP":
                    w.append((SL, addr + SL,
                              "scale −%d · within %s · %s" % (depth, addr, SL), ""))
            sub = self.fan_out_parallel(w, panes)
            surfaces.update(sub)
            # converge every descended corner's V in ONE parallel wave
            conv = []
            for (L, addr, _r) in to_descend:
                handoff = {"G": sub[addr + "G"], "Q": sub[addr + "Q"],
                           "P": sub[addr + "P"]}
                conv.append(("V", addr + "V",
                             "scale −%d · converge %s (its own B″)" % (depth, addr),
                             handoff))
            cv = self.fan_out_parallel(conv, panes)
            next_frontier = []
            for (L, addr, _r) in to_descend:
                surfaces[addr] = cv[addr + "V"]
                descended.add(addr)
                self.nav_line("converge", addr + "V", "scale −%d" % depth, "—",
                              "descended corner replaced by its own B″")
                next_frontier.extend([(SL, addr + SL, "scale −%d" % depth)
                                      for SL in "GQP"])
            frontier = next_frontier

        # scale 0 — school converge (V)
        log("scale 0 · school converge (V)")
        self.nav_line("converge", "GV (school)", "scale 0", "—",
                      "school V composes the B″ from α + the (descended) corners")
        school_b = self.ask(
            "V", "GV",
            "scale 0 · V — compose the B″: crystallize the one field as the thing "
            "the school teaches, carrying α faithfully",
            {"G (essence)": surfaces["GG"],
             "Q (resonance)": surfaces["GQ"],
             "P (gradient)": surfaces["GP"]},
            panes)
        results["SCHOOL_B"] = school_b
        ended_in, status = self._semantic_end(school_b)
        log("scale 0 · school B″ composed (%s / %s)" % (ended_in, status))

        # scale +1 — the field: ascend for unity/clarity
        log("scale +1 · field fan-out + converge (the ascent)")
        self.nav_line("ascend", "ε (field)", "scale +1", "—",
                      "ascend to the field — resolve fragmentation, read the unity from above")
        r = {"G (the school)": school_b}
        r.update(self.fan_out([
            ("Q", "Q", "scale +1 · Q — what does the field hold that meets the "
                       "school's one field?"),
            ("P", "P", "scale +1 · P — where does the school's energy flow in the "
                       "wider field?"),
        ], panes))
        r["V"] = self.ask(
            "V", "V",
            "scale +1 · V — compose the final B″ across the scales",
            r, panes)
        results["FIELD_B"] = r["V"]

        axis_rec = self.close_axis(ended_in, r["V"])
        log("DONE")
        total_s = round(time.time() - t0, 1)
        self._append_line(self._swarm_line(
            "run-end", "NOTE", None,
            "the adaptive navigation swarm ended — %d turns, %.1fs total, ended_in %s"
            % (len(self.turns), total_s, ended_in),
            {"status": status, "ended_in": ended_in,
             "actions": len(self.turns), "total_s": total_s,
             "navigation": self.nav, "axis": axis_rec}))

        out = os.path.join(CELL, "swarm", "navigation-run-result.json")
        with open(out, "w", encoding="utf-8") as fh:
            json.dump({"results": results, "turns": self.turns,
                       "navigation": self.nav, "axis": axis_rec,
                       "max_depth": max_depth, "total_s": total_s,
                       "status": status, "ended_in": ended_in},
                      fh, ensure_ascii=False, indent=2)
        self.log_run_generic("field-grammar-navigation", status, ended_in, total_s,
                             extra={"bpp": school_b[:600],
                                    "axis": axis_rec,
                                    "navigation": self.nav})
        return {"status": status, "ended_in": ended_in,
                "turns": len(self.turns), "total_s": total_s,
                "saved": out, "navigation": self.nav, "axis": axis_rec,
                "results": results}


def main(argv):
    import argparse
    p = argparse.ArgumentParser(prog="navigation_conductor")
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
    nc = NavigationConductor(args.scenario, args.ledger, args.trail, spec=spec)
    result = nc.run_navigation(max_depth=args.max_depth, axis=args.axis)
    result["reset"] = not args.no_reset
    print(json.dumps({"status": result["status"], "ended_in": result["ended_in"],
                      "turns": result["turns"], "total_s": result["total_s"],
                      "saved": result["saved"], "reset": result["reset"],
                      "axis": result["axis"], "navigation": result["navigation"]},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main(sys.argv[1:])
