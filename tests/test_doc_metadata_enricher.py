"""Unit tests for doc_metadata_enricher."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from doc_metadata_enricher import (
    Entity,
    Field,
    MetadataError,
    enrich,
    parse_date,
)
from doc_metadata_enricher.__main__ import main


def test_acceptance_1_frontmatter() -> None:
    """Enrich Markdown with frontmatter title, author, date, and lang."""
    text = "---\ntitle: Q3 Report\nauthor: Ana Ruiz\ndate: 2026-10-01\nlang: es\n---\n# Other"
    meta = enrich(text, fmt="markdown")
    assert meta.title == Field("Q3 Report", "frontmatter")
    assert meta.author == Field("Ana Ruiz", "frontmatter")
    assert meta.date == Field("2026-10-01", "frontmatter")
    assert meta.language == Field("es", "frontmatter")


def test_acceptance_2_heuristics_markdown() -> None:
    """enrich('# Release Notes\nBy Sam Lee\nPublished November 6, 2026', fmt='markdown')"""
    text = "# Release Notes\nBy Sam Lee\nPublished November 6, 2026"
    meta = enrich(text, fmt="markdown")
    assert meta.title == Field("Release Notes", "heuristic")
    assert meta.author == Field("Sam Lee", "heuristic")
    assert meta.date == Field("2026-11-06", "heuristic")


def test_acceptance_3_html() -> None:
    """HTML meta tags, title, lang and no entity from script."""
    html_text = (
        '<html lang="fr-CA"><head><title>Rapport</title>'
        '<meta name="author" content="Luc">'
        '<meta property="article:published_time" content="2026-03-04T10:00:00Z"></head>'
        "<body><script>x@y.zz</script></body></html>"
    )
    meta = enrich(html_text, fmt="html")
    assert meta.title == Field("Rapport", "html_meta")
    assert meta.author == Field("Luc", "html_meta")
    assert meta.date == Field("2026-03-04", "html_meta")
    assert meta.language == Field("fr", "html_meta")
    assert not any("x@y.zz" in ent.text for ent in meta.entities)


def test_acceptance_4_parse_date() -> None:
    """Verify parse_date behaviour with valid and invalid dates."""
    assert parse_date("2026-02-30") is None
    assert parse_date("6 de noviembre de 2026") == date(2026, 11, 6)
    assert parse_date("6 November 2026") == date(2026, 11, 6)
    assert parse_date("31/12/2026") is None


def test_acceptance_5_language_detection() -> None:
    """Stopword heuristics and custom detector precedence."""
    text = "the cat and the dog are in the house"
    meta = enrich(text)
    assert meta.language == Field("en", "heuristic")

    short_text = "just hello"
    assert enrich(short_text).language is None

    detector_meta = enrich(short_text, detect_language=lambda _: "pt")
    assert detector_meta.language == Field("pt", "detector")

    fm_text = "---\nlang: es\n---\nhello world"
    fm_meta = enrich(fm_text, detect_language=lambda _: "pt")
    assert fm_meta.language == Field("es", "frontmatter")


def test_acceptance_6_entities() -> None:
    """Extract entities and offsets."""
    text = "Mail ana@example.com or see https://example.com/a?b=1."
    meta = enrich(text)
    assert meta.entities == (
        Entity("email", "ana@example.com", 5, 20),
        Entity("url", "https://example.com/a?b=1", 28, 53),
    )


def test_acceptance_7_bounds_and_truncation() -> None:
    """Check max_input_chars, max_entities, and title truncation."""
    long_input = "a" * 2_000_001
    with pytest.raises(MetadataError) as exc_info:
        enrich(long_input)
    assert exc_info.value.code == "input_too_large"

    many_entities_text = " ".join(f"https://example.com/{i}" for i in range(1200))
    meta_entities = enrich(many_entities_text, max_entities=1000)
    assert len(meta_entities.entities) == 1000
    assert meta_entities.entities_truncated is True

    long_title = "A" * 350
    meta_title = enrich(f"---\ntitle: {long_title}\n---\nbody")
    assert meta_title.title is not None
    assert len(meta_title.title.value) == 300
    assert meta_title.title.value == "A" * 300


def test_acceptance_8_cli(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """main CLI test with --format markdown and missing file."""
    md_file = tmp_path / "doc.md"
    md_file.write_text("# Guide\nBy Alex Fox\nPublished 2026-05-12", encoding="utf-8")

    ret = main(["--format", "markdown", str(md_file)])
    assert ret == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["title"]["value"] == "Guide"
    assert data["author"]["value"] == "Alex Fox"
    assert data["date"]["value"] == "2026-05-12"

    ret_missing = main(["--format", "markdown", str(tmp_path / "missing.md")])
    assert ret_missing == 2


def test_invalid_format() -> None:
    with pytest.raises(MetadataError) as exc:
        enrich("hello", fmt="unsupported")  # type: ignore[arg-type]
    assert exc.value.code == "invalid_format"


def test_empty_input() -> None:
    meta = enrich("")
    assert meta.title is None
    assert meta.author is None
    assert meta.date is None
    assert meta.language is None
    assert meta.entities == ()
    assert meta.entities_truncated is False


def test_crlf_and_unclosed_frontmatter() -> None:
    # CRLF in frontmatter
    text_crlf = "---\r\ntitle: Windows Doc\r\n---\r\nContent"
    meta = enrich(text_crlf)
    assert meta.title == Field("Windows Doc", "frontmatter")

    # Unclosed frontmatter is treated as body text
    unclosed = "---\ntitle: Not Frontmatter\nNo closing line"
    meta_unclosed = enrich(unclosed, fmt="text")
    assert meta_unclosed.title is not None
    assert meta_unclosed.title.source == "heuristic"


def test_author_variations() -> None:
    text1 = "Author: Jane Doe\nText"
    assert enrich(text1).author == Field("Jane Doe", "heuristic")

    text2 = "Por Carlos Ruiz\nText"
    assert enrich(text2).author == Field("Carlos Ruiz", "heuristic")


def test_date_variations() -> None:
    assert parse_date("") is None
    assert parse_date("   ") is None
    assert parse_date("2026-12-01T15:30:00Z") == date(2026, 12, 1)
    assert parse_date("November 6, 2026") == date(2026, 11, 6)
    assert parse_date("15 de setiembre de 2025") == date(2025, 9, 15)
    assert parse_date("invalid-date-string") is None
    assert parse_date("2026-13-40") is None


def test_stopwords_tie_and_other_languages() -> None:
    # German stopwords
    de_text = "das ist ein test mit der sonne und dem mond"
    assert enrich(de_text).language == Field("de", "heuristic")

    # Portuguese stopwords
    pt_text = "o livro e a caneta para um estudante"
    assert enrich(pt_text).language == Field("pt", "heuristic")

    # French stopwords
    fr_text = "le chat et la souris dans une maison pour les enfants"
    assert enrich(fr_text).language == Field("fr", "heuristic")

    # Tie between languages (1 each, below threshold anyway)
    tie_text = "the le der"
    assert enrich(tie_text).language is None


def test_html_tags_and_style_ignoring() -> None:
    html_doc = """<!DOCTYPE html>
    <html lang="en-US">
      <head>
        <title> My Website </title>
        <meta name="date" content="2025-01-15">
        <style>body { color: red; contact: test@style.com }</style>
      </head>
      <body>
        <p>Contact info@example.org</p>
        <template><p>secret@template.com</p></template>
      </body>
    </html>"""
    meta = enrich(html_doc, fmt="html")
    assert meta.title == Field("My Website", "html_meta")
    assert meta.date == Field("2025-01-15", "html_meta")
    assert meta.language == Field("en", "html_meta")
    entity_texts = [e.text for e in meta.entities]
    assert "info@example.org" in entity_texts
    assert "test@style.com" not in entity_texts
    assert "secret@template.com" not in entity_texts


def test_cli_stdin(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr("sys.stdin.read", lambda: "# Heading\nSome body content")
    ret = main(["-f", "markdown"])
    assert ret == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["title"]["value"] == "Heading"


def test_cli_metadata_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    large_f = tmp_path / "large.txt"
    large_f.write_text("a" * 2_000_001, encoding="utf-8")
    ret = main([str(large_f)])
    assert ret == 1
    err = capsys.readouterr().err
    assert "Metadata extraction error" in err


def test_cli_io_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Read error on file
    f = tmp_path / "file.txt"
    f.write_text("hello", encoding="utf-8")
    monkeypatch.setattr(
        Path, "read_text", lambda *a, **kw: (_ for _ in ()).throw(OSError("disk fail"))
    )
    assert main([str(f)]) == 2

    # Read error on stdin
    monkeypatch.setattr("sys.stdin.read", lambda: (_ for _ in ()).throw(OSError("stdin fail")))
    assert main([]) == 2


def test_cli_usage_error() -> None:
    assert main(["--format", "invalid-fmt"]) == 2
