from fastapi import APIRouter

from app.core.config import settings


router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check() -> dict[str, object]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.app_env,
        "database_configured": settings.database_configured,
    }
