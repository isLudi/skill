"""Shared user-facing errors."""

from __future__ import annotations


class UsageError(RuntimeError):
    """User-actionable script error."""
