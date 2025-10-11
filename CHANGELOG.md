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
