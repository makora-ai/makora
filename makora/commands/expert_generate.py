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

from ..models.openapi import ExpertGenerateRequest, KernelGenerationResult, KernelLanguage
from ..models.internal import TargetDevice
from ..web.auth import ensure_authenticated, get_current_credentials
from ..web.conn import open_connection


async def cli_expert_generate_async(
    file: Path,
    problem: Path | None,
    device: TargetDevice,
    language: str,
    speedup: float | None,
    url: str | None = None,
) -> None:
    creds = get_current_credentials()
    if creds is None:
        raise SystemExit("You need to login first with 'makora login'")

    if not file.exists():
        typer.echo(f"Error: File not found: {file}", err=True)
        raise typer.Exit(1)
    if problem is not None and not problem.exists():
        typer.echo(f"Error: File not found: {problem}", err=True)
        raise typer.Exit(1)

    kernel_code = file.read_text()
    problem_code = problem.read_text() if problem is not None else None

    try:
        lang = KernelLanguage(language)
    except ValueError:
        typer.echo(
            f"Error: Invalid language '{language}'. Must be one of: {[e.value for e in KernelLanguage]}",
            err=True,
        )
        raise typer.Exit(1) from None

    target_hardware = device.to_api_device()

    request = ExpertGenerateRequest(
        kernel_code=kernel_code,
        reference_code=problem_code,
        language=lang,
        target_hardware=target_hardware,
        current_speedup=speedup,
        benchmark_info=None,
    )

    typer.echo("Generating optimized kernel...", err=True)

    async with open_connection(url) as conn:
        await ensure_authenticated(conn)
        response = await conn.post(
            "additional-tools/expert-generate",
            request,
            reply_format=KernelGenerationResult,
            token=creds.token,
        )

    if response.summary:
        typer.echo(f"Summary: {response.summary}", err=True)

    typer.echo(response.code)


def cli_expert_generate(
    file: Annotated[Path, typer.Argument(help="Path to the kernel file to optimize")],
    device: Annotated[TargetDevice, typer.Option("-d", "--device", help="Device type")],
    problem: Annotated[
        Path | None,
        typer.Option("-p", "--problem", help="Path to the reference/problem file for context"),
    ] = None,
    language: Annotated[str, typer.Option("-l", "--language", help="Programming language")] = "cuda",
    speedup: Annotated[
        float | None,
        typer.Option("--speedup", help="Current speedup vs baseline for context"),
    ] = None,
    url: Annotated[str | None, typer.Option(help="Override the Makora API URL")] = None,
) -> None:
    """Generate an optimized GPU kernel using expert optimization patterns."""
    try:
        asyncio.run(
            cli_expert_generate_async(
                file=file,
                problem=problem,
                device=device,
                language=language,
                speedup=speedup,
                url=url,
            )
        )
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from e
