from dataclasses import dataclass
import smtplib
from email.message import EmailMessage

from app.core.config import settings


@dataclass(frozen=True)
class EmailDelivery:
    recipient: str
    subject: str
    body: str


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


def _valid_recipient(recipient: str) -> bool:
    if recipient.count("@") != 1 or any(character.isspace() for character in recipient):
        return False
    local, domain = recipient.rsplit("@", 1)
    return bool(local and domain and "." in domain and not domain.startswith(".") and not domain.endswith("."))


def get_email_provider() -> EmailProvider:
    return _test_provider if settings.app_env == "test" else SmtpEmailProvider()


def get_test_email_outbox() -> list[EmailDelivery]:
    if settings.app_env != "test":
        raise RuntimeError("El buzón interno solo está disponible en pruebas.")
    return _test_provider.outbox
