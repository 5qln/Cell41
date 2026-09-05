---
name: scope-ignited-memory
description: Build a 5QLN scope-ignited formation trail from Hindsight canon; derive requirements, cite authority, and append human-gated phase events.
---

# Scope-Ignited Memory

Use when the human asks about a formation trail, ledger, scope ignition, memory field, question-field, or developing dsh from the 5QLN language-field.

## Boundary

- `canon` is source-only. Never write to it.
- Do not generate doctrine. Derive requirements only from cited canon context plus the human's live words.
- The human originates X and attests resonance. Machine output is K: structure, citations, contrasts, and candidate requirements.
- A trail event is appended only after an explicit human signal.
- No V event without a return question.

## Command surface

The bridge is installed at:

```bash
python3 /home/deploy/ops/scope_memory.py
```

### 1. Recall the scoped canon field

```bash
python3 /home/deploy/ops/scope_memory.py context \
  --scope "<scope>" \
  --question "<the human's live question or current input>"
```

For long input, write it to a temp file and use `--input-file`.

The JSON result contains authority-tiered packs: ground-truth, formation-trail, core-context, implementation-context, vision-context. Raw exploration is excluded unless explicitly requested with `--include-raw`.

### 2. Present a compact context pack

Use this shape:

```text
SCOPE: <scope>
X: <the live question, stated as a question>

CANON CONTEXT:
- [authority] <title> — <document_id> — <one-line relevance>

DERIVED REQUIREMENTS (machine-structured, not doctrine):
1. ...
2. ...

ATTESTATION NEEDED:
<one direct question for the human>
```

Do not paste long excerpts unless asked. Cite `document_id`, `source_url`, or `source_vault_path`.

### 3. Append a trail event only after human validation

```bash
python3 /home/deploy/ops/scope_memory.py append \
  --scope "<scope>" \
  --phase S|G|Q|P|V|NOTE \
  --source human|machine|system \
  --signal "<exact human signal>" \
  --content "<what is being recorded>"
```

For V:

```bash
python3 /home/deploy/ops/scope_memory.py append \
  --scope "<scope>" \
  --phase V \
  --source human \
  --signal "<exact human signal>" \
  --content "<B'' artifact>" \
  --return-question "<∞0′ return question>"
```

### 4. Read the scoped trail

```bash
python3 /home/deploy/ops/scope_memory.py snapshot --scope "<scope>" --limit 20
```

## Interpretation rule

The whole field is gravity; the scoped cell is working memory. Do not flood the local scope with unrelated canon. Retrieve only what supports the live question, then return to the human for attestation.
