#!/usr/bin/env python3
"""fractal_conductor — the real 3-scale fractal swarm (spawn + lock + walk + converge + RECORD).

Extends `swarm/conductor.Conductor` (and therefore the attested `Orchestrator`)
so every turn lands in the B0 hash-chained ledger (`gates.jsonl`) and the
formation trail (`trail.jsonl`) — the multi-scale run is now *tracked*, not just
logged to `runs/`.

Proven mechanics (this session): `herdr agent start` spawns a fresh Pi agent in a
split pane (its own session); `5qln-lock` returns `status: locked`; `agent prompt`
fires; the answer is read from the agent's OWN session file by fence marker; two
Pi agents run in parallel.

The walk (bound B): the constitution stone is thrown at three scales — the school
cell (root), two levels down (each desk's own 4+1, then one representative branch),
and one level up (the father-frame). Each cell fans its G/Q/P corners out in
parallel and converges at its V. Results thread bottom-up; the school's V composes
the constitution B″, the field's V composes the final B″.

Every turn: spawn → lock → prompt → read → `_land_record` (ledger) + turn line
(trail). Boot + seed + run-end land on the trail; the chain verifies from GENESIS.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

sys.dont_write_bytecode = True

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from conductor import Conductor  # noqa: E402  (corrected read + planted word)

HERDR = "/usr/local/bin/herdr"
CELL = "/home/deploy/the-cell"
DESKS = os.path.join(CELL, "desks")
LOCK = os.path.join(CELL, "skills", "5qln-lock", "lock.py")
AUTHORED = os.path.join(CELL, "rounds", "R07-integration", "authored")
QUESTION = os.path.join(CELL, "nodes", "_", "question.md")

sys.path.insert(0, AUTHORED)
import surface_contract as sc  # noqa: E402  (the seam — pins the engine)

render_bundle = sc.grammar.render_bundle
parse_surface = sc.parse_surface
EQUATION_FORMS = sc.EQUATION_FORMS

AXIS_LOG = os.path.join(CELL, "swarm", "axis.jsonl")
NAV_JSONL = os.path.join(CELL, "swarm", "navigation.jsonl")
NAV_TEXT = os.path.join(CELL, "swarm", "navigation.log")


def reset_state(ledger_path, trail_path):
    """Archive + remove the ledger/trail so the next run starts a clean chain.

    MUST be called BEFORE constructing a conductor — the trail object must not
    have cached the old chain's last-hash. This fixes the re-arm bug: no stale
    prev_hash, and no double-seed (the run's `_seed_record` writes the single
    mechanical seed; the human's attestation is carried conversationally)."""
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    state_dir = os.path.dirname(ledger_path)
    removed = False
    for n in ("gates.jsonl", "trail.jsonl"):
        src = os.path.join(state_dir, n)
        if os.path.exists(src):
            backup = os.path.join(state_dir, "backup-" + stamp)
            os.makedirs(backup, exist_ok=True)
            shutil.copy2(src, os.path.join(backup, n))
            os.remove(src)
            removed = True
    return removed

# The ⟦runtime slot⟧ placeholder every desk's template carries until it fills the
# slot for real. A slot whose parsed ref equals this is UNFORMED, not content.
_PLACEHOLDER_REF = "sha256:" + hashlib.sha256(
    "⟦runtime slot — filled when this desk speaks⟧".encode("utf-8")).hexdigest()


class FractalConductor(Conductor):
    def __init__(self, scenario_path, ledger_path, trail_path, spec=None):
        super().__init__(scenario_path, ledger_path, trail_path, spec=spec)
        self._c = {"n": 0}
        self._idx = 0
        self.turns = []
        self.nav = []
        self.axis = ""

    # -- the navigation decision engine (shared) ---------------------------
    def nav_line(self, move, node, level, klass, reason):
        rec = {
            "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "move": move, "node": node, "level": level,
            "surface": klass, "reason": reason,
        }
        self.nav.append(rec)
        print("[NAV] node=%s level=%s surface=%s move=%s because=%s"
              % (node, level, klass, move, reason), flush=True)
        with open(NAV_JSONL, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        with open(NAV_TEXT, "a", encoding="utf-8") as fh:
            fh.write("[NAV] node=%s level=%s surface=%s move=%s because=%s\n"
                     % (node, level, klass, move, reason))

    def classify(self, letter, text):
        """Classify a desk surface: formed | unformed, semantically.

        formed = the desk's signature slot is filled (real content, not the
        runtime placeholder) — judged via parse_surface, not length. unformed =
        held / placeholder / no filled slot. (fragmented is resolved by the
        ascent, so it is not a descent trigger.)"""
        t = (text or "").strip()
        low = t.lower()
        if ":: held" in low or "i hold" in low:
            return "unformed", "desk held — refused to produce a surface"
        if "⟦runtime slot⟧" in t:
            return "unformed", "surface still carries the unfilled runtime slot"
        sig = {"G": ("α", "{α'}"),
               "Q": ("φ", "Ω"),
               "P": ("∇", "A"),
               "V": ("B''", "B″", "∞0'", "∞0′")}.get(letter, ())
        try:
            parsed = parse_surface(t, equation_forms=EQUATION_FORMS)
            slots = parsed.get("slots") or {}
            for name in sig:
                v = slots.get(name)
                if (isinstance(v, dict) and v.get("ref")
                        and v["ref"] != _PLACEHOLDER_REF and v.get("len", 0) > 0):
                    return "formed", "signature slot '%s' filled" % name
        except Exception:
            pass
        if len(t) < 250:
            return "unformed", "surface too thin (%d chars)" % len(t)
        return "formed", "surface formed (%d chars, slot not detected)" % len(t)

    def _inf0(self, text):
        """Extract only the return-question (∞0′) sentence — the line that
        STARTS with the ∞0′/∞0' marker (em-dash OR colon form), skipping the
        template definition line and the empty slot marker."""
        hits = []
        for ln in (text or "").splitlines():
            s = ln.strip().lstrip("*").strip()
            if not (s.startswith("∞0′") or s.startswith("∞0'")):
                continue
            if " :: " in s or "Enriched Return |" in s:
                continue
            if (s.startswith("∞0′ —") or s.startswith("∞0' —")
                    or s.startswith("∞0′:") or s.startswith("∞0':")):
                hits.append(s)
        return " ".join(hits)

    def load_axis(self):
        """Read the prior cycle's outgoing ∞0′ as this run's incoming axis."""
        if not os.path.exists(AXIS_LOG):
            return ""
        last = ""
        for line in open(AXIS_LOG, encoding="utf-8"):
            if line.strip():
                last = line
        if not last:
            return ""
        try:
            return json.loads(last).get("outgoing_∞0′") or ""
        except Exception:
            return ""

    def close_axis(self, ended_in, field_b_text=""):
        """Record the cycle: incoming ∞0′ → outgoing ∞0′."""
        outgoing = self._inf0(field_b_text)
        rec = {
            "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "incoming_∞0′": self.axis,
            "outgoing_∞0′": outgoing,
            "ended_in": ended_in,
        }
        with open(AXIS_LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        self.nav_line("axis", "∞0′", "cycle", "—",
                      "cycle closed: ∞0′ opened from %r → %r"
                      % (self.axis[:60], outgoing[:60]))
        return rec

    # -- primitives ---------------------------------------------------------
    def sh(self, argv, timeout=180):
        return subprocess.run(argv, capture_output=True, text=True, timeout=timeout)

    def _name(self):
        self._c["n"] += 1
        return "w%d" % self._c["n"]

    def planted(self):
        with open(QUESTION, encoding="utf-8") as fh:
            return fh.read().strip()

    def pane_map(self):
        data = json.loads(self.sh([HERDR, "pane", "list"]).stdout)
        return {(p.get("label") or "").strip(): p["pane_id"]
                for p in data["result"]["panes"]
                if (p.get("label") or "").strip() in ("G", "Q", "P", "V")}

    def spawn(self, letter, panes):
        name = self._name()
        pane = json.loads(self.sh([HERDR, "pane", "split", panes[letter],
                                   "--direction", "right",
                                   "--cwd", os.path.join(DESKS, letter)]).stdout)
        pane_id = pane["result"]["pane"]["pane_id"]
        started = json.loads(self.sh([HERDR, "agent", "start", name, "--kind", "pi",
                                      "--pane", pane_id, "--timeout", "90000", "--",
                                      "--skill", LOCK]).stdout)
        agent = started["result"]["agent"]
        # robust: under a rapid N-way fan-out, `agent start` can return the agent
        # before its session field is assigned — poll the agent list for it.
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
            raise RuntimeError("agent start failed for %s (no agent_session)" % name)
        ok = json.loads(self.sh(["python3", LOCK, letter, "--system",
                                 os.path.join(DESKS, letter, "SYSTEM.md")]).stdout)
        if ok.get("status") != "locked":
            raise RuntimeError("lock failed for %s: %s" % (letter, ok))
        time.sleep(0.5)
        return name, pane_id, agent["agent_session"]["value"]

    def fire(self, name, text):
        marker = "⟦END %s⟧" % name
        self.sh([HERDR, "agent", "prompt", name,
                 text + "\n\nWhen your answer is complete, emit exactly this end "
                 "marker on a line by itself, nothing after it: " + marker])
        return marker

    def read_fenced(self, session_path, marker, timeout_s=400):
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            last = None
            try:
                with open(session_path, encoding="utf-8") as fh:
                    for line in fh:
                        try:
                            obj = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        if obj.get("type") != "message":
                            continue
                        m = obj.get("message") or {}
                        if m.get("role") != "assistant":
                            continue
                        for c in m.get("content") or []:
                            if (isinstance(c, dict) and c.get("type") == "text"
                                    and marker in c["text"]):
                                last = c["text"]
            except OSError:
                pass
            if last is not None:
                return last
            time.sleep(1.0)
        raise RuntimeError("timeout reading %s" % session_path)

    def close(self, pane_id):
        try:
            self.sh([HERDR, "pane", "close", pane_id])
        except Exception:
            pass

    def build_prompt(self, letter, address, level, handoff):
        name = address if address else "ε"
        lines = ["⟦TURN cell=%s desk=%s⟧" % (name, letter),
                 render_bundle(address, letter).rstrip("\n"),
                 "⟦SCALE⟧ %s ⟦END SCALE⟧" % level,
                 "⟦PLANTED WORD — the human's question, carried verbatim⟧",
                 self.planted(),
                 "⟦END PLANTED WORD⟧"]
        if handoff:
            lines.append("⟦HANDOFF (content, never references)⟧")
            if isinstance(handoff, dict):
                lines.append("\n\n".join("=== %s ===\n%s" % (k, v)
                                         for k, v in handoff.items()))
            else:
                lines.append(str(handoff))
            lines.append("⟦END HANDOFF⟧")
        if self.axis:
            lines.append("⟦AXIS — the previous cycle's enriched return (∞0′), "
                         "carried forward as the seed of this cycle⟧\n"
                         + self.axis + "\n⟦END AXIS⟧")
        return "\n\n".join(lines)

    # -- recording ----------------------------------------------------------
    def _record_turn(self, letter, address, text, turn_time_s=None):
        self._idx += 1
        payload_ref = "fenced:sha256:" + hashlib.sha256(
            text.encode("utf-8")).hexdigest()
        visit = {"address": address, "letter": letter, "index": self._idx}
        landed = self._land_record(visit, payload_ref)
        content = {"detail": "answered", "payload_ref": payload_ref}
        if turn_time_s is not None:
            content["turn_time_s"] = round(turn_time_s, 1)
        self._append_line(self._swarm_line(
            "turn", letter, letter,
            "fractal %s turn at %s — attended live" % (letter, address or "ε"),
            content))
        self.turns.append({"address": address, "letter": letter,
                           "index": self._idx, "payload_ref": payload_ref,
                           "turn_key": landed.get("turn_key"),
                           "turn_time_s": (round(turn_time_s, 1)
                                           if turn_time_s is not None else None)})
        return text

    def fan_out(self, corners, panes):
        """corners: list of (letter, address, level). Fire all in parallel,
        read, record. Returns {address: answer}."""
        spawned = []
        for letter, address, level in corners:
            name, pane_id, session = self.spawn(letter, panes)
            t_start = time.time()
            marker = self.fire(name, self.build_prompt(letter, address, level, ""))
            spawned.append((letter, address, session, marker, pane_id, t_start))
        out = {}
        for letter, address, session, marker, pane_id, t_start in spawned:
            try:
                answer = self.read_fenced(session, marker)
                out[address] = self._record_turn(
                    letter, address, answer, time.time() - t_start)
            finally:
                self.close(pane_id)
        return out

    def fan_out_parallel(self, corners, panes):
        """corners: list of (letter, cell, level, handoff). Spawn + fire all in
        parallel, read all, record all. Returns {cell: answer}. Unlike fan_out,
        each corner carries its own handoff (for parallel converge waves)."""
        spawned = []
        for letter, cell, level, handoff in corners:
            name, pane_id, session = self.spawn(letter, panes)
            t_start = time.time()
            marker = self.fire(name, self.build_prompt(letter, cell, level, handoff))
            spawned.append((letter, cell, session, marker, pane_id, t_start))
        out = {}
        for letter, cell, session, marker, pane_id, t_start in spawned:
            try:
                answer = self.read_fenced(session, marker)
                out[cell] = self._record_turn(letter, cell, answer,
                                              time.time() - t_start)
            finally:
                self.close(pane_id)
        return out

    def _turn(self, letter, address, level, handoff, panes):
        name, pane_id, session = self.spawn(letter, panes)
        try:
            t_start = time.time()
            marker = self.fire(name, self.build_prompt(letter, address, level, handoff))
            answer = self.read_fenced(session, marker)
            return self._record_turn(letter, address, answer, time.time() - t_start)
        finally:
            self.close(pane_id)

    def _semantic_end(self, text):
        """Judge the school B″ SEMANTICALLY, not by slot presence: the B″ and
        ∞0′ slots must be FILLED (real content, not the ⟦runtime slot⟧
        placeholder) and V must not have held. Returns (ended_in, status)."""
        parsed = parse_surface(text, equation_forms=EQUATION_FORMS)
        slots = parsed.get("slots") or {}

        def filled(names):
            for n in names:
                v = slots.get(n)
                if isinstance(v, dict) and v.get("ref") \
                        and v["ref"] != _PLACEHOLDER_REF and v.get("len", 0) > 0:
                    return True
            return False

        v_held = ":: held" in (text or "")
        inf_formed = filled(("∞0'", "∞0′"))
        bpp_formed = filled(("B''", "B″"))
        if inf_formed and bpp_formed and not v_held:
            return "∞0′", "complete"
        return None, "inconclusive"

    # -- re-arm is deprecated: use reset_state() BEFORE construction ---------
    def re_arm(self, *a, **k):
        raise RuntimeError(
            "re_arm is deprecated — call reset_state(ledger, trail) BEFORE "
            "constructing the conductor; the run's _seed_record writes the single "
            "mechanical seed (the human's attestation is carried conversationally).")

    def log_run_generic(self, name, status, ended_in, total_s, extra=None):
        """Unified auto-log: append state/runs.jsonl + write runs/<ts>-<name>.md."""
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        stone = self.planted()[:200]
        entry = {
            "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "run_id": "%s-%s" % (name, stamp),
            "conductor": self.__class__.__name__,
            "stone": stone,
            "status": status, "ended_in": ended_in,
            "turns": len(self.turns), "total_s": total_s,
        }
        entry.update(extra or {})
        with open(os.path.join(CELL, "state", "runs.jsonl"), "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
        md = os.path.join(CELL, "runs", "%s-%s.md" % (stamp, name))
        with open(md, "w", encoding="utf-8") as fh:
            fh.write("# Run — %s (auto-logged)\n\n" % name)
            fh.write("- **when:** %s\n" % entry["ts"])
            fh.write("- **conductor:** %s\n" % entry["conductor"])
            fh.write("- **stone:** %s\n" % stone)
            fh.write("- **status:** %s · **ended_in:** %s · **turns:** %d · **%.1fs**\n\n"
                     % (status, ended_in, len(self.turns), total_s))
            fh.write("## Turn times\n\n")
            for t in self.turns:
                fh.write("- %s @ %s — %.1fs\n"
                         % (t["letter"], t["address"] or "ε", t["turn_time_s"] or 0))
            for k, v in (extra or {}).items():
                fh.write("\n## %s\n\n%s\n" % (k, v))
        return md

    def save_preset(self, depth, results, status, ended_in, total_s):
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        preset = {
            "name": "fractal-%s-d%d" % (stamp, depth),
            "depth": depth,
            "walk": "3-scale (bound B)" if depth == 2 else (
                "2-scale" if depth == 1 else "flat school+field"),
            "turns": len(self.turns),
            "status": status, "ended_in": ended_in, "total_s": total_s,
            "keys": sorted(results),
            "turns_detail": [{"letter": t["letter"], "address": t["address"],
                              "index": t["index"],
                              "turn_time_s": t["turn_time_s"]} for t in self.turns],
        }
        path = os.path.join(CELL, "swarm", "presets",
                            "fractal-%s-d%d.json" % (stamp, depth))
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(preset, fh, ensure_ascii=False, indent=2)
        return path

    def log_run(self, depth, results, status, ended_in, total_s, preset_path):
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        school_b = results.get("SCHOOL_B") or ""
        entry = {
            "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "run_id": "fractal-%s-d%d" % (stamp, depth),
            "depth": depth,
            "stone": self.planted()[:80],
            "status": status, "ended_in": ended_in,
            "turns": len(self.turns), "total_s": total_s,
            "turn_times_s": [t["turn_time_s"] for t in self.turns],
            "preset": preset_path,
            "constitution_excerpt": school_b[:300],
        }
        with open(os.path.join(CELL, "state", "runs.jsonl"), "a",
                  encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
        md = os.path.join(CELL, "runs", "%s-fractal-depth%d.md" % (stamp, depth))
        with open(md, "w", encoding="utf-8") as fh:
            fh.write("# Run — fractal depth %d (auto-logged)\n\n" % depth)
            fh.write("- **when:** %s\n" % entry["ts"])
            fh.write("- **stone:** %s\n" % self.planted()[:200])
            fh.write("- **status:** %s · **ended_in:** %s · **turns:** %d · **%.1fs**\n\n"
                     % (status, ended_in, len(self.turns), total_s))
            fh.write("## Turn times\n\n")
            for t in self.turns:
                fh.write("- %s @ %s — %.1fs\n"
                         % (t["letter"], t["address"] or "ε",
                            t["turn_time_s"] or 0))
            fh.write("\n## The constitution (SCHOOL_B)\n\n")
            fh.write(school_b + "\n")
        return md

    # -- the walk -----------------------------------------------------------
    def run_fractal(self, panes=None, depth=2):
        if any(line.get("event") == "run-end"
               for line in self._read_trail_lines()):
            return {"status": "already-complete", "actions": 0}
        panes = panes or self.pane_map()
        assert set(panes) == {"G", "Q", "P", "V"}, panes
        results = {}
        t0 = time.time()

        def log(k):
            print("[%6.1fs] %s" % (time.time() - t0, k), flush=True)

        self._emit_boot(self.read_states())
        self._seed_record({"address": "", "index": 0},
                          self.scenario["seed"]["ref"])

        # scale -2: cell GGG (only when depth >= 2)
        r_ggg = None
        if depth >= 2:
            log("scale -2 fan-out")
            r = self.fan_out([
                ("G", "GGGG", "scale -2 · the essence OF the essence OF the essence of the constitution"),
                ("Q", "GGGQ", "scale -2 · the resonance OF the essence-of-essence"),
                ("P", "GGGP", "scale -2 · the gradient OF the essence-of-essence"),
            ], panes)
            r["GGGV"] = self._turn("V", "GGGV",
                                   "scale -2 · the seed OF the essence-of-essence (converge)",
                                   r, panes)
            r_ggg = r["GGGV"]
            results["R_GGG"] = r_ggg
            log("scale -2 converged")

        # scale -1: four desk cells (only when depth >= 1)
        r_gg = r_gq = r_gp = r_gv = None
        if depth >= 1:
            def cell(center, g_descent=None, label=""):
                r = {}
                if g_descent is not None:
                    r["%sG" % center] = g_descent
                else:
                    r.update(self.fan_out([("G", "%sG" % center,
                                            "scale -1 · the essence within the %s desk" % label)],
                                          panes))
                r.update(self.fan_out([
                    ("Q", "%sQ" % center, "scale -1 · the resonance within the %s desk" % label),
                    ("P", "%sP" % center, "scale -1 · the gradient within the %s desk" % label),
                ], panes))
                v = "%sV" % center
                r[v] = self._turn("V", v,
                                  "scale -1 · the seed within the %s desk (converge)" % label,
                                  r, panes)
                return r, r[v]

            log("scale -1 · cell GG (essence%s)" % (", GGG carried" if r_ggg is not None else ""))
            _, r_gg = cell("GG", g_descent=r_ggg, label="essence")
            log("scale -1 · cell GQ (resonance)")
            _, r_gq = cell("GQ", label="resonance")
            log("scale -1 · cell GP (gradient)")
            _, r_gp = cell("GP", label="gradient")
            log("scale -1 · cell GV (seed)")
            _, r_gv = cell("GV", label="seed")
            results.update({"R_GG": r_gg, "R_GQ": r_gq,
                            "R_GP": r_gp, "R_GV": r_gv})

        # scale 0: the school cell (G)
        if depth >= 1:
            log("scale 0 · school converge (descended desks)")
            school_surfaces = {"GG (essence)": r_gg,
                               "GQ (resonance)": r_gq,
                               "GP (gradient)": r_gp,
                               "GV (seed)": r_gv}
            school_b = self._turn("V", "GV",
                                  "scale 0 · the school's Value — compose the constitution B″ "
                                  "from the four descended desks", school_surfaces, panes)
        else:
            log("scale 0 · school (flat — no descent)")
            r = self.fan_out([
                ("G", "GG", "scale 0 · the school's essence (α)"),
                ("Q", "GQ", "scale 0 · the school's resonance (φ⋂Ω)"),
                ("P", "GP", "scale 0 · the school's gradient (δE/δV)"),
            ], panes)
            r["GV"] = self._turn("V", "GV",
                                 "scale 0 · the school's Value — compose the constitution B″",
                                 r, panes)
            school_b = r["GV"]
        results["SCHOOL_B"] = school_b
        log("scale 0 · school B″ composed")
        ended_in, status = self._semantic_end(school_b)

        # scale +1: the field cell (ε)
        log("scale +1 · field fan-out + converge")
        r = {"G (the school)": school_b}
        r.update(self.fan_out([
            ("Q", "Q", "scale +1 · the field's resonance — what does the field hold that meets the school?"),
            ("P", "P", "scale +1 · the field's gradient — where does the school's energy flow in the field?"),
        ], panes))
        r["V"] = self._turn("V", "V",
                            "scale +1 · the field's Value — compose the final B″ across three scales",
                            r, panes)
        results["FIELD_B"] = r["V"]
        log("DONE")

        total_s = round(time.time() - t0, 1)
        self._append_line(self._swarm_line(
            "run-end", "NOTE", None,
            "the fractal swarm ended (depth %d) — %d turns, %.1fs total, ended_in %s"
            % (depth, len(self.turns), total_s, ended_in),
            {"status": status, "ended_in": ended_in,
             "actions": len(self.turns), "depth": depth, "total_s": total_s}))

        out = os.path.join(CELL, "swarm", "fractal-run-result-%s-d%d.json" % (
            datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
            depth))
        with open(out, "w", encoding="utf-8") as fh:
            json.dump({"results": results, "turns": self.turns,
                       "depth": depth, "total_s": total_s,
                       "status": status, "ended_in": ended_in},
                      fh, ensure_ascii=False, indent=2)
        return {"status": status, "ended_in": ended_in,
                "turns": len(self.turns), "depth": depth, "total_s": total_s,
                "saved": out, "keys": sorted(results), "results": results}


def main(argv):
    import argparse
    p = argparse.ArgumentParser(prog="fractal_conductor")
    p.add_argument("--scenario", default=os.path.join(CELL, "state", "word.json"))
    p.add_argument("--ledger", default=os.path.join(CELL, "state", "gates.jsonl"))
    p.add_argument("--trail", default=os.path.join(CELL, "state", "trail.jsonl"))
    p.add_argument("--spec", default=os.path.join(AUTHORED, "spec.json"))
    p.add_argument("--depth", type=int, default=2,
                   help="descent levels below the school: 0 none, 1 one, 2 full (default)")
    p.add_argument("--no-reset", action="store_true",
                   help="skip the state reset (continue on the existing chain)")
    args = p.parse_args(argv)
    spec = json.load(open(args.spec)) if os.path.exists(args.spec) else {}
    if not args.no_reset:
        reset_state(args.ledger, args.trail)
    fc = FractalConductor(args.scenario, args.ledger, args.trail, spec=spec)
    result = fc.run_fractal(depth=args.depth)
    result["reset"] = not args.no_reset
    if result.get("status") == "complete":
        preset = fc.save_preset(args.depth, result["results"],
                                result["status"], result["ended_in"],
                                result["total_s"])
        run_log = fc.log_run(args.depth, result["results"],
                             result["status"], result["ended_in"],
                             result["total_s"], preset)
        result["preset"] = preset
        result["run_log"] = run_log
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main(sys.argv[1:])
