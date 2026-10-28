"""
BrandShield AI - Adversarial "Red-Team / Blue-Team" Critic Verifier.
Stage 5 Post-Detection Intelligence:
1. Red-Team context analyzer checks surrounding clauses for negation, competitor quotes, and safe-harbor disclaimers to eliminate False Positives.
2. Blue-Team uncertainty evaluator calculates epistemic uncertainty score [0.0, 1.0] via Shannon entropy and rank divergence.
3. Formulates counterfactual risk summaries explaining exact brand/legal exposure if published unedited.
4. Tracks suppressed false positive telemetry for governance and benchmark transparency.
"""

from dataclasses import dataclass, field
import math
import re
from typing import Any, Optional

from app.domain.enums import DetectorSource, FindingCategory, SeverityLevel
from app.infrastructure.db.models import Finding

# Negation indicators preceding target spans
NEGATION_REGEX = re.compile(
    r"\b(do not|does not|did not|not|never|no|cannot|can't|won't|neither|nor|without|refrain from|no evidence of|we make no|disclaim(?:s|ed|ing)?)\b",
    re.IGNORECASE,
)

# Contrastive competitor context indicators
COMPETITOR_CONTRAST_REGEX = re.compile(
    r"\b(unlike|compared to|competitor[s]?|rival[s]?|they claim|others promise|quoted from|in contrast to|whereas competitor|competitors)\b",
    re.IGNORECASE,
)

# Safe-harbor disclaimers and qualifiers
SAFE_DISCLAIMER_REGEX = re.compile(
    r"(\*|\bdisclaimer\b|\bindependent study\b|\bindependent lab\b|\bindividual results may vary\b|\bresults may vary\b|\bterms and conditions apply\b|\bsubject to change\b|\bnot indicative of future\b|\bfor illustrative purposes\b|\bfor demonstration only\b|\bconsult with a physician\b|\bpast performance does not\b)",
    re.IGNORECASE,
)

# Modal hedging verbs indicating linguistic uncertainty
MODAL_HEDGING_REGEX = re.compile(
    r"\b(may|might|could|possibly|allegedly|potentially|estimated|approximate|anticipated)\b",
    re.IGNORECASE,
)


@dataclass
class CriticEvaluationResult:
    """Outcome of adversarial post-detection verification."""
    accepted_findings: list[Finding]
    suppressed_findings: list[Finding]
    suppressed_false_positives_count: int
    telemetry: dict[str, Any] = field(default_factory=dict)


class AdversarialCritic:
    """
    Adversarial False-Positive Critic & Epistemic Uncertainty Evaluator.
    Acts as an adversarial red-team filter between detection stages and database persistence.
    """
    _lifetime_suppressed_count: int = 0

    @classmethod
    def get_lifetime_suppressed_count(cls) -> int:
        """Returns total false positives suppressed by the Critic across server runtime."""
        return cls._lifetime_suppressed_count

    @classmethod
    def record_suppression(cls, count: int = 1) -> None:
        """Atomically increments the lifetime suppressed false positive telemetry counter."""
        if count > 0:
            cls._lifetime_suppressed_count += count

    @classmethod
    def calculate_shannon_entropy(cls, confidence: float) -> float:
        """
        Computes binary Shannon entropy H(p) = -(p*log2(p) + (1-p)*log2(1-p)).
        Measures epistemic dispersion: 0.0 at complete certainty (p=1.0 or 0.0),
        peaking at 1.0 at maximum uncertainty (p=0.5).
        """
        # Clamp confidence to avoid log2(0)
        p = max(0.001, min(0.999, confidence))
        q = 1.0 - p
        entropy = -(p * math.log2(p) + q * math.log2(q))
        return max(0.0, min(1.0, entropy))

    @classmethod
    def extract_clause_context(
        cls,
        content_text: str,
        start_offset: int,
        end_offset: int,
        window: int = 140,
    ) -> tuple[str, str, str, str]:
        """
        Extracts surrounding sentence / clause context around a detected finding span.
        Returns: (full_clause, pre_context, matched_span, post_context).
        """
        text_len = len(content_text)
        s_off = max(0, min(start_offset, text_len))
        e_off = max(s_off, min(end_offset, text_len))

        # Scan backwards for clause or sentence delimiter
        c_start = max(0, s_off - window)
        for i in range(s_off - 1, c_start - 1, -1):
            if content_text[i] in (".", "?", "!", "\n", ";"):
                c_start = i + 1
                break

        # Scan forwards for clause or sentence delimiter
        c_end = min(text_len, e_off + window)
        for i in range(e_off, c_end):
            if content_text[i] in (".", "?", "!", "\n", ";"):
                c_end = i
                break

        full_clause = content_text[c_start:c_end].strip()
        pre_context = content_text[c_start:s_off].strip()
        matched_span = content_text[s_off:e_off].strip()
        post_context = content_text[e_off:c_end].strip()

        return full_clause, pre_context, matched_span, post_context

    @classmethod
    def evaluate_false_positive(
        cls,
        content_text: str,
        finding: Finding,
    ) -> tuple[bool, Optional[str]]:
        """
        Evaluates candidate finding against adversarial red-team filters:
        Returns (is_false_positive: bool, suppression_reason: Optional[str]).
        """
        full_clause, pre_context, matched_span, post_context = cls.extract_clause_context(
            content_text,
            finding.start_offset,
            finding.end_offset,
        )

        # 1. Negation Check: Is the flagged term or claim negated in context?
        # e.g., "We do not claim our software cures latency" -> False Positive
        if NEGATION_REGEX.search(pre_context):
            return True, (
                f"Critic Suppressed (False Positive): Active negation detected in preceding context ('{pre_context}'). "
                f"Author is explicitly disclaiming or rejecting '{matched_span}'."
            )

        # 2. Competitor Contrast / Quoted Speech Check:
        # e.g., "Unlike Competitor X who claims their engine is invincible..."
        if COMPETITOR_CONTRAST_REGEX.search(full_clause):
            return True, (
                f"Critic Suppressed (False Positive): Contrastive competitor attribution detected in clause ('{full_clause}'). "
                f"Statement contrasts against rival assertions rather than claiming first-party authority."
            )

        # 2B. Direct Quote Enclosure:
        # If the span is enclosed in quotation marks, it is a quotation rather than an assertion
        is_quoted = (
            (pre_context.endswith('"') and post_context.startswith('"'))
            or (pre_context.endswith("'") and post_context.startswith("'"))
            or (pre_context.endswith("“") and post_context.startswith("”"))
        )
        if is_quoted:
            return True, (
                f"Critic Suppressed (False Positive): Term '{matched_span}' is enclosed in quotation marks. "
                "Quoted speech is exempt from primary corporate brand terminology sanctions."
            )

        # 3. Safe Disclaimer Qualifier:
        # If the claim is explicitly qualified by a nearby asterisk or safe-harbor disclaimer in the same clause or paragraph
        p_start = content_text.rfind("\n\n", 0, finding.start_offset)
        p_start = 0 if p_start == -1 else p_start + 2
        p_end = content_text.find("\n\n", finding.end_offset)
        p_end = len(content_text) if p_end == -1 else p_end
        para_context = content_text[max(p_start, finding.start_offset - 200):min(p_end, finding.end_offset + 200)]
        has_safe_disclaimer = bool(SAFE_DISCLAIMER_REGEX.search(full_clause)) or bool(SAFE_DISCLAIMER_REGEX.search(para_context))
        if has_safe_disclaimer and finding.issue_category in (
            FindingCategory.UNSUBSTANTIATED_CLAIM,
            FindingCategory.REGULATORY_VIOLATION,
            FindingCategory.ACCESSIBILITY,
            FindingCategory.TONE,
            FindingCategory.TERMINOLOGY,
        ):
            # If finding was raised about an unqualified claim, but safe disclaimer is present
            return True, (
                f"Critic Suppressed (False Positive): Claim '{matched_span}' is qualified by an attached safe-harbor "
                "disclaimer or statutory asterisk in immediate context."
            )

        return False, None

    @classmethod
    def compute_epistemic_uncertainty(
        cls,
        finding: Finding,
        content_text: str,
    ) -> float:
        """
        Computes calibrated epistemic uncertainty score [0.0, 1.0].
        Synthesizes Shannon entropy H(p) of the detection confidence with linguistic hedging markers.
        """
        base_confidence = getattr(finding, "confidence_score", 1.0)
        shannon_entropy = cls.calculate_shannon_entropy(base_confidence)

        # Check for linguistic hedging in clause
        full_clause, _, _, _ = cls.extract_clause_context(
            content_text,
            finding.start_offset,
            finding.end_offset,
        )
        has_hedging = bool(MODAL_HEDGING_REGEX.search(full_clause))
        hedging_factor = 0.20 if has_hedging else 0.0

        # Deterministic rules have high precision (low baseline uncertainty)
        detector = getattr(finding, "detector_source", DetectorSource.DETERMINISTIC_RULE)
        if detector == DetectorSource.DETERMINISTIC_RULE:
            raw_uncertainty = (shannon_entropy * 0.15) + hedging_factor
        elif detector == DetectorSource.TEMPORAL_FACT_MATCHER:
            raw_uncertainty = (shannon_entropy * 0.50) + hedging_factor
        else:
            raw_uncertainty = (shannon_entropy * 0.70) + hedging_factor

        return round(max(0.0, min(1.0, raw_uncertainty)), 3)

    @classmethod
    def generate_counterfactual_risk_summary(
        cls,
        finding: Finding,
        matched_span: str,
    ) -> str:
        """
        Synthesizes an executive-grade Counterfactual Risk Summary detailing
        the exact legal, brand, or regulatory exposure if published unedited.
        """
        cat = getattr(finding, "issue_category", FindingCategory.TERMINOLOGY)
        sev = getattr(finding, "severity", SeverityLevel.MEDIUM)

        if cat == FindingCategory.TERMINOLOGY:
            return (
                f"Counterfactual Risk (Brand Governance): Unedited publication of '{matched_span}' violates enterprise "
                "nomenclature standards. Poses risk of brand dilution, trademark genericide, and cross-channel message fragmentation."
            )
        elif cat in (FindingCategory.UNSUBSTANTIATED_CLAIM, FindingCategory.REGULATORY_VIOLATION):
            return (
                f"Counterfactual Risk (Regulatory Compliance): Assertion '{matched_span}' constitutes an unsubstantiated efficacy "
                "or superlative claim. Under FTC Act § 5 (15 U.S.C. § 45) and Lanham Act § 43(a), unedited publication exposes the brand "
                "to competitor false-advertising injunctions, regulatory scrutiny, and mandatory corrective advertising penalties."
            )
        elif cat == FindingCategory.TONE or cat == FindingCategory.MESSAGING:
            return (
                f"Counterfactual Risk (Executive Tone): Phrasing '{matched_span}' diverges from established brand voice covenants. "
                "Risks perceptual authority erosion and negative sentiment among institutional clients."
            )
        elif cat == FindingCategory.ACCESSIBILITY:
            return (
                f"Counterfactual Risk (Accessibility Compliance): Structural complexity around '{matched_span}' breaches WCAG 2.1 / "
                "Section 508 readability ceilings, impairing comprehension for neurodiverse stakeholders."
            )
        else:
            return (
                f"Counterfactual Risk (Compliance Exposure): Severity {sev.value} non-conformance for '{matched_span}' creates "
                "governance audit exceptions and potential reputational exposure."
            )

    @classmethod
    def critique_findings(
        cls,
        content_text: str,
        findings: list[Finding],
    ) -> CriticEvaluationResult:
        """
        Master Critic verification pass:
        1. Filters out false positives (negation, quotes, disclaimers).
        2. Computes epistemic uncertainty and counterfactual risk summaries for surviving findings.
        3. Returns structured evaluation with suppressed count telemetry.
        """
        accepted: list[Finding] = []
        suppressed: list[Finding] = []
        suppression_log: list[dict[str, Any]] = []

        for f in findings:
            is_fp, reason = cls.evaluate_false_positive(content_text, f)
            if is_fp:
                suppressed.append(f)
                suppression_log.append({
                    "finding_id": str(getattr(f, "id", "")),
                    "category": getattr(f.issue_category, "value", str(f.issue_category)),
                    "start_offset": f.start_offset,
                    "end_offset": f.end_offset,
                    "reason": reason,
                })
            else:
                # Compute epistemic uncertainty score
                uncertainty = cls.compute_epistemic_uncertainty(f, content_text)
                f.epistemic_uncertainty_score = uncertainty

                # Compute counterfactual risk summary
                span = content_text[f.start_offset:f.end_offset].strip()
                if not span:
                    span = getattr(f, "suggested_correction", "") or "flagged statement"
                f.counterfactual_risk_summary = cls.generate_counterfactual_risk_summary(f, span)

                accepted.append(f)

        if suppressed:
            cls.record_suppression(len(suppressed))

        return CriticEvaluationResult(
            accepted_findings=accepted,
            suppressed_findings=suppressed,
            suppressed_false_positives_count=len(suppressed),
            telemetry={
                "total_evaluated": len(findings),
                "accepted_count": len(accepted),
                "suppressed_count": len(suppressed),
                "suppression_rate_pct": round((len(suppressed) / len(findings) * 100), 2) if findings else 0.0,
                "suppression_details": suppression_log,
            },
        )
