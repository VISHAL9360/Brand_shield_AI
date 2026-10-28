import React, { useState } from "react";
import {
  Shield,
  ShieldCheck,
  Lock,
  Eye,
  EyeOff,
  Sparkles,
  Scale,
  CheckCircle2,
  Server,
  ArrowRight,
  Database,
  KeyRound,
  FileCheck2,
  Cpu,
  Layers,
  Zap,
} from "lucide-react";
import { useAuth, SEEDED_CREDENTIALS } from "@/context/AuthContext";
import { ThemeToggle } from "@/components/ThemeToggle";
import { UserRole } from "@/api/brandshieldClient";

interface LoginPageProps {
  onSuccessLogin?: () => void;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onSuccessLogin }) => {
  const { login, isLoading, error, clearError } = useAuth();

  // Default to Administrator persona for instant 1-click demo readiness
  const [email, setEmail] = useState<string>("administrator@brandshield.ai");
  const [password, setPassword] = useState<string>("DemoSecure2026!");
  const [showPassword, setShowPassword] = useState<boolean>(false);
  const [selectedRole, setSelectedRole] = useState<UserRole | null>("ADMINISTRATOR");
  const [loginFeedback, setLoginFeedback] = useState<{
    type: "idle" | "success" | "error";
    message: string;
  }>({ type: "idle", message: "" });

  const handleSelectRole = (role: UserRole) => {
    const cred = SEEDED_CREDENTIALS[role];
    if (cred) {
      setSelectedRole(role);
      setEmail(cred.email);
      setPassword(cred.password);
      clearError();
      setLoginFeedback({
        type: "idle",
        message: `Loaded ${cred.label} credentials (${cred.name}). Ready to sign in.`,
      });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    setLoginFeedback({ type: "idle", message: "" });

    try {
      const loggedUser = await login(email, password);
      setLoginFeedback({
        type: "success",
        message: `Authenticated as ${loggedUser.full_name} (${loggedUser.role})`,
      });
      if (onSuccessLogin) {
        onSuccessLogin();
      }
    } catch (err: any) {
      setLoginFeedback({
        type: "error",
        message: err.message || "Failed to authenticate. Please check server connection.",
      });
    }
  };

  return (
    <div className="min-h-screen w-full flex flex-col lg:flex-row bg-[#F8FAFC] dark:bg-[#090A0F] text-slate-900 dark:text-slate-100 transition-colors duration-200">
      {/* =====================================================================
          LEFT COLUMN: Enterprise Architecture Showcase (Stripe/Linear Aesthetic)
          ===================================================================== */}
      <div className="lg:w-7/12 xl:w-3/5 p-8 sm:p-12 lg:p-16 flex flex-col justify-between bg-gradient-to-br from-[#0B0D14] via-[#0E111B] to-[#121624] text-white border-r border-[#1E293B] relative overflow-hidden">
        {/* Subtle Ambient Radial Gradients */}
        <div className="absolute -top-40 -left-40 w-96 h-96 bg-indigo-600/15 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 right-0 w-[500px] h-[500px] bg-violet-600/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute top-1/2 left-1/3 w-64 h-64 bg-emerald-500/5 rounded-full blur-3xl pointer-events-none" />

        {/* Top Header & Platform Badge */}
        <div className="relative z-10">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-11 h-11 rounded-2xl bg-gradient-to-tr from-indigo-500 via-indigo-600 to-violet-500 flex items-center justify-center shadow-lg shadow-indigo-500/30 ring-1 ring-white/20">
                <Shield className="w-6 h-6 text-white stroke-[2.2]" />
              </div>
              <div>
                <h1 className="font-display font-extrabold text-2xl tracking-tight text-white flex items-center gap-2">
                  BrandShield<span className="text-indigo-400">AI</span>
                </h1>
                <p className="text-xs font-mono text-slate-400 uppercase tracking-widest">
                  Enterprise Brand Safety & Truth Engine
                </p>
              </div>
            </div>

            <div className="hidden sm:inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-mono">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              Sovereign Perimeter Active
            </div>
          </div>

          {/* Hero Statement */}
          <div className="mt-12 max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-md bg-indigo-500/10 border border-indigo-500/25 text-indigo-300 text-xs font-medium mb-4">
              <Zap className="w-3.5 h-3.5 text-indigo-400" />
              Multi-Stage Autonomous Compliance Pipeline
            </div>
            <h2 className="font-display text-3xl sm:text-4xl lg:text-[42px] font-bold tracking-tight text-white leading-[1.15]">
              Guaranteed Brand Truth & Zero-Hallucination Governance.
            </h2>
            <p className="mt-4 text-slate-300 text-sm sm:text-base leading-relaxed font-normal">
              BrandShield AI combines deterministic finite-automaton rules, pgvector temporal claim RAG, and an immutable SHA-256 Merkle audit ledger into a unified regulatory firewall.
            </p>
          </div>

          {/* Architecture Highlights: 3 Executive Cards */}
          <div className="mt-10 grid gap-4 max-w-2xl">
            {/* Card 1: Zero-Trust Privacy Gate */}
            <div className="group p-4 sm:p-5 rounded-xl bg-white/[0.03] hover:bg-white/[0.06] border border-white/10 hover:border-indigo-500/40 transition-all duration-300 backdrop-blur-xs">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-lg bg-indigo-500/20 border border-indigo-500/40 flex items-center justify-center shrink-0 text-indigo-300 group-hover:scale-105 transition-transform">
                  <Lock className="w-5 h-5" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <h3 className="text-sm font-semibold text-white tracking-tight flex items-center gap-2">
                      Zero-Trust Privacy Gate & Circuit Breaker
                    </h3>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-950/60 text-indigo-300 border border-indigo-800/40">
                      Sub-10ms Gate
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-slate-300 leading-relaxed">
                    Tenant policy checks and automated PII/PHI redaction execute within your sovereign perimeter before model invocation. Semantic vector caching prevents unnecessary external token leakage.
                  </p>
                  <div className="mt-2.5 flex items-center gap-3 text-[11px] font-mono text-slate-400">
                    <span className="flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3 text-emerald-400" /> PII Sanitized
                    </span>
                    <span className="flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3 text-emerald-400" /> Air-Gapped Ready
                    </span>
                    <span className="flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3 text-emerald-400" /> Zero Retention
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Card 2: Deterministic + Hybrid RAG Triage */}
            <div className="group p-4 sm:p-5 rounded-xl bg-white/[0.03] hover:bg-white/[0.06] border border-white/10 hover:border-emerald-500/40 transition-all duration-300 backdrop-blur-xs">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-lg bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center shrink-0 text-emerald-300 group-hover:scale-105 transition-transform">
                  <Layers className="w-5 h-5" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <h3 className="text-sm font-semibold text-white tracking-tight flex items-center gap-2">
                      Deterministic + Hybrid RAG Triage
                    </h3>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950/60 text-emerald-300 border border-emerald-800/40">
                      Aho-Corasick O(N)
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-slate-300 leading-relaxed">
                    Sub-millisecond automaton scans banned terminology while pgvector HNSW + BM25 RRF matches claims against approved facts. Flags stale facts past temporal expiration dates.
                  </p>
                  <div className="mt-2.5 flex items-center gap-3 text-[11px] font-mono text-slate-400">
                    <span className="flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3 text-emerald-400" /> Temporal Verification
                    </span>
                    <span className="flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3 text-emerald-400" /> RRF Fusion
                    </span>
                    <span className="flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3 text-emerald-400" /> Zero Hallucinations
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Card 3: SHA-256 Immutable Revision Ledger */}
            <div className="group p-4 sm:p-5 rounded-xl bg-white/[0.03] hover:bg-white/[0.06] border border-white/10 hover:border-violet-500/40 transition-all duration-300 backdrop-blur-xs">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-lg bg-violet-500/20 border border-violet-500/40 flex items-center justify-center shrink-0 text-violet-300 group-hover:scale-105 transition-transform">
                  <FileCheck2 className="w-5 h-5" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <h3 className="text-sm font-semibold text-white tracking-tight flex items-center gap-2">
                      SHA-256 Immutable Revision Ledger
                    </h3>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-violet-950/60 text-violet-300 border border-violet-800/40">
                      Merkle DAG
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-slate-300 leading-relaxed">
                    Git-like content addressing with diff patches for every edit. Produces tamper-evident Ed25519 publication attestation certificates with verifiable Merkle roots.
                  </p>
                  <div className="mt-2.5 flex items-center gap-3 text-[11px] font-mono text-slate-400">
                    <span className="flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3 text-emerald-400" /> Cryptographic Hashes
                    </span>
                    <span className="flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3 text-emerald-400" /> Tamper-Proof
                    </span>
                    <span className="flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3 text-emerald-400" /> W3C Trace Chain
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Trust & Compliance Bar */}
        <div className="mt-12 pt-6 border-t border-white/10 flex flex-wrap items-center justify-between gap-4 text-xs font-mono text-slate-400 relative z-10">
          <div className="flex items-center gap-4">
            <span>SOC 2 TYPE II</span>
            <span>•</span>
            <span>ISO 27001</span>
            <span>•</span>
            <span>FINRA REG BI</span>
            <span>•</span>
            <span>ARGON2ID</span>
          </div>
          <div className="flex items-center gap-1.5 text-slate-400">
            <Server className="w-3.5 h-3.5 text-indigo-400" />
            <span>FastAPI Core: <span className="text-slate-300">http://localhost:8000/api/v1</span></span>
          </div>
        </div>
      </div>

      {/* =====================================================================
          RIGHT COLUMN: Executive Authentication Portal & 1-Click Role Fill
          ===================================================================== */}
      <div className="lg:w-5/12 xl:w-2/5 p-6 sm:p-10 lg:p-12 flex flex-col justify-between bg-white dark:bg-[#090A0F] border-slate-200 dark:border-[#1E293B]">
        {/* Top Control Bar */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-indigo-600 dark:bg-indigo-400 animate-ping" />
            <span className="text-xs font-mono font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Tenant Authentication Gateway
            </span>
          </div>
          <ThemeToggle showLabel={true} />
        </div>

        {/* Center Auth Card */}
        <div className="my-auto py-8 max-w-md mx-auto w-full">
          <div>
            <h2 className="font-display text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
              Executive Portal
            </h2>
            <p className="mt-1.5 text-xs sm:text-sm text-slate-600 dark:text-slate-400">
              Select an RBAC Persona below to 1-click populate credentials, or enter your work credentials.
            </p>
          </div>

          {/* 3 "Click-to-Fill Credential Cards" */}
          <div className="mt-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 font-mono">
                Click-to-Fill Demo Personas
              </span>
              <span className="text-[11px] font-mono text-indigo-600 dark:text-indigo-400">
                1-Sec JWT Sign In
              </span>
            </div>

            <div className="grid gap-2.5">
              {/* Persona 1: Administrator */}
              <button
                type="button"
                id="role-card-administrator"
                onClick={() => handleSelectRole("ADMINISTRATOR")}
                className={`w-full text-left p-3 rounded-xl border transition-all duration-200 cursor-pointer ${
                  selectedRole === "ADMINISTRATOR"
                    ? "bg-purple-50/80 dark:bg-purple-950/30 border-purple-400 dark:border-purple-600 ring-2 ring-purple-500/20 shadow-xs"
                    : "bg-white dark:bg-[#12141C] border-slate-200 dark:border-[#1E293B] hover:border-purple-300 dark:hover:border-purple-800 hover:bg-slate-50/80 dark:hover:bg-[#181B26]"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-lg bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300 flex items-center justify-center shrink-0">
                      <ShieldCheck className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-slate-900 dark:text-white">
                          Elena Rostova
                        </span>
                        <span className="px-1.5 py-0.2 rounded text-[10px] font-mono font-bold uppercase bg-purple-100 text-purple-700 border border-purple-200 dark:bg-purple-950/60 dark:text-purple-300 dark:border-purple-800">
                          ADMINISTRATOR
                        </span>
                      </div>
                      <div className="text-[11px] text-slate-500 dark:text-slate-400 font-mono truncate">
                        administrator@brandshield.ai
                      </div>
                    </div>
                  </div>
                  {selectedRole === "ADMINISTRATOR" && (
                    <CheckCircle2 className="w-4 h-4 text-purple-600 dark:text-purple-400 shrink-0" />
                  )}
                </div>
              </button>

              {/* Persona 2: Creator */}
              <button
                type="button"
                id="role-card-creator"
                onClick={() => handleSelectRole("CREATOR")}
                className={`w-full text-left p-3 rounded-xl border transition-all duration-200 cursor-pointer ${
                  selectedRole === "CREATOR"
                    ? "bg-emerald-50/80 dark:bg-emerald-950/30 border-emerald-400 dark:border-emerald-600 ring-2 ring-emerald-500/20 shadow-xs"
                    : "bg-white dark:bg-[#12141C] border-slate-200 dark:border-[#1E293B] hover:border-emerald-300 dark:hover:border-emerald-800 hover:bg-slate-50/80 dark:hover:bg-[#181B26]"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-lg bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300 flex items-center justify-center shrink-0">
                      <Sparkles className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-slate-900 dark:text-white">
                          Alex Chen
                        </span>
                        <span className="px-1.5 py-0.2 rounded text-[10px] font-mono font-bold uppercase bg-emerald-100 text-emerald-700 border border-emerald-200 dark:bg-emerald-950/60 dark:text-emerald-300 dark:border-emerald-800">
                          CREATOR
                        </span>
                      </div>
                      <div className="text-[11px] text-slate-500 dark:text-slate-400 font-mono truncate">
                        creator@brandshield.ai
                      </div>
                    </div>
                  </div>
                  {selectedRole === "CREATOR" && (
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
                  )}
                </div>
              </button>

              {/* Persona 3: Reviewer */}
              <button
                type="button"
                id="role-card-reviewer"
                onClick={() => handleSelectRole("REVIEWER")}
                className={`w-full text-left p-3 rounded-xl border transition-all duration-200 cursor-pointer ${
                  selectedRole === "REVIEWER"
                    ? "bg-amber-50/80 dark:bg-amber-950/30 border-amber-400 dark:border-amber-600 ring-2 ring-amber-500/20 shadow-xs"
                    : "bg-white dark:bg-[#12141C] border-slate-200 dark:border-[#1E293B] hover:border-amber-300 dark:hover:border-amber-800 hover:bg-slate-50/80 dark:hover:bg-[#181B26]"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-lg bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300 flex items-center justify-center shrink-0">
                      <Scale className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-slate-900 dark:text-white">
                          Marcus Vance
                        </span>
                        <span className="px-1.5 py-0.2 rounded text-[10px] font-mono font-bold uppercase bg-amber-100 text-amber-700 border border-amber-200 dark:bg-amber-950/60 dark:text-amber-300 dark:border-amber-800">
                          REVIEWER
                        </span>
                      </div>
                      <div className="text-[11px] text-slate-500 dark:text-slate-400 font-mono truncate">
                        reviewer@brandshield.ai
                      </div>
                    </div>
                  </div>
                  {selectedRole === "REVIEWER" && (
                    <CheckCircle2 className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0" />
                  )}
                </div>
              </button>
            </div>
          </div>

          {/* Authentication Form */}
          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            {/* Email Field */}
            <div>
              <label
                htmlFor="auth-email-input"
                className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5"
              >
                Tenant Work Email
              </label>
              <div className="relative">
                <input
                  type="email"
                  id="auth-email-input"
                  required
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    setSelectedRole(null);
                  }}
                  placeholder="name@brandshield.ai"
                  className="w-full pl-3.5 pr-10 py-2.5 rounded-lg border border-slate-300 dark:border-[#1E293B] bg-white dark:bg-[#12141C] text-slate-900 dark:text-white placeholder:text-slate-400 dark:placeholder:text-slate-500 text-xs sm:text-sm font-mono focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 dark:focus:border-indigo-500 transition-all shadow-xs"
                />
                <KeyRound className="w-4 h-4 text-slate-400 absolute right-3.5 top-3" />
              </div>
            </div>

            {/* Password Field */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label
                  htmlFor="auth-password-input"
                  className="block text-xs font-semibold text-slate-700 dark:text-slate-300"
                >
                  Password (Argon2id Encrypted)
                </label>
                <span className="text-[11px] font-mono text-slate-400">
                  Demo: <code className="text-indigo-600 dark:text-indigo-400">DemoSecure2026!</code>
                </span>
              </div>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  id="auth-password-input"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full pl-3.5 pr-10 py-2.5 rounded-lg border border-slate-300 dark:border-[#1E293B] bg-white dark:bg-[#12141C] text-slate-900 dark:text-white placeholder:text-slate-400 dark:placeholder:text-slate-500 text-xs sm:text-sm font-mono focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 dark:focus:border-indigo-500 transition-all shadow-xs"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3.5 top-3 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 focus:outline-none cursor-pointer"
                  title={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? (
                    <EyeOff className="w-4 h-4" />
                  ) : (
                    <Eye className="w-4 h-4" />
                  )}
                </button>
              </div>
            </div>

            {/* Feedback & Error Banner */}
            {(error || loginFeedback.type === "error") && (
              <div className="p-3 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900/60 text-rose-700 dark:text-rose-300 text-xs flex items-start gap-2">
                <ShieldCheck className="w-4 h-4 text-rose-500 shrink-0 mt-0.5" />
                <div className="flex-1">
                  <div className="font-semibold">Authentication Notice</div>
                  <div className="text-[11px] mt-0.5">{error || loginFeedback.message}</div>
                </div>
              </div>
            )}

            {loginFeedback.type === "success" && (
              <div className="p-3 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-900/60 text-emerald-700 dark:text-emerald-300 text-xs flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                <span className="font-medium">{loginFeedback.message}</span>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              id="sign-in-jwt-btn"
              disabled={isLoading}
              className="w-full mt-2 py-3 px-4 rounded-xl bg-gradient-to-r from-indigo-600 via-indigo-600 to-indigo-700 hover:from-indigo-500 hover:to-indigo-600 text-white font-semibold text-xs sm:text-sm tracking-wide shadow-md shadow-indigo-500/25 hover:shadow-indigo-500/40 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 dark:focus:ring-offset-[#090A0F] transition-all duration-200 flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50 active:scale-[0.99]"
            >
              {isLoading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Verifying Credentials & Issuing JWT...</span>
                </>
              ) : (
                <>
                  <span>Sign In with JWT</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Quick Explanatory Note */}
          <div className="mt-5 p-3 rounded-lg bg-slate-100/70 dark:bg-[#12141C] border border-slate-200 dark:border-[#1E293B] text-[11px] text-slate-500 dark:text-slate-400 leading-normal flex items-start gap-2">
            <Database className="w-3.5 h-3.5 text-indigo-500 shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-slate-700 dark:text-slate-300">FastAPI RBAC Router:</span>{" "}
              Dispatches directly to <code className="font-mono text-indigo-600 dark:text-indigo-400">POST /api/v1/auth/login</code>. Role switching is enforced via cryptographic session termination at <code className="font-mono text-indigo-600 dark:text-indigo-400">/login</code>.
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="pt-4 border-t border-slate-200 dark:border-[#1E293B] text-center text-xs text-slate-400 dark:text-slate-500 font-mono">
          BrandShield AI Architecture v1.0 • Built with React 19 + Vite + Tailwind CSS
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
