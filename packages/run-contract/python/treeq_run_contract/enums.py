"""Closed vocabularies for the run contract.

Every vocabulary here is closed on purpose. An open string field is where a
producer writes "ok" and a consumer reads it as "accepted", and the two words
mean different things in this project: one is about whether the code ran, the
other about whether the number it produced can be used.
"""

from __future__ import annotations

from enum import Enum


class LengthUnit(str, Enum):
    """The unit the source file's coordinates are in.

    Required on every source declaration and never defaulted. A .ply carrying
    millimetres and a .ply carrying metres are the same file extension, and the
    difference is a factor of 1000 in every diameter this pipeline reports.
    """

    METRE = "metre"
    CENTIMETRE = "centimetre"
    MILLIMETRE = "millimetre"
    FOOT = "foot"
    US_SURVEY_FOOT = "us_survey_foot"


class SourceFormat(str, Enum):
    """Container format of the uploaded point cloud, as declared."""

    PLY = "ply"
    LAS = "las"
    LAZ = "laz"
    TXT = "txt"
    XYZ = "xyz"
    CSV = "csv"


class DeclarationSource(str, Enum):
    """Where a declared physical property came from.

    There is deliberately no member for the file name. Reading a unit, a datum,
    a CRS, a species or a wood density out of a file name is guessing, and this
    enum is the mechanism that makes the guess unrepresentable: a producer that
    wants to record "I got the species from the file name" has nothing valid to
    write and must instead leave the declaration absent, which is the truth.
    """

    OPERATOR = "operator"
    FILE_HEADER = "file_header"
    DATASET_METADATA = "dataset_metadata"
    INSTRUMENT_METADATA = "instrument_metadata"


class ExecutionStatus(str, Enum):
    """Whether the code ran. Says nothing about whether the result is usable.

    This axis and `QuantityStatus` are kept apart because they disagree in both
    directions. A run that completes without raising can still produce a
    diameter that no protocol will accept, and a run that fails partway can
    still have produced usable measurements for the trees it reached.
    """

    OK = "ok"
    PARTIAL = "partial"
    FAILED = "failed"


class QuantityStatus(str, Enum):
    """Whether one derived number can be used, and under what claim."""

    #: Meets the criteria of the protocol named on the quantity.
    #:
    #: This is a statement about one named protocol and nothing else. It is not
    #: a statement of accuracy, it is not a certification, and it is not a
    #: carbon credit. A quantity may be `accepted` under a protocol whose
    #: criteria are weak, and the protocol reference is mandatory so that a
    #: reader can go and see which criteria were actually met.
    ACCEPTED = "accepted"

    #: Computed, but the protocol's criteria were not fully met.
    #:
    #: A provisional quantity carries a value, because it was computed. It may
    #: never be promoted to `accepted` by anything downstream of it, and
    #: anything that depends on it is capped at `provisional` too.
    PROVISIONAL = "provisional"

    #: Cannot be used. Carries no value at all, and a reason that says why.
    #:
    #: The value is `None` rather than 0.0 deliberately. A zero that means
    #: "we could not work this out" is the defect this contract exists to make
    #: impossible: it sums into plot totals and reads as a measured absence.
    UNUSABLE = "unusable"


class UnusableReason(str, Enum):
    """Why a quantity cannot be used.

    Required whenever a quantity is `unusable`, so the document always answers
    "why not" without a reader having to reconstruct it from the logs.
    """

    #: A quantity this one is derived from was never produced.
    DEPENDENCY_MISSING = "dependency_missing"
    #: A dependency was produced but the producer declined to stand behind it.
    DEPENDENCY_REFUSED = "dependency_refused"
    #: A dependency exists in a form this pipeline cannot consume.
    DEPENDENCY_UNSUPPORTED = "dependency_unsupported"
    #: A dependency is itself `unusable`.
    DEPENDENCY_UNUSABLE = "dependency_unusable"
    #: An input was outside the range the method is defined over.
    INPUT_OUT_OF_RANGE = "input_out_of_range"
    #: The stage that would produce this is a stub or is not built yet.
    NOT_IMPLEMENTED = "not_implemented"
    #: The run failed before this quantity could be produced.
    EXECUTION_FAILED = "execution_failed"
    #: Computed, then rejected by the protocol's own criteria.
    PROTOCOL_NOT_MET = "protocol_not_met"
