from app.core.config import settings


def get_database_url() -> str | None:
    return settings.database_url
