import type { RiskLevel, ApprovalStatus, AuditDecision } from "@/lib/types";

type BadgeVariant =
  | RiskLevel
  | ApprovalStatus
  | AuditDecision
  | "COMPLETED"
  | "FAILED"
  | "SYSTEM"
  | string;

const STYLES: Record<string, string> = {
  ALLOWED:   "bg-emerald-50 text-emerald-700 border-emerald-200",
  APPROVED:  "bg-emerald-50 text-emerald-700 border-emerald-200",
  COMPLETED: "bg-emerald-50 text-emerald-700 border-emerald-200",
  LOW:       "bg-sky-50 text-sky-700 border-sky-200",
  MEDIUM:    "bg-amber-50 text-amber-700 border-amber-200",
  PENDING:   "bg-amber-50 text-amber-700 border-amber-200",
  HIGH:      "bg-orange-50 text-orange-700 border-orange-200",
  DENIED:    "bg-red-50 text-red-700 border-red-200",
  REJECTED:  "bg-red-50 text-red-700 border-red-200",
  BLOCKED:   "bg-red-50 text-red-700 border-red-200",
  FAILED:    "bg-slate-100 text-slate-600 border-slate-200",
  CRITICAL:  "bg-red-100 text-red-800 border-red-300 font-semibold",
  SYSTEM:    "bg-slate-100 text-slate-600 border-slate-200",
};

const DOTS: Record<string, string> = {
  ALLOWED:   "bg-emerald-500",
  APPROVED:  "bg-emerald-500",
  COMPLETED: "bg-emerald-500",
  LOW:       "bg-sky-500",
  MEDIUM:    "bg-amber-500",
  PENDING:   "bg-amber-500",
  HIGH:      "bg-orange-500",
  DENIED:    "bg-red-500",
  REJECTED:  "bg-red-500",
  BLOCKED:   "bg-red-500",
  FAILED:    "bg-slate-400",
  CRITICAL:  "bg-red-600",
  SYSTEM:    "bg-slate-400",
};

interface BadgeProps {
  value: BadgeVariant;
  showDot?: boolean;
  size?: "xs" | "sm";
  className?: string;
}

export function Badge({ value, showDot = false, size = "xs", className = "" }: BadgeProps) {
  const style = STYLES[value] ?? "bg-slate-100 text-slate-600 border-slate-200";
  const dot   = DOTS[value]  ?? "bg-slate-400";

  return (
    <span
      className={[
        "inline-flex items-center gap-1 border rounded font-mono tracking-wide uppercase",
        size === "xs" ? "text-[10px] px-1.5 py-0.5" : "text-[11px] px-2 py-0.5",
        style,
        className,
      ].join(" ")}
    >
      {showDot && (
        <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${dot}`} aria-hidden="true" />
      )}
      {value}
    </span>
  );
}
