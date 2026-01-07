from datetime import datetime
from typing import Optional, List, Literal

from .base import EskizSMSBase
from .exceptions import ContactNotFound
from .types import User, Contact, Response, ContactCreated


class EskizSMS(EskizSMSBase):
    @property
    def user(self) -> Optional[User]:
        self._user = self._user_data()
        return self._user

    def _user_data(self) -> Optional[User]:
        response = self._request.get("/auth/user")
        if 'data' in response:
            response = response['data']
        return User(**response)

    def add_contact(self, name: str, email: str, group: str, mobile_phone: str) -> ContactCreated:
        response = self._request.post(
            "/contact",
            payload={
                "name": name,
                "email": email,
                "group": group,
                "mobile_phone": str(mobile_phone),
            })
        return ContactCreated(response['data'])

    def update_contact(self, contact_id: int, name: str, group: str, mobile_phone: str) -> Optional[Contact]:
        response = self._request.put(
            f"/contact/{contact_id}",
            payload={
                "name": name,
                "group": group,
                "mobile_phone": str(mobile_phone),
            })
        if response and isinstance(response, list):
            return Contact(**response[0])
        return None

    def get_contact(self, contact_id: int, raise_exception=False) -> Optional[Contact]:
        response = self._request.get(f"/contact/{contact_id}")
        if not response:
            if raise_exception:
                raise ContactNotFound
            return None
        return Contact(**response[0])

    def delete_contact(self, contact_id: int) -> Response:
        response = self._request.delete(f"/contact/{contact_id}")
        return Response(**response)

    def send_sms(self, mobile_phone: str, message: str, from_whom: str = '4546',
                 callback_url: str = None) -> Response:

        payload = {
            "mobile_phone": str(mobile_phone),
            "message": message,
            "from_whom": from_whom,
        }
        callback_url = self._get_callback_url(callback_url)
        if callback_url:
            payload['callback_url'] = callback_url
        return Response(**self._request.post("/message/sms/send", payload=payload))

    def send_global_sms(self, mobile_phone: str, message: str, country_code: str,
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
        return Response(**self._request.post("/message/sms/send-global", payload=payload))

    def send_batch(self, *, messages: List[dict], from_whom: str = "4546", dispatch_id: int) -> Response:
        return Response(**self._request.post(
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
            }))

    def get_user_messages(self, from_date: str, to_date: str) -> Response:
        return Response(**self._request.get(
            "/message/sms/get-user-messages",
            payload={
                "from_date": from_date,
                "to_date": to_date,
                "user_id": self.user.id
            }
        ))

    def get_user_messages_by_dispatch(self, dispatch_id: int) -> Response:
        return Response(**self._request.get(
            "/message/sms/get-user-messages-by-dispatch",
            payload={
                "dispatch_id": dispatch_id,
                "user_id": self.user.id
            }))

    def get_dispatch_status(self, dispatch_id: int) -> Response:
        return Response(**self._request.get(
            "/message/sms/get-dispatch-status",
            payload={
                "dispatch_id": dispatch_id,
                "user_id": self.user.id
            }))

    def create_template(self, text: str) -> Response:
        return Response(**self._request.post(
            "/user/template",
            payload={
                "template": text,
            }))

    def get_templates(self) -> Response:
        return Response(**self._request.get("/user/templates"))

    def totals(self, year: int, month: int) -> Response:
        return Response(**self._request.post(
            "/user/totals",
            payload={
                "year": year,
                "month": month,
            }))

    def nick_me(self) -> Optional[Response]:
        response = self._request.get("/nick/me")
        if response:
            return Response(**response)
        return None

    def message_sms_normalizer(self):
        response = self._request.post("/message/sms/normalizer")
        return Response(data=response)

    def get_limit(self) -> Response:
        return Response(**self._request.get("/user/get-limit"))

    def message_export(self, year: int, month: int, start: datetime, end: datetime,
                       status: Literal["all", "delivered", "rejected"] = "all"):
        date_format = "%Y-%m-%d %H:%M:%S"
        response = self._request.post(
            "/message/export",
            payload={
                "year": year,
                "month": month,
                "start": start.strftime(date_format),
                "end": end.strftime(date_format),
            },
            params={"status": status}
        )
        return response

    def total_by_month(self, year: int):
        response = self._request.get(
            "/report/total-by-month",
            params={"year": year}
        )
        return Response(**response)

    def total_by_smsc(self, year: int, month: int, smsc_id: int):
        response = self._request.post(
            "/report/total-by-smsc",
            payload={
                "year": year,
                "month": month,
                "smsc_id": smsc_id
            }
        )
        return Response(**response)

    def logs_sms(self, sms_id: str):
        response = self._request.get(f"/logs/sms/{sms_id}", )
        return Response(**response)
