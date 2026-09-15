"use client";

import React, { useState, useEffect } from "react";
import {
  LiveKitRoom,
  RoomAudioRenderer,
  useConnectionState,
  useLocalParticipant,
  useRoomContext,
} from "@livekit/components-react";
import { ConnectionState, RoomEvent } from "livekit-client";
import { Mic, MicOff, PhoneOff, Radio, Volume2, Zap, AudioLines, Shield } from "lucide-react";
import { TurnTelemetry } from "@/lib/types";
import { CharacterAvatar } from "./CharacterAvatar";
import { getAgentCharacter } from "@/lib/personas";

interface VoiceRoomProps {
  token: string | null;
  serverUrl: string;
  onDisconnect: () => void;
  onTelemetryReceived: (telemetry: TurnTelemetry) => void;
  onLiveSpeech?: (speech: string) => void;
  activeVertical: string;
}

export const VoiceRoom: React.FC<VoiceRoomProps> = ({
  token,
  serverUrl,
  onDisconnect,
  onTelemetryReceived,
  onLiveSpeech,
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
        onLiveSpeech={onLiveSpeech}
        activeVertical={activeVertical}
      />
      <RoomAudioRenderer />
    </LiveKitRoom>
  );
};

const VoiceRoomInner: React.FC<{
  onDisconnect: () => void;
  onTelemetryReceived: (telemetry: TurnTelemetry) => void;
  onLiveSpeech?: (speech: string) => void;
  activeVertical: string;
}> = ({ onDisconnect, onTelemetryReceived, onLiveSpeech, activeVertical }) => {
  const room = useRoomContext();
  const connectionState = useConnectionState();
  const { localParticipant, isMicrophoneEnabled } = useLocalParticipant();
  const [liveSpeech, setLiveSpeech] = useState<string>("");

  // Ensure microphone is enabled upon WebRTC connection
  useEffect(() => {
    if (connectionState === ConnectionState.Connected && localParticipant && !isMicrophoneEnabled) {
      localParticipant.setMicrophoneEnabled(true).catch((err) => {
        console.warn("Failed to auto-enable microphone on connect:", err);
      });
    }
  }, [connectionState, localParticipant, isMicrophoneEnabled]);

  // Listen to WebRTC Data Channel packets broadcasted by Tandem Voice Agent
  useEffect(() => {
    if (!room) return;

    const handleDataReceived = (payload: Uint8Array) => {
      try {
        const text = new TextDecoder().decode(payload);
        const data = JSON.parse(text);
        if (data.type === "telemetry" && data.payload) {
          onTelemetryReceived(data.payload as TurnTelemetry);
          setLiveSpeech("");
          if (onLiveSpeech) onLiveSpeech("");
        } else if (data.type === "live_user_speech" && data.payload) {
          const spokenText = data.payload.text || "";
          setLiveSpeech(spokenText);
          if (onLiveSpeech) onLiveSpeech(spokenText);
          if (data.payload.is_final) {
            setTimeout(() => {
              setLiveSpeech((prev) => (prev === spokenText ? "" : prev));
              if (onLiveSpeech) onLiveSpeech("");
            }, 3000);
          }
        }
      } catch (err) {
        console.debug("Failed to decode data message:", err);
      }
    };

    room.on(RoomEvent.DataReceived, handleDataReceived);
    return () => {
      room.off(RoomEvent.DataReceived, handleDataReceived);
    };
  }, [room, onTelemetryReceived, onLiveSpeech]);

  // Toggle Microphone
  const toggleMic = async () => {
    if (localParticipant) {
      await localParticipant.setMicrophoneEnabled(!isMicrophoneEnabled);
    }
  };

  // Instant Barge-In Interruption
  const triggerBargeIn = async () => {
    if (localParticipant) {
      await localParticipant.setMicrophoneEnabled(true);
      const payload = JSON.stringify({ type: "barge_in", reason: "user_interrupted" });
      await localParticipant.publishData(new TextEncoder().encode(payload), { reliable: true });
    }
  };

  const isSpeaking = localParticipant?.isSpeaking || false;

  const character = getAgentCharacter(activeVertical);

  return (
    <div className="bg-[#111013] border border-white/[0.08] rounded-xl p-5 shadow-2xl relative overflow-hidden">
      {/* Visual Ambient Persona Glow */}
      <div
        className="absolute top-0 right-1/4 w-56 h-56 rounded-full blur-3xl pointer-events-none opacity-20"
        style={{ backgroundColor: character.accentColor }}
      />

      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
        {/* Character Card & Status info */}
        <div className="flex items-center space-x-4">
          <CharacterAvatar
            verticalId={activeVertical}
            size="lg"
            isSpeaking={isSpeaking || connectionState === ConnectionState.Connected}
            showBadge={true}
          />

          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-base font-bold text-[#fffaea] flex items-center gap-2">
                <span>{character.characterName}</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded font-semibold border border-white/10"
                  style={{
                    backgroundColor: `${character.accentColor}18`,
                    color: character.accentColor,
                  }}
                >
                  {character.callsign}
                </span>
              </h3>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#1f1f23] border border-white/[0.08] text-[#9acdbf]">
                {connectionState === ConnectionState.Connected
                  ? isSpeaking
                    ? "Audio Active"
                    : "Listening"
                  : "Connecting"}
              </span>
            </div>

            <p className="text-xs text-[#a1a1aa] mt-0.5">
              <span className="text-white font-medium">{character.roleTitle}</span>
              <span className="mx-1.5">&bull;</span>
              <span className={isMicrophoneEnabled ? "text-[#62f6b5]" : "text-amber-400"}>
                {isMicrophoneEnabled ? "Microphone Live" : "Mic Muted"}
              </span>
            </p>

            <p className="text-[11px] text-[#71717a] italic mt-1 line-clamp-1">
              {character.quote}
            </p>
          </div>
        </div>

        {/* Action Controls in Tandem Design Language */}
        <div className="flex items-center space-x-2.5">
          {/* Mute/Unmute */}
          <button
            onClick={toggleMic}
            className={`px-3.5 py-2 rounded-lg border text-xs font-medium flex items-center space-x-1.5 transition-all ${
              !isMicrophoneEnabled
                ? "bg-amber-950/30 border-amber-500/40 text-amber-300"
                : "bg-white/[0.06] hover:bg-white/[0.1] border-white/[0.08] text-[#fffaea]"
            }`}
          >
            {!isMicrophoneEnabled ? <MicOff className="w-4 h-4 text-amber-400" /> : <Mic className="w-4 h-4 text-[#62f6b5]" />}
            <span>{!isMicrophoneEnabled ? "Unmute Mic" : "Mute Mic"}</span>
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

      {/* Real-time Subtitle / Teleprompter Bar (Approach 1: Server-Side STT Data Channel) */}
      <div className="mt-4 pt-3.5 border-t border-white/[0.06] flex items-center gap-3">
        <div className="flex items-center gap-2 flex-shrink-0">
          <span className="relative flex h-2 w-2">
            <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${
              liveSpeech ? "bg-[#62f6b5] opacity-75" : "bg-zinc-600"
            }`} />
            <span className={`relative inline-flex rounded-full h-2 w-2 ${
              liveSpeech ? "bg-[#62f6b5]" : "bg-zinc-600"
            }`} />
          </span>
          <span className="text-[10px] font-mono font-semibold uppercase tracking-wider text-[#9acdbf]">
            Live Speech
          </span>
        </div>

        <div className="flex-1 text-xs font-mono min-h-[22px] flex items-center overflow-hidden">
          {liveSpeech ? (
            <p className="text-[#fffaea] font-medium truncate">
              &ldquo;{liveSpeech}&rdquo;
              <span className="inline-block w-1.5 h-3.5 ml-1 bg-[#62f6b5] animate-pulse align-middle" />
            </p>
          ) : (
            <p className="text-[#71717a] italic text-[11px] truncate">
              {connectionState === ConnectionState.Connected
                ? isSpeaking
                  ? "Detecting speech & transcribing..."
                  : "Listening... Speak into your microphone to view live words"
                : "Connecting..."}
            </p>
          )}
        </div>
      </div>
    </div>
  );
};
