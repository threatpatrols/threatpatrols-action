#
#  Copyright (c) 2025 Threat Patrols Pty Ltd <contact@threatpatrols.com>
#  See LICENSE.md for terms
#

__title__ = "Threat Patrols Action"
__initials__ = "TPAS"  # == Threat Patrols ActionS
__version__ = "0.1.0"

# Invokes Dynaconf and loads config.yml
from .config import config  # noqa: F401


class action_models(dict):  # noqa
    def __getattr__(self, key):
        return self[key]

    def __setattr__(self, key, value):
        self[key] = value


class state_handlers(dict):  # noqa
    def __getattr__(self, key):
        return self[key]

    def __setattr__(self, key, value):
        self[key] = value
