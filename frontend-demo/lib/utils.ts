import type { Decision, RiskLevel, StepStatus } from "./types";

export function fmtTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });
}

export function fmtDateTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });
}

export function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const s = Math.floor(diff / 1000);
  if (s < 60) return `${s}s ago`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

export function fmtNumber(n: number): string {
  return n.toLocaleString("en-US");
}

export function decisionColor(d: Decision | string): string {
  switch (d) {
    case "ALLOWED":
    case "APPROVED":
      return "text-emerald-700 bg-emerald-50 border-emerald-200";
    case "DENIED":
    case "REJECTED":
      return "text-red-700 bg-red-50 border-red-200";
    case "BLOCKED":
      return "text-orange-700 bg-orange-50 border-orange-200";
    case "PENDING_APPROVAL":
    case "PENDING":
      return "text-amber-700 bg-amber-50 border-amber-200";
    default:
      return "text-slate-600 bg-slate-50 border-slate-200";
  }
}

export function riskColor(r: RiskLevel): string {
  switch (r) {
    case "LOW":
      return "text-emerald-700 bg-emerald-50 border-emerald-200";
    case "MEDIUM":
      return "text-sky-700 bg-sky-50 border-sky-200";
    case "HIGH":
      return "text-orange-700 bg-orange-50 border-orange-200";
    case "CRITICAL":
      return "text-red-700 bg-red-50 border-red-200";
  }
}

export function stepStatusColor(s: StepStatus): {
  bg: string;
  border: string;
  text: string;
  icon: string;
} {
  switch (s) {
    case "passed":
      return {
        bg: "bg-emerald-50",
        border: "border-emerald-300",
        text: "text-emerald-700",
        icon: "✓",
      };
    case "failed":
    case "blocked":
      return {
        bg: "bg-red-50",
        border: "border-red-300",
        text: "text-red-700",
        icon: "✗",
      };
    case "pending":
      return {
        bg: "bg-amber-50",
        border: "border-amber-300",
        text: "text-amber-700",
        icon: "⏸",
      };
    case "running":
      return {
        bg: "bg-blue-50",
        border: "border-blue-300",
        text: "text-blue-700",
        icon: "◌",
      };
    case "skipped":
      return {
        bg: "bg-slate-50",
        border: "border-slate-200",
        text: "text-slate-400",
        icon: "—",
      };
    default:
      return {
        bg: "bg-slate-50",
        border: "border-slate-200",
        text: "text-slate-400",
        icon: "·",
      };
  }
}

export function shortId(id: string): string {
  return id.slice(-8);
}
