from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from http.client import responses
from json import JSONDecodeError
from typing import Optional, TYPE_CHECKING, Union

import httpx

from .enums import Message as ResponseMessage
from .enums import Status as ResponseStatus
from .exceptions import (
    HTTPError,
    BadRequest,
    TokenInvalid,
    InvalidCredentials,
    TokenExpiredException,
)
from .logging import logger

if TYPE_CHECKING:
    from .base import EskizSMSBase

BASE_URL = "https://notify.eskiz.uz/api"
API_VERSION_RE = re.compile("API version: ([0-9.]+)")


# full path
def _url(path: str):
    return BASE_URL + path


@dataclass
class _Response:
    status_code: int
    data: Union[dict, str]
    token_expired: bool = False


@dataclass
class _Request:
    method: str
    url: str
    data: dict = None
    params: dict = None
    headers: dict = None


class BaseRequest:

    @staticmethod
    def _prepare_request(method: str, path: str, data: dict = None, params: dict = None, headers: dict = None):
        return _Request(method, _url(path), data, params=params, headers=headers)

    @staticmethod
    def _exception(_response: _Response):
        if isinstance(_response.data, dict):
            status = _response.data.get('status')
            message = _response.data.get('message') or responses[_response.status_code]
        else:
            status = _response.status_code
            message = _response.data
        if status == ResponseStatus.TOKEN_INVALID:
            return TokenInvalid(
                message=message,
                status=status,
                status_code=_response.status_code
            )
        if _response.token_expired:
            return TokenExpiredException(
                message=message,
                status=status,
                status_code=_response.status_code
            )
        if message == ResponseMessage.INVALID_CREDENTIALS:
            return InvalidCredentials(message="Invalid credentials", status_code=_response.status_code)
        return BadRequest(
            message=message,
            status=status,
            status_code=_response.status_code
        )

    @staticmethod
    def _get_authorization_header(token):
        return {
            "Authorization": f"Bearer {token}"
        }

    def _request(self, _request: _Request):
        try:
            with httpx.Client() as client:
                response = client.request(**asdict(_request))
                return self._check_response(response)
        except httpx.HTTPError as e:
            raise HTTPError(message=str(e))

    async def _a_request(self, _request: _Request):
        try:
            async with httpx.AsyncClient() as client:
                return self._check_response(await client.request(**asdict(_request)))
        except httpx.HTTPError as e:
            raise HTTPError(message=str(e))

    def _check_response(self, r: httpx.Response) -> _Response:
        content_type = r.headers.get('content-type', 'application/json; charset=utf-8').split(';')[0]
        response: Optional[_Response] = None
        if content_type == 'application/json':
            try:
                response = _Response(status_code=r.status_code, data=r.json())
            except JSONDecodeError:
                response = _Response(r.status_code, data=r.text)
        elif content_type == 'text/csv':
            response = _Response(status_code=r.status_code, data=r.text)
        else:
            api_version = API_VERSION_RE.search(r.text)
            if api_version:
                response = _Response(status_code=r.status_code, data={'api_version': api_version.groups()[0]})

        if response is None:
            response = _Response(status_code=r.status_code, data={'message': responses[r.status_code]})
        logger.debug(f"Eskiz request status_code={response.status_code} body={response.data}...")
        if response.status_code == 401:
            if response.data.get('message') == ResponseMessage.EXPIRED_TOKEN:
                response.token_expired = True
                return response

        if response.status_code not in [200, 201]:
            raise self._exception(response)

        return response


class Request(BaseRequest):
    def __init__(self, eskiz: EskizSMSBase):
        self._eskiz = eskiz

    def __call__(self, method: str, path: str, payload: dict = None, params: dict = None):
        _request = self._prepare_request(
            method,
            path,
            data=self._prepare_payload(payload),
            params=params,
        )
        if getattr(self._eskiz, 'is_async', False):  # noqa
            return self.async_request(_request)
        return self.request(_request)

    async def async_request(self, _request: _Request) -> dict:
        _request.headers = self._get_authorization_header(await self._eskiz.token.get())
        response = await self._a_request(_request)
        if response.token_expired and self._eskiz.token.auto_update:
            logger.debug("Refreshing the token")
            _request.headers = self._get_authorization_header(await self._eskiz.token.get(get_new=True))
            response = await self._a_request(_request)
        if response.status_code not in [200, 201]:
            raise self._exception(response)
        return response.data

    def request(self, _request: _Request) -> dict:
        _request.headers = self._get_authorization_header(self._eskiz.token.get())
        response = self._request(_request)
        if response.token_expired and self._eskiz.token.auto_update:
            logger.debug("Refreshing eskiz token")
            _request.headers = self._get_authorization_header(self._eskiz.token.get(get_new=True))
            response = self._request(_request)
        if response.status_code not in [200, 201]:
            raise self._exception(response)
        return response.data

    @staticmethod
    def _prepare_payload(payload: dict):
        payload = payload or {}
        if 'from_whom' in payload:
            payload['from'] = payload.pop('from_whom')
        if 'mobile_phone' in payload:
            payload['mobile_phone'] = payload['mobile_phone'].replace("+", "").replace(" ", "")
        return payload

    def post(self, path: str, payload: dict = None, params: dict = None):
        return self("POST", path, payload, params)

    def put(self, path: str, payload: dict = None, params: dict = None):
        return self("PUT", path, payload, params)

    def get(self, path: str, payload: Optional[dict] = None, params: dict = None):
        return self("GET", path, payload, params)

    def delete(self, path: str, payload: dict = None, params: dict = None):
        return self("DELETE", path, payload, params)

    def patch(self, path: str, payload: dict = None, params: dict = None):
        return self("PATCH", path, payload, params)
