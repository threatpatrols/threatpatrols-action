import json
from pathlib import Path


class UserAgent:

    user_agents: list[str] = None

    def __init__(self, datafile=None, family="desktop") -> None:
        if not datafile:
            datafile = Path(__file__).parent.parent / f"data/{family}.json"
        if not Path(datafile).exists():
            raise ValueError("User agent datafile could not be found.")

        if not self.user_agents:
            with open(datafile, "r") as f:
                self.user_agents = json.load(f)

    def find(self, *matching_strings) -> str:
        for user_agent in self.user_agents:
            match_count = 0
            for matching_string in matching_strings:
                if matching_string in user_agent:
                    match_count += 1
            if match_count == len(matching_strings):
                return user_agent
