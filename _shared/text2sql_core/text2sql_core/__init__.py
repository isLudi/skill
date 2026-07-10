"""Shared, domain-safe Text2SQL primitives."""

from .models import Diagnostic, QueryPlan, QuerySpec, ValidationResult

__all__ = ["Diagnostic", "QueryPlan", "QuerySpec", "ValidationResult"]
__version__ = "2.0.0"
