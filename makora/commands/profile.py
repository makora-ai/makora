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
    KernelEvaluationStatus,
    KernelProfilingDetails,
    ProfileKernelRequest,
    ProfilingMode,
)
from ..models.internal import TargetDevice
from ..web.auth import ensure_authenticated, get_current_credentials
from ..web.conn import open_connection


def _extract_error(details: KernelProfilingDetails) -> str:
    run = details.kernel_profiling_run
    if run is None:
        return "No profiling details returned by server."
    if run.profiling_result and run.profiling_result.error:
        return run.profiling_result.error.message
    if run.compilation_result and run.compilation_result.error:
        return run.compilation_result.error.message
    if run.preparation_result and run.preparation_result.error:
        return run.preparation_result.error.message
    return "Profiling did not complete successfully."


async def cli_profile_async(
    reference_file: Path, optimized_file: Path, device: TargetDevice, url: str | None = None
) -> None:
    creds = get_current_credentials()
    if creds is None:
        raise SystemExit("You need to login first with 'makora login'")

    if not reference_file.exists():
        typer.echo(f"Error: File not found: {reference_file}", err=True)
        raise typer.Exit(1)

    if not optimized_file.exists():
        typer.echo(f"Error: File not found: {optimized_file}", err=True)
        raise typer.Exit(1)

    hardware_provider, hardware_model = device.to_api_device().split(":")

    request = ProfileKernelRequest(
        reference_code=reference_file.read_text(),
        optimized_code=optimized_file.read_text(),
        name=optimized_file.name,
        origin="user",
        extras={},
        mode=ProfilingMode.full,
    )

    typer.echo("Profiling code...")

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
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from e

    run = response.kernel_profiling_run
    if run is None or run.status != KernelEvaluationStatus.COMPLETED:
        typer.echo("\nProfiling failed!", err=True)
        typer.echo(f"\nError: {_extract_error(response)}", err=True)
        raise typer.Exit(1)

    profiling_result = run.profiling_result
    if profiling_result is None:
        typer.echo("\nNo kernel profiling data available.")
        return

    typer.echo("\nProfiling successful!")
    kernels = profiling_result.kernel_info or []
    if not kernels:
        typer.echo("\nNo kernel profiling data available.")
        return

    typer.echo(f"\nProfiled {len(kernels)} kernel(s):\n")
    for i, kernel in enumerate(kernels, 1):
        typer.echo(f"--- Kernel {i} ---")
        if kernel.raw_metrics:
            typer.echo("\nMetrics:")
            for key, value in kernel.raw_metrics.items():
                typer.echo(f"  {key}: {value}")
        if kernel.details_page_text:
            typer.echo("\nDetails:")
            typer.echo(kernel.details_page_text)
        if kernel.nsys_report_text:
            typer.echo("\nNsys Report:")
            typer.echo(kernel.nsys_report_text)
        typer.echo()


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
