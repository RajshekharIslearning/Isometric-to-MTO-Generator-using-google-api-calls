"""
Turns an uploaded file (PNG/JPG/PDF) into a single PNG image, capped to a
reasonable resolution, ready to send to the vision model.
"""

from __future__ import annotations

import io

from PIL import Image

MAX_SIDE_PX = 2000
ALLOWED_CONTENT_TYPES = {"image/png", "image/jpeg", "application/pdf"}
MAX_UPLOAD_MB = 20


class PreprocessError(Exception):
    pass


def validate_upload(content_type: str, size_bytes: int) -> None:
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise PreprocessError(
            f"Unsupported file type '{content_type}'. Upload a PNG, JPG, or PDF."
        )
    if size_bytes > MAX_UPLOAD_MB * 1024 * 1024:
        raise PreprocessError(
            f"File is too large ({size_bytes / (1024 * 1024):.1f} MB). "
            f"Max size is {MAX_UPLOAD_MB} MB."
        )


def _resize_cap(img: Image.Image) -> Image.Image:
    w, h = img.size
    longest = max(w, h)
    if longest <= MAX_SIDE_PX:
        return img
    scale = MAX_SIDE_PX / longest
    return img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)


def to_png_bytes(raw: bytes, content_type: str) -> bytes:
    """Convert the uploaded file to resized PNG bytes for the vision model."""
    if content_type == "application/pdf":
        try:
            import fitz  # PyMuPDF
        except ImportError as e:  # pragma: no cover
            raise PreprocessError(
                "PDF support requires PyMuPDF (pip install pymupdf)."
            ) from e
        doc = fitz.open(stream=raw, filetype="pdf")
        if doc.page_count == 0:
            raise PreprocessError("The PDF has no pages.")
        page = doc.load_page(0)  # first page only (documented assumption)
        # Render at ~200 DPI, then let _resize_cap enforce the final cap.
        zoom = 200 / 72
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
        img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
    else:
        img = Image.open(io.BytesIO(raw)).convert("RGB")

    img = _resize_cap(img)
    out = io.BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()
