import re
from lib.types import NormalizedDocument, Section

_NUMBERED_RE = re.compile(r"^(\d+(?:\.\d+)*)[.)]?\s+(.{2,100})$")


def _is_likely_heading(line: str) -> tuple[str, int] | None:
    trimmed = line.strip()
    if not trimmed or len(trimmed) > 100:
        return None

    numbered = _NUMBERED_RE.match(trimmed)
    if numbered:
        depth = len(numbered.group(1).split("."))
        return numbered.group(2).strip(), min(depth, 4)

    words = trimmed.split()
    is_short_line = len(words) <= 8
    looks_like_title = (
        is_short_line
        and not trimmed.endswith(".")
        and not trimmed.endswith(",")
        and (trimmed == trimmed.upper() or trimmed[:1].isupper())
    )

    if looks_like_title and len(trimmed) >= 3:
        return re.sub(r":$", "", trimmed), 1

    return None


def text_to_normalized_document(raw_text: str, source_file_name: str | None, file_type: str | None) -> NormalizedDocument:
    lines = raw_text.replace("\r\n", "\n").split("\n")
    sections: list[Section] = []
    current: Section | None = None
    title = ""

    for line in lines:
        trimmed = line.strip()
        if not trimmed:
            continue

        heading_match = _is_likely_heading(line)
        if heading_match:
            heading_text, level = heading_match
            if not title:
                title = heading_text
                continue
            if current:
                sections.append(current)
            current = Section(heading=heading_text, content="", level=level)
            continue

        if not title:
            title = trimmed[:120]
            continue

        if not current:
            current = Section(heading="Untitled Section", content="", level=1)
        current.content += ("\n" if current.content else "") + trimmed

    if current:
        sections.append(current)

    for s in sections:
        s.word_count = len(s.content.split())

    return NormalizedDocument(
        title=title or source_file_name or "Untitled Document",
        source_file_name=source_file_name,
        file_type=file_type,
        sections=sections,
    )
