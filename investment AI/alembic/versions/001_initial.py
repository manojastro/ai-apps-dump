"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-09-14
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "households",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "profiles",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("household_id", sa.String(40), sa.ForeignKey("households.id")),
        sa.Column("payload", sa.Text(), nullable=False),
    )
    op.create_table(
        "goals",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("household_id", sa.String(40), sa.ForeignKey("households.id")),
        sa.Column("payload", sa.Text(), nullable=False),
    )
    op.create_table(
        "holdings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("household_id", sa.String(40), sa.ForeignKey("households.id")),
        sa.Column("payload", sa.Text(), nullable=False),
    )
    op.create_table(
        "ips_versions",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("household_id", sa.String(40), sa.ForeignKey("households.id")),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "plan_jobs",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("plan_id", sa.String(40), index=True),
        sa.Column("status", sa.String(20), default="queued"),
        sa.Column("progress_pct", sa.Integer(), default=0),
        sa.Column("message", sa.Text(), default=""),
        sa.Column("events", sa.Text(), default="[]"),
        sa.Column("error", sa.Text(), default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "plans",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("household_id", sa.String(40), default=""),
        sa.Column("version", sa.Integer(), default=1),
        sa.Column("selected", sa.String(20), default=""),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("snapshot_id", sa.String(40), default=""),
        sa.Column("rules_version", sa.String(20), default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "plan_scenarios",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("plan_id", sa.String(40), sa.ForeignKey("plans.id")),
        sa.Column("name", sa.String(20)),
        sa.Column("payload", sa.Text(), nullable=False),
    )
    op.create_table(
        "regulatory_snapshots",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "market_snapshots",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "source_records",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("plan_id", sa.String(40), default=""),
        sa.Column("payload", sa.Text(), nullable=False),
    )
    op.create_table(
        "risk_findings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("plan_id", sa.String(40)),
        sa.Column("payload", sa.Text(), nullable=False),
    )
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("event", sa.String(64), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("plan_id", sa.String(40), default=""),
        sa.Column("component", sa.String(64), default=""),
        sa.Column("metadata", sa.Text(), default="{}"),
    )
    op.create_table(
        "pdf_artifacts",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("plan_id", sa.String(40)),
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    for table in [
        "pdf_artifacts",
        "audit_events",
        "risk_findings",
        "source_records",
        "market_snapshots",
        "regulatory_snapshots",
        "plan_scenarios",
        "plans",
        "plan_jobs",
        "ips_versions",
        "holdings",
        "goals",
        "profiles",
        "households",
    ]:
        op.drop_table(table)
