import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

from app.core.config import settings


PASSWORD_HASH = PasswordHash.recommended()
DUMMY_PASSWORD_HASH = PASSWORD_HASH.hash("Dentia dummy password 2026")


class AccessTokenError(ValueError):
    pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def normalize_email(email: str) -> str:
    return email.strip().casefold()


def hash_password(password: str) -> str:
    return PASSWORD_HASH.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return PASSWORD_HASH.verify(password, password_hash)
    except Exception:
        return False


def verify_dummy_password(password: str) -> None:
    verify_password(password, DUMMY_PASSWORD_HASH)


def email_fingerprint(normalized_email: str) -> str:
    return hmac.new(
        settings.jwt_secret.encode("utf-8"),
        normalized_email.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_refresh_token(session_id: UUID) -> str:
    secret = secrets.token_urlsafe(48)
    return f"{session_id}.{secret}"


def get_refresh_session_id(token: str) -> UUID:
    session_id, separator, secret = token.partition(".")
    if not separator or not secret:
        raise ValueError("Invalid refresh token.")
    return UUID(session_id)


def refresh_token_matches(token: str, stored_hash: str) -> bool:
    return hmac.compare_digest(hash_refresh_token(token), stored_hash)


def create_access_token(
    *,
    user_id: UUID,
    session_id: UUID,
    company_id: UUID,
    site_id: UUID | None,
    roles: list[str],
    auth_version: int,
) -> tuple[str, datetime]:
    issued_at = utc_now()
    expires_at = issued_at + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {
        "sub": str(user_id),
        "sid": str(session_id),
        "empresa_id": str(company_id),
        "sede_id": str(site_id) if site_id else None,
        "roles": roles,
        "ver": auth_version,
        "type": "access",
        "jti": str(uuid4()),
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": issued_at,
        "nbf": issued_at,
        "exp": expires_at,
    }
    token = jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    return token, expires_at


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
            options={
                "require": [
                    "sub",
                    "sid",
                    "empresa_id",
                    "type",
                    "jti",
                    "iat",
                    "nbf",
                    "exp",
                ]
            },
        )
    except InvalidTokenError as exc:
        raise AccessTokenError("Invalid access token.") from exc

    if payload.get("type") != "access":
        raise AccessTokenError("Invalid token type.")
    return payload
