"use client";

import React, { useState } from "react";
import {
  Copy,
  Check,
  HelpCircle,
  ArrowRight,
} from "lucide-react";
import { AGENT_CHARACTERS } from "@/lib/personas";
import { CALLER_QUESTIONS, CallerQuestion } from "@/lib/simulationQuestions";

interface AgentQuestionsGuideProps {
  activeVerticalId: string;
  onSelectVertical: (verticalId: string) => void;
  onTestPrompt?: (verticalId: string, prompt: string) => void;
}

export const AgentQuestionsGuide: React.FC<AgentQuestionsGuideProps> = ({
  activeVerticalId,
  onSelectVertical,
}) => {
  const [selectedVerticalId, setSelectedVerticalId] = useState<string>(activeVerticalId);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  React.useEffect(() => {
    setSelectedVerticalId(activeVerticalId);
  }, [activeVerticalId]);

  const character = AGENT_CHARACTERS[selectedVerticalId] || AGENT_CHARACTERS.dispatch;
  const questions: CallerQuestion[] = CALLER_QUESTIONS[selectedVerticalId] || CALLER_QUESTIONS.dispatch;

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <section id="questions-guide" className="scroll-mt-20 py-16 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full border-t border-white/[0.08]">
      {/* Header */}
      <div className="text-center max-w-3xl mx-auto mb-10 space-y-3">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#62f6b5]/10 border border-[#62f6b5]/30 text-[#62f6b5] text-xs font-mono font-semibold">
          <HelpCircle className="w-3.5 h-3.5" />
          <span>QUESTIONS RUNBOOK</span>
        </div>
        <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
          Questions to Ask Every Agent
        </h2>
        <p className="text-xs sm:text-sm text-[#a1a1aa] leading-relaxed">
          Select an agent below to browse curated operational questions. Click any question to copy it or test it directly in the live voice terminal.
        </p>
      </div>

      {/* Agent Switcher Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-3 mb-8 no-scrollbar">
        {Object.entries(AGENT_CHARACTERS).map(([vId, char]) => {
          const isSelected = selectedVerticalId === vId;
          return (
            <button
              key={vId}
              onClick={() => setSelectedVerticalId(vId)}
              className={`flex items-center gap-2 px-3.5 py-2.5 rounded-xl border text-xs font-semibold whitespace-nowrap transition-all ${
                isSelected
                  ? "bg-white/[0.08] border-white/40 text-white shadow-md"
                  : "bg-[#111013]/70 border-white/[0.06] text-[#a1a1aa] hover:text-white hover:border-white/20"
              }`}
            >
              <div
                className="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold text-white shadow-sm"
                style={{ backgroundColor: char.accentColor }}
              >
                {char.avatarInitial}
              </div>
              <span>{char.characterName}</span>
              <span className="text-[10px] font-mono text-[#71717a] hidden sm:inline">
                ({char.callsign})
              </span>
            </button>
          );
        })}
      </div>

      {/* Active Agent Highlight Banner */}
      <div className="p-4 rounded-2xl bg-[#111013] border border-white/[0.08] mb-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div
            className="w-11 h-11 rounded-xl flex items-center justify-center text-sm font-bold text-white shadow-md border border-white/10"
            style={{ backgroundColor: character.accentColor }}
          >
            {character.avatarInitial}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-white">{character.characterName}</h3>
              <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-white/[0.06] text-[#a1a1aa] border border-white/[0.08]">
                {character.callsign}
              </span>
              <span className="text-[10px] text-[#71717a] hidden md:inline">
                &bull; {character.department}
              </span>
            </div>
            <p className="text-xs text-[#a1a1aa] mt-0.5">{character.tagline}</p>
          </div>
        </div>

        {selectedVerticalId !== activeVerticalId ? (
          <button
            onClick={() => onSelectVertical(selectedVerticalId)}
            className="px-3 py-1.5 rounded-lg bg-[#62f6b5]/10 border border-[#62f6b5]/30 text-[#62f6b5] text-xs font-semibold hover:bg-[#62f6b5]/20 transition-all flex items-center gap-1.5"
          >
            <span>Activate Operator</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        ) : (
          <div className="flex items-center gap-2 px-3 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-mono">
            <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>Active in Voice Terminal</span>
          </div>
        )}
      </div>

      {/* Questions Grid for Selected Agent */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {questions.map((q, index) => (
          <div
            key={q.id || index}
            className="p-4 rounded-xl bg-[#111013] border border-white/[0.08] hover:border-white/20 transition-all flex flex-col justify-between space-y-3 shadow-sm group"
          >
            {/* Card Header: Category & Copy Button */}
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-md border text-[11px] font-bold bg-white/[0.04] text-[#a1a1aa] border-white/[0.08]">
                  {q.category}
                </span>
                {q.shortTitle && (
                  <span className="text-xs text-[#71717a] font-medium hidden sm:inline">
                    &bull; {q.shortTitle}
                  </span>
                )}
              </div>

              <button
                onClick={() => handleCopy(q.id || String(index), q.prompt)}
                title="Copy question text"
                className="p-1.5 rounded-lg text-[#71717a] hover:text-white hover:bg-white/[0.06] transition-colors"
              >
                {copiedId === (q.id || String(index)) ? (
                  <Check className="w-3.5 h-3.5 text-emerald-400" />
                ) : (
                  <Copy className="w-3.5 h-3.5" />
                )}
              </button>
            </div>

            {/* Question Text */}
            <div className="p-3.5 rounded-xl bg-black/40 border border-white/[0.04]">
              <p className="text-xs sm:text-sm text-[#fffaea] font-medium leading-relaxed">
                &ldquo;{q.prompt}&rdquo;
              </p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};
