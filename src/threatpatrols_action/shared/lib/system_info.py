#
# Copyright [2023-2024] Threat Patrols Pty Ltd (https://www.threatpatrols.com)
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
import subprocess

import psutil
from fastapi import BackgroundTasks


def get_system_info() -> dict[str, str]:
    data = {**get_system_lsb(), **get_system_resources(), **get_system_uname()}
    for k in ["codename", "description", "version"]:
        data.pop(k, None)
    return dict(sorted(data.items()))  # type: ignore


def get_system_uname() -> dict[str, str]:
    data = {}
    for key in ["sysname", "nodename", "release", "version", "machine"]:
        if hasattr(os.uname(), key):
            data[key] = str(getattr(os.uname(), key))
    return data


def get_system_lsb() -> dict[str, str]:
    data = {}
    try:
        sp = subprocess.run(args=["lsb_release", "-a"], capture_output=True, check=False)
    except Exception:
        return {}
    for line in sp.stdout.decode().split("\n"):
        if ":" not in line:
            continue
        k, v = line.split(":")
        key_full = k.strip().lower().replace(" ", "_").replace("distributor_id", "vendor")
        data[key_full] = v.strip()
    return data


def get_system_resources() -> dict[str, int | float]:
    return {
        "cpu_usage_p": psutil.cpu_percent(),
        "memory_usage_p": psutil.virtual_memory().percent,
        "background_tasks": len(BackgroundTasks().tasks),
    }
