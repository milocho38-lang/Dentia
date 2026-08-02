import logging
import smtplib

import pytest

from app.core.config import settings
from app.services.email_service import EmailDeliveryError, MemoryEmailProvider, SmtpEmailProvider, build_consent_otp_email, get_email_provider


class CapturingSmtp:
    messages = []
    connection = None

    def __init__(self, host, port, timeout):
        type(self).connection = (host, port, timeout)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def starttls(self):
        return None

    def login(self, username, password):
        self.credentials = (username, password)

    def send_message(self, message):
        type(self).messages.append(message)


def _smtp_settings(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "local")
    monkeypatch.setattr(settings, "smtp_host", "127.0.0.1")
    monkeypatch.setattr(settings, "smtp_port", 1025)
    monkeypatch.setattr(settings, "smtp_username", "dentia-local")
    monkeypatch.setattr(settings, "smtp_password", "dentia-local-only")
    monkeypatch.setattr(settings, "smtp_from_email", "no-reply@dentia.local")
    monkeypatch.setattr(settings, "smtp_use_tls", False)
    monkeypatch.setattr(settings, "smtp_timeout_seconds", 5)


def test_smtp_captures_only_generic_otp_message(monkeypatch, caplog):
    _smtp_settings(monkeypatch)
    CapturingSmtp.messages.clear()
    monkeypatch.setattr(smtplib, "SMTP", CapturingSmtp)
    otp = "482619"
    delivery = build_consent_otp_email("patient@dentia.local", otp, 10)
    with caplog.at_level(logging.INFO):
        SmtpEmailProvider().send(delivery)
    assert CapturingSmtp.connection == ("127.0.0.1", 1025, 5)
    assert len(CapturingSmtp.messages) == 1
    message = CapturingSmtp.messages[0]
    body = message.get_content()
    assert message["Subject"] == "Código de seguridad para revisar un consentimiento"
    assert otp in body and otp not in caplog.text
    for forbidden in ("diagnóstico", "procedimiento", "identificación", "documento del paciente", "/consentimiento/"):
        assert forbidden not in body.casefold()


@pytest.mark.parametrize("recipient", ["", "invalid", "two@@dentia.local", "patient @dentia.local", "patient@localhost"])
def test_smtp_rejects_invalid_recipient(monkeypatch, recipient):
    _smtp_settings(monkeypatch)
    with pytest.raises(EmailDeliveryError, match="destinatario"):
        SmtpEmailProvider().send(build_consent_otp_email(recipient, "123456", 10))


def test_smtp_timeout_is_closed_failure(monkeypatch):
    _smtp_settings(monkeypatch)
    class TimeoutSmtp:
        def __init__(self, *_args, **_kwargs):
            raise TimeoutError("local simulated timeout")
    monkeypatch.setattr(smtplib, "SMTP", TimeoutSmtp)
    with pytest.raises(EmailDeliveryError, match="entregar"):
        SmtpEmailProvider().send(build_consent_otp_email("patient@dentia.local", "123456", 10))


def test_production_without_smtp_fails_closed_and_never_uses_memory(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "smtp_host", None)
    monkeypatch.setattr(settings, "smtp_from_email", None)
    provider = get_email_provider()
    assert isinstance(provider, SmtpEmailProvider)
    assert not isinstance(provider, MemoryEmailProvider)
    with pytest.raises(EmailDeliveryError, match="no está configurado"):
        provider.send(build_consent_otp_email("patient@dentia.local", "123456", 10))
