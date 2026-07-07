import type { MTOItem } from "../lib/types";

const CATEGORY_STYLES: Record<string, string> = {
  PIPE: "bg-[#EAF1F4] text-[#1F5C73]",
  FITTING: "bg-[#F0EEE4] text-[#7A6A2E]",
  FLANGE: "bg-[#EEEBF6] text-[#5C4C9E]",
  VALVE: "bg-[#FBEAE6] text-[#A34632]",
  GASKET: "bg-[#EDF3E6] text-[#4C7A2E]",
  BOLT: "bg-[#EDF3E6] text-[#4C7A2E]",
  SUPPORT: "bg-[#F1F1F1] text-[#5A5A5A]",
  OTHER: "bg-[#F1F1F1] text-[#5A5A5A]",
};

interface ConfidenceInfo {
  color: string;
  label: string;
  bgColor: string;
}

function getConfidenceInfo(c: number | null | undefined): ConfidenceInfo {
  if (c === null || c === undefined) {
    return { color: "#9AA5AD", label: "n/a", bgColor: "#F1F2F0" };
  }
  if (c >= 0.85) return { color: "#1E6B47", label: `${Math.round(c * 100)}%`, bgColor: "#E8F5EE" };
  if (c >= 0.65) return { color: "#8A5E0A", label: `${Math.round(c * 100)}%`, bgColor: "#FDF3DC" };
  return { color: "#8B3120", label: `${Math.round(c * 100)}%`, bgColor: "#FBE9E4" };
}

function ConfidenceBadge({ confidence }: { confidence: number | null | undefined }) {
  const info = getConfidenceInfo(confidence);
  return (
    <span
      className="inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-semibold font-mono"
      style={{ color: info.color, backgroundColor: info.bgColor }}
      aria-label={`Confidence: ${info.label}`}
    >
      {info.label}
    </span>
  );
}

export default function MTOTable({ items }: { items: MTOItem[] }) {
  if (items.length === 0) {
    return (
      <div className="rounded-lg border border-[#D8DCD6] bg-white p-8 text-center text-sm text-[#7A848C]">
        No MTO items to display.
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-[#D8DCD6] bg-white overflow-hidden" role="region" aria-label="Material Take-Off table">
      <div className="overflow-x-auto">
        <table className="w-full text-sm" aria-label="MTO line items">
          <thead>
            <tr className="bg-paper text-left text-[#5C6773] text-xs uppercase tracking-wide">
              <th scope="col" className="px-3 py-2.5 font-medium whitespace-nowrap">#</th>
              <th scope="col" className="px-3 py-2.5 font-medium whitespace-nowrap">Category</th>
              <th scope="col" className="px-3 py-2.5 font-medium">Description</th>
              <th scope="col" className="px-3 py-2.5 font-medium whitespace-nowrap">Size (NPS)</th>
              <th scope="col" className="px-3 py-2.5 font-medium whitespace-nowrap">Sched/Class</th>
              <th scope="col" className="px-3 py-2.5 font-medium whitespace-nowrap">Material</th>
              <th scope="col" className="px-3 py-2.5 font-medium whitespace-nowrap">End</th>
              <th scope="col" className="px-3 py-2.5 font-medium text-right whitespace-nowrap">Qty</th>
              <th scope="col" className="px-3 py-2.5 font-medium whitespace-nowrap">Unit</th>
              <th scope="col" className="px-3 py-2.5 font-medium text-center whitespace-nowrap">Conf.</th>
            </tr>
          </thead>
          <tbody>
            {items.map((it, i) => (
              <tr
                key={it.item_no}
                className={`border-t border-[#EDEFEC] transition-colors hover:bg-[#F7F8F6] ${
                  i % 2 === 1 ? "bg-[#FBFBFA]" : ""
                }`}
              >
                <td className="px-3 py-2.5 text-[#9AA5AD] font-mono text-xs">{it.item_no}</td>
                <td className="px-3 py-2.5">
                  <span
                    className={`inline-block rounded px-1.5 py-0.5 text-[10px] font-medium whitespace-nowrap ${
                      CATEGORY_STYLES[it.category] ?? "bg-[#F1F1F1] text-[#5A5A5A]"
                    }`}
                  >
                    {it.category}
                  </span>
                </td>
                <td className="px-3 py-2.5 text-ink max-w-[200px]">
                  <span className="line-clamp-2">{it.description}</span>
                  {it.remarks && (
                    <span className="block text-[10px] text-[#9AA5AD] mt-0.5 italic">
                      {it.remarks}
                    </span>
                  )}
                </td>
                <td className="px-3 py-2.5 font-mono text-xs whitespace-nowrap">{it.size_nps ?? "—"}</td>
                <td className="px-3 py-2.5 font-mono text-xs whitespace-nowrap">{it.schedule_rating ?? "—"}</td>
                <td className="px-3 py-2.5 text-[#5C6773] text-xs">{it.material_spec ?? "—"}</td>
                <td className="px-3 py-2.5 font-mono text-xs whitespace-nowrap">{it.end_type ?? "—"}</td>
                <td className="px-3 py-2.5 text-right font-mono text-xs whitespace-nowrap">
                  {it.category === "PIPE" ? (it.length_m ?? it.quantity) : it.quantity}
                </td>
                <td className="px-3 py-2.5 text-[#5C6773] text-xs whitespace-nowrap">
                  {it.category === "PIPE" ? "M" : it.unit}
                </td>
                <td className="px-3 py-2.5 text-center">
                  <ConfidenceBadge confidence={it.confidence} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
