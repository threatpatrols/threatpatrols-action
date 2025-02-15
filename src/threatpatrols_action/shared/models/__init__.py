from typing import Optional

from pydantic import BaseModel


class TagsBaseModel(BaseModel):
    tags: Optional[dict[str, str]] = None

    def model_post_init(self, *_, **__) -> None:
        if not self.tags:
            self.tags = {}


from .callback import Callback, CallbackHttp, CallbackSmtp
from .health import HealthResponse
from .task import TaskListItemResponse, TaskResponse, TaskState
