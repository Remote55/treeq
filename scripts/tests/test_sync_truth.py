"""Tests for the manifest-driven truth synchronizer."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest
from scripts.sync_truth import (
    CAMEROON_PUBLISHED_FIELDS,
    CAMEROON_RESULT_PATH,
    DEMOL_PUBLISHED_FIELDS,
    DEMOL_RESULT_PATH,
    FIGURE_PROSE_DOCS,
    PROMOTION_POLICY,
    load_manifest,
    missing_evidence_paths,
    render_capability_matrix,
    render_truth_block,
    render_typescript,
    replace_truth_block,
    stale_figures_in_text,
)

#: A plausible derived block. The values are not the real ones -- what these
#: tests check is that the manifest and the artefact are held to each other, not
#: what either says.
DEMOL_METRICS: dict[str, object] = {
    field: f"{index}/65" if field.endswith("_within_10_pct") else round(index * 0.7, 6)
    for index, field in enumerate(DEMOL_PUBLISHED_FIELDS, start=1)
} | {"trees": 65}

#: The same idea for the tropical cohort. CAMEROON_PUBLISHED_FIELDS maps the
#: manifest's name for each figure to the artefact's, because one of them
#: differs -- the manifest calls the cohort size `trees` and the artefact calls
#: it `cohort_size` -- so the fixture is keyed by the artefact's names.
CAMEROON_METRICS: dict[str, object] = {
    metrics_key: round(index * 0.4, 6)
    for index, metrics_key in enumerate(CAMEROON_PUBLISHED_FIELDS.values(), start=1)
}

CURRENT_CLAIM_DOCS = (
    Path("README.md"),
    Path("AGENTS.md"),
    Path("docs/PROJECT_SPEC.md"),
    Path("docs/CAPABILITY_MATRIX.md"),
    Path("docs/ml/PIPELINE.md"),
    Path("docs/ml/WOODLEAF_RESULTS.md"),
)

STATUS_BANNER_DOCS = (
    Path("docs/AI_AGENT_CONTEXT.md"),
    Path("docs/SESSION_HANDOFF.md"),
    Path("docs/ARCHITECTURE.md"),
    Path("docs/API.md"),
    Path("docs/DEPLOYMENT.md"),
    Path("docs/DEVELOPMENT_PLAN.md"),
    Path("docs/P1_SPRINT_PLAN.md"),
    Path("docs/DATASET_REQUEST.md"),
    Path("docs/ROADMAP.md"),
    Path("docs/learning/README.md"),
    Path("docs/decisions/README.md"),
    Path("proposal/outline.md"),
    Path("docs/proposal/DATASET_SECTION.md"),
    Path("docs/proposal/SYSTEM_OVERVIEW.md"),
    Path("proposal/5-questions-answers.md"),
    Path("services/api/README.md"),
    Path("services/ml/README.md"),
    Path("apps/web/README.md"),
    # apps/mobile/README.md was here until the phone path was dropped. The file
    # went with the app; the entry did not, so this parametrised test failed on
    # a missing file rather than on a missing banner.
)

WAN_DEVELOPMENT_DOCS = (
    Path("docs/ml/FINETUNE_REALDATA.md"),
    Path("docs/ml/WOODLEAF_RESULTS.md"),
    Path("docs/ml/PIPELINE.md"),
)

CONTROLLED_WAN_METRIC_DOCS = (
    Path("docs/ml/WOODLEAF_RESULTS.md"),
    Path("docs/ml/PIPELINE.md"),
)


UNSUPPORTED_WAN_POSITIVE_CLAIMS = (
    re.compile(
        r"\b(?:is|provides|uses)\s+(?:a\s+)?leakage[- ]free\s+(?:held[- ]out|split)\b"
    ),
    re.compile(
        r"\b(?:is|constitutes|provides)\s+(?:an?\s+)?real\s+(?:tls\s+)?test(?:\s+set)?\b"
    ),
    re.compile(
        r"\b(?:is|constitutes|provides)\s+(?:an?\s+)?independent\s+final\s+test\b"
    ),
    re.compile(
        r"\b(?:wan\s+)?(?:figures|evidence)\s+(?:are|constitute|provide)\s+"
        r"independent\s+real\s+tls/(?:final[- ]test)\s+evidence\b"
    ),
    re.compile(
        r"\bper[- ]epoch\s+validation\s+is\s+(?:the\s+)?honest\s+"
        r"independent\s+test\s+number(?:\s+to\s+report)?\b"
    ),
    re.compile(
        r"\b(?:the\s+)?split\s+(?:guarantees|ensures|proves|confirms|shows)\s+"
        r"(?:that\s+)?no\s+shared\s+trees?\b"
    ),
    re.compile(
        r"(?<!not )(?<!cannot )(?<!does not )\b(?:guarantees|ensures|proves|confirms|shows)\s+"
        r"(?:\w+\s+){0,4}unseen\s+trees?\b"
    ),
    re.compile(
        r"\btrain\s*(?:/|and)\s*(?:test|development)\b[^.\n]{0,60}\bnever\s+share(?:s)?\s+"
        r"(?:a\s+)?tree\b"
    ),
)


def _without_generated_truth_blocks(text: str) -> str:
    """Return prose that authors, rather than sync_truth, control."""
    start = "<!-- TREEQ_TRUTH_START -->"
    end = "<!-- TREEQ_TRUTH_END -->"
    while start in text:
        block_end = text.index(end, text.index(start)) + len(end)
        text = text[: text.index(start)] + text[block_end:]
    return text


def _unsupported_wan_positive_claims(prose: str) -> tuple[str, ...]:
    """Find only affirmative, unsupported Wan split claims in author prose."""
    lowered = " ".join(prose.lower().split())
    return tuple(
        pattern.pattern
        for pattern in UNSUPPORTED_WAN_POSITIVE_CLAIMS
        if pattern.search(lowered)
    )


def _write_artefact(root: Path, relative: str, metrics: dict[str, object]) -> str:
    """Write a derivation artefact under `root` and return its SHA-256.

    Both cohorts publish through the same shape -- a `metrics` object beside a
    pinned hash -- so both test classes build their fixtures with this.
    """
    artefact = root / relative
    artefact.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps({"metrics": metrics}).encode("utf-8")
    artefact.write_bytes(payload)
    return hashlib.sha256(payload).hexdigest()


def _cameroon_block() -> dict[str, object]:
    """The manifest block, named the manifest's way, valued the artefact's."""
    return {
        "result_path": CAMEROON_RESULT_PATH,
        "result_sha256": "5" * 64,
        **{
            manifest_key: CAMEROON_METRICS[metrics_key]
            for manifest_key, metrics_key in CAMEROON_PUBLISHED_FIELDS.items()
        },
    }


def _manifest(tmp_path: Path) -> Path:
    path = tmp_path / "manifest.json"
    path.write_text(
        json.dumps(
            {
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
                        "failed_criteria": ["independent_real_test"],
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
                        "result_sha256": "4" * 64,
                        **DEMOL_METRICS,
                    },
                    "cameroon_61": _cameroon_block(),
                },
                "capabilities": [
                    {
                        "name": "Species classification",
                        "status": "Stub",
                        "implementation": "No learned classifier",
                        "evidence": "services/ml/pipeline/species_classifier.py",
                        "claim": "Not implemented",
                    }
                ],
                "core_demo": {
                    "reproducible": True,
                    "analyzed_commit": "9" * 40,
                    "git_dirty": False,
                    "pipeline_version": "0.3.0",
                    "input_sha256": "1" * 64,
                    "normalized_result_sha256": "2" * 64,
                    "segmented_ply_sha256": "3" * 64,
                    "total_trees": 3,
                    "total_carbon_kg": 1320.39,
                    "total_co2eq_kg": 4841.48,
                },
            }
        ),
        encoding="utf-8",
    )
    return path


class TestThePublishedDemolFiguresHaveASource:
    """The block used to be guarded by `if block["dbh_mae_cm"] != 1.1673846154`.

    A literal in sync_truth.py compared against a copy of itself in the
    manifest. It could catch someone editing one of the two and nothing else,
    and the number it certified had never been produced by an evaluation --
    every linear statistic in the block was an exact multiple of 1/65 of a
    two-decimal sum, because it was averaged from a table already rounded for
    display. The manifest now has to agree with a committed artefact that
    `services/ml/scripts/derive_demol_evidence.py --check` re-derives from the
    cohort, and these are the ways that can fail.
    """

    @staticmethod
    def _with_artefact(tmp_path: Path, metrics: dict[str, object] | None = None) -> Path:
        """A manifest beside a derivation artefact it correctly cites.

        The tropical artefact is written too, because `cameroon_61` is required
        the same way this block is; without it every case below would fail on
        the wrong cohort. `validate_demol` runs first, so the failures these
        tests assert on are still Demol's.
        """
        path = _manifest(tmp_path)
        demol_sha = _write_artefact(tmp_path, DEMOL_RESULT_PATH, metrics or DEMOL_METRICS)
        cameroon_sha = _write_artefact(tmp_path, CAMEROON_RESULT_PATH, CAMEROON_METRICS)

        data = json.loads(path.read_text(encoding="utf-8"))
        data["validation"]["demol_65"]["result_sha256"] = demol_sha
        data["validation"]["cameroon_61"]["result_sha256"] = cameroon_sha
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def test_a_manifest_matching_its_artefact_loads(self, tmp_path: Path):
        path = self._with_artefact(tmp_path)

        assert load_manifest(path, repo_root=tmp_path)["validation"]["demol_65"]

    def test_a_figure_with_no_artefact_behind_it_is_refused(self, tmp_path: Path):
        path = _manifest(tmp_path)

        with pytest.raises(ValueError, match="have no source"):
            load_manifest(path, repo_root=tmp_path)

    def test_a_block_that_cites_nothing_is_refused(self, tmp_path: Path):
        path = _manifest(tmp_path)
        data = json.loads(path.read_text(encoding="utf-8"))
        del data["validation"]["demol_65"]["result_path"]
        path.write_text(json.dumps(data), encoding="utf-8")

        with pytest.raises(ValueError, match="missing required keys"):
            load_manifest(path)

    def test_a_block_citing_some_other_file_is_refused(self, tmp_path: Path):
        """The path is pinned, not merely required to exist. Otherwise the
        block could cite any file whose hash happened to be recorded."""
        path = self._with_artefact(tmp_path)
        data = json.loads(path.read_text(encoding="utf-8"))
        data["validation"]["demol_65"]["result_path"] = "docs/evidence/elsewhere.json"
        path.write_text(json.dumps(data), encoding="utf-8")

        with pytest.raises(ValueError, match="result_path must be"):
            load_manifest(path, repo_root=tmp_path)

    def test_a_hand_edited_figure_is_refused(self, tmp_path: Path):
        """The failure the old literal was reaching for, done properly."""
        path = self._with_artefact(tmp_path)
        data = json.loads(path.read_text(encoding="utf-8"))
        data["validation"]["demol_65"]["dbh_mae_cm"] = 0.1
        path.write_text(json.dumps(data), encoding="utf-8")

        with pytest.raises(ValueError, match=r"disagrees with the derived result.*dbh_mae_cm"):
            load_manifest(path, repo_root=tmp_path)

    def test_a_rewritten_artefact_is_refused(self, tmp_path: Path):
        """Editing the artefact to match a hand-edited manifest is the obvious
        way around the check above. The pinned sha256 closes it."""
        path = self._with_artefact(tmp_path)
        artefact = tmp_path / DEMOL_RESULT_PATH
        artefact.write_bytes(
            json.dumps({"metrics": {**DEMOL_METRICS, "dbh_mae_cm": 0.1}}).encode("utf-8")
        )

        with pytest.raises(ValueError, match="has changed since it was reviewed"):
            load_manifest(path, repo_root=tmp_path)

    def test_every_published_field_is_compared_not_just_the_quoted_ones(
        self, tmp_path: Path
    ):
        """Three of the eighteen reach the documents. The old guard checked one.
        A block is only as sourced as its least-checked number."""
        for field in DEMOL_PUBLISHED_FIELDS:
            root = tmp_path / field
            root.mkdir()
            path = self._with_artefact(root)
            data = json.loads(path.read_text(encoding="utf-8"))
            data["validation"]["demol_65"][field] = "tampered"
            path.write_text(json.dumps(data), encoding="utf-8")

            with pytest.raises(ValueError, match=rf"disagrees with the derived result.*{field}"):
                load_manifest(path, repo_root=root)


class TestThePublishedCameroonFiguresHaveASource:
    """The tropical block had no validator at all.

    `validate_demol` re-hashes its artefact and compares every published field
    against it. `cameroon_61` had neither: `load_manifest` did not require the
    block, nothing re-hashed `docs/evidence/cameroon_61/result.json`, and no
    test held the two to each other. The only thing reading the block was
    `published_figure_values`, which uses it to spot stale prose -- so a
    manifest figure that had drifted from its own artefact would have been used
    to certify documents quoting the drifted number.

    That left the newest and strongest evidence in the repository -- 61 trees
    cut down and weighed, the only cohort that checks the allometric stage --
    guarded less than the 65-tree cohort it supersedes for tropical claims.
    """

    @staticmethod
    def _with_artefacts(
        tmp_path: Path, metrics: dict[str, object] | None = None
    ) -> Path:
        """A manifest beside both derivation artefacts, correctly cited."""
        path = _manifest(tmp_path)
        demol_sha = _write_artefact(tmp_path, DEMOL_RESULT_PATH, DEMOL_METRICS)
        cameroon_sha = _write_artefact(
            tmp_path, CAMEROON_RESULT_PATH, metrics or CAMEROON_METRICS
        )

        data = json.loads(path.read_text(encoding="utf-8"))
        data["validation"]["demol_65"]["result_sha256"] = demol_sha
        data["validation"]["cameroon_61"]["result_sha256"] = cameroon_sha
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def test_a_manifest_matching_its_artefact_loads(self, tmp_path: Path):
        path = self._with_artefacts(tmp_path)

        assert load_manifest(path, repo_root=tmp_path)["validation"]["cameroon_61"]

    def test_a_manifest_with_no_tropical_block_is_refused(self, tmp_path: Path):
        """The block was optional. A cohort that can be dropped from the
        manifest without a gate noticing is a cohort the gate does not hold."""
        path = self._with_artefacts(tmp_path)
        data = json.loads(path.read_text(encoding="utf-8"))
        del data["validation"]["cameroon_61"]
        path.write_text(json.dumps(data), encoding="utf-8")

        with pytest.raises(ValueError, match="validation missing required keys"):
            load_manifest(path, repo_root=tmp_path)

    def test_a_figure_with_no_artefact_behind_it_is_refused(self, tmp_path: Path):
        path = _manifest(tmp_path)
        _write_artefact(tmp_path, DEMOL_RESULT_PATH, DEMOL_METRICS)
        data = json.loads(path.read_text(encoding="utf-8"))
        data["validation"]["demol_65"]["result_sha256"] = hashlib.sha256(
            json.dumps({"metrics": DEMOL_METRICS}).encode("utf-8")
        ).hexdigest()
        path.write_text(json.dumps(data), encoding="utf-8")

        with pytest.raises(ValueError, match="have no source"):
            load_manifest(path, repo_root=tmp_path)

    def test_a_block_that_cites_nothing_is_refused(self, tmp_path: Path):
        path = self._with_artefacts(tmp_path)
        data = json.loads(path.read_text(encoding="utf-8"))
        del data["validation"]["cameroon_61"]["result_path"]
        path.write_text(json.dumps(data), encoding="utf-8")

        with pytest.raises(ValueError, match="missing required keys"):
            load_manifest(path, repo_root=tmp_path)

    def test_a_block_citing_some_other_file_is_refused(self, tmp_path: Path):
        path = self._with_artefacts(tmp_path)
        data = json.loads(path.read_text(encoding="utf-8"))
        data["validation"]["cameroon_61"]["result_path"] = "docs/evidence/elsewhere.json"
        path.write_text(json.dumps(data), encoding="utf-8")

        with pytest.raises(ValueError, match="result_path must be"):
            load_manifest(path, repo_root=tmp_path)

    def test_a_hand_edited_figure_is_refused(self, tmp_path: Path):
        path = self._with_artefacts(tmp_path)
        data = json.loads(path.read_text(encoding="utf-8"))
        data["validation"]["cameroon_61"]["dbh_gate_applied_mae_cm"] = 0.1
        path.write_text(json.dumps(data), encoding="utf-8")

        with pytest.raises(
            ValueError,
            match=r"disagrees with the derived result.*dbh_gate_applied_mae_cm",
        ):
            load_manifest(path, repo_root=tmp_path)

    def test_a_rewritten_artefact_is_refused(self, tmp_path: Path):
        path = self._with_artefacts(tmp_path)
        artefact = tmp_path / CAMEROON_RESULT_PATH
        artefact.write_bytes(
            json.dumps(
                {"metrics": {**CAMEROON_METRICS, "dbh_gate_applied_mae_cm": 0.1}}
            ).encode("utf-8")
        )

        with pytest.raises(ValueError, match="has changed since it was reviewed"):
            load_manifest(path, repo_root=tmp_path)

    def test_every_published_field_is_compared_not_just_the_quoted_ones(
        self, tmp_path: Path
    ):
        """Six of the twenty-five reach `published_figure_values`. The rest --
        the gate counts, the two allometric routes, the measurement share --
        are quoted in CAMEROON_EVIDENCE_CHAIN.md and on the site, and a block is
        only as sourced as its least-checked number."""
        for manifest_key in CAMEROON_PUBLISHED_FIELDS:
            root = tmp_path / manifest_key
            root.mkdir()
            path = self._with_artefacts(root)
            data = json.loads(path.read_text(encoding="utf-8"))
            data["validation"]["cameroon_61"][manifest_key] = "tampered"
            path.write_text(json.dumps(data), encoding="utf-8")

            with pytest.raises(
                ValueError, match=rf"disagrees with the derived result.*{manifest_key}"
            ):
                load_manifest(path, repo_root=root)

    def test_the_checked_in_manifest_agrees_with_its_committed_artefact(self):
        """Not a fixture: the real manifest against the real 61-tree result."""
        manifest = load_manifest(
            Path("docs/evidence/core_demo_manifest.json"), repo_root=Path.cwd()
        )

        assert manifest["validation"]["cameroon_61"]["gate_passed_trees"] == 27
        assert manifest["validation"]["cameroon_61"]["gate_refused_trees"] == 33


def test_manifest_rejects_promoted_pointnet_without_gate(tmp_path: Path):
    path = _manifest(tmp_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["candidate"]["promoted"] = True
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="promotion evidence"):
        load_manifest(path)


def test_manifest_rejects_incomplete_promotion_policy(tmp_path: Path):
    path = _manifest(tmp_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["candidate"]["promotion_evidence"]["policy"] = (
        "Promote only when Wood IoU improves on an independent real test while DBH "
        "and volume do not regress."
    )
    path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ValueError, match="promotion policy"):
        load_manifest(path)


def test_checked_in_manifest_uses_canonical_promotion_policy():
    manifest = load_manifest(
        Path("docs/evidence/core_demo_manifest.json"), repo_root=Path.cwd()
    )

    assert manifest["candidate"]["promotion_evidence"]["policy"] == PROMOTION_POLICY


def test_manifest_rejects_dirty_core_demo(tmp_path: Path):
    path = _manifest(tmp_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["core_demo"]["git_dirty"] = True
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="clean Git worktree"):
        load_manifest(path)


def test_manifest_rejects_incomplete_core_demo_provenance(tmp_path: Path):
    path = _manifest(tmp_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    del data["core_demo"]["input_sha256"]
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="core_demo missing required keys"):
        load_manifest(path)


def test_generated_outputs_contain_exact_truth(tmp_path: Path):
    data = load_manifest(_manifest(tmp_path))
    typescript = render_typescript(data)
    matrix = render_capability_matrix(data)
    assert "woodIoU: 0.418" in typescript
    assert "leafIoU: 0.808" in typescript
    assert f"dbhMaeCm: {DEMOL_METRICS['dbh_mae_cm']}" in typescript
    assert "PointNet++" in matrix
    assert "Experimental" in matrix
    assert "Species classification" in matrix
    assert "Stub" in matrix


class TestTheTropicalCohortReachesTheGeneratedSurfaces:
    """The site published the temperate figure as the accuracy of the product.

    `render_typescript` emitted `wanHeldOut`, `demol65` and
    `pointnetIndependent` and stopped. `render_truth_block` emitted the first
    two. So `apps/web/src/generated/core-demo-evidence.ts` had no tropical
    figure to show, the landing page's accuracy panel read `0.90 cm` from the
    65 Belgian trees, and the truth block in docs/PROJECT_SPEC.md said nothing
    about the cohort that was cut down and weighed.

    The number a visitor saw was true of temperate isolated trees. The product
    is aimed at tropical forest, the tropical cohort had been measured, and the
    gate that exists to stop documents drifting from evidence could not help,
    because the evidence never reached the document.
    """

    def test_the_typescript_the_site_reads_carries_the_tropical_cohort(
        self, tmp_path: Path
    ):
        data = load_manifest(_manifest(tmp_path))

        typescript = render_typescript(data)

        assert "cameroon61" in typescript
        assert (
            f"dbhGateAppliedMaeCm: {CAMEROON_METRICS['dbh_gate_applied_mae_cm']}"
            in typescript
        )

    def test_the_typescript_carries_how_many_trees_the_gate_refused(
        self, tmp_path: Path
    ):
        """The headline is an average over the trees that passed. Without the
        refused count beside it, 27 of 60 looks like 60 of 60."""
        data = load_manifest(_manifest(tmp_path))

        typescript = render_typescript(data)

        assert f"gatePassedTrees: {CAMEROON_METRICS['gate_passed_trees']}" in typescript
        assert (
            f"gateRefusedTrees: {CAMEROON_METRICS['gate_refused_trees']}" in typescript
        )

    def test_the_typescript_carries_the_ungated_upper_bound(self, tmp_path: Path):
        """The figure for every tree that produced a number. It is the honest
        ceiling on this cohort and it is an order of magnitude worse, so
        publishing the gated figure alone overstates what the pipeline does."""
        data = load_manifest(_manifest(tmp_path))

        typescript = render_typescript(data)

        assert f"dbhMaeCm: {CAMEROON_METRICS['dbh_mae_cm']}" in typescript

    def test_the_truth_block_states_the_tropical_result(self, tmp_path: Path):
        data = load_manifest(_manifest(tmp_path))

        block = render_truth_block(data)

        assert "Cameroon" in block
        assert str(CAMEROON_METRICS["dbh_gate_applied_mae_cm"]) in block

    def test_the_truth_block_states_what_the_tropical_cohort_does_not_validate(
        self, tmp_path: Path
    ):
        """These clouds arrive leaf-stripped and are single trees, so stages
        1-4 and stage 5 are untouched by them. A truth block that gave the
        figure without that would be the drift it exists to prevent."""
        data = load_manifest(_manifest(tmp_path))

        block = render_truth_block(data)

        assert "leaf-stripped" in block


def test_truth_block_requires_exactly_one_marker_pair():
    source = (
        "before\n"
        "<!-- TREEQ_TRUTH_START -->\n"
        "old\n"
        "<!-- TREEQ_TRUTH_END -->\n"
        "after\n"
    )
    updated = replace_truth_block(source, "new")
    assert (
        "before\n"
        "<!-- TREEQ_TRUTH_START -->\n"
        "new\n"
        "<!-- TREEQ_TRUTH_END -->\n"
        "after"
    ) in updated

    with pytest.raises(ValueError, match="truth markers"):
        replace_truth_block("no markers", "new")

    duplicate = source + source
    with pytest.raises(ValueError, match="truth markers"):
        replace_truth_block(duplicate, "new")


def test_ml_ci_does_not_swallow_test_failures():
    workflow = Path(".github/workflows/ci-ml.yml").read_text(encoding="utf-8")
    assert "pytest tests/ -v --tb=short || true" not in workflow
    assert "scripts/run_core_demo.py" in workflow
    assert "scripts/sync_truth.py --check" in workflow
    assert "python-docx" in workflow
    assert "python -m pytest scripts/tests/" in workflow
    assert workflow.count('"docs/evidence/pointnet_independent_eval/**"') == 2
    assert "ruff check pipeline/ training/" in workflow


def test_ml_ci_lints_only_directories_that_exist():
    """A lint command naming a missing directory fails before it lints anything.

    This assertion used to read `ruff check pipeline/ photogrammetry/ training/`,
    pinning a command that could not run: photogrammetry/ has no tracked files
    since the photo path was dropped, so on a fresh checkout ruff exits E902
    "cannot find the file specified" and the step fails without evaluating a
    single rule. The test passed the whole time, because it checked that the
    string was present rather than that the command worked.
    """
    workflow = Path(".github/workflows/ci-ml.yml").read_text(encoding="utf-8")
    repo_root = Path(__file__).resolve().parents[2]
    for match in re.finditer(r"(?m)^\s+run: ruff (?:check|format[^\n]*?--diff) (.+)$", workflow):
        for token in match.group(1).split():
            if token.startswith("-") or "*" in token or token == "||":
                break
            target = (repo_root / "services" / "ml" / token).resolve()
            assert target.exists(), (
                f"ci-ml.yml lints {token!r}, which does not exist in the repository"
            )


def test_api_ci_runs_the_type_checker_it_configures():
    """pyproject has said `strict = true` since the service was written.

    Nothing ran it, so it described a standard the code was never held to —
    the same shape as LOG_FORMAT="json" over a service that used print(). The
    step must also be blocking: a type check that cannot fail the build is the
    claim without the check.
    """
    workflow = Path(".github/workflows/ci-api.yml").read_text(encoding="utf-8")
    pyproject = Path("services/api/pyproject.toml").read_text(encoding="utf-8")

    assert "strict = true" in pyproject
    mypy_step = re.search(r"(?ms)^\s+- name: mypy.*?(?=^\s+- name: |\Z)", workflow)
    assert mypy_step is not None, "ci-api.yml configures mypy but never runs it"

    body = mypy_step.group()
    assert re.search(r"(?m)^\s+run: mypy\s*$", body), "the mypy step does not run mypy"
    for escape in ("|| true", "|| echo", "continue-on-error"):
        assert escape not in body, f"the mypy step is non-blocking via {escape!r}"


def test_every_dockerfile_copy_source_exists():
    """A COPY of a path that is not there fails the build, late and obscurely.

    The API image could not be built at all because pyproject declares
    `readme = "README.md"` and the builder stage copied only pyproject.toml, so
    hatchling raised OSError while generating metadata. Nothing noticed, because
    the tests run against the source tree rather than the image.

    Sources are repository-relative: the build context is the repository root.
    """
    repo_root = Path(__file__).resolve().parents[2]
    dockerfile = repo_root / "services/api/Dockerfile"
    missing = []
    for line in dockerfile.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped.startswith("COPY "):
            continue
        tokens = stripped.split()[1:]
        # --from=builder copies out of an earlier stage, not the context.
        if any(token.startswith("--from=") for token in tokens):
            continue
        sources = [token for token in tokens if not token.startswith("--")][:-1]
        for source in sources:
            if not (repo_root / source).exists():
                missing.append(source)
    assert not missing, f"Dockerfile COPYs paths that do not exist: {missing}"


def test_api_ci_builds_and_exercises_the_image():
    """Building it is the only thing that can prove it builds.

    docs/DEPLOY_PUBLIC.md carried "the image is unbuilt" as an open item for
    long enough that it broke without anyone finding out. /health is not enough
    on its own — an earlier image passed it while every analysis failed, because
    the ML pipeline was not in it.
    """
    workflow = Path(".github/workflows/ci-api.yml").read_text(encoding="utf-8")

    assert "docker/build-push-action" in workflow, "nothing builds the image"
    assert "file: services/api/Dockerfile" in workflow
    assert "context: ." in workflow, "the build context must be the repository root"
    assert "GIT_COMMIT=" in workflow, "process_points refuses a run it cannot attribute"
    assert "/api/v1/health/pipeline" in workflow, "readiness is what proves the ML runtime"
    assert "/api/v1/upload/analyze" in workflow, "the route the product is stays unexercised"
    # A pipeline change alters the image's contents, so it has to trigger this.
    assert '"services/ml/pipeline/**"' in workflow


def test_ml_ci_checkout_fetches_full_provenance_history():
    workflow = Path(".github/workflows/ci-ml.yml").read_text(encoding="utf-8")
    checkout_step = re.search(
        r"(?ms)^\s+- name: Checkout\s*$.*?(?=^\s+- name: Setup Python\s*$)",
        workflow,
    )

    assert checkout_step is not None
    assert re.search(r"(?m)^\s+fetch-depth:\s*0\s*$", checkout_step.group())


def test_current_claim_documents_share_exact_evidence():
    texts = {path: path.read_text(encoding="utf-8") for path in CURRENT_CLAIM_DOCS}
    combined = "\n".join(texts.values())

    for path, text in texts.items():
        assert "tlsep" in text, path
        assert "PointNet++" in text, path
    for exact in (
        "0.418",
        "0.808",
        "0.613",
        "0.831",
        "0.898318",
        "0.543323",
        "11.520556",
    ):
        assert exact in combined

    assert "wood IoU = 0.42" not in combined
    assert "PointNet++ เป็น production default" not in combined


@pytest.mark.parametrize("path", WAN_DEVELOPMENT_DOCS)
def test_wan_development_prose_states_split_limits(path: Path):
    prose = " ".join(
        _without_generated_truth_blocks(path.read_text(encoding="utf-8")).split()
    ).lower()

    for fact in (
        "spatially separated development split",
        "2.5 m excluded band",
        "native tree ids are unavailable",
        "same dev loader selected the epoch",
    ):
        assert fact in prose, (path, fact)

    assert not _unsupported_wan_positive_claims(prose), path


@pytest.mark.parametrize(
    "honest_prose",
    (
        "This development split does not prove unseen trees.",
        "The current evidence is not an independent final test.",
        "A future independent final test is required before promotion.",
    ),
)
def test_wan_positive_claim_detector_accepts_honest_limitations(honest_prose: str):
    assert not _unsupported_wan_positive_claims(honest_prose)


@pytest.mark.parametrize(
    "unsupported_prose",
    (
        "This is a leakage-free split.",
        "The Wan evaluation is a real test set.",
        "The split guarantees no shared trees.",
        "The split guarantees unseen trees.",
        "Train/test never share a tree.",
        "The Wan evaluation is an independent final test.",
        "The Wan figures are independent real TLS/final-test evidence.",
        "Per-epoch validation is the honest independent test number to report.",
    ),
)
def test_wan_positive_claim_detector_rejects_unsupported_claims(unsupported_prose: str):
    assert _unsupported_wan_positive_claims(unsupported_prose)


def test_wan_converter_legacy_test_names_are_disclosed():
    text = Path("docs/ml/FINETUNE_REALDATA.md").read_text(encoding="utf-8").lower()
    assert "--out-test" in text
    assert "wan_test.npz" in text
    assert "legacy names for the development/validation split" in text


def test_wan_same_environment_section_uses_development_not_test_framing():
    text = Path("docs/ml/FINETUNE_REALDATA.md").read_text(encoding="utf-8")
    lowered = text.lower()

    assert "same-environment experiments (train+development on real wan" in lowered
    assert "train+test on real wan" not in lowered
    assert "train/test on the **same real environment**" not in lowered

    held_out_index = lowered.index("[held-out]")
    nearby = lowered[held_out_index : held_out_index + 300]
    assert "legacy output label" in nearby
    assert "not an independent or final test" in nearby


@pytest.mark.parametrize("path", CONTROLLED_WAN_METRIC_DOCS)
def test_controlled_wan_documents_retain_exact_recorded_metrics(path: Path):
    text = path.read_text(encoding="utf-8")
    for metric in ("0.418", "0.808", "0.613", "0.831"):
        assert metric in text, (path, metric)


def test_g3_is_confounded_historical_comparison_not_promotion_evidence():
    source = Path("services/ml/notebooks/experiment_g3_pointnet_volume.py").read_text(
        encoding="utf-8"
    )
    lowered = source.lower()

    assert "confounded historical experiment" in source
    assert "not promotion evidence" in source
    assert "both segmentation and volume method changed" in lowered
    assert "within-script historical comparison only" in lowered
    assert "not an adoption or promotion decision" in lowered
    assert "adopt sectional" not in lowered
    assert "~18.8% mape" in lowered
    assert "~18.8% mae" not in lowered


@pytest.mark.parametrize("path", STATUS_BANNER_DOCS)
def test_mixed_or_historical_documents_have_status_banner(path: Path):
    opening = "\n".join(path.read_text(encoding="utf-8").splitlines()[:15])
    assert "[!CAUTION]" in opening or "[!NOTE]" in opening
    status_words = ("current", "historical", "target", "superseded", "archived")
    assert "ปัจจุบัน" in opening or any(word in opening.lower() for word in status_words)


def test_active_web_package_uses_current_product_name():
    package = json.loads(Path("apps/web/package.json").read_text(encoding="utf-8"))

    assert package["description"] == "TreeQ Carbon Platform — Web Dashboard (Next.js 14)"


def test_nothing_still_refers_to_the_deleted_mobile_app():
    """apps/mobile and ci-mobile.yml are gone; their guards must go with them.

    This was test_mobile_ci_uses_flutter_version_supported_by_app, checking that
    the Flutter version in ci-mobile.yml matched apps/mobile/pubspec.yaml. Both
    files were deleted with the phone path and the test stayed, failing on
    FileNotFoundError ever since — one of the reasons `pytest scripts/tests/`
    has been red. Replaced by the check that actually still means something.
    """
    for path in (Path(".github/workflows/ci-mobile.yml"), Path("apps/mobile")):
        assert not path.exists(), f"{path} is back; the guard it needs is not"


#: Surfaces a visitor or a new reader meets first, where the project has to say
#: what it currently is.
#:
#: NSC 2026 was the competition this repository was built for. It was not won,
#: and CLAUDE.md records that the framing is retired: the goal is now correct
#: science that can be published and used. The badge, the hero eyebrow, the
#: page metadata and the footer went on saying otherwise for weeks after,
#: because nothing checked. Historical documents and the proposal keep the
#: reference -- rewriting those would be falsifying a record -- so this is
#: scoped to the surfaces that speak in the present tense.
CURRENT_FRAMING_SURFACES = (
    Path("README.md"),
    Path("AGENTS.md"),
    Path("apps/web/src/app/page.tsx"),
    Path("apps/web/src/app/layout.tsx"),
    Path("apps/web/src/app/demo/page.tsx"),
)


@pytest.mark.parametrize("path", CURRENT_FRAMING_SURFACES)
def test_no_current_surface_still_claims_the_competition(path: Path):
    text = path.read_text(encoding="utf-8")

    assert "NSC 2026" not in text, (
        f"{path} still presents the project as an NSC 2026 entry. The "
        "competition was not won and the framing is retired; see CLAUDE.md."
    )


def test_the_retired_framing_is_still_recorded_where_it_belongs():
    """The opposite failure: erasing it everywhere.

    docs/DOCUMENT_STATUS.md classifies the proposal and the historical
    documents as records of decisions taken. Deleting the competition from
    those would be rewriting what happened, which this repository treats as a
    worse fault than an out-of-date badge.
    """
    assert "NSC" in Path("docs/DOCUMENT_STATUS.md").read_text(encoding="utf-8")


CORE_DEMO_PROSE_DOCS = (Path("README.md"), Path("docs/PROJECT_SPEC.md"))

#: "1036.09 kg C" / "3798.99 kg CO₂e", written into a sentence by hand rather
#: than generated into a TREEQ_TRUTH block.
_CARBON_IN_PROSE = re.compile(r"(\d+\.\d{2})\s*kg\s*C(?![O₂a-zA-Z])")
_CO2E_IN_PROSE = re.compile(r"(\d+\.\d{2})\s*kg\s*CO(?:₂|2)e")


def test_core_demo_figures_quoted_in_prose_match_the_manifest():
    """sync_truth regenerates what lives inside TREEQ_TRUTH markers. It cannot
    touch a number an author typed into a sentence next to them.

    Both of these documents carried 1320.39 kg C and 4841.48 kg CO2e for as long
    as the manifest did, and would have kept carrying them after the manifest
    was corrected on 2026-08-14. The manifest figures were three releases stale;
    the prose copies were stale twice over, and nothing in the repository looked
    at them. A number is only as checked as its least-checked copy.
    """
    root = Path(__file__).resolve().parents[2]
    manifest = json.loads(
        (root / "docs/evidence/core_demo_manifest.json").read_text(encoding="utf-8")
    )["core_demo"]

    for relative in CORE_DEMO_PROSE_DOCS:
        prose = (root / relative).read_text(encoding="utf-8")
        for pattern, field in (
            (_CARBON_IN_PROSE, "total_carbon_kg"),
            (_CO2E_IN_PROSE, "total_co2eq_kg"),
        ):
            for quoted in pattern.findall(prose):
                assert float(quoted) == manifest[field], (
                    f"{relative} quotes {quoted} for {field}, and the manifest "
                    f"says {manifest[field]}. Re-derive with "
                    "services/ml/scripts/run_core_demo.py and fix the sentence; "
                    "sync_truth only regenerates what is inside the markers"
                )


@pytest.mark.parametrize("relative", CORE_DEMO_PROSE_DOCS, ids=str)
def test_that_check_actually_looks_at_something(relative: Path):
    """A scan that matches nothing passes forever.

    Per document rather than in total. A single count across both files was the
    first version, and it survived deleting both figures from README.md, because
    PROJECT_SPEC.md quotes them twice over and kept the total above the
    threshold. A guard against vacuousness that is itself vacuous for one of the
    two files it guards is not much of one.
    """
    prose = (Path(__file__).resolve().parents[2] / relative).read_text(encoding="utf-8")

    for pattern, label in ((_CARBON_IN_PROSE, "kg C"), (_CO2E_IN_PROSE, "kg CO2e")):
        assert pattern.findall(prose), (
            f"{relative} no longer quotes a core-demo figure in '{label}', so "
            "the check above stopped looking at it. Either the document changed "
            "shape or the pattern did"
        )


def _repo_manifest() -> tuple[Path, dict[str, object]]:
    """The checkout and its committed manifest, loaded the way sync uses it."""
    repo_root = Path(__file__).resolve().parents[2]
    manifest = load_manifest(
        repo_root / "docs/evidence/core_demo_manifest.json", repo_root=repo_root
    )
    return repo_root, manifest


def test_stale_figures_accepts_a_manifest_value():
    """A figure that equals a manifest field is not stale."""
    _, manifest = _repo_manifest()
    demol = manifest["validation"]["demol_65"]
    document = f"Demol 65 trees give DBH MAE {demol['dbh_mae_cm']} cm.\n"

    assert stale_figures_in_text(document, manifest) == ()


def test_stale_figures_reports_a_superseded_value():
    """1.1673846154 is the pre-derivation DBH MAE and must be caught."""
    _, manifest = _repo_manifest()
    document = "Demol 65 trees give DBH MAE 1.1673846154 cm.\n"

    assert stale_figures_in_text(document, manifest) == (
        (1, "DBH MAE", "1.1673846154"),
    )


def test_no_controlled_document_quotes_a_stale_figure():
    """Every accuracy figure in prose must equal one the manifest records.

    docs/ml/DEMOL_EVIDENCE_CHAIN.md:97 labels 1.1674 and 18.77 "published
    before"; the derived values are 0.8983 and 11.52. Both were in the tree at
    once, in the same documents, and sync_truth --check passed because it
    compares the manifest against an artefact and never against the markdown
    that quotes it.
    """
    repo_root, manifest = _repo_manifest()
    offences = []
    for relative in FIGURE_PROSE_DOCS:
        text = (repo_root / relative).read_text(encoding="utf-8")
        for lineno, label, raw in stale_figures_in_text(text, manifest):
            offences.append(f"{relative.as_posix()}:{lineno} {label} = {raw}")

    assert offences == [], "Figures not found in the manifest:\n" + "\n".join(offences)


def test_missing_evidence_paths_accepts_a_file_that_exists():
    repo_root = Path(__file__).resolve().parents[2]
    capabilities = [{"name": "x", "evidence": "scripts/sync_truth.py"}]

    assert missing_evidence_paths(repo_root, capabilities) == ()


def test_missing_evidence_paths_reports_a_file_that_does_not():
    repo_root = Path(__file__).resolve().parents[2]
    capabilities = [{"name": "Mobile", "evidence": "apps/mobile/lib/main.dart"}]

    assert missing_evidence_paths(repo_root, capabilities) == (
        ("Mobile", "apps/mobile/lib/main.dart"),
    )


def test_missing_evidence_paths_ignores_a_hash_beside_a_path():
    """The evidence column mixes paths with SHA-256 text; only paths resolve."""
    repo_root = Path(__file__).resolve().parents[2]
    capabilities = [
        {"name": "x", "evidence": "scripts/sync_truth.py; SHA-256 5892abc"}
    ]

    assert missing_evidence_paths(repo_root, capabilities) == ()


def test_no_capability_cites_evidence_that_does_not_exist():
    """A capability whose evidence file is gone is a claim with nothing behind it."""
    repo_root, manifest = _repo_manifest()

    missing = missing_evidence_paths(repo_root, manifest["capabilities"])

    assert missing == (), "Capabilities citing files that do not exist: " + "; ".join(
        f"{name} -> {path}" for name, path in missing
    )
