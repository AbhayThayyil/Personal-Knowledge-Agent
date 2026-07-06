from pathlib import Path

from pypdf import PdfReader


def extract_pages(file_path: str) -> list[str]:
    """Return a list of page texts. Non-PDF files are treated as one page."""
    extension = Path(file_path).suffix.lower()

    if extension == ".pdf":
        reader = PdfReader(file_path)
        return [page.extract_text() or "" for page in reader.pages]

    text = Path(file_path).read_text(encoding="utf-8", errors="ignore")
    return [text]
