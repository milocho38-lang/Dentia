from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Iterable


class RouteCategory(StrEnum):
    PUBLIC = "pública"
    AUTHENTICATED = "autenticada"
    CLINICAL = "clínica"
    FINANCIAL = "financiera"
    ADMINISTRATIVE = "administrativa"
    PLATFORM = "plataforma"
    FILE_DOWNLOAD = "archivo/descarga"


class RiskLevel(StrEnum):
    CRITICAL = "crítico"
    HIGH = "alto"
    MEDIUM = "medio"
    LOW = "bajo"


class Scope(StrEnum):
    PLATFORM = "plataforma"
    COMPANY = "empresa"
    SITE = "sede"
    USER = "usuario"


class ControlType(StrEnum):
    AUTHENTICATION = "autenticación"
    PERMISSION = "permiso"
    TENANT = "tenant"
    SITE = "sede"
    OWNER = "propietario"


class TestStatus(StrEnum):
    DB_BACKED = "DB_BACKED"
    CHARACTERIZED = "CHARACTERIZED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    PENDING = "PENDING"


@dataclass(frozen=True)
class RouteSecurityEntry:
    method: str
    path: str
    module: str
    category: RouteCategory
    risk: RiskLevel
    scope: Scope
    controls: tuple[ControlType, ...]
    test_status: TestStatus
    covered_by: str
    justification: str = ""

    @property
    def is_download(self) -> bool:
        lower_path = self.path.lower()
        return (
            self.category == RouteCategory.FILE_DOWNLOAD
            or "pdf" in lower_path
            or "receipt" in lower_path
            or "download" in lower_path
            or "/branding/{kind}" in lower_path
        )

    @property
    def is_mutation(self) -> bool:
        return self.method in {"POST", "PUT", "PATCH", "DELETE"}


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


def _module_for(path: str) -> str:
    if path == "/health":
        return "health"
    if path.startswith("/api/auth"):
        return "auth"
    if path.startswith("/api/platform"):
        return "platform"
    if path.startswith("/api/reports"):
        return "reports"
    if path.startswith("/api/finance"):
        return "finance"
    if path.startswith("/api/payments"):
        return "payments"
    if path.startswith("/api/budgets"):
        return "budgets"
    if path.startswith("/api/treatments"):
        return "treatments"
    if path.startswith("/api/company/branding"):
        return "branding"
    if path.startswith("/api/company"):
        return "company"
    if path.startswith("/api/sites"):
        return "sites"
    if path.startswith("/api/dentists"):
        return "dentists"
    if path.startswith("/api/users"):
        return "users"
    if path.startswith("/api/prescriptions"):
        return "prescriptions"
    if path.startswith("/api/clinical-documents"):
        return "clinical_documents"
    if path.startswith("/api/patients"):
        return "patients"
    if path.startswith("/api/appointments"):
        return "appointments"
    if path.startswith("/api/agenda"):
        return "agenda"
    if path.startswith("/api/clinical-records"):
        return "clinical_records"
    if path.startswith("/api/clinical-evolutions"):
        return "clinical_evolutions"
    if path.startswith("/api/odontogram") or "/odontogram" in path:
        return "odontogram"
    if path.startswith("/api/followups"):
        return "followups"
    if path.startswith("/api/procedure-catalog"):
        return "procedure_catalog"
    return "unclassified"


def _category_for(path: str) -> RouteCategory:
    lower_path = path.lower()
    if (path == "/health") or path.startswith("/api/auth"):
        return RouteCategory.PUBLIC if any((method, path) in PUBLIC_ROUTES for method in {"GET", "POST"}) else RouteCategory.AUTHENTICATED
    if path.startswith("/api/platform"):
        return RouteCategory.PLATFORM
    if (
        "pdf" in lower_path
        or "receipt" in lower_path
        or "download" in lower_path
        or path.startswith("/api/company/branding/{kind}")
    ):
        return RouteCategory.FILE_DOWNLOAD
    if path.startswith(("/api/finance", "/api/payments", "/api/budgets")):
        return RouteCategory.FINANCIAL
    if path.startswith(("/api/company", "/api/sites", "/api/dentists", "/api/users", "/api/procedure-catalog")):
        return RouteCategory.ADMINISTRATIVE
    if path.startswith("/api/reports"):
        return RouteCategory.FINANCIAL
    return RouteCategory.CLINICAL


def _scope_for(path: str) -> Scope:
    if path.startswith("/api/platform"):
        return Scope.PLATFORM
    if path.startswith("/api/auth"):
        return Scope.USER
    if "/sites" in path or path.startswith("/api/agenda") or path.startswith("/api/reports"):
        return Scope.SITE
    return Scope.COMPANY


def _controls_for(path: str, category: RouteCategory) -> tuple[ControlType, ...]:
    if (path == "/health") or any((method, path) in PUBLIC_ROUTES for method in {"GET", "POST"}):
        return (ControlType.AUTHENTICATION,)
    controls: list[ControlType] = [ControlType.AUTHENTICATION]
    if path.startswith("/api/"):
        controls.append(ControlType.PERMISSION)
    if category not in {RouteCategory.PUBLIC, RouteCategory.AUTHENTICATED, RouteCategory.PLATFORM}:
        controls.append(ControlType.TENANT)
    if _scope_for(path) == Scope.SITE:
        controls.append(ControlType.SITE)
    if "{user_id}" in path:
        controls.append(ControlType.OWNER)
    return tuple(dict.fromkeys(controls))


def _is_critical(path: str, method: str, category: RouteCategory) -> bool:
    if category in {RouteCategory.FILE_DOWNLOAD, RouteCategory.FINANCIAL, RouteCategory.PLATFORM}:
        return True
    if path.startswith(("/api/users", "/api/company", "/api/sites", "/api/dentists", "/api/reports")):
        return True
    if path.startswith("/api/treatments") and (
        "budget" in path or "payments" in path or method in {"POST", "PATCH", "DELETE"}
    ):
        return True
    return False


def _status_and_coverage(method: str, path: str, category: RouteCategory, risk: RiskLevel) -> tuple[TestStatus, str, str]:
    key = (method, path)
    if key in PUBLIC_ROUTES:
        return TestStatus.NOT_APPLICABLE, "backend/scripts/security_characterization_tests.py", "Ruta pública explícita."
    if key in AUTHENTICATED_ONLY_ROUTES:
        return TestStatus.CHARACTERIZED, "backend/scripts/security_characterization_tests.py", "Ruta de sesión propia autenticada, sin datos tenant externos."

    if category == RouteCategory.FILE_DOWNLOAD:
        if path.startswith("/api/company/branding/{kind}"):
            return TestStatus.DB_BACKED, "backend/tests/administration/test_admin_finance_reports.py::test_branding_authorized_update_assets_and_insufficient_role_denied", ""
        if path.startswith("/api/budgets"):
            return TestStatus.DB_BACKED, "backend/tests/finance/test_budgets_payments_finance.py::test_budget_pdf_authorized_and_cross_tenant_denied", ""
        if path.startswith("/api/payments"):
            return TestStatus.DB_BACKED, "backend/tests/finance/test_budgets_payments_finance.py::test_payment_receipt_authorized_cross_tenant_and_role_denied", ""
        if path.startswith("/api/prescriptions"):
            return TestStatus.DB_BACKED, "backend/tests/storage/test_document_downloads.py", ""
        if path.startswith("/api/clinical-documents"):
            return TestStatus.DB_BACKED, "backend/tests/storage/test_document_downloads.py", ""
        return TestStatus.PENDING, "", "Ruta de descarga sin prueba DB-backed asignada."

    if path.startswith(("/api/payments", "/api/finance", "/api/budgets")) or "/payments" in path or "/budget" in path:
        return TestStatus.DB_BACKED, "backend/tests/finance/test_budgets_payments_finance.py", ""
    if path.startswith("/api/reports"):
        return TestStatus.DB_BACKED, "backend/tests/administration/test_admin_finance_reports.py::test_reports_are_tenant_scoped_financially_restricted_and_platform_denied", ""
    if path.startswith(("/api/company", "/api/sites", "/api/dentists", "/api/users")):
        return TestStatus.DB_BACKED, "backend/tests/administration/test_admin_finance_reports.py", ""
    if path.startswith("/api/platform"):
        return TestStatus.DB_BACKED, "backend/tests/security/test_platform_admin.py backend/tests/administration/test_admin_finance_reports.py", ""
    if path.startswith(("/api/patients", "/api/agenda", "/api/appointments", "/api/treatments", "/api/clinical-records", "/api/clinical-evolutions", "/api/odontogram", "/api/prescriptions", "/api/clinical-documents")):
        return TestStatus.DB_BACKED, "backend/tests/multitenancy backend/tests/storage backend/tests/security", ""
    if path.startswith(("/api/followups", "/api/procedure-catalog")):
        return TestStatus.CHARACTERIZED, "backend/scripts/security_characterization_tests.py", "Ruta no crítica para la compuerta financiera/administrativa de FIX2; cubierta por grafo de auth/permisos."
    if risk == RiskLevel.LOW:
        return TestStatus.CHARACTERIZED, "backend/scripts/security_characterization_tests.py", "Ruta no crítica cubierta por grafo de permisos."
    return TestStatus.CHARACTERIZED, "backend/scripts/security_characterization_tests.py", "Ruta privada no crítica cubierta por grafo de auth/permisos; agregar DB-backed si se vuelve crítica."


def classify_route(method: str, path: str) -> RouteSecurityEntry:
    category = _category_for(path)
    module = _module_for(path)
    risk = RiskLevel.CRITICAL if _is_critical(path, method, category) else (
        RiskLevel.LOW if (method, path) in PUBLIC_ROUTES or (method, path) in AUTHENTICATED_ONLY_ROUTES else RiskLevel.HIGH
    )
    status, covered_by, justification = _status_and_coverage(method, path, category, risk)
    return RouteSecurityEntry(
        method=method,
        path=path,
        module=module,
        category=category,
        risk=risk,
        scope=_scope_for(path),
        controls=_controls_for(path, category),
        test_status=status,
        covered_by=covered_by,
        justification=justification,
    )


def iter_api_routes(app) -> Iterable[tuple[str, str]]:
    for route in app.routes:
        path = getattr(route, "path", "")
        if not path.startswith("/api/") and path != "/health":
            continue
        for method in sorted(getattr(route, "methods", set()) or []):
            if method in {"HEAD", "OPTIONS"}:
                continue
            yield method, path


def build_route_security_registry(app) -> list[RouteSecurityEntry]:
    return sorted(
        (classify_route(method, path) for method, path in iter_api_routes(app)),
        key=lambda entry: (entry.path, entry.method),
    )


def route_security_metrics(entries: Iterable[RouteSecurityEntry]) -> dict[str, int]:
    collected = list(entries)
    return {
        "total": len(collected),
        "critical": sum(entry.risk == RiskLevel.CRITICAL for entry in collected),
        "db_backed": sum(entry.test_status == TestStatus.DB_BACKED for entry in collected),
        "characterized": sum(entry.test_status == TestStatus.CHARACTERIZED for entry in collected),
        "not_applicable": sum(entry.test_status == TestStatus.NOT_APPLICABLE for entry in collected),
        "pending": sum(entry.test_status == TestStatus.PENDING for entry in collected),
        "downloads": sum(entry.is_download for entry in collected),
        "downloads_db_backed": sum(entry.is_download and entry.test_status == TestStatus.DB_BACKED for entry in collected),
        "critical_mutations": sum(entry.risk == RiskLevel.CRITICAL and entry.is_mutation for entry in collected),
        "critical_mutations_db_backed": sum(entry.risk == RiskLevel.CRITICAL and entry.is_mutation and entry.test_status == TestStatus.DB_BACKED for entry in collected),
    }
