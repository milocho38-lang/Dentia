from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text


IMPORT_REVISION = "20261006_0047"
USERNAME_REVISION = "20261006_0046"


def _config() -> Config:
    return Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))


def test_import_migration_assigns_permission_only_to_clinic_admin_roles(
    db_session, security_world
) -> None:
    db_session.close()
    config = _config()
    command.downgrade(config, USERNAME_REVISION)
    command.upgrade(config, IMPORT_REVISION)

    engine = db_session.get_bind()
    with engine.connect() as connection:
        assigned = set(
            connection.execute(
                text(
                    """
                    SELECT DISTINCT r.code
                    FROM rol_permisos rp
                    JOIN roles r ON r.id = rp.rol_id
                    JOIN permisos p ON p.id = rp.permiso_id
                    WHERE p.code = 'patients.import' AND rp.is_active = true
                    """
                )
            ).scalars()
        )
        version = connection.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar_one()
        table_exists = connection.execute(
            text("SELECT to_regclass('public.patient_external_references')")
        ).scalar_one()
    assert assigned == {"ADMINISTRATOR", "DENTIST_ADMIN"}
    assert version == IMPORT_REVISION
    assert table_exists == "patient_external_references"


def test_import_migration_downgrade_fails_closed_before_any_mutation(
    db_session, security_world
) -> None:
    company_id = security_world.tenant_a.company.id
    patient_id = security_world.tenant_a.patient.id
    user_id = security_world.tenant_a.admin.user.id
    source_id = uuid4()
    reference_id = uuid4()
    db_session.execute(
        text(
            """
            INSERT INTO patient_import_sources (
                id, company_id, source_system, code, label, created_by, is_active
            ) VALUES (
                :id, :company_id, 'DENTALINK', 'dl-failclosed',
                'Origen fail closed', :user_id, true
            )
            """
        ),
        {"id": source_id, "company_id": company_id, "user_id": user_id},
    )
    db_session.execute(
        text(
            """
            INSERT INTO patient_external_references (
                id, company_id, source_id, patient_id, source_patient_id,
                source_file_sha256, imported_by
            ) VALUES (
                :id, :company_id, :source_id, :patient_id, 'origin-1',
                :file_hash, :user_id
            )
            """
        ),
        {
            "id": reference_id,
            "company_id": company_id,
            "source_id": source_id,
            "patient_id": patient_id,
            "file_hash": "a" * 64,
            "user_id": user_id,
        },
    )
    db_session.commit()
    permission_links_before = db_session.execute(
        text(
            """
            SELECT count(*) FROM rol_permisos rp
            JOIN permisos p ON p.id = rp.permiso_id
            WHERE p.code = 'patients.import'
            """
        )
    ).scalar_one()
    db_session.close()

    with pytest.raises(RuntimeError, match="Downgrade bloqueado"):
        command.downgrade(_config(), USERNAME_REVISION)

    engine = db_session.get_bind()
    with engine.connect() as connection:
        assert connection.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar_one() == IMPORT_REVISION
        assert connection.execute(
            text("SELECT count(*) FROM patient_external_references WHERE id = :id"),
            {"id": reference_id},
        ).scalar_one() == 1
        assert connection.execute(
            text("SELECT count(*) FROM patient_import_sources WHERE id = :id"),
            {"id": source_id},
        ).scalar_one() == 1
        assert connection.execute(
            text("SELECT count(*) FROM pacientes WHERE id = :id"),
            {"id": patient_id},
        ).scalar_one() == 1
        assert connection.execute(
            text(
                """
                SELECT count(*) FROM rol_permisos rp
                JOIN permisos p ON p.id = rp.permiso_id
                WHERE p.code = 'patients.import'
                """
            )
        ).scalar_one() == permission_links_before
