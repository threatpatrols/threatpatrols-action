from typing import Optional

from pydantic import BaseModel, ConfigDict


class ActionBaseModel(BaseModel):

    # tags is always required
    tags: Optional[dict[str, str]] = None

    def model_post_init(self, *_, **__) -> None:
        if not self.tags:
            self.tags = {}
