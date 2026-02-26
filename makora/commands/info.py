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


from ..utils import get_env_vars, get_rich_console
from ..components.logo import print_header
from ..components.strings import create_styled_table
from ..web.auth import get_current_credentials


def cli_info() -> None:
    """Shows current information about user status and env variables."""
    from ..version import info

    console = get_rich_console()

    print_header(console)

    ver_info = info()

    console.print("[bold]Makora version[/bold]:", ver_info["version"])
    if ver_info["repo"] != "unknown":
        console.print("[dim]    Repo: " + ver_info["repo"] + "[/dim]")
        console.print("[dim]    Commit: " + ver_info["commit"] + "[/dim]")
    console.print()

    user = get_current_credentials()
    if user is not None:
        console.print("[bold]Logged in as:[/bold]", f"[cyan]{user.user}[/cyan]")
    else:
        console.print("[bold]Currently logged out[/bold]")

    console.print()
    console.print("[bold]Existing knobs and their values (non-value in red):[/bold]")

    table = create_styled_table()
    table.add_column("Env Variable")
    table.add_column("Value")
    table.add_column("Default")

    for var in get_env_vars():
        if var.hidden:
            continue

        not_default = var.value != var.default
        if not_default:
            value = f"[red bold]{var.value}[/red bold]"
        else:
            value = var.value

        table.add_row(var.var_name, value, f"[dim]{var.default}[/dim]")

    console.print(table)
