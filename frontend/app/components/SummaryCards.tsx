import { Activity, Disc, Layers, Ruler, Settings, Wrench, Zap } from "lucide-react";
import type { LucideProps } from "lucide-react";
import type { ForwardRefExoticComponent, RefAttributes } from "react";
import type { Summary } from "../lib/types";

// Use the actual Lucide icon component type to avoid generic component narrowing issues
type LucideIcon = ForwardRefExoticComponent<Omit<LucideProps, "ref"> & RefAttributes<SVGSVGElement>>;

interface Card {
  label: string;
  value: string | number;
  icon: LucideIcon;
  unit?: string;
}

export default function SummaryCards({ summary }: { summary: Summary }) {
  const cards: Card[] = [
    {
      label: "Pipe length",
      value: summary.total_pipe_length_m,
      unit: "m",
      icon: Ruler,
    },
    { label: "Fittings", value: summary.fittings, icon: Settings },
    { label: "Flanges", value: summary.flanges, icon: Disc },
    { label: "Valves", value: summary.valves, icon: Activity },
    { label: "Gaskets", value: summary.gaskets, icon: Layers },
    { label: "Bolt sets", value: summary.bolt_sets, icon: Wrench },
    { label: "Field welds", value: summary.field_welds, icon: Zap },
  ];

  return (
    <div
      className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3 mb-6"
      role="region"
      aria-label="MTO summary"
    >
      {cards.map((c) => {
        const Icon = c.icon;
        return (
          <div
            key={c.label}
            className="rounded-lg border border-[#D8DCD6] bg-white px-3 py-3 text-center hover:border-[#B0BAC3] transition-colors"
          >
            <Icon className="w-4 h-4 mx-auto text-[#9AA5AD] mb-1.5" strokeWidth={1.5} aria-hidden />
            <p className="text-lg font-semibold text-navy font-mono leading-tight">
              {c.value}
              {c.unit && (
                <span className="text-xs font-normal text-[#7A848C] ml-0.5">{c.unit}</span>
              )}
            </p>
            <p className="text-[10px] uppercase tracking-wide text-[#9AA5AD] mt-0.5 leading-tight">
              {c.label}
            </p>
          </div>
        );
      })}
    </div>
  );
}
