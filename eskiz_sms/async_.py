from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Literal

from .base import EskizSMSBase
from .exceptions import ContactNotFound
from .types import Response, Contact, User, ContactCreated

__all__ = ['EskizSMS']


class EskizSMS(EskizSMSBase, async_=True):
    @property
    async def user(self) -> Optional[User]:
        self._user = await self._user_data()
        return self._user

    async def _user_data(self) -> Optional[User]:
        response = await self._request.get("/auth/user")
        if 'data' in response:
            response = response['data']
        return User(**response)

    async def add_contact(self, name: str, email: str, group: str, mobile_phone: str) -> ContactCreated:
        response = await self._request.post(
            "/contact",
            payload={
                "name": name,
                "email": email,
                "group": group,
                "mobile_phone": str(mobile_phone),
            })
        return ContactCreated(response['data'])

    async def update_contact(self, contact_id: int, name: str, group: str, mobile_phone: str) -> Optional[Contact]:
        response = await self._request.put(
            f"/contact/{contact_id}",
            payload={
                "name": name,
                "group": group,
                "mobile_phone": str(mobile_phone),
            })
        if response and isinstance(response, list):
            return Contact(**response[0])

    async def get_contact(self, contact_id: int, raise_exception=False) -> Optional[Contact]:
        response = await self._request.get(f"/contact/{contact_id}")
        if not response:
            if raise_exception:
                raise ContactNotFound
            return None
        return Contact(**response[0])

    async def delete_contact(self, contact_id: int) -> Response:
        response = await self._request.delete(f"/contact/{contact_id}")
        return Response(**response)

    async def send_sms(self, mobile_phone: str, message: str, from_whom: str = '4546',
                       callback_url: str = None) -> Response:

        payload = {
            "mobile_phone": str(mobile_phone),
            "message": message,
            "from_whom": from_whom,
        }
        callback_url = self._get_callback_url(callback_url)
        if callback_url:
            payload['callback_url'] = callback_url
        response = await self._request.post("/message/sms/send", payload=payload)
        return Response(**response)

    async def send_global_sms(self, mobile_phone: str, message: str, country_code: str,
                              callback_url: str = None, unicode: str = "0") -> Response:
        payload = {
            "mobile_phone": str(mobile_phone),
            "message": message,
            "country_code": country_code,
            "unicode": unicode
        }
        callback_url = self._get_callback_url(callback_url)
        if callback_url:
            payload['callback_url'] = callback_url
        response = await self._request.post("/message/sms/send-global", payload=payload)
        return Response(**response)

    async def send_batch(self, *, messages: List[dict], from_whom: str = "4546", dispatch_id: int) -> Response:
        response = await self._request.post(
            "/message/sms/send-batch",
            payload={
                "messages": [
                    {
                        "user_sms_id": message["user_sms_id"],
                        "to": str(message["to"]),
                        "text": message["text"]
                    } for message in messages
                ],
                "from_whom": from_whom,
                "dispatch_id": dispatch_id
            })
        return Response(**response)

    async def get_user_messages(self, from_date: str, to_date: str) -> Response:
        user = await self.user
        response = await self._request.get(
            "/message/sms/get-user-messages",
            payload={
                "from_date": from_date,
                "to_date": to_date,
                "user_id": user.id
            }
        )
        return Response(**response)

    async def get_user_messages_by_dispatch(self, dispatch_id: int) -> Response:
        user = await self.user
        response = await self._request.get(
            "/message/sms/get-user-messages-by-dispatch",
            payload={
                "dispatch_id": dispatch_id,
                "user_id": user.id
            })
        return Response(**response)

    async def get_dispatch_status(self, dispatch_id: int) -> Response:
        user = await self.user
        response = self._request.get(
            "/message/sms/get-dispatch-status",
            payload={
                "dispatch_id": dispatch_id,
                "user_id": user.id
            })
        return Response(**response)

    async def create_template(self, name: str, text: str) -> Response:
        response = await self._request.post(
            "/template",
            payload={
                "name": name,
                "text": text,
            })
        return Response(**response)

    async def update_template(self, template_id: int, name: str, text: str) -> Response:
        response = await self._request.put(
            f"/template/{template_id}",
            payload={
                "name": name,
                "text": text,
            }
        )
        return Response(**response)

    async def get_template(self, template_id: int) -> Response:
        response = await self._request.get(f"/template/{template_id}")
        return Response(**response)

    async def get_templates(self) -> Response:
        response = await self._request.get("/template")
        return Response(**response)

    async def totals(self, year: int, month: int) -> Response:
        response = await self._request.post(
            "/user/totals",
            payload={
                "year": year,
                "month": month,
            })
        return Response(**response)

    async def nick_me(self):
        response = await self._request.get("/nick/me")
        return Response(data=response)

    async def message_sms_normalizer(self):
        response = await self._request.get("/message/sms/normalizer")
        return Response(data=response)

    async def get_limit(self) -> Response:
        response = await self._request.get("/user/get-limit")
        return Response(**response)

    async def message_export(self, year: int, month: int, start: datetime, end: datetime,
                             status: Literal["all", "delivered", "rejected"] = "all"):
        response = await self._request.post(
            "/message/export",
            payload={
                "year": year,
                "month": month,
                "start": start,
                "end": end,
            },
            params={"status": status}
        )
        return Response(data=response)

    async def total_by_month(self, year: int):
        response = await self._request.get(
            "/report/total-by-month",
            params={"year": year}
        )
        return Response(**response)

    async def total_by_smsc(self, year: int, month: int, smsc_id: int):
        response = await self._request.post(
            "/report/total-by-smsc",
            payload={
                "year": year,
                "month": month,
                "smsc_id": smsc_id
            }
        )
        return Response(**response)

    async def logs_sms(self, sms_id: str):
        response = await self._request.get(f"/logs/sms/{sms_id}", )
        return Response(**response)
