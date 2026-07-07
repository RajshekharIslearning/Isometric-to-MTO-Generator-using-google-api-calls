"use client";

import { FileText, UploadCloud, X } from "lucide-react";
import { useRef, useState } from "react";

const MAX_MB = 20;
const OK_TYPES = ["image/png", "image/jpeg", "application/pdf"];

interface Props {
  onFileReady: (file: File) => void;
  onError: (message: string) => void;
}

export default function UploadDropzone({ onFileReady, onError }: Props) {
  const [dragOver, setDragOver] = useState(false);
  const [selected, setSelected] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const validate = (file: File): string | null => {
    if (!OK_TYPES.includes(file.type)) {
      return "Unsupported file type. Upload a PNG, JPG, or PDF isometric drawing.";
    }
    if (file.size > MAX_MB * 1024 * 1024) {
      return `File is too large (${(file.size / (1024 * 1024)).toFixed(1)} MB). Max size is ${MAX_MB} MB.`;
    }
    return null;
  };

  const handleFile = (file: File) => {
    const err = validate(file);
    if (err) {
      onError(err);
      return;
    }
    if (preview) URL.revokeObjectURL(preview);
    setSelected(file);
    setPreview(file.type.startsWith("image/") ? URL.createObjectURL(file) : null);
  };

  const clear = () => {
    if (preview) URL.revokeObjectURL(preview);
    setSelected(null);
    setPreview(null);
    // Reset input so the same file can be re-selected if needed
    if (inputRef.current) inputRef.current.value = "";
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      inputRef.current?.click();
    }
  };

  if (selected) {
    return (
      <div
        className="rounded-lg border border-[#D8DCD6] bg-white p-5"
        role="region"
        aria-label="Selected file"
      >
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3 min-w-0">
            {preview ? (
              <img
                src={preview}
                alt="Drawing preview thumbnail"
                className="w-16 h-16 object-cover rounded border border-[#D8DCD6] flex-shrink-0"
              />
            ) : (
              <div className="w-16 h-16 rounded border border-[#D8DCD6] bg-paper flex items-center justify-center flex-shrink-0">
                <FileText className="w-7 h-7 text-[#7A848C]" aria-hidden />
              </div>
            )}
            <div className="min-w-0">
              <p className="font-medium text-sm text-ink truncate" title={selected.name}>
                {selected.name}
              </p>
              <p className="text-xs text-[#7A848C]">
                {(selected.size / 1024).toFixed(0)} KB ·{" "}
                {selected.type === "application/pdf" ? "PDF" : selected.type.split("/")[1].toUpperCase()}
              </p>
            </div>
          </div>
          <button
            onClick={clear}
            className="text-[#9AA5AD] hover:text-[#B4472E] transition-colors flex-shrink-0 rounded p-0.5"
            aria-label="Remove selected file"
          >
            <X className="w-5 h-5" aria-hidden />
          </button>
        </div>
        <button
          id="generate-mto-btn"
          onClick={() => onFileReady(selected)}
          className="mt-5 w-full rounded-md bg-navy hover:bg-navyLight text-white text-sm font-medium py-2.5 transition-colors focus-visible:ring-2 focus-visible:ring-steel focus-visible:ring-offset-2"
        >
          Generate MTO
        </button>
      </div>
    );
  }

  return (
    <div
      role="button"
      tabIndex={0}
      aria-label="Upload drawing: drag and drop or press Enter to browse"
      id="drawing-upload-zone"
      onDragOver={(e) => {
        e.preventDefault();
        setDragOver(true);
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragOver(false);
        const file = e.dataTransfer.files?.[0];
        if (file) handleFile(file);
      }}
      onClick={() => inputRef.current?.click()}
      onKeyDown={handleKeyDown}
      className={`cursor-pointer rounded-lg border-2 border-dashed transition-colors select-none ${
        dragOver
          ? "border-steel bg-[#EAF1F4]"
          : "border-[#C7CDD1] bg-white hover:border-steel hover:bg-[#F7FAFB]"
      } px-8 py-16 flex flex-col items-center justify-center text-center`}
    >
      <UploadCloud
        className={`w-10 h-10 mb-4 transition-colors ${dragOver ? "text-steel" : "text-[#9AA5AD]"}`}
        strokeWidth={1.5}
        aria-hidden
      />
      <p className="font-medium text-ink">Drag and drop your drawing here</p>
      <p className="text-sm text-[#7A848C] mt-1">or click to browse your files</p>
      <p className="text-xs text-[#9AA5AD] mt-3">PNG, JPG, or PDF · max {MAX_MB} MB</p>
      <input
        ref={inputRef}
        id="drawing-file-input"
        type="file"
        accept="image/png,image/jpeg,application/pdf"
        className="hidden"
        aria-hidden="true"
        tabIndex={-1}
        onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
      />
    </div>
  );
}
