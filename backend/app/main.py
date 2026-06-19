from fastapi import FastAPI

from app.core.config import settings
from app.core.logging import configure_logging
from app.routers.agenda_router import router as agenda_router
from app.routers.auth_router import router as auth_router
from app.routers.health_router import router as health_router
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
    app.include_router(agenda_router)

    return app


app = create_app()
