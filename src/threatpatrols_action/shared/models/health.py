from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    status: str
    memory_usage: float
    cpu_usage: float
    background_tasks: int

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"status": "healthy", "memory_usage": 44.2, "cpu_usage": 14.3, "background_tasks": 0}
        }
    )
