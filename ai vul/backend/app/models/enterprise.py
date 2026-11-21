"""Enterprise inventory synchronised from the CMDB (ServiceNow or its simulator)."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, JSONType
from app.core.types import UTCDateTime, new_id, utcnow

if TYPE_CHECKING:
    from app.models.vulnerability import Finding


class BusinessService(Base):
    __tablename__ = "business_services"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    division: Mapped[str] = mapped_column(String(100))
    criticality: Mapped[str] = mapped_column(String(16))
    owner_team: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cmdb_sys_id: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)

    assets: Mapped[list[Asset]] = relationship(back_populates="business_service")


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)  # e.g. ASSET-1024
    hostname: Mapped[str] = mapped_column(String(255), index=True)
    fqdn: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    asset_type: Mapped[str] = mapped_column(String(32))  # server, workstation, vm, container
    operating_system: Mapped[str | None] = mapped_column(String(128), nullable=True)
    os_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    environment: Mapped[str | None] = mapped_column(String(16), index=True, nullable=True)
    business_criticality: Mapped[str | None] = mapped_column(String(16), index=True, nullable=True)
    business_service_id: Mapped[str | None] = mapped_column(
        ForeignKey("business_services.id", ondelete="SET NULL"), index=True, nullable=True
    )
    owner: Mapped[str | None] = mapped_column(String(255), nullable=True)
    support_group: Mapped[str | None] = mapped_column(String(255), nullable=True)
    internet_exposed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)  # None = unknown
    cloud_provider: Mapped[str | None] = mapped_column(String(32), nullable=True)
    location: Mapped[str | None] = mapped_column(String(128), nullable=True)
    operational_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    cmdb_sys_id: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    defender_device_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    tags: Mapped[list[Any]] = mapped_column(JSONType, default=list)
    last_sync_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)

    business_service: Mapped[BusinessService | None] = relationship(back_populates="assets")
    findings: Mapped[list[Finding]] = relationship(back_populates="asset")


class AssetDependency(Base):
    """Directed dependency: ``source`` depends on ``target`` (mirrors cmdb_rel_ci)."""

    __tablename__ = "asset_dependencies"
    __table_args__ = (UniqueConstraint("source_asset_id", "target_asset_id", "dependency_type"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    source_asset_id: Mapped[str] = mapped_column(ForeignKey("assets.id", ondelete="CASCADE"), index=True)
    target_asset_id: Mapped[str] = mapped_column(ForeignKey("assets.id", ondelete="CASCADE"), index=True)
    dependency_type: Mapped[str] = mapped_column(String(64), default="Depends on::Used by")
    cmdb_rel_sys_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
