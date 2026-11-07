# Security notes

## Threat model

`trysac-doc-metadata-enricher` is a pure library without I/O. 

- **Untrusted input**: Callers may pass hostile strings. We defend this by strictly validating input and failing with explicit `MetadataError` exceptions. Messages are truncated at 200 characters to prevent log injection or memory exhaustion.
- **Resource exhaustion**: Mitigation is built-in. Inputs are bounded by `max_input_chars` (default 2,000,000) and extracted entity counts are bounded by `max_entities` (default 1000).
- **Supply chain**: No runtime dependencies are used. All actions are pinned to major versions.
- **Code execution**: Never `eval`, `exec` or deserialize untrusted data. We use only standard-library modules `html.parser`, `re`, and `unicodedata`.