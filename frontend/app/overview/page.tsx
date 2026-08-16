"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { runtime, health, audit } from "@/lib/api";
import type { RuntimeStatus, HealthResponse, AuditEvent } from "@/lib/types";
import { Badge } from "@/components/ui/Badge";
import { Skeleton, CardSkeleton } from "@/components/ui/Skeleton";
import { GovernancePipeline } from "@/components/governance/GovernancePipeline";
import type { PipelineStep } from "@/components/governance/GovernancePipeline";
import { timeAgo, agentDisplayName } from "@/lib/utils";

const DEMO_TOKEN = ""; // Bearer token not required for read endpoints

export default function OverviewPage() {
  const [stats,   setStats]   = useState<RuntimeStatus | null>(null);
  const [health_, setHealth]  = useState<HealthResponse | null>(null);
  const [events,  setEvents]  = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    try {
      const [h, a] = await Promise.allSettled([
        health.get(),
        audit.list({ limit: 10 }),
      ]);
      if (h.status === "fulfilled") setHealth(h.value);
      if (a.status === "fulfilled") setEvents(a.value.items);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { void load(); }, []);

  const PIPELINE_DEMO: PipelineStep[] = [
    { id: "identity", label: "Identity",  state: "success", detail: "JWT verified" },
    { id: "agent",    label: "Agent",     state: "success", detail: "Billing Agent" },
    { id: "policy",   label: "Policy",    state: "success", detail: "ALLOWED" },
    { id: "risk",     label: "Risk",      state: "warning", detail: "HIGH" },
    { id: "approval", label: "Approval",  state: "warning", detail: "Awaiting review" },
    { id: "exec",     label: "Execution", state: "idle" },
    { id: "audit",    label: "Audit",     state: "idle" },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-[22px] font-bold text-[#0f172a] tracking-tight">Governance Overview</h1>
        <p className="text-[13px] text-[#94a3b8] mt-1">
          Real-time visibility into agent decisions, policy enforcement, and secure execution.
        </p>
      </div>

      {/* Top row: metrics + pipeline */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Metrics 2/3 width */}
        <div className="lg:col-span-2 space-y-4">
          {loading ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {Array.from({ length: 5 }).map((_, i) => <CardSkeleton key={i} />)}
            </div>
          ) : (
            <StatsGrid stats={stats} />
          )}

          {/* Recent activity */}
          <div className="bg-white rounded-xl border border-[#e4e7ec] shadow-card overflow-hidden">
            <div className="px-5 py-4 border-b border-[#f0f2f5] flex items-center justify-between">
              <h2 className="text-[13px] font-semibold text-[#0f172a]">Recent Governance Activity</h2>
              <Link href="/audit" className="text-[12px] text-aegis-600 hover:text-aegis-700 font-medium">
                View all →
              </Link>
            </div>
            {loading ? (
              <div className="px-5 py-4 space-y-3">
                {Array.from({ length: 4 }).map((_, i) => (
                  <div key={i} className="flex gap-3">
                    <Skeleton className="w-2 h-2 rounded-full mt-1.5 flex-shrink-0" />
                    <div className="flex-1 space-y-1.5">
                      <Skeleton className="h-3 w-3/4" />
                      <Skeleton className="h-2 w-1/2" />
                    </div>
                  </div>
                ))}
              </div>
            ) : events.length === 0 ? (
              <div className="px-5 py-10 text-center">
                <div className="text-[13px] text-[#94a3b8]">No governance events yet.</div>
                <div className="text-[12px] text-[#cbd5e1] mt-1">
                  Run an agent request to generate your first trace.
                </div>
              </div>
            ) : (
              <div className="divide-y divide-[#f0f2f5]">
                {events.map((evt) => (
                  <ActivityRow key={evt.id} event={evt} />
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right: pipeline + health 1/3 width */}
        <div className="space-y-4">
          {/* Pipeline */}
          <div className="bg-white rounded-xl border border-[#e4e7ec] shadow-card p-5">
            <div className="text-[12px] font-semibold text-[#0f172a] uppercase tracking-wide mb-4">
              Governance Pipeline
            </div>
            <GovernancePipeline steps={PIPELINE_DEMO} />
          </div>

          {/* Health */}
          {health_ && (
            <div className="bg-white rounded-xl border border-[#e4e7ec] shadow-card p-5">
              <div className="text-[12px] font-semibold text-[#0f172a] uppercase tracking-wide mb-3">
                System Health
              </div>
              <div className="space-y-2">
                {Object.entries(health_.dependencies).map(([name, dep]) => (
                  <HealthRow key={name} name={name} status={dep.status} />
                ))}
              </div>
            </div>
          )}

          {/* Quick links */}
          <div className="bg-white rounded-xl border border-[#e4e7ec] shadow-card p-5">
            <div className="text-[12px] font-semibold text-[#0f172a] uppercase tracking-wide mb-3">
              Quick Actions
            </div>
            <div className="space-y-2">
              {[
                { href: "/agent",     label: "Run an agent request",   icon: "→" },
                { href: "/approvals", label: "Review pending approvals", icon: "✓" },
                { href: "/audit",     label: "Explore audit trail",    icon: "⊙" },
                { href: "/runtime",   label: "Runtime metrics",        icon: "◷" },
              ].map((l) => (
                <Link
                  key={l.href}
                  href={l.href}
                  className="flex items-center gap-2 text-[13px] text-[#475569] hover:text-[#3b5bdb] py-1 transition-colors"
                >
                  <span className="text-[10px] w-4 text-center">{l.icon}</span>
                  {l.label}
                </Link>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatsGrid({ stats }: { stats: RuntimeStatus | null }) {
  const s = stats?.summary;
  const a = stats?.approvals;
  const cards = [
    { label: "Tool Calls",       value: s?.total_decisions ?? 0,    color: "text-[#0f172a]" },
    { label: "Allowed",          value: s?.allowed ?? 0,            color: "text-emerald-600" },
    { label: "Denied",           value: s?.denied ?? 0,             color: "text-red-600" },
    { label: "Blocked",          value: s?.blocked ?? 0,            color: "text-orange-600" },
    { label: "Pending Approvals",value: a?.pending ?? (s?.pending_approvals ?? 0), color: "text-amber-600" },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
      {cards.map((c) => (
        <div key={c.label} className="bg-white rounded-xl border border-[#e4e7ec] shadow-card p-4">
          <div className={`text-[28px] font-bold tabular ${c.color}`}>{c.value}</div>
          <div className="text-[11px] text-[#94a3b8] mt-1">{c.label}</div>
        </div>
      ))}
    </div>
  );
}

function ActivityRow({ event }: { event: AuditEvent }) {
  return (
    <div className="px-5 py-3 flex items-start gap-3 hover:bg-[#f7f8fa] transition-colors">
      <div className="mt-1.5">
        <DecisionDot decision={event.decision} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-[12px] font-medium text-[#0f172a]">
            {agentDisplayName(event.agent_id)}
          </span>
          <span className="text-[11px] font-mono text-[#94a3b8]">
            {event.action_type.replace(/_/g, " ").toLowerCase()}
          </span>
          <Badge value={event.decision} size="xs" />
        </div>
        <div className="flex items-center gap-2 mt-0.5">
          <span className="text-[11px] text-[#94a3b8] font-mono truncate max-w-[120px]">{event.trace_id}</span>
          <span className="text-[11px] text-[#cbd5e1]">{timeAgo(event.created_at)}</span>
        </div>
      </div>
    </div>
  );
}

function DecisionDot({ decision }: { decision: string }) {
  const colors: Record<string, string> = {
    ALLOWED:  "bg-emerald-500",
    APPROVED: "bg-emerald-500",
    DENIED:   "bg-red-500",
    REJECTED: "bg-red-500",
    BLOCKED:  "bg-orange-500",
    PENDING:  "bg-amber-500",
  };
  return (
    <span className={`w-2 h-2 rounded-full block ${colors[decision] ?? "bg-slate-400"}`} />
  );
}

function HealthRow({ name, status }: { name: string; status: string }) {
  const healthy = status === "healthy";
  const unconfigured = status === "unconfigured";
  return (
    <div className="flex items-center justify-between">
      <span className="text-[13px] text-[#475569] capitalize">{name}</span>
      <div className="flex items-center gap-1.5">
        <span
          className={`w-1.5 h-1.5 rounded-full ${
            healthy ? "bg-emerald-500" : unconfigured ? "bg-slate-300" : "bg-amber-500"
          }`}
        />
        <span className={`text-[11px] ${healthy ? "text-emerald-600" : unconfigured ? "text-[#94a3b8]" : "text-amber-600"}`}>
          {status.charAt(0).toUpperCase() + status.slice(1)}
        </span>
      </div>
    </div>
  );
}
