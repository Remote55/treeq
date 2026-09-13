"""The ML service can import the shared contract, and the two agree.

Scope note: this file deliberately imports only `pipeline.provenance`, not
`pipeline.main`. provenance owns both couplings that matter here - the
algorithm map that lands in a report, and the point hash the contract names -
and it needs nothing beyond numpy, so this stays a seconds-long check rather
than one that drags in scipy, laspy and scikit-image. Running the pipeline
end-to-end against the contract is a separate, heavier test.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from pipeline.provenance import ALGORITHM_MAP, hash_points, sha256_bytes
from treeq_run_contract import CONTRACT_VERSION, RunProvenance

import numpy as np

COMMIT = "c" * 40


def _provenance(**overrides: object) -> RunProvenance:
    payload: dict[str, object] = {
        "pipeline_version": "0.4.0",
        "git_commit": COMMIT,
        "git_dirty": False,
        "algorithms": dict(ALGORITHM_MAP),
        "wood_leaf_backend": "tlsep",
        "checkpoint_sha256": None,
        "analysed_points_sha256": "b" * 64,
        "n_source_points": 5_000_000,
        "n_analysed_points": 200_000,
    }
    payload.update(overrides)
    return RunProvenance.model_validate(payload)


def test_contract_is_installed() -> None:
    assert CONTRACT_VERSION == "2.0.0"


def test_algorithm_map_fits_the_contract() -> None:
    """Every stage this pipeline names must survive the trip into a report."""
    provenance = _provenance()
    assert provenance.algorithms == ALGORITHM_MAP
    assert set(provenance.algorithms) == set(ALGORITHM_MAP)
    for stage, algorithm in ALGORITHM_MAP.items():
        assert isinstance(stage, str) and stage
        assert isinstance(algorithm, str) and algorithm


def test_point_hash_is_accepted_as_the_analysed_hash() -> None:
    points = np.array([[0.0, 0.0, 0.0], [1.5, 2.5, 3.5]], dtype="<f8")
    digest = hash_points(points)
    provenance = _provenance(
        analysed_points_sha256=digest,
        n_source_points=2,
        n_analysed_points=2,
    )
    assert provenance.analysed_points_sha256 == digest


def test_the_analysed_hash_is_not_the_file_hash() -> None:
    """The distinction the contract exists to keep straight.

    pipeline.main fills the legacy `input_sha256` from `hash_points(points)`,
    which covers the thinned float64 XYZ array and not the uploaded bytes. The
    contract carries that value as `analysed_points_sha256` and keeps the file's
    own digest on the request, because for any thinned run they are different
    numbers describing different things.
    """
    file_bytes = b"ply\nformat ascii 1.0\nelement vertex 2\n0 0 0\n1 1 1\n"
    file_digest = sha256_bytes(file_bytes)
    analysed = hash_points(np.array([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]], dtype="<f8"))
    assert analysed != file_digest

    provenance = _provenance(analysed_points_sha256=analysed)
    assert provenance.analysed_points_sha256 == analysed
    assert not hasattr(provenance, "input_sha256")
    assert not hasattr(provenance, "file_sha256")


def test_thinning_is_recorded_rather_than_implied() -> None:
    provenance = _provenance()
    assert provenance.n_analysed_points < provenance.n_source_points
    assert provenance.analysed_point_fraction == pytest.approx(0.04)


def test_a_cloud_cannot_be_larger_than_its_source() -> None:
    with pytest.raises(ValidationError, match="exceeds"):
        _provenance(n_source_points=1_000, n_analysed_points=5_000)
