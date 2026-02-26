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


import typer

from .commands import (
    cli_evaluate,
    cli_install,
    cli_login,
    cli_logout,
    cli_info,
    cli_profile,
    cli_expert_generate,
    cli_document_search,
    cli_generate,
    cli_kernels,
    cli_check,
    cli_jobs,
    cli_stop,
    cli_refcode,
)
from .web.auth import AuthError
from .components.logo import print_header
from .utils import get_rich_console


def main() -> None:
    app = typer.Typer(name="Makora CLI", pretty_exceptions_show_locals=False)

    @app.callback(
        invoke_without_command=True,
        epilog="Documentation available at: https://docs.makora.com\n\nMade with :heart: by [bold]Makora[/bold].",
    )
    def default_callback(ctx: typer.Context) -> None:
        if ctx.invoked_subcommand is None:
            console = get_rich_console()
            print_header(console)
            console.print("[dim]Run[/dim] [cyan]makora --help[/cyan] [dim]for reference of commands.[/dim]")
            console.print("[dim]Documentation available at: https://docs.makora.com")
            console.print()

    app.command("login")(cli_login)
    app.command("logout")(cli_logout)
    app.command("info")(cli_info)
    app.command("generate")(cli_generate)
    app.command("jobs")(cli_jobs)
    app.command("stop")(cli_stop)
    app.command("kernels")(cli_kernels)
    app.command("check")(cli_check)
    app.command("refcode")(cli_refcode)
    app.command("profile")(cli_profile)
    app.command("evaluate")(cli_evaluate)
    app.command("expert-generate")(cli_expert_generate)
    app.command("document-search")(cli_document_search)
    app.command("install")(cli_install)

    try:
        app()
    except AuthError as e:
        console = get_rich_console()
        console.print(f"[red]{e}[/red]")


if __name__ == "__main__":
    main()
