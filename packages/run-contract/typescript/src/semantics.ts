// HAND-WRITTEN. This is the half of the contract that JSON Schema cannot carry,
// so it is not generated and will not be overwritten by
// tools/generate_contract.py.
//
// Two kinds of rule live here:
//
//   1. Structural rules that are pydantic `model_validator`s in Python. They
//      constrain one object across several of its own fields - "an unusable
//      quantity carries no value" - and JSON Schema has no way to say that, so
//      the generated Zod schemas do not enforce them. Without this file the
//      TypeScript side would accept documents the Python side refuses.
//   2. Relational rules over the dependency graph, mirroring semantics.py.
//
// The shared fixture corpus in ../../fixtures is what proves this file and
// semantics.py agree: both suites read the same files and must accept and
// reject the same ones for the same stated reason.

import { z } from "zod";

import { RunReportSchema } from "./zod.js";
import type { Quantity, RunReport } from "./types.js";

/** Dependency names with this prefix resolve against plot-level quantities. */
export const PLOT_PREFIX = "plot.";

export const SUPPORTED_CONTRACT_VERSIONS: ReadonlySet<string> = new Set(["2.0.0"]);

/** Reasons an unusable dependency can account for. Mirrors _DEPENDENCY_REASONS. */
const DEPENDENCY_REASONS: ReadonlySet<string> = new Set([
  "dependency_missing",
  "dependency_refused",
  "dependency_unsupported",
  "dependency_unusable",
  // A whole-run failure is a cause, not a symptom: when the run died every
  // quantity is unusable for that reason, including those whose dependencies
  // collapsed with it.
  "execution_failed",
]);

/** Claims a sensitivity range may not make about itself. */
const INTERVAL_CLAIMS = [
  "confidence interval",
  "95% ci",
  "95%ci",
  "credible interval",
];

export interface SemanticViolation {
  readonly code: string;
  readonly path: string;
  readonly message: string;
}

function addIssue(ctx: z.RefinementCtx, path: (string | number)[], message: string): void {
  ctx.addIssue({ code: z.ZodIssueCode.custom, path, message });
}

function refineQuantity(
  quantity: Quantity,
  ctx: z.RefinementCtx,
  path: (string | number)[],
): void {
  const value = quantity.value ?? null;
  if (quantity.status === "unusable") {
    if (value !== null) {
      addIssue(
        ctx,
        [...path, "value"],
        "an unusable quantity must not carry a value; a number nobody may use still gets summed if it is present",
      );
    }
    if (!quantity.unusable_reason) {
      addIssue(
        ctx,
        [...path, "unusable_reason"],
        "an unusable quantity must say why it is unusable",
      );
    }
    if (quantity.sensitivity) {
      addIssue(
        ctx,
        [...path, "sensitivity"],
        "an unusable quantity has nothing to be sensitive to",
      );
    }
  } else {
    if (value === null) {
      addIssue(
        ctx,
        [...path, "value"],
        `a ${quantity.status} quantity must carry a value; use status=unusable when there is no number`,
      );
    }
    if (quantity.unusable_reason) {
      addIssue(
        ctx,
        [...path, "unusable_reason"],
        `a ${quantity.status} quantity must not carry an unusable_reason`,
      );
    }
  }

  if (quantity.status === "accepted" && !quantity.protocol) {
    addIssue(
      ctx,
      [...path, "protocol"],
      "an accepted quantity must name the protocol whose criteria it met; 'accepted' on its own is not a checkable claim",
    );
  }

  const sensitivity = quantity.sensitivity;
  if (sensitivity) {
    if (sensitivity.low > sensitivity.high) {
      addIssue(
        ctx,
        [...path, "sensitivity"],
        `sensitivity low ${sensitivity.low} exceeds high ${sensitivity.high}`,
      );
    }
    const basis = sensitivity.basis.toLowerCase();
    for (const claim of INTERVAL_CLAIMS) {
      if (basis.includes(claim)) {
        addIssue(
          ctx,
          [...path, "sensitivity", "basis"],
          `a sensitivity range may not be described as a '${claim}'; it varies an assumption and carries no sampling distribution`,
        );
      }
    }
  }
}

/**
 * RunReport with every structural rule the Python models enforce.
 *
 * Use this rather than the generated `RunReportSchema`: on its own that schema
 * describes the shape and nothing about whether the shape means anything.
 */
export const StrictRunReportSchema = RunReportSchema.superRefine((report, ctx) => {
  const document = report as unknown as RunReport;

  for (const version of [document.contract_version, document.request?.contract_version]) {
    if (version !== undefined && !SUPPORTED_CONTRACT_VERSIONS.has(version)) {
      addIssue(
        ctx,
        ["contract_version"],
        `unsupported contract_version '${version}'; this build reads ${[...SUPPORTED_CONTRACT_VERSIONS].join(", ")}`,
      );
    }
  }
  if (
    document.request !== undefined &&
    document.request.contract_version !== document.contract_version
  ) {
    addIssue(
      ctx,
      ["contract_version"],
      `report contract_version '${document.contract_version}' does not match request contract_version '${document.request.contract_version}'`,
    );
  }

  const provenance = document.provenance;
  if (provenance && provenance.n_analysed_points > provenance.n_source_points) {
    addIssue(
      ctx,
      ["provenance", "n_analysed_points"],
      `n_analysed_points=${provenance.n_analysed_points} exceeds n_source_points=${provenance.n_source_points}; a thinned cloud cannot be larger than the file it came from`,
    );
  }

  const execution = document.execution;
  if (execution) {
    const failed = execution.status === "failed";
    if (failed && !execution.error_code) {
      addIssue(ctx, ["execution", "error_code"], "a failed run must carry an error_code");
    }
    if (!failed && execution.error_code) {
      addIssue(
        ctx,
        ["execution", "error_code"],
        `execution status ${execution.status} must not carry an error_code; use status=failed or status=partial`,
      );
    }
  }

  for (const [name, quantity] of Object.entries(document.quantities ?? {})) {
    refineQuantity(quantity, ctx, ["quantities", name]);
  }
  (document.trees ?? []).forEach((tree, index) => {
    for (const [name, quantity] of Object.entries(tree.quantities ?? {})) {
      refineQuantity(quantity, ctx, ["trees", index, "quantities", name]);
    }
  });
});

function resolve(
  dep: string,
  scope: Readonly<Record<string, Quantity>>,
  plot: Readonly<Record<string, Quantity>>,
): Quantity | undefined {
  return dep.startsWith(PLOT_PREFIX) ? plot[dep.slice(PLOT_PREFIX.length)] : scope[dep];
}

function checkScope(
  scope: Readonly<Record<string, Quantity>>,
  plot: Readonly<Record<string, Quantity>>,
  pathPrefix: string,
  violations: SemanticViolation[],
): void {
  for (const [name, quantity] of Object.entries(scope)) {
    const path = `${pathPrefix}${name}`;
    for (const dep of quantity.depends_on ?? []) {
      const resolved = resolve(dep, scope, plot);
      if (!resolved) {
        violations.push({
          code: "unresolved_dependency",
          path,
          message: `depends on '${dep}', which no quantity in scope provides; a dependency that cannot be located cannot be checked`,
        });
        continue;
      }

      if (resolved.status === "unusable") {
        if (quantity.status !== "unusable") {
          violations.push({
            code: "usable_from_unusable",
            path,
            message: `is ${quantity.status} but depends on '${dep}', which is unusable (${resolved.unusable_reason ?? "no reason"}); a quantity derived from something nobody may use is not usable either`,
          });
        } else if (!DEPENDENCY_REASONS.has(quantity.unusable_reason ?? "")) {
          violations.push({
            code: "wrong_unusable_reason",
            path,
            message: `is unusable because of dependency '${dep}' but reports ${quantity.unusable_reason ?? "nothing"}; the reason must name the dependency failure so a reader can follow it upstream`,
          });
        }
      } else if (resolved.status === "provisional" && quantity.status === "accepted") {
        violations.push({
          code: "accepted_from_provisional",
          path,
          message: `is accepted but depends on '${dep}', which is provisional; acceptance cannot be created downstream of an input that does not have it`,
        });
      }
    }
  }
}

function detectCycles(
  scope: Readonly<Record<string, Quantity>>,
  pathPrefix: string,
  violations: SemanticViolation[],
): void {
  const WHITE = 0;
  const GREY = 1;
  const BLACK = 2;
  const colour = new Map<string, number>(Object.keys(scope).map((name) => [name, WHITE]));

  const visit = (name: string, trail: readonly string[]): void => {
    if (colour.get(name) === BLACK) {
      return;
    }
    if (colour.get(name) === GREY) {
      violations.push({
        code: "dependency_cycle",
        path: `${pathPrefix}${name}`,
        message: `is derived from itself via ${[...trail, name].join(" -> ")}; a cycle has no upstream to inherit status from`,
      });
      return;
    }
    colour.set(name, GREY);
    for (const dep of scope[name]?.depends_on ?? []) {
      // Only same-scope edges can close a cycle; a `plot.` edge leaves this
      // scope and is checked when the plot scope is walked.
      if (!dep.startsWith(PLOT_PREFIX) && dep in scope) {
        visit(dep, [...trail, name]);
      }
    }
    colour.set(name, BLACK);
  };

  for (const name of Object.keys(scope)) {
    visit(name, []);
  }
}

/** Return every relational rule this report breaks, in document order. */
export function validateSemantics(report: RunReport): SemanticViolation[] {
  const violations: SemanticViolation[] = [];
  const plot = report.quantities ?? {};

  detectCycles(plot, "quantities.", violations);
  checkScope(plot, plot, "quantities.", violations);

  for (const tree of report.trees ?? []) {
    const prefix = `trees[${tree.tree_id}].quantities.`;
    detectCycles(tree.quantities ?? {}, prefix, violations);
    checkScope(tree.quantities ?? {}, plot, prefix, violations);
  }

  if (report.execution?.status === "failed") {
    const scopes: [Readonly<Record<string, Quantity>>, string][] = [[plot, "quantities."]];
    for (const tree of report.trees ?? []) {
      scopes.push([tree.quantities ?? {}, `trees[${tree.tree_id}].quantities.`]);
    }
    for (const [scope, prefix] of scopes) {
      for (const [name, quantity] of Object.entries(scope)) {
        if (quantity.status !== "unusable") {
          violations.push({
            code: "accepted_after_failure",
            path: `${prefix}${name}`,
            message: `is ${quantity.status} but the run's execution status is failed; a run that did not finish has not established any number`,
          });
        }
      }
    }
  }
  return violations;
}

export class SemanticError extends Error {
  readonly violations: readonly SemanticViolation[];

  constructor(violations: readonly SemanticViolation[]) {
    const joined = violations.map((v) => `${v.path}: [${v.code}] ${v.message}`).join("\n  ");
    super(`${violations.length} semantic violation(s):\n  ${joined}`);
    this.name = "SemanticError";
    this.violations = violations;
  }
}

/** Parse a document and apply every rule. Throws on the first kind that fails. */
export function parseRunReport(document: unknown): RunReport {
  const report = StrictRunReportSchema.parse(document) as unknown as RunReport;
  const violations = validateSemantics(report);
  if (violations.length > 0) {
    throw new SemanticError(violations);
  }
  return report;
}
