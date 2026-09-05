// cellctl.mjs — the conductor binding's single executable path.
//
// This module is the WHOLE runtime of the binding: it loads the declared
// tool table (DATA — src/tool-table.json), builds argv from tool params
// byte-verbatim, spawns the seam binary exactly once per invocation
// (shell:false — no interpolation, no shell), and shapes the result for
// the pi tool contract.  index.ts adds only the pi registration glue on
// top; the fixture probe imports this same module, so the code the tests
// execute IS the code the extension runs (C3, lens 2).
//
// Structural facts this file obeys (C1/C2/C5/C7/C8):
//   * the ONLY subprocess anywhere in the binding is the seam binary
//     (CELLCTL_BIN, default: the R07 attested cellctl) — one call per
//     tool invocation, never a sequence;
//   * no socket code, no record-writing, no ledger/trail logic, no
//     engine import — the seam carries all of that;
//   * the orchestration method lives in the brick data the engine reads,
//     never here: this file knows no scenario path, no desk order;
//   * argv items ride as separate strings byte-for-byte (lens 4: the
//     ∞0′ → ‖ needle survives untouched; nothing is re-encoded);
//   * exit 0 = the declared success status; any other exit is returned
//     as an error carrying the raw report — INCONCLUSIVE never reads
//     clean (C6); an absent binary reads the same honest shape.
//
// Deterministic and stdlib-only: no network, no wall-clock in logic.
// The declared config surface is env-only: CELLCTL_BIN (the seam) and
// HERDR_BIN (declared for parity with the sibling package's env-only
// pattern; read by NO code path here — this package never shells to
// the platform CLI, so no code uses it; it is carried as declared
// config surface, never a hidden authority).

import { spawn } from "node:child_process";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));

// -- env-only config (the declared surface) -------------------------------

export const DEFAULT_CELLCTL_BIN =
  "/home/deploy/the-cell/rounds/R07-integration/authored/cellctl";

/** The seam binary path: CELLCTL_BIN env or the declared default. */
export function resolveCellctlBin() {
  return process.env.CELLCTL_BIN || DEFAULT_CELLCTL_BIN;
}

/** HERDR_BIN — declared, unused: see the module header. */
export function herdrBin() {
  return process.env.HERDR_BIN || "";
}

// -- the data table --------------------------------------------------------

let cachedTable = null;

/** Load src/tool-table.json (the declared stud surface — data, one
 * place to change; a new stud = a new row, zero re-authoring). */
export function loadTable() {
  if (cachedTable === null) {
    cachedTable = JSON.parse(
      readFileSync(join(HERE, "tool-table.json"), "utf8"),
    );
  }
  return cachedTable;
}

// -- argv building (byte-exact, deterministic order) -----------------------

/**
 * Build the argv for one tool invocation: the subcommand, then positional
 * params in table order, then flag params in table order.  Values ride as
 * separate argv items — byte-verbatim, never shell-interpolated (lens 4).
 * Booleans add their flag only when true; integers are stringified.
 */
export function buildArgv(row, params) {
  const argv = [row.subcommand];
  for (const spec of row.params || []) {
    if (spec.optional === false || (params && params[spec.name] !== undefined)) {
      const value = params ? params[spec.name] : undefined;
      if (spec.kind === "boolean") {
        if (value === true) argv.push(spec.flag);
      } else if (spec.flag) {
        if (value !== undefined && value !== null) {
          argv.push(spec.flag, String(value));
        }
      } else if (value !== undefined && value !== null) {
        argv.push(String(value));
      }
    }
  }
  return argv;
}

/** The table row for a tool name, or null. */
export function rowFor(name) {
  const table = loadTable();
  return (table.tools || []).find((row) => row.name === name) || null;
}

// -- the one spawn ---------------------------------------------------------

/**
 * Run the seam binary once with the given argv.  Never throws: every
 * failure path resolves to {ok:false, reason} — an absent binary, a
 * refused spawn, a non-zero exit, all read INCONCLUSIVE, never clean,
 * never a substituted value (C6).
 */
export function runCellctl(argv, opts = {}) {
  const bin = opts.bin || resolveCellctlBin();
  return new Promise((resolve) => {
    let child;
    try {
      child = spawn(bin, argv, { shell: false, env: process.env });
    } catch (error) {
      resolve({
        ok: false,
        exitCode: null,
        stdout: "",
        stderr: "",
        reason:
          "cellctl cannot be spawned at " + JSON.stringify(bin) +
          " (" + String(error) + ") — INCONCLUSIVE, never a stand-in",
      });
      return;
    }
    let stdout = "";
    let stderr = "";
    let settled = false;
    const finish = (result) => {
      if (settled) return;
      settled = true;
      resolve(result);
    };
    child.stdout?.on("data", (chunk) => {
      stdout += chunk;
    });
    child.stderr?.on("data", (chunk) => {
      stderr += chunk;
    });
    child.on("error", (error) => {
      const code = error && error.code;
      finish({
        ok: false,
        exitCode: null,
        stdout,
        stderr,
        reason:
          "cellctl is absent or refused at " + JSON.stringify(bin) +
          (code ? " (" + String(code) + ")" : "") +
          " — INCONCLUSIVE, never a stand-in",
      });
    });
    child.on("close", (exitCode) => {
      finish({
        ok: exitCode === 0,
        exitCode,
        stdout,
        stderr,
        reason:
          exitCode === 0
            ? undefined
            : "cellctl exited " + String(exitCode) +
              " — the report's status is carried verbatim above; " +
              "INCONCLUSIVE never reads clean",
      });
    });
  });
}

/** The declared result shape: the pi tool contract on top of one run.
 * A non-zero exit with a report forwards the report verbatim; a failure
 * with no report carries the INCONCLUSIVE reason as the content — a
 * blind spot never reads clean and never reads empty (C6). */
export function toolResult(name, params, run, argv) {
  const report = run.stdout;
  const failed = !run.ok;
  const text = report || (run.reason ? run.reason : "");
  return {
    content: [{ type: "text", text }],
    details: {
      tool: name,
      argv,
      exitCode: run.exitCode,
      cellctlBin: resolveCellctlBin(),
      stderr: run.stderr || undefined,
      reason: run.reason,
    },
    isError: failed,
  };
}

/** One full tool invocation: table lookup + argv + spawn + shape. */
export async function invokeTool(name, params, opts = {}) {
  const row = rowFor(name);
  if (row === null) {
    return {
      content: [{ type: "text", text: "no such tool: " + String(name) }],
      details: { tool: name },
      isError: true,
    };
  }
  const argv = buildArgv(row, params);
  const run = await runCellctl(argv, opts);
  return toolResult(name, params, run, argv);
}
