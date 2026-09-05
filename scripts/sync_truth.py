"""Generate and verify user-facing truth from one reviewed evidence manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

try:  # Supports both ``python scripts/sync_truth.py`` and package imports in tests.
    from scripts.review_pointnet_evidence import validate_imported_independent
except ModuleNotFoundError:  # pragma: no cover - exercised by the documented CLI.
    from review_pointnet_evidence import validate_imported_independent

TRUTH_START = "<!-- TREEQ_TRUTH_START -->"
TRUTH_END = "<!-- TREEQ_TRUTH_END -->"
VALID_STATUSES = {"Implemented", "Experimental", "Stub", "Planned"}
CONTROLLED_DOCS = (
    Path("docs/PROJECT_SPEC.md"),
    Path("docs/ml/PIPELINE.md"),
    Path("docs/ml/WOODLEAF_RESULTS.md"),
)

EXPECTED_WAN = {
    "wood_iou": 0.418,
    "leaf_iou": 0.808,
    "mean_iou": 0.613,
    "accuracy": 0.831,
}
PROMOTION_POLICY = (
    "Promote only after verified checkpoint and training provenance, a reproducible "
    "independent real-data evaluation, improved Wood IoU, non-regressing "
    "DBH/height/volume errors, and a candidate measurable-tree count at least as high "
    "as the baseline."
)


def _require_keys(value: dict[str, Any], keys: set[str], label: str) -> None:
    missing = sorted(keys - value.keys())
    if missing:
        raise ValueError(f"{label} missing required keys: {missing}")


def _require_sha256(value: Any, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{label} must be a 64-character SHA-256")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{label} must be hexadecimal") from exc


#: The Demol figures this manifest publishes, and which
#: services/ml/scripts/derive_demol_evidence.py derives.
DEMOL_PUBLISHED_FIELDS = (
    "trees",
    "dbh_mae_cm",
    "dbh_rmse_cm",
    "dbh_bias_cm",
    "dbh_mape_pct",
    "dbh_within_10_pct",
    "dbh_worst_pct",
    "dbh_worst_abs_cm",
    "height_mae_m",
    "height_rmse_m",
    "height_bias_m",
    "height_mape_pct",
    "height_within_10_pct",
    "volume_mae_m3",
    "volume_mape_pct",
    "volume_bias_m3",
    "volume_within_10_pct",
    "volume_worst_pct",
)

DEMOL_RESULT_PATH = "docs/evidence/demol_65/result.json"

#: The Cameroon figures this manifest publishes, mapped to the key each one has
#: in the artefact that derives them.
#:
#: Almost all of them are named the same on both sides. `trees` is the one that
#: is not: the manifest names the cohort the way the other validation blocks
#: name theirs, and `services/ml/scripts/derive_cameroon_evidence.py` writes it
#: as `cohort_size`. Mapping rather than assuming equality is what lets the
#: comparison below cover every published number instead of the subset whose
#: names happen to line up.
CAMEROON_PUBLISHED_FIELDS = {
    "trees": "cohort_size",
    "trees_measured": "trees_measured",
    "trees_excluded": "trees_excluded",
    "dbh_gate_applied_mae_cm": "dbh_gate_applied_mae_cm",
    "gate_passed_trees": "gate_passed_trees",
    "gate_refused_trees": "gate_refused_trees",
    "gate_min_dbh_fit_quality": "gate_min_dbh_fit_quality",
    "dbh_mae_cm_small_stems": "dbh_mae_cm_small_stems",
    "dbh_mae_cm_small_stems_n": "dbh_mae_cm_small_stems_n",
    "dbh_mae_cm": "dbh_mae_cm",
    "dbh_bias_cm": "dbh_bias_cm",
    "dbh_mae_vs_reference_cm": "dbh_mae_vs_reference_cm",
    "dbh_bias_vs_reference_cm": "dbh_bias_vs_reference_cm",
    "height_mae_m": "height_mae_m",
    "height_bias_m": "height_bias_m",
    "volume_mape_pct": "volume_mape_pct",
    "volume_vs_reference_qsm_mape_pct": "volume_vs_reference_qsm_mape_pct",
    "chave_route_a_ape_pct_median": "chave_route_a_ape_pct_median",
    "chave_route_b_ape_pct_median": "chave_route_b_ape_pct_median",
    "chave_measurement_share_pct_median": "chave_measurement_share_pct_median",
    "tver_route_a_ape_pct_median": "tver_route_a_ape_pct_median",
    "tver_route_b_ape_pct_median": "tver_route_b_ape_pct_median",
    "tver_measurement_share_pct_median": "tver_measurement_share_pct_median",
    "chave_vs_tver_route_b_chave_closer_count": "chave_vs_tver_route_b_chave_closer_count",
    "chave_vs_tver_route_b_tver_closer_count": "chave_vs_tver_route_b_tver_closer_count",
}

CAMEROON_RESULT_PATH = "docs/evidence/cameroon_61/result.json"

#: Documents that quote accuracy figures in hand-written prose.
#:
#: The TREEQ_TRUTH block is regenerated from the manifest, so the numbers inside
#: it are correct by construction. Everything outside it is typed by hand and
#: drifts. docs/PROJECT_SPEC.md carried both at once: the derived 0.898318 at
#: line 16 and the superseded 1.1673846154 at line 234.
#:
#: docs/DOCUMENT_STATUS.md belongs here for a sharper reason than the other
#: four: it is the document that declares which documents are current truth,
#: and its own "Non-negotiable truth snapshot" section quoted the superseded
#: Demol figures under that heading. The file that defines what counts as
#: authoritative is not exempt from being checked against the manifest --
#: if anything it is the one place this gate can least afford to miss.
FIGURE_PROSE_DOCS = (
    Path("README.md"),
    Path("AGENTS.md"),
    Path("docs/PROJECT_SPEC.md"),
    Path("docs/ml/PIPELINE.md"),
    Path("docs/DOCUMENT_STATUS.md"),
)

#: A metric name followed by its value, however the document spaces or marks it up.
_FIGURE_PATTERN = re.compile(
    r"(DBH MAE|Height MAE|Volume MAPE)[^0-9\n]{0,24}([0-9]+\.[0-9]+)"
)


def published_figure_values(manifest: dict[str, Any]) -> frozenset[float]:
    """Every DBH MAE, Height MAE and Volume MAPE the manifest records.

    Every evaluation is included. The Demol block, the independent PointNet
    review and the Cameroon block measure different cohorts, or the same cohort
    by different routes, and legitimately differ; all three are quoted in prose,
    so a figure matching any of them is current.

    The Cameroon block contributes four DBH figures rather than one, because
    that cohort has no single honest answer: the shipped gate refuses 33 of its
    60 measurable trees, the tape is not always taken at 1.30 m above about
    50 cm, and the archive publishes its own TLS measurement to compare against.
    Each of those is a different question, so each is quotable and each has to
    be recognised here. See docs/ml/CAMEROON_EVIDENCE_CHAIN.md section 2b.
    """
    demol = manifest["validation"]["demol_65"]
    values = {
        float(demol["dbh_mae_cm"]),
        float(demol["height_mae_m"]),
        float(demol["volume_mape_pct"]),
    }
    independent = manifest["validation"].get("pointnet_independent")
    if independent is not None:
        for side in ("baseline", "candidate"):
            block = independent[side]
            values |= {
                float(block["dbh_mae_cm"]),
                float(block["height_mae_m"]),
                float(block["volume_mape_pct"]),
            }
    cameroon = manifest["validation"].get("cameroon_61")
    if cameroon is not None:
        for field in (
            "dbh_gate_applied_mae_cm",
            "dbh_mae_cm_small_stems",
            "dbh_mae_cm",
            "dbh_mae_vs_reference_cm",
            "height_mae_m",
            "volume_mape_pct",
        ):
            if field in cameroon:
                values.add(float(cameroon[field]))
    return frozenset(values)


def stale_figures_in_text(
    text: str, manifest: dict[str, Any]
) -> tuple[tuple[int, str, str], ...]:
    """Accuracy figures in `text` that no manifest field records.

    Args:
        text: a document's full contents.
        manifest: the parsed core demo manifest.

    Returns:
        `(line_number, metric_name, value_as_written)` for each offending figure,
        empty when every figure quoted is one the manifest holds.
    """
    allowed = published_figure_values(manifest)
    found: list[tuple[int, str, str]] = []
    for lineno, line in enumerate(text.splitlines(), 1):
        for label, raw in _FIGURE_PATTERN.findall(line):
            if float(raw) not in allowed:
                found.append((lineno, label, raw))
    return tuple(found)


#: An evidence entry that names a file rather than a hash or a sentence.
#:
#: The evidence column mixes both - "docs/evidence/x.json; SHA-256 5892..." - so
#: only entries shaped like a repository path are resolved.
_EVIDENCE_FILE = re.compile(r"^[A-Za-z0-9_./-]+\.(?:py|ts|tsx|json|csv|md|dart)$")


def missing_evidence_paths(
    repo_root: str | Path, capabilities: list[dict[str, Any]]
) -> tuple[tuple[str, str], ...]:
    """Capability evidence files that are not in the checkout.

    A capability is a claim, and the evidence column is where the claim is meant
    to be checkable. When the file is gone the row is an assertion with nothing
    behind it, which is how a mobile capture flow stayed in the matrix for ten
    days after `8ce6021` deleted the application.

    Args:
        repo_root: the repository checkout.
        capabilities: the manifest's `capabilities` list.

    Returns:
        `(capability_name, missing_path)` pairs, empty when every cited file
        exists.
    """
    root = Path(repo_root)
    missing: list[tuple[str, str]] = []
    for capability in capabilities:
        for entry in str(capability.get("evidence", "")).split(";"):
            candidate = entry.strip()
            if _EVIDENCE_FILE.match(candidate) and not (root / candidate).exists():
                missing.append((str(capability.get("name", "")), candidate))
    return tuple(missing)


def validate_demol(block: Any, *, repo_root: str | Path | None) -> None:
    """Check the published Demol figures against the artefact that derived them.

    This used to read ``if block.get("dbh_mae_cm") != 1.1673846154: raise``. A
    literal in this file, compared against a copy of itself in the manifest --
    it could only catch someone editing one of the two, and it certified as
    correct a number that no evaluation had ever produced. The block was
    averaged from a per-tree table already rounded for display, which is visible
    in the arithmetic: 1.1673846154 x 65 is exactly 75.88.

    Now the manifest has to agree, field for field, with a committed artefact
    that `derive_demol_evidence.py --check` can re-derive from the cohort. The
    number is still guarded against a stray edit, and it is now also guarded
    against being wrong.
    """
    if not isinstance(block, dict):
        raise ValueError("validation.demol_65 must be an object")
    _require_keys(
        block,
        {"result_path", "result_sha256", *DEMOL_PUBLISHED_FIELDS},
        "validation.demol_65",
    )
    if block["result_path"] != DEMOL_RESULT_PATH:
        raise ValueError(f"validation.demol_65 result_path must be {DEMOL_RESULT_PATH}")
    _require_sha256(block["result_sha256"], "validation.demol_65 result_sha256")

    if repo_root is None:
        # Structure is checked above without touching the filesystem. sync()
        # always supplies repo_root, so the comparison below runs on every
        # `sync_truth.py --check`, which is what CI runs.
        return

    result_file = Path(repo_root) / DEMOL_RESULT_PATH
    if not result_file.is_file():
        raise ValueError(f"{DEMOL_RESULT_PATH} is missing; the published figures have no source")
    raw = result_file.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != block["result_sha256"]:
        raise ValueError(
            f"{DEMOL_RESULT_PATH} has changed since it was reviewed "
            f"(recorded {block['result_sha256']}, found {digest})"
        )

    metrics = json.loads(raw.decode("utf-8")).get("metrics")
    if not isinstance(metrics, dict):
        raise ValueError(f"{DEMOL_RESULT_PATH} has no metrics block")
    disagreeing = sorted(
        field for field in DEMOL_PUBLISHED_FIELDS if block[field] != metrics.get(field)
    )
    if disagreeing:
        raise ValueError(
            "validation.demol_65 disagrees with the derived result for "
            f"{disagreeing}; re-run derive_demol_evidence.py rather than editing "
            "the manifest"
        )


def validate_cameroon(block: Any, *, repo_root: str | Path | None) -> None:
    """Check the published Cameroon figures against the artefact that derived them.

    Written to the same standard as `validate_demol`, because until it existed
    the tropical block was held to none. `load_manifest` did not require it,
    nothing re-hashed `docs/evidence/cameroon_61/result.json`, and no test
    compared the two -- so the only cohort in this repository that has been cut
    down and weighed, and the only one that reaches the allometric stage at all,
    was the least guarded evidence in it.

    The asymmetry mattered because `published_figure_values` reads this block to
    decide whether a figure quoted in prose is current. A manifest number that
    had drifted from its own artefact would have been used to certify documents
    quoting the drifted number.
    """
    if not isinstance(block, dict):
        raise ValueError("validation.cameroon_61 must be an object")
    _require_keys(
        block,
        {"result_path", "result_sha256", *CAMEROON_PUBLISHED_FIELDS},
        "validation.cameroon_61",
    )
    if block["result_path"] != CAMEROON_RESULT_PATH:
        raise ValueError(
            f"validation.cameroon_61 result_path must be {CAMEROON_RESULT_PATH}"
        )
    _require_sha256(block["result_sha256"], "validation.cameroon_61 result_sha256")

    if repo_root is None:
        # Structure only, matching validate_demol: sync() always supplies
        # repo_root, so the comparison below runs on every `--check`.
        return

    result_file = Path(repo_root) / CAMEROON_RESULT_PATH
    if not result_file.is_file():
        raise ValueError(
            f"{CAMEROON_RESULT_PATH} is missing; the published figures have no source"
        )
    raw = result_file.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != block["result_sha256"]:
        raise ValueError(
            f"{CAMEROON_RESULT_PATH} has changed since it was reviewed "
            f"(recorded {block['result_sha256']}, found {digest})"
        )

    metrics = json.loads(raw.decode("utf-8")).get("metrics")
    if not isinstance(metrics, dict):
        raise ValueError(f"{CAMEROON_RESULT_PATH} has no metrics block")
    disagreeing = sorted(
        manifest_key
        for manifest_key, metrics_key in CAMEROON_PUBLISHED_FIELDS.items()
        if block[manifest_key] != metrics.get(metrics_key)
    )
    if disagreeing:
        raise ValueError(
            "validation.cameroon_61 disagrees with the derived result for "
            f"{disagreeing}; re-run derive_cameroon_evidence.py rather than "
            "editing the manifest"
        )


def load_manifest(
    path: str | Path, *, repo_root: str | Path | None = None
) -> dict[str, Any]:
    """Load and validate the reviewed truth manifest."""
    manifest_path = Path(path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    _require_keys(
        manifest,
        {
            "schema_version",
            "project",
            "baseline",
            "candidate",
            "validation",
            "capabilities",
            "core_demo",
        },
        "manifest",
    )
    if manifest["schema_version"] != "1":
        raise ValueError("unsupported manifest schema_version")
    if manifest["project"] != "TreeQ Carbon Platform":
        raise ValueError("project name must be TreeQ Carbon Platform")

    baseline = manifest["baseline"]
    if baseline != {"backend": "tlsep", "status": "Implemented"}:
        raise ValueError("baseline must be tlsep with Implemented status")

    candidate = manifest["candidate"]
    _require_keys(
        candidate,
        {
            "backend",
            "display_name",
            "status",
            "promoted",
            "promotion_evidence",
        },
        "candidate",
    )
    if candidate["backend"] != "pointnet" or candidate["display_name"] != "PointNet++":
        raise ValueError("candidate must identify the PointNet++ backend")
    if candidate["status"] not in VALID_STATUSES:
        raise ValueError("candidate has an invalid status")
    promotion = candidate["promotion_evidence"]
    _require_keys(
        promotion, {"all_passed", "failed_criteria", "policy"}, "promotion evidence"
    )
    if promotion["policy"] != PROMOTION_POLICY:
        raise ValueError("promotion policy must match the canonical formal-gate policy")
    if candidate["promoted"] is not False or candidate["status"] != "Experimental":
        raise ValueError("promotion evidence cannot auto-promote PointNet++")

    validation = manifest["validation"]
    # cameroon_61 is required, not optional. It was optional, which meant the
    # tropical cohort could be dropped from the manifest and every gate would
    # still pass -- and the figures the site publishes would silently revert to
    # the temperate ones.
    _require_keys(
        validation, {"wan_held_out", "demol_65", "cameroon_61"}, "validation"
    )
    wan = validation["wan_held_out"]
    for name, expected in EXPECTED_WAN.items():
        if wan.get(name) != expected:
            raise ValueError(f"Wan held-out {name} must equal {expected}")
    validate_demol(validation["demol_65"], repo_root=repo_root)
    validate_cameroon(validation["cameroon_61"], repo_root=repo_root)
    independent = validation.get("pointnet_independent")
    if independent is not None:
        if repo_root is None:
            raise ValueError("repo_root is required to validate imported PointNet evidence")
        validated_independent = validate_imported_independent(
            independent, repo_root=repo_root
        )
        if promotion["all_passed"] != (
            validated_independent["verdict"] == "PROMOTE_POINTNET"
        ):
            raise ValueError("promotion evidence all_passed disagrees with reviewed verdict")
        expected_failed = (
            []
            if promotion["all_passed"]
            else validated_independent["failed_criteria"]
        )
        if promotion["failed_criteria"] != expected_failed:
            raise ValueError("promotion evidence failed criteria disagree with reviewed result")

    capabilities = manifest["capabilities"]
    if not isinstance(capabilities, list) or not capabilities:
        raise ValueError("capabilities must be a non-empty list")
    seen_names: set[str] = set()
    required_capability_keys = {"name", "status", "implementation", "evidence", "claim"}
    for row in capabilities:
        _require_keys(row, required_capability_keys, "capability")
        if row["status"] not in VALID_STATUSES:
            raise ValueError(f"invalid capability status: {row['status']}")
        if row["name"] in seen_names:
            raise ValueError(f"duplicate capability: {row['name']}")
        seen_names.add(row["name"])

    core_demo = manifest["core_demo"]
    _require_keys(
        core_demo,
        {
            "reproducible",
            "analyzed_commit",
            "git_dirty",
            "pipeline_version",
            "input_sha256",
            "normalized_result_sha256",
            "segmented_ply_sha256",
            "total_trees",
            "total_carbon_kg",
            "total_co2eq_kg",
        },
        "core_demo",
    )
    if core_demo["reproducible"] is not True:
        raise ValueError("core demo must be reproducible")
    if core_demo["git_dirty"] is not False:
        raise ValueError("core demo evidence must come from a clean Git worktree")
    commit = core_demo["analyzed_commit"]
    if not isinstance(commit, str) or len(commit) != 40:
        raise ValueError("core_demo analyzed_commit must be a 40-character Git SHA")
    for field in ("input_sha256", "normalized_result_sha256", "segmented_ply_sha256"):
        _require_sha256(core_demo[field], f"core_demo {field}")
    if not isinstance(core_demo["total_trees"], int) or core_demo["total_trees"] < 1:
        raise ValueError("core_demo total_trees must be a positive integer")
    for field in ("total_carbon_kg", "total_co2eq_kg"):
        if not isinstance(core_demo[field], (int, float)) or core_demo[field] <= 0:
            raise ValueError(f"core_demo {field} must be positive")

    return manifest


def _md(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_capability_matrix(manifest: dict[str, Any]) -> str:
    """Render the complete capability matrix from validated data."""
    candidate = manifest["candidate"]
    promotion_label = "promoted" if candidate["promoted"] else "not promoted"
    lines = [
        "# TreeQ Carbon Platform — Capability Matrix",
        "",
        "> Generated from `docs/evidence/core_demo_manifest.json`; do not edit by hand.",
        "",
        f"Baseline: `{manifest['baseline']['backend']}` (`{manifest['baseline']['status']}`).",
        f"Candidate: {candidate['display_name']} (`{candidate['status']}`, {promotion_label}).",
        "",
        "| Capability | Status | Actual implementation | Evidence | Allowed claim |",
        "|---|---|---|---|---|",
    ]
    for row in manifest["capabilities"]:
        lines.append(
            "| "
            + " | ".join(
                _md(row[key])
                for key in ("name", "status", "implementation", "evidence", "claim")
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def _js_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def render_typescript(manifest: dict[str, Any]) -> str:
    """Render the immutable subset used by the Next.js UI."""
    wan = manifest["validation"]["wan_held_out"]
    demol = manifest["validation"]["demol_65"]
    cameroon = manifest["validation"]["cameroon_61"]
    core = manifest["core_demo"]
    candidate = manifest["candidate"]
    independent = manifest["validation"].get("pointnet_independent")
    return "\n".join(
        [
            "// Generated by scripts/sync_truth.py from the reviewed evidence manifest.",
            "// Do not edit this file by hand.",
            "export const CORE_DEMO_EVIDENCE = {",
            f"  project: {_js_string(manifest['project'])},",
            "  baseline: {",
            f"    backend: {_js_string(manifest['baseline']['backend'])},",
            f"    status: {_js_string(manifest['baseline']['status'])},",
            "  },",
            "  candidate: {",
            f"    backend: {_js_string(candidate['backend'])},",
            f"    displayName: {_js_string(candidate['display_name'])},",
            f"    status: {_js_string(candidate['status'])},",
            f"    promoted: {str(candidate['promoted']).lower()},",
            "  },",
            "  validation: {",
            "    wanHeldOut: {",
            f"      woodIoU: {wan['wood_iou']},",
            f"      leafIoU: {wan['leaf_iou']},",
            f"      meanIoU: {wan['mean_iou']},",
            f"      accuracy: {wan['accuracy']},",
            "    },",
            "    demol65: {",
            f"      dbhMaeCm: {demol['dbh_mae_cm']},",
            f"      volumeMapePct: {demol['volume_mape_pct']},",
            "    },",
            # The tropical cohort, and the three numbers that have to travel
            # together. dbhGateAppliedMaeCm is what a user is handed; it is an
            # average over gatePassedTrees of gatePassedTrees + gateRefusedTrees,
            # and dbhMaeCm is what the same stage produces when forced to answer
            # for every tree. Publishing the first alone is how 27 of 60 reads
            # as 60 of 60.
            "    cameroon61: {",
            f"      treesMeasured: {cameroon['trees_measured']},",
            f"      dbhGateAppliedMaeCm: {cameroon['dbh_gate_applied_mae_cm']},",
            f"      gatePassedTrees: {cameroon['gate_passed_trees']},",
            f"      gateRefusedTrees: {cameroon['gate_refused_trees']},",
            f"      dbhMaeCmSmallStems: {cameroon['dbh_mae_cm_small_stems']},",
            f"      dbhMaeCmSmallStemsN: {cameroon['dbh_mae_cm_small_stems_n']},",
            f"      dbhMaeCm: {cameroon['dbh_mae_cm']},",
            f"      chaveRouteBApePctMedian: {cameroon['chave_route_b_ape_pct_median']},",
            f"      tverRouteBApePctMedian: {cameroon['tver_route_b_ape_pct_median']},",
            f"      chaveMeasurementSharePctMedian: {cameroon['chave_measurement_share_pct_median']},",
            "    },",
            *(
                [
                    "    pointnetIndependent: {",
                    f"      verdict: {_js_string(independent['verdict'])},",
                    "      baseline: {",
                    f"        externalMacroWoodIoU: {independent['baseline']['external_macro_wood_iou']},",
                    f"        dbhMaeCm: {independent['baseline']['dbh_mae_cm']},",
                    f"        heightMaeM: {independent['baseline']['height_mae_m']},",
                    f"        volumeMapePct: {independent['baseline']['volume_mape_pct']},",
                    f"        measurableTrees: {independent['baseline']['measurable_trees']},",
                    "      },",
                    "      candidate: {",
                    f"        externalMacroWoodIoU: {independent['candidate']['external_macro_wood_iou']},",
                    f"        dbhMaeCm: {independent['candidate']['dbh_mae_cm']},",
                    f"        heightMaeM: {independent['candidate']['height_mae_m']},",
                    f"        volumeMapePct: {independent['candidate']['volume_mape_pct']},",
                    f"        measurableTrees: {independent['candidate']['measurable_trees']},",
                    "      },",
                    "    },",
                ]
                if independent is not None
                else []
            ),
            "  },",
            "  coreDemo: {",
            f"    reproducible: {str(core['reproducible']).lower()},",
            f"    analyzedCommit: {_js_string(core['analyzed_commit'])},",
            f"    pipelineVersion: {_js_string(core['pipeline_version'])},",
            f"    backend: {_js_string(manifest['baseline']['backend'])},",
            f"    totalTrees: {core.get('total_trees', 0)},",
            f"    totalCarbonKg: {core.get('total_carbon_kg', 0)},",
            f"    totalCo2eqKg: {core.get('total_co2eq_kg', 0)},",
            "  },",
            "} as const;",
            "",
        ]
    )


def render_truth_block(manifest: dict[str, Any]) -> str:
    """Render a compact human-readable snapshot for controlled documents."""
    wan = manifest["validation"]["wan_held_out"]
    demol = manifest["validation"]["demol_65"]
    cameroon = manifest["validation"]["cameroon_61"]
    core = manifest["core_demo"]
    candidate = manifest["candidate"]
    independent = manifest["validation"].get("pointnet_independent")
    candidate_line = (
        f"- {candidate['display_name']}: **{candidate['status']}**, not promoted; "
        "reviewed evidence never changes the default automatically."
        if independent is not None
        else (
            f"- {candidate['display_name']}: **{candidate['status']}**, not promoted; "
            "no verified independent final-test gate."
        )
    )
    return "\n".join(
        [
            "### Verified truth snapshot (generated)",
            "",
            f"- Baseline: `{manifest['baseline']['backend']}` — **Implemented**.",
            candidate_line,
            (
                f"- Wan 2021 held-out: Wood IoU `{wan['wood_iou']}`, "
                f"Leaf IoU `{wan['leaf_iou']}`, Mean IoU `{wan['mean_iou']}`, "
                f"accuracy `{wan['accuracy']}`. The held-out loader was also used for best-epoch selection."
            ),
            (
                f"- Demol isolated-tree validation (65 trees): DBH MAE "
                f"`{demol['dbh_mae_cm']} cm`; Volume MAPE "
                f"`{demol['volume_mape_pct']}%`. This is not an eight-stage or carbon validation."
            ),
            (
                f"- Cameroon destructive tropical validation "
                f"({cameroon['trees']} trees, {cameroon['trees_measured']} measurable): "
                f"DBH MAE `{cameroon['dbh_gate_applied_mae_cm']} cm` over the "
                f"`{cameroon['gate_passed_trees']}` trees the shipped gate passes, "
                f"`{cameroon['gate_refused_trees']}` refused; "
                f"`{cameroon['dbh_mae_cm']} cm` if every measurable tree is forced "
                "to answer, which is the ceiling and not the error."
            ),
            (
                f"- Cameroon allometric, scored against harvested mass: Chave 2014 "
                f"median APE `{cameroon['chave_route_b_ape_pct_median']}%` against "
                f"T-VER `{cameroon['tver_route_b_ape_pct_median']}%`, with the "
                f"measurement contributing `{cameroon['chave_measurement_share_pct_median']}%` "
                "at the median. These clouds arrive leaf-stripped and are single "
                "trees, so this validates neither stage 5 nor stages 1-4, and "
                "Cameroon is not Thailand."
            ),
            *(
                [
                    (
                        f"- Independent PointNet review: verdict `{independent['verdict']}`; "
                        f"candidate/baseline external macro Wood IoU "
                        f"`{independent['candidate']['external_macro_wood_iou']}`/"
                        f"`{independent['baseline']['external_macro_wood_iou']}`."
                    ),
                    (
                        f"- Independent downstream candidate/baseline: DBH MAE "
                        f"`{independent['candidate']['dbh_mae_cm']}`/"
                        f"`{independent['baseline']['dbh_mae_cm']}` cm; Height MAE "
                        f"`{independent['candidate']['height_mae_m']}`/"
                        f"`{independent['baseline']['height_mae_m']}` m; Volume MAPE "
                        f"`{independent['candidate']['volume_mape_pct']}`/"
                        f"`{independent['baseline']['volume_mape_pct']}`%; measurable trees "
                        f"`{independent['candidate']['measurable_trees']}`/"
                        f"`{independent['baseline']['measurable_trees']}`."
                    ),
                ]
                if independent is not None
                else []
            ),
            (
                f"- Deterministic core demo: `{core['total_trees']}` trees, "
                f"`{core['total_carbon_kg']} kg C`, `{core['total_co2eq_kg']} kg CO2e`; "
                f"analyzed commit `{core['analyzed_commit'][:12]}` with a clean worktree."
            ),
            "- Species classification: **Stub**. Carbon stock/CO2e estimates are not certified credits.",
        ]
    )


def replace_truth_block(text: str, rendered: str) -> str:
    """Replace exactly one generated block; fail on absent or ambiguous anchors."""
    if text.count(TRUTH_START) != 1 or text.count(TRUTH_END) != 1:
        raise ValueError("document must contain exactly one pair of truth markers")
    start = text.index(TRUTH_START) + len(TRUTH_START)
    end = text.index(TRUTH_END)
    if start > end:
        raise ValueError("truth markers are out of order")
    return text[:start] + "\n" + rendered.rstrip() + "\n" + text[end:]


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def sync(repo_root: Path, *, check: bool) -> int:
    """Write generated truth, or compare it with the checked-in bytes."""
    manifest = load_manifest(
        repo_root / "docs/evidence/core_demo_manifest.json", repo_root=repo_root
    )
    expected_files = {
        repo_root / "docs/CAPABILITY_MATRIX.md": render_capability_matrix(manifest),
        repo_root / "apps/web/src/generated/core-demo-evidence.ts": render_typescript(manifest),
    }
    truth_block = render_truth_block(manifest)
    for relative in CONTROLLED_DOCS:
        path = repo_root / relative
        expected_files[path] = replace_truth_block(path.read_text(encoding="utf-8"), truth_block)

    drift: list[str] = []
    for path, expected in expected_files.items():
        if check:
            if not path.is_file() or path.read_text(encoding="utf-8") != expected:
                drift.append(str(path.relative_to(repo_root)))
        else:
            _write_text(path, expected)
    if drift:
        print(json.dumps({"status": "drift", "files": drift}, sort_keys=True))
        return 1
    print(json.dumps({"status": "ok", "mode": "check" if check else "write"}))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    args = parser.parse_args()
    return sync(repo_root=args.repo_root.resolve(), check=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
