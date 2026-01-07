from dataclasses import dataclass
from datetime import datetime
from typing import Union, Optional


@dataclass
class Response:
    id: Optional[str] = None
    success: Optional[bool] = None
    status: Optional[str] = None
    data: Optional[Union[dict, list, str]] = None
    result: Optional[Union[dict, list, str]] = None
    message: Optional[Union[str, dict]] = None


@dataclass
class User:
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    api_token: Optional[str] = None
    status: Optional[str] = None
    is_vip: Optional[bool] = None
    balance: Optional[int] = None


@dataclass
class Contact:
    id: Optional[int] = None
    user_id: Optional[int] = None
    group: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    mobile_phone: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class ContactCreated:
    contact_id: int
