"use client";

import {
  AlertTriangle,
  CheckCircle,
  Crosshair,
  Download,
  FileSpreadsheet,
  FileWarning,
  Loader2,
  RefreshCw,
} from "lucide-react";
import { useState } from "react";
import DrawingMetaPanel from "./components/DrawingMetaPanel";
import MTOTable from "./components/MTOTable";
import SummaryCards from "./components/SummaryCards";
import UploadDropzone from "./components/UploadDropzone";
import { ApiRequestError, exportCsv, extractMto } from "./lib/api";
import { exportExcel } from "./lib/excel";
import type { MTOResponse } from "./lib/types";

type ViewState = "idle" | "processing" | "done" | "error";

const PROCESSING_STEPS = [
  "Validating upload…",
  "Preprocessing drawing…",
  "Running AI vision extraction…",
  "Validating and computing MTO…",
];

export default function Home() {
  const [state, setState] = useState<ViewState>("idle");
  const [errorMsg, setErrorMsg] = useState("");
  const [result, setResult] = useState<MTOResponse | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [isPdf, setIsPdf] = useState(false);
  const [fileName, setFileName] = useState<string>("");
  const [processingStep, setProcessingStep] = useState(0);
  const [excelExporting, setExcelExporting] = useState(false);

  const runExtraction = async (file: File) => {
    const isFilePdf = file.type === "application/pdf";
    setFileName(file.name);
    setIsPdf(isFilePdf);
    setPreview(!isFilePdf ? URL.createObjectURL(file) : null);
    setState("processing");
    setProcessingStep(0);

    // Simulate incremental step progress while waiting for the API
    const stepInterval = setInterval(() => {
      setProcessingStep((s) => Math.min(s + 1, PROCESSING_STEPS.length - 1));
    }, 1800);

    try {
      const mto = await extractMto(file);
      clearInterval(stepInterval);
      setResult(mto);
      setState("done");
    } catch (e) {
      clearInterval(stepInterval);
      const message =
        e instanceof ApiRequestError ? e.message : "Something unexpected went wrong.";
      setErrorMsg(message);
      setState("error");
    }
  };

  const handleError = (message: string) => {
    setErrorMsg(message);
    setState("error");
  };

  const reset = () => {
    if (preview) URL.revokeObjectURL(preview);
    setState("idle");
    setResult(null);
    setPreview(null);
    setIsPdf(false);
    setErrorMsg("");
    setProcessingStep(0);
  };

  const handleExportCsv = async () => {
    if (!result) return;
    try {
      const blob = await exportCsv(result);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${result.drawing_meta.drawing_no || "mto"}.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (e) {
      const message = e instanceof ApiRequestError ? e.message : "CSV export failed.";
      setErrorMsg(message);
      setState("error");
    }
  };

  const handleExportExcel = async () => {
    if (!result || excelExporting) return;
    setExcelExporting(true);
    try {
      await exportExcel(result);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Excel export failed.";
      setErrorMsg(msg);
      setState("error");
    } finally {
      setExcelExporting(false);
    }
  };

  return (
    <div className="min-h-screen w-full bg-paper text-ink">
      {/* Subtle engineering grid backdrop */}
      <div
        aria-hidden
        className="fixed inset-0 pointer-events-none opacity-[0.04]"
        style={{
          backgroundImage:
            "linear-gradient(#12263A 1px, transparent 1px), linear-gradient(90deg, #12263A 1px, transparent 1px)",
          backgroundSize: "28px 28px",
        }}
      />

      {/* Header */}
      <header className="relative border-b border-[#D8DCD6] bg-navy" role="banner">
        <div className="max-w-6xl mx-auto px-6 py-5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Crosshair className="w-6 h-6 text-[#7FB3C9]" strokeWidth={1.5} aria-hidden />
            <div>
              <h1 className="text-white text-lg font-semibold tracking-tight">
                Isometric &rarr; MTO Generator
              </h1>
              <p className="text-[#93A3B3] text-xs font-mono">
                one drawing in — a validated bill of materials out
              </p>
            </div>
          </div>
        </div>
      </header>

      <main className="relative max-w-6xl mx-auto px-6 py-10" id="main-content">
        {/* ── Idle: Upload ───────────────────────────────────────────────── */}
        {state === "idle" && (
          <div className="max-w-2xl mx-auto" role="region" aria-label="Upload drawing">
            <div className="mb-6 text-center">
              <h2 className="text-2xl font-semibold text-navy">Upload a piping isometric</h2>
              <p className="text-sm text-[#5C6773] mt-1">
                PNG, JPG, or PDF · one drawing per upload · max 20 MB
              </p>
            </div>
            <UploadDropzone onFileReady={runExtraction} onError={handleError} />
          </div>
        )}

        {/* ── Processing ─────────────────────────────────────────────────── */}
        {state === "processing" && (
          <div
            className="max-w-2xl mx-auto"
            role="status"
            aria-live="polite"
            aria-label="Processing drawing"
          >
            <div className="rounded-lg border border-[#D8DCD6] bg-white p-8">
              <div className="flex flex-col items-center text-center mb-6">
                <Loader2 className="w-8 h-8 text-steel animate-spin mb-3" aria-hidden />
                <p className="text-sm font-medium text-ink">Running AI extraction pipeline…</p>
                <p className="text-xs text-[#7A848C] mt-1 font-mono">{fileName}</p>
              </div>
              <ol className="space-y-2">
                {PROCESSING_STEPS.map((step, idx) => {
                  const done = idx < processingStep;
                  const active = idx === processingStep;
                  return (
                    <li
                      key={step}
                      className={`flex items-center gap-2.5 text-sm transition-all ${
                        done
                          ? "text-[#2E7D5B]"
                          : active
                          ? "text-ink font-medium"
                          : "text-[#C7CDD1]"
                      }`}
                    >
                      {done ? (
                        <CheckCircle className="w-4 h-4 flex-shrink-0" aria-hidden />
                      ) : active ? (
                        <Loader2 className="w-4 h-4 flex-shrink-0 animate-spin" aria-hidden />
                      ) : (
                        <div className="w-4 h-4 rounded-full border-2 border-current flex-shrink-0" aria-hidden />
                      )}
                      {step}
                    </li>
                  );
                })}
              </ol>
            </div>
          </div>
        )}

        {/* ── Error ──────────────────────────────────────────────────────── */}
        {state === "error" && (
          <div
            className="max-w-2xl mx-auto"
            role="alert"
            aria-live="assertive"
          >
            <div className="rounded-lg border border-[#EAD3CB] bg-[#FBF3F0] p-8 text-center">
              <FileWarning className="w-8 h-8 mx-auto text-[#B4472E] mb-3" aria-hidden />
              <p className="font-medium text-[#7A3220]">Something went wrong</p>
              <p className="text-sm text-[#8A5A48] mt-2 max-w-sm mx-auto">{errorMsg}</p>
              <button
                id="try-again-btn"
                onClick={reset}
                className="mt-6 inline-flex items-center gap-2 rounded-md bg-navy hover:bg-navyLight text-white text-sm font-medium px-4 py-2 transition-colors"
              >
                <RefreshCw className="w-4 h-4" aria-hidden /> Try again
              </button>
            </div>
          </div>
        )}

        {/* ── Results ────────────────────────────────────────────────────── */}
        {state === "done" && result && (
          <div role="region" aria-label="Extraction results">
            {/* Mock data banner */}
            {result.mock && (
              <div
                role="note"
                className="mb-5 rounded-md border border-[#E3D8A8] bg-[#FBF6E3] px-4 py-2.5 flex items-center gap-2 text-sm text-[#7A6A2E]"
              >
                <AlertTriangle className="w-4 h-4 flex-shrink-0" aria-hidden />
                <span>
                  <strong>Mock data</strong> — no vision model API key configured on the server.
                  Set{" "}
                  <code className="text-xs bg-white/60 px-1 rounded font-mono">GEMINI_API_KEY</code>{" "}
                  for live extraction.
                </span>
              </div>
            )}

            {/* Toolbar */}
            <div className="flex flex-wrap items-start justify-between gap-4 mb-6">
              <div>
                <h2 className="text-xl font-semibold text-navy">Extraction complete</h2>
                <p className="text-sm text-[#7A848C] mt-0.5 font-mono">{fileName}</p>
              </div>
              <div className="flex flex-wrap gap-2">
                <button
                  id="export-csv-btn"
                  onClick={handleExportCsv}
                  className="inline-flex items-center gap-2 rounded-md border border-[#C7CDD1] bg-white hover:bg-[#F0F2EE] text-sm font-medium px-3.5 py-2 transition-colors"
                >
                  <Download className="w-4 h-4" aria-hidden /> Export CSV
                </button>
                <button
                  id="export-xlsx-btn"
                  onClick={handleExportExcel}
                  disabled={excelExporting}
                  className="inline-flex items-center gap-2 rounded-md border border-[#C7CDD1] bg-white hover:bg-[#F0F2EE] text-sm font-medium px-3.5 py-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {excelExporting ? (
                    <Loader2 className="w-4 h-4 animate-spin" aria-hidden />
                  ) : (
                    <FileSpreadsheet className="w-4 h-4" aria-hidden />
                  )}
                  Export Excel
                </button>
                <button
                  id="new-drawing-btn"
                  onClick={reset}
                  className="inline-flex items-center gap-2 rounded-md bg-navy hover:bg-navyLight text-white text-sm font-medium px-3.5 py-2 transition-colors"
                >
                  <RefreshCw className="w-4 h-4" aria-hidden /> New drawing
                </button>
              </div>
            </div>

            {/* Main results layout */}
            <div className="grid grid-cols-1 lg:grid-cols-[300px_1fr] gap-6">
              <DrawingMetaPanel
                meta={result.drawing_meta}
                preview={preview}
                isPdf={isPdf}
              />
              <div>
                <SummaryCards summary={result.summary} />
                <MTOTable items={result.items} />
                <p className="text-xs text-[#9AA5AD] mt-3">
                  Gasket and bolt-set rows marked &ldquo;Derived&rdquo; were computed server-side
                  (1 each per flanged joint), not read directly off the drawing. Confidence
                  scores are the model&rsquo;s own self-assessment; treat them as triage signals,
                  not ground truth.
                </p>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
