"""Versioned RunRequest/RunReport contract shared by the API, the ML pipeline
and the web client.

The Python models in here are the source of truth. The JSON Schema in
`schema/`, and the TypeScript types and Zod validators in `typescript/src/`,
are generated from them by `tools/generate_contract.py` and are checked for
drift in CI - see that script's `--check` mode.
"""

from .enums import (
    DeclarationSource,
    ExecutionStatus,
    LengthUnit,
    QuantityStatus,
    SourceFormat,
    UnusableReason,
)
from .fixtures import (
    invalid_fixture_names,
    load_invalid_fixture,
    load_valid_fixture,
    valid_fixture_names,
)
from .models import (
    CrsDeclaration,
    DeclaredDensity,
    ProtocolRef,
    Quantity,
    RunExecution,
    RunProvenance,
    RunReport,
    RunRequest,
    SensitivityRange,
    SourceDeclaration,
    SpeciesDeclaration,
    TreeReport,
)
from .semantics import (
    SemanticError,
    SemanticViolation,
    assert_semantics,
    validate_semantics,
)
from .version import CONTRACT_VERSION, SUPPORTED_CONTRACT_VERSIONS

__all__ = [
    "CONTRACT_VERSION",
    "SUPPORTED_CONTRACT_VERSIONS",
    "CrsDeclaration",
    "DeclarationSource",
    "DeclaredDensity",
    "ExecutionStatus",
    "LengthUnit",
    "ProtocolRef",
    "Quantity",
    "QuantityStatus",
    "RunExecution",
    "RunProvenance",
    "RunReport",
    "RunRequest",
    "SemanticError",
    "SemanticViolation",
    "SensitivityRange",
    "SourceDeclaration",
    "SourceFormat",
    "SpeciesDeclaration",
    "TreeReport",
    "UnusableReason",
    "assert_semantics",
    "invalid_fixture_names",
    "load_invalid_fixture",
    "load_valid_fixture",
    "valid_fixture_names",
    "validate_semantics",
]
