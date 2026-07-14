import io
from lib.types import NormalizedDocument
from lib.parsers.normalize import text_to_normalized_document


def parse_pdf(data: bytes, file_name: str) -> NormalizedDocument:
    import pdfplumber

    try:
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            text = "\n".join((page.extract_text() or "") for page in pdf.pages).strip()
    except Exception as err:
        raise ValueError(
            "Failed to parse PDF. The file may be corrupted or scanned as images without a text layer."
        ) from err

    if not text:
        raise ValueError("The PDF contains no extractable text (it may be a scanned image without OCR).")

    return text_to_normalized_document(text, file_name, "pdf")
