import React, { useState, useEffect } from "react";
import {
  Shield,
  ShieldAlert,
  ShieldCheck,
  CheckCircle2,
  Clock,
  AlertTriangle,
  AlertOctagon,
  FileText,
  Key,
  Database,
  ArrowUpRight,
  Layers,
  Sparkles,
  Scale,
  LogOut,
  RefreshCw,
  Terminal,
  Activity,
  Check,
  Copy,
} from "lucide-react";
import { useAuth, SEEDED_CREDENTIALS } from "@/context/AuthContext";
import { RoleBadge } from "@/components/RoleBadge";
import { StatusBadge } from "@/components/StatusBadge";
import brandshield, { UserRole } from "@/api/brandshieldClient";

export const DashboardPage: React.FC = () => {
  const { user, token, logout } = useAuth();
  const [copiedToken, setCopiedToken] = useState(false);
  const [apiPingStatus, setApiPingStatus] = useState<"checking" | "online" | "offline">("checking");
  const [apiLatency, setApiLatency] = useState<number | null>(null);

  const activeRole: UserRole = (user?.role as UserRole) || "ADMINISTRATOR";
  const roleConfig = SEEDED_CREDENTIALS[activeRole] || SEEDED_CREDENTIALS.ADMINISTRATOR;

  // Check backend connectivity on mount
  useEffect(() => {
    let isMounted = true;
    const checkApi = async () => {
      const startTime = performance.now();
      try {
        // Try calling auth/me or demo-tokens to test API
        await fetch(`${import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1"}/auth/demo-tokens`, {
          method: "GET",
          headers: { Accept: "application/json" },
        });
        if (isMounted) {
          setApiLatency(Math.round(performance.now() - startTime));
          setApiPingStatus("online");
        }
      } catch {
        if (isMounted) {
          setApiPingStatus("offline");
          setApiLatency(null);
        }
      }
    };
    checkApi();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleCopyToken = () => {
    if (token) {
      navigator.clipboard.writeText(token);
      setCopiedToken(true);
      setTimeout(() => setCopiedToken(false), 2000);
    }
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto space-y-8 animate-in fade-in duration-300">
      {/* =====================================================================
          1. HERO & RBAC PERSONA BANNER
          ===================================================================== */}
      <div className="relative rounded-2xl border border-slate-200 dark:border-[#1E293B] bg-white dark:bg-[#12141C] p-6 sm:p-8 shadow-xs overflow-hidden transition-colors">
        {/* Subtle accent glow top-right */}
        <div className="absolute top-0 right-0 w-80 h-80 bg-gradient-to-br from-indigo-500/10 via-purple-500/5 to-transparent rounded-full blur-2xl pointer-events-none" />

        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-3">
            <div className="flex flex-wrap items-center gap-2.5">
              <span className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                Active Tenant Session
              </span>
              <span className="text-slate-300 dark:text-slate-700">•</span>
              <RoleBadge role={user?.role} size="md" />
              <span className="text-slate-300 dark:text-slate-700">•</span>
              <span className="inline-flex items-center gap-1.5 text-xs font-mono text-emerald-600 dark:text-emerald-400">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                JWT Authenticated
              </span>
            </div>

            <h1 className="font-display text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
              Welcome back, {user?.full_name || "Enterprise Operator"}
            </h1>

            <p className="text-sm text-slate-600 dark:text-slate-400 max-w-2xl leading-relaxed">
              {roleConfig.description}
            </p>
          </div>

          {/* Quick Session Switching Callout */}
          <div className="shrink-0 p-4 rounded-xl border border-slate-200 dark:border-[#1E293B] bg-slate-50/70 dark:bg-[#181B26] max-w-xs space-y-2.5">
            <div className="flex items-center justify-between text-xs font-semibold text-slate-900 dark:text-slate-200">
              <span className="flex items-center gap-1.5">
                <Key className="w-3.5 h-3.5 text-indigo-500" />
                Session Guard
              </span>
              <span className="font-mono text-[10px] text-slate-500 dark:text-slate-400">
                RBAC Isolated
              </span>
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-normal">
              Role switching is strictly guarded. Log out to return to the executive login portal and assume a different persona.
            </p>
            <button
              type="button"
              onClick={logout}
              className="w-full py-1.5 px-3 rounded-lg border border-slate-300 dark:border-slate-700 hover:border-rose-300 dark:hover:border-rose-900 bg-white dark:bg-[#12141C] hover:bg-rose-50 dark:hover:bg-rose-950/30 text-slate-700 dark:text-slate-300 hover:text-rose-600 dark:hover:text-rose-300 text-xs font-medium transition-all flex items-center justify-center gap-2 cursor-pointer"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Log Out to Switch Role</span>
            </button>
          </div>
        </div>
      </div>

      {/* =====================================================================
          2. SEMANTIC STATUS BADGES PALETTE SHOWCASE (Executive Verification)
          ===================================================================== */}
      <div className="rounded-2xl border border-slate-200 dark:border-[#1E293B] bg-white dark:bg-[#12141C] p-6 shadow-xs space-y-4 transition-colors">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 dark:border-[#1E293B] pb-4">
          <div>
            <h2 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <Activity className="w-4 h-4 text-indigo-500" />
              Enterprise Semantic Status Badges
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Strict color-coded compliance states with high contrast in both Daylight and Obsidian Dark modes.
            </p>
          </div>
          <span className="text-xs font-mono text-slate-400">Design System Tokens</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Emerald: Compliant */}
          <div className="p-4 rounded-xl border border-slate-200 dark:border-[#1E293B] bg-slate-50/50 dark:bg-[#181B26]/50 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-slate-500 dark:text-slate-400">Emerald State</span>
              <StatusBadge status="COMPLIANT" count={142} />
            </div>
            <p className="text-xs font-medium text-slate-700 dark:text-slate-300">
              Compliant / High-Confidence Verified
            </p>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-normal">
              Applied when claim matches approved active facts within validity window with &gt;95% confidence score.
            </p>
          </div>

          {/* Amber: Needs Verification */}
          <div className="p-4 rounded-xl border border-slate-200 dark:border-[#1E293B] bg-slate-50/50 dark:bg-[#181B26]/50 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-slate-500 dark:text-slate-400">Amber State</span>
              <StatusBadge status="NEEDS_VERIFICATION" count={18} />
            </div>
            <p className="text-xs font-medium text-slate-700 dark:text-slate-300">
              Needs Verification / Human Triage
            </p>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-normal">
              Applied when factual assertions lack corroborating citations or confidence score is below human triage threshold.
            </p>
          </div>

          {/* Purple: Stale/Expired Fact */}
          <div className="p-4 rounded-xl border border-slate-200 dark:border-[#1E293B] bg-slate-50/50 dark:bg-[#181B26]/50 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-slate-500 dark:text-slate-400">Purple State</span>
              <StatusBadge status="STALE_FACT" count={7} />
            </div>
            <p className="text-xs font-medium text-slate-700 dark:text-slate-300">
              Stale / Expired Temporal Fact
            </p>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-normal">
              Triggered when an approved fact exceeds its explicit validity date, triggering blast-radius re-verification.
            </p>
          </div>

          {/* Rose: Guideline Violation */}
          <div className="p-4 rounded-xl border border-slate-200 dark:border-[#1E293B] bg-slate-50/50 dark:bg-[#181B26]/50 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-slate-500 dark:text-slate-400">Rose State</span>
              <StatusBadge status="VIOLATION" count={3} />
            </div>
            <p className="text-xs font-medium text-slate-700 dark:text-slate-300">
              Guideline & Regulatory Violation
            </p>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-normal">
              Hard deterministic violation detected by Aho-Corasick automaton (banned terminology, regulatory mandate).
            </p>
          </div>
        </div>
      </div>

      {/* =====================================================================
          3. CORE ARCHITECTURE TELEMETRY & FASTAPI INTEGRATION
          ===================================================================== */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Column 1 & 2: Pipeline Stage Readiness */}
        <div className="lg:col-span-2 rounded-2xl border border-slate-200 dark:border-[#1E293B] bg-white dark:bg-[#12141C] p-6 shadow-xs space-y-4 transition-colors">
          <div className="flex items-center justify-between border-b border-slate-100 dark:border-[#1E293B] pb-3">
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-indigo-500" />
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                Multi-Stage Intelligence Architecture
              </h3>
            </div>
            <span className="text-xs font-mono text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" /> All 4 Stages Primed
            </span>
          </div>

          <div className="space-y-3">
            {/* Stage 1 */}
            <div className="p-3 rounded-xl border border-slate-100 dark:border-[#1E293B] bg-slate-50/60 dark:bg-[#181B26] flex items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <span className="w-7 h-7 rounded-lg bg-indigo-100 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300 text-xs font-mono font-bold flex items-center justify-center">
                  01
                </span>
                <div>
                  <div className="text-xs font-semibold text-slate-900 dark:text-white">
                    Deterministic Automaton Engine
                  </div>
                  <div className="text-[11px] text-slate-500 dark:text-slate-400">
                    Aho-Corasick O(N) banned term scanner, regex AST objective claim detectors, readability index.
                  </div>
                </div>
              </div>
              <span className="font-mono text-xs text-slate-600 dark:text-slate-300 shrink-0 font-medium">
                &lt; 5ms
              </span>
            </div>

            {/* Stage 2 */}
            <div className="p-3 rounded-xl border border-slate-100 dark:border-[#1E293B] bg-slate-50/60 dark:bg-[#181B26] flex items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <span className="w-7 h-7 rounded-lg bg-emerald-100 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300 text-xs font-mono font-bold flex items-center justify-center">
                  02
                </span>
                <div>
                  <div className="text-xs font-semibold text-slate-900 dark:text-white">
                    Temporal Fact & Vector Engine (Hybrid RAG)
                  </div>
                  <div className="text-[11px] text-slate-500 dark:text-slate-400">
                    pgvector HNSW + BM25 RRF search, temporal expiration date enforcement, blast radius triggers.
                  </div>
                </div>
              </div>
              <span className="font-mono text-xs text-slate-600 dark:text-slate-300 shrink-0 font-medium">
                ~ 42ms
              </span>
            </div>

            {/* Stage 3 */}
            <div className="p-3 rounded-xl border border-slate-100 dark:border-[#1E293B] bg-slate-50/60 dark:bg-[#181B26] flex items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <span className="w-7 h-7 rounded-lg bg-purple-100 text-purple-700 dark:bg-purple-950/60 dark:text-purple-300 text-xs font-mono font-bold flex items-center justify-center">
                  03
                </span>
                <div>
                  <div className="text-xs font-semibold text-slate-900 dark:text-white">
                    Zero-Trust Privacy Gate & Circuit Breaker
                  </div>
                  <div className="text-[11px] text-slate-500 dark:text-slate-400">
                    Tenant policy governance, PII/PHI sanitization, semantic vector caching, multi-model fallback.
                  </div>
                </div>
              </div>
              <span className="font-mono text-xs text-slate-600 dark:text-slate-300 shrink-0 font-medium">
                &lt; 15ms
              </span>
            </div>

            {/* Stage 4 */}
            <div className="p-3 rounded-xl border border-slate-100 dark:border-[#1E293B] bg-slate-50/60 dark:bg-[#181B26] flex items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <span className="w-7 h-7 rounded-lg bg-amber-100 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300 text-xs font-mono font-bold flex items-center justify-center">
                  04
                </span>
                <div>
                  <div className="text-xs font-semibold text-slate-900 dark:text-white">
                    Confidence Triage & Automation-Bias Safeguards
                  </div>
                  <div className="text-[11px] text-slate-500 dark:text-slate-400">
                    Deterministic confidence tiering, stochastic reviewer audit injection, human queue dispatch.
                  </div>
                </div>
              </div>
              <span className="font-mono text-xs text-slate-600 dark:text-slate-300 shrink-0 font-medium">
                ~ 8ms
              </span>
            </div>
          </div>
        </div>

        {/* Column 3: Fast API & JWT Session Telemetry */}
        <div className="rounded-2xl border border-slate-200 dark:border-[#1E293B] bg-white dark:bg-[#12141C] p-6 shadow-xs space-y-4 transition-colors">
          <div className="flex items-center justify-between border-b border-slate-100 dark:border-[#1E293B] pb-3">
            <div className="flex items-center gap-2">
              <Database className="w-4 h-4 text-indigo-500" />
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                API Session Telemetry
              </h3>
            </div>
            <span
              className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-mono ${
                apiPingStatus === "online"
                  ? "bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300"
                  : "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400"
              }`}
            >
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  apiPingStatus === "online" ? "bg-emerald-500 animate-pulse" : "bg-slate-400"
                }`}
              />
              {apiPingStatus === "online" ? `${apiLatency}ms Online` : "Standby Mode"}
            </span>
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <span className="text-slate-500 dark:text-slate-400 block font-mono text-[11px]">
                API Base Target
              </span>
              <code className="text-indigo-600 dark:text-indigo-400 font-mono break-all text-[11px]">
                {import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1"}
              </code>
            </div>

            <div>
              <span className="text-slate-500 dark:text-slate-400 block font-mono text-[11px]">
                Workspace Tenant UUID
              </span>
              <code className="text-slate-700 dark:text-slate-300 font-mono text-[11px]">
                {user?.workspace_id || "ws-acme-global-brand-001"}
              </code>
            </div>

            <div>
              <span className="text-slate-500 dark:text-slate-400 block font-mono text-[11px]">
                Actor User ID
              </span>
              <code className="text-slate-700 dark:text-slate-300 font-mono text-[11px]">
                {user?.id}
              </code>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-slate-500 dark:text-slate-400 font-mono text-[11px]">
                  Active JWT Bearer Token
                </span>
                <button
                  type="button"
                  onClick={handleCopyToken}
                  className="text-[11px] font-mono text-indigo-600 dark:text-indigo-400 hover:underline flex items-center gap-1 cursor-pointer"
                >
                  {copiedToken ? (
                    <>
                      <Check className="w-3 h-3 text-emerald-500" />
                      <span>Copied!</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3 h-3" />
                      <span>Copy</span>
                    </>
                  )}
                </button>
              </div>
              <div className="p-2 rounded-lg bg-slate-100 dark:bg-[#181B26] border border-slate-200 dark:border-slate-800 font-mono text-[10px] text-slate-600 dark:text-slate-300 break-all max-h-20 overflow-y-auto">
                {token || "No active JWT token present"}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
