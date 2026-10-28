import { BrandProfile, BrandGuideline, ApprovedFact, Finding } from "./brandshieldClient";

export const DEFAULT_BRAND_PROFILE: BrandProfile = {
  id: "bp-acme-fintech-global-001",
  workspace_id: "ws-acme-global-brand-001",
  name: "Acme FinTech Global Profile",
  description: "Enterprise compliance, deterministic terminology matrix, and zero-trust privacy policy for Acme FinTech Global.",
  tone_parameters: {
    target_formality: 8.5,
    max_grade_level: 12.0,
    max_passive_voice_ratio: 0.15,
    forbidden_sentiments: ["hyperbolic", "casual_slang", "hype", "uncalibrated_superlatives"],
  },
  banned_terminology_map: {
    "100% risk-free": {
      reason: "Prohibited absolute superlative risk-free guarantee under SEC / FINRA rules.",
      severity: "CRITICAL",
      suggested_replacements: ["institutionally hedged", "risk-managed architecture"],
    },
    "risk-free": {
      reason: "Absolute risk-free guarantees are prohibited in institutional financial products.",
      severity: "CRITICAL",
      suggested_replacements: ["hedged", "collateral-backed"],
    },
    "guaranteed monopoly": {
      reason: "Unlawful antitrust and anti-competitive guarantee.",
      severity: "CRITICAL",
      suggested_replacements: ["industry leadership", "strong institutional presence"],
    },
    "cure": {
      reason: "Medical and therapeutic metaphors prohibited in financial documentation.",
      severity: "HIGH",
      suggested_replacements: ["mitigate", "resolve", "address"],
    },
    "crypto casino": {
      reason: "Prohibited gambling and speculative terminology in institutional collateral docs.",
      severity: "CRITICAL",
      suggested_replacements: ["digital asset clearing network"],
    },
    "foolproof": {
      reason: "Absolute infallibility claim prohibited under marketing guidelines.",
      severity: "HIGH",
      suggested_replacements: ["resilient", "fault-tolerant"],
    },
    "unbeatable": {
      reason: "Unsubstantiated competitive superlative without audited empirical benchmark.",
      severity: "HIGH",
      suggested_replacements: ["highly competitive", "industry-leading"],
    },
    "crazy fast": {
      reason: "Informal hyperbolic colloquialism violates professional B2B executive tone.",
      severity: "MEDIUM",
      suggested_replacements: ["sub-millisecond throughput", "ultra-low latency"],
    },
  },
  preferred_terminology_map: {
    "Acme FinTech": {
      approved_term: "Acme FinTech™",
      reason: "Requires registered trademark symbol on first or primary brand reference.",
      severity: "HIGH",
    },
    "cheap": {
      approved_term: "cost-effective",
      reason: "Maintain executive market positioning.",
      severity: "MEDIUM",
    },
    "fast": {
      approved_term: "high-throughput",
      reason: "Maintain technical precision and rigor.",
      severity: "LOW",
    },
  },
  messaging_rules: {
    required_disclaimers: [
      "Capital at risk. Past performance is not indicative of future results.",
      "Investments are subject to market volatility. Tier-1 bank settlement only.",
    ],
    regulatory_framework: "SEC / FINRA / FCA / MiFID II",
  },
  privacy_gate_config: {
    allow_external_llm: false,
    contract_verified_at: "2026-01-15T09:00:00Z",
    approved_providers: ["Azure OpenAI (Zero-Data-Retention)", "Anthropic (Commercial VPC)"],
    retention_days: 0,
  },
  is_active: true,
  created_at: "2026-01-01T00:00:00Z",
};

export const DEFAULT_GUIDELINES: BrandGuideline[] = [
  // Tone
  {
    id: "g-tone-01",
    brand_profile_id: "bp-acme-fintech-global-001",
    clause_identifier: "ACME-TONE-01",
    clause_text: "Maintain an authoritative, objective B2B executive tone. Target formality score of 8/10 or higher across all commercial disclosures.",
    category: "TONE",
    severity: "MEDIUM",
    created_at: "2026-01-10T12:00:00Z",
  },
  {
    id: "g-tone-02",
    brand_profile_id: "bp-acme-fintech-global-001",
    clause_identifier: "ACME-TONE-02",
    clause_text: "Favor active voice construction. Passive voice must not exceed 15% of total sentence count in any document section.",
    category: "TONE",
    severity: "LOW",
    created_at: "2026-01-10T12:00:00Z",
  },
  {
    id: "g-tone-03",
    brand_profile_id: "bp-acme-fintech-global-001",
    clause_identifier: "ACME-TONE-03",
    clause_text: "Prohibit hyperbolic promotional slang and informal colloquialisms such as 'crazy', 'insane', 'left in the dust', or 'blown away'.",
    category: "TONE",
    severity: "HIGH",
    created_at: "2026-01-10T12:00:00Z",
  },
  // Terminology
  {
    id: "g-term-01",
    brand_profile_id: "bp-acme-fintech-global-001",
    clause_identifier: "ACME-TERM-01",
    clause_text: "All references to the primary brand 'Acme FinTech' must incorporate the trademark symbol 'Acme FinTech™'.",
    category: "TERMINOLOGY",
    severity: "HIGH",
    created_at: "2026-01-10T12:00:00Z",
  },
  {
    id: "g-term-02",
    brand_profile_id: "bp-acme-fintech-global-001",
    clause_identifier: "ACME-TERM-02",
    clause_text: "Absolute risk-free superlatives ('100% risk-free', 'zero risk guarantee', 'guaranteed monopoly') are strictly prohibited.",
    category: "TERMINOLOGY",
    severity: "CRITICAL",
    created_at: "2026-01-10T12:00:00Z",
  },
  {
    id: "g-term-03",
    brand_profile_id: "bp-acme-fintech-global-001",
    clause_identifier: "ACME-TERM-03",
    clause_text: "Medical, therapeutic, and gaming metaphors ('cure', 'panacea', 'crypto casino') are prohibited across all whitepapers.",
    category: "TERMINOLOGY",
    severity: "HIGH",
    created_at: "2026-01-10T12:00:00Z",
  },
  // Messaging
  {
    id: "g-msg-01",
    brand_profile_id: "bp-acme-fintech-global-001",
    clause_identifier: "ACME-MSG-01",
    clause_text: "Every public commercial announcement or partnership briefing must incorporate the mandatory disclaimer: 'Capital at risk. Past performance is not indicative of future results.'",
    category: "MESSAGING",
    severity: "HIGH",
    created_at: "2026-01-10T12:00:00Z",
  },
  {
    id: "g-msg-02",
    brand_profile_id: "bp-acme-fintech-global-001",
    clause_identifier: "ACME-MSG-02",
    clause_text: "Market share claims exceeding 50% require verifiable citations from accredited third-party auditing firms (Gartner, IDC, or Big-4).",
    category: "MESSAGING",
    severity: "CRITICAL",
    created_at: "2026-01-10T12:00:00Z",
  },
  // Accessibility
  {
    id: "g-acc-01",
    brand_profile_id: "bp-acme-fintech-global-001",
    clause_identifier: "ACME-ACC-01",
    clause_text: "Content must maintain a Flesch-Kincaid Grade Level at or below 12.0 to ensure readability across global institutional stakeholders.",
    category: "ACCESSIBILITY",
    severity: "MEDIUM",
    created_at: "2026-01-10T12:00:00Z",
  },
  {
    id: "g-acc-02",
    brand_profile_id: "bp-acme-fintech-global-001",
    clause_identifier: "ACME-ACC-02",
    clause_text: "Avoid run-on sentences exceeding 40 words. Decompose complex multi-clause sentences for accessibility compliance.",
    category: "ACCESSIBILITY",
    severity: "LOW",
    created_at: "2026-01-10T12:00:00Z",
  },
];

export const DEFAULT_APPROVED_FACTS: ApprovedFact[] = [
  // Intentionally Expired Facts (Temporal Staleness & Blast Radius Showcase)
  {
    id: "fact-exp-01",
    workspace_id: "ws-acme-global-brand-001",
    brand_profile_id: "bp-acme-fintech-global-001",
    fact_statement: "Acme FinTech maintains $50M in assets under custody as of our 2023 annual filing.",
    original_source_url: "https://acmefintech.com/investors/2023-annual-filing.pdf",
    evidence_excerpt: "Assets under custody (AUC) stood at $50,210,000 as of December 31, 2023.",
    verification_date: "2024-01-15T00:00:00Z",
    expiry_date: "2024-12-31T23:59:59Z", // Expired
    responsible_owner_id: "Marcus Vance (Legal Reviewer)",
    is_active: true,
    created_at: "2024-01-15T10:00:00Z",
  },
  {
    id: "fact-exp-02",
    workspace_id: "ws-acme-global-brand-001",
    brand_profile_id: "bp-acme-fintech-global-001",
    fact_statement: "Acme FinTech processes 10,000 transactions per second with 99.9% uptime according to our Q1 2023 audit.",
    original_source_url: "https://acmefintech.com/audits/2023-q1-sla.pdf",
    evidence_excerpt: "Audited throughput verified at 10,000 TPS with 99.9% SLA.",
    verification_date: "2023-04-01T00:00:00Z",
    expiry_date: "2023-12-31T23:59:59Z", // Expired
    responsible_owner_id: "Marcus Vance (Legal Reviewer)",
    is_active: true,
    created_at: "2023-04-01T10:00:00Z",
  },
  // Active Valid Facts
  {
    id: "fact-act-01",
    workspace_id: "ws-acme-global-brand-001",
    brand_profile_id: "bp-acme-fintech-global-001",
    fact_statement: "Acme FinTech infrastructure is certified compliant with SOC 2 Type II and ISO 27001 standards.",
    original_source_url: "https://trust.acmefintech.com/soc2-type2-certificate.pdf",
    evidence_excerpt: "Independent auditor report confirms SOC 2 Type II security and ISO 27001 operational compliance.",
    verification_date: "2026-01-10T00:00:00Z",
    expiry_date: "2027-01-10T23:59:59Z", // Active Valid
    responsible_owner_id: "Elena Rostova (Compliance Lead)",
    is_active: true,
    created_at: "2026-01-10T08:00:00Z",
  },
  {
    id: "fact-act-02",
    workspace_id: "ws-acme-global-brand-001",
    brand_profile_id: "bp-acme-fintech-global-001",
    fact_statement: "Acme FinTech API responses maintain a 99th percentile processing time under 50 milliseconds for cached endpoints.",
    original_source_url: "https://acmefintech.com/telemetry/p99-latency-report.pdf",
    evidence_excerpt: "Production gateway latency benchmark confirmed P99 < 50ms across all regional clusters.",
    verification_date: "2026-02-01T00:00:00Z",
    expiry_date: "2026-12-31T23:59:59Z", // Active Valid
    responsible_owner_id: "Alex Chen (Product Marketer)",
    is_active: true,
    created_at: "2026-02-01T09:00:00Z",
  },
  {
    id: "fact-act-03",
    workspace_id: "ws-acme-global-brand-001",
    brand_profile_id: "bp-acme-fintech-global-001",
    fact_statement: "All client data at rest is encrypted using AES-256 and audit trails are recorded in a SHA-256 tamper-evident ledger.",
    original_source_url: "https://trust.acmefintech.com/crypto-architecture.pdf",
    evidence_excerpt: "Data-at-rest encryption verified with AES-256-GCM hardware keys and hash-chained audit trails.",
    verification_date: "2026-01-01T00:00:00Z",
    expiry_date: "2027-06-30T23:59:59Z", // Active Valid
    responsible_owner_id: "Elena Rostova (Compliance Lead)",
    is_active: true,
    created_at: "2026-01-01T12:00:00Z",
  },
  {
    id: "fact-act-04",
    workspace_id: "ws-acme-global-brand-001",
    brand_profile_id: "bp-acme-fintech-global-001",
    fact_statement: "Acme FinTech™ supports multi-currency settlement in USD, EUR, and GBP for verified enterprise accounts.",
    original_source_url: "https://acmefintech.com/settlement-currencies-spec.pdf",
    evidence_excerpt: "Supported fiat settlement corridors include USD, EUR, and GBP with real-time gross settlement.",
    verification_date: "2026-01-15T00:00:00Z",
    expiry_date: "2027-01-15T23:59:59Z", // Active Valid
    responsible_owner_id: "Marcus Vance (Legal Reviewer)",
    is_active: true,
    created_at: "2026-01-15T14:00:00Z",
  },
];

export interface DemoDocInfo {
  id: string;
  name: string;
  filename: string;
  fileType: "pdf" | "docx";
  magicBytes: string;
  magicByteName: string;
  description: string;
  badge: string;
  badgeClass: string;
  content: string;
  expectedFindings: {
    critical: number;
    high: number;
    medium: number;
    low: number;
    staleFacts: number;
    unsubstantiated: number;
  };
}

export const DEMO_DOCUMENTS: DemoDocInfo[] = [
  {
    id: "acme-q3-press-release",
    name: "Acme Q3 Press Release",
    filename: "acme_q3_press_release.pdf",
    fileType: "pdf",
    magicBytes: "%PDF-1.7 (25 50 44 46 2d)",
    magicByteName: "%PDF- Verified",
    badge: "Multi-Issue Stress Test",
    badgeClass: "badge-rose",
    description: "Contains banned superlatives ('100% risk-free', 'guaranteed monopoly'), expired 2023 fact ($50M AUC), ungrounded 84.7% market share claim, aggressive tone, and run-on sentences.",
    content: `ACME FINTECH GLOBAL - FOR IMMEDIATE RELEASE

Acme FinTech Unveils Q3 Global Liquidity Infrastructure

NEW YORK, NY -- Acme FinTech is thrilled to announce our next-generation enterprise clearing architecture. The platform delivers a 100% risk-free settlement environment establishing a guaranteed monopoly across modern interbank financial infrastructure. Our innovative algorithmic pipelines eliminate operational volatility entirely.

Demonstrating consistent corporate traction, Acme FinTech maintains $50M in assets under custody as of our 2023 annual filing. Our global transaction pipeline continues to process institutional order volume with high velocity and deterministic ledger tracking across primary market counterparties.

According to recent independent market research, Acme FinTech has captured 84.7% of the global institutional digital asset clearing market. This unprecedented adoption confirms our uncontested dominance across multi-asset collateral reconciliation networks worldwide.

Competitors are getting crushed and left in the dust by our crazy fast transaction engine. While conventional legacy infrastructure providers stumble through catastrophic outages and antiquated batch-processing workflows, our revolutionary autonomous routing matrix instantaneously and seamlessly orchestrates distributed multi-currency settlements without ever requiring manual intervention or intermediate reconciliation, delivering unmatched operational superiority that leaves every other legacy market participant completely hopeless.`,
    expectedFindings: {
      critical: 2, // 100% risk-free, guaranteed monopoly
      high: 2,     // missing trademark, ungrounded 84.7% market share
      medium: 1,   // crazy fast tone
      low: 1,      // 55-word run-on sentence
      staleFacts: 1, // $50M 2023 filing
      unsubstantiated: 1, // 84.7% market share
    },
  },
  {
    id: "acme-partner-pitch",
    name: "Strategic Partner Briefing",
    filename: "acme_partner_pitch.docx",
    fileType: "docx",
    magicBytes: "PK\\x03\\x04 (50 4b 03 04)",
    magicByteName: "PK\\x03\\x04 Verified",
    badge: "Factual Contradiction",
    badgeClass: "badge-amber",
    description: "Contains factual contradiction against Active Fact: claims P99 latency is 350ms (active verified fact is < 50ms), missing trademark symbol, and missing regulatory disclaimers.",
    content: `Strategic Partner Briefing: Acme FinTech Enterprise Platform
Confidential Institutional Partnership Proposal - Fiscal 2026

1. Executive Architecture Overview
Acme FinTech provides mission-critical liquidity infrastructure engineered for Tier-1 investment banks and liquidity providers. The platform enforces strict zero-trust role-based access control with Argon2id password hashing and cryptographic audit ledger verification.

2. Production Telemetry & SLA Benchmarks
Our telemetry logging infrastructure captures end-to-end distributed execution metrics across all active gateways. Acme FinTech API responses maintain a 99th percentile processing time of 350 milliseconds for cached endpoints.

3. Performance Matrix Summary
API P99 Latency (Cached): 350 milliseconds (Audit Reference: Internal Telemetry)
Encryption Standard: AES-256 GCM (SOC 2 Type II Annex C)
Multi-Currency Clearing: USD, EUR, GBP (Product Settlement Spec)

Capital at risk. Past performance is not indicative of future results.`,
    expectedFindings: {
      critical: 0,
      high: 2, // missing trademark, factual contradiction on P99 SLA
      medium: 0,
      low: 0,
      staleFacts: 0,
      unsubstantiated: 1, // 350ms contradicted metric
    },
  },
  {
    id: "acme-compliant-memo",
    name: "Executive Compliance Memo",
    filename: "acme_compliant_memo.pdf",
    fileType: "pdf",
    magicBytes: "%PDF-1.7 (25 50 44 46 2d)",
    magicByteName: "%PDF- Verified",
    badge: "100% Clean Benchmark",
    badgeClass: "badge-emerald",
    description: "Gold standard compliance benchmark. Incorporates Acme FinTech™ trademark, cites verified SOC 2 and AES-256 facts, professional tone, and required SEC regulatory disclaimers. 0% false positives.",
    content: `ACME FINTECH GLOBAL - COMPLIANCE EXECUTIVE MEMORANDUM
Enterprise Security & Infrastructure Status Report

This memorandum provides an executive overview of our production security and regulatory posture. Acme FinTech™ infrastructure is certified compliant with SOC 2 Type II and ISO 27001 standards. Our engineering teams maintain continuous control monitoring to protect institutional client assets.

All client data at rest is encrypted using AES-256 and audit trails are recorded in a SHA-256 tamper-evident ledger. The platform enforces strict zero-trust role-based access control with Argon2id password hashing to safeguard institutional account credentials against credential stuffing attacks.

Acme FinTech™ supports multi-currency settlement in USD, EUR, and GBP for verified enterprise accounts. Acme FinTech operates secondary redundant data centers across two distinct geographical regions to maintain uninterrupted settlement services during scheduled maintenance windows.

Capital at risk. Past performance is not indicative of future results. Investments are subject to market risk.`,
    expectedFindings: {
      critical: 0,
      high: 0,
      medium: 0,
      low: 0,
      staleFacts: 0,
      unsubstantiated: 0,
    },
  },
];
