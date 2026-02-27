"""
PitchCraft Preview Service — PPTX → Slide Images
==================================================
Converts a generated PPTX file into individual PNG images (one per slide)
using LibreOffice headless for PPTX→PDF and PyMuPDF for PDF→PNG.

Pipeline:
  PPTX bytes → temp file → libreoffice --headless → PDF → PyMuPDF → list[PNG bytes]
"""

# ============================================================================
# SECTION: Imports & Configuration
# ============================================================================

import logging
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

_RENDER_SCALE = 2.0  # 2× for HiDPI quality


# ============================================================================
# SECTION: PPTX → PDF Conversion (LibreOffice Headless)
# ============================================================================

def _pptx_to_pdf(pptx_bytes: bytes, output_dir: Path) -> Path:
    """
    Convert PPTX bytes to a PDF file using LibreOffice headless.

    Args:
        pptx_bytes: Raw PPTX file bytes.
        output_dir: Directory to write the output PDF.

    Returns:
        Path to the generated PDF file.

    Raises:
        RuntimeError: If LibreOffice conversion fails.
    """
    pptx_path = output_dir / "presentation.pptx"
    pptx_path.write_bytes(pptx_bytes)

    result = subprocess.run(
        [
            "libreoffice",
            "--headless",
            "--convert-to", "pdf",
            "--outdir", str(output_dir),
            str(pptx_path),
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )

    if result.returncode != 0:
        logger.error("LibreOffice conversion failed: %s", result.stderr)
        raise RuntimeError(f"LibreOffice conversion failed: {result.stderr[:500]}")

    pdf_path = output_dir / "presentation.pdf"
    if not pdf_path.exists():
        raise RuntimeError("LibreOffice did not produce a PDF file.")

    return pdf_path


# ============================================================================
# SECTION: PDF → PNG Conversion (PyMuPDF)
# ============================================================================

def _render_page(pdf_path: str, page_num: int) -> tuple[int, bytes]:
    """Render a single PDF page to PNG bytes.

    Each worker opens its own fitz.Document so rendering is thread-safe.

    Args:
        pdf_path:  Path to the PDF file (string for pickling).
        page_num:  Zero-based page index.

    Returns:
        Tuple of (page_num, png_bytes).
    """
    doc = fitz.open(pdf_path)
    matrix = fitz.Matrix(_RENDER_SCALE, _RENDER_SCALE)
    page = doc.load_page(page_num)
    pix = page.get_pixmap(matrix=matrix)
    png = pix.tobytes("png")
    doc.close()
    return page_num, png


def _pdf_to_pngs(pdf_path: Path) -> list[bytes]:
    """
    Convert each page of a PDF to a PNG image.

    Uses parallel rendering for PDFs with multiple pages.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        List of PNG bytes, one per page.
    """
    doc = fitz.open(str(pdf_path))
    total = len(doc)
    doc.close()

    if total <= 2:
        # Sequential for small PDFs (thread overhead not worth it)
        doc = fitz.open(str(pdf_path))
        matrix = fitz.Matrix(_RENDER_SCALE, _RENDER_SCALE)
        images = []
        for i in range(total):
            page = doc.load_page(i)
            pix = page.get_pixmap(matrix=matrix)
            images.append(pix.tobytes("png"))
        doc.close()
        return images

    # Parallel rendering for larger presentations
    images: list[bytes] = [b""] * total
    with ThreadPoolExecutor(max_workers=min(4, total)) as executor:
        futures = [executor.submit(_render_page, str(pdf_path), i) for i in range(total)]
        for future in futures:
            idx, png = future.result()
            images[idx] = png

    return images


# ============================================================================
# SECTION: Main Entry Point
# ============================================================================

def convert_pptx_to_slide_images(pptx_bytes: bytes) -> list[bytes]:
    """
    Convert PPTX file bytes to a list of PNG images (one per slide).

    Uses LibreOffice headless for PPTX→PDF conversion, then PyMuPDF for
    PDF→PNG rendering at 2× scale for HiDPI quality.

    Args:
        pptx_bytes: Raw PPTX file bytes.

    Returns:
        List of PNG image bytes, one per slide.

    Raises:
        RuntimeError: If conversion fails at any stage.
    """
    with tempfile.TemporaryDirectory(prefix="pitchcraft_preview_") as tmp_dir:
        output_dir = Path(tmp_dir)

        logger.info("Converting PPTX to PDF via LibreOffice headless...")
        pdf_path = _pptx_to_pdf(pptx_bytes, output_dir)

        logger.info("Converting PDF pages to PNG images...")
        images = _pdf_to_pngs(pdf_path)

        logger.info("Preview conversion complete: %d slide(s)", len(images))
        return images
