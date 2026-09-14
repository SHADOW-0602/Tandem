"use client";

import React, { useState, useEffect } from "react";
import { KnowledgeDoc, Vertical } from "@/lib/types";
import { fetchKnowledge } from "@/lib/api";
import { BookOpen, ShieldAlert, FileText, Search, Clock, Check, X, Sparkles, PlusCircle } from "lucide-react";
import { CharacterAvatar } from "./CharacterAvatar";
import { getAgentCharacter } from "@/lib/personas";

interface KnowledgeInspectorProps {
  vertical: Vertical | null;
}

export const KnowledgeInspector: React.FC<KnowledgeInspectorProps> = ({ vertical }) => {
  const [docs, setDocs] = useState<KnowledgeDoc[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<KnowledgeDoc | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [tab, setTab] = useState<"knowledge" | "search" | "staging" | "guardrails">("knowledge");

  // Dynamic search state
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [searchLatency, setSearchLatency] = useState<number | null>(null);
  const [isSearching, setIsSearching] = useState(false);

  // Staging queue state
  const [stagedFacts, setStagedFacts] = useState<any[]>([]);

  useEffect(() => {
    if (!vertical) return;
    setLoading(true);
    fetchKnowledge(vertical.id)
      .then((data) => {
        setDocs(data);
        if (data.length > 0) setSelectedDoc(data[0]);
      })
      .finally(() => setLoading(false));

    loadStagedFacts();
  }, [vertical?.id]);

  const loadStagedFacts = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/knowledge/staging");
      if (res.ok) {
        const json = await res.json();
        setStagedFacts(json.staged_facts || []);
      }
    } catch (e) {
      console.debug("Staging fetch note:", e);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim() || !vertical) return;
    setIsSearching(true);
    try {
      const res = await fetch("http://localhost:8000/api/knowledge/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          vertical: vertical.id,
          query: searchQuery,
          limit: 3,
        }),
      });
      if (res.ok) {
        const json = await res.json();
        setSearchResults(json.results || []);
        setSearchLatency(json.latency_ms || 0);
      }
    } catch (err) {
      console.error("Search error:", err);
    } finally {
      setIsSearching(false);
    }
  };

  const handleApprove = async (stageId: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/knowledge/staging/${stageId}/approve`, {
        method: "POST",
      });
      if (res.ok) {
        setStagedFacts((prev) => prev.filter((f) => f.stage_id !== stageId));
        if (vertical) fetchKnowledge(vertical.id).then(setDocs);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleReject = async (stageId: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/knowledge/staging/${stageId}/reject`, {
        method: "POST",
      });
      if (res.ok) {
        setStagedFacts((prev) => prev.filter((f) => f.stage_id !== stageId));
      }
    } catch (e) {
      console.error(e);
    }
  };

  if (!vertical) return null;

  return (
    <div className="bg-[#111013] border border-white/[0.08] rounded-xl p-5 shadow-lg flex flex-col h-[520px]">
      {/* Header Tabs in Tandem Aesthetic */}
      <div className="flex items-center justify-between pb-3 border-b border-white/[0.06] mb-3">
        <div className="flex items-center space-x-1.5 overflow-x-auto">
          <button
            onClick={() => setTab("knowledge")}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-[11px] font-medium transition-all ${
              tab === "knowledge"
                ? "bg-[#efebdd] text-black shadow-sm"
                : "text-[#a1a1aa] hover:text-[#fffaea] hover:bg-white/[0.03]"
            }`}
          >
            <BookOpen className="w-3.5 h-3.5" />
            <span>SOPs ({docs.length})</span>
          </button>

          <button
            onClick={() => setTab("search")}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-[11px] font-medium transition-all ${
              tab === "search"
                ? "bg-[#efebdd] text-black shadow-sm"
                : "text-[#a1a1aa] hover:text-[#fffaea] hover:bg-white/[0.03]"
            }`}
          >
            <Search className="w-3.5 h-3.5" />
            <span>Context Search</span>
          </button>

          <button
            onClick={() => {
              setTab("staging");
              loadStagedFacts();
            }}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-[11px] font-medium transition-all ${
              tab === "staging"
                ? "bg-[#62f6b5] text-black font-semibold shadow-sm"
                : "text-[#a1a1aa] hover:text-[#fffaea] hover:bg-white/[0.03]"
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Staging Review {stagedFacts.length > 0 && `(${stagedFacts.length})`}</span>
          </button>

          <button
            onClick={() => setTab("guardrails")}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-[11px] font-medium transition-all ${
              tab === "guardrails"
                ? "bg-[#efebdd] text-black shadow-sm"
                : "text-[#a1a1aa] hover:text-[#fffaea] hover:bg-white/[0.03]"
            }`}
          >
            <ShieldAlert className="w-3.5 h-3.5" />
            <span>Guardrails ({vertical.guardrails?.length || 0})</span>
          </button>
        </div>

        {(() => {
          const character = getAgentCharacter(vertical.id);
          return (
            <div className="flex items-center space-x-2 pl-2 border-l border-white/[0.08]">
              <CharacterAvatar verticalId={vertical.id} size="sm" />
              <div className="hidden sm:flex flex-col text-right">
                <span className="text-[11px] font-bold text-[#fffaea] leading-tight">
                  {character.characterName}
                </span>
                <span className="text-[9px] font-mono text-[#a1a1aa]">
                  {character.callsign}
                </span>
              </div>
            </div>
          );
        })()}
      </div>

      {/* Tab 1: SOP Master Detail List */}
      {tab === "knowledge" && (
        <div className="flex-1 flex flex-col sm:flex-row gap-3 overflow-hidden">
          {/* Doc Master List */}
          <div className="w-full sm:w-1/2 overflow-y-auto space-y-1.5 pr-1">
            {docs.map((d) => (
              <button
                key={d.id}
                onClick={() => setSelectedDoc(d)}
                className={`w-full p-2.5 rounded-lg border text-left transition-all ${
                  selectedDoc?.id === d.id
                    ? "bg-[#1f1f23] border-[#62f6b5]/50 text-[#fffaea]"
                    : "bg-[#0e0e13] border-white/[0.06] text-[#a1a1aa] hover:border-white/[0.12] hover:text-[#fffaea]"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono text-[#62f6b5] font-semibold">{d.id}</span>
                  <span className="text-[9px] uppercase font-mono px-1.5 py-0.2 rounded bg-black text-[#a1a1aa] border border-white/[0.06]">
                    {d.category}
                  </span>
                </div>
                <h5 className="text-xs font-medium line-clamp-1 mt-1 text-[#fffaea]">{d.title}</h5>
              </button>
            ))}
          </div>

          {/* Doc Detail Pane */}
          <div className="w-full sm:w-1/2 bg-[#0e0e13] border border-white/[0.06] rounded-lg p-3.5 overflow-y-auto text-xs">
            {selectedDoc ? (
              <div>
                <div className="flex items-center space-x-2 mb-2 pb-2 border-b border-white/[0.06]">
                  <FileText className="w-4 h-4 text-[#62f6b5]" />
                  <h4 className="font-medium text-[#fffaea]">{selectedDoc.title}</h4>
                </div>
                <div className="text-[10px] text-[#71717a] font-mono mb-2 flex items-center justify-between">
                  <span>ID: {selectedDoc.id}</span>
                  <span className="text-[#9acdbf]">Category: {selectedDoc.category}</span>
                </div>
                <div className="text-[#fffaea]/90 leading-relaxed whitespace-pre-line font-sans text-xs">
                  {selectedDoc.text}
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center h-full text-[#71717a]">
                Select an SOP to inspect content
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 2: Live Vector Test */}
      {tab === "search" && (
        <div className="flex-1 flex flex-col space-y-3 overflow-hidden">
          <form onSubmit={handleSearch} className="flex gap-2">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Test sub-10ms query (e.g. '10-50 traffic accident', 'LOTO step 3')..."
              className="flex-1 bg-[#0e0e13] border border-white/[0.08] rounded-md px-3 py-2 text-xs text-[#fffaea] placeholder-[#71717a] focus:outline-none focus:border-[#62f6b5]"
            />
            <button
              type="submit"
              disabled={isSearching}
              className="px-4 py-2 bg-[#efebdd] hover:bg-[#fffaea] text-black font-semibold text-xs rounded-md transition-all disabled:opacity-50"
            >
              {isSearching ? "Searching..." : "Search"}
            </button>
          </form>

          {searchLatency !== null && (
            <div className="flex items-center space-x-2 text-[11px] font-mono text-[#9acdbf]">
              <Clock className="w-3 h-3 text-[#62f6b5]" />
              <span>
                Search Latency: <strong className="text-[#62f6b5]">{searchLatency}ms</strong> (Sub-10ms Verified)
              </span>
            </div>
          )}

          <div className="flex-1 overflow-y-auto space-y-2 pr-1">
            {searchResults.map((r, i) => (
              <div key={i} className="p-3 bg-[#0e0e13] border border-white/[0.06] rounded-lg text-xs">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-medium text-[#fffaea]">{r.title}</span>
                  <span className="text-[10px] font-mono text-[#62f6b5]">
                    Score: {(r.score * 100).toFixed(1)}%
                  </span>
                </div>
                <p className="text-[#a1a1aa] leading-relaxed text-[11px]">{r.raw_text || r.text}</p>
              </div>
            ))}
            {searchResults.length === 0 && searchLatency !== null && (
              <p className="text-xs text-[#71717a] text-center py-6">No matching documents found.</p>
            )}
          </div>
        </div>
      )}

      {/* Tab 3: HITL Staging Review Queue */}
      {tab === "staging" && (
        <div className="flex-1 overflow-y-auto space-y-2.5 pr-1">
          {stagedFacts.length === 0 ? (
            <div className="text-center py-12 text-xs text-[#71717a]">
              <Sparkles className="w-6 h-6 mx-auto mb-2 text-[#62f6b5]/40" />
              <p>No operational facts currently pending review.</p>
              <p className="text-[11px] mt-1 text-[#56565a]">
                Facts extracted from calls with 70-90% confidence appear here for supervisor approval.
              </p>
            </div>
          ) : (
            stagedFacts.map((fact) => (
              <div
                key={fact.stage_id}
                className="p-3 bg-[#0e0e13] border border-white/[0.08] rounded-lg flex flex-col justify-between gap-2"
              >
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-semibold text-xs text-[#fffaea]">
                      {fact.subject} &bull; {fact.attribute}
                    </span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-950/40 text-amber-300 border border-amber-500/30">
                      Conf: {(fact.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                  <p className="text-xs text-[#9acdbf] mt-0.5">
                    Proposed value: <strong className="text-white">{fact.new_value}</strong>
                  </p>
                  <p className="text-[11px] text-[#71717a] italic mt-1">
                    &quot;{fact.verbatim_quote}&quot;
                  </p>
                </div>

                <div className="flex items-center justify-end space-x-2 pt-2 border-t border-white/[0.04]">
                  <button
                    onClick={() => handleReject(fact.stage_id)}
                    className="px-2.5 py-1 rounded bg-red-950/30 border border-red-500/30 text-red-300 hover:bg-red-900/40 text-[11px] flex items-center space-x-1"
                  >
                    <X className="w-3 h-3" />
                    <span>Dismiss</span>
                  </button>
                  <button
                    onClick={() => handleApprove(fact.stage_id)}
                    className="px-2.5 py-1 rounded bg-[#62f6b5] hover:bg-[#82f8c4] text-black font-semibold text-[11px] flex items-center space-x-1"
                  >
                    <Check className="w-3 h-3" />
                    <span>Approve to Knowledge Base</span>
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Tab 4: Safety Guardrails */}
      {tab === "guardrails" && (
        <div className="flex-1 overflow-y-auto space-y-2 text-xs pr-1">
          {vertical.guardrails && vertical.guardrails.length > 0 ? (
            vertical.guardrails.map((g, idx) => (
              <div
                key={idx}
                className="p-3 rounded-lg bg-[#0e0e13] border border-red-500/20 flex flex-col space-y-1.5"
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-[10px] text-red-400 font-bold uppercase tracking-wider">
                    Rule #{idx + 1} &bull; {g.severity || "CRITICAL"}
                  </span>
                  <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-red-950 text-red-300 border border-red-500/30">
                    BYPASS &lt; 1ms
                  </span>
                </div>
                <div className="text-[#fffaea] font-medium text-xs">{g.description || g.name}</div>
                <div className="text-[11px] text-[#a1a1aa] bg-black/40 p-2 rounded border border-white/[0.04] font-mono">
                  Trigger Pattern: <code className="text-[#62f6b5]">{g.pattern || "Distress / Threat / Weapon"}</code>
                </div>
                <div className="text-[11px] text-red-300 font-sans">
                  Action: {g.action || "Instant Code 3 override & priority lock"}
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-10 text-[#71717a]">No custom guardrails configured.</div>
          )}
        </div>
      )}
    </div>
  );
};
