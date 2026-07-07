import io
import os

os.environ.pop("GEMINI_API_KEY", None)  # force mock pipeline for these tests

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def _fake_png_bytes() -> bytes:
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (10, 10), color="white").save(buf, format="PNG")
    return buf.getvalue()


def test_extract_returns_mock_when_no_api_key():
    files = {"file": ("drawing.png", _fake_png_bytes(), "image/png")}
    r = client.post("/api/extract", files=files)
    assert r.status_code == 200
    body = r.json()
    assert body["mock"] is True
    assert "items" in body and len(body["items"]) > 0
    assert "summary" in body
    assert "job_id" in body


def test_extract_rejects_bad_content_type():
    files = {"file": ("notes.txt", b"hello", "text/plain")}
    r = client.post("/api/extract", files=files)
    assert r.status_code == 400


def test_extract_rejects_oversized_file():
    big = b"0" * (21 * 1024 * 1024)
    files = {"file": ("drawing.png", big, "image/png")}
    r = client.post("/api/extract", files=files)
    assert r.status_code == 400


def test_csv_export_roundtrip():
    files = {"file": ("drawing.png", _fake_png_bytes(), "image/png")}
    extract_resp = client.post("/api/extract", files=files).json()
    extract_resp.pop("job_id", None)
    r = client.post("/api/extract/csv", json={"mto": extract_resp})
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    assert "item_no" in r.text
