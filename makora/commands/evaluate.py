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

from ..models.openapi import EvaluateKernelRequest, KernelEvaluationDetails, KernelEvaluationStatus, Unit
from ..models.internal import TargetDevice
from ..web.auth import ensure_authenticated, get_current_credentials
from ..web.conn import open_connection


async def cli_evaluate_async(
    reference_file: Path,
    optimized_file: Path,
    device: TargetDevice,
    url: str | None = None,
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

    request = EvaluateKernelRequest(
        reference_code=reference_file.read_text(),
        optimized_code=optimized_file.read_text(),
        name=optimized_file.name,
        origin="user",
        extras={},
    )

    typer.echo("Evaluating code...")

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
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from e

    evaluation = response.evaluation
    if evaluation is None or evaluation.status != KernelEvaluationStatus.COMPLETED:
        typer.echo("\n✗ Evaluation failed!", err=True)
        raise typer.Exit(1)

    optimized_time = evaluation.optimized_time
    reference_time = evaluation.reference_time
    speedup = evaluation.speedup

    # Default to milliseconds when unit is absent.
    unit = evaluation.optimized_time_unit or evaluation.reference_time_unit or Unit.ms
    unit_value = unit.value

    typer.echo("\n✓ Evaluation successful!")
    typer.echo("\nBenchmark Results:")
    if reference_time is not None:
        typer.echo(f"  Reference time: {reference_time:.6f} {unit_value}")
    if optimized_time is not None:
        typer.echo(f"  Solution time:  {optimized_time:.6f} {unit_value}")
    if speedup is not None:
        typer.echo(f"  Speedup:        {speedup:.2f}x")


def cli_evaluate(
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
    """Evaluate code against a reference implementation on remote hardware."""
    asyncio.run(
        cli_evaluate_async(reference_file=reference_file, optimized_file=optimized_file, device=device, url=url)
    )
