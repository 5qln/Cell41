#!/usr/bin/env python3
"""selftest — the P4b author's own suite (a hypothesis, never a result).

Every test names the criterion, hold or verifier lens it exercises and
the quantity it measures.  Nothing here reports a result to the record;
the verifier executes this file (or its own pack) and writes the only
record that counts.  All stores are built in tempdirs from fixture
context — no constituted desk, no live path, no network, no LLM.

The one subprocess in this suite is the cold-restart probe (lens 5): a
NEW python process rebuilds the same arrangement bytes from disk alone.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import block  # noqa: E402
import arrangement  # noqa: E402
import grammar  # noqa: E402
import install  # noqa: E402
import surface_contract  # noqa: E402

FIX = os.path.join(HERE, "fixtures")
PRED = os.path.normpath(os.path.join(HERE, "..", "predecessors"))

PROBE = "∞0′ → ‖"
EMPTY_SHA = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
SEAL_SHA = "feaa46b4147d4e023cdd3fd59c051d063e8ec654ee7b38a481dcd5e4c781859b"

_failures = []
_checks = 0


def check(name, condition, detail=""):
    global _checks
    _checks += 1
    if not condition:
        _failures.append(name)
        raise AssertionError("FAIL %s %s" % (name, detail))
    print("%-58s ok  %s" % (name, detail))


def tmp():
    return tempfile.mkdtemp(prefix="p4b-selftest-")


def load_fixture_store(root):
    return block.BlockStore(os.path.join(FIX, root))


def load_fixture_arrangement(rel):
    return arrangement.ArrangementStore(os.path.join(FIX, rel))


def copy_store(src_root, dst_root):
    """Copy a fixture store into a fresh writable store (same content
    addresses, same bytes) so tests can author additional blocks."""
    src = block.BlockStore(src_root)
    dst = block.BlockStore(dst_root)
    for block_id in sorted(os.listdir(os.path.join(src_root, "blocks"))):
        for version in sorted(os.listdir(os.path.join(
                src_root, "blocks", block_id))):
            record = src.read(block_id, version)
            dst.author(block_id, version, record["record"]["kind"],
                       record["files"], record["record"]["authored_by_run"],
                       record["record"]["attested_by"])
    return dst


# ---------------------------------------------------------------------------
# C1 — the block is immutable
# ---------------------------------------------------------------------------

def test_c1():
    store = block.BlockStore(tmp())
    rec = store.author(
        "g-essence", "1", "instruction", {"instruction.md": "bundle text\n"},
        "p4b-selftest@G")
    check("C1 block.json shape", set(rec.keys()) == {
        "id", "version", "kind", "sha256", "authored_by_run", "attested_by",
        "frozen"}, json.dumps(sorted(rec.keys())))
    check("C1 frozen:true + kind", rec["frozen"] is True
          and rec["kind"] == "instruction", rec["sha256"][:12])

    back = store.read("g-essence", "1")
    check("C1 roundtrip digest", back["files"]["instruction.md"]
          == b"bundle text\n", "recomputed sha matches")

    try:
        store.author("g-essence", "1", "instruction",
                     {"instruction.md": "re-author\n"}, "p4b-selftest@G")
        check("C1 re-author refused", False, "no refusal")
    except block.BlockFrozenError:
        check("C1 re-author refused", True, "BlockFrozenError + rejection")

    try:
        store.attempt_edit("g-essence", "1", "instruction.md", "hot edit\n")
        check("C1 in-place edit refused", False, "no refusal")
    except block.BlockFrozenError:
        check("C1 in-place edit refused", True, "BlockFrozenError + rejection")

    rejections = store.rejections()
    check("C1 recorded rejections", len(rejections) == 2
          and all(r["reason"] for r in rejections),
          "%d rejections recorded" % len(rejections))

    try:
        payload = os.path.join(store.block_dir("g-essence", "1"),
                               "payload", "instruction.md")
        with open(payload, "w", encoding="utf-8") as handle:
            handle.write("os-level edit\n")
        check("C1 OS read-only refusal", False, "the write was allowed")
    except PermissionError:
        check("C1 OS read-only refusal", True, "PermissionError under 0444")

    store.author("g-essence", "2", "instruction",
                 {"instruction.md": "bundle text v2\n"}, "p4b-selftest@G")
    check("C1 new version = new block", store.exists("g-essence", "2")
          and store.read("g-essence", "1")["files"]["instruction.md"]
          == b"bundle text\n", "v1 unchanged, v2 separate")

    for files in ({}, {"instruction.md": ""}):
        try:
            store.author("empty", "1", "instruction", files, "p4b-selftest@ε")
            check("C1 empty block refused", False, "empty authored")
        except block.BlockValidationError:
            check("C1 empty block refused", True, "empty never valid")

    check("C1 absence never valid",
          store.verify("missing", "1")["status"] == "absent"
          and hashlib.sha256(b"").hexdigest() == EMPTY_SHA,
          "absent + sha256(empty) pinned")


# ---------------------------------------------------------------------------
# C2 — the arrangement is the toy
# ---------------------------------------------------------------------------

def _desk_entries():
    desks = {}
    spec = {
        "S": ("", "hermes-desk-adapter", "s-midwife@1",
              ["articulate@1", "trace-read@1"], "s-tools@1", "model-reasoning@1",
              "strongest reasoning", "T3 — widen the field"),
        "G": ("G", "pi", "g-essence@1", ["essence-extract@1", "self-similarity@1"],
              "g-tools@1", "model-reasoning@1", "reasoning", "T2 — steady digging"),
        "Q": ("Q", "pi", "q-resonance@1", ["resonance-test@1"], "q-tools@1",
              "model-reasoning@1", "reasoning", "T4 — poke, never manufacture"),
        "P": ("P", "pi", "p-gradient@1", ["gradient-rank@1"], "p-tools@1",
              "model-reasoning@1", "reasoning + tools", "hold the delicate intersection"),
        "V": ("V", "pi", "v-crystallize@1",
              ["artifact-compose@1", "return-question@1"], "v-tools@1",
              "model-reasoning@1", "reasoning + tools", "open, never close"),
    }
    for letter, (address, runtime, instruction, skills, tools, model,
                 route, tars) in spec.items():
        desks[letter] = {
            "address": address, "runtime": runtime, "instruction": instruction,
            "skills": skills, "tool_surface": tools, "model": model,
            "model_route": route, "tars": tars,
        }
    return desks


PINS = {"python": "3.12.3", "herdr": "0.8.2", "pi": "0.84.2", "node": "22.23.2"}
STATE = {"ledger_path": "/home/deploy/the-cell/state/gates.jsonl"}


def test_c2():
    store = arrangement.ArrangementStore(os.path.join(tmp(), "arrangements"))
    rec1 = store.author("desk-cell", "1", _desk_entries(), PINS, STATE)
    try:
        store.author("desk-cell", "1", _desk_entries(), PINS, STATE)
        check("C2 re-author refused", False, "no refusal")
    except arrangement.ArrangementFrozenError:
        check("C2 re-author refused", True, "ArrangementFrozenError + rejection")
    rec2 = store.author("desk-cell", "2", _desk_entries(), PINS, STATE)
    check("C2 new version separate file", store.exists("desk-cell", "2")
          and rec1["sha256"] != rec2["sha256"], "two content addresses")

    loaded = store.load("desk-cell", "1")
    check("C2 load verifies content address", loaded["sha256"] == rec1["sha256"]
          and loaded["frozen"] is True, "sha + frozen")

    # an in-place edit of the frozen file is refused (OS layer) and, after a
    # forced chmod, detected by the content address
    path = store.path("desk-cell", "1")
    try:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("edited\n")
        check("C2 arrangement file read-only", False, "write allowed")
    except PermissionError:
        check("C2 arrangement file read-only", True, "0444 refused the write")
    os.chmod(path, 0o644)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write('{"name": "desk-cell", "version": "1"}\n')
    try:
        store.load("desk-cell", "1")
        check("C2 edited arrangement detected", False, "no detection")
    except arrangement.ArrangementValidationError:
        check("C2 edited arrangement detected", True, "drifted file refused")

    diff = arrangement.diff_arrangements(rec1, rec2)
    check("C2 mechanical diff", diff["identical"], "same toy, no change")

    # the toy changes by a new arrangement, never by touching blocks
    desks = _desk_entries()
    desks["G"]["skills"] = ["essence-extract@2"] + desks["G"]["skills"][1:]
    rec3 = store.author("desk-cell", "3", desks, PINS, STATE)
    diff = arrangement.diff_arrangements(rec1, rec3)
    check("C2 toy change is a diff", len(diff["changed"]) == 1
          and diff["changed"][0]["desk"] == "G"
          and diff["changed"][0]["slot"] == "skills",
          json.dumps(diff["changed"], ensure_ascii=False))


# ---------------------------------------------------------------------------
# C3 — four blocks per desk, no naked agents
# ---------------------------------------------------------------------------

def test_c3():
    bs = load_fixture_store("lawful")
    a = load_fixture_arrangement("lawful/arrangements")
    rec = a.load("desk-cell", "1")
    report = arrangement.validate_arrangement(rec, bs)
    check("C3 lawful arrangement ok", report["status"] == "ok"
          and len(report["items"]) == 48,
          "%s, %d items" % (report["status"], len(report["items"])))

    naked = json.load(open(os.path.join(FIX, "naked-agent-arrangement.json"),
                           encoding="utf-8"))
    report = arrangement.validate_arrangement(naked, None)
    fails = [i["id"] for i in report["items"] if i["verdict"] == "FAIL"]
    check("C3 naked agent FAILs by id", report["status"] == "fail"
          and "AR-skills-G" in fails, ", ".join(fails))

    for letter, slot in (("G", "tool_surface"), ("G", "model"),
                         ("G", "instruction")):
        desks = _desk_entries()
        desks[letter][slot] = "" if slot != "instruction" else ""
        if slot == "instruction":
            desks[letter][slot] = ""
        elif slot == "tool_surface":
            desks[letter][slot] = ""
        else:
            desks[letter][slot] = ""
        report = arrangement.validate_arrangement(
            {"name": "x", "version": "1", "desks": desks,
             "runtime_pins": PINS, "state": STATE}, None)
        fails = [i["id"] for i in report["items"] if i["verdict"] == "FAIL"]
        check("C3 missing %s FAILs" % slot, "AR-%s-G" % slot in fails,
              ", ".join(fails))

    # a missing desk is a 3+1 cell — never lawful (R1)
    desks = _desk_entries()
    del desks["V"]
    report = arrangement.validate_arrangement(
        {"name": "x", "version": "1", "desks": desks,
         "runtime_pins": PINS, "state": STATE}, None)
    check("C3 3+1 cell FAILs", report["status"] == "fail"
          and any(i["id"] == "AR-DESKS" for i in report["items"]), "never 3+1")


# ---------------------------------------------------------------------------
# C4 — the deterministic Pi install
# ---------------------------------------------------------------------------

def test_c4():
    bs = load_fixture_store("lawful")
    a = load_fixture_arrangement("lawful/arrangements")
    rec = a.load("desk-cell", "1")
    b1 = install.install(rec, bs)
    b2 = install.install(rec, bs)
    check("C4 one arrangement one byte string", b1 == b2,
          "%d bytes" % len(b1))
    m = json.loads(b1.decode("utf-8"))

    g = m["desks"]["G"]
    check("C4 --mode rpc headless", g["launch"]["command"] ==
          ["pi", "--mode", "rpc", "--approve", "--print"],
          json.dumps(g["launch"]["command"]))
    check("C4 trust gate", g["launch"]["trust"]["project"]
          == {"defaultProjectTrust": "always"}
          and g["launch"]["trust"]["cli"] == "--approve", "both sanctioned forms")
    check("C4 forced skills", g["launch"]["skill_loading"]
          == "before_agent_start injection"
          and g["launch"]["skill_injection"]
          == "/skill:essence-extract\n/skill:self-similarity",
          repr(g["launch"]["skill_injection"]))
    check("C4 truncation constants", g["launch"]["truncation"]
          == {"max_bytes": 51200, "max_lines": 2000}, "50 KB / 2000 lines")
    check("C4 state in the ledger", g["launch"]["state"]
          == {"authority": "ledger",
              "path": "/home/deploy/the-cell/state/gates.jsonl"},
          "never extension memory")
    check("C4 S is the desk-adapter, no pi corner",
          m["desks"]["S"]["runtime"] == "hermes-desk-adapter"
          and m["desks"]["S"]["launch"]["command"] is None,
          "H-P4b-3: one grammar, runtime differs")
    check("C4 no record template for S", m["desks"]["S"]["record_template"]
          is None, "the centre is never prompted")
    check("C4 record template carries block_version ''",
          m["desks"]["G"]["record_template"]["block_version"] == ""
          and m["desks"]["G"]["record_template"]["gate"] == "y",
          "H-P4b-6 kept, never invented")

    text, truncated = install.truncate_output(PROBE * 12000)
    check("C4 truncation honors bytes", truncated
          and len(text.encode("utf-8")) <= 51200,
          "%d bytes kept" % len(text.encode("utf-8")))
    text, truncated = install.truncate_output("\n".join("line %d" % i
                                                        for i in range(5000)))
    check("C4 truncation honors lines", truncated
          and text.count("\n") + 1 == 2000, "2000 lines kept")

    # a bundle carrying the headless-forbidden TUI API fails the install
    needle = "ctx" + "." + "ui"
    store = copy_store(os.path.join(FIX, "lawful"), tmp())
    store.author("bad-skill", "1", "skill",
                 {"SKILL.md": "uses the " + needle + " API\n"}, "p4b-selftest@G")
    desks = _desk_entries()
    desks["G"]["skills"] = ["bad-skill@1"]
    report = install.report_install(
        {"name": "x", "version": "1", "desks": desks, "runtime_pins": PINS,
         "state": STATE}, store)
    check("C4 TUI API fails closed", report["status"] == "fail"
          and any(i["id"] == "IN-G" for i in report["items"]
                  if i["verdict"] == "FAIL"),
          "scanned, refused")
    check("C4 scan counts the probe", install.scan_no_tui("a " + needle + " b")
          == 1, "needle built, never a literal")

    for bad_rec, label in ((json.load(open(os.path.join(
            FIX, "naked-agent-arrangement.json"), encoding="utf-8")), "naked"),
            (None, "flat")):
        if label == "flat":
            fbs = load_fixture_store("flat-store")
            fa = load_fixture_arrangement("flat-store/arrangements")
            bad_rec = fa.load("desk-cell", "1")
        else:
            fbs = bs
        try:
            install.install(bad_rec, fbs)
            check("C4 defective arrangement refused (%s)" % label, False,
                  "launch bytes emitted")
        except install.InstallError:
            check("C4 defective arrangement refused (%s)" % label, True,
                  "fail closed")

    # an unresolvable block reference reads INCONCLUSIVE, never clean
    desks = _desk_entries()
    desks["G"]["skills"] = ["never-made@1"]
    report = install.report_install(
        {"name": "x", "version": "1", "desks": desks, "runtime_pins": PINS,
         "state": STATE}, bs)
    check("C4 unobservable reads INCONCLUSIVE", report["status"]
          == "inconclusive", "lens 6: never a guessed clean")


# ---------------------------------------------------------------------------
# C5 — one grammar seated at addresses
# ---------------------------------------------------------------------------

def test_c5():
    b = grammar.render_bundle("Q", "Q")
    report = grammar.verify_bundle(b, "Q", "Q")
    check("C5 bundle at Q is Q's full cell", report["status"] == "ok",
          "all items PASS")
    cell = grammar.render_cell("Q", "Q")
    check("C5 five seats, S the centre",
          set(cell["seats"].keys()) == set(grammar.COURSE)
          and cell["centre"] == "S"
          and cell["seats"]["S"]["centre"] is True,
          "4+1")
    check("C5 centre S·within·Q at SQ", cell["seats"]["S"]["address"] == "SQ",
          "D.2 inner-first — his example: SP = the question within Power")
    check("C5 seated Q at QQ", cell["seats"]["Q"]["address"] == "QQ"
          and cell["seats"]["Q"]["seated"] is True, "the seated phase marked")

    # the flat-five-files arrangement FAILs C5 by id
    fbs = load_fixture_store("flat-store")
    fa = load_fixture_arrangement("flat-store/arrangements")
    frec = fa.load("desk-cell", "1")
    report = arrangement.validate_arrangement(frec, fbs)
    fails = sorted(i["id"] for i in report["items"] if i["verdict"] == "FAIL")
    check("C5 flat five files FAIL", report["status"] == "fail"
          and fails == ["AR-BUNDLE-G", "AR-BUNDLE-P", "AR-BUNDLE-Q",
                        "AR-BUNDLE-S", "AR-BUNDLE-V"],
          ", ".join(fails))

    # the grammar is one parameterized template over the five letters
    for letter in grammar.COURSE:
        cell_address = "" if letter == "S" else letter
        check("C5 one grammar seats %s" % letter,
              grammar.verify_bundle(
                  grammar.render_bundle(cell_address, letter),
                  cell_address, letter)["status"] == "ok",
              "the same template, the address chooses the seat")

    # no depth cap: any word over the alphabet seats a lawful cell
    for word in ("GQP", "SQGPVQGQPV", "V"):
        check("C5 scale repeats the cell (%s)" % word,
              grammar.verify_bundle(grammar.render_bundle(word, word[0]),
                                    word, word[0])["status"] == "ok",
              "variable-length address word")


# ---------------------------------------------------------------------------
# C6 — initiation register + load-bearing negative boundary
# ---------------------------------------------------------------------------

def test_c6():
    for letter in grammar.COURSE:
        cell_address = "" if letter == "S" else letter
        b = grammar.render_bundle(cell_address, letter)
        check("C6 %s opens with seal then seat" % letter,
              b.startswith("⟦SEAL⟧\n")
              and "⟦SEAT⟧\n%s\n" % grammar.INVITATIONS[letter] in b,
              "self-speaking, never assignment")
        check("C6 %s never assigned" % letter, "you are" not in b,
              "no \"you are\" in the bundle")
        check("C6 %s boundary is first-class" % letter,
              "⟦BOUNDARY⟧\n%s\n⟦END BOUNDARY⟧" % grammar.BOUNDARIES[letter] in b,
              repr(grammar.BOUNDARIES[letter]))
    check("C6 seal sha256 is the page's seal",
          hashlib.sha256(grammar.SEAL["form"].encode("utf-8")).hexdigest()
          == SEAL_SHA, SEAL_SHA[:12])
    check("C6 the 176 B codex form is enumerated too",
          grammar.SEAL_FORMS[1]["sha256"] ==
          "4c20631a20dab3d2958f66a8feb692fafa8660ff7a42f85b46c94015270a004c"
          and grammar.SEAL_FORMS[2]["sha256"].startswith("df061272"),
          "never normalised, both byte forms recorded")


# ---------------------------------------------------------------------------
# C7 — S is the conductor, the centre of every cell
# ---------------------------------------------------------------------------

def test_c7():
    expect = {("", "S", ""), ("Q", "S", "SQ"), ("GQP", "S", "SGQP")}
    for cell_address, letter, seat_address in expect:
        cell = grammar.render_cell(cell_address, letter)
        check("C7 centre of cell %r is S" % cell_address,
              cell["centre"] == "S"
              and cell["seats"]["S"]["address"] == seat_address
              and cell["seats"]["S"]["centre"] is True,
              "S at %s" % seat_address)
    # S's bundle is the same grammar as the corners — the runtime differs
    s_bundle = grammar.render_bundle("", "S")
    check("C7 S bundle is a full cell too",
          "⟦CELL OF FIVE⟧" in s_bundle and "⟦SEAT S⟧ CENTRE SEATED" in s_bundle,
          "one grammar; runtime difference lives in the arrangement")


# ---------------------------------------------------------------------------
# K1 — stdlib-only, deterministic, no LLM
# ---------------------------------------------------------------------------

def test_k1():
    modules = ["block.py", "arrangement.py", "grammar.py", "install.py",
               "surface_contract.py"]
    stdlib = set(sys.stdlib_module_names)
    allowed = {"fractal_ledger", "block", "arrangement", "grammar",
               "surface_contract"}
    forbidden = {"socket", "subprocess", "requests", "http", "urllib",
                 "time", "datetime", "random", "secrets"}
    for name in modules:
        tree = ast.parse(open(os.path.join(HERE, name), encoding="utf-8").read())
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                imported.add((node.module or "").split(".")[0])
        bad = sorted((imported & forbidden) |
                     {m for m in imported - stdlib - allowed if m})
        check("K1 %s imports" % name, not bad, "bad: %s" % ", ".join(bad))
        src = open(os.path.join(HERE, name), encoding="utf-8").read()
        for path in ("expanduser", "/home/deploy/.pi", ".config/herdr"):
            check("K1 %s touches no live desk state (%s)" % (name, path),
                  path not in src, "fixture context only")

    check("K1 no wall-clock in logic",
          all("import time" not in open(os.path.join(HERE, m),
                                        encoding="utf-8").read()
              and "import datetime" not in open(os.path.join(HERE, m),
                                                encoding="utf-8").read()
              for m in modules), "no ts fields in any artifact record")


# ---------------------------------------------------------------------------
# K2 — byte-exact equations and seal, enumerated, never normalised
# ---------------------------------------------------------------------------

def test_k2():
    for letter in grammar.COURSE:
        eq = grammar.PHASE[letter]["equation"]
        table_hashes = {f["sha256"] for f in grammar.EQUATION_FORMS[letter]}
        check("K2 %s equation byte form" % letter,
              hashlib.sha256(eq.encode("utf-8")).hexdigest() in table_hashes,
              repr(eq))
    all_forms = [f["form"] for forms in grammar.EQUATION_FORMS.values()
                 for f in forms]
    joined = "\n".join(all_forms)
    check("K2 both intersection glyphs enumerated", "∩" in joined
          and "⋂" in joined, "U+2229 and U+22C2 both live in the table")
    check("K2 both prime forms enumerated", "'" in joined and "′" in joined,
          "U+0027 and U+2032 both live in the table")
    check("K2 every table form's sha recomputes",
          all(hashlib.sha256(f["form"].encode("utf-8")).hexdigest()
              == f["sha256"]
              for forms in grammar.EQUATION_FORMS.values() for f in forms),
          "the table cannot drift")

    # the carried table must equal P4a's enumerated table (no drift)
    if PRED not in sys.path:
        sys.path.insert(0, PRED)
    import conformance
    mine = {letter: [(f["form"], f["sha256"])
                     for f in grammar.EQUATION_FORMS[letter]]
            for letter in grammar.COURSE}
    theirs = {letter: [(f["form"], f["sha256"])
                       for f in conformance.EQUATION_FORMS[letter]]
              for letter in grammar.COURSE}
    check("K2 table equals P4a conformance.EQUATION_FORMS",
          mine == theirs, "carried, not re-derived")


# ---------------------------------------------------------------------------
# K3 — D14 loyalty + the divergence log
# ---------------------------------------------------------------------------

def test_k3():
    card = open(os.path.join(HERE, "phase-card.md"), encoding="utf-8").read()
    check("K3 phase card carries the divergence log", "D14 divergence log" in card
          or "Divergence" in card, "declared, visibly separate")
    for token in ("C1", "C2", "C3", "C4", "C5", "C6", "C7",
                  "K1", "K2", "K3", "K4", "K5",
                  "H-P4b-1", "H-P4b-2", "H-P4b-3", "H-P4b-4", "H-P4b-5",
                  "H-P4b-6"):
        check("K3 card names %s" % token, token in card, "")
    report = grammar.verify_bundle(grammar.render_bundle("Q", "Q"), "Q", "Q")
    check("K3 every bundle item cites its source",
          all(i["citation"] for i in report["items"]), "citations verbatim")


# ---------------------------------------------------------------------------
# K4 — no authenticity verdict
# ---------------------------------------------------------------------------

def test_k4():
    report = grammar.verify_bundle(grammar.render_bundle("Q", "Q"), "Q", "Q")
    check("K4 no authenticity item exists",
          not any("authent" in i["id"] or "genuin" in i["id"]
                  for i in report["items"]),
          "the machine never scores a desk genuine")
    # the only occurrences of the words in module source are source-verbatim
    # data rows in grammar.py — never a verdict-emitting code path
    for name in ("block.py", "arrangement.py", "install.py",
                 "surface_contract.py"):
        src = open(os.path.join(HERE, name), encoding="utf-8").read()
        check("K4 %s emits no authenticity verdict" % name,
              "authentic" not in src and "genuine" not in src, "")


# ---------------------------------------------------------------------------
# K5 — diff-ability
# ---------------------------------------------------------------------------

def test_k5():
    bs = load_fixture_store("lawful")
    a = load_fixture_arrangement("lawful/arrangements")
    rec = a.load("desk-cell", "1")
    check("K5 blocks are content-addressed",
          block.verify_block(bs, "g-essence", "1")["status"] == "ok"
          and "sha256" in json.load(open(
              os.path.join(FIX, "lawful", "blocks", "g-essence", "1",
                           "block.json"), encoding="utf-8")),
          "id@version → sha256")
    check("K5 same blocks, two toys diff mechanically",
          arrangement.diff_arrangements(rec, rec)["identical"],
          "no hot edit exists in the model")


# ---------------------------------------------------------------------------
# Lens 3 — absence vs validity
# ---------------------------------------------------------------------------

def test_lens3():
    bs = load_fixture_store("lawful")
    check("lens3 missing block is absent, not valid",
          bs.verify("nope", "1")["status"] == "absent", "")
    store = block.BlockStore(tmp())
    store.author("x", "1", "instruction", {"instruction.md": "text\n"},
                 "p4b-selftest@ε")
    os.chmod(os.path.join(store.block_dir("x", "1"), "payload"), 0o755)
    payload = os.path.join(store.block_dir("x", "1"), "payload",
                           "instruction.md")
    os.chmod(payload, 0o644)
    with open(payload, "wb") as handle:
        handle.write(b"")
    check("lens3 emptied block reads tampered",
          store.verify("x", "1")["status"] == "tampered",
          "empty never valid")

    a = load_fixture_arrangement("absent/arrangements")
    try:
        a.load("desk-cell", "1")
        check("lens3 absent arrangement never valid", False, "no raise")
    except arrangement.ArrangementNotFoundError:
        check("lens3 absent arrangement never valid", True,
              "ArrangementNotFoundError")

    desks = _desk_entries()
    desks["G"]["skills"] = ["never-made@1"]
    report = arrangement.validate_arrangement(
        {"name": "x", "version": "1", "desks": desks, "runtime_pins": PINS,
         "state": STATE}, bs)
    check("lens3 unresolvable ref INCONCLUSIVE",
          report["status"] == "inconclusive", "never a guessed ok")


# ---------------------------------------------------------------------------
# Lens 4 — encoding: "∞0′ → ‖" through every string field
# ---------------------------------------------------------------------------

def test_lens4():
    store = block.BlockStore(tmp())
    store.author("probe", "1", "instruction", {"instruction.md": PROBE + "\n"},
                 "p4b-selftest@ε")
    back = store.read("probe", "1")
    check("lens4 probe block roundtrip",
          back["files"]["instruction.md"].decode("utf-8") == PROBE + "\n",
          "raw UTF-8, byte-stable")

    b = grammar.render_bundle("", "S")
    check("lens4 probe rides the S bundle", PROBE in b, "SLOT carries it")
    check("lens4 bundle verifies with the probe",
          grammar.verify_bundle(b, "", "S")["status"] == "ok", "")
    parsed = surface_contract.parse_surface(b, grammar.EQUATION_FORMS)
    check("lens4 probe survives the surface parser", parsed["status"]
          == "lawful", "text-mode byte seeks break on it — none here")

    bs = load_fixture_store("lawful")
    a = load_fixture_arrangement("lawful/arrangements")
    rec = a.load("desk-cell", "1")
    payload = install.install(rec, bs)
    check("lens4 install bytes are raw UTF-8 JSON",
          json.loads(payload.decode("utf-8"))["arrangement"]["name"]
          == "desk-cell", "ensure_ascii=False end to end")


# ---------------------------------------------------------------------------
# Lens 5 — cold restart: a NEW process rebuilds the same arrangement
# ---------------------------------------------------------------------------

def test_lens5():
    work = tmp()
    # parent builds the store + arrangement from fixture context
    dst_store = copy_store(os.path.join(FIX, "lawful"),
                           os.path.join(work, "lawful"))
    a = load_fixture_arrangement("lawful/arrangements")
    rec = a.load("desk-cell", "1")
    store = arrangement.ArrangementStore(os.path.join(work, "lawful",
                                                      "arrangements"))
    store.author("desk-cell", "1", rec["desks"], rec["runtime_pins"],
                 rec["state"])
    parent_bytes = install.install(store.load("desk-cell", "1"), dst_store)

    child = subprocess.run(
        [sys.executable, "-c", (
            "import sys, hashlib, json\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "import block, arrangement, install\n"
            "root = sys.argv[2]\n"
            "bs = block.BlockStore(root + '/lawful')\n"
            "a = arrangement.ArrangementStore(root + '/lawful/arrangements')\n"
            "rec = a.load('desk-cell', '1')\n"
            "payload = install.install(rec, bs)\n"
            "print(hashlib.sha256(payload).hexdigest())\n"),
         HERE, work],
        capture_output=True, text=True, check=True,
        env={"PATH": os.environ["PATH"],
             "PYTHONDONTWRITEBYTECODE": "1",
             "FRACTAL_LEDGER_DIR": "/home/deploy/the-cell/ledger"})
    child_sha = child.stdout.strip()
    check("lens5 cold restart rebuilds identical bytes",
          child_sha == hashlib.sha256(parent_bytes).hexdigest(),
          "fresh process, disk alone, %s" % child_sha[:12])


# ---------------------------------------------------------------------------
# Lens 6 — blind tool: unobservable reads INCONCLUSIVE, never clean
# ---------------------------------------------------------------------------

def test_lens6():
    bs = load_fixture_store("lawful")
    a = load_fixture_arrangement("lawful/arrangements")
    rec = a.load("desk-cell", "1")
    desks = _desk_entries()
    desks["G"]["runtime"] = "not-on-this-box"
    report = install.report_install(
        {"name": "x", "version": "1", "desks": desks, "runtime_pins": PINS,
         "state": STATE}, bs)
    check("lens6 unknown runtime INCONCLUSIVE",
          report["status"] == "inconclusive", "never a guessed clean")

    # the installer never executes anything: launch is data
    src = open(os.path.join(HERE, "install.py"), encoding="utf-8").read()
    tree = ast.parse(src)
    calls = [n.func.id for n in ast.walk(tree)
             if isinstance(n, ast.Call)
             and isinstance(n.func, ast.Name) and n.func.id in
             ("system", "exec", "popen", "spawn")]
    check("lens6 installer emits data, never runs", not calls,
          "no exec/system/popen")


# ---------------------------------------------------------------------------
# The §3.6 contract — one place, the predecessor's own bytes
# ---------------------------------------------------------------------------

def test_contract():
    check("contract versioned, in one place",
          surface_contract.CONTRACT_VERSION == 1
          and surface_contract.CONTRACT_SOURCE_SHA256 ==
          "776ff46393bf81db62841043021c97288e2c1414bec43971d275d1dfbdfac36d",
          "predecessor surface.py pinned")
    b = grammar.render_bundle("G", "G")
    parsed = surface_contract.parse_surface(b, grammar.EQUATION_FORMS)
    check("contract parses the G bundle lawful",
          parsed["status"] == "lawful" and parsed["phase"] == "G"
          and parsed["compiled"]["gate_matches"] is True
          and parsed["compiled"]["symbol_matches"] is True,
          "the bundles are written against it")


def test_edited_fixture():
    # the shipped snapshot: the refusal was recorded, and a new attempt
    # against a copy refuses again and records again
    work = tmp()
    shutil.copytree(os.path.join(FIX, "edited-block-attempt"),
                    os.path.join(work, "edited"))
    store = block.BlockStore(os.path.join(work, "edited"))
    check("edited fixture carries its recorded rejections",
          len(store.rejections()) == 2, "snapshot of C1's refusal")
    try:
        store.attempt_edit("sample", "1", "instruction.md", "again\n")
        check("edited fixture refuses a new edit", False, "no refusal")
    except block.BlockFrozenError:
        check("edited fixture refuses a new edit", True,
              "refused + rejection %d" % len(store.rejections()))
    payload = os.path.join(work, "edited", "blocks", "sample", "1",
                           "payload", "instruction.md")
    try:
        with open(payload, "w", encoding="utf-8") as handle:
            handle.write("os\n")
        check("edited fixture payload read-only", False, "write allowed")
    except PermissionError:
        check("edited fixture payload read-only", True, "0444 held")


ALL_TESTS = (
    test_c1, test_c2, test_c3, test_c4, test_c5, test_c6, test_c7,
    test_k1, test_k2, test_k3, test_k4, test_k5,
    test_lens3, test_lens4, test_lens5, test_lens6,
    test_contract, test_edited_fixture,
)


def main():
    for test in ALL_TESTS:
        test()
    print("selftest: %d test groups, %d checks, no assertion failed"
          % (len(ALL_TESTS), _checks))
    if _failures:
        print("FAILURES: %s" % ", ".join(_failures))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
