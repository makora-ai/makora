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


import textwrap
from uuid import UUID

from .errors import Http404, HttpError
from .conn import Connection
from .auth import get_current_credentials
from ..models.internal import TargetDevice, SessionExtra
from ..models.openapi import (
    KernelLanguage,
    PredefinedKernelGenerationRequest,
    AgentSession,
    ThinkingLevel,
    AgentGenerationAttempt,
    AgentSessions,
    AgentSessionSummary,
    SessionKernels,
    EvaluatedKernel,
    UserInstruction,
)


async def new_session(
    conn: Connection,
    problem_id: UUID,
    language: KernelLanguage,
    device: TargetDevice,
    label: str,
    atol: float,
    rtol: float,
    user_prompt: str,
) -> str:
    creds = get_current_credentials()
    if creds is None:
        raise RuntimeError("User needs to be logged in")

    req = PredefinedKernelGenerationRequest(
        label=label,
        problem_id=str(problem_id),
        thinking_level=ThinkingLevel.high,
        backend=language,
        target_hardware=device.to_api_device(),
        user_prompt=user_prompt,
        budget_limit=None,
        atol=atol,
        rtol=rtol,
    )

    repl = await conn.post("agent-session", req, reply_format=AgentSession, token=creds.token)
    return str(repl.id)


async def fetch_session_extra(conn: Connection, session_id: UUID) -> SessionExtra | None:
    """Fetch extra session data from best-attempt endpoint."""
    creds = get_current_credentials()
    if creds is None:
        raise RuntimeError("User needs to be logged in")

    try:
        repl = await conn.get(
            f"agent-session/{session_id}/best-attempt",
            reply_format=AgentGenerationAttempt,
            token=creds.token,
        )
    except Http404:
        return None

    device = repl.request.target_hardware
    bench = repl.evaluation_state.benchmarking_result
    speedup: float | None = None
    if bench is not None:
        ref_compiled = bench.ref_compiled_time
        optimized = bench.optimized_time
        if ref_compiled and optimized and optimized > 0:
            speedup = ref_compiled / optimized

    return SessionExtra(
        speedup=speedup,
        device=TargetDevice.from_api_name(device) if device else None,
    )


async def resolve_session(sessions: list[AgentSessionSummary], session_id: str) -> AgentSessionSummary | None:
    """Find session matching the given ID prefix."""
    matches: list[AgentSessionSummary] = []
    for s in sessions:
        if str(s.id).startswith(session_id):
            matches.append(s)

    if not matches:
        return None
    elif len(matches) > 1:
        session_list = [" * " + str(s.id) for s in matches]
        session_block = textwrap.indent("\n".join(session_list), "    ")
        raise ValueError(f"Session ID prefix: {session_id!r} is matching more than one session:\n" + session_block)

    return matches[0]


async def get_user_sessions(conn: Connection) -> list[AgentSessionSummary]:
    """Fetch a list of sessions belonging to the current user."""
    creds = get_current_credentials()
    if creds is None:
        raise RuntimeError("User needs to be logged in")

    ret: list[AgentSessionSummary] = []

    offset = 0
    while True:
        repl = await conn.get(f"agent-session?offset={offset}", reply_format=AgentSessions, token=creds.token)
        for s in repl.sessions:
            if not s.deleted_at:
                ret.append(s)

        offset += len(repl.sessions)
        if offset >= repl.total:
            break

    return ret


async def get_session_kernels(conn: Connection, session_id: str) -> list[list[EvaluatedKernel]]:
    creds = get_current_credentials()
    if creds is None:
        raise RuntimeError("User needs to be logged in")

    ret: list[list[EvaluatedKernel]] = []

    repl = await conn.get(
        f"agent-session/{session_id}/kernels",
        reply_format=SessionKernels,
        token=creds.token,
    )

    sorted_attempts = sorted(repl.attempts, key=lambda a: a.attempt_number)
    for attempt in sorted_attempts:
        if not attempt.kernels:
            continue

        ret.append(attempt.kernels)

    return ret


async def stop_instruction(conn: Connection, instruction_id: str) -> UserInstruction:
    creds = get_current_credentials()
    if creds is None:
        raise RuntimeError("User needs to be logged in")

    repl = await conn.post(
        f"agent-session/instruction/{instruction_id}/stop",
        reply_format=UserInstruction,
        token=creds.token,
    )
    return repl


async def stop_job(conn: Connection, session_id: UUID) -> bool:
    session = await get_session(conn, str(session_id))
    for attempt in session.generation_attempts:
        if attempt.user_instruction and attempt.stop_requested_at is None:
            try:
                await stop_instruction(conn, str(attempt.user_instruction.id))
                return True
            except HttpError:
                pass
    return False


async def get_session(conn: Connection, session_id: str) -> AgentSession:
    creds = get_current_credentials()
    if creds is None:
        raise RuntimeError("User needs to be logged in")

    repl = await conn.get(
        f"agent-session/{session_id}",
        reply_format=AgentSession,
        token=creds.token,
    )
    return repl
