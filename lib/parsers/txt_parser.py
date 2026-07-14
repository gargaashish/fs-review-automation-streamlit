from lib.types import NormalizedDocument
from lib.parsers.normalize import text_to_normalized_document


def parse_txt(data: bytes, file_name: str) -> NormalizedDocument:
    text = data.decode("utf-8", errors="replace").strip()
    if not text:
        raise ValueError("The text file is empty.")
    return text_to_normalized_document(text, file_name, "txt")
