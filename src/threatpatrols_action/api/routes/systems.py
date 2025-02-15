import psutil
from fastapi import APIRouter, BackgroundTasks

from ...shared.models import HealthResponse

router = APIRouter()


@router.get(
    f"/health",
    tags=["System"],
    summary="Get basic system-health and system-status data.",
)
async def health_check(background_tasks: BackgroundTasks) -> HealthResponse:
    return HealthResponse(
        status="healthy",
        memory_usage=psutil.virtual_memory().percent,
        cpu_usage=psutil.cpu_percent(),
        background_tasks=len(background_tasks.tasks),
    )
