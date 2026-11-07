"""CLI entry point for doc-metadata-enricher."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from doc_metadata_enricher import MetadataError, enrich


def main(argv: Sequence[str] | None = None) -> int:
    """Run CLI commands for document metadata enrichment."""
    parser = argparse.ArgumentParser(
        prog="doc-metadata-enricher",
        description="Extract document metadata and entities with explicit provenance.",
    )
    parser.add_argument(
        "--format",
        "-f",
        dest="fmt",
        choices=["text", "markdown", "html"],
        default="text",
        help="Input format (text, markdown, html; default: text)",
    )
    parser.add_argument(
        "path",
        nargs="?",
        help="File path to process (if omitted, reads from stdin)",
    )

    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code
        return int(code) if isinstance(code, int) else 2

    if args.path is not None:
        path = Path(args.path)
        if not path.is_file():
            sys.stderr.write(f"Error: file not found: {args.path}\n")
            return 2
        try:
            content = path.read_text(encoding="utf-8")
        except Exception as exc:
            sys.stderr.write(f"Error reading file: {exc}\n")
            return 2
    else:
        try:
            content = sys.stdin.read()
        except Exception as exc:
            sys.stderr.write(f"Error reading stdin: {exc}\n")
            return 2

    try:
        metadata = enrich(content, fmt=args.fmt)
    except MetadataError as exc:
        sys.stderr.write(f"Metadata extraction error: {exc}\n")
        return 1
    except Exception as exc:
        sys.stderr.write(f"Unexpected error: {exc}\n")
        return 2

    output_dict = metadata.to_dict()
    sys.stdout.write(json.dumps(output_dict, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
