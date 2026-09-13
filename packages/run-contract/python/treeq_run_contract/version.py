"""Contract version, and the rule for changing it.

The version is part of every RunRequest and RunReport document. A consumer
reads it first and refuses a document it was not built for, which is the whole
point of versioning the package: a pipeline result that reaches a report
generator built against a different shape must fail loudly rather than be
read with the wrong field meanings.

Bump MAJOR when an existing field changes meaning or disappears, because that
is the change that silently corrupts a number already published. Bump MINOR
when a field is added that older documents will not carry. Bump PATCH for
documentation and validation-message changes that leave the shape alone.

Renaming a field counts as a meaning change even when the type is identical.
`input_sha256` -> `analysed_points_sha256` is exactly such a rename, and it is
why this contract starts at 2.0.0 rather than continuing the 0.x line of the
legacy analyze response.
"""

CONTRACT_VERSION = "2.0.0"

#: Versions this build can parse. A document outside this set is refused by
#: `treeq_run_contract.models.RunReport`, rather than parsed on the assumption
#: that the unrecognised parts do not matter.
SUPPORTED_CONTRACT_VERSIONS: frozenset[str] = frozenset({"2.0.0"})
