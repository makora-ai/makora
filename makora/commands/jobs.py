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
from typing import Annotated
from uuid import UUID

import typer
from rich.table import Table
from rich import box

from ..utils import get_rich_console
from ..web.conn import open_connection
from ..web.auth import get_current_credentials
from ..web.sessions import fetch_session_extra, get_user_sessions, stop_job, resolve_session
from ..models.openapi import AgentSessionSummary
from ..models.internal import SessionExtra
from ..components.strings import format_status, format_time_ago, format_device, format_speedup


def create_jobs_table(
    sessions: list[AgentSessionSummary],
    extras: dict[UUID, SessionExtra] | None = None,
    title: str = "Jobs",
) -> Table:
    table = Table(
        title=title,
        box=box.SIMPLE,
        header_style="bold cyan",
        border_style="dim",
        title_style="bold white",
        show_lines=False,
        padding=(0, 1),
    )

    table.add_column("Session ID", style="cyan", no_wrap=True)
    table.add_column("Status", no_wrap=True)
    table.add_column("Label", no_wrap=True, max_width=20)
    if extras is not None:
        table.add_column("Device", no_wrap=True)
        table.add_column("vs torch.compile", justify="right")
    table.add_column("Started", justify="right")

    for session in sessions:
        session_id = str(session.id)[:8]
        status_display = format_status(session.status)
        label = session.label or "-"
        if len(label) > 20:
            label = label[:17] + "..."
        started = format_time_ago(session.started_at)

        row = [session_id, status_display, label]
        if extras is not None:
            extra = extras.get(session.id, SessionExtra())
            row.append(format_device(extra.device))
            row.append(format_speedup(extra.speedup))
        row.append(started)

        table.add_row(*row)

    return table


async def cli_stop_async(job_uuid: str, url: str | None = None) -> None:
    if get_current_credentials() is None:
        raise SystemExit("You need to login first with 'makora login'")

    console = get_rich_console()

    async with open_connection(url) as conn:
        sessions = await get_user_sessions(conn)
        session = await resolve_session(sessions, job_uuid)
        if session is None:
            console.print(f"[red]Job {job_uuid} not found.[/red]")
            raise SystemExit(1)
        session_id = session.id
        console.print(f"Found job: [cyan]{session_id}[/cyan]")
        if await stop_job(conn, session_id):
            console.print(f"[green]Job {str(session_id)[:8]} stopped successfully.[/green]")
        else:
            console.print(f"[yellow]Job {str(session_id)[:8]} is not running.[/yellow]")


async def cli_jobs_async(fast: bool, url: str | None = None) -> None:
    creds = get_current_credentials()
    if creds is None:
        raise SystemExit("You need to login first with 'makora login'")

    console = get_rich_console()
    async with open_connection(url) as conn:
        sessions = await get_user_sessions(conn)

        if not sessions:
            console.print("[dim]No jobs found.[/dim]")
            return

        extras: dict[UUID, SessionExtra] | None = None
        if not fast:
            # Fetch extras in parallel
            tasks = [fetch_session_extra(conn, s.id) for s in sessions]
            results = await asyncio.gather(*tasks)
            extras = {s.id: r for s, r in zip(sessions, results) if r is not None}

    table = create_jobs_table(sessions, extras)
    console.print(table)


def cli_jobs(
    fast: Annotated[bool, typer.Option(help="Skip fetching extra data (device, speedup).")] = False,
    url: Annotated[
        str | None,
        typer.Option(
            help="Overwrite the base URL used to communicate with the service. If "
            "not provided will use the one controlled by MAKORA_URL env var. "
            "Use `makora info` for its value."
        ),
    ] = None,
) -> None:
    """Lists jobs created by the user."""
    asyncio.run(cli_jobs_async(fast, url))


def cli_stop(
    job_uuid: Annotated[str, typer.Argument(help="The UUID (or prefix) of the job to stop.")],
    url: Annotated[
        str | None,
        typer.Option(
            help="Overwrite the base URL used to communicate with the service. If "
            "not provided will use the one controlled by MAKORA_URL env var. "
            "Use `makora info` for its value."
        ),
    ] = None,
) -> None:
    """Request to stop a running job."""
    asyncio.run(cli_stop_async(job_uuid, url))
