"""Local, bounded extraction of text from PDF and DOCX resumes."""

from __future__ import annotations

from io import BytesIO
from pathlib import PurePath
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile

from pypdf import PdfReader

MAX_RESUME_BYTES = 10 * 1024 * 1024


class ResumeParseError(ValueError):
    """Raised when a resume cannot be safely or usefully extracted."""


def extract_resume_text(filename: str, data: bytes) -> str:
    if not data:
        raise ResumeParseError("The uploaded file is empty.")
    if len(data) > MAX_RESUME_BYTES:
        raise ResumeParseError("The resume exceeds the 10 MB upload limit.")
    extension = PurePath(filename).suffix.lower()
    if extension == ".pdf":
        text = _extract_pdf(data)
    elif extension == ".docx":
        text = _extract_docx(data)
    else:
        raise ResumeParseError("Unsupported file type. Upload a PDF or DOCX resume.")
    if not text.strip():
        raise ResumeParseError(
            "No readable text was found. This may be a scanned PDF; use a text-based PDF "
            "or run OCR separately before uploading. OCR is not included."
        )
    return text.strip()


def _extract_pdf(data: bytes) -> str:
    try:
        reader = PdfReader(BytesIO(data), strict=True)
        if reader.is_encrypted:
            try:
                if not reader.decrypt(""):
                    raise ResumeParseError("This PDF is encrypted and requires a password.")
            except NotImplementedError as exc:
                raise ResumeParseError("This encrypted PDF cannot be read.") from exc
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except ResumeParseError:
        raise
    except Exception as exc:
        raise ResumeParseError(f"The PDF is corrupted or unreadable: {exc}") from exc


def _extract_docx(data: bytes) -> str:
    try:
        with ZipFile(BytesIO(data)) as document:
            xml = document.read("word/document.xml")
        root = ElementTree.fromstring(xml)
        namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        paragraphs = []
        for paragraph in root.findall(".//w:p", namespace):
            value = "".join(
                node.text or ""
                for node in paragraph.findall(".//w:t", namespace)
            )
            if value:
                paragraphs.append(value)
        return "\n".join(paragraphs)
    except (BadZipFile, KeyError, ElementTree.ParseError, OSError) as exc:
        raise ResumeParseError(f"The DOCX file is corrupted or unreadable: {exc}") from exc
