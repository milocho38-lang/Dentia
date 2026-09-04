from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

from sqlalchemy import select

from app.core.config import settings
from app.core.security import (
    create_refresh_token,
    hash_refresh_token,
    parse_refresh_token,
    utc_now,
)
from app.models.audit_event import AuditEvent
from app.models.auth_session import AuthSession


TEST_PASSWORD = "DentiaTestPassword123!"


def _login(api_client, security_world):
    response = api_client.post(
        "/api/auth/login",
        json={
            "email": security_world.tenant_a.admin.user.email,
            "password": TEST_PASSWORD,
        },
    )
    assert response.status_code == 200, response.text
    refresh_token = response.cookies.get(settings.refresh_cookie_name)
    assert refresh_token
    return response, refresh_token


def _refresh(api_client, refresh_token: str):
    return api_client.post(
        "/api/auth/refresh",
        headers={
            "Cookie": f"{settings.refresh_cookie_name}={refresh_token}",
        },
    )


def _session(db_session, refresh_token: str) -> AuthSession:
    session_id = parse_refresh_token(refresh_token).session_id
    db_session.expire_all()
    auth_session = db_session.get(AuthSession, session_id)
    assert auth_session is not None
    return auth_session


def _response_refresh_token(response) -> str:
    token = response.cookies.get(settings.refresh_cookie_name)
    assert token
    return token


def test_refresh_token_generation_is_signed_and_tamper_evident() -> None:
    from uuid import uuid4

    session_id = uuid4()
    token = create_refresh_token(session_id, generation=7)
    claims = parse_refresh_token(token)
    assert claims.session_id == session_id
    assert claims.generation == 7
    assert claims.is_legacy is False

    replacement = "0" if token[-1] != "0" else "1"
    tampered = f"{token[:-1]}{replacement}"
    try:
        parse_refresh_token(tampered)
    except ValueError:
        pass
    else:
        raise AssertionError("A tampered refresh token must be rejected.")


def test_normal_refresh_rotates_generation_and_preserves_absolute_expiry(
    api_client,
    db_session,
    security_world,
) -> None:
    login_response, token_0 = _login(api_client, security_world)
    claims_0 = parse_refresh_token(token_0)
    assert claims_0.generation == 0
    set_cookie = login_response.headers["set-cookie"].casefold()
    assert "max-age=28800" in set_cookie
    assert "httponly" in set_cookie
    assert "samesite=lax" in set_cookie
    assert "path=/api/auth" in set_cookie
    assert "domain=" not in set_cookie
    original_expiry = _session(db_session, token_0).expires_at

    response = _refresh(api_client, token_0)
    assert response.status_code == 200, response.text
    token_1 = _response_refresh_token(response)
    claims_1 = parse_refresh_token(token_1)
    assert claims_1.session_id == claims_0.session_id
    assert claims_1.generation == 1
    assert _session(db_session, token_1).expires_at == original_expiry


def test_two_concurrent_refreshes_keep_session_active(
    api_client,
    db_session,
    security_world,
) -> None:
    _, token_0 = _login(api_client, security_world)
    barrier = Barrier(2)

    def request_refresh():
        barrier.wait(timeout=5)
        return _refresh(api_client, token_0)

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(lambda _: request_refresh(), range(2)))

    assert sorted(response.status_code for response in responses) == [200, 409]
    success = next(response for response in responses if response.status_code == 200)
    race = next(response for response in responses if response.status_code == 409)
    assert race.json()["detail"]["code"] == "REFRESH_RACE_RETRY"
    assert settings.refresh_cookie_name not in race.headers.get("set-cookie", "")

    current_token = _response_refresh_token(success)
    auth_session = _session(db_session, current_token)
    assert auth_session.is_active is True
    assert auth_session.revoked_at is None
    assert auth_session.rotation_counter == 1

    race_audits = list(
        db_session.scalars(
            select(AuditEvent).where(
                AuditEvent.session_id == auth_session.id,
                AuditEvent.action == "TOKEN_REFRESH_RACE_ACCEPTED",
            )
        )
    )
    assert len(race_audits) == 1
    assert race_audits[0].detail["generation"] == 0

    follow_up = _refresh(api_client, current_token)
    assert follow_up.status_code == 200, follow_up.text
    assert _session(db_session, _response_refresh_token(follow_up)).is_active


def test_immediate_previous_token_returns_retry_without_revocation(
    api_client,
    db_session,
    security_world,
) -> None:
    _, token_0 = _login(api_client, security_world)
    current_response = _refresh(api_client, token_0)
    assert current_response.status_code == 200
    token_1 = _response_refresh_token(current_response)

    race_response = _refresh(api_client, token_0)
    assert race_response.status_code == 409
    assert race_response.json()["detail"]["code"] == "REFRESH_RACE_RETRY"
    auth_session = _session(db_session, token_1)
    assert auth_session.is_active is True
    assert auth_session.revoked_at is None


def test_previous_token_after_grace_is_replay_and_revokes_session(
    api_client,
    db_session,
    security_world,
) -> None:
    _, token_0 = _login(api_client, security_world)
    current_response = _refresh(api_client, token_0)
    token_1 = _response_refresh_token(current_response)
    auth_session = _session(db_session, token_1)
    auth_session.last_seen_at = utc_now() - timedelta(
        seconds=settings.refresh_token_race_grace_seconds + 1
    )
    db_session.commit()

    replay = _refresh(api_client, token_0)
    assert replay.status_code == 401
    auth_session = _session(db_session, token_1)
    assert auth_session.is_active is False
    assert auth_session.revoke_reason == "REFRESH_TOKEN_REUSE"


def test_generation_n_minus_two_is_immediate_replay(
    api_client,
    db_session,
    security_world,
) -> None:
    _, token_0 = _login(api_client, security_world)
    response_1 = _refresh(api_client, token_0)
    token_1 = _response_refresh_token(response_1)
    response_2 = _refresh(api_client, token_1)
    token_2 = _response_refresh_token(response_2)

    replay = _refresh(api_client, token_0)
    assert replay.status_code == 401
    auth_session = _session(db_session, token_2)
    assert auth_session.is_active is False
    assert auth_session.revoke_reason == "REFRESH_TOKEN_REUSE"


def test_logout_invalidates_current_and_previous_tokens(
    api_client,
    db_session,
    security_world,
) -> None:
    _, token_0 = _login(api_client, security_world)
    response = _refresh(api_client, token_0)
    token_1 = _response_refresh_token(response)
    access_token = response.json()["access_token"]

    logout = api_client.post(
        "/api/auth/logout",
        token=access_token,
        headers={
            "Cookie": f"{settings.refresh_cookie_name}={token_1}",
        },
    )
    assert logout.status_code == 200, logout.text
    assert _refresh(api_client, token_1).status_code == 401
    assert _refresh(api_client, token_0).status_code == 401
    auth_session = _session(db_session, token_1)
    assert auth_session.is_active is False
    assert auth_session.revoke_reason == "LOGOUT"


def test_grace_does_not_revive_idle_or_absolutely_expired_session(
    api_client,
    db_session,
    security_world,
) -> None:
    _, idle_token_0 = _login(api_client, security_world)
    idle_response = _refresh(api_client, idle_token_0)
    idle_token_1 = _response_refresh_token(idle_response)
    idle_session = _session(db_session, idle_token_1)
    idle_session.last_seen_at = utc_now() - timedelta(
        minutes=settings.session_idle_timeout_minutes + 1
    )
    db_session.commit()
    assert _refresh(api_client, idle_token_0).status_code == 401
    assert _session(db_session, idle_token_1).revoke_reason == "SESSION_EXPIRED"

    _, expired_token_0 = _login(api_client, security_world)
    expired_response = _refresh(api_client, expired_token_0)
    expired_token_1 = _response_refresh_token(expired_response)
    expired_session = _session(db_session, expired_token_1)
    expired_session.expires_at = utc_now() - timedelta(seconds=1)
    db_session.commit()
    assert _refresh(api_client, expired_token_0).status_code == 401
    assert _session(db_session, expired_token_1).revoke_reason == "SESSION_EXPIRED"


def test_session_remains_valid_after_seventy_five_seconds_of_inactivity(
    api_client,
    db_session,
    security_world,
) -> None:
    _, token_0 = _login(api_client, security_world)
    response_1 = _refresh(api_client, token_0)
    assert response_1.status_code == 200, response_1.text
    token_1 = _response_refresh_token(response_1)
    auth_session = _session(db_session, token_1)
    auth_session.last_seen_at = utc_now() - timedelta(seconds=75)
    db_session.commit()

    response_2 = _refresh(api_client, token_1)
    assert response_2.status_code == 200, response_2.text
    token_2 = _response_refresh_token(response_2)
    auth_session = _session(db_session, token_2)
    assert auth_session.is_active is True
    assert auth_session.revoked_at is None
    assert auth_session.rotation_counter == 2


def test_invalid_signature_does_not_revoke_valid_session(
    api_client,
    db_session,
    security_world,
) -> None:
    _, token = _login(api_client, security_world)
    replacement = "0" if token[-1] != "0" else "1"
    tampered = f"{token[:-1]}{replacement}"
    assert _refresh(api_client, tampered).status_code == 401
    assert _session(db_session, token).is_active is True
    assert _refresh(api_client, token).status_code == 200


def test_legacy_session_is_revoked_once_for_safe_format_upgrade(
    api_client,
    db_session,
    security_world,
) -> None:
    _, signed_token = _login(api_client, security_world)
    auth_session = _session(db_session, signed_token)
    legacy_token = f"{auth_session.id}.legacy-refresh-value"
    auth_session.refresh_token_hash = hash_refresh_token(legacy_token)
    db_session.commit()

    response = _refresh(api_client, legacy_token)
    assert response.status_code == 401
    auth_session = _session(db_session, signed_token)
    assert auth_session.is_active is False
    assert auth_session.revoke_reason == "REFRESH_TOKEN_FORMAT_UPGRADE"


def test_password_change_skips_race_grace_for_prior_cookie(
    api_client,
    db_session,
    security_world,
) -> None:
    login_response, token_0 = _login(api_client, security_world)
    access_token = login_response.json()["access_token"]
    changed = api_client.post(
        "/api/auth/change-password",
        token=access_token,
        json={
            "current_password": TEST_PASSWORD,
            "new_password": "DentiaChangedPassword456!",
            "confirm_password": "DentiaChangedPassword456!",
        },
    )
    assert changed.status_code == 200, changed.text
    token_2 = _response_refresh_token(changed)
    assert parse_refresh_token(token_2).generation == 2

    replay = _refresh(api_client, token_0)
    assert replay.status_code == 401
    auth_session = _session(db_session, token_2)
    assert auth_session.is_active is False
    assert auth_session.revoke_reason == "REFRESH_TOKEN_REUSE"
