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
from ..log import get_logger
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
    get_logger().info(
        "Creating session: problem_id={} language={} device={} atol={} rtol={}",
        problem_id,
        language.value,
        device.value,
        atol,
        rtol,
    )
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
        agent_definition_id=None,
    )

    repl = await conn.post("agent-session", req, reply_format=AgentSession, token=creds.token)
    get_logger().info("Session created: id={}", repl.id)
    return str(repl.id)


async def fetch_session_extra(conn: Connection, session_id: UUID) -> SessionExtra | None:
    """Fetch extra session data from best-attempt endpoint."""
    get_logger().debug("Fetching extra data for session={}", session_id)
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
        get_logger().debug("No best attempt found for session={}", session_id)
        return None

    device = repl.request.target_hardware
    bench = repl.evaluation_state.benchmarking_result
    speedup: float | None = None
    if bench is not None:
        ref_compiled = bench.ref_compiled_time
        optimized = bench.optimized_time
        if ref_compiled and optimized and optimized > 0:
            speedup = ref_compiled / optimized

    get_logger().debug("Session extra: device={} speedup={}", device, speedup)
    return SessionExtra(
        speedup=speedup,
        device=TargetDevice.from_api_name(device) if device else None,
    )


async def resolve_session(sessions: list[AgentSessionSummary], session_id: str) -> AgentSessionSummary | None:
    """Find session matching the given ID prefix."""
    get_logger().debug("Resolving session prefix={} from {} sessions", session_id, len(sessions))
    matches: list[AgentSessionSummary] = []
    for s in sessions:
        if str(s.id).startswith(session_id):
            matches.append(s)

    if not matches:
        get_logger().debug("No sessions match prefix={}", session_id)
        return None
    elif len(matches) > 1:
        get_logger().warning("Ambiguous prefix={}: {} matches", session_id, len(matches))
        session_list = [" * " + str(s.id) for s in matches]
        session_block = textwrap.indent("\n".join(session_list), "    ")
        raise ValueError(f"Session ID prefix: {session_id!r} is matching more than one session:\n" + session_block)

    get_logger().debug("Resolved to session={}", matches[0].id)
    return matches[0]


async def get_user_sessions(conn: Connection) -> list[AgentSessionSummary]:
    """Fetch a list of sessions belonging to the current user."""
    get_logger().debug("Fetching user sessions")
    creds = get_current_credentials()
    if creds is None:
        raise RuntimeError("User needs to be logged in")

    ret: list[AgentSessionSummary] = []

    offset = 0
    while True:
        repl = await conn.get(f"agent-session?offset={offset}", reply_format=AgentSessions, token=creds.token)
        get_logger().debug("Sessions page: offset={} got={} total={}", offset, len(repl.sessions), repl.total)
        for s in repl.sessions:
            if not s.deleted_at:
                ret.append(s)

        offset += len(repl.sessions)
        if offset >= repl.total:
            break

    get_logger().debug("Fetched {} active sessions", len(ret))
    return ret


async def get_session_kernels(conn: Connection, session_id: str) -> list[list[EvaluatedKernel]]:
    get_logger().debug("Fetching kernels for session={}", session_id)
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

    total = sum(len(a) for a in ret)
    get_logger().debug("Fetched {} kernels across {} attempts for session={}", total, len(ret), session_id)
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
    get_logger().info("Stopping job: session_id={}", session_id)
    session = await get_session(conn, str(session_id))
    for attempt in session.generation_attempts:
        if attempt.user_instruction and attempt.stop_requested_at is None:
            instruction_id = str(attempt.user_instruction.id)
            get_logger().debug("Stopping instruction={}", instruction_id)
            try:
                await stop_instruction(conn, instruction_id)
                get_logger().info("Instruction stopped: {}", instruction_id)
                return True
            except HttpError as exc:
                get_logger().warning("Failed to stop instruction={}: {}", instruction_id, exc)
    get_logger().debug("No active instruction found for session={}", session_id)
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
