"""Text extraction service — extracts text from PDFs and images."""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Minimum characters on a PDF page before we try OCR fallback
MIN_TEXT_CHARS = 50


class ExtractionError(Exception):
    """Raised when text extraction fails."""

    def __init__(self, error_code: str, message: str):
        self.error_code = error_code
        self.message = message
        super().__init__(message)


@dataclass
class PageText:
    """Extracted text from a single page."""

    page_number: int  # 1-indexed
    text: str
    char_count: int
    method: str  # "pdfplumber" | "tesseract"


def extract_text_from_pdf(file_bytes: bytes) -> list[PageText]:
    """
    Extract text from a PDF using PyMuPDF (fitz).
    Falls back to OCR via Tesseract for pages with < MIN_TEXT_CHARS characters.

    Raises ExtractionError if the PDF is encrypted or cannot be read.
    """
    import fitz  # PyMuPDF

    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as exc:
        raise ExtractionError("unsupported_file", f"Cannot open PDF: {exc}") from exc

    if doc.is_encrypted:
        doc.close()
        raise ExtractionError(
            "encrypted_pdf",
            "PDF dosyasi sifre korumali. Lutfen sifreyi kaldirip tekrar yukleyin.",
        )

    pages: list[PageText] = []

    for page_idx in range(len(doc)):
        page = doc[page_idx]
        text = page.get_text("text").strip()
        page_number = page_idx + 1

        if len(text) >= MIN_TEXT_CHARS:
            pages.append(
                PageText(
                    page_number=page_number,
                    text=text,
                    char_count=len(text),
                    method="pdfplumber",
                )
            )
        else:
            # Attempt OCR fallback for this page
            ocr_text = _ocr_pdf_page(page)
            method = "tesseract" if ocr_text else "pdfplumber"
            final_text = ocr_text if ocr_text and len(ocr_text) > len(text) else text
            pages.append(
                PageText(
                    page_number=page_number,
                    text=final_text,
                    char_count=len(final_text),
                    method=method,
                )
            )

    doc.close()

    if not pages:
        raise ExtractionError("ocr_failed", "PDF contains no pages.")

    return pages


def _ocr_pdf_page(page) -> str:
    """OCR a single PDF page by rendering it to an image and running Tesseract."""
    try:
        import pytesseract
        from PIL import Image

        # Render page to image at 300 DPI
        pix = page.get_pixmap(dpi=300)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        text = pytesseract.image_to_string(img).strip()
        return text
    except Exception as exc:
        logger.warning("OCR fallback failed for page: %s", exc)
        return ""


def extract_text_from_image(file_bytes: bytes) -> list[PageText]:
    """
    Extract text from an image (JPEG/PNG) using Tesseract OCR.

    Raises ExtractionError if OCR fails entirely.
    """
    try:
        import pytesseract
        from PIL import Image

        img = Image.open(io.BytesIO(file_bytes))
        text = pytesseract.image_to_string(img).strip()

        if not text:
            raise ExtractionError(
                "low_quality_image",
                "Goruntu kalitesi cok dusuk. Lutfen daha net bir goruntu yukleyin.",
            )

        return [
            PageText(
                page_number=1,
                text=text,
                char_count=len(text),
                method="tesseract",
            )
        ]
    except ExtractionError:
        raise
    except Exception as exc:
        raise ExtractionError(
            "ocr_failed",
            "Metin cikarilmasi basarisiz oldu. Lutfen daha net bir goruntu yukleyin.",
        ) from exc


def extract_text(file_bytes: bytes, mime_type: str) -> list[PageText]:
    """
    Main entry point: routes to the correct extraction method based on MIME type.

    Returns list of PageText (one per page).
    Raises ExtractionError on failure.
    """
    if mime_type == "application/pdf":
        return extract_text_from_pdf(file_bytes)
    elif mime_type in ("image/jpeg", "image/png"):
        return extract_text_from_image(file_bytes)
    else:
        raise ExtractionError(
            "unsupported_file",
            "Dosya icerigi beklenen formata uymuyor.",
        )
