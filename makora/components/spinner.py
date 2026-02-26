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
from typing import ContextManager, Any

from rich.console import Console

from ..utils import get_rich_console, NO_RICH, dummy_context


def show_spinner(message: str, console: Console | None = None) -> ContextManager[Any]:
    """Context manager for showing a spinner during operations"""

    if console is None:
        console = get_rich_console()

    if bool(NO_RICH.value) or not sys.stdout.isatty():
        console.print(message)
        return dummy_context(None)

    return console.status(f"[cyan]{message}[/cyan]", spinner="dots")
