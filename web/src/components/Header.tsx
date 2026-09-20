"use client";

import React, { useState } from "react";
import { Zap, Menu, X, PhoneCall, Radio, Shield, Users, Layers, Activity } from "lucide-react";
import { CharacterAvatar } from "./CharacterAvatar";
import { getAgentCharacter } from "@/lib/personas";
import { BackendStatus } from "./BackendStatus";

interface HeaderProps {
  activeVerticalId: string;
  activeVerticalName: string;
  isCallActive: boolean;
}

export const Header: React.FC<HeaderProps> = ({ activeVerticalId, activeVerticalName, isCallActive }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const character = getAgentCharacter(activeVerticalId);

  return (
    <header className="w-full sticky top-0 z-50 bg-[#0e0e13]/95 backdrop-blur-xl border-b border-white/[0.08] transition-all">
      <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Left: Brand Logo & Tagline */}
          <div className="flex items-center space-x-3 flex-shrink-0">
            <a href="#" className="flex items-center space-x-2.5 group">
              <div className="w-8 h-8 rounded-lg bg-[#efebdd] flex items-center justify-center shadow-sm group-hover:scale-105 transition-transform">
                <Zap className="w-4 h-4 text-black fill-black" />
              </div>
              <div className="flex flex-col">
                <span className="text-xl font-bold tracking-tight text-[#fffaea] leading-tight">
                  Tandem
                </span>
                <span className="hidden sm:inline text-[10px] text-[#a1a1aa] font-normal leading-none mt-0.5">
                  Intelligent Voice Operations
                </span>
              </div>
            </a>
          </div>

          {/* Desktop Navigation Links */}
          <nav className="hidden md:flex items-center space-x-1 text-xs text-[#a1a1aa]">
            <a
              href="#terminal"
              className="px-3 py-1.5 rounded-lg hover:text-[#fffaea] hover:bg-white/[0.04] transition-colors font-medium"
            >
              Voice Terminal
            </a>
            <a
              href="#capabilities"
              className="px-3 py-1.5 rounded-lg hover:text-[#fffaea] hover:bg-white/[0.04] transition-colors font-medium"
            >
              Capabilities
            </a>
            <a
              href="#architecture"
              className="px-3 py-1.5 rounded-lg hover:text-[#fffaea] hover:bg-white/[0.04] transition-colors font-medium"
            >
              Performance
            </a>
            <a
              href="#questions-guide"
              className="px-3 py-1.5 rounded-lg hover:text-[#62f6b5] hover:bg-white/[0.04] transition-colors font-medium text-[#62f6b5]/90"
            >
              Questions Guide
            </a>
          </nav>

          {/* Right: Backend Health Status & Active Persona Pill (Desktop) */}
          <div className="hidden lg:flex items-center space-x-2.5 text-xs flex-shrink-0">
            {/* Real-time Backend Health Status */}
            <BackendStatus />

            {/* Active Character Agent Pill */}
            <div className="px-2.5 py-1.5 rounded-lg bg-[#151419] border border-white/[0.1] flex items-center space-x-2 shadow-sm">
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

            {/* Call Active Indicator */}
            {isCallActive && (
              <div className="px-2.5 py-1.5 rounded-md border border-red-500/30 bg-red-950/40 text-red-300 text-[11px] font-medium flex items-center space-x-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-red-400 animate-ping" />
                <span className="font-mono text-[10px]">LIVE CALL</span>
              </div>
            )}
          </div>

          {/* Mobile Right Controls: Status & Hamburger Button */}
          <div className="flex items-center space-x-2 lg:hidden">
            {/* Call Active Indicator on mobile */}
            {isCallActive && (
              <div className="px-2 py-1 rounded-md border border-red-500/30 bg-red-950/40 text-red-300 text-[10px] font-medium flex items-center space-x-1">
                <span className="w-1.5 h-1.5 rounded-full bg-red-400 animate-ping" />
                <span>CALL ACTIVE</span>
              </div>
            )}

            {/* Mobile Menu Toggle Button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-lg bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] text-[#fffaea] transition-colors cursor-pointer"
              aria-label="Toggle Navigation Menu"
            >
              {mobileMenuOpen ? (
                <X className="w-5 h-5 text-white" />
              ) : (
                <Menu className="w-5 h-5 text-white" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer / Dropdown Menu */}
      {mobileMenuOpen && (
        <div className="lg:hidden border-t border-white/[0.08] bg-[#0e0e13] px-4 py-4 space-y-4 shadow-2xl transition-all">
          {/* Navigation Links */}
          <nav className="flex flex-col space-y-1 text-sm font-medium">
            <a
              href="#terminal"
              onClick={() => setMobileMenuOpen(false)}
              className="px-3 py-2 rounded-lg hover:bg-white/[0.06] text-[#fffaea] flex items-center justify-between transition-colors"
            >
              <span>Voice Terminal</span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#62f6b5]/10 text-[#62f6b5]">LIVE</span>
            </a>
            <a
              href="#capabilities"
              onClick={() => setMobileMenuOpen(false)}
              className="px-3 py-2 rounded-lg hover:bg-white/[0.06] text-[#a1a1aa] hover:text-white transition-colors"
            >
              Capabilities
            </a>
            <a
              href="#architecture"
              onClick={() => setMobileMenuOpen(false)}
              className="px-3 py-2 rounded-lg hover:bg-white/[0.06] text-[#a1a1aa] hover:text-white transition-colors"
            >
              Performance &amp; SLA
            </a>
            <a
              href="#questions-guide"
              onClick={() => setMobileMenuOpen(false)}
              className="px-3 py-2 rounded-lg hover:bg-white/[0.06] text-[#62f6b5] hover:text-white transition-colors flex items-center justify-between"
            >
              <span>Questions Guide</span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#62f6b5]/10 text-[#62f6b5]">RUNBOOK</span>
            </a>
          </nav>

          {/* Active Agent Info Card on Mobile */}
          <div className="p-3 rounded-xl bg-[#151419] border border-white/[0.08] flex items-center space-x-3">
            <CharacterAvatar verticalId={activeVerticalId} size="md" isSpeaking={isCallActive} />
            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-1.5">
                <span className="font-bold text-white text-xs truncate">{character.characterName}</span>
                <span
                  className="text-[9px] font-mono px-1 py-0.2 rounded border border-white/10"
                  style={{
                    backgroundColor: `${character.accentColor}18`,
                    color: character.accentColor,
                  }}
                >
                  {character.callsign}
                </span>
              </div>
              <p className="text-[11px] text-[#a1a1aa] truncate">{character.roleTitle}</p>
            </div>
          </div>

          {/* Backend Status Section on Mobile */}
          <div className="pt-2 border-t border-white/[0.06] flex flex-col gap-2">
            <span className="text-[10px] uppercase font-mono tracking-wider text-[#71717a]">
              Infrastructure Health
            </span>
            <BackendStatus />
          </div>
        </div>
      )}
    </header>
  );
};
