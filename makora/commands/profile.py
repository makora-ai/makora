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

from ..models.openapi import (
    AppEvaluationEvaluationCompilationResult,
    AppEvaluationEvaluationPreparationResult,
    EvalRefMode,
    KernelProfile,
    KernelEvaluationStatus,
    KernelProfilingDetails,
    OrchestrationResult,
    ProfileKernelRequest,
    ProfilingResult,
    ProfilingMode,
)
from ..models.internal import TargetDevice
from ..web.auth import ensure_authenticated, get_current_credentials
from ..web.conn import open_connection
from ..log import get_logger
from ..utils import get_rich_console, extract_stage_error, format_stage_error


ProfilingStageResult = (
    OrchestrationResult
    | AppEvaluationEvaluationPreparationResult
    | AppEvaluationEvaluationCompilationResult
    | ProfilingResult
)


def _stage_has_failed(result: ProfilingStageResult | None) -> bool:
    return result is not None and (result.error is not None or result.successful is False)


def _kernel_text_sections(kernel: KernelProfile) -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []
    seen: set[str] = set()

    for label, value in [
        ("Details", kernel.details_page_text),
        ("Profiler Details", kernel.details_page_all_text),
        ("Source View", kernel.source_page_text),
        ("CUDA Source", kernel.source_cuda_code),
        ("SASS Source", kernel.source_sass_code),
        ("Annotated Source", kernel.annotated_source_file),
        ("Nsys Report", kernel.nsys_report_text),
        ("Torch Trace", kernel.torch_trace),
    ]:
        text = (value or "").strip()
        if text and text not in seen:
            sections.append((label, text))
            seen.add(text)

    return sections


def _kernel_has_output(kernel: KernelProfile) -> bool:
    return bool(kernel.raw_metrics) or bool(_kernel_text_sections(kernel))


def _profiling_detected_no_kernels(result: ProfilingResult | None) -> bool:
    if result is None:
        return False

    stdout = result.stdout or ""
    if "No known kernels exist in the user's module" in stdout:
        return True
    if "Kernel names: []" in stdout:
        return True

    return False


def _extract_no_kernel_error(result: ProfilingResult) -> str:
    return f"{format_stage_error('profiling', result)}\n  Error: No kernels were detected to profile."


def _extract_error(details: KernelProfilingDetails) -> str:
    run = details.kernel_profiling_run
    if run is None:
        return "No profiling details returned by server."

    if _profiling_detected_no_kernels(run.profiling_result):
        assert run.profiling_result is not None
        return _extract_no_kernel_error(run.profiling_result)

    stages: list[tuple[str, ProfilingStageResult | None]] = [
        ("orchestration", run.orchestration_result),
        ("preparation", run.preparation_result),
        ("compilation", run.compilation_result),
        ("profiling", run.profiling_result),
    ]
    return extract_stage_error(stages, f"Profiling did not complete successfully (status={run.status}).")


async def cli_profile_async(
    reference_file: Path, optimized_file: Path, device: TargetDevice, url: str | None = None
) -> None:
    get_logger().info(
        "profile: reference={} optimized={} device={}",
        reference_file,
        optimized_file,
        device.value,
    )
    console = get_rich_console()
    creds = get_current_credentials()
    if creds is None:
        console.print("[red]You need to login first with 'makora login'[/red]")
        raise typer.Exit(1)

    if not reference_file.exists():
        console.print(f"[red]Error:[/red] File not found: {reference_file}")
        raise typer.Exit(1)

    if not optimized_file.exists():
        console.print(f"[red]Error:[/red] File not found: {optimized_file}")
        raise typer.Exit(1)

    hardware_provider, hardware_model = device.to_api_device().split(":")
    get_logger().debug("Parsed device: provider={} model={}", hardware_provider, hardware_model)

    request = ProfileKernelRequest(
        reference_code=reference_file.read_text(),
        optimized_code=optimized_file.read_text(),
        name=optimized_file.name,
        origin="user",
        extras={},
        ref_modes=[EvalRefMode.EAGER, EvalRefMode.COMPILED],
        rtol=1e-3,
        atol=1e-3,
        mode=ProfilingMode.full,
    )

    console.print("[cyan]Profiling code...[/cyan]")

    try:
        async with open_connection(url) as conn:
            await ensure_authenticated(conn)
            response = await conn.post(
                f"kernel-evaluation/profile/{hardware_provider}/{hardware_model}",
                request,
                reply_format=KernelProfilingDetails,
                token=creds.token,
            )
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e

    run = response.kernel_profiling_run
    get_logger().debug("Profiling response: run_status={}", run.status if run else None)
    stages: list[ProfilingStageResult | None] = []
    if run is not None:
        stages = [
            run.orchestration_result,
            run.preparation_result,
            run.compilation_result,
            run.profiling_result,
        ]

    if (
        run is None
        or run.status != KernelEvaluationStatus.COMPLETED
        or any(_stage_has_failed(stage) for stage in stages)
        or _profiling_detected_no_kernels(run.profiling_result if run is not None else None)
    ):
        get_logger().debug("Profiling failed: {}", _extract_error(response))
        console.print("\n[red]✗ Profiling failed![/red]")
        console.print(f"[red]Error:[/red] {_extract_error(response)}")
        raise typer.Exit(1)

    profiling_result = run.profiling_result
    if profiling_result is None:
        console.print("[dim]No kernel profiling data available.[/dim]")
        return

    console.print("\n[green]✓ Profiling successful![/green]")
    kernels = profiling_result.kernel_info or []
    get_logger().debug("Profiling result: {} kernels", len(kernels))
    if not kernels:
        console.print("[dim]No kernel profiling data available.[/dim]")
        return

    kernels_with_output = [kernel for kernel in kernels if _kernel_has_output(kernel)]
    get_logger().info("{} of {} kernels have output", len(kernels_with_output), len(kernels))

    if not kernels_with_output:
        console.print("\n[bold]Profiler Output:[/bold]")
        if profiling_result.stdout:
            console.print(profiling_result.stdout.rstrip(), highlight=False)
        if profiling_result.logs:
            console.print("\n[bold]Logs:[/bold]")
            for log in profiling_result.logs:
                if log.timestamp:
                    console.print(f"  [dim][{log.timestamp}][/dim] {log.message}")
                else:
                    console.print(f"  {log.message}")
        return

    console.print(f"\n[bold]Profiled {len(kernels_with_output)} kernel(s):[/bold]\n")
    for i, kernel in enumerate(kernels_with_output, 1):
        console.print(f"[bold cyan]─── Kernel {i} ───[/bold cyan]")
        if kernel.raw_metrics:
            console.print("\n[bold]Metrics:[/bold]")
            for key, value in sorted(kernel.raw_metrics.items()):
                console.print(f"  [dim]{key}:[/dim] {value}")
        for title, text in _kernel_text_sections(kernel):
            console.print(f"\n[bold]{title}:[/bold]")
            console.print(text, highlight=False, markup=False)
        console.print()


def cli_profile(
    reference_file: Annotated[Path, typer.Argument(help="Path to file containing reference code.")],
    optimized_file: Annotated[Path, typer.Argument(help="Path to file containing optimized code.")],
    device: Annotated[TargetDevice, typer.Option("-d", "--device", help="Device type.")],
    url: Annotated[
        str | None,
        typer.Option(
            help="Overwrite the base URL used to communicate with the service. If "
            "not provided will use the one controlled by MAKORA_URL env var. "
            "Use `makora info` for its value."
        ),
    ] = None,
) -> None:
    """Profile code using the remote Makora evaluator."""
    asyncio.run(cli_profile_async(reference_file=reference_file, optimized_file=optimized_file, device=device, url=url))
