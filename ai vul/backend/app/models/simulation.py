"""State of the simulated Microsoft Defender for Endpoint tenant.

Devices and their installed software live here. The mock Defender adapter derives
vulnerabilities by matching installed software against NVD CPE version ranges, so
findings are reproducible and a simulated patch genuinely changes the next scan.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, JSONType
from app.core.types import UTCDateTime, new_id, utcnow


class SimDevice(Base):
    __tablename__ = "sim_defender_devices"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # Defender machine id (40 hex chars)
    computer_dns_name: Mapped[str] = mapped_column(String(255), index=True)
    os_platform: Mapped[str] = mapped_column(String(64))
    os_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    health_status: Mapped[str] = mapped_column(String(32), default="Active")
    risk_score: Mapped[str] = mapped_column(String(16), default="None")
    exposure_level: Mapped[str] = mapped_column(String(16), default="None")
    machine_tags: Mapped[list[Any]] = mapped_column(JSONType, default=list)
    is_cloud: Mapped[bool] = mapped_column(default=False)
    last_seen: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)

    software: Mapped[list[SimDeviceSoftware]] = relationship(back_populates="device", cascade="all, delete-orphan")


class SimDeviceSoftware(Base):
    __tablename__ = "sim_defender_software"
    __table_args__ = (UniqueConstraint("device_id", "vendor", "product"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    device_id: Mapped[str] = mapped_column(ForeignKey("sim_defender_devices.id", ondelete="CASCADE"), index=True)
    vendor: Mapped[str] = mapped_column(String(64))  # CPE vendor
    product: Mapped[str] = mapped_column(String(64))  # CPE product
    display_name: Mapped[str] = mapped_column(String(128))
    version: Mapped[str] = mapped_column(String(64))
    sw_edition: Mapped[str | None] = mapped_column(String(32), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)

    device: Mapped[SimDevice] = relationship(back_populates="software")
