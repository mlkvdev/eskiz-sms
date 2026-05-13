# eskiz-sms

Modern Python SDK for the [Eskiz.uz](https://eskiz.uz) SMS gateway.
Sync and async clients, full type hints, Pydantic v2 models.

[![Downloads](https://pepy.tech/badge/eskiz-sms)](https://pepy.tech/project/eskiz-sms)
[![Downloads](https://pepy.tech/badge/eskiz-sms/month)](https://pepy.tech/project/eskiz-sms)

Discussion group: https://t.me/+xFkMROBeFp45ZmQ0

> **v1.0.0 is a ground-up rewrite.** The import path and public API changed.
> See [Migrating from v0.x](#migrating-from-v0x) below. v0.x is preserved on
> the `master` branch.

## Installation

Requires Python 3.11+.

```bash
pip install eskiz-sms
```

Optional extras:

```bash
pip install "eskiz-sms[dotenv]"   # for DotenvTokenStorage
```

## Quickstart

```python
from eskiz import EskizSMS

with EskizSMS(email="you@example.com", password="your-password") as client:
    result = client.sms.send(
        mobile_phone="998901234567",
        message="Hello from Eskiz!",
        from_whom="4546",
    )
    print(result.id, result.status)
```

## Async

```python
import asyncio
from eskiz import AsyncEskizSMS

async def main() -> None:
    async with AsyncEskizSMS(email="you@example.com", password="your-password") as client:
        result = await client.sms.send(
            mobile_phone="998901234567",
            message="Hello!",
        )
        print(result.id, result.status)

asyncio.run(main())
```

## Resources

The client exposes four resource namespaces. Every method has the same
signature on the sync and async clients.

### `client.auth`

| Method  | Returns | Notes                  |
| ------- | ------- | ---------------------- |
| `me()`  | `User`  | Current account info.  |

### `client.sms`

| Method                              | Returns                  |
| ----------------------------------- | ------------------------ |
| `send(...)`                         | `SendResult`             |
| `send_global(...)`                  | `SendResult`             |
| `send_batch(messages=, ...)`        | `BatchSendResult`        |
| `list_messages(start_date=, ...)`   | `PaginatedMessages`      |
| `list_by_dispatch(dispatch_id=...)` | `PaginatedMessages`      |
| `dispatch_status(dispatch_id=, user_id=)` | `list[DispatchStatusRow]` |
| `status(sms_id)`                    | `SmsStatusDetail`        |
| `nicks()`                           | `list[str]`              |
| `normalize(message)`                | `list[NormalizerCharacter]` |
| `check(message)`                    | `SmsCheckResult`         |

### `client.templates`

| Method                | Returns          |
| --------------------- | ---------------- |
| `create(template)`    | `TemplateCreated` |
| `list_all()`          | `TemplateList`   |

### `client.reports`

| Method                              | Returns                  |
| ----------------------------------- | ------------------------ |
| `balance()`                         | `LimitInfo`              |
| `prices()`                          | `PriceList`              |
| `totals(year=, month=, is_global=)` | `list[Total]`            |
| `by_month(year)`                    | `list[TotalByMonth]`     |
| `by_smsc(year=, month=)`            | `list[SmscTotal]`        |
| `by_range(start_date=, to_date=, ...)` | `list[RangeExpense]`  |
| `by_dispatch(dispatch_id=, ...)`    | `list[DispatchExpense]`  |
| `export(year=, month=, ...)`        | `str` (CSV)              |
| `logs(sms_id)`                      | `SmsLogResponse`         |

## Sending a batch

```python
from eskiz import EskizSMS
from eskiz.models import BatchMessage

with EskizSMS(email=..., password=...) as client:
    result = client.sms.send_batch(
        dispatch_id=42,
        messages=[
            BatchMessage(user_sms_id="s1", to="998990000001", text="Hi A"),
            BatchMessage(user_sms_id="s2", to="998990000002", text="Hi B"),
        ],
    )
```

Plain dicts work too — `to` is normalized (`+`, spaces, dashes stripped) and
ints are coerced:

```python
client.sms.send_batch(
    dispatch_id=42,
    messages=[{"user_sms_id": "s1", "to": 998990000001, "text": "Hi"}],
)
```

## Token storage

Tokens are cached in memory by default. To persist across runs, pass a
`TokenStorage` to the client:

```python
from eskiz import DotenvTokenStorage, EskizSMS

with EskizSMS(
    email="you@example.com",
    password="your-password",
    token_storage=DotenvTokenStorage(env_path=".env"),
) as client:
    client.sms.send(mobile_phone="998901234567", message="Hi")
# Token written to .env; next run reuses it without re-logging in.
```

`DotenvTokenStorage` requires `pip install "eskiz-sms[dotenv]"`. You can also
implement your own storage (Redis, DB, etc.) by conforming to the
`TokenStorage` Protocol:

```python
class TokenStorage(Protocol):
    def get(self) -> str | None: ...
    def set(self, token: str) -> None: ...
    def clear(self) -> None: ...
```

## Token refresh

The SDK automatically refreshes expired tokens via `PATCH /auth/refresh`. If
refresh fails (revoked token, etc.), it falls back to a fresh
`POST /auth/login`. Concurrent callers share a single in-flight refresh —
under load you'll never hammer `/auth/login` even if 100 requests hit a 401
simultaneously.

## Default callback URL

Pass `callback_url=` to the client and every send uses it unless overridden
per-call:

```python
client = EskizSMS(
    email="you@example.com",
    password="your-password",
    callback_url="https://your-app.com/eskiz/callback",
)
```

## Errors

All errors derive from `EskizError`:

```
EskizError
├── EskizHTTPError         network / TLS / transport failure
├── AuthError
│   ├── InvalidCredentials login email or password is wrong
│   ├── TokenExpired       (rarely surfaced; auto-handled)
│   └── TokenInvalid       token revoked or refresh failed
├── EskizBadRequest        API rejected the request (validation, etc.)
└── EskizValidationError   local input failed validation (bad URL, ...)
```

The `Eskiz*` prefix on the exception names is deliberate — `BadRequest`,
`HTTPError`, and `ValidationError` collide with web frameworks, urllib,
and pydantic respectively.

```python
from eskiz import EskizBadRequest, EskizSMS, InvalidCredentials

try:
    client.sms.send(mobile_phone="998901234567", message="Hi")
except InvalidCredentials:
    print("check your email/password")
except EskizBadRequest as e:
    print(f"API error: {e.message} (status={e.status_code})")
```

## Migrating from v0.x

| v0.x                                     | v1.0                                       |
| ---------------------------------------- | ------------------------------------------ |
| `from eskiz_sms import EskizSMS`         | `from eskiz import EskizSMS`               |
| `EskizSMS(email, password, save_token=True)` | `EskizSMS(email=, password=, token_storage=DotenvTokenStorage())` |
| `eskiz.send_sms(...)`                    | `client.sms.send(...)`                     |
| `eskiz.send_global_sms(...)`             | `client.sms.send_global(...)`              |
| `eskiz.send_batch(...)`                  | `client.sms.send_batch(...)`               |
| `eskiz.get_user_messages(...)`           | `client.sms.list_messages(...)`            |
| `eskiz.get_dispatch_status(...)`         | `client.sms.dispatch_status(...)`          |
| `eskiz.get_template(...)` / `get_templates()` | `client.templates.list_all()`         |
| `eskiz.create_template(...)`             | `client.templates.create(...)`             |
| `eskiz.totals(...)`                      | `client.reports.totals(...)`               |
| `eskiz.total_by_month(...)`              | `client.reports.by_month(...)`             |
| `eskiz.total_by_smsc(...)`               | `client.reports.by_smsc(...)`              |
| `eskiz.message_export(...)`              | `client.reports.export(...)`               |
| `eskiz.get_limit()`                      | `client.reports.balance()`                 |
| `eskiz.logs_sms(...)`                    | `client.reports.logs(...)`                 |
| `eskiz.user`                             | `client.auth.me()`                         |
| `from eskiz_sms.async_ import EskizSMS`  | `from eskiz import AsyncEskizSMS`          |

Other notable changes:

- Python 3.11+ required (was 3.8+).
- All endpoint methods take **keyword-only arguments**.
- All return values are typed Pydantic models, not raw `dict`s.
- Contact endpoints (`add_contact`, `get_contact`, etc.) are no longer
  exposed — they were not in the official Postman collection.
- `client.token.set(...)` removed; use a custom `TokenStorage` instead.

## Integration tests

The unit suite uses `respx` to mock the HTTP layer. A separate, opt-in
integration suite under `tests/integration/` exercises the SDK against the
real Eskiz API. It is skipped by default — pass `--run-integration` to run it.

Set credentials in `.env.integration` (see `.env.integration.example`):

```bash
cp .env.integration.example .env.integration
# fill in ESKIZ_EMAIL / ESKIZ_PASSWORD
```

Run only the read-only smokes (no SMS sent, no credits used):

```bash
pytest --run-integration tests/integration/test_readonly.py tests/integration/test_async.py
```

Run the live send test as well — set `ESKIZ_TEST_PHONE` to a number you
control. Eskiz moderates SMS bodies per-account; if the default `Eskiz Test`
body isn't approved on yours, set `ESKIZ_TEST_BODY` to one that is:

```bash
ESKIZ_TEST_PHONE=998901234567 pytest --run-integration tests/integration
```

## License

MIT
