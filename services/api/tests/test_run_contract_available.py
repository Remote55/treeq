"""The API can import the shared contract, and the legacy response is untouched.

The contract is additive. `POST /upload/analyze` still returns AnalyzeResponse
and still means exactly what it meant before this package existed. These tests
exist so that stays true while the two shapes coexist: the failure mode worth
guarding against is someone "migrating" the legacy response by renaming its
fields to the contract's names, which would change what published numbers mean
without changing any number.
"""

from __future__ import annotations

from app.schemas.analyze import AnalyzeMetadata, AnalyzeResponse, AnalyzeTree
from treeq_run_contract import (
    CONTRACT_VERSION,
    QuantityStatus,
    RunReport,
    load_valid_fixture,
    validate_semantics,
)


def test_contract_is_installed_in_the_api_environment() -> None:
    assert CONTRACT_VERSION == "2.0.0"


def test_a_contract_document_validates_here() -> None:
    report = RunReport.model_validate(load_valid_fixture("accepted_single_tree"))
    assert validate_semantics(report) == []
    assert report.provenance.n_analysed_points < report.provenance.n_source_points


def test_the_legacy_analyze_response_still_exists_unchanged() -> None:
    """AnalyzeResponse is not RunReport and must not be quietly replaced."""
    assert set(AnalyzeResponse.model_fields) == {
        "metadata",
        "summary",
        "trees",
        "diagnostics",
        "segmented_cloud_id",
    }
    assert "contract_version" not in AnalyzeResponse.model_fields


def test_legacy_biomass_kg_keeps_its_meaning() -> None:
    """Legacy biomass_kg is AGB+BGB. Renaming it to AGB would restate results.

    allometric.calculate_carbon sets `biomass = agb + bgb`, and every number
    already published through this field carries that meaning. The contract
    spells the same quantity `biomass_total_kg` precisely so the two can coexist
    without one being mistaken for the other.
    """
    assert "biomass_kg" in AnalyzeTree.model_fields
    assert "agb_kg" not in AnalyzeTree.model_fields
    assert "biomass_total_kg" not in AnalyzeTree.model_fields

    tree_quantities = RunReport.model_fields["trees"]  # presence check only
    assert tree_quantities is not None

    report = RunReport.model_validate(load_valid_fixture("accepted_single_tree"))
    quantities = report.trees[0].quantities
    assert "biomass_total_kg" in quantities
    assert "biomass_kg" not in quantities


def test_the_legacy_hash_field_is_not_renamed_in_place() -> None:
    """input_sha256 stays on the legacy metadata; the contract renames nothing.

    The legacy name reads like a file hash and is not one, but the fix is a new
    field on a new contract, not a rename that changes what stored results claim.
    """
    assert "input_sha256" in AnalyzeMetadata.model_fields
    assert "analysed_points_sha256" not in AnalyzeMetadata.model_fields


def test_legacy_results_carry_no_acceptance() -> None:
    """A legacy result has no protocol behind it, so it cannot be 'accepted'.

    Nothing in the legacy response records which criteria a number met, so no
    adapter may mint that claim on the way out. This asserts the legacy shape
    has no field that could carry one.
    """
    legacy_fields = set(AnalyzeTree.model_fields) | set(AnalyzeMetadata.model_fields)
    assert not {"status", "accepted", "protocol"} & legacy_fields - {"status"}
    # `status` on the metadata is the execution axis ("ok"), not acceptance.
    assert AnalyzeMetadata.model_fields["status"].annotation is str
    assert QuantityStatus.ACCEPTED.value == "accepted"
