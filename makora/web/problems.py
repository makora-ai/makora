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

import logging
from asyncio import sleep
from datetime import datetime
from typing import Callable

from .conn import Connection
from .auth import get_current_credentials
from ..log import get_logger
from ..models.openapi import (
    ProblemDescriptionCode,
    ProblemCreationRequest,
    ProblemCreationResponse,
    ProblemValidationTaskStatus,
    StepStatus,
)
from ..models.internal import TargetDevice


async def submit_custom_problem(
    conn: Connection, code: str, target_device: TargetDevice, problem_name: str = "", fix: bool = False
) -> str:
    get_logger().info("Submitting custom problem: device={} fix={} code_len={}", target_device.value, fix, len(code))
    creds = get_current_credentials()
    if creds is None:
        raise RuntimeError("User needs to be logged in")

    request = ProblemCreationRequest(
        problem_name=problem_name,
        problem_description_code=ProblemDescriptionCode(code=code),
        enable_fix_suggestions=fix,
        target_hardware=target_device.to_api_device(),
    )

    repl = await conn.post("problems/custom", request, reply_format=ProblemCreationResponse, token=creds.token)
    task_id = str(repl.problem_validation_task_id)
    get_logger().info("Problem submitted: task_id={}", task_id)
    return task_id  ## from uuid


async def poll_validation_task(
    conn: Connection,
    task_id: str,
    poll_interval: float = 1.0,
    on_progress: Callable[[str], None] | None = None,
) -> ProblemValidationTaskStatus:
    creds = get_current_credentials()
    if creds is None:
        raise RuntimeError("User needs to be logged in")

    get_logger().debug("Polling validation task: task_id={}", task_id)
    last_seen_at: datetime | None = None

    while True:
        status = await conn.get(
            f"problems/custom/verification-task/{task_id}",
            reply_format=ProblemValidationTaskStatus,
            token=creds.token,
        )

        logger = get_logger()
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "Validation task status={} error={}",
                status.status,
                {
                    "compilation": (
                        status.compilation_result.compilation_error
                        if status.compilation_result is not None
                        else "(not started)"
                    ),
                    "preparation": (
                        status.preparation_result.preparation_error
                        if status.preparation_result is not None
                        else "(not started)"
                    ),
                    "benchmarking": (
                        status.benchmarking_result.benchmarking_error
                        if status.benchmarking_result is not None
                        else "(not started)"
                    ),
                },
            )

        if status.error_logs and on_progress:
            for log in status.error_logs:
                if last_seen_at and log.created_at and log.created_at.timestamp() <= last_seen_at.timestamp():
                    continue

                if log.type == StepStatus.in_progress:
                    on_progress(log.step)

                if log.created_at and (last_seen_at is None or log.created_at.timestamp() > last_seen_at.timestamp()):
                    last_seen_at = log.created_at

        if status.status in {StepStatus.not_started, StepStatus.in_progress}:
            await sleep(poll_interval)
            continue

        get_logger().info("Validation task finished: status={}", status.status)
        return status


async def submit_and_poll_validation(
    conn: Connection,
    code: str,
    problem_name: str,
    target_device: TargetDevice,
    fix: bool = False,
    poll_interval: float = 1.0,
    on_progress: Callable[[str], None] | None = None,
) -> ProblemValidationTaskStatus:
    task_id = await submit_custom_problem(conn, code, target_device, problem_name, fix)
    status = await poll_validation_task(conn, task_id, poll_interval, on_progress)
    return status
