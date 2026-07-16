from __future__ import annotations

import csv
import io
import logging
import os
import uuid

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.models import MTOResponse
from app.pipeline import mock_pipeline
from app.pipeline.gemini_client import GeminiError, extract_mto
from app.pipeline.postprocess import PostprocessError, process_raw_extraction
from app.pipeline.preprocess import PreprocessError, to_png_bytes, validate_upload

logger = logging.getLogger("mto_app")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Isometric to MTO Generator", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


# In-memory store so the CSV endpoint can look results up by job_id without
# a database. Fine for an assessment/demo; would move to Redis/DB otherwise.
_RESULTS: dict[str, MTOResponse] = {}

MOCK_FALLBACK_ON_ERROR = os.environ.get("MOCK_FALLBACK_ON_ERROR", "true").lower() == "true"


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/gemini-test")
def gemini_test():
    """Diagnostic endpoint: lists available Gemini models for the configured API key."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {"error": "GEMINI_API_KEY is not set"}
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        models = [m.name for m in client.models.list()]
        generate_models = [m for m in models if "generateContent" in (getattr(client.models.get(model=m), "supported_actions", []) or [])]
        return {"api_key_set": True, "available_models": models[:20]}
    except Exception as e:
        return {"api_key_set": True, "error": str(e)}


@app.post("/api/extract")
async def extract(file: UploadFile = File(...)):
    raw = await file.read()

    try:
        validate_upload(file.content_type, len(raw))
        png_bytes = to_png_bytes(raw, file.content_type)
    except PreprocessError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    use_mock = not os.environ.get("GEMINI_API_KEY")
    mto: MTOResponse

    if use_mock:
        logger.info("No GEMINI_API_KEY set - serving mock MTO.")
        mto = mock_pipeline.build_mock_response()
    else:
        try:
            raw_extraction = extract_mto(png_bytes)
            mto = process_raw_extraction(raw_extraction, mock=False)
        except (GeminiError, PostprocessError) as e:
            logger.warning("Live pipeline failed: %s", e)
            if MOCK_FALLBACK_ON_ERROR:
                mto = mock_pipeline.build_mock_response()
            else:
                raise HTTPException(
                    status_code=502,
                    detail="The extraction pipeline failed. Please try again.",
                ) from e

    # Generate thumbnail for frontend preview
    try:
        import base64
        from PIL import Image
        img = Image.open(io.BytesIO(png_bytes))
        img.thumbnail((600, 800))
        thumb_io = io.BytesIO()
        img.save(thumb_io, format="PNG")
        mto.drawing_meta.thumbnail_base64 = base64.b64encode(thumb_io.getvalue()).decode("utf-8")
    except Exception as e:
        logger.warning(f"Could not generate thumbnail: {e}")

    job_id = str(uuid.uuid4())
    mto.job_id = job_id
    _RESULTS[job_id] = mto

    return JSONResponse(mto.model_dump())


class CsvExportRequest(BaseModel):
    mto: MTOResponse


@app.post("/api/extract/csv")
def export_csv(body: CsvExportRequest):
    """
    Accepts the MTO JSON directly in the request body (rather than requiring
    a server-side job_id) so the frontend can export whatever it currently
    has on screen, including after a page refresh.
    """
    mto = body.mto
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        ["item_no", "category", "description", "size_nps", "schedule_rating",
         "material_spec", "end_type", "quantity", "unit", "length_m", "confidence", "remarks"]
    )
    for item in mto.items:
        writer.writerow([
            item.item_no, item.category.value, item.description, item.size_nps or "",
            item.schedule_rating or "", item.material_spec or "", item.end_type or "",
            item.quantity, item.unit, item.length_m or "", item.confidence or "", item.remarks or "",
        ])
    buf.seek(0)

    filename = f"{mto.drawing_meta.drawing_no or 'mto'}.csv"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/extract/{job_id}")
def get_result(job_id: str):
    mto = _RESULTS.get(job_id)
    if not mto:
        raise HTTPException(status_code=404, detail="job_id not found")
    return mto
