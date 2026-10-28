// Synchronised with OpenAPI 0.1.0
/**
 * BrandShield AI - Zero-Dependency Enterprise TypeScript SDK
 * Engineered for React 18+, Next.js 14+, Vite, and vanilla TypeScript frontends.
 * Features strict types matching Pydantic v2 backend schemas, typed fetch wrappers,
 * built-in 1-click role switcher, Server-Sent Events (SSE) streaming,
 * and zero-transformation Recharts-ready analytics datasets.
 */

export type UserRole = "CREATOR" | "REVIEWER" | "ADMINISTRATOR";

export type WorkflowState =
  | "SUBMITTED"
  | "ANALYZING"
  | "TRIAGED"
  | "IN_CREATOR_REVISION"
  | "IN_HUMAN_REVIEW"
  | "CHANGES_REQUESTED"
  | "APPROVED";

export type FindingCategory =
  | "TONE"
  | "TERMINOLOGY"
  | "MESSAGING"
  | "ACCESSIBILITY"
  | "UNSUBSTANTIATED_CLAIM"
  | "STALE_FACT"
  | "REGULATORY_VIOLATION";

export type SeverityLevel = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";

export type TriageStatus =
  | "FLAGGED_HIGH_CONFIDENCE"
  | "ROUTED_TO_HUMAN_LOW_CONFIDENCE"
  | "STALE_FACT_REVERIFY"
  | "NEEDS_VERIFICATION_MISSING_EVIDENCE"
  | "CLEARED_COMPLIANT";

export type ReviewSignOff = "APPROVED" | "CHANGES_REQUESTED";

// =============================================================================
// Domain Contracts & Schemas
// =============================================================================

export interface TokenResponse {
  access_token: string;
  refresh_token?: string;
  token_type: string;
  expires_in?: number;
  user: User;
}

export interface DemoRoleAuthBundle {
  access_token: string;
  token_type: string;
  expires_in: number;
  role: UserRole;
  user: User;
}

export interface DemoTokensResponse {
  creator: DemoRoleAuthBundle;
  reviewer: DemoRoleAuthBundle;
  administrator: DemoRoleAuthBundle;
  CREATOR?: DemoRoleAuthBundle;
  REVIEWER?: DemoRoleAuthBundle;
  ADMINISTRATOR?: DemoRoleAuthBundle;
  [key: string]: any;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  workspace_id: string;
  is_active: boolean;
  created_at?: string;
}

export interface BrandProfile {
  id: string;
  workspace_id: string;
  name: string;
  description: string;
  tone_parameters: {
    target_formality?: number;
    max_grade_level?: number;
    max_passive_voice_ratio?: number;
    forbidden_sentiments?: string[];
  };
  banned_terminology_map: Record<
    string,
    { reason: string; severity: SeverityLevel; suggested_replacements?: string[] }
  >;
  preferred_terminology_map: Record<
    string,
    { approved_term: string; reason: string; severity: SeverityLevel }
  >;
  messaging_rules: {
    required_disclaimers?: string[];
    regulatory_framework?: string;
  };
  privacy_gate_config: {
    allow_external_llm: boolean;
    contract_verified_at?: string;
    approved_providers?: string[];
    retention_days?: number;
  };
  is_active: boolean;
  created_at: string;
}

export interface BrandGuideline {
  id: string;
  brand_profile_id: string;
  clause_identifier: string;
  clause_text: string;
  category: FindingCategory;
  severity: SeverityLevel;
  embedding?: number[];
  created_at?: string;
}

export interface ApprovedFact {
  id: string;
  workspace_id: string;
  brand_profile_id: string;
  fact_statement: string;
  original_source_url: string;
  evidence_excerpt?: string;
  verification_date: string;
  expiry_date: string;
  responsible_owner_id: string;
  is_active: boolean;
  created_at?: string;
}

export interface CreateApprovedFactRequest {
  brand_profile_id: string;
  fact_statement: string;
  original_source_url: string;
  evidence_excerpt?: string;
  verification_date: string;
  expiry_date: string;
  responsible_owner_id?: string;
  workspace_id?: string;
}

export interface ASTSpanNode {
  id: string;
  node_type: string;
  text: string;
  start_char: number;
  end_char: number;
  page_number?: number;
  bbox?: [number, number, number, number];
}

export interface DocumentRevision {
  id: string;
  submission_id: string;
  revision_number: number;
  parent_revision_id: string | null;
  content_text: string;
  ast_span_map: ASTSpanNode[];
  created_by_id: string;
  sha256_content_hash: string;
  diff_summary?: Record<string, unknown> | null;
  created_at: string;
}

export interface Finding {
  id: string;
  revision_id: string;
  issue_category: FindingCategory;
  severity: SeverityLevel;
  confidence_score: number;
  triage_status: TriageStatus;
  start_offset: number;
  end_offset: number;
  highlighted_text?: string;
  explanation_reason: string;
  suggested_correction?: string | null;
  detector_source: string;
  linked_guideline_id?: string | null;
  linked_fact_id?: string | null;
  is_automation_bias_audit: boolean;
  creator_action?: string | null;
  epistemic_uncertainty_score?: number | null;
  counterfactual_risk_summary?: string | null;
  created_at: string;
}

export interface Submission {
  id: string;
  workspace_id: string;
  creator_id: string;
  assigned_reviewer_id?: string | null;
  brand_profile_id: string;
  title: string;
  document_type: string;
  workflow_state: WorkflowState;
  current_revision_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ReviewDecision {
  id: string;
  submission_id: string;
  revision_id: string;
  reviewer_id: string;
  decision: ReviewSignOff;
  comments: string;
  stipulations?: Record<string, unknown> | null;
  created_at: string;
}

export interface InstantAnalysisResponse {
  submission: Submission;
  findings: Finding[];
  triage_summary: {
    total_findings: number;
    flagged_high_confidence: number;
    routed_to_human_low_confidence: number;
    stale_facts_to_reverify: number;
    needs_verification_missing_evidence: number;
    automation_bias_audits_injected: number;
    suppressed_false_positives_count: number;
    processing_duration_ms: number;
  };
}

export interface RevisionDiffResponse {
  submission_id: string;
  from_revision_number: number;
  to_revision_number: number;
  from_revision_id: string;
  to_revision_id: string;
  total_additions: number;
  total_deletions: number;
  unified_diff: string;
  token_diffs: Array<{
    operation: "EQUAL" | "INSERT" | "DELETE";
    text: string;
    start_char?: number;
    end_char?: number;
  }>;
}

// =============================================================================
// Recharts-Ready Pre-Formatted Datasets
// =============================================================================

export interface RechartsCategoryBar {
  category: string;
  name: string;
  count: number;
  value: number;
  fill: string;
  CRITICAL: number;
  HIGH: number;
  MEDIUM: number;
  LOW: number;
}

export interface RechartsReviewTrendLine {
  date: string;
  name?: string;
  value?: number;
  count?: number;
  approved: number;
  changes_requested: number;
  total_reviews: number;
  fill?: string;
}

export interface RechartsTriagePie {
  name: string;
  value: number;
  count?: number;
  fill: string;
  key?: string;
  percentage: number;
}

export interface RechartsSeverityBar {
  name: string;
  value: number;
  count: number;
  fill: string;
  severity: string;
}

export interface RechartsSummaryKPI {
  name: string;
  value: string | number;
  count: number;
  fill: string;
  description?: string;
}

export interface GovernanceReportResponse {
  workspace_id: string;
  brand_profile_id?: string | null;
  total_findings: number;
  category_counts: Record<string, number>;
  severity_counts: Record<string, number>;
  triage_status_counts: Record<string, number>;
  detector_source_counts: Record<string, number>;
  creator_action_counts?: Record<string, number>;
  category_severity_cube?: any[];
  // Zero-transformation Recharts arrays for direct binding
  category_chart_data: RechartsCategoryBar[];
  triage_pie_data: RechartsTriagePie[];
  severity_breakdown: RechartsSeverityBar[];
  review_trend_series: RechartsReviewTrendLine[];
  summary_kpis: RechartsSummaryKPI[];
  // Backward compatibility
  recharts_category_bar: RechartsCategoryBar[];
  recharts_review_trends_line: RechartsReviewTrendLine[];
  recharts_triage_pie: RechartsTriagePie[];
  generated_at: string;
}

export interface TraceabilityMetricsResponse {
  workspace_id: string;
  brand_profile_id?: string | null;
  total_findings: number;
  grounded_findings_count: number;
  ungrounded_findings_count: number;
  traceability_percentage: number;
  guideline_linked_count: number;
  fact_linked_count: number;
  is_zero_ungrounded_verified: boolean;
  audit_timestamp: string;
}

export interface AuditChainVerificationResult {
  is_valid: boolean;
  total_records: number;
  tampered_sequence_id?: number | null;
  verification_message: string;
  chain_valid?: boolean;
}

export interface EvaluationBenchmarkResponse {
  total_samples: number;
  true_positives: number;
  false_positives: number;
  false_negatives: number;
  precision: number;
  recall: number;
  f1_score: number;
  p95_latency_ms: number;
  avg_latency_ms: number;
  min_latency_ms: number;
  max_latency_ms: number;
  evaluated_at: string;
}

// Cryptographic Publication Attestation & Preflight Schemas
export interface PublicationAttestationCertificateRead {
  id: string;
  certificate_id: string;
  submission_id: string;
  approved_revision_id: string;
  document_sha256_hash: string;
  reviewer_id: string;
  brand_profile_id: string;
  merkle_root_of_cited_facts_and_guidelines: string;
  active_cited_fact_ids: string[];
  earliest_fact_expiry: string | null;
  issued_at: string;
  valid_until: string;
  cryptographic_signature: string;
  revocation_reason: string | null;
  revoked_at: string | null;
}

export interface AttestationVerifyRequest {
  certificate_id: string;
  document_content?: string | null;
  document_sha256_hash?: string | null;
}

export interface AttestationVerifyResponse {
  is_valid: boolean;
  verification_code: string;
  certificate_id: string;
  submission_id: string | null;
  verified_at: string;
  details: Record<string, unknown>;
}

export interface InlineSpanHighlight {
  start_char: number;
  end_char: number;
  flagged_text: string;
  issue_category: FindingCategory;
  severity: SeverityLevel;
  explanation_reason: string;
  suggested_correction: string | null;
  epistemic_uncertainty_score: number;
  counterfactual_risk_summary: string;
}

export interface InlinePreflightRequest {
  brand_profile_id: string;
  text_snippet: string;
}

export interface InlinePreflightResponse {
  brand_profile_id: string;
  is_compliant: boolean;
  total_spans_detected: number;
  spans: InlineSpanHighlight[];
  processing_duration_ms: number;
}

export interface CharacterSpanCitation {
  submission_id: string;
  submission_title: string;
  revision_id: string;
  revision_number: number;
  finding_id: string;
  start_offset: number;
  end_offset: number;
  citation_hash: string;
}

export interface BlastRadiusTriggerResponse {
  fact_id: string;
  fact_statement: string;
  expiry_date?: string | null;
  trigger_reason: string;
  brand_profile_id?: string | null;
  affected_submissions_count: number;
  affected_pages: number;
  affected_citations_count: number;
  exact_character_spans: CharacterSpanCitation[];
  outbox_event_id?: string | null;
  outbox_delivery_status: string;
  timestamp: string;
}

export interface EnterpriseBlastRadiusOverview {
  workspace_id: string;
  brand_profile_id?: string | null;
  total_citation_edges: number;
  total_stale_facts: number;
  total_affected_approved_submissions: number;
  total_outbox_events_pending: number;
  total_outbox_events_delivered: number;
  total_outbox_events_dlq: number;
  recent_events: Record<string, unknown>[];
}

export interface OutboxFlushResponse {
  processed_count: number;
  delivered_count: number;
  failed_retrying_count: number;
  dlq_count: number;
  duration_ms: number;
}

// =============================================================================
// Default Environment Base URL
// =============================================================================

const DEFAULT_API_BASE_URL: string =
  (typeof import.meta !== "undefined" &&
    (import.meta as any).env &&
    (import.meta as any).env.VITE_API_BASE_URL) ||
  (typeof process !== "undefined" &&
    process.env &&
    (process.env.VITE_API_BASE_URL || process.env.REACT_APP_API_BASE_URL)) ||
  "http://localhost:8000/api/v1";

// =============================================================================
// Typed BrandShield AI Client
// =============================================================================

export class BrandShieldClient {
  private baseUrl: string;
  private token: string | null = null;
  private activeDemoRole: UserRole | null = null;
  private cachedDemoTokens: DemoTokensResponse | null = null;

  constructor(baseUrl?: string, token?: string) {
    const raw = baseUrl || DEFAULT_API_BASE_URL;
    // Strip trailing slash and normalize /api/v1
    this.baseUrl = raw.replace(/\/+$/, "").replace(/\/api\/v1$/, "");
    this.token = token || null;
  }

  // ---------------------------------------------------------------------------
  // Authentication & 1-Click Role Switcher
  // ---------------------------------------------------------------------------

  public setToken(token: string | null): void {
    this.token = token;
  }

  public getToken(): string | null {
    return this.token;
  }

  public setActiveDemoRole(role: UserRole | null): void {
    this.activeDemoRole = role;
  }

  public getActiveDemoRole(): UserRole | null {
    return this.activeDemoRole;
  }

  /**
   * Fetches pre-signed demo tokens and profiles for CREATOR, REVIEWER, and ADMINISTRATOR.
   */
  public async fetchDemoTokens(): Promise<DemoTokensResponse> {
    const tokens = await this.request<DemoTokensResponse>("/api/v1/auth/demo-tokens");
    this.cachedDemoTokens = tokens;
    return tokens;
  }

  /**
   * 1-Click Role Switcher: switches active demo role, updates JWT bearer token, and returns user profile.
   */
  public async switchRole(role: UserRole): Promise<User> {
    this.setActiveDemoRole(role);
    if (!this.cachedDemoTokens) {
      await this.fetchDemoTokens();
    }
    const roleKey = role.toLowerCase() as "creator" | "reviewer" | "administrator";
    const bundle = this.cachedDemoTokens?.[roleKey] || (this.cachedDemoTokens as any)?.[role];
    if (bundle && bundle.access_token) {
      this.setToken(bundle.access_token);
      return bundle.user;
    }
    return this.getCurrentUser();
  }

  public async login(email: string, password: string): Promise<TokenResponse> {
    const res = await this.request<TokenResponse>("/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    this.setToken(res.access_token);
    return res;
  }

  public async getCurrentUser(): Promise<User> {
    return this.request<User>("/api/v1/auth/me");
  }

  // ---------------------------------------------------------------------------
  // Core HTTP Request Wrapper
  // ---------------------------------------------------------------------------

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const cleanPath = endpoint.startsWith("/api/v1")
      ? endpoint
      : `/api/v1${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;
    const url = `${this.baseUrl}${cleanPath}`;

    const headers: Record<string, string> = {
      Accept: "application/json",
      ...(options.headers as Record<string, string>),
    };

    if (this.token && !headers["Authorization"]) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }

    if (this.activeDemoRole && !headers["X-Demo-Role"]) {
      headers["X-Demo-Role"] = this.activeDemoRole;
    }

    const response = await fetch(url, { ...options, headers });
    if (!response.ok) {
      let problemDetail: any = null;
      try {
        problemDetail = await response.json();
      } catch {
        // non-json response
      }
      throw new Error(
        problemDetail?.detail ||
          problemDetail?.title ||
          problemDetail?.message ||
          `API Request failed with status ${response.status}: ${response.statusText}`
      );
    }

    return response.json() as Promise<T>;
  }

  // ---------------------------------------------------------------------------
  // Screen 1: Brand Setup & Knowledge Grounding
  // ---------------------------------------------------------------------------

  /**
   * Resolves the primary active brand profile in the workspace.
   */
  public async getPrimaryBrandProfile(): Promise<BrandProfile> {
    const profiles = await this.request<BrandProfile[]>("/api/v1/brands/");
    if (!profiles || profiles.length === 0) {
      throw new Error("No active Brand Profile configured in workspace.");
    }
    return profiles[0];
  }

  public async getBrandProfile(profileId: string): Promise<BrandProfile> {
    return this.request<BrandProfile>(`/api/v1/brands/${profileId}`);
  }

  public async listBrandProfiles(): Promise<BrandProfile[]> {
    return this.request<BrandProfile[]>("/api/v1/brands/");
  }

  public async getGuidelines(brandProfileId?: string): Promise<BrandGuideline[]> {
    if (brandProfileId) {
      return this.request<BrandGuideline[]>(`/api/v1/brands/${brandProfileId}/guidelines`);
    }
    const profile = await this.getPrimaryBrandProfile();
    return this.request<BrandGuideline[]>(`/api/v1/brands/${profile.id}/guidelines`);
  }

  public async getApprovedFacts(brandProfileId?: string): Promise<ApprovedFact[]> {
    const q = brandProfileId ? `?brand_profile_id=${brandProfileId}` : "";
    return this.request<ApprovedFact[]>(`/api/v1/facts/${q}`);
  }

  public async createApprovedFact(fact: CreateApprovedFactRequest): Promise<ApprovedFact> {
    return this.request<ApprovedFact>("/api/v1/facts/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(fact),
    });
  }

  // ---------------------------------------------------------------------------
  // Screen 2: Multi-Modal Ingestion
  // ---------------------------------------------------------------------------

  /**
   * Ingests raw text or Markdown into the Git-like revision DAG.
   */
  public async submitText(
    title: string,
    content: string,
    brandProfileId?: string
  ): Promise<Submission> {
    return this.request<Submission>("/api/v1/submissions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title,
        content_text: content,
        brand_profile_id: brandProfileId,
        document_type: "TEXT",
      }),
    });
  }

  /**
   * Uploads and verifies document binary assets (PDF, DOCX, TXT, MD).
   */
  public async submitDocumentFile(
    file: Blob | File,
    title?: string,
    brandProfileId?: string,
    filename?: string
  ): Promise<Submission> {
    const formData = new FormData();
    const resolvedName =
      filename || (file instanceof File ? file.name : "uploaded_document.pdf");
    formData.append("file", file, resolvedName);
    if (title) formData.append("title", title);
    if (brandProfileId) formData.append("brand_profile_id", brandProfileId);

    return this.request<Submission>("/api/v1/submissions", {
      method: "POST",
      body: formData,
    });
  }

  /**
   * 1-Step Convenience Endpoint: Ingests text or file, runs 4-stage pipeline,
   * and returns submission + findings + triage summary in a single HTTP round-trip!
   */
  public async submitAndAnalyzeInstant(options: {
    text?: string;
    file?: Blob | File;
    filename?: string;
    title?: string;
    brandProfileId?: string;
  }): Promise<InstantAnalysisResponse> {
    if (options.file) {
      const formData = new FormData();
      const resolvedName =
        options.filename ||
        (options.file instanceof File ? options.file.name : "upload.pdf");
      formData.append("file", options.file, resolvedName);
      if (options.title) formData.append("title", options.title);
      if (options.brandProfileId) formData.append("brand_profile_id", options.brandProfileId);

      return this.request<InstantAnalysisResponse>("/api/v1/submissions/analyze-instant", {
        method: "POST",
        body: formData,
      });
    }

    return this.request<InstantAnalysisResponse>("/api/v1/submissions/analyze-instant", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: options.title,
        content_text: options.text || "",
        brand_profile_id: options.brandProfileId,
      }),
    });
  }

  public async getSubmission(submissionId: string): Promise<Submission> {
    return this.request<Submission>(`/api/v1/submissions/${submissionId}`);
  }

  public async listSubmissions(): Promise<Submission[]> {
    return this.request<Submission[]>("/api/v1/submissions/");
  }

  public async listRevisions(submissionId: string): Promise<DocumentRevision[]> {
    return this.request<DocumentRevision[]>(`/api/v1/submissions/${submissionId}/revisions`);
  }

  // ---------------------------------------------------------------------------
  // Screen 3: 4-Stage Intelligence Pipeline & Live Stream
  // ---------------------------------------------------------------------------

  public async analyzeSubmission(
    submissionId: string,
    requestedProvider: string = "Azure OpenAI"
  ): Promise<any> {
    const q = new URLSearchParams({ requested_provider: requestedProvider });
    return this.request(`/api/v1/analysis/submissions/${submissionId}/run?${q.toString()}`, {
      method: "POST",
    });
  }

  /**
   * Real-time Server-Sent Events (SSE) stream for interactive stage latencies and live findings.
   */
  public streamAnalysisSSE(
    submissionId: string,
    callbacks: {
      onStage?: (stage: string, latencyMs: number) => void;
      onFinding?: (finding: Finding) => void;
      onComplete?: (totalFindings: number, durationMs: number) => void;
      onError?: (error: Error) => void;
    }
  ): () => void {
    const tokenParam = this.token ? `?token=${encodeURIComponent(this.token)}` : "";
    const url = `${this.baseUrl}/api/v1/submissions/${submissionId}/analyze/stream${tokenParam}`;

    const eventSource = new EventSource(url);

    eventSource.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.stage && callbacks.onStage) {
          callbacks.onStage(payload.stage, payload.latency_ms || 0);
        }
        if (payload.findings && Array.isArray(payload.findings) && callbacks.onFinding) {
          payload.findings.forEach((f: Finding) => callbacks.onFinding?.(f));
        }
        if (payload.stage === "PIPELINE_COMPLETE") {
          callbacks.onComplete?.(payload.total_findings || 0, payload.duration_ms || 0);
          eventSource.close();
        }
      } catch (err: any) {
        callbacks.onError?.(err);
      }
    };

    eventSource.onerror = (err) => {
      callbacks.onError?.(new Error("SSE Stream connection error"));
      eventSource.close();
    };

    return () => eventSource.close();
  }

  public streamAnalysis(
    submissionId: string,
    callbacks: {
      onStage?: (stage: string, latencyMs: number) => void;
      onFinding?: (finding: Finding) => void;
      onComplete?: (totalFindings: number, durationMs: number) => void;
      onError?: (error: Error) => void;
    }
  ): () => void {
    return this.streamAnalysisSSE(submissionId, callbacks);
  }

  /**
   * Sub-10ms inline co-pilot preflight evaluation for active text highlights.
   */
  public async preflightInline(
    brandProfileId: string,
    textSnippet: string
  ): Promise<InlinePreflightResponse> {
    return this.request<InlinePreflightResponse>("/api/v1/analysis/preflight-inline", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        brand_profile_id: brandProfileId,
        text_snippet: textSnippet,
      }),
    });
  }

  // ---------------------------------------------------------------------------
  // Screen 4: Triage & Creator Workspace
  // ---------------------------------------------------------------------------

  public async getFindings(revisionId: string): Promise<Finding[]> {
    return this.request<Finding[]>(`/api/v1/analysis/revisions/${revisionId}/findings`);
  }

  /**
   * Resolves a finding suggestion (ACCEPT, REJECT, or EDIT) and produces an immutable vN+1 revision.
   */
  public async resolveFindingSuggestion(
    findingId: string,
    action: "ACCEPT" | "REJECT" | "EDIT" | "ACCEPT_SUGGESTION" | "CUSTOM_EDIT" | "REJECT_WITH_RATIONALE",
    customReplacement?: string,
    rationale?: string,
    submissionId?: string
  ): Promise<any> {
    let normalizedAction = action;
    if (action === "ACCEPT") normalizedAction = "ACCEPT_SUGGESTION";
    if (action === "REJECT") normalizedAction = "REJECT_WITH_RATIONALE";
    if (action === "EDIT") normalizedAction = "CUSTOM_EDIT";

    const path = submissionId
      ? `/api/v1/workflow/${submissionId}/findings/${findingId}/resolve`
      : `/api/v1/workflow/findings/${findingId}/resolve`;

    return this.request(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action: normalizedAction,
        custom_replacement: customReplacement,
        rationale: rationale,
      }),
    });
  }

  public async resolveFinding(
    findingId: string,
    action: "ACCEPT_SUGGESTION" | "CUSTOM_EDIT" | "REJECT_WITH_RATIONALE",
    customReplacement?: string,
    rationale?: string
  ): Promise<any> {
    return this.resolveFindingSuggestion(findingId, action, customReplacement, rationale);
  }

  // ---------------------------------------------------------------------------
  // Screen 5: Governance Review & State Machine
  // ---------------------------------------------------------------------------

  public async submitForReview(submissionId: string): Promise<Submission> {
    return this.request<Submission>(`/api/v1/workflow/${submissionId}/submit-for-review`, {
      method: "POST",
    });
  }

  public async submitHumanReviewDecision(
    submissionId: string,
    decision: ReviewSignOff,
    comments: string,
    stipulations?: Record<string, unknown>
  ): Promise<ReviewDecision> {
    return this.request<ReviewDecision>(`/api/v1/workflow/${submissionId}/review`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        decision,
        comments,
        stipulations,
      }),
    });
  }

  public async executeReviewDecision(
    submissionId: string,
    decision: ReviewSignOff,
    comments: string,
    stipulations?: Record<string, unknown>
  ): Promise<ReviewDecision> {
    return this.submitHumanReviewDecision(submissionId, decision, comments, stipulations);
  }

  public async getRevisionDiff(
    submissionId: string,
    fromRevision: number = 1,
    toRevision?: number
  ): Promise<RevisionDiffResponse> {
    const q = new URLSearchParams({ from_revision: fromRevision.toString() });
    if (toRevision) q.append("to_revision", toRevision.toString());
    return this.request<RevisionDiffResponse>(
      `/api/v1/workflow/${submissionId}/revisions/diff?${q.toString()}`
    );
  }

  // ---------------------------------------------------------------------------
  // Screen 6: Recharts Governance Dashboard
  // ---------------------------------------------------------------------------

  public async getGovernanceDashboardReport(
    brandProfileId?: string
  ): Promise<GovernanceReportResponse> {
    const q = brandProfileId ? `?brand_profile_id=${brandProfileId}` : "";
    return this.request<GovernanceReportResponse>(`/api/v1/governance/reports${q}`);
  }

  public async getGovernanceReports(
    brandProfileId?: string
  ): Promise<GovernanceReportResponse> {
    return this.getGovernanceDashboardReport(brandProfileId);
  }

  public async getTraceabilityMetrics(
    brandProfileId?: string
  ): Promise<TraceabilityMetricsResponse> {
    const q = brandProfileId ? `?brand_profile_id=${brandProfileId}` : "";
    return this.request<TraceabilityMetricsResponse>(
      `/api/v1/governance/traceability-metrics${q}`
    );
  }

  public async verifyAuditChain(): Promise<AuditChainVerificationResult> {
    return this.request<AuditChainVerificationResult>(
      "/api/v1/governance/audit-verify",
      { method: "POST" }
    );
  }

  public async runLabelledTestSetBenchmark(
    brandProfileId?: string
  ): Promise<EvaluationBenchmarkResponse> {
    const q = brandProfileId ? `?brand_profile_id=${brandProfileId}` : "";
    return this.request<EvaluationBenchmarkResponse>(
      `/api/v1/governance/evaluate-testset${q}`,
      { method: "POST" }
    );
  }

  // ---------------------------------------------------------------------------
  // Screen 7: Safeguards & Attestation Authority
  // ---------------------------------------------------------------------------

  public async getPublicationCertificate(
    submissionId: string
  ): Promise<PublicationAttestationCertificateRead> {
    return this.request<PublicationAttestationCertificateRead>(
      `/api/v1/submissions/${submissionId}/certificate`
    );
  }

  public async verifyPublicationCertificate(
    payload: AttestationVerifyRequest
  ): Promise<AttestationVerifyResponse> {
    return this.request<AttestationVerifyResponse>("/api/v1/attestation/verify", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  }

  public async verifyAttestationCertificate(
    payload: AttestationVerifyRequest
  ): Promise<AttestationVerifyResponse> {
    return this.verifyPublicationCertificate(payload);
  }

  public async verifyPublicationAttestation(
    payload: AttestationVerifyRequest
  ): Promise<AttestationVerifyResponse> {
    return this.verifyPublicationCertificate(payload);
  }

  // ---------------------------------------------------------------------------
  // Screen 8: Knowledge Graph & Webhooks
  // ---------------------------------------------------------------------------

  public async triggerFactBlastRadius(
    factId: string,
    reason: string = "MANUAL_REVERIFICATION"
  ): Promise<BlastRadiusTriggerResponse> {
    return this.request<BlastRadiusTriggerResponse>(
      `/api/v1/facts/${factId}/blast-radius?trigger_reason=${encodeURIComponent(reason)}`,
      { method: "POST" }
    );
  }

  public async getBlastRadius(
    brandProfileId?: string
  ): Promise<EnterpriseBlastRadiusOverview> {
    const q = brandProfileId ? `?brand_profile_id=${brandProfileId}` : "";
    return this.request<EnterpriseBlastRadiusOverview>(
      `/api/v1/governance/blast-radius${q}`
    );
  }

  public async flushWebhookOutbox(
    limit: number = 50
  ): Promise<OutboxFlushResponse> {
    return this.request<OutboxFlushResponse>(
      `/api/v1/webhooks/outbox/flush?limit=${limit}`,
      { method: "POST" }
    );
  }
}

// Export default singleton instance for fast import:
// import brandshield from "@/frontend_sdk/brandshieldClient";
export const brandshield = new BrandShieldClient();
export default brandshield;
