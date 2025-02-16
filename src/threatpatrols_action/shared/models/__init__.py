from typing import Optional

from pydantic import BaseModel, ConfigDict, ValidationError


class PrivateHandleBaseModel(BaseModel):

    _tags: Optional[dict[str, str]] = None
    _callbacks: Optional[dict[str, str]] = None
    model_config = ConfigDict(extra="allow")  # enabled for private _keys

    def model_post_init(self, *_, **__) -> None:
        if not self._tags:
            self._tags = {}
        if (not self.model_config) or ("extra" not in self.model_config) or (self.model_config.get("extra") != "allow"):
            raise ValidationError("Model.model_config['extra'] must == allow")

    def model_dump(self, *args, **kwargs):
        private_attr_data = {}
        for private_attr in self.__private_attributes__.keys():
            try:
                private_data = getattr(self, private_attr)
            except AttributeError:
                private_data = None
            if private_data and isinstance(private_data, dict):
                private_attr_data[private_attr] = dict(sorted(private_data.items()))
            elif private_data:
                private_attr_data[private_attr] = private_data
        return dict(sorted({**super().model_dump(*args, **kwargs), **private_attr_data}.items()))


from .callback import Callback, CallbackHttp, CallbackSmtp
from .health import HealthResponse
from .task import TaskListItemResponse, TaskResponse, TaskState
