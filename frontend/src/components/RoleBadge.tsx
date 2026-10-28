import React from "react";
import { ShieldCheck, Sparkles, Scale, UserCheck } from "lucide-react";
import { UserRole } from "@/api/brandshieldClient";

interface RoleBadgeProps {
  role?: UserRole | string | null;
  size?: "sm" | "md" | "lg";
  showIcon?: boolean;
  className?: string;
}

export const RoleBadge: React.FC<RoleBadgeProps> = ({
  role = "CREATOR",
  size = "md",
  showIcon = true,
  className = "",
}) => {
  const normalizedRole = (role || "CREATOR").toUpperCase();

  const config = {
    ADMINISTRATOR: {
      label: "ADMINISTRATOR",
      classes: "bg-purple-50 text-purple-700 border-purple-200 dark:bg-purple-950/40 dark:text-purple-300 dark:border-purple-800/60",
      dotColor: "bg-purple-500",
      icon: ShieldCheck,
    },
    CREATOR: {
      label: "CREATOR",
      classes: "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800/60",
      dotColor: "bg-emerald-500",
      icon: Sparkles,
    },
    REVIEWER: {
      label: "REVIEWER",
      classes: "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-800/60",
      dotColor: "bg-amber-500",
      icon: Scale,
    },
  }[normalizedRole] || {
    label: normalizedRole,
    classes: "bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700",
    dotColor: "bg-slate-400",
    icon: UserCheck,
  };

  const IconComponent = config.icon;

  const sizeClasses = {
    sm: "px-2 py-0.5 text-[11px] gap-1 font-semibold tracking-wider",
    md: "px-2.5 py-1 text-xs gap-1.5 font-semibold tracking-wider",
    lg: "px-3 py-1.5 text-sm gap-2 font-bold tracking-wider",
  }[size];

  const iconSizes = {
    sm: "w-3 h-3",
    md: "w-3.5 h-3.5",
    lg: "w-4 h-4",
  }[size];

  return (
    <span
      className={`inline-flex items-center rounded-md border font-mono uppercase transition-colors ${config.classes} ${sizeClasses} ${className}`}
    >
      {showIcon && <IconComponent className={`${iconSizes} shrink-0`} />}
      <span className="leading-none">{config.label}</span>
    </span>
  );
};

export default RoleBadge;
