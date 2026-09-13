"""Access to the fixture corpus shared by the Python and TypeScript suites.

Both language bindings are checked against the same files on disk, so a shape
that one accepts and the other rejects shows up as a test failure rather than
as a runtime surprise at the boundary between them.

An invalid fixture carries its expectation inside the document, under
`__expect__`, so the corpus states what is wrong with each case rather than
leaving a reader to work it out:

    {"__expect__": {"error": "schema"|"semantic", "contains": "..."},
     "document": { ... }}
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

def _fixture_root() -> Path:
    """Locate the corpus in both the source tree and an installed wheel.

    Installed, the wheel carries the corpus next to the module. In the source
    tree it lives at the package root, two levels up from this file. Trying the
    installed location first means an editable install and a real install both
    read the same files rather than one of them silently reading none.
    """
    here = Path(__file__).resolve()
    packaged = here.parent / "fixtures"
    if packaged.is_dir():
        return packaged
    return here.parents[2] / "fixtures"


FIXTURE_ROOT = _fixture_root()
VALID_DIR = FIXTURE_ROOT / "valid"
INVALID_DIR = FIXTURE_ROOT / "invalid"


def _names(directory: Path) -> list[str]:
    if not directory.is_dir():
        return []
    return sorted(p.stem for p in directory.glob("*.json"))


def valid_fixture_names() -> list[str]:
    """Names of the documents every binding must accept."""
    return _names(VALID_DIR)


def invalid_fixture_names() -> list[str]:
    """Names of the documents every binding must reject."""
    return _names(INVALID_DIR)


def load_valid_fixture(name: str) -> dict[str, Any]:
    """Return one valid RunReport document."""
    payload: dict[str, Any] = json.loads(
        (VALID_DIR / f"{name}.json").read_text(encoding="utf-8")
    )
    return payload


def load_invalid_fixture(name: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return one invalid document and the expectation recorded beside it."""
    raw = json.loads((INVALID_DIR / f"{name}.json").read_text(encoding="utf-8"))
    expect = raw["__expect__"]
    document: dict[str, Any] = raw["document"]
    if expect.get("error") not in {"schema", "semantic"}:
        raise ValueError(
            f"fixture {name!r} must expect error 'schema' or 'semantic', "
            f"got {expect.get('error')!r}"
        )
    return document, expect
