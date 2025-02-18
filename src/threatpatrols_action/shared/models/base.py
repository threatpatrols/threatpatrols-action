from typing import Optional

from pydantic import BaseModel, ConfigDict, ValidationError


class BaseModelPrivateHandler(BaseModel):

    _tags: Optional[dict[str, str]] = None
    _callbacks: Optional[dict[str, str]] = None
    model_config = ConfigDict(extra="allow")  # enabled for private _keys

    def model_post_init(self, *_, **__) -> None:
        if not self._tags:
            self._tags = {}
        if (not self.model_config) or ("extra" not in self.model_config) or (self.model_config.get("extra") != "allow"):
            raise ValidationError("Model.model_config['extra'] must == allow")

    def model_dump(self, *args, include_private=True, exclude_extra=True, **kwargs):

        dump_data = super().model_dump(*args, **kwargs)  # NB: includes private
        keys = set(list(dump_data.keys()) + list(self.model_fields.keys()) + list(self.__private_attributes__.keys()))

        for key in keys:
            key_is_extra = True if key not in self.model_fields.keys() else False
            key_is_private = True if key.startswith("_") else False

            if include_private is True and key_is_private is True:
                if dump_data.get(key) is None and getattr(self, key) is not None:
                    dump_data[key] = getattr(self, key)
                    continue

            if include_private is False and key_is_private is True:
                del dump_data[key]

            if exclude_extra is True and key_is_extra is True:
                if key_is_private is True and include_private is True:
                    continue
                del dump_data[key]

        return dict(sorted(dump_data.items()))
