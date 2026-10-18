from sqlalchemy import select

from app.models.associations import RolePermission, UserRole
from app.models.permission import Permission
from app.models.role import Role
from app.services.bootstrap_service import BootstrapInput, bootstrap_installation


def test_post_0050_bootstrap_preserves_clinical_role_boundaries(db_session) -> None:
    result = bootstrap_installation(
        db_session,
        BootstrapInput(
            company_name="Clínica sintética posterior a 0050",
            company_slug="clinica-post-0050",
            site_name="Sede sintética",
            admin_name="Administradora sintética",
            admin_username="admin.post0050",
            admin_email="admin-post0050@example.test",
            admin_password="SyntheticPassword!42",
        ),
    )
    db_session.commit()

    rows = db_session.execute(
        select(Role.code, Permission.code)
        .join(RolePermission, RolePermission.role_id == Role.id)
        .join(Permission, Permission.id == RolePermission.permission_id)
        .where(
            Role.company_id == result.company_id,
            RolePermission.is_active.is_(True),
            Permission.code.like("clinical_files.%"),
        )
    ).all()
    permissions_by_role: dict[str, set[str]] = {}
    for role_code, permission_code in rows:
        permissions_by_role.setdefault(role_code, set()).add(permission_code)

    assert permissions_by_role.get("DENTIST") == {
        "clinical_files.create",
        "clinical_files.view",
    }
    assert permissions_by_role.get("DENTIST_ADMIN") == {
        "clinical_files.create",
        "clinical_files.manage",
        "clinical_files.view",
    }
    assert permissions_by_role.get("ADMINISTRATOR", set()) == set()

    admin_roles = set(
        db_session.scalars(
            select(Role.code)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == result.admin_user_id, UserRole.is_active.is_(True))
        )
    )
    assert {"ADMINISTRATOR", "DENTIST_ADMIN"}.issubset(admin_roles)
