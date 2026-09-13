import { Vertical, TelemetryStats, KnowledgeDoc, TurnTelemetry } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_CONTROL_PLANE_URL || "http://localhost:8000";

export async function fetchVerticals(): Promise<Vertical[]> {
  try {
    const res = await fetch(`${API_BASE}/api/verticals`, { cache: "no-store" });
    if (!res.ok) throw new Error(`Failed to fetch verticals: ${res.statusText}`);
    return await res.json();
  } catch (err) {
    console.error("fetchVerticals error:", err);
    return [];
  }
}

export async function fetchKnowledge(verticalId: string): Promise<KnowledgeDoc[]> {
  try {
    const res = await fetch(`${API_BASE}/api/knowledge/${verticalId}`, { cache: "no-store" });
    if (!res.ok) throw new Error("Failed to fetch knowledge");
    return await res.json();
  } catch (err) {
    console.error("fetchKnowledge error:", err);
    return [];
  }
}

export async function mintLiveKitToken(roomName?: string, vertical?: string): Promise<{
  token: string;
  url: string;
  room_name: string;
  identity: string;
  vertical: string;
}> {
  const res = await fetch(`${API_BASE}/api/token`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      room_name: roomName,
      vertical: vertical || "dispatch",
    }),
  });
  if (!res.ok) throw new Error("Failed to mint voice session token");
  return await res.json();
}

export async function fetchTelemetryStats(): Promise<TelemetryStats> {
  try {
    const res = await fetch(`${API_BASE}/api/telemetry/stats`, { cache: "no-store" });
    if (!res.ok) throw new Error("Failed to fetch telemetry stats");
    return await res.json();
  } catch (err) {
    return {
      total_turns: 0,
      avg_moss_latency_ms: 0,
      avg_total_latency_ms: 0,
      p50_total_latency_ms: 0,
      p95_total_latency_ms: 0,
      sub_10ms_ratio: 1,
      recent_turns: [],
      guardrail_events: [],
    };
  }
}

export async function simulateTurn(vertical: string, text: string): Promise<TurnTelemetry> {
  const res = await fetch(`${API_BASE}/api/simulate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ vertical, text }),
  });
  if (!res.ok) throw new Error("Simulation failed");
  return await res.json();
}

export async function runEvals(): Promise<{
  status: string;
  total_cases: number;
  passed: number;
  pass_rate_pct: number;
  results: TurnTelemetry[];
}> {
  const res = await fetch(`${API_BASE}/api/evals/run`, { cache: "no-store" });
  if (!res.ok) throw new Error("Evals execution failed");
  return await res.json();
}

export async function fetchScenarios(vertical?: string): Promise<any[]> {
  try {
    const url = vertical
      ? `${API_BASE}/api/simulations/scenarios?vertical=${vertical}`
      : `${API_BASE}/api/simulations/scenarios`;
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) return [];
    const data = await res.json();
    return data.scenarios || [];
  } catch {
    return [];
  }
}

export async function fetchPersonalities(): Promise<any[]> {
  try {
    const res = await fetch(`${API_BASE}/api/simulations/personalities`, { cache: "no-store" });
    if (!res.ok) return [];
    const data = await res.json();
    return data.personalities || [];
  } catch {
    return [];
  }
}

export async function runAITesterSimulation(payload: {
  scenario_id?: string;
  personality_id?: string;
  custom_scenario?: any;
  custom_personality?: any;
  max_turns?: number;
}): Promise<any> {
  const res = await fetch(`${API_BASE}/api/simulations/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Simulation failed: ${err}`);
  }
  return await res.json();
}

