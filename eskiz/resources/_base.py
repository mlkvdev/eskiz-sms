"""Executors and resource base — the only place that touches the transport.

The executor takes a :class:`RequestPlan` and runs it, wrapping
:class:`pydantic.ValidationError` from any plan parser as
:class:`BadRequest` so the SDK's exception hierarchy can't be bypassed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from pydantic import ValidationError as PydanticValidationError

from eskiz._protocol import RequestPlan
from eskiz.exceptions import BadRequest
from eskiz.transport.base import RawResponse, raise_for_response

if TYPE_CHECKING:
    from eskiz.config import Config
    from eskiz.transport.aio import AsyncTransport
    from eskiz.transport.sync import SyncTransport

T = TypeVar("T")

_MAX_PARSE_ERROR = 200


def _safe_parse(plan: RequestPlan[T], response: RawResponse) -> T:
    try:
        return plan.parse(response)
    except PydanticValidationError as exc:
        msg = str(exc)
        if len(msg) > _MAX_PARSE_ERROR:
            msg = msg[:_MAX_PARSE_ERROR] + "..."
        raise BadRequest(
            f"Could not parse response: {msg}", status_code=response.status_code
        ) from exc


class SyncExecutor:
    """Runs :class:`RequestPlan` instances against a :class:`SyncTransport`."""

    __slots__ = ("_transport",)

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def run(self, plan: RequestPlan[T]) -> T:
        response = self._transport.request(
            plan.method, plan.path, data=plan.data, json=plan.json, params=plan.params
        )
        return _safe_parse(plan, response)

    def run_unauth(self, plan: RequestPlan[T]) -> T:
        response = self._transport.request_unauth(
            plan.method, plan.path, data=plan.data, json=plan.json, params=plan.params
        )
        return _safe_parse(plan, response)

    def run_with_token(self, plan: RequestPlan[T], token: str) -> T:
        response = self._transport.request_raw(
            plan.method,
            plan.path,
            token=token,
            data=plan.data,
            json=plan.json,
            params=plan.params,
        )
        raise_for_response(response)
        return _safe_parse(plan, response)


class AsyncExecutor:
    """Runs :class:`RequestPlan` instances against an :class:`AsyncTransport`."""

    __slots__ = ("_transport",)

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def run(self, plan: RequestPlan[T]) -> T:
        response = await self._transport.request(
            plan.method, plan.path, data=plan.data, json=plan.json, params=plan.params
        )
        return _safe_parse(plan, response)

    async def run_unauth(self, plan: RequestPlan[T]) -> T:
        response = await self._transport.request_unauth(
            plan.method, plan.path, data=plan.data, json=plan.json, params=plan.params
        )
        return _safe_parse(plan, response)

    async def run_with_token(self, plan: RequestPlan[T], token: str) -> T:
        response = await self._transport.request_raw(
            plan.method,
            plan.path,
            token=token,
            data=plan.data,
            json=plan.json,
            params=plan.params,
        )
        raise_for_response(response)
        return _safe_parse(plan, response)


class _SyncResource:
    """Base for sync resources — holds executor and config."""

    __slots__ = ("_config", "_exec")

    def __init__(self, executor: SyncExecutor, config: Config) -> None:
        self._exec = executor
        self._config = config


class _AsyncResource:
    """Base for async resources — holds executor and config."""

    __slots__ = ("_config", "_exec")

    def __init__(self, executor: AsyncExecutor, config: Config) -> None:
        self._exec = executor
        self._config = config
