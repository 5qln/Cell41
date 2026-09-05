// probe.mjs — the bindings round's executable twin of the pi extension.
//
// This probe IS the binding's runtime: it imports the same cellctl.mjs
// module the pi extension registers (table + argv builder + one spawn
// of the seam binary + result shaping), so the code the tests execute
// is the code the extension runs — no transliteration, no duplication
// (C3, lens 2).  It lets the author's suite (and the verifier) drive
// one tool invocation from a fresh process (lens 5's second process).
//
// usage:
//   node probe.mjs <tool> '<params-json>' [--bin PATH] [--argv-only]
//     --argv-only : print the built argv (JSON array) instead of running
//   CELLCTL_BIN env — the seam binary (default: the R07 attested cellctl;
//     point it at fixtures/fake_cellctl.py for the fixture world)
//
// Exit 0 when the tool result is not an error, 1 otherwise; the result
// is printed as JSON on stdout.  Deterministic: no wall-clock, no
// network — the ONLY subprocess is the seam binary (K1).

import { buildArgv, invokeTool, rowFor } from "../pi-cell/src/cellctl.mjs";

const args = process.argv.slice(2);
const usage =
  "usage: node probe.mjs <tool> '<params-json>' [--bin PATH] [--argv-only]";

if (args.length < 2) {
  console.error(usage);
  process.exit(2);
}

const tool = args[0];
let paramsJson = args[1];
let bin = null;
let argvOnly = false;
for (let i = 2; i < args.length; i += 1) {
  if (args[i] === "--bin" && i + 1 < args.length) {
    bin = args[i + 1];
    i += 1;
  } else if (args[i] === "--argv-only") {
    argvOnly = true;
  } else {
    console.error(usage);
    process.exit(2);
  }
}

let params = {};
try {
  params = JSON.parse(paramsJson);
} catch (error) {
  console.error("probe: params are not JSON: " + String(error));
  process.exit(2);
}

const row = rowFor(tool);
if (row === null) {
  console.error("probe: no such tool: " + tool);
  process.exit(2);
}

const argv = buildArgv(row, params);
if (argvOnly) {
  process.stdout.write(JSON.stringify(argv) + "\n");
  process.exit(0);
}

const result = await invokeTool(tool, params, { bin: bin || undefined });
process.stdout.write(JSON.stringify(result) + "\n");
process.exit(result.isError ? 1 : 0);
