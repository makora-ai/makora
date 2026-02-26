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


import textwrap

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from ..utils import get_rich_console
from ..models.openapi import (
    AppEvaluationEvaluationStepBenchmarkingResult,
    LogMessage,
    ProblemValidationTaskStatus,
    StepStatus,
)
from .strings import format_status, format_time, create_styled_table


def create_logs_table(
    logs: list[LogMessage] | None,
    title: str = "Validation Logs",
    max_message_len: int = 200,
) -> Table | None:
    if not logs:
        return None

    table = create_styled_table(title)
    table.add_column("Step", style="cyan", no_wrap=True)
    table.add_column("Status", no_wrap=True)
    table.add_column("Message", overflow="fold")

    for log in logs:
        status_display = format_status(log.type)
        message = log.message or ""
        if len(message) > max_message_len:
            message = message[: max_message_len - 3] + "..."
        table.add_row(log.step, status_display, message)

    return table


def print_logs(
    logs: list[LogMessage] | None,
    console: Console | None = None,
    title: str = "Validation Logs",
) -> None:
    if console is None:
        console = get_rich_console()
    table = create_logs_table(logs, title)
    if table:
        console.print(table)


def create_benchmark_table(
    result: AppEvaluationEvaluationStepBenchmarkingResult,
    title: str = "Benchmark Results",
) -> Table | None:
    if not result.benchmarked:
        return None

    table = create_styled_table(title)
    table.add_column("Metric", style="dim")
    table.add_column("Value", justify="right")

    if result.ref_time is not None:
        table.add_row("Reference (eager)", format_time(result.ref_time, result.ref_time_unit))
    if result.ref_compiled_time is not None:
        table.add_row("Reference (compiled)", format_time(result.ref_compiled_time, result.ref_compiled_time_unit))
    if result.optimized_time is not None:
        if isinstance(result.optimized_time, list):
            for i, t in enumerate(result.optimized_time):
                table.add_row(f"Optimized (shape {i + 1})", format_time(t, result.optimized_time_unit))
        else:
            table.add_row("Optimized", format_time(result.optimized_time, result.optimized_time_unit))

    return table


def print_benchmark_result(
    result: AppEvaluationEvaluationStepBenchmarkingResult | None,
    console: Console | None = None,
    title: str = "Benchmark Results",
) -> None:
    if result is None:
        return

    if console is None:
        console = get_rich_console()

    if not result.benchmarked:
        if result.benchmarking_error:
            console.print(f"[red]Benchmarking failed:[/red] {result.benchmarking_error}")
        return

    table = create_benchmark_table(result, title)
    if table:
        console.print(table)


def print_success_panel(
    message: str,
    console: Console | None = None,
    title: str = "✓ SUCCESS",
) -> None:
    if console is None:
        console = get_rich_console()
    console.print(
        Panel(
            f"[green]{message}[/green]",
            title=f"[green]{title}[/green]",
            border_style="green",
            box=box.ROUNDED,
        )
    )


def print_error_panel(
    message: str,
    console: Console | None = None,
    title: str = "✗ FAILED",
) -> None:
    if console is None:
        console = get_rich_console()
    console.print(
        Panel(
            f"[red]{message}[/red]",
            title=f"[red]{title}[/red]",
            border_style="red",
            box=box.ROUNDED,
        )
    )


def get_last_error(logs: list[LogMessage] | None) -> LogMessage | None:
    if not logs:
        return None
    for log in reversed(logs):
        if log.type == StepStatus.failed and log.message:
            return log
    return None


def print_validation_result(
    status: ProblemValidationTaskStatus,
    *,
    task_id: str | None = None,
    console: Console | None = None,
    show_benchmark: bool = True,
) -> None:
    """Display validation result with consistent formatting."""
    if console is None:
        console = get_rich_console()

    if task_id:
        console.print(f"[dim]Task:[/dim] {task_id}")
        console.print()

    if status.status == StepStatus.completed:
        print_success_panel(
            f"Validation completed successfully!\n\n[dim]Problem ID:[/dim] [cyan]{status.problem_id}[/cyan]",
        )

        if show_benchmark and status.benchmarking_result:
            console.print()
            print_benchmark_result(status.benchmarking_result)

    elif status.status == StepStatus.failed:
        print_error_panel("Validation failed\n\nCheck the error logs below for details.")

        if status.error_logs:
            console.print()
            print_logs(status.error_logs)

        if status.compilation_result and status.compilation_result.compilation_error:
            console.print()
            console.print("[red]Compilation error:[/red]")
            console.print(textwrap.indent(status.compilation_result.compilation_error, "    "))

        if status.preparation_result and status.preparation_result.preparation_error:
            console.print()
            console.print("[red]Preparation error:[/red]")
            console.print(textwrap.indent(status.preparation_result.preparation_error, "    "))

        if status.benchmarking_result and status.benchmarking_result.benchmarking_error:
            console.print()
            console.print("[red]Benchmarking error:[/red]")
            console.print(textwrap.indent(status.benchmarking_result.benchmarking_error, "    "))

    elif status.status == StepStatus.cancelled:
        console.print("[yellow]Validation was cancelled.[/yellow]")

    else:
        console.print(f"[yellow]Unexpected status: {status.status}[/yellow]")
