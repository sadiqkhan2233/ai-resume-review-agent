"""Validate uploads and extract text from PDF / DOCX resumes (in memory only)."""
import io
import re
from pathlib import Path

from .config import (
    ALLOWED_EXTENSIONS,
    MAX_FILE_BYTES,
    MAX_FILE_SIZE_MB,
    MAX_PDF_PAGES,
    MIN_RESUME_CHARS,
)


class ExtractionError(Exception):
    """Raised with a user-friendly message when a resume cannot be read."""


def validate_upload(filename: str, data: bytes) -> str:
    """Check extension, size and file signature. Returns the lower-case extension."""
    ext = Path(filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ExtractionError("Unsupported file type. Please upload a PDF or DOCX resume.")
    if not data:
        raise ExtractionError("The uploaded file is empty.")
    if len(data) > MAX_FILE_BYTES:
        raise ExtractionError(f"File is too large. Maximum size is {MAX_FILE_SIZE_MB} MB.")
    if ext == ".pdf" and b"%PDF" not in data[:1024]:
        raise ExtractionError("This file is not a valid PDF (it may be corrupted or renamed).")
    if ext == ".docx" and data[:2] != b"PK":
        raise ExtractionError("This file is not a valid DOCX (it may be corrupted or renamed).")
    return ext


def _extract_pdf(data: bytes) -> str:
    import pymupdf  # PyMuPDF

    try:
        doc = pymupdf.open(stream=data, filetype="pdf")
    except Exception as exc:
        raise ExtractionError("Could not open the PDF. The file may be corrupted.") from exc

    with doc:
        if doc.needs_pass:
            raise ExtractionError("This PDF is password-protected. Please remove the password.")
        pages = []
        for index, page in enumerate(doc):
            if index >= MAX_PDF_PAGES:
                break
            pages.append(page.get_text("text"))
    return "\n".join(pages)


def _extract_docx(data: bytes) -> str:
    from docx import Document

    try:
        document = Document(io.BytesIO(data))
    except Exception as exc:
        raise ExtractionError("Could not open the DOCX. The file may be corrupted.") from exc

    parts = [p.text for p in document.paragraphs if p.text.strip()]
    for table in document.tables:
        for row in table.rows:
            cells = []
            for cell in row.cells:
                text = cell.text.strip()
                if text and text not in cells:
                    cells.append(text)
            if cells:
                parts.append(" | ".join(cells))
    return "\n".join(parts)


def clean_text(text: str) -> str:
    text = text.replace("\x00", " ").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_resume_text(filename: str, data: bytes) -> str:
    """Main entry point: returns clean resume text or raises ExtractionError."""
    ext = validate_upload(filename, data)
    raw = _extract_pdf(data) if ext == ".pdf" else _extract_docx(data)
    text = clean_text(raw)
    if len(text) < MIN_RESUME_CHARS:
        raise ExtractionError(
            "Very little text could be read from this file. It may be empty or a scanned "
            "image. Please upload a text-based PDF or DOCX."
        )
    return text
