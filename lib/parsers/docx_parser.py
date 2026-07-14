import io
import re
from lib.types import NormalizedDocument, Section


def _iter_block_items(parent):
    """Yield paragraphs and tables from a python-docx Document in document order."""
    from docx.document import Document as _Document
    from docx.oxml.ns import qn
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    parent_elm = parent.element.body if isinstance(parent, _Document) else parent._element
    for child in parent_elm.iterchildren():
        if child.tag == qn("w:p"):
            yield Paragraph(child, parent)
        elif child.tag == qn("w:tbl"):
            yield Table(child, parent)


def _heading_level(style_name: str) -> int | None:
    if style_name == "Title":
        return 1
    if style_name == "Subtitle":
        return None  # folded into front matter as plain text, not a heading
    match = re.match(r"^Heading (\d+)$", style_name or "")
    if match:
        return min(int(match.group(1)), 6)
    return None


def _table_text(table) -> str:
    rows = []
    for row in table.rows:
        cells = [c.text.strip() for c in row.cells]
        cells = [c for c in cells if c]
        if cells:
            rows.append(" | ".join(cells))
    return "\n".join(rows)


def parse_docx(data: bytes, file_name: str) -> NormalizedDocument:
    from docx import Document

    try:
        doc = Document(io.BytesIO(data))
    except Exception as err:
        raise ValueError("Failed to open the DOCX file. It may be corrupted.") from err

    blocks: list[tuple[int | None, str, str]] = []
    for item in _iter_block_items(doc):
        if item.__class__.__name__ == "Paragraph":
            text = item.text.strip()
            if not text:
                continue
            style_name = item.style.name if item.style else ""
            level = _heading_level(style_name)
            # A non-"Title"/"Subtitle" style that isn't explicitly "Heading N" is body text.
            if style_name in ("Title",) or (style_name or "").startswith("Heading "):
                blocks.append((level, text, style_name))
            else:
                blocks.append((None, text, ""))
        else:
            text = _table_text(item)
            if text:
                blocks.append((None, text, ""))

    if not blocks:
        raise ValueError("The DOCX file contains no extractable text.")

    def word_count(text: str) -> int:
        return len(text.split())

    title = ""
    title_parts_count = 0
    sections: list[Section] = []
    current: Section | None = None

    for level, text, style_name in blocks:
        # A short block right after the title is only folded into it when the block itself
        # is title-tier (plain front-matter text, or a "Title"-styled paragraph) - never when
        # it's a genuine "Heading N" paragraph, which is the document's first real section.
        is_title_tier = level is None or style_name == "Title"
        if title_parts_count == 1 and current is None and is_title_tier and word_count(text) <= 15:
            title = f"{title} — {text}"
            title_parts_count = 2
            continue

        if level is not None:
            if not title:
                title = text
                title_parts_count = 1
                continue
            if current:
                sections.append(current)
            current = Section(heading=text, content="", level=level)
            continue

        if not title:
            title = text[:120]
            title_parts_count = 1
            continue

        if current is None:
            continue
        current.content += ("\n" if current.content else "") + text

    if current:
        sections.append(current)

    for s in sections:
        s.word_count = len(s.content.split())

    return NormalizedDocument(
        title=title or file_name,
        source_file_name=file_name,
        file_type="docx",
        sections=sections,
    )
