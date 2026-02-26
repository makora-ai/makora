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


from typing import Any

from aiohttp import ClientResponse


class HttpError(ValueError):
    def __init__(self, code: int, url: str, *args: Any) -> None:
        super().__init__(code, url, *args)
        self.code = code
        self.url = url


class Http404(HttpError):
    def __init__(self, url: str, *args: Any) -> None:
        super().__init__(404, url, *args)


async def map_errors(resp: ClientResponse) -> None:
    if resp.status in {200, 201}:
        return

    if resp.content_type == "application/json":
        data = await resp.json()
    else:
        data = await resp.text()

    match resp.status:
        case 404:
            raise Http404(str(resp.real_url), data)
        case _:
            raise HttpError(resp.status, str(resp.real_url), data)
