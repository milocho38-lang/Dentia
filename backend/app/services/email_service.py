from dataclasses import dataclass
from contextlib import contextmanager
from contextvars import ContextVar
import hashlib
import re
import smtplib
from email.message import EmailMessage
from typing import Iterator
from uuid import UUID

from app.core.config import settings


@dataclass(frozen=True)
class EmailDelivery:
    recipient: str
    subject: str
    body: str
    attachments: tuple[tuple[str, str, bytes], ...] = ()


class EmailDeliveryError(RuntimeError):
    pass


class EmailProvider:
    def send(self, delivery: EmailDelivery) -> None:
        raise NotImplementedError


def build_consent_otp_email(recipient: str, otp: str, expires_in_minutes: int) -> EmailDelivery:
    return EmailDelivery(
        recipient=recipient,
        subject="Código de seguridad para revisar un consentimiento",
        body=(
            f"Su código de seguridad es: {otp}\n"
            f"Vence en {expires_in_minutes} minutos. No lo comparta. "
            "Dentia nunca solicitará contraseñas ni información bancaria."
        ),
    )


class MemoryEmailProvider(EmailProvider):
    def __init__(self) -> None:
        self.outbox: list[EmailDelivery] = []

    def send(self, delivery: EmailDelivery) -> None:
        self.outbox.append(delivery)


@dataclass(frozen=True)
class DemoEmailRecord:
    """Non-sensitive evidence retained by the demo-only mail sink."""

    recipient_masked: str
    subject: str
    body_redacted: str
    attachment_names: tuple[str, ...]
    attachment_sha256: tuple[str, ...]


class DemoEmailSink(EmailProvider):
    """Fail-closed provider used only inside an explicitly scoped demo command.

    OTP values remain in memory long enough for the orchestrator to exercise the
    real consent flow. They are never included in records, logs or exceptions.
    """

    _otp_pattern = re.compile(r"(?<!\d)(\d{6})(?!\d)")
    _token_pattern = re.compile(r"(/consentimiento/)[A-Za-z0-9_-]+")

    def __init__(self, allowed_recipient: str) -> None:
        normalized = allowed_recipient.strip().casefold()
        if not _valid_recipient(normalized):
            raise ValueError("El destinatario interno del demo no es válido.")
        self._allowed_recipient = normalized
        self._otp_values: list[str] = []
        self.records: list[DemoEmailRecord] = []

    def send(self, delivery: EmailDelivery) -> None:
        recipient = delivery.recipient.strip().casefold()
        if recipient != self._allowed_recipient:
            raise EmailDeliveryError(
                "DemoEmailSink rechazó un destinatario fuera de la allowlist."
            )
        otp_matches = self._otp_pattern.findall(delivery.body)
        self._otp_values.extend(otp_matches)
        redacted = self._otp_pattern.sub("[CODIGO REDACTADO]", delivery.body)
        redacted = self._token_pattern.sub(r"\1[TOKEN REDACTADO]", redacted)
        self.records.append(
            DemoEmailRecord(
                recipient_masked=mask_email(recipient),
                subject=delivery.subject,
                body_redacted=redacted,
                attachment_names=tuple(item[0] for item in delivery.attachments),
                attachment_sha256=tuple(
                    hashlib.sha256(item[2]).hexdigest() for item in delivery.attachments
                ),
            )
        )

    def consume_latest_otp(self) -> str:
        if not self._otp_values:
            raise RuntimeError("DemoEmailSink no tiene un OTP pendiente.")
        return self._otp_values.pop()


def mask_email(value: str) -> str:
    local, domain = value.rsplit("@", 1)
    visible = local[:1] if local else "*"
    return f"{visible}***@{domain}"


class SmtpEmailProvider(EmailProvider):
    def send(self, delivery: EmailDelivery) -> None:
        if not settings.smtp_host or not settings.smtp_from_email:
            raise EmailDeliveryError("El proveedor de correo no está configurado.")
        if not _valid_recipient(delivery.recipient):
            raise EmailDeliveryError("El destinatario de correo no es válido.")
        message = EmailMessage()
        message["From"] = settings.smtp_from_email
        message["To"] = delivery.recipient
        message["Subject"] = delivery.subject
        message.set_content(delivery.body)
        for filename, mime_type, content in delivery.attachments:
            maintype, subtype = mime_type.split("/", 1)
            message.add_attachment(content, maintype=maintype, subtype=subtype, filename=filename)
        try:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=settings.smtp_timeout_seconds) as client:
                if settings.smtp_use_tls:
                    client.starttls()
                if settings.smtp_username:
                    client.login(settings.smtp_username, settings.smtp_password or "")
                client.send_message(message)
        except Exception as exc:
            raise EmailDeliveryError("No fue posible entregar el correo de seguridad.") from exc


_test_provider = MemoryEmailProvider()
_company_provider: ContextVar[tuple[UUID, EmailProvider] | None] = ContextVar(
    "dentia_company_email_provider",
    default=None,
)
_email_company_id: ContextVar[UUID | None] = ContextVar(
    "dentia_email_company_id",
    default=None,
)


def _valid_recipient(recipient: str) -> bool:
    if recipient.count("@") != 1 or any(character.isspace() for character in recipient):
        return False
    local, domain = recipient.rsplit("@", 1)
    return bool(local and domain and "." in domain and not domain.startswith(".") and not domain.endswith("."))


@contextmanager
def use_company_email_provider(
    company_id: UUID,
    provider: EmailProvider,
) -> Iterator[None]:
    """Temporarily override delivery for exactly one company in this context."""

    token = _company_provider.set((company_id, provider))
    try:
        yield
    finally:
        _company_provider.reset(token)


@contextmanager
def use_email_company(company_id: UUID) -> Iterator[None]:
    """Bind a delivery call to its tenant without changing the provider API."""

    token = _email_company_id.set(company_id)
    try:
        yield
    finally:
        _email_company_id.reset(token)


def get_email_provider(company_id: UUID | None = None) -> EmailProvider:
    override = _company_provider.get()
    effective_company_id = company_id or _email_company_id.get()
    if override is not None and effective_company_id == override[0]:
        return override[1]
    return _test_provider if settings.app_env == "test" else SmtpEmailProvider()


def get_test_email_outbox() -> list[EmailDelivery]:
    if settings.app_env != "test":
        raise RuntimeError("El buzón interno solo está disponible en pruebas.")
    return _test_provider.outbox
