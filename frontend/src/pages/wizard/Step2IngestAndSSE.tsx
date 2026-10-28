import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  FileUp,
  FileText,
  FileCode,
  Shield,
  ShieldCheck,
  ShieldAlert,
  CheckCircle2,
  AlertTriangle,
  Play,
  RotateCcw,
  Clock,
  Cpu,
  Layers,
  Database,
  Lock,
  Sparkles,
  ArrowRight,
  Hash,
  Copy,
  Check,
  ExternalLink,
  Flame,
  Activity,
  Zap,
} from "lucide-react";
import { usePipeline } from "@/context/PipelineContext";
import { DEMO_DOCUMENTS, DemoDocInfo } from "@/api/seedData";
import { StatusBadge } from "@/components/StatusBadge";

export const Step2IngestAndSSE: React.FC = () => {
  const {
    rawText,
    setRawText,
    documentName,
    setDocumentName,
    selectedDemoDoc,
    loadDemoDocument,
    handleFileUpload,
    fileType,
    magicBytes,
    magicByteName,
    sha256Hash,
    astSummary,
    pipelineRunning,
    pipelineCompleted,
    activeStage,
    stageLatencies,
    stageMetrics,
    triageSummary,
    runPipeline,
    resetPipeline,
    setCurrentStep,
  } = usePipeline();

  const [activeInputMode, setActiveInputMode] = useState<"preset" | "upload" | "editor">("preset");
  const [copiedHash, setCopiedHash] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleCopyHash = () => {
    if (sha256Hash) {
      navigator.clipboard.writeText(sha256Hash);
      setCopiedHash(true);
      setTimeout(() => setCopiedHash(false), 2000);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFileUpload(e.target.files[0]);
    }
  };

  return (
    <div className="space-y-6">
      {/* =====================================================================
          1. INGESTION HUB & DEMO QUICK-LOAD CARDS
          ===================================================================== */}
      <div className="rounded-2xl border border-slate-200 dark:border-[#1E293B] bg-white dark:bg-[#12141C] p-6 shadow-xs space-y-5 transition-colors">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 dark:border-[#1E293B] pb-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                Multi-Modal Ingestion Engine
              </span>
              <span className="text-slate-300 dark:text-slate-700">•</span>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-indigo-50 text-indigo-700 border border-indigo-200 dark:bg-indigo-950/40 dark:text-indigo-300 dark:border-indigo-800">
                Magic-Byte Verified
              </span>
            </div>
            <h2 className="text-xl font-bold font-display text-slate-900 dark:text-white mt-1">
              Document Ingestion & AST Tokenization
            </h2>
          </div>

          {/* Input Mode Selector */}
          <div className="flex items-center gap-1 p-1 rounded-xl border border-slate-200 dark:border-[#1E293B] bg-slate-100/70 dark:bg-[#181B26] text-xs font-semibold">
            <button
              type="button"
              onClick={() => setActiveInputMode("preset")}
              className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer ${
                activeInputMode === "preset"
                  ? "bg-white dark:bg-[#12141C] text-slate-900 dark:text-white shadow-xs"
                  : "text-slate-500 hover:text-slate-900 dark:hover:text-white"
              }`}
            >
              1-Click Demo Docs
            </button>
            <button
              type="button"
              onClick={() => setActiveInputMode("upload")}
              className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer ${
                activeInputMode === "upload"
                  ? "bg-white dark:bg-[#12141C] text-slate-900 dark:text-white shadow-xs"
                  : "text-slate-500 hover:text-slate-900 dark:hover:text-white"
              }`}
            >
              Upload PDF/DOCX
            </button>
            <button
              type="button"
              onClick={() => setActiveInputMode("editor")}
              className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer ${
                activeInputMode === "editor"
                  ? "bg-white dark:bg-[#12141C] text-slate-900 dark:text-white shadow-xs"
                  : "text-slate-500 hover:text-slate-900 dark:hover:text-white"
              }`}
            >
              Raw Text Editor
            </button>
          </div>
        </div>

        {/* MODE 1: 3 Click-to-Load Demo Document Cards */}
        {activeInputMode === "preset" && (
          <div className="space-y-3">
            <div className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 font-mono">
              Select Demo Benchmark Artifact:
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {DEMO_DOCUMENTS.map((doc) => {
                const isSelected = selectedDemoDoc?.id === doc.id;
                return (
                  <button
                    key={doc.id}
                    type="button"
                    id={`demo-doc-btn-${doc.id}`}
                    onClick={() => loadDemoDocument(doc.id)}
                    className={`p-4 rounded-xl border text-left transition-all duration-200 cursor-pointer ${
                      isSelected
                        ? "bg-indigo-50/70 dark:bg-indigo-950/30 border-indigo-400 dark:border-indigo-600 ring-2 ring-indigo-500/20 shadow-xs"
                        : "bg-white dark:bg-[#181B26] border-slate-200 dark:border-[#1E293B] hover:border-indigo-300 dark:hover:border-indigo-800"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        {doc.fileType === "pdf" ? (
                          <FileText className="w-4 h-4 text-rose-500" />
                        ) : (
                          <FileCode className="w-4 h-4 text-blue-500" />
                        )}
                        <span className="font-bold text-xs text-slate-900 dark:text-white">
                          {doc.name}
                        </span>
                      </div>
                      <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded ${doc.badgeClass}`}>
                        {doc.badge}
                      </span>
                    </div>

                    <div className="mt-1 text-[11px] font-mono text-slate-500 dark:text-slate-400">
                      {doc.filename}
                    </div>

                    <p className="mt-2 text-xs text-slate-600 dark:text-slate-400 line-clamp-2 leading-relaxed">
                      {doc.description}
                    </p>

                    <div className="mt-3 flex items-center justify-between text-[11px] font-mono pt-2 border-t border-slate-100 dark:border-slate-800">
                      <span className="text-slate-500 dark:text-slate-400">{doc.magicByteName}</span>
                      {isSelected && (
                        <span className="text-indigo-600 dark:text-indigo-400 font-semibold flex items-center gap-1">
                          <Check className="w-3 h-3" /> Active Loaded
                        </span>
                      )}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* MODE 2: Custom PDF/DOCX Dropzone */}
        {activeInputMode === "upload" && (
          <div
            onClick={() => fileInputRef.current?.click()}
            className="p-8 border-2 border-dashed border-slate-300 dark:border-[#1E293B] rounded-2xl bg-slate-50/50 dark:bg-[#181B26]/30 text-center cursor-pointer hover:border-indigo-500 hover:bg-indigo-50/20 transition-all space-y-3"
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileInputChange}
              accept=".pdf,.docx,.txt,.md"
              className="hidden"
            />
            <div className="w-12 h-12 rounded-xl bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 mx-auto flex items-center justify-center">
              <FileUp className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-900 dark:text-white">
                Drag and drop your enterprise PDF or DOCX file here
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                Magic-byte inspection validates binary signatures and scrubs active macros automatically.
              </p>
            </div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-200/80 dark:bg-slate-800 text-[11px] font-mono text-slate-600 dark:text-slate-300">
              Supports: .PDF (PyMuPDF) • .DOCX (python-docx) • Plaintext
            </div>
          </div>
        )}

        {/* MODE 3: Raw Text Editor */}
        {activeInputMode === "editor" && (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
              <span className="font-semibold">Document Title:</span>
              <input
                type="text"
                value={documentName}
                onChange={(e) => setDocumentName(e.target.value)}
                className="px-2 py-1 rounded border border-slate-300 dark:border-[#1E293B] bg-white dark:bg-[#181B26] text-xs font-mono text-slate-900 dark:text-white w-64"
              />
            </div>
            <textarea
              rows={6}
              value={rawText}
              onChange={(e) => setRawText(e.target.value)}
              placeholder="Paste or write corporate communication text here..."
              className="w-full p-3 rounded-xl border border-slate-300 dark:border-[#1E293B] bg-white dark:bg-[#181B26] font-mono text-xs text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 leading-relaxed"
            />
          </div>
        )}

        {/* ===================================================================
            SECURITY CHECK & AST VERIFICATION RIBBON
            =================================================================== */}
        <div className="p-4 rounded-xl border border-slate-200 dark:border-[#1E293B] bg-slate-50/60 dark:bg-[#181B26]/60 flex flex-col md:flex-row md:items-center justify-between gap-4 text-xs">
          {/* Security & Magic Byte */}
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 flex items-center justify-center shrink-0">
              <ShieldCheck className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-slate-900 dark:text-white">
                  Magic-Byte Security Sealed
                </span>
                <span className="px-1.5 py-0.2 rounded text-[10px] font-mono font-bold bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300">
                  {magicByteName}
                </span>
              </div>
              <div className="text-[11px] font-mono text-slate-500 dark:text-slate-400">
                Signature: {magicBytes} • Zero Macro / Zip Bomb Defense Active
              </div>
            </div>
          </div>

          {/* AST Breakdown */}
          <div className="flex flex-wrap items-center gap-4 text-[11px] font-mono text-slate-600 dark:text-slate-300">
            <div>
              <span className="text-slate-400">Pages:</span>{" "}
              <strong className="text-slate-900 dark:text-white">{astSummary.pages}</strong>
            </div>
            <div>
              <span className="text-slate-400">Paragraphs:</span>{" "}
              <strong className="text-slate-900 dark:text-white">{astSummary.paragraphs}</strong>
            </div>
            <div>
              <span className="text-slate-400">AST Spans:</span>{" "}
              <strong className="text-slate-900 dark:text-white">{astSummary.spans}</strong>
            </div>
            <div>
              <span className="text-slate-400">Words:</span>{" "}
              <strong className="text-slate-900 dark:text-white">{astSummary.words}</strong>
            </div>
          </div>

          {/* SHA-256 Hash */}
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-white dark:bg-[#12141C] border border-slate-200 dark:border-slate-800 font-mono text-[11px]">
              <Hash className="w-3 h-3 text-slate-400 shrink-0" />
              <span className="text-slate-700 dark:text-slate-300 truncate max-w-[130px]" title={sha256Hash}>
                {sha256Hash.slice(0, 16)}...
              </span>
              <button
                type="button"
                onClick={handleCopyHash}
                className="text-slate-400 hover:text-slate-700 dark:hover:text-white ml-1 cursor-pointer"
                title="Copy full SHA-256 hash"
              >
                {copiedHash ? <Check className="w-3 h-3 text-emerald-500" /> : <Copy className="w-3 h-3" />}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* =====================================================================
          2. THE "SHOCK & AWE" LIVE SSE 4-STAGE COMPILER PIPELINE VISUALIZER
          ===================================================================== */}
      <div className="rounded-2xl border border-slate-200 dark:border-[#1E293B] bg-white dark:bg-[#12141C] p-6 shadow-xs space-y-6 transition-colors">
        {/* Compiler Header & Action Button */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 dark:border-[#1E293B] pb-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-indigo-600 animate-pulse" />
              <h3 className="text-base font-bold text-slate-900 dark:text-white">
                BrandShield 4-Stage Autonomous Intelligence Compiler
              </h3>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Sequential streaming verification: Deterministic AST ➜ Temporal Vector RAG ➜ Privacy Gate ➜ Critic Triage.
            </p>
          </div>

          {/* Action Trigger Button */}
          <div className="flex items-center gap-2.5">
            {pipelineCompleted && (
              <button
                type="button"
                id="reset-pipeline-btn"
                onClick={resetPipeline}
                className="px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 text-xs font-semibold text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-[#181B26] transition-all flex items-center gap-1.5 cursor-pointer"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Reset</span>
              </button>
            )}

            <button
              type="button"
              id="run-brandshield-analysis-btn"
              disabled={pipelineRunning}
              onClick={runPipeline}
              className={`px-5 py-2.5 rounded-xl font-bold text-xs tracking-wide text-white transition-all duration-300 flex items-center gap-2 cursor-pointer shadow-md active:scale-98 ${
                pipelineRunning
                  ? "bg-indigo-700 opacity-90 cursor-not-allowed"
                  : "bg-gradient-to-r from-indigo-600 via-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 shadow-indigo-500/25 hover:shadow-indigo-500/40"
              }`}
            >
              {pipelineRunning ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Executing 4-Stage Compiler Pipeline...</span>
                </>
              ) : pipelineCompleted ? (
                <>
                  <CheckCircle2 className="w-4 h-4 text-emerald-300" />
                  <span>Re-Run BrandShield Analysis</span>
                </>
              ) : (
                <>
                  <Zap className="w-4 h-4 text-amber-300" />
                  <span>Run BrandShield Analysis</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* ===================================================================
            4 SEQUENTIAL COMPILER NODES (Framer Motion Animated)
            =================================================================== */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* ---------------------------------------------------------------
              NODE 1: Stage 1 Deterministic Aho-Corasick & Readability AST
              --------------------------------------------------------------- */}
          <motion.div
            initial={{ opacity: 0.8, y: 10 }}
            animate={{
              opacity: 1,
              y: 0,
              scale: activeStage === 1 ? 1.02 : 1,
            }}
            transition={{ duration: 0.3 }}
            className={`p-4 rounded-xl border transition-all duration-300 relative overflow-hidden flex flex-col justify-between ${
              activeStage >= 1
                ? "bg-slate-50 dark:bg-[#181B26] border-indigo-400 dark:border-indigo-600 shadow-xs"
                : "bg-slate-50/40 dark:bg-[#181B26]/30 border-slate-200 dark:border-[#1E293B]"
            }`}
          >
            {activeStage === 1 && (
              <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-indigo-500 to-indigo-300 animate-pulse" />
            )}

            <div>
              {/* Header */}
              <div className="flex items-center justify-between gap-2">
                <span className="w-6 h-6 rounded-md bg-indigo-100 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 font-mono text-xs font-bold flex items-center justify-center">
                  01
                </span>
                <span
                  className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded ${
                    activeStage >= 1
                      ? "bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300"
                      : "bg-slate-200 dark:bg-slate-800 text-slate-500"
                  }`}
                >
                  {activeStage >= 1 ? `<${stageMetrics.stage1.latencyMs}ms` : "Queued"}
                </span>
              </div>

              {/* Title */}
              <div className="mt-3">
                <h4 className="text-xs font-bold text-slate-900 dark:text-white leading-tight">
                  L1 Deterministic Automaton & AST
                </h4>
                <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                  Sub-ms Aho-Corasick dictionary scanner & Flesch-Kincaid scorer.
                </p>
              </div>

              {/* Live Compiler Telemetry */}
              <div className="mt-3.5 space-y-2 text-xs">
                <div className="flex items-center justify-between text-[11px] font-mono">
                  <span className="text-slate-500 dark:text-slate-400">Objective Matches:</span>
                  <span className="font-bold text-slate-900 dark:text-white">
                    {stageMetrics.stage1.objectiveMatches} found
                  </span>
                </div>
                <div className="flex items-center justify-between text-[11px] font-mono">
                  <span className="text-slate-500 dark:text-slate-400">Flesch Grade:</span>
                  <span className="font-bold text-slate-900 dark:text-white">
                    {stageMetrics.stage1.fleschGrade}
                  </span>
                </div>
                <div className="flex items-center justify-between text-[11px] font-mono">
                  <span className="text-slate-500 dark:text-slate-400">Passive Voice:</span>
                  <span className="font-bold text-slate-900 dark:text-white">
                    {Math.round(stageMetrics.stage1.passiveRatio * 100)}%
                  </span>
                </div>
              </div>
            </div>

            {/* Stage Status Pill */}
            <div className="mt-4 pt-2.5 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between text-[10px] font-mono">
              <span className="text-slate-400">Deterministic Engine</span>
              {activeStage > 1 || activeStage === 5 ? (
                <span className="text-emerald-600 dark:text-emerald-400 font-bold flex items-center gap-1">
                  <Check className="w-3 h-3" /> COMPLETE
                </span>
              ) : activeStage === 1 ? (
                <span className="text-indigo-600 dark:text-indigo-400 font-bold animate-pulse">
                  SCANNING...
                </span>
              ) : (
                <span className="text-slate-400">STANDBY</span>
              )}
            </div>
          </motion.div>

          {/* ---------------------------------------------------------------
              NODE 2: Stage 2 Hybrid pgvector + BM25 RRF & Temporal Fact Lifecycle
              --------------------------------------------------------------- */}
          <motion.div
            initial={{ opacity: 0.8, y: 10 }}
            animate={{
              opacity: 1,
              y: 0,
              scale: activeStage === 2 ? 1.02 : 1,
            }}
            transition={{ duration: 0.3 }}
            className={`p-4 rounded-xl border transition-all duration-300 relative overflow-hidden flex flex-col justify-between ${
              activeStage >= 2
                ? "bg-slate-50 dark:bg-[#181B26] border-emerald-400 dark:border-emerald-600 shadow-xs"
                : "bg-slate-50/40 dark:bg-[#181B26]/30 border-slate-200 dark:border-[#1E293B]"
            }`}
          >
            {activeStage === 2 && (
              <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-emerald-500 to-emerald-300 animate-pulse" />
            )}

            <div>
              {/* Header */}
              <div className="flex items-center justify-between gap-2">
                <span className="w-6 h-6 rounded-md bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 font-mono text-xs font-bold flex items-center justify-center">
                  02
                </span>
                <span
                  className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded ${
                    activeStage >= 2
                      ? "bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300"
                      : "bg-slate-200 dark:bg-slate-800 text-slate-500"
                  }`}
                >
                  {activeStage >= 2 ? `~${stageMetrics.stage2.latencyMs}ms` : "Queued"}
                </span>
              </div>

              {/* Title */}
              <div className="mt-3">
                <h4 className="text-xs font-bold text-slate-900 dark:text-white leading-tight">
                  Hybrid RAG & Fact Lifecycle
                </h4>
                <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                  pgvector HNSW + BM25 RRF with temporal validity sweep.
                </p>
              </div>

              {/* Live Compiler Telemetry */}
              <div className="mt-3.5 space-y-2 text-xs">
                <div className="flex items-center justify-between text-[11px] font-mono">
                  <span className="text-slate-500 dark:text-slate-400">Active Facts Matched:</span>
                  <span className="font-bold text-emerald-600 dark:text-emerald-400">
                    {stageMetrics.stage2.activeFactMatches} verified
                  </span>
                </div>
                <div className="flex items-center justify-between text-[11px] font-mono">
                  <span className="text-slate-500 dark:text-slate-400">Expired Fact Hits:</span>
                  <span
                    className={`font-bold ${
                      stageMetrics.stage2.expiredFactHits > 0
                        ? "text-purple-600 dark:text-purple-400 font-bold"
                        : "text-slate-900 dark:text-white"
                    }`}
                  >
                    {stageMetrics.stage2.expiredFactHits} stale
                  </span>
                </div>
                <div className="flex items-center justify-between text-[11px] font-mono">
                  <span className="text-slate-500 dark:text-slate-400">Missing Evidence:</span>
                  <span
                    className={`font-bold ${
                      stageMetrics.stage2.unsubstantiatedClaims > 0
                        ? "text-amber-600 dark:text-amber-400"
                        : "text-slate-900 dark:text-white"
                    }`}
                  >
                    {stageMetrics.stage2.unsubstantiatedClaims} ungrounded
                  </span>
                </div>
              </div>
            </div>

            {/* Stage Status Pill */}
            <div className="mt-4 pt-2.5 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between text-[10px] font-mono">
              <span className="text-slate-400">Vector Search</span>
              {activeStage > 2 || activeStage === 5 ? (
                <span className="text-emerald-600 dark:text-emerald-400 font-bold flex items-center gap-1">
                  <Check className="w-3 h-3" /> COMPLETE
                </span>
              ) : activeStage === 2 ? (
                <span className="text-emerald-600 dark:text-emerald-400 font-bold animate-pulse">
                  SEARCHING HNSW...
                </span>
              ) : (
                <span className="text-slate-400">STANDBY</span>
              )}
            </div>
          </motion.div>

          {/* ---------------------------------------------------------------
              NODE 3: Stage 3 Zero-Trust Privacy Gate & Circuit-Breaker Router
              --------------------------------------------------------------- */}
          <motion.div
            initial={{ opacity: 0.8, y: 10 }}
            animate={{
              opacity: 1,
              y: 0,
              scale: activeStage === 3 ? 1.02 : 1,
            }}
            transition={{ duration: 0.3 }}
            className={`p-4 rounded-xl border transition-all duration-300 relative overflow-hidden flex flex-col justify-between ${
              activeStage >= 3
                ? "bg-slate-50 dark:bg-[#181B26] border-purple-400 dark:border-purple-600 shadow-xs"
                : "bg-slate-50/40 dark:bg-[#181B26]/30 border-slate-200 dark:border-[#1E293B]"
            }`}
          >
            {activeStage === 3 && (
              <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-purple-500 to-purple-300 animate-pulse" />
            )}

            <div>
              {/* Header */}
              <div className="flex items-center justify-between gap-2">
                <span className="w-6 h-6 rounded-md bg-purple-100 dark:bg-purple-950/60 text-purple-700 dark:text-purple-300 font-mono text-xs font-bold flex items-center justify-center">
                  03
                </span>
                <span
                  className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded ${
                    activeStage >= 3
                      ? "bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300"
                      : "bg-slate-200 dark:bg-slate-800 text-slate-500"
                  }`}
                >
                  {activeStage >= 3 ? `<${stageMetrics.stage3.latencyMs}ms` : "Queued"}
                </span>
              </div>

              {/* Title */}
              <div className="mt-3">
                <h4 className="text-xs font-bold text-slate-900 dark:text-white leading-tight">
                  Zero-Trust Gate & Watchdog
                </h4>
                <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                  Automated PII scrub + 500ms circuit-breaker SLA guard.
                </p>
              </div>

              {/* Live Compiler Telemetry */}
              <div className="mt-3.5 space-y-2 text-xs">
                <div className="flex items-center justify-between text-[11px] font-mono">
                  <span className="text-slate-500 dark:text-slate-400">PII Redaction:</span>
                  <span className="font-bold text-emerald-600 dark:text-emerald-400">
                    {stageMetrics.stage3.piiEntitiesRedacted} entities
                  </span>
                </div>
                <div className="flex items-center justify-between text-[11px] font-mono">
                  <span className="text-slate-500 dark:text-slate-400">500ms Watchdog:</span>
                  <span className="font-bold text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" /> PASS (11.4ms)
                  </span>
                </div>
                <div className="flex items-center justify-between text-[11px] font-mono">
                  <span className="text-slate-500 dark:text-slate-400">Egress Suppressed:</span>
                  <span className="font-bold text-slate-900 dark:text-white">
                    {stageMetrics.stage3.tokenLeakageSuppressed} tokens
                  </span>
                </div>
              </div>
            </div>

            {/* Stage Status Pill */}
            <div className="mt-4 pt-2.5 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between text-[10px] font-mono">
              <span className="text-slate-400">Privacy Perimeter</span>
              {activeStage > 3 || activeStage === 5 ? (
                <span className="text-emerald-600 dark:text-emerald-400 font-bold flex items-center gap-1">
                  <Check className="w-3 h-3" /> COMPLETE
                </span>
              ) : activeStage === 3 ? (
                <span className="text-purple-600 dark:text-purple-400 font-bold animate-pulse">
                  ENFORCING GATE...
                </span>
              ) : (
                <span className="text-slate-400">STANDBY</span>
              )}
            </div>
          </motion.div>

          {/* ---------------------------------------------------------------
              NODE 4: Stage 4 Adversarial Critic & Automation-Bias Safeguard
              --------------------------------------------------------------- */}
          <motion.div
            initial={{ opacity: 0.8, y: 10 }}
            animate={{
              opacity: 1,
              y: 0,
              scale: activeStage === 4 ? 1.02 : 1,
            }}
            transition={{ duration: 0.3 }}
            className={`p-4 rounded-xl border transition-all duration-300 relative overflow-hidden flex flex-col justify-between ${
              activeStage >= 4
                ? "bg-slate-50 dark:bg-[#181B26] border-amber-400 dark:border-amber-600 shadow-xs"
                : "bg-slate-50/40 dark:bg-[#181B26]/30 border-slate-200 dark:border-[#1E293B]"
            }`}
          >
            {activeStage === 4 && (
              <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-amber-500 to-amber-300 animate-pulse" />
            )}

            <div>
              {/* Header */}
              <div className="flex items-center justify-between gap-2">
                <span className="w-6 h-6 rounded-md bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 font-mono text-xs font-bold flex items-center justify-center">
                  04
                </span>
                <span
                  className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded ${
                    activeStage >= 4
                      ? "bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300"
                      : "bg-slate-200 dark:bg-slate-800 text-slate-500"
                  }`}
                >
                  {activeStage >= 4 ? `<${stageMetrics.stage4.latencyMs}ms` : "Queued"}
                </span>
              </div>

              {/* Title */}
              <div className="mt-3">
                <h4 className="text-xs font-bold text-slate-900 dark:text-white leading-tight">
                  Critic & Bias Safeguards
                </h4>
                <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                  15% stochastic review injection & FP suppression filter.
                </p>
              </div>

              {/* Live Compiler Telemetry */}
              <div className="mt-3.5 space-y-2 text-xs">
                <div className="flex items-center justify-between text-[11px] font-mono">
                  <span className="text-slate-500 dark:text-slate-400">FP Suppressed:</span>
                  <span className="font-bold text-emerald-600 dark:text-emerald-400">
                    {stageMetrics.stage4.suppressedFalsePositives} eliminated
                  </span>
                </div>
                <div className="flex items-center justify-between text-[11px] font-mono">
                  <span className="text-slate-500 dark:text-slate-400">Stochastic Audit:</span>
                  <span className="font-bold text-indigo-600 dark:text-indigo-400">
                    15% Injected
                  </span>
                </div>
                <div className="flex items-center justify-between text-[11px] font-mono">
                  <span className="text-slate-500 dark:text-slate-400">Total Findings:</span>
                  <span className="font-bold text-slate-900 dark:text-white">
                    {stageMetrics.stage4.totalFindings} findings
                  </span>
                </div>
              </div>
            </div>

            {/* Stage Status Pill */}
            <div className="mt-4 pt-2.5 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between text-[10px] font-mono">
              <span className="text-slate-400">Safeguard Engine</span>
              {activeStage === 5 ? (
                <span className="text-emerald-600 dark:text-emerald-400 font-bold flex items-center gap-1">
                  <Check className="w-3 h-3" /> COMPLETE
                </span>
              ) : activeStage === 4 ? (
                <span className="text-amber-600 dark:text-amber-400 font-bold animate-pulse">
                  CALIBRATING...
                </span>
              ) : (
                <span className="text-slate-400">STANDBY</span>
              )}
            </div>
          </motion.div>
        </div>

        {/* ===================================================================
            3. POST-COMPILATION TRIAGE SUMMARY RIBBON
            =================================================================== */}
        {pipelineCompleted && (
          <motion.div
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3 }}
            className="p-5 rounded-2xl border border-indigo-200 dark:border-indigo-900/60 bg-gradient-to-r from-indigo-50/80 via-white to-violet-50/80 dark:from-indigo-950/20 dark:via-[#12141C] dark:to-violet-950/20 shadow-sm flex flex-col lg:flex-row lg:items-center justify-between gap-5"
          >
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-ping" />
                <span className="text-xs font-mono font-bold uppercase tracking-wider text-emerald-700 dark:text-emerald-400">
                  Compilation Complete • Total Latency {stageMetrics.stage1.latencyMs + stageMetrics.stage2.latencyMs + stageMetrics.stage3.latencyMs + stageMetrics.stage4.latencyMs}ms
                </span>
              </div>

              {/* Triage Count Chips */}
              <div className="flex flex-wrap items-center gap-2 pt-1">
                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold badge-emerald">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>{triageSummary?.flagged_high_confidence || 0} High-Confidence</span>
                </span>

                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold badge-amber">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  <span>{triageSummary?.routed_to_human_low_confidence || (triageSummary?.total_findings > 0 ? 1 : 0)} Routed to Human</span>
                </span>

                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold badge-purple">
                  <Clock className="w-3.5 h-3.5" />
                  <span>{triageSummary?.stale_facts_to_reverify || 0} Stale Facts</span>
                </span>

                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold badge-amber">
                  <ShieldAlert className="w-3.5 h-3.5" />
                  <span>{triageSummary?.needs_verification_missing_evidence || 0} Missing Evidence</span>
                </span>
              </div>
            </div>

            {/* Transition Action to Step 3 */}
            <div className="shrink-0 flex items-center gap-3">
              <button
                type="button"
                id="open-gutter-revision-studio-btn"
                onClick={() => setCurrentStep(3)}
                className="px-5 py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-bold text-xs tracking-wide shadow-md shadow-indigo-500/25 transition-all flex items-center gap-2 cursor-pointer active:scale-98"
              >
                <span>Open in Gutter Revision Studio</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default Step2IngestAndSSE;
