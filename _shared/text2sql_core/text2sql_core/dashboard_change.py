"""Pure-local dashboard design, diff, and receipt contracts for P3A/P3B.

This module deliberately has no browser or platform dependency.  A profile,
design, or change plan is evidence; none of them grants write or publish
authority.  The operator owns all platform I/O and must obtain explicit user
authorization before applying an otherwise safe change plan.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .dashboard_contracts import validate_dataset_contract_registry_evidence
from .dashboard_domains import validate_dashboard_domain_registration


SCHEMA_VERSION = "4.0.0"
SUPPORTED_DOMAINS = {"market_consultant", "qingcheng"}
PROFILE_DOMAINS = {*SUPPORTED_DOMAINS, "unresolved"}
SAFE_OPERATION_TYPES = {
    "update_component_fields",
    "update_filter_dynamic_default",
    "update_formula",
    "update_layout",
    "update_theme",
}
RECOGNIZED_DESIGN_OPERATION_TYPES = {
    "create_component",
    "delete_component",
    "change_component_type",
    "rebind_dataset",
    "move_component_container",
    "update_existing_component",
    "update_component_fields",
    "update_layout",
    "create_formula",
    "delete_formula",
    "update_formula",
    "create_public_filter",
    "delete_public_filter",
    "rebind_filter",
    "update_filter",
    "update_filter_dynamic_default",
    "update_component_filter",
    "update_theme",
    "create_dataset",
    "delete_dataset",
    "replace_dataset",
}
PROFILE_VOLATILE_KEYS = {"captured_at", "profiled_at", "html_id"}
PROFILE_REQUIRED_SECTIONS = (
    "components",
    "layout",
    "formulas",
    "public_filters",
    "component_filters",
    "datasets",
    "theme",
)
DOMAIN_SKILL_NAMES = {
    "market_consultant": "sql-query-writer-for-dashboard",
    "qingcheng": "qingcheng-dashboard-sql",
}


def _json_value(value: Any) -> Any:
    """Return a detached, JSON-compatible value with stable dict ordering."""

    if isinstance(value, Mapping):
        return {str(key): _json_value(value[key]) for key in sorted(value, key=str)}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"value is not JSON compatible: {type(value).__name__}")


def canonical_json_bytes(value: Any, *, omit_top_level: Iterable[str] = ()) -> bytes:
    """Serialize JSON deterministically.

    Only explicitly named top-level keys are omitted.  In particular, upstream
    ``*_sha256`` bindings remain part of downstream hashes.
    """

    payload = _json_value(value)
    if isinstance(payload, dict):
        for key in omit_top_level:
            payload.pop(key, None)
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonical_sha256(value: Any, *, omit_top_level: Iterable[str] = ()) -> str:
    """Return a canonical SHA-256 while retaining all non-omitted bindings."""

    return hashlib.sha256(canonical_json_bytes(value, omit_top_level=omit_top_level)).hexdigest()


def artifact_sha256(value: Mapping[str, Any], hash_field: str) -> str:
    """Hash an artifact while omitting only its own top-level hash field."""

    return canonical_sha256(value, omit_top_level={hash_field})


def profile_sha256(profile: Mapping[str, Any]) -> str:
    """Hash edit-relevant profile state, ignoring capture time and self hash."""

    return canonical_sha256(
        profile,
        omit_top_level={"profile_sha256", *PROFILE_VOLATILE_KEYS},
    )


def _require_text(value: Any, name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{name} is required")
    return text


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _first(item: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in item and item[key] not in (None, ""):
            return item[key]
    return None


def _stable_unique(values: Iterable[Any]) -> list[str]:
    return sorted({_require_text(value, "identifier") for value in values if value not in (None, "")})


def _normalize_component(item: Mapping[str, Any]) -> dict[str, Any]:
    component_id = _require_text(
        _first(item, "component_id", "node_id", "id", "chart_id", "unit_id"),
        "component.component_id",
    )
    known = {
        "component_id", "node_id", "id", "chart_id", "unit_id", "component_type", "type",
        "chart_type", "title", "name", "container_id", "tab_id", "dataset_id",
        "fields", "dimensions", "metrics", "formula_ids", "filter_ids", "sort",
        "pagination", "display", "config", "layout", "updated_at", "created_at",
        "parent_node_id", "container_path", "node_component", "node_title",
        "component_name", "hidden", "locked", "extensions",
    }
    fields = item.get("fields")
    if fields is None:
        fields = {
            "dimensions": item.get("dimensions", []),
            "metrics": item.get("metrics", []),
        }
    extensions = dict(item.get("extensions", {})) if isinstance(item.get("extensions"), Mapping) else {}
    extensions.update({
        str(key): _json_value(value)
        for key, value in item.items()
        if key not in known
    })
    return {
        "component_id": component_id,
        "unit_id": _optional_text(_first(item, "unit_id")),
        "component_type": _require_text(
            _first(item, "component_type", "type", "chart_type") or "unknown",
            "component.component_type",
        ),
        "title": str(_first(item, "title", "node_title", "name", "component_name") or ""),
        "container_id": _optional_text(_first(item, "container_id", "parent_node_id")),
        "tab_id": _optional_text(item.get("tab_id")),
        "dataset_id": _optional_text(item.get("dataset_id")),
        "fields": _json_value(fields),
        "formula_ids": _stable_unique(item.get("formula_ids", [])),
        "filter_ids": _stable_unique(item.get("filter_ids", [])),
        "sort": _json_value(item.get("sort", [])),
        "pagination": _json_value(item.get("pagination", {})),
        "display": _json_value(
            item.get(
                "display",
                {"hidden": bool(item.get("hidden", False)), "locked": bool(item.get("locked", False))},
            )
        ),
        "config": _json_value(item.get("config", {})),
        "extensions": _json_value(extensions),
    }


def _normalize_layout(item: Mapping[str, Any], component: Mapping[str, Any] | None = None) -> dict[str, Any]:
    component_id = _require_text(
        _first(item, "component_id", "node_id", "id", "chart_id", "unit_id")
        or (component or {}).get("component_id"),
        "layout.component_id",
    )

    def number(*keys: str, default: int) -> int | float:
        raw = _first(item, *keys)
        if raw is None:
            return default
        if isinstance(raw, bool):
            raise ValueError(f"layout {component_id} coordinate cannot be boolean")
        parsed = float(raw)
        return int(parsed) if parsed.is_integer() else parsed

    return {
        "component_id": component_id,
        "unit_id": _optional_text(_first(item, "unit_id") or (component or {}).get("unit_id")),
        "container_id": _optional_text(
            _first(item, "container_id", "parent_node_id")
            if _first(item, "container_id", "parent_node_id") is not None
            else (component or {}).get("container_id")
        ),
        "tab_id": _optional_text(item.get("tab_id") if "tab_id" in item else (component or {}).get("tab_id")),
        "x": number("x", "left", default=0),
        "y": number("y", "top", default=0),
        "w": number("w", "width", default=1),
        "h": number("h", "height", default=1),
        "z": number("z", "z_index", default=0),
    }


def _normalize_formula(item: Mapping[str, Any]) -> dict[str, Any]:
    formula_id = _first(item, "formula_id", "id")
    if not formula_id and item.get("field_id"):
        formula_id = f"{item.get('unit_id') or 'dashboard'}::{item['field_id']}"
    formula_id = _require_text(formula_id, "formula.formula_id")
    dependencies: list[Any] = []
    for dependency in item.get("dependencies", []):
        if isinstance(dependency, Mapping):
            dependencies.append(_json_value(dependency))
        else:
            dependencies.append(str(dependency))
    dependencies.sort(key=lambda value: json.dumps(value, ensure_ascii=False, sort_keys=True))
    return {
        "formula_id": formula_id,
        "name": str(item.get("name") or item.get("business_name") or ""),
        "expression": str(item.get("expression") or item.get("formula") or ""),
        "dependencies": dependencies,
        "scope": str(item.get("scope") or "component"),
        "shared": bool(item.get("shared", False)),
        "component_ids": _stable_unique(
            item.get("component_ids", [item.get("unit_id")] if item.get("unit_id") else [])
        ),
        "dataset_id": _optional_text(item.get("dataset_id")),
        "contract_id": _optional_text(item.get("contract_id")),
        "config": _json_value(item.get("config", {})),
    }


def _normalize_filter(item: Mapping[str, Any]) -> dict[str, Any]:
    filter_id = _require_text(_first(item, "filter_id", "id", "relation_id"), "public_filter.filter_id")
    known = {
        "filter_id", "id", "relation_id", "field_id", "field", "field_name",
        "dataset_id", "operator", "values", "value", "default_value", "dynamic_default",
        "target_component_ids", "component_ids", "title", "name", "config",
        "filter_key", "filter_name", "show_name", "condition", "multiple_filter",
        "dynamics_filter", "dynamics_filter_value", "auto_search_default_value",
        "order_index", "extensions",
    }
    extensions = dict(item.get("extensions", {})) if isinstance(item.get("extensions"), Mapping) else {}
    extensions.update({
        str(key): _json_value(value)
        for key, value in item.items()
        if key not in known
    })
    values = item.get("values", item.get("value", []))
    if not isinstance(values, list):
        values = [values]
    relation_id = _optional_text(item.get("relation_id"))
    field_id = _optional_text(_first(item, "field_id", "field"))
    filter_key = str(
        item.get("filter_key")
        or f"{relation_id or '<missing-relation>'}::{filter_id}::{field_id or '<missing-field>'}"
    )
    return {
        "filter_key": filter_key,
        "filter_id": filter_id,
        "relation_id": relation_id,
        "field_id": field_id,
        "field_name": str(item.get("field_name") or item.get("show_name") or ""),
        "dataset_id": _optional_text(item.get("dataset_id")),
        "title": str(_first(item, "title", "name", "filter_name") or ""),
        "operator": str(item.get("operator") or item.get("condition") or ""),
        "values": _json_value(values),
        "default_value": _json_value(item.get("default_value")),
        "dynamic_default": _json_value(item.get("dynamic_default")),
        "dynamics_filter": _json_value(item.get("dynamics_filter")),
        "dynamics_filter_value": _json_value(item.get("dynamics_filter_value")),
        "auto_search_default_value": _json_value(item.get("auto_search_default_value")),
        "target_component_ids": _stable_unique(
            item.get("target_component_ids", item.get("component_ids", []))
        ),
        "config": _json_value(item.get("config", {})),
        "extensions": _json_value(extensions),
    }


def _normalize_component_filter(item: Mapping[str, Any]) -> dict[str, Any]:
    unit_id = _require_text(item.get("unit_id"), "component_filter.unit_id")
    field_id = _require_text(item.get("field_id"), "component_filter.field_id")
    return {
        "component_filter_key": str(
            item.get("component_filter_key") or f"{unit_id}::{field_id}"
        ),
        "unit_id": unit_id,
        "field_id": field_id,
        "business_name": str(item.get("business_name") or ""),
        "condition": _json_value(item.get("condition")),
        "filter_type": _json_value(item.get("filter_type", [])),
        "config": _json_value(item.get("config", {})),
    }


def _normalize_dataset(item: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "dataset_id": _require_text(_first(item, "dataset_id", "id"), "dataset.dataset_id"),
        "name": str(item.get("name") or ""),
        "source": _json_value(item.get("source", {})),
        "config": _json_value(item.get("config", {})),
    }


def _normalize_theme(item: Mapping[str, Any] | None) -> dict[str, Any]:
    value = item if isinstance(item, Mapping) else {}
    return {
        "background_color": _optional_text(
            _first(value, "background_color", "backgroundColor")
        ),
        "theme_type": _optional_text(_first(value, "theme_type", "themeType")),
        "style_id": _optional_text(_first(value, "style_id", "styleId")),
    }


def _ensure_unique(items: Sequence[Mapping[str, Any]], key: str, collection: str) -> None:
    values = [str(item.get(key, "")) for item in items]
    duplicates = sorted({value for value in values if values.count(value) > 1})
    if duplicates:
        raise ValueError(f"duplicate {collection} identity: {', '.join(duplicates)}")


def _normalize_list(
    values: Iterable[Mapping[str, Any]],
    normalizer: Any,
    identity: str,
    collection: str,
) -> list[dict[str, Any]]:
    result = [normalizer(item) for item in values]
    _ensure_unique(result, identity, collection)
    return sorted(result, key=lambda item: str(item[identity]))


def normalize_dashboard_profile(profile: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize a read-only dashboard profile and attach a stable state hash."""

    snapshot = profile.get("snapshot") if isinstance(profile.get("snapshot"), Mapping) else profile
    dashboard_meta = (
        snapshot.get("dashboard")
        if isinstance(snapshot.get("dashboard"), Mapping)
        else {}
    )
    domain = _require_text(profile.get("domain") or snapshot.get("domain"), "profile.domain")
    if domain not in PROFILE_DOMAINS:
        raise ValueError(f"unsupported profile domain: {domain}")
    dashboard_id = _require_text(
        profile.get("dashboard_id")
        or snapshot.get("dashboard_id")
        or _first(dashboard_meta, "dashboard_id", "id"),
        "profile.dashboard_id",
    )
    components = _normalize_list(
        snapshot.get("components", []), _normalize_component, "component_id", "component"
    )
    component_by_id = {item["component_id"]: item for item in components}
    raw_layout = snapshot.get("layout")
    if raw_layout is None:
        raw_layout = [
            {
                **dict(item.get("layout", {})),
                "component_id": _first(item, "component_id", "node_id", "id", "unit_id"),
            }
            for item in snapshot.get("components", [])
            if isinstance(item.get("layout"), Mapping)
        ]
    layout = [
        _normalize_layout(
            item,
            component_by_id.get(
                str(_first(item, "component_id", "node_id", "id", "unit_id"))
            ),
        )
        for item in raw_layout
    ]
    _ensure_unique(layout, "component_id", "layout")
    layout.sort(key=lambda item: item["component_id"])
    formulas = _normalize_list(snapshot.get("formulas", []), _normalize_formula, "formula_id", "formula")
    public_filters = _normalize_list(
        snapshot.get("public_filters", snapshot.get("filters", [])),
        _normalize_filter,
        "filter_key",
        "public filter",
    )
    component_filters = _normalize_list(
        snapshot.get("component_filters", []),
        _normalize_component_filter,
        "component_filter_key",
        "component filter",
    )
    datasets = _normalize_list(
        snapshot.get("datasets", []), _normalize_dataset, "dataset_id", "dataset"
    )
    theme = _normalize_theme(snapshot.get("theme"))
    raw_completeness = (
        profile.get("completeness")
        if isinstance(profile.get("completeness"), Mapping)
        else snapshot.get("completeness")
        if isinstance(snapshot.get("completeness"), Mapping)
        else {}
    )
    required_sections = _stable_unique(
        raw_completeness.get(
            "required",
            raw_completeness.get("required_sections", PROFILE_REQUIRED_SECTIONS),
        )
    )
    observed_sections = sorted(
        section
        for section in required_sections
        if section in snapshot
        and (
            isinstance(snapshot.get(section), list)
            or (section == "theme" and isinstance(snapshot.get(section), Mapping))
        )
        or section == "theme"
    )
    missing_sections = sorted(set(required_sections) - set(observed_sections))
    explicit_missing = _stable_unique(
        raw_completeness.get(
            "missing", raw_completeness.get("missing_sections", [])
        )
    )
    missing_sections = sorted(set(missing_sections) | set(explicit_missing))
    reasons = _stable_unique(raw_completeness.get("reasons", []))
    declared_status = str(raw_completeness.get("status") or "").strip()
    if declared_status and declared_status not in {"complete", "incomplete"}:
        reasons.append(f"unsupported completeness status: {declared_status}")
    if declared_status == "incomplete" and not reasons:
        reasons.append("source profile declared itself incomplete")
    completeness_status = (
        "complete"
        if not missing_sections and not reasons and declared_status != "incomplete"
        else "incomplete"
    )
    completeness = {
        "status": completeness_status,
        "required": required_sections,
        "observed": observed_sections,
        "missing": missing_sections,
        "reasons": sorted(set(reasons)),
        "details": _json_value(raw_completeness.get("details", {})),
    }
    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "artifact_type": "dashboard_profile",
        "mode": "read_only_profile",
        "domain": domain,
        "dashboard_id": dashboard_id,
        "dashboard_name": str(
            profile.get("dashboard_name")
            or snapshot.get("dashboard_name")
            or _first(dashboard_meta, "dashboard_name", "name")
            or ""
        ),
        "version_id": str(
            profile.get("version_id")
            or snapshot.get("version_id")
            or dashboard_meta.get("version_id")
            or "draft"
        ),
        "html_id": _optional_text(
            profile.get("html_id") or snapshot.get("html_id") or dashboard_meta.get("html_id")
        ),
        "draft_revision": _optional_text(
            profile.get("draft_revision")
            or snapshot.get("draft_revision")
            or dashboard_meta.get("draft_revision")
        ),
        "components": components,
        "layout": layout,
        "formulas": formulas,
        "public_filters": public_filters,
        "component_filters": component_filters,
        "datasets": datasets,
        "theme": theme,
        "layout_policy": _json_value(snapshot.get("layout_policy", {"max_columns": 24})),
        "completeness": completeness,
        "write_boundary": {
            "may_profile": True,
            "may_design": True,
            "may_diff": True,
            "may_modify_dashboard": False,
            "may_publish_dashboard": False,
        },
    }
    captured_at = _optional_text(profile.get("captured_at") or profile.get("profiled_at"))
    if captured_at:
        result["captured_at"] = captured_at
    result["profile_sha256"] = profile_sha256(result)
    return result


def _state_from_profile(profile: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "components": copy.deepcopy(profile.get("components", [])),
        "layout": copy.deepcopy(profile.get("layout", [])),
        "formulas": copy.deepcopy(profile.get("formulas", [])),
        "public_filters": copy.deepcopy(profile.get("public_filters", [])),
        "component_filters": copy.deepcopy(profile.get("component_filters", [])),
        "datasets": copy.deepcopy(profile.get("datasets", [])),
        "theme": copy.deepcopy(profile.get("theme", _normalize_theme(None))),
        "layout_policy": copy.deepcopy(profile.get("layout_policy", {})),
    }


def _normalize_desired_state(
    profile: Mapping[str, Any],
    *,
    desired_components: Sequence[Mapping[str, Any]] | None,
    desired_layout: Sequence[Mapping[str, Any]] | None,
    desired_formulas: Sequence[Mapping[str, Any]] | None,
    desired_public_filters: Sequence[Mapping[str, Any]] | None,
    desired_component_filters: Sequence[Mapping[str, Any]] | None,
    desired_theme: Mapping[str, Any] | None,
) -> dict[str, Any]:
    state = _state_from_profile(profile)
    if desired_components is not None:
        state["components"] = _normalize_list(
            desired_components, _normalize_component, "component_id", "component"
        )
    component_by_id = {item["component_id"]: item for item in state["components"]}
    if desired_layout is not None:
        state["layout"] = [
            _normalize_layout(item, component_by_id.get(str(_first(item, "component_id", "id", "unit_id"))))
            for item in desired_layout
        ]
        _ensure_unique(state["layout"], "component_id", "layout")
        state["layout"].sort(key=lambda item: item["component_id"])
    if desired_formulas is not None:
        state["formulas"] = _normalize_list(
            desired_formulas, _normalize_formula, "formula_id", "formula"
        )
    if desired_public_filters is not None:
        state["public_filters"] = _normalize_list(
            desired_public_filters, _normalize_filter, "filter_key", "public filter"
        )
    if desired_component_filters is not None:
        state["component_filters"] = _normalize_list(
            desired_component_filters,
            _normalize_component_filter,
            "component_filter_key",
            "component filter",
        )
    if desired_theme is not None:
        state["theme"] = _normalize_theme(desired_theme)
    return state


def _contract_domain_diagnostics(domain: str, values: Any, path: str = "") -> list[dict[str, Any]]:
    diagnostics: list[dict[str, Any]] = []
    if isinstance(values, Mapping):
        for key, value in values.items():
            child_path = f"{path}.{key}" if path else str(key)
            if key == "contract_id" and isinstance(value, str) and ":" in value:
                prefix = value.split(":", 1)[0]
                if prefix in SUPPORTED_DOMAINS and prefix != domain:
                    diagnostics.append(
                        _diagnostic(
                            "DASHBOARD_CROSS_DOMAIN_CONTRACT",
                            "error",
                            f"contract {value!r} does not belong to domain {domain!r}",
                            child_path,
                        )
                    )
            diagnostics.extend(_contract_domain_diagnostics(domain, value, child_path))
    elif isinstance(values, list):
        for index, value in enumerate(values):
            diagnostics.extend(_contract_domain_diagnostics(domain, value, f"{path}[{index}]"))
    return diagnostics


def _dataset_contract_evidence_diagnostics(
    dataset_spec: Mapping[str, Any], domain: str
) -> list[dict[str, Any]]:
    diagnostics: list[dict[str, Any]] = []
    collections = (
        ("fields", dataset_spec.get("fields", [])),
        ("scope_contracts", dataset_spec.get("scope_contracts", [])),
        ("default_filters", dataset_spec.get("default_filters", [])),
    )
    for collection, raw_items in collections:
        if not isinstance(raw_items, list):
            diagnostics.append(
                _diagnostic(
                    "DASHBOARD_DATASET_COLLECTION_INVALID",
                    "error",
                    f"DatasetSpec {collection} must be an array",
                    collection,
                )
            )
            continue
        for index, item in enumerate(raw_items):
            if not isinstance(item, Mapping):
                diagnostics.append(
                    _diagnostic(
                        "DASHBOARD_DATASET_ITEM_INVALID",
                        "error",
                        f"DatasetSpec {collection} entries must be objects",
                        f"{collection}[{index}]",
                    )
                )
                continue
            contract_id = item.get("contract_id")
            if collection == "scope_contracts":
                contract_id = contract_id or item.get("id")
            contract_expected = (
                collection == "scope_contracts"
                or item.get("role") == "scope_contract"
                or bool(contract_id)
            )
            if not contract_expected:
                # Neutral physical fields and ordinary time/display filters are allowed.
                continue
            path = f"{collection}[{index}]"
            contract_id_text = str(contract_id or "").strip()
            if not contract_id_text:
                diagnostics.append(
                    _diagnostic(
                        "DASHBOARD_CONTRACT_ID_REQUIRED",
                        "error",
                        "contract-backed dataset evidence requires contract_id",
                        f"{path}.contract_id",
                    )
                )
            elif not contract_id_text.startswith(f"{domain}:"):
                diagnostics.append(
                    _diagnostic(
                        "DASHBOARD_CONTRACT_ID_INVALID",
                        "error",
                        f"contract {contract_id_text!r} is not namespaced to {domain!r}",
                        f"{path}.contract_id",
                    )
                )
            if item.get("source_domain") != domain:
                diagnostics.append(
                    _diagnostic(
                        "DASHBOARD_CONTRACT_SOURCE_DOMAIN_INVALID",
                        "error",
                        "contract evidence source_domain must equal the resolved dashboard domain",
                        f"{path}.source_domain",
                    )
                )
            if item.get("contract_status") != "confirmed":
                diagnostics.append(
                    _diagnostic(
                        "DASHBOARD_CONTRACT_NOT_CONFIRMED",
                        "error",
                        "only confirmed contract evidence may enter DashboardDesignSpec",
                        f"{path}.contract_status",
                    )
                )
            source_path = str(item.get("source_path") or "").strip().replace("\\", "/")
            if not source_path:
                diagnostics.append(
                    _diagnostic(
                        "DASHBOARD_CONTRACT_SOURCE_PATH_REQUIRED",
                        "error",
                        "contract evidence requires a non-empty source_path",
                        f"{path}.source_path",
                    )
                )
            else:
                other_skill = next(
                    skill
                    for candidate_domain, skill in DOMAIN_SKILL_NAMES.items()
                    if candidate_domain != domain
                )
                path_parts = [part for part in source_path.split("/") if part]
                absolute_or_escaping = (
                    source_path.startswith("/")
                    or bool(re.match(r"^[A-Za-z]:/", source_path))
                    or ".." in path_parts
                )
                if absolute_or_escaping:
                    diagnostics.append(
                        _diagnostic(
                            "DASHBOARD_CONTRACT_SOURCE_PATH_INVALID",
                            "error",
                            "contract evidence source_path must be a non-escaping relative path",
                            f"{path}.source_path",
                        )
                    )
                if other_skill in path_parts or other_skill in source_path:
                    diagnostics.append(
                        _diagnostic(
                            "DASHBOARD_CONTRACT_SOURCE_CROSS_DOMAIN",
                            "error",
                            "contract evidence source_path references the other business skill",
                            f"{path}.source_path",
                        )
                    )
            if not re.fullmatch(r"[0-9a-f]{64}", str(item.get("source_sha256") or "")):
                diagnostics.append(
                    _diagnostic(
                        "DASHBOARD_CONTRACT_SOURCE_HASH_INVALID",
                        "error",
                        "contract evidence requires a canonical source_sha256",
                        f"{path}.source_sha256",
                    )
                )
    return diagnostics


def build_dashboard_design_spec(
    dataset_spec: Mapping[str, Any],
    profile: Mapping[str, Any],
    *,
    desired_components: Sequence[Mapping[str, Any]] | None = None,
    desired_layout: Sequence[Mapping[str, Any]] | None = None,
    desired_formulas: Sequence[Mapping[str, Any]] | None = None,
    desired_public_filters: Sequence[Mapping[str, Any]] | None = None,
    desired_component_filters: Sequence[Mapping[str, Any]] | None = None,
    desired_theme: Mapping[str, Any] | None = None,
    query_plan_sha256: str | None = None,
    design_intent: str = "preserve_current",
    business_skill_roots: Mapping[str, str | Path] | None = None,
    dashboard_domain_repo_root: Path | None = None,
) -> dict[str, Any]:
    """Build a design-only artifact from a P2 dataset spec and current profile."""

    normalized = normalize_dashboard_profile(profile)
    if dataset_spec.get("artifact_type") != "dashboard_dataset_spec":
        raise ValueError("dataset_spec must be a dashboard_dataset_spec")
    dataset_domain = _require_text(dataset_spec.get("domain"), "dataset_spec.domain")
    domain_diagnostics: list[dict[str, Any]] = []
    if normalized["domain"] not in SUPPORTED_DOMAINS:
        domain_diagnostics.append(
            _diagnostic(
                "DASHBOARD_DOMAIN_UNRESOLVED",
                "error",
                "dashboard domain must be resolved before design or apply",
                "domain",
            )
        )
    if dataset_domain != normalized["domain"]:
        domain_diagnostics.append(
            _diagnostic(
                "DASHBOARD_DOMAIN_MISMATCH",
                "error",
                f"dataset/profile domain mismatch: {dataset_domain!r} != {normalized['domain']!r}",
                "domain",
            )
        )
    if normalized.get("completeness", {}).get("status") != "complete":
        domain_diagnostics.append(
            _diagnostic(
                "DASHBOARD_PROFILE_INCOMPLETE",
                "error",
                "an incomplete read-only profile cannot become a DashboardDesignSpec",
                "completeness",
            )
        )
    if dataset_spec.get("status") != "ready":
        domain_diagnostics.append(
            _diagnostic(
                "DASHBOARD_DATASET_NOT_READY",
                "error",
                "DashboardDesignSpec requires a ready DashboardDatasetSpec",
                "status",
            )
        )
    dashboard_domain_resolution: dict[str, Any] = {
        "dashboard_id": normalized["dashboard_id"],
        "requested_domain": normalized["domain"],
        "status": "blocked",
        "registered_domain": None,
        "evidence": [],
    }
    if normalized["domain"] in SUPPORTED_DOMAINS:
        dashboard_domain_resolution, registration_diagnostics = (
            validate_dashboard_domain_registration(
                normalized["dashboard_id"],
                normalized["domain"],
                repo_root=dashboard_domain_repo_root,
            )
        )
        domain_diagnostics.extend(registration_diagnostics)
    desired_state = _normalize_desired_state(
        normalized,
        desired_components=desired_components,
        desired_layout=desired_layout,
        desired_formulas=desired_formulas,
        desired_public_filters=desired_public_filters,
        desired_component_filters=desired_component_filters,
        desired_theme=desired_theme,
    )
    embedded_query_plan_hash = _optional_text(dataset_spec.get("query_plan_sha256"))
    supplied_query_plan_hash = _optional_text(query_plan_sha256)
    effective_query_plan_hash = supplied_query_plan_hash or embedded_query_plan_hash
    actual_dataset_hash = artifact_sha256(dataset_spec, "dataset_spec_sha256")
    embedded_dataset_hash = _optional_text(dataset_spec.get("dataset_spec_sha256"))
    binding_diagnostics: list[dict[str, Any]] = []
    if not embedded_dataset_hash:
        binding_diagnostics.append(
            _diagnostic(
                "DASHBOARD_DATASET_SPEC_HASH_REQUIRED",
                "error",
                "DatasetSpec must carry its canonical dataset_spec_sha256",
                "dataset_spec_sha256",
            )
        )
    elif not re.fullmatch(r"[0-9a-f]{64}", embedded_dataset_hash):
        binding_diagnostics.append(
            _diagnostic(
                "DASHBOARD_DATASET_SPEC_HASH_INVALID",
                "error",
                "dataset_spec_sha256 must be a canonical lowercase SHA-256",
                "dataset_spec_sha256",
            )
        )
    elif embedded_dataset_hash != actual_dataset_hash:
        binding_diagnostics.append(
            _diagnostic(
                "DASHBOARD_DATASET_SPEC_HASH_MISMATCH",
                "error",
                "embedded dataset_spec_sha256 does not match the canonical DatasetSpec",
                "dataset_spec_sha256",
            )
        )
    if not embedded_query_plan_hash:
        binding_diagnostics.append(
            _diagnostic(
                "DASHBOARD_QUERY_PLAN_HASH_REQUIRED",
                "error",
                "DatasetSpec must bind its source QueryPlan SHA-256",
                "query_plan_sha256",
            )
        )
    elif not re.fullmatch(r"[0-9a-f]{64}", embedded_query_plan_hash):
        binding_diagnostics.append(
            _diagnostic(
                "DASHBOARD_QUERY_PLAN_HASH_INVALID",
                "error",
                "query_plan_sha256 must be a canonical lowercase SHA-256",
                "query_plan_sha256",
            )
        )
    if supplied_query_plan_hash and not re.fullmatch(
        r"[0-9a-f]{64}", supplied_query_plan_hash
    ):
        binding_diagnostics.append(
            _diagnostic(
                "DASHBOARD_QUERY_PLAN_HASH_INVALID",
                "error",
                "explicit query_plan_sha256 must be a canonical lowercase SHA-256",
                "query_plan_sha256",
            )
        )
    if (
        embedded_query_plan_hash
        and supplied_query_plan_hash
        and embedded_query_plan_hash != supplied_query_plan_hash
    ):
        binding_diagnostics.append(
            _diagnostic(
                "DASHBOARD_QUERY_PLAN_HASH_CONFLICT",
                "error",
                "explicit query_plan_sha256 conflicts with the DatasetSpec binding",
                "query_plan_sha256",
            )
        )
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "artifact_type": "dashboard_design_spec",
        "mode": "design_only",
        "domain": normalized["domain"],
        "dashboard_id": normalized["dashboard_id"],
        "dashboard_name": normalized["dashboard_name"],
        "dashboard_domain_resolution": dashboard_domain_resolution,
        "source_profile_sha256": normalized["profile_sha256"],
        "source_plan_id": _optional_text(dataset_spec.get("plan_id")),
        "query_plan_sha256": effective_query_plan_hash,
        "dataset_spec_sha256": actual_dataset_hash,
        "design_intent": str(design_intent or "preserve_current"),
        "available_fields": _json_value(dataset_spec.get("fields", [])),
        "dataset_default_filters": _json_value(dataset_spec.get("default_filters", [])),
        "desired_components": desired_state["components"],
        "desired_layout": desired_state["layout"],
        "desired_formulas": desired_state["formulas"],
        "desired_public_filters": desired_state["public_filters"],
        "desired_component_filters": desired_state["component_filters"],
        "desired_datasets": desired_state["datasets"],
        "desired_theme": desired_state["theme"],
        "layout_policy": desired_state["layout_policy"],
        "write_boundary": {
            "phase": "P3A_design",
            "may_generate_diff": True,
            "may_dry_run": True,
            "apply_authorized": False,
            "may_publish_dashboard": False,
        },
    }
    diagnostics = domain_diagnostics + binding_diagnostics
    if normalized["domain"] in SUPPORTED_DOMAINS:
        diagnostics.extend(
            _dataset_contract_evidence_diagnostics(dataset_spec, normalized["domain"])
        )
        diagnostics.extend(
            validate_dataset_contract_registry_evidence(
                dataset_spec,
                normalized["domain"],
                business_skill_roots=business_skill_roots,
            )
        )
    if payload["domain"] in SUPPORTED_DOMAINS:
        diagnostics.extend(_contract_domain_diagnostics(payload["domain"], payload))
    payload["diagnostics"] = diagnostics
    payload["status"] = "blocked" if _has_errors(diagnostics) else "ready"
    payload["design_sha256"] = artifact_sha256(payload, "design_sha256")
    return payload


def _diagnostic(code: str, severity: str, message: str, path: str | None = None) -> dict[str, Any]:
    return {
        key: value
        for key, value in {
            "code": code,
            "severity": severity,
            "message": message,
            "path": path,
        }.items()
        if value is not None
    }


def _has_errors(diagnostics: Iterable[Mapping[str, Any]]) -> bool:
    return any(item.get("severity") == "error" for item in diagnostics)


def _items_by_id(items: Sequence[Mapping[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    return {str(item[key]): dict(item) for item in items}


def _target_for(collection: str, item: Mapping[str, Any]) -> dict[str, Any]:
    if collection == "components":
        return {
            "component_id": item.get("component_id"),
            "unit_id": item.get("unit_id"),
        }
    if collection == "layout":
        return {
            "component_id": item.get("component_id"),
            "unit_id": item.get("unit_id"),
        }
    if collection == "formulas":
        return {"formula_id": item.get("formula_id")}
    if collection == "public_filters":
        return {
            "filter_id": item.get("filter_id"),
            "relation_id": item.get("relation_id"),
            "field_id": item.get("field_id"),
        }
    if collection == "component_filters":
        return {
            "unit_id": item.get("unit_id"),
            "field_id": item.get("field_id"),
        }
    return {"dataset_id": item.get("dataset_id")}


def _operation(
    operation_type: str,
    collection: str,
    before: Mapping[str, Any] | None,
    after: Mapping[str, Any] | None,
    *,
    risk: str,
    allowed: bool,
    blocked_reasons: Sequence[str] = (),
    target_override: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    target_item = after or before or {}
    body: dict[str, Any] = {
        "type": operation_type,
        "collection": collection,
        "target": _json_value(target_override or _target_for(collection, target_item)),
        "before": _json_value(before),
        "after": _json_value(after),
        "write_status": "supported" if allowed else "blocked_unsupported",
        "status": "planned",
        "risk": risk,
        "blocked_reasons": sorted(set(blocked_reasons)),
    }
    body["operation_id"] = f"op_{canonical_sha256(body)[:16]}"
    return body


def _component_field_entries(component: Mapping[str, Any]) -> list[dict[str, Any]]:
    fields = component.get("fields")
    if not isinstance(fields, Mapping):
        return []
    entries: list[dict[str, Any]] = []
    for collection_name in ("dimensions", "metrics"):
        values = fields.get(collection_name, [])
        if not isinstance(values, list):
            return []
        for item in values:
            if not isinstance(item, Mapping):
                return []
            entry = copy.deepcopy(dict(item))
            entry["_collection"] = collection_name
            entries.append(entry)
    return entries


def _component_field_group(item: Mapping[str, Any]) -> str | None:
    group = str(item.get("group") or "")
    return {
        "row_dimension": "unitRowDimensionList",
        "column_dimension": "unitColumnDimensionList",
        "measure": "unitMeasureList",
    }.get(group)


def _single_component_field_rename(
    before: Mapping[str, Any], after: Mapping[str, Any]
) -> tuple[dict[str, Any] | None, list[str]]:
    before_items = _component_field_entries(before)
    after_items = _component_field_entries(after)
    reasons: list[str] = []
    if not before.get("unit_id") or before.get("unit_id") != after.get("unit_id"):
        reasons.append("component field rename requires one stable unit_id")
    if len(before_items) != len(after_items):
        reasons.append("component field add/delete is outside P4B")
        return None, reasons
    changes: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for old, new in zip(before_items, after_items):
        old_identity = (old.get("_collection"), old.get("field_id"))
        new_identity = (new.get("_collection"), new.get("field_id"))
        if old_identity != new_identity:
            reasons.append("component field identity or ordering changed")
            return None, reasons
        old_without_name = {key: value for key, value in old.items() if key != "business_name"}
        new_without_name = {key: value for key, value in new.items() if key != "business_name"}
        if old_without_name != new_without_name:
            reasons.append("only an existing field display name may change")
            return None, reasons
        if old.get("business_name") != new.get("business_name"):
            changes.append((old, new))
    if len(changes) != 1:
        reasons.append("P4B component apply requires exactly one field display-name change")
        return None, reasons
    old, new = changes[0]
    field_group = _component_field_group(new)
    if not field_group:
        reasons.append("component field group has no verified write mapping")
        return None, reasons
    if not str(new.get("business_name") or "").strip():
        reasons.append("component field display name must be non-empty")
        return None, reasons
    if reasons:
        return None, reasons
    return {
        "component_id": after.get("component_id"),
        "unit_id": after.get("unit_id"),
        "field_group": field_group,
        "field_id": new.get("field_id"),
    }, []


def _component_operations(
    before: Mapping[str, Any], after: Mapping[str, Any]
) -> list[dict[str, Any]]:
    operations: list[dict[str, Any]] = []
    if before.get("component_type") != after.get("component_type"):
        operations.append(
            _operation(
                "change_component_type", "components", before, after,
                risk="high", allowed=False,
                blocked_reasons=["component type changes are outside P3B"],
            )
        )
        return operations
    if before.get("dataset_id") != after.get("dataset_id"):
        operations.append(
            _operation(
                "rebind_dataset", "components", before, after,
                risk="high", allowed=False,
                blocked_reasons=["dataset rebinding is outside P3B"],
            )
        )
    if (
        before.get("container_id") != after.get("container_id")
        or before.get("tab_id") != after.get("tab_id")
    ):
        operations.append(
            _operation(
                "move_component_container", "components", before, after,
                risk="high", allowed=False,
                blocked_reasons=["cross-container or cross-tab moves are outside P3B"],
            )
        )
    field_keys = {"fields", "formula_ids", "filter_ids"}
    if any(before.get(key) != after.get(key) for key in field_keys):
        target, reasons = _single_component_field_rename(before, after)
        safe = (
            target is not None
            and before.get("formula_ids") == after.get("formula_ids")
            and before.get("filter_ids") == after.get("filter_ids")
        )
        if before.get("formula_ids") != after.get("formula_ids"):
            reasons.append("component formula binding changes are outside P4B")
        if before.get("filter_ids") != after.get("filter_ids"):
            reasons.append("component filter binding changes are outside P4B")
        operations.append(
            _operation(
                "update_component_fields", "components", before, after,
                risk="low" if safe else "high", allowed=safe,
                blocked_reasons=reasons,
                target_override=target,
            )
        )
    ignored = field_keys | {
        "component_id", "unit_id", "component_type", "dataset_id", "container_id", "tab_id"
    }
    if any(before.get(key) != after.get(key) for key in set(before) | set(after) if key not in ignored):
        operations.append(
            _operation(
                "update_existing_component", "components", before, after,
                risk="low", allowed=False,
                blocked_reasons=["component presentation edits are diff-only in P3A"],
            )
        )
    return operations


def _diff_collection(
    collection: str,
    identity: str,
    before_items: Sequence[Mapping[str, Any]],
    after_items: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    before = _items_by_id(before_items, identity)
    after = _items_by_id(after_items, identity)
    operations: list[dict[str, Any]] = []
    for item_id in sorted(set(before) | set(after)):
        old = before.get(item_id)
        new = after.get(item_id)
        if old is None:
            operations.append(
                _operation(
                    f"create_{collection.rstrip('s')}", collection, None, new,
                    risk="high", allowed=False,
                    blocked_reasons=["create operations are outside P3B"],
                )
            )
            continue
        if new is None:
            operations.append(
                _operation(
                    f"delete_{collection.rstrip('s')}", collection, old, None,
                    risk="high", allowed=False,
                    blocked_reasons=["delete operations are outside P3B"],
                )
            )
            continue
        if old == new:
            continue
        if collection == "components":
            operations.extend(_component_operations(old, new))
        elif collection == "layout":
            container_changed = (
                old.get("container_id") != new.get("container_id")
                or old.get("tab_id") != new.get("tab_id")
            )
            changed_keys = {
                key for key in set(old) | set(new) if old.get(key) != new.get(key)
            }
            verified_keys = {"x", "y", "w", "h"}
            stable_keys = {"component_id", "unit_id", "container_id", "tab_id", "z"}
            stable_identity = all(old.get(key) == new.get(key) for key in stable_keys)
            safe_layout = (
                not container_changed
                and stable_identity
                and bool(changed_keys)
                and changed_keys <= verified_keys
            )
            reasons = []
            if container_changed:
                reasons.append("cross-container or cross-tab moves are outside P3B")
            if not stable_identity:
                reasons.append("layout apply requires stable component, unit, container, tab, and z")
            if changed_keys - verified_keys:
                reasons.append("only x/y/w/h layout keys have a verified P4B adapter")
            operations.append(
                _operation(
                    "move_component_container" if container_changed else "update_layout",
                    collection, old, new,
                    risk="low" if safe_layout else "high",
                    allowed=safe_layout,
                    blocked_reasons=reasons,
                )
            )
        elif collection == "formulas":
            shared = bool(old.get("shared") or new.get("shared"))
            safe_scope = old.get("scope") == new.get("scope") == "component"
            component_ids = set(old.get("component_ids", [])) | set(new.get("component_ids", []))
            changed_keys = {
                key for key in set(old) | set(new) if old.get(key) != new.get(key)
            }
            safe = (
                not shared
                and safe_scope
                and len(component_ids) == 1
                and changed_keys == {"expression"}
                and bool(str(new.get("expression") or "").strip())
            )
            reasons: list[str] = []
            if shared:
                reasons.append("shared formula updates require impact review")
            if not safe_scope:
                reasons.append("only component-local formula updates are supported in P3B")
            if len(component_ids) > 1:
                reasons.append("formula affects multiple components")
            if len(component_ids) != 1:
                reasons.append("formula apply requires exactly one affected component")
            if changed_keys != {"expression"}:
                reasons.append("only an existing formula expression may change; dependencies and identity must remain stable")
            if not str(new.get("expression") or "").strip():
                reasons.append("formula expression must be non-empty")
            operations.append(
                _operation(
                    "update_formula", collection, old, new,
                    risk="medium" if safe else "high", allowed=safe,
                    blocked_reasons=reasons,
                )
            )
        elif collection == "public_filters":
            binding_keys = {
                "filter_key", "filter_id", "relation_id", "field_id", "dataset_id",
                "target_component_ids",
            }
            binding_changed = any(old.get(key) != new.get(key) for key in binding_keys)
            dynamic_keys = {
                "dynamic_default", "default_value", "dynamics_filter",
                "dynamics_filter_value", "auto_search_default_value",
            }
            changed_keys = {
                key for key in set(old) | set(new)
                if old.get(key) != new.get(key)
            }
            dynamic_default_only = bool(changed_keys) and changed_keys <= dynamic_keys
            stable_identity = all(
                old.get(key) and old.get(key) == new.get(key)
                for key in ("filter_id", "relation_id", "field_id")
            )
            valid_dynamic_value = new.get("dynamics_filter_value") not in (None, "")
            valid_dynamic_mode = (
                new.get("dynamics_filter") is True
                and new.get("auto_search_default_value") is False
            )
            supported_dynamic_default = (
                not binding_changed
                and dynamic_default_only
                and stable_identity
                and valid_dynamic_value
                and valid_dynamic_mode
            )
            reasons: list[str] = []
            if binding_changed:
                reasons.append("filter binding changes are outside P3B")
            elif dynamic_default_only and not stable_identity:
                reasons.append(
                    "dynamic-default apply requires stable filter_id, relation_id, and field_id"
                )
            elif dynamic_default_only and not valid_dynamic_value:
                reasons.append("dynamics_filter_value must be explicit and non-empty")
            elif dynamic_default_only and not valid_dynamic_mode:
                reasons.append(
                    "supported dynamic defaults require dynamics_filter=true and auto_search_default_value=false"
                )
            elif not dynamic_default_only:
                reasons.append("generic filter edits are diff-only in P3A")
            operations.append(
                _operation(
                    (
                        "rebind_filter"
                        if binding_changed
                        else "update_filter_dynamic_default"
                        if dynamic_default_only
                        else "update_filter"
                    ),
                    collection, old, new,
                    risk="low" if supported_dynamic_default else "high" if binding_changed else "medium",
                    allowed=supported_dynamic_default,
                    blocked_reasons=reasons,
                )
            )
        elif collection == "component_filters":
            operations.append(
                _operation(
                    "update_component_filter", collection, old, new,
                    risk="medium", allowed=False,
                    blocked_reasons=["component filter edits are diff-only in P3A"],
                )
            )
        else:
            operations.append(
                _operation(
                    "replace_dataset", collection, old, new,
                    risk="high", allowed=False,
                    blocked_reasons=["dataset replacement is outside P3B"],
                )
            )
    return operations


def _rectangles_overlap(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    if (left.get("container_id"), left.get("tab_id")) != (
        right.get("container_id"), right.get("tab_id")
    ):
        return False
    return not (
        float(left["x"]) + float(left["w"]) <= float(right["x"])
        or float(right["x"]) + float(right["w"]) <= float(left["x"])
        or float(left["y"]) + float(left["h"]) <= float(right["y"])
        or float(right["y"]) + float(right["h"]) <= float(left["y"])
    )


def _collision_pairs(layout: Sequence[Mapping[str, Any]]) -> set[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()
    for index, left in enumerate(layout):
        for right in layout[index + 1 :]:
            if _rectangles_overlap(left, right):
                pairs.add(tuple(sorted((str(left["component_id"]), str(right["component_id"])))))
    return pairs


def _layout_diagnostics(
    baseline: Mapping[str, Any], target: Mapping[str, Any]
) -> list[dict[str, Any]]:
    diagnostics: list[dict[str, Any]] = []
    before_by_id = _items_by_id(baseline.get("layout", []), "component_id")
    after_layout = target.get("layout", [])
    max_columns = float(target.get("layout_policy", {}).get("max_columns", 24))
    for index, item in enumerate(after_layout):
        changed = before_by_id.get(str(item["component_id"])) != item
        if not changed:
            continue
        if float(item["x"]) < 0 or float(item["y"]) < 0 or float(item["w"]) <= 0 or float(item["h"]) <= 0:
            diagnostics.append(
                _diagnostic(
                    "DASHBOARD_LAYOUT_INVALID_BOUNDS", "error",
                    f"layout for {item['component_id']} has invalid coordinates or size",
                    f"target_state.layout[{index}]",
                )
            )
        if float(item["x"]) + float(item["w"]) > max_columns:
            diagnostics.append(
                _diagnostic(
                    "DASHBOARD_LAYOUT_OUT_OF_GRID", "error",
                    f"layout for {item['component_id']} exceeds {max_columns:g} columns",
                    f"target_state.layout[{index}]",
                )
            )
    new_collisions = _collision_pairs(after_layout) - _collision_pairs(baseline.get("layout", []))
    for left, right in sorted(new_collisions):
        diagnostics.append(
            _diagnostic(
                "DASHBOARD_LAYOUT_COLLISION", "error",
                f"desired layout introduces a collision between {left} and {right}",
                "target_state.layout",
            )
        )
    return diagnostics


def _formula_dependency_ids(formula: Mapping[str, Any]) -> list[str]:
    ids: list[str] = []
    for dependency in formula.get("dependencies", []):
        if isinstance(dependency, Mapping):
            if dependency.get("kind") == "formula" and dependency.get("id"):
                ids.append(str(dependency["id"]))
        elif dependency:
            ids.append(str(dependency))
    return ids


def _formula_diagnostics(state: Mapping[str, Any]) -> list[dict[str, Any]]:
    formulas = _items_by_id(state.get("formulas", []), "formula_id")
    graph = {
        formula_id: [dep for dep in _formula_dependency_ids(formula) if dep in formulas]
        for formula_id, formula in formulas.items()
    }
    visiting: set[str] = set()
    visited: set[str] = set()
    diagnostics: list[dict[str, Any]] = []

    def visit(node: str, path: list[str]) -> None:
        if node in visiting:
            start = path.index(node) if node in path else 0
            cycle = path[start:] + [node]
            diagnostics.append(
                _diagnostic(
                    "DASHBOARD_FORMULA_CYCLE", "error",
                    "formula dependency cycle: " + " -> ".join(cycle),
                    "target_state.formulas",
                )
            )
            return
        if node in visited:
            return
        visiting.add(node)
        for dependency in graph.get(node, []):
            visit(dependency, path + [node])
        visiting.remove(node)
        visited.add(node)

    for formula_id in sorted(graph):
        visit(formula_id, [])
    unique: dict[tuple[str, str], dict[str, Any]] = {}
    for item in diagnostics:
        unique[(str(item["code"]), str(item["message"]))] = item
    return list(unique.values())


def _design_state(design: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "components": copy.deepcopy(design.get("desired_components", [])),
        "layout": copy.deepcopy(design.get("desired_layout", [])),
        "formulas": copy.deepcopy(design.get("desired_formulas", [])),
        "public_filters": copy.deepcopy(design.get("desired_public_filters", [])),
        "component_filters": copy.deepcopy(design.get("desired_component_filters", [])),
        "datasets": copy.deepcopy(design.get("desired_datasets", [])),
        "theme": copy.deepcopy(design.get("desired_theme", _normalize_theme(None))),
        "layout_policy": copy.deepcopy(design.get("layout_policy", {})),
    }


def _theme_operation(
    before: Mapping[str, Any], after: Mapping[str, Any]
) -> dict[str, Any] | None:
    if before == after:
        return None
    changed_keys = {
        key for key in set(before) | set(after) if before.get(key) != after.get(key)
    }
    background = str(after.get("background_color") or "")
    safe = changed_keys == {"background_color"} and bool(
        re.fullmatch(r"#[0-9A-Fa-f]{6}", background)
    )
    reasons: list[str] = []
    if changed_keys != {"background_color"}:
        reasons.append("only the dashboard root background color is writable in P4B")
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", background):
        reasons.append("root background color must be an explicit #RRGGBB value")
    return _operation(
        "update_theme",
        "theme",
        before,
        after,
        risk="low" if safe else "high",
        allowed=safe,
        blocked_reasons=reasons,
        target_override={"scope": "dashboard_root"},
    )


def _diff_states(
    baseline: Mapping[str, Any], target: Mapping[str, Any]
) -> list[dict[str, Any]]:
    operations: list[dict[str, Any]] = []
    for collection, identity in (
        ("components", "component_id"),
        ("layout", "component_id"),
        ("formulas", "formula_id"),
        ("public_filters", "filter_key"),
        ("component_filters", "component_filter_key"),
        ("datasets", "dataset_id"),
    ):
        operations.extend(
            _diff_collection(
                collection,
                identity,
                baseline.get(collection, []),
                target.get(collection, []),
            )
        )
    theme_operation = _theme_operation(
        baseline.get("theme", _normalize_theme(None)),
        target.get("theme", _normalize_theme(None)),
    )
    if theme_operation is not None:
        operations.append(theme_operation)
    operations.sort(key=lambda item: (item["type"], item["operation_id"]))
    return operations


def diff_dashboard(profile: Mapping[str, Any], design_spec: Mapping[str, Any]) -> dict[str, Any]:
    """Create a deterministic P3A dry-run plan from current and desired state."""

    normalized = normalize_dashboard_profile(profile)
    diagnostics: list[dict[str, Any]] = []
    if design_spec.get("artifact_type") != "dashboard_design_spec":
        raise ValueError("design_spec must be a dashboard_design_spec")
    if design_spec.get("domain") != normalized["domain"]:
        diagnostics.append(
            _diagnostic("DASHBOARD_DOMAIN_MISMATCH", "error", "profile/design domain mismatch", "domain")
        )
    if str(design_spec.get("dashboard_id")) != normalized["dashboard_id"]:
        diagnostics.append(
            _diagnostic(
                "DASHBOARD_ID_MISMATCH", "error", "profile/design dashboard_id mismatch", "dashboard_id"
            )
        )
    expected_design_hash = artifact_sha256(design_spec, "design_sha256")
    if design_spec.get("design_sha256") != expected_design_hash:
        diagnostics.append(
            _diagnostic("DASHBOARD_DESIGN_HASH_MISMATCH", "error", "design hash is invalid", "design_sha256")
        )
    if design_spec.get("source_profile_sha256") != normalized["profile_sha256"]:
        diagnostics.append(
            _diagnostic(
                "DASHBOARD_PROFILE_STALE", "error",
                "current profile no longer matches the design source hash",
                "source_profile_sha256",
            )
        )
    if design_spec.get("status") == "blocked":
        diagnostics.extend(copy.deepcopy(design_spec.get("diagnostics", [])))
    baseline = _state_from_profile(normalized)
    target = _design_state(design_spec)
    operations = _diff_states(baseline, target)
    diagnostics.extend(_layout_diagnostics(baseline, target))
    diagnostics.extend(_formula_diagnostics(target))
    diagnostics.extend(_contract_domain_diagnostics(normalized["domain"], target, "target_state"))
    for operation in operations:
        if operation["write_status"] != "supported":
            diagnostics.append(
                _diagnostic(
                    "DASHBOARD_OPERATION_BLOCKED", "error",
                    f"{operation['type']} is blocked: " + "; ".join(operation["blocked_reasons"]),
                    f"operations[{operation['operation_id']}]",
                )
            )
        elif operation["type"] not in SAFE_OPERATION_TYPES:
            diagnostics.append(
                _diagnostic(
                    "DASHBOARD_OPERATION_NOT_ALLOWLISTED", "error",
                    f"{operation['type']} is not in the P3B allowlist",
                    f"operations[{operation['operation_id']}]",
                )
            )
    blocked_reasons = sorted(
        {str(item["message"]) for item in diagnostics if item.get("severity") == "error"}
    )
    if blocked_reasons:
        status = "blocked"
    elif not operations:
        status = "no_changes"
    else:
        status = "ready_for_dry_run"
    plan: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "artifact_type": "dashboard_change_plan",
        "mode": "dry_run_only",
        "domain": normalized["domain"],
        "dashboard_id": normalized["dashboard_id"],
        "dashboard_name": normalized["dashboard_name"],
        "base_profile_sha256": normalized["profile_sha256"],
        "design_sha256": str(design_spec.get("design_sha256") or ""),
        "query_plan_sha256": design_spec.get("query_plan_sha256"),
        "dataset_spec_sha256": design_spec.get("dataset_spec_sha256"),
        "status": status,
        "dry_run": True,
        "operations": operations,
        "blocked_reasons": blocked_reasons,
        "diagnostics": diagnostics,
        "baseline_state": baseline,
        "target_state": target,
        "summary": {
            "operation_count": len(operations),
            "supported_count": sum(item["write_status"] == "supported" for item in operations),
            "blocked_count": sum(item["write_status"] != "supported" for item in operations),
            "risk_counts": {
                risk: sum(item["risk"] == risk for item in operations)
                for risk in ("low", "medium", "high")
            },
        },
        "authorization": {
            "apply_authorized": False,
            "publish_authorized": False,
            "requires_explicit_apply_authorization": True,
            "requires_separate_publish_confirmation": True,
        },
        "write_boundary": {
            "may_dry_run": True,
            "may_apply_from_this_artifact_alone": False,
            "may_publish_dashboard": False,
        },
    }
    plan["change_plan_sha256"] = artifact_sha256(plan, "change_plan_sha256")
    return plan


def validate_dashboard_change_plan(
    plan: Mapping[str, Any], current_profile: Mapping[str, Any] | None = None
) -> list[dict[str, Any]]:
    """Validate a plan before dry-run or explicit P3B apply authorization."""

    diagnostics: list[dict[str, Any]] = []
    if plan.get("artifact_type") != "dashboard_change_plan":
        return [_diagnostic("DASHBOARD_CHANGE_PLAN_REQUIRED", "error", "invalid artifact type")]
    if plan.get("change_plan_sha256") != artifact_sha256(plan, "change_plan_sha256"):
        diagnostics.append(
            _diagnostic(
                "DASHBOARD_CHANGE_PLAN_HASH_MISMATCH", "error",
                "change plan hash is invalid", "change_plan_sha256",
            )
        )
    for field in (
        "base_profile_sha256",
        "design_sha256",
        "query_plan_sha256",
        "dataset_spec_sha256",
        "change_plan_sha256",
    ):
        if not re.fullmatch(r"[0-9a-f]{64}", str(plan.get(field) or "")):
            diagnostics.append(
                _diagnostic(
                    "DASHBOARD_HASH_BINDING_INVALID", "error",
                    f"{field} must be a canonical lowercase SHA-256",
                    field,
                )
            )
    if plan.get("domain") not in SUPPORTED_DOMAINS:
        diagnostics.append(_diagnostic("DASHBOARD_DOMAIN_INVALID", "error", "unsupported domain", "domain"))
    if plan.get("status") == "blocked" or plan.get("blocked_reasons"):
        diagnostics.append(
            _diagnostic(
                "DASHBOARD_CHANGE_PLAN_BLOCKED", "error",
                "change plan contains blocking diagnostics and cannot be applied",
                "blocked_reasons",
            )
        )
    if plan.get("dry_run") is not True or plan.get("mode") != "dry_run_only":
        diagnostics.append(
            _diagnostic("DASHBOARD_DRY_RUN_REQUIRED", "error", "change plans must remain dry-run only", "mode")
        )
    expected_authorization = {
        "apply_authorized": False,
        "publish_authorized": False,
        "requires_explicit_apply_authorization": True,
        "requires_separate_publish_confirmation": True,
    }
    if plan.get("authorization") != expected_authorization:
        diagnostics.append(
            _diagnostic(
                "DASHBOARD_PLAN_AUTHORIZATION_INVALID", "error",
                "a change plan must retain the fixed no-authorization boundary",
                "authorization",
            )
        )
    expected_write_boundary = {
        "may_dry_run": True,
        "may_apply_from_this_artifact_alone": False,
        "may_publish_dashboard": False,
    }
    if plan.get("write_boundary") != expected_write_boundary:
        diagnostics.append(
            _diagnostic(
                "DASHBOARD_PLAN_WRITE_BOUNDARY_INVALID", "error",
                "a change plan must retain the fixed dry-run-only write boundary",
                "write_boundary",
            )
        )
    operations = plan.get("operations", [])
    if not isinstance(operations, list):
        diagnostics.append(
            _diagnostic("DASHBOARD_OPERATIONS_INVALID", "error", "operations must be an array", "operations")
        )
        operations = []
    recomputed_operations = _diff_states(
        plan.get("baseline_state", {}), plan.get("target_state", {})
    )
    if operations != recomputed_operations:
        diagnostics.append(
            _diagnostic(
                "DASHBOARD_OPERATIONS_STATE_MISMATCH", "error",
                "operations do not equal the canonical diff of baseline_state and target_state",
                "operations",
            )
        )
    operation_ids = [str(item.get("operation_id") or "") for item in operations]
    if len(operation_ids) != len(set(operation_ids)):
        diagnostics.append(
            _diagnostic(
                "DASHBOARD_OPERATION_ID_DUPLICATE", "error",
                "operation_id values must be unique", "operations",
            )
        )
    for index, operation in enumerate(operations):
        operation_type = str(operation.get("type") or "")
        if operation_type not in SAFE_OPERATION_TYPES:
            diagnostics.append(
                _diagnostic(
                    "DASHBOARD_OPERATION_NOT_ALLOWLISTED", "error",
                    f"operation {operation.get('type')!r} is not P3B-safe",
                    f"operations[{index}].type",
                )
            )
        target = operation.get("target") if isinstance(operation.get("target"), Mapping) else {}
        after = operation.get("after") if isinstance(operation.get("after"), Mapping) else {}
        if operation_type == "update_filter_dynamic_default" and not all(
            target.get(key) for key in ("relation_id", "filter_id", "field_id")
        ):
            diagnostics.append(
                _diagnostic(
                    "DASHBOARD_FILTER_STABLE_ID_REQUIRED", "error",
                    "supported filter apply requires relation_id, filter_id, and field_id",
                    f"operations[{index}].target",
                )
            )
        if operation_type == "update_filter_dynamic_default" and not (
            after.get("dynamics_filter") is True
            and after.get("dynamics_filter_value") not in (None, "")
            and after.get("auto_search_default_value") is False
        ):
            diagnostics.append(
                _diagnostic(
                    "DASHBOARD_FILTER_DYNAMIC_DEFAULT_INVALID", "error",
                    "supported filter apply requires an explicit verified dynamic default",
                    f"operations[{index}].after",
                )
            )
        if operation_type == "update_layout" and not target.get("component_id"):
            diagnostics.append(
                _diagnostic(
                    "DASHBOARD_LAYOUT_STABLE_ID_REQUIRED", "error",
                    "layout apply requires a stable component_id",
                    f"operations[{index}].target",
                )
            )
        if operation_type == "update_component_fields" and not all(
            target.get(key) for key in ("component_id", "unit_id", "field_group", "field_id")
        ):
            diagnostics.append(
                _diagnostic(
                    "DASHBOARD_COMPONENT_FIELD_STABLE_ID_REQUIRED", "error",
                    "component field apply requires component_id, unit_id, field_group, and field_id",
                    f"operations[{index}].target",
                )
            )
        if operation_type == "update_formula" and not target.get("formula_id"):
            diagnostics.append(
                _diagnostic(
                    "DASHBOARD_FORMULA_STABLE_ID_REQUIRED", "error",
                    "formula apply requires a stable formula_id",
                    f"operations[{index}].target",
                )
            )
        if operation_type == "update_theme" and target.get("scope") != "dashboard_root":
            diagnostics.append(
                _diagnostic(
                    "DASHBOARD_THEME_SCOPE_INVALID", "error",
                    "theme apply is limited to dashboard_root",
                    f"operations[{index}].target",
                )
            )
        if operation.get("write_status") != "supported":
            diagnostics.append(
                _diagnostic(
                    "DASHBOARD_OPERATION_BLOCKED", "error",
                    f"operation {operation.get('operation_id')!r} is blocked",
                    f"operations[{index}].write_status",
                )
            )
    blocked_operation = any(
        item.get("write_status") != "supported" or item.get("type") not in SAFE_OPERATION_TYPES
        for item in operations
    )
    if blocked_operation or plan.get("blocked_reasons"):
        expected_status = "blocked"
    elif operations:
        expected_status = "ready_for_dry_run"
    else:
        expected_status = "no_changes"
    if plan.get("status") != expected_status:
        diagnostics.append(
            _diagnostic(
                "DASHBOARD_CHANGE_PLAN_STATUS_INCONSISTENT", "error",
                f"status must be {expected_status!r} for the contained operations",
                "status",
            )
        )
    diagnostics.extend(_layout_diagnostics(plan.get("baseline_state", {}), plan.get("target_state", {})))
    diagnostics.extend(_formula_diagnostics(plan.get("target_state", {})))
    diagnostics.extend(
        _contract_domain_diagnostics(str(plan.get("domain")), plan.get("target_state", {}), "target_state")
    )
    if current_profile is not None:
        normalized = normalize_dashboard_profile(current_profile)
        if normalized["domain"] != plan.get("domain") or normalized["dashboard_id"] != str(plan.get("dashboard_id")):
            diagnostics.append(
                _diagnostic(
                    "DASHBOARD_PROFILE_IDENTITY_MISMATCH", "error",
                    "current profile identity does not match the change plan",
                )
            )
        if normalized["profile_sha256"] != plan.get("base_profile_sha256"):
            diagnostics.append(
                _diagnostic(
                    "DASHBOARD_PROFILE_STALE", "error",
                    "current draft profile hash differs from the change plan baseline",
                    "base_profile_sha256",
                )
            )
    return _dedupe_diagnostics(diagnostics)


def _dedupe_diagnostics(diagnostics: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    result: dict[tuple[str, str, str], dict[str, Any]] = {}
    for item in diagnostics:
        key = (
            str(item.get("code", "")),
            str(item.get("message", "")),
            str(item.get("path", "")),
        )
        result[key] = dict(item)
    return list(result.values())


def _profile_matches_target(profile: Mapping[str, Any], target: Mapping[str, Any]) -> bool:
    return _state_from_profile(profile) == _json_value(target)


def build_apply_receipt(
    change_plan: Mapping[str, Any],
    post_profile: Mapping[str, Any],
    *,
    operation_results: Sequence[Mapping[str, Any]] | None = None,
    recovery: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a readback-bound receipt after an operator attempted P3B apply.

    This helper does not perform or authorize writes.
    """

    plan_diagnostics = validate_dashboard_change_plan(change_plan)
    normalized_post = normalize_dashboard_profile(post_profile)
    planned = [item for item in change_plan.get("operations", []) if item.get("write_status") == "supported"]
    if operation_results is None:
        operation_results = [
            {"operation_id": item["operation_id"], "status": "applied"}
            for item in planned
        ]
    results: list[dict[str, Any]] = []
    for item in operation_results:
        raw_status = str(item.get("status") or "")
        response = item.get("write_response") if isinstance(item.get("write_response"), Mapping) else {}
        response_ok = response.get("status") in (None, "success")
        if raw_status == "applied" or (item.get("ok") is True and response_ok):
            status = "applied"
        elif raw_status == "skipped":
            status = "skipped"
        else:
            status = "failed"
        normalized_result: dict[str, Any] = {
            "operation_id": str(item.get("operation_id") or ""),
            "status": status,
        }
        message = item.get("message")
        if message:
            normalized_result["message"] = str(message)
        results.append(normalized_result)
    result_ids = {str(item.get("operation_id")) for item in results if item.get("status") == "applied"}
    expected_ids = {str(item.get("operation_id")) for item in planned}
    target_matches = _profile_matches_target(normalized_post, change_plan.get("target_state", {}))
    ok = (
        not _has_errors(plan_diagnostics)
        and change_plan.get("status") in {"ready_for_dry_run", "no_changes"}
        and result_ids == expected_ids
        and all(item.get("status") == "applied" for item in results)
        and target_matches
        and normalized_post["domain"] == change_plan.get("domain")
        and normalized_post["dashboard_id"] == str(change_plan.get("dashboard_id"))
    )
    receipt: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "artifact_type": "dashboard_apply_receipt",
        "domain": change_plan.get("domain"),
        "dashboard_id": change_plan.get("dashboard_id"),
        "change_plan_sha256": change_plan.get("change_plan_sha256"),
        "pre_profile_sha256": change_plan.get("base_profile_sha256"),
        "post_profile_sha256": normalized_post["profile_sha256"],
        "operations": results,
        "verification": {
            "profile_readback_performed": True,
            "target_state_matches": target_matches,
            "all_planned_operations_accounted_for": result_ids == expected_ids,
            "plan_validation_ok": not _has_errors(plan_diagnostics),
        },
        "status": "applied" if ok and expected_ids else ("no_changes" if ok else "failed"),
        "ok": ok,
        "recovery": _json_value(
            recovery
            or {
                "attempted": False,
                "status": "not_needed",
                "restored_profile_sha256": None,
                "operations": [],
                "errors": [],
            }
        ),
        "publish_boundary": {
            "publish_authorized": False,
            "requires_separate_publish_confirmation": True,
        },
    }
    receipt["apply_receipt_sha256"] = artifact_sha256(receipt, "apply_receipt_sha256")
    return receipt


def validate_apply_receipt(
    receipt: Mapping[str, Any],
    change_plan: Mapping[str, Any],
    post_profile: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    diagnostics: list[dict[str, Any]] = []
    if receipt.get("artifact_type") != "dashboard_apply_receipt":
        return [_diagnostic("DASHBOARD_APPLY_RECEIPT_REQUIRED", "error", "invalid artifact type")]
    if receipt.get("apply_receipt_sha256") != artifact_sha256(receipt, "apply_receipt_sha256"):
        diagnostics.append(
            _diagnostic("DASHBOARD_APPLY_RECEIPT_HASH_MISMATCH", "error", "apply receipt hash is invalid")
        )
    if receipt.get("change_plan_sha256") != change_plan.get("change_plan_sha256"):
        diagnostics.append(
            _diagnostic("DASHBOARD_RECEIPT_PLAN_MISMATCH", "error", "receipt does not bind this change plan")
        )
    if receipt.get("pre_profile_sha256") != change_plan.get("base_profile_sha256"):
        diagnostics.append(
            _diagnostic("DASHBOARD_RECEIPT_BASE_MISMATCH", "error", "receipt baseline hash is invalid")
        )
    if receipt.get("domain") != change_plan.get("domain") or str(receipt.get("dashboard_id")) != str(change_plan.get("dashboard_id")):
        diagnostics.append(
            _diagnostic("DASHBOARD_RECEIPT_IDENTITY_MISMATCH", "error", "receipt identity is invalid")
        )
    recovery = receipt.get("recovery") if isinstance(receipt.get("recovery"), Mapping) else {}
    if receipt.get("status") == "applied" and (
        recovery.get("attempted") is not False or recovery.get("status") != "not_needed"
    ):
        diagnostics.append(
            _diagnostic(
                "DASHBOARD_APPLY_RECOVERY_INCONSISTENT", "error",
                "a successful apply receipt cannot claim recovery was attempted",
                "recovery",
            )
        )
    if recovery.get("status") == "restored" and recovery.get("restored_profile_sha256") != change_plan.get("base_profile_sha256"):
        diagnostics.append(
            _diagnostic(
                "DASHBOARD_APPLY_RECOVERY_HASH_MISMATCH", "error",
                "a restored transaction must return to the ChangePlan baseline profile hash",
                "recovery.restored_profile_sha256",
            )
        )
    expected_ids = {
        str(item.get("operation_id"))
        for item in change_plan.get("operations", [])
        if item.get("write_status") == "supported"
    }
    applied_ids = {
        str(item.get("operation_id"))
        for item in receipt.get("operations", [])
        if item.get("status") == "applied"
    }
    if applied_ids != expected_ids:
        diagnostics.append(
            _diagnostic(
                "DASHBOARD_RECEIPT_OPERATIONS_INCOMPLETE", "error",
                "receipt does not account for every planned safe operation",
            )
        )
    if not receipt.get("verification", {}).get("profile_readback_performed"):
        diagnostics.append(
            _diagnostic("DASHBOARD_RECEIPT_READBACK_REQUIRED", "error", "post-apply readback is required")
        )
    if not receipt.get("verification", {}).get("target_state_matches"):
        diagnostics.append(
            _diagnostic("DASHBOARD_RECEIPT_TARGET_MISMATCH", "error", "post-apply state differs from target")
        )
    if receipt.get("publish_boundary", {}).get("publish_authorized"):
        diagnostics.append(
            _diagnostic(
                "DASHBOARD_APPLY_CANNOT_AUTHORIZE_PUBLISH", "error",
                "an apply receipt cannot grant publish authorization",
            )
        )
    if post_profile is not None:
        normalized = normalize_dashboard_profile(post_profile)
        if normalized["profile_sha256"] != receipt.get("post_profile_sha256"):
            diagnostics.append(
                _diagnostic("DASHBOARD_RECEIPT_POST_HASH_MISMATCH", "error", "post profile hash is invalid")
            )
        if not _profile_matches_target(normalized, change_plan.get("target_state", {})):
            diagnostics.append(
                _diagnostic("DASHBOARD_RECEIPT_POST_STATE_MISMATCH", "error", "post profile differs from target")
            )
    if not receipt.get("ok") or receipt.get("status") not in {"applied", "no_changes"}:
        diagnostics.append(
            _diagnostic("DASHBOARD_APPLY_NOT_VERIFIED", "error", "apply was not fully verified")
        )
    return _dedupe_diagnostics(diagnostics)


def build_publish_receipt(
    apply_receipt: Mapping[str, Any],
    *,
    pre_publish_profile_sha256: str,
    confirmed: bool,
    version_description: str,
    publish_status: str,
    post_publish_draft_profile_sha256: str | None = None,
    readback_performed: bool = False,
    published_version_profile_sha256: str | None = None,
    published_version_readback_performed: bool = False,
    published_at: str | None = None,
) -> dict[str, Any]:
    """Build a publication receipt without overstating available readback evidence."""

    expected_hash = apply_receipt.get("post_profile_sha256")
    formal_version_verified = bool(
        published_version_readback_performed
        and published_version_profile_sha256
        and published_version_profile_sha256 == expected_hash
    )
    if publish_status == "published_verified" and formal_version_verified:
        verification_status = "published_version_verified"
    elif publish_status == "publish_requested_unverified":
        verification_status = "draft_only_unverified_published_version"
    elif publish_status == "not_attempted":
        verification_status = "not_attempted"
    else:
        verification_status = "failed"

    receipt: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "artifact_type": "dashboard_publish_receipt",
        "domain": apply_receipt.get("domain"),
        "dashboard_id": apply_receipt.get("dashboard_id"),
        "apply_receipt_sha256": apply_receipt.get("apply_receipt_sha256"),
        "change_plan_sha256": apply_receipt.get("change_plan_sha256"),
        "expected_draft_profile_sha256": apply_receipt.get("post_profile_sha256"),
        "pre_publish_profile_sha256": str(pre_publish_profile_sha256),
        "post_publish_draft_profile_sha256": _optional_text(
            post_publish_draft_profile_sha256
        ),
        "readback_performed": bool(readback_performed),
        "readback_scope": "published_version" if formal_version_verified else "draft_profile_only",
        "published_version_readback_performed": bool(
            published_version_readback_performed
        ),
        "published_version_profile_sha256": _optional_text(
            published_version_profile_sha256
        ),
        "verification_status": verification_status,
        "fully_verified": formal_version_verified,
        "confirmed": bool(confirmed),
        "version_description": str(version_description),
        "publish_status": str(publish_status),
        "published_at": published_at or datetime.now(timezone.utc).isoformat(),
    }
    applied_operations = [
        item for item in apply_receipt.get("operations", [])
        if item.get("status") == "applied"
    ]
    request_acknowledged = publish_status in {
        "publish_requested_unverified",
        "published_verified",
    }
    receipt["ok"] = bool(
        apply_receipt.get("ok")
        and apply_receipt.get("status") == "applied"
        and applied_operations
        and confirmed
        and request_acknowledged
        and pre_publish_profile_sha256 == apply_receipt.get("post_profile_sha256")
        and readback_performed
        and post_publish_draft_profile_sha256
        == apply_receipt.get("post_profile_sha256")
        and (publish_status != "published_verified" or formal_version_verified)
    )
    receipt["publish_receipt_sha256"] = artifact_sha256(receipt, "publish_receipt_sha256")
    return receipt


def validate_publish_receipt(
    receipt: Mapping[str, Any], apply_receipt: Mapping[str, Any]
) -> list[dict[str, Any]]:
    diagnostics: list[dict[str, Any]] = []
    if receipt.get("artifact_type") != "dashboard_publish_receipt":
        return [_diagnostic("DASHBOARD_PUBLISH_RECEIPT_REQUIRED", "error", "invalid artifact type")]
    if receipt.get("publish_receipt_sha256") != artifact_sha256(receipt, "publish_receipt_sha256"):
        diagnostics.append(
            _diagnostic("DASHBOARD_PUBLISH_RECEIPT_HASH_MISMATCH", "error", "publish receipt hash is invalid")
        )
    if receipt.get("apply_receipt_sha256") != apply_receipt.get("apply_receipt_sha256"):
        diagnostics.append(
            _diagnostic("DASHBOARD_PUBLISH_APPLY_MISMATCH", "error", "publish receipt binds another apply receipt")
        )
    if not apply_receipt.get("ok"):
        diagnostics.append(
            _diagnostic("DASHBOARD_PUBLISH_APPLY_NOT_VERIFIED", "error", "publish requires a verified apply receipt")
        )
    if apply_receipt.get("status") != "applied" or not any(
        item.get("status") == "applied" for item in apply_receipt.get("operations", [])
    ):
        diagnostics.append(
            _diagnostic(
                "DASHBOARD_PUBLISH_APPLIED_CHANGE_REQUIRED", "error",
                "a no-op receipt cannot authorize publication",
            )
        )
    if not receipt.get("confirmed"):
        diagnostics.append(
            _diagnostic("DASHBOARD_PUBLISH_CONFIRMATION_REQUIRED", "error", "explicit publish confirmation is required")
        )
    expected = apply_receipt.get("post_profile_sha256")
    if receipt.get("expected_draft_profile_sha256") != expected or receipt.get("pre_publish_profile_sha256") != expected:
        diagnostics.append(
            _diagnostic("DASHBOARD_PUBLISH_PROFILE_STALE", "error", "draft profile changed after apply verification")
        )
    post_publish_hash = receipt.get("post_publish_draft_profile_sha256")
    readback_scope = receipt.get("readback_scope")
    if readback_scope not in {"draft_profile_only", "published_version"}:
        diagnostics.append(
            _diagnostic(
                "DASHBOARD_PUBLISH_READBACK_SCOPE_INVALID", "error",
                "publication readback scope is invalid",
                "readback_scope",
            )
        )
    if not receipt.get("readback_performed"):
        diagnostics.append(
            _diagnostic(
                "DASHBOARD_PUBLISH_POST_READBACK_REQUIRED", "error",
                "publication requires a post-publish draft-profile readback",
                "readback_performed",
            )
        )
    if not re.fullmatch(r"[0-9a-f]{64}", str(post_publish_hash or "")):
        diagnostics.append(
            _diagnostic(
                "DASHBOARD_PUBLISH_POST_HASH_INVALID", "error",
                "post_publish_draft_profile_sha256 must be a canonical SHA-256",
                "post_publish_draft_profile_sha256",
            )
        )
    elif post_publish_hash != expected:
        diagnostics.append(
            _diagnostic(
                "DASHBOARD_PUBLISH_POST_READBACK_MISMATCH", "error",
                "post-publish draft profile differs from the verified applied draft",
                "post_publish_draft_profile_sha256",
            )
        )
    publish_status = receipt.get("publish_status")
    published_version_hash = receipt.get("published_version_profile_sha256")
    published_version_readback = bool(
        receipt.get("published_version_readback_performed")
    )
    fully_verified = bool(receipt.get("fully_verified"))
    if publish_status == "published_verified":
        if (
            not published_version_readback
            or published_version_hash != expected
            or readback_scope != "published_version"
            or receipt.get("verification_status") != "published_version_verified"
            or not fully_verified
        ):
            diagnostics.append(
                _diagnostic(
                    "DASHBOARD_PUBLISHED_VERSION_READBACK_REQUIRED",
                    "error",
                    "published_verified requires a matching formal published-version readback",
                    "published_version_profile_sha256",
                )
            )
    elif publish_status == "publish_requested_unverified":
        if (
            published_version_readback
            or published_version_hash is not None
            or readback_scope != "draft_profile_only"
            or receipt.get("verification_status")
            != "draft_only_unverified_published_version"
            or fully_verified
        ):
            diagnostics.append(
                _diagnostic(
                    "DASHBOARD_PUBLISH_VERIFICATION_STATUS_INVALID",
                    "error",
                    "unverified publication receipts must remain draft-readback-only",
                    "verification_status",
                )
            )
        else:
            diagnostics.append(
                _diagnostic(
                    "DASHBOARD_PUBLISHED_VERSION_UNVERIFIED",
                    "warning",
                    "publish API acknowledged the request, but no formal published-version profile was available",
                    "verification_status",
                )
            )
    else:
        diagnostics.append(
            _diagnostic(
                "DASHBOARD_PUBLISH_REQUEST_FAILED",
                "error",
                "dashboard publication was not acknowledged by the platform",
                "publish_status",
            )
        )
    if not receipt.get("ok"):
        diagnostics.append(
            _diagnostic(
                "DASHBOARD_PUBLISH_NOT_ACCEPTED",
                "error",
                "publication request or required draft readback was not accepted",
            )
        )
    return _dedupe_diagnostics(diagnostics)


# Explicit alias for callers that prefer action-oriented naming.
build_dashboard_change_plan = diff_dashboard


__all__ = [
    "RECOGNIZED_DESIGN_OPERATION_TYPES",
    "SAFE_OPERATION_TYPES",
    "SCHEMA_VERSION",
    "artifact_sha256",
    "build_apply_receipt",
    "build_dashboard_change_plan",
    "build_dashboard_design_spec",
    "build_publish_receipt",
    "canonical_json_bytes",
    "canonical_sha256",
    "diff_dashboard",
    "normalize_dashboard_profile",
    "profile_sha256",
    "validate_apply_receipt",
    "validate_dashboard_change_plan",
    "validate_publish_receipt",
]
