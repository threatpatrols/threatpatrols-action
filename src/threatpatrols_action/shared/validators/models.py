from pydantic import BaseModel

from ...exceptions import ThreatPatrolsException


def action_model_validator(action_models: object):
    """
    Checks to confirm the action models are roughly okay
    """

    check_models = ("ActionRequest", "ActionResponse", "ActionListItemResponse")

    for action in check_models:

        try:
            model: BaseModel = getattr(action_models, str(action))
        except:
            raise ThreatPatrolsException(f"Unable to load the {action!r} required model.")

        if not issubclass(model, BaseModel):
            raise ThreatPatrolsException(f"Action model {action!r} parent is not BaseModel type.")

        try:
            keys = list(model.model_fields.keys())
        except:
            raise ThreatPatrolsException(f"Unable to get keys from {action!r} Action model.")

        if "tags" not in keys:
            raise ThreatPatrolsException(f"Action model {action!r} does not contain 'tags' attribute.")
