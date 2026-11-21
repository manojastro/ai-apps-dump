from __future__ import annotations

from fastapi import Request

from app.constants import DISCLAIMER, RULES_VERSION
from app.models.facts import ApiMeta


def meta_for(request: Request) -> ApiMeta:
    return ApiMeta(
        disclaimer=DISCLAIMER,
        data_mode=getattr(request.app.state, "data_mode", "mock"),
        rules_version=RULES_VERSION,
    )
