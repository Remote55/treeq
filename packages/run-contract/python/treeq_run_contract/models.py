"""Strict shapes for one pipeline run: what was asked for, and what came back.

Every model here forbids unknown fields. A producer that grows a field without
bumping the contract fails at the boundary instead of shipping a document whose
extra key some consumer silently drops.

Two naming decisions in here are load-bearing and should not be "tidied":

* `analysed_points_sha256` hashes the float64 XYZ array the measurement
  actually ran on, after thinning. It is NOT the hash of the uploaded file.
  The legacy analyze response calls this same value `input_sha256`, which reads
  like a file hash and is not one - see pipeline.main.process_points, which
  fills it from `hash_points(points)`. The file's own digest is
  `source.file_sha256`, and the two are different numbers for any run that was
  thinned.
* `biomass_total_kg` is above-ground plus below-ground, matching what the
  legacy `biomass_kg` field has always held (allometric.calculate_carbon sets
  `biomass = agb + bgb`). It is spelled out here so nobody "corrects" it into
  AGB later; `agb_kg` and `bgb_kg` are carried separately for anyone who needs
  one of the halves.
"""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .enums import (
    DeclarationSource,
    ExecutionStatus,
    LengthUnit,
    QuantityStatus,
    SourceFormat,
    UnusableReason,
)
from .version import CONTRACT_VERSION, SUPPORTED_CONTRACT_VERSIONS

Sha256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


class _Strict(BaseModel):
    """Base for every contract model: unknown fields are an error."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class ProtocolRef(_Strict):
    """The named criteria a quantity was judged against.

    Mandatory on every `accepted` quantity. Without it, "accepted" is a bare
    assertion; with it, a reader can fetch the criteria and disagree.
    """

    id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    #: Where the criteria are written down. Optional because some protocols in
    #: this project are defined by a document in this repository rather than a
    #: public URI, but a protocol nobody can look up is a weak one.
    criteria_uri: str | None = None


class CrsDeclaration(_Strict):
    """A declared coordinate reference system.

    Absent means nobody declared one. It does not mean WGS84, and no consumer
    may substitute a default.
    """

    authority: str = Field(min_length=1, examples=["EPSG"])
    code: str = Field(min_length=1, examples=["32632"])
    source: DeclarationSource


class DeclaredDensity(_Strict):
    """Wood density, with where the number came from.

    A density is never a bare float in this contract. The pipeline does not
    measure density, and the value chosen moves every mass it reports roughly
    proportionally, so the reference travels with it.
    """

    value_g_cm3: float = Field(gt=0.0, le=2.0)
    source: DeclarationSource
    #: Citation for the value: a species database row, a published table, a
    #: field measurement report.
    reference: str = Field(min_length=1)


class SpeciesDeclaration(_Strict):
    """A declared species. Absent means unknown, never "assume something"."""

    scientific_name: str = Field(min_length=1)
    source: DeclarationSource


class SourceDeclaration(_Strict):
    """The uploaded file and the physical facts that cannot be read off it."""

    file_name: str = Field(min_length=1)
    #: Digest of the bytes as uploaded. Distinct from
    #: `RunProvenance.analysed_points_sha256`.
    file_sha256: Sha256
    byte_size: int = Field(ge=0)
    format: SourceFormat
    #: Required, never inferred. See LengthUnit.
    length_unit: LengthUnit
    length_unit_source: DeclarationSource
    #: None means undeclared. Consumers must treat an undeclared CRS as absent
    #: and refuse anything that needs one, not fall back to a guess.
    crs: CrsDeclaration | None = None
    vertical_datum: str | None = None


class RunRequest(_Strict):
    """Everything the pipeline was told before it ran.

    Nothing in here is derived from the file name. The properties a file name
    is commonly abused to supply - unit, CRS, datum, species, density - are
    either required with an explicit `DeclarationSource`, or optional and
    genuinely absent when undeclared.
    """

    contract_version: str = CONTRACT_VERSION
    request_id: str = Field(min_length=1)
    source: SourceDeclaration
    #: None means the species is unknown, which is a supported state: the
    #: allometric stage falls back to Chave and must say so on the quantity.
    species: SpeciesDeclaration | None = None
    #: None means no density was declared, and the allometric stage must supply
    #: one from a named reference and record that choice.
    wood_density: DeclaredDensity | None = None
    wood_leaf_backend: str = Field(min_length=1)
    #: The protocol the caller is asking the run to be judged against.
    protocol: ProtocolRef
    #: Thinning ceiling. The run records what it actually analysed in
    #: `RunProvenance`, which is what a reader should trust.
    max_points: int | None = Field(default=None, ge=1)

    @field_validator("contract_version")
    @classmethod
    def _known_version(cls, value: str) -> str:
        if value not in SUPPORTED_CONTRACT_VERSIONS:
            raise ValueError(
                f"unsupported contract_version {value!r}; "
                f"this build reads {sorted(SUPPORTED_CONTRACT_VERSIONS)}"
            )
        return value


class SensitivityRange(_Strict):
    """A range produced by varying an assumption, not a confidence interval.

    The low and high ends of this range come from recomputing the same number
    at the ends of a plausible input range - in this pipeline, wood density.
    That is not a 95% confidence interval and must never be relabelled as one:
    it contains no sampling distribution, no error model for the measurement,
    and no allowance for the allometric equation being wrong.

    The basis text is required, and a basis that claims an interval this range
    is not is refused outright.
    """

    low: float
    high: float
    #: What was varied to produce the ends, in words.
    basis: str = Field(min_length=1)

    @model_validator(mode="after")
    def _ordered(self) -> SensitivityRange:
        if self.low > self.high:
            raise ValueError(f"sensitivity low {self.low} exceeds high {self.high}")
        return self

    @field_validator("basis")
    @classmethod
    def _not_a_confidence_interval(cls, value: str) -> str:
        lowered = value.lower()
        for claim in ("confidence interval", "95% ci", "95%ci", "credible interval"):
            if claim in lowered:
                raise ValueError(
                    "a sensitivity range may not be described as a "
                    f"{claim!r}; it varies an assumption and carries no "
                    "sampling distribution"
                )
        return value


class Quantity(_Strict):
    """One derived number, its status, and what it was derived from.

    The `value`/`status` pairing is the contract's core rule:

    * `accepted` and `provisional` carry a value and a unit.
    * `unusable` carries `value=None` and an `unusable_reason`.
    * `value=0.0` is a real zero and is only ever written when the quantity
      really is zero. Missing is `None`, and the two are never interchanged.
    """

    value: float | None = None
    unit: str = Field(min_length=1)
    status: QuantityStatus
    #: Required when `accepted`.
    protocol: ProtocolRef | None = None
    #: Names of the quantities this one is derived from. A name beginning with
    #: `plot.` resolves against the report's plot-level quantities; any other
    #: name resolves within the same scope (the same tree, or the plot).
    depends_on: tuple[str, ...] = ()
    #: Required when `unusable`.
    unusable_reason: UnusableReason | None = None
    #: Free text saying how the number was arrived at, or why it was refused.
    basis: str | None = None
    sensitivity: SensitivityRange | None = None

    @model_validator(mode="after")
    def _status_matches_payload(self) -> Quantity:
        if self.status is QuantityStatus.UNUSABLE:
            if self.value is not None:
                raise ValueError(
                    "an unusable quantity must not carry a value; a number "
                    "nobody may use still gets summed if it is present"
                )
            if self.unusable_reason is None:
                raise ValueError("an unusable quantity must say why it is unusable")
            if self.sensitivity is not None:
                raise ValueError("an unusable quantity has nothing to be sensitive to")
        else:
            if self.value is None:
                raise ValueError(
                    f"a {self.status.value} quantity must carry a value; use "
                    "status=unusable when there is no number"
                )
            if self.unusable_reason is not None:
                raise ValueError(
                    f"a {self.status.value} quantity must not carry an "
                    "unusable_reason"
                )
        if self.status is QuantityStatus.ACCEPTED and self.protocol is None:
            raise ValueError(
                "an accepted quantity must name the protocol whose criteria it "
                "met; 'accepted' on its own is not a checkable claim"
            )
        return self


class RunProvenance(_Strict):
    """Which code, which inputs, and how much of the input was actually used."""

    pipeline_version: str = Field(min_length=1)
    git_commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    git_dirty: bool
    #: Stage name -> algorithm identifier.
    algorithms: dict[str, str]
    wood_leaf_backend: str = Field(min_length=1)
    checkpoint_sha256: Sha256 | None = None
    #: Hash of the XYZ array the measurement ran on, AFTER thinning. Not a file
    #: hash. See the module docstring.
    analysed_points_sha256: Sha256
    #: Points in the source file.
    n_source_points: int = Field(ge=0)
    #: Points that reached the measurement.
    n_analysed_points: int = Field(ge=0)

    @model_validator(mode="after")
    def _analysed_fits_in_source(self) -> RunProvenance:
        if self.n_analysed_points > self.n_source_points:
            raise ValueError(
                f"n_analysed_points={self.n_analysed_points} exceeds "
                f"n_source_points={self.n_source_points}; a thinned cloud "
                "cannot be larger than the file it came from"
            )
        return self

    @property
    def analysed_point_fraction(self) -> float | None:
        """Share of the source that was measured, or None for an empty source.

        Derived rather than stored, so it cannot drift from the two counts.
        """
        if self.n_source_points == 0:
            return None
        return self.n_analysed_points / self.n_source_points


class RunExecution(_Strict):
    """Whether the code ran. Kept apart from whether the numbers are usable."""

    status: ExecutionStatus
    started_at: str = Field(min_length=1)
    finished_at: str = Field(min_length=1)
    error_code: str | None = None
    error_message: str | None = None

    @model_validator(mode="after")
    def _failure_is_explained(self) -> RunExecution:
        failed = self.status is ExecutionStatus.FAILED
        if failed and not self.error_code:
            raise ValueError("a failed run must carry an error_code")
        if not failed and self.error_code:
            raise ValueError(
                f"execution status {self.status.value} must not carry an "
                "error_code; use status=failed or status=partial"
            )
        return self


class TreeReport(_Strict):
    """One detected tree and every quantity derived for it."""

    tree_id: int
    #: Quantity name -> quantity. Names are scope-local; a tree quantity may
    #: depend on another quantity of the same tree, or on `plot.<name>`.
    quantities: dict[str, Quantity]
    point_count: int = Field(ge=0)
    species: SpeciesDeclaration | None = None


class RunReport(_Strict):
    """The full, versioned result of one pipeline run."""

    contract_version: str = CONTRACT_VERSION
    run_id: str = Field(min_length=1)
    request: RunRequest
    execution: RunExecution
    provenance: RunProvenance
    #: Plot-level quantities, referenced from trees as `plot.<name>`.
    quantities: dict[str, Quantity] = Field(default_factory=dict)
    trees: tuple[TreeReport, ...] = ()
    #: What this run does not establish. Present so that a report cannot be
    #: read as a broader claim than it is.
    limitations: tuple[str, ...] = ()

    @field_validator("contract_version")
    @classmethod
    def _known_version(cls, value: str) -> str:
        if value not in SUPPORTED_CONTRACT_VERSIONS:
            raise ValueError(
                f"unsupported contract_version {value!r}; "
                f"this build reads {sorted(SUPPORTED_CONTRACT_VERSIONS)}"
            )
        return value

    @model_validator(mode="after")
    def _request_version_agrees(self) -> RunReport:
        if self.request.contract_version != self.contract_version:
            raise ValueError(
                f"report contract_version {self.contract_version!r} does not "
                f"match request contract_version "
                f"{self.request.contract_version!r}"
            )
        return self

    def to_document(self) -> dict[str, Any]:
        """Serialise to a plain JSON-ready document."""
        return self.model_dump(mode="json")
