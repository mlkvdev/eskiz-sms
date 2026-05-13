## [1.0.1] - 2026-05-13

Post-release polish. Public renames are breaking changes from 1.0.0; the
hierarchy and overall design are unchanged.

### Changed (breaking)

- The `Config` dataclass is no longer part of the public surface. Pass
  what were previously its fields directly as kwargs to `EskizSMS(...)` /
  `AsyncEskizSMS(...)` — matching the convention used by `openai`,
  `anthropic`, `httpx`, `redis-py`, and `stripe`. Migration:
  `EskizSMS(Config(email=..., password=...))` → `EskizSMS(email=..., password=...)`.
- `BadRequest` → `EskizBadRequest`,
  `HTTPError` → `EskizHTTPError`,
  `ValidationError` → `EskizValidationError`. The old names collided with
  web frameworks, urllib, and pydantic respectively. `EskizError`,
  `AuthError`, and the token error subclasses are unchanged.
- `max_token_refresh_retries: int` → `enable_token_refresh: bool` (default
  `True`). The old knob was treated as a boolean internally; rename
  matches the real semantics.
- Parsers no longer return silent empty results when a response payload
  has an unexpected shape. `sms.nicks`, `sms.normalize`,
  `sms.list_by_dispatch`, `reports.prices`, `reports.export`, and
  `reports.logs` now raise `EskizBadRequest` on shape mismatch so a
  shifted API surfaces as an error instead of an empty page.

### Added

- `from_whom: str = "4546"` kwarg — the default alphanumeric sender id used
  by `sms.send` and `sms.send_batch` when the caller doesn't pass one.
  Callers with a non-default approved nick no longer have to pass it on
  every call.
- The `logger` kwarg is now actually used: `sms.send` retries,
  `/auth/refresh` failures, and httpx transport errors emit
  `INFO`/`DEBUG`/`WARNING` records. Tokens and passwords are never logged.

### Changed (non-breaking)

- `Development Status` classifier promoted to `5 - Production/Stable`.
- `EskizError.__str__` now prefixes the class name (`BadRequest: …` →
  `EskizBadRequest: …`) so log output identifies the exception type.
- `ResponseEnvelope.status` tightened from `EnvelopeStatus | str | None`
  to `EnvelopeStatus | None` — the `str` union made the enum useless.
- `DotenvTokenStorage` now probes its optional dependency via
  `importlib.util.find_spec` and documents the event-loop-blocking caveat
  for async callers.
- Internal model and resource base classes renamed from leading-
  underscore names (`_Base`, `_SyncResource`, `_AsyncResource`) to
  `BaseEskizModel`, `SyncResource`, `AsyncResource` — they were used
  across sibling modules and the underscore form was strict-pyright
  noise. These are not in `eskiz.__all__`.

## [1.0.0] - 2026-05-05

Ground-up rewrite. Import path and public API have changed; v0.x is preserved
on the `master` branch. See "Migrating from v0.x" in the README for the full
migration map.

### Added

- New top-level API: `EskizSMS` (sync) and `AsyncEskizSMS` (async), both
  configured by an immutable `Config` dataclass.
- Resource namespaces: `client.auth`, `client.sms`, `client.reports`,
  `client.templates` — same method signatures on the sync and async clients.
- Full type hints with `py.typed` marker; all return values are Pydantic v2
  models instead of raw `dict`s.
- Pluggable token storage via the `TokenStorage` protocol. Built-ins:
  `MemoryTokenStorage` (default) and `DotenvTokenStorage` (extra:
  `pip install "eskiz-sms[dotenv]"`).
- Single-flight token refresh: concurrent 401s collapse into one
  `/auth/refresh` call across threads (sync) and tasks (async).
- New `LocalPriceEntry` model for `PriceList.local`, which has a different
  shape than country-keyed `global` entries (`smsc_id, name, price, ad_price`).

### Changed

- `sms.check` now uses `POST /message/sms/check` (was `GET`). The live API
  only routes POST; the previous `GET` returned 404.
- Phone numbers are normalized to digits-only on input.
- Errors are surfaced as a typed exception hierarchy rooted at `EskizError`:
  `AuthError`, `InvalidCredentials`, `TokenExpired`, `TokenInvalid`,
  `BadRequest`, `HTTPError`, `ValidationError`.
- Default callback URL can be set once on `Config` instead of passed per
  call.

### Removed

- Contact endpoints (`add_contact`, `get_contact`, …) — they were not in the
  official Postman collection.
- `client.token.set(...)` — use a custom `TokenStorage` instead.

## [0.2.4] - 2025-10-11

### Added

- Implemented new API methods:
    - `nick_me()`
    - `message_sms_normalizer()` — analyzes SMS for special characters and suggests replacements to reduce cost.
    - `get_limit()` — retrieves account limits.
    - `message_export(year, month, start, end, status)` — exports SMS messages by date range and status.
    - `total_by_month(year)` — returns monthly message totals.
    - `total_by_smsc(year, month, smsc_id)` — returns totals per operator (Mobiuz, Beeline, Ucell, etc.).
    - `logs_sms(sms_id)` — retrieves delivery logs for a given SMS.

### Changed

- Updated `httpx` dependency to the latest version for compatibility.
