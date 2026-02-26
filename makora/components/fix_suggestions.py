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


import difflib

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from ..utils import get_rich_console
from ..models.openapi import FixSuggestion


def print_fix_suggestion(
    fix_suggestion: FixSuggestion,
    original_code: str | None = None,
    console: Console | None = None,
    language: str = "python",
    theme: str = "monokai",
    no_diffs: bool = False,
) -> None:
    if console is None:
        console = get_rich_console()

    console.print()
    console.print("[yellow]Fix Suggestion:[/yellow]")
    console.print(f"{fix_suggestion.summary}")
    console.print()

    if original_code and not no_diffs:
        to_display = "\n".join(
            difflib.unified_diff(
                original_code.splitlines(),
                fix_suggestion.formatted_code.splitlines(),
                fromfile="Original",
                tofile="New",
                lineterm="",
            )
        )
        lexer = "diff"
        line_numbers = False
    else:
        to_display = fix_suggestion.formatted_code
        lexer = language
        line_numbers = True

    syntax = Syntax(
        to_display,
        lexer,
        theme=theme,
        line_numbers=line_numbers,
    )
    console.print(Panel(syntax))
    console.print()


def prompt_accept_fix(console: Console | None = None) -> bool:
    if console is None:
        console = get_rich_console()

    return typer.confirm("Accept this fix?", default=True)
