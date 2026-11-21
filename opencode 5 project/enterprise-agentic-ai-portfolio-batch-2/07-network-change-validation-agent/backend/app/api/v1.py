"""API v1 router assembly."""
from fastapi import APIRouter

from app.api import changes, network

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(network.router)
api_v1_router.include_router(network.views)
api_v1_router.include_router(changes.router)
