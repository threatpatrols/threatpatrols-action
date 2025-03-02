import json

from pydantic import BaseModel, ConfigDict

from . import HEALTH_ITEM_EXAMPLE


class HealthResponse(BaseModel):
    cpu_usage_p: float
    memory_used_p: float

    model_config = ConfigDict(extra="allow", json_schema_extra={"example": json.loads(HEALTH_ITEM_EXAMPLE)})
