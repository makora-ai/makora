# Copyright 2026 Makora Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Configuration management for Makora CLI."""

from .utils import EnvVar


GENERATE_BASE_URL = EnvVar("MAKORA_URL", "https://generate.makora.com")


def _normalize_generate_api_url(url: str) -> str:
    normalized = url.strip().rstrip("/")
    if normalized.endswith("/api/v1"):
        return f"{normalized}/"
    return f"{normalized}/api/v1/"


def get_generate_base_url(url: str | None = None) -> str:
    """Get normalized base URL for Generate API requests."""
    return _normalize_generate_api_url(url or GENERATE_BASE_URL.value)
