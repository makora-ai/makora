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

from ..utils import get_rich_console
from ..models.openapi import KernelLanguage
from ..models.internal import TargetDevice
from ..web.conn import open_connection
from ..web.auth import ensure_authenticated
from ..web.sessions import new_session
from ..components.spinner import show_spinner
from ..components.logo import print_mini_header
from ..components.results import print_success_panel
from ..components.problem_validation import validate_problem


async def cli_generate_async(
    file: Path,
    device: TargetDevice,
    language: KernelLanguage | None,
    label: str,
    atol: float,
    rtol: float,
    url: str | None,
    fix: bool = False,
    instr: list[Path] | None = None,
    interactive: bool = True,
) -> None:
    console = get_rich_console()
    print_mini_header(f"Generate: {file.name}")

    if not file.exists():
        console.print(f"[red]Error:[/red] File not found: {file}")
        raise typer.Exit(1)

    code = file.read_text()

    user_prompt = ""
    if instr:
        for instr_file in instr:
            if not instr_file.exists():
                console.print(f"[red]Provided instruction file: {instr_file} could not be found")
                raise typer.Exit(1)

            user_prompt += instr_file.read_text().strip() + "\n\n"

        user_prompt = user_prompt.strip()

    if language is None:
        language = device.get_default_language()

    elif not device.supports_language(language):
        console.print(f"[red]Error:[/red] Device {device.value} does not support {language.value}")
        raise typer.Exit(1)

    console.print(f"[dim]Device:[/dim] {device.value}")
    console.print(f"[dim]Language:[/dim] {language.value}")
    console.print()

    async with open_connection(url) as conn:
        await ensure_authenticated(conn)

        hint_command = f"makora generate --file {file} --device {device.value}"
        validation_result = await validate_problem(
            conn=conn,
            code=code,
            device=device,
            label=label,
            fix=fix,
            interactive=interactive,
            hint_command=hint_command,
            console=console,
        )

        if validation_result is None:
            raise typer.Exit(1)

        problem_id, *_ = validation_result

        console.print()
        with show_spinner("Creating session..."):
            session_id = await new_session(
                conn=conn,
                problem_id=problem_id,
                language=language,
                device=device,
                label=label,
                atol=atol,
                rtol=rtol,
                user_prompt=user_prompt,
            )

    console.print()
    print_success_panel(
        f"Session created!\n\n"
        f"[dim]Session ID:[/dim] [cyan]{session_id}[/cyan]\n"
        f"[dim]Problem ID:[/dim] [cyan]{problem_id}[/cyan]"
    )
    console.print()
    console.print("[dim]Monitor progress with:[/dim] [cyan]makora jobs[/cyan]")


def cli_generate(
    file: Annotated[Path, typer.Option(help="A file containing problem definition (reference code).")],
    device: Annotated[TargetDevice, typer.Option("-d", "--device", help="Device type.")],
    language: Annotated[
        KernelLanguage | None,
        typer.Option(help="Target language. If not provided will use the default for the given device."),
    ] = None,
    label: Annotated[str, typer.Option(help="Optional user-defined label for the job.")] = "",
    atol: Annotated[float, typer.Option(help="Absolute tolerance to use when validating generated solutions.")] = 1e-2,
    rtol: Annotated[float, typer.Option(help="Relative tolerance to use when validating generated solutions.")] = 1e-2,
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
    instr: Annotated[
        list[Path] | None,
        typer.Option(
            help="A path to a markdown file containing additional instructions that will "
            "be passed to the agent. Can be specified multiple times, in which case "
            "all files' content will be concatenated, in the order in which the files "
            "are specified."
        ),
    ] = None,
    alone: Annotated[bool, typer.Option(help="Disables any interactivity.")] = False,
) -> None:
    """Submit a new kernel generation job to the agent."""
    asyncio.run(
        cli_generate_async(
            file=file,
            device=device,
            language=language,
            label=label,
            atol=atol,
            rtol=rtol,
            url=url,
            fix=fix,
            instr=instr,
            interactive=(not alone and sys.stdin.isatty()),
        )
    )
