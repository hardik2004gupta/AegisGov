"use client";

import { useEffect, useState, useCallback } from "react";
import { audit as auditApi } from "@/lib/api";
import type { AuditEvent, TraceTimeline } from "@/lib/types";
import { Badge } from "@/components/ui/Badge";
import { Skeleton, SkeletonRow } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { GovernanceTimeline } from "@/components/governance/GovernanceTimeline";
import { timeAgo, agentDisplayName } from "@/lib/utils";

const DECISIONS = ["", "ALLOWED", "DENIED", "BLOCKED", "PENDING", "APPROVED", "REJECTED"];
const ACTION_TYPES = [
  "", "IDENTITY_VERIFIED", "IDENTITY_DENIED", "INPUT_BLOCKED",
  "AGENT_HANDOFF_ALLOWED", "AGENT_HANDOFF_DENIED",
  "POLICY_ALLOWED", "POLICY_DENIED", "RISK_CLASSIFIED",
  "APPROVAL_CREATED", "APPROVAL_APPROVED", "APPROVAL_REJECTED",
  "TOOL_EXECUTION_COMPLETED", "TOOL_EXECUTION_FAILED",
];

export default function AuditPage() {
  const [events,   setEvents]   = useState<AuditEvent[]>([]);
  const [total,    setTotal]    = useState(0);
  const [loading,  setLoading]  = useState(true);
  const [error,    setError]    = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>(null); // trace_id
  const [timeline, setTimeline] = useState<TraceTimeline | null>(null);
  const [tlLoading,setTlLoading]= useState(false);

  // Filters
  const [search,     setSearch]     = useState("");
  const [decision,   setDecision]   = useState("");
  const [actionType, setActionType] = useState("");
  const [offset,     setOffset]     = useState(0);
  const LIMIT = 25;

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string | number> = { limit: LIMIT, offset };
      if (search)     params.trace_id    = search;
      if (decision)   params.decision    = decision;
      if (actionType) params.action_type = actionType;
      const data = await auditApi.list(params);
      setEvents(data.items);
      setTotal(data.total);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load audit events");
    } finally {
      setLoading(false);
    }
  }, [search, decision, actionType, offset]);

  useEffect(() => { void load(); }, [load]);

  async function openTrace(traceId: string) {
    setSelected(traceId);
    setTlLoading(true);
    try {
      const tl = await auditApi.trace(traceId);
      setTimeline(tl);
    } catch {
      setTimeline(null);
    } finally {
      setTlLoading(false);
    }
  }

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-[22px] font-bold text-[#0f172a] tracking-tight">Audit Explorer</h1>
        <p className="text-[13px] text-[#94a3b8] mt-1">
          Trace every governance decision from identity verification to execution.
        </p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl border border-[#e4e7ec] shadow-card p-4 flex flex-wrap gap-3 items-end">
        <div className="flex-1 min-w-[160px]">
          <label className="block text-[10px] font-semibold text-[#94a3b8] uppercase tracking-wide mb-1">Trace ID</label>
          <input
            type="text"
            value={search}
            onChange={e => { setSearch(e.target.value); setOffset(0); }}
            placeholder="trc_…"
            className="w-full text-[12px] font-mono bg-[#f7f8fa] border border-[#e4e7ec] rounded-lg px-3 py-2 text-[#0f172a] placeholder-[#cbd5e1] focus:outline-none focus:border-aegis-400 transition-colors"
          />
        </div>
        <div className="min-w-[140px]">
          <label className="block text-[10px] font-semibold text-[#94a3b8] uppercase tracking-wide mb-1">Decision</label>
          <select
            value={decision}
            onChange={e => { setDecision(e.target.value); setOffset(0); }}
            className="w-full text-[12px] bg-[#f7f8fa] border border-[#e4e7ec] rounded-lg px-3 py-2 text-[#475569] focus:outline-none focus:border-aegis-400 transition-colors"
          >
            {DECISIONS.map(d => <option key={d} value={d}>{d || "All decisions"}</option>)}
          </select>
        </div>
        <div className="min-w-[180px]">
          <label className="block text-[10px] font-semibold text-[#94a3b8] uppercase tracking-wide mb-1">Action</label>
          <select
            value={actionType}
            onChange={e => { setActionType(e.target.value); setOffset(0); }}
            className="w-full text-[12px] bg-[#f7f8fa] border border-[#e4e7ec] rounded-lg px-3 py-2 text-[#475569] focus:outline-none focus:border-aegis-400 transition-colors"
          >
            {ACTION_TYPES.map(a => <option key={a} value={a}>{a || "All actions"}</option>)}
          </select>
        </div>
        <button
          onClick={() => { setSearch(""); setDecision(""); setActionType(""); setOffset(0); }}
          className="px-3 py-2 text-[12px] text-[#475569] border border-[#e4e7ec] rounded-lg hover:bg-[#f7f8fa] transition-colors"
        >
          Reset
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-5">
        {/* Table (3/5) */}
        <div className="lg:col-span-3">
          <div className="bg-white rounded-xl border border-[#e4e7ec] shadow-card overflow-hidden">
            {/* Count */}
            {!loading && !error && (
              <div className="px-5 py-3 border-b border-[#f0f2f5] text-[12px] text-[#94a3b8]">
                {total} event{total !== 1 ? "s" : ""}
              </div>
            )}

            {error ? (
              <ErrorState message={error} onRetry={load} />
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-[12px]">
                  <thead>
                    <tr className="border-b border-[#f0f2f5]">
                      {["Time", "Trace", "Agent", "Action", "Decision"].map(h => (
                        <th key={h} className="text-left px-4 py-3 text-[11px] font-semibold text-[#94a3b8] uppercase tracking-wide">
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#f7f8fa]">
                    {loading ? (
                      Array.from({ length: 8 }).map((_, i) => <SkeletonRow key={i} cols={5} />)
                    ) : events.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="py-16">
                          <EmptyState
                            title="No governance events"
                            description="Run an agent request to generate your first governance trace."
                          />
                        </td>
                      </tr>
                    ) : (
                      events.map(evt => (
                        <tr
                          key={evt.id}
                          className={`hover:bg-[#f7f8fa] transition-colors cursor-pointer ${selected === evt.trace_id ? "bg-aegis-50" : ""}`}
                          onClick={() => openTrace(evt.trace_id)}
                        >
                          <td className="px-4 py-2.5 text-[11px] text-[#94a3b8] font-mono whitespace-nowrap">
                            {timeAgo(evt.created_at)}
                          </td>
                          <td className="px-4 py-2.5">
                            <span className="font-mono text-[11px] text-[#475569]">{evt.trace_id.slice(-12)}</span>
                          </td>
                          <td className="px-4 py-2.5 text-[#475569]">{agentDisplayName(evt.agent_id)}</td>
                          <td className="px-4 py-2.5">
                            <span className="font-mono text-[11px] text-[#475569]">
                              {evt.action_type.replace(/_/g, "_")}
                            </span>
                          </td>
                          <td className="px-4 py-2.5">
                            <Badge value={evt.decision} showDot size="xs" />
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            )}

            {/* Pagination */}
            {!loading && total > LIMIT && (
              <div className="px-5 py-3 border-t border-[#f0f2f5] flex items-center justify-between text-[12px]">
                <span className="text-[#94a3b8]">
                  {offset + 1}–{Math.min(offset + LIMIT, total)} of {total}
                </span>
                <div className="flex gap-2">
                  <button
                    disabled={offset === 0}
                    onClick={() => setOffset(Math.max(0, offset - LIMIT))}
                    className="px-3 py-1.5 border border-[#e4e7ec] rounded-lg text-[#475569] disabled:opacity-40 hover:border-aegis-300 transition-colors"
                  >
                    ← Prev
                  </button>
                  <button
                    disabled={offset + LIMIT >= total}
                    onClick={() => setOffset(offset + LIMIT)}
                    className="px-3 py-1.5 border border-[#e4e7ec] rounded-lg text-[#475569] disabled:opacity-40 hover:border-aegis-300 transition-colors"
                  >
                    Next →
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Timeline detail (2/5) */}
        <div className="lg:col-span-2">
          {!selected ? (
            <div className="bg-white rounded-xl border border-[#e4e7ec] shadow-card h-full flex items-center justify-center p-8">
              <div className="text-center">
                <div className="text-[13px] text-[#94a3b8]">Select an event</div>
                <div className="text-[12px] text-[#cbd5e1] mt-1">to view the full governance trace</div>
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-xl border border-[#e4e7ec] shadow-card overflow-hidden">
              <div className="px-5 py-4 border-b border-[#f0f2f5]">
                <div className="text-[13px] font-semibold text-[#0f172a]">Governance Trace</div>
                <div className="text-[11px] font-mono text-[#94a3b8] mt-0.5 break-all">{selected}</div>
              </div>

              {/* Summary */}
              {timeline && !tlLoading && (
                <div className="px-5 py-3 bg-[#f7f8fa] border-b border-[#f0f2f5] flex flex-wrap gap-3">
                  <div>
                    <div className="text-[10px] text-[#94a3b8] uppercase tracking-wide">Final Decision</div>
                    <Badge value={timeline.summary.final_decision} showDot size="xs" />
                  </div>
                  <div>
                    <div className="text-[10px] text-[#94a3b8] uppercase tracking-wide">Events</div>
                    <div className="text-[13px] font-semibold text-[#0f172a]">{timeline.summary.total_events}</div>
                  </div>
                  {timeline.summary.agent_ids.length > 0 && (
                    <div>
                      <div className="text-[10px] text-[#94a3b8] uppercase tracking-wide">Agent</div>
                      <div className="text-[12px] text-[#475569]">{agentDisplayName(timeline.summary.agent_ids[0])}</div>
                    </div>
                  )}
                </div>
              )}

              <div className="p-5">
                {tlLoading ? (
                  <div className="space-y-4">
                    {Array.from({ length: 4 }).map((_, i) => (
                      <div key={i} className="flex gap-3">
                        <Skeleton className="w-8 h-8 rounded-full flex-shrink-0" />
                        <div className="flex-1 space-y-2 pt-1">
                          <Skeleton className="h-3 w-2/3" />
                          <Skeleton className="h-2 w-1/2" />
                        </div>
                      </div>
                    ))}
                  </div>
                ) : timeline ? (
                  <GovernanceTimeline events={timeline.events} />
                ) : (
                  <div className="text-[13px] text-[#94a3b8] text-center py-4">Failed to load trace.</div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
