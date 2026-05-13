## [1.0.1] - 2026-05-13

First published v1 release — a ground-up rewrite of the SDK. Import path
and public API have changed from v0.x; see "Migrating from v0.x" in the
README. v0.x remains on the `master` branch.

(An earlier `1.0.0` tag was an internal prep milestone, not published to
PyPI; if you saw it on TestPyPI, the artifact uploaded there is
equivalent to this `1.0.1` build.)

### Added

- New top-level API: `EskizSMS` (sync) and `AsyncEskizSMS` (async).
  Configuration is passed as keyword-only kwargs (the convention used by
  `openai`, `anthropic`, `httpx`, `redis-py`, `stripe`).
- Resource namespaces: `client.auth`, `client.sms`, `client.reports`,
  `client.templates` — same method signatures on the sync and async clients.
- Full type hints with `py.typed` marker; all return values are Pydantic v2
  models instead of raw `dict`s.
- Pluggable token storage via the `TokenStorage` protocol. Built-ins:
  `MemoryTokenStorage` (default) and `DotenvTokenStorage` (extra:
  `pip install "eskiz-sms[dotenv]"`).
- Single-flight token refresh: concurrent 401s collapse into one
  `/auth/refresh` call across threads (sync) and tasks (async).
- `from_whom` kwarg (default `"4546"`) — sender id used by `sms.send` and
  `sms.send_batch` when the caller doesn't pass one.
- `enable_token_refresh` kwarg (default `True`) — when off, 401s surface
  immediately as `TokenExpired` instead of triggering a refresh retry.
- `logger` kwarg — refresh, login fallback, and httpx transport errors
  emit `INFO`/`DEBUG`/`WARNING` records. Tokens and passwords are never
  logged.
- `LocalPriceEntry` model for `PriceList.local`, which has a different
  shape than country-keyed `global` entries (`smsc_id, name, price,
  ad_price`).

### Changed

- `sms.check` uses `POST /message/sms/check` (was `GET` in v0.x). The
  live API only routes POST; the previous `GET` returned 404.
- Phone numbers are normalized to digits-only on input.
- Errors form a typed hierarchy rooted at `EskizError`: `AuthError`,
  `InvalidCredentials`, `TokenExpired`, `TokenInvalid`, `EskizBadRequest`,
  `EskizHTTPError`, `EskizValidationError`. The `Eskiz*` prefix on the
  framework-collision-prone names is deliberate
  (`BadRequest`/`HTTPError`/`ValidationError` are taken by web frameworks,
  urllib, and pydantic respectively).
- Default `callback_url` is set once on the client instead of per call.
- Parsers raise `EskizBadRequest` on unexpected response shape rather than
  returning silent empty results — a shifted API surfaces as an error
  instead of an empty page.
- `EskizError.__str__` prefixes the class name (`EskizBadRequest: …`) so
  log lines identify the exception type.
- `Development Status` classifier promoted to `5 - Production/Stable`.

### Removed

- Contact endpoints (`add_contact`, `get_contact`, …) — they were not in
  the official Postman collection.
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
