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
from pathlib import Path
from typing import Annotated

import typer
from rich.syntax import Syntax

from ..utils import get_rich_console
from ..web.conn import open_connection
from ..web.auth import get_current_credentials
from ..web.sessions import get_user_sessions, get_session, resolve_session


async def cli_refcode_async(session_id: str, output: str | None, url: str | None) -> None:
    creds = get_current_credentials()
    if creds is None:
        raise SystemExit("You need to login first with 'makora login'")

    console = get_rich_console()

    async with open_connection(url) as conn:
        sessions = await get_user_sessions(conn)
        match = await resolve_session(sessions, session_id)

        if not match:
            raise SystemExit(f"No session found matching '{session_id}'")

        session = await get_session(conn, str(match.id))

    code = session.request.problem_description_code.code
    if not code:
        raise SystemExit("No refcode available for this session.")

    if output:
        Path(output).write_text(code, encoding="utf-8")
        console.print(f"[green]Refcode saved to: {output}[/green]")
        return

    syntax = Syntax(
        code,
        "python",
        theme="monokai",
        line_numbers=False,
        word_wrap=False,
    )
    console.print(syntax)


def cli_refcode(
    session_id: Annotated[str, typer.Argument(help="Session ID (or prefix).")],
    output: Annotated[str | None, typer.Option("-o", "--output", help="Save refcode to a file.")] = None,
    url: Annotated[
        str | None,
        typer.Option(
            help="Overwrite the base URL used to communicate with the service. If "
            "not provided will use the one controlled by MAKORA_URL env var. "
            "Use `makora info` for its value."
        ),
    ] = None,
) -> None:
    """Show the original refcode submitted for a session."""
    asyncio.run(cli_refcode_async(session_id, output, url))
