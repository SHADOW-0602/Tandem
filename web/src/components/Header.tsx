"use client";

import React from "react";
import { Activity, Zap } from "lucide-react";
import { CharacterAvatar } from "./CharacterAvatar";
import { getAgentCharacter } from "@/lib/personas";

interface HeaderProps {
  activeVerticalId: string;
  activeVerticalName: string;
  isCallActive: boolean;
}

export const Header: React.FC<HeaderProps> = ({ activeVerticalId, activeVerticalName, isCallActive }) => {
  const character = getAgentCharacter(activeVerticalId);

  return (
    <header className="border-b border-white/[0.08] bg-[#0e0e13]/85 backdrop-blur-xl px-6 py-3.5 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        {/* Left: Brand & Tagline in Tandem Aesthetic */}
        <div className="flex items-center space-x-3.5">
          <div className="w-9 h-9 rounded-lg bg-[#efebdd] flex items-center justify-center shadow-sm">
            <Zap className="w-5 h-5 text-black fill-black" />
          </div>
          <div>
            <div className="flex items-center space-x-2.5">
              <h1 className="text-lg font-semibold tracking-tight text-[#fffaea] flex items-center gap-2">
                Tandem <span className="text-[10px] px-2 py-0.5 rounded font-mono font-medium tracking-wide bg-[#62f6b5]/10 border border-[#62f6b5]/30 text-[#62f6b5]">SUB-10MS</span>
              </h1>
            </div>
            <p className="text-[11px] text-[#a1a1aa] font-normal">
              Intelligent Voice Operations &bull; Real-Time Context Engine
            </p>
          </div>
        </div>

        {/* Center/Right: Live System Metrics & Active Character */}
        <div className="flex items-center flex-wrap gap-2.5 text-xs">
          {/* Active Character Agent Pill */}
          <div className="px-3 py-1.5 rounded-lg bg-[#151419] border border-white/[0.1] flex items-center space-x-2.5 shadow-sm">
            <CharacterAvatar verticalId={activeVerticalId} size="sm" isSpeaking={isCallActive} />
            <div className="flex flex-col text-left">
              <div className="flex items-center space-x-1.5">
                <span className="font-bold text-[#fffaea] text-xs leading-none">{character.characterName}</span>
                <span
                  className="text-[9px] font-mono font-semibold px-1 py-0.2 rounded border border-white/10"
                  style={{
                    backgroundColor: `${character.accentColor}18`,
                    color: character.accentColor,
                  }}
                >
                  {character.callsign}
                </span>
              </div>
              <span className="text-[#a1a1aa] text-[10px] mt-0.5">{character.roleTitle}</span>
            </div>
          </div>

          {/* Sub-10ms Badge */}
          <div className="px-3 py-1.5 rounded-md bg-[#0d241e]/70 border border-[#62f6b5]/30 flex items-center space-x-2 glow-sub10">
            <span className="w-1.5 h-1.5 rounded-full bg-[#62f6b5] animate-pulse" />
            <span className="text-[#9acdbf] text-[11px]">Retrieval SLA:</span>
            <span className="font-mono font-semibold text-[#62f6b5] text-[11px]">&lt; 10ms</span>
          </div>

          {/* Response Budget SLA */}
          <div className="px-3 py-1.5 rounded-md bg-[#111013] border border-white/[0.08] flex items-center space-x-2">
            <Activity className="w-3.5 h-3.5 text-[#efebdd]" />
            <span className="text-[#a1a1aa] text-[11px]">Turnaround:</span>
            <span className="font-mono font-medium text-[#efebdd] text-[11px]">~580ms</span>
          </div>

          {/* Call State */}
          <div
            className={`px-3 py-1.5 rounded-md border text-[11px] font-medium flex items-center space-x-2 transition-colors ${
              isCallActive
                ? "bg-red-950/40 border-red-500/30 text-red-300"
                : "bg-[#111013] border-white/[0.08] text-[#71717a]"
            }`}
          >
            <span className={`w-1.5 h-1.5 rounded-full ${isCallActive ? "bg-red-400 animate-ping" : "bg-neutral-600"}`} />
            <span>{isCallActive ? "CALL ACTIVE" : "IDLE"}</span>
          </div>
        </div>
      </div>
    </header>
  );
};
