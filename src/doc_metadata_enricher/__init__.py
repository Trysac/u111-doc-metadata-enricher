"""Document metadata and entity enrichment with provenance."""

from __future__ import annotations

import html.parser
import logging
import re
import unicodedata
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import date
from typing import Literal

__all__ = [
    "Entity",
    "Field",
    "Metadata",
    "MetadataError",
    "__version__",
    "enrich",
    "parse_date",
]

__version__ = "0.1.0"

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class MetadataError(Exception):
    """Base exception raised when metadata enrichment or parsing fails."""

    def __init__(
        self, code: Literal["input_too_large", "invalid_format"], message: str = ""
    ) -> None:
        super().__init__(message or code)
        self.code = code


@dataclass(frozen=True)
class Field:
    """A metadata field with value and provenance source."""

    value: str
    source: Literal["frontmatter", "html_meta", "heuristic", "detector"]


@dataclass(frozen=True)
class Entity:
    """An extracted entity with type and code-point offsets."""

    kind: Literal["email", "url", "date"]
    text: str
    start: int
    end: int


@dataclass(frozen=True)
class Metadata:
    """Enriched metadata extracted from a document."""

    title: Field | None
    author: Field | None
    date: Field | None
    language: Field | None
    entities: tuple[Entity, ...]
    entities_truncated: bool

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable dictionary representation."""
        return asdict(self)


_ENGLISH_MONTHS: dict[str, int] = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}

_SPANISH_MONTHS: dict[str, int] = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "setiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}

_STOPWORDS: dict[str, set[str]] = {
    "en": {"the", "and", "is", "are", "of", "to", "in", "that", "with", "for"},
    "es": {"el", "la", "de", "que", "y", "en", "los", "las", "por", "con"},
    "fr": {"le", "la", "les", "et", "des", "est", "une", "que", "dans", "pour"},
    "de": {"der", "die", "das", "und", "ist", "nicht", "mit", "ein", "eine", "zu"},
    "pt": {"o", "a", "os", "de", "que", "e", "em", "um", "uma", "para"},
}


def _make_month_pattern(months: dict[str, int]) -> str:
    return "|".join(sorted(months.keys(), key=len, reverse=True))


_EN_MONTH_PAT = _make_month_pattern(_ENGLISH_MONTHS)
_ES_MONTH_PAT = _make_month_pattern(_SPANISH_MONTHS)


def _safe_date(year: int, month: int, day: int) -> date | None:
    try:
        return date(year, month, day)
    except (ValueError, OverflowError):
        return None


def parse_date(s: str) -> date | None:
    """Parse a date from standard supported formats or return None.

    Accepts: ISO 'YYYY-MM-DD' optionally followed by 'T' and a time (time ignored),
    'Month D, YYYY' and 'D Month YYYY' with English month names, and
    'D de mes de YYYY' with Spanish month names (enero ... diciembre, also 'setiembre').
    Names are case-insensitive. Invalid calendar dates and all-numeric formats
    other than ISO return None.
    """
    trimmed = s.strip()
    if not trimmed:
        return None

    # 1. ISO format: YYYY-MM-DD optionally followed by 'T' and time
    m_iso = re.match(r"^([0-9]{4})-([0-9]{2})-([0-9]{2})(?:[Tt].*)?$", trimmed)
    if m_iso:
        y, m, d = int(m_iso.group(1)), int(m_iso.group(2)), int(m_iso.group(3))
        return _safe_date(y, m, d)

    # Reject all-numeric formats (like 31/12/2026, 12-31-2026, 2026.12.31)
    if re.match(r"^[0-9]+[/._ -]+[0-9]+[/._ -]+[0-9]+$", trimmed):
        return None

    # 2. English 'Month D, YYYY'
    m1 = re.match(
        rf"^({_EN_MONTH_PAT})\s+([0-9]{{1,2}}),\s+([0-9]{{4}})$",
        trimmed,
        re.IGNORECASE,
    )
    if m1:
        month_num = _ENGLISH_MONTHS[m1.group(1).lower()]
        day_num = int(m1.group(2))
        year_num = int(m1.group(3))
        return _safe_date(year_num, month_num, day_num)

    # 3. English 'D Month YYYY'
    m2 = re.match(
        rf"^([0-9]{{1,2}})\s+({_EN_MONTH_PAT})\s+([0-9]{{4}})$",
        trimmed,
        re.IGNORECASE,
    )
    if m2:
        day_num = int(m2.group(1))
        month_num = _ENGLISH_MONTHS[m2.group(2).lower()]
        year_num = int(m2.group(3))
        return _safe_date(year_num, month_num, day_num)

    # 4. Spanish 'D de mes de YYYY'
    m3 = re.match(
        rf"^([0-9]{{1,2}})\s+de\s+({_ES_MONTH_PAT})\s+de\s+([0-9]{{4}})$",
        trimmed,
        re.IGNORECASE,
    )
    if m3:
        day_num = int(m3.group(1))
        month_num = _SPANISH_MONTHS[m3.group(2).lower()]
        year_num = int(m3.group(3))
        return _safe_date(year_num, month_num, day_num)

    return None


def _normalise_language(lang: str) -> str:
    """Normalise a language tag to its lowercase primary subtag."""
    cleaned = lang.strip().lower()
    subtag = cleaned.split("-")[0].split("_")[0].strip()
    return subtag


def _clean_text(s: str, max_chars: int = 300) -> str:
    """Collapse whitespace, strip quotes/spaces, and truncate to max_chars."""
    normalized = unicodedata.normalize("NFC", s)
    trimmed = normalized.strip()
    if (trimmed.startswith('"') and trimmed.endswith('"')) or (
        trimmed.startswith("'") and trimmed.endswith("'")
    ):
        trimmed = trimmed[1:-1].strip()
    collapsed = re.sub(r"\s+", " ", trimmed).strip()
    return collapsed[:max_chars]


def _parse_frontmatter(
    text: str,
) -> tuple[dict[str, str], int] | None:
    """Parse Markdown frontmatter if present at the start of text.

    Returns (metadata_dict, end_offset) where end_offset is the index after the closing '---' line.
    Returns None if text does not start with '---' or closing '---' is absent.
    """
    lines = text.splitlines(keepends=True)
    if not lines:
        return None
    first_line = lines[0].rstrip("\r\n")
    if first_line != "---":
        return None

    frontmatter_lines: list[str] = []
    closing_idx = -1
    char_offset = len(lines[0])

    for idx, line in enumerate(lines[1:], start=1):
        stripped = line.rstrip("\r\n")
        char_offset += len(line)
        if stripped == "---":
            closing_idx = idx
            break
        frontmatter_lines.append(stripped)

    if closing_idx == -1:
        return None

    kv_pairs: dict[str, str] = {}
    for f_line in frontmatter_lines:
        if ":" in f_line:
            key, val = f_line.split(":", 1)
            k = key.strip().lower()
            v = val.strip()
            if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                v = v[1:-1]
            kv_pairs[k] = v

    return kv_pairs, char_offset


class _HTMLMetadataParser(html.parser.HTMLParser):
    """HTML parser extracting title, meta tags, lang, and body text."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title: str | None = None
        self.author: str | None = None
        self.date_str: str | None = None
        self.lang: str | None = None
        self.body_text_parts: list[str] = []
        self._in_title = False
        self._ignore_stack: list[str] = []
        self._title_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag_lower = tag.lower()
        attr_dict = {k.lower(): (v or "") for k, v in attrs}

        if (
            tag_lower == "html"
            and self.lang is None
            and "lang" in attr_dict
            and attr_dict["lang"].strip()
        ):
            self.lang = attr_dict["lang"].strip()

        if tag_lower in ("script", "style", "template"):
            self._ignore_stack.append(tag_lower)
            return

        if tag_lower == "title":
            self._in_title = True
            return

        if tag_lower == "meta":
            name = attr_dict.get("name", "").lower()
            prop = attr_dict.get("property", "").lower()
            content = attr_dict.get("content", "").strip()

            if name == "author" and self.author is None and content:
                self.author = content
            elif (
                (name == "date" or prop == "article:published_time")
                and self.date_str is None
                and content
            ):
                self.date_str = content

    def handle_endtag(self, tag: str) -> None:
        tag_lower = tag.lower()
        if self._ignore_stack and self._ignore_stack[-1] == tag_lower:
            self._ignore_stack.pop()
            return
        if tag_lower == "title":
            self._in_title = False
            if self.title is None:
                self.title = "".join(self._title_parts).strip()

    def handle_data(self, data: str) -> None:
        if self._ignore_stack:
            return
        if self._in_title:
            self._title_parts.append(data)
            return
        self.body_text_parts.append(data)


def _detect_language_stopwords(text: str) -> str | None:
    """Detect language using the bundled stopword heuristic."""
    tokens = re.findall(r"\w+", text.lower())
    if not tokens:
        return None

    token_counts: dict[str, int] = {}
    for tok in tokens:
        token_counts[tok] = token_counts.get(tok, 0) + 1

    scores: dict[str, int] = {}
    for lang, sw_set in _STOPWORDS.items():
        score = sum(token_counts.get(sw, 0) for sw in sw_set)
        scores[lang] = score

    sorted_langs = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    best_lang, best_score = sorted_langs[0]
    second_score = sorted_langs[1][1] if len(sorted_langs) > 1 else 0

    if best_score >= 3 and best_score > second_score:
        return best_lang
    return None


_EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")

# URLs: https?://\S+
# with trailing .,;:!?)]' and quote characters removed
_URL_RAW_PATTERN = re.compile(r"https?://\S+")
_TRAILING_URL_PUNCT = ".,;:!?)]'\"`"

# Date regex patterns within text to find dates with parse_date
_DATE_CANDIDATE_RE = re.compile(
    r"(?:"
    r"\b[0-9]{4}-[0-9]{2}-[0-9]{2}"
    r"(?:[Tt][0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?(?:[Zz]|[+-][0-9]{2}:?[0-9]{2})?)?\b"
    rf"|\b(?:{_EN_MONTH_PAT})\s+[0-9]{{1,2}},\s+[0-9]{{4}}\b"
    rf"|\b[0-9]{{1,2}}\s+(?:{_EN_MONTH_PAT})\s+[0-9]{{4}}\b"
    rf"|\b[0-9]{{1,2}}\s+de\s+(?:{_ES_MONTH_PAT})\s+de\s+[0-9]{{4}}\b"
    r")",
    re.IGNORECASE,
)


def _extract_entities(text: str, max_entities: int) -> tuple[tuple[Entity, ...], bool]:
    """Extract email, URL, and date entities from text.

    Offsets are code-point offsets in the input text.
    Entities are sorted by start and deduplicated by (kind, start).
    """
    found: list[Entity] = []

    # 1. URLs
    for m in _URL_RAW_PATTERN.finditer(text):
        start = m.start()
        end = m.end()
        while end > start and text[end - 1] in _TRAILING_URL_PUNCT:
            end -= 1
        cleaned_url = text[start:end]
        if cleaned_url:
            found.append(Entity(kind="url", text=cleaned_url, start=start, end=end))

    # 2. Emails
    for m in _EMAIL_PATTERN.finditer(text):
        found.append(Entity(kind="email", text=m.group(0), start=m.start(), end=m.end()))

    # 3. Dates
    for m in _DATE_CANDIDATE_RE.finditer(text):
        candidate = m.group(0)
        d = parse_date(candidate)
        if d is not None:
            found.append(Entity(kind="date", text=candidate, start=m.start(), end=m.end()))

    # Deduplicate by (kind, start) and sort by start
    seen: set[tuple[str, int]] = set()
    deduped: list[Entity] = []
    for ent in sorted(found, key=lambda e: (e.start, e.end)):
        key = (ent.kind, ent.start)
        if key not in seen:
            seen.add(key)
            deduped.append(ent)

    deduped.sort(key=lambda e: e.start)

    if len(deduped) > max_entities:
        return tuple(deduped[:max_entities]), True
    return tuple(deduped), False


def enrich(
    text: str,
    *,
    fmt: Literal["text", "markdown", "html"] = "text",
    detect_language: Callable[[str], str | None] | None = None,
    max_input_chars: int = 2_000_000,
    max_entities: int = 1000,
) -> Metadata:
    """Extract metadata and entities from text, Markdown, or HTML.

    Parameters:
        text: Input document content.
        fmt: Format of the document ('text', 'markdown', or 'html').
        detect_language: Optional custom callable to detect language.
        max_input_chars: Maximum allowed input length in characters (default 2,000,000).
        max_entities: Maximum entities to return (default 1000).

    Returns:
        Metadata object containing title, author, date, language fields with provenance,
        and extracted entities.

    Raises:
        MetadataError: If input length exceeds max_input_chars or format is invalid.
    """
    if fmt not in ("text", "markdown", "html"):
        safe_fmt = fmt[:200] if isinstance(fmt, str) else str(type(fmt))
        raise MetadataError("invalid_format", f"Unsupported format: {safe_fmt}")

    if len(text) > max_input_chars:
        raise MetadataError(
            "input_too_large",
            f"Input length {len(text)} exceeds maximum allowed {max_input_chars}",
        )

    title_field: Field | None = None
    author_field: Field | None = None
    date_field: Field | None = None
    lang_field: Field | None = None

    body_for_heuristics = text
    entity_target_text = text

    # Precedence Step 1: Markdown frontmatter
    fm_data = _parse_frontmatter(text)
    if fm_data is not None:
        fm_dict, fm_end_offset = fm_data
        if fm_dict.get("title"):
            title_field = Field(_clean_text(fm_dict["title"]), "frontmatter")
        if fm_dict.get("author"):
            author_field = Field(_clean_text(fm_dict["author"]), "frontmatter")
        if fm_dict.get("date"):
            parsed_dt = parse_date(fm_dict["date"])
            if parsed_dt is not None:
                date_field = Field(parsed_dt.isoformat(), "frontmatter")
        fm_lang = fm_dict.get("lang") or fm_dict.get("language")
        if fm_lang and fm_lang.strip():
            lang_field = Field(_normalise_language(fm_lang), "frontmatter")

        body_for_heuristics = text[fm_end_offset:]

    # Precedence Step 2: HTML
    if fmt == "html":
        parser = _HTMLMetadataParser()
        try:
            parser.feed(text)
            parser.close()
        except Exception as err:
            logger.debug("HTML parse failure handled: %s", err)

        if title_field is None and parser.title:
            title_field = Field(_clean_text(parser.title), "html_meta")
        if author_field is None and parser.author:
            author_field = Field(_clean_text(parser.author), "html_meta")
        if date_field is None and parser.date_str:
            parsed_dt = parse_date(parser.date_str)
            if parsed_dt is not None:
                date_field = Field(parsed_dt.isoformat(), "html_meta")
        if lang_field is None and parser.lang:
            lang_field = Field(_normalise_language(parser.lang), "html_meta")

        extracted_html_text = "".join(parser.body_text_parts)
        body_for_heuristics = extracted_html_text
        entity_target_text = extracted_html_text

    # Precedence Step 3: Heuristics on body text
    # Title heuristic
    if title_field is None:
        if fmt == "markdown":
            for line in body_for_heuristics.splitlines():
                stripped_line = line.strip()
                if stripped_line.startswith("# "):
                    candidate_title = stripped_line[2:].strip()
                    if candidate_title:
                        title_field = Field(_clean_text(candidate_title), "heuristic")
                        break
        elif fmt == "text":
            for line in body_for_heuristics.splitlines():
                trimmed_line = line.strip()
                if trimmed_line and len(trimmed_line) <= 120:
                    title_field = Field(_clean_text(trimmed_line), "heuristic")
                    break

    # Author heuristic: line matching ^(By|Author:|Por)\s+(.{2,80})$
    if author_field is None:
        author_regex = re.compile(r"^(?:By|Author:|Por)\s+(.{2,80})$", re.MULTILINE)
        m_auth = author_regex.search(body_for_heuristics)
        if m_auth:
            candidate_author = m_auth.group(1).strip()
            author_field = Field(_clean_text(candidate_author), "heuristic")

    # Date heuristic: first parse_date match in the first 2000 characters
    if date_field is None:
        head_chunk = body_for_heuristics[:2000]
        for m in _DATE_CANDIDATE_RE.finditer(head_chunk):
            parsed = parse_date(m.group(0))
            if parsed is not None:
                date_field = Field(parsed.isoformat(), "heuristic")
                break

    # Precedence Step 4: Language detection
    # detect_language, then stopword heuristic
    if lang_field is None:
        if detect_language is not None:
            custom_lang = detect_language(body_for_heuristics)
            if custom_lang and custom_lang.strip():
                lang_field = Field(_normalise_language(custom_lang), "detector")

        if lang_field is None:
            sw_lang = _detect_language_stopwords(body_for_heuristics)
            if sw_lang is not None:
                lang_field = Field(sw_lang, "heuristic")

    # Entities extraction
    entities, entities_truncated = _extract_entities(entity_target_text, max_entities)

    return Metadata(
        title=title_field,
        author=author_field,
        date=date_field,
        language=lang_field,
        entities=entities,
        entities_truncated=entities_truncated,
    )
