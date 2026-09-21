from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


DEMO_REQUEST_STATUSES = (
    "NEW",
    "CONTACTED",
    "DEMO_SCHEDULED",
    "DEMO_COMPLETED",
    "CONVERTED",
    "NOT_CONTINUING",
)
DEMO_PRACTICE_TYPES = (
    "INDEPENDENT_DENTIST",
    "DENTAL_OFFICE",
    "DENTAL_CLINIC",
)


class DemoRequest(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "demo_requests"
    __table_args__ = (
        CheckConstraint(
            f"status IN {DEMO_REQUEST_STATUSES}",
            name="demo_request_status",
        ),
        CheckConstraint(
            f"practice_type IN {DEMO_PRACTICE_TYPES}",
            name="demo_request_practice_type",
        ),
        CheckConstraint(
            "source = 'WEBSITE'",
            name="demo_request_source",
        ),
        CheckConstraint(
            "notification_status IN ('PENDING', 'SENT', 'FAILED', 'NOT_CONFIGURED')",
            name="demo_request_notification_status",
        ),
        CheckConstraint(
            "dentist_count >= 1",
            name="demo_request_dentist_count_positive",
        ),
        CheckConstraint(
            "row_version >= 1",
            name="demo_request_row_version_positive",
        ),
        Index("ix_demo_requests_created_at", "created_at"),
        Index("ix_demo_requests_status_created", "status", "created_at"),
        Index("ix_demo_requests_country_created", "country", "created_at"),
        Index("ix_demo_requests_assigned_created", "assigned_to_user_id", "created_at"),
        Index("ix_demo_requests_submission_fingerprint", "submission_fingerprint"),
    )

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    normalized_email: Mapped[str] = mapped_column(String(320), nullable=False)
    phone: Mapped[str] = mapped_column(String(50), nullable=False)
    country: Mapped[str] = mapped_column(String(80), nullable=False)
    city: Mapped[str] = mapped_column(String(120), nullable=False)
    practice_type: Mapped[str] = mapped_column(String(40), nullable=False)
    dentist_count: Mapped[int] = mapped_column(Integer, nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(
        String(40), nullable=False, default="WEBSITE", server_default="WEBSITE"
    )
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="NEW", server_default="NEW"
    )
    assigned_to_user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )
    scheduled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    timezone: Mapped[str | None] = mapped_column(String(80), nullable=True)
    meeting_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    contacted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    converted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    consent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    consent_version: Mapped[str] = mapped_column(String(80), nullable=False)
    row_version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default="1"
    )
    submission_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    notification_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="PENDING", server_default="PENDING"
    )
    notification_attempted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    notification_error_code: Mapped[str | None] = mapped_column(
        String(80), nullable=True
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class DemoRequestNote(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "demo_request_notes"
    __table_args__ = (
        Index("ix_demo_request_notes_request_created", "demo_request_id", "created_at"),
    )

    demo_request_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("demo_requests.id", ondelete="RESTRICT"),
        nullable=False,
    )
    author_user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
