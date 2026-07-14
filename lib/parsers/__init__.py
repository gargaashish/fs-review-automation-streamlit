from lib.types import NormalizedDocument
from lib.parsers.docx_parser import parse_docx
from lib.parsers.pdf_parser import parse_pdf
from lib.parsers.txt_parser import parse_txt

SUPPORTED_EXTENSIONS = ("docx", "pdf", "txt", "md")


class UnsupportedFileTypeError(ValueError):
    def __init__(self, ext: str):
        super().__init__(f'Unsupported file type ".{ext}". Supported types: {", ".join(SUPPORTED_EXTENSIONS)}.')


def parse_file(data: bytes, file_name: str) -> NormalizedDocument:
    ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""

    if len(data) == 0:
        raise ValueError(f'"{file_name}" is empty.')

    if ext == "docx":
        return parse_docx(data, file_name)
    if ext == "pdf":
        return parse_pdf(data, file_name)
    if ext in ("txt", "md"):
        return parse_txt(data, file_name)
    raise UnsupportedFileTypeError(ext)
