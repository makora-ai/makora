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

"""Claude Code plugin installation utilities."""

import shutil
import subprocess
from pathlib import Path

from ..log import get_logger

PLUGIN_DIR = Path(__file__).resolve().parent.parent / "data" / "claude-plugin"


class ClaudeInstallError(Exception):
    """Raised when Claude Code plugin installation fails."""

    pass


def install_claude_code_plugin() -> dict[str, str]:
    """Install the Makora plugin for Claude Code."""
    get_logger().info("Installing Claude Code plugin from {}", PLUGIN_DIR)
    messages: dict[str, str] = {}
    data_path = PLUGIN_DIR.resolve()

    cache_path = Path.home() / ".claude" / "plugins" / "cache" / "makora"
    if cache_path.exists():
        get_logger().debug("Removing plugin cache: {}", cache_path)
        shutil.rmtree(cache_path)
        messages["cache_removed"] = f"Removed cache folder: {cache_path}"

    get_logger().debug("Running: claude plugin marketplace remove makora")
    result = subprocess.run(
        ["claude", "plugin", "marketplace", "remove", "makora"],
        capture_output=True,
        text=True,
    )
    get_logger().debug("marketplace remove: returncode={}", result.returncode)
    if result.returncode == 0:
        messages["removed"] = "Removed existing makora marketplace."

    get_logger().debug("Running: claude plugin marketplace add {}", data_path)
    result = subprocess.run(
        ["claude", "plugin", "marketplace", "add", str(data_path)],
        capture_output=True,
        text=True,
    )
    get_logger().debug("marketplace add: returncode={} stderr={}", result.returncode, result.stderr)
    if result.returncode != 0:
        raise ClaudeInstallError(f"Failed to add marketplace: {result.stderr}")
    messages["marketplace"] = result.stdout.strip() if result.stdout.strip() else "Marketplace added."

    get_logger().debug("Running: claude plugin install makora-plugin@makora")
    result = subprocess.run(
        ["claude", "plugin", "install", "makora-plugin@makora"],
        capture_output=True,
        text=True,
    )
    get_logger().debug("plugin install: returncode={} stderr={}", result.returncode, result.stderr)
    if result.returncode != 0:
        raise ClaudeInstallError(f"Failed to install plugin: {result.stderr}")
    messages["plugin"] = result.stdout.strip() if result.stdout.strip() else "Plugin installed."

    get_logger().info("Plugin installation complete")
    return messages
