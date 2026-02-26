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


from types import TracebackType
from typing import TypeVar, Any
from typing_extensions import Self

import aiohttp
from pydantic import BaseModel

from ..config import get_generate_base_url
from .errors import map_errors


T = TypeVar("T", bound=BaseModel)


class Connection:
    def __init__(self, base_url: str) -> None:
        if not base_url:
            raise ValueError("empty base_url")
        if not base_url.endswith("/"):
            base_url += "/"

        self.base_url = base_url
        self.client: aiohttp.ClientSession | None = None

    async def __aenter__(self) -> Self:
        client = aiohttp.ClientSession(base_url=self.base_url, raise_for_status=False)
        await client.__aenter__()
        self.client = client
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        assert self.client is not None
        await self.client.__aexit__(exc_type, exc_val, exc_tb)
        self.client = None
        return

    async def _reconnect(self) -> None:
        if self.client is not None:
            await self.client.__aexit__(None, None, None)
            self.client = None
        client = aiohttp.ClientSession(base_url=self.base_url, raise_for_status=False)
        await client.__aenter__()
        self.client = client

    async def post(
        self,
        endpoint: str,
        *payload: BaseModel,
        reply_format: type[T],
        token: str | None = None,
        json: bool = True,
    ) -> T:
        if self.client is None:
            raise ValueError("Connection has not been opened or has been already closed")

        kwargs = {}
        if token is not None:
            kwargs["headers"] = {"Authorization": f"Bearer {token}"}

        if payload:
            params: dict[str, Any] = {}
            for p in payload:
                params.update(p.model_dump(mode="json"))

            if json:
                kwargs["json"] = params
            else:
                kwargs["data"] = params

        try:
            async with self.client.post(
                endpoint,
                **kwargs,  # type: ignore[arg-type,unused-ignore]
            ) as resp:
                await map_errors(resp)
                repl = await resp.text()
                return reply_format.model_validate_json(repl)
        except aiohttp.ServerDisconnectedError:
            await self._reconnect()
            async with self.client.post(
                endpoint,
                **kwargs,  # type: ignore[arg-type,unused-ignore]
            ) as resp:
                await map_errors(resp)
                repl = await resp.text()
                return reply_format.model_validate_json(repl)

    async def get(self, endpoint: str, reply_format: type[T], token: str | None = None) -> T:
        if self.client is None:
            raise ValueError("Connection has not been opened or has been already closed")

        headers: dict[str, str] = {}
        if token is not None:
            headers["Authorization"] = f"Bearer {token}"

        try:
            async with self.client.get(endpoint, headers=headers) as resp:
                await map_errors(resp)
                repl = await resp.text()
                return reply_format.model_validate_json(repl)
        except aiohttp.ServerDisconnectedError:
            await self._reconnect()
            async with self.client.get(endpoint, headers=headers) as resp:
                await map_errors(resp)
                repl = await resp.text()
                return reply_format.model_validate_json(repl)


def open_connection(url: str | None = None) -> Connection:
    return Connection(get_generate_base_url(url))
