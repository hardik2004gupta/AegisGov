import type { Decision, RiskLevel } from "@/lib/types";
import { decisionColor, riskColor } from "@/lib/utils";

interface BadgeProps {
  children: React.ReactNode;
  className?: string;
}

export function Badge({ children, className = "" }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${className}`}
    >
      {children}
    </span>
  );
}

export function DecisionBadge({ decision }: { decision: Decision | string }) {
  return <Badge className={decisionColor(decision)}>{decision}</Badge>;
}

export function RiskBadge({ risk }: { risk: RiskLevel }) {
  return <Badge className={riskColor(risk)}>{risk}</Badge>;
}
