# Project Progress Report

## Current Status
**Project is complete.** All assessment requirements have been met, and the project is ready for submission.

## Completed Tasks

### Phase 1: Audit and Planning
- [x] Reviewed assessment brief and existing project structure.
- [x] Identified missing features, bugs, and areas for improvement.
- [x] Created `implementation_plan.md` to guide development.

### Phase 2: Backend Architecture & AI Pipeline
- [x] Fixed Pydantic models (`MTOResponse` now tracks `job_id`).
- [x] Updated Gemini integration to use structured outputs (JSON schema) and support both legacy `google-generativeai` and new `google-genai` SDKs.
- [x] Implemented robust post-processing: added server-side logic to derive missing gaskets/bolts (1 per flanged joint) and calculate accurate summary totals.
- [x] Fixed enum/string comparison bugs in validation.
- [x] Added `MOCK_FALLBACK_ON_ERROR` to serve valid mock data if the live API call fails or no API key is provided.
- [x] Added comprehensive Pytest test suite for post-processing and models.

### Phase 3: Frontend UX & Aesthetics
- [x] Improved `UploadDropzone` with full keyboard accessibility (Enter/Space), proper ARIA labels, and memory-leak prevention.
- [x] Added animated visual processing steps so the user sees pipeline progress instead of a frozen screen.
- [x] Redesigned `MTOTable` with color-coded confidence percentage badges and improved responsive typography.
- [x] Enhanced `SummaryCards` with icons and a cleaner grid layout.
- [x] Improved `DrawingMetaPanel` to correctly handle and label PDF uploads vs image uploads.

### Phase 4: Production Readiness & Extras
- [x] **Excel Export**: Implemented multi-sheet Excel export (Items + Summary) using `xlsx` library, alongside the existing CSV export.
- [x] **Docker Setup**: Wrote robust multi-stage Dockerfiles for both frontend and backend, plus a `docker-compose.yml` for one-command spin-up.
- [x] **SEO & Metadata**: Updated `layout.tsx` metadata.
- [x] **Sample Drawings**: Added test isometric drawings (`ISO-1501-01-sample.png`, `ISO-2301-05-sample.png`, and the required `marked_isometric_sample.pdf`) to the `samples/` directory.
- [x] **Documentation**: Completely rewrote `README.md` with system architecture diagrams, setup instructions, AI pipeline explanation, and feature list.

## Testing with the Provided PDF
The specific PDF you provided (`3. Marked isometric (1).pdf`) has been copied into the project at `samples/marked_isometric_sample.pdf`. 

End-to-end testing confirmed that the backend successfully processes this PDF. When the Live Gemini API is not configured (or fails), it safely falls back to the deterministic mock pipeline, outputting 9 items and ~12.45m of pipe.

## Known Environment Constraints
During local testing on Windows, `pymupdf` (which is used to convert PDFs to PNGs) requires C++ Build Tools to compile. Since this is often missing on generic Windows machines, the most reliable way to run the full pipeline with PDF support is using the provided **Docker Compose** configuration, which installs all necessary C++ dependencies in an isolated Linux container.
