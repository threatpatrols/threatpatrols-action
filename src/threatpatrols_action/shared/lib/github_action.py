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

import os
from pathlib import Path
from typing import Optional


class GithubSummary:
    filename: Path
    content: str

    def __init__(self, filename: Optional[Path] = None, content: str = "") -> None:
        if filename:
            self.filename = filename
        else:
            self.filename = Path(os.getenv("GITHUB_STEP_SUMMARY", "/tmp/github-step-summary.txt"))

        self.content = content

    def add_line(self, content):
        self.content += content + "\n"

    def write(self, sort_lines=False):
        if self.filename:
            content_lines = self.content.strip().split("\n")
            if sort_lines:
                content_lines = sorted(content_lines)
            with open(self.filename, "w") as f:
                f.write("\n".join(content_lines))


class GithubOutput:
    filename: Path
    content: str

    def __init__(self, filename: Optional[Path] = None, content: str = "") -> None:
        if filename:
            self.filename = filename
        else:
            self.filename = Path(os.getenv("GITHUB_OUTPUT", "/tmp/github-output.txt"))

        self.content = content

    def add_item(self, key, value):
        self.content += f"{key}={value}\n" + "\n"

    def write(self):
        if self.filename:
            with open(self.filename, "a") as f:
                f.write(self.content.strip())


class GithubInput:
    name: str
    github_summary: GithubSummary | None

    def __init__(self, name: str, github_summary: Optional[GithubSummary] = None) -> None:
        self.name = name
        self.github_summary = github_summary

    def get(self, default: Optional[str] = None, prefix: str = "INPUT_") -> str | None:
        env_name = f"{prefix}{self.name}".upper()
        value = os.getenv(env_name, default)
        if self.github_summary:
            self.github_summary.add_line(f"{self.name}: {value}")
        return value
