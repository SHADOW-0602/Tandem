"use client";

import React, { useState, useEffect } from "react";
import { Header } from "@/components/Header";
import { VerticalSelector } from "@/components/VerticalSelector";
import { LatencyWaterfall } from "@/components/LatencyWaterfall";
import { VoiceRoom } from "@/components/VoiceRoom";
import { TranscriptViewer } from "@/components/TranscriptViewer";
import { Vertical, TurnTelemetry } from "@/lib/types";
import { fetchVerticals, mintLiveKitToken, simulateTurn } from "@/lib/api";
import { CharacterAvatar } from "@/components/CharacterAvatar";
import { AgentQuestionsGuide } from "@/components/AgentQuestionsGuide";
import { getAgentCharacter, AGENT_CHARACTERS } from "@/lib/personas";
import { getNextCallerQuestion, getCallerQuestions } from "@/lib/simulationQuestions";
import {
  PhoneCall,
  Zap,
  ShieldCheck,
  Activity,
  ArrowRight,
  Headphones,
  Sparkles,
  CheckCircle2,
  Layers,
  Volume2,
  Clock,
  Radio,
} from "lucide-react";

const DEFAULT_VERTICALS: Vertical[] = [
  { id: "dispatch", name: "911 & Tactical CAD", description: "Tactical CAD & Emergency Dispatch Lead", icon: "Radio", moss_index: "dispatch_emergency_ops", knowledge_file: "dispatch_sops.json", sample_prompts: [], latency_target_ms: 590 },
  { id: "healthcare", name: "Clinical Triage", description: "Chief Clinical Triage Specialist", icon: "Stethoscope", moss_index: "clinical_healthcare_triage", knowledge_file: "healthcare_triage.json", sample_prompts: [], latency_target_ms: 590 },
  { id: "field_worker", name: "Industrial Safety", description: "Lead Industrial Safety Foreman", icon: "HardHat", moss_index: "field_worker_safety", knowledge_file: "field_worker_safety.json", sample_prompts: [], latency_target_ms: 590 },
  { id: "customer_support", name: "Enterprise Support", description: "Executive SLA & Escalations Concierge", icon: "Headphones", moss_index: "customer_support_sla", knowledge_file: "customer_support_sla.json", sample_prompts: [], latency_target_ms: 590 },
  { id: "logistics_fleet", name: "Logistics & Fleet", description: "Global Logistics & Aviation Controller", icon: "Truck", moss_index: "logistics_fleet_ops", knowledge_file: "logistics_fleet.json", sample_prompts: [], latency_target_ms: 590 },
  { id: "financial_compliance", name: "Financial Compliance", description: "Principal Fraud & AML Special Agent", icon: "Shield", moss_index: "financial_compliance_aml", knowledge_file: "financial_compliance.json", sample_prompts: [], latency_target_ms: 590 },
];

export default function DashboardPage() {
  const [verticals, setVerticals] = useState<Vertical[]>(DEFAULT_VERTICALS);
  const [activeVerticalId, setActiveVerticalId] = useState<string>("dispatch");
  const [liveToken, setLiveToken] = useState<string | null>(null);
  const [liveKitUrl, setLiveKitUrl] = useState<string>("wss://parity-9hhf288x.livekit.cloud");
  const [isConnecting, setIsConnecting] = useState(false);
  const [currentTelemetry, setCurrentTelemetry] = useState<TurnTelemetry | null>(null);
  const [turnHistory, setTurnHistory] = useState<TurnTelemetry[]>([]);
  const [liveSpeech, setLiveSpeech] = useState<string>("");
  const [isSimulating, setIsSimulating] = useState<boolean>(false);
  const [simulatedQuestionIndices, setSimulatedQuestionIndices] = useState<Record<string, number>>({});

  // Load verticals on mount
  useEffect(() => {
    fetchVerticals().then((data) => {
      if (data && data.length > 0) {
        setVerticals(data);
      }
    });
  }, []);

  const activeVertical = verticals.find((v) => v.id === activeVerticalId);

  // Mint LiveKit token and connect to room
  const handleStartCall = async () => {
    if (isConnecting) return;
    setIsConnecting(true);
    try {
      const roomName = `room-${activeVerticalId}-${Date.now()}`;
      const data = await mintLiveKitToken(roomName, activeVerticalId);
      setLiveToken(data.token);
      if (data.url) setLiveKitUrl(data.url);
    } catch (err) {
      console.error("Failed to start voice call:", err);
    } finally {
      setIsConnecting(false);
    }
  };

  // Disconnect from voice room
  const handleEndCall = () => {
    setLiveToken(null);
    setLiveSpeech("");
  };

  // Handle telemetry turn from voice agent
  const handleNewTelemetry = (telemetry: TurnTelemetry) => {
    setCurrentTelemetry(telemetry);
    setTurnHistory((prev) => [telemetry, ...prev]);
    setLiveSpeech("");
  };

  // Quick 1-click simulation of a domain turn (cycles through a new question every single time)
  const handleSimulateSample = async (customPrompt?: string, overrideVerticalId?: string) => {
    setIsSimulating(true);
    const targetVerticalId = overrideVerticalId || activeVerticalId;
    const currentIndex = simulatedQuestionIndices[targetVerticalId] || 0;
    const { question, nextIndex } = getNextCallerQuestion(targetVerticalId, currentIndex);
    const text = customPrompt || question.prompt;

    // Immediately stream the caller's speech into the live transcript
    setLiveSpeech(text);

    // Advance the question index so the next simulate click asks the next question
    setSimulatedQuestionIndices((prev) => ({
      ...prev,
      [targetVerticalId]: nextIndex,
    }));

    try {
      const telemetry = await simulateTurn(targetVerticalId, text);
      if (telemetry) {
        handleNewTelemetry(telemetry);
      }
    } catch (err) {
      console.error("Failed to run simulated turn:", err);
      setLiveSpeech("");
    } finally {
      setIsSimulating(false);
    }
  };

  const scrollToSection = (id: string) => {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: "smooth" });
    }
  };

  const activeCharacter = getAgentCharacter(activeVerticalId);

  return (
    <div className="min-h-screen flex flex-col bg-dark-bg text-[#fffaea] selection:bg-[#62f6b5]/20 selection:text-[#62f6b5]">
      {/* Header */}
      <Header
        activeVerticalId={activeVerticalId}
        activeVerticalName={activeVertical?.name || "Dispatch Operations"}
        isCallActive={Boolean(liveToken)}
      />

      {/* Hero Section */}
      <section className="relative pt-12 pb-16 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full overflow-hidden">
        {/* Subtle Ambient Radial Glow */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] bg-[#62f6b5]/[0.06] blur-[120px] rounded-full pointer-events-none -z-10" />

        <div className="text-center max-w-3xl mx-auto space-y-6">
          {/* Hero Eyebrow Pill */}
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-white/[0.04] border border-white/[0.08] text-xs text-[#9acdbf]">
            <span className="w-2 h-2 rounded-full bg-[#62f6b5] animate-pulse" />
            <span className="font-semibold tracking-wide">SUB-10MS CONTEXT RETRIEVAL PLATFORM</span>
          </div>

          {/* Main Headline */}
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-white leading-[1.15]">
            Intelligent Voice Operations for Mission-Critical Teams
          </h1>

          {/* Subheading */}
          <p className="text-base sm:text-lg text-[#a1a1aa] leading-relaxed max-w-2xl mx-auto font-normal">
            Deploy ultra-low-latency voice agents that retrieve operational context and enforce domain safety guardrails before you finish speaking.
          </p>

          {/* Action CTAs */}
          <div className="pt-2 flex flex-wrap items-center justify-center gap-3">
            <button
              onClick={() => scrollToSection("terminal")}
              className="px-6 py-3 rounded-xl bg-dark-cream hover:bg-white text-[#0e0e13] font-bold text-xs uppercase tracking-wider flex items-center space-x-2 transition-all shadow-lg shadow-black/40 hover:shadow-black/60"
            >
              <PhoneCall className="w-4 h-4 text-[#0e0e13]" />
              <span>Launch Voice Terminal</span>
            </button>
            <button
              onClick={() => scrollToSection("capabilities")}
              className="px-6 py-3 rounded-xl bg-[#151419] hover:bg-white/[0.08] border border-white/[0.1] text-white font-medium text-xs uppercase tracking-wider flex items-center space-x-2 transition-all"
            >
              <span>Explore Capabilities</span>
              <ArrowRight className="w-4 h-4 text-[#a1a1aa]" />
            </button>
          </div>

          {/* Key Metrics Ribbon */}
          <div className="pt-8 grid grid-cols-2 sm:grid-cols-4 gap-3 text-left">
            <div className="p-3.5 rounded-xl bg-[#111013] border border-white/[0.06]">
              <span className="text-[10px] text-[#71717a] uppercase tracking-wider block font-mono">Context SLA</span>
              <span className="text-xl sm:text-2xl font-black font-mono text-[#62f6b5]">&lt; 10ms</span>
              <span className="text-[11px] text-[#a1a1aa] block mt-0.5">Pre-warmed lookup</span>
            </div>
            <div className="p-3.5 rounded-xl bg-[#111013] border border-white/[0.06]">
              <span className="text-[10px] text-[#71717a] uppercase tracking-wider block font-mono">Turnaround</span>
              <span className="text-xl sm:text-2xl font-black font-mono text-[#fffaea]">~568ms</span>
              <span className="text-[11px] text-[#a1a1aa] block mt-0.5">Total response latency</span>
            </div>
            <div className="p-3.5 rounded-xl bg-[#111013] border border-white/[0.06]">
              <span className="text-[10px] text-[#71717a] uppercase tracking-wider block font-mono">Personas</span>
              <span className="text-xl sm:text-2xl font-black font-mono text-[#fffaea]">6 Agents</span>
              <span className="text-[11px] text-[#a1a1aa] block mt-0.5">Domain-specialized</span>
            </div>
            <div className="p-3.5 rounded-xl bg-[#111013] border border-white/[0.06]">
              <span className="text-[10px] text-[#71717a] uppercase tracking-wider block font-mono">Voice Mode</span>
              <span className="text-xl sm:text-2xl font-black font-mono text-[#fffaea]">Full Duplex</span>
              <span className="text-[11px] text-[#a1a1aa] block mt-0.5">Instant natural barge-in</span>
            </div>
          </div>
        </div>

        {/* Dynamic Agent Selector Pills */}
        <div className="mt-10 max-w-5xl mx-auto flex flex-col items-center">
          <div className="flex items-center space-x-2 text-[10px] uppercase font-mono tracking-widest text-[#a1a1aa] mb-3">
            <span className="w-1.5 h-1.5 rounded-full animate-ping" style={{ backgroundColor: activeCharacter.accentColor }} />
            <span>Select Domain Specialist to Inspect Live Operations Command Center</span>
          </div>

          <div className="w-full flex items-center justify-start sm:justify-center gap-2 overflow-x-auto pb-2 scrollbar-none">
            {Object.values(AGENT_CHARACTERS).map((agent) => {
              const isSelected = agent.id === activeVerticalId;
              return (
                <button
                  key={agent.id}
                  onClick={() => setActiveVerticalId(agent.id)}
                  className={`flex items-center space-x-2 px-3 py-1.5 rounded-xl border text-xs transition-all whitespace-nowrap flex-shrink-0 cursor-pointer ${
                    isSelected
                      ? "bg-white/[0.1] shadow-lg border-white/25 text-white scale-[1.03]"
                      : "bg-[#111013]/80 border-white/[0.06] text-[#a1a1aa] hover:text-white hover:bg-white/[0.04]"
                  }`}
                >
                  <CharacterAvatar verticalId={agent.id} size="sm" isSpeaking={isSelected && Boolean(liveToken)} />
                  <div className="flex flex-col text-left">
                    <span className="font-semibold leading-tight text-xs">{agent.characterName}</span>
                    <span
                      className="text-[9px] font-mono leading-none"
                      style={{ color: isSelected ? agent.accentColor : "#71717a" }}
                    >
                      {agent.callsign}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Hero Visual Display with Dynamic Persona Command Center */}
        <div className="mt-4 max-w-5xl mx-auto relative rounded-2xl overflow-hidden border border-white/[0.12] shadow-2xl group">
          <div className="relative aspect-[16/9] w-full overflow-hidden bg-[#0c0b0e]">
            {/* Dynamic Agent Hero Image */}
            <img
              key={activeCharacter.id}
              src={activeCharacter.heroImage}
              alt={`${activeCharacter.characterName} - ${activeCharacter.roleTitle}`}
              className="w-full h-full object-cover object-center group-hover:scale-102 transition-transform duration-700 opacity-90 animate-fade-in-image"
            />
            {/* Subtle Gradient Overlays */}
            <div className="absolute inset-0 bg-gradient-to-t from-[#0e0e13] via-transparent to-black/30" />
            <div className="absolute inset-0 bg-gradient-to-r from-black/50 via-transparent to-black/50" />

            {/* Floating Telemetry Badge Overlay (Top Left) */}
            <div className="absolute top-3 left-3 sm:top-6 sm:left-6 flex items-center space-x-2.5 sm:space-x-3 px-3 py-1.5 sm:px-3.5 sm:py-2 rounded-xl bg-[#0e0e13]/85 backdrop-blur-md border border-white/10 shadow-lg transition-all">
              <div
                className="w-2.5 h-2.5 rounded-full animate-pulse flex-shrink-0"
                style={{ backgroundColor: activeCharacter.accentColor }}
              />
              <div className="flex flex-col text-left">
                <span
                  className="text-[9px] sm:text-[10px] uppercase font-mono tracking-wider font-bold transition-colors"
                  style={{ color: activeCharacter.accentColor }}
                >
                  {activeCharacter.heroStatusTitle}
                </span>
                <span className="text-[10px] sm:text-[11px] text-white font-mono">
                  {activeCharacter.heroStatusSubtitle}
                </span>
              </div>
            </div>

            {/* Floating Persona Identity Badge Overlay (Top Right) */}
            <div className="hidden sm:flex absolute top-6 right-6 items-center space-x-2.5 px-3 py-1.5 rounded-xl bg-[#0e0e13]/85 backdrop-blur-md border border-white/10 shadow-lg transition-all">
              <CharacterAvatar verticalId={activeVerticalId} size="sm" isSpeaking={Boolean(liveToken)} />
              <div className="flex flex-col text-left">
                <div className="flex items-center space-x-1.5">
                  <span className="font-bold text-white text-xs">{activeCharacter.characterName}</span>
                  <span
                    className="text-[9px] font-mono px-1 py-0.2 rounded border font-semibold"
                    style={{
                      backgroundColor: `${activeCharacter.accentColor}18`,
                      borderColor: `${activeCharacter.accentColor}40`,
                      color: activeCharacter.accentColor,
                    }}
                  >
                    {activeCharacter.callsign}
                  </span>
                </div>
                <span className="text-[10px] text-[#a1a1aa]">{activeCharacter.roleTitle}</span>
              </div>
            </div>

            {/* Floating Animated Waveform Equalizer (Bottom Left) */}
            <div className="absolute bottom-3 left-3 sm:bottom-6 sm:left-6 flex items-end space-x-1.5 px-3 py-2 sm:px-4 sm:py-3 rounded-xl bg-[#0e0e13]/85 backdrop-blur-md border border-white/10 shadow-lg transition-all">
              <span
                className="text-[10px] sm:text-xs font-mono font-bold mr-1.5 sm:mr-2 transition-colors"
                style={{ color: activeCharacter.accentColor }}
              >
                VOICE FREQ
              </span>
              <div className="w-1 rounded-full wave-bar-1 transition-colors" style={{ backgroundColor: activeCharacter.accentColor }} />
              <div className="w-1 rounded-full wave-bar-2 transition-colors" style={{ backgroundColor: activeCharacter.accentColor }} />
              <div className="w-1 rounded-full wave-bar-3 transition-colors" style={{ backgroundColor: activeCharacter.accentColor }} />
              <div className="w-1 rounded-full wave-bar-4 transition-colors" style={{ backgroundColor: activeCharacter.accentColor }} />
              <div className="w-1 rounded-full wave-bar-2 transition-colors" style={{ backgroundColor: activeCharacter.accentColor }} />
              <div className="w-1 rounded-full wave-bar-1 transition-colors" style={{ backgroundColor: activeCharacter.accentColor }} />
              <div className="w-1 rounded-full wave-bar-3 transition-colors" style={{ backgroundColor: activeCharacter.accentColor }} />
            </div>

            {/* Floating SLA Tag (Bottom Right) */}
            <div
              className="hidden sm:flex absolute bottom-6 right-6 items-center space-x-2 px-3.5 py-2 rounded-xl border font-mono text-xs shadow-lg transition-all"
              style={{
                backgroundColor: `${activeCharacter.accentColor}15`,
                borderColor: `${activeCharacter.accentColor}40`,
                color: activeCharacter.accentColor,
              }}
            >
              <Zap className="w-4 h-4" style={{ color: activeCharacter.accentColor }} />
              <span>{activeCharacter.heroSlaTag}</span>
            </div>
          </div>
        </div>
      </section>

      {/* Flagship Section: Interactive Voice Terminal */}
      <section id="terminal" className="scroll-mt-20 py-8 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2.5">
              <span>Interactive Voice Terminal</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#62f6b5]/10 border border-[#62f6b5]/30 text-[#62f6b5]">
                LIVE SYSTEM
              </span>
            </h2>
            <p className="text-xs text-[#a1a1aa] mt-0.5">
              Select any specialized domain agent below and initiate a real-time hands-free voice conversation.
            </p>
          </div>
        </div>

        <div className="space-y-6">
          {/* 1. Vertical Selector Bar for 6 Agents */}
          <VerticalSelector
            verticals={verticals}
            activeVerticalId={activeVerticalId}
            onSelect={(vid) => setActiveVerticalId(vid)}
            disabled={Boolean(liveToken)}
          />

          {/* 2. Sub-10ms Latency Waterfall Widget (Minimized) */}
          <LatencyWaterfall telemetry={currentTelemetry} />

          {/* 3. Side-by-Side: Call Options on Left, Live Conversation on Right */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-stretch">
            {/* Left Column: Call Connection & Active Voice Room */}
            <div className="h-full">
              {liveToken ? (
                <VoiceRoom
                  token={liveToken}
                  serverUrl={liveKitUrl}
                  onDisconnect={handleEndCall}
                  onTelemetryReceived={handleNewTelemetry}
                  onLiveSpeech={setLiveSpeech}
                  activeVertical={activeVerticalId}
                />
              ) : (() => {
                const character = activeCharacter;
                return (
                  <div className="bg-dark-card border border-dark-border rounded-xl p-6 shadow-xl relative overflow-hidden flex flex-col justify-between h-[520px]">
                    <div
                      className="absolute top-0 right-0 w-64 h-64 rounded-full blur-3xl pointer-events-none opacity-15"
                      style={{ backgroundColor: character.accentColor }}
                    />

                    <div>
                      {/* Character Identity & Callsign */}
                      <div className="flex items-start justify-between gap-4 pb-4 border-b border-white/[0.06]">
                        <div className="flex items-center space-x-3.5">
                          <CharacterAvatar
                            verticalId={activeVerticalId}
                            size="lg"
                            showBadge={true}
                          />
                          <div>
                            <div className="flex items-center space-x-2">
                              <h3 className="text-base font-bold text-dark-cream">
                                {character.characterName}
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
                          </div>
                        </div>
                      </div>

                      {/* Briefing & Operational Greeting */}
                      <div className="mt-5 space-y-3">
                        <div className="bg-[#0e0e13] border border-white/[0.06] rounded-xl p-4">
                          <span className="text-[10px] font-mono uppercase tracking-wider text-[#71717a] block mb-1">
                            Standard Operational Greeting
                          </span>
                          <p className="text-xs text-[#9acdbf] italic leading-relaxed">
                            &quot;{character.greeting}&quot;
                          </p>
                        </div>

                        <div className="bg-[#0e0e13] border border-white/[0.06] rounded-xl p-4 space-y-1.5">
                          <span className="text-[10px] font-mono uppercase tracking-wider text-[#71717a] block">
                            Mission Scope &amp; Specialization
                          </span>
                          <p className="text-xs text-[#a1a1aa] leading-relaxed">
                            {character.tagline}
                          </p>
                          <div className="flex flex-wrap gap-1.5 pt-1.5">
                            {character.specialties.map((spec, sIdx) => (
                              <span
                                key={sIdx}
                                className="text-[10px] font-mono px-2 py-0.5 rounded bg-white/[0.04] border border-white/[0.08] text-[#fffaea]/80"
                              >
                                {spec}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Start Call CTA Button */}
                    <div className="pt-4 border-t border-white/[0.06]">
                      <button
                        onClick={handleStartCall}
                        disabled={isConnecting}
                        className="w-full py-3.5 rounded-xl bg-dark-cream hover:bg-white text-[#0e0e13] font-bold text-xs uppercase tracking-wider flex items-center justify-center space-x-2.5 transition-all shadow-lg shadow-black/40 hover:shadow-black/60 disabled:opacity-50 cursor-pointer"
                      >
                        <PhoneCall className="w-4 h-4 text-[#0e0e13]" />
                        <span>{isConnecting ? "Connecting to Agent..." : `Start Voice Call with ${character.characterName}`}</span>
                      </button>
                    </div>
                  </div>
                );
              })()}
            </div>

            {/* Right Column: Live Conversation & Context Stream */}
            <div className="h-full">
              <TranscriptViewer
                turns={turnHistory}
                liveSpeech={liveSpeech}
                isCallActive={Boolean(liveToken)}
                activeVerticalId={activeVerticalId}
                onSimulateSample={handleSimulateSample}
                isSimulating={isSimulating}
              />
            </div>
          </div>
        </div>
      </section>

      {/* Section 3: Architectural Capabilities */}
      <section id="capabilities" className="scroll-mt-20 py-16 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full border-t border-white/[0.06]">
        <div className="text-center max-w-2xl mx-auto mb-12 space-y-3">
          <span className="text-xs font-mono font-semibold text-[#62f6b5] uppercase tracking-wider">
            Operational Capabilities
          </span>
          <h2 className="text-3xl font-bold tracking-tight text-white">
            Engineered for Mission-Critical Reliability
          </h2>
          <p className="text-xs sm:text-sm text-[#a1a1aa]">
            Built from the ground up for instantaneous sub-10ms context retrieval, safety guardrails, and full-duplex speech.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Card 1 */}
          <div className="bg-[#111013] border border-white/[0.08] rounded-2xl p-6 shadow-md space-y-4">
            <div className="w-10 h-10 rounded-xl bg-[#62f6b5]/10 border border-[#62f6b5]/30 flex items-center justify-center">
              <Zap className="w-5 h-5 text-[#62f6b5]" />
            </div>
            <h3 className="text-base font-bold text-white">Sub-10ms Context Engine</h3>
            <p className="text-xs text-[#a1a1aa] leading-relaxed">
              Dual-tier architecture combining pre-warmed memory cache and high-dimensional semantic search. Context is populated in under 10ms while the user speaks.
            </p>
            <ul className="space-y-2 pt-2 text-xs text-[#9acdbf]">
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-[#62f6b5] flex-shrink-0" />
                <span>Synchronized knowledge injection</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-[#62f6b5] flex-shrink-0" />
                <span>Dynamic memory across conversation turns</span>
              </li>
            </ul>
          </div>

          {/* Card 2 */}
          <div className="bg-[#111013] border border-white/[0.08] rounded-2xl p-6 shadow-md space-y-4">
            <div className="w-10 h-10 rounded-xl bg-blue-500/10 border border-blue-500/30 flex items-center justify-center">
              <ShieldCheck className="w-5 h-5 text-blue-400" />
            </div>
            <h3 className="text-base font-bold text-white">Zero-Trust Guardrails</h3>
            <p className="text-xs text-[#a1a1aa] leading-relaxed">
              Every turn is evaluated against strict domain safety triggers, protocol overrides, and automatic PII redaction to prevent hallucinations in high-stakes environments.
            </p>
            <ul className="space-y-2 pt-2 text-xs text-[#9acdbf]">
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-blue-400 flex-shrink-0" />
                <span>Deterministic emergency override alerts</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-blue-400 flex-shrink-0" />
                <span>Zero-hallucination factual validation</span>
              </li>
            </ul>
          </div>

          {/* Card 3 */}
          <div className="bg-[#111013] border border-white/[0.08] rounded-2xl p-6 shadow-md space-y-4">
            <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center">
              <Volume2 className="w-5 h-5 text-amber-400" />
            </div>
            <h3 className="text-base font-bold text-white">Full-Duplex Natural Speech</h3>
            <p className="text-xs text-[#a1a1aa] leading-relaxed">
              Sub-second voice turnaround with seamless barge-in interruption. The agent immediately yields when you speak, mirroring natural tactical radio coordination.
            </p>
            <ul className="space-y-2 pt-2 text-xs text-[#9acdbf]">
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
                <span>Instant sub-second barge-in cancellation</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
                <span>Adaptive backchanneling & pacing</span>
              </li>
            </ul>
          </div>
        </div>
      </section>

      {/* Section 5: Latency Waterfall Architecture */}
      <section id="architecture" className="scroll-mt-20 py-16 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full border-t border-white/[0.06]">
        <div className="text-center max-w-2xl mx-auto mb-12 space-y-3">
          <span className="text-xs font-mono font-semibold text-[#62f6b5] uppercase tracking-wider">
            Latency Architecture
          </span>
          <h2 className="text-3xl font-bold tracking-tight text-white">
            Total Turnaround: Under 590ms
          </h2>
          <p className="text-xs sm:text-sm text-[#a1a1aa]">
            Every microsecond of the voice pipeline is measured, optimized, and held to strict operational SLAs.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-5 rounded-xl bg-[#111013] border border-white/[0.08] flex flex-col justify-between">
            <div className="flex items-center justify-between mb-3">
              <span className="text-[10px] uppercase font-mono tracking-wider text-[#a1a1aa]">1. Speech Input</span>
              <span className="text-[10px] font-mono text-[#71717a]">Stage 1</span>
            </div>
            <div className="my-2">
              <span className="text-3xl font-extrabold font-mono text-white">240</span>
              <span className="text-xs font-mono text-[#a1a1aa] ml-1">ms</span>
            </div>
            <p className="text-xs text-[#71717a]">Neural speech recognition and audio boundary finalization.</p>
          </div>

          <div className="p-5 rounded-xl bg-[#0d241e]/70 border border-[#62f6b5]/50 flex flex-col justify-between relative overflow-hidden shadow-lg shadow-[#62f6b5]/10">
            <div className="flex items-center justify-between mb-3">
              <span className="text-[10px] uppercase font-mono tracking-wider text-[#62f6b5] font-bold">2. Context Engine</span>
              <span className="text-[9px] font-mono font-bold px-1.5 py-0.2 rounded bg-[#62f6b5] text-black">HERO</span>
            </div>
            <div className="my-2">
              <span className="text-3xl font-extrabold font-mono text-[#62f6b5]">6.8</span>
              <span className="text-xs font-mono text-[#9acdbf] ml-1">ms</span>
            </div>
            <p className="text-xs text-[#9acdbf]">High-speed cache and vector index retrieval in under 10ms.</p>
          </div>

          <div className="p-5 rounded-xl bg-[#111013] border border-white/[0.08] flex flex-col justify-between">
            <div className="flex items-center justify-between mb-3">
              <span className="text-[10px] uppercase font-mono tracking-wider text-[#a1a1aa]">3. Language Model</span>
              <span className="text-[10px] font-mono text-[#71717a]">Stage 3</span>
            </div>
            <div className="my-2">
              <span className="text-3xl font-extrabold font-mono text-white">175</span>
              <span className="text-xs font-mono text-[#a1a1aa] ml-1">ms</span>
            </div>
            <p className="text-xs text-[#71717a]">Time to first token generation with grounded operational context.</p>
          </div>

          <div className="p-5 rounded-xl bg-[#111013] border border-white/[0.08] flex flex-col justify-between">
            <div className="flex items-center justify-between mb-3">
              <span className="text-[10px] uppercase font-mono tracking-wider text-[#a1a1aa]">4. Voice Synthesis</span>
              <span className="text-[10px] font-mono text-[#71717a]">Stage 4</span>
            </div>
            <div className="my-2">
              <span className="text-3xl font-extrabold font-mono text-white">145</span>
              <span className="text-xs font-mono text-[#a1a1aa] ml-1">ms</span>
            </div>
            <p className="text-xs text-[#71717a]">Streaming neural text-to-speech audio packet transmission.</p>
          </div>
        </div>
      </section>

      {/* Section 6: What Type of Questions to Ask Every Agent */}
      <AgentQuestionsGuide
        activeVerticalId={activeVerticalId}
        onSelectVertical={(vId) => setActiveVerticalId(vId)}
        onTestPrompt={(vId, prompt) => handleSimulateSample(prompt, vId)}
      />

      {/* Footer */}
      <footer className="border-t border-white/[0.08] bg-[#0e0e13] py-12 px-4 sm:px-6 lg:px-8 mt-auto">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="flex items-center space-x-3">
            <div className="w-7 h-7 rounded-lg bg-[#efebdd] flex items-center justify-center">
              <Zap className="w-4 h-4 text-black fill-black" />
            </div>
            <span className="text-base font-bold text-white">Tandem</span>
            <span className="text-xs text-[#71717a] font-normal">&bull; Intelligent Voice Operations</span>
          </div>

          <div className="flex items-center space-x-6 text-xs text-[#a1a1aa]">
            <button onClick={() => scrollToSection("terminal")} className="hover:text-white transition-colors">
              Voice Terminal
            </button>
            <button onClick={() => scrollToSection("capabilities")} className="hover:text-white transition-colors">
              Capabilities
            </button>
            <button onClick={() => scrollToSection("architecture")} className="hover:text-white transition-colors">
              Performance
            </button>
            <button onClick={() => scrollToSection("questions-guide")} className="hover:text-white transition-colors text-[#62f6b5]">
              Questions Guide
            </button>
          </div>

          <div className="text-xs text-[#71717a] font-mono">
            Sub-10ms Operational Platform
          </div>
        </div>
      </footer>
    </div>
  );
}
