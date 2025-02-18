from pydantic import BaseModel

from ...exceptions import ThreatPatrolsException


def action_model_validator(action_models: object):
    """
    Checks to confirm the action models are roughly okay
    """

    check_models = ("ActionRequest", "ActionItem", "ActionListItem")

    for action in check_models:

        try:
            model: BaseModel = getattr(action_models, str(action))
        except AttributeError:
            raise ThreatPatrolsException(f"Unable to load the {action!r} required model.")

        if not issubclass(model, BaseModel):
            raise ThreatPatrolsException(f"Action model {action!r} parent is not BaseModel type.")

        try:
            _ = model._tags
        except AttributeError:
            raise ThreatPatrolsException(f"Action model {action!r} does not contain '_tags' attribute.")
