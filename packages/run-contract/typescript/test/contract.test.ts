// The TypeScript half of the contract, checked against the same fixture files
// the Python suite reads. A rule that holds on one side and not the other shows
// up here rather than at the process boundary in production.

import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";
import { ZodError } from "zod";

import { CONTRACT_VERSION } from "../src/index.js";
import {
  SemanticError,
  StrictRunReportSchema,
  parseRunReport,
  validateSemantics,
} from "../src/semantics.js";
import type { RunReport } from "../src/types.js";

const HERE = fileURLToPath(new URL(".", import.meta.url));
const FIXTURE_ROOT = join(HERE, "..", "..", "fixtures");

function names(kind: "valid" | "invalid"): string[] {
  return readdirSync(join(FIXTURE_ROOT, kind))
    .filter((f) => f.endsWith(".json"))
    .map((f) => f.replace(/\.json$/, ""))
    .sort();
}

function read(kind: "valid" | "invalid", name: string): unknown {
  return JSON.parse(readFileSync(join(FIXTURE_ROOT, kind, `${name}.json`), "utf-8"));
}

const VALID = names("valid");
const INVALID = names("invalid");

describe("fixture corpus", () => {
  it("is not empty", () => {
    // A green suite that validated nothing is the failure mode to avoid.
    expect(VALID.length).toBeGreaterThan(0);
    expect(INVALID.length).toBeGreaterThan(0);
  });

  it("declares the contract version the models were generated from", () => {
    expect(CONTRACT_VERSION).toBe("2.0.0");
  });
});

describe.each(VALID)("valid fixture %s", (name) => {
  it("parses and breaks no relational rule", () => {
    const report = parseRunReport(read("valid", name));
    expect(validateSemantics(report)).toEqual([]);
  });

  it("round-trips through JSON unchanged", () => {
    const once = parseRunReport(read("valid", name));
    const twice = parseRunReport(JSON.parse(JSON.stringify(once)));
    expect(twice).toEqual(once);
  });
});

describe.each(INVALID)("invalid fixture %s", (name) => {
  const raw = read("invalid", name) as {
    __expect__: { error: "schema" | "semantic"; contains: string };
    document: unknown;
  };

  it(`is rejected as a ${raw.__expect__.error} failure`, () => {
    if (raw.__expect__.error === "schema") {
      expect(() => StrictRunReportSchema.parse(raw.document)).toThrow(ZodError);
      return;
    }

    // A semantic case must survive schema validation, or it is not testing the
    // relational rule it claims to test.
    const report = StrictRunReportSchema.parse(raw.document) as unknown as RunReport;
    const violations = validateSemantics(report);
    expect(violations.length).toBeGreaterThan(0);
    expect(violations.map((v) => v.code).join(",")).toContain(raw.__expect__.contains);
    expect(() => parseRunReport(raw.document)).toThrow(SemanticError);
  });
});

describe("rules that JSON Schema cannot carry", () => {
  it("refuses a value on an unusable quantity", () => {
    const document = read("valid", "accepted_single_tree") as Record<string, any>;
    document.trees[0].quantities.dbh_cm = {
      value: 0.0,
      unit: "cm",
      status: "unusable",
      protocol: null,
      depends_on: [],
      unusable_reason: "protocol_not_met",
      basis: null,
      sensitivity: null,
    };
    expect(() => StrictRunReportSchema.parse(document)).toThrow(/must not carry a value/);
  });

  it("refuses a sensitivity range relabelled as a confidence interval", () => {
    const document = read("valid", "accepted_single_tree") as Record<string, any>;
    document.trees[0].quantities.co2eq_kg.sensitivity.basis =
      "95% confidence interval on the CO2e estimate";
    expect(() => StrictRunReportSchema.parse(document)).toThrow(/confidence interval/);
  });

  it("treats a counted zero as a real value", () => {
    const report = parseRunReport(read("valid", "accepted_single_tree"));
    // `quantities` is optional in the contract (it defaults to empty), so the
    // narrowing here is the type doing its job rather than noise to suppress.
    const excluded = report.quantities?.excluded_tree_count;
    expect(excluded).toBeDefined();
    expect(excluded?.value).toBe(0);
    expect(excluded?.status).toBe("accepted");
  });

  it("will not let a provisional input produce an accepted output", () => {
    const document = read("valid", "species_unknown_chave_fallback") as Record<string, any>;
    document.trees[0].quantities.co2eq_kg.status = "accepted";
    document.trees[0].quantities.co2eq_kg.protocol = {
      id: "treeq-geometry-v1",
      version: "1.0.0",
      criteria_uri: null,
    };
    const report = StrictRunReportSchema.parse(document) as unknown as RunReport;
    expect(validateSemantics(report).map((v) => v.code)).toEqual([
      "accepted_from_provisional",
    ]);
  });

  it("keeps the analysed hash distinct from the file hash", () => {
    const report = parseRunReport(read("valid", "accepted_single_tree"));
    expect(report.provenance.analysed_points_sha256).not.toBe(
      report.request.source.file_sha256,
    );
    expect(report.provenance.n_analysed_points).toBeLessThan(
      report.provenance.n_source_points,
    );
  });
});
