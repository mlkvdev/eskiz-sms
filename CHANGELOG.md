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
