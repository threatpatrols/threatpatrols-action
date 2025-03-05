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

import json
from pathlib import Path


class UserAgent:

    user_agents: list[str]

    def __init__(self, datafile=None, family="desktop") -> None:
        if not datafile:
            datafile = Path(__file__).parent.parent / f"data/{family}.json"
        if not Path(datafile).exists():
            raise ValueError("User agent datafile could not be found.")
        with open(datafile, "r") as f:
            self.user_agents = json.load(f)

    def find(self, *matching_strings) -> str | None:
        for user_agent in self.user_agents:
            match_count = 0
            for matching_string in matching_strings:
                if matching_string in user_agent:
                    match_count += 1
            if match_count == len(matching_strings):
                return user_agent

        return None
