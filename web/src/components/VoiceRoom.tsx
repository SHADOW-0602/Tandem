"use client";

import React, { useState, useEffect } from "react";
import {
  LiveKitRoom,
  RoomAudioRenderer,
  useConnectionState,
  useLocalParticipant,
} from "@livekit/components-react";
import { ConnectionState } from "livekit-client";
import { Mic, MicOff, PhoneOff, Radio, Volume2, Zap } from "lucide-react";
import { TurnTelemetry } from "@/lib/types";

interface VoiceRoomProps {
  token: string | null;
  serverUrl: string;
  onDisconnect: () => void;
  onTelemetryReceived: (telemetry: TurnTelemetry) => void;
  activeVertical: string;
}

export const VoiceRoom: React.FC<VoiceRoomProps> = ({
  token,
  serverUrl,
  onDisconnect,
  onTelemetryReceived,
  activeVertical,
}) => {
  if (!token) return null;

  return (
    <LiveKitRoom
      token={token}
      serverUrl={serverUrl}
      connect={true}
      audio={true}
      video={false}
      onDisconnected={onDisconnect}
      className="w-full"
    >
      <VoiceRoomInner
        onDisconnect={onDisconnect}
        onTelemetryReceived={onTelemetryReceived}
        activeVertical={activeVertical}
      />
      <RoomAudioRenderer />
    </LiveKitRoom>
  );
};

const VoiceRoomInner: React.FC<{
  onDisconnect: () => void;
  onTelemetryReceived: (telemetry: TurnTelemetry) => void;
  activeVertical: string;
}> = ({ onDisconnect, onTelemetryReceived, activeVertical }) => {
  const connectionState = useConnectionState();
  const { localParticipant } = useLocalParticipant();
  const [isMuted, setIsMuted] = useState(false);

  // Toggle Microphone
  const toggleMic = async () => {
    if (localParticipant) {
      const nextState = !isMuted;
      await localParticipant.setMicrophoneEnabled(!nextState);
      setIsMuted(nextState);
    }
  };

  // Instant Barge-In Interruption
  const triggerBargeIn = async () => {
    if (localParticipant) {
      await localParticipant.setMicrophoneEnabled(true);
      setIsMuted(false);
      const payload = JSON.stringify({ type: "barge_in", reason: "user_interrupted" });
      await localParticipant.publishData(new TextEncoder().encode(payload), { reliable: true });
    }
  };

  return (
    <div className="bg-[#111013] border border-white/[0.08] rounded-xl p-5 shadow-2xl relative overflow-hidden">
      {/* Visual Ambient Mint Glow */}
      <div className="absolute top-0 right-1/4 w-48 h-48 bg-[#62f6b5]/10 rounded-full blur-3xl pointer-events-none" />

      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
        {/* Connection & Status info in Tandem Style */}
        <div className="flex items-center space-x-3.5">
          <div className="relative">
            <div
              className={`w-11 h-11 rounded-lg flex items-center justify-center transition-colors ${
                connectionState === ConnectionState.Connected
                  ? "bg-[#0d241e] text-[#62f6b5] border border-[#62f6b5]/40"
                  : "bg-amber-950/30 text-amber-300 border border-amber-500/40 animate-pulse"
              }`}
            >
              <Radio className="w-5 h-5" />
            </div>
            {connectionState === ConnectionState.Connected && (
              <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-[#62f6b5] border-2 border-[#111013] rounded-full" />
            )}
          </div>

          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-sm font-semibold text-[#fffaea]">
                {connectionState === ConnectionState.Connected
                  ? "Full-Duplex Voice Session Active"
                  : "Connecting WebRTC Transport..."}
              </h3>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#1f1f23] border border-white/[0.08] text-[#9acdbf]">
                LiveKit SFU
              </span>
            </div>
            <p className="text-xs text-[#a1a1aa] mt-0.5">
              Domain: <span className="text-[#fffaea] font-medium uppercase">{activeVertical}</span> &bull; Silero VAD Barge-in active &bull; Sub-10ms Moss+Qdrant
            </p>
          </div>
        </div>

        {/* Action Controls in Tandem Design Language */}
        <div className="flex items-center space-x-2.5">
          {/* Mute/Unmute */}
          <button
            onClick={toggleMic}
            className={`px-3.5 py-2 rounded-lg border text-xs font-medium flex items-center space-x-1.5 transition-all ${
              isMuted
                ? "bg-amber-950/30 border-amber-500/40 text-amber-300"
                : "bg-white/[0.06] hover:bg-white/[0.1] border-white/[0.08] text-[#fffaea]"
            }`}
          >
            {isMuted ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4 text-[#62f6b5]" />}
            <span>{isMuted ? "Unmute" : "Mute"}</span>
          </button>

          {/* Instant Barge-In (Tandem Primary Action) */}
          <button
            onClick={triggerBargeIn}
            className="px-3.5 py-2 rounded-lg bg-[#efebdd] hover:bg-[#fffaea] text-black font-semibold text-xs flex items-center space-x-1.5 transition-all shadow-sm"
          >
            <Zap className="w-4 h-4 fill-black" />
            <span>Instant Barge-In</span>
          </button>

          {/* Disconnect */}
          <button
            onClick={onDisconnect}
            className="px-3.5 py-2 rounded-lg bg-red-950/40 hover:bg-red-900/50 border border-red-500/30 text-red-300 font-medium text-xs flex items-center space-x-1.5 transition-all"
          >
            <PhoneOff className="w-4 h-4" />
            <span>Hang Up</span>
          </button>
        </div>
      </div>
    </div>
  );
};
