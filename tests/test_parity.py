"""Sync/async parity — both clients must expose the same resource methods."""

from __future__ import annotations

import inspect


def _public_methods(obj_type: type) -> set[str]:
    return {
        name
        for name, _ in inspect.getmembers(obj_type, predicate=inspect.isfunction)
        if not name.startswith("_")
    }


def _resource_pairs() -> list[tuple[str, type, type]]:
    """Return (resource_name, sync_resource_type, async_resource_type) tuples."""
    from eskiz.resources.auth import AsyncAuthResource, AuthResource
    from eskiz.resources.reports import AsyncReportsResource, ReportsResource
    from eskiz.resources.sms import AsyncSmsResource, SmsResource
    from eskiz.resources.templates import AsyncTemplatesResource, TemplatesResource

    return [
        ("auth", AuthResource, AsyncAuthResource),
        ("sms", SmsResource, AsyncSmsResource),
        ("templates", TemplatesResource, AsyncTemplatesResource),
        ("reports", ReportsResource, AsyncReportsResource),
    ]


def test_each_resource_has_identical_method_names() -> None:
    for name, sync_t, async_t in _resource_pairs():
        sync_methods = _public_methods(sync_t)
        async_methods = _public_methods(async_t)
        assert sync_methods == async_methods, (
            f"{name}: sync has {sync_methods - async_methods}, "
            f"async has {async_methods - sync_methods}"
        )


def test_each_method_signature_matches() -> None:
    for name, sync_t, async_t in _resource_pairs():
        for method in _public_methods(sync_t):
            sync_sig = inspect.signature(getattr(sync_t, method))
            async_sig = inspect.signature(getattr(async_t, method))
            assert list(sync_sig.parameters.keys()) == list(async_sig.parameters.keys()), (
                f"{name}.{method}: sync={list(sync_sig.parameters)} "
                f"async={list(async_sig.parameters)}"
            )


def test_async_methods_are_coroutines() -> None:
    for name, _sync_t, async_t in _resource_pairs():
        for method in _public_methods(async_t):
            fn = getattr(async_t, method)
            assert inspect.iscoroutinefunction(fn), f"{name}.{method} is not async"
