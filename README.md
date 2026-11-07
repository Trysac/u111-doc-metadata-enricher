# doc-metadata-enricher

[![PyPI version](https://img.shields.io/pypi/v/trysac-doc-metadata-enricher)](https://pypi.org/project/trysac-doc-metadata-enricher/)
[![License: MIT](https://img.shields.io/pypi/l/trysac-doc-metadata-enricher)](LICENSE)
[![CI](https://github.com/Trysac/u111-doc-metadata-enricher/actions/workflows/ci.yml/badge.svg)](https://github.com/Trysac/u111-doc-metadata-enricher/actions/workflows/ci.yml)

Extract title, author, date, language and email, URL and date entities from text, Markdown and HTML with explicit provenance per field and bounded input

## Problem

Describe in two or three sentences the concrete problem this utility solves, who hits it, and what
they do today without it. Replace this paragraph when the first real feature lands.

## Install

```sh
pip install trysac-doc-metadata-enricher
# or
uv add trysac-doc-metadata-enricher
```

Requires Python 3.10 or newer. No runtime dependencies.

## Usage

```python
import doc_metadata_enricher

# normalize() trims surrounding whitespace and lower-cases the text.
print(doc_metadata_enricher.normalize("  Hello World "))  # -> "hello world"

# Blank input is rejected explicitly instead of returning an empty string.
try:
    doc_metadata_enricher.normalize("   ")
except ValueError as exc:
    print(f"rejected: {exc}")
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) and [decisions](docs/decisions/)
- [Testing](docs/TESTING.md) and [security](docs/SECURITY.md)
- [Project record](docs/PROJECT.md) and [stack](docs/STACK.md)
- [Changelog](CHANGELOG.md) and [contributing guide](CONTRIBUTING.md)

## License

[MIT](LICENSE) (c) 2026 Miguel Gomez
