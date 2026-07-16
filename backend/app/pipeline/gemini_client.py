"""
Thin wrapper around the Gemini API for the extraction step.

Uses the google-genai SDK (v1.x) with structured output.
Tries multiple models in order until one succeeds, so the app
degrades gracefully if a particular model is unavailable or over quota.
"""

from __future__ import annotations

import json
import logging
import os
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel

logger = logging.getLogger("mto_app")

# Primary model from env var; if not set, defaults to gemini-2.5-flash.
_PRIMARY_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

# Ordered fallback list — stops at first success.
# Only models confirmed available for this API key.
_MODEL_FALLBACK_ORDER = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-2.5-flash-lite",
]

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "extract_prompt.txt"


class GeminiError(Exception):
    pass


def _load_prompt() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Extraction schema — no 'default' values so the Gemini API accepts it.
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Single-model extraction using the new google-genai SDK
# ---------------------------------------------------------------------------

def _extract_with_model(api_key: str, model: str, image_png_bytes: bytes) -> dict[str, Any]:
    """Call one specific model. Raises on any error."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
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


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def extract_mto(image_png_bytes: bytes) -> dict[str, Any]:
    """
    Try each model in the fallback list until one succeeds.
    Raises GeminiError if all models fail.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise GeminiError("GEMINI_API_KEY is not set")

    # Build ordered list: env-specified model first (if set), then fallbacks
    models_to_try: list[str] = []
    if _PRIMARY_MODEL:
        models_to_try.append(_PRIMARY_MODEL)
    for m in _MODEL_FALLBACK_ORDER:
        if m not in models_to_try:
            models_to_try.append(m)

    last_error: Exception | None = None
    for model in models_to_try:
        try:
            result = _extract_with_model(api_key, model, image_png_bytes)
            logger.info("Extraction completed via model: %s", model)
            return result
        except ImportError as e:
            raise GeminiError(
                "google-genai is not installed. Run: pip install google-genai"
            ) from e
        except Exception as e:  # noqa: BLE001
            logger.warning("Model %s failed: %s", model, e)
            last_error = e
            # Continue to next model

    raise GeminiError(
        f"All models exhausted. Last error: {last_error}"
    ) from last_error
