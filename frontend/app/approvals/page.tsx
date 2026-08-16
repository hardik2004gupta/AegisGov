"use client";

import { useEffect, useState, useCallback } from "react";
import { approvals as approvalsApi } from "@/lib/api";
import type { ApprovalItem } from "@/lib/types";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { timeAgo, agentDisplayName } from "@/lib/utils";

export default function ApprovalsPage() {
  const [items,    setItems]   = useState<ApprovalItem[]>([]);
  const [loading,  setLoading] = useState(true);
  const [error,    setError]   = useState<string | null>(null);
  const [filter,   setFilter]  = useState<"ALL" | "PENDING" | "APPROVED" | "REJECTED">("ALL");
  const [selected, setSelected]= useState<ApprovalItem | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = filter === "ALL"
        ? { pending_only: false, limit: 50 }
        : filter === "PENDING"
        ? { pending_only: true, limit: 50 }
        : { status: filter, pending_only: false, limit: 50 };
      const data = await approvalsApi.list(params);
      setItems(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load approvals");
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => { void load(); }, [load]);

  const counts = {
    pending:  items.filter(i => i.status === "PENDING").length,
    approved: items.filter(i => i.status === "APPROVED").length,
    rejected: items.filter(i => i.status === "REJECTED").length,
    critical: items.filter(i => i.risk_level === "CRITICAL").length,
  };

  function onResolved() {
    setSelected(null);
    void load();
  }

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-[22px] font-bold text-[#0f172a] tracking-tight">Approval Center</h1>
        <p className="text-[13px] text-[#94a3b8] mt-1">
          Review high-risk agent actions before they execute.
        </p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: "Pending",  value: counts.pending,  color: "text-amber-600",  bg: "bg-amber-50 border-amber-200" },
          { label: "Approved", value: counts.approved, color: "text-emerald-600",bg: "bg-emerald-50 border-emerald-200" },
          { label: "Rejected", value: counts.rejected, color: "text-red-600",    bg: "bg-red-50 border-red-200" },
          { label: "Critical", value: counts.critical, color: "text-red-800",    bg: "bg-red-100 border-red-300" },
        ].map(c => (
          <div key={c.label} className={`rounded-xl border p-4 ${c.bg}`}>
            <div className={`text-[26px] font-bold tabular ${c.color}`}>{c.value}</div>
            <div className="text-[11px] text-[#94a3b8] mt-1">{c.label}</div>
          </div>
        ))}
      </div>

      {/* Filter tabs */}
      <div className="flex gap-1">
        {(["ALL", "PENDING", "APPROVED", "REJECTED"] as const).map(f => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={[
              "px-3 py-1.5 text-[12px] font-medium rounded-lg transition-colors",
              filter === f
                ? "bg-aegis-600 text-white"
                : "bg-white border border-[#e4e7ec] text-[#475569] hover:border-aegis-300 hover:text-aegis-600",
            ].join(" ")}
          >
            {f}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-[#e4e7ec] shadow-card overflow-hidden">
        {error ? (
          <ErrorState message={error} onRetry={load} />
        ) : loading ? (
          <div className="p-6 space-y-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="flex gap-3">
                <Skeleton className="h-3 w-16" />
                <Skeleton className="h-3 w-32" />
                <Skeleton className="h-3 w-24" />
                <Skeleton className="h-3 w-20" />
                <Skeleton className="h-3 w-16" />
              </div>
            ))}
          </div>
        ) : items.length === 0 ? (
          <EmptyState
            icon={<ChecklistIcon />}
            title="No approvals"
            description="High-risk actions requiring human review will appear here."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-[12px]">
              <thead>
                <tr className="border-b border-[#f0f2f5]">
                  {["Risk", "Tool", "Agent", "User", "Created", "Status", ""].map(h => (
                    <th key={h} className="text-left px-4 py-3 text-[11px] font-semibold text-[#94a3b8] uppercase tracking-wide">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[#f7f8fa]">
                {items.map(item => (
                  <ApprovalRow
                    key={item.approval_id}
                    item={item}
                    onSelect={() => setSelected(item)}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Detail drawer */}
      {selected && (
        <ApprovalModal
          item={selected}
          onClose={() => setSelected(null)}
          onResolved={onResolved}
        />
      )}
    </div>
  );
}

function ApprovalRow({ item, onSelect }: { item: ApprovalItem; onSelect: () => void }) {
  return (
    <tr className="hover:bg-[#f7f8fa] transition-colors cursor-pointer" onClick={onSelect}>
      <td className="px-4 py-3">
        <Badge value={item.risk_level} />
      </td>
      <td className="px-4 py-3">
        <span className="font-mono text-[#0f172a]">{item.tool_name}</span>
      </td>
      <td className="px-4 py-3 text-[#475569]">{agentDisplayName(item.agent_id)}</td>
      <td className="px-4 py-3 text-[#475569]">{item.user_id}</td>
      <td className="px-4 py-3 text-[#94a3b8]">{timeAgo(item.created_at)}</td>
      <td className="px-4 py-3">
        <Badge value={item.status} showDot />
      </td>
      <td className="px-4 py-3">
        <span className="text-aegis-600 hover:text-aegis-700 font-medium">Review →</span>
      </td>
    </tr>
  );
}

function ApprovalModal({ item, onClose, onResolved }: {
  item: ApprovalItem;
  onClose: () => void;
  onResolved: () => void;
}) {
  const [token,   setToken]   = useState("");
  const [reason,  setReason]  = useState("");
  const [confirm, setConfirm] = useState<"APPROVED" | "REJECTED" | null>(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState<string | null>(null);

  async function resolve(decision: "APPROVED" | "REJECTED") {
    if (!token.trim()) { setError("Bearer token required"); return; }
    setLoading(true);
    setError(null);
    try {
      await approvalsApi.resolve(item.approval_id, decision, reason || "Manual review", token);
      onResolved();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to resolve");
    } finally {
      setLoading(false);
      setConfirm(null);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/20 backdrop-blur-sm" role="dialog" aria-modal="true">
      <div className="bg-white rounded-2xl border border-[#e4e7ec] shadow-modal w-full max-w-lg animate-slide-up">
        {/* Header */}
        <div className="px-6 py-5 border-b border-[#f0f2f5] flex items-start justify-between">
          <div>
            <div className="text-[15px] font-bold text-[#0f172a]">Approval Request</div>
            <div className="text-[12px] text-[#94a3b8] mt-0.5 font-mono">{item.approval_id}</div>
          </div>
          <button onClick={onClose} className="text-[#94a3b8] hover:text-[#0f172a] p-1 rounded-lg hover:bg-[#f7f8fa] transition-colors" aria-label="Close">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/></svg>
          </button>
        </div>

        <div className="px-6 py-5 space-y-4">
          {/* Risk banner */}
          {item.risk_level === "CRITICAL" && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-3 flex items-center gap-2">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="text-red-500 flex-shrink-0">
                <path d="M8 2L14.5 13H1.5L8 2z" stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round"/>
                <path d="M8 6v3.5M8 11h.01" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/>
              </svg>
              <span className="text-[12px] font-semibold text-red-700">Critical Action — Irreversible</span>
            </div>
          )}

          {/* Details grid */}
          <div className="grid grid-cols-2 gap-3">
            <Detail label="Tool" value={item.tool_name} mono />
            <Detail label="Risk" value={<Badge value={item.risk_level} />} />
            <Detail label="Agent" value={agentDisplayName(item.agent_id)} />
            <Detail label="User" value={item.user_id} />
            <Detail label="Status" value={<Badge value={item.status} showDot />} />
            <Detail label="Created" value={timeAgo(item.created_at)} />
          </div>

          {/* Arguments */}
          <div>
            <div className="text-[11px] font-semibold text-[#94a3b8] uppercase tracking-wide mb-2">Arguments</div>
            <pre className="text-[11px] text-[#475569] bg-[#f7f8fa] border border-[#e4e7ec] rounded-lg p-3 overflow-x-auto">
              {JSON.stringify(item.arguments, null, 2)}
            </pre>
          </div>

          {/* Trace ID */}
          {item.trace_id && (
            <div className="text-[11px] text-[#94a3b8] font-mono">Trace: {item.trace_id}</div>
          )}

          {/* Token (only needed for PENDING) */}
          {item.status === "PENDING" && (
            <>
              <div>
                <label className="block text-[11px] font-semibold text-[#94a3b8] uppercase tracking-wide mb-1">
                  Admin JWT (required to resolve)
                </label>
                <input
                  type="text"
                  value={token}
                  onChange={e => setToken(e.target.value)}
                  placeholder="Bearer token…"
                  className="w-full text-[12px] font-mono bg-[#f7f8fa] border border-[#e4e7ec] rounded-lg px-3 py-2 text-[#0f172a] placeholder-[#cbd5e1] focus:outline-none focus:border-aegis-400 transition-colors"
                />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-[#94a3b8] uppercase tracking-wide mb-1">
                  Resolution note (optional)
                </label>
                <input
                  type="text"
                  value={reason}
                  onChange={e => setReason(e.target.value)}
                  placeholder="e.g. Verified administrative request"
                  className="w-full text-[12px] bg-[#f7f8fa] border border-[#e4e7ec] rounded-lg px-3 py-2 text-[#0f172a] placeholder-[#cbd5e1] focus:outline-none focus:border-aegis-400 transition-colors"
                />
              </div>
            </>
          )}

          {error && (
            <div className="text-[12px] text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">{error}</div>
          )}
        </div>

        {/* Actions */}
        {item.status === "PENDING" && (
          <div className="px-6 py-4 border-t border-[#f0f2f5] flex gap-2 justify-end">
            <button onClick={onClose} className="px-4 py-2 text-[13px] text-[#475569] bg-white border border-[#e4e7ec] rounded-lg hover:border-[#cdd2da] transition-colors">
              Cancel
            </button>
            {!confirm ? (
              <>
                <button
                  onClick={() => setConfirm("REJECTED")}
                  disabled={loading}
                  className="px-4 py-2 text-[13px] text-red-600 bg-red-50 border border-red-200 rounded-lg hover:bg-red-100 transition-colors disabled:opacity-40"
                >
                  Reject
                </button>
                <button
                  onClick={() => setConfirm("APPROVED")}
                  disabled={loading}
                  className="px-4 py-2 text-[13px] text-white bg-aegis-600 rounded-lg hover:bg-aegis-700 transition-colors disabled:opacity-40"
                >
                  Approve
                </button>
              </>
            ) : (
              <>
                <div className="flex-1 text-[12px] text-[#475569] flex items-center">
                  Confirm {confirm === "APPROVED" ? "approval" : "rejection"}?
                </div>
                <button onClick={() => setConfirm(null)} className="px-3 py-2 text-[12px] text-[#475569] border border-[#e4e7ec] rounded-lg hover:bg-[#f7f8fa] transition-colors">
                  Cancel
                </button>
                <button
                  onClick={() => resolve(confirm)}
                  disabled={loading}
                  className={[
                    "px-4 py-2 text-[13px] font-semibold text-white rounded-lg transition-colors disabled:opacity-40",
                    confirm === "APPROVED" ? "bg-aegis-600 hover:bg-aegis-700" : "bg-red-600 hover:bg-red-700",
                  ].join(" ")}
                >
                  {loading ? "…" : confirm === "APPROVED" ? "Confirm Approve" : "Confirm Reject"}
                </button>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function Detail({ label, value }: { label: string; value: React.ReactNode; mono?: boolean }) {
  return (
    <div>
      <div className="text-[10px] font-semibold text-[#94a3b8] uppercase tracking-wide mb-1">{label}</div>
      <div className="text-[13px] text-[#0f172a]">{value}</div>
    </div>
  );
}

function ChecklistIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <rect x="3" y="3" width="14" height="14" rx="3" stroke="currentColor" strokeWidth="1.4"/>
      <path d="M7 10l2 2 4-4" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}
