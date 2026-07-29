from __future__ import annotations


def test_platform_admin_can_list_companies(api_client, security_world) -> None:
    response = api_client.get("/api/platform/companies", token=security_world.platform_admin.token)
    assert response.status_code == 200, response.text
    assert str(security_world.tenant_a.company.id) in response.text
    assert str(security_world.tenant_b.company.id) in response.text


def test_platform_admin_cannot_access_tenant_clinical_patient_endpoint(api_client, security_world) -> None:
    response = api_client.get(
        f"/api/patients/{security_world.tenant_a.patient.id}",
        token=security_world.platform_admin.token,
    )
    assert response.status_code == 403, response.text
    assert str(security_world.tenant_a.patient.id) not in response.text
    assert "Paciente A" not in response.text


def test_platform_admin_cannot_download_tenant_clinical_document(api_client, security_world) -> None:
    response = api_client.get(
        f"/api/clinical-documents/{security_world.tenant_a.clinical_document.id}/pdf",
        token=security_world.platform_admin.token,
    )
    assert response.status_code == 403, response.text
    assert security_world.tenant_a.clinical_document_content not in response.content
