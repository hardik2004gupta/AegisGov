"use client";

import { useEffect, useState, useCallback } from "react";
import { runtime as runtimeApi, health as healthApi, audit as auditApi } from "@/lib/api";
import type { RuntimeStatus, HealthResponse, AuditEvent } from "@/lib/types";
import { Badge } from "@/components/ui/Badge";
import { CardSkeleton, Skeleton } from "@/components/ui/Skeleton";
import { ErrorState } from "@/components/ui/ErrorState";
import { timeAgo, agentDisplayName } from "@/lib/utils";

export default function RuntimePage() {
  const [stats,   setStats]   = useState<RuntimeStatus | null>(null);
  const [health_, setHealth]  = useState<HealthResponse | null>(null);
  const [denied,  setDenied]  = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [h, d] = await Promise.allSettled([
        healthApi.get(),
        auditApi.list({ decision: "DENIED", limit: 10 }),
      ]);
      if (h.status === "fulfilled") setHealth(h.value);
      if (d.status === "fulfilled") setDenied(d.value.items);

      // runtime/status requires auth — attempt without token first (will 401)
      try {
        const s = await runtimeApi.status();
        setStats(s);
      } catch {
        // no token available; leave stats null
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load runtime data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-[22px] font-bold text-[#0f172a] tracking-tight">Runtime</h1>
        <p className="text-[13px] text-[#94a3b8] mt-1">
          Monitor agent execution, governance decisions, and runtime safety limits.
        </p>
      </div>

      {error && <ErrorState message={error} onRetry={load} />}

      {/* KPI row */}
      {loading ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          {Array.from({ length: 5 }).map((_, i) => <CardSkeleton key={i} />)}
        </div>
      ) : stats ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          {[
            { label: "Total Decisions", value: stats.summary.total_decisions, color: "text-[#0f172a]" },
            { label: "Allowed",         value: stats.summary.allowed,         color: "text-emerald-600" },
            { label: "Denied",          value: stats.summary.denied,          color: "text-red-600" },
            { label: "Blocked",         value: stats.summary.blocked,         color: "text-orange-600" },
            { label: "Pending",         value: stats.approvals.pending,       color: "text-amber-600" },
          ].map(c => (
            <div key={c.label} className="bg-white rounded-xl border border-[#e4e7ec] shadow-card p-4">
              <div className={`text-[28px] font-bold tabular ${c.color}`}>{c.value}</div>
              <div className="text-[11px] text-[#94a3b8] mt-1">{c.label}</div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-[#e4e7ec] shadow-card p-4 text-[13px] text-[#94a3b8]">
          Runtime metrics require an authenticated token. Use the Agent Console with a valid JWT first.
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Decision distribution */}
        {stats && (
          <div className="bg-white rounded-xl border border-[#e4e7ec] shadow-card p-5">
            <div className="text-[12px] font-semibold text-[#0f172a] uppercase tracking-wide mb-4">
              Decision Distribution
            </div>
            <DecisionChart stats={stats} />
          </div>
        )}

        {/* Approval distribution */}
        {stats && (
          <div className="bg-white rounded-xl border border-[#e4e7ec] shadow-card p-5">
            <div className="text-[12px] font-semibold text-[#0f172a] uppercase tracking-wide mb-4">
              Approvals
            </div>
            <ApprovalChart stats={stats} />

            {/* Runtime limits */}
            <div className="mt-6">
              <div className="text-[12px] font-semibold text-[#0f172a] uppercase tracking-wide mb-3">
                Safety Limits
              </div>
              <div className="space-y-2 text-[12px]">
                {[
                  { label: "Max tool calls",          value: stats.limits.max_tool_calls },
                  { label: "Max agent handoffs",      value: stats.limits.max_agent_handoffs },
                  { label: "Max execution time",      value: `${stats.limits.max_execution_time_seconds}s` },
                  { label: "Max identical calls",     value: stats.limits.max_identical_tool_calls },
                ].map(l => (
                  <div key={l.label} className="flex justify-between items-center py-1 border-b border-[#f7f8fa]">
                    <span className="text-[#475569]">{l.label}</span>
                    <span className="text-[#0f172a] font-semibold tabular">{l.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* System health */}
        <div className="bg-white rounded-xl border border-[#e4e7ec] shadow-card p-5">
          <div className="text-[12px] font-semibold text-[#0f172a] uppercase tracking-wide mb-4">
            System Health
          </div>
          {loading ? (
            <div className="space-y-3">
              {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-6 w-full" />)}
            </div>
          ) : health_ ? (
            <>
              <div className="space-y-2">
                {Object.entries(health_.dependencies).map(([name, dep]) => (
                  <HealthRow key={name} name={name} status={dep.status} latency={dep.latency_ms} />
                ))}
              </div>
              <div className="mt-4 pt-4 border-t border-[#f0f2f5]">
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${health_.status === "healthy" ? "bg-emerald-500" : "bg-amber-500"}`} />
                  <span className="text-[13px] font-medium text-[#0f172a]">
                    {health_.status === "healthy" ? "All systems operational" : "Degraded"}
                  </span>
                </div>
                <div className="text-[11px] text-[#94a3b8] mt-1">
                  {health_.service} v{health_.version}
                </div>
              </div>
            </>
          ) : (
            <ErrorState message="Health check unavailable" onRetry={load} />
          )}
        </div>
      </div>

      {/* Security events */}
      <div className="bg-white rounded-xl border border-[#e4e7ec] shadow-card overflow-hidden">
        <div className="px-5 py-4 border-b border-[#f0f2f5]">
          <h2 className="text-[13px] font-semibold text-[#0f172a]">Security Events</h2>
          <p className="text-[12px] text-[#94a3b8] mt-0.5">Most recent denied and blocked actions.</p>
        </div>
        {loading ? (
          <div className="p-5 space-y-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="flex gap-3">
                <Skeleton className="w-2 h-2 rounded-full mt-2 flex-shrink-0" />
                <Skeleton className="h-4 flex-1" />
              </div>
            ))}
          </div>
        ) : denied.length === 0 ? (
          <div className="px-5 py-10 text-center">
            <div className="text-[13px] text-[#94a3b8]">No denied events recorded.</div>
          </div>
        ) : (
          <div className="divide-y divide-[#f7f8fa]">
            {denied.map(evt => (
              <div key={evt.id} className="px-5 py-3 flex items-start gap-3">
                <div className="mt-1.5 w-2 h-2 rounded-full bg-red-500 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-[12px] font-medium text-[#0f172a]">{agentDisplayName(evt.agent_id)}</span>
                    <span className="text-[11px] font-mono text-[#94a3b8]">{evt.action_type.replace(/_/g," ").toLowerCase()}</span>
                    <Badge value={evt.decision} size="xs" />
                  </div>
                  {evt.reason && <div className="text-[11px] text-[#94a3b8] mt-0.5">{evt.reason}</div>}
                  <div className="text-[10px] text-[#cbd5e1] mt-0.5 font-mono">{evt.trace_id} · {timeAgo(evt.created_at)}</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function DecisionChart({ stats }: { stats: RuntimeStatus }) {
  const total = stats.summary.total_decisions || 1;
  const bars = [
    { label: "Allowed", value: stats.summary.allowed, color: "bg-emerald-500", textColor: "text-emerald-600" },
    { label: "Denied",  value: stats.summary.denied,  color: "bg-red-400",     textColor: "text-red-600" },
    { label: "Blocked", value: stats.summary.blocked, color: "bg-orange-400",  textColor: "text-orange-600" },
  ];
  return (
    <div className="space-y-3">
      {bars.map(b => (
        <div key={b.label}>
          <div className="flex justify-between items-center mb-1">
            <span className="text-[12px] text-[#475569]">{b.label}</span>
            <span className={`text-[12px] font-semibold tabular ${b.textColor}`}>{b.value}</span>
          </div>
          <div className="h-2 bg-[#f0f2f5] rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${b.color}`}
              style={{ width: `${Math.round((b.value / total) * 100)}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

function ApprovalChart({ stats }: { stats: RuntimeStatus }) {
  const total = (stats.approvals.pending + stats.approvals.approved + stats.approvals.rejected) || 1;
  const bars = [
    { label: "Pending",  value: stats.approvals.pending,  color: "bg-amber-400",   textColor: "text-amber-600" },
    { label: "Approved", value: stats.approvals.approved, color: "bg-emerald-500", textColor: "text-emerald-600" },
    { label: "Rejected", value: stats.approvals.rejected, color: "bg-red-400",     textColor: "text-red-600" },
  ];
  return (
    <div className="space-y-3">
      {bars.map(b => (
        <div key={b.label}>
          <div className="flex justify-between items-center mb-1">
            <span className="text-[12px] text-[#475569]">{b.label}</span>
            <span className={`text-[12px] font-semibold tabular ${b.textColor}`}>{b.value}</span>
          </div>
          <div className="h-2 bg-[#f0f2f5] rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${b.color}`}
              style={{ width: `${Math.round((b.value / total) * 100)}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

function HealthRow({ name, status, latency }: { name: string; status: string; latency?: number }) {
  const healthy     = status === "healthy";
  const unconfigured = status === "unconfigured";
  return (
    <div className="flex items-center justify-between py-1.5 border-b border-[#f7f8fa] last:border-0">
      <span className="text-[13px] text-[#475569] capitalize">{name}</span>
      <div className="flex items-center gap-2">
        {latency && <span className="text-[11px] text-[#94a3b8] tabular">{latency.toFixed(0)}ms</span>}
        <div className="flex items-center gap-1.5">
          <span className={`w-1.5 h-1.5 rounded-full ${healthy ? "bg-emerald-500" : unconfigured ? "bg-slate-300" : "bg-amber-500"}`} />
          <span className={`text-[11px] font-medium ${healthy ? "text-emerald-600" : unconfigured ? "text-[#94a3b8]" : "text-amber-600"}`}>
            {status.charAt(0).toUpperCase() + status.slice(1)}
          </span>
        </div>
      </div>
    </div>
  );
}
