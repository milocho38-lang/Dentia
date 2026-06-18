from fastapi import FastAPI

from app.core.config import settings
from app.core.logging import configure_logging
from app.routers.auth_router import router as auth_router
from app.routers.health_router import router as health_router


def create_app() -> FastAPI:
    configure_logging()

    app = FastAPI(
        title=settings.app_name,
        debug=settings.app_debug,
    )

    app.include_router(health_router)
    app.include_router(auth_router)

    return app


app = create_app()
