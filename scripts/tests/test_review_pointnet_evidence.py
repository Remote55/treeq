"""Production-shaped contract tests for reviewed PointNet evidence imports."""

from __future__ import annotations

import copy
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

import pytest
from scripts.review_pointnet_evidence import _load_json, _validate_result, import_reviewed_result
from scripts.sync_truth import (
    CAMEROON_PUBLISHED_FIELDS,
    CAMEROON_RESULT_PATH,
    CONTROLLED_DOCS,
    DEMOL_PUBLISHED_FIELDS,
    DEMOL_RESULT_PATH,
    PROMOTION_POLICY,
    TRUTH_END,
    TRUTH_START,
    load_manifest,
    render_truth_block,
    sync,
)

ROOT = Path(__file__).resolve().parents[2]

#: The Demol block now has to agree with a committed derivation artefact, so a
#: repo built for these tests needs one. The values are arbitrary; what is under
#: test here is the PointNet import, not the Demol figures.
DEMOL_METRICS: dict[str, object] = {
    field: f"{index}/65" if field.endswith("_within_10_pct") else round(index * 0.7, 6)
    for index, field in enumerate(DEMOL_PUBLISHED_FIELDS, start=1)
} | {"trees": 65}
DEMOL_ARTEFACT = json.dumps({"metrics": DEMOL_METRICS}, sort_keys=True).encode("utf-8")
DEMOL_SHA256 = hashlib.sha256(DEMOL_ARTEFACT).hexdigest()

#: The tropical block is required by load_manifest, so this fixture carries one
#: too. Nothing here tests it -- these are the PointNet review's tests -- it
#: just has to be present and self-consistent for the manifest to load.
CAMEROON_METRICS: dict[str, object] = {
    metrics_key: round(index * 0.4, 6)
    for index, metrics_key in enumerate(CAMEROON_PUBLISHED_FIELDS.values(), start=1)
}
CAMEROON_ARTEFACT = json.dumps({"metrics": CAMEROON_METRICS}, sort_keys=True).encode(
    "utf-8"
)
CAMEROON_SHA256 = hashlib.sha256(CAMEROON_ARTEFACT).hexdigest()
EXTERNAL_IDS = tuple(f"tree-{index:02d}" for index in range(1, 11))
review_pointnet_evidence = sys.modules[_validate_result.__module__]


def _naive_sum(values):
    total = 0
    for value in values:
        total += value
    return total


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


@pytest.mark.parametrize(
    ("raw", "label"),
    [
        (b"\xff", "invalid UTF-8"),
        (b'{"unterminated":', "malformed JSON"),
    ],
)
def test_load_json_routes_decode_and_syntax_failures_to_parse_error(
    tmp_path: Path, raw: bytes, label: str
):
    path = tmp_path / "invalid.json"
    path.write_bytes(raw)

    with pytest.raises(ValueError, match=rf"{label} cannot be parsed as finite JSON"):
        _load_json(path, label=label)


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()


def _manifest() -> dict[str, object]:
    return {
        "schema_version": "1",
        "project": "TreeQ Carbon Platform",
        "baseline": {"backend": "tlsep", "status": "Implemented"},
        "candidate": {
            "backend": "pointnet",
            "display_name": "PointNet++",
            "status": "Experimental",
            "promoted": False,
            "promotion_evidence": {
                "all_passed": False,
                "failed_criteria": ["independent_real_test_not_recorded"],
                "policy": PROMOTION_POLICY,
            },
        },
        "validation": {
            "wan_held_out": {
                "wood_iou": 0.418,
                "leaf_iou": 0.808,
                "mean_iou": 0.613,
                "accuracy": 0.831,
            },
            "demol_65": {
                "result_path": DEMOL_RESULT_PATH,
                "result_sha256": DEMOL_SHA256,
                **DEMOL_METRICS,
            },
            "cameroon_61": {
                "result_path": CAMEROON_RESULT_PATH,
                "result_sha256": CAMEROON_SHA256,
                **{
                    manifest_key: CAMEROON_METRICS[metrics_key]
                    for manifest_key, metrics_key in CAMEROON_PUBLISHED_FIELDS.items()
                },
            },
        },
        "capabilities": [
            {
                "name": "5b. PointNet++ wood/leaf candidate",
                "status": "Experimental",
                "implementation": "candidate",
                "evidence": "historical",
                "claim": "historical",
            },
            {
                "name": "Species classification",
                "status": "Stub",
                "implementation": "stub",
                "evidence": "stub.py",
                "claim": "not implemented",
            },
        ],
        "core_demo": {
            "reproducible": True,
            "analyzed_commit": "a" * 40,
            "git_dirty": False,
            "pipeline_version": "0.3.0",
            "input_sha256": "b" * 64,
            "normalized_result_sha256": "c" * 64,
            "segmented_ply_sha256": "d" * 64,
            "total_trees": 3,
            "total_carbon_kg": 1320.39,
            "total_co2eq_kg": 4841.48,
        },
    }


def _metrics(confusion: dict[str, int]) -> dict[str, object]:
    wood, wood_leaf, leaf_wood, leaf = (
        confusion[key] for key in ("wood_as_wood", "wood_as_leaf", "leaf_as_wood", "leaf_as_leaf")
    )
    wood_iou = wood / (wood + wood_leaf + leaf_wood) if wood + wood_leaf + leaf_wood else 1.0
    leaf_iou = leaf / (leaf + wood_leaf + leaf_wood) if leaf + wood_leaf + leaf_wood else 1.0
    return {
        "wood_iou": wood_iou,
        "leaf_iou": leaf_iou,
        "mean_iou": (wood_iou + leaf_iou) / 2.0,
        "accuracy": (wood + leaf) / sum(confusion.values()),
        "confusion": confusion,
    }


def _segmentation(confusion: dict[str, int]) -> dict[str, object]:
    one = _metrics(confusion)
    count = len(EXTERNAL_IDS)
    total = {key: value * count for key, value in confusion.items()}
    return {
        "per_tree": {tree_id: copy.deepcopy(one) for tree_id in EXTERNAL_IDS},
        "macro": {key: one[key] for key in ("wood_iou", "leaf_iou", "mean_iou", "accuracy")},
        "pooled": _metrics(total),
    }


def _committed_result() -> dict[str, object]:
    return json.loads(
        (ROOT / "docs/evidence/pointnet_independent_eval/result.json").read_text(
            encoding="utf-8"
        )
    )


def _set_wood_delta(result: dict[str, object], estimate: float) -> None:
    result["paired_deltas"]["wood_iou_delta"]["estimate"] = estimate
    result["confidence_intervals"]["wood_iou_delta"] = {
        "estimate": estimate,
        "lower": estimate - 0.1,
        "upper": estimate + 0.1,
    }


def _offset_ulps(value: float, steps: int) -> float:
    for _ in range(steps):
        value = math.nextafter(value, math.inf)
    return value


def _external(
    protocol_sha: str, freeze_sha: str, checkpoint: str, experiment: str
) -> dict[str, object]:
    tree_ids = list(EXTERNAL_IDS)
    files = []
    for tree_id in tree_ids:
        for part in ("leaf", "wood"):
            files.append(
                {
                    "filename": f"{tree_id}_{part}.pcd",
                    "tree_id": tree_id,
                    "part": part,
                    "publisher_md5": "a" * 32,
                    "publisher_size_bytes": 1,
                    "sha256": "b" * 64,
                    "size_bytes": 1,
                }
            )
    return {
        "schema_version": "1",
        "experiment_id": experiment,
        "protocol_sha256": protocol_sha,
        "freeze_manifest_sha256": freeze_sha,
        "checkpoint_sha256": checkpoint,
        "record": {
            "provider": "Zenodo",
            "record_id": 6831378,
            "doi": "10.5281/zenodo.6831378",
            "license": "CC-BY-4.0",
        },
        "tree_ids": tree_ids,
        "files": files,
    }


def _freeze(
    protocol: dict[str, object], protocol_sha: str, training_commit: str, checkpoint: str
) -> dict[str, object]:
    metrics = {"wood_iou": 0.5, "leaf_iou": 0.5, "mean_iou": 0.5, "accuracy": 0.5}
    seed = protocol["training"]["seeds"][0]
    return {
        "schema_version": "1",
        "experiment_id": protocol["experiment_id"],
        "protocol_sha256": protocol_sha,
        "wan_manifest_sha256": "c" * 64,
        "training_runs_sha256": "d" * 64,
        "training_git_commit": training_commit,
        "working_tree_clean": True,
        "training_command": ["python", "-m", "scripts.pointnet_evidence", "train"],
        "environment": {},
        "architecture": "PointNet2SegSSG",
        "training_configuration": protocol["training"],
        "wan_evidence": {
            "schema_version": "1",
            "config": {},
            "sources": [
                {"filename": "reference_pc_White_Birch.txt", "sha256": "a" * 64, "size_bytes": 101}
            ],
            "outputs": {"train": {}, "dev": {}},
        },
        "winner": {
            "seed": seed,
            "selected_epoch": 7,
            "dev_metrics": metrics,
            "checkpoint_file": "winner.pt",
            "checkpoint_sha256": checkpoint,
            "state_dict_sha256": "e" * 64,
        },
        "rerun_evidence": {
            "seed": seed,
            "best_epoch": 7,
            "best_macro_tile_wood_iou": 0.6,
            "state_dict_sha256": "e" * 64,
            "checkpoint_file": "seed-1-rerun.pt",
            "checkpoint_sha256": "1" * 64,
            "reproducible": True,
        },
    }


def _result(verdict: str, evaluation_commit: str, hashes: dict[str, str]) -> dict[str, object]:
    baseline = {
        "external_segmentation": _segmentation(
            {"wood_as_wood": 2, "wood_as_leaf": 2, "leaf_as_wood": 1, "leaf_as_leaf": 2}
        ),
        "downstream": {
            "dbh_mae_cm": 1.0,
            "height_mae_m": 0.5,
            "volume_mape_pct": 10.0,
            "measurable_trees": 65,
        },
    }
    failing = verdict in {"FAIL_METRICS", "INVALID_EVIDENCE"}
    candidate = {
        "external_segmentation": _segmentation(
            {
                "wood_as_wood": 2 if failing else 3,
                "wood_as_leaf": 2 if failing else 1,
                "leaf_as_wood": 1,
                "leaf_as_leaf": 2 if failing else 3,
            }
        ),
        "downstream": {
            "dbh_mae_cm": 1.1 if failing else 0.9,
            "height_mae_m": 0.5 if failing else 0.4,
            "volume_mape_pct": 10.0 if failing else 9.0,
            "measurable_trees": 65,
        },
    }
    base = {
        "wood_iou": baseline["external_segmentation"]["macro"]["wood_iou"],
        **baseline["downstream"],
    }
    cand = {
        "wood_iou": candidate["external_segmentation"]["macro"]["wood_iou"],
        **candidate["downstream"],
    }
    delta_fields = {
        "wood_iou_delta": ("Wood IoU candidate-minus-baseline", "proportion", "wood_iou"),
        "dbh_abs_error_delta": ("DBH absolute-error candidate-minus-baseline", "cm", "dbh_mae_cm"),
        "height_abs_error_delta": (
            "Height absolute-error candidate-minus-baseline",
            "m",
            "height_mae_m",
        ),
        "volume_ape_delta": ("Volume APE candidate-minus-baseline", "percent", "volume_mape_pct"),
    }
    intervals = {}
    paired = {}
    for key, (name, unit, metric) in delta_fields.items():
        estimate = cand[metric] - base[metric]
        lower, upper = (
            (estimate, estimate)
            if verdict == "PROMOTE_POINTNET"
            else (0.0, 0.2)
            if key == "wood_iou_delta" and not failing
            else (estimate - 0.1, estimate + 0.1)
        )
        intervals[key] = {"estimate": estimate, "lower": lower, "upper": upper}
        paired[key] = {"name": name, "unit": unit, "estimate": estimate}
    failed = ["wood_iou_improves", "dbh_mae_non_regression"] if failing else []
    return {
        "schema_version": "1",
        "experiment_id": "pointnet-independent-eval-2026-07-16",
        **hashes,
        "checkpoint_sha256": "f" * 64,
        "evaluation_git_commit": evaluation_commit,
        "baseline": baseline,
        "candidate": candidate,
        "paired_deltas": paired,
        "confidence_intervals": intervals,
        "formal_gate": {
            "promote": not failing,
            "status": "rejected" if failing else "promoted",
            "failed_criteria": failed,
            "baseline": base,
            "candidate": cand,
        },
        "verdict": {"verdict": verdict, "promote": verdict == "PROMOTE_POINTNET"},
        "limitations": ["Synthetic production-shaped fixture.", "No automatic default promotion."],
    }


@pytest.fixture
def reviewed_repo(tmp_path: Path) -> tuple[Path, Path, Path]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    evidence = repo / "docs/evidence/pointnet_independent_eval"
    protocol = json.loads(
        (ROOT / "docs/evidence/pointnet_independent_eval/protocol.json").read_text(encoding="utf-8")
    )
    protocol_path = evidence / "protocol.json"
    _write(protocol_path, protocol)
    demol_artefact = repo / DEMOL_RESULT_PATH
    demol_artefact.parent.mkdir(parents=True, exist_ok=True)
    demol_artefact.write_bytes(DEMOL_ARTEFACT)
    cameroon_artefact = repo / CAMEROON_RESULT_PATH
    cameroon_artefact.parent.mkdir(parents=True, exist_ok=True)
    cameroon_artefact.write_bytes(CAMEROON_ARTEFACT)
    manifest_path = repo / "docs/evidence/core_demo_manifest.json"
    _write(manifest_path, _manifest())
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "training provenance")
    training = _git(repo, "rev-parse", "HEAD")
    freeze_path = evidence / "freeze_manifest.json"
    _write(freeze_path, _freeze(protocol, _sha(protocol_path), training, "f" * 64))
    _git(repo, "add", str(freeze_path.relative_to(repo)))
    _git(repo, "commit", "-m", "freeze evidence")
    external_path = evidence / "external_dataset_manifest.json"
    _write(
        external_path,
        _external(_sha(protocol_path), _sha(freeze_path), "f" * 64, str(protocol["experiment_id"])),
    )
    _git(repo, "add", str(external_path.relative_to(repo)))
    _git(repo, "commit", "-m", "external evidence")
    evaluation = _git(repo, "rev-parse", "HEAD")
    result_path = evidence / "result.json"
    _write(
        result_path,
        _result(
            "FAIL_METRICS",
            evaluation,
            {
                "protocol_sha256": _sha(protocol_path),
                "freeze_manifest_sha256": _sha(freeze_path),
                "external_manifest_sha256": _sha(external_path),
            },
        ),
    )
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "result after evaluation")
    return repo, result_path, manifest_path


def _commit_result(
    repo: Path, result_path: Path, result: dict[str, object], message: str = "updated result"
) -> None:
    _write(result_path, result)
    _git(repo, "add", result_path.relative_to(repo).as_posix())
    if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=repo, check=False).returncode:
        _git(repo, "commit", "-m", message)


def _refresh_segmentation(segmentation: dict[str, object]) -> None:
    per_tree = segmentation["per_tree"]
    records = list(per_tree.values())
    segmentation["macro"] = {
        key: math.fsum(record[key] for record in records) / len(records)
        for key in ("wood_iou", "leaf_iou", "mean_iou", "accuracy")
    }
    totals = {
        key: sum(record["confusion"][key] for record in records)
        for key in ("wood_as_wood", "wood_as_leaf", "leaf_as_wood", "leaf_as_leaf")
    }
    segmentation["pooled"] = _metrics(totals)


def test_refresh_segmentation_uses_reproducible_float_aggregation(monkeypatch):
    record = {
        "wood_iou": 0.1,
        "leaf_iou": 0.1,
        "mean_iou": 0.1,
        "accuracy": 0.1,
        "confusion": {
            "wood_as_wood": 1,
            "wood_as_leaf": 0,
            "leaf_as_wood": 0,
            "leaf_as_leaf": 1,
        },
    }
    segmentation = {
        "per_tree": {f"tree-{index:02d}": copy.deepcopy(record) for index in range(10)}
    }
    monkeypatch.setattr(sys.modules[__name__], "sum", _naive_sum, raising=False)

    _refresh_segmentation(segmentation)

    assert segmentation["macro"] == {
        "wood_iou": 0.1,
        "leaf_iou": 0.1,
        "mean_iou": 0.1,
        "accuracy": 0.1,
    }


def _rehash_result(result: dict[str, object], evidence: Path, evaluation: str) -> None:
    result["protocol_sha256"] = _sha(evidence / "protocol.json")
    result["freeze_manifest_sha256"] = _sha(evidence / "freeze_manifest.json")
    result["external_manifest_sha256"] = _sha(evidence / "external_dataset_manifest.json")
    result["evaluation_git_commit"] = evaluation


def _commit_changed_freeze_and_external(repo: Path, result_path: Path, mutate) -> None:
    evidence = result_path.parent
    freeze_path, external_path = (
        evidence / "freeze_manifest.json",
        evidence / "external_dataset_manifest.json",
    )
    _git(repo, "rm", external_path.relative_to(repo).as_posix())
    _git(repo, "commit", "-m", "remove external before freeze")
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    mutate(freeze)
    _write(freeze_path, freeze)
    _git(repo, "add", freeze_path.relative_to(repo).as_posix())
    _git(repo, "commit", "-m", "changed freeze")
    external = _external(
        _sha(evidence / "protocol.json"),
        _sha(freeze_path),
        "f" * 64,
        "pointnet-independent-eval-2026-07-16",
    )
    _write(external_path, external)
    _git(repo, "add", external_path.relative_to(repo).as_posix())
    _git(repo, "commit", "-m", "changed external")
    result = _result(
        "FAIL_METRICS",
        _git(repo, "rev-parse", "HEAD"),
        {
            "protocol_sha256": _sha(evidence / "protocol.json"),
            "freeze_manifest_sha256": _sha(freeze_path),
            "external_manifest_sha256": _sha(external_path),
        },
    )
    _commit_result(repo, result_path, result, "result after changed evidence")


def test_data_validator_accepts_committed_wood_paired_mean_despite_six_ulp_macro_drift():
    result = _committed_result()
    baseline = result["baseline"]["external_segmentation"]
    candidate = result["candidate"]["external_segmentation"]
    tree_ids = sorted(baseline["per_tree"])
    assert tree_ids == sorted(candidate["per_tree"])
    paired_mean = sum(
        candidate["per_tree"][tree_id]["wood_iou"]
        - baseline["per_tree"][tree_id]["wood_iou"]
        for tree_id in tree_ids
    ) / len(tree_ids)
    paired_estimate = result["paired_deltas"]["wood_iou_delta"]["estimate"]
    macro_difference = (
        candidate["macro"]["wood_iou"] - baseline["macro"]["wood_iou"]
    )
    assert paired_estimate == paired_mean
    assert abs(paired_estimate - macro_difference) == 6 * math.ulp(paired_estimate)

    _validate_result(result)


def test_data_validator_macro_is_independent_of_runtime_sum_algorithm(monkeypatch):
    result = _committed_result()
    monkeypatch.setattr(review_pointnet_evidence, "sum", _naive_sum, raising=False)

    _validate_result(result)


def test_data_validator_rejects_coordinated_material_wood_delta_mutation():
    result = _committed_result()
    paired_estimate = result["paired_deltas"]["wood_iou_delta"]["estimate"]
    _set_wood_delta(result, paired_estimate + 1e-8)

    with pytest.raises(ValueError, match="per-tree Wood IoUs"):
        _validate_result(result)


def test_data_validator_allows_wood_delta_within_eight_ulp_bound():
    result = _committed_result()
    paired_estimate = result["paired_deltas"]["wood_iou_delta"]["estimate"]
    _set_wood_delta(result, _offset_ulps(paired_estimate, 8))

    _validate_result(result)


def test_data_validator_rejects_wood_delta_beyond_eight_ulp_bound():
    result = _committed_result()
    paired_estimate = result["paired_deltas"]["wood_iou_delta"]["estimate"]
    _set_wood_delta(result, _offset_ulps(paired_estimate, 9))

    with pytest.raises(ValueError, match="per-tree Wood IoUs"):
        _validate_result(result)


@pytest.mark.parametrize(
    ("mutate", "match"),
    [
        (lambda source: source.pop("size_bytes"), "schema is not exact"),
        (lambda source: source.update(size_bytes=True), "size_bytes"),
        (lambda source: source.update(size_bytes=1.0), "size_bytes"),
        (lambda source: source.update(size_bytes=0), "size_bytes"),
        (lambda source: source.update(size_bytes=-1), "size_bytes"),
        (lambda source: source.update(unexpected="value"), "schema is not exact"),
    ],
)
def test_review_importer_rejects_invalid_frozen_wan_source_sizes(
    reviewed_repo: tuple[Path, Path, Path], mutate, match: str
):
    repo, result_path, manifest_path = reviewed_repo

    def mutate_freeze(freeze):
        mutate(freeze["wan_evidence"]["sources"][0])

    _commit_changed_freeze_and_external(repo, result_path, mutate_freeze)

    with pytest.raises(ValueError, match=match):
        import_reviewed_result(result_path, manifest_path, repo_root=repo)


@pytest.mark.parametrize(
    "verdict", ["FAIL_METRICS", "POINT_ESTIMATE_PASS_ONLY", "PROMOTE_POINTNET"]
)
def test_imports_all_declared_verdicts_without_auto_promotion(
    reviewed_repo: tuple[Path, Path, Path], verdict: str
):
    repo, result_path, manifest_path = reviewed_repo
    hashes = {
        key: _sha(result_path.parent / name)
        for key, name in (
            ("protocol_sha256", "protocol.json"),
            ("freeze_manifest_sha256", "freeze_manifest.json"),
            ("external_manifest_sha256", "external_dataset_manifest.json"),
        )
    }
    result = _result(verdict, _git(repo, "rev-parse", "HEAD~1"), hashes)
    _commit_result(repo, result_path, result, verdict)
    before = json.loads(manifest_path.read_text(encoding="utf-8"))
    after = import_reviewed_result(result_path, manifest_path, repo_root=repo)
    assert after["baseline"] == before["baseline"] and after["core_demo"] == before["core_demo"]
    assert (
        after["candidate"]["status"] == "Experimental" and after["candidate"]["promoted"] is False
    )
    assert after["capabilities"][1] == before["capabilities"][1]
    assert after["validation"]["pointnet_independent"]["verdict"] == verdict
    assert after["candidate"]["promotion_evidence"]["all_passed"] is (verdict == "PROMOTE_POINTNET")


def test_rejects_invalid_evidence_even_with_production_shaped_artifacts(
    reviewed_repo: tuple[Path, Path, Path],
):
    repo, result_path, manifest_path = reviewed_repo
    result = json.loads(result_path.read_text(encoding="utf-8"))
    result["verdict"] = {"verdict": "INVALID_EVIDENCE", "promote": False}
    _commit_result(repo, result_path, result)
    with pytest.raises(ValueError, match="INVALID_EVIDENCE cannot be imported"):
        import_reviewed_result(result_path, manifest_path, repo_root=repo)


@pytest.mark.parametrize("change", ["missing", "extra", "wrong"])
def test_rejects_per_tree_ids_that_do_not_equal_external_manifest(
    reviewed_repo: tuple[Path, Path, Path], change: str
):
    repo, result_path, manifest_path = reviewed_repo
    result = json.loads(result_path.read_text(encoding="utf-8"))
    for backend in ("baseline", "candidate"):
        segmentation = result[backend]["external_segmentation"]
        records = segmentation["per_tree"]
        if change == "missing":
            records.pop(EXTERNAL_IDS[-1])
        elif change == "extra":
            records["tree-extra"] = copy.deepcopy(records[EXTERNAL_IDS[0]])
        else:
            records["wrong-tree"] = records.pop(EXTERNAL_IDS[-1])
        _refresh_segmentation(segmentation)
    _commit_result(repo, result_path, result, f"{change} cohort IDs")
    with pytest.raises(ValueError, match="canonical cohort"):
        import_reviewed_result(result_path, manifest_path, repo_root=repo)


def test_rejects_duplicate_per_tree_json_key(reviewed_repo: tuple[Path, Path, Path]):
    repo, result_path, manifest_path = reviewed_repo
    raw = result_path.read_text(encoding="utf-8").replace('"tree-02":', '"tree-01":', 1)
    result_path.write_text(raw, encoding="utf-8", newline="\n")
    _git(repo, "add", result_path.relative_to(repo).as_posix())
    _git(repo, "commit", "-m", "duplicate result ID")
    with pytest.raises(ValueError, match="duplicate JSON key"):
        import_reviewed_result(result_path, manifest_path, repo_root=repo)


@pytest.mark.parametrize("count", [0, 66])
def test_rejects_measurable_tree_count_outside_protocol_bounds(
    reviewed_repo: tuple[Path, Path, Path], count: int
):
    repo, result_path, manifest_path = reviewed_repo
    result = json.loads(result_path.read_text(encoding="utf-8"))
    result["candidate"]["downstream"]["measurable_trees"] = count
    result["formal_gate"]["candidate"]["measurable_trees"] = count
    _commit_result(repo, result_path, result, f"count {count}")
    with pytest.raises(ValueError, match="measurable_trees"):
        import_reviewed_result(result_path, manifest_path, repo_root=repo)


def test_allows_65_baseline_49_candidate_measurable_trees_and_paired_downstream_delta(
    reviewed_repo: tuple[Path, Path, Path],
):
    repo, result_path, manifest_path = reviewed_repo
    result = json.loads(result_path.read_text(encoding="utf-8"))
    result["candidate"]["downstream"]["measurable_trees"] = 49
    result["formal_gate"]["candidate"]["measurable_trees"] = 49
    result["formal_gate"]["failed_criteria"].append("measurable_tree_count")
    result["paired_deltas"]["dbh_abs_error_delta"]["estimate"] = -0.3
    result["confidence_intervals"]["dbh_abs_error_delta"] = {
        "estimate": -0.3,
        "lower": -0.4,
        "upper": -0.2,
    }
    _commit_result(repo, result_path, result, "different paired counts")
    imported = import_reviewed_result(result_path, manifest_path, repo_root=repo)
    validation = imported["validation"]["pointnet_independent"]
    assert validation["baseline"]["measurable_trees"] == 65
    assert validation["candidate"]["measurable_trees"] == 49


def test_records_exact_count_failure_when_candidate_has_64_of_65_measurable_trees(
    reviewed_repo: tuple[Path, Path, Path],
):
    repo, result_path, manifest_path = reviewed_repo
    result = json.loads(result_path.read_text(encoding="utf-8"))
    result["candidate"]["downstream"]["measurable_trees"] = 64
    result["formal_gate"]["candidate"]["measurable_trees"] = 64
    result["formal_gate"]["failed_criteria"] = [
        "wood_iou_improves",
        "dbh_mae_non_regression",
        "measurable_tree_count",
    ]
    _commit_result(repo, result_path, result, "candidate loses measurable tree")
    imported = import_reviewed_result(result_path, manifest_path, repo_root=repo)
    assert imported["candidate"]["promotion_evidence"]["failed_criteria"] == [
        "wood_iou_improves",
        "dbh_mae_non_regression",
        "measurable_tree_count",
    ]


@pytest.mark.parametrize(
    "mutate, message",
    [
        (lambda freeze: freeze["winner"].update({"seed": 1}), "winner seed"),
        (lambda freeze: freeze["rerun_evidence"].update({"seed": 20260717}), "rerun seed"),
        (lambda freeze: freeze["rerun_evidence"].update({"best_epoch": 8}), "best epoch"),
        (
            lambda freeze: freeze["rerun_evidence"].update({"state_dict_sha256": "0" * 64}),
            "state identity",
        ),
    ],
)
def test_rejects_freeze_reproducibility_cross_link_mutations(
    reviewed_repo: tuple[Path, Path, Path], mutate, message: str
):
    repo, result_path, manifest_path = reviewed_repo
    _commit_changed_freeze_and_external(repo, result_path, mutate)
    with pytest.raises(ValueError, match=message):
        import_reviewed_result(result_path, manifest_path, repo_root=repo)


def test_rejects_same_commit_freeze_and_external_introduction(
    reviewed_repo: tuple[Path, Path, Path],
):
    repo, result_path, manifest_path = reviewed_repo
    evidence = result_path.parent
    freeze_path, external_path = (
        evidence / "freeze_manifest.json",
        evidence / "external_dataset_manifest.json",
    )
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    freeze["environment"] = {"same": True}
    _write(freeze_path, freeze)
    external = json.loads(external_path.read_text(encoding="utf-8"))
    external["freeze_manifest_sha256"] = _sha(freeze_path)
    _write(external_path, external)
    _git(
        repo,
        "add",
        freeze_path.relative_to(repo).as_posix(),
        external_path.relative_to(repo).as_posix(),
    )
    _git(repo, "commit", "-m", "same commit")
    result = _result(
        "FAIL_METRICS",
        _git(repo, "rev-parse", "HEAD"),
        {
            "protocol_sha256": _sha(evidence / "protocol.json"),
            "freeze_manifest_sha256": _sha(freeze_path),
            "external_manifest_sha256": _sha(external_path),
        },
    )
    _commit_result(repo, result_path, result)
    with pytest.raises(ValueError, match="strict ancestor"):
        import_reviewed_result(result_path, manifest_path, repo_root=repo)


def test_rejects_external_manifest_introduced_before_current_freeze(
    reviewed_repo: tuple[Path, Path, Path],
):
    repo, result_path, manifest_path = reviewed_repo
    evidence = result_path.parent
    freeze_path, external_path = (
        evidence / "freeze_manifest.json",
        evidence / "external_dataset_manifest.json",
    )
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    freeze["environment"] = {"reverse": True}
    staged = evidence / "staged-freeze.json"
    _write(staged, freeze)
    future_hash = _sha(staged)
    staged.unlink()
    external = json.loads(external_path.read_text(encoding="utf-8"))
    external["freeze_manifest_sha256"] = future_hash
    _write(external_path, external)
    _git(repo, "add", external_path.relative_to(repo).as_posix())
    _git(repo, "commit", "-m", "external before freeze")
    _write(freeze_path, freeze)
    _git(repo, "add", freeze_path.relative_to(repo).as_posix())
    _git(repo, "commit", "-m", "freeze after external")
    result = _result(
        "FAIL_METRICS",
        _git(repo, "rev-parse", "HEAD"),
        {
            "protocol_sha256": _sha(evidence / "protocol.json"),
            "freeze_manifest_sha256": _sha(freeze_path),
            "external_manifest_sha256": _sha(external_path),
        },
    )
    _commit_result(repo, result_path, result)
    with pytest.raises(ValueError, match="strict ancestor"):
        import_reviewed_result(result_path, manifest_path, repo_root=repo)


def test_rejects_freeze_changed_at_external_commit_then_restored_later(
    reviewed_repo: tuple[Path, Path, Path],
):
    repo, result_path, manifest_path = reviewed_repo
    evidence = result_path.parent
    freeze_path, external_path = (
        evidence / "freeze_manifest.json",
        evidence / "external_dataset_manifest.json",
    )
    original = freeze_path.read_bytes()
    original_hash = hashlib.sha256(original).hexdigest()
    freeze = json.loads(original)
    freeze["environment"] = {"temporary": True}
    _write(freeze_path, freeze)
    _git(repo, "add", freeze_path.relative_to(repo).as_posix())
    _git(repo, "commit", "-m", "temporary freeze")
    external = json.loads(external_path.read_text(encoding="utf-8"))
    external["freeze_manifest_sha256"] = original_hash
    external["files"][0]["sha256"] = "c" * 64
    _write(external_path, external)
    _git(repo, "add", external_path.relative_to(repo).as_posix())
    _git(repo, "commit", "-m", "external against future freeze")
    freeze_path.write_bytes(original)
    _git(repo, "add", freeze_path.relative_to(repo).as_posix())
    _git(repo, "commit", "-m", "restore freeze")
    result = _result(
        "FAIL_METRICS",
        _git(repo, "rev-parse", "HEAD"),
        {
            "protocol_sha256": _sha(evidence / "protocol.json"),
            "freeze_manifest_sha256": _sha(freeze_path),
            "external_manifest_sha256": _sha(external_path),
        },
    )
    _commit_result(repo, result_path, result)
    with pytest.raises(ValueError, match="freeze manifest bytes differ"):
        import_reviewed_result(result_path, manifest_path, repo_root=repo)


def test_rejects_old_external_path_present_when_current_freeze_is_introduced(
    reviewed_repo: tuple[Path, Path, Path],
):
    repo, result_path, manifest_path = reviewed_repo
    evidence = result_path.parent
    freeze_path, external_path = (
        evidence / "freeze_manifest.json",
        evidence / "external_dataset_manifest.json",
    )
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    freeze["environment"] = {"late": True}
    _write(freeze_path, freeze)
    _git(repo, "add", freeze_path.relative_to(repo).as_posix())
    _git(repo, "commit", "-m", "freeze while old external exists")
    external = json.loads(external_path.read_text(encoding="utf-8"))
    external["freeze_manifest_sha256"] = _sha(freeze_path)
    external["files"][0]["sha256"] = "c" * 64
    _write(external_path, external)
    _git(repo, "add", external_path.relative_to(repo).as_posix())
    _git(repo, "commit", "-m", "final external after freeze")
    result = _result(
        "FAIL_METRICS",
        _git(repo, "rev-parse", "HEAD"),
        {
            "protocol_sha256": _sha(evidence / "protocol.json"),
            "freeze_manifest_sha256": _sha(freeze_path),
            "external_manifest_sha256": _sha(external_path),
        },
    )
    _commit_result(repo, result_path, result)
    with pytest.raises(ValueError, match="external manifest must not exist at freeze introduction"):
        import_reviewed_result(result_path, manifest_path, repo_root=repo)


def test_rejects_training_merged_after_freeze_but_before_external(
    reviewed_repo: tuple[Path, Path, Path],
):
    repo, result_path, manifest_path = reviewed_repo
    evidence = result_path.parent
    current_branch = _git(repo, "branch", "--show-current")
    _git(repo, "checkout", "-b", "training-side")
    (repo / "parallel.txt").write_text("parallel\n", encoding="utf-8")
    _git(repo, "add", "parallel.txt")
    _git(repo, "commit", "-m", "parallel training")
    parallel = _git(repo, "rev-parse", "HEAD")
    _git(repo, "checkout", current_branch)
    freeze_path, external_path = (
        evidence / "freeze_manifest.json",
        evidence / "external_dataset_manifest.json",
    )
    _git(repo, "rm", external_path.relative_to(repo).as_posix())
    _git(repo, "commit", "-m", "remove external before freeze")
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    freeze["training_git_commit"] = parallel
    _write(freeze_path, freeze)
    _git(repo, "add", freeze_path.relative_to(repo).as_posix())
    _git(repo, "commit", "-m", "freeze references side training")
    _git(repo, "merge", "--no-ff", "training-side", "-m", "merge training after freeze")
    _write(
        external_path,
        _external(
            _sha(evidence / "protocol.json"),
            _sha(freeze_path),
            "f" * 64,
            "pointnet-independent-eval-2026-07-16",
        ),
    )
    _git(repo, "add", external_path.relative_to(repo).as_posix())
    _git(repo, "commit", "-m", "external after merge")
    result = _result(
        "FAIL_METRICS",
        _git(repo, "rev-parse", "HEAD"),
        {
            "protocol_sha256": _sha(evidence / "protocol.json"),
            "freeze_manifest_sha256": _sha(freeze_path),
            "external_manifest_sha256": _sha(external_path),
        },
    )
    _commit_result(repo, result_path, result)
    with pytest.raises(
        ValueError, match="training_git_commit/freeze introduction must be a strict ancestor"
    ):
        import_reviewed_result(result_path, manifest_path, repo_root=repo)


def test_rejects_winner_checkpoint_mismatch_with_result_and_external(
    reviewed_repo: tuple[Path, Path, Path],
):
    repo, result_path, manifest_path = reviewed_repo
    _commit_changed_freeze_and_external(
        repo, result_path, lambda freeze: freeze["winner"].update({"checkpoint_sha256": "0" * 64})
    )
    with pytest.raises(ValueError, match="freeze checkpoint"):
        import_reviewed_result(result_path, manifest_path, repo_root=repo)


@pytest.mark.parametrize(
    "mutate, message",
    [
        (
            lambda result: result["formal_gate"].update(
                {"promote": True, "status": "promoted", "failed_criteria": []}
            ),
            "formal gate",
        ),
        (
            lambda result: result["confidence_intervals"]["wood_iou_delta"].update({"lower": 0.3}),
            "bounds",
        ),
        (
            lambda result: result["candidate"]["external_segmentation"]["per_tree"][
                EXTERNAL_IDS[0]
            ].update({"wood_iou": True}),
            "not a boolean",
        ),
        (
            lambda result: result["confidence_intervals"]["wood_iou_delta"].update({"extra": 1}),
            "missing or extra",
        ),
        (
            lambda result: result["formal_gate"].update({"failed_criteria": ["not_a_criterion"]}),
            "failed_criteria",
        ),
        (
            lambda result: result["verdict"].update(
                {"verdict": "POINT_ESTIMATE_PASS_ONLY", "promote": True}
            ),
            "verdict",
        ),
    ],
)
def test_rejects_forged_nested_result(reviewed_repo: tuple[Path, Path, Path], mutate, message: str):
    repo, result_path, manifest_path = reviewed_repo
    result = json.loads(result_path.read_text(encoding="utf-8"))
    mutate(result)
    _commit_result(repo, result_path, result)
    with pytest.raises(ValueError, match=message):
        import_reviewed_result(result_path, manifest_path, repo_root=repo)


def test_rejects_noncanonical_paths_and_preimport_candidate_mutation(
    reviewed_repo: tuple[Path, Path, Path],
):
    repo, result_path, manifest_path = reviewed_repo
    with pytest.raises(ValueError, match="canonical"):
        import_reviewed_result(
            result_path.parent / ".." / "pointnet_independent_eval/result.json",
            manifest_path,
            repo_root=repo,
        )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["candidate"]["promoted"] = True
    _write(manifest_path, manifest)
    with pytest.raises(ValueError, match="pre-import candidate"):
        import_reviewed_result(result_path, manifest_path, repo_root=repo)


def test_rejects_non_ancestral_commit_and_committed_sibling_byte_drift(
    reviewed_repo: tuple[Path, Path, Path],
):
    repo, result_path, manifest_path = reviewed_repo
    result = json.loads(result_path.read_text(encoding="utf-8"))
    result["evaluation_git_commit"] = "0" * 40
    _commit_result(repo, result_path, result, "forged commit")
    with pytest.raises(ValueError, match="Git validation"):
        import_reviewed_result(result_path, manifest_path, repo_root=repo)
    result["evaluation_git_commit"] = _git(repo, "rev-parse", "HEAD~2")
    _commit_result(repo, result_path, result, "restore eval")
    protocol = result_path.parent / "protocol.json"
    protocol.write_text(protocol.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="committed Git version"):
        import_reviewed_result(result_path, manifest_path, repo_root=repo)


def test_sync_rechecks_result_bytes_and_renders_reviewed_metrics(
    reviewed_repo: tuple[Path, Path, Path],
):
    repo, result_path, manifest_path = reviewed_repo
    import_reviewed_result(result_path, manifest_path, repo_root=repo)
    manifest = load_manifest(manifest_path, repo_root=repo)
    truth = render_truth_block(manifest)
    assert (
        "FAIL_METRICS" in truth
        and "0.418" in truth
        and str(DEMOL_METRICS["dbh_mae_cm"]) in truth
        and "measurable trees" in truth
    )
    for relative in CONTROLLED_DOCS:
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"{TRUTH_START}\n{TRUTH_END}\n", encoding="utf-8")
    assert sync(repo, check=False) == 0 and sync(repo, check=True) == 0
    result_path.write_text(result_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="committed Git version"):
        sync(repo, check=True)


def test_ci_filters_include_importer_for_push_and_pull_request():
    workflow = (ROOT / ".github/workflows/ci-ml.yml").read_text(encoding="utf-8")
    assert workflow.count('"scripts/review_pointnet_evidence.py"') == 2
