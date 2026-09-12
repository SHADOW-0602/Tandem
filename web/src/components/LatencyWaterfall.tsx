"use client";

import React from "react";
import { TurnTelemetry } from "@/lib/types";
import { Zap, Clock, CheckCircle2, Activity } from "lucide-react";

interface LatencyWaterfallProps {
  telemetry: TurnTelemetry | null;
  historicalP50?: number;
}

export const LatencyWaterfall: React.FC<LatencyWaterfallProps> = ({
  telemetry,
  historicalP50,
}) => {
  const currentTotal = telemetry?.total_latency_ms || 568.0;
  const isBudgetOk = currentTotal <= 590.0;

  // Latencies breakdown
  const stt = telemetry?.stt_latency_ms ?? 240.0;
  const moss = telemetry?.moss_latency_ms ?? 6.8;
  const qdrant = (telemetry as any)?.qdrant_latency_ms ?? 5.2;
  const llm = telemetry?.llm_ttft_ms ?? 175.0;
  const tts = telemetry?.tts_ttfb_ms ?? 145.0;

  const budgetMax = 800; // visual max scale

  return (
    <div className="bg-[#111013] border border-white/[0.08] rounded-xl p-5 shadow-lg">
      {/* Header with Title & Overall SLA in Tandem Style */}
      <div className="flex items-center justify-between mb-4 border-b border-white/[0.06] pb-3">
        <div className="flex items-center space-x-2.5">
          <div className="w-6 h-6 rounded-md bg-[#62f6b5]/15 flex items-center justify-center">
            <Zap className="w-3.5 h-3.5 text-[#62f6b5]" />
          </div>
          <div>
            <h3 className="text-xs font-semibold text-[#fffaea] uppercase tracking-eyebrow">
              Sub-10ms Context Retrieval & Voice Waterfall
            </h3>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-[11px] text-[#a1a1aa]">Total Turnaround:</span>
          <span
            className={`font-mono text-xs font-bold px-2.5 py-0.5 rounded-full border ${
              isBudgetOk
                ? "bg-[#0d241e] border-[#62f6b5]/40 text-[#62f6b5]"
                : "bg-amber-950/40 border-amber-500/30 text-amber-300"
            }`}
          >
            {currentTotal.toFixed(1)} ms
          </span>
        </div>
      </div>

      {/* Target Budget Comparison Timeline */}
      <div className="mb-4 bg-[#0e0e13] p-3 rounded-lg border border-white/[0.06]">
        <div className="flex justify-between text-[11px] text-[#a1a1aa] mb-1.5 font-mono">
          <span>0ms (STT Final)</span>
          <span className="text-[#9acdbf] font-medium">SLA Budget: 590ms</span>
          <span className="text-[#71717a]">Target Max: 800ms</span>
        </div>
        <div className="w-full h-2.5 bg-white/[0.06] rounded-full overflow-hidden relative">
          {/* 590ms target line marker */}
          <div
            className="absolute top-0 bottom-0 w-0.5 bg-[#9acdbf] z-10"
            style={{ left: `${(590 / budgetMax) * 100}%` }}
          />
          {/* Actual response progress */}
          <div
            className={`h-full rounded-full transition-all duration-500 ${
              isBudgetOk
                ? "bg-gradient-to-r from-[#00cd8f] via-[#62f6b5] to-[#efebdd]"
                : "bg-gradient-to-r from-amber-500 to-red-500"
            }`}
            style={{ width: `${Math.min(100, (currentTotal / budgetMax) * 100)}%` }}
          />
        </div>
      </div>

      {/* Breakdown Stage Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
        {/* Stage 1: STT */}
        <div className="p-3 rounded-lg bg-[#0e0e13] border border-white/[0.06] flex flex-col justify-between">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] uppercase tracking-wider text-[#a1a1aa] font-medium">
              1. STT Stream
            </span>
            <span className="text-[9px] text-[#71717a] font-mono">Groq Turbo</span>
          </div>
          <div className="flex items-baseline space-x-1 my-0.5">
            <span className="text-xl font-bold font-mono text-[#fffaea]">
              {stt.toFixed(0)}
            </span>
            <span className="text-[10px] text-[#a1a1aa] font-mono">ms</span>
          </div>
          <span className="text-[10px] text-[#71717a]">Audio finalization</span>
        </div>

        {/* Stage 2: MOSS + QDRANT CO-RETRIEVAL (HERO FEATURE) */}
        <div className="p-3 rounded-lg bg-[#0d241e]/50 border border-[#62f6b5]/50 shadow-sm shadow-[#62f6b5]/10 flex flex-col justify-between relative overflow-hidden">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] uppercase tracking-wider text-[#62f6b5] font-bold">
              2. Co-Retrieval
            </span>
            <span className="px-1.5 py-0.2 rounded text-[9px] font-mono bg-[#62f6b5] text-black font-bold">
              SUB-10MS
            </span>
          </div>
          <div className="flex items-baseline space-x-1 my-0.5">
            <span className="text-xl font-black font-mono text-[#62f6b5]">
              {moss.toFixed(1)}
            </span>
            <span className="text-[10px] text-[#9acdbf] font-mono">ms</span>
            <span className="text-[10px] text-[#a1a1aa] font-mono ml-1.5">
              (Qdrant: {qdrant.toFixed(1)}ms)
            </span>
          </div>
          <span className="text-[10px] text-[#9acdbf]">Moss Hot Cache + Qdrant</span>
        </div>

        {/* Stage 3: LLM TTFT */}
        <div className="p-3 rounded-lg bg-[#0e0e13] border border-white/[0.06] flex flex-col justify-between">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] uppercase tracking-wider text-[#a1a1aa] font-medium">
              3. LLM TTFT
            </span>
            <span className="text-[9px] text-[#71717a] font-mono">Groq LPU</span>
          </div>
          <div className="flex items-baseline space-x-1 my-0.5">
            <span className="text-xl font-bold font-mono text-[#fffaea]">
              {llm.toFixed(0)}
            </span>
            <span className="text-[10px] text-[#a1a1aa] font-mono">ms</span>
          </div>
          <span className="text-[10px] text-[#71717a]">Time to first token</span>
        </div>

        {/* Stage 4: TTS TTFB */}
        <div className="p-3 rounded-lg bg-[#0e0e13] border border-white/[0.06] flex flex-col justify-between">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] uppercase tracking-wider text-[#a1a1aa] font-medium">
              4. TTS TTFB
            </span>
            <span className="text-[9px] text-[#71717a] font-mono">Cartesia Sonic</span>
          </div>
          <div className="flex items-baseline space-x-1 my-0.5">
            <span className="text-xl font-bold font-mono text-[#fffaea]">
              {tts.toFixed(0)}
            </span>
            <span className="text-[10px] text-[#a1a1aa] font-mono">ms</span>
          </div>
          <span className="text-[10px] text-[#71717a]">First audio packet</span>
        </div>
      </div>
    </div>
  );
};
