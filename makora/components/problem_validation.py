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


from uuid import UUID

from rich.console import Console

from ..utils import get_rich_console
from ..web.conn import Connection
from ..web.problems import submit_and_poll_validation
from ..models.internal import TargetDevice
from ..models.openapi import StepStatus
from ..components.spinner import show_spinner
from ..components.fix_suggestions import print_fix_suggestion, prompt_accept_fix
from ..components.results import print_validation_result


STEP_TO_SPINNER_LABEL = {
    "compilation": "Compiling...",
    "preparation": "Preparing objects for execution...",
    "benchmarking": "Benchmarking...",
    "Suggesting fixes": "Suggesting fixes...",
}


async def validate_problem(
    conn: Connection,
    code: str,
    device: TargetDevice,
    label: str,
    fix: bool,
    interactive: bool,
    hint_command: str | None = None,
    console: Console | None = None,
) -> tuple[UUID, str, bool] | None:
    if console is None:
        console = get_rich_console()

    revalidating = False
    while True:
        spinner_message = "Re-testing fixed code..." if revalidating else "Validating problem..."
        with show_spinner(spinner_message) as spinner:

            def on_progress(step: str) -> None:
                if spinner is None:
                    return
                label = STEP_TO_SPINNER_LABEL.get(step, f"{step}...")
                spinner.update(f"[cyan]{label}[/cyan]")

            status = await submit_and_poll_validation(
                conn,
                code,
                label,
                target_device=device,
                fix=fix,
                on_progress=on_progress,
            )

        print_validation_result(status, show_benchmark=True)

        if status.status == StepStatus.completed:
            break

        if not fix:
            if hint_command:
                console.print()
                console.print("[dim]Hint: try submitting with --fix to get automatic fix suggestions:[/dim]")
                console.print(f"[dim]  {hint_command} --fix[/dim]")
            return None

        if status.fix_suggestions is None:
            console.print("[red]No fixes to suggest! Sorry :(")
            return None

        print_fix_suggestion(status.fix_suggestions, code, console)

        if not interactive or prompt_accept_fix(console):
            code = status.fix_suggestions.formatted_code
            revalidating = True
            console.print()
            if not interactive:
                console.print("[dim]Auto-accepting the fix in a non-interactive mode[/dim]")
            console.print("[dim]Resubmitting with fixed code...[/dim]")
            console.print()
        else:
            return None

    if status.problem_id is None:
        console.print("[red]Error:[/red] No problem ID returned")
        return None

    return status.problem_id, code, revalidating
