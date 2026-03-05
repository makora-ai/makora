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
from ..utils import get_rich_console


class InstallTarget(Enum):
    claude = "claude"


def cli_install(
    target: Annotated[InstallTarget, typer.Argument(help="Platform to install for (currently only 'claude').")],
) -> None:
    """Install the Makora plugin for a supported platform."""
    console = get_rich_console()
    creds = get_current_credentials()
    if creds is None:
        console.print("[red]You need to login first with 'makora login'[/red]")
        raise typer.Exit(1)

    if target != InstallTarget.claude:
        console.print(f"[red]Unsupported install target: {target}[/red]")
        raise typer.Exit(1)

    console.print("[cyan]Installing Makora plugin for Claude Code...[/cyan]")
    try:
        messages = install_claude_code_plugin()
        if "cache_removed" in messages:
            console.print(f"[yellow]{messages['cache_removed']}[/yellow]")
        if "removed" in messages:
            console.print(f"[yellow]{messages['removed']}[/yellow]")
        console.print(f"[dim]{messages['marketplace']}[/dim]")
        console.print("[cyan]Installing makora-plugin...[/cyan]")
        console.print(f"[dim]{messages['plugin']}[/dim]")
        console.print("\n[green]✓ Makora plugin installed successfully for Claude Code![/green]")
    except ClaudeInstallError as e:
        console.print(f"[red]{str(e)}[/red]")
        raise typer.Exit(1)
