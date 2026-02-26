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


from enum import Enum
from typing import Annotated

import typer

from ..plugins.claude import ClaudeInstallError, install_claude_code_plugin
from ..web.auth import get_current_credentials


class InstallTarget(Enum):
    claude = "claude"


def cli_install(
    target: Annotated[InstallTarget, typer.Argument(help="Platform to install for (currently only 'claude').")],
) -> None:
    """Install the Makora plugin for a supported platform."""
    creds = get_current_credentials()
    if creds is None:
        raise SystemExit("You need to login first with 'makora login'")

    if target != InstallTarget.claude:
        typer.echo(f"Unsupported install target: {target}", err=True)
        raise typer.Exit(1)

    typer.echo("Installing Makora plugin for Claude Code...")
    try:
        messages = install_claude_code_plugin()
        if "cache_removed" in messages:
            typer.echo(messages["cache_removed"])
        if "removed" in messages:
            typer.echo(messages["removed"])
        typer.echo(messages["marketplace"])
        typer.echo("Installing makora-plugin...")
        typer.echo(messages["plugin"])
        typer.echo("\nMakora plugin installed successfully for Claude Code!")
    except ClaudeInstallError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1)
