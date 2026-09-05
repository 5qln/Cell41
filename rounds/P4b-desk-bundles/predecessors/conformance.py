#!/usr/bin/env python3
"""conformance — the operational-fractal checks, mechanical (P4a).

Three source families, kept visibly separate and separately numbered so
nothing drifts the source's own numbering (D14's jacket):

  * AD-SYN/SEM/DRF 1..5 — Appendix D §D.12, verbatim (15 items);
  * CX-SYN/SEM/DRF 1..6 — Codex §3.5, verbatim (18 items);
  * R1..R13 — Codex §3.4, the source's own numbering, never renumbered
    (13 items);
  * DC-DECODE / DC-COMPILE — his D12 pair (derived, from D12's own words
    plus Codex §3.2/§3.3);
  * DC-AUTH-1 / DC-AUTH-2 — this artifact's two K3 checks (derived):
    permanent INCONCLUSIVE — whether an α is THE essence, and whether an
    ∞0′ question is more alive than the X it came from, is the human's
    click.  A machine that reports resonance has failed the measure.

Every item carries its source citation verbatim, its scope (static |
cell | step | session), its verdict (PASS | FAIL | INCONCLUSIVE) and its
evidence.  A check that cannot be decided reads INCONCLUSIVE, never
clean.  Verdicts are deterministic functions of the context — no LLM, no
network, stdlib only.

EQUATION_FORMS enumerates the accepted byte forms of the five equations,
each with source + sha256 (commission P4a §3.3, executed).  The checks
compare BYTES against the table and NEVER normalise: folding ⋂→∩, ′→'
or collapsing whitespace would itself be renaming an L1 symbol, which is
exactly what AD-SYN-2's check forbids.  A form outside the table is a
paraphrase → FAIL, and the FAIL names the codepoint that differs.

Import-time self-consistency (commission §3.7 lesson 5): the set of item
ids the evaluator can decide EQUALS the set of ids in CHECKS — asserted
at import, cheap and permanent, so the table and the evaluation can
never drift apart.
"""

from __future__ import annotations

import ast
import hashlib
import os
import re
import sys

# B0's module is imported, never copied (R01 attested and closed).
_LEDGER_DIR = os.environ.get(
    "FRACTAL_LEDGER_DIR", "/home/deploy/the-cell/ledger")
if _LEDGER_DIR not in sys.path:
    sys.path.insert(0, _LEDGER_DIR)

from fractal_ledger import LedgerLoader  # noqa: E402
from surface import (  # noqa: E402
    COMPILED_OUTPUTS,
    CONTEXT_IN,
    DECODING_OPS,
    LENSES,
    OUTPUT_SYMBOLS,
    PHASES,
    SYMBOL_VOCABULARY,
)
from walker import COURSE, DESK_GATES  # noqa: E402

__all__ = [
    "CHECKS",
    "evaluate",
    "aggregate",
    "EQUATION_FORMS",
    "CORRUPTION_CODES",
    "CORRUPTION_FAILURES",
    "SYMBOL_TABLE",
    "SYMBOL_ALIASES",
    "build_live_context",
    "CHECK_ORDER",
]

# ---------------------------------------------------------------------------
# The enumerated equation byte forms (commission P4a §3.3, executed — never
# re-derived, never normalised).  Each form carries its source, its section
# line(s) in the held files, and the sha256 of the exact string.
# ---------------------------------------------------------------------------

_CODEX = "5qln-codex.txt"
_APPD = "5qln-codex-appendix-D-the-fractal.txt"

EQUATION_FORMS = {
    "S": [
        {
            "form": "S = ∞0 → ?",
            "sha256": "de0b90963d6110bf2092013401576c5ccb71751a8a7c9e3ab900a481c1dbfb1d",
            "source": "Codex §1.3 L14 · Codex §3.1 L257 · AppD D.1 L24",
            "locations": [(_CODEX, 14), (_CODEX, 257), (_APPD, 24)],
            "label": None,
        },
        {
            "form": "S=∞0→?",
            "sha256": "4fb171bab276a63cf5dd04a42a92ef6ceef41fa9b7ae1f71c0b74f5e14b13250",
            "source": "AppD D.14 L205 (prefixed CELL:, suffixed (c) for centre)",
            "locations": [(_APPD, 205)],
            "label": None,
        },
    ],
    "G": [
        {
            "form": "G = α ≡ {α'}",
            "sha256": "c2b0ed6eb2f0b8ce737b4656929e0b4bea1903d2071eca13d7961a99744a5c7e",
            "source": "Codex §1.3 L15 · Codex §3.1 L258",
            "locations": [(_CODEX, 15), (_CODEX, 258)],
            "label": None,
        },
        {
            "form": "G=α≡{α'}",
            "sha256": "98950e70a7de42c8d8b2eb2ecc0fc4b2e93833124d075a11931b570619490656",
            "source": "AppD D.14 L205",
            "locations": [(_APPD, 205)],
            "label": None,
        },
    ],
    "Q": [
        {
            "form": "Q = φ ⋂ Ω",
            "sha256": "cd20931fc7cd729a4de3779ccf63e63e627871a643cfc7c955961f9694a49bee",
            "source": "Codex §1.3 L16 · Codex §3.1 L259",
            "locations": [(_CODEX, 16), (_CODEX, 259)],
            "label": None,
        },
        {
            "form": "Q=φ⋂Ω",
            "sha256": "6e0609332484796cd5d584f2966511d94c2a459f6098a37b6b1313393f9a82f0",
            "source": "AppD D.14 L205",
            "locations": [(_APPD, 205)],
            "label": None,
        },
    ],
    "P": [
        {
            "form": "P = δE/δV → ∇",
            "sha256": "8175a49a811b0fb0402da736e404c341662fc970dbd327a6439efbb670f0ef49",
            "source": "Codex §1.3 L17 · Codex §3.1 L260",
            "locations": [(_CODEX, 17), (_CODEX, 260)],
            "label": None,
        },
        {
            "form": "P=δE/δV→∇",
            "sha256": "ae9433ec8ed4a190f7d7483c795762005217c0181c5bb7ba99f1977593261ee0",
            "source": "AppD D.14 L205",
            "locations": [(_APPD, 205)],
            "label": None,
        },
    ],
    "V": [
        {
            "form": "V = (L ∩ G → B'') → ∞0'",
            "sha256": "7c8305fa45c203b50ac5ceb91cb85ac80722b8d0fb2eaed01988a1764eb65177",
            "source": "Codex §3.1 L261 (the Constitutional Block); also Codex §1.3 L19",
            "locations": [(_CODEX, 261), (_CODEX, 19)],
            "label": "constitutional form",
            # sha256 of the extracted §1.3 L19 line, label included — the
            # commission's executed table; the label itself is never part
            # of the form string.
            "source_line_sha256": [
                "6a89f27c9f35c50f55f9cab7ecd505411aef5c923465fc203ac023b8b1b1c6dc"],
        },
        {
            "form": "V=(L⋂G→B'')→∞0′",
            "sha256": "05101fd680e1d139487e3450ff751e4ab384dd0760547e2aafb9cc4cc8c5314a",
            "source": "AppD D.14 L205 (the Block, extended)",
            "locations": [(_APPD, 205)],
            "label": None,
        },
        {
            "form": "V = L ⋂ G → ∞",
            "sha256": "528f868c2eb51024d49f261a68024f04a6f388ed057e89c65463e6f7686bad56",
            "source": "Codex §1.3 L18 — the public form, a distinct compression "
                      "the Codex itself labels",
            "locations": [(_CODEX, 18)],
            "label": "public form",
            # sha256 of the extracted §1.3 L18 line, label included — the
            # commission's executed table; the label itself is never part
            # of the form string.
            "source_line_sha256": [
                "9b3f8a068966d191f7ac4151dc0a565fbd88248db2e2777ecc6f1dd734b4c9b9"],
        },
    ],
}

# The five corruption codes — exactly, frozen (Codex §2.8 / §3.1 / §3.5;
# Appendix D.12).  No sixth code exists anywhere in the artifact; the
# static scan below proves that from the artifact's own source.
CORRUPTION_CODES = frozenset(("L1", "L2", "L3", "L4", "V\u2205"))

# Each code's decoding failure, verbatim from Codex §2.8 (R9's data).
CORRUPTION_FAILURES = {
    "L1": ("Closing", "→ was skipped. An answer was inserted where "
           "emergence should occur. ∞0 was not held"),
    "L2": ("Generating", "X was generated from K instead of received "
           "from ∞0. The spark was manufactured"),
    "L3": ("Claiming", "Someone claims to decode ∞0 directly. ∞0 reveals "
           "itself — it cannot be accessed"),
    "L4": ("Performing", "The decoding is performed (symbols used, "
           "language spoken) but the operation is empty. Form without "
           "substance"),
    "V\u2205": ("Incomplete", "B'' was formed but ∞0' was not. The return "
                "question is missing. The cycle has no continuity"),
}

# The symbol table with its §1.9 source names (CX-DRF-1: no symbol
# renamed without source name present).  Data, verbatim meanings.
SYMBOL_TABLE = {
    "H": ("Human", "The human participant"),
    "∞0": ("Infinite Zero", "The state of not-knowing; no question has "
           "formed, the space is open"),
    "A": ("Artificial", "The AI participant (in the covenant context)"),
    "K": ("Known", "The domain of existing knowledge, patterns, and "
          "recombination"),
    "|": ("Membrane", "The boundary separating ∞0 from K"),
    "S": ("Start", "∞0 → ?"),
    "G": ("Growth", "α ≡ {α'}"),
    "Q": ("Quality", "φ ⋂ Ω"),
    "P": ("Power", "δE/δV → ∇"),
    "V": ("Value", "(L ∩ G → B'') → ∞0'"),
    "?": ("Authentic Question", "The first inquiry that arrives from the "
          "open space — unexpected, not manufactured"),
    "X": ("Validated Spark", "The confirmed output of S — a genuine "
          "question, not a manufactured one"),
    "α": ("Core Essence", "The irreducible pattern within X; remove it "
          "and X collapses"),
    "{α'}": ("Self-Similar Expressions", "The different forms α takes "
             "across scales, domains, and contexts"),
    "Y": ("Validated Pattern", "The confirmed output of G — α has been "
          "found, tested, and echoed"),
    "φ": ("Self-Nature", "What the inquirer directly perceives about Y — "
          "not theory, not data"),
    "Ω": ("Universal Potential", "What the larger context makes possible "
          "beyond the individual"),
    "Z": ("Resonant Key", "The confirmed output of Q — the moment φ and Ω "
          "meet and something locks"),
    "δE/δV": ("Energy/Value Ratio", "Where effort is wasted (high energy, "
              "low value) vs. where movement is effortless (low energy, "
              "high value)"),
    "δE": ("Energy (differential)", "Where energy is being invested, "
           "spent, or lost"),
    "δV": ("Value (differential)", "Where value is appearing, growing, "
           "or blocked"),
    "∇": ("Natural Gradient", "The path of least resistance leading "
          "toward α (essence) — the direction already present in the "
          "situation"),
    "L": ("Local Actualization", "The specific, tangible, immediate "
          "result of a cycle"),
    "B": ("Benefit", "The decoded output: fulfillment of the inquiry's "
          "aim + what propagates beyond it"),
    "B''": ("Fractal Seed", "The actual artifact produced — containing "
            "the cycle holographically, carrying α"),
    "∞0'": ("Enriched Return", "Return to Infinite Zero carrying the "
            "question the cycle opens. ∞0' is not accumulated knowledge "
            "— it is ∞0 deepened by the question"),
    "→ ∞": ("Creates", "Infinite Expansion. Public form of the V-phase "
            "output"),
    "∞": ("→ ∞", "Infinite Expansion — public form of the V-phase output"),
    "→": ("Context-dependent", "Emergence (in S), Reveals (in P), Creates "
          "(in V), Leads to (general)"),
    "≡": ("Identity Preservation", "α remains identical across all "
          "expressions"),
    "⋂": ("Natural Intersection", "Where two elements meet without "
          "forcing"),
    "×": ("In relation with", "Connects the covenant to the cycle in the "
          "master equation"),
    ":=": ("Is defined as", "Definitional operator (holographic law)"),
    "∈": ("Belongs to", "Set membership"),
    "No...without...": ("Constitutional completion rule",
                        "Enforcement operator"),
    "φ⋂Ω": ("Natural Intersection (compact)", "§3.3's compact reading of "
            "φ ⋂ Ω"),
    "∅": ("Empty context", "S decodes with ∅ (or ∞0' from prior cycle)"),
}

# Spelling aliases: the Appendix's U+2032 prime and U+22C2 glyphs are the
# same L1 symbols wearing their Appendix-D face — enumerated here, never
# folded (folding would be renaming an L1 symbol).
SYMBOL_ALIASES = {
    "∞0′": "∞0'",
    "B″": "B''",
    "∩": "⋂",
}

# ---------------------------------------------------------------------------
# The check table.  id -> {source, citation (verbatim), scope, derived}.
# The order is the emission order; the citation text matches the held
# source bytes.
# ---------------------------------------------------------------------------

CHECK_ORDER = (
    # Appendix D §D.12 — Syntax (5)
    "AD-SYN-1", "AD-SYN-2", "AD-SYN-3", "AD-SYN-4", "AD-SYN-5",
    # Appendix D §D.12 — Semantic (5)
    "AD-SEM-1", "AD-SEM-2", "AD-SEM-3", "AD-SEM-4", "AD-SEM-5",
    # Appendix D §D.12 — Drift (5)
    "AD-DRF-1", "AD-DRF-2", "AD-DRF-3", "AD-DRF-4", "AD-DRF-5",
    # Codex §3.5 — Syntax (6)
    "CX-SYN-1", "CX-SYN-2", "CX-SYN-3", "CX-SYN-4", "CX-SYN-5",
    "CX-SYN-6",
    # Codex §3.5 — Semantic (6)
    "CX-SEM-1", "CX-SEM-2", "CX-SEM-3", "CX-SEM-4", "CX-SEM-5",
    "CX-SEM-6",
    # Codex §3.5 — Drift (6)
    "CX-DRF-1", "CX-DRF-2", "CX-DRF-3", "CX-DRF-4", "CX-DRF-5",
    "CX-DRF-6",
    # Codex §3.4 — the thirteen decoder rules, the source's own numbering
    "R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9", "R10", "R11",
    "R12", "R13",
    # The D12 pair + the two K3 authenticity checks (derived — divergence
    # log in the phase card)
    "DC-DECODE", "DC-COMPILE", "DC-AUTH-1", "DC-AUTH-2",
)

CHECKS = {
    # ---------------- Appendix D §D.12, Syntax ----------------
    "AD-SYN-1": {"source": "Appendix D §D.12 (syntax)",
                 "citation": "4+1 invariant holds at every observed cell",
                 "scope": "cell", "derived": False},
    "AD-SYN-2": {"source": "Appendix D §D.12 (syntax)",
                 "citation": "The five equations appear verbatim at every "
                             "cell (S = ∞0 → ? … V = (L⋂G→B'') → ∞0′)",
                 "scope": "cell", "derived": False},
    "AD-SYN-3": {"source": "Appendix D §D.12 (syntax)",
                 "citation": "No L1 symbol added, renamed, or paraphrased",
                 "scope": "cell", "derived": False},
    "AD-SYN-4": {"source": "Appendix D §D.12 (syntax)",
                 "citation": "+/− used only as a navigational operator; "
                             "never inside a phase equation",
                 "scope": "cell", "derived": False},
    "AD-SYN-5": {"source": "Appendix D §D.12 (syntax)",
                 "citation": "No corruption code beyond L1 L2 L3 L4 V∅",
                 "scope": "cell", "derived": False},
    "AD-SEM-1": {"source": "Appendix D §D.12 (semantic)",
                 "citation": "Context flows father → daughter (k = frames "
                             "to climb)",
                 "scope": "step", "derived": False},
    "AD-SEM-2": {"source": "Appendix D §D.12 (semantic)",
                 "citation": "The sign is relative, not absolute — it "
                             "adapts to the current vantage",
                 "scope": "step", "derived": False},
    "AD-SEM-3": {"source": "Appendix D §D.12 (semantic)",
                 "citation": "∞0′ ≡ ∞0 preserves the Completion Rule "
                             "across cells",
                 "scope": "step", "derived": False},
    "AD-SEM-4": {"source": "Appendix D §D.12 (semantic)",
                 "citation": "The true start carries no sign; the sign "
                             "appears only between strangers",
                 "scope": "step", "derived": False},
    "AD-SEM-5": {"source": "Appendix D §D.12 (semantic)",
                 "citation": "A shared question is one ∞0-field, not one "
                             "node",
                 "scope": "cell", "derived": False},
    "AD-DRF-1": {"source": "Appendix D §D.12 (drift)",
                 "citation": "25 is the first in-zoom of a cell, never a "
                             "cap — scale is self-proven by the law",
                 "scope": "static", "derived": False},
    "AD-DRF-2": {"source": "Appendix D §D.12 (drift)",
                 "citation": "The zoom-out inverse is a derived reading, "
                             "marked as such (§1.10 source-authoritative)",
                 "scope": "static", "derived": False},
    "AD-DRF-3": {"source": "Appendix D §D.12 (drift)",
                 "citation": "No decoding step omitted or reordered",
                 "scope": "session", "derived": False},
    "AD-DRF-4": {"source": "Appendix D §D.12 (drift)",
                 "citation": "No sixth corruption code",
                 "scope": "static", "derived": False},
    "AD-DRF-5": {"source": "Appendix D §D.12 (drift)",
                 "citation": "Lens questions still target the parent "
                             "output",
                 "scope": "cell", "derived": False},
    # ---------------- Codex §3.5, Syntax ----------------
    "CX-SYN-1": {"source": "Codex §3.5 (syntax)",
                 "citation": "Every symbol resolves to the symbol table "
                             "(§1.9 / §3.2)",
                 "scope": "cell", "derived": False},
    "CX-SYN-2": {"source": "Codex §3.5 (syntax)",
                 "citation": "Every phase carries its exact equation",
                 "scope": "cell", "derived": False},
    "CX-SYN-3": {"source": "Codex §3.5 (syntax)",
                 "citation": "Every decoding operation follows D1 "
                             "symbol-by-symbol",
                 "scope": "cell", "derived": False},
    "CX-SYN-4": {"source": "Codex §3.5 (syntax)",
                 "citation": "All five phases present, all 25 sub-phases "
                             "available",
                 "scope": "static", "derived": False},
    "CX-SYN-5": {"source": "Codex §3.5 (syntax)",
                 "citation": "Five corruption codes exactly",
                 "scope": "static", "derived": False},
    "CX-SYN-6": {"source": "Codex §3.5 (syntax)",
                 "citation": "No V without ∞0' enforceable",
                 "scope": "step", "derived": False},
    "CX-SEM-1": {"source": "Codex §3.5 (semantic)",
                 "citation": "Each phase's decoding receives the correct "
                             "adaptive context",
                 "scope": "cell", "derived": False},
    "CX-SEM-2": {"source": "Codex §3.5 (semantic)",
                 "citation": "Context chain is unbroken: S→G→Q→P→V, each "
                             "receiving prior outputs",
                 "scope": "step", "derived": False},
    "CX-SEM-3": {"source": "Codex §3.5 (semantic)",
                 "citation": "B, B'', ∞0' are three distinct things with "
                             "distinct decoding steps",
                 "scope": "cell", "derived": False},
    "CX-SEM-4": {"source": "Codex §3.5 (semantic)",
                 "citation": "Sub-phase lenses refine the parent "
                             "equation's decoding (not replace)",
                 "scope": "cell", "derived": False},
    "CX-SEM-5": {"source": "Codex §3.5 (semantic)",
                 "citation": "Crystallization reads the formation trail "
                             "(not generated from nothing)",
                 "scope": "step", "derived": False},
    "CX-SEM-6": {"source": "Codex §3.5 (semantic)",
                 "citation": "∞0' carries a question",
                 "scope": "step", "derived": False},
    "CX-DRF-1": {"source": "Codex §3.5 (drift)",
                 "citation": "No symbol renamed without source name "
                             "present",
                 "scope": "static", "derived": False},
    "CX-DRF-2": {"source": "Codex §3.5 (drift)",
                 "citation": "No equation paraphrased — symbolic form is "
                             "exact",
                 "scope": "static", "derived": False},
    "CX-DRF-3": {"source": "Codex §3.5 (drift)",
                 "citation": "No decoding step omitted or reordered",
                 "scope": "session", "derived": False},
    "CX-DRF-4": {"source": "Codex §3.5 (drift)",
                 "citation": "No corruption code added beyond five",
                 "scope": "static", "derived": False},
    "CX-DRF-5": {"source": "Codex §3.5 (drift)",
                 "citation": "Adaptive context chain preserved",
                 "scope": "session", "derived": False},
    "CX-DRF-6": {"source": "Codex §3.5 (drift)",
                 "citation": "Lens questions target parent output",
                 "scope": "cell", "derived": False},
    # ---------------- Codex §3.4, R1-R13 ----------------
    "R1": {"source": "Codex §3.4 R1",
           "citation": "Each phase decodes one equation to form one "
                       "output",
           "scope": "step", "derived": False},
    "R2": {"source": "Codex §3.4 R2",
           "citation": "B = decoded output (fulfillment + propagation), "
                       "B'' = artifact, ∞0' = return with question",
           "scope": "step", "derived": False},
    "R3": {"source": "Codex §3.4 R3",
           "citation": "Sub-phases refine the decoding through borrowed "
                       "qualities — they never replace the output",
           "scope": "cell", "derived": False},
    "R4": {"source": "Codex §3.4 R4",
           "citation": "25 lenses: each applies one equation's quality "
                       "to another equation's decoding",
           "scope": "static", "derived": False},
    "R5": {"source": "Codex §3.4 R5",
           "citation": "Cycle trace maps creative line positions to "
                       "actual content as it forms",
           "scope": "cell", "derived": False},
    "R6": {"source": "Codex §3.4 R6",
           "citation": "Formation trail: per-output ordered record, "
                       "lens-tagged — what B'' reads",
           "scope": "cell", "derived": False},
    "R7": {"source": "Codex §3.4 R7",
           "citation": "Crystallization at V only — two passes (analysis "
                       "of trail → composition of artifact)",
           "scope": "step", "derived": False},
    "R8": {"source": "Codex §3.4 R8",
           "citation": "No V without ∞0'. ∞0' carries a question. No "
                       "question = not ∞0'",
           "scope": "step", "derived": False},
    "R9": {"source": "Codex §3.4 R9",
           "citation": "Five corruption codes: L1 L2 L3 L4 V∅. Each names "
                       "a specific decoding failure",
           "scope": "static", "derived": False},
    "R10": {"source": "Codex §3.4 R10",
            "citation": "H = ∞0 | A = K defines the asymmetry",
            "scope": "step", "derived": False},
    "R11": {"source": "Codex §3.4 R11",
            "citation": "Attestation: provenance travels with B'', "
                        "fingerprint hashes invariant only",
            "scope": "step", "derived": False},
    "R12": {"source": "Codex §3.4 R12",
            "citation": "Center is coherence only — where the five "
                        "decodings cohere as one field",
            "scope": "step", "derived": False},
    "R13": {"source": "Codex §3.4 R13",
            "citation": "Scale by repeating the lawful cell — decoding "
                        "operations do not change at scale",
            "scope": "static", "derived": False},
    # ---------------- the D12 pair and the K3 pair (derived) ----------
    "DC-DECODE": {"source": "D12 (his word, 2026-08-28) + Codex §3.2/§3.3",
                  "citation": "\"success in each phase is contextual "
                              "DECODING of context to language and "
                              "Compilation of output xyzab — nothing is "
                              "more actual then that.\" — Decode = the "
                              "phase's context turned into the language "
                              "(Codex §3.2 CONTEXT IN, §3.3 chain)",
                  "scope": "step", "derived": True},
    "DC-COMPILE": {"source": "D12 (his word, 2026-08-28) + Codex §3.2/§3.3",
                   "citation": "\"success in each phase is contextual "
                               "DECODING of context to language and "
                               "Compilation of output xyzab — nothing is "
                               "more actual then that.\" — Compile = the "
                               "phase's output symbol formed (S→X G→Y "
                               "Q→Z P→A V→B+B''+∞0′); the gate record IS "
                               "the compiled output, the gate letters are "
                               "the phase outputs lowercased (x y z a b)",
                   "scope": "step", "derived": True},
    "DC-AUTH-1": {"source": "his decision (K3) + Codex §2.2 success criterion",
                  "citation": "Whether an α is THE essence is the human's "
                              "click.  Codex §2.2: \"The decoding succeeds "
                              "when someone could see α in every member "
                              "of {α'} without being told.\" — the step "
                              "mode checks that the slot is filled and "
                              "referenced, never that it is true.",
                  "scope": "step", "derived": True},
    "DC-AUTH-2": {"source": "his decision (K3) + Codex §2.5 success criterion",
                  "citation": "Whether an ∞0' question is more alive than "
                              "the X it came from is the human's click.  "
                              "Codex §2.5: \"The decoding succeeds when "
                              "B'' carries α faithfully AND ∞0' contains "
                              "a question that is more alive than X "
                              "was.\" — the step mode checks that the "
                              "slot is filled and referenced, never that "
                              "it is true.",
                  "scope": "step", "derived": True},
}

# Import-time self-consistency (commission §3.7 lesson 5): the table and
# the evaluation can never drift apart — asserted, cheap and permanent.
_EVALUATED_IDS = frozenset(CHECK_ORDER)
assert _EVALUATED_IDS == frozenset(CHECKS), (
    "CHECKS table and CHECK_ORDER drifted apart: %s"
    % (_EVALUATED_IDS ^ frozenset(CHECKS),))

# ---------------------------------------------------------------------------
# Static facts about the ARTIFACT, decided by reading its own source and
# data tables (AST or text) — never by text search, never by opinion.
# Cached by the digest of the scanned files so a mutated twin re-scans.
# ---------------------------------------------------------------------------

# The artifact modules the static scans read (the shipped artifact — test
# apparatus is not part of what the checks judge).
_ARTIFACT_MODULES = (
    "step.py", "conformance.py", "surface.py", "driver.py",
    "instrument.py", "walker.py", "lens.py", "dialects.py",
)

_FLAG_WORDS = ("address", "word", "zoom", "frame", "daughter", "node",
               "path", "father")
_SIXTH_L = re.compile(r"\AL[0-9]+\Z")
# A sixth corruption code wears "V" plus a symbol suffix (like V∅).  The
# 25 lens ids (VS VG VQ VP VV) are letters, never flagged.
_SIXTH_V = re.compile(r"\AV[^\sA-Za-z0-9]{1,2}\Z")
_GRAMMAR_NEEDLE = "\\[" + "SGQPV" + "\\]"          # built, never a literal
_GRAMMAR = re.compile(_GRAMMAR_NEEDLE)
_REF_SHAPE = re.compile(r"\A[a-z][a-z0-9_.+-]*:[^\s]{1,200}\Z")
_HEX64 = re.compile(r"\A[0-9a-f]{64}\Z")
_CAP_NAMES = re.compile(r".*depth.*", re.IGNORECASE)
_ARTIFACT_DIR = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_SOURCES_DIR = os.path.join(
    os.path.dirname(_ARTIFACT_DIR), "sources")

_static_cache = {}


def _cap_scan_verdict(tree, path):
    """AST scan for a hard-coded cap on the address word (commission
    §3.7 lesson 4: by ast.Name / ast.Compare / ast.Subscript, never by
    text)."""
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and _CAP_NAMES.match(node.id):
            found.append("%s:%d identifier %r" % (path, node.lineno, node.id))
        if isinstance(node, ast.Compare) and node.ops and node.comparators:
            if not any(isinstance(op, (ast.Lt, ast.LtE, ast.Gt, ast.GtE))
                       for op in node.ops):
                continue
            if not all(isinstance(c, ast.Constant)
                       and isinstance(c.value, (int, float))
                       for c in node.comparators):
                continue
            left = node.left
            if (isinstance(left, ast.Call)
                    and isinstance(left.func, ast.Name)
                    and left.func.id == "len" and left.args):
                arg = left.args[0]
                name = None
                if isinstance(arg, ast.Name):
                    name = arg.id
                elif isinstance(arg, ast.Attribute):
                    name = arg.attr
                if name and any(flag in name for flag in _FLAG_WORDS):
                    found.append("%s:%d len(...) compared against a "
                                 "constant" % (path, node.lineno))
    return found


def _code_scan_verdict(tree, path):
    """AST scan of ast.Constant strings for a sixth corruption code
    (lesson 4: constants, so a regex DESCRIBING the codes is not
    mistaken for one)."""
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            value = node.value
            if _SIXTH_L.match(value) and value not in CORRUPTION_CODES:
                found.append("%s:%d string %r" % (path, node.lineno, value))
            elif _SIXTH_V.match(value) and value not in CORRUPTION_CODES:
                found.append("%s:%d string %r" % (path, node.lineno, value))
    return found


def _grammar_scan_verdict(tree, path):
    """AST scan for a re-implemented address grammar: a literal pattern
    carrying the [SGQPV] alphabet compiled anywhere in the artifact (B0's
    grammar is imported, never re-implemented)."""
    found = []
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "compile" and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
                and _GRAMMAR.search(node.args[0].value)):
            found.append("%s:%d re.compile(%r)" % (
                path, node.lineno, node.args[0].value))
    return found


def _static_facts():
    """Compute (and cache, keyed by the scanned bytes' digest) the
    artifact's static facts: depth caps, sixth codes, grammar
    re-implementations, and the equation constants' sign scan."""
    digests = []
    for name in _ARTIFACT_MODULES:
        path = os.path.join(_ARTIFACT_DIR, name)
        try:
            with open(path, "rb") as handle:
                raw = handle.read()
        except OSError:
            continue
        digests.append(hashlib.sha256(raw).hexdigest())
    key = hashlib.sha256("\n".join(digests).encode("ascii")).hexdigest()
    if key in _static_cache:
        return _static_cache[key]

    caps, codes, grammars = [], [], []
    for name in _ARTIFACT_MODULES:
        path = os.path.join(_ARTIFACT_DIR, name)
        try:
            with open(path, encoding="utf-8") as handle:
                source = handle.read()
        except OSError:
            continue
        tree = ast.parse(source)
        caps.extend(_cap_scan_verdict(tree, name))
        codes.extend(_code_scan_verdict(tree, name))
        grammars.extend(_grammar_scan_verdict(tree, name))

    # AD-SYN-4's static half: no + / − (U+2212) inside any equation
    # constant of the artifact.
    signed_equations = []
    for letter, entries in EQUATION_FORMS.items():
        for entry in entries:
            form = entry["form"]
            if "+" in form or "−" in form:
                signed_equations.append("%s %r" % (letter, form))

    facts = {
        "caps": caps,
        "sixth_codes": codes,
        "grammar_reimpls": grammars,
        "signed_equations": signed_equations,
        "modules_scanned": [n for n in _ARTIFACT_MODULES
                            if os.path.exists(
                                os.path.join(_ARTIFACT_DIR, n))],
    }
    _static_cache[key] = facts
    return facts


# ---------------------------------------------------------------------------
# Item evaluation helpers
# ---------------------------------------------------------------------------

def _inc(reason, evidence=None):
    return {"verdict": "INCONCLUSIVE", "evidence": list(evidence or []),
            "reason": reason}


def _pass(evidence=None):
    return {"verdict": "PASS", "evidence": list(evidence or []),
            "reason": None}


def _fail(reason, evidence=None):
    return {"verdict": "FAIL", "evidence": list(evidence or []),
            "reason": reason}


def _cell_observed(ctx):
    cell = ctx.get("cell") or {}
    return bool(cell.get("observed"))


def _surfaces(ctx):
    cell = ctx.get("cell") or {}
    return cell.get("surfaces") or {}


def _step(ctx):
    return ctx.get("step") or {}


def _ledger(ctx):
    return ctx.get("ledger") or {}


def _records(ctx):
    return _ledger(ctx).get("records") or []


def _slot_ref(slots, *names):
    for name in names:
        if name in slots:
            return name, slots[name]
    return None, None


def _attested_gates(records):
    """gate letters with a human attestation record (state attested +
    non-null attestation_ref) — provenance read off §5.1's fields."""
    gates = set()
    for record in records:
        if (record.get("state") == "attested"
                and record.get("attestation_ref") is not None
                and isinstance(record.get("gate"), str)):
            gates.add(record["gate"])
    return gates


def _plant(records):
    for record in records:
        if (record.get("gate") == "x" and record.get("address") == ""):
            return record
    return None


def _is_v_step(step):
    return step.get("kind") == "turn" and step.get("desk") == "V"


def _parse_for(ctx, desk):
    return _surfaces(ctx).get(desk) or {}


# ---------------------------------------------------------------------------
# The 50 evaluations.  Each returns {verdict, evidence, reason}; verdict
# is one of PASS | FAIL | INCONCLUSIVE and reason is present exactly when
# the verdict is not PASS.
# ---------------------------------------------------------------------------

def _ev_AD_SYN_1(ctx):
    if not _cell_observed(ctx):
        return _inc("no cell observed — no desk is constituted on this "
                    "box (H-P4a-4: INCONCLUSIVE is the correct live "
                    "verdict; P4b's desk bundles are what will turn it "
                    "into PASS)")
    cell = ctx["cell"]
    desks = sorted(set(cell.get("arrangement") or []))
    if desks == ["G", "P", "Q", "S", "V"]:
        return _pass(desks)
    if len(desks) < 5:
        missing = sorted(set("SGQPV") - set(desks))
        return _fail("3+1: the observed cell misses %s" % ", ".join(missing),
                     desks)
    return _fail("6+1: the observed cell carries extra desk(s) beyond "
                 "S G Q P V", desks)


def _ev_AD_SYN_2(ctx):
    surfaces = _surfaces(ctx)
    if not surfaces:
        return _inc("no desk surface observed — no desk's answer "
                    "announces a ⟦SURFACE v1⟧ block, so no cell's "
                    "equations are observable (the contract is what "
                    "P4b's desk bundles will be written against)")
    for desk, parsed in sorted(surfaces.items()):
        if parsed.get("status") != "lawful":
            return _fail("the surface of desk %s is %s, not lawful"
                         % (desk, parsed.get("status")),
                         [desk, parsed.get("status")])
        equations = parsed.get("equations") or {}
        for letter in PHASES:
            eq = equations.get(letter) or {}
            if not eq.get("match"):
                if not eq.get("observed_sha256") or not eq.get("len"):
                    return _fail(
                        "the surface of desk %s carries no equation line "
                        "for phase %s — the five equations do not all "
                        "appear at the cell" % (desk, letter),
                        [desk, letter])
                codepoint = eq.get("first_differing_codepoint")
                return _fail(
                    "paraphrased equation for phase %s on desk %s: the "
                    "observed bytes match no enumerated form — first "
                    "differing codepoint %s (observed sha256 %s, %d bytes)"
                    % (letter, desk,
                       ("U+%04X" % codepoint) if codepoint is not None
                       else "end-of-string",
                       eq.get("observed_sha256"), eq.get("len")),
                    [desk, letter, eq.get("observed_sha256"),
                     codepoint, eq.get("len")])
    evidence = []
    for letter in PHASES:
        for surface in surfaces.values():
            entry = (surface.get("equations") or {}).get(letter) or {}
            if entry.get("sha256"):
                evidence.append({"phase": letter,
                                 "form_sha256": entry["sha256"]})
            break
    return _pass(evidence)


def _ev_AD_SYN_3(ctx):
    surfaces = _surfaces(ctx)
    if not surfaces:
        return _inc("no desk surface observed — no symbol usage is "
                    "observable")
    for desk, parsed in sorted(surfaces.items()):
        for entry in (parsed.get("symbols") or []):
            if not entry.get("in_vocabulary"):
                return _fail(
                    "an L1 symbol was added or renamed: %r (desk %s)"
                    % (entry.get("name"), desk),
                    [desk, entry.get("name")])
    return _pass(sorted({e["name"] for s in surfaces.values()
                         for e in (s.get("symbols") or [])}))


def _ev_AD_SYN_4(ctx):
    facts = _static_facts()
    static_ok = not facts["signed_equations"]
    if not _cell_observed(ctx):
        if not static_ok:
            return _fail("the artifact's own equation constants carry a "
                         "sign: %s" % ", ".join(facts["signed_equations"]),
                         facts["signed_equations"])
        return _inc("the artifact's own equation constants carry no +/− "
                    "(static scan over %s), but no cell was observed — "
                    "the cell half is unobservable"
                    % ", ".join(facts["modules_scanned"]))
    for desk, parsed in sorted(_surfaces(ctx).items()):
        equations = parsed.get("equations") or {}
        for letter in PHASES:
            eq = equations.get(letter) or {}
            sha = eq.get("observed_sha256")
            if not sha:
                continue
            if eq.get("first_differing_codepoint") in (
                    ord("+"), ord("-"), ord("−")):
                return _fail("the sign +/− appears inside the equation "
                             "for phase %s on desk %s" % (letter, desk),
                             [desk, letter])
    if not static_ok:
        return _fail("the artifact's own equation constants carry a "
                     "sign: %s" % ", ".join(facts["signed_equations"]),
                     facts["signed_equations"])
    return _pass(["static: no sign in any equation constant"])


def _ev_AD_SYN_5(ctx):
    surfaces = _surfaces(ctx)
    if not surfaces:
        return _inc("no desk surface observed — no corruption line is "
                    "observable")
    for desk, parsed in sorted(surfaces.items()):
        observed = set(parsed.get("corruption_codes") or [])
        if not observed:
            return _fail("the surface of desk %s announces no corruption "
                         "line — the constitutional block is not exact"
                         % desk, [desk])
        if observed != set(CORRUPTION_CODES):
            extra = sorted(observed - set(CORRUPTION_CODES))
            if extra:
                return _fail("a corruption code beyond L1 L2 L3 L4 V∅ is "
                             "announced: %s (desk %s)"
                             % (", ".join(sorted(extra)), desk),
                             [desk, sorted(observed)])
            return _fail("the surface of desk %s announces fewer than the "
                         "five codes: %s" % (desk, sorted(observed)),
                         [desk, sorted(observed)])
    return _pass(sorted(CORRUPTION_CODES))


def _ev_AD_SEM_1(ctx):
    step = _step(ctx)
    if step.get("kind") != "turn":
        return _inc("no context flows on a %s step" % step.get("kind"))
    outcome = step.get("outcome") or {}
    if outcome.get("status") == "refused":
        # the out-of-order attempt was refused AND recorded — no context
        # flowed without the father's outputs; the guard held
        return _pass(["out-of-order attempt refused and recorded — no "
                      "fatherless flow occurred"])
    desk = step.get("desk")
    zoom = step.get("zoom") or {}
    if not (zoom.get("op") == "in" and zoom.get("sign") == "−"
            and zoom.get("letter") == desk):
        return _fail("the turn's zoom does not carry the father → "
                     "daughter move (op in, sign −, letter = the desk)",
                     [zoom])
    if desk not in COURSE:
        return _inc("desk %r is not on the course" % desk)
    index = COURSE.index(desk)
    gates = _attested_gates(_records(ctx))
    prior = [DESK_GATES[d] for d in COURSE[:index]]
    missing = [g for g in prior if g not in gates]
    if missing:
        return _fail("context does not flow father → daughter: gate(s) %s "
                     "have no attestation record — the daughter's decode "
                     "lacks the father's output" % ", ".join(missing),
                     missing)
    return _pass(prior)


def _ev_AD_SEM_2(ctx):
    step = _step(ctx)
    zoom = step.get("zoom") or {}
    kind = step.get("kind")
    if kind == "turn":
        if (zoom.get("op") == "in" and zoom.get("sign") == "−"
                and zoom.get("letter") == step.get("desk")):
            return _pass([zoom])
        return _fail("the sign is not relative to the step's vantage: a "
                     "turn must carry op in, sign −, letter = the desk",
                     [zoom])
    if kind in ("boot", "advance", "position"):
        if zoom.get("op") == "none" and zoom.get("sign") is None:
            return _pass([zoom])
        return _fail("a %s step carries a sign where none exists"
                     % kind, [zoom])
    return _inc("the sign is not observable on a %s step" % kind)


def _ev_AD_SEM_3(ctx):
    if not _is_v_step(_step(ctx)):
        return _inc("no V closes on this step")
    decoded = _step(ctx).get("decoded") or {}
    if decoded.get("source") != "desk_surface":
        return _inc("the V desk announced no surface — whether the cell "
                    "closed with ∞0′ is not observable")
    slots = decoded.get("slots") or {}
    name, ref = _slot_ref(slots, "∞0′", "∞0'")
    if name is None:
        return _fail("the V closes with no ∞0′ — the Completion Rule is "
                     "broken across the cell boundary")
    return _pass([name, ref.get("ref"), ref.get("len")])


def _ev_AD_SEM_4(ctx):
    records = _records(ctx)
    if not records:
        return _inc("the ledger holds no records — the true start is not "
                    "observable")
    first = records[0]
    address = first.get("address")
    if address is None:
        return _inc("the first record carries no address field")
    if address[:1] in ("+", "-", "−"):
        return _fail("signed true start: the first record's address %r "
                     "carries a sign — the true start is signless"
                     % address, [address, first.get("record_id")])
    return _pass([address, first.get("record_id")])


def _ev_AD_SEM_5(ctx):
    if not _cell_observed(ctx):
        return _inc("no cell observed — the question's field is not "
                    "observable")
    x_refs = []
    for desk, parsed in sorted(_surfaces(ctx).items()):
        slots = parsed.get("slots") or {}
        if "X" in slots:
            x_refs.append((desk, slots["X"]["ref"]))
    if not x_refs:
        return _inc("no observed surface declares an X slot — the shared "
                    "question's reference is not observable")
    distinct = {ref for _desk, ref in x_refs}
    if len(distinct) > 1:
        return _fail("the shared question is not one ∞0-field: the "
                     "observed X references disagree across desks",
                     [{"desk": d, "ref": r} for d, r in x_refs])
    return _pass([{"desk": d, "ref": r} for d, r in x_refs])


def _ev_AD_DRF_1(ctx):
    facts = _static_facts()
    if facts["caps"]:
        return _fail("a hard-coded cap on the address word exists in the "
                     "artifact: %s" % "; ".join(facts["caps"]),
                     facts["caps"])
    return _pass(["AST scan over %s: no identifier names a depth and no "
                  "len(address-like) is compared against a constant"
                  % ", ".join(facts["modules_scanned"])])


def _ev_AD_DRF_2(ctx):
    import step
    kinds = step.STEP_KINDS
    zoom_out = kinds.get("zoom_out") or {}
    zoom_in = kinds.get("zoom_in") or {}
    if zoom_out.get("derived_reading") is True and not zoom_out.get(
            "implemented") and not zoom_in.get("implemented"):
        return _pass(["zoom_out.derived_reading = True (marked); both "
                      "zoom entries reserved for B3"])
    return _fail("the zoom-out inverse is not marked as a derived "
                 "reading, or a zoom entry gained an implementation")


def _ev_AD_DRF_3(ctx):
    lines = (ctx.get("session") or {}).get("lines") or []
    walked = [line.get("desk") for line in lines
              if line.get("kind") == "turn"
              and (line.get("outcome") or {}).get("status") == "proposed"]
    if not walked or len(walked) < 4:
        return _inc("fewer than four turns were walked to proposal — the "
                    "session did not complete the walk; no ordering "
                    "verdict is possible")
    if walked == ["G", "Q", "P", "V"]:
        return _pass(walked)
    return _fail("a decoding step was omitted or reordered: the walked "
                 "phases are %s, the course order is G Q P V"
                 % ", ".join(walked), walked)


def _ev_AD_DRF_4(ctx):
    facts = _static_facts()
    if facts["sixth_codes"]:
        return _fail("a sixth corruption code exists in the artifact: %s"
                     % "; ".join(facts["sixth_codes"]), facts["sixth_codes"])
    return _pass(["AST constant scan over %s: the only corruption-code "
                  "strings are L1 L2 L3 L4 V∅"
                  % ", ".join(facts["modules_scanned"])])


def _ev_AD_DRF_5(ctx):
    surfaces = _surfaces(ctx)
    if not surfaces:
        return _inc("no desk surface observed — no lens questions are "
                    "observable")
    lenses = [lens for parsed in surfaces.values()
              for lens in (parsed.get("lenses") or [])]
    if not lenses:
        return _inc("no observed surface carries a lens section — no "
                    "lens questions are observable")
    for lens in lenses:
        if not lens.get("target_ok"):
            return _fail(
                "lens %s targets %s — the parent output is %s (the "
                "question must target OUTPUT_SYMBOL[id[0]], parent FIRST)"
                % (lens.get("id"), lens.get("target"),
                   OUTPUT_SYMBOLS[lens.get("id")[0]]),
                [lens])
    return _pass([l["id"] for l in lenses])


def _ev_CX_SYN_1(ctx):
    surfaces = _surfaces(ctx)
    if not surfaces:
        return _inc("no desk surface observed — symbol resolution is not "
                    "observable")
    for desk, parsed in sorted(surfaces.items()):
        for entry in (parsed.get("symbols") or []):
            if not entry.get("covered"):
                return _fail("symbol %r is used on desk %s but resolves "
                             "to no symbol-table entry (§1.9 / §3.2)"
                             % (entry.get("name"), desk),
                             [desk, entry.get("name")])
    return _pass(["every used symbol resolves"])


def _ev_CX_SYN_2(ctx):
    surfaces = _surfaces(ctx)
    if not surfaces:
        return _inc("no desk surface observed — no phase equation is "
                    "observable")
    for desk, parsed in sorted(surfaces.items()):
        active = parsed.get("active") or {}
        equation = active.get("equation") or {}
        phase = active.get("phase")
        if not equation.get("match"):
            codepoint = equation.get("first_differing_codepoint")
            return _fail(
                "the compiled form of phase %s on desk %s does not carry "
                "its exact equation — observed bytes match no enumerated "
                "form (first differing codepoint %s, observed sha256 %s)"
                % (phase, desk,
                   ("U+%04X" % codepoint) if codepoint is not None
                   else "end-of-string",
                   equation.get("observed_sha256")),
                [desk, phase, equation.get("observed_sha256"), codepoint])
    return _pass(["every observed phase carries its exact equation"])


def _ev_CX_SYN_3(ctx):
    surfaces = _surfaces(ctx)
    if not surfaces:
        return _inc("no desk surface observed — no decoding operation is "
                    "observable")
    for desk, parsed in sorted(surfaces.items()):
        decoding = parsed.get("decoding") or {}
        if decoding.get("matches") is not True:
            return _fail(
                "the decoding operation of desk %s does not follow D1 "
                "symbol-by-symbol — first mismatch at operation index %s"
                % (desk, decoding.get("first_mismatch_index")),
                [desk, decoding.get("first_mismatch_index")])
    return _pass(["every observed decoding follows D1"])


def _ev_CX_SYN_4(ctx):
    if set(PHASES) == {"S", "G", "Q", "P", "V"} and len(PHASES) == 5 \
            and len(LENSES) == 25 and set(LENSES) == {
                a + b for a in "SGQPV" for b in "SGQPV"}:
        return _pass(["5 phases present, 25 sub-phases available "
                      "(the data tables)"])
    return _fail("the phase or sub-phase tables are incomplete: %d "
                 "phases, %d lenses" % (len(PHASES), len(LENSES)))


def _ev_CX_SYN_5(ctx):
    if CORRUPTION_CODES == frozenset(("L1", "L2", "L3", "L4", "V\u2205")):
        return _pass(sorted(CORRUPTION_CODES))
    return _fail("CORRUPTION_CODES is not exactly the five codes",
                 sorted(CORRUPTION_CODES))


def _ev_CX_SYN_6(ctx):
    if not _is_v_step(_step(ctx)):
        return _inc("no V closes on this step")
    decoded = _step(ctx).get("decoded") or {}
    if decoded.get("source") != "desk_surface":
        return _inc("the V desk announced no surface — whether the "
                    "completion rule held is not observable")
    slots = decoded.get("slots") or {}
    name, ref = _slot_ref(slots, "∞0′", "∞0'")
    if name is None:
        return _fail("a V closed without ∞0′ — the completion rule is "
                     "not enforceable at this cell")
    return _pass([name, ref.get("ref"), ref.get("len")])


def _ev_CX_SEM_1(ctx):
    surfaces = _surfaces(ctx)
    if not surfaces:
        return _inc("no desk surface observed — the adaptive context is "
                    "not observable")
    for desk, parsed in sorted(surfaces.items()):
        active = parsed.get("active") or {}
        phase = active.get("phase")
        if phase not in PHASES:
            continue
        declared = active.get("context_in")
        expected = CONTEXT_IN[phase]
        if declared != expected:
            return _fail(
                "the decoding of phase %s on desk %s receives the wrong "
                "adaptive context: %s (Codex §3.3 expects %s)"
                % (phase, desk, " + ".join(declared or []),
                   " + ".join(expected)),
                [desk, phase, declared, expected])
    return _pass(["every observed decoding receives its §3.3 context"])


def _ev_CX_SEM_2(ctx):
    step = _step(ctx)
    if step.get("kind") != "turn":
        return _inc("no context chain advances on a %s step"
                    % step.get("kind"))
    desk = step.get("desk")
    outcome = step.get("outcome") or {}
    if desk not in COURSE:
        return _inc("desk %r is not on the course" % desk)
    index = COURSE.index(desk)
    gates = _attested_gates(_records(ctx))
    prior = [DESK_GATES[d] for d in COURSE[:index]]
    missing = [g for g in prior if g not in gates]
    if outcome.get("status") == "refused":
        # The out-of-order attempt was refused AND recorded — the guard
        # held, the chain is unbroken (the refusal is the evidence).
        return _pass(["out-of-order attempt refused and recorded — the "
                      "context chain is unbroken"])
    if missing:
        return _fail("the context chain is broken at this step: the turn "
                     "for desk %s was performed while gate(s) %s carry no "
                     "attestation record" % (desk, ", ".join(missing)),
                     missing)
    return _pass(prior)


def _ev_CX_SEM_3(ctx):
    surfaces = _surfaces(ctx)
    if not surfaces:
        return _inc("no desk surface observed — B, B'' and ∞0′ are not "
                    "observable")
    for desk, parsed in sorted(surfaces.items()):
        if parsed.get("phase") != "V":
            continue
        slots = parsed.get("slots") or {}
        names = [n for n in ("B", "B''", "B″") if n in slots]
        names += [n for n in ("∞0′", "∞0'") if n in slots]
        if len(names) < 3:
            return _inc("not all three things are observable on desk %s "
                        "(the absence itself is CX-SYN-6's failure) — "
                        "distinctness of absent slots cannot be judged"
                        % desk)
        refs = {slots[n]["ref"] for n in names}
        if len(refs) < len(names):
            return _fail("B, B'' and ∞0′ are not three distinct things "
                         "on desk %s — two slots share one reference"
                         % desk, [names])
    return _pass(["the three things carry distinct references"])


def _ev_CX_SEM_4(ctx):
    surfaces = _surfaces(ctx)
    if not surfaces:
        return _inc("no desk surface observed — no lens is observable")
    lenses = [lens for parsed in surfaces.values()
              for lens in (parsed.get("lenses") or [])]
    if not lenses:
        return _inc("no observed surface carries a lens section")
    for lens in lenses:
        if not lens.get("equation_ok"):
            return _fail(
                "lens %s refines the wrong equation (the lens must carry "
                "the parent's equation, id[0])" % lens.get("id"),
                [lens])
    return _pass([l["id"] for l in lenses])


def _ev_CX_SEM_5(ctx):
    if not _is_v_step(_step(ctx)):
        return _inc("no crystallization happens on this step")
    step = _step(ctx)
    parsed = step.get("surface_parse") or {}
    if parsed.get("status") != "lawful":
        return _inc("the V desk announced no surface — whether "
                    "crystallization read the formation trail is not "
                    "observable from the gate record alone")
    trail = parsed.get("trail")
    if trail is None:
        return _inc("the V surface carries no formation-trail section — "
                    "not observable")
    passes = trail.get("passes") or {}
    if not (passes.get("Pass 1") and passes.get("Pass 2")):
        return _fail("crystallization did not read the formation trail: "
                     "the two passes (analysis of trail → composition of "
                     "artifact) are not both declared", [passes])
    return _pass([passes])


def _ev_CX_SEM_6(ctx):
    if not _is_v_step(_step(ctx)):
        return _inc("no ∞0′ forms on this step")
    slots = ((_step(ctx).get("decoded") or {}).get("slots") or {})
    name, ref = _slot_ref(slots, "∞0′", "∞0'")
    if name is None:
        return _inc("no ∞0′ slot is observable on this step (its absence "
                    "is CX-SYN-6's failure)")
    if ref.get("len"):
        return _pass([name, ref.get("ref"), ref.get("len")])
    return _fail("the ∞0′ slot is empty — a questionless ∞0′ is not ∞0′ "
                 "(no question = not ∞0′)", [name, ref.get("ref"), 0])


def _ev_CX_DRF_1(ctx):
    missing = []
    for name in SYMBOL_VOCABULARY:
        if name in SYMBOL_TABLE or name in SYMBOL_ALIASES:
            continue
        missing.append(name)
    if missing:
        return _fail("symbol(s) renamed without source name present: %s"
                     % ", ".join(sorted(missing)), missing)
    return _pass(["every vocabulary symbol carries its §1.9 source name"])


def _ev_CX_DRF_2(ctx):
    sources_dir = (ctx.get("sources_dir") or _DEFAULT_SOURCES_DIR)
    problems = []
    checked = 0
    for letter, entries in EQUATION_FORMS.items():
        for entry in entries:
            form = entry["form"]
            found = False
            for filename, line_no in entry["locations"]:
                path = os.path.join(sources_dir, filename)
                try:
                    with open(path, encoding="utf-8") as handle:
                        lines = handle.read().splitlines()
                except OSError:
                    return _inc("the held source file %s is not readable "
                                "from %s — the equation table cannot be "
                                "checked against the source"
                                % (filename, sources_dir))
                if (line_no - 1) < len(lines) and form in lines[line_no - 1]:
                    found = True
                    break
            checked += 1
            if not found:
                problems.append("%s %r" % (letter, form))
    if problems:
        return _fail("the equation table drifts from the source: %s"
                     % "; ".join(problems), problems)
    return _pass(["%d enumerated form(s) found verbatim at their "
                  "declared source lines" % checked])


def _ev_CX_DRF_3(ctx):
    lines = (ctx.get("session") or {}).get("lines") or []
    walked = [line for line in lines
              if line.get("kind") == "turn"
              and (line.get("outcome") or {}).get("status") == "proposed"]
    if not walked or len(walked) < 4:
        return _inc("fewer than four turns were walked — no decoding "
                    "sequence is observable")
    import surface as surface_module
    problems = []
    observable = []
    for line in walked:
        desk = line.get("desk")
        if desk not in DECODING_OPS:
            continue
        decoded = line.get("decoded") or {}
        steps = decoded.get("operation_steps") or []
        expected = [step_op.split(" — ")[0] for step_op in
                    surface_module.DECODING_OPS[desk]]
        expected = [step.split(":")[0] for step in expected]
        if decoded.get("source") != "desk_surface":
            continue  # not observable — never a silent omission either
        observable.append(desk)
        if [s if isinstance(s, str) else s.get("op")
                for s in steps] != expected:
            problems.append("%s" % desk)
    if not observable:
        return _inc("no walked phase announced a surface — the decoding "
                    "steps are not observable")
    if problems:
        return _fail("a decoding step was omitted or reordered on the "
                     "announced surface of: %s" % ", ".join(problems),
                     problems)
    return _pass(["the recorded operation steps follow D1 order on %s"
                  % ", ".join(observable)])


def _ev_CX_DRF_4(ctx):
    return _ev_AD_DRF_4(ctx)  # mirror by source design (D.12 and §3.5
    # both state the five-code rule; the scan is the same scan)


def _ev_CX_DRF_5(ctx):
    lines = (ctx.get("session") or {}).get("lines") or []
    walked = [line for line in lines
              if line.get("kind") == "turn"
              and (line.get("outcome") or {}).get("status") == "proposed"]
    if not walked or len(walked) < 4:
        return _inc("fewer than four turns were walked — the adaptive "
                    "context chain is not fully observable")
    problems = []
    for line in walked:
        desk = line.get("desk")
        if desk not in COURSE:
            continue
        prior = [DESK_GATES[d] for d in COURSE[:COURSE.index(desk)]]
        observed = {entry.get("gate") for entry in
                    ((line.get("context_in") or {}).get("prior_outputs")
                     or [])}
        missing = [g for g in prior if g not in observed]
        if missing:
            problems.append({"desk": desk, "missing": missing})
    if problems:
        return _fail("the adaptive context chain was not preserved: %s"
                     % problems, problems)
    return _pass(["every walked step's context_in carried its prior "
                  "outputs"])


def _ev_CX_DRF_6(ctx):
    return _ev_AD_DRF_5(ctx)  # mirror by source design (D.12 drift and
    # §3.5 drift both end with the same lens rule)


def _ev_R1(ctx):
    step = _step(ctx)
    if step.get("kind") != "turn":
        return _inc("no phase decodes on a %s step" % step.get("kind"))
    parsed = step.get("surface_parse") or {}
    if parsed.get("status") != "lawful":
        return _inc("the desk announced no lawful surface — the decode "
                    "is not observable")
    active = parsed.get("active") or {}
    if active.get("output_matches") is not True:
        return _fail(
            "the phase did not decode its one equation to its one "
            "output: the announced OUTPUT is %r, Codex §3.2 expects %r"
            % (active.get("output"),
               PHASES.get(active.get("phase"), {}).get("output")),
            [active.get("phase"), active.get("output")])
    return _pass([active.get("phase"), active.get("output")])


def _ev_R2(ctx):
    if not _is_v_step(_step(ctx)):
        return _inc("no V output forms on this step")
    decoded = _step(ctx).get("decoded") or {}
    if decoded.get("source") != "desk_surface":
        return _inc("the V desk announced no surface — B, B'' and ∞0' "
                    "are not observable")
    slots = decoded.get("slots") or {}
    _, b_ref = _slot_ref(slots, "B")
    _, b2_ref = _slot_ref(slots, "B''", "B″")
    _, r_ref = _slot_ref(slots, "∞0′", "∞0'")
    missing = []
    if b_ref is None:
        missing.append("B")
    if b2_ref is None:
        missing.append("B''")
    if r_ref is None:
        missing.append("∞0'")
    if missing:
        return _fail("the three things of R2 are not all formed at V: "
                     "missing %s" % ", ".join(missing), missing)
    return _pass(["B", "B''", "∞0'"])


def _ev_R3(ctx):
    surfaces = _surfaces(ctx)
    if not surfaces:
        return _inc("no desk surface observed — no sub-phase lens is "
                    "observable")
    lenses = [lens for parsed in surfaces.values()
              for lens in (parsed.get("lenses") or [])]
    if not lenses:
        return _inc("no observed surface carries a lens section")
    for lens in lenses:
        if not (lens.get("target_ok") and lens.get("quality_ok")):
            return _fail(
                "sub-phase lens %s does not refine through a borrowed "
                "quality while keeping the parent's output (target %s)"
                % (lens.get("id"), lens.get("target")), [lens])
    return _pass([l["id"] for l in lenses])


def _ev_R4(ctx):
    expected = {a + b for a in "SGQPV" for b in "SGQPV"}
    if set(LENSES) == expected and len(LENSES) == 25:
        return _pass(["the 25-lens table is complete"])
    return _fail("the 25-lens table is incomplete: %d of 25"
                 % len(LENSES))


def _ev_R5(ctx):
    surfaces = _surfaces(ctx)
    if not surfaces:
        return _inc("no desk surface observed — no cycle trace is "
                    "observable")
    traces = [parsed.get("trace") for parsed in surfaces.values()
              if parsed.get("trace")]
    if not traces:
        return _inc("no observed surface carries a cycle trace — not "
                    "observable")
    from surface import CREATIVE_LINE
    for trace in traces:
        if not trace.get("entries"):
            return _fail("the cycle trace declares no positions")
        if not trace.get("all_mapped"):
            unmapped = [entry.get("position") for entry in
                        trace["entries"] if not entry.get("mapped")]
            return _fail("the cycle trace does not map every declared "
                         "position to actual content as it forms: "
                         "unmapped %s" % ", ".join(unmapped), unmapped)
        positions = [entry.get("position") for entry in trace["entries"]]
        if any(pos not in CREATIVE_LINE for pos in positions):
            return _fail("the cycle trace carries a position outside the "
                         "creative line: %s" % ", ".join(positions),
                         positions)
        indices = [CREATIVE_LINE.index(pos) for pos in positions]
        if indices != sorted(indices):
            return _fail("the cycle trace reorders the creative line",
                         positions)
    return _pass(["every declared trace position maps to a filled slot, "
                  "in creative-line order"])


def _ev_R6(ctx):
    surfaces = _surfaces(ctx)
    if not surfaces:
        return _inc("no desk surface observed — no formation trail is "
                    "observable")
    trails = [parsed.get("trail") for parsed in surfaces.values()
              if parsed.get("trail")]
    if not trails:
        return _inc("no observed surface carries a formation trail — not "
                    "observable")
    for trail in trails:
        entries = trail.get("entries") or []
        if not entries:
            return _fail("the formation trail is declared but carries no "
                         "ordered record")
        for entry in entries:
            if entry.get("lens") not in LENSES or not entry.get(
                    "ref_present"):
                return _fail("a formation-trail record is not lens-tagged "
                             "or carries no reference", [entry])
    return _pass(["every formation-trail record is ordered, lens-tagged "
                  "and referenced"])


def _ev_R7(ctx):
    step = _step(ctx)
    if not _is_v_step(step):
        return _pass(["no crystallization is claimed on this step — "
                      "crystallization happens at V only"])
    parsed = step.get("surface_parse") or {}
    if parsed.get("status") != "lawful":
        return _inc("the V desk announced no surface — the two passes are "
                    "not observable")
    trail = parsed.get("trail")
    if trail is None:
        return _inc("the V surface carries no formation-trail section")
    passes = trail.get("passes") or {}
    if not (passes.get("Pass 1") and passes.get("Pass 2")):
        return _fail("crystallization at V did not run its two passes "
                     "(analysis of trail → composition of artifact)",
                     [passes])
    return _pass([passes])


def _ev_R8(ctx):
    if not _is_v_step(_step(ctx)):
        return _inc("no V output forms on this step")
    decoded = _step(ctx).get("decoded") or {}
    if decoded.get("source") != "desk_surface":
        return _inc("the V desk announced no surface — the return "
                    "question is not observable")
    slots = decoded.get("slots") or {}
    name, ref = _slot_ref(slots, "∞0′", "∞0'")
    if name is None:
        return _fail("no V without ∞0' — the V closed with no return "
                     "question")
    if not ref.get("len"):
        return _fail("the ∞0′ carries no question — no question = not ∞0′")
    return _pass([name, ref.get("ref"), ref.get("len")])


def _ev_R9(ctx):
    codes = set(CORRUPTION_CODES)
    if codes != {"L1", "L2", "L3", "L4", "V\u2205"}:
        return _fail("the corruption-code table is not exactly the five",
                     sorted(codes))
    missing_failures = [code for code in codes
                        if code not in CORRUPTION_FAILURES]
    if missing_failures:
        return _fail("corruption code(s) name no decoding failure: %s"
                     % ", ".join(missing_failures), missing_failures)
    return _pass(["each of the five codes names its §2.8 decoding "
                  "failure"])


def _ev_R10(ctx):
    records = _records(ctx)
    if not records:
        return _inc("the ledger holds no records — the asymmetry is not "
                    "observable")
    offenders = []
    for record in records:
        if record.get("mark") == "mechanical" and (
                record.get("state") == "attested"
                or record.get("attestation_ref") is not None):
            offenders.append(record.get("record_id"))
    if offenders:
        return _fail("the membrane is crossed: machine-marked record(s) "
                     "carry state attested or a non-null attestation_ref "
                     "— provenance is read off mark, never off a "
                     "convention", offenders)
    return _pass(["every mechanical record stays on the A = K side"])


def _ev_R11(ctx):
    records = _records(ctx)
    if not records:
        return _inc("the ledger holds no records — provenance is not "
                    "observable")
    offenders = []
    for record in records:
        ref = record.get("payload_ref")
        if not isinstance(ref, str) or not ref:
            offenders.append({"record_id": record.get("record_id"),
                              "shape": "absent-or-empty"})
            continue
        if _REF_SHAPE.match(ref) or _HEX64.match(ref):
            continue
        offenders.append({"record_id": record.get("record_id"),
                          "shape": "not-a-reference"})
    if offenders:
        return _fail("a payload_ref is not a reference: a scheme-prefixed "
                     "locator or a bare fingerprint hash is the only "
                     "lawful shape — provenance travels with the hashes, "
                     "never with content", offenders)
    return _pass(["every payload_ref is a reference (scheme-prefixed "
                  "locator or bare 64-hex fingerprint)"])


def _ev_R12(ctx):
    records = _records(ctx)
    plant = _plant(records)
    if plant is None:
        return _inc("the ledger carries no centre record (gate x, "
                    "address '') — the centre is not observable")
    if (plant.get("mark") == "emergent"
            and plant.get("state") == "attested"
            and plant.get("attestation_ref") is not None):
        return _pass(["the centre record is the human's emergent, "
                      "attested plant — coherence only, never a sixth "
                      "phase", plant.get("record_id")])
    return _fail("the centre record is not the human's: mark %r, state "
                 "%r — the centre is coherence only, and a machine "
                 "record claiming it would be a sixth phase"
                 % (plant.get("mark"), plant.get("state")),
                 [plant.get("record_id")])


def _ev_R13(ctx):
    facts = _static_facts()
    problems = []
    if facts["grammar_reimpls"]:
        problems.append("a second address grammar is compiled in the "
                        "artifact: %s"
                        % "; ".join(facts["grammar_reimpls"]))
    if facts["caps"]:
        problems.append("a hard-coded cap exists: %s"
                        % "; ".join(facts["caps"]))
    if tuple(COURSE) != ("S", "G", "Q", "P", "V"):
        problems.append("the address alphabet is not the data-table "
                        "course S G Q P V")
    if problems:
        return _fail("scale by repeating the lawful cell is broken: %s"
                     % " | ".join(problems), problems)
    return _pass(["no second address grammar, no depth cap, no root "
                  "assumption — the alphabet is the data table and the "
                  "decoding operations are one table at every scale"])


def _ev_DC_DECODE(ctx):
    step = _step(ctx)
    if step.get("kind") != "turn":
        return _inc("no decode occurs on a %s step" % step.get("kind"))
    decoded = step.get("decoded") or {}
    if decoded.get("source") != "desk_surface":
        return _inc("the desk's answer announces no surface — the "
                    "contextual decode is not observable (references "
                    "only; the contract is what P4b's bundles are "
                    "written against)")
    desk = step.get("desk")
    index = COURSE.index(desk) if desk in COURSE else -1
    if index > 0:
        gates = _attested_gates(_records(ctx))
        prior = [DESK_GATES[d] for d in COURSE[:index]]
        missing = [g for g in prior if g not in gates]
        if missing:
            return _fail("the decode did not receive its context: gate(s) "
                         "%s carry no attestation record — success in "
                         "each phase is contextual DECODING of context "
                         "to language" % ", ".join(missing), missing)
    return _pass(["the context was decoded to the language by reference",
                  decoded.get("slots") or {}])


def _ev_DC_COMPILE(ctx):
    step = _step(ctx)
    if step.get("kind") != "turn":
        return _inc("no compile occurs on a %s step" % step.get("kind"))
    outcome = step.get("outcome") or {}
    compiled = step.get("compiled") or {}
    if outcome.get("status") != "proposed":
        return _inc("nothing was compiled on this step (status %s)"
                    % outcome.get("status"))
    desk = step.get("desk")
    if compiled.get("symbol") != COMPILED_OUTPUTS.get(desk) \
            or compiled.get("gate") != DESK_GATES.get(desk):
        return _fail("the compiled output does not match the phase: "
                     "symbol %s, gate %s (desk %s expects %s / %s)"
                     % (compiled.get("symbol"), compiled.get("gate"),
                        desk, COMPILED_OUTPUTS.get(desk),
                        DESK_GATES.get(desk)),
                     [compiled])
    if not compiled.get("landed"):
        return _fail("the compiled output did not land: the gate record "
                     "is the compiled output (D12)", [compiled])
    return _pass([compiled.get("symbol"), compiled.get("gate"),
                  compiled.get("landed")])


def _ev_DC_AUTH_1(ctx):
    step = _step(ctx)
    reason = ("whether α is THE essence is the human's click — the step "
              "mode checks that the slot is filled and referenced, never "
              "that it is true (K3).  Codex §2.2: \"The decoding succeeds "
              "when someone could see α in every member of {α'} without "
              "being told.\"  A machine that reports resonance has "
              "failed the measure.")
    if step.get("kind") == "turn" and step.get("desk") == "G":
        slots = ((step.get("decoded") or {}).get("slots") or {})
        name, ref = _slot_ref(slots, "α")
        evidence = ([name, ref.get("ref"), ref.get("len")]
                    if name is not None
                    else ["no α slot observed — the essence is not "
                          "referenced"])
        return _inc(reason, evidence)
    return _inc(reason, ["no α decode on this step"])


def _ev_DC_AUTH_2(ctx):
    step = _step(ctx)
    reason = ("whether the ∞0' question is more alive than the X it came "
              "from is the human's click — the step mode checks that the "
              "slot is filled and referenced, never that it is true "
              "(K3).  Codex §2.5: \"The decoding succeeds when B'' "
              "carries α faithfully AND ∞0' contains a question that is "
              "more alive than X was.\"  A machine that reports "
              "resonance has failed the measure.")
    if _is_v_step(step):
        slots = ((step.get("decoded") or {}).get("slots") or {})
        _, r_ref = _slot_ref(slots, "∞0′", "∞0'")
        _, x_ref = _slot_ref(slots, "X")
        evidence = [("∞0'", r_ref) if r_ref else "no ∞0′ slot observed",
                    ("X", x_ref) if x_ref else "no X slot observed"]
        return _inc(reason, evidence)
    return _inc(reason, ["no V output on this step"])


_EVALUATORS = {
    "AD-SYN-1": _ev_AD_SYN_1, "AD-SYN-2": _ev_AD_SYN_2,
    "AD-SYN-3": _ev_AD_SYN_3, "AD-SYN-4": _ev_AD_SYN_4,
    "AD-SYN-5": _ev_AD_SYN_5,
    "AD-SEM-1": _ev_AD_SEM_1, "AD-SEM-2": _ev_AD_SEM_2,
    "AD-SEM-3": _ev_AD_SEM_3, "AD-SEM-4": _ev_AD_SEM_4,
    "AD-SEM-5": _ev_AD_SEM_5,
    "AD-DRF-1": _ev_AD_DRF_1, "AD-DRF-2": _ev_AD_DRF_2,
    "AD-DRF-3": _ev_AD_DRF_3, "AD-DRF-4": _ev_AD_DRF_4,
    "AD-DRF-5": _ev_AD_DRF_5,
    "CX-SYN-1": _ev_CX_SYN_1, "CX-SYN-2": _ev_CX_SYN_2,
    "CX-SYN-3": _ev_CX_SYN_3, "CX-SYN-4": _ev_CX_SYN_4,
    "CX-SYN-5": _ev_CX_SYN_5, "CX-SYN-6": _ev_CX_SYN_6,
    "CX-SEM-1": _ev_CX_SEM_1, "CX-SEM-2": _ev_CX_SEM_2,
    "CX-SEM-3": _ev_CX_SEM_3, "CX-SEM-4": _ev_CX_SEM_4,
    "CX-SEM-5": _ev_CX_SEM_5, "CX-SEM-6": _ev_CX_SEM_6,
    "CX-DRF-1": _ev_CX_DRF_1, "CX-DRF-2": _ev_CX_DRF_2,
    "CX-DRF-3": _ev_CX_DRF_3, "CX-DRF-4": _ev_CX_DRF_4,
    "CX-DRF-5": _ev_CX_DRF_5, "CX-DRF-6": _ev_CX_DRF_6,
    "R1": _ev_R1, "R2": _ev_R2, "R3": _ev_R3, "R4": _ev_R4,
    "R5": _ev_R5, "R6": _ev_R6, "R7": _ev_R7, "R8": _ev_R8,
    "R9": _ev_R9, "R10": _ev_R10, "R11": _ev_R11, "R12": _ev_R12,
    "R13": _ev_R13,
    "DC-DECODE": _ev_DC_DECODE, "DC-COMPILE": _ev_DC_COMPILE,
    "DC-AUTH-1": _ev_DC_AUTH_1, "DC-AUTH-2": _ev_DC_AUTH_2,
}

assert frozenset(_EVALUATORS) == frozenset(CHECKS), (
    "the evaluator set drifted from CHECKS: %s"
    % (frozenset(_EVALUATORS) ^ frozenset(CHECKS),))


# ---------------------------------------------------------------------------
# The public surface: evaluate(context) and aggregate(session)
# ---------------------------------------------------------------------------

def evaluate(context):
    """evaluate(context) -> the conformance report of one step.

    ``context`` carries what was actually observed — never content:

      * ``step`` — the step event (kind, desk, gate, addresses, zoom,
        operation, outcome, decoded references, compiled references);
        None for a static-only evaluation;
      * ``ledger`` — {path, records, count, head} of the ledger replay;
      * ``cell`` — the observed cell: {observed, arrangement, surfaces
        (parse results — references only), question_ref};
      * ``session`` — {lines: [...trail lines...]} for session-scope
        items (at aggregation);
      * ``sources_dir`` — where the held source files live (default
        ../sources).

    Every item is evaluated and re-emitted — no item is ever silently
    omitted; an item that cannot be decided reads INCONCLUSIVE with a
    reason, never clean.  The report's verdict: FAIL if any item FAILed,
    INCONCLUSIVE if any item is INCONCLUSIVE, else PASS.
    """
    ctx = dict(context or {})
    items = []
    counts = {"PASS": 0, "FAIL": 0, "INCONCLUSIVE": 0}
    for item_id in CHECK_ORDER:
        meta = CHECKS[item_id]
        result = _EVALUATORS[item_id](ctx)
        entry = {
            "id": item_id,
            "source": meta["source"],
            "citation": meta["citation"],
            "scope": meta["scope"],
            "verdict": result["verdict"],
            "evidence": result["evidence"],
        }
        if result["reason"] is not None:
            entry["reason"] = result["reason"]
        if meta["derived"]:
            entry["derived"] = True
        counts[result["verdict"]] += 1
        items.append(entry)
    if counts["FAIL"]:
        verdict = "FAIL"
    elif counts["INCONCLUSIVE"]:
        verdict = "INCONCLUSIVE"
    else:
        verdict = "PASS"
    return {"verdict": verdict, "counts": counts, "items": items}


def aggregate(context, reports=None):
    """aggregate(session) -> the session verdict.

    PASS only if every item reached PASS at least once and no item ever
    FAILed; FAIL if any item ever FAILed; otherwise INCONCLUSIVE, listing
    every item that never decided.  Silence is never a pass.  With no
    reports passed, the per-step reports are rebuilt from the trail lines
    alone — the session verdict is reconstructable from the TRAIL.
    Session-scope items are decided here, from the whole trail.
    """
    ctx = dict(context or {})
    if reports is None:
        lines = (ctx.get("session") or {}).get("lines") or []
        reports = [line.get("conformance") for line in lines
                   if isinstance(line, dict) and line.get("conformance")]
    reports = list(reports or [])
    finals = {}
    for report in reports:
        for entry in report.get("items", []):
            verdict = entry["verdict"]
            prior = finals.get(entry["id"])
            if prior == "FAIL" or verdict == "FAIL":
                finals[entry["id"]] = "FAIL"
            elif prior == "PASS" or verdict == "PASS":
                finals[entry["id"]] = "PASS"
            else:
                finals.setdefault(entry["id"], "INCONCLUSIVE")
    # session-scope items are decided here, from the whole trail
    for item_id in ("AD-DRF-3", "CX-DRF-3", "CX-DRF-5"):
        result = _EVALUATORS[item_id](context or {})
        if result["verdict"] == "FAIL":
            finals[item_id] = "FAIL"
        elif finals.get(item_id) is None:
            finals[item_id] = result["verdict"]
    for item_id in CHECK_ORDER:
        finals.setdefault(item_id, "INCONCLUSIVE")
    counts = {"PASS": 0, "FAIL": 0, "INCONCLUSIVE": 0}
    never_decided = []
    for item_id in CHECK_ORDER:
        verdict = finals[item_id]
        counts[verdict] += 1
        if verdict == "INCONCLUSIVE":
            never_decided.append(item_id)
    if counts["FAIL"]:
        verdict = "FAIL"
    elif counts["INCONCLUSIVE"]:
        verdict = "INCONCLUSIVE"
    else:
        verdict = "PASS"
    return {"verdict": verdict, "counts": counts,
            "never_decided": never_decided, "items": finals}


def build_live_context(ledger_path=None, sources_dir=None):
    """The live tier's context: replay the canon ledger (read-only —
    write_index=False so no sidecar is ever written), no step, no cell.
    Every cell-scope item then reads INCONCLUSIVE — the correct live
    verdict on a box where no desk is constituted (commission P4a §3.4)."""
    import fractal_ledger
    path = ledger_path or fractal_ledger.DEFAULT_LEDGER_PATH
    loaded = LedgerLoader(path).load(write_index=False)
    return {
        "step": None,
        "ledger": {"path": path, "records": loaded.records,
                   "count": loaded.count, "head": loaded.head},
        "cell": {"observed": False, "arrangement": None, "surfaces": {},
                 "question_ref": None},
        "session": {"lines": []},
        "sources_dir": sources_dir or _DEFAULT_SOURCES_DIR,
    }
