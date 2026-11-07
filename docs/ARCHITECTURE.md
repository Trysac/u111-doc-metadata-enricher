# Architecture

`doc-metadata-enricher` provides a unified document enrichment pipeline with deterministic field extraction and explicit provenance tracking.

## Ingestion Precedence

Fields are evaluated in strict priority order:

1. **Markdown Frontmatter**: Delimited by `---` header and trailer lines at the start. Extracts `title`, `author`, `date`, `lang`/`language`.
2. **HTML Meta Tags**: Parsed via `html.parser`. Includes `<title>`, `<meta name="author">`, `<meta name="date">`, `<meta property="article:published_time">`, and `<html>` lang attributes. Content from `<script>`, `<style>`, and `<template>` is strictly ignored.
3. **Body Heuristics**: Fallbacks to Markdown headings (`# `), standard text title lines (<= 120 chars), signature lines like `By ...`, and dates within the first 2,000 characters.
4. **Language Detection**: Prioritizes an injected custom detector, then falls back to a deterministic 5-language stopword frequency evaluator.