from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import text


PREVIOUS_REVISION = "20261017_0050"
VENEER_REVISION = "20261021_0051"


def _config() -> Config:
    return Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))


def test_existing_veneer_migration_catalog_and_clinical_flow(
    api_client, db_session, security_world
) -> None:
    db_session.close()
    command.downgrade(_config(), PREVIOUS_REVISION)
    command.upgrade(_config(), VENEER_REVISION)

    tenant = security_world.tenant_a
    token = tenant.dentist_admin.token
    catalog_response = api_client.get("/api/odontogram/catalog", token=token)
    assert catalog_response.status_code == 200, catalog_response.text
    veneers = [
        item for item in catalog_response.json() if item["code"] == "FIND_VENEER"
    ]
    assert len(veneers) == 1
    veneer = veneers[0]
    assert veneer["name"] == "Carilla existente"
    assert veneer["type"] == "FINDING"
    assert veneer["allowed_scopes"] == ["TOOTH"]
    assert veneer["allowed_surfaces"] is None

    created = api_client.post(
        f"/api/patients/{tenant.patient.id}/odontogram/events",
        token=token,
        json={
            "event_type": "FINDING_ADDED",
            "status": "CONFIRMED",
            "details": [
                {
                    "catalog_item_id": veneer["id"],
                    "scope_type": "TOOTH",
                    "tooth_code": "11",
                    "dentition": "PERMANENT",
                    "layer": "FINDING",
                }
            ],
        },
    )
    assert created.status_code == 201, created.text
    detail = created.json()["details"][0]
    assert detail["catalog_code"] == "FIND_VENEER"
    assert detail["catalog_name"] == "Carilla existente"
    assert detail["scope_type"] == "TOOTH"
    assert detail["surfaces"] is None

    current = api_client.get(
        f"/api/patients/{tenant.patient.id}/odontogram/current", token=token
    )
    assert current.status_code == 200, current.text
    tooth = next(item for item in current.json()["teeth"] if item["tooth_code"] == "11")
    assert tooth["layers"]["FINDING"][0]["catalog_code"] == "FIND_VENEER"

    history = api_client.get(
        f"/api/patients/{tenant.patient.id}/odontogram/teeth/11/history",
        token=token,
    )
    assert history.status_code == 200, history.text
    assert history.json()["items"][0]["details"][0]["catalog_code"] == "FIND_VENEER"

    command.downgrade(_config(), PREVIOUS_REVISION)
    with db_session.get_bind().connect() as connection:
        assert connection.execute(
            text("SELECT count(*) FROM odontograma_catalogo WHERE id = :id"),
            {"id": veneer["id"]},
        ).scalar_one() == 1
        assert connection.execute(
            text(
                "SELECT count(*) FROM odontograma_evento_detalles "
                "WHERE catalog_item_id = :id"
            ),
            {"id": veneer["id"]},
        ).scalar_one() == 1
    command.upgrade(_config(), "head")


def test_existing_global_veneer_catalog_is_not_overwritten_or_deleted(
    db_session,
) -> None:
    db_session.close()
    command.downgrade(_config(), PREVIOUS_REVISION)
    engine = db_session.get_bind()
    with engine.begin() as connection:
        connection.execute(
            text("DELETE FROM odontograma_catalogo WHERE empresa_id IS NULL AND codigo = 'FIND_VENEER'")
        )
        connection.execute(
            text(
                """
                INSERT INTO odontograma_catalogo (
                    id, empresa_id, codigo, nombre, tipo, categoria, descripcion,
                    color, pattern, symbol, allowed_scopes, allowed_surfaces,
                    is_active, created_at, updated_at
                ) VALUES (
                    gen_random_uuid(), NULL, 'FIND_VENEER', 'Carilla preexistente',
                    'FINDING', 'Hallazgo local', 'Configuración preexistente',
                    '#123456', 'outline', 'VP', '["TOOTH"]'::jsonb, NULL,
                    false, now(), now()
                )
                """
            )
        )

    command.upgrade(_config(), VENEER_REVISION)
    command.downgrade(_config(), PREVIOUS_REVISION)
    with engine.connect() as connection:
        preserved = connection.execute(
            text(
                "SELECT nombre, categoria, descripcion, color, pattern, symbol, is_active "
                "FROM odontograma_catalogo "
                "WHERE empresa_id IS NULL AND codigo = 'FIND_VENEER'"
            )
        ).one()
    assert tuple(preserved) == (
        "Carilla preexistente",
        "Hallazgo local",
        "Configuración preexistente",
        "#123456",
        "outline",
        "VP",
        False,
    )
    command.upgrade(_config(), "head")
