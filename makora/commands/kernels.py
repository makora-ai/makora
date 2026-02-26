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
import textwrap
import itertools as itr
from pathlib import Path
from typing import Annotated
from uuid import UUID

import typer
from rich.syntax import Syntax
from rich.table import Table

from ..utils import get_rich_console
from ..web.conn import open_connection
from ..web.auth import get_current_credentials
from ..web.sessions import get_user_sessions, get_session_kernels, resolve_session
from ..models.openapi import EvaluatedKernel
from ..components.strings import (
    create_styled_table,
    format_close_miss_status,
    format_status,
    format_time,
    format_speedup,
)


def create_kernels_table(kernels: list[list[EvaluatedKernel]], title: str = "Kernels") -> Table:
    table = create_styled_table(title)

    table.add_column("Attempt", justify="center")
    table.add_column("Kernel ID", style="cyan", no_wrap=True)
    table.add_column("Name", no_wrap=True, max_width=15)
    table.add_column("Status", no_wrap=True)
    table.add_column("Time", justify="right")
    table.add_column("vs torch.compile", justify="right")

    for attempt_num, attempt_kernels in enumerate(kernels):
        for kernel in attempt_kernels:
            kernel_id = str(kernel.id)[:8]
            name = kernel.name
            if len(name) > 15:
                name = name[:12] + "..."
            speedup = kernel.speed_up_compiled

            if kernel.is_close_miss:
                status_display = format_close_miss_status(kernel.best_atol, kernel.best_rtol)
            else:
                status_display = format_status(kernel.evaluation_status)

            table.add_row(
                str(attempt_num + 1),
                kernel_id,
                name,
                status_display,
                format_time(kernel.time, kernel.time_unit),
                format_speedup(speedup),
            )

    return table


async def resolve_kernel(
    kernels: list[list[EvaluatedKernel]],
    session_id: UUID,
    kernel_id: str,
) -> EvaluatedKernel | None:
    """Find kernel matching the given ID prefix. Returns (full_kernel_id, kernels_data)."""

    matches: list[EvaluatedKernel] = []
    for krn in itr.chain.from_iterable(kernels):
        if str(krn.id).startswith(kernel_id):
            matches.append(krn)

    if not matches:
        return None
    elif len(matches) > 1:
        kernel_list = [" * " + str(k.id) for k in matches]
        kernel_block = textwrap.indent("\n".join(kernel_list), "    ")
        raise ValueError(
            f"Kernel ID prefix: {kernel_id} is matching more than one kernel from session {session_id!r}:\n"
            + kernel_block
        )

    return matches[0]


async def cli_kernels_list_async(session_id: str, url: str | None = None) -> None:
    creds = get_current_credentials()
    if creds is None:
        raise SystemExit("You need to login first with 'makora login'")

    console = get_rich_console()

    async with open_connection(url) as conn:
        sessions = await get_user_sessions(conn)
        match = await resolve_session(sessions, session_id)

        if not match:
            raise SystemExit(f"No session found matching '{session_id}'")

        kernels = await get_session_kernels(conn, str(match.id))

    if not kernels:
        console.print("[dim]No kernels found for this session.[/dim]")
        return

    table = create_kernels_table(kernels, title=f"Kernels for {str(match.id)[:8]} ({match.label})")
    console.print(table)


async def cli_kernels_code_async(session_id: str, kernel_id: str, output: str | None, url: str | None = None) -> None:
    creds = get_current_credentials()
    if creds is None:
        raise SystemExit("You need to login first with 'makora login'")

    console = get_rich_console()

    async with open_connection(url) as conn:
        sessions = await get_user_sessions(conn)
        match = await resolve_session(sessions, session_id)

        if not match:
            raise SystemExit(f"No session found matching '{session_id}'")

        kernels = await get_session_kernels(conn, str(match.id))

        # Resolve kernel ID and get perf data from list endpoint
        kernel = await resolve_kernel(kernels, match.id, kernel_id)

        if not kernel:
            console.print(f"[red]No kernel found matching '{kernel_id}'[/red]")
            if kernels:
                console.print("\nAvailable kernels:")
                for krn in itr.chain.from_iterable(kernels):
                    console.print(f"  {str(krn.id)[:8]}  {krn.name}")

            raise SystemExit(1)

    if not kernel.code:
        raise SystemExit("No code available for this kernel.")

    # Save to file if requested
    if output:
        Path(output).write_text(kernel.code, encoding="utf-8")
        console.print(f"[green]Kernel saved to: {output}[/green]")
        return

    # Display with syntax highlighting (no box for easy copy/paste)
    lexer = "python"

    syntax = Syntax(
        kernel.code,
        lexer,
        theme="monokai",
        line_numbers=False,
        word_wrap=False,
    )
    console.print(syntax)

    # Show performance data
    console.print()
    console.print(f"[bold cyan]── {kernel.name or 'Kernel'} ({str(kernel.id)[:8]}) ──[/bold cyan]")

    if kernel.is_close_miss:
        console.print(f"  Status:           {format_close_miss_status(kernel.best_atol, kernel.best_rtol)}")

    time_ms = kernel.time
    ref_eager = kernel.reference_eager
    ref_compiled = kernel.reference_compile
    speedup_eager = kernel.speed_up_eager
    speedup_compiled = kernel.speed_up_compiled

    if time_ms:
        console.print(f"  Kernel time:      [cyan]{time_ms:.3f} ms[/cyan]")
    if ref_eager:
        console.print(f"  Reference eager:  [dim]{ref_eager:.3f} ms[/dim]")
    if ref_compiled:
        console.print(f"  torch.compile:    [dim]{ref_compiled:.3f} ms[/dim]")
    if speedup_eager:
        console.print(f"  vs eager:         {format_speedup(speedup_eager)}")
    if speedup_compiled:
        console.print(f"  vs torch.compile: {format_speedup(speedup_compiled)}")


def cli_kernels(
    session_id: Annotated[str, typer.Argument(help="Session ID (or prefix).")],
    kernel_id: Annotated[
        str | None,
        typer.Argument(help="Kernel ID (or prefix) - if provided, shows kernel code."),
    ] = None,
    output: Annotated[str | None, typer.Option("-o", "--output", help="Save kernel code to file.")] = None,
    url: Annotated[
        str | None,
        typer.Option(
            help="Overwrite the base URL used to communicate with the service. If "
            "not provided will use the one controlled by MAKORA_URL env var. "
            "Use `makora info` for its value."
        ),
    ] = None,
) -> None:
    """List kernels for a session, or view kernel code if kernel_id is provided."""
    if kernel_id:
        asyncio.run(cli_kernels_code_async(session_id, kernel_id, output, url))
    else:
        asyncio.run(cli_kernels_list_async(session_id, url))
