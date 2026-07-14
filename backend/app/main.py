from fastapi import FastAPI

from app.core.config import settings
from app.core.logging import configure_logging
from app.routers.agenda_router import router as agenda_router
from app.routers.auth_router import router as auth_router
from app.routers.clinical_record_router import (
    evolution_router as clinical_evolution_router,
    router as clinical_record_router,
)
from app.routers.health_router import router as health_router
from app.routers.organization_router import router as organization_router
from app.routers.followup_router import router as followup_router
from app.routers.odontogram_router import (
    odontogram_router,
    router as patient_odontogram_router,
)
from app.routers.patient_router import router as patient_router
from app.routers.platform_router import router as platform_router
from app.routers.report_router import router as report_router
from app.routers.treatment_router import router as treatment_router
from app.routers.user_router import router as user_router


def create_app() -> FastAPI:
    configure_logging()

    app = FastAPI(
        title=settings.app_name,
        debug=settings.app_debug,
    )

    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(user_router)
    app.include_router(organization_router)
    app.include_router(agenda_router)
    app.include_router(patient_router)
    app.include_router(patient_odontogram_router)
    app.include_router(odontogram_router)
    app.include_router(clinical_record_router)
    app.include_router(clinical_evolution_router)
    app.include_router(followup_router)
    app.include_router(platform_router)
    app.include_router(report_router)
    app.include_router(treatment_router)

    return app


app = create_app()
