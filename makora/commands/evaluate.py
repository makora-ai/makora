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
    AppEvaluationEvaluationBenchmarkingResult,
    AppEvaluationEvaluationCompilationResult,
    AppEvaluationEvaluationPreparationResult,
    EvalRefMode,
    EvaluateKernelRequest,
    KernelEvaluationDetails,
    KernelEvaluationStatus,
    OrchestrationResult,
    Unit,
    ValidationResult,
)
from ..models.internal import TargetDevice
from ..web.auth import ensure_authenticated, get_current_credentials
from ..web.conn import open_connection
from ..log import get_logger
from ..utils import get_rich_console, extract_stage_error


EvaluationStageResult = (
    OrchestrationResult
    | AppEvaluationEvaluationPreparationResult
    | AppEvaluationEvaluationCompilationResult
    | ValidationResult
    | AppEvaluationEvaluationBenchmarkingResult
)


def _extract_error(details: KernelEvaluationDetails) -> str:
    evaluation = details.evaluation
    if evaluation is None:
        return "No evaluation details returned by server."

    stages: list[tuple[str, EvaluationStageResult | None]] = [
        ("orchestration", evaluation.orchestration_result),
        ("preparation", evaluation.preparation_result),
        ("compilation", evaluation.compilation_result),
        ("validation", evaluation.validation_result),
        ("benchmarking", evaluation.benchmarking_result),
    ]
    return extract_stage_error(stages, f"Evaluation did not complete successfully (status={evaluation.status}).")


async def cli_evaluate_async(
    reference_file: Path,
    optimized_file: Path,
    device: TargetDevice,
    ref_modes: list[EvalRefMode] | None = None,
    url: str | None = None,
    atol: float = 1e-3,
    rtol: float = 1e-3,
) -> None:
    if ref_modes is None:
        ref_modes = [EvalRefMode.EAGER, EvalRefMode.COMPILED]
    get_logger().info(
        "evaluate: reference={} optimized={} device={}",
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

    ref_code = reference_file.read_text()
    opt_code = optimized_file.read_text()
    get_logger().debug("File sizes: reference={} bytes optimized={} bytes", len(ref_code), len(opt_code))

    request = EvaluateKernelRequest(
        reference_code=ref_code,
        optimized_code=opt_code,
        name=optimized_file.name,
        origin="user",
        extras={},
        ref_modes=ref_modes,
        atol=atol,
        rtol=rtol,
    )

    console.print("[cyan]Evaluating code...[/cyan]")

    try:
        async with open_connection(url) as conn:
            await ensure_authenticated(conn)
            response = await conn.post(
                f"kernel-evaluation/evaluation/{hardware_provider}/{hardware_model}",
                request,
                reply_format=KernelEvaluationDetails,
                token=creds.token,
            )
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e

    evaluation = response.evaluation
    get_logger().debug(
        "Evaluation response: status={} has_evaluation={}",
        evaluation.status if evaluation else None,
        evaluation is not None,
    )
    if evaluation is None or evaluation.status != KernelEvaluationStatus.COMPLETED:
        console.print("\n[red]✗ Evaluation failed![/red]")
        console.print(f"Error: {_extract_error(response)}")
        raise typer.Exit(1)

    optimized_time = evaluation.optimized_time
    reference_time = evaluation.reference_time
    speedup = evaluation.speedup
    get_logger().info(
        "Evaluation results: reference_time={} optimized_time={} speedup={}",
        reference_time,
        optimized_time,
        speedup,
    )

    # Default to milliseconds when unit is absent.
    unit = evaluation.optimized_time_unit or evaluation.reference_time_unit or Unit.ms
    unit_value = unit.value

    console.print("\n[green]✓ Evaluation successful![/green]")
    console.print("\n[bold]Benchmark Results:[/bold]")
    if reference_time is not None:
        console.print(f"[dim]Reference time:[/dim] [cyan]{reference_time:.6f} {unit_value}[/cyan]")
    if optimized_time is not None:
        console.print(f"[dim]Solution time:[/dim]  [cyan]{optimized_time:.6f} {unit_value}[/cyan]")
    if speedup is not None:
        console.print(f"[dim]Speedup:[/dim]        [green bold]{speedup:.2f}x[/green bold]")

    benchmarking_result = evaluation.benchmarking_result
    if benchmarking_result is not None:
        user_times = benchmarking_result.user_times
        ref_times = benchmarking_result.ref_times

        ref_timings: list[float] = []
        if ref_times and ref_times[0].results:
            ref_timings = [t.kernel.mean for t in ref_times[0].results]

        if user_times and len(user_times) > 0:
            console.print("\n[bold]Per-input timings:[/bold]")
            for i, timing in enumerate(user_times):
                shape_unit = timing.kernel.unit.value if timing.kernel.unit else unit_value
                user_time = timing.kernel.mean
                ref_time_str = f"{ref_timings[i]:.6f}" if i < len(ref_timings) else "-"
                console.print(
                    f"  [dim]Input {i}:[/dim] [cyan]{user_time:.6f}[/cyan] [dim]ref:[/dim] [cyan]{ref_time_str}[/cyan] {shape_unit}"
                )


def cli_evaluate(
    reference_file: Annotated[Path, typer.Argument(help="Path to file containing reference code.")],
    optimized_file: Annotated[Path, typer.Argument(help="Path to file containing optimized code.")],
    device: Annotated[TargetDevice, typer.Option("-d", "--device", help="Device type.")],
    ref_modes: Annotated[
        list[EvalRefMode] | None,
        typer.Option(
            "--ref-mode",
            help="Reference evaluation mode(s). Can be specified multiple times. "
            "Options: EAGER, COMPILED, REDUCE_OVERHEAD, MAX_AUTOTUNE, MAX_AUTOTUNE_NO_CUDAGRAPHS.",
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
    atol: Annotated[float, typer.Option(help="Absolute tolerance to use when validating generated solutions.")] = 1e-3,
    rtol: Annotated[float, typer.Option(help="Relative tolerance to use when validating generated solutions.")] = 1e-3,
) -> None:
    """Evaluate code against a reference implementation on remote hardware."""
    asyncio.run(
        cli_evaluate_async(
            reference_file=reference_file,
            optimized_file=optimized_file,
            device=device,
            ref_modes=ref_modes,
            url=url,
            atol=atol,
            rtol=rtol,
        )
    )
