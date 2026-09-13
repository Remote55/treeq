"""Contract behaviour, checked against the shared fixture corpus.

Every case here is about a defect this project has actually had, or a rule in
CLAUDE.md that had no mechanical enforcement before this package existed. The
fixtures are the same files the TypeScript suite reads, so a rule that holds
here and not there shows up as a failure rather than at the process boundary.
"""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

import pytest
from pydantic import ValidationError

from treeq_run_contract import (
    CONTRACT_VERSION,
    DeclarationSource,
    QuantityStatus,
    RunReport,
    SemanticError,
    SensitivityRange,
    assert_semantics,
    invalid_fixture_names,
    load_invalid_fixture,
    load_valid_fixture,
    valid_fixture_names,
    validate_semantics,
)

PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def test_corpus_is_not_empty() -> None:
    """A green suite that validated nothing is the failure mode to avoid."""
    assert valid_fixture_names()
    assert invalid_fixture_names()


@pytest.mark.parametrize("name", valid_fixture_names())
def test_valid_fixture_parses_and_passes_semantics(name: str) -> None:
    report = RunReport.model_validate(load_valid_fixture(name))
    assert not validate_semantics(report)


@pytest.mark.parametrize("name", valid_fixture_names())
def test_valid_fixture_round_trips(name: str) -> None:
    """Serialising and re-parsing must not change the document."""
    original = load_valid_fixture(name)
    once = RunReport.model_validate(original).to_document()
    twice = RunReport.model_validate(once).to_document()
    assert once == twice


@pytest.mark.parametrize("name", invalid_fixture_names())
def test_invalid_fixture_is_rejected_for_the_stated_reason(name: str) -> None:
    document, expect = load_invalid_fixture(name)
    contains = expect["contains"].lower()

    if expect["error"] == "schema":
        with pytest.raises(ValidationError) as caught:
            RunReport.model_validate(document)
        assert contains in str(caught.value).lower()
        return

    # A semantic case must survive schema validation - otherwise it is not
    # testing the relational rule it claims to test.
    report = RunReport.model_validate(document)
    violations = validate_semantics(report)
    assert violations, f"{name} was expected to break a relational rule"
    assert contains in " ".join(v.code for v in violations).lower()
    with pytest.raises(SemanticError):
        assert_semantics(report)


def test_package_version_tracks_contract_version() -> None:
    pyproject = tomllib.loads(
        (PACKAGE_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    assert pyproject["project"]["version"] == CONTRACT_VERSION


def test_a_real_zero_is_not_missing() -> None:
    """0.0 counted and "not recorded" are different documents, both legal."""
    report = RunReport.model_validate(load_valid_fixture("accepted_single_tree"))
    excluded = report.quantities["excluded_tree_count"]
    assert excluded.value == 0.0
    assert excluded.status is QuantityStatus.ACCEPTED

    document = load_valid_fixture("accepted_single_tree")
    document["quantities"]["excluded_tree_count"]["value"] = None
    with pytest.raises(ValidationError):
        # Missing cannot be dressed as an accepted zero.
        RunReport.model_validate(document)


def test_unusable_quantity_carries_no_number() -> None:
    report = RunReport.model_validate(
        load_valid_fixture("unusable_from_refused_dependency")
    )
    tree = report.trees[0]
    for name in ("dbh_cm", "agb_kg", "biomass_total_kg", "co2eq_kg"):
        quantity = tree.quantities[name]
        assert quantity.status is QuantityStatus.UNUSABLE
        assert quantity.value is None, f"{name} offered a number it refused"
        assert quantity.unusable_reason is not None


def test_provisional_dependency_caps_downstream() -> None:
    report = RunReport.model_validate(
        load_valid_fixture("species_unknown_chave_fallback")
    )
    tree = report.trees[0]
    assert tree.quantities["co2eq_kg"].status is QuantityStatus.PROVISIONAL
    assert not validate_semantics(report)

    # Promoting the downstream number alone is exactly the move the rule exists
    # to stop.
    document = load_valid_fixture("species_unknown_chave_fallback")
    promoted = document["trees"][0]["quantities"]["co2eq_kg"]
    promoted["status"] = "accepted"
    promoted["protocol"] = {
        "id": "treeq-geometry-v1",
        "version": "1.0.0",
        "criteria_uri": None,
    }
    violations = validate_semantics(RunReport.model_validate(document))
    assert [v.code for v in violations] == ["accepted_from_provisional"]


def test_declaration_source_cannot_be_a_filename() -> None:
    """The enum has no filename member, so the guess is unrepresentable."""
    assert "filename" not in {member.value for member in DeclarationSource}


def test_sensitivity_range_may_not_claim_to_be_a_confidence_interval() -> None:
    with pytest.raises(ValidationError, match="confidence interval"):
        SensitivityRange(
            low=1.0, high=2.0, basis="95% confidence interval on the estimate"
        )
    # The honest description of the same numbers is accepted.
    assert SensitivityRange(
        low=1.0, high=2.0, basis="recomputed at the ends of the density range"
    ).basis


def test_analysed_hash_is_not_called_a_file_hash() -> None:
    """The rename is the reason this contract is 2.0.0 rather than 0.5.0."""
    fields = set(RunReport.model_fields)
    provenance_fields = set(
        RunReport.model_fields["provenance"].annotation.model_fields  # type: ignore[union-attr]
    )
    assert "analysed_points_sha256" in provenance_fields
    assert "input_sha256" not in provenance_fields
    assert "file_sha256" not in provenance_fields
    assert fields  # guards against the model losing its fields entirely


def test_analysed_and_source_hashes_are_separate_values() -> None:
    report = RunReport.model_validate(load_valid_fixture("accepted_single_tree"))
    assert report.provenance.analysed_points_sha256 != report.request.source.file_sha256
    assert report.provenance.n_analysed_points < report.provenance.n_source_points
    assert report.provenance.analysed_point_fraction == pytest.approx(0.04)


def test_biomass_total_is_above_plus_below_ground() -> None:
    """Legacy biomass_kg holds AGB+BGB; the new name must mean the same."""
    report = RunReport.model_validate(load_valid_fixture("accepted_single_tree"))
    quantities = report.trees[0].quantities
    agb = quantities["agb_kg"].value
    bgb = quantities["bgb_kg"].value
    total = quantities["biomass_total_kg"].value
    assert agb is not None and bgb is not None and total is not None
    assert total == pytest.approx(agb + bgb)
    assert set(quantities["biomass_total_kg"].depends_on) == {"agb_kg", "bgb_kg"}


def test_fixtures_on_disk_are_canonical_json() -> None:
    """Fixtures are regenerated, not hand-edited; drift shows up here."""
    for directory in ("valid", "invalid"):
        for path in sorted((PACKAGE_ROOT / "fixtures" / directory).glob("*.json")):
            raw = path.read_text(encoding="utf-8")
            expected = (
                json.dumps(json.loads(raw), indent=2, sort_keys=True, ensure_ascii=False)
                + "\n"
            )
            assert raw == expected, f"{path.name} is not canonical; regenerate it"
