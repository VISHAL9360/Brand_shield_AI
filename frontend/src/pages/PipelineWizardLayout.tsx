import React from "react";
import {
  Shield,
  Layers,
  FileText,
  FileCheck2,
  BarChart3,
  CheckCircle2,
  ArrowRight,
  ArrowLeft,
  Lock,
  Sparkles,
  Scale,
  Users,
} from "lucide-react";
import { usePipeline } from "@/context/PipelineContext";
import { useAuth } from "@/context/AuthContext";
import { RoleBadge } from "@/components/RoleBadge";
import { Step1BrandSetup } from "./wizard/Step1BrandSetup";
import { Step2IngestAndSSE } from "./wizard/Step2IngestAndSSE";

interface StepConfig {
  number: number;
  id: string;
  title: string;
  subtitle: string;
  requiredRole: "ADMINISTRATOR" | "CREATOR" | "REVIEWER" | "ALL";
  roleLabel: string;
  icon: React.ComponentType<{ className?: string }>;
}

const WIZARD_STEPS: StepConfig[] = [
  {
    number: 1,
    id: "brand-setup",
    title: "Brand & Fact Setup",
    subtitle: "Guidelines, Tone, Dated Facts & Gate",
    requiredRole: "ADMINISTRATOR",
    roleLabel: "Administrator",
    icon: Shield,
  },
  {
    number: 2,
    id: "ingest-compile",
    title: "Document Ingestion & Compiler",
    subtitle: "Upload & Live 4-Stage SSE Visualizer",
    requiredRole: "CREATOR",
    roleLabel: "Creator",
    icon: FileText,
  },
  {
    number: 3,
    id: "gutter-studio",
    title: "Creator Gutter Studio",
    subtitle: "Google Docs-Style In-line Diff & Triage",
    requiredRole: "CREATOR",
    roleLabel: "Creator",
    icon: Layers,
  },
  {
    number: 4,
    id: "reviewer-attestation",
    title: "Reviewer Attestation",
    subtitle: "Diff Inspection, Bias Safeguard & Passport",
    requiredRole: "REVIEWER",
    roleLabel: "Reviewer",
    icon: Scale,
  },
  {
    number: 5,
    id: "governance-analytics",
    title: "Governance & Evaluation",
    subtitle: "Recharts Dashboard & Test Set Benchmarks",
    requiredRole: "ALL",
    roleLabel: "All Roles",
    icon: BarChart3,
  },
];

export const PipelineWizardLayout: React.FC = () => {
  const { currentStep, setCurrentStep, pipelineCompleted } = usePipeline();
  const { user } = useAuth();

  const activeStepConfig = WIZARD_STEPS.find((s) => s.number === currentStep) || WIZARD_STEPS[0];

  const handleNext = () => {
    if (currentStep < 5) {
      setCurrentStep(currentStep + 1);
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  };

  const handlePrev = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6 animate-in fade-in duration-200">
      {/* =====================================================================
          1. HORIZONTAL STRIPE-STYLE INTERACTIVE STEPPER HEADER
          ===================================================================== */}
      <div className="rounded-2xl border border-slate-200 dark:border-[#1E293B] bg-white dark:bg-[#12141C] p-4 sm:p-6 shadow-xs transition-colors">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 dark:border-[#1E293B] pb-4 mb-5">
          <div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse" />
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                End-to-End Governance Lifecycle
              </span>
            </div>
            <h1 className="text-xl sm:text-2xl font-bold font-display text-slate-900 dark:text-white mt-0.5">
              BrandShield AI Governance Pipeline Wizard
            </h1>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500 dark:text-slate-400 font-mono">Current Operator:</span>
            <RoleBadge role={user?.role} size="sm" />
          </div>
        </div>

        {/* The 5-Step Horizontal Stepper Bar */}
        <div className="relative">
          {/* Background Track Line */}
          <div className="hidden lg:block absolute top-1/2 left-8 right-8 h-0.5 -translate-y-4 bg-slate-200 dark:bg-slate-800 pointer-events-none" />

          {/* Stepper Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 relative z-10">
            {WIZARD_STEPS.map((step) => {
              const isActive = step.number === currentStep;
              const isPast = step.number < currentStep || (step.number === 2 && pipelineCompleted);
              const IconComponent = step.icon;

              const roleBadgeClass = {
                ADMINISTRATOR: "bg-purple-100 dark:bg-purple-950/60 text-purple-700 dark:text-purple-300 border-purple-200 dark:border-purple-800",
                CREATOR: "bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800",
                REVIEWER: "bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 border-amber-200 dark:border-amber-800",
                ALL: "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700",
              }[step.requiredRole];

              return (
                <button
                  key={step.id}
                  type="button"
                  id={`wizard-step-btn-${step.number}`}
                  onClick={() => setCurrentStep(step.number)}
                  className={`p-3 rounded-xl border text-left transition-all duration-200 cursor-pointer flex flex-col justify-between ${
                    isActive
                      ? "bg-indigo-50/80 dark:bg-indigo-950/30 border-indigo-400 dark:border-indigo-600 ring-2 ring-indigo-500/20 shadow-xs"
                      : isPast
                      ? "bg-white dark:bg-[#181B26] border-slate-200 dark:border-[#1E293B] hover:border-indigo-300 dark:hover:border-indigo-800"
                      : "bg-slate-50/50 dark:bg-[#12141C]/60 border-slate-200 dark:border-[#1E293B] opacity-75 hover:opacity-100"
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <div
                        className={`w-7 h-7 rounded-lg font-mono text-xs font-bold flex items-center justify-center shrink-0 ${
                          isActive
                            ? "bg-indigo-600 text-white shadow-sm"
                            : isPast
                            ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-950/80 dark:text-emerald-300"
                            : "bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-400"
                        }`}
                      >
                        {isPast ? <CheckCircle2 className="w-4 h-4" /> : `0${step.number}`}
                      </div>
                      <span className="font-bold text-xs text-slate-900 dark:text-white truncate">
                        Step {step.number}
                      </span>
                    </div>

                    <span className={`text-[9px] font-mono font-bold uppercase px-1.5 py-0.2 rounded border ${roleBadgeClass}`}>
                      {step.roleLabel}
                    </span>
                  </div>

                  <div className="mt-2.5">
                    <div className="font-semibold text-xs text-slate-900 dark:text-white leading-tight">
                      {step.title}
                    </div>
                    <div className="text-[10px] text-slate-500 dark:text-slate-400 truncate mt-0.5">
                      {step.subtitle}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Previous & Next Action Ribbon */}
        <div className="mt-5 pt-4 border-t border-slate-100 dark:border-[#1E293B] flex items-center justify-between gap-4">
          <button
            type="button"
            id="wizard-prev-stage-btn"
            disabled={currentStep === 1}
            onClick={handlePrev}
            className="px-3.5 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 text-xs font-semibold text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-[#181B26] transition-all disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1.5 cursor-pointer"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Previous Stage</span>
          </button>

          <div className="text-xs font-mono font-medium text-slate-500 dark:text-slate-400">
            Stage {currentStep} of 5: <span className="text-slate-900 dark:text-white font-semibold">{activeStepConfig.title}</span>
          </div>

          <button
            type="button"
            id="wizard-next-stage-btn"
            disabled={currentStep === 5}
            onClick={handleNext}
            className="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-xs transition-all disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1.5 cursor-pointer active:scale-98"
          >
            <span>Continue to Next Stage</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* =====================================================================
          2. STEP STAGE RENDERER
          ===================================================================== */}
      {currentStep === 1 && <Step1BrandSetup />}
      {currentStep === 2 && <Step2IngestAndSSE />}

      {/* Step 3 Preview */}
      {currentStep === 3 && (
        <div className="rounded-2xl border border-slate-200 dark:border-[#1E293B] bg-white dark:bg-[#12141C] p-8 shadow-xs text-center space-y-4">
          <div className="w-12 h-12 rounded-2xl bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 mx-auto flex items-center justify-center">
            <Layers className="w-6 h-6" />
          </div>
          <div className="max-w-md mx-auto space-y-2">
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">
              Stage 3: Creator Gutter Revision Studio
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
              Google Docs-style side-by-side annotation studio. Resolve findings with 1-click accept, rejection with rationale, or custom editing to produce immutable v2+ revisions.
            </p>
          </div>
          <div className="pt-2 flex justify-center gap-3">
            <button
              type="button"
              onClick={() => setCurrentStep(2)}
              className="px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-700 text-xs font-semibold text-slate-700 dark:text-slate-300 cursor-pointer"
            >
              Back to Compiler Analysis (Stage 2)
            </button>
            <button
              type="button"
              onClick={() => setCurrentStep(4)}
              className="px-4 py-2 rounded-lg bg-indigo-600 text-white text-xs font-semibold cursor-pointer"
            >
              Inspect Reviewer Attestation (Stage 4)
            </button>
          </div>
        </div>
      )}

      {/* Step 4 Preview */}
      {currentStep === 4 && (
        <div className="rounded-2xl border border-slate-200 dark:border-[#1E293B] bg-white dark:bg-[#12141C] p-8 shadow-xs text-center space-y-4">
          <div className="w-12 h-12 rounded-2xl bg-amber-50 dark:bg-amber-950/60 text-amber-600 dark:text-amber-400 mx-auto flex items-center justify-center">
            <Scale className="w-6 h-6" />
          </div>
          <div className="max-w-md mx-auto space-y-2">
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">
              Stage 4: Human Reviewer Sign-Off & Attestation
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
              Token-level diff comparison between revisions v1 and vN, adversarial bias verification, and publication passport generation with SHA-256 Merkle root.
            </p>
          </div>
          <div className="pt-2 flex justify-center gap-3">
            <button
              type="button"
              onClick={() => setCurrentStep(3)}
              className="px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-700 text-xs font-semibold text-slate-700 dark:text-slate-300 cursor-pointer"
            >
              Back to Revision Studio (Stage 3)
            </button>
            <button
              type="button"
              onClick={() => setCurrentStep(5)}
              className="px-4 py-2 rounded-lg bg-indigo-600 text-white text-xs font-semibold cursor-pointer"
            >
              View Governance Analytics (Stage 5)
            </button>
          </div>
        </div>
      )}

      {/* Step 5 Preview */}
      {currentStep === 5 && (
        <div className="rounded-2xl border border-slate-200 dark:border-[#1E293B] bg-white dark:bg-[#12141C] p-8 shadow-xs text-center space-y-4">
          <div className="w-12 h-12 rounded-2xl bg-violet-50 dark:bg-violet-950/60 text-violet-600 dark:text-violet-400 mx-auto flex items-center justify-center">
            <BarChart3 className="w-6 h-6" />
          </div>
          <div className="max-w-md mx-auto space-y-2">
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">
              Stage 5: Governance & Evaluation Analytics
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
              Zero-transformation Recharts executive analytics: category bars, triage pie charts, 7-day review trendlines, audit hash chain verification, and 100-sample test set benchmarks.
            </p>
          </div>
          <div className="pt-2 flex justify-center gap-3">
            <button
              type="button"
              onClick={() => setCurrentStep(1)}
              className="px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-700 text-xs font-semibold text-slate-700 dark:text-slate-300 cursor-pointer"
            >
              Restart Pipeline from Brand Setup
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default PipelineWizardLayout;
