from uuid import UUID

from sqlalchemy import select

from app.models.user import User
from app.services.bootstrap_service import BootstrapInput, bootstrap_installation


def test_bootstrap_persists_explicit_normalized_admin_username(db_session) -> None:
    result = bootstrap_installation(
        db_session,
        BootstrapInput(
            company_name="Clínica Bootstrap",
            company_slug="clinica-bootstrap",
            site_name="Sede Principal",
            admin_name="Administradora Bootstrap",
            admin_username="  Admin.Bootstrap  ",
            admin_email="admin-bootstrap@example.test",
            admin_password="DentiaBootstrapPassword2026!",
        ),
    )

    admin = db_session.get(User, UUID(result.admin_user_id))
    assert admin is not None
    assert admin.username == "Admin.Bootstrap"
    assert admin.normalized_username == "admin.bootstrap"
    assert admin.company_id is not None
    assert admin.default_site_id is not None


def test_platform_company_allows_existing_contact_email_with_new_global_username(
    api_client, db_session, security_world
) -> None:
    shared_email = security_world.tenant_a.admin.user.email
    response = api_client.post(
        "/api/platform/companies",
        token=security_world.platform_admin.token,
        json={
            "company_name": "Clínica Username Plataforma",
            "company_type": "Clínica",
            "tax_id": "USERNAME-PLATFORM-2026",
            "phone": None,
            "email": "contacto-plataforma@example.test",
            "address": "Calle 123",
            "city": "Bogotá",
            "country": "Colombia",
            "timezone": "America/Bogota",
            "admin_name": "Administradora Plataforma",
            "admin_username": "admin.plataforma.nueva",
            "admin_email": shared_email,
            "admin_password": "DentiaPlatformPassword2026!",
        },
    )

    assert response.status_code == 201, response.text
    admin_id = response.json()["admin_user"]["id"]
    admin = db_session.get(User, UUID(admin_id))
    assert admin is not None
    assert admin.username == "admin.plataforma.nueva"
    assert admin.normalized_username == "admin.plataforma.nueva"
    assert admin.normalized_email == security_world.tenant_a.admin.user.normalized_email
    same_email_users = list(
        db_session.scalars(
            select(User).where(User.normalized_email == admin.normalized_email)
        )
    )
    assert len(same_email_users) == 2
    assert len({item.company_id for item in same_email_users}) == 2
