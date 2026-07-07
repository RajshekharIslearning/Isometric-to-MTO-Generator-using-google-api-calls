# Isometric &rarr; MTO Generator

Full-stack AI assessment submission: upload a piping isometric drawing
(PNG/JPG/PDF), get back a validated Material Take-Off (MTO).

---

## Architecture

```
┌─────────────┐   multipart/form-data   ┌────────────────────┐
│   Next.js    │ ───────────────────────▶│      FastAPI        │
│  frontend    │                         │      backend        │
│ (App Router) │◀─────────────────────── │                    │
└─────────────┘      MTOResponse JSON    │ preprocess          │
                                         │  (PDF/img → PNG)   │
                                         │       │            │
                                         │       ▼            │
                                         │  gemini_client      │
                                         │  (vision + schema)  │
                                         │       │            │
                                         │       ▼            │
                                         │  postprocess        │
                                         │  (validate, derive  │
                                         │   gaskets/bolts,   │
                                         │   compute summary) │
                                         └────────────────────┘
                                                  │
                                    no GEMINI_API_KEY, or the
                                    live call fails
                                                  ▼
                                         mock_pipeline (canned,
                                         schema-valid MTO)
```

**Design choice — synchronous API**: `POST /api/extract` returns the full
`MTOResponse` in one call. The brief allows async (job-queue/polling); sync
was chosen to keep surface area small and failure modes easy to reason
about. The in-memory `job_id` store (for `GET /api/extract/{job_id}`) is a
forward-compatibility shim that would be replaced with Redis/DB in
production.

---

## Setup

### Python / Node requirements

| Component | Required version |
|-----------|-----------------|
| Python    | 3.10 or higher (developed on 3.12) |
| Node.js   | 18 or higher (developed on 20) |

### Backend

```bash
cd backend
python -m venv venv

# Activate the virtual environment
# macOS/Linux:
source venv/bin/activate
# Windows PowerShell:
venv\Scripts\Activate.ps1
# Windows cmd:
venv\Scripts\activate.bat

pip install -r requirements.txt

# Copy the example env file and add your key (optional — leave blank for mock mode)
cp .env.example .env

# Start the server
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.
Interactive docs (Swagger UI): `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local   # points to http://localhost:8000 by default
npm run dev
```

Open `http://localhost:3000`.

### Docker (optional — requires Docker Compose)

```bash
# Copy backend env file first
cp backend/.env.example backend/.env

docker compose up --build
```

Builds and runs both services. Frontend at `http://localhost:3000`,
backend at `http://localhost:8000`.

---

## No API key? No problem.

With `GEMINI_API_KEY` unset (or blank), the backend serves a deterministic,
schema-valid **mock MTO** so the full flow (upload → processing → results
table → CSV export → Excel export) is testable out of the box. The mock
response is clearly labelled with `"mock": true` and the frontend displays
a banner.

---

## Environment variables

| Variable | Where | Purpose | Default |
|---|---|---|---|
| `GEMINI_API_KEY` | backend | Google AI Studio key for the Gemini vision model | (empty = mock mode) |
| `GEMINI_MODEL` | backend | Gemini model name | `gemini-2.5-flash` |
| `CORS_ORIGINS` | backend | Comma-separated list of allowed origins | `http://localhost:3000` |
| `MOCK_FALLBACK_ON_ERROR` | backend | Fall back to mock MTO if the live pipeline throws | `true` |
| `NEXT_PUBLIC_API_BASE_URL` | frontend | Backend base URL | `http://localhost:8000` |

---

## API reference

| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/api/health` | Liveness check → `{"status":"ok"}` |
| `POST` | `/api/extract` | multipart file → `MTOResponse` JSON |
| `POST` | `/api/extract/csv` | `{"mto": MTOResponse}` → CSV file download |
| `GET`  | `/api/extract/{job_id}` | Look up a previous result by ID (in-memory, resets on restart) |

Full interactive docs at `http://localhost:8000/docs` (Swagger UI, generated
automatically by FastAPI).

---

## AI pipeline explanation

### 1. Pre-process (`app/pipeline/preprocess.py`)

- Validates content-type (PNG, JPG, PDF only) and file size (≤ 20 MB) both
  client-side and server-side.
- Renders the **first page** of a PDF to PNG via PyMuPDF at ~200 DPI (chosen
  to preserve fine linework on dense drawings), then normalises any uploaded
  image through Pillow.
- Caps the longest side to **2000 px** with LANCZOS resampling before
  sending to the model — Gemini's vision input doesn't benefit from higher
  resolution and larger payloads slow the round-trip.

### 2. Extract (`app/pipeline/gemini_client.py`)

- Sends the preprocessed PNG + a domain-rich prompt
  (`app/prompts/extract_prompt.txt`) to `gemini-2.5-flash`.
- Uses Gemini's **structured-output mode** (`response_mime_type:
  application/json`, `response_schema: <JSON Schema>`) so the response is
  directly parseable JSON with zero markdown-fence stripping.
- Supports both the new `google-genai` SDK (v1.x) and the legacy
  `google-generativeai` SDK (v0.x), trying the new one first.
- Temperature set to **0.1** to minimise hallucination while still allowing
  the model to reason about ambiguous symbols.

### 3. Post-process / validate (`app/pipeline/postprocess.py`)

- Validates raw JSON into **Pydantic models** (rejects malformed data rather
  than crashing; surfaces a clean `PostprocessError`).
- Derives **gasket and bolt-set rows** if the model didn't report them
  explicitly: 1 gasket + 1 bolt set per flanged joint (approximated as 1 per
  FLANGE item + 1 per valve with `end_type == FLGD`). Derived rows are
  flagged in `remarks`.
- Recomputes all **summary totals server-side** — the model's own arithmetic
  is never trusted.

### 4. Mock fallback (`app/pipeline/mock_pipeline.py`)

- Used automatically when `GEMINI_API_KEY` is unset, or when the live call
  throws and `MOCK_FALLBACK_ON_ERROR=true`.
- Returns a fixed, schema-valid MTO (6" carbon steel line with pipe, 4
  fittings, 2 flanges, 1 valve, 2 gaskets, 2 bolt sets, 1 support with field
  weld) with `mock: true`.

### Prompt strategy

The prompt (`app/prompts/extract_prompt.txt`) teaches the model:
- Isometric drawing conventions (title block layout, line-number format).
- The full component glossary (elbows, tees, reducers, flanges, valves,
  olets, caps, supports).
- Weld point recognition (shop vs field welds).
- Unit conventions (pipe by length in metres, discrete items by count,
  bolts by set).
- The gasket/bolt derivation rule (1 per flanged joint).
- Confidence reporting instructions.

The JSON schema (`app/prompts/mto_schema.json`) enforces the output
structure at the model level, so every field has the right type without
any post-hoc regex parsing.

---

## Frontend features

- **Drag-and-drop + file picker** with client-side validation (type, size)
- **Animated processing steps** showing pipeline progress while waiting
- **Results panel**:
  - Drawing preview (image files) or PDF placeholder
  - Extracted title-block metadata
  - Summary cards with icons
  - Full MTO table with colour-coded confidence badges (% shown)
  - **Export CSV** (via backend endpoint)
  - **Export Excel** (client-side via SheetJS; two-sheet workbook: items + summary)
- **Mock data banner** when running without a live API key
- Responsive layout (mobile → tablet → desktop)
- Full keyboard accessibility (tabIndex, ARIA roles, live regions, skip link)

---

## Running tests

```bash
cd backend

# Activate your virtual environment first
# macOS/Linux: source venv/bin/activate
# Windows: venv\Scripts\Activate.ps1

PYTHONPATH=. pytest tests/ -v
```

Test coverage includes:
- Pydantic model validation (valid and invalid inputs)
- `/api/extract` endpoint happy-path, bad content-type, oversized file
- `/api/extract/csv` round-trip
- Gasket/bolt derivation logic
- Server-side summary computation
- `process_raw_extraction` end-to-end

---

## Assumptions

- One isometric drawing per upload; multi-sheet PDFs use only the first page.
- English-language drawings using standard ASME/ANSI-style piping symbols.
- Pipe length is reported as one aggregated row per distinct size/spec,
  summed across all straight runs (not one row per segment).
- Confidence scores are the model's own self-assessment, not an independently
  computed metric — treat them as a rough triage signal, not ground truth.
- "Flanged joint" is approximated as 1 per FLANGE item + 1 per FLGD valve
  for the gasket/bolt derivation; this may over-count on blind flanges or
  under-count on unusual configurations.

## Known limitations

- Dense or low-resolution drawings, hand-drawn isometrics, and heavily
  rotated/overlapping label text reduce extraction accuracy.
- No OCR/CV fallback — purely a single vision-model pass per drawing.
- In-memory result storage: `GET /api/extract/{job_id}` only works until the
  backend process restarts.
- No authentication or rate limiting — not suitable for public deployment.
- Excel export is client-side only (SheetJS); backend CSV is server-side.

## What I'd improve with more time

1. **Async job-queue design** so very large PDFs don't block on a single
   synchronous HTTP request.
2. **Second validation pass**: a lightweight OCR check on the BOM table
   (if present on the drawing) to cross-validate the vision model's reading.
3. **Bounding-box overlay** on the drawing preview showing where each MTO
   row was detected, to make low-confidence items easy to manually verify.
4. **Persistent storage** (Postgres/SQLite) instead of the in-memory dict.
5. **Multi-sheet PDF support** (currently only page 1 is used).
6. **Confidence calibration**: the model's self-reported confidence is
   uncalibrated — a small labeled dataset could train a simple classifier to
   produce calibrated scores.

---

## Repo layout

```
backend/
  app/
    main.py                 FastAPI app + routes
    models.py               Pydantic schema (DrawingMeta, MTOItem, MTOResponse)
    pipeline/
      preprocess.py          upload validation, PDF/image → PNG
      gemini_client.py       Gemini vision call, structured output (new + legacy SDK)
      mock_pipeline.py       deterministic fallback MTO
      postprocess.py         validation, gasket/bolt derivation, summary
    prompts/
      extract_prompt.txt     vision model instructions
      mto_schema.json        JSON schema for structured output
  tests/
    test_models.py
    test_extract_endpoint.py
    test_postprocess.py      (gasket/bolt derivation, summary computation)
  Dockerfile
  requirements.txt
  .env.example
frontend/
  app/
    page.tsx                 upload/processing/results/error states
    layout.tsx               root layout + SEO metadata
    globals.css              base styles
    components/
      UploadDropzone.tsx      drag-drop + file picker (keyboard accessible)
      SummaryCards.tsx        summary stats with icons
      MTOTable.tsx            MTO line-items table with confidence badges
      DrawingMetaPanel.tsx    title-block metadata + drawing preview
    lib/
      api.ts                  fetch wrapper to the backend
      types.ts                shared TypeScript types
      excel.ts                client-side Excel export (SheetJS)
  Dockerfile
  package.json
  .env.example
docker-compose.yml
.gitignore
samples/                     sample isometric drawings used for testing
screenshots/                 app screenshots
README.md
```
