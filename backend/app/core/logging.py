import logging
import logging.config
import re

from app.core.config import settings


_CONSENT_TOKEN_PATH = re.compile(r"(/(?:api/public/consents|consentimiento)/)[A-Za-z0-9_-]{20,}")


class RedactConsentTokenFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        redacted = _CONSENT_TOKEN_PATH.sub(r"\1[REDACTED]", message)
        if redacted != message:
            record.msg = redacted
            record.args = ()
        return True


def configure_logging() -> None:
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                }
            },
            "filters": {"redact_consent_tokens": {"()": "app.core.logging.RedactConsentTokenFilter"}},
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "filters": ["redact_consent_tokens"],
                }
            },
            "root": {
                "handlers": ["console"],
                "level": settings.log_level,
            },
            "loggers": {
                "uvicorn.access": {"handlers": ["console"], "level": settings.log_level, "propagate": False},
                "httpx": {"handlers": ["console"], "level": settings.log_level, "propagate": False},
            },
        }
    )
