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


from datetime import datetime, timezone

from rich.table import Table
from rich import box

from ..models.openapi import StepStatus, KernelEvaluationStatus, Unit
from ..models.internal import TargetDevice


STATUS_COLORS = {
    "in_progress": "yellow",
    "completed": "green",
    "not_started": "bright_black",
    "failed": "red",
    "cancelled": "red",
}

STATUS_INDICATORS = {
    "in_progress": "*",
    "completed": "+",
    "not_started": "o",
    "failed": "x",
    "cancelled": "x",
}

STATUS_LABELS = {
    "in_progress": "running",
    "completed": "done",
    "not_started": "queued",
    "failed": "failed",
    "cancelled": "cancelled",
}


DEVICE_LABELS = {
    TargetDevice.H100: "NVIDIA H100",
    TargetDevice.H200: "NVIDIA H200",
    TargetDevice.B200: "NVIDIA B200",
    TargetDevice.L40S: "NVIDIA L40S",
    TargetDevice.MI300X: "AMD MI300X",
    TargetDevice.ADRENO_750: "Snapdragon 8 Gen 3 - GPU",
    TargetDevice.ADRENO_830: "Snapdragon 8 Elite - GPU",
    TargetDevice.HEXAGON_V75: "Snapdragon 8 Gen 3 - NPU",
    TargetDevice.HEXAGON_V79: "Snapdragon 8 Elite - NPU",
}


def format_status(status: StepStatus | KernelEvaluationStatus | str | None) -> str:
    if isinstance(status, (StepStatus, KernelEvaluationStatus)):
        status_str = status.value.lower()
    else:
        status_str = status if status else "[dim]unknown[/dim]"

    color = STATUS_COLORS.get(status_str, "white")
    indicator = STATUS_INDICATORS.get(status_str, "?")
    label = STATUS_LABELS.get(status_str, status_str)
    return f"[{color}]{indicator} {label}[/{color}]"


def format_close_miss_status(best_atol: float | None, best_rtol: float | None) -> str:
    tol_str = f" (a:{best_atol} r:{best_rtol})" if best_atol is not None else ""
    return f"[yellow]~ low precision{tol_str}[/yellow]"


def format_time_ago(dt: datetime | None) -> str:
    if dt is None:
        return "-"
    now = datetime.now(timezone.utc)
    seconds = (now - dt).total_seconds()
    if seconds < 0:
        return "now"
    if seconds < 60:
        return f"{int(seconds)}s ago"
    elif seconds < 3600:
        return f"{int(seconds / 60)}m ago"
    elif seconds < 86400:
        return f"{int(seconds / 3600)}h ago"
    else:
        return f"{int(seconds / 86400)}d ago"


def format_device(device: TargetDevice | str | None) -> str:
    if isinstance(device, TargetDevice):
        return DEVICE_LABELS.get(device, "[dim]unknown[/dim]")

    return device or "-"


def format_time(value: float | None, unit: Unit | None = None) -> str:
    if value is None:
        return "-"
    label = unit.value if unit else "ms"
    return f"{value:.3f} {label}"


def format_speedup(ratio: float | None) -> str:
    if ratio is None:
        return "-"
    if ratio >= 1.0:
        return f"[green]{ratio:.2f}x faster[/green]"
    else:
        slowdown = 1.0 / ratio
        if ratio >= 0.5:
            return f"[yellow]{slowdown:.2f}x slower[/yellow]"
        else:
            return f"[red]{slowdown:.2f}x slower[/red]"


def create_styled_table(title: str | None = None) -> Table:
    """Create a table with consistent styling."""
    return Table(
        title=title,
        box=box.SIMPLE,
        header_style="bold cyan",
        border_style="dim",
        title_style="bold white",
        show_lines=False,
        padding=(0, 1),
    )
