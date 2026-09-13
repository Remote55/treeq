"""Cross-field rules that a per-field schema cannot express.

Field validation in `models.py` checks one quantity at a time. The rules that
matter most in this project are relational: they are about what a number was
derived FROM. A diameter that no protocol accepted does not stop being a
diameter, but every mass computed from it has to stop being acceptable, and
nothing about the mass's own fields records that.

The propagation rules are deliberately one-directional and monotonic:

* a dependency that is `unusable` forces the dependent to be `unusable`
* a dependency that is `provisional` caps the dependent at `provisional`
* a dependency that is `accepted` constrains nothing on its own

so status can only ever get worse as it flows downstream. There is no rule by
which combining inputs produces a result more acceptable than its worst input,
which is the direction that makes a weak result look strong.
"""

from __future__ import annotations

from dataclasses import dataclass

from .enums import ExecutionStatus, QuantityStatus, UnusableReason
from .models import Quantity, RunReport

#: Dependency names beginning with this prefix resolve against the report's
#: plot-level quantities instead of the current scope.
PLOT_PREFIX = "plot."


@dataclass(frozen=True)
class SemanticViolation:
    """One broken relational rule, located well enough to fix."""

    code: str
    path: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}: [{self.code}] {self.message}"


class SemanticError(ValueError):
    """Raised by `assert_semantics` when a report breaks a relational rule."""

    def __init__(self, violations: list[SemanticViolation]) -> None:
        self.violations = violations
        joined = "\n  ".join(str(v) for v in violations)
        super().__init__(f"{len(violations)} semantic violation(s):\n  {joined}")


def _resolve(
    dep: str,
    scope: dict[str, Quantity],
    plot: dict[str, Quantity],
) -> Quantity | None:
    if dep.startswith(PLOT_PREFIX):
        return plot.get(dep[len(PLOT_PREFIX) :])
    return scope.get(dep)


def _check_scope(
    scope: dict[str, Quantity],
    plot: dict[str, Quantity],
    path_prefix: str,
    violations: list[SemanticViolation],
) -> None:
    for name, quantity in scope.items():
        path = f"{path_prefix}{name}"
        for dep in quantity.depends_on:
            resolved = _resolve(dep, scope, plot)
            if resolved is None:
                violations.append(
                    SemanticViolation(
                        code="unresolved_dependency",
                        path=path,
                        message=(
                            f"depends on {dep!r}, which no quantity in scope "
                            "provides; a dependency that cannot be located "
                            "cannot be checked"
                        ),
                    )
                )
                continue

            if resolved.status is QuantityStatus.UNUSABLE:
                if quantity.status is not QuantityStatus.UNUSABLE:
                    violations.append(
                        SemanticViolation(
                            code="usable_from_unusable",
                            path=path,
                            message=(
                                f"is {quantity.status.value} but depends on "
                                f"{dep!r}, which is unusable "
                                f"({resolved.unusable_reason.value if resolved.unusable_reason else 'no reason'}); "
                                "a quantity derived from something nobody may "
                                "use is not usable either"
                            ),
                        )
                    )
                elif quantity.unusable_reason not in _DEPENDENCY_REASONS:
                    violations.append(
                        SemanticViolation(
                            code="wrong_unusable_reason",
                            path=path,
                            message=(
                                f"is unusable because of dependency {dep!r} but "
                                f"reports {quantity.unusable_reason.value if quantity.unusable_reason else 'nothing'}; "
                                "the reason must name the dependency failure so "
                                "a reader can follow it upstream"
                            ),
                        )
                    )

            elif resolved.status is QuantityStatus.PROVISIONAL:
                if quantity.status is QuantityStatus.ACCEPTED:
                    violations.append(
                        SemanticViolation(
                            code="accepted_from_provisional",
                            path=path,
                            message=(
                                f"is accepted but depends on {dep!r}, which is "
                                "provisional; acceptance cannot be created "
                                "downstream of an input that does not have it"
                            ),
                        )
                    )


#: Reasons that an unusable dependency can account for.
#:
#: The four DEPENDENCY_* reasons point at the upstream quantity. EXECUTION_FAILED
#: is here because it is a whole-run cause: when the run died, every quantity is
#: unusable for that reason, including the ones whose dependencies also went
#: unusable in the same collapse. Demanding DEPENDENCY_UNUSABLE there would force
#: a document to report the symptom in place of the cause.
_DEPENDENCY_REASONS = frozenset(
    {
        UnusableReason.DEPENDENCY_MISSING,
        UnusableReason.DEPENDENCY_REFUSED,
        UnusableReason.DEPENDENCY_UNSUPPORTED,
        UnusableReason.DEPENDENCY_UNUSABLE,
        UnusableReason.EXECUTION_FAILED,
    }
)


def _detect_cycles(
    scope: dict[str, Quantity],
    plot: dict[str, Quantity],
    path_prefix: str,
    violations: list[SemanticViolation],
) -> None:
    """Report any quantity that is, transitively, derived from itself."""
    WHITE, GREY, BLACK = 0, 1, 2
    colour: dict[str, int] = {name: WHITE for name in scope}

    def visit(name: str, trail: tuple[str, ...]) -> None:
        if colour.get(name) == BLACK:
            return
        if colour.get(name) == GREY:
            loop = " -> ".join((*trail, name))
            violations.append(
                SemanticViolation(
                    code="dependency_cycle",
                    path=f"{path_prefix}{name}",
                    message=(
                        f"is derived from itself via {loop}; a cycle has no "
                        "upstream to inherit status from"
                    ),
                )
            )
            return
        colour[name] = GREY
        quantity = scope.get(name)
        if quantity is not None:
            for dep in quantity.depends_on:
                # Only same-scope edges can close a cycle here; a `plot.` edge
                # leaves this scope and is checked when the plot scope is walked.
                if not dep.startswith(PLOT_PREFIX) and dep in scope:
                    visit(dep, (*trail, name))
        colour[name] = BLACK

    for name in scope:
        visit(name, ())


def validate_semantics(report: RunReport) -> list[SemanticViolation]:
    """Return every relational rule this report breaks, in document order."""
    violations: list[SemanticViolation] = []
    plot = report.quantities

    _detect_cycles(plot, plot, "quantities.", violations)
    _check_scope(plot, plot, "quantities.", violations)

    for tree in report.trees:
        prefix = f"trees[{tree.tree_id}].quantities."
        _detect_cycles(tree.quantities, plot, prefix, violations)
        _check_scope(tree.quantities, plot, prefix, violations)

    if report.execution.status is ExecutionStatus.FAILED:
        for scope, prefix in _all_scopes(report):
            for name, quantity in scope.items():
                if quantity.status is not QuantityStatus.UNUSABLE:
                    violations.append(
                        SemanticViolation(
                            code="accepted_after_failure",
                            path=f"{prefix}{name}",
                            message=(
                                f"is {quantity.status.value} but the run's "
                                "execution status is failed; a run that did not "
                                "finish has not established any number"
                            ),
                        )
                    )
    return violations


def _all_scopes(report: RunReport) -> list[tuple[dict[str, Quantity], str]]:
    scopes: list[tuple[dict[str, Quantity], str]] = [(report.quantities, "quantities.")]
    for tree in report.trees:
        scopes.append((tree.quantities, f"trees[{tree.tree_id}].quantities."))
    return scopes


def assert_semantics(report: RunReport) -> None:
    """Raise `SemanticError` if the report breaks any relational rule."""
    violations = validate_semantics(report)
    if violations:
        raise SemanticError(violations)
