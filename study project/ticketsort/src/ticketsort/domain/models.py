"""Pydantic shapes. Code decides priority — LLM only extracts."""

from enum import StrEnum

from pydantic import BaseModel, Field


class Category(StrEnum):
    NETWORK = "network"
    HARDWARE = "hardware"
    SOFTWARE = "software"
    ACCESS = "access"
    EMAIL = "email"
    DATABASE = "database"
    SECURITY = "security"


class Service(StrEnum):
    EMAIL = "email"
    VPN = "vpn"
    SSO = "sso"
    PAYROLL_APP = "payroll-app"
    POS_API = "pos-api"
    ORDERS_DB = "orders-db"
    NETWORK_CORE = "network-core"
    UNKNOWN = "unknown"


class Channel(StrEnum):
    EMAIL = "email"
    PORTAL = "portal"
    PHONE = "phone"
    CHAT = "chat"


class Priority(StrEnum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"
    P5 = "P5"


class TicketIn(BaseModel):
    ticket_id: str
    short_description: str
    description: str
    caller_department: str
    channel: Channel


class Extraction(BaseModel):
    category: Category
    subcategory: str = ""
    impact: int = Field(ge=1, le=3)
    urgency: int = Field(ge=1, le=3)
    affected_service: Service = Service.UNKNOWN
    summary: str
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str = ""


class LLMMeta(BaseModel):
    model: str = ""
    tokens_in: int = 0
    tokens_out: int = 0
    latency_ms: int = 0
    cost_usd: float = 0.0


class TriageResult(Extraction):
    priority: Priority
    assignment_group: str
    needs_human: bool = False
    llm_meta: LLMMeta = LLMMeta()
    prompt_version: str = "v1"
