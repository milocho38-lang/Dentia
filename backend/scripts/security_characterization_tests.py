#!/usr/bin/env python3
"""C018R.4 security characterization tests.

This suite is intentionally dependency-light: it uses only the standard
library plus Dentia's installed application dependencies. It does not open a
network connection, does not require a live server, and does not mutate data.

It verifies hard security invariants that can be checked from the current
codebase:

- protected API endpoints declare authentication/permission dependencies;
- PDF downloads are UUID-based, not arbitrary path-based;
- document and prescription downloads scope by company and verify SHA-256;
- storage path helpers enforce root containment;
- platform permissions are not mixed into business roles;
- production Compose keeps the known project/volume/network names and storage
  bind mount;
- generated clinical storage and real env files remain ignored by Git.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"


PUBLIC_ROUTES = {
    ("GET", "/health"),
    ("POST", "/api/auth/login"),
    ("POST", "/api/auth/refresh"),
}

AUTHENTICATED_ONLY_ROUTES = {
    ("POST", "/api/auth/logout"),
    ("GET", "/api/auth/me"),
    ("GET", "/api/auth/sites"),
    ("POST", "/api/auth/switch-site"),
    ("POST", "/api/auth/change-password"),
}

EXPECTED_ROUTE_COUNT = 187


def read(relative: str) -> str:
    return (REPO_ROOT / relative).read_text(encoding="utf-8")


def git_check_ignore(path: str) -> bool:
    result = subprocess.run(
        ["git", "check-ignore", "-q", path],
        cwd=REPO_ROOT,
        check=False,
    )
    return result.returncode == 0


class EndpointProtectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        sys.path.insert(0, str(BACKEND_ROOT))
        # Import lazily after sys.path is set. This does not open DB
        # connections; it only builds the FastAPI router graph.
        from app.main import create_app  # noqa: PLC0415

        cls.app = create_app()

    def test_non_public_api_routes_require_authentication_or_permission(self) -> None:
        unprotected: list[str] = []
        for route in self.app.routes:
            path = getattr(route, "path", "")
            methods = sorted(getattr(route, "methods", set()) or [])
            if not path.startswith("/api/") and path != "/health":
                continue
            for method in methods:
                if method in {"HEAD", "OPTIONS"}:
                    continue
                key = (method, path)
                if key in PUBLIC_ROUTES:
                    continue
                dependency_names = {
                    getattr(dependency.call, "__name__", repr(dependency.call))
                    for dependency in getattr(route, "dependant", None).dependencies
                }
                protected = bool(
                    {"permission_dependency", "get_current_auth_context"}
                    & dependency_names
                )
                if not protected:
                    unprotected.append(f"{method} {path} deps={sorted(dependency_names)}")
        self.assertEqual(unprotected, [])

    def test_authenticated_only_routes_are_known_and_explicit(self) -> None:
        discovered = set()
        for route in self.app.routes:
            path = getattr(route, "path", "")
            for method in getattr(route, "methods", set()) or []:
                if method in {"HEAD", "OPTIONS"}:
                    continue
                if (method, path) in AUTHENTICATED_ONLY_ROUTES:
                    discovered.add((method, path))
        self.assertEqual(discovered, AUTHENTICATED_ONLY_ROUTES)

    def test_pdf_download_endpoints_are_identifier_based(self) -> None:
        unsafe: list[str] = []
        for route in self.app.routes:
            path = getattr(route, "path", "")
            lower_path = path.lower()
            if (
                "pdf" not in lower_path
                and "download" not in lower_path
                and "receipt" not in lower_path
            ):
                continue
            if any(fragment in path.lower() for fragment in {"{path", "{file", "{filename", "{storage"}):
                unsafe.append(path)
        self.assertEqual(unsafe, [])

    def test_route_security_registry_covers_all_private_routes(self) -> None:
        from tests.route_security_registry import (  # noqa: PLC0415
            RiskLevel,
            TestStatus,
            build_route_security_registry,
            route_security_metrics,
        )

        entries = build_route_security_registry(self.app)
        metrics = route_security_metrics(entries)
        self.assertEqual(metrics["total"], EXPECTED_ROUTE_COUNT)

        pending = [
            f"{entry.method} {entry.path} ({entry.module})"
            for entry in entries
            if entry.test_status == TestStatus.PENDING
        ]
        self.assertEqual(pending, [])

        critical_pending = [
            f"{entry.method} {entry.path} ({entry.module})"
            for entry in entries
            if entry.risk == RiskLevel.CRITICAL and entry.test_status == TestStatus.PENDING
        ]
        self.assertEqual(critical_pending, [])

        not_applicable_without_reason = [
            f"{entry.method} {entry.path}"
            for entry in entries
            if entry.test_status == TestStatus.NOT_APPLICABLE and not entry.justification
        ]
        self.assertEqual(not_applicable_without_reason, [])

    def test_download_routes_have_db_backed_security_tests(self) -> None:
        from tests.route_security_registry import (  # noqa: PLC0415
            TestStatus,
            build_route_security_registry,
        )

        entries = build_route_security_registry(self.app)
        missing = [
            f"{entry.method} {entry.path}"
            for entry in entries
            if entry.is_download and entry.test_status != TestStatus.DB_BACKED
        ]
        self.assertEqual(missing, [])

    def test_critical_mutations_have_db_backed_cross_tenant_contracts(self) -> None:
        from tests.route_security_registry import (  # noqa: PLC0415
            RiskLevel,
            TestStatus,
            build_route_security_registry,
        )

        entries = build_route_security_registry(self.app)
        missing = [
            f"{entry.method} {entry.path}"
            for entry in entries
            if entry.risk == RiskLevel.CRITICAL
            and entry.method in {"POST", "PUT", "PATCH", "DELETE"}
            and entry.test_status != TestStatus.DB_BACKED
        ]
        self.assertEqual(missing, [])


class DocumentStorageSafetyTests(unittest.TestCase):
    def test_clinical_document_download_is_company_scoped_and_hash_verified(self) -> None:
        source = read("backend/app/services/clinical_document_service.py")
        self.assertIn("ClinicalDocument.company_id == context.user.company_id", source)
        self.assertIn("hashlib.sha256(content).hexdigest() != document.pdf_sha256", source)
        self.assertIn("CLINICAL_DOCUMENT_PDF_INTEGRITY_FAILED", source)

    def test_prescription_download_is_company_scoped_and_hash_verified(self) -> None:
        source = read("backend/app/services/prescription_service.py")
        self.assertIn("Prescription.company_id == context.user.company_id", source)
        self.assertIn("hashlib.sha256(content).hexdigest() != prescription.pdf_sha256", source)
        self.assertIn("PRESCRIPTION_PDF_INTEGRITY_FAILED", source)

    def test_budget_and_payment_pdf_generation_are_company_scoped(self) -> None:
        source = read("backend/app/services/treatment_service.py")
        self.assertIn("Budget.company_id == context.user.company_id", source)
        self.assertIn("TreatmentPayment.company_id == context.user.company_id", source)
        self.assertIn("generate_budget_pdf", source)
        self.assertIn("generate_payment_receipt_pdf", source)

    def test_storage_path_helpers_enforce_root_containment(self) -> None:
        for relative in [
            "backend/app/services/clinical_document_service.py",
            "backend/app/services/prescription_service.py",
        ]:
            source = read(relative)
            self.assertIn("candidate = (root / relative_path).resolve()", source)
            self.assertIn("if root not in candidate.parents and candidate != root", source)

    def test_backup_inventory_rejects_unsafe_paths_and_links(self) -> None:
        source = read("scripts/production/dentia_document_inventory.py")
        self.assertIn("path.is_absolute()", source)
        self.assertIn("\"..\"", source)
        self.assertIn("member.issym() or member.islnk()", source)
        self.assertIn("hash_mismatch", source)


class AuthorizationCatalogTests(unittest.TestCase):
    def test_platform_permission_set_is_separate_from_clinical_sensitive_permissions(self) -> None:
        source = read("backend/app/core/security_catalog.py")
        tree = ast.parse(source)
        names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        self.assertIn("PLATFORM_PERMISSION_CODES", names)
        self.assertIn("CLINICAL_SENSITIVE_PERMISSION_CODES", names)
        self.assertIn("CLINIC_ADMIN_PERMISSION_CODES", names)
        self.assertIn("ALL_PERMISSION_CODES - PLATFORM_PERMISSION_CODES - CLINICAL_SENSITIVE_PERMISSION_CODES", source)

    def test_platform_admin_does_not_inherit_clinical_permissions_by_catalog_design(self) -> None:
        source = read("backend/app/core/security_catalog.py")
        self.assertIn('"platform.companies.view"', source)
        self.assertIn('"platform.companies.manage"', source)
        platform_role_block = source[source.find("RoleDefinition("):]
        self.assertIn("PLATFORM_ADMIN", platform_role_block)
        self.assertNotIn("clinical_documents.download\",", platform_role_block.split("PLATFORM_ADMIN", 1)[1].split(")", 1)[0])


class ComposeAndArtifactSafetyTests(unittest.TestCase):
    def test_compose_preserves_production_project_volume_network_and_mount(self) -> None:
        compose = read("docker-compose.yml")
        self.assertIn("name: dentia", compose)
        self.assertIn("image: postgres:17", compose)
        self.assertIn("dentia_db_data:/var/lib/postgresql/data", compose)
        self.assertIn("dentia-network", compose)
        self.assertIn("./backend/storage:/app/storage", compose)
        self.assertIn('"${DENTIA_BACKEND_BIND:-8001}:8000"', compose)
        self.assertIn('"${DENTIA_FRONTEND_BIND:-3001}:3000"', compose)
        self.assertIn("API_PROXY_TARGET", compose)

    def test_real_env_and_generated_storage_are_git_ignored(self) -> None:
        self.assertTrue(git_check_ignore(".env"))
        self.assertTrue(git_check_ignore(".env.production"))
        self.assertTrue(git_check_ignore("backend/storage/prescriptions/fake.pdf"))
        self.assertTrue(git_check_ignore("backend/storage/branding/fake.png"))
        self.assertTrue(git_check_ignore("backups/fake.dump"))
        self.assertFalse(git_check_ignore(".env.production.example"))

    def test_c018r3_is_marked_closed_in_readiness_documentation(self) -> None:
        source = read("DOCS/readiness/C018R3-Complete-Backup-and-Restore.md")
        self.assertIn("C018R.3 — CERRADO", source)
        self.assertIn("dentia_20260729_040400", source)
        self.assertIn("BACKUP_VALID", source)
        self.assertIn("RESTORE_VALID", source)
        self.assertIn("dentia_dentia_db_data", source)


if __name__ == "__main__":
    os.environ.setdefault("APP_ENV", "test")
    unittest.main(verbosity=2)
