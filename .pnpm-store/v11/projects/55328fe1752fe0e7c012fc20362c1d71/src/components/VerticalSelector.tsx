"use client";

import React from "react";
import { Vertical } from "@/lib/types";
import { CharacterAvatar } from "./CharacterAvatar";
import { getAgentCharacter } from "@/lib/personas";
import { Users } from "lucide-react";

interface VerticalSelectorProps {
  verticals: Vertical[];
  activeVerticalId: string;
  onSelect: (verticalId: string) => void;
  disabled?: boolean;
}

export const VerticalSelector: React.FC<VerticalSelectorProps> = ({
  verticals,
  activeVerticalId,
  onSelect,
  disabled = false,
}) => {
  return (
    <div className="w-full bg-[#111013] border border-white/[0.08] rounded-xl p-3.5 shadow-md">
      <div className="flex items-center justify-between mb-3 px-1">
        <div className="flex items-center space-x-2">
          <Users className="w-3.5 h-3.5 text-[#62f6b5]" />
          <span className="text-[11px] font-semibold uppercase tracking-eyebrow text-[#fffaea]">
            Select Agent Character Persona
          </span>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/[0.05] border border-white/[0.08] text-[#a1a1aa] font-mono">
            6 Specialized Operators
          </span>
        </div>
        <span className="text-[10px] text-[#71717a] font-mono tracking-wider hidden sm:inline">
          REAL-TIME CONTEXT ENGINE
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5">
        {verticals.map((v) => {
          const isSelected = v.id === activeVerticalId;
          const character = getAgentCharacter(v.id);

          return (
            <button
              key={v.id}
              onClick={() => onSelect(v.id)}
              disabled={disabled}
              className={`group flex flex-col items-start p-3 rounded-xl border text-left transition-all duration-200 relative overflow-hidden ${
                isSelected
                  ? "bg-[#18171c] border-white/30 text-[#fffaea] shadow-lg"
                  : "bg-[#0e0e13] border-white/[0.06] text-[#a1a1aa] hover:border-white/[0.2] hover:bg-white/[0.02] hover:text-[#fffaea]"
              } ${disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
              style={
                isSelected
                  ? {
                      borderColor: character.accentColor,
                      boxShadow: `0 0 16px ${character.accentColor}25`,
                    }
                  : undefined
              }
            >
              {/* Top Accent Bar on Selected Card */}
              {isSelected && (
                <div
                  className="absolute top-0 left-0 right-0 h-0.5"
                  style={{ backgroundColor: character.accentColor }}
                />
              )}

              {/* Character Avatar & Callsign Badge */}
              <div className="flex items-center justify-between w-full mb-2.5">
                <CharacterAvatar
                  verticalId={v.id}
                  size="sm"
                  isSpeaking={isSelected}
                />
                <span
                  className="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold tracking-tight border border-white/10"
                  style={{
                    backgroundColor: `${character.accentColor}18`,
                    color: character.accentColor,
                  }}
                >
                  {character.callsign}
                </span>
              </div>

              {/* Character Name */}
              <h4 className="text-xs font-bold text-[#fffaea] group-hover:text-white line-clamp-1">
                {character.characterName}
              </h4>

              {/* Character Role / Domain */}
              <span className="text-[10px] text-[#a1a1aa] line-clamp-1 mt-0.5">
                {character.roleTitle}
              </span>

              {/* Key specialty tag */}
              <div className="mt-2 pt-2 border-t border-white/[0.05] w-full flex items-center justify-between text-[9px] font-mono text-[#71717a]">
                <span className="truncate">{character.specialties[0]}</span>
                {isSelected && (
                  <span
                    className="w-1.5 h-1.5 rounded-full animate-pulse ml-1 flex-shrink-0"
                    style={{ backgroundColor: character.accentColor }}
                  />
                )}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};
