# Testing

## Running

```sh
uv run pytest --cov=doc_metadata_enricher   # tests with coverage report
uv run python scripts/check.py      # every gate, as CI and the factory run it
```

## Tests

Tests are located in `tests/test_doc_metadata_enricher.py`. They cover:

- **Acceptance**: Validating field precedence (Frontmatter > HTML > Heuristics > Detectors).
- **Date Parsing**: Validating supported formats and rejection of ambiguous all-numeric formats.
- **Language Detection**: Testing stopword frequency heuristics for supported languages (en, es, fr, de, pt).
- **Entity Extraction**: Validating email and URL regexes, offset calculation, and deduplication logic.
- **Limits**: Ensuring `max_input_chars` and `max_entities` correctly trigger truncation and errors.
- **Edge Cases**: Empty input, malformed HTML, email/URL overlaps, and CRLF line endings.