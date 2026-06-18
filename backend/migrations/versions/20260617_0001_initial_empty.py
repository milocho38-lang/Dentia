"""Initial empty database revision.

Revision ID: 20260617_0001
Revises:
Create Date: 2026-06-17

"""


revision: str = "20260617_0001"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Establish the initial migration baseline without business tables."""


def downgrade() -> None:
    """Return to the empty pre-Alembic baseline."""

