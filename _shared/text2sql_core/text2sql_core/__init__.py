"""Shared, domain-safe Text2SQL primitives."""

from .dashboard_change import (
    SAFE_OPERATION_TYPES,
    artifact_sha256,
    build_apply_receipt,
    build_dashboard_change_plan,
    build_dashboard_design_spec,
    build_publish_receipt,
    canonical_sha256,
    diff_dashboard,
    normalize_dashboard_profile,
    validate_apply_receipt,
    validate_dashboard_change_plan,
    validate_publish_receipt,
)
from .models import Diagnostic, QueryPlan, QuerySpec, ValidationResult

__all__ = [
    "Diagnostic",
    "QueryPlan",
    "QuerySpec",
    "SAFE_OPERATION_TYPES",
    "ValidationResult",
    "artifact_sha256",
    "build_apply_receipt",
    "build_dashboard_change_plan",
    "build_dashboard_design_spec",
    "build_publish_receipt",
    "canonical_sha256",
    "diff_dashboard",
    "normalize_dashboard_profile",
    "validate_apply_receipt",
    "validate_dashboard_change_plan",
    "validate_publish_receipt",
]
__version__ = "2.0.0"
