import type { MTOResponse } from "./types";

// In production the build-time env var is preferred; fall back to the live
// Render deployment so the hosted Vercel app always reaches the real backend.
const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  (typeof window !== "undefined" && window.location.hostname !== "localhost"
    ? "https://isometric-mto-backend.onrender.com"
    : "http://localhost:8000");

export class ApiRequestError extends Error {
  status?: number;
  constructor(message: string, status?: number) {
    super(message);
    this.name = "ApiRequestError";
    this.status = status;
  }
}

/**
 * Sends the drawing file to the backend extraction pipeline.
 * Returns the full MTOResponse including job_id and summary.
 */
export async function extractMto(file: File): Promise<MTOResponse> {
  const formData = new FormData();
  formData.append("file", file);

  let res: Response;
  try {
    res = await fetch(`${API_BASE}/api/extract`, {
      method: "POST",
      body: formData,
    });
  } catch {
    throw new ApiRequestError(
      "Couldn't reach the extraction service. Check that the backend is running and reachable."
    );
  }

  if (!res.ok) {
    let detail = `Request failed with status ${res.status}.`;
    try {
      const body = await res.json();
      detail = body.detail || body.error || detail;
    } catch {
      // response wasn't JSON — keep the generic message
    }
    throw new ApiRequestError(detail, res.status);
  }

  return res.json();
}

/**
 * Exports the current MTO as a CSV download.
 * Sends the MTO JSON to the backend (excluding job_id which is
 * only used for server-side lookup and not needed for CSV generation).
 */
export async function exportCsv(mto: MTOResponse): Promise<Blob> {
  // Exclude job_id — the CSV endpoint accepts just the MTO body
  const { job_id: _jobId, ...rest } = mto;

  let res: Response;
  try {
    res = await fetch(`${API_BASE}/api/extract/csv`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mto: rest }),
    });
  } catch {
    throw new ApiRequestError("Couldn't reach the export service.");
  }

  if (!res.ok) {
    throw new ApiRequestError(
      `CSV export failed with status ${res.status}.`,
      res.status
    );
  }

  return res.blob();
}
