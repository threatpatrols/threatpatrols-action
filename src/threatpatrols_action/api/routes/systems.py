from fastapi import APIRouter

from ...shared.lib.system_info import get_system_info
from ...shared.models import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    tags=["System"],
    summary="Get basic system-health and system-status data.",
)
async def health_check() -> HealthResponse:
    return HealthResponse(**get_system_info())
