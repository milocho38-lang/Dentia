from sqlalchemy import select

from app.models.agenda import Patient


SHARED_MOBILE_FORMATTED = "(300) 123-4567"
SHARED_MOBILE_PLAIN = "3001234567"


def _patient_payload(
    *,
    first_names: str,
    document: str,
    mobile: str,
    birth_date: str,
    minor: bool = False,
):
    return {
        "first_names": first_names,
        "last_names": "Contacto Compartido",
        "document_type": "TI" if minor else "CC",
        "document": document,
        "mobile": mobile,
        "birth_date": birth_date,
        "sex": "no informa",
        "acknowledge_duplicate_warning": False,
        "responsibles": [
            {
                "name": "Responsable Familiar",
                "document_type": "CC",
                "document": f"R-{document}",
                "relationship": "Madre",
                "mobile": SHARED_MOBILE_PLAIN,
                "email": None,
                "is_primary": True,
            }
        ] if minor else [],
    }


def test_create_and_update_patients_can_share_normalized_mobile(
    api_client, db_session, security_world
):
    tenant = security_world.tenant_a
    minor = api_client.post(
        "/api/patients",
        token=tenant.dentist_admin.token,
        json=_patient_payload(
            first_names="Niña",
            document="TI-SHARED-1",
            mobile=SHARED_MOBILE_FORMATTED,
            birth_date="2015-05-10",
            minor=True,
        ),
    )
    adult = api_client.post(
        "/api/patients",
        token=tenant.dentist_admin.token,
        json=_patient_payload(
            first_names="Adulto",
            document="CC-SHARED-2",
            mobile=SHARED_MOBILE_PLAIN,
            birth_date="1985-04-20",
        ),
    )
    elder_payload = _patient_payload(
        first_names="Persona Mayor",
        document="CC-SHARED-3",
        mobile="3110000000",
        birth_date="1940-03-15",
    )
    elder = api_client.post(
        "/api/patients",
        token=tenant.dentist_admin.token,
        json=elder_payload,
    )
    assert minor.status_code == adult.status_code == elder.status_code == 201

    elder_payload["mobile"] = "300 123 4567"
    updated = api_client.patch(
        f"/api/patients/{elder.json()['id']}",
        token=tenant.dentist_admin.token,
        json=elder_payload,
    )
    assert updated.status_code == 200, updated.text

    ids = {minor.json()["id"], adult.json()["id"], elder.json()["id"]}
    rows = db_session.scalars(select(Patient).where(Patient.id.in_(ids))).all()
    assert len(rows) == 3
    assert {row.normalized_mobile for row in rows} == {SHARED_MOBILE_PLAIN}
    assert {row.document for row in rows} == {
        "TI-SHARED-1",
        "CC-SHARED-2",
        "CC-SHARED-3",
    }


def test_shared_mobile_remains_tenant_isolated_and_document_identity_still_blocks(
    api_client, db_session, security_world
):
    tenant_a, tenant_b = security_world.tenant_a, security_world.tenant_b
    payload_a = _patient_payload(
        first_names="Paciente Empresa A",
        document="DOC-SAME-PHONE-A",
        mobile=SHARED_MOBILE_PLAIN,
        birth_date="1990-01-02",
    )
    payload_b = _patient_payload(
        first_names="Paciente Empresa B",
        document="DOC-SAME-PHONE-B",
        mobile=SHARED_MOBILE_FORMATTED,
        birth_date="1992-02-03",
    )
    created_a = api_client.post(
        "/api/patients", token=tenant_a.dentist_admin.token, json=payload_a
    )
    created_b = api_client.post(
        "/api/patients", token=tenant_b.dentist_admin.token, json=payload_b
    )
    assert created_a.status_code == created_b.status_code == 201
    assert created_a.json()["id"] != created_b.json()["id"]
    assert db_session.scalar(
        select(Patient.company_id).where(Patient.id == created_a.json()["id"])
    ) == tenant_a.company.id
    assert db_session.scalar(
        select(Patient.company_id).where(Patient.id == created_b.json()["id"])
    ) == tenant_b.company.id

    duplicate_document = dict(payload_a)
    duplicate_document["first_names"] = "Otra Persona"
    duplicate_document["mobile"] = "3229999999"
    blocked = api_client.post(
        "/api/patients",
        token=tenant_a.dentist_admin.token,
        json=duplicate_document,
    )
    assert blocked.status_code == 409
    assert "documento" in blocked.text.casefold()


def test_unrelated_patient_validation_is_unchanged(api_client, security_world):
    tenant = security_world.tenant_a
    future_birth = _patient_payload(
        first_names="Fecha Futura",
        document="DOC-FUTURE",
        mobile=SHARED_MOBILE_PLAIN,
        birth_date="2099-01-01",
    )
    response = api_client.post(
        "/api/patients",
        token=tenant.dentist_admin.token,
        json=future_birth,
    )
    assert response.status_code == 422

    short_mobile = _patient_payload(
        first_names="Celular Corto",
        document="DOC-SHORT",
        mobile="123",
        birth_date="1990-01-01",
    )
    response = api_client.post(
        "/api/patients",
        token=tenant.dentist_admin.token,
        json=short_mobile,
    )
    assert response.status_code == 422
