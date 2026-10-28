import React from "react";
import { CheckCircle2, AlertTriangle, Clock, AlertOctagon } from "lucide-react";

export type SemanticStatus =
  | "COMPLIANT"
  | "NEEDS_VERIFICATION"
  | "STALE_FACT"
  | "VIOLATION"
  | "FLAGGED_HIGH_CONFIDENCE"
  | "ROUTED_TO_HUMAN";

interface StatusBadgeProps {
  status: SemanticStatus;
  label?: string;
  className?: string;
  count?: number;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  label,
  className = "",
  count,
}) => {
  const configs: Record<
    SemanticStatus,
    {
      defaultLabel: string;
      badgeClass: string;
      icon: React.ComponentType<{ className?: string }>;
    }
  > = {
    COMPLIANT: {
      defaultLabel: "Compliant / Verified",
      badgeClass: "badge-emerald",
      icon: CheckCircle2,
    },
    FLAGGED_HIGH_CONFIDENCE: {
      defaultLabel: "High Confidence Flag",
      badgeClass: "badge-emerald",
      icon: CheckCircle2,
    },
    NEEDS_VERIFICATION: {
      defaultLabel: "Needs Verification",
      badgeClass: "badge-amber",
      icon: AlertTriangle,
    },
    ROUTED_TO_HUMAN: {
      defaultLabel: "Routed to Human",
      badgeClass: "badge-amber",
      icon: AlertTriangle,
    },
    STALE_FACT: {
      defaultLabel: "Stale / Expired Fact",
      badgeClass: "badge-purple",
      icon: Clock,
    },
    VIOLATION: {
      defaultLabel: "Guideline Violation",
      badgeClass: "badge-rose",
      icon: AlertOctagon,
    },
  };

  const config = configs[status] || configs.COMPLIANT;
  const IconComponent = config.icon;
  const displayLabel = label || config.defaultLabel;

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium tracking-tight transition-colors ${config.badgeClass} ${className}`}
    >
      <IconComponent className="w-3.5 h-3.5 shrink-0" />
      <span>{displayLabel}</span>
      {typeof count === "number" && (
        <span className="ml-1 px-1.5 py-0.2 rounded-full text-[10px] font-mono bg-black/10 dark:bg-white/10 font-bold">
          {count}
        </span>
      )}
    </span>
  );
};

export default StatusBadge;
