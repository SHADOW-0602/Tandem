"use client";

import React from "react";
import { getAgentCharacter, AgentCharacter } from "@/lib/personas";
import { Radio, Stethoscope, HardHat, Headphones, Truck, ShieldCheck, User } from "lucide-react";

interface CharacterAvatarProps {
  verticalId: string;
  size?: "sm" | "md" | "lg" | "xl";
  isSpeaking?: boolean;
  showBadge?: boolean;
  className?: string;
}

const ICON_MAP: Record<string, React.ElementType> = {
  dispatch: Radio,
  healthcare: Stethoscope,
  field_worker: HardHat,
  customer_support: Headphones,
  logistics_fleet: Truck,
  financial_compliance: ShieldCheck,
};

export const CharacterAvatar: React.FC<CharacterAvatarProps> = ({
  verticalId,
  size = "md",
  isSpeaking = false,
  showBadge = false,
  className = "",
}) => {
  const character = getAgentCharacter(verticalId);
  const Icon = ICON_MAP[verticalId] || User;

  const sizeClasses = {
    sm: "w-8 h-8 text-xs",
    md: "w-11 h-11 text-sm",
    lg: "w-14 h-14 text-base",
    xl: "w-20 h-20 text-xl",
  };

  const iconSizes = {
    sm: "w-4 h-4",
    md: "w-5 h-5",
    lg: "w-6 h-6",
    xl: "w-9 h-9",
  };

  return (
    <div className={`relative inline-flex items-center justify-center ${className}`}>
      {/* Speaking Aura Animation */}
      {isSpeaking && (
        <span
          className="absolute inset-0 rounded-2xl animate-ping opacity-40 pointer-events-none"
          style={{ backgroundColor: character.accentColor }}
        />
      )}

      {/* Main Avatar Body */}
      <div
        className={`relative ${sizeClasses[size]} rounded-2xl bg-gradient-to-br ${character.avatarGradient} border ${
          isSpeaking ? "border-white shadow-lg" : character.avatarBorderColor
        } flex items-center justify-center text-white font-bold tracking-tight shadow-md transition-all duration-200`}
        style={isSpeaking ? { boxShadow: `0 0 20px ${character.accentColor}66` } : undefined}
      >
        <Icon className={`${iconSizes[size]} text-white drop-shadow-sm`} />

        {/* Live Call / Speaking indicator dot */}
        {isSpeaking && (
          <span
            className="absolute -top-1 -right-1 w-3.5 h-3.5 rounded-full border-2 border-[#111013] animate-pulse"
            style={{ backgroundColor: character.accentColor }}
          />
        )}
      </div>

      {/* Optional Callsign Badge on bottom */}
      {showBadge && (
        <span
          className="absolute -bottom-2 px-1.5 py-0.2 rounded font-mono text-[9px] font-bold border border-white/20 shadow-sm"
          style={{
            backgroundColor: `${character.accentColor}22`,
            color: character.accentColor,
          }}
        >
          {character.callsign}
        </span>
      )}
    </div>
  );
};
