#
# Copyright [2025] Threat Patrols Pty Ltd (https://www.threatpatrols.com)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

__title__ = "Threat Patrols Action"
__initials__ = "TPAS"  # == Threat Patrols ActionS
__version__ = "0.1.0"

# Invokes Dynaconf and loads config.yml
from .config import config  # noqa: F401


class action_functions(dict):  # noqa
    def __getattr__(self, key):
        return self[key]

    def __setattr__(self, key, value):
        self[key] = value


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
