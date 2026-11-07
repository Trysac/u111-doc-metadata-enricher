# doc-metadata-enricher

Documents ingested for search arrive with metadata in different places: Markdown frontmatter, HTML meta tags, a 'By' line, or nowhere at all. Without normalised title, author, date, and language fields, filtering and citation in retrieval are unreliable. This library extracts those fields with a fixed precedence and provides explicit provenance per field, all within a strictly bounded, zero-dependency environment.

## Installation

```bash
pip install trysac-doc-metadata-enricher
```

## Usage Example

```python
from doc_metadata_enricher import enrich

text = """---
title: Q3 Report
author: Ana Ruiz
date: 2026-10-01
lang: es
---
# Other"""

meta = enrich(text, fmt="markdown")
print(meta.title)  # Field(value='Q3 Report', source='frontmatter')
print(meta.date)  # Field(value='2026-10-01', source='frontmatter')
```

## Public API Summary

- `enrich(text: str, *, fmt: Literal['text', 'markdown', 'html'] = 'text', detect_language: Callable[[str], str | None] | None = None, max_input_chars: int = 2_000_000, max_entities: int = 1000) -> Metadata`
- `parse_date(s: str) -> date | None`: Parses specific formats (ISO, English Month D, YYYY, D Month YYYY, and Spanish D de mes de YYYY).
- `Metadata`: Frozen dataclass containing `title`, `author`, `date`, `language` (as `Field` objects), `entities` (tuple of `Entity`), and `entities_truncated` (bool).
- `Field`: Contains `value` (str) and `source` (Literal['frontmatter', 'html_meta', 'heuristic', 'detector']).
- `Entity`: Contains `kind`, `text`, `start`, and `end` offsets.
- `MetadataError`: Raised for inputs exceeding `max_input_chars` or invalid formats (code: `input_too_large`, `invalid_format`).

## Why not extruct?

While tools like `extruct` provide HTML metadata parsing, `doc-metadata-enricher` provides a unified precedence model across text, Markdown, and HTML. It explicitly tracks provenance for every field and enforces strict resource boundaries, all within a zero-dependency standard-library-only package.

[Security Policy](docs/SECURITY.md)