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


from pathlib import Path
from typing import overload, Literal
from datetime import datetime

import yaml
from pydantic import BaseModel, ConfigDict, Field

from .conn import Connection
from ..utils import EnvVar
from ..models.openapi import Tokens, User


USER_FILE = EnvVar("MAKORA_USER_FILE", "~/.makora/user")
AUTH_BASE_URL = EnvVar("MAKORA_AUTH_URL", "https://be.stage.makora.com/api/v1/", hidden=True)


class AuthError(RuntimeError):
    pass


def get_auth_url() -> str:
    url = AUTH_BASE_URL.value
    while url.endswith("/"):
        url = url[:-1]
    return url


class Credentials(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: str
    user: str | None = None
    full_name: str | None = None

    roles: list[str] = Field(exclude=True, default_factory=list)
    validated: bool = Field(exclude=True, default=False)


class LoginPasswordRequest(BaseModel):
    username: str
    password: str


class LoginReply(BaseModel):
    access_token: str
    token_type: str


class TestTokenReply(BaseModel):
    email: str
    is_active: bool
    is_superuser: bool
    full_name: str
    id: str
    has_password: bool
    created_at: datetime
    roles: list[str]


@overload
def get_identity_file(create: Literal[True]) -> Path: ...


@overload
def get_identity_file(create: bool = ...) -> Path | None: ...


def get_identity_file(create: bool = False) -> Path | None:
    filename = USER_FILE.value
    file = Path(filename).expanduser().resolve()
    if not file.exists():
        if not create:
            return None
        file.parent.mkdir(parents=True, exist_ok=True)
        # owner=rw, everyone else none
        file.touch(mode=0o600, exist_ok=False)

    # TODO: consider checking permission?
    return file


def get_current_credentials() -> Credentials | None:
    file = get_identity_file(create=False)
    if file is None:
        return None

    try:
        with file.open("r") as f:
            data = yaml.safe_load(f)

        if not isinstance(data, dict):
            raise TypeError()

        return Credentials(**data)
    except Exception:
        file.unlink()
        return None


def save_or_clear_credentials(creds: Credentials | None) -> None:
    if creds is None:
        file = get_identity_file(create=False)
        if file is not None:
            file.unlink()
    else:
        file = get_identity_file(create=True)
        with file.open("w") as f:
            yaml.safe_dump(creds.model_dump(), f, sort_keys=False)


async def _validate_token(conn: Connection, creds: Credentials, jot: bool) -> bool:
    if creds.validated:
        return True

    try:
        if jot:
            repl_jot = await conn.post(
                f"{get_auth_url()}/login/test-token",
                reply_format=TestTokenReply,
                token=creds.token,
            )
            if not repl_jot.is_active:
                return False
            if creds.user is None:
                creds.user = repl_jot.email
            elif creds.user != repl_jot.email:
                return False

            creds.full_name = repl_jot.full_name
            creds.roles = repl_jot.roles
            return True
        else:
            repl = await conn.get("auth/me", reply_format=User, token=creds.token)
            if creds.user is None:
                creds.user = repl.email
            elif creds.user != repl.email:
                return False

            creds.roles = repl.roles or []
            return True
    except Exception:
        return False
    finally:
        creds.validated = True


def logout() -> None:
    print("Logging out!")
    save_or_clear_credentials(None)


async def login_with_password(conn: Connection, user: str, password: str) -> Credentials:
    creds = get_current_credentials()
    if creds is not None:
        if creds.user == user and await _validate_token(conn, creds, jot=False):
            return creds
        logout()

    repl = await conn.post(
        f"{get_auth_url()}/login/access-token",
        LoginPasswordRequest(username=user, password=password),
        reply_format=LoginReply,
        json=False,
    )
    creds = Credentials(user=user, token=repl.access_token)
    if not await _validate_token(conn, creds, jot=True):
        raise AuthError("Login succeeded but the returned token seems to not work!")

    repl2 = await conn.get("user/tokens", reply_format=Tokens, token=creds.token)
    now = datetime.now().astimezone()
    tokens = sorted(
        repl2.tokens,
        key=(lambda t: ((t.expires_at - now).total_seconds() if t.expires_at else float("inf"))),
        reverse=True,
    )
    if not tokens:
        raise AuthError(
            "User has successfully logged in but no active tokens has been found! "
            f"Please go to: {conn.base_url}tokens and create a new token."
        )

    found_token = False

    for tok in tokens:
        if tok.expires_at and tok.expires_at <= now:
            continue

        creds.token = tok.token
        if await _validate_token(conn, creds, jot=False):
            found_token = True
            break

    if not found_token:
        raise AuthError(
            "All API tokens seem to have expired or otherwise failed to validate. "
            f"Please go to: {conn.base_url}tokens and check a valid token exists."
        )

    save_or_clear_credentials(creds)
    return creds


async def login_with_token(conn: Connection, user: str | None, token: str) -> Credentials:
    creds = get_current_credentials()
    if creds is not None:
        if creds.token == token and await _validate_token(conn, creds, jot=False):
            return creds
        logout()

    creds = Credentials(user=user, token=token)
    if not await _validate_token(conn, creds, jot=False):
        raise AuthError("Provided API token did not validate successfully. Try logging out and in again.")

    save_or_clear_credentials(creds)
    return creds


async def ensure_authenticated(conn: Connection) -> None:
    creds = get_current_credentials()
    if creds is None:
        raise AuthError("You need to login first with 'makora login'")

    if not await _validate_token(conn, creds, jot=False):
        raise AuthError("Currently stored credentials seem to not validate! Please re-login to refresh tokens.")
