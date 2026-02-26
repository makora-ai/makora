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


from rich.console import Console

from ..utils import get_rich_console


MAKORA_LOGO = """[bold cyan]
 ███╗   ███╗ █████╗ ██╗  ██╗ ██████╗ ██████╗  █████╗ 
 ████╗ ████║██╔══██╗██║ ██╔╝██╔═══██╗██╔══██╗██╔══██╗
 ██╔████╔██║███████║█████╔╝ ██║   ██║██████╔╝███████║
 ██║╚██╔╝██║██╔══██║██╔═██╗ ██║   ██║██╔══██╗██╔══██║
 ██║ ╚═╝ ██║██║  ██║██║  ██╗╚██████╔╝██║  ██║██║  ██║
 ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝[/bold cyan]
[dim]        Automatically unlock peak GPU performance.[/dim]"""


MAKORA_MINI = "[bold cyan]MAKORA[/bold cyan]"


def print_header(console: Console | None = None) -> None:
    """Print the MAKORA header"""
    if console is None:
        console = get_rich_console()

    console.print(MAKORA_LOGO)
    console.print()


def print_mini_header(subtitle: str = "", console: Console | None = None) -> None:
    """Print a minimal header for commands"""
    if console is None:
        console = get_rich_console()

    text = f"{MAKORA_MINI}"
    if subtitle:
        text += f" [dim]|[/dim] [white]{subtitle}[/white]"
    console.print(text)
    console.print()
