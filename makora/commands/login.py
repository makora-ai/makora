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


import sys
import asyncio
import getpass
from typing import Annotated
from pathlib import Path

import typer

from ..utils import get_rich_console
from ..config import GENERATE_BASE_URL
from ..web.conn import open_connection
from ..web.auth import login_with_token


async def cli_login_async(
    user: str | None,
    token: str | None = None,
    interactive: bool = True,
    url: str | None = None,
) -> None:
    console = get_rich_console()

    if token is None:
        if not interactive:
            console.print(
                "[red]You have to provide your user's token, or a "
                "file containing it, using --token when running "
                "non-interactively.[/red]"
            )
            raise typer.Exit(1)

        console.print(
            f"Please go to: {url or GENERATE_BASE_URL.value}/tokens and select an "
            "API token you want to use for this session."
        )
        console.print("Create a new token if none shows up. You need to have an account and login to access the page.")
        console.print()
        token = getpass.getpass("Token: ")

    maybe_token_file = Path(token)
    if maybe_token_file.exists():
        if not maybe_token_file.is_file():
            console.print(f"[red]Path {token!r} exists but is not a file! Cannot read the user's token.[/red]")
            raise typer.Exit(1)

        token = maybe_token_file.read_text()
        if not token:
            console.print(f"[red]Token file at: {str(maybe_token_file)!r} is empty.[/red]")
            raise typer.Exit(1)

    async with open_connection(url) as conn:
        creds = await login_with_token(conn, user, token)
        if creds.token == token:
            console.print("[green][bold]Logged in successfully![/]")
        else:
            console.print(
                "[red]Warning: Login succeeded but resulted in a different token "
                "being in-use than the provided one! This is unexpected and might "
                "result in further errors.[/red]"
            )


def cli_login(
    user: Annotated[
        str | None,
        typer.Option(
            help="Your user's email address. Optional: if provided will make "
            "sure the user associated with the provided token matches the given user."
        ),
    ] = None,
    token: Annotated[
        str | None,
        typer.Option(
            help="Your user's API token. If not provided, the app will ask for "
            "it interactively (or fail if running non-interactively). If "
            "provided, can be the token itself or a path to a file containing "
            "the token."
        ),
    ] = None,
    url: Annotated[
        str | None,
        typer.Option(
            help="Overwrite the base URL used to communicate with the service. If "
            "not provided will use the one controlled by MAKORA_URL env var. "
            "Use `makora info` for its value."
        ),
    ] = None,
    alone: Annotated[bool, typer.Option(help="Disables any interactivity.")] = False,
) -> None:
    """Login command to the service."""
    asyncio.run(
        cli_login_async(
            user=user,
            token=token,
            interactive=(not alone and sys.stdin.isatty()),
            url=url,
        )
    )
