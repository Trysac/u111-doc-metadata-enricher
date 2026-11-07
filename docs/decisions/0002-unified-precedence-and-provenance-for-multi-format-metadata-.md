# Unified Precedence and Provenance for Multi-format Metadata Enrichment

Status: accepted (generated, pending human review)

## Context

Ingested documents in search, RAG, and retrieval pipelines originate from diverse formats (plain text, Markdown, HTML) with metadata distributed inconsistently across headers, tags, and inline text. Downstream filtering and citation require normalised metadata while preserving where each value was derived.

## Decision

Implement a pure standard-library enrichment engine that extracts title, author, date, language, and entities (emails, URLs, dates) using a deterministic four-tier precedence hierarchy (frontmatter > HTML meta tags > body heuristics > language detection). Every field attaches a provenance source ('frontmatter', 'html_meta', 'heuristic', 'detector') and enforces strict size limits on inputs and outputs.

## Consequences

Callers receive predictable, typed metadata with provenance flags. Parsing is fast and secure against denial-of-service through bounded entity lists and string lengths, without external dependencies.
