"use client";

import React from "react";
import { Vertical } from "@/lib/types";
import { Radio, Stethoscope, HardHat, Headphones, Truck, ShieldCheck } from "lucide-react";

interface VerticalSelectorProps {
  verticals: Vertical[];
  activeVerticalId: string;
  onSelect: (verticalId: string) => void;
  disabled?: boolean;
}

const ICON_MAP: Record<string, React.ReactNode> = {
  dispatch: <Radio className="w-3.5 h-3.5" />,
  healthcare: <Stethoscope className="w-3.5 h-3.5" />,
  field_worker: <HardHat className="w-3.5 h-3.5" />,
  customer_support: <Headphones className="w-3.5 h-3.5" />,
  logistics_fleet: <Truck className="w-3.5 h-3.5" />,
  financial_compliance: <ShieldCheck className="w-3.5 h-3.5" />,
};

export const VerticalSelector: React.FC<VerticalSelectorProps> = ({
  verticals,
  activeVerticalId,
  onSelect,
  disabled = false,
}) => {
  return (
    <div className="w-full bg-[#111013] border border-white/[0.08] rounded-xl p-3.5 shadow-md">
      <div className="flex items-center justify-between mb-2.5 px-1">
        <span className="text-[11px] font-medium uppercase tracking-eyebrow text-[#a1a1aa]">
          Enterprise Operational Domain
        </span>
        <span className="text-[10px] text-[#71717a] font-mono tracking-wider">
          MOSS HOT CACHE + QDRANT PARTITION
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
        {verticals.map((v) => {
          const isSelected = v.id === activeVerticalId;
          const icon = ICON_MAP[v.id] || <Radio className="w-3.5 h-3.5" />;

          return (
            <button
              key={v.id}
              onClick={() => onSelect(v.id)}
              disabled={disabled}
              className={`flex flex-col items-start p-2.5 rounded-lg border text-left transition-all duration-150 ${
                isSelected
                  ? "bg-[#1f1f23] border-[#62f6b5]/60 text-[#fffaea] shadow-sm shadow-[#62f6b5]/10"
                  : "bg-transparent border-white/[0.06] text-[#a1a1aa] hover:border-white/[0.15] hover:bg-white/[0.02] hover:text-[#fffaea]"
              } ${disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
            >
              <div className="flex items-center justify-between w-full mb-2">
                <span
                  className={`p-1.5 rounded-md ${
                    isSelected
                      ? "bg-[#62f6b5]/15 text-[#62f6b5]"
                      : "bg-white/[0.04] text-[#a1a1aa]"
                  }`}
                >
                  {icon}
                </span>
                {isSelected && (
                  <span className="w-1.5 h-1.5 rounded-full bg-[#62f6b5] animate-pulse" />
                )}
              </div>
              <span className="text-xs font-medium leading-tight line-clamp-1">
                {v.name}
              </span>
              <span className="text-[10px] text-[#71717a] font-mono mt-1 line-clamp-1">
                {v.moss_index}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
};
