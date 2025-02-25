#
# Copyright [2025] Threat Patrols Pty Ltd (https://www.threatpatrols.com)
#

import os


class GithubSummary:

    filename: str
    content: str

    def __init__(self, filename=None, content: str = ""):
        if filename:
            self.filename = filename
        else:
            self.filename = os.getenv("GITHUB_STEP_SUMMARY")

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

    filename: str
    content: str

    def __init__(self, filename=None, content: str = ""):
        if filename:
            self.filename = filename
        else:
            self.filename = os.getenv("GITHUB_OUTPUT")

        self.content = content

    def add_item(self, key, value):
        self.content += f"{key}={value}\n" + "\n"

    def write(self):
        if self.filename:
            with open(self.filename, "a") as f:
                f.write(self.content.strip())


class GithubInput:

    name: str
    github_summary: GithubSummary

    def __init__(self, name, github_summary: GithubSummary = None):
        self.name = name
        self.github_summary = github_summary

    def get(self, default=None, prefix="INPUT_"):
        env_name = f"{prefix}{self.name}".upper()
        value = os.getenv(env_name, default)
        if self.github_summary:
            self.github_summary.add_line(f"{self.name}: {value}")
        return value
