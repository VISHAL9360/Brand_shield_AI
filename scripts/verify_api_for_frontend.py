"""
BrandShield AI - End-to-End Frontend Simulation Smoke Test.
Simulates every API interaction and workflow screen made by our
React + Tailwind CSS + Recharts frontend teammate:
1. CORS Preflight (OPTIONS /api/v1/submissions)
2. One-Click Demo Role Switcher (GET /api/v1/auth/demo-tokens)
3. Development Header Bypass (X-Demo-Role: CREATOR | REVIEWER | ADMINISTRATOR)
4. Knowledge Grounding (Brand Profiles, Guidelines, Facts)
5. Dual-Mode Text Submission (POST /api/v1/submissions JSON)
6. Dual-Mode File Upload Dropzone (POST /api/v1/submissions multipart)
7. Instant 1-Step Ingestion & Analysis (POST /api/v1/submissions/analyze-instant)
8. Creator Suggestion Resolution -> v2 Diff (POST /resolve & GET /diff)
9. Reviewer Sign-Off & Clearance Certificate (POST /review & GET /certificate)
10. Attestation Gateway Verification (POST /attestation/verify)
11. Zero-Transformation Recharts Dashboard (GET /api/v1/governance/reports)
"""

import asyncio
from datetime import datetime, timezone
import io
import os
import sys
import time
from typing import Any

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import httpx

from app.core.config import get_settings
from app.infrastructure.db.session import AsyncSessionLocal
from app.infrastructure.db.seed import seed_database
from app.main import app

settings = get_settings()

GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"


class FrontendSimulationRunner:
    def __init__(self) -> None:
        self.results: list[dict[str, Any]] = []

    def record(
        self,
        step: str,
        method: str,
        endpoint: str,
        status_code: int,
        duration_ms: float,
        success: bool,
        notes: str = "",
    ) -> None:
        self.results.append({
            "step": step,
            "method": method,
            "endpoint": endpoint,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "success": success,
            "notes": notes,
        })

    def print_summary(self) -> None:
        print("\n" + "=" * 90)
        print(f"{BOLD}{CYAN}BRANDSHIELD AI - FRONTEND API & DX VERIFICATION REPORT{RESET}")
        print("=" * 90)
        print(
            f"{BOLD}{'Step':<4} {'Method':<7} {'Status':<7} {'Latency':<10} {'Endpoint':<36} {'Result':<10}{RESET}"
        )
        print("-" * 90)

        all_passed = True
        for idx, r in enumerate(self.results, 1):
            status_color = GREEN if r["success"] else RED
            result_str = f"{GREEN}PASS{RESET}" if r["success"] else f"{RED}FAIL{RESET}"
            if not r["success"]:
                all_passed = False
            lat_str = f"{r['duration_ms']:.1f}ms"
            print(
                f"{idx:<4} {r['method']:<7} {status_color}{r['status_code']:<7}{RESET} {lat_str:<10} {r['endpoint']:<36} {result_str}"
            )
            if r["notes"]:
                print(f"     {YELLOW}-> {r['notes']}{RESET}")

        print("=" * 90)

        if all_passed:
            print(f"\n{BOLD}{GREEN}ALL {len(self.results)} FRONTEND INTEGRATION CHECKS PASSED WITH 100% SUCCESS!{RESET}\n")
        else:
            print(f"\n{BOLD}{RED}SOME FRONTEND INTEGRATION CHECKS FAILED.{RESET}\n")

        print(f"{BOLD}{CYAN}RECOMMENDED REACT + VITE .env CONFIGURATION:{RESET}")
        print("-" * 50)
        print("VITE_API_BASE_URL=http://localhost:8000/api/v1")
        print("VITE_ENABLE_DEMO_ROLE_SWITCHER=true")
        print("VITE_DEFAULT_DEMO_ROLE=CREATOR")
        print("-" * 50 + "\n")


async def run_frontend_simulation() -> bool:
    print(f"\n{BOLD}{CYAN}Preparing test environment and ensuring seeded demo data...{RESET}")
    async with AsyncSessionLocal() as session:
        await seed_database(session)

    runner = FrontendSimulationRunner()

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://localhost:8000") as client:

        # ----------------------------------------------------------------------
        # 1. Bulletproof CORS Preflight
        # ----------------------------------------------------------------------
        t0 = time.perf_counter()
        cors_resp = await client.options(
            "/api/v1/submissions",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Authorization, Content-Type, X-Demo-Role",
            },
        )
        cors_lat = (time.perf_counter() - t0) * 1000
        allow_origin = cors_resp.headers.get("access-control-allow-origin")
        allow_cred = cors_resp.headers.get("access-control-allow-credentials")
        cors_ok = (
            cors_resp.status_code == 200
            and allow_origin == "http://localhost:5173"
            and allow_cred == "true"
        )
        runner.record(
            "CORS",
            "OPTIONS",
            "/api/v1/submissions",
            cors_resp.status_code,
            cors_lat,
            cors_ok,
            f"Allowed Origin: {allow_origin}, Credentials: {allow_cred}",
        )

        # ----------------------------------------------------------------------
        # 2. One-Click Demo Role Switcher Endpoint
        # ----------------------------------------------------------------------
        t0 = time.perf_counter()
        demo_tokens_resp = await client.get("/api/v1/auth/demo-tokens")
        dt_lat = (time.perf_counter() - t0) * 1000
        dt_data = demo_tokens_resp.json() if demo_tokens_resp.status_code == 200 else {}
        has_all_roles = (
            "creator" in dt_data
            and "reviewer" in dt_data
            and "administrator" in dt_data
            and "access_token" in dt_data["creator"]
        )
        runner.record(
            "Auth",
            "GET",
            "/api/v1/auth/demo-tokens",
            demo_tokens_resp.status_code,
            dt_lat,
            demo_tokens_resp.status_code == 200 and has_all_roles,
            f"Resolved Roles: {list(dt_data.keys())[:3]}",
        )

        creator_token = dt_data.get("creator", {}).get("access_token")
        reviewer_token = dt_data.get("reviewer", {}).get("access_token")

        # ----------------------------------------------------------------------
        # 3. Development Header Bypass (X-Demo-Role: CREATOR | REVIEWER | ADMINISTRATOR)
        # ----------------------------------------------------------------------
        t0 = time.perf_counter()
        hdr_resp = await client.get("/api/v1/auth/me", headers={"X-Demo-Role": "CREATOR"})
        hdr_lat = (time.perf_counter() - t0) * 1000
        hdr_data = hdr_resp.json() if hdr_resp.status_code == 200 else {}
        hdr_ok = hdr_resp.status_code == 200 and hdr_data.get("role") == "CREATOR"
        runner.record(
            "Auth",
            "GET",
            "/api/v1/auth/me [X-Demo-Role]",
            hdr_resp.status_code,
            hdr_lat,
            hdr_ok,
            f"Current User Role: {hdr_data.get('role')}, Email: {hdr_data.get('email')}",
        )

        # ----------------------------------------------------------------------
        # 4. Brand Profile & Guidelines Setup
        # ----------------------------------------------------------------------
        t0 = time.perf_counter()
        brands_resp = await client.get("/api/v1/brands/", headers={"X-Demo-Role": "ADMINISTRATOR"})
        brands_lat = (time.perf_counter() - t0) * 1000
        brands_data = brands_resp.json() if brands_resp.status_code == 200 else []
        brand_profile_id = brands_data[0]["id"] if brands_data else None
        runner.record(
            "Setup",
            "GET",
            "/api/v1/brands/",
            brands_resp.status_code,
            brands_lat,
            brands_resp.status_code == 200 and len(brands_data) > 0,
            f"Primary Brand Profile ID: {brand_profile_id}",
        )

        t0 = time.perf_counter()
        facts_resp = await client.get("/api/v1/facts/", headers={"X-Demo-Role": "CREATOR"})
        facts_lat = (time.perf_counter() - t0) * 1000
        facts_data = facts_resp.json() if facts_resp.status_code == 200 else []
        runner.record(
            "Setup",
            "GET",
            "/api/v1/facts/",
            facts_resp.status_code,
            facts_lat,
            facts_resp.status_code == 200 and len(facts_data) > 0,
            f"Approved Facts in Catalog: {len(facts_data)}",
        )

        # ----------------------------------------------------------------------
        # 5. Dual-Mode Text Submission (JSON body)
        # ----------------------------------------------------------------------
        t0 = time.perf_counter()
        sub_text_resp = await client.post(
            "/api/v1/submissions",
            headers={
                "X-Demo-Role": "CREATOR",
                "Content-Type": "application/json",
            },
            json={
                "title": "Dual-Mode Text Test",
                "content_text": "Our platform guarantees risk-free 50% quarterly yields with zero down-side risk.",
            },
        )
        sub_text_lat = (time.perf_counter() - t0) * 1000
        sub_text_data = sub_text_resp.json() if sub_text_resp.status_code == 201 else {}
        sub_text_ok = sub_text_resp.status_code == 201 and "id" in sub_text_data
        runner.record(
            "Ingest",
            "POST",
            "/api/v1/submissions [JSON]",
            sub_text_resp.status_code,
            sub_text_lat,
            sub_text_ok,
            f"Submission ID: {sub_text_data.get('id')}, Rev: {sub_text_data.get('current_revision_id')}",
        )

        # ----------------------------------------------------------------------
        # 6. Dual-Mode File Upload Dropzone (multipart/form-data without profile id)
        # ----------------------------------------------------------------------
        fake_pdf = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n%%EOF"
        t0 = time.perf_counter()
        sub_file_resp = await client.post(
            "/api/v1/submissions",
            headers={"X-Demo-Role": "CREATOR"},
            data={"title": "Uploaded Financial Report"},
            files={"file": ("financial_report.pdf", io.BytesIO(fake_pdf), "application/pdf")},
        )
        sub_file_lat = (time.perf_counter() - t0) * 1000
        sub_file_data = sub_file_resp.json() if sub_file_resp.status_code == 201 else {}
        sub_file_ok = sub_file_resp.status_code == 201 and "id" in sub_file_data
        runner.record(
            "Ingest",
            "POST",
            "/api/v1/submissions [Dropzone File]",
            sub_file_resp.status_code,
            sub_file_lat,
            sub_file_ok,
            f"Submission ID: {sub_file_data.get('id')}, Doc Type: {sub_file_data.get('document_type')}",
        )

        # ----------------------------------------------------------------------
        # 7. 1-Step Instant Ingestion & 4-Stage Analysis Endpoint
        # ----------------------------------------------------------------------
        instant_text = (
            "Acme FinTech Global guarantees risk-free 24% annual returns for all institutional investors. "
            "Our proprietary automated algorithms completely eliminate loss under SEC guidelines."
        )
        t0 = time.perf_counter()
        instant_resp = await client.post(
            "/api/v1/submissions/analyze-instant",
            headers={
                "X-Demo-Role": "CREATOR",
                "Content-Type": "application/json",
            },
            json={
                "title": "Instant Marketing Collateral Review",
                "content_text": instant_text,
            },
        )
        instant_lat = (time.perf_counter() - t0) * 1000
        instant_data = instant_resp.json() if instant_resp.status_code == 200 else {}
        instant_ok = (
            instant_resp.status_code == 200
            and "submission" in instant_data
            and "findings" in instant_data
            and "triage_summary" in instant_data
        )
        active_sub_id = instant_data.get("submission", {}).get("id")
        findings_list = instant_data.get("findings", [])
        runner.record(
            "Pipeline",
            "POST",
            "/api/v1/submissions/analyze-instant",
            instant_resp.status_code,
            instant_lat,
            instant_ok,
            f"Total Findings Detected: {len(findings_list)}, Submission: {active_sub_id}",
        )

        # ----------------------------------------------------------------------
        # 8. Creator Suggestion Resolution -> v2 Diff
        # ----------------------------------------------------------------------
        if findings_list and active_sub_id:
            target_finding = findings_list[0]
            target_finding_id = target_finding["id"]

            t0 = time.perf_counter()
            resolve_resp = await client.post(
                f"/api/v1/workflow/{active_sub_id}/findings/{target_finding_id}/resolve",
                headers={"X-Demo-Role": "CREATOR"},
                json={
                    "action": "ACCEPT_SUGGESTION",
                    "custom_replacement": target_finding.get("suggested_correction") or "mitigated investment yields",
                    "rationale": "Accepted compliance suggestion",
                },
            )
            res_lat = (time.perf_counter() - t0) * 1000
            res_data = resolve_resp.json() if resolve_resp.status_code == 200 else {}
            res_ok = resolve_resp.status_code == 200 and "new_revision_id" in res_data
            runner.record(
                "Triage",
                "POST",
                f"/api/v1/workflow/{active_sub_id}/findings/resolve",
                resolve_resp.status_code,
                res_lat,
                res_ok,
                f"Generated Revision #{res_data.get('revision_number')}: {res_data.get('new_revision_id')}",
            )

            # Revision Diff Verification
            t0 = time.perf_counter()
            diff_resp = await client.get(
                f"/api/v1/workflow/{active_sub_id}/revisions/diff?from_revision=1&to_revision=2",
                headers={"X-Demo-Role": "CREATOR"},
            )
            diff_lat = (time.perf_counter() - t0) * 1000
            diff_data = diff_resp.json() if diff_resp.status_code == 200 else {}
            diff_ok = diff_resp.status_code == 200 and "token_diffs" in diff_data
            runner.record(
                "DAG",
                "GET",
                f"/api/v1/workflow/{active_sub_id}/revisions/diff",
                diff_resp.status_code,
                diff_lat,
                diff_ok,
                f"Token Diffs: {len(diff_data.get('token_diffs', []))}, Added: {diff_data.get('total_additions')}",
            )

            # ------------------------------------------------------------------
            # 9. Submit for Human Review & Reviewer Sign-Off
            # ------------------------------------------------------------------
            t0 = time.perf_counter()
            sfr_resp = await client.post(
                f"/api/v1/workflow/{active_sub_id}/submit-for-review",
                headers={"X-Demo-Role": "CREATOR"},
            )
            sfr_lat = (time.perf_counter() - t0) * 1000
            sfr_ok = sfr_resp.status_code == 200
            runner.record(
                "Review",
                "POST",
                f"/api/v1/workflow/{active_sub_id}/submit-for-review",
                sfr_resp.status_code,
                sfr_lat,
                sfr_ok,
                "Workflow State transitioned to IN_HUMAN_REVIEW",
            )

            t0 = time.perf_counter()
            review_resp = await client.post(
                f"/api/v1/workflow/{active_sub_id}/review",
                headers={"X-Demo-Role": "REVIEWER"},
                json={
                    "decision": "APPROVED",
                    "comments": "Audited and verified compliant for publication release.",
                },
            )
            rev_lat = (time.perf_counter() - t0) * 1000
            rev_data = review_resp.json() if review_resp.status_code in (200, 201) else {}
            rev_ok = review_resp.status_code in (200, 201) and rev_data.get("decision") == "APPROVED"
            runner.record(
                "Review",
                "POST",
                f"/api/v1/workflow/{active_sub_id}/review",
                review_resp.status_code,
                rev_lat,
                rev_ok,
                f"Certified Decision: {rev_data.get('decision')}",
            )

            # ------------------------------------------------------------------
            # 10. Publication Attestation Certificate & Verification
            # ------------------------------------------------------------------
            t0 = time.perf_counter()
            cert_resp = await client.get(
                f"/api/v1/submissions/{active_sub_id}/certificate",
                headers={"X-Demo-Role": "REVIEWER"},
            )
            cert_lat = (time.perf_counter() - t0) * 1000
            cert_data = cert_resp.json() if cert_resp.status_code == 200 else {}
            cert_ok = cert_resp.status_code == 200 and "cryptographic_signature" in cert_data
            runner.record(
                "CA",
                "GET",
                f"/api/v1/submissions/{active_sub_id}/certificate",
                cert_resp.status_code,
                cert_lat,
                cert_ok,
                f"Cert ID: {cert_data.get('certificate_id')}, Sig: {cert_data.get('cryptographic_signature', '')[:16]}...",
            )

            if cert_ok:
                t0 = time.perf_counter()
                verify_resp = await client.post(
                    "/api/v1/attestation/verify",
                    json={
                        "certificate_id": cert_data["certificate_id"],
                        "document_sha256_hash": cert_data["document_sha256_hash"],
                    },
                )
                ver_lat = (time.perf_counter() - t0) * 1000
                ver_data = verify_resp.json() if verify_resp.status_code == 200 else {}
                ver_ok = verify_resp.status_code == 200 and ver_data.get("is_valid") is True
                runner.record(
                    "CA",
                    "POST",
                    "/api/v1/attestation/verify",
                    verify_resp.status_code,
                    ver_lat,
                    ver_ok,
                    f"Verification Code: {ver_data.get('verification_code')}",
                )

        # ----------------------------------------------------------------------
        # 11. Zero-Transformation Recharts Governance Dashboard
        # ----------------------------------------------------------------------
        t0 = time.perf_counter()
        gov_resp = await client.get(
            "/api/v1/governance/reports",
            headers={"X-Demo-Role": "REVIEWER"},
        )
        gov_lat = (time.perf_counter() - t0) * 1000
        gov_data = gov_resp.json() if gov_resp.status_code == 200 else {}

        # Validate that all 5 pre-formatted Recharts datasets are present with required keys
        cat_chart = gov_data.get("category_chart_data", [])
        triage_pie = gov_data.get("triage_pie_data", [])
        sev_breakdown = gov_data.get("severity_breakdown", [])
        trend_series = gov_data.get("review_trend_series", [])
        kpis = gov_data.get("summary_kpis", [])

        has_recharts_keys = (
            isinstance(cat_chart, list)
            and isinstance(triage_pie, list)
            and isinstance(sev_breakdown, list)
            and isinstance(trend_series, list)
            and isinstance(kpis, list)
            and len(triage_pie) > 0
            and all("name" in x and "value" in x and "fill" in x for x in triage_pie)
            and all("name" in x and "value" in x and "fill" in x for x in sev_breakdown)
        )

        runner.record(
            "Recharts",
            "GET",
            "/api/v1/governance/reports",
            gov_resp.status_code,
            gov_lat,
            gov_resp.status_code == 200 and has_recharts_keys,
            f"Charts: category({len(cat_chart)}), pie({len(triage_pie)}), severity({len(sev_breakdown)}), kpis({len(kpis)})",
        )

    runner.print_summary()
    return all(r["success"] for r in runner.results)


if __name__ == "__main__":
    success = asyncio.run(run_frontend_simulation())
    sys.exit(0 if success else 1)
