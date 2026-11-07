"""Behavior tests for the public API of doc_metadata_enricher."""

from __future__ import annotations

import pytest

import doc_metadata_enricher


def test_normalize_trims_and_lowercases() -> None:
    assert doc_metadata_enricher.normalize("  Hello World ") == "hello world"


@pytest.mark.parametrize("value", ["", "   ", "\t\n"])
def test_normalize_rejects_blank_input(value: str) -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        doc_metadata_enricher.normalize(value)


def test_version_is_semver() -> None:
    parts = doc_metadata_enricher.__version__.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)
