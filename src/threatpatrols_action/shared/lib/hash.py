#
# Copyright [2023-2025] Threat Patrols Pty Ltd (https://www.threatpatrols.com)
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

import hashlib
import os.path
from base64 import b64encode
from pathlib import Path

HASH_METHOD_DEFAULT = "sha256"


def hash_of_string(input_string: str, hash_method: str = HASH_METHOD_DEFAULT, encoding: str = "utf8") -> str:
    h = hashlib.new(hash_method)
    h.update(input_string.encode(encoding))
    return h.hexdigest()


def hash_of_bytes(input_bytes: bytes, hash_method: str = HASH_METHOD_DEFAULT) -> str:
    h = hashlib.new(hash_method)
    h.update(input_bytes)
    return h.hexdigest()


def hash_of_file(
    file: str | Path, hash_method: str = HASH_METHOD_DEFAULT, chunk_size: int = 8192, base64_encoded: bool = False
) -> str:
    h = hashlib.new(hash_method)
    with open(file, "rb") as f:
        chunk = f.read(chunk_size)
        while chunk:
            h.update(chunk)
            chunk = f.read(chunk_size)
    if base64_encoded:
        return b64encode(h.digest()).decode()
    return h.hexdigest()


def generate_sha256sums_file(path: Path, recursive: bool = True, sha256sums_filename: str = "SHA256SUMS") -> Path:
    if not recursive:
        path_glob = path.glob("*")
    else:
        path_glob = path.rglob("*")

    content = ""
    for path_name in path_glob:
        if not os.path.isfile(path_name):
            continue
        content += f"{hash_of_file(path_name)}  {os.path.relpath(path_name, path)}" + "\n"

    filename = Path(os.path.join(path, sha256sums_filename))
    with open(filename, "w") as f:
        f.write(content.strip())

    return filename
