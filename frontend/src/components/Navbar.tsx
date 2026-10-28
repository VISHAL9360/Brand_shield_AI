import React from "react";
import { Shield, LogOut, Building2, Activity, Workflow, LayoutDashboard } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { RoleBadge } from "@/components/RoleBadge";
import { ThemeToggle } from "@/components/ThemeToggle";

interface NavbarProps {
  activeView?: "wizard" | "telemetry";
  onViewChange?: (view: "wizard" | "telemetry") => void;
  onLogout?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeView = "wizard",
  onViewChange,
  onLogout,
}) => {
  const { user, logout } = useAuth();

  const handleLogout = () => {
    logout();
    if (onLogout) {
      onLogout();
    }
  };

  const userInitial = user?.full_name ? user.full_name.charAt(0).toUpperCase() : (user?.email?.charAt(0).toUpperCase() || "U");

  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-200 dark:border-[#1E293B] bg-white/90 dark:bg-[#090A0F]/90 backdrop-blur-md transition-colors duration-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
        {/* Brand & Workspace Identity */}
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-violet-500 flex items-center justify-center text-white shadow-md shadow-indigo-500/20 ring-1 ring-white/20">
              <Shield className="w-5 h-5 stroke-[2.2]" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-display font-bold text-base tracking-tight text-slate-900 dark:text-white">
                  BrandShield<span className="text-indigo-600 dark:text-indigo-400">AI</span>
                </span>
                <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-semibold uppercase bg-indigo-50 text-indigo-700 border border-indigo-200 dark:bg-indigo-950/40 dark:text-indigo-300 dark:border-indigo-800">
                  v1.0 Prod
                </span>
              </div>
              <div className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
                <Building2 className="w-3 h-3 text-slate-400" />
                <span className="font-medium">Acme FinTech Global</span>
              </div>
            </div>
          </div>

          {/* Navigation Mode Switcher: Pipeline Wizard vs Overview */}
          {onViewChange && (
            <div className="hidden lg:flex items-center gap-1 p-1 rounded-xl border border-slate-200 dark:border-[#1E293B] bg-slate-100/70 dark:bg-[#12141C] text-xs font-semibold">
              <button
                type="button"
                id="nav-view-wizard-btn"
                onClick={() => onViewChange("wizard")}
                className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer flex items-center gap-1.5 ${
                  activeView === "wizard"
                    ? "bg-white dark:bg-[#181B26] text-slate-900 dark:text-white shadow-xs"
                    : "text-slate-500 hover:text-slate-900 dark:hover:text-white"
                }`}
              >
                <Workflow className="w-3.5 h-3.5 text-indigo-500" />
                <span>Governance Pipeline</span>
              </button>
              <button
                type="button"
                id="nav-view-telemetry-btn"
                onClick={() => onViewChange("telemetry")}
                className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer flex items-center gap-1.5 ${
                  activeView === "telemetry"
                    ? "bg-white dark:bg-[#181B26] text-slate-900 dark:text-white shadow-xs"
                    : "text-slate-500 hover:text-slate-900 dark:hover:text-white"
                }`}
              >
                <LayoutDashboard className="w-3.5 h-3.5 text-slate-400" />
                <span>Overview & Badges</span>
              </button>
            </div>
          )}
        </div>

        {/* Authenticated Actor Session & Controls */}
        <div className="flex items-center gap-3">
          {/* User Profile Pill */}
          <div className="hidden md:flex items-center gap-3 py-1 px-2.5 rounded-lg border border-slate-200 dark:border-[#1E293B] bg-slate-50/80 dark:bg-[#12141C]">
            <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-slate-700 to-slate-900 dark:from-indigo-900 dark:to-violet-700 text-white text-xs font-semibold flex items-center justify-center shrink-0">
              {userInitial}
            </div>
            <div className="text-left">
              <div className="text-xs font-semibold text-slate-900 dark:text-slate-100 leading-tight truncate max-w-[160px]">
                {user?.full_name || "Enterprise User"}
              </div>
              <div className="text-[11px] font-mono text-slate-500 dark:text-slate-400 leading-tight truncate max-w-[160px]" title={user?.email}>
                {user?.email}
              </div>
            </div>
          </div>

          {/* Color-Coded RBAC Role Badge */}
          <RoleBadge role={user?.role} size="md" />

          {/* Daylight / Obsidian Theme Toggle */}
          <ThemeToggle />

          {/* Dedicated "Log Out to Switch Role" Button */}
          <button
            type="button"
            id="logout-switch-role-btn"
            onClick={handleLogout}
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border border-rose-200 dark:border-rose-900/60 bg-rose-50/80 hover:bg-rose-100 text-rose-700 dark:bg-rose-950/30 dark:hover:bg-rose-900/40 dark:text-rose-300 text-xs font-semibold transition-all duration-200 cursor-pointer shadow-xs active:scale-[0.98]"
            title="End current JWT session and return to /login to switch roles"
          >
            <LogOut className="w-3.5 h-3.5 shrink-0" />
            <span className="tracking-tight whitespace-nowrap">Log Out to Switch Role</span>
          </button>
        </div>
      </div>
    </header>
  );
};

export default Navbar;
