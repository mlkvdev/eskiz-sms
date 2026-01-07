import re
from datetime import datetime
from typing import Optional, List, Literal

from eskiz_sms.request import Request
from .exceptions import InvalidCallbackUrl
from .token import Token
from .types import User, Contact, Response


class Meta(type):
    def __new__(mcs, name, bases, dct, async_=False):
        x = super().__new__(mcs, name, bases, dct)
        setattr(x, 'is_async', async_)
        return x


class EskizSMSBase(metaclass=Meta):
    __slots__ = (
        "token",
        "_user",
        "callback_url",
        "is_async",
        "_request",
    )

    def __init__(
            self,
            email: str,
            password: str,
            callback_url: str = None,
            save_token: bool = False,
            env_file_path: str = None,
            auto_update_token=True,
    ):

        if callback_url is not None:
            self._validate_callback_url(callback_url)
        self.callback_url = callback_url

        self.token = Token(
            email,
            password,
            save_token=save_token,
            env_file_path=env_file_path,
            auto_update=auto_update_token,
            is_async=getattr(self, 'is_async')
        )
        self._request = Request(self)
        self._user: Optional[User] = None

    @staticmethod
    def _validate_callback_url(url):
        if url_validator(url) is False:
            raise InvalidCallbackUrl(message="Invalid callback url")

    def _get_callback_url(self, callback_url: str = None):
        if callback_url is not None:
            self._validate_callback_url(callback_url)
            return callback_url
        return self.callback_url

    @property
    def user(self) -> Optional[User]:
        raise NotImplementedError

    def _user_data(self) -> Optional[User]:
        raise NotImplementedError

    def add_contact(self, name: str, email: str, group: str, mobile_phone: str) -> Contact:
        raise NotImplementedError

    def update_contact(self, contact_id: int, name: str, group: str, mobile_phone: str) -> Optional[Contact]:
        raise NotImplementedError

    def get_contact(self, contact_id: int, raise_exception=False) -> Optional[Contact]:
        raise NotImplementedError

    def delete_contact(self, contact_id: int) -> Response:
        raise NotImplementedError

    def send_sms(self, mobile_phone: str, message: str, from_whom: str = '4546',
                 callback_url: str = None) -> Response:
        """
        :param mobile_phone: Phone number without plus sign
        :param message: Message to send
        :param from_whom: To use a nickname, you need to change the field to your own
        :param callback_url: This is an optional field that is used to automatically receive SMS status from the server.
            Specify the callback URL where you will receive POST data in the following format:
            {"message_id": "4385062", "user_sms_id": "your_id_here", "country": "UZ",
            "phone_number": "998991234567", "sms_count": "1",
            "status" : "DELIVER", "status_date": "2021-04-02 00:39:36"}
        :return: Response
        """
        raise NotImplementedError

    def send_global_sms(self, mobile_phone: str, message: str, country_code: str,
                        callback_url: str = None, unicode: str = "0") -> Response:
        """
        :param mobile_phone: Phone number without plus sign
        :param message: Message to send
        :param country_code: e.g. 'US'
        :param callback_url: Pass a callback url to get notified when the message is sent
        :param unicode: Default is 0, pass 1 if you want to send cyrillic message
        :return:
        """

        raise NotImplementedError

    def send_batch(self, *, messages: List[dict], from_whom: str = "4546", dispatch_id: int) -> Response:
        """
        :param messages: List of messages to send.
            [{"user_sms_id":"sms1","to": 998998046210, "text": "eto test"}]
        :param from_whom: 4546
        :param dispatch_id:
        :returns: Response
        :rtype: eskiz_sms.types.Response
        """
        raise NotImplementedError

    def get_user_messages(self, from_date: str, to_date: str) -> Response:
        raise NotImplementedError

    def get_user_messages_by_dispatch(self, dispatch_id: int) -> Response:
        raise NotImplementedError

    def get_dispatch_status(self, dispatch_id: int) -> Response:
        raise NotImplementedError

    def create_template(self, text: str) -> Response:
        raise NotImplementedError

    def update_template(self, template_id: int, name: str, text: str) -> Response:
        raise NotImplementedError

    def get_template(self, template_id: int) -> Response:
        raise NotImplementedError

    def get_templates(self) -> Response:
        raise NotImplementedError

    def totals(self, year: int, month: int) -> Response:
        raise NotImplementedError

    def nick_me(self):
        raise NotImplementedError

    def message_sms_normalizer(self):
        """
        Этот API предоставляет информацию о наличии специальных символов в SMS-сообщении, а также о том, какими символами можно заменить специальные символы.
        Используя этот API, вы можете отправлять свои SMS дешевле.
        """
        raise NotImplementedError

    def get_limit(self) -> Response:
        raise NotImplementedError

    def message_export(self, year: int, month: int, start: datetime, end: datetime,
                       status: Literal["all", "delivered", "rejected"] = "all"):
        raise NotImplementedError

    def total_by_month(self, year: int):
        raise NotImplementedError

    def total_by_smsc(self, year: int, month: int, smsc_id: int):
        """
        :param year: Year
        :param month: Month
        :param smsc_id: ID компании
            1 - Mobiuz;
            2 - Beeline;
            3 - Ucell;
            4 - Humans;
            5 - Uzmobile GSM;
            6 - Uzmobile CDMA;
            7 - Perfectum;
            8 - Global
        :return: Response
        """
        raise NotImplementedError

    def logs_sms(self, sms_id: str):
        """
        :param sms_id: SMS ID
        :return: Response
        """
        raise NotImplementedError


URL_RE = re.compile(
    r"[(http(s)?):\/\/(www\.)?a-zA-Z0-9@:%._\+~#=]"  # noqa
    r"{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)"  # noqa
)


def url_validator(url: str):
    return bool(URL_RE.search(url))
