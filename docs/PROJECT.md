# Project record

## Objective

Extract title, author, date, language and entities (email, URL, date) from text, Markdown and HTML with explicit provenance per field and bounded input.

## Scope

- In scope: The public API documented in [README.md](../README.md), typed and tested.
- Out of scope: Person and organisation named entity recognition (needs a model), PDF and DOCX parsing, other languages' date names, keyword extraction.

## Timeline

| Date | Event |
|---|---|
| 2026 | Repository created from the factory utility template. |

## Effort metrics

Measured values only; a value that has not been measured stays "pending measurement".

| Metric | Value |
|---|---|
| Tokens (input / output) | 3836321 / 44964 |
| Hours (human) | pending measurement |
| Cost (USD) | 0.7574 |

## Factory run u111 (measured from API usage)

| Phase | Model | Batch | Input | Output | Cache write | Cache read | Cost (USD) |
|---|---|---|---|---|---|---|---|
| generation | gemini-3.8-flash | yes | 4589 | 16786 | 0 | 0 | 0.0332 |
| fix-1 | gemini-3.8-flash | no | 96626 | 5988 | 0 | 1010254 | 0.1707 |
| fix-2 | gemini-3.8-flash | no | 100083 | 5483 | 0 | 893358 | 0.1626 |
| fix-3 | gemini-3.8-flash | no | 173166 | 11907 | 0 | 968128 | 0.2471 |
| fix-4 | gemini-3.8-flash | no | 37175 | 499 | 0 | 133667 | 0.0398 |
| fix-1 | gemini-3.8-flash | no | 44596 | 1658 | 0 | 161917 | 0.0518 |
| audit | gemini-3.1-flash-lite | no | 37905 | 522 | 0 | 22365 | 0.0108 |
| docs | gemini-3.1-flash-lite | no | 152492 | 2121 | 0 | 0 | 0.0413 |

Total: $0.7574. Prices: Anthropic list prices.
