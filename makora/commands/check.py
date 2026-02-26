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


import asyncio
import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.syntax import Syntax

from ..utils import get_rich_console
from ..models.internal import TargetDevice
from ..web.conn import open_connection
from ..web.auth import ensure_authenticated
from ..components.logo import print_mini_header
from ..components.problem_validation import validate_problem


async def cli_check_async(
    file: Path,
    device: TargetDevice,
    url: str | None = None,
    fix: bool = False,
    interactive: bool = True,
) -> None:
    console = get_rich_console()
    print_mini_header(f"Check: {file.name}")

    if not file.exists():
        console.print(f"[red]Error:[/red] File not found: {file}")
        raise typer.Exit(1)

    code = file.read_text()

    async with open_connection(url) as conn:
        await ensure_authenticated(conn)

        hint_command = f"makora check --file {file} --device {device.value}"
        validation_result = await validate_problem(
            conn=conn,
            code=code,
            device=device,
            label=file.name,
            fix=fix,
            interactive=interactive,
            hint_command=hint_command,
            console=console,
        )

        if validation_result is None:
            raise typer.Exit(1)

        _, final_code, fixed = validation_result

        if fixed:
            # Display with syntax highlighting (no box for easy copy/paste)
            lexer = "python"
            syntax = Syntax(
                final_code,
                lexer,
                theme="monokai",
                line_numbers=False,
                word_wrap=False,
            )
            console.print()
            console.print("[bold]Final working solution, after applying fixes:[/bold]")
            console.print(syntax)


def cli_check(
    file: Annotated[Path, typer.Argument(help="Path to Python file to validate.")],
    device: Annotated[TargetDevice, typer.Option("-d", "--device", help="Device type.")],
    url: Annotated[
        str | None,
        typer.Option(
            help="Overwrite the base URL used to communicate with the service. If "
            "not provided will use the one controlled by MAKORA_URL env var. "
            "Use `makora info` for its value."
        ),
    ] = None,
    fix: Annotated[
        bool,
        typer.Option(
            help="Enables automatic fix suggestions if the provided problem file "
            "contains errors. Any fix has to be accepted by the user interactively, "
            "unless --alone if passed or input is not a TTY, in which case all fixes "
            "will be accepted automatically."
        ),
    ] = False,
    alone: Annotated[bool, typer.Option(help="Disables any interactivity.")] = False,
) -> None:
    """Evaluates the given reference catching possible errors."""
    asyncio.run(
        cli_check_async(
            file=file,
            device=device,
            url=url,
            fix=fix,
            interactive=(not alone and sys.stdin.isatty()),
        )
    )
