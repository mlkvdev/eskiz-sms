# v1.0.0 — review TODO

Findings from the deep review of the v1.0.0 branch. Grouped by severity.
Critical and High items are now landed (see check-marks); Medium / Low items
are polish work.

---

## Critical (resolved)

- [x] **C1. `Config.password` redacted from `repr`** — `password: str = field(repr=False)`.
  Verified by `tests/test_auth.py::test_password_not_in_config_repr`.

- [x] **C2. Login 401 → `InvalidCredentials`** — `client.py::_login` and
  `aio.py::_login` catch `TokenExpired` and re-raise as `InvalidCredentials`.
  Verified by `tests/test_auth.py::test_login_401_with_unfamiliar_message_still_raises_invalid_credentials`.

- [x] **C3. Any 401 triggers refresh except `token_invalid`** —
  `transport/base.py::is_token_expired` simplified; `_TOKEN_EXPIRED_MARKERS`
  removed. Verified by `tests/test_auth.py::test_token_invalid_status_skips_refresh`.

- [x] **C4. `BatchMessage.to` int coercion** — `field_validator(mode="before")`
  in `models/sms.py` runs `normalize_phone(str(v))`. Verified by
  `tests/test_resources.py::test_sms_send_batch_uses_json` (sends `to=998990000000`
  as int).

- [x] **C5. `PaginatedMessages.result` widened** — now
  `list[dict[str, Any]] | str | None` to accept the by-dispatch string
  response form. Combined with **H5** so any further shape drift surfaces as
  `BadRequest`.

---

## High (resolved)

- [x] **H1. `AsyncTransport` task race** — eager client construction in
  `__init__`.

- [x] **H2. Token manager held lock during HTTP I/O** — refactored to
  `_single_flight()` using `concurrent.futures.Future` (sync) /
  `asyncio.Future` (async). Lock now only guards short critical sections;
  HTTP round-trip happens unguarded; queued callers wait on the shared
  Future. Verified by `tests/test_concurrency.py` (8 concurrent threads
  produce ≤1 refresh).

- [ ] **H3. Confusing transport method names** — `request_raw` /
  `request_unauth` / `request`. Cosmetic; defer.

- [x] **H4. Reports return typed models** — `by_smsc → list[SmscTotal]`,
  `by_range → list[RangeExpense]`, `by_dispatch → list[DispatchExpense]`.

- [x] **H5. Pydantic `ValidationError` wrapped** — `resources/_base.py::_safe_parse`
  converts to `BadRequest`. Verified by
  `tests/test_resources.py::test_validation_error_wrapped_as_bad_request`.

- [x] **H6. Post-refresh failure → `TokenInvalid`** — both transports raise
  `TokenInvalid("Token refresh produced a token that was rejected on retry")`
  on the second 401. Verified by
  `tests/test_auth.py::test_post_refresh_invalid_token_raises_token_invalid`.

---

## Medium

- [ ] **M1. Two layers own retry logic.** Transport handles 401-retry;
  token manager handles refresh-then-relogin fallback. Document, or
  consolidate via httpx event hooks.

- [ ] **M2. No `ServerError` class — 5xx and 4xx all become `BadRequest`.**
  Add `ServerError(EskizError)`; route in `raise_for_response`.

- [ ] **M3. `TokenStorage` Protocol is not `@runtime_checkable`.**

- [ ] **M4. `MemoryTokenStorage` lock is redundant with manager's lock.**
  Document and keep, or drop.

- [x] **M5. `_envelope_data` truncates payload** — capped at 200 chars.

- [ ] **M6. `endpoints.py` mixes constants and helpers.** Cosmetic.

- [ ] **M7. `dispatch_status` requires `user_id`.** Try omitting; Eskiz
  may infer from bearer.

- [ ] **M8. `User.balance: float` but API returns int.** Cosmetic.

- [ ] **M9. `EnvelopeStatus` / `ResponseEnvelope` exported but unused.**
  Drop or adopt.

- [ ] **M10. `AsyncEskizSMS.__aenter__` is a no-op.** Cosmetic.

---

## Low / cleanup

- [ ] **L1. `RequestPlan.data` is mutable** despite `frozen=True`.
- [ ] **L2. Audit unused imports / dead exports.**
- [ ] **L3. `_Base.str_strip_whitespace=True`** could silently mangle SMS
  bodies. Consider removing.
- [ ] **L4. `from __future__ import annotations` is everywhere** — noise on 3.11+.
- [ ] **L5. Sparse top-level re-exports.** Add `BatchMessage`, `SendResult`,
  `User` to `eskiz/__init__.py` for ergonomics.
- [ ] **L6. `AsyncTokenManager._lock` can be `None`.** Fragile; safe in
  practice.
- [ ] **L7. `Config.logger` is set but nothing logs.** Wire up redacted
  debug logging or drop.
- [ ] **L8. README / CHANGELOG still v0.x.** Rewrite for v1.
- [x] **L9. Tests.** 23 passing tests covering auth flow, refresh, error
  mapping, concurrency single-flight, sync/async parity, per-resource
  round-trips. See `tests/`.

---

## Architectural verdict (resolved)

Refactored on 2026-05-04. The layout:

- **`_protocol/`** — pure plan factories (auth, sms, templates, reports).
  No SDK semantics. Trivially unit-testable without HTTP.
- **`resources/`** — `SmsResource`/`AsyncSmsResource` etc., one file per
  domain. Each holds an executor (`SyncExecutor`/`AsyncExecutor`) and the
  config; methods apply defaults and call the protocol layer.
- **`client.py` / `aio.py`** — pure composition (~85 lines each). Expose
  `client.sms`, `client.auth`, `client.templates`, `client.reports`.

The plan-based dedup carries over — endpoint logic lives once in
`_protocol/`. The mirror at the resource layer is bounded per-resource
(max ~10 methods). Pydantic `ValidationError` wrapping lives centrally in
`_safe_parse`.

---

## Status

All Critical and High items resolved. Medium / Low items are polish work to
schedule as needed. Test suite: 23 / 23 passing. `ruff` and `ty` clean.
