"""
Thin wrapper around the Gemini API for the extraction step.

Supports both the legacy google-generativeai SDK (v0.x) and the newer
google-genai SDK (v1.x). The newer SDK is tried first; if unavailable,
the legacy SDK is used as fallback. Both use structured-output mode
(response_mime_type + response_schema) so we get back JSON that matches
app/prompts/mto_schema.json without needing to parse markdown fences.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger("mto_app")

MODEL_NAME = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "extract_prompt.txt"


class GeminiError(Exception):
    pass


def _load_prompt() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


from pydantic import BaseModel
from enum import Enum

class ExtCategory(str, Enum):
    PIPE = "PIPE"
    FITTING = "FITTING"
    FLANGE = "FLANGE"
    VALVE = "VALVE"
    GASKET = "GASKET"
    BOLT = "BOLT"
    SUPPORT = "SUPPORT"
    OTHER = "OTHER"

class ExtDrawingMeta(BaseModel):
    drawing_no: str | None
    revision: str | None
    line_number: str | None
    nps: str | None
    material_class: str | None
    service: str | None

class ExtMTOItem(BaseModel):
    item_no: int
    category: ExtCategory
    description: str
    size_nps: str | None
    schedule_rating: str | None
    material_spec: str | None
    end_type: str | None
    quantity: float
    unit: str | None
    length_m: float | None
    confidence: float | None
    remarks: str | None

class ExtSummary(BaseModel):
    total_pipe_length_m: float
    fittings: int
    flanges: int
    valves: int
    gaskets: int
    bolt_sets: int
    field_welds: int

class ExtMTOResponse(BaseModel):
    drawing_meta: ExtDrawingMeta
    items: list[ExtMTOItem]
    summary: ExtSummary

def _extract_with_new_sdk(api_key: str, image_png_bytes: bytes) -> dict[str, Any]:
    """Use the google-genai SDK (v1.x+)."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[
            _load_prompt(),
            types.Part.from_bytes(data=image_png_bytes, mime_type="image/png"),
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ExtMTOResponse,
            temperature=0.1,
        ),
    )
    return json.loads(response.text)


def _extract_with_legacy_sdk(api_key: str, image_png_bytes: bytes) -> dict[str, Any]:
    """Use the legacy google-generativeai SDK (v0.x)."""
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(MODEL_NAME)

    response = model.generate_content(
        [
            _load_prompt(),
            {"mime_type": "image/png", "data": image_png_bytes},
        ],
        generation_config={
            "response_mime_type": "application/json",
            "response_schema": ExtMTOResponse,
            "temperature": 0.1,
        },
    )

    return json.loads(response.text)


def extract_mto(image_png_bytes: bytes) -> dict[str, Any]:
    """
    Calls Gemini with the preprocessed drawing image and returns the parsed
    JSON dict (drawing_meta + items, NOT yet validated against Pydantic).
    Raises GeminiError on any failure so the caller can decide whether to
    fall back to the mock pipeline.

    Tries the newer google-genai SDK first, falls back to google-generativeai.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise GeminiError("GEMINI_API_KEY is not set")

    last_error: Exception | None = None

    # Try new SDK first
    try:
        result = _extract_with_new_sdk(api_key, image_png_bytes)
        logger.info("Extraction completed via google-genai SDK.")
        return result
    except ImportError:
        logger.debug("google-genai not installed, trying legacy SDK.")
    except Exception as e:  # noqa: BLE001
        last_error = e
        logger.warning("New SDK extraction failed: %s", e)

    # Fall back to legacy SDK
    try:
        result = _extract_with_legacy_sdk(api_key, image_png_bytes)
        logger.info("Extraction completed via legacy google-generativeai SDK.")
        return result
    except ImportError as e:
        raise GeminiError(
            "Neither google-genai nor google-generativeai is installed. "
            "Run: pip install google-generativeai"
        ) from e
    except Exception as e:  # noqa: BLE001
        # If both SDKs failed, surface the more informative error
        cause = last_error or e
        raise GeminiError(f"Gemini extraction failed: {cause}") from cause
