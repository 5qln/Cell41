// index.ts — the pi extension entry point (the conductor binding).
//
// Registers the thirteen cellctl subcommands as pi slash tools: each
// stud is one thin shell to the seam binary, built from the declared
// tool table (src/tool-table.json — DATA) and executed by the single
// runtime in src/cellctl.mjs.  This file is registration glue only:
// it generates TypeBox parameter schemas from the table rows and
// forwards every invocation to the shared runtime — no orchestration
// sequence, no socket code, no record-writing, no engine import (C1,
// C2, C7, C8).  The orchestration method stays data the engine reads
// (the brick: scenario + spec + soft config), never code here.
//
// Conduction is one line: conduction = call `conduct` — the conductor
// never re-derives the walk (SCOPE §0, the governing line).

import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";
import { StringEnum } from "@earendil-works/pi-ai";
import { invokeTool, loadTable } from "./src/cellctl.mjs";

// -- the TypeBox schema for one table row (generated, never hand-set) ------
//
// TypeBox 1.x (what pi ships) has no fluent .description()/chainable
// modifiers — descriptions are constructor options.  Each builder takes
// the options object (or undefined) and passes it straight through, so
// a description is declared where the type is declared.

const KIND_BUILDERS = {
  string: (opts) => Type.String(opts),
  integer: (opts) => Type.Integer(opts),
  boolean: (opts) => Type.Boolean(opts),
};

function schemaFor(row) {
  const fields = {};
  for (const spec of row.params || []) {
    const opts = spec.description ? { description: spec.description } : undefined;
    let schema;
    if (spec.kind === "enum") {
      schema = StringEnum(spec.values, opts);
    } else {
      schema = KIND_BUILDERS[spec.kind](opts);
    }
    fields[spec.name] =
      spec.optional === false ? schema : Type.Optional(schema);
  }
  return Type.Object(fields);
}

// -- registration -----------------------------------------------------------

export default function (pi: ExtensionAPI): void {
  const table = loadTable();
  for (const row of table.tools || []) {
    pi.registerTool({
      name: row.name,
      label: row.label || row.name,
      description: row.description,
      promptSnippet: row.promptSnippet,
      promptGuidelines: row.promptGuidelines || [],
      parameters: schemaFor(row),
      async execute(_toolCallId, params, _signal, _onUpdate, _ctx) {
        // one stud = one cellctl call: the shared runtime spawns the
        // seam binary exactly once and forwards its bytes untouched.
        return await invokeTool(row.name, params || {});
      },
    });
  }
}
