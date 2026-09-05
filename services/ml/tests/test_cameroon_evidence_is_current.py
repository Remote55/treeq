"""The published tropical figures still reproduce from the cohort.

`docs/evidence/cameroon_61/result.json` is the derived source for every
tropical number this project publishes: the diameter error on the trees the
gate passes, the count it refuses, and the two allometric routes scored
against mass that was actually weighed. Those numbers reach the manifest, the
truth block in docs/PROJECT_SPEC.md and the landing page's accuracy panel.

`scripts/sync_truth.py` holds the manifest to this artefact byte for byte, and
that check runs on CI. What it cannot check is the step before: whether the
artefact still reproduces from the 61 trees. That needs the 1.29 GB archive,
so it lives here and skips where the archive is absent -- the same shape, and
the same limitation, as test_published_evidence_is_current.py for Demol.

See docs/ml/WHAT_CI_DOES_NOT_CHECK.md.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

ML_ROOT = Path(__file__).resolve().parent.parent
ARCHIVE = ML_ROOT / "data" / "raw" / "dryad_cameroon" / "Trees"
ARTEFACT = ML_ROOT.parent.parent / "docs" / "evidence" / "cameroon_61" / "result.json"

needs_archive = pytest.mark.skipif(
    not (ARCHIVE / "database.xls").is_file(),
    reason="Cameroon archive not present: see docs/ml/CAMEROON_EVIDENCE_CHAIN.md",
)

#: How far a fresh run may sit from the published artefact before it is stale.
#:
#: Not a precision claim, and read the same way as the Demol file's: the
#: protocol fixes the 61-tree keying, the 20,000-point cap and the seed, so an
#: unchanged pipeline reproduces the artefact exactly. The tolerance exists so
#: a refactor or a platform float difference does not turn the build red.
#:
#: The gated figure gets the tightest band of the three because it is the one a
#: user is handed. It is an average over 27 trees, so a single tree moving in or
#: out of the gate shifts it by more than a refactor ever should -- which is
#: precisely the change this file exists to catch.
TOLERANCES = {
    "dbh_gate_applied_mae_cm": 0.05,
    "dbh_mae_cm": 0.20,
    "height_mae_m": 0.10,
    "volume_mape_pct": 2.00,
    "chave_route_b_ape_pct_median": 0.50,
    "tver_route_b_ape_pct_median": 0.50,
}

#: Counts, not measurements. A tolerance would be meaningless: the gate either
#: passes the same trees or it does not, and if it does not, every figure above
#: is an average over a different population than the published one.
EXACT_FIELDS = (
    "cohort_size",
    "trees_measured",
    "trees_excluded",
    "gate_passed_trees",
    "gate_refused_trees",
    "dbh_mae_cm_small_stems_n",
)


@pytest.fixture(scope="module")
def published() -> dict[str, Any]:
    return json.loads(ARTEFACT.read_text(encoding="utf-8"))["metrics"]


@pytest.fixture(scope="module")
def measured() -> dict[str, Any]:
    """A fresh run of the derivation the published artefact came from.

    Imports the script rather than reimplementing it, for the reason the Demol
    file gives: a test that recomputed these statistics its own way would pass
    while the script that writes the published file was broken.
    """
    sys.path.insert(0, str(ML_ROOT / "scripts"))
    try:
        from derive_cameroon_evidence import derive
    finally:
        sys.path.pop(0)

    return derive(archive_root=ARCHIVE)["metrics"]


@needs_archive
@pytest.mark.parametrize("field", sorted(TOLERANCES))
def test_the_published_figures_have_not_drifted(field, published, measured):
    drift = measured[field] - published[field]

    assert abs(drift) <= TOLERANCES[field], (
        f"{field}: published {published[field]}, measured {measured[field]} "
        f"({drift:+.4f}). Re-run scripts/derive_cameroon_evidence.py, repin the "
        "manifest from it, and re-run sync_truth.py --write."
    )


@needs_archive
@pytest.mark.parametrize("field", EXACT_FIELDS)
def test_the_cohort_and_the_gate_still_partition_it_the_same_way(
    field, published, measured
):
    assert measured[field] == published[field], (
        f"{field}: published {published[field]}, measured {measured[field]}. "
        "The gate is passing a different set of trees, so every averaged "
        "figure in this artefact is an average over a different population."
    )


@needs_archive
def test_every_published_field_still_reproduces(published, measured):
    """The six in TOLERANCES are the quoted ones. An artefact is only as
    current as its least-checked number, so the rest are compared too."""
    stale = sorted(
        field
        for field, value in published.items()
        if isinstance(value, (int, float))
        and field not in TOLERANCES
        and field not in EXACT_FIELDS
        and field in measured
        and abs(measured[field] - value) > 0.01
    )

    assert not stale, (
        f"{stale} no longer reproduce. Run "
        "scripts/derive_cameroon_evidence.py --check for the full comparison."
    )


def test_the_artefact_the_manifest_cites_is_present():
    """Runs everywhere, archive or not. sync_truth.py's validate_cameroon
    re-hashes this file on every --check; if it is gone, that check has
    nothing to compare the manifest against."""
    assert ARTEFACT.is_file(), f"{ARTEFACT} is missing"
