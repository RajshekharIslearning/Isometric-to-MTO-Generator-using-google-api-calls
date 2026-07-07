import { FileText, Image as ImageIcon } from "lucide-react";
import type { DrawingMeta } from "../lib/types";

interface MetaFieldProps {
  label: string;
  value: string | null;
  span?: boolean;
  title?: string;
}

function MetaField({ label, value, span, title }: MetaFieldProps) {
  return (
    <div className={span ? "col-span-2" : ""} title={title}>
      <dt className="text-[10px] uppercase tracking-wider text-[#9AA5AD] font-sans">{label}</dt>
      <dd className="text-ink font-medium mt-0.5 truncate" title={value ?? undefined}>
        {value ?? <span className="text-[#C7CDD1]">—</span>}
      </dd>
    </div>
  );
}

interface Props {
  meta: DrawingMeta;
  preview: string | null;
  isPdf?: boolean;
}

export default function DrawingMetaPanel({ meta, preview, isPdf }: Props) {
  const corners = ["top-1 left-1", "top-1 right-1", "bottom-1 left-1", "bottom-1 right-1"] as const;

  return (
    <div
      className="rounded-lg border border-[#D8DCD6] bg-white overflow-hidden h-fit lg:sticky lg:top-6"
      role="complementary"
      aria-label="Drawing metadata"
    >
      {/* Drawing preview / placeholder */}
      <div className="relative aspect-[3/4] bg-paper flex items-center justify-center border-b border-[#D8DCD6]">
        {preview || meta.thumbnail_base64 ? (
          <img
            src={preview || `data:image/png;base64,${meta.thumbnail_base64}`}
            alt="Uploaded isometric drawing preview"
            className="w-full h-full object-contain"
          />
        ) : isPdf ? (
          <div className="flex flex-col items-center gap-2 text-[#C7CDD1]">
            <FileText className="w-10 h-10" strokeWidth={1} aria-hidden />
            <span className="text-xs text-[#9AA5AD]">PDF — no preview</span>
          </div>
        ) : (
          <ImageIcon className="w-10 h-10 text-[#C7CDD1]" strokeWidth={1} aria-hidden />
        )}
        {/* Engineering-style corner brackets */}
        {corners.map((pos) => (
          <span
            key={pos}
            aria-hidden
            className={`absolute ${pos} w-3 h-3 border-[#9AA5AD]`}
            style={{
              borderTopWidth: pos.includes("top") ? 1.5 : 0,
              borderBottomWidth: pos.includes("bottom") ? 1.5 : 0,
              borderLeftWidth: pos.includes("left") ? 1.5 : 0,
              borderRightWidth: pos.includes("right") ? 1.5 : 0,
            }}
          />
        ))}
      </div>

      {/* Title block metadata */}
      <div className="p-4">
        <p className="text-[10px] uppercase tracking-widest text-[#9AA5AD] mb-3 font-mono">
          Title block
        </p>
        <dl className="grid grid-cols-2 gap-x-3 gap-y-3 text-xs font-mono">
          <MetaField label="Drawing No." value={meta.drawing_no} />
          <MetaField label="Rev." value={meta.revision} />
          <MetaField
            label="Line No."
            value={meta.line_number}
            span
            title="Format: Size-Service-Sequence-MaterialClass-Insulation"
          />
          <MetaField label="NPS" value={meta.nps} />
          <MetaField label="Material Cl." value={meta.material_class} />
          <MetaField label="Service" value={meta.service} span />
        </dl>
      </div>
    </div>
  );
}
