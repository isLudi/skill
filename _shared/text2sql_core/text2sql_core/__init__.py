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
from .dashboard_build import (
    COMPONENT_TYPES,
    REQUIRED_CAPABILITIES,
    build_dashboard_build_plan,
    build_dashboard_build_publish_receipt,
    build_dashboard_build_receipt,
    normalize_dashboard_build_spec,
    validate_dashboard_build_plan,
    validate_dashboard_build_publish_receipt,
    validate_dashboard_build_receipt,
    validate_dashboard_build_spec,
)
from .models import Diagnostic, QueryPlan, QuerySpec, ValidationResult

__all__ = [
    "Diagnostic",
    "QueryPlan",
    "QuerySpec",
    "SAFE_OPERATION_TYPES",
    "ValidationResult",
    "COMPONENT_TYPES",
    "REQUIRED_CAPABILITIES",
    "artifact_sha256",
    "build_apply_receipt",
    "build_dashboard_change_plan",
    "build_dashboard_design_spec",
    "build_publish_receipt",
    "canonical_sha256",
    "build_dashboard_build_plan",
    "build_dashboard_build_publish_receipt",
    "build_dashboard_build_receipt",
    "diff_dashboard",
    "normalize_dashboard_profile",
    "normalize_dashboard_build_spec",
    "validate_apply_receipt",
    "validate_dashboard_build_plan",
    "validate_dashboard_build_publish_receipt",
    "validate_dashboard_build_receipt",
    "validate_dashboard_build_spec",
    "validate_dashboard_change_plan",
    "validate_publish_receipt",
]
__version__ = "2.0.0"
