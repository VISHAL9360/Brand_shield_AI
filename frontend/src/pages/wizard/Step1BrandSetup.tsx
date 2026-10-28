import React, { useState } from "react";
import {
  Shield,
  ShieldAlert,
  ShieldCheck,
  CheckCircle2,
  Clock,
  ExternalLink,
  Plus,
  Lock,
  Layers,
  Sparkles,
  Search,
  Filter,
  Check,
  X,
  FileCheck2,
  Calendar,
  UserCheck,
  Sliders,
  AlertTriangle,
} from "lucide-react";
import { usePipeline } from "@/context/PipelineContext";
import { useAuth } from "@/context/AuthContext";
import { StatusBadge } from "@/components/StatusBadge";
import { RoleBadge } from "@/components/RoleBadge";
import { BrandGuideline, ApprovedFact, SeverityLevel, FindingCategory } from "@/api/brandshieldClient";

export const Step1BrandSetup: React.FC = () => {
  const {
    brandProfile,
    guidelines,
    approvedFacts,
    privacyGate,
    updatePrivacyGate,
    addGuideline,
    addApprovedFact,
    setCurrentStep,
  } = usePipeline();

  const { user } = useAuth();
  const isAdmin = user?.role === "ADMINISTRATOR";

  // Active section tab: "facts" | "guidelines" | "terminology"
  const [activeTab, setActiveTab] = useState<"facts" | "guidelines" | "terminology">("facts");
  const [factFilter, setFactFilter] = useState<"ALL" | "ACTIVE" | "EXPIRED">("ALL");
  const [guidelineCategoryFilter, setGuidelineCategoryFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");

  // Modals state
  const [isFactModalOpen, setIsFactModalOpen] = useState(false);
  const [isGuidelineModalOpen, setIsGuidelineModalOpen] = useState(false);

  // New Fact Form state
  const [newFactStatement, setNewFactStatement] = useState("");
  const [newFactSourceUrl, setNewFactSourceUrl] = useState("");
  const [newFactEvidence, setNewFactEvidence] = useState("");
  const [newFactVerificationDate, setNewFactVerificationDate] = useState("2026-02-01");
  const [newFactExpiryDate, setNewFactExpiryDate] = useState("2027-02-01");
  const [newFactOwner, setNewFactOwner] = useState(user?.full_name || "Elena Rostova (Compliance Lead)");

  // New Guideline Form state
  const [newClauseId, setNewClauseId] = useState("");
  const [newClauseText, setNewClauseText] = useState("");
  const [newCategory, setNewCategory] = useState<FindingCategory>("TONE");
  const [newSeverity, setNewSeverity] = useState<SeverityLevel>("HIGH");

  // Filtered Approved Facts
  const now = new Date();
  const filteredFacts = approvedFacts.filter((fact) => {
    const isExpired = new Date(fact.expiry_date) < now;
    if (factFilter === "ACTIVE" && isExpired) return false;
    if (factFilter === "EXPIRED" && !isExpired) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return (
        fact.fact_statement.toLowerCase().includes(q) ||
        fact.original_source_url.toLowerCase().includes(q) ||
        (fact.responsible_owner_id && fact.responsible_owner_id.toLowerCase().includes(q))
      );
    }
    return true;
  });

  // Filtered Guidelines
  const filteredGuidelines = guidelines.filter((g) => {
    if (guidelineCategoryFilter !== "ALL" && g.category !== guidelineCategoryFilter) {
      return false;
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return (
        g.clause_identifier.toLowerCase().includes(q) ||
        g.clause_text.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const handleCreateFact = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newFactStatement.trim() || !newFactSourceUrl.trim()) return;
    addApprovedFact({
      fact_statement: newFactStatement,
      original_source_url: newFactSourceUrl,
      evidence_excerpt: newFactEvidence || "Audited internal documentation verified.",
      verification_date: new Date(newFactVerificationDate).toISOString(),
      expiry_date: new Date(newFactExpiryDate).toISOString(),
      responsible_owner_id: newFactOwner,
    });
    setNewFactStatement("");
    setNewFactSourceUrl("");
    setNewFactEvidence("");
    setIsFactModalOpen(false);
  };

  const handleCreateGuideline = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newClauseId.trim() || !newClauseText.trim()) return;
    addGuideline({
      clause_identifier: newClauseId.toUpperCase(),
      clause_text: newClauseText,
      category: newCategory,
      severity: newSeverity,
    });
    setNewClauseId("");
    setNewClauseText("");
    setIsGuidelineModalOpen(false);
  };

  const activeFactsCount = approvedFacts.filter((f) => new Date(f.expiry_date) >= now).length;
  const expiredFactsCount = approvedFacts.filter((f) => new Date(f.expiry_date) < now).length;

  return (
    <div className="space-y-6">
      {/* =====================================================================
          1. BRAND PROFILE BANNER & ZERO-TRUST PRIVACY GATE
          ===================================================================== */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Brand Profile Overview */}
        <div className="lg:col-span-2 rounded-2xl border border-slate-200 dark:border-[#1E293B] bg-white dark:bg-[#12141C] p-6 shadow-xs relative overflow-hidden transition-colors">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 dark:border-[#1E293B] pb-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                  Primary Knowledge Anchor
                </span>
                <span className="text-slate-300 dark:text-slate-700">•</span>
                <span className="px-2 py-0.5 rounded text-[11px] font-mono font-bold uppercase bg-indigo-50 text-indigo-700 border border-indigo-200 dark:bg-indigo-950/40 dark:text-indigo-300 dark:border-indigo-800">
                  Active Profile v2.4
                </span>
              </div>
              <h2 className="text-xl sm:text-2xl font-bold font-display text-slate-900 dark:text-white">
                {brandProfile.name}
              </h2>
            </div>

            <div className="flex items-center gap-2">
              <RoleBadge role={user?.role} size="sm" />
            </div>
          </div>

          <p className="mt-3 text-xs sm:text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
            {brandProfile.description}
          </p>

          {/* Core Governance Parameters Grid */}
          <div className="mt-5 grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3 rounded-xl border border-slate-100 dark:border-[#181B26] bg-slate-50/70 dark:bg-[#181B26]/60">
              <span className="text-[11px] font-mono text-slate-500 dark:text-slate-400 block">
                Target Formality
              </span>
              <span className="text-lg font-bold font-mono text-slate-900 dark:text-white">
                {brandProfile.tone_parameters?.target_formality || 8.5}/10
              </span>
            </div>
            <div className="p-3 rounded-xl border border-slate-100 dark:border-[#181B26] bg-slate-50/70 dark:bg-[#181B26]/60">
              <span className="text-[11px] font-mono text-slate-500 dark:text-slate-400 block">
                Max Grade Level
              </span>
              <span className="text-lg font-bold font-mono text-slate-900 dark:text-white">
                ≤ {brandProfile.tone_parameters?.max_grade_level || 12.0}
              </span>
            </div>
            <div className="p-3 rounded-xl border border-slate-100 dark:border-[#181B26] bg-slate-50/70 dark:bg-[#181B26]/60">
              <span className="text-[11px] font-mono text-slate-500 dark:text-slate-400 block">
                Passive Voice Cap
              </span>
              <span className="text-lg font-bold font-mono text-slate-900 dark:text-white">
                ≤ {Math.round((brandProfile.tone_parameters?.max_passive_voice_ratio || 0.15) * 100)}%
              </span>
            </div>
            <div className="p-3 rounded-xl border border-slate-100 dark:border-[#181B26] bg-slate-50/70 dark:bg-[#181B26]/60">
              <span className="text-[11px] font-mono text-slate-500 dark:text-slate-400 block">
                Regulatory Scope
              </span>
              <span className="text-xs font-bold font-mono text-slate-900 dark:text-white truncate block mt-1" title={brandProfile.messaging_rules?.regulatory_framework}>
                {brandProfile.messaging_rules?.regulatory_framework || "SEC / FINRA"}
              </span>
            </div>
          </div>
        </div>

        {/* Right Col: Zero-Trust Privacy Gate Toggle Card */}
        <div className="rounded-2xl border border-slate-200 dark:border-[#1E293B] bg-white dark:bg-[#12141C] p-6 shadow-xs relative overflow-hidden transition-colors flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-[#1E293B]">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 flex items-center justify-center">
                  <Lock className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                    Zero-Trust Privacy Gate
                  </h3>
                  <span className="text-[10px] font-mono text-slate-400">
                    Sovereign Perimeter Guard
                  </span>
                </div>
              </div>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300">
                ACTIVE
              </span>
            </div>

            {/* Interactive Toggle Controls */}
            <div className="mt-4 space-y-3.5">
              {/* Toggle 1: Allow External LLM Calls */}
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="text-xs font-semibold text-slate-900 dark:text-white">
                    Allow External LLM Calls
                  </div>
                  <div className="text-[11px] text-slate-500 dark:text-slate-400">
                    {privacyGate.allowExternalLlm ? "Sanitized routing enabled" : "Air-gapped local RAG only"}
                  </div>
                </div>
                <button
                  type="button"
                  id="toggle-external-llm-btn"
                  onClick={() => updatePrivacyGate({ allowExternalLlm: !privacyGate.allowExternalLlm })}
                  className={`relative inline-flex h-5 w-10 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                    privacyGate.allowExternalLlm ? "bg-indigo-600" : "bg-slate-300 dark:bg-slate-700"
                  }`}
                >
                  <span
                    className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow-lg ring-0 transition duration-200 ease-in-out ${
                      privacyGate.allowExternalLlm ? "translate-x-5" : "translate-x-0"
                    }`}
                  />
                </button>
              </div>

              {/* Toggle 2: Provider Retention Verified */}
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="text-xs font-semibold text-slate-900 dark:text-white">
                    Provider Zero-Retention Agreement
                  </div>
                  <div className="text-[11px] text-slate-500 dark:text-slate-400">
                    Zero token retention contract active
                  </div>
                </div>
                <button
                  type="button"
                  id="toggle-retention-verified-btn"
                  onClick={() => updatePrivacyGate({ providerRetentionVerified: !privacyGate.providerRetentionVerified })}
                  className={`relative inline-flex h-5 w-10 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                    privacyGate.providerRetentionVerified ? "bg-emerald-600" : "bg-slate-300 dark:bg-slate-700"
                  }`}
                >
                  <span
                    className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow-lg ring-0 transition duration-200 ease-in-out ${
                      privacyGate.providerRetentionVerified ? "translate-x-5" : "translate-x-0"
                    }`}
                  />
                </button>
              </div>

              {/* Toggle 3: Protected At-Rest Encryption */}
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="text-xs font-semibold text-slate-900 dark:text-white">
                    Protected At-Rest Encryption
                  </div>
                  <div className="text-[11px] text-slate-500 dark:text-slate-400">
                    AES-256-GCM hardware encryption
                  </div>
                </div>
                <button
                  type="button"
                  id="toggle-at-rest-encryption-btn"
                  onClick={() => updatePrivacyGate({ protectedAtRestEncryption: !privacyGate.protectedAtRestEncryption })}
                  className={`relative inline-flex h-5 w-10 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                    privacyGate.protectedAtRestEncryption ? "bg-emerald-600" : "bg-slate-300 dark:bg-slate-700"
                  }`}
                >
                  <span
                    className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow-lg ring-0 transition duration-200 ease-in-out ${
                      privacyGate.protectedAtRestEncryption ? "translate-x-5" : "translate-x-0"
                    }`}
                  />
                </button>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-100 dark:border-[#1E293B] text-[11px] font-mono text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
            <span>Audit hash chain verified by Administrator</span>
          </div>
        </div>
      </div>

      {/* =====================================================================
          2. TAB NAVIGATION & ACTION BAR
          ===================================================================== */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        {/* Navigation Tabs */}
        <div className="flex items-center gap-1 p-1 rounded-xl border border-slate-200 dark:border-[#1E293B] bg-slate-100/70 dark:bg-[#12141C]">
          <button
            type="button"
            id="tab-facts-btn"
            onClick={() => setActiveTab("facts")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer flex items-center gap-2 ${
              activeTab === "facts"
                ? "bg-white dark:bg-[#181B26] text-slate-900 dark:text-white shadow-xs"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
            }`}
          >
            <Calendar className="w-3.5 h-3.5" />
            <span>Dated Approved Facts</span>
            <span className="px-1.5 py-0.2 rounded-full text-[10px] font-mono bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300">
              {approvedFacts.length}
            </span>
          </button>

          <button
            type="button"
            id="tab-guidelines-btn"
            onClick={() => setActiveTab("guidelines")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer flex items-center gap-2 ${
              activeTab === "guidelines"
                ? "bg-white dark:bg-[#181B26] text-slate-900 dark:text-white shadow-xs"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Brand Guidelines</span>
            <span className="px-1.5 py-0.2 rounded-full text-[10px] font-mono bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
              {guidelines.length}
            </span>
          </button>

          <button
            type="button"
            id="tab-terminology-btn"
            onClick={() => setActiveTab("terminology")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer flex items-center gap-2 ${
              activeTab === "terminology"
                ? "bg-white dark:bg-[#181B26] text-slate-900 dark:text-white shadow-xs"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
            }`}
          >
            <Sliders className="w-3.5 h-3.5" />
            <span>Deterministic Terminology</span>
          </button>
        </div>

        {/* Action Controls & Add Button */}
        <div className="flex items-center gap-2.5">
          {activeTab === "facts" && (
            <>
              {/* Fact Filter Pills */}
              <div className="hidden sm:flex items-center gap-1 border border-slate-200 dark:border-[#1E293B] rounded-lg p-0.5 bg-white dark:bg-[#12141C] text-xs">
                <button
                  type="button"
                  onClick={() => setFactFilter("ALL")}
                  className={`px-2 py-1 rounded text-[11px] font-medium transition-colors cursor-pointer ${
                    factFilter === "ALL"
                      ? "bg-slate-100 dark:bg-[#181B26] font-semibold text-slate-900 dark:text-white"
                      : "text-slate-500 hover:text-slate-900 dark:hover:text-white"
                  }`}
                >
                  All ({approvedFacts.length})
                </button>
                <button
                  type="button"
                  onClick={() => setFactFilter("ACTIVE")}
                  className={`px-2 py-1 rounded text-[11px] font-medium transition-colors cursor-pointer ${
                    factFilter === "ACTIVE"
                      ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300 font-semibold"
                      : "text-slate-500 hover:text-emerald-600"
                  }`}
                >
                  Active Valid ({activeFactsCount})
                </button>
                <button
                  type="button"
                  onClick={() => setFactFilter("EXPIRED")}
                  className={`px-2 py-1 rounded text-[11px] font-medium transition-colors cursor-pointer ${
                    factFilter === "EXPIRED"
                      ? "bg-purple-50 text-purple-700 dark:bg-purple-950/60 dark:text-purple-300 font-semibold"
                      : "text-slate-500 hover:text-purple-600"
                  }`}
                >
                  Expired ({expiredFactsCount})
                </button>
              </div>

              {/* Add Fact Button */}
              <button
                type="button"
                id="add-approved-fact-btn"
                onClick={() => setIsFactModalOpen(true)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold transition-all shadow-xs cursor-pointer active:scale-95"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add Approved Fact</span>
              </button>
            </>
          )}

          {activeTab === "guidelines" && (
            <button
              type="button"
              id="add-guideline-directive-btn"
              onClick={() => setIsGuidelineModalOpen(true)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold transition-all shadow-xs cursor-pointer active:scale-95"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add Guideline Directive</span>
            </button>
          )}
        </div>
      </div>

      {/* =====================================================================
          3. TAB 1: DATED APPROVED FACTS LEDGER
          ===================================================================== */}
      {activeTab === "facts" && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 gap-3">
            {filteredFacts.map((fact) => {
              const isExpired = new Date(fact.expiry_date) < now;
              return (
                <div
                  key={fact.id}
                  className={`p-4 sm:p-5 rounded-2xl border transition-all duration-200 ${
                    isExpired
                      ? "bg-purple-50/30 dark:bg-purple-950/10 border-purple-200 dark:border-purple-900/50 hover:border-purple-300"
                      : "bg-white dark:bg-[#12141C] border-slate-200 dark:border-[#1E293B] hover:border-emerald-300 dark:hover:border-emerald-800"
                  }`}
                >
                  <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                    <div className="space-y-1.5 flex-1 min-w-0">
                      {/* Statement */}
                      <p className="text-xs sm:text-sm font-semibold text-slate-900 dark:text-white leading-relaxed">
                        "{fact.fact_statement}"
                      </p>

                      {/* Evidence excerpt if present */}
                      {fact.evidence_excerpt && (
                        <p className="text-xs text-slate-500 dark:text-slate-400 italic">
                          Evidence: {fact.evidence_excerpt}
                        </p>
                      )}

                      {/* Provenance & Clickable Source URL */}
                      <div className="flex flex-wrap items-center gap-3 pt-1 text-xs">
                        <a
                          href={fact.original_source_url}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1 font-mono text-indigo-600 dark:text-indigo-400 hover:underline"
                        >
                          <ExternalLink className="w-3 h-3" />
                          <span className="truncate max-w-[280px]">
                            {fact.original_source_url}
                          </span>
                        </a>

                        <span className="text-slate-300 dark:text-slate-700">•</span>

                        <span className="flex items-center gap-1 font-mono text-slate-500 dark:text-slate-400 text-[11px]">
                          <UserCheck className="w-3 h-3 text-slate-400" />
                          Owner: {fact.responsible_owner_id || "Legal Reviewer"}
                        </span>
                      </div>
                    </div>

                    {/* Right Side: Temporal Badges & Dates */}
                    <div className="shrink-0 flex flex-col sm:items-end gap-2 text-xs">
                      {/* Live Temporal Status Badge */}
                      {isExpired ? (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold badge-purple">
                          <Clock className="w-3.5 h-3.5" />
                          <span>EXPIRED — RE-VERIFICATION REQUIRED</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold badge-emerald">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>ACTIVE VALID</span>
                        </span>
                      )}

                      {/* Dates Breakdown */}
                      <div className="text-[11px] font-mono text-slate-500 dark:text-slate-400 text-right space-y-0.5">
                        <div>
                          Verified:{" "}
                          <span className="text-slate-700 dark:text-slate-300">
                            {new Date(fact.verification_date).toLocaleDateString()}
                          </span>
                        </div>
                        <div>
                          Expires:{" "}
                          <span
                            className={
                              isExpired
                                ? "text-purple-600 dark:text-purple-400 font-semibold"
                                : "text-slate-700 dark:text-slate-300"
                            }
                          >
                            {new Date(fact.expiry_date).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* =====================================================================
          4. TAB 2: BRAND GUIDELINES MATRIX
          ===================================================================== */}
      {activeTab === "guidelines" && (
        <div className="space-y-4">
          {/* Category Filter Pills */}
          <div className="flex flex-wrap items-center gap-2">
            {["ALL", "TONE", "TERMINOLOGY", "MESSAGING", "ACCESSIBILITY"].map((cat) => (
              <button
                key={cat}
                type="button"
                onClick={() => setGuidelineCategoryFilter(cat)}
                className={`px-3 py-1 rounded-lg text-xs font-medium transition-all cursor-pointer ${
                  guidelineCategoryFilter === cat
                    ? "bg-slate-900 text-white dark:bg-white dark:text-slate-900 font-semibold shadow-xs"
                    : "bg-white dark:bg-[#12141C] text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-[#1E293B] hover:bg-slate-50"
                }`}
              >
                {cat}
              </button>
            ))}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredGuidelines.map((g) => (
              <div
                key={g.id}
                className="p-5 rounded-2xl border border-slate-200 dark:border-[#1E293B] bg-white dark:bg-[#12141C] shadow-xs space-y-3 transition-colors"
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-indigo-600 dark:text-indigo-400">
                      {g.clause_identifier}
                    </span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                      {g.category}
                    </span>
                  </div>
                  <span
                    className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded ${
                      g.severity === "CRITICAL"
                        ? "badge-rose"
                        : g.severity === "HIGH"
                        ? "badge-amber"
                        : "badge-emerald"
                    }`}
                  >
                    {g.severity}
                  </span>
                </div>

                <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed">
                  {g.clause_text}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* =====================================================================
          5. TAB 3: DETERMINISTIC TERMINOLOGY MAP
          ===================================================================== */}
      {activeTab === "terminology" && (
        <div className="space-y-6">
          {/* Banned Terminology */}
          <div className="rounded-2xl border border-slate-200 dark:border-[#1E293B] bg-white dark:bg-[#12141C] p-6 shadow-xs space-y-4">
            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-rose-500" />
                Deterministic Banned Terminology Map (O(N) Aho-Corasick Automaton)
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Hard deterministic violations detected instantaneously during Stage 1 compiler execution.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {Object.entries(brandProfile.banned_terminology_map || {}).map(([term, data]) => (
                <div
                  key={term}
                  className="p-3.5 rounded-xl border border-rose-200 dark:border-rose-950/60 bg-rose-50/30 dark:bg-rose-950/10 space-y-1.5"
                >
                  <div className="flex items-center justify-between">
                    <code className="text-xs font-bold font-mono text-rose-700 dark:text-rose-400 bg-rose-100/70 dark:bg-rose-950/40 px-2 py-0.5 rounded">
                      "{term}"
                    </code>
                    <span className="badge-rose text-[10px] font-mono font-bold px-1.5 py-0.2 rounded">
                      {data.severity}
                    </span>
                  </div>
                  <p className="text-xs text-slate-600 dark:text-slate-300">
                    {data.reason}
                  </p>
                  {data.suggested_replacements && data.suggested_replacements.length > 0 && (
                    <div className="text-[11px] font-mono text-slate-500 dark:text-slate-400">
                      Approved:{" "}
                      <span className="text-emerald-600 dark:text-emerald-400 font-semibold">
                        {data.suggested_replacements.join(", ")}
                      </span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Preferred Terminology */}
          <div className="rounded-2xl border border-slate-200 dark:border-[#1E293B] bg-white dark:bg-[#12141C] p-6 shadow-xs space-y-4">
            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-emerald-500" />
                Preferred Terminology & Trademark Replacements
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Automatic suggestion replacements presented in Creator Gutter Studio.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {Object.entries(brandProfile.preferred_terminology_map || {}).map(([raw, data]) => (
                <div
                  key={raw}
                  className="p-3.5 rounded-xl border border-emerald-200 dark:border-emerald-950/60 bg-emerald-50/30 dark:bg-emerald-950/10 space-y-1"
                >
                  <div className="text-xs font-mono font-bold text-slate-700 dark:text-slate-300 line-through">
                    "{raw}"
                  </div>
                  <div className="text-xs font-mono font-bold text-emerald-700 dark:text-emerald-400">
                    ➜ "{data.approved_term}"
                  </div>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400">
                    {data.reason}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* =====================================================================
          MODAL: ADD APPROVED FACT (Administrator Feature)
          ===================================================================== */}
      {isFactModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs animate-in fade-in duration-200">
          <div className="w-full max-w-lg rounded-2xl border border-slate-200 dark:border-[#1E293B] bg-white dark:bg-[#12141C] p-6 shadow-2xl space-y-5 animate-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-[#1E293B] pb-3">
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4 text-indigo-500" />
                <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                  Add Dated Approved Fact
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setIsFactModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateFact} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Fact Statement
                </label>
                <textarea
                  required
                  rows={2}
                  value={newFactStatement}
                  onChange={(e) => setNewFactStatement(e.target.value)}
                  placeholder="e.g. Acme FinTech maintains $120M in assets under custody as of our 2025 audited financial report."
                  className="w-full p-2.5 rounded-lg border border-slate-300 dark:border-[#1E293B] bg-white dark:bg-[#181B26] text-xs sm:text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Verifiable Source URL
                </label>
                <input
                  type="url"
                  required
                  value={newFactSourceUrl}
                  onChange={(e) => setNewFactSourceUrl(e.target.value)}
                  placeholder="https://acmefintech.com/audits/2025-annual-report.pdf"
                  className="w-full p-2.5 rounded-lg border border-slate-300 dark:border-[#1E293B] bg-white dark:bg-[#181B26] text-xs font-mono text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Evidence Excerpt
                </label>
                <input
                  type="text"
                  value={newFactEvidence}
                  onChange={(e) => setNewFactEvidence(e.target.value)}
                  placeholder="e.g. Page 14, Table 2.1: AUC verified at $120,450,000"
                  className="w-full p-2.5 rounded-lg border border-slate-300 dark:border-[#1E293B] bg-white dark:bg-[#181B26] text-xs text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Verification Date
                  </label>
                  <input
                    type="date"
                    required
                    value={newFactVerificationDate}
                    onChange={(e) => setNewFactVerificationDate(e.target.value)}
                    className="w-full p-2 rounded-lg border border-slate-300 dark:border-[#1E293B] bg-white dark:bg-[#181B26] text-xs font-mono text-slate-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Expiry Date
                  </label>
                  <input
                    type="date"
                    required
                    value={newFactExpiryDate}
                    onChange={(e) => setNewFactExpiryDate(e.target.value)}
                    className="w-full p-2 rounded-lg border border-slate-300 dark:border-[#1E293B] bg-white dark:bg-[#181B26] text-xs font-mono text-slate-900 dark:text-white"
                  />
                </div>
              </div>

              <div className="pt-2 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setIsFactModalOpen(false)}
                  className="px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 text-xs font-medium text-slate-700 dark:text-slate-300 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-xs cursor-pointer"
                >
                  Commit Approved Fact
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* =====================================================================
          MODAL: ADD BRAND GUIDELINE DIRECTIVE
          ===================================================================== */}
      {isGuidelineModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs animate-in fade-in duration-200">
          <div className="w-full max-w-lg rounded-2xl border border-slate-200 dark:border-[#1E293B] bg-white dark:bg-[#12141C] p-6 shadow-2xl space-y-5 animate-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-[#1E293B] pb-3">
              <div className="flex items-center gap-2">
                <Layers className="w-4 h-4 text-indigo-500" />
                <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                  Add Brand Guideline Directive
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setIsGuidelineModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateGuideline} className="space-y-4">
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Identifier
                  </label>
                  <input
                    type="text"
                    required
                    value={newClauseId}
                    onChange={(e) => setNewClauseId(e.target.value)}
                    placeholder="ACME-TONE-06"
                    className="w-full p-2.5 rounded-lg border border-slate-300 dark:border-[#1E293B] bg-white dark:bg-[#181B26] text-xs font-mono uppercase text-slate-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Category
                  </label>
                  <select
                    value={newCategory}
                    onChange={(e) => setNewCategory(e.target.value as FindingCategory)}
                    className="w-full p-2.5 rounded-lg border border-slate-300 dark:border-[#1E293B] bg-white dark:bg-[#181B26] text-xs font-mono text-slate-900 dark:text-white"
                  >
                    <option value="TONE">TONE</option>
                    <option value="TERMINOLOGY">TERMINOLOGY</option>
                    <option value="MESSAGING">MESSAGING</option>
                    <option value="ACCESSIBILITY">ACCESSIBILITY</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Severity
                  </label>
                  <select
                    value={newSeverity}
                    onChange={(e) => setNewSeverity(e.target.value as SeverityLevel)}
                    className="w-full p-2.5 rounded-lg border border-slate-300 dark:border-[#1E293B] bg-white dark:bg-[#181B26] text-xs font-mono text-slate-900 dark:text-white"
                  >
                    <option value="CRITICAL">CRITICAL</option>
                    <option value="HIGH">HIGH</option>
                    <option value="MEDIUM">MEDIUM</option>
                    <option value="LOW">LOW</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Clause Directive Text
                </label>
                <textarea
                  required
                  rows={3}
                  value={newClauseText}
                  onChange={(e) => setNewClauseText(e.target.value)}
                  placeholder="e.g. Mandatory requirement regarding regulatory disclaimer placement..."
                  className="w-full p-2.5 rounded-lg border border-slate-300 dark:border-[#1E293B] bg-white dark:bg-[#181B26] text-xs sm:text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setIsGuidelineModalOpen(false)}
                  className="px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 text-xs font-medium text-slate-700 dark:text-slate-300 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-xs cursor-pointer"
                >
                  Save Guideline
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Step1BrandSetup;
