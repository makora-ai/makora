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
import json
from typing import Annotated

import typer

from ..models.openapi import DocumentSearchRequest, DocumentSearchResult
from ..web.auth import ensure_authenticated, get_current_credentials
from ..web.conn import open_connection


async def cli_document_search_async(query: str, max_entries: int, url: str | None = None) -> None:
    creds = get_current_credentials()
    if creds is None:
        raise SystemExit("You need to login first with 'makora login'")

    query = query.strip()
    if not query:
        typer.echo("Error: Query cannot be empty.", err=True)
        raise typer.Exit(1)

    request = DocumentSearchRequest(query=query, max_entries=max_entries)
    typer.echo("Searching documents...")

    try:
        async with open_connection(url) as conn:
            await ensure_authenticated(conn)
            response = await conn.post(
                "additional-tools/document-search",
                request,
                reply_format=DocumentSearchResult,
                token=creds.token,
            )
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from e

    documents = response.documents
    if not documents:
        typer.echo("No documents found.")
        return

    typer.echo(f"Found {len(documents)} document(s):\n")
    for index, document in enumerate(documents, 1):
        typer.echo(f"--- Document {index} ---")
        typer.echo(f"id: {document.id}")
        if document.score is not None:
            typer.echo(f"score: {document.score}")
        if document.meta:
            typer.echo(f"meta: {json.dumps(document.meta, ensure_ascii=True)}")
        if document.content:
            typer.echo("content:")
            typer.echo(document.content)
        typer.echo()


def cli_document_search(
    query: Annotated[str, typer.Argument(help="Search query string.")],
    max_entries: Annotated[
        int,
        typer.Option("-n", "--max-entries", min=1, max=49, help="Maximum number of documents to return (1-49)."),
    ] = 5,
    url: Annotated[
        str | None,
        typer.Option(
            help="Overwrite the base URL used to communicate with the service. If "
            "not provided will use the one controlled by MAKORA_URL env var. "
            "Use `makora info` for its value."
        ),
    ] = None,
) -> None:
    """Search documents using Makora additional tools."""
    asyncio.run(cli_document_search_async(query=query, max_entries=max_entries, url=url))
