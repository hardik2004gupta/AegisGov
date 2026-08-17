"use client";

import { useState } from "react";
import { Topbar } from "@/components/layout/Topbar";
import { DecisionBadge, RiskBadge } from "@/components/ui/Badge";
import { GovernanceTimeline } from "@/components/governance/GovernanceTimeline";
import { getAuditEvents } from "@/lib/mock-api";
import { TRACE_EVENTS } from "@/data/audit";
import { fmtDateTime, timeAgo } from "@/lib/utils";
import type { AuditEvent } from "@/lib/types";

export default function AuditPage() {
  const events = getAuditEvents();
  const [selectedTrace, setSelectedTrace] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  const filtered = events.filter((e) => {
    const q = search.toLowerCase();
    return (
      !q ||
      e.traceId.includes(q) ||
      e.userName.toLowerCase().includes(q) ||
      e.agentId.toLowerCase().includes(q) ||
      (e.toolName?.includes(q) ?? false) ||
      e.decision.toLowerCase().includes(q)
    );
  });

  const traceEvents: AuditEvent[] =
    selectedTrace && TRACE_EVENTS[selectedTrace]
      ? TRACE_EVENTS[selectedTrace]
      : selectedTrace
        ? events.filter((e) => e.traceId === selectedTrace)
        : [];

  return (
    <div>
      <Topbar
        title="Audit Explorer"
        subtitle="Every governance decision — immutable, queryable, trace-linked"
      />

      <div className="p-6">
        <div className="flex gap-6">
          {/* table */}
          <div className="flex-1 min-w-0">
            <div className="mb-4">
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search by trace ID, user, agent, tool, or decision…"
                className="w-full max-w-md px-4 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-700 placeholder-slate-400 bg-white"
              />
            </div>

            <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-200 bg-slate-50">
                      <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                        Time
                      </th>
                      <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                        Trace ID
                      </th>
                      <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                        User
                      </th>
                      <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                        Agent
                      </th>
                      <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                        Tool
                      </th>
                      <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                        Decision
                      </th>
                      <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                        Risk
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.map((evt) => (
                      <tr
                        key={evt.id}
                        onClick={() =>
                          setSelectedTrace(
                            selectedTrace === evt.traceId ? null : evt.traceId
                          )
                        }
                        className={`border-b border-slate-100 last:border-0 cursor-pointer transition-colors ${
                          selectedTrace === evt.traceId
                            ? "bg-blue-50"
                            : "hover:bg-slate-50"
                        }`}
                      >
                        <td className="px-4 py-3 text-xs text-slate-500 whitespace-nowrap" suppressHydrationWarning>
                          <div suppressHydrationWarning>{timeAgo(evt.createdAt)}</div>
                          <div className="text-slate-400" suppressHydrationWarning>
                            {fmtDateTime(evt.createdAt)}
                          </div>
                        </td>
                        <td className="px-4 py-3 font-mono text-xs text-slate-600 whitespace-nowrap">
                          {evt.traceId.slice(-8)}
                        </td>
                        <td className="px-4 py-3 text-xs">
                          <div className="font-medium text-slate-700">
                            {evt.userName}
                          </div>
                        </td>
                        <td className="px-4 py-3 font-mono text-xs text-slate-600 whitespace-nowrap">
                          {evt.agentId}
                        </td>
                        <td className="px-4 py-3 font-mono text-xs text-slate-600 whitespace-nowrap">
                          {evt.toolName ?? "—"}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <DecisionBadge decision={evt.decision} />
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          {evt.riskLevel ? (
                            <RiskBadge risk={evt.riskLevel} />
                          ) : (
                            <span className="text-slate-400">—</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {filtered.length === 0 && (
                <div className="px-4 py-12 text-center text-sm text-slate-400">
                  No events match your search.
                </div>
              )}
            </div>
          </div>

          {/* trace detail */}
          {selectedTrace && (
            <div className="w-72 flex-shrink-0">
              <div className="bg-white border border-slate-200 rounded-xl p-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-semibold text-slate-700">
                    Trace Detail
                  </h3>
                  <button
                    onClick={() => setSelectedTrace(null)}
                    className="text-slate-400 hover:text-slate-600 text-lg leading-none"
                  >
                    ×
                  </button>
                </div>
                <div className="font-mono text-xs text-slate-500 mb-4">
                  {selectedTrace}
                </div>
                <GovernanceTimeline events={traceEvents} />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
