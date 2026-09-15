"use client";

import React, { useState, useEffect } from "react";
import { Vertical, TurnTelemetry } from "@/lib/types";
import { simulateTurn, fetchScenarios, fetchPersonalities, runAITesterSimulation } from "@/lib/api";
import { getCallerQuestions } from "@/lib/simulationQuestions";
import { Play, Sparkles, Send, Loader2, Bot, User, CheckCircle2, XCircle, ChevronRight, SlidersHorizontal } from "lucide-react";

interface SimulationBenchProps {
  vertical: Vertical | null;
  onSimulationComplete: (telemetry: TurnTelemetry) => void;
}

export const SimulationBench: React.FC<SimulationBenchProps> = ({
  vertical,
  onSimulationComplete,
}) => {
  const [mode, setMode] = useState<"quick" | "ai_tester">("quick");

  // --- Quick Turn Simulation State ---
  const [inputText, setInputText] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSimulate = async (promptText: string) => {
    if (!vertical || !promptText.trim() || loading) return;
    setLoading(true);
    try {
      const telemetry = await simulateTurn(vertical.id, promptText.trim());
      onSimulationComplete(telemetry);
    } catch (err) {
      console.error("Simulation error:", err);
    } finally {
      setLoading(false);
    }
  };

  const [runningEvals, setRunningEvals] = useState(false);
  const [evalResult, setEvalResult] = useState<{ passed: number; total: number; pass_rate: number } | null>(null);

  const handleRunEvals = async () => {
    setRunningEvals(true);
    try {
      const { runEvals } = await import("@/lib/api");
      const res = await runEvals();
      setEvalResult({ passed: res.passed, total: res.total_cases, pass_rate: res.pass_rate_pct });
      if (res.results && res.results.length > 0) {
        onSimulationComplete(res.results[0]);
      }
    } catch (err) {
      console.error("Evals error:", err);
    } finally {
      setRunningEvals(false);
    }
  };

  // --- AI Tester Simulation State ---
  const [scenarios, setScenarios] = useState<any[]>([]);
  const [personalities, setPersonalities] = useState<any[]>([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>("");
  const [selectedPersonalityId, setSelectedPersonalityId] = useState<string>("impatient_concise");
  const [runningAiTester, setRunningAiTester] = useState(false);
  const [simulationRunResult, setSimulationRunResult] = useState<any | null>(null);

  useEffect(() => {
    async function loadPresets() {
      const scList = await fetchScenarios(vertical?.id);
      const pList = await fetchPersonalities();
      setScenarios(scList);
      setPersonalities(pList);
      if (scList.length > 0) {
        setSelectedScenarioId(scList[0].id);
      }
    }
    loadPresets();
  }, [vertical?.id]);

  const handleRunAiTester = async () => {
    if (!selectedScenarioId || runningAiTester) return;
    setRunningAiTester(true);
    setSimulationRunResult(null);
    try {
      const result = await runAITesterSimulation({
        scenario_id: selectedScenarioId,
        personality_id: selectedPersonalityId,
      });
      setSimulationRunResult(result);
      // Update telemetry dashboard using last turn of simulation
      if (result.turns && result.turns.length > 0) {
        const lastTurn = result.turns[result.turns.length - 1];
        onSimulationComplete({
          call_id: result.run_id,
          turn_id: lastTurn.turn_id,
          vertical: result.vertical,
          user_transcript: lastTurn.tester_utterance,
          agent_response: lastTurn.agent_response,
          moss_latency_ms: lastTurn.moss_latency_ms,
          llm_ttft_ms: lastTurn.llm_ttft_ms,
          total_latency_ms: lastTurn.total_latency_ms,
          stt_latency_ms: 240.0,
          tts_ttfb_ms: 145.0,
          is_sub_10ms_moss: lastTurn.moss_latency_ms < 10.0,
          within_budget: lastTurn.total_latency_ms <= 590.0,
          guardrail_action: lastTurn.guardrail_action,
          retrieved_doc_ids: lastTurn.retrieved_docs || [],
          retrieved_snippets: [],
          timestamp: lastTurn.timestamp,
        });
      }
    } catch (err) {
      console.error("AI tester simulation error:", err);
    } finally {
      setRunningAiTester(false);
    }
  };

  const selectedScenario = scenarios.find((s) => s.id === selectedScenarioId);
  const selectedPersonality = personalities.find((p) => p.id === selectedPersonalityId);

  return (
    <div className="bg-dark-card border border-dark-border rounded-2xl p-4 shadow-xl">
      {/* Header & Mode Switch */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3 border-b border-dark-border pb-3">
        <div className="flex items-center space-x-2">
          <Sparkles className="w-4 h-4 text-dark-mint" />
          <h4 className="text-xs font-mono font-semibold text-dark-cream uppercase tracking-wider">
            Simulation & AI Tester Bench
          </h4>
        </div>
        <div className="flex items-center space-x-2">
          {/* Mode Tabs */}
          <div className="flex items-center bg-dark-bg border border-dark-border rounded-lg p-0.5 text-xs">
            <button
              onClick={() => setMode("quick")}
              className={`px-2.5 py-1 rounded-md transition-all font-medium ${
                mode === "quick"
                  ? "bg-dark-card border border-dark-border text-dark-mint shadow-sm"
                  : "text-dark-muted hover:text-dark-cream"
              }`}
            >
              Quick Turn
            </button>
            <button
              onClick={() => setMode("ai_tester")}
              className={`px-2.5 py-1 rounded-md transition-all font-medium flex items-center space-x-1 ${
                mode === "ai_tester"
                  ? "bg-dark-mint/10 text-dark-mint border border-dark-mint/40 shadow-sm"
                  : "text-dark-muted hover:text-dark-cream"
              }`}
            >
              <Bot className="w-3 h-3 text-dark-mint" />
              <span>AI Tester Multi-Turn</span>
            </button>
          </div>

          {mode === "quick" && (
            <>
              {evalResult && (
                <span className="text-[11px] font-mono text-dark-mint bg-dark-mint/10 border border-dark-mint/30 px-2 py-0.5 rounded">
                  Evals: {evalResult.passed}/{evalResult.total} ({evalResult.pass_rate}%)
                </span>
              )}
              <button
                onClick={handleRunEvals}
                disabled={runningEvals}
                className="px-2.5 py-1 rounded-lg bg-dark-mint/15 hover:bg-dark-mint/25 text-dark-mint border border-dark-mint/40 text-[11px] font-medium flex items-center space-x-1 transition-all disabled:opacity-50"
              >
                {runningEvals ? <Loader2 className="w-3 h-3 animate-spin" /> : <Play className="w-3 h-3" />}
                <span>{runningEvals ? "Benchmarking..." : "Run Evals"}</span>
              </button>
            </>
          )}
        </div>
      </div>

      {/* QUICK TURN MODE */}
      {mode === "quick" && (
        <div>
          {/* Suggested Quick-Test Prompts */}
          {(() => {
            const prompts =
              vertical?.sample_prompts && vertical.sample_prompts.length > 0
                ? vertical.sample_prompts
                : getCallerQuestions(vertical?.id || "dispatch").map((q) => q.prompt);

            return (
              <div className="flex flex-wrap gap-2 mb-3">
                {prompts.map((prompt, idx) => (
                  <button
                    key={idx}
                    disabled={loading}
                    onClick={() => {
                      setInputText(prompt);
                      handleSimulate(prompt);
                    }}
                    className="px-3 py-1.5 rounded-lg bg-dark-bg/80 border border-dark-border hover:border-dark-mint/50 hover:bg-dark-card text-dark-cream/80 text-xs text-left transition-all flex items-center space-x-1.5 shadow-sm disabled:opacity-50"
                  >
                    <Play className="w-3 h-3 text-dark-mint flex-shrink-0" />
                    <span className="line-clamp-1">{prompt}</span>
                  </button>
                ))}
              </div>
            );
          })()}

          {/* Custom Utterance Input Bar */}
          <div className="flex items-center space-x-2">
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSimulate(inputText)}
              placeholder={`Test an utterance for ${vertical?.name || "active vertical"}...`}
              disabled={loading}
              className="flex-1 bg-dark-bg border border-dark-border focus:border-dark-mint/60 rounded-xl px-4 py-2.5 text-xs text-dark-cream placeholder-dark-muted focus:outline-none focus:ring-1 focus:ring-dark-mint/60 transition-all font-sans"
            />
            <button
              onClick={() => handleSimulate(inputText)}
              disabled={loading || !inputText.trim()}
              className="px-4 py-2.5 rounded-xl bg-dark-mint hover:bg-dark-mint-accent disabled:opacity-50 text-[#0e0e13] font-semibold text-xs flex items-center space-x-1.5 transition-all shadow-md shadow-dark-mint/20"
            >
              {loading ? (
                <Loader2 className="w-4 h-4 animate-spin text-[#0e0e13]" />
              ) : (
                <Send className="w-4 h-4 text-[#0e0e13]" />
              )}
              <span>{loading ? "Running..." : "Test Turn"}</span>
            </button>
          </div>
        </div>
      )}

      {/* AI TESTER MULTI-TURN MODE */}
      {mode === "ai_tester" && (
        <div className="space-y-3">
          {/* Controls: Select Scenario & Personality */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {/* Scenario Picker */}
            <div className="bg-dark-bg/60 p-2.5 rounded-xl border border-dark-border">
              <label className="text-[10px] uppercase font-mono font-semibold text-dark-muted mb-1 block">
                1. Test Scenario (Goal & Stopping Condition)
              </label>
              <select
                value={selectedScenarioId}
                onChange={(e) => setSelectedScenarioId(e.target.value)}
                disabled={runningAiTester}
                className="w-full bg-dark-card border border-dark-border text-dark-cream rounded-lg px-2.5 py-1.5 text-xs focus:outline-none focus:border-dark-mint/60"
              >
                {scenarios.map((sc) => (
                  <option key={sc.id} value={sc.id}>
                    {sc.name} {sc.is_builtin ? "(Built-in)" : "(Custom)"}
                  </option>
                ))}
              </select>
              {selectedScenario && (
                <p className="text-[11px] text-dark-muted mt-1.5 line-clamp-2 italic">
                  {selectedScenario.instructions}
                </p>
              )}
            </div>

            {/* Personality Picker */}
            <div className="bg-dark-bg/60 p-2.5 rounded-xl border border-dark-border">
              <label className="text-[10px] uppercase font-mono font-semibold text-dark-muted mb-1 block">
                2. AI Tester Personality (Tone & Timing)
              </label>
              <select
                value={selectedPersonalityId}
                onChange={(e) => setSelectedPersonalityId(e.target.value)}
                disabled={runningAiTester}
                className="w-full bg-dark-card border border-dark-border text-dark-cream rounded-lg px-2.5 py-1.5 text-xs focus:outline-none focus:border-dark-mint/60"
              >
                {personalities.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} {p.is_builtin ? "(Built-in)" : "(Custom)"}
                  </option>
                ))}
              </select>
              {selectedPersonality && (
                <div className="flex items-center space-x-2 text-[10px] text-dark-muted mt-1.5 font-mono">
                  <span>Model: {selectedPersonality.assistant?.model?.model || "gemini-2.0-flash"}</span>
                  <span>•</span>
                  <span>Turns: up to {selectedPersonality.assistant?.maxTurns || 6}</span>
                </div>
              )}
            </div>
          </div>

          {/* Action Button */}
          <div className="flex items-center justify-between">
            <div className="text-[11px] text-dark-muted flex items-center space-x-1">
              <SlidersHorizontal className="w-3.5 h-3.5 text-dark-mint" />
              <span>
                Simulates natural caller turns using Gemini against Tandem’s sub-10ms pipeline
              </span>
            </div>
            <button
              onClick={handleRunAiTester}
              disabled={runningAiTester || !selectedScenarioId}
              className="px-4 py-2 rounded-xl bg-dark-mint hover:bg-dark-mint-accent text-[#0e0e13] font-semibold text-xs flex items-center space-x-1.5 transition-all shadow-md shadow-dark-mint/20 disabled:opacity-50"
            >
              {runningAiTester ? (
                <Loader2 className="w-4 h-4 animate-spin text-[#0e0e13]" />
              ) : (
                <Play className="w-4 h-4 text-[#0e0e13]" />
              )}
              <span>{runningAiTester ? "Simulating Multi-Turn Dialog..." : "Run AI Tester Simulation"}</span>
            </button>
          </div>

          {/* Simulation Results Display */}
          {simulationRunResult && (
            <div className="mt-3 p-3 bg-dark-bg/90 border border-dark-border rounded-xl space-y-2.5">
              {/* Scorecard Header */}
              <div className="flex items-center justify-between pb-2 border-b border-dark-border">
                <div className="flex items-center space-x-2">
                  {simulationRunResult.passed ? (
                    <CheckCircle2 className="w-4 h-4 text-dark-mint" />
                  ) : (
                    <XCircle className="w-4 h-4 text-red-400" />
                  )}
                  <span className="text-xs font-semibold text-dark-cream">
                    {simulationRunResult.scenario_name}
                  </span>
                  <span
                    className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${
                      simulationRunResult.passed
                        ? "bg-dark-mint/10 border-dark-mint/50 text-dark-mint"
                        : "bg-red-950/80 border-red-500/50 text-red-300"
                    }`}
                  >
                    {simulationRunResult.passed ? "PASSED" : "FAILED"} (
                    {simulationRunResult.evaluation_score}%)
                  </span>
                </div>
                <div className="text-[10px] text-dark-muted font-mono space-x-2">
                  <span>Turns: {simulationRunResult.total_turns}</span>
                  <span>•</span>
                  <span>Avg Latency: {simulationRunResult.avg_latency_ms}ms</span>
                </div>
              </div>

              {/* Multi-Turn Dialog Transcript */}
              <div className="max-h-48 overflow-y-auto space-y-2 pr-1 text-xs">
                {simulationRunResult.turns.map((turn: any) => (
                  <div key={turn.turn_id} className="space-y-1">
                    {/* Tester Utterance */}
                    <div className="flex items-start space-x-2 bg-dark-card p-2 rounded-lg border border-dark-border">
                      <User className="w-3.5 h-3.5 text-dark-mint mt-0.5 flex-shrink-0" />
                      <div className="flex-1">
                        <span className="text-[10px] font-mono font-semibold text-dark-mint uppercase">
                          AI Tester (Turn {turn.turn_id})
                        </span>
                        <p className="text-dark-cream mt-0.5">{turn.tester_utterance}</p>
                      </div>
                    </div>

                    {/* Agent Response */}
                    <div className="flex items-start space-x-2 bg-dark-mint/10 p-2 rounded-lg border border-dark-mint/30 ml-3">
                      <Bot className="w-3.5 h-3.5 text-dark-mint mt-0.5 flex-shrink-0" />
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] font-mono font-semibold text-dark-mint uppercase">
                            Tandem Agent
                          </span>
                          <span className="text-[10px] font-mono text-dark-muted">
                            Moss: {turn.moss_latency_ms}ms | Total: {turn.total_latency_ms}ms
                          </span>
                        </div>
                        <p className="text-dark-cream mt-0.5">{turn.agent_response}</p>
                        {turn.guardrail_action && (
                          <span className="inline-block mt-1 text-[9px] font-mono text-red-300 bg-red-950/80 border border-red-500/40 px-1.5 py-0.5 rounded">
                            Guardrail: {turn.guardrail_action}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Evaluation Checklist */}
              {simulationRunResult.evaluation_breakdown?.details && (
                <div className="pt-2 border-t border-dark-border flex flex-wrap gap-1.5">
                  {simulationRunResult.evaluation_breakdown.details.map((detail: string, i: number) => (
                    <span
                      key={i}
                      className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
                        detail.startsWith("PASS")
                          ? "bg-dark-mint/10 border-dark-mint/30 text-dark-mint"
                          : "bg-red-950/40 border-red-500/30 text-red-300"
                      }`}
                    >
                      {detail}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
