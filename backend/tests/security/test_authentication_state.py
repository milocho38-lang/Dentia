from __future__ import annotations

from sqlalchemy import select

from app.models.associations import UserRole, UserSite
from app.models.company import Company
from app.models.user import User


def test_missing_token_is_rejected(api_client) -> None:
    response = api_client.get("/api/patients")
    assert response.status_code == 401, response.text


def test_invalid_token_is_rejected(api_client) -> None:
    response = api_client.get("/api/patients", token="not-a-real-token")
    assert response.status_code == 401, response.text


def test_user_inactivated_after_token_is_rejected(api_client, db_session, security_world) -> None:
    user = db_session.scalar(select(User).where(User.id == security_world.tenant_a.secretary.user.id))
    user.is_active = False
    user.status = "Inactivo"
    db_session.commit()
    response = api_client.get("/api/patients", token=security_world.tenant_a.secretary.token)
    assert response.status_code == 401, response.text


def test_company_inactivated_after_token_is_rejected(api_client, db_session, security_world) -> None:
    company = db_session.scalar(select(Company).where(Company.id == security_world.tenant_a.company.id))
    company.status = "Inactiva"
    company.is_active = False
    db_session.commit()
    response = api_client.get("/api/patients", token=security_world.tenant_a.secretary.token)
    assert response.status_code == 401, response.text


def test_role_removed_after_token_removes_permission(api_client, db_session, security_world) -> None:
    db_session.query(UserRole).filter(UserRole.user_id == security_world.tenant_a.secretary.user.id).update({"is_active": False})
    db_session.commit()
    response = api_client.get("/api/patients", token=security_world.tenant_a.secretary.token)
    assert response.status_code == 403, response.text


def test_site_membership_removed_after_token_is_rejected(api_client, db_session, security_world) -> None:
    db_session.query(UserSite).filter(UserSite.user_id == security_world.tenant_a.secretary.user.id).update({"is_active": False})
    db_session.commit()
    response = api_client.get("/api/patients", token=security_world.tenant_a.secretary.token)
    assert response.status_code == 401, response.text
