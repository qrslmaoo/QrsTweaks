# src/qrs/utils/safe_exec.py
from __future__ import annotations

"""
Global safe-execution helpers for QrsTweaks.

Goal of Phase 12:
    - Provide a single, reusable place to wrap calls so they:
        * Never crash the UI
        * Always return a consistent (ok, message, payload) shape
        * Produce readable error strings instead of raw tracebacks

This module does NOT change any existing behavior by itself. You opt-in
by calling safe_call(...) or using SafeExecutorMixin in a class.
"""

from typing import Any, Callable, Tuple, TypeVar, Generic

T = TypeVar("T")


class SafeExecutorMixin:
    """
    Mixin that gives any class a `_safe_call` helper.

    Usage in a class:

        class WindowsOptimizer(SafeExecutorMixin):
            def create_restore_point_safe(self, description: str):
                return self._safe_call(
                    "create_restore_point",
                    self.create_restore_point,
                    description,
                )

    `_safe_call` always returns: (ok: bool, message: str, payload: Any | None)
    """

    def _safe_call(
        self,
        label: str,
        func: Callable[..., T],
        *args: Any,
        **kwargs: Any,
    ) -> Tuple[bool, str, T | None]:
        try:
            result = func(*args, **kwargs)
            # If the function already returns a (ok, msg) or (ok, msg, payload),
            # preserve that structure as much as possible.
            if isinstance(result, tuple):
                # Try to interpret common patterns
                if len(result) == 2 and isinstance(result[0], bool):
                    ok, msg = result
                    return ok, str(msg), None
                if len(result) == 3 and isinstance(result[0], bool):
                    ok, msg, payload = result
                    return ok, str(msg), payload  # type: ignore[return-value]
            # Any non-tuple result is treated as a payload with implicit success.
            return True, f"{label} completed successfully.", result
        except Exception as e:
            # Last-resort safety: never let exceptions bubble into the UI loop.
            return False, f"{label} failed with error: {e!r}", None


def safe_call(
    label: str,
    func: Callable[..., T],
    *args: Any,
    **kwargs: Any,
) -> Tuple[bool, str, T | None]:
    """
    Standalone safe-call helper for non-class usage.

    Example:

        ok, msg, payload = safe_call(
            "run_dism_sfc",
            windows_optimizer.run_dism_sfc,
        )
    """
    try:
        result = func(*args, **kwargs)
        if isinstance(result, tuple):
            if len(result) == 2 and isinstance(result[0], bool):
                ok, msg = result
                return ok, str(msg), None
            if len(result) == 3 and isinstance(result[0], bool):
                ok, msg, payload = result
                return ok, str(msg), payload  # type: ignore[return-value]
        return True, f"{label} completed successfully.", result
    except Exception as e:
        return False, f"{label} failed with error: {e!r}", None
