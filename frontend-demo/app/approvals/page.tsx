"use client";

import { useState, useCallback } from "react";
import { Topbar } from "@/components/layout/Topbar";
import { DecisionBadge, RiskBadge } from "@/components/ui/Badge";
import { Toast } from "@/components/ui/Toast";
import { getApprovals, resolveApproval } from "@/lib/mock-api";
import { fmtDateTime, timeAgo } from "@/lib/utils";
import type { Approval } from "@/lib/types";

function ApprovalCard({
  approval,
  onResolve,
}: {
  approval: Approval;
  onResolve: (
    id: string,
    decision: "APPROVED" | "REJECTED",
    reason: string
  ) => void;
}) {
  const [reason, setReason] = useState("");
  const [resolving, setResolving] = useState(false);

  const isPending = approval.status === "PENDING";

  const handleResolve = async (decision: "APPROVED" | "REJECTED") => {
    if (resolving) return;
    if (!reason.trim() && decision === "REJECTED") return;
    setResolving(true);
    await onResolve(approval.id, decision, reason || "Approved.");
    setResolving(false);
  };

  return (
    <div
      className={`bg-white border rounded-xl p-5 ${
        isPending
          ? approval.riskLevel === "CRITICAL"
            ? "border-red-200"
            : "border-amber-200"
          : approval.status === "APPROVED"
            ? "border-emerald-200"
            : "border-slate-200"
      }`}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-mono text-sm font-semibold text-slate-800">
              {approval.toolName}
            </span>
            <RiskBadge risk={approval.riskLevel} />
            <DecisionBadge decision={approval.status} />
          </div>

          <div className="mt-2 font-mono text-xs bg-slate-50 border border-slate-200 rounded px-2 py-1 text-slate-700 overflow-x-auto">
            {JSON.stringify(approval.toolArgs)}
          </div>

          <div className="mt-3 grid grid-cols-2 gap-2 text-xs text-slate-600">
            <div>
              <span className="text-slate-400">Requested by</span>
              <div className="font-medium">{approval.userName}</div>
              <div className="text-slate-400">{approval.userRole}</div>
            </div>
            <div>
              <span className="text-slate-400">Agent</span>
              <div className="font-mono">{approval.agentId}</div>
            </div>
            <div>
              <span className="text-slate-400">Created</span>
              <div suppressHydrationWarning>{timeAgo(approval.createdAt)}</div>
              <div className="text-slate-400" suppressHydrationWarning>
                {fmtDateTime(approval.createdAt)}
              </div>
            </div>
            <div>
              <span className="text-slate-400">Approval ID</span>
              <div className="font-mono">{approval.id.slice(-8)}</div>
            </div>
          </div>

          <div className="mt-2 text-xs text-slate-500 italic">
            {approval.reason}
          </div>

          {!isPending && approval.resolvedAt && (
            <div className="mt-3 pt-3 border-t border-slate-100 text-xs text-slate-500" suppressHydrationWarning>
              Resolved {timeAgo(approval.resolvedAt)} by {approval.resolvedBy}
              {approval.resolutionReason && (
                <div className="mt-1 italic">&ldquo;{approval.resolutionReason}&rdquo;</div>
              )}
            </div>
          )}
        </div>
      </div>

      {isPending && (
        <div className="mt-4 pt-4 border-t border-slate-100">
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Resolution reason (required for rejection)…"
            rows={2}
            className="w-full text-sm border border-slate-200 rounded-lg px-3 py-2 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-700 placeholder-slate-400"
          />
          <div className="flex gap-2 mt-2">
            <button
              onClick={() => handleResolve("APPROVED")}
              disabled={resolving}
              className="flex-1 py-2 text-sm font-semibold bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50 transition-colors"
            >
              Approve
            </button>
            <button
              onClick={() => handleResolve("REJECTED")}
              disabled={resolving || !reason.trim()}
              className="flex-1 py-2 text-sm font-semibold bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors"
            >
              Reject
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function ApprovalsPage() {
  const [approvals, setApprovals] = useState<Approval[]>(getApprovals());
  const [filter, setFilter] = useState<"ALL" | "PENDING" | "APPROVED" | "REJECTED">("ALL");
  const [toast, setToast] = useState<{
    msg: string;
    type: "success" | "error";
  } | null>(null);

  const handleResolve = useCallback(
    async (id: string, decision: "APPROVED" | "REJECTED", reason: string) => {
      await resolveApproval(id, decision, reason);
      setApprovals(getApprovals());
      setToast({
        msg: `Approval ${id.slice(-8)} ${decision.toLowerCase()}.`,
        type: decision === "APPROVED" ? "success" : "error",
      });
    },
    []
  );

  const filtered =
    filter === "ALL" ? approvals : approvals.filter((a) => a.status === filter);
  const pendingCount = approvals.filter((a) => a.status === "PENDING").length;

  return (
    <div>
      <Topbar
        title="Approval Queue"
        subtitle={`${pendingCount} action${pendingCount !== 1 ? "s" : ""} pending human review`}
      >
        <div className="flex gap-1">
          {(["ALL", "PENDING", "APPROVED", "REJECTED"] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                filter === f
                  ? "bg-blue-600 text-white"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      </Topbar>

      <div className="p-6">
        {filtered.length === 0 ? (
          <div className="bg-white border border-slate-200 rounded-xl p-12 text-center">
            <div className="text-3xl mb-3">✓</div>
            <div className="text-sm text-slate-500">No approvals match this filter.</div>
          </div>
        ) : (
          <div className="grid gap-4 max-w-3xl">
            {filtered
              .sort((a, b) => {
                if (a.status === "PENDING" && b.status !== "PENDING") return -1;
                if (a.status !== "PENDING" && b.status === "PENDING") return 1;
                return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
              })
              .map((a) => (
                <ApprovalCard key={a.id} approval={a} onResolve={handleResolve} />
              ))}
          </div>
        )}
      </div>

      {toast && (
        <Toast
          message={toast.msg}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  );
}
