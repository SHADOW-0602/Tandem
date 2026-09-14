"use client";

import React, { useState, useEffect, useCallback } from "react";
import { RefreshCw, Server, Bot } from "lucide-react";

interface ServiceStatus {
  state: "checking" | "active" | "waking" | "inactive";
  latencyMs: number | null;
  message?: string;
}

const CONTROL_PLANE_URL = process.env.NEXT_PUBLIC_CONTROL_PLANE_URL || "https://tandem-laravel-api.onrender.com";
const VOICE_AGENT_URL = process.env.NEXT_PUBLIC_VOICE_AGENT_URL || "https://tandem-voice-agent.onrender.com";

export const BackendStatus: React.FC = () => {
  const [controlPlane, setControlPlane] = useState<ServiceStatus>({
    state: "checking",
    latencyMs: null,
  });

  const [voiceAgent, setVoiceAgent] = useState<ServiceStatus>({
    state: "checking",
    latencyMs: null,
  });

  const [isRefreshing, setIsRefreshing] = useState(false);

  const checkHealth = useCallback(async () => {
    setIsRefreshing(true);

    // 1. Check Control Plane (Laravel API)
    const checkControlPlane = async (): Promise<ServiceStatus> => {
      const start = performance.now();
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 12000);

      try {
        const res = await fetch(`${CONTROL_PLANE_URL}/api/health`, {
          cache: "no-store",
          signal: controller.signal,
        });
        clearTimeout(timeoutId);
        const latency = Math.round(performance.now() - start);

        if (res.ok) {
          return { state: "active", latencyMs: latency };
        }
        return { state: "inactive", latencyMs: latency, message: `HTTP ${res.status}` };
      } catch (err: any) {
        clearTimeout(timeoutId);
        const latency = Math.round(performance.now() - start);
        if (err.name === "AbortError" || latency > 4000) {
          return { state: "waking", latencyMs: latency, message: "Waking up..." };
        }
        return { state: "inactive", latencyMs: latency, message: "Unreachable" };
      }
    };

    // 2. Check Voice Agent Worker (LiveKit Python Agent)
    const checkVoiceAgent = async (): Promise<ServiceStatus> => {
      const start = performance.now();
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 12000);

      try {
        await fetch(`${VOICE_AGENT_URL}/`, {
          mode: "no-cors",
          cache: "no-store",
          signal: controller.signal,
        });
        clearTimeout(timeoutId);
        const latency = Math.round(performance.now() - start);

        return { state: "active", latencyMs: latency };
      } catch (err: any) {
        clearTimeout(timeoutId);
        const latency = Math.round(performance.now() - start);
        if (err.name === "AbortError" || latency > 4000) {
          return { state: "waking", latencyMs: latency, message: "Waking up..." };
        }
        return { state: "inactive", latencyMs: latency, message: "Unreachable" };
      }
    };

    const [cpRes, vaRes] = await Promise.all([checkControlPlane(), checkVoiceAgent()]);
    setControlPlane(cpRes);
    setVoiceAgent(vaRes);
    setIsRefreshing(false);
  }, []);

  useEffect(() => {
    checkHealth();
    // Auto-poll every 25 seconds (keeps Render awake while tab is open)
    const interval = setInterval(checkHealth, 25000);
    return () => clearInterval(interval);
  }, [checkHealth]);

  const renderBadge = (title: string, icon: React.ReactNode, status: ServiceStatus) => {
    let dot = <span className="inline-flex rounded-full h-2 w-2 bg-neutral-500" />;
    let badgeStyle = "bg-[#111013] border-white/[0.08] text-neutral-400";
    let statusText = "Checking...";

    if (status.state === "active") {
      dot = (
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#62f6b5] opacity-75" />
          <span className="relative inline-flex rounded-full h-2 w-2 bg-[#62f6b5]" />
        </span>
      );
      badgeStyle = "bg-[#0d241e]/80 border-[#62f6b5]/30 text-[#9acdbf]";
      statusText = `Active ${status.latencyMs ? `(${status.latencyMs}ms)` : ""}`;
    } else if (status.state === "waking") {
      dot = (
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75" />
          <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-400" />
        </span>
      );
      badgeStyle = "bg-amber-950/40 border-amber-500/30 text-amber-300";
      statusText = "Waking Up (~30s)";
    } else if (status.state === "inactive") {
      dot = <span className="inline-flex rounded-full h-2 w-2 bg-red-500" />;
      badgeStyle = "bg-red-950/40 border-red-500/30 text-red-300";
      statusText = status.message || "Sleep / Down";
    }

    return (
      <div
        className={`px-2.5 py-1.5 rounded-md border text-[11px] font-medium flex items-center space-x-2 transition-all ${badgeStyle}`}
        title={`${title}: ${statusText}`}
      >
        {dot}
        <span className="text-white/70 flex items-center gap-1 font-semibold">
          {icon}
          {title}:
        </span>
        <span className="font-mono text-[10px]">{statusText}</span>
      </div>
    );
  };

  return (
    <div className="flex items-center flex-wrap gap-1.5 sm:gap-2">
      {renderBadge("Control Plane", <Server className="w-3 h-3 text-[#9acdbf]" />, controlPlane)}
      {renderBadge("Voice Agent", <Bot className="w-3 h-3 text-[#9acdbf]" />, voiceAgent)}

      <button
        onClick={checkHealth}
        disabled={isRefreshing}
        className="p-1.5 rounded-md bg-[#111013] hover:bg-white/[0.08] border border-white/[0.08] text-neutral-400 hover:text-white transition-colors disabled:opacity-50"
        title="Refresh backend status"
        aria-label="Refresh backend status"
      >
        <RefreshCw className={`w-3 h-3 ${isRefreshing ? "animate-spin text-[#62f6b5]" : ""}`} />
      </button>
    </div>
  );
};
