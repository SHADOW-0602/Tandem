import React, { useState } from "react";
import { TurnTelemetry } from "@/lib/types";
import { MessageSquare, Bot, User, FileText, ShieldAlert, Sparkles, ChevronDown, ChevronUp, Play, Loader2 } from "lucide-react";
import { CharacterAvatar } from "./CharacterAvatar";
import { getAgentCharacter } from "@/lib/personas";

interface TranscriptViewerProps {
  turns: TurnTelemetry[];
  liveSpeech?: string;
  isCallActive?: boolean;
  activeVerticalId?: string;
  onSimulateSample?: () => void;
  isSimulating?: boolean;
}

export const TranscriptViewer: React.FC<TranscriptViewerProps> = ({
  turns,
  liveSpeech,
  isCallActive = false,
  activeVerticalId = "dispatch",
  onSimulateSample,
  isSimulating = false,
}) => {
  const [expandedDoc, setExpandedDoc] = useState<string | null>(null);
  const character = getAgentCharacter(activeVerticalId);

  return (
    <div className="bg-[#111013] border border-white/[0.08] rounded-xl p-5 shadow-lg flex flex-col h-[520px]">
      <div className="flex items-center justify-between pb-3 border-b border-white/[0.06] mb-3">
        <div className="flex items-center space-x-2">
          <div className="w-5 h-5 rounded bg-white/[0.04] flex items-center justify-center">
            <MessageSquare className="w-3 h-3 text-[#fffaea]" />
          </div>
          <h3 className="text-xs font-semibold text-[#fffaea] uppercase tracking-eyebrow">
            Live Conversation
          </h3>
        </div>

        <div className="flex items-center space-x-2">
          {onSimulateSample && (
            <button
              onClick={onSimulateSample}
              disabled={isSimulating}
              className="px-2.5 py-1 rounded-lg bg-white/[0.06] hover:bg-white/[0.1] border border-white/10 text-[10px] font-mono text-[#62f6b5] flex items-center space-x-1.5 transition-all disabled:opacity-50 cursor-pointer shadow-sm hover:border-[#62f6b5]/40"
              title="Ask a sample question"
            >
              {isSimulating ? (
                <Loader2 className="w-3 h-3 animate-spin text-[#62f6b5]" />
              ) : (
                <Play className="w-2.5 h-2.5 fill-[#62f6b5] text-[#62f6b5]" />
              )}
              <span>{isSimulating ? "Asking..." : "Ask Question"}</span>
            </button>
          )}
          <span className="text-[10px] text-[#71717a] font-mono">
            {turns.length} message{turns.length === 1 ? "" : "s"}
          </span>
        </div>
      </div>

      {/* Turns scrollable list */}
      <div className="flex-1 overflow-y-auto space-y-3.5 pr-1">
        {/* Live speech interim stream bubble (while user speaks) */}
        {liveSpeech && (
          <div className="flex items-start space-x-2.5 p-3 rounded-xl bg-[#0e0e13] border border-[#62f6b5]/40 shadow-md animate-pulse">
            <div className="w-6 h-6 rounded bg-[#62f6b5]/10 border border-[#62f6b5]/30 text-[#62f6b5] flex items-center justify-center flex-shrink-0 mt-0.5">
              <User className="w-3 h-3" />
            </div>
            <div className="flex-1 text-xs">
              <div className="flex items-center justify-between mb-1">
                <span className="font-semibold text-[#62f6b5] text-[10px] tracking-wider uppercase flex items-center gap-1.5">
                  <span>Caller Speaking...</span>
                  <span className="w-1.5 h-1.5 rounded-full bg-[#62f6b5] animate-ping" />
                </span>
              </div>
              <p className="text-white font-medium italic leading-relaxed">
                &ldquo;{liveSpeech}&rdquo;
              </p>
            </div>
          </div>
        )}

        {turns.length === 0 && !liveSpeech ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 text-[#71717a]">
            <Bot className="w-8 h-8 mb-2 stroke-1 text-[#56565a]" />
            <p className="text-xs font-medium text-[#a1a1aa]">No messages yet</p>
            <p className="text-[11px] text-[#71717a] max-w-xs mt-1 mb-4">
              {isCallActive
                ? "Listening... Speak into your microphone to talk."
                : "Start a call on the left, or click below to ask a question."}
            </p>

            {onSimulateSample && (
              <button
                onClick={onSimulateSample}
                disabled={isSimulating}
                className="px-4 py-2.5 rounded-xl bg-white/[0.06] hover:bg-white/[0.1] border border-[#62f6b5]/30 text-[#62f6b5] font-mono text-xs flex items-center space-x-2 transition-all shadow-md disabled:opacity-50 cursor-pointer hover:border-[#62f6b5]/60"
              >
                {isSimulating ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Sparkles className="w-3.5 h-3.5 text-[#62f6b5]" />
                )}
                <span>{isSimulating ? "Asking..." : "Ask a Question"}</span>
              </button>
            )}
          </div>
        ) : (
          turns.map((turn, idx) => {
            const character = getAgentCharacter(turn.vertical);

            return (
              <div key={idx} className="space-y-2">
                {/* User Turn */}
                <div className="flex items-start space-x-2.5">
                  <div className="w-6 h-6 rounded bg-[#1f1f23] border border-white/[0.08] text-[#a1a1aa] flex items-center justify-center flex-shrink-0 mt-0.5">
                    <User className="w-3 h-3" />
                  </div>
                  <div className="flex-1 bg-[#0e0e13] border border-white/[0.06] rounded-lg p-2.5 text-xs">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium text-[#9acdbf] text-[10px] tracking-wider flex items-center gap-1.5">
                        <span>Caller to</span>
                        <strong className="text-white font-semibold">{character.characterName}</strong>
                        <span className="text-[9px] font-mono px-1 rounded border border-white/10"
                          style={{
                            backgroundColor: `${character.accentColor}18`,
                            color: character.accentColor,
                          }}
                        >
                          {character.callsign}
                        </span>
                      </span>
                      <span className="text-[10px] text-[#71717a] font-mono">
                        STT: {turn.stt_latency_ms.toFixed(0)}ms
                      </span>
                    </div>
                    <p className="text-[#fffaea] leading-relaxed">{turn.user_transcript}</p>
                  </div>
                </div>

                {/* Guardrail Alert (if any) */}
                {turn.guardrail_action && (
                  <div className="ml-8 p-2 rounded-lg bg-red-950/40 border border-red-500/30 flex items-center space-x-2 text-xs text-red-300">
                    <ShieldAlert className="w-3.5 h-3.5 text-red-400 flex-shrink-0" />
                    <span className="text-[11px]">
                      Guardrail Triggered: <span className="font-mono text-white">{turn.guardrail_action}</span> (Immediate Safety Bypass)
                    </span>
                  </div>
                )}

                {/* Retrieved Context Pills */}
                {turn.retrieved_doc_ids && turn.retrieved_doc_ids.length > 0 && (
                  <div className="ml-8">
                    <div className="flex items-center flex-wrap gap-1.5 mb-1">
                      <span className="text-[10px] font-mono text-[#62f6b5] flex items-center gap-1">
                        <Sparkles className="w-2.5 h-2.5" /> Retrieved in {turn.moss_latency_ms.toFixed(1)}ms:
                      </span>
                      {turn.retrieved_doc_ids.map((docId, dIdx) => (
                        <button
                          key={dIdx}
                          onClick={() => setExpandedDoc(expandedDoc === docId ? null : docId)}
                          className="text-[9px] font-mono px-2 py-0.5 rounded bg-[#0d241e] border border-[#62f6b5]/30 text-[#62f6b5] hover:bg-[#1f4038] flex items-center gap-1 transition-colors"
                        >
                          <FileText className="w-2.5 h-2.5" />
                          <span>{docId}</span>
                          {expandedDoc === docId ? <ChevronUp className="w-2 h-2" /> : <ChevronDown className="w-2 h-2" />}
                        </button>
                      ))}
                    </div>

                    {/* Expanded Snippet */}
                    {expandedDoc && turn.retrieved_doc_ids.includes(expandedDoc) && (
                      <div className="p-2.5 rounded-md bg-[#0e0e13] border border-[#62f6b5]/30 text-[11px] text-[#9acdbf] font-mono mb-2">
                        <p className="font-semibold text-[#62f6b5] mb-0.5 text-[10px]">Context Injected:</p>
                        <p className="whitespace-pre-wrap text-[11px] text-[#fffaea]/90">
                          {turn.retrieved_snippets[0] || "Prewarmed SOP Procedure."}
                        </p>
                      </div>
                    )}
                  </div>
                )}

                {/* Agent Voice Reply */}
                <div className="flex items-start space-x-2.5">
                  <CharacterAvatar verticalId={turn.vertical} size="sm" />
                  <div className="flex-1 bg-[#1f1f23] border border-white/[0.08] rounded-lg p-2.5 text-xs">
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center space-x-2">
                        <span className="font-bold text-[#fffaea] text-[11px]">
                          {character.characterName}
                        </span>
                        <span
                          className="text-[9px] font-mono px-1.5 py-0.2 rounded font-semibold border border-white/10"
                          style={{
                            backgroundColor: `${character.accentColor}18`,
                            color: character.accentColor,
                          }}
                        >
                          {character.callsign}
                        </span>
                        <span className="text-[10px] text-[#a1a1aa] hidden sm:inline">
                          &bull; {character.roleTitle}
                        </span>
                      </div>
                      <span className="text-[10px] text-[#a1a1aa] font-mono">
                        TTFT: {turn.llm_ttft_ms.toFixed(0)}ms &bull; Total: {turn.total_latency_ms.toFixed(0)}ms
                      </span>
                    </div>
                    <p className="text-[#fffaea] leading-relaxed">{turn.agent_response}</p>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
