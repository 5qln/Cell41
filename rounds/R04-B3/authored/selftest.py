#!/usr/bin/env python3
"""selftest — the B3 author's own suite (a hypothesis, never a result).

Every check names the criterion, hold or verifier lens it exercises and
the quantity it measures — the criterion AS WRITTEN, never a neighbour of
it (lens 1).  Nothing here reports a result to the record: a separate
verifier executes this file (or its own pack) and writes the only record
that counts, recomputing every verdict with its own implementation.  All
stores and node trees are built in tempdirs from the fixture context
under ./fixtures — no constituted desk, no socket, no network, no LLM
(H-B3-1).  Every run uses a fixed ledger clock so a byte-exact rebuild
is checkable (lens 2 / lens 5).

The one subprocess in this suite is the cold-restart probe (lens 5): a
NEW python process rebuilds the same node tree and ledger from the
static fixture on disk alone, and its bytes are compared against the
expected pins and against this process's own rebuild.
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

import descent  # noqa: E402
from descent import (  # noqa: E402
    Descent,
    apply_signed_path,
    axis_verdict,
    field_bytes,
    field_handoff,
    path_between,
    validate_node_record,
    validate_signed_path,
    validate_word,
    zoom_in,
    zoom_out,
)
import surface_contract  # noqa: E402

FIX = os.path.join(HERE, "fixtures")

# --- deterministic fixture constants ---------------------------------------

PROBE = "∞0′ → ‖"
EMPTY_SHA = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
FIXED_TS = "2026-08-29T12:00:00Z"
PLANT_QUESTION = "What is ∞0′ → ‖?\n"
ARTIFACT_TEXT = "⟦artifact⟧ B″: ∞0′ → ‖\n"
RETURN_TEXT = "∞0′ → ‖\n"
PLANT_REF = ("nodes/_/question.md@sha256:"
             + hashlib.sha256(PLANT_QUESTION.encode("utf-8")).hexdigest())
SKILL_TEXT = ("skill: descent-skill — PRD §7: at least one skill per desk "
              "(no naked agents, R4); the exact contents are a build task, "
              "not a requirements task (REQUIREMENTS E2).\n")
TOOL_TEXT = ("tool surface: descent-tool — PRD §7: a tool surface per desk; "
             "the descent never exercises it (H-B3-1).\n")
MODEL_TEXT = ("model: descent-model — PRD §7: one model across the desks "
              "(D6); the model is a block, swappable, never hardcoded "
              "doctrine (PRD §7 note).\n")
COURSE = ("S", "G", "Q", "P", "V")
ORDER = ("x", "y", "z", "a", "b")


def fixed_clock():
    return FIXED_TS


def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _att_ref(address, gate):
    return "attestation:fixture:" + hashlib.sha256(
        (address + "|" + gate).encode("utf-8")).hexdigest()[:12]


def _gate_payload(gate, address):
    return "fenced:sha256:" + _sha("fixture output for gate %s at %s"
                                   % (gate, address or "_"))


def _failing_payload(gate, address):
    return "fenced:sha256:" + _sha("fixture failing gate %s at %s"
                                   % (gate, address or "_"))


def _attested_record(address, gate, field, payload_ref):
    return descent.make_record(
        address=address, gate=gate, state="attested", mark="emergent",
        payload_ref=payload_ref,
        axis={"field": field, "delta": []}, axis_verdict="STASIS",
        corruption=None, tentative=False,
        turn_key=descent.turn_key(address, gate, "1", ""),
        block_version="", attestation_ref=_att_ref(address, gate))


def _failing_record(address, gate, field):
    return descent.make_record(
        address=address, gate=gate, state="held-pending", mark="mechanical",
        payload_ref=_failing_payload(gate, address),
        axis={"field": field, "delta": []}, axis_verdict="STASIS",
        corruption=None, tentative=False,
        turn_key=descent.turn_key(address, gate, "1", ""),
        block_version="", attestation_ref=None)


class FixtureWorld:
    """The fixture world — the caller-supplied stand-in for the desk walk
    and the human's acts (P4a's attest-provider pattern: the provider
    plays the human's channel; the engine never fabricates any of it and
    never writes ``state: "attested"`` itself)."""

    def __init__(self, nodes_root, ledger_path):
        self.nodes_root = nodes_root
        self.ledger_path = ledger_path

    def _node_record(self, address):
        path = os.path.join(self.nodes_root, descent.word_to_disk(address),
                            "cell.node.json")
        with open(path, "r", encoding="utf-8") as handle:
            return json.loads(handle.read())

    def _node_field(self, address):
        return self._node_record(address)["axis"]["field"]

    def _append(self, record):
        with descent.LedgerWriter(self.ledger_path, clock=fixed_clock) as w:
            return w.append(record)

    def _has_key(self, address, gate, key):
        loaded = descent.LedgerLoader(self.ledger_path).load(write_index=False)
        return any(r.get("turn_key") == key and r.get("address") == address
                   for r in loaded.records)

    def _attested(self, address, gate, payload_ref=None):
        key = descent.turn_key(address, gate, "1", "")
        if self._has_key(address, gate, key):
            return
        field = self._node_field(address)
        self._append(_attested_record(
            address, gate, field,
            payload_ref if payload_ref is not None
            else _gate_payload(gate, address)))

    def _failing(self, address, gate):
        key = descent.turn_key(address, gate, "1", "")
        if self._has_key(address, gate, key):
            return
        field = self._node_field(address)
        self._append(_failing_record(address, gate, field))

    def prepare(self, address, spec):
        """Lay the node's walk state: the gates before the failing one are
        walked and attested (the fixture's human fiction), the failing
        gate is proposed and fails to lock.  ``consume`` declares that a
        downstream gate consumed the tentative seed as evidence (the
        T-R5-02 dependency-audit case)."""
        gate = spec.get("gate")
        index = ORDER.index(gate)
        if spec.get("consume"):
            node = self._node_record(address)
            priors = ORDER[1:index]
            for position, prior in enumerate(priors):
                if position == len(priors) - 1:
                    # the last walked gate consumed the tentative seed as
                    # evidence (the T-R5-02 dependency-audit case)
                    self._attested(address, prior,
                                   payload_ref=node.get("seed_ref"))
                else:
                    self._attested(address, prior)
            self._failing(address, gate)
        else:
            for prior in ORDER[1:index]:
                self._attested(address, prior)
            self._failing(address, gate)

    def materialize(self, address, leaf):
        """Play the leaf's V evidence: the walked gates (y z a b, the
        human's acts) and the artifact / ∞0′ content files, with the
        node record's evidence refs.  ``unattested_v`` leaves the V
        proposed-but-unattested (the held path)."""
        leaf = leaf or {}
        walks = leaf.get("walks") or "yzab"
        for gate in walks:
            if gate == "b" and leaf.get("unattested_v"):
                self._failing(address, "b")
            else:
                self._attested(address, gate)
        record = self._node_record(address)
        updates = {}
        disk = descent.word_to_disk(address)
        if leaf.get("artifact_text") is not None:
            path = os.path.join(self.nodes_root, disk, "artifact.md")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(leaf["artifact_text"])
            updates["artifact_ref"] = (
                "nodes/%s/artifact.md@sha256:%s"
                % (disk, _sha(leaf["artifact_text"])))
        if leaf.get("return_text") is not None:
            path = os.path.join(self.nodes_root, disk, "return.md")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(leaf["return_text"])
            updates["infinity_zero_prime_ref"] = (
                "nodes/%s/return.md@sha256:%s"
                % (disk, _sha(leaf["return_text"])))
        if updates:
            record.update(updates)
            node_path = os.path.join(self.nodes_root, disk, "cell.node.json")
            with open(node_path, "w", encoding="utf-8") as handle:
                handle.write(descent.canonical_json(record) + "\n")


# --- the fixture builders --------------------------------------------------


def _root_record(anchor):
    return {
        "axis": {
            "field": {"mode": "inherited", "anchor": anchor},
            "delta": [anchor],
        },
        "signed_path": "",
        "tentative": False,
        "arrangement": "cell-%s@1" % _sha("")[:10],
    }


def _append_record(ledger_path, record):
    with descent.LedgerWriter(ledger_path, clock=fixed_clock) as writer:
        return writer.append(record)


def build_start_case(target_dir):
    """The lawful start state shared by the descent cases: the root cell
    `_` (the plant — fixture fiction: human-written — already attested),
    gate y attested, gate z PROPOSED and failing to lock (the descent
    trigger), the shared blocks, and the root cell's arrangement seated
    through the P4b machinery (imported, never re-authored)."""
    nodes_root = os.path.join(target_dir, "nodes")
    ledger_path = os.path.join(target_dir, "state", "gates.jsonl")
    store_root = os.path.join(target_dir, "store")
    os.makedirs(os.path.join(nodes_root, "_"), exist_ok=False)
    os.makedirs(os.path.dirname(ledger_path), exist_ok=False)
    with open(os.path.join(nodes_root, "_", "question.md"), "w",
              encoding="utf-8") as handle:
        handle.write(PLANT_QUESTION)
    engine = Descent(nodes_root=nodes_root, ledger_path=ledger_path,
                     store_root=store_root, anchor="",
                     block_version="", clock=fixed_clock)
    block_store = descent.block.BlockStore(store_root)
    for block_id, kind, text in (("descent-skill", "skill", SKILL_TEXT),
                                 ("descent-tool", "surface", TOOL_TEXT),
                                 ("descent-model", "model", MODEL_TEXT)):
        block_store.author(block_id, "1", kind, {"payload.md": text.encode(
            "utf-8")}, authored_by_run="R04-B3-fixtures", attested_by=None)
    seating = engine.seat_arrangement("")
    with open(os.path.join(nodes_root, "_", "cell.node.json"), "w",
              encoding="utf-8") as handle:
        handle.write(descent.canonical_json(_root_record(PLANT_REF)) + "\n")
    anchored = {"mode": "anchored", "anchor": PLANT_REF}
    _append_record(ledger_path, descent.make_record(
        address="", gate="x", state="attested", mark="emergent",
        payload_ref=PLANT_REF,
        axis={"field": anchored, "delta": [PLANT_REF]},
        axis_verdict=None, corruption=None, tentative=False,
        turn_key=descent.turn_key("", "x", "1", ""),
        block_version="", attestation_ref="attestation:fixture:plant"))
    _append_record(ledger_path, _attested_record(
        "", "y", {"mode": "inherited", "anchor": PLANT_REF},
        _gate_payload("y", "")))
    _append_record(ledger_path, _failing_record(
        "", "z", {"mode": "inherited", "anchor": PLANT_REF}))
    return {"nodes_root": nodes_root, "ledger_path": ledger_path,
            "store_root": store_root, "arrangement": seating["ref"]}


LAWFUL_SCRIPT = {
    "steps": [{"gate": "z"}, {"gate": "a"}, {"gate": "y"}],
    "leaf": {"walks": "yzab", "artifact_text": ARTIFACT_TEXT,
             "return_text": RETURN_TEXT},
}

DRIFTED_FIELD = {"mode": "inherited",
                 "anchor": "nodes/_/question.md@sha256:" + "0" * 64}

MOVING_SCRIPT = {
    "steps": [{"gate": "z"}, {"gate": "a", "field": DRIFTED_FIELD}],
    "leaf": {},
}

VOID_SCRIPT = {
    "steps": [{"gate": "z"}],
    "leaf": {"walks": "yzab", "artifact_text": ARTIFACT_TEXT},
}

CONSUMED_SCRIPT = {
    "steps": [{"gate": "z"}, {"gate": "a", "consume": True}],
    "leaf": {},
}


def run_case(start_dir, out_dir, script, budget=None):
    """Copy the start fixture to ``out_dir`` and walk the descent — the
    engine plus the fixture world.  Returns the walk result."""
    shutil.copytree(start_dir, out_dir, ignore=shutil.ignore_patterns(
        "expected", "*.lock", "spec.json", "README*"))
    nodes_root = os.path.join(out_dir, "nodes")
    ledger_path = os.path.join(out_dir, "state", "gates.jsonl")
    store_root = os.path.join(out_dir, "store")
    engine = Descent(nodes_root=nodes_root, ledger_path=ledger_path,
                     store_root=store_root, anchor="",
                     block_version="", clock=fixed_clock,
                     resource_budget=budget,
                     world=FixtureWorld(nodes_root, ledger_path))
    return engine.walk("", script)


def rebuild_probe(case_dir, out_dir):
    """The cold-restart probe (lens 5): rebuild the case's node tree and
    ledger from the static fixture on disk alone — a fresh process, a
    fresh Descent, nothing carried from a prior run."""
    with open(os.path.join(case_dir, "spec.json"), "r",
              encoding="utf-8") as handle:
        script = json.loads(handle.read())
    start = os.path.join(out_dir + ".start")
    shutil.copytree(case_dir, start, ignore=shutil.ignore_patterns(
        "expected", "*.lock", "spec.json", "README*"))
    return run_case(start, out_dir, script)


def _compare_tree(path_a, path_b):
    """Byte-compare two directory trees (every file, every byte)."""
    files_a = {}
    for dirpath, _, names in os.walk(path_a):
        for name in names:
            rel = os.path.relpath(os.path.join(dirpath, name), path_a)
            with open(os.path.join(dirpath, name), "rb") as handle:
                files_a[rel] = handle.read()
    files_b = {}
    for dirpath, _, names in os.walk(path_b):
        for name in names:
            rel = os.path.relpath(os.path.join(dirpath, name), path_b)
            with open(os.path.join(dirpath, name), "rb") as handle:
                files_b[rel] = handle.read()
    return files_a == files_b, files_a, files_b


# --- the suite ---------------------------------------------------------------

_failures = []
_checks = 0


def check(name, condition, detail=""):
    global _checks
    _checks += 1
    if not condition:
        _failures.append(name)
        raise AssertionError("FAIL %s %s" % (name, detail))
    print("%-56s ok  %s" % (name, detail))


def tmp():
    return tempfile.mkdtemp(prefix="b3-selftest-")


def _read_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.loads(handle.read())


def _source_lines(module_path):
    with open(module_path, "r", encoding="utf-8") as handle:
        return handle.read().split("\n")


def suite():
    descent_path = os.path.join(HERE, "descent.py")
    lines = _source_lines(descent_path)
    source = "\n".join(lines)
    tree = ast.parse(source)

    # -- C2 / H-B3-2: address ops under the DECLARED parameter ---------------
    check("C2-zoom-roundtrip-carried",
          zoom_in("Q", "P") == "PQ" and zoom_out("PQ") == "Q"
          and zoom_in("", "Q") == "Q" and zoom_out("Q") == ""
          and descent.grammar.WORD_ORDER == "inner_first",
          "the carried WORD_ORDER value drives the round-trips")
    check("C2-zoom-primitives-compose",
          zoom_in(zoom_in(zoom_in("", "Q"), "P"), "G") == "GPQ"
          and descent.deep_letter("GPQ") == "G"
          and descent.ancestor_chain("GPQ") == ["GPQ", "PQ", "Q", ""],
          "child addresses compose from zoom_in; ancestry from zoom_out")
    saved_order = descent.grammar.WORD_ORDER
    try:
        descent.grammar.WORD_ORDER = "outer_first"
        check("H-B3-2-outer-first-flip",
              zoom_in("Q", "P") == "QP" and zoom_out("QP") == "Q"
              and zoom_in(zoom_in(zoom_in("", "Q"), "P"), "G") == "QPG"
              and path_between("", "QPG") == "−Q−P−G"
              and apply_signed_path("", "−Q−P−G") == "QPG",
              "flipping the declared parameter flips the addresses — the "
              "same signed path string, no logic change (one-table flip)")
    finally:
        descent.grammar.WORD_ORDER = saved_order
    word_order_loads = [node for node in ast.walk(tree)
                        if isinstance(node, ast.Attribute)
                        and node.attr == "WORD_ORDER"
                        and isinstance(node.ctx, ast.Load)]
    parent_map = {}
    for parent_node in ast.walk(tree):
        for child in ast.iter_child_nodes(parent_node):
            parent_map[child] = parent_node
    one_spot = len(word_order_loads) == 1
    if one_spot:
        current = word_order_loads[0]
        while current is not None and not isinstance(current,
                                                     ast.FunctionDef):
            current = parent_map.get(current)
        one_spot = isinstance(current, ast.FunctionDef) and \
            current.name == "zoom_out"
    check("H-B3-2-WORD_ORDER-one-code-line",
          one_spot,
          "the letter-order touches exactly the two declared spots: "
          "zoom_in delegates to the imported seat_address, zoom_out is "
          "the only code branch on WORD_ORDER")
    check("C2-address-never-stored",
          validate_node_record(
              {"axis": {"field": {"mode": "inherited", "anchor": PLANT_REF},
                        "delta": []},
               "signed_path": "", "tentative": False,
               "address": "GPQ"})["status"] == "refused",
          "a node record storing an address is refused — addressing is "
          "derived, never stored as a separate identity (PRD §5.3)")
    check("C2-coordinate-anchor",
          zoom_out("") == "" and descent.word_to_disk("") == "_"
          and validate_word("GPQ") and not validate_word("gpq")
          and not validate_word("-GPQ"),
          "ε is a coordinate anchor (D.3/D.7), never a privileged root; "
          "the word grammar is byte-loyal (no case folding)")

    # -- C2: the signed path (AR3) -------------------------------------------
    check("C2-signed-path-malformed-ascii",
          validate_signed_path("-P-Q-P")["status"] == "malformed"
          and validate_signed_path("+-G")["status"] == "malformed"
          and "ASCII hyphen" in validate_signed_path("-P-Q-P")["reason"],
          "the malformed signed paths `-P-Q-P` and `+-G` are rejected — "
          "the ASCII hyphen is not the U+2212 descent operator (no byte "
          "normalisation, K2)")
    check("C2-signed-path-lawful-forms",
          validate_signed_path("")["status"] == "ok"
          and validate_signed_path("−P−Q−P") == {
              "status": "ok", "k": 0, "letters": ["P", "Q", "P"],
              "reason": "normalized +^k · −x₁…−x_m"}
          and validate_signed_path("+−G")["k"] == 1
          and validate_signed_path("+−G")["letters"] == ["G"]
          and validate_signed_path("+++−G")["k"] == 3
          and validate_signed_path("+·−G")["status"] == "ok"
          and validate_signed_path("++")["letters"] == [],
          "the AR3 forms parse; the empty path is the same node (D.6)")
    check("C2-signed-path-structural-rejections",
          validate_signed_path("+−+G")["status"] == "malformed"
          and validate_signed_path("−PQ")["status"] == "malformed"
          and validate_signed_path("P")["status"] == "malformed"
          and validate_signed_path("−")["status"] == "malformed"
          and validate_signed_path(None)["status"] == "absent",
          "all + first then all −; each − step carries exactly one letter "
          "(AR3, D.5)")
    check("C2-signed-path-roundtrip",
          path_between("", "GPQ") == "−Q−P−G"
          and apply_signed_path("", "−Q−P−G") == "GPQ"
          and path_between("Q", "GPQ") == "−P−G"
          and path_between("QP", "G") == "++·−G"
          and apply_signed_path("QP", "++·−G") == "G",
          "the path is the descent steps (chronological) — the same "
          "string under either convention; cousins normalize (D.6)")

    # -- C1: the axis ---------------------------------------------------------
    anchored = {"mode": "anchored", "anchor": PLANT_REF}
    inherited = field_handoff(anchored)
    check("C1-field-handoff",
          inherited == {"mode": "inherited", "anchor": PLANT_REF}
          and field_handoff(inherited) == inherited
          and field_bytes(inherited) == field_bytes(inherited),
          "the handoff carries the anchor byte-exact; provenance "
          "re-stamping is the descent's own act, never a drift")
    try:
        field_handoff({"mode": "inherited", "anchor": ""})
        check("C1-field-never-empty", False, "an empty anchor was accepted")
    except ValueError:
        check("C1-field-never-empty", True,
              "an empty axis anchor is refused — the field is never empty "
              "(PRD §5.4)")
    other_anchor = {"mode": "inherited",
                    "anchor": "nodes/_/question.md@sha256:" + "f" * 64}
    check("C1-verdicts",
          axis_verdict(anchored, other_anchor, "a@1", "b@1") == "MOVING"
          and axis_verdict(anchored, inherited, "a@1", "a@1") == "recast"
          and axis_verdict(anchored, inherited, "a@1", "b@1") == "STASIS",
          "MOVING iff fields differ · recast iff fields equal and surfaces "
          "equal · STASIS iff fields equal and surfaces differ (PRD §5.4)")

    # -- the lawful 3-deep descent (C1/C2/C3/C4/C6, lenses 1/2/3/4) -----------
    case_dir = os.path.join(FIX, "lawful-3deep")
    with open(os.path.join(case_dir, "spec.json"), "r",
              encoding="utf-8") as handle:
        lawful_script = json.loads(handle.read())
    work = tmp()
    result = run_case(case_dir, os.path.join(work, "run"), lawful_script)
    check("C1-3deep-returned",
          result["status"] == "returned" and result["steps_taken"] == 3
          and result["visited"] == ["", "Q", "PQ", "GPQ"],
          "PRD §B3: a 3-deep descent returns artifact + genuine ∞0′")
    run_nodes = os.path.join(work, "run", "nodes")
    fields = {}
    for address in ("", "Q", "PQ", "GPQ"):
        record = _read_json(os.path.join(
            run_nodes, descent.word_to_disk(address), "cell.node.json"))
        fields[address] = field_bytes(record["axis"]["field"])
    check("C1-field-byte-identical-end-to-end",
          len(set(fields.values())) == 1
          and fields[""] == field_bytes(inherited)
          and all(fields[a] == fields[""] for a in ("Q", "PQ", "GPQ")),
          "one invariant: axis.field byte-identical from root to leaf "
          "across the WHOLE descent, never per call (lens 2)")
    check("C1-step-handoffs-byte-exact",
          all(step["handoff_bytes_sha256"] == step[
              "child_field_bytes_sha256"] for step in result["steps"])
          and all(step["axis_verdict"] == "STASIS"
                  for step in result["steps"]),
          "each step's carried bytes equal the handoff bytes; the "
          "continuation reads STASIS (fields equal, surfaces differ)")
    check("C1-seed-records-honest",
          all(step["guard"]["corruption"] == "L2"
              for step in result["steps"]),
          "the machine-posed seed carries its L2 manufacturing signal — "
          "recorded, never hidden")
    ret = result["return"]
    check("C4-return-criterion",
          ret["status"] == "returned"
          and ret["artifact"]["sha256"] == _sha(ARTIFACT_TEXT)
          and ret["infinity_zero_prime"]["sha256"] == _sha(RETURN_TEXT)
          and ret["infinity_zero_prime"]["ref"].endswith("return.md@"
                                                         "sha256:%s"
                                                         % _sha(RETURN_TEXT)),
          "artifact + genuine ∞0′ — the return criterion (PRD §B3)")
    check("C6-child-nodes-and-arrangements",
          os.path.isdir(os.path.join(run_nodes, "Q"))
          and os.path.isdir(os.path.join(run_nodes, "PQ"))
          and os.path.isdir(os.path.join(run_nodes, "GPQ"))
          and all(step["arrangement"].startswith("cell-")
                  for step in result["steps"]),
          "gate-fails-to-lock → child node + address append + arrangement "
          "(PRD §B3)")
    store_root = os.path.join(work, "run", "store")
    block_store = descent.block.BlockStore(store_root)
    arr_store = descent.arrangement.ArrangementStore(
        os.path.join(store_root, "arrangements"))
    gpq_arr = arr_store.load("cell-%s" % _sha("GPQ")[:10], "1")
    validation = descent.arrangement.validate_arrangement(gpq_arr,
                                                          block_store)
    check("C6-arrangement-lawful-at-depth",
          validation["status"] == "ok",
          "the child's arrangement is a P4b arrangement: five desks, four "
          "blocks each, every instruction payload the desk's full-cell "
          "bundle (validated through P4b's own checks)")
    bundle_ok = descent.grammar.verify_bundle(
        block_store.read("cell-%s-g" % _sha("GPQ")[:10], "1")["files"][
            "instruction.md"].decode("utf-8"),
        cell_address=descent.grammar.seat_address("GPQ", "G"),
        seated_letter="G")
    check("C6-bundle-at-depth",
          bundle_ok["status"] == "ok",
          "the seated bundle at depth is the P4b grammar's full cell at "
          "the desk's own address, never a flat per-desk file (C5)")
    ledger_run = os.path.join(work, "run", "state", "gates.jsonl")
    from fractal_ledger import verify_ledger  # noqa: E402
    verified = verify_ledger(ledger_run)
    check("B0-chain-verifies",
          verified.count == 14,
          "the descent's ledger chain verifies from GENESIS through B0's "
          "own verifier (start 3 + 3 seeds + 5 world records at "
          "intermediate cells + 4 attested at the leaf − 1 = 14)")

    # -- C1: the manufactured field change → MOVING + stop-and-surface --------
    case_dir = os.path.join(FIX, "moving-stop")
    work = tmp()
    result = run_case(case_dir, os.path.join(work, "run"), MOVING_SCRIPT)
    check("C1-moving-dominates",
          result["status"] == "moving" and result["steps_taken"] == 2
          and result["visited"] == ["", "Q", "PQ"]
          and result["steps"][1]["axis_verdict"] == "MOVING",
          "a manufactured field change yields MOVING and a stop-and-"
          "surface — nothing descends past the drift (PRD §B3/§5.4)")
    run_nodes = os.path.join(work, "run", "nodes")
    check("C1-moving-drift-carried-honestly",
          _read_json(os.path.join(run_nodes, "PQ", "cell.node.json"))[
              "axis"]["field"] == DRIFTED_FIELD
          and not os.path.isdir(os.path.join(run_nodes, "GPQ")),
          "the drifted field is the world's truth — the engine never "
          "repairs a drift; the third level never opens")
    loaded = descent.LedgerLoader(os.path.join(
        work, "run", "state", "gates.jsonl")).load(write_index=False)
    stop_records = [r for r in loaded.records
                    if r.get("axis_verdict") == "MOVING"]
    check("C1-moving-logged",
          len(stop_records) == 1
          and stop_records[0]["address"] == "PQ"
          and stop_records[0]["gate"] == "x"
          and stop_records[0]["state"] == "held-pending",
          "the stop is logged as a record — surface and wait, never "
          "silent (§4.4, §8)")

    # -- C3: a V with no ∞0′ → refused ---------------------------------------
    case_dir = os.path.join(FIX, "v-without-return")
    work = tmp()
    result = run_case(case_dir, os.path.join(work, "run"), VOID_SCRIPT)
    check("C3-v-without-return-refused",
          result["status"] == "refused"
          and result["return"]["corruption"] == "V∅",
          "a V with no ∞0′ is refused (R6 — the done-when)")
    check("C3-guard-void-refused",
          result["guards"][-1]["status"] == "refused"
          and any(item["id"] == "GS-VOID" and item["verdict"] == "REFUSED"
                  for item in result["guards"][-1]["items"]),
          "the guard pass at the node flags V∅ — no artifact is accepted")
    loaded = descent.LedgerLoader(os.path.join(
        work, "run", "state", "gates.jsonl")).load(write_index=False)
    void_refusals = [r for r in loaded.records
                     if "refusal:v-without-infinity-zero-prime"
                     in r.get("payload_ref", "")]
    check("C3-refusal-recorded",
          len(void_refusals) == 1
          and void_refusals[0]["corruption"] == "V∅"
          and void_refusals[0]["gate"] == "b"
          and void_refusals[0]["turn_key"] == descent.turn_key(
              "Q", "b", "refusal:1", ""),
          "the refusal is recorded with B2's refusal keying (imported) — "
          "a silent refusal is a bug (§8)")
    check("C4-held-path",
          run_case(os.path.join(FIX, "lawful-3deep"),
                   os.path.join(tmp(), "run"),
                   {"steps": [{"gate": "z"}],
                    "leaf": {"walks": "yzab", "unattested_v": True,
                             "artifact_text": ARTIFACT_TEXT,
                             "return_text": RETURN_TEXT}})["status"]
          == "held",
          "an unattested V is held — the human's click is the only "
          "authenticity authority; the engine reports presence, never "
          "judges genuineness (commission §6)")

    # -- C5: the tentative node is never consumed -----------------------------
    case_dir = os.path.join(FIX, "tentative-unconsumed")
    work = tmp()
    result = run_case(case_dir, os.path.join(work, "run"), CONSUMED_SCRIPT)
    check("C5-tentative-never-consumed",
          result["status"] == "refused"
          and result["steps"][1]["status"] == "refused"
          and "tentative" in result["steps"][1]["reason"],
          "a downstream gate that consumed the tentative seed as evidence "
          "is refused — a tentative node is non-data (C5, T-R5-02)")
    check("C5-no-podium-write",
          not os.path.exists(os.path.join(work, "run", "nodes", "Q",
                                          "question.md"))
          and not os.path.exists(os.path.join(work, "run", "nodes", "PQ",
                                              "question.md"))
          and os.path.exists(os.path.join(work, "run", "nodes", "Q",
                                          "seed.md")),
          "the descent never writes the podium (question.md); the "
          "tentative seed lives in the node's own file (D7)")

    # -- the malformed signed paths fixture (C2, lens 3) ----------------------
    mal_dir = os.path.join(FIX, "malformed-signed-paths")
    engine = Descent(nodes_root=os.path.join(mal_dir, "nodes"),
                     ledger_path=os.path.join(mal_dir, "state",
                                              "gates.jsonl"),
                     store_root=os.path.join(mal_dir, "store"),
                     anchor="", clock=fixed_clock)
    read_p = engine.read_node("P")
    read_g = engine.read_node("G")
    check("C2-malformed-signed-path-nodes-refused",
          read_p["status"] == "refused" and read_g["status"] == "refused"
          and "-P-Q-P" in read_p["reason"] and "+-G" in read_g["reason"],
          "the fixture nodes carrying `-P-Q-P` and `+-G` are refused "
          "whole — the signed path field is validated, never tolerated")

    # -- C3: the guard pass at every depth, all five codes --------------------
    case_dir = os.path.join(FIX, "lawful-3deep")
    work = tmp()
    result = run_case(case_dir, os.path.join(work, "run"), LAWFUL_SCRIPT)
    check("C3-guard-at-every-depth",
          len(result["guards"]) == 4
          and all(len(g["items"]) == 5 for g in result["guards"])
          and all(any(i["id"] == "GS-VOID" for i in g["items"])
                  for g in result["guards"]),
          "the guard pass ran at every node and depth: L1 L2 L3 L4 V∅ "
          "(PRD §5.5)")
    check("C3-guard-leaf-clean-of-void",
          result["guards"][-1]["status"] == "flagged"
          and any(i["id"] == "GS-VOID" and i["verdict"] == "PASS"
                  for i in result["guards"][-1]["items"]),
          "the leaf's V carries its ∞0′ (GS-VOID PASS) while its seed "
          "keeps the honest L2 flag")
    scratch_nodes = os.path.join(work, "scratch", "nodes")
    scratch_ledger = os.path.join(work, "scratch", "state", "gates.jsonl")
    os.makedirs(os.path.join(scratch_nodes, "S"), exist_ok=True)
    scratch_record = {"axis": {"field": inherited, "delta": []},
                      "signed_path": "", "tentative": False}
    with open(os.path.join(scratch_nodes, "S", "cell.node.json"), "w",
              encoding="utf-8") as handle:
        handle.write(descent.canonical_json(scratch_record) + "\n")
    scratch = Descent(nodes_root=scratch_nodes, ledger_path=scratch_ledger,
                      store_root=os.path.join(work, "scratch", "store"),
                      anchor="", clock=fixed_clock)
    with descent.LedgerWriter(scratch_ledger, clock=fixed_clock) as writer:
        writer.append(_attested_record("S", "b", inherited,
                                       _gate_payload("b", "S")))
    guard = scratch.guard_pass("S")
    check("C3-guard-l1-skipped-arrow",
          any(i["id"] == "GS-L1" and i["verdict"] == "FLAG"
              for i in guard["items"]),
          "a gate with no predecessor record flags L1 — the arrow was "
          "skipped")
    claim_dir = os.path.join(work, "l3", "nodes")
    os.makedirs(os.path.join(claim_dir, "S"), exist_ok=True)
    bundle = descent.grammar.render_bundle("", "G")
    surface_start = bundle.index("⟦SURFACE v1⟧")
    surface_end = bundle.index("⟦END SURFACE⟧") + len("⟦END SURFACE⟧")
    claimed = (bundle[:surface_start]
               + bundle[surface_start:surface_end].replace(
                   "CORRUPTION: L1 L2 L3 L4 V∅",
                   "CORRUPTION: L1 L2 L3 L4 V∅ L5")
               + bundle[surface_end:])
    claim_record = {"axis": {"field": inherited, "delta": []},
                    "signed_path": "", "tentative": False,
                    "claimed_surface": claimed}
    with open(os.path.join(claim_dir, "S", "cell.node.json"), "w",
              encoding="utf-8") as handle:
        handle.write(descent.canonical_json(claim_record) + "\n")
    l3_engine = Descent(nodes_root=claim_dir,
                        ledger_path=os.path.join(work, "l3", "state",
                                                 "gates.jsonl"),
                        store_root=os.path.join(work, "l3", "store"),
                        anchor="", clock=fixed_clock)
    guard = l3_engine.guard_pass("S")
    check("C3-guard-l3-claimed-symbol",
          any(i["id"] == "GS-L3" and i["verdict"] == "FLAG"
              for i in guard["items"]),
          "a claimed surface declaring a sixth corruption code flags L3 — "
          "checked through P4a's own parser, imported")
    hollow_dir = os.path.join(work, "l4", "nodes")
    hollow_ledger = os.path.join(work, "l4", "state", "gates.jsonl")
    os.makedirs(os.path.join(hollow_dir, "S"), exist_ok=True)
    with open(os.path.join(hollow_dir, "S", "cell.node.json"), "w",
              encoding="utf-8") as handle:
        handle.write(descent.canonical_json(scratch_record) + "\n")
    hollow = Descent(nodes_root=hollow_dir, ledger_path=hollow_ledger,
                     store_root=os.path.join(work, "l4", "store"),
                     anchor="", clock=fixed_clock)
    with descent.LedgerWriter(hollow_ledger, clock=fixed_clock) as writer:
        writer.append(descent.make_record(
            address="S", gate="x", state="held-pending", mark="mechanical",
            payload_ref="⟦runtime slot — filled when this desk speaks⟧",
            axis={"field": inherited, "delta": []},
            axis_verdict="STASIS", corruption=None, tentative=True,
            turn_key=descent.turn_key("S", "x", "1", ""),
            block_version="", attestation_ref=None))
    guard = hollow.guard_pass("S")
    check("C3-guard-l4-hollow-payload",
          any(i["id"] == "GS-L4" and i["verdict"] == "FLAG"
              for i in guard["items"]),
          "an unfilled placeholder payload flags L4 — the operation "
          "without substance")
    bare_dir = os.path.join(work, "bare", "nodes")
    os.makedirs(os.path.join(bare_dir, "S"), exist_ok=True)
    with open(os.path.join(bare_dir, "S", "cell.node.json"), "w",
              encoding="utf-8") as handle:
        handle.write(descent.canonical_json(scratch_record) + "\n")
    bare = Descent(nodes_root=bare_dir,
                   ledger_path=os.path.join(work, "bare", "state",
                                            "gates.jsonl"),
                   store_root=os.path.join(work, "bare", "store"),
                   anchor="", clock=fixed_clock)
    guard = bare.guard_pass("S")
    check("C3-guard-unobservable-inconclusive",
          guard["status"] == "inconclusive"
          and any(i["id"] == "GS-L3" and i["verdict"] == "INCONCLUSIVE"
                  for i in guard["items"]),
          "a node whose evidence is unobservable reads INCONCLUSIVE, "
          "never clean (lens 6)")

    # -- C7: the five structural commitments ----------------------------------
    five_deep = run_case(
        os.path.join(FIX, "lawful-3deep"), os.path.join(tmp(), "run"),
        {"steps": [{"gate": "z"}, {"gate": "a"}, {"gate": "y"},
                   {"gate": "z"}, {"gate": "a"}],
         "leaf": {"walks": "yzab", "artifact_text": ARTIFACT_TEXT,
                  "return_text": RETURN_TEXT}})
    check("C7-1-no-depth-cap",
          "max_depth" not in source.lower()
          and "MAX_DEPTH" not in source
          and five_deep["status"] == "returned"
          and five_deep["steps_taken"] == 5,
          "no hard-coded maximum depth: a five-deep walk completes; the "
          "only bound is the caller's step budget")
    check("C7-2-alphabet-extensible",
          "[SGQPV]" not in source,
          "no five-letter literal anywhere — the alphabet is imported "
          "data (P4b's COURSE), so a jump marker can exist beside "
          "{S,G,Q,P,V}")
    saved_alphabet = descent.ALPHABET
    try:
        descent.ALPHABET = "SGQPVJ"
        check("C7-2-extended-alphabet-probe",
              validate_signed_path("−J")["status"] == "ok",
              "the signed-path letter class follows the alphabet data — "
              "an added marker letter validates with no code change")
    finally:
        descent.ALPHABET = saved_alphabet
    check("C7-3-loop-stops-on-resources",
          run_case(os.path.join(FIX, "lawful-3deep"),
                   os.path.join(tmp(), "run"), LAWFUL_SCRIPT,
                   budget=2)["status"] == "resource-exhausted",
          "with a step budget of 2 the walk stops at two steps — "
          "RESOURCES, never semantic completion")
    budget_run = run_case(os.path.join(FIX, "lawful-3deep"),
                          os.path.join(tmp(), "run"), LAWFUL_SCRIPT,
                          budget=2)
    check("C7-3-budget-leaves-nothing-below",
          budget_run["steps_taken"] == 2
          and len(budget_run["visited"]) == 3,
          "the budget stop never fabricates the remaining material")
    check("C7-4-nothing-narrows",
          all("len(address" not in line and "len(bundle" not in line
              and "len(child" not in line and "len(parent" not in line
              for line in lines)
          and len(descent.grammar.render_bundle(
              "GPQ", "G").encode("utf-8"))
          > len(descent.grammar.render_bundle(
              "", "G").encode("utf-8")),
          "no size comparison prunes a child — the deeper cell's bundle "
          "is LARGER and accepted: descent opens dimensions, it never "
          "narrows them (C7-4)")
    nonroot_work = tmp()
    nonroot_nodes = os.path.join(nonroot_work, "nodes")
    nonroot_ledger = os.path.join(nonroot_work, "state", "gates.jsonl")
    os.makedirs(os.path.join(nonroot_nodes, "Q"), exist_ok=True)
    with open(os.path.join(nonroot_nodes, "Q", "cell.node.json"), "w",
              encoding="utf-8") as handle:
        handle.write(descent.canonical_json(
            {"axis": {"field": {"mode": "inherited",
                                "anchor": PLANT_REF}, "delta": [PLANT_REF]},
             "signed_path": "−Q", "tentative": False}) + "\n")
    nonroot = Descent(nodes_root=nonroot_nodes, ledger_path=nonroot_ledger,
                      store_root=os.path.join(nonroot_work, "store"),
                      anchor="", block_version="", clock=fixed_clock,
                      world=FixtureWorld(nonroot_nodes, nonroot_ledger))
    with descent.LedgerWriter(nonroot_ledger, clock=fixed_clock) as writer:
        writer.append(descent.make_record(
            address="Q", gate="x", state="attested", mark="emergent",
            payload_ref=PLANT_REF,
            axis={"field": {"mode": "inherited", "anchor": PLANT_REF},
                  "delta": [PLANT_REF]},
            axis_verdict="STASIS", corruption=None, tentative=False,
            turn_key=descent.turn_key("Q", "x", "1", ""),
            block_version="", attestation_ref=_att_ref("Q", "x")))
        writer.append(_failing_record(
            "Q", "z", {"mode": "inherited", "anchor": PLANT_REF}))
    nonroot_result = nonroot.walk(
        "Q", {"steps": [{"gate": "z"}],
              "leaf": {"walks": "yzab", "artifact_text": ARTIFACT_TEXT,
                       "return_text": RETURN_TEXT}})
    check("C7-5-no-root-assumption",
          nonroot_result["status"] == "returned"
          and nonroot_result["visited"] == ["Q", "QQ"]
          and _read_json(os.path.join(
              nonroot_nodes, "QQ", "cell.node.json"))["signed_path"]
          == "−Q−Q"
          and path_between("Q", "GPQ") == "−P−G",
          "a descent STARTED AT a non-ε cell walks identically — the "
          "address is a parameter, ε a coordinate, never a privileged "
          "root (Appendix D.2: no root, no leaf)")
    walk_def = next(n for n in tree.body
                    if isinstance(n, ast.ClassDef)
                    and n.name == "Descent")
    walk_fn = next(n for n in walk_def.body
                   if isinstance(n, ast.FunctionDef) and n.name == "walk")
    allowed = ("resource-exhausted", "no-trigger", "moving", "refused",
               "inconclusive", "resource_budget")
    parent_map = {}
    for parent_node in ast.walk(walk_fn):
        for child in ast.iter_child_nodes(parent_node):
            parent_map[child] = parent_node
    breaks_ok = True
    for node in ast.walk(walk_fn):
        if not isinstance(node, ast.Break):
            continue
        current = parent_map.get(node)
        while current is not None and not isinstance(current, ast.If):
            current = parent_map.get(current)
        if current is None:
            breaks_ok = False
            break
        segment = ast.get_source_segment(source, current.test) or ""
        if not any(token in segment for token in allowed):
            breaks_ok = False
            break
    check("C7-3-loop-breaks-never-semantic",
          breaks_ok,
          "every break in the walk loop is guarded by resources or "
          "mandated stops — the return criterion is observed after the "
          "loop, never a break condition")

    # -- the six verifier lenses ----------------------------------------------
    check("lens-1-criterion-as-written",
          "byte-identical axis.field from root to leaf"
          in " ".join(source.split())
          and "a manufactured field change yields `MOVING`"
          in " ".join(source.split())
          and "a V with no ∞0′ is refused" in " ".join(source.split()),
          "the criteria are carried verbatim where they are measured")
    check("lens-3-absence-never-valid",
          engine.read_node("V")["status"] == "absent",
          "a missing node reads absent — never valid")
    empty_node_dir = os.path.join(work, "empty", "nodes")
    os.makedirs(os.path.join(empty_node_dir, "V"), exist_ok=True)
    with open(os.path.join(empty_node_dir, "V", "cell.node.json"), "w",
              encoding="utf-8") as handle:
        handle.write("")
    empty_engine = Descent(nodes_root=empty_node_dir,
                           ledger_path=os.path.join(work, "empty",
                                                    "state", "gates.jsonl"),
                           store_root=os.path.join(work, "empty", "store"),
                           anchor="", clock=fixed_clock)
    check("lens-3-empty-never-valid",
          empty_engine.read_node("V")["status"] == "absent"
          and empty_engine.read_node("V")["sha256"] == EMPTY_SHA
          and EMPTY_SHA != _sha(RETURN_TEXT),
          "an empty node record reads absent — sha256 of empty is "
          "e3b0c44298fc…, never a valid ref")
    check("lens-4-probe-through-every-field",
          PLANT_QUESTION.find(PROBE) != -1
          and ARTIFACT_TEXT.find(PROBE) != -1
          and RETURN_TEXT.strip() == PROBE
          and ret["infinity_zero_prime"]["sha256"] == _sha(PROBE + "\n")
          and "\\u" not in descent.canonical_json(
              {"probe": PROBE}),
          "`∞0′ → ‖` rides the plant, the artifact and the ∞0′ end to "
          "end; every JSON is UTF-8 passthrough, no escapes, no "
          "text-mode byte seeks")
    expected_nodes = os.path.join(case_dir, "expected", "nodes")
    expected_ledger = os.path.join(case_dir, "expected", "gates.jsonl")
    run_nodes2 = os.path.join(work, "run", "nodes")
    ledger2 = os.path.join(work, "run", "state", "gates.jsonl")
    same, files_a, files_b = _compare_tree(expected_nodes, run_nodes2)
    with open(expected_ledger, "rb") as a, open(ledger2, "rb") as b:
        ledger_same = a.read() == b.read()
    check("lens-2-invariant-rebuild-exact",
          same and ledger_same,
          "the rebuilt tree and ledger equal the byte-pinned expected "
          "fixture — one invariant, end to end")
    out_dir = os.path.join(work, "cold")
    probe = subprocess.run(
        [sys.executable, "-c",
         "import sys; sys.path.insert(0, %r); import selftest; "
         "selftest.rebuild_probe(%r, %r)" % (HERE, case_dir, out_dir)],
        cwd=HERE, capture_output=True, text=True,
        env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
    check("lens-5-cold-restart-second-process",
          probe.returncode == 0,
          "a NEW process rebuilt the node tree from disk alone: %s"
          % (probe.stderr.strip() or "exit 0"))
    same2, _, _ = _compare_tree(expected_nodes,
                                os.path.join(out_dir, "nodes"))
    with open(os.path.join(out_dir, "state", "gates.jsonl"), "rb") as a:
        ledger_cold = a.read()
    with open(expected_ledger, "rb") as b:
        ledger_same2 = ledger_cold == b.read()
    check("lens-5-second-process-bytes",
          same2 and ledger_same2,
          "the second process's bytes equal the pins — the tree rebuilds "
          "from disk alone")
    blind_work = tmp()
    blind_nodes = os.path.join(blind_work, "missing", "nodes")
    blind_ledger = os.path.join(blind_work, "missing", "state",
                                "gates.jsonl")
    os.makedirs(blind_nodes, exist_ok=True)
    blind = Descent(nodes_root=blind_nodes, ledger_path=blind_ledger,
                    store_root=os.path.join(blind_work, "missing", "store"),
                    anchor="", clock=fixed_clock)
    with descent.LedgerWriter(blind_ledger, clock=fixed_clock) as writer:
        writer.append(_failing_record("G", "z", inherited))
    report = blind.descend("G", "z")
    check("lens-6-blind-tool-inconclusive",
          report["status"] == "inconclusive",
          "an unobservable parent reads INCONCLUSIVE, never clean")
    blind_dir = os.path.join(blind_work, "no-world")
    shutil.copytree(os.path.join(FIX, "lawful-3deep"), blind_dir,
                    ignore=shutil.ignore_patterns(
                        "expected", "*.lock", "spec.json", "README*"))
    no_world = Descent(nodes_root=os.path.join(blind_dir, "nodes"),
                       ledger_path=os.path.join(blind_dir, "state",
                                                "gates.jsonl"),
                       store_root=os.path.join(blind_dir, "store"),
                       anchor="", clock=fixed_clock, world=None)
    check("lens-6-no-world-never-fabricates",
          no_world.walk("", LAWFUL_SCRIPT)["status"] == "inconclusive",
          "without the fixture world the engine fabricates nothing — "
          "the walk ends INCONCLUSIVE, never clean (H-B3-1)")

    # -- K-loyalties -----------------------------------------------------------
    check("K-imported-never-reauthored",
          descent.turn_key("Q", "x", "1", "") == hashlib.sha256(
              "Qx1".encode("utf-8")).hexdigest()
          and descent.CORRUPTION_CODES == ("L1", "L2", "L3", "L4", "V∅"),
          "the turn_key is B2's (imported) and the corruption codes are "
          "exactly the sealed five — no sixth code")
    check("K-surface-contract-pinned",
          surface_contract.CONTRACT_VERSION == 1
          and surface_contract.DESCENT_SURFACE["version"] == 1
          and surface_contract.SURFACE_CONTRACT["version"] == 1,
          "the descent surface is declared against the §3.6 contract — "
          "P4a/P4b read by path, sha-pinned, one version")
    docstring = ast.get_docstring(tree, clean=False) or ""
    doc_start = source.index(docstring) if docstring else 0
    doc_end = doc_start + len(docstring)
    jumps_ok = True
    position = 0
    while True:
        hit = source.lower().find("jump", position)
        if hit == -1:
            break
        line_no = source[:hit].count("\n")
        in_doc = doc_start <= hit < doc_end
        is_comment = lines[line_no].lstrip().startswith("#")
        if not (in_doc or is_comment):
            jumps_ok = False
            break
        position = hit + 1
    check("H-B3-4-jump-planned-never-implemented",
          jumps_ok,
          "the word 'jump' appears only in the module docstring — the "
          "quantum jump is a structural constraint, never a feature "
          "(H-B3-4)")
    check("K-podium-untouched",
          not any(("question.md" in line and "open(" in line
                   and "write" in line)
                  for line in lines),
          "no write path to the podium exists in the descent module "
          "(PRD §2.1, T-R3-02)")


def _make_writable(root):
    """Unfreeze a fixture tree for regeneration (the block store freezes
    0444/0555 — regeneration is the authoring path, never an edit)."""
    for dirpath, dirnames, filenames in os.walk(root):
        for name in filenames:
            try:
                os.chmod(os.path.join(dirpath, name), 0o644)
            except OSError:
                pass
        for name in dirnames:
            try:
                os.chmod(os.path.join(dirpath, name), 0o755)
            except OSError:
                pass


def build_static_fixtures(fixtures_dir=None):
    """Generate the static fixtures under ./authored/fixtures — the start
    states, the specs and the byte-pinned expected outcomes.  Run once at
    authoring time; the suite then REBUILDS against these pins."""
    fixtures_dir = fixtures_dir if fixtures_dir is not None else FIX
    os.makedirs(fixtures_dir, exist_ok=True)
    for name in os.listdir(fixtures_dir):
        _make_writable(os.path.join(fixtures_dir, name))
        shutil.rmtree(os.path.join(fixtures_dir, name))
    cases = {
        "lawful-3deep": LAWFUL_SCRIPT,
        "moving-stop": MOVING_SCRIPT,
        "v-without-return": VOID_SCRIPT,
        "tentative-unconsumed": CONSUMED_SCRIPT,
    }
    for name, script in cases.items():
        case_dir = os.path.join(fixtures_dir, name)
        os.makedirs(case_dir)
        start = build_start_case(case_dir)
        with open(os.path.join(case_dir, "spec.json"), "w",
                  encoding="utf-8") as handle:
            handle.write(descent.canonical_json(script) + "\n")
        with open(os.path.join(case_dir, "README.md"), "w",
                  encoding="utf-8") as handle:
            handle.write(README_TEXT[name])
        work = tmp()
        out_dir = os.path.join(work, "run")
        run_case(case_dir, out_dir, script)
        expected = os.path.join(case_dir, "expected")
        os.makedirs(expected)
        shutil.copytree(os.path.join(out_dir, "nodes"),
                        os.path.join(expected, "nodes"))
        shutil.copyfile(os.path.join(out_dir, "state", "gates.jsonl"),
                        os.path.join(expected, "gates.jsonl"))
        for path in (os.path.join(case_dir, "state", "gates.jsonl.lock"),
                     os.path.join(out_dir, "state", "gates.jsonl.lock")):
            if os.path.exists(path):
                os.remove(path)
    mal_dir = os.path.join(fixtures_dir, "malformed-signed-paths")
    os.makedirs(os.path.join(mal_dir, "nodes", "P"))
    os.makedirs(os.path.join(mal_dir, "nodes", "G"))
    for letter, bad_path in (("P", "-P-Q-P"), ("G", "+-G")):
        record = {"axis": {"field": {"mode": "inherited",
                                     "anchor": PLANT_REF}, "delta": []},
                  "signed_path": bad_path, "tentative": False}
        with open(os.path.join(mal_dir, "nodes", letter,
                               "cell.node.json"), "w",
                  encoding="utf-8") as handle:
            handle.write(descent.canonical_json(record) + "\n")
    with open(os.path.join(mal_dir, "README.md"), "w",
              encoding="utf-8") as handle:
        handle.write(README_TEXT["malformed-signed-paths"])


README_TEXT = {
    "lawful-3deep": (
        "# fixture — lawful-3deep (a 3-deep descent)\n\n"
        "Start state: the root cell `_` with a human-planted question "
        "(fixture fiction) attested at gate x, gate y attested, gate z "
        "PROPOSED and failing to lock — the descent trigger.\n\n"
        "Prediction: the walk descends ε → Q → PQ → GPQ with "
        "byte-identical `axis.field` from root to leaf; the leaf's V is "
        "attested and carries artifact + ∞0′ — the return criterion. "
        "`expected/` pins the byte-exact node tree and ledger.\n"),
    "moving-stop": (
        "# fixture — moving-stop (a manufactured field change)\n\n"
        "Start state as lawful-3deep; step 2 declares a drifted child "
        "field (a manufactured change in the axis anchor).\n\n"
        "Prediction: the descent computes MOVING at the drift, stops and "
        "surfaces — the child `PQ` exists with the drifted field as the "
        "world's truth, the stop is logged, and nothing descends "
        "further.\n"),
    "v-without-return": (
        "# fixture — v-without-return (a V with no ∞0′)\n\n"
        "Start state as lawful-3deep; the leaf's V is attested but the "
        "∞0′ is absent.\n\n"
        "Prediction: refused — the guard flags V∅, the refusal is "
        "recorded, no artifact is accepted (seal line 8, R6).\n"),
    "tentative-unconsumed": (
        "# fixture — tentative-unconsumed (a tentative node consumed)\n\n"
        "Start state as lawful-3deep; step 2 declares a downstream gate "
        "that consumed the tentative seed as evidence.\n\n"
        "Prediction: refused — a tentative node is non-data; no "
        "heuristic promotes it and no downstream gate consumes it "
        "(C5, T-R5-02). The descent never writes the podium.\n"),
    "malformed-signed-paths": (
        "# fixture — malformed-signed-paths (`-P-Q-P`, `+-G`)\n\n"
        "Two node records whose signed-path field uses the ASCII hyphen "
        "instead of the U+2212 descent operator.\n\n"
        "Prediction: rejected — the validator refuses both, and the "
        "nodes read refused, never valid (commission §7, K2).\n"),
}


def main():
    print("b3 selftest — a hypothesis, never a result (predictions only)")
    try:
        suite()
    except AssertionError as exc:
        print("FAILED:", exc)
        return 1
    if _failures:
        print("FAILED %d check(s)" % len(_failures))
        return 1
    print("all %d checks predicted — the verifier writes the only record "
          "that counts" % _checks)
    return 0


if __name__ == "__main__":
    sys.exit(main())
