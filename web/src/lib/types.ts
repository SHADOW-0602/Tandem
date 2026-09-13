export interface Vertical {
  id: string;
  name: string;
  description: string;
  icon: string;
  moss_index: string;
  knowledge_file: string;
  sample_prompts: string[];
  latency_target_ms: number;
  system_prompt?: string;
  guardrails?: Array<{
    id: string;
    trigger_phrases?: string[];
    severity?: string;
    action?: string;
    override_message?: string;
    name?: string;
    description?: string;
    pattern?: string;
  }>;
}

export interface TurnTelemetry {
  call_id: string;
  turn_id: number;
  vertical: string;
  user_transcript: string;
  agent_response: string;
  retrieved_doc_ids: string[];
  retrieved_snippets: string[];
  guardrail_action: string | null;
  stt_latency_ms: number;
  moss_latency_ms: number;
  llm_ttft_ms: number;
  tts_ttfb_ms: number;
  total_latency_ms: number;
  is_sub_10ms_moss: boolean;
  within_budget: boolean;
  timestamp: number;
}

export interface TelemetryStats {
  total_turns: number;
  avg_moss_latency_ms: number;
  avg_total_latency_ms: number;
  p50_total_latency_ms: number;
  p95_total_latency_ms: number;
  sub_10ms_ratio: number;
  recent_turns: TurnTelemetry[];
  guardrail_events: Array<{
    call_id: string;
    vertical: string;
    action: string;
    user_transcript: string;
    timestamp: number;
  }>;
}

export interface KnowledgeDoc {
  id: string;
  title: string;
  vertical: string;
  category: string;
  text: string;
}
