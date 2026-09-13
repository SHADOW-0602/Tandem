"use client";

import React, { useState, useEffect } from "react";
import { Header } from "@/components/Header";
import { VerticalSelector } from "@/components/VerticalSelector";
import { LatencyWaterfall } from "@/components/LatencyWaterfall";
import { VoiceRoom } from "@/components/VoiceRoom";
import { TranscriptViewer } from "@/components/TranscriptViewer";
import { KnowledgeInspector } from "@/components/KnowledgeInspector";
import { Vertical, TurnTelemetry } from "@/lib/types";
import { fetchVerticals, mintLiveKitToken } from "@/lib/api";
import { CharacterAvatar } from "@/components/CharacterAvatar";
import { getAgentCharacter } from "@/lib/personas";
import { PhoneCall, Radio } from "lucide-react";

export default function DashboardPage() {
  const [verticals, setVerticals] = useState<Vertical[]>([]);
  const [activeVerticalId, setActiveVerticalId] = useState<string>("dispatch");
  const [liveToken, setLiveToken] = useState<string | null>(null);
  const [liveKitUrl, setLiveKitUrl] = useState<string>("wss://parity-9hhf288x.livekit.cloud");
  const [isConnecting, setIsConnecting] = useState(false);
  const [currentTelemetry, setCurrentTelemetry] = useState<TurnTelemetry | null>(null);
  const [turnHistory, setTurnHistory] = useState<TurnTelemetry[]>([]);

  // Load verticals on mount
  useEffect(() => {
    fetchVerticals().then((data) => {
      if (data && data.length > 0) {
        setVerticals(data);
      }
    });
  }, []);

  const activeVertical = verticals.find((v) => v.id === activeVerticalId) || verticals[0] || null;

  // Start live WebRTC call
  const handleStartCall = async () => {
    setIsConnecting(true);
    try {
      const resp = await mintLiveKitToken(undefined, activeVerticalId);
      setLiveToken(resp.token);
      if (resp.url) setLiveKitUrl(resp.url);
    } catch (err) {
      console.error("Failed to start call:", err);
      alert("Failed to connect to voice session. Please ensure control plane is running on http://localhost:8000");
    } finally {
      setIsConnecting(false);
    }
  };

  // Hang up
  const handleEndCall = () => {
    setLiveToken(null);
  };

  // Handle telemetry turn from WebRTC data channel or simulation
  const handleNewTelemetry = (telemetry: TurnTelemetry) => {
    setCurrentTelemetry(telemetry);
    setTurnHistory((prev) => [telemetry, ...prev]);
  };

  return (
    <div className="min-h-screen flex flex-col bg-dark-bg">
      {/* Header */}
      <Header
        activeVerticalId={activeVerticalId}
        activeVerticalName={activeVertical?.name || "Dispatch Operations"}
        isCallActive={Boolean(liveToken)}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-6 space-y-6">
        {/* 1. Vertical Selector Bar */}
        <VerticalSelector
          verticals={verticals}
          activeVerticalId={activeVerticalId}
          onSelect={(vid) => {
            setActiveVerticalId(vid);
            // If in active call, could notify room via data channel
          }}
          disabled={Boolean(liveToken)}
        />

        {/* 2. WebRTC Call Action or Active Room */}
        {liveToken ? (
          <VoiceRoom
            token={liveToken}
            serverUrl={liveKitUrl}
            onDisconnect={handleEndCall}
            onTelemetryReceived={handleNewTelemetry}
            activeVertical={activeVerticalId}
          />
        ) : (() => {
          const character = getAgentCharacter(activeVerticalId);
          return (
            <div className="bg-dark-card border border-dark-border rounded-2xl p-5 flex flex-col sm:flex-row items-center justify-between gap-5 shadow-xl relative overflow-hidden">
              <div
                className="absolute top-0 right-0 w-64 h-64 rounded-full blur-3xl pointer-events-none opacity-15"
                style={{ backgroundColor: character.accentColor }}
              />

              <div className="flex items-center space-x-4">
                <CharacterAvatar
                  verticalId={activeVerticalId}
                  size="lg"
                  showBadge={true}
                />
                <div>
                  <div className="flex items-center space-x-2">
                    <h3 className="text-base font-bold text-dark-cream flex items-center gap-2">
                      <span>Connect with {character.characterName}</span>
                    </h3>
                    <span
                      className="text-[9px] font-mono font-bold px-2 py-0.5 rounded border border-white/10"
                      style={{
                        backgroundColor: `${character.accentColor}18`,
                        color: character.accentColor,
                      }}
                    >
                      {character.callsign}
                    </span>
                  </div>
                  <p className="text-xs text-[#a1a1aa] mt-0.5">
                    <span className="text-white font-medium">{character.roleTitle}</span> &bull; {character.department}
                  </p>
                  <p className="text-xs text-[#9acdbf] mt-1 italic line-clamp-1">
                    &quot;{character.greeting}&quot;
                  </p>
                </div>
              </div>

              <button
                onClick={handleStartCall}
                disabled={isConnecting}
                className="px-6 py-3 rounded-xl bg-dark-cream hover:bg-white text-[#0e0e13] font-bold text-xs uppercase tracking-wider flex items-center space-x-2 transition-all shadow-lg shadow-black/40 hover:shadow-black/60 disabled:opacity-50 flex-shrink-0"
              >
                <PhoneCall className="w-4 h-4 text-[#0e0e13]" />
                <span>{isConnecting ? "Connecting..." : `Start Call with ${character.characterName}`}</span>
              </button>
            </div>
          );
        })()}

        {/* 3. Sub-10ms Latency Waterfall Widget */}
        <LatencyWaterfall telemetry={currentTelemetry} />

        {/* 4. Split Panel: Live Transcripts & Knowledge Base Inspector */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <TranscriptViewer turns={turnHistory} />
          <KnowledgeInspector vertical={activeVertical} />
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-dark-border py-4 text-center text-xs text-dark-muted font-mono">
        Tandem Operations Center
      </footer>
    </div>
  );
}
