from uuid import uuid4

from sqlalchemy import func, select

from app.models.audit_event import AuditEvent
from app.models.consent_template import ConsentTemplateVersion
from app.models.treatment import ProcedureCatalogItem
from app.services.consent_template_service import find_applicable_published_templates, validate_content


def _payload(code: str = "CONSENT-DEMO", *, country: str = "CO", scope: str = "GENERAL", sites=None, procedures=None):
    return {
        "code": code,
        "name": "Plantilla ficticia de seguridad",
        "description": "Contenido de pruebas; no aprobado para uso clínico.",
        "document_kind": "PROCEDURE_CONSENT",
        "country_code": country,
        "language_code": f"es-{country}",
        "initial_version": {
            "title": "Consentimiento de demostración",
            "content": "# BORRADOR DE DEMOSTRACIÓN\n\nPaciente: **{{ patient.full_name }}**\n\n- Profesional: {{ professional.full_name }}\n- Especialidad: {{ professional.specialty }}\n- Registro: {{ professional.license_number }}\n- Procedimiento: {{ procedure.name }}\n- Plan: {{ treatment.plan_number }}\n- Generado: {{ document.generated_date }} {{ document.local_time }}",
            "change_summary": "Versión ficticia inicial",
            "scope_type": scope,
            "priority": 100 if scope == "SPECIFIC" else 0,
            "site_ids": sites or [],
            "procedure_ids": procedures or [],
            "specialties": [],
        },
    }


def _create(api_client, actor, payload=None):
    response = api_client.post("/api/consent-templates", token=actor.token, json=payload or _payload())
    assert response.status_code == 201, response.text
    return response.json()


def test_template_version_lifecycle_is_immutable_atomic_and_audited(api_client, db_session, security_world):
    actor = security_world.tenant_a.dentist_admin
    created = _create(api_client, actor)
    template_id = created["id"]
    first = created["draft_versions"][0]

    preview = api_client.post(f"/api/consent-templates/{template_id}/versions/{first['id']}/preview", token=actor.token)
    assert preview.status_code == 200
    assert preview.json()["warning"] == "BORRADOR DE DEMOSTRACIÓN — NO APROBADO PARA USO CLÍNICO"
    assert "Paciente de demostración" in preview.json()["rendered_content"]
    assert "Dra. Profesional de demostración" in preview.json()["rendered_content"]
    assert "Especialidad de demostración" in preview.json()["rendered_content"]
    assert "REG-DEMO" in preview.json()["rendered_content"]
    assert "PLAN-DEMO-001" in preview.json()["rendered_content"]
    assert "10:30 a. m." in preview.json()["rendered_content"]

    published = api_client.post(f"/api/consent-templates/{template_id}/versions/{first['id']}/publish", token=actor.token)
    assert published.status_code == 200, published.text
    first_published = published.json()
    assert first_published["status"] == "PUBLISHED"
    assert len(first_published["content_sha256"]) == 64
    assert sorted(first_published["variable_schema_snapshot"]) == [
        "document.generated_date",
        "document.local_time",
        "patient.full_name",
        "procedure.name",
        "professional.full_name",
        "professional.license_number",
        "professional.specialty",
        "treatment.plan_number",
    ]

    immutable = api_client.patch(
        f"/api/consent-templates/{template_id}/versions/{first['id']}",
        token=actor.token,
        json={**_payload()["initial_version"], "row_version": first_published["row_version"]},
    )
    assert immutable.status_code == 409

    draft = api_client.post(
        f"/api/consent-templates/{template_id}/versions/{first['id']}/create-draft",
        token=actor.token,
        json={"change_summary": "Cambio prospectivo de prueba"},
    )
    assert draft.status_code == 201, draft.text
    second = draft.json()
    assert second["version_number"] == 2
    assert second["based_on_version_id"] == first["id"]

    second_published = api_client.post(f"/api/consent-templates/{template_id}/versions/{second['id']}/publish", token=actor.token)
    assert second_published.status_code == 200, second_published.text
    history = api_client.get(f"/api/consent-templates/{template_id}/versions", token=actor.token).json()
    assert {item["version_number"]: item["status"] for item in history} == {2: "PUBLISHED", 1: "SUPERSEDED"}
    assert db_session.scalar(select(func.count()).select_from(ConsentTemplateVersion).where(ConsentTemplateVersion.template_id == template_id, ConsentTemplateVersion.status == "PUBLISHED")) == 1

    retired = api_client.post(
        f"/api/consent-templates/{template_id}/versions/{second['id']}/retire",
        token=actor.token,
        json={"reason": "Retiro administrativo de prueba"},
    )
    assert retired.status_code == 200
    assert retired.json()["status"] == "RETIRED"

    actions = set(db_session.scalars(select(AuditEvent.action).where(AuditEvent.entity_id == template_id)))
    assert {"CONSENT_TEMPLATE_CREATED", "CONSENT_TEMPLATE_PREVIEW_GENERATED", "CONSENT_TEMPLATE_VERSION_PUBLISHED", "CONSENT_TEMPLATE_VERSION_SUPERSEDED", "CONSENT_TEMPLATE_VERSION_RETIRED"}.issubset(actions)
    audit_response = api_client.get(f"/api/consent-templates/{template_id}/audit", token=actor.token)
    assert audit_response.status_code == 200
    assert all("content" not in (item.get("detail") or {}) for item in audit_response.json())


def test_tenant_associations_idor_and_role_boundaries(api_client, db_session, security_world):
    tenant_a = security_world.tenant_a
    tenant_b = security_world.tenant_b
    procedure_a = ProcedureCatalogItem(company_id=tenant_a.company.id, name="Procedimiento ficticio A", normalized_name=f"procedimiento ficticio a {uuid4()}", is_active=True, created_by=tenant_a.admin.user.id)
    procedure_b = ProcedureCatalogItem(company_id=tenant_b.company.id, name="Procedimiento ficticio B", normalized_name=f"procedimiento ficticio b {uuid4()}", is_active=True, created_by=tenant_b.admin.user.id)
    db_session.add_all([procedure_a, procedure_b])
    db_session.commit()

    created_a = _create(api_client, tenant_a.dentist, _payload("A-SPECIFIC", scope="SPECIFIC", sites=[str(tenant_a.site_1.id)], procedures=[str(procedure_a.id)]))
    _create(api_client, tenant_b.dentist_admin, _payload("A-SPECIFIC", country="CL"))

    cross_list = api_client.get("/api/consent-templates", token=tenant_b.dentist_admin.token)
    assert cross_list.status_code == 200
    assert all(item["company_id"] == str(tenant_b.company.id) for item in cross_list.json()["items"])
    assert api_client.get(f"/api/consent-templates/{created_a['id']}", token=tenant_b.dentist_admin.token).status_code == 404
    assert api_client.get(f"/api/consent-templates/{created_a['id']}", token=security_world.platform_admin.token).status_code == 403

    bad_site = api_client.post("/api/consent-templates", token=tenant_a.dentist_admin.token, json=_payload("BAD-SITE", scope="SPECIFIC", sites=[str(tenant_b.site_1.id)]))
    assert bad_site.status_code == 403
    bad_procedure = api_client.post("/api/consent-templates", token=tenant_a.dentist_admin.token, json=_payload("BAD-PROC", scope="SPECIFIC", procedures=[str(procedure_b.id)]))
    assert bad_procedure.status_code == 403

    first = created_a["draft_versions"][0]
    assert api_client.post(f"/api/consent-templates/{created_a['id']}/versions/{first['id']}/publish", token=tenant_a.dentist.token).status_code == 403
    assert api_client.patch(
        f"/api/consent-templates/{created_a['id']}/versions/{first['id']}",
        token=tenant_a.dentist_admin.token,
        json={**_payload("A-SPECIFIC", scope="SPECIFIC", sites=[str(tenant_a.site_1.id)], procedures=[str(procedure_a.id)])["initial_version"], "row_version": first["row_version"]},
    ).status_code == 200
    assert api_client.get("/api/consent-templates", token=tenant_a.secretary.token).status_code == 200
    assert api_client.post("/api/consent-templates", token=tenant_a.secretary.token, json=_payload("NO-SECRETARY")).status_code == 403


def test_variables_content_limits_void_and_applicability(api_client, db_session, security_world):
    actor = security_world.tenant_a.dentist_admin
    catalog = api_client.get("/api/consent-template-catalog/variables", token=actor.token)
    assert catalog.status_code == 200
    catalog_codes = {item["code"] for item in catalog.json()}
    assert {
        "professional.full_name",
        "professional.specialty",
        "professional.license_number",
        "treatment.plan_number",
        "document.generated_date",
        "document.local_time",
    }.issubset(catalog_codes)
    assert validate_content("{{ patient.full_name }}", require_registered=True).valid
    assert validate_content("{{ professional.full_name }} {{ professional.specialty }} {{ professional.license_number }}", require_registered=True).valid
    assert not validate_content("{{ patient.__class__ }}", require_registered=True).valid
    assert not validate_content("{{ patient.full_name | safe }}", require_registered=True).valid
    assert validate_content("<script>alert(1)</script>").syntax_errors
    assert validate_content("[clic](javascript:alert(1))").syntax_errors

    malicious = _payload("XSS")
    malicious["initial_version"]["content"] = "<img src=x onerror=alert(1)>"
    assert api_client.post("/api/consent-templates", token=actor.token, json=malicious).status_code == 422

    unknown = _create(api_client, actor, {**_payload("UNKNOWN"), "initial_version": {**_payload("UNKNOWN")["initial_version"], "content": "{{ patient.unknown }}"}})
    unknown_version = unknown["draft_versions"][0]
    validation = api_client.post(f"/api/consent-templates/{unknown['id']}/versions/{unknown_version['id']}/validate", token=actor.token)
    assert validation.status_code == 200
    assert validation.json()["valid"] is False
    preview = api_client.post(f"/api/consent-templates/{unknown['id']}/versions/{unknown_version['id']}/preview", token=actor.token)
    assert preview.status_code == 200
    assert "[VARIABLE NO REGISTRADA: patient.unknown]" in preview.json()["rendered_content"]
    publish = api_client.post(f"/api/consent-templates/{unknown['id']}/versions/{unknown_version['id']}/publish", token=actor.token)
    assert publish.status_code == 422
    assert "No se puede publicar. Corrige las siguientes variables no registradas" in publish.text
    voided = api_client.post(f"/api/consent-templates/{unknown['id']}/versions/{unknown_version['id']}/void", token=actor.token, json={"reason": "Variable inválida de prueba"})
    assert voided.status_code == 200
    assert voided.json()["status"] == "VOIDED"

    published_template = _create(api_client, actor, _payload("APPLICABLE"))
    version = published_template["draft_versions"][0]
    published = api_client.post(f"/api/consent-templates/{published_template['id']}/versions/{version['id']}/publish", token=actor.token)
    assert published.status_code == 200
    candidates = find_applicable_published_templates(db_session, company_id=security_world.tenant_a.company.id, country_code="CO", language_code="es-CO")
    assert [item.template_code for item in candidates] == ["APPLICABLE"]
    assert find_applicable_published_templates(db_session, company_id=security_world.tenant_b.company.id, country_code="CO", language_code="es-CO") == []


def test_duplicate_codes_and_optimistic_conflict(api_client, security_world):
    actor = security_world.tenant_a.dentist_admin
    created = _create(api_client, actor, _payload("UNIQUE-CODE"))
    assert api_client.post("/api/consent-templates", token=actor.token, json=_payload("UNIQUE-CODE")).status_code == 409
    draft = created["draft_versions"][0]
    payload = {**_payload("UNIQUE-CODE")["initial_version"], "row_version": draft["row_version"]}
    first = api_client.patch(f"/api/consent-templates/{created['id']}/versions/{draft['id']}", token=actor.token, json=payload)
    assert first.status_code == 200
    stale = api_client.patch(f"/api/consent-templates/{created['id']}/versions/{draft['id']}", token=actor.token, json=payload)
    assert stale.status_code == 409
