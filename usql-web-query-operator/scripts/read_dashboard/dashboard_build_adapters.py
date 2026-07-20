"""Evidence-backed production P4C adapter for Taitan dashboard creation."""

from __future__ import annotations

import copy
import json
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Mapping, Sequence

from _shared.auth import ensure_authenticated
from _shared.errors import UsageError

from .constants import DASHBOARD_MARKET_URL
from .dashboard_build_evidence import menu_folder_snapshot
from .dashboard_change import canonical_sha256, require_complete_profile
from .dashboard_write_adapters import (
    _formula_item,
    _write_dashboard_schema,
    _write_formula,
    _write_unit_detail,
    find_layout_item,
    find_unit_field,
)
from .edit_profile import (
    build_edit_url,
    fetch_dataset_fields,
    fetch_edit_dashboard_config,
    fetch_edit_unit_detail,
    open_edit_page,
    profile_edit_dashboard,
)
from .filter_edit import fetch_public_filter_detail
from .menu import fetch_dashboard_menu
from .profile import default_unit_value_payload, post_json, summarize_unit_value


UNIT_TYPE_BY_COMPONENT = {
    "metric_group": "card",
    "pivot": "u_pivot",
    "bar": "u_bar",
    "pie": "u_pie",
}
OPERATION_BY_COMPONENT = {
    "metric_group": "create_metric_group_component",
    "pivot": "create_pivot_component",
    "bar": "create_bar_component",
    "pie": "create_pie_component",
}
EDIT_UNIT_VALUE_API = "https://udata.baijia.com/uanalysis-intelligence/value/unit"


def _schema_nodes_by_name(schema: Mapping[str, Any], component_name: str) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []

    def walk(value: Any) -> None:
        if isinstance(value, Mapping):
            if str(value.get("componentName") or "") == component_name and value.get("id"):
                matches.append(dict(value))
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(schema.get("componentsTree") or [])
    return matches


def _field_ids(detail: Mapping[str, Any], group: str) -> list[str]:
    return [
        str(item.get("fieldId") or "")
        for item in detail.get(group) or []
        if isinstance(item, Mapping) and item.get("fieldId") not in (None, "")
    ]


def _dataset_by_ref(plan: Mapping[str, Any], dataset_ref: str) -> dict[str, Any]:
    matches = [
        dict(item)
        for item in plan.get("datasets") or []
        if isinstance(item, Mapping) and str(item.get("dataset_ref") or "") == dataset_ref
    ]
    if len(matches) != 1:
        raise UsageError(f"DashboardBuildPlan dataset_ref must resolve once: {dataset_ref}")
    return matches[0]


def _component_resource(
    resource_map: Mapping[str, Any], logical_id: str
) -> dict[str, Any] | None:
    value = resource_map.get(f"component:{logical_id}")
    return dict(value) if isinstance(value, Mapping) else None


def _direct_data_unit_id(node: Mapping[str, Any]) -> str:
    props = node.get("props") if isinstance(node.get("props"), Mapping) else {}
    settings = props.get("settings") if isinstance(props.get("settings"), Mapping) else {}
    if not settings and isinstance(node.get("settings"), Mapping):
        settings = node["settings"]
    if str(settings.get("componentType") or "") not in set(UNIT_TYPE_BY_COMPONENT.values()):
        return ""
    return str(settings.get("unitId") or "")


def _is_customized_field(item: Mapping[str, Any]) -> bool:
    return str(item.get("key") or item.get("field_id") or "").startswith("customized_")


def _prune_unplanned_data_nodes(
    schema: Mapping[str, Any], planned_unit_ids: set[str]
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    """Detach stale data nodes from a new dashboard without deleting their units."""

    detached: list[dict[str, str]] = []
    detached_node_ids: set[str] = set()

    def visit(value: Any) -> Any:
        if isinstance(value, list):
            result: list[Any] = []
            for item in value:
                if isinstance(item, Mapping):
                    unit_id = _direct_data_unit_id(item)
                    if unit_id and unit_id not in planned_unit_ids:
                        node_id = str(item.get("id") or "")
                        detached.append({"unit_id": unit_id, "component_id": node_id})
                        if node_id:
                            detached_node_ids.add(node_id)
                        continue
                result.append(visit(item))
            return result
        if isinstance(value, Mapping):
            return {str(key): visit(child) for key, child in value.items()}
        return copy.deepcopy(value)

    pruned = visit(schema)

    def prune_layouts(value: Any) -> None:
        if isinstance(value, dict):
            for key, child in list(value.items()):
                if key in {"layout", "layouts"} and isinstance(child, list):
                    value[key] = [
                        item
                        for item in child
                        if not (
                            isinstance(item, Mapping)
                            and str(item.get("i") or "").lstrip(".$")
                            in {node_id.lstrip(".$") for node_id in detached_node_ids}
                        )
                    ]
                prune_layouts(value[key])
        elif isinstance(value, list):
            for child in value:
                prune_layouts(child)

    prune_layouts(pruned)
    return pruned, detached


class TaitanDashboardBuildV1Adapter:
    """Creation-saga adapter proven by the immutable P4C sandbox evidence set.

    New dashboard/component/filter shells are driven through the same visible UI
    sequence used for evidence capture. Formula creation and final dashboardHtml
    assembly use the exact redacted request shapes captured from that UI and are
    immediately read back. Existing resources are never overwritten on resume.
    """

    def __init__(self, *, page: Any, args: Any) -> None:
        self.page = page
        self.args = args
        self.artifacts_dir = Path(args.artifacts_dir) / "production-dashboard-build-adapter"
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self._resume_dashboard_id: str | None = None
        resume_path = getattr(args, "resume_receipt", None)
        if isinstance(resume_path, Path) and resume_path.is_file():
            receipt = json.loads(resume_path.read_text(encoding="utf-8"))
            for resource in [
                *(receipt.get("created_resources") or []),
                *(receipt.get("reused_resources") or []),
            ]:
                if isinstance(resource, Mapping) and resource.get("logical_id") == "dashboard":
                    self._resume_dashboard_id = str(
                        resource.get("dashboard_id") or resource.get("resource_id") or ""
                    ) or None

    def _authenticate_market(self) -> None:
        ensure_authenticated(self.page, self.args, context=None)
        self.page.goto(DASHBOARD_MARKET_URL, wait_until="domcontentloaded", timeout=45_000)
        self.page.wait_for_timeout(getattr(self.args, "wait_ms", 3000))

    def _folder_snapshot(self, plan: Mapping[str, Any]) -> dict[str, Any]:
        folder = plan["target_folder"]
        return menu_folder_snapshot(
            fetch_dashboard_menu(self.page),
            folder_id=str(folder["folder_id"]),
            folder_path=str(folder["folder_path"]),
            folder_name=str(folder["folder_name"]),
        )

    def _open_dashboard(self, resource_map: Mapping[str, Any]) -> tuple[str, str | None]:
        dashboard = resource_map.get("dashboard")
        if not isinstance(dashboard, Mapping):
            raise UsageError("Dashboard shell identity is missing from creation saga resources.")
        dashboard_id = str(dashboard.get("dashboard_id") or dashboard.get("resource_id") or "")
        html_id = str(dashboard.get("html_id") or "") or None
        if not dashboard_id:
            raise UsageError("Dashboard shell has no stable dashboard_id.")
        open_edit_page(
            self.page,
            self.args,
            context=None,
            edit_url=build_edit_url(dashboard_id, html_id),
        )
        self.page.wait_for_timeout(getattr(self.args, "wait_ms", 3000))
        config = fetch_edit_dashboard_config(self.page, dashboard_id, "draft")
        return dashboard_id, str(config.get("htmlId") or html_id or "") or None

    def _profile(
        self, plan: Mapping[str, Any], resource_map: Mapping[str, Any], *, fields: bool
    ) -> dict[str, Any]:
        dashboard_id, html_id = self._open_dashboard(resource_map)
        raw = profile_edit_dashboard(
            page=self.page,
            dashboard_id=dashboard_id,
            html_id=html_id,
            edit_url=build_edit_url(dashboard_id, html_id),
            version_id="draft",
            artifacts_dir=self.artifacts_dir,
            debug_artifacts=False,
            include_dataset_fields=fields,
            domain=str(plan["domain"]),
        )
        return require_complete_profile(raw, "P4C production adapter DashboardProfile")

    def _live_fields(
        self, plan: Mapping[str, Any], dataset: Mapping[str, Any]
    ) -> list[dict[str, Any]]:
        config = dataset.get("config") if isinstance(dataset.get("config"), Mapping) else {}
        resolution_dashboard_id = str(config.get("field_resolution_dashboard_id") or "")
        if not resolution_dashboard_id:
            raise UsageError("Dataset config requires field_resolution_dashboard_id for pre-shell readback.")
        result = fetch_dataset_fields(
            self.page,
            resolution_dashboard_id,
            [int(dataset["subject_id"])],
            [int(dataset["model_type"])],
            [],
        )
        if len(result) != 1 or result[0].get("error"):
            raise UsageError(f"Dataset field-tree readback failed: {result}")
        return [
            copy.deepcopy(dict(item))
            for item in result[0].get("fields") or []
            if isinstance(item, Mapping) and not _is_customized_field(item)
        ]

    def verify_target_folder(self, plan: Mapping[str, Any]) -> Mapping[str, Any]:
        self._authenticate_market()
        snapshot = self._folder_snapshot(plan)
        matching = [
            item
            for item in snapshot.get("dashboards") or []
            if item.get("dashboard_name") == plan.get("dashboard_name")
        ]
        dashboard_name_available = not matching
        comparable = copy.deepcopy(snapshot)
        comparable.pop("snapshot_sha256", None)
        if matching and self._resume_dashboard_id:
            if len(matching) == 1 and matching[0].get("dashboard_id") == self._resume_dashboard_id:
                comparable["dashboards"] = [
                    item
                    for item in comparable.get("dashboards") or []
                    if item.get("dashboard_id") != self._resume_dashboard_id
                ]
                dashboard_name_available = True
        comparable_sha256 = canonical_sha256(comparable)
        resume_safe_drift = bool(
            self._resume_dashboard_id
            and len(matching) == 1
            and matching[0].get("dashboard_id") == self._resume_dashboard_id
            and dashboard_name_available
        )
        return {
            "ok": comparable_sha256 == plan.get("folder_snapshot_sha256")
            or resume_safe_drift,
            "dashboard_name_available": dashboard_name_available,
            "folder_snapshot_sha256": comparable_sha256,
            "resume_safe_drift": resume_safe_drift,
        }

    def verify_dataset_bindings(
        self, plan: Mapping[str, Any]
    ) -> Sequence[Mapping[str, Any]]:
        results: list[dict[str, Any]] = []
        for dataset in plan.get("datasets") or []:
            if not isinstance(dataset, Mapping):
                continue
            fields = sorted(
                self._live_fields(plan, dataset),
                key=lambda item: str(item.get("field_id") or item.get("key") or ""),
            )
            schema_sha256 = canonical_sha256(fields)
            bindings = sorted(
                [dict(item) for item in dataset.get("field_bindings") or [] if isinstance(item, Mapping)],
                key=lambda item: str(item.get("field_ref") or item.get("logical_field_ref") or ""),
            )
            binding_sha256 = canonical_sha256(bindings)
            results.append(
                {
                    "dataset_ref": dataset.get("dataset_ref"),
                    "ok": schema_sha256 == dataset.get("dataset_schema_sha256")
                    and binding_sha256 == dataset.get("field_binding_sha256"),
                    "application_model_id": dataset.get("application_model_id"),
                    "subject_id": dataset.get("subject_id"),
                    "model_type": dataset.get("model_type"),
                    "dataset_schema_sha256": schema_sha256,
                    "field_binding_sha256": binding_sha256,
                }
            )
        return results

    def ensure_dashboard_shell(
        self, plan: Mapping[str, Any], resume_resources: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        existing = resume_resources.get("dashboard")
        self._authenticate_market()
        before = self._folder_snapshot(plan)
        if isinstance(existing, Mapping):
            dashboard_id = str(existing.get("dashboard_id") or existing.get("resource_id") or "")
            matches = [
                item
                for item in before.get("dashboards") or []
                if item.get("dashboard_id") == dashboard_id
                and item.get("dashboard_name") == plan.get("dashboard_name")
            ]
            if len(matches) != 1:
                raise UsageError("Resume dashboard shell identity no longer matches the target folder.")
            open_edit_page(
                self.page,
                self.args,
                context=None,
                edit_url=build_edit_url(dashboard_id, str(existing.get("html_id") or "") or None),
            )
            config = fetch_edit_dashboard_config(self.page, dashboard_id, "draft")
            resource = dict(existing)
            resource.update({"dashboard_id": dashboard_id, "html_id": config.get("htmlId")})
            return {"status": "reused", "resource": resource}
        conflicts = [
            item
            for item in before.get("dashboards") or []
            if item.get("dashboard_name") == plan.get("dashboard_name")
        ]
        if conflicts:
            raise UsageError("Target dashboard name became occupied before shell creation.")
        from .commands.capture_dashboard_build_evidence import _automate_folder_dashboard_creation

        folder = plan["target_folder"]
        ui_args = SimpleNamespace(
            folder_id=str(folder["folder_id"]),
            folder_name=str(folder["folder_name"]),
            expected_new_dashboard_name=str(plan["dashboard_name"]),
        )
        _automate_folder_dashboard_creation(self.page, ui_args)
        after = self._folder_snapshot(plan)
        before_ids = {str(item.get("dashboard_id") or "") for item in before.get("dashboards") or []}
        created = [
            item
            for item in after.get("dashboards") or []
            if str(item.get("dashboard_id") or "") not in before_ids
            and item.get("dashboard_name") == plan.get("dashboard_name")
        ]
        if len(created) != 1:
            raise UsageError(f"Dashboard shell readback expected one new identity, found {len(created)}.")
        dashboard_id = str(created[0]["dashboard_id"])
        open_edit_page(
            self.page,
            self.args,
            context=None,
            edit_url=build_edit_url(dashboard_id, None),
        )
        config = fetch_edit_dashboard_config(self.page, dashboard_id, "draft")
        if config.get("dashboardName") != plan.get("dashboard_name"):
            raise UsageError("Dashboard shell name readback mismatch.")
        return {
            "status": "applied",
            "resource": {
                "resource_type": "dashboard",
                "resource_id": dashboard_id,
                "dashboard_id": dashboard_id,
                "html_id": config.get("htmlId"),
                "resource_name": plan.get("dashboard_name"),
                "folder_id": folder.get("folder_id"),
            },
        }

    def _formula_subject(
        self,
        plan: Mapping[str, Any],
        column: Mapping[str, Any],
        resource_map: Mapping[str, Any],
    ) -> tuple[int, str]:
        dataset = _dataset_by_ref(plan, str(column["dataset_ref"]))
        config = dataset.get("config") if isinstance(dataset.get("config"), Mapping) else {}
        if config.get("subject_identity_policy") == "dashboard_scoped_clone":
            subject_ids = {
                str(resource.get("subject_id") or "")
                for key, resource in resource_map.items()
                if str(key).startswith("component:")
                and isinstance(resource, Mapping)
                and resource.get("dataset_ref") == column.get("dataset_ref")
                and resource.get("subject_id")
            }
            if len(subject_ids) != 1:
                raise UsageError(
                    "Dashboard-scoped formula creation requires one exact allocated component subject."
                )
            dashboard = resource_map.get("dashboard") or {}
            dashboard_id = str(
                dashboard.get("dashboard_id") or dashboard.get("resource_id") or ""
            )
            if not dashboard_id:
                raise UsageError("Dashboard-scoped formula creation has no dashboard identity.")
            return int(next(iter(subject_ids))), dashboard_id
        resolution_dashboard_id = str(config.get("field_resolution_dashboard_id") or "")
        return int(dataset["subject_id"]), resolution_dashboard_id

    def _formula_match(
        self,
        plan: Mapping[str, Any],
        column: Mapping[str, Any],
        resource_map: Mapping[str, Any],
    ) -> tuple[dict[str, Any] | None, list[dict[str, Any]], int]:
        dataset = _dataset_by_ref(plan, str(column["dataset_ref"]))
        subject_id, resolution_dashboard_id = self._formula_subject(
            plan, column, resource_map
        )
        result = fetch_dataset_fields(
            self.page,
            resolution_dashboard_id,
            [subject_id],
            [int(dataset["model_type"])],
            [],
        )
        fields = [dict(item) for item in result[0].get("fields") or [] if isinstance(item, Mapping)]
        matches = [item for item in fields if item.get("title") == column.get("name")]
        if len(matches) > 1:
            raise UsageError(f"Calculated-column name is ambiguous: {column.get('name')}")
        return (matches[0] if matches else None), fields, subject_id

    def ensure_calculated_column(
        self,
        plan: Mapping[str, Any],
        column: Mapping[str, Any],
        resource_map: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        dataset = _dataset_by_ref(plan, str(column["dataset_ref"]))
        existing, _, target_subject_id = self._formula_match(
            plan, column, resource_map
        )
        if existing:
            detail = _formula_item(self.page, str(existing["key"]))
            if str(detail.get("formula") or "") != str(column.get("formula_template") or ""):
                raise UsageError("Same-name calculated column has a different expression.")
            resource = {
                "resource_type": "calculated_column",
                "resource_id": str(existing["key"]),
                "formula_id": str(existing["key"]),
                "field_id": str(existing["key"]),
                "resource_name": column.get("name"),
                "dataset_ref": column.get("dataset_ref"),
                "subject_id": str(target_subject_id),
            }
            return {"status": "reused", "resource": resource}
        if str(column.get("data_type") or "").lower() not in {
            "decimal",
            "number",
            "numeric",
        }:
            raise UsageError("taitan_dashboard_build_v1 currently supports numeric calculated columns only.")
        binding_by_id = {
            str(item.get("field_id") or ""): item
            for item in dataset.get("field_bindings") or []
            if isinstance(item, Mapping)
        }
        dependencies: list[dict[str, Any]] = []
        for field_id in column.get("dependency_field_ids") or []:
            binding = binding_by_id.get(str(field_id), {})
            dependencies.append(
                {
                    "paramId": str(field_id),
                    "orgParamType": int(binding.get("org_param_type") or 1),
                }
            )
        payload = {
            "subjectId": target_subject_id,
            "columnKey": None,
            "columnName": str(column["name"]),
            "columnDesc": "",
            "dataType": 1,
            "formula": str(column["formula_template"]),
            "dependency": dependencies,
            "globalFilterSpecialConfig": [],
        }
        _write_formula(self.page, payload, [])
        self.page.wait_for_timeout(1500)
        created, _, readback_subject_id = self._formula_match(
            plan, column, resource_map
        )
        if not created:
            raise UsageError("Calculated column was not present in the subject field tree after creation.")
        detail = _formula_item(self.page, str(created["key"]))
        if str(detail.get("formula") or "") != str(column["formula_template"]):
            raise UsageError("Calculated-column expression readback mismatch.")
        return {
            "status": "applied",
            "resource": {
                "resource_type": "calculated_column",
                "resource_id": str(created["key"]),
                "formula_id": str(created["key"]),
                "field_id": str(created["key"]),
                "resource_name": column.get("name"),
                "dataset_ref": column.get("dataset_ref"),
                "subject_id": str(readback_subject_id),
            },
        }

    def _manifest_field(
        self, field: Mapping[str, Any], resource_map: Mapping[str, Any]
    ) -> dict[str, Any]:
        calculated = str(field.get("calculated_column_ref") or "")
        if calculated:
            resource = resource_map.get(f"formula:{calculated}")
            if not isinstance(resource, Mapping):
                raise UsageError(f"Calculated-column resource is missing: {calculated}")
            return {
                "logical_field_ref": str(resource.get("resource_name") or calculated),
                "field_name": str(resource.get("resource_name") or calculated),
                "field_id": str(resource.get("field_id") or resource.get("resource_id") or ""),
            }
        return {
            "logical_field_ref": str(field.get("field_ref") or ""),
            "field_name": str(field.get("field_name") or field.get("field_ref") or ""),
            "field_id": str(field.get("field_id") or ""),
        }

    def _resolved_field_id(
        self, field: Mapping[str, Any], resource_map: Mapping[str, Any]
    ) -> str:
        calculated = str(field.get("calculated_column_ref") or "")
        if calculated:
            resource = resource_map.get(f"formula:{calculated}")
            if not isinstance(resource, Mapping):
                raise UsageError(f"Calculated-column resource is missing: {calculated}")
            return str(resource.get("field_id") or resource.get("resource_id") or "")
        return str(field.get("field_id") or "")

    def _component_binding_mismatches(
        self,
        component: Mapping[str, Any],
        detail: Mapping[str, Any],
        resource_map: Mapping[str, Any],
    ) -> list[str]:
        expected_dimensions = [
            self._resolved_field_id(item, resource_map)
            for item in component.get("dimensions") or []
            if isinstance(item, Mapping)
        ]
        expected_measures = [
            self._resolved_field_id(item, resource_map)
            for item in component.get("measures") or []
            if isinstance(item, Mapping)
        ]
        expected_filters = [
            self._resolved_field_id(item.get("field") or {}, resource_map)
            for item in component.get("local_filters") or []
            if isinstance(item, Mapping)
        ]
        comparisons = {
            "dimensions": (
                Counter(expected_dimensions),
                Counter(_field_ids(detail, "unitDimensionList")),
            ),
            "measures": (
                Counter(expected_measures),
                Counter(
                    [
                        *_field_ids(detail, "unitMeasureList"),
                        *_field_ids(detail, "unitAideMeasureList"),
                    ]
                ),
            ),
            "local_filters": (
                Counter(expected_filters),
                Counter(_field_ids(detail, "unitFilterList")),
            ),
        }
        return [
            f"{label}:expected={dict(expected)},actual={dict(actual)}"
            for label, (expected, actual) in comparisons.items()
            if expected != actual
        ]

    def _repair_new_component_bindings(
        self,
        *,
        dashboard_id: str,
        component: Mapping[str, Any],
        detail: Mapping[str, Any],
        resource_map: Mapping[str, Any],
    ) -> tuple[dict[str, Any], list[str]]:
        """Repair UI field-selection drift using exact same-build unit readbacks.

        The target and every donor must be a component resource created or
        resumed by this exact creation Saga.  No existing unplanned unit is
        queried or modified, and a missing exact donor leaves the build failed.
        """

        repaired = copy.deepcopy(dict(detail))
        donor_details: list[Mapping[str, Any]] = [repaired]
        target_unit_id = str(repaired.get("unitId") or repaired.get("id") or "")
        target_dataset_ref = str(component.get("dataset_ref") or "")
        for key, resource in resource_map.items():
            if not str(key).startswith("component:") or not isinstance(resource, Mapping):
                continue
            unit_id = str(resource.get("unit_id") or resource.get("resource_id") or "")
            if not unit_id or unit_id == target_unit_id:
                continue
            if str(resource.get("dataset_ref") or "") != target_dataset_ref:
                continue
            donor_details.append(
                fetch_edit_unit_detail(self.page, unit_id, dashboard_id, "draft")
            )

        def exact_template(field_id: str, groups: Sequence[str]) -> dict[str, Any] | None:
            matches: list[dict[str, Any]] = []
            for donor in donor_details:
                for group in groups:
                    matches.extend(
                        copy.deepcopy(dict(item))
                        for item in donor.get(group) or []
                        if isinstance(item, Mapping)
                        and str(item.get("fieldId") or "") == field_id
                    )
            if not matches:
                return None
            # Unit-level display/sort metadata may legitimately differ between
            # two donors with the same stable platform field ID. Preserve one
            # complete, unmodified donor object in deterministic Saga order;
            # target readback and type-aware value validation remain mandatory.
            return matches[0]

        expected = {
            "unitDimensionList": [
                self._resolved_field_id(item, resource_map)
                for item in component.get("dimensions") or []
                if isinstance(item, Mapping)
            ],
            "unitMeasureList": [
                self._resolved_field_id(item, resource_map)
                for item in component.get("measures") or []
                if isinstance(item, Mapping)
            ],
            "unitFilterList": [
                self._resolved_field_id(item.get("field") or {}, resource_map)
                for item in component.get("local_filters") or []
                if isinstance(item, Mapping)
            ],
        }
        donor_groups = {
            "unitDimensionList": ("unitDimensionList",),
            "unitMeasureList": ("unitMeasureList", "unitAideMeasureList"),
            "unitFilterList": ("unitFilterList",),
        }
        missing: list[str] = []
        for target_group, field_ids in expected.items():
            if Counter(_field_ids(repaired, target_group)) == Counter(field_ids):
                continue
            replacements: list[dict[str, Any]] = []
            for field_id in field_ids:
                template = exact_template(field_id, donor_groups[target_group])
                if template is None:
                    missing.append(f"{target_group}:{field_id}")
                    continue
                replacements.append(template)
            if len(replacements) == len(field_ids):
                repaired[target_group] = replacements
                if target_group == "unitMeasureList":
                    repaired["unitAideMeasureList"] = []
        if missing:
            return repaired, [f"missing exact same-build donor {item}" for item in missing]
        _write_unit_detail(self.page, dashboard_id, repaired, [])
        self.page.wait_for_timeout(1500)
        readback = fetch_edit_unit_detail(
            self.page,
            str(repaired.get("unitId") or repaired.get("id") or target_unit_id),
            dashboard_id,
            "draft",
        )
        return readback, self._component_binding_mismatches(
            component, readback, resource_map
        )

    @staticmethod
    def _component_resource_from_unit(
        component: Mapping[str, Any], unit: Mapping[str, Any]
    ) -> dict[str, Any]:
        logical_id = str(component["component_id"])
        return {
            "resource_type": "dashboard_component",
            "resource_id": str(unit["unit_id"]),
            "unit_id": str(unit["unit_id"]),
            "actual_component_id": str(unit.get("component_id") or ""),
            "unit_type": str(unit["unit_type"]),
            "resource_name": str(component.get("title") or logical_id),
            "dataset_ref": component.get("dataset_ref"),
            "subject_id": str((unit.get("model_identity") or {}).get("subject_id") or ""),
            "application_model_id": str(
                (unit.get("model_identity") or {}).get("application_model_id") or ""
            ),
        }

    def ensure_component(
        self,
        plan: Mapping[str, Any],
        component: Mapping[str, Any],
        resource_map: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        logical_id = str(component["component_id"])
        if component.get("container_ref"):
            raise UsageError(
                f"Nested component {logical_id} must be created by its verified tab-container saga step."
            )
        existing = _component_resource(resource_map, logical_id)
        dashboard_id, _ = self._open_dashboard(resource_map)
        if existing:
            detail = fetch_edit_unit_detail(
                self.page, str(existing.get("unit_id") or existing.get("resource_id")), dashboard_id, "draft"
            )
            if str(detail.get("unitType") or "") != UNIT_TYPE_BY_COMPONENT[str(component["type"])]:
                raise UsageError("Resume component unit type drifted.")
            dashboard_model = (
                detail.get("dashboardModel")
                if isinstance(detail.get("dashboardModel"), Mapping)
                else {}
            )
            existing["subject_id"] = str(dashboard_model.get("subjectId") or "") or existing.get(
                "subject_id"
            )
            existing["application_model_id"] = str(
                dashboard_model.get("applicationModelId") or detail.get("modelId") or ""
            ) or existing.get("application_model_id")
            mismatches = self._component_binding_mismatches(
                component, detail, resource_map
            )
            if mismatches:
                detail, mismatches = self._repair_new_component_bindings(
                    dashboard_id=dashboard_id,
                    component=component,
                    detail=detail,
                    resource_map=resource_map,
                )
                if mismatches:
                    raise UsageError(
                        f"Resume component binding drifted for {logical_id}: "
                        + "; ".join(mismatches)
                    )
                existing["binding_repaired_after_ui_drift"] = True
                existing["binding_repair_sha256"] = canonical_sha256(
                    {
                        "unit_id": str(existing.get("unit_id") or ""),
                        "component_id": logical_id,
                        "field_groups": {
                            group: _field_ids(detail, group)
                            for group in (
                                "unitDimensionList",
                                "unitMeasureList",
                                "unitAideMeasureList",
                                "unitFilterList",
                            )
                        },
                    }
                )
            return {"status": "reused", "resource": existing}
        before = self._profile(plan, resource_map, fields=False)
        before_ids = {str(item.get("unit_id") or "") for item in before.get("data_units") or []}
        dataset = _dataset_by_ref(plan, str(component["dataset_ref"]))
        dataset_config = dataset.get("config") if isinstance(dataset.get("config"), Mapping) else {}
        dataset_name = str(dataset_config.get("dataset_name") or "")
        if not dataset_name:
            raise UsageError("Dataset config requires dataset_name for component creation.")
        manifest = {
            "dataset": {
                "dataset_name": dataset_name,
                "application_model_id": dataset["application_model_id"],
                "subject_id": dataset["subject_id"],
                "model_type": dataset["model_type"],
                "dataset_schema_sha256": dataset["dataset_schema_sha256"],
                "field_binding_sha256": dataset["field_binding_sha256"],
            },
            "component_name": str(component.get("title") or logical_id),
            "dimensions": [
                self._manifest_field(item, resource_map)
                for item in component.get("dimensions") or []
                if isinstance(item, Mapping)
            ],
            "measures": [
                self._manifest_field(item, resource_map)
                for item in component.get("measures") or []
                if isinstance(item, Mapping)
            ],
            "local_filters": [
                self._manifest_field(item.get("field") or {}, resource_map)
                for item in component.get("local_filters") or []
                if isinstance(item, Mapping)
            ],
        }
        operation = OPERATION_BY_COMPONENT[str(component["type"])]
        from .commands.capture_dashboard_build_evidence import _automate_dashboard_component_creation

        ui_args = SimpleNamespace(
            operation=operation,
            sandbox_dashboard_id=dashboard_id,
            expected_dashboard_name=str(plan["dashboard_name"]),
        )
        _automate_dashboard_component_creation(
            self.page, ui_args, manifest, self.artifacts_dir
        )
        after = self._profile(plan, resource_map, fields=False)
        created = [
            item
            for item in after.get("data_units") or []
            if str(item.get("unit_id") or "") not in before_ids
            and str(item.get("unit_type") or "") == UNIT_TYPE_BY_COMPONENT[str(component["type"])]
        ]
        if len(created) != 1:
            raise UsageError(f"Component readback expected one new unit, found {len(created)}.")
        unit = created[0]
        actual_component_id = str(unit.get("component_id") or "")
        resource = self._component_resource_from_unit(component, unit)
        detail = fetch_edit_unit_detail(
            self.page, str(unit["unit_id"]), dashboard_id, "draft"
        )
        mismatches = self._component_binding_mismatches(component, detail, resource_map)
        repaired = False
        if mismatches:
            detail, mismatches = self._repair_new_component_bindings(
                dashboard_id=dashboard_id,
                component=component,
                detail=detail,
                resource_map=resource_map,
            )
            repaired = not mismatches
            if repaired:
                resource["binding_repaired_after_ui_drift"] = True
                resource["binding_repair_sha256"] = canonical_sha256(
                    {
                        "unit_id": str(unit["unit_id"]),
                        "component_id": logical_id,
                        "field_groups": {
                            group: _field_ids(detail, group)
                            for group in (
                                "unitDimensionList",
                                "unitMeasureList",
                                "unitAideMeasureList",
                                "unitFilterList",
                            )
                        },
                    }
                )
        result: dict[str, Any] = {"status": "applied", "resource": resource}
        if mismatches:
            result["verification_error"] = (
                f"new component {logical_id} binding readback mismatch: "
                + "; ".join(mismatches)
            )
        return result

    def ensure_text_component(
        self,
        plan: Mapping[str, Any],
        text_component: Mapping[str, Any],
        resource_map: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        logical_id = str(text_component["text_id"])
        existing = resource_map.get(f"text:{logical_id}")
        dashboard_id, _ = self._open_dashboard(resource_map)
        config = fetch_edit_dashboard_config(self.page, dashboard_id, "draft")
        schema = json.loads(str(config.get("dashboardHtmlJson") or "{}"))
        if isinstance(existing, Mapping):
            matches = [
                item
                for item in _schema_nodes_by_name(schema, "Text")
                if str(item.get("id") or "") == str(existing.get("actual_component_id") or "")
            ]
            if len(matches) != 1:
                raise UsageError(f"Resume text component drifted: {logical_id}")
            return {"status": "reused", "resource": dict(existing)}
        before_ids = {
            str(item.get("id") or "") for item in _schema_nodes_by_name(schema, "Text")
        }
        from .commands.capture_dashboard_build_evidence import (
            _automate_palette_only_component_creation,
        )

        ui_args = SimpleNamespace(
            operation="create_text_component",
            sandbox_dashboard_id=dashboard_id,
            expected_dashboard_name=str(plan["dashboard_name"]),
        )
        _automate_palette_only_component_creation(
            self.page,
            ui_args,
            {
                "logical_resource_id": logical_id,
                "initial_text": str(text_component["initial_text"]),
            },
            self.artifacts_dir,
        )
        readback = fetch_edit_dashboard_config(self.page, dashboard_id, "draft")
        readback_schema = json.loads(str(readback.get("dashboardHtmlJson") or "{}"))
        created = [
            item
            for item in _schema_nodes_by_name(readback_schema, "Text")
            if str(item.get("id") or "") not in before_ids
        ]
        if len(created) != 1:
            raise UsageError(f"Text readback expected one new node, found {len(created)}.")
        node_id = str(created[0]["id"])
        return {
            "status": "applied",
            "resource": {
                "resource_type": "dashboard_text",
                "resource_id": node_id,
                "actual_component_id": node_id,
                "resource_name": str(text_component.get("title") or logical_id),
            },
        }

    def ensure_tab_container(
        self,
        plan: Mapping[str, Any],
        container: Mapping[str, Any],
        resource_map: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        logical_id = str(container["container_id"])
        dashboard_id, _ = self._open_dashboard(resource_map)
        config = fetch_edit_dashboard_config(self.page, dashboard_id, "draft")
        schema = json.loads(str(config.get("dashboardHtmlJson") or "{}"))
        existing = resource_map.get(f"container:{logical_id}")
        before_tab_ids = {
            str(item.get("id") or "")
            for item in _schema_nodes_by_name(schema, "SingleTabs")
        }
        slot_components = {
            str(slot["slot_id"]): next(
                (
                    item
                    for item in plan.get("components") or []
                    if item.get("container_ref") == logical_id
                    and item.get("slot_ref") == slot["slot_id"]
                ),
                None,
            )
            for slot in container.get("slots") or []
        }
        if any(item is None for item in slot_components.values()):
            raise UsageError(f"Tab container {logical_id} does not resolve every planned slot.")

        if not isinstance(existing, Mapping):
            manifest_slots: list[dict[str, Any]] = []
            for slot in container.get("slots") or []:
                component = slot_components[str(slot["slot_id"])]
                if component.get("local_filters"):
                    raise UsageError(
                        "Evidence-backed nested pivots do not support local filters; place "
                        "multi-layer local filters on root components."
                    )
                dataset = _dataset_by_ref(plan, str(component["dataset_ref"]))
                dataset_config = (
                    dataset.get("config")
                    if isinstance(dataset.get("config"), Mapping)
                    else {}
                )
                manifest_slots.append(
                    {
                        "logical_slot_id": str(slot["slot_id"]),
                        "label": str(slot["label"]),
                        "component": {
                            "logical_resource_id": str(component["component_id"]),
                            "component_name": str(
                                component.get("title") or component["component_id"]
                            ),
                            "dataset": {
                                "dataset_name": str(dataset_config.get("dataset_name") or ""),
                                "application_model_id": dataset["application_model_id"],
                                "subject_id": dataset["subject_id"],
                                "model_type": dataset["model_type"],
                                "dataset_schema_sha256": dataset["dataset_schema_sha256"],
                                "field_binding_sha256": dataset["field_binding_sha256"],
                            },
                            "dimensions": [
                                self._manifest_field(item, resource_map)
                                for item in component.get("dimensions") or []
                            ],
                            "measures": [
                                self._manifest_field(item, resource_map)
                                for item in component.get("measures") or []
                            ],
                        },
                    }
                )
            from .commands.capture_dashboard_build_evidence import (
                _automate_palette_only_component_creation,
            )

            ui_args = SimpleNamespace(
                operation="create_tab_container",
                sandbox_dashboard_id=dashboard_id,
                expected_dashboard_name=str(plan["dashboard_name"]),
            )
            _automate_palette_only_component_creation(
                self.page,
                ui_args,
                {
                    "logical_resource_id": logical_id,
                    "component_name": str(container["title"]),
                    "component_description": str(container.get("description") or ""),
                    "slots": manifest_slots,
                },
                self.artifacts_dir,
            )

        profile = self._profile(plan, resource_map, fields=False)
        candidates = [
            item
            for item in profile.get("components") or []
            if item.get("component_type") == "SingleTabs"
            and (
                str(item.get("component_id") or "")
                == str((existing or {}).get("actual_component_id") or "")
                if isinstance(existing, Mapping)
                else str(item.get("component_id") or "") not in before_tab_ids
            )
        ]
        if len(candidates) != 1:
            raise UsageError(
                f"Tab-container readback expected one exact node, found {len(candidates)}."
            )
        tab = candidates[0]
        actual_slots = tab.get("config", {}).get("slots") or []
        if [str(item.get("label") or "") for item in actual_slots] != [
            str(item["label"]) for item in container.get("slots") or []
        ]:
            raise UsageError(f"Tab-container slot-label readback mismatch: {logical_id}")
        units_by_component = {
            str(item.get("component_id") or ""): item
            for item in profile.get("data_units") or []
            if isinstance(item, Mapping)
        }
        child_resources: list[dict[str, Any]] = []
        verification_errors: list[str] = []
        for planned_slot, actual_slot in zip(container["slots"], actual_slots):
            component = slot_components[str(planned_slot["slot_id"])]
            actual_component_ids = actual_slot.get("component_ids") or []
            if len(actual_component_ids) != 1:
                raise UsageError(
                    f"Tab slot {planned_slot['slot_id']} must contain one persisted pivot."
                )
            unit = units_by_component.get(str(actual_component_ids[0]))
            if not unit or unit.get("unit_type") != "u_pivot":
                raise UsageError(
                    f"Tab slot {planned_slot['slot_id']} nested pivot readback is missing."
                )
            resource = self._component_resource_from_unit(component, unit)
            resource["logical_id"] = f"component:{component['component_id']}"
            detail = fetch_edit_unit_detail(
                self.page, str(unit["unit_id"]), dashboard_id, "draft"
            )
            mismatches = self._component_binding_mismatches(
                component, detail, resource_map
            )
            if mismatches:
                verification_errors.append(
                    f"{component['component_id']}:" + ";".join(mismatches)
                )
            child_resources.append(
                {
                    "status": "reused" if isinstance(existing, Mapping) else "applied",
                    "resource": resource,
                }
            )
        result: dict[str, Any] = {
            "status": "reused" if isinstance(existing, Mapping) else "applied",
            "resource": {
                "resource_type": "dashboard_tab_container",
                "resource_id": str(tab["component_id"]),
                "actual_component_id": str(tab["component_id"]),
                "resource_name": str(container["title"]),
            },
            "component_resources": child_resources,
        }
        if verification_errors:
            result["verification_error"] = (
                "nested pivot binding readback mismatch: " + " | ".join(verification_errors)
            )
        return result

    def ensure_metric_names(
        self,
        plan: Mapping[str, Any],
        component: Mapping[str, Any],
        resource_map: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        targets = [
            item
            for item in component.get("measures") or []
            if isinstance(item, Mapping) and item.get("display_name")
        ]
        if not targets:
            return {"status": "reused"}
        resource_key = f"component:{component['component_id']}"
        resource = resource_map.get(resource_key)
        if not isinstance(resource, dict):
            raise UsageError(f"Metric-rename component resource is missing: {resource_key}")
        dashboard_id, _ = self._open_dashboard(resource_map)
        unit_id = str(resource.get("unit_id") or resource.get("resource_id") or "")
        detail = fetch_edit_unit_detail(self.page, unit_id, dashboard_id, "draft")
        expected_ids = [self._resolved_field_id(item, resource_map) for item in targets]
        actual_ids = [
            *_field_ids(detail, "unitMeasureList"),
            *_field_ids(detail, "unitAideMeasureList"),
        ]
        if Counter(expected_ids) != Counter(actual_ids):
            raise UsageError(
                f"Metric rename must cover every metric instance in {unit_id}: "
                f"expected={dict(Counter(expected_ids))}, actual={dict(Counter(actual_ids))}."
            )
        current: dict[str, str] = {}
        groups: dict[str, str] = {}
        for field_id in expected_ids:
            present_groups = [
                group
                for group in ("unitMeasureList", "unitAideMeasureList")
                if field_id in _field_ids(detail, group)
            ]
            if len(present_groups) != 1:
                raise UsageError(f"Metric {field_id} is not unique in unit {unit_id}.")
            groups[field_id] = present_groups[0]
            current[field_id] = str(
                find_unit_field(detail, present_groups[0], field_id).get("showName") or ""
            )
        target_names = {
            self._resolved_field_id(item, resource_map): str(item["display_name"])
            for item in targets
        }
        if current == target_names:
            resource["metric_names_applied"] = True
            resource["metric_display_names_sha256"] = canonical_sha256(target_names)
            return {"status": "reused"}
        if resource.get("metric_names_applied"):
            raise UsageError(
                f"Metric display names drifted after a prior successful write: {component['component_id']}"
            )
        before = copy.deepcopy(detail)
        try:
            for field_id, display_name in target_names.items():
                if not display_name or len(display_name) > 100:
                    raise UsageError(f"Invalid metric display name for {field_id}.")
                find_unit_field(detail, groups[field_id], field_id)["showName"] = display_name
            _write_unit_detail(self.page, dashboard_id, detail, [])
            self.page.wait_for_timeout(1500)
            readback = fetch_edit_unit_detail(self.page, unit_id, dashboard_id, "draft")
            for field_id, display_name in target_names.items():
                actual = str(
                    find_unit_field(readback, groups[field_id], field_id).get("showName") or ""
                )
                if actual != display_name:
                    raise UsageError(
                        f"Metric display-name readback mismatch for {unit_id}/{field_id}."
                    )
        except Exception:
            _write_unit_detail(self.page, dashboard_id, before, [])
            restored = fetch_edit_unit_detail(self.page, unit_id, dashboard_id, "draft")
            for field_id, before_name in current.items():
                if str(
                    find_unit_field(restored, groups[field_id], field_id).get("showName") or ""
                ) != before_name:
                    raise UsageError(
                        "Metric rename failed and complete display-name compensation was not proven."
                    )
            raise
        resource["metric_names_applied"] = True
        resource["metric_display_names_sha256"] = canonical_sha256(target_names)
        return {"status": "applied"}

    def ensure_global_filter(
        self,
        plan: Mapping[str, Any],
        global_filter: Mapping[str, Any],
        resource_map: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        logical_id = str(global_filter["filter_id"])
        existing = resource_map.get(f"filter:{logical_id}")
        dashboard_id, _ = self._open_dashboard(resource_map)
        if isinstance(existing, Mapping):
            detail = fetch_public_filter_detail(
                self.page,
                dashboard_id,
                str(existing.get("relation_id") or existing.get("resource_id")),
            )
            if not isinstance(detail, Mapping):
                raise UsageError("Resume global-filter readback is empty.")
            return {"status": "reused", "resource": dict(existing)}
        planned_unit_ids = {
            str(resource.get("unit_id") or "")
            for ref in global_filter.get("target_component_refs") or []
            for resource in [_component_resource(resource_map, str(ref)) or {}]
            if resource.get("unit_id")
        }
        declared_orphan_unit_ids = {
            str(resource.get("unit_id") or "")
            for logical_id, resource in resource_map.items()
            if str(logical_id).startswith("orphan:")
            and isinstance(resource, Mapping)
            and resource.get("unit_id")
        }
        if declared_orphan_unit_ids:
            config = fetch_edit_dashboard_config(self.page, dashboard_id, "draft")
            schema = json.loads(str(config.get("dashboardHtmlJson") or "{}"))
            pruned, detached = _prune_unplanned_data_nodes(schema, planned_unit_ids)
            detached_ids = {item["unit_id"] for item in detached}
            if not detached_ids.issubset(declared_orphan_unit_ids):
                raise UsageError(
                    "Dashboard contains an unplanned data unit that is not declared by the "
                    "resume receipt; no recovery write was attempted."
                )
            if detached:
                _write_dashboard_schema(
                    self.page, dashboard_id, str(plan["dashboard_name"]), pruned, []
                )
                self.page.wait_for_timeout(1500)
        before = self._profile(plan, resource_map, fields=False)
        before_relations = {
            str(item.get("relation_id") or "") for item in before.get("public_filters") or []
        }
        field = global_filter.get("field") if isinstance(global_filter.get("field"), Mapping) else {}
        targets = []
        target_components = []
        for ref in global_filter.get("target_component_refs") or []:
            resource = _component_resource(resource_map, str(ref))
            if not resource:
                raise UsageError(f"Global-filter target component is missing: {ref}")
            targets.append(str(resource.get("resource_name") or ref))
            target_components.append(
                {
                    "name": str(resource.get("resource_name") or ref),
                    "component_id": str(resource.get("actual_component_id") or ""),
                    "unit_id": str(resource.get("unit_id") or ""),
                }
            )
        manifest = {
            "field": self._manifest_field(field, resource_map),
            "filter_name": str(global_filter.get("title") or logical_id),
            "target_component_names": targets,
            "target_components": target_components,
        }
        from .commands.capture_dashboard_build_evidence import _automate_dashboard_component_creation

        ui_args = SimpleNamespace(
            operation="create_public_filter",
            sandbox_dashboard_id=dashboard_id,
            expected_dashboard_name=str(plan["dashboard_name"]),
        )
        _automate_dashboard_component_creation(
            self.page, ui_args, manifest, self.artifacts_dir
        )
        after = self._profile(plan, resource_map, fields=False)
        created = [
            item
            for item in after.get("public_filters") or []
            if str(item.get("relation_id") or "") not in before_relations
        ]
        if len(created) != 1:
            raise UsageError(f"Global-filter readback expected one new relation, found {len(created)}.")
        item = created[0]
        return {
            "status": "applied",
            "resource": {
                "resource_type": "global_filter",
                "resource_id": str(item["relation_id"]),
                "relation_id": str(item["relation_id"]),
                "filter_id": str(item["filter_id"]),
                "field_id": str(item["field_id"]),
                "resource_name": str(global_filter.get("title") or logical_id),
            },
        }

    def apply_styles(
        self, plan: Mapping[str, Any], resource_map: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        dashboard_id, _ = self._open_dashboard(resource_map)
        config = fetch_edit_dashboard_config(self.page, dashboard_id, "draft")
        schema = json.loads(str(config.get("dashboardHtmlJson") or "{}"))
        from .commands.capture_dashboard_build_evidence import (
            _automate_component_styles,
            _find_schema_node,
            _style_projection,
        )

        targets: list[tuple[str, str, dict[str, Any]]] = []
        color = str((plan.get("theme") or {}).get("background_color") or "")
        if color:
            pages = _schema_nodes_by_name(schema, "Page")
            if len(pages) != 1:
                raise UsageError(f"Dashboard style requires one Page node, found {len(pages)}.")
            current_style = copy.deepcopy(
                (pages[0].get("props") or {}).get("style") or {}
            )
            current_style["backgroundColor"] = color
            targets.append((str(pages[0]["id"]), "Page", {"style": current_style}))

        schema_name_by_type = {
            "metric_group": "IndicatorCard",
            "pivot": "PivotTable",
            "bar": "BarChart",
            "pie": "PieChart",
        }
        for component in plan.get("components") or []:
            style = component.get("style") if isinstance(component.get("style"), Mapping) else {}
            if not style:
                continue
            resource = _component_resource(resource_map, str(component["component_id"]))
            if not resource:
                raise UsageError(f"Style component resource is missing: {component['component_id']}")
            targets.append(
                (
                    str(resource["actual_component_id"]),
                    schema_name_by_type[str(component["type"])],
                    copy.deepcopy(dict(style)),
                )
            )
        for container in plan.get("containers") or []:
            style = container.get("style") if isinstance(container.get("style"), Mapping) else {}
            if not style:
                continue
            resource = resource_map.get(f"container:{container['container_id']}")
            if not isinstance(resource, Mapping):
                raise UsageError(f"Style container resource is missing: {container['container_id']}")
            targets.append(
                (
                    str(resource["actual_component_id"]),
                    "SingleTabs",
                    copy.deepcopy(dict(style)),
                )
            )
        for text_component in plan.get("text_components") or []:
            resource = resource_map.get(f"text:{text_component['text_id']}")
            if not isinstance(resource, Mapping):
                raise UsageError(f"Style text resource is missing: {text_component['text_id']}")
            props_patch = copy.deepcopy(dict(text_component.get("style") or {}))
            props_patch["text_content_html"] = str(text_component["content_html"])
            targets.append(
                (str(resource["actual_component_id"]), "Text", props_patch)
            )

        patches: list[dict[str, Any]] = []
        seen: set[str] = set()
        for component_id, component_name, props_patch in targets:
            if component_id in seen:
                raise UsageError(f"Duplicate style target in build plan: {component_id}")
            seen.add(component_id)
            node = _find_schema_node(schema, component_id)
            if str(node.get("componentName") or "") != component_name:
                raise UsageError(
                    f"Style target type drift for {component_id}: expected {component_name}."
                )
            before_projection = _style_projection(node)
            after_projection = copy.deepcopy(before_projection)
            after_projection.update(copy.deepcopy(props_patch))
            if after_projection == before_projection:
                continue
            patches.append(
                {
                    "component_id": component_id,
                    "component_name": component_name,
                    "before_style_sha256": canonical_sha256(before_projection),
                    "props_patch": props_patch,
                    "after_style_sha256": canonical_sha256(after_projection),
                }
            )
        if not patches:
            return {"status": "reused"}
        ui_args = SimpleNamespace(
            sandbox_dashboard_id=dashboard_id,
            expected_dashboard_name=str(plan["dashboard_name"]),
        )
        _automate_component_styles(self.page, ui_args, {"patches": patches}, [])
        return {"status": "applied"}

    def assemble_dashboard(
        self, plan: Mapping[str, Any], resource_map: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        dashboard_id, _ = self._open_dashboard(resource_map)
        config = fetch_edit_dashboard_config(self.page, dashboard_id, "draft")
        schema = json.loads(str(config.get("dashboardHtmlJson") or "{}"))
        changed = False
        planned_unit_ids = {
            str(resource.get("unit_id") or "")
            for component in plan.get("components") or []
            for resource in [
                _component_resource(resource_map, str(component["component_id"])) or {}
            ]
            if resource.get("unit_id")
        }
        schema, detached = _prune_unplanned_data_nodes(schema, planned_unit_ids)
        changed = bool(detached)
        for component in plan.get("components") or []:
            resource = _component_resource(resource_map, str(component["component_id"]))
            if not resource:
                raise UsageError(f"Assembly component resource is missing: {component['component_id']}")
            layout = find_layout_item(schema, str(resource["actual_component_id"]))
            target = component["layout"]
            for key in ("x", "y", "w", "h"):
                if layout.get(key) != target.get(key):
                    layout[key] = target.get(key)
                    changed = True
        for collection, prefix, id_key in (
            (plan.get("containers") or [], "container", "container_id"),
            (plan.get("text_components") or [], "text", "text_id"),
        ):
            for item in collection:
                resource = resource_map.get(f"{prefix}:{item[id_key]}")
                if not isinstance(resource, Mapping):
                    raise UsageError(
                        f"Assembly {prefix} resource is missing: {item[id_key]}"
                    )
                layout = find_layout_item(schema, str(resource["actual_component_id"]))
                for key in ("x", "y", "w", "h"):
                    if layout.get(key) != item["layout"].get(key):
                        layout[key] = item["layout"].get(key)
                        changed = True
        root = (schema.get("componentsTree") or [None])[0]
        color = str((plan.get("theme") or {}).get("background_color") or "")
        if color and isinstance(root, dict):
            props = root.setdefault("props", {})
            style = props.setdefault("style", {})
            if style.get("backgroundColor") != color:
                style["backgroundColor"] = color
                changed = True
        if changed:
            _write_dashboard_schema(
                self.page, dashboard_id, str(plan["dashboard_name"]), schema, []
            )
            self.page.wait_for_timeout(1500)
        readback = fetch_edit_dashboard_config(self.page, dashboard_id, "draft")
        readback_schema = json.loads(str(readback.get("dashboardHtmlJson") or "{}"))
        for component in plan.get("components") or []:
            resource = _component_resource(resource_map, str(component["component_id"]))
            item = find_layout_item(readback_schema, str(resource["actual_component_id"]))
            if any(item.get(key) != component["layout"].get(key) for key in ("x", "y", "w", "h")):
                raise UsageError(f"Assembly layout readback mismatch: {component['component_id']}")
        for collection, prefix, id_key in (
            (plan.get("containers") or [], "container", "container_id"),
            (plan.get("text_components") or [], "text", "text_id"),
        ):
            for planned in collection:
                resource = resource_map.get(f"{prefix}:{planned[id_key]}")
                item = find_layout_item(
                    readback_schema, str(resource["actual_component_id"])
                )
                if any(
                    item.get(key) != planned["layout"].get(key)
                    for key in ("x", "y", "w", "h")
                ):
                    raise UsageError(
                        f"Assembly layout readback mismatch: {prefix}:{planned[id_key]}"
                    )
        return {
            "status": "applied" if changed else "reused",
            "resource": {
                "resource_type": "dashboard_html",
                "resource_id": str(readback.get("htmlId") or ""),
                "html_id": readback.get("htmlId"),
                "dashboard_id": dashboard_id,
                "detached_orphan_units": detached,
            },
        }

    def read_complete_profile(
        self, plan: Mapping[str, Any], resource_map: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        return self._profile(plan, resource_map, fields=True)

    def verify_profile_target(
        self,
        plan: Mapping[str, Any],
        profile: Mapping[str, Any],
        resource_map: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        mismatches: list[str] = []
        if profile.get("dashboard_name") != plan.get("dashboard_name"):
            mismatches.append("dashboard_name")
        units = {
            str(item.get("unit_id") or ""): item
            for item in profile.get("data_units") or []
            if isinstance(item, Mapping)
        }
        planned_unit_ids = {
            str(resource.get("unit_id") or "")
            for component in plan.get("components") or []
            for resource in [
                _component_resource(resource_map, str(component["component_id"])) or {}
            ]
            if resource.get("unit_id")
        }
        if set(units) != planned_unit_ids:
            mismatches.append("components:exact_unit_set")
        layouts = {
            str(item.get("component_id") or ""): item
            for item in profile.get("layout") or []
            if isinstance(item, Mapping)
        }
        profile_components = {
            str(item.get("component_id") or ""): item
            for item in profile.get("components") or []
            if isinstance(item, Mapping)
        }
        for component in plan.get("components") or []:
            resource = _component_resource(resource_map, str(component["component_id"]))
            if not resource:
                mismatches.append(f"component:{component['component_id']}:resource")
                continue
            unit = units.get(str(resource.get("unit_id") or ""))
            if not unit or unit.get("unit_type") != UNIT_TYPE_BY_COMPONENT[str(component["type"])]:
                mismatches.append(f"component:{component['component_id']}:unit")
                continue
            dataset = _dataset_by_ref(plan, str(component["dataset_ref"]))
            identity = unit.get("model_identity") or {}
            if str(identity.get("application_model_id") or "") != str(
                dataset.get("application_model_id") or ""
            ):
                mismatches.append(f"component:{component['component_id']}:application_model")
            subject_policy = (dataset.get("config") or {}).get("subject_identity_policy")
            expected_subject = (
                str(resource.get("subject_id") or "")
                if subject_policy == "dashboard_scoped_clone"
                else str(dataset.get("subject_id") or "")
            )
            if str(identity.get("subject_id") or "") != expected_subject:
                mismatches.append(f"component:{component['component_id']}:subject")
            expected_dims = {
                str(item.get("field_id") or "") for item in component.get("dimensions") or []
            }
            expected_measures: set[str] = set()
            for item in component.get("measures") or []:
                if item.get("calculated_column_ref"):
                    formula = resource_map.get(f"formula:{item['calculated_column_ref']}") or {}
                    expected_measures.add(str(formula.get("field_id") or formula.get("resource_id") or ""))
                else:
                    expected_measures.add(str(item.get("field_id") or ""))
            groups = unit.get("field_groups") or {}
            if set(groups.get("row_dimension") or []) != expected_dims:
                mismatches.append(f"component:{component['component_id']}:dimensions")
            if set(groups.get("measure") or []) != expected_measures:
                mismatches.append(f"component:{component['component_id']}:measures")
            expected_filters = {
                str((item.get("field") or {}).get("field_id") or "")
                for item in component.get("local_filters") or []
            }
            if set(groups.get("filter") or []) != expected_filters:
                mismatches.append(f"component:{component['component_id']}:filters")
            profiled_component = profile_components.get(
                str(resource.get("actual_component_id") or "")
            )
            if not profiled_component:
                if component.get("style") or any(
                    item.get("display_name")
                    for item in component.get("measures") or []
                    if isinstance(item, Mapping)
                ):
                    mismatches.append(f"component:{component['component_id']}:profile")
            else:
                actual_metric_names = {
                    str(item.get("field_id") or ""): str(item.get("display_name") or "")
                    for item in (profiled_component.get("fields") or {}).get("metrics") or []
                    if isinstance(item, Mapping)
                }
                for measure in component.get("measures") or []:
                    display_name = measure.get("display_name")
                    if not display_name:
                        continue
                    field_id = self._resolved_field_id(measure, resource_map)
                    if actual_metric_names.get(field_id) != str(display_name):
                        mismatches.append(
                            f"component:{component['component_id']}:metric_name:{field_id}"
                        )
                actual_style = (
                    (profiled_component.get("config") or {}).get("visual_style") or {}
                )
                for key, expected in (component.get("style") or {}).items():
                    if actual_style.get(key) != expected:
                        mismatches.append(
                            f"component:{component['component_id']}:style:{key}"
                        )
            layout = layouts.get(str(resource.get("actual_component_id") or ""))
            if not layout or any(
                layout.get(key) != component["layout"].get(key) for key in ("x", "y", "w", "h")
            ):
                mismatches.append(f"component:{component['component_id']}:layout")
        for container in plan.get("containers") or []:
            resource = resource_map.get(f"container:{container['container_id']}") or {}
            actual = profile_components.get(str(resource.get("actual_component_id") or ""))
            if not actual or actual.get("component_type") != "SingleTabs":
                mismatches.append(f"container:{container['container_id']}:profile")
                continue
            actual_slots = (actual.get("config") or {}).get("slots") or []
            expected_slot_rows = []
            for slot in container.get("slots") or []:
                child = next(
                    item
                    for item in plan.get("components") or []
                    if item.get("container_ref") == container["container_id"]
                    and item.get("slot_ref") == slot["slot_id"]
                )
                child_resource = _component_resource(
                    resource_map, str(child["component_id"])
                ) or {}
                expected_slot_rows.append(
                    (
                        str(slot["label"]),
                        [str(child_resource.get("actual_component_id") or "")],
                    )
                )
            actual_slot_rows = [
                (
                    str(item.get("label") or ""),
                    [str(value) for value in item.get("component_ids") or []],
                )
                for item in actual_slots
                if isinstance(item, Mapping)
            ]
            if actual_slot_rows != expected_slot_rows:
                mismatches.append(f"container:{container['container_id']}:slots")
            actual_style = (actual.get("config") or {}).get("visual_style") or {}
            for key, expected in (container.get("style") or {}).items():
                if actual_style.get(key) != expected:
                    mismatches.append(f"container:{container['container_id']}:style:{key}")
            layout = layouts.get(str(resource.get("actual_component_id") or ""))
            if not layout or any(
                layout.get(key) != container["layout"].get(key)
                for key in ("x", "y", "w", "h")
            ):
                mismatches.append(f"container:{container['container_id']}:layout")
        for text_component in plan.get("text_components") or []:
            resource = resource_map.get(f"text:{text_component['text_id']}") or {}
            actual = profile_components.get(str(resource.get("actual_component_id") or ""))
            if not actual or actual.get("component_type") not in {"Text", "u_text"}:
                mismatches.append(f"text:{text_component['text_id']}:profile")
                continue
            config = actual.get("config") or {}
            if str(config.get("text_content_html") or "") != str(
                text_component["content_html"]
            ):
                mismatches.append(f"text:{text_component['text_id']}:content")
            actual_style = config.get("visual_style") or {}
            for key, expected in (text_component.get("style") or {}).items():
                if actual_style.get(key) != expected:
                    mismatches.append(f"text:{text_component['text_id']}:style:{key}")
            layout = layouts.get(str(resource.get("actual_component_id") or ""))
            if not layout or any(
                layout.get(key) != text_component["layout"].get(key)
                for key in ("x", "y", "w", "h")
            ):
                mismatches.append(f"text:{text_component['text_id']}:layout")
        filters = {
            str(item.get("relation_id") or ""): item
            for item in profile.get("public_filters") or []
            if isinstance(item, Mapping)
        }
        for item in plan.get("global_filters") or []:
            resource = resource_map.get(f"filter:{item['filter_id']}") or {}
            actual = filters.get(str(resource.get("relation_id") or ""))
            expected_targets = {
                str((_component_resource(resource_map, str(ref)) or {}).get("actual_component_id") or "")
                for ref in item.get("target_component_refs") or []
            }
            if not actual or actual.get("field_id") != str((item.get("field") or {}).get("field_id") or ""):
                mismatches.append(f"filter:{item['filter_id']}:field")
            elif set(actual.get("target_component_ids") or []) != expected_targets:
                mismatches.append(f"filter:{item['filter_id']}:targets")
        if str((profile.get("theme") or {}).get("background_color") or "").upper() != str(
            (plan.get("theme") or {}).get("background_color") or ""
        ).upper():
            mismatches.append("theme")
        return {"ok": not mismatches, "mismatches": mismatches}

    def check_component_values(
        self, plan: Mapping[str, Any], resource_map: Mapping[str, Any]
    ) -> Sequence[Mapping[str, Any]]:
        self._open_dashboard(resource_map)
        results: list[dict[str, Any]] = []
        for component in plan.get("components") or []:
            resource = _component_resource(resource_map, str(component["component_id"])) or {}
            unit_id = str(resource.get("unit_id") or resource.get("resource_id") or "")
            payload = default_unit_value_payload(unit_id, 200)
            payload["versionId"] = "draft"
            response = post_json(self.page, EDIT_UNIT_VALUE_API, payload, timeout_ms=60_000)
            summary = summarize_unit_value(
                unit_id, response, UNIT_TYPE_BY_COMPONENT[str(component["type"])]
            )
            results.append(
                {
                    "component_id": component["component_id"],
                    "unit_id": unit_id,
                    "ok": summary.get("status") == "data_ready",
                    "response_shape": summary.get("response_shape"),
                    "status": summary.get("status"),
                }
            )
        return results

    def check_global_filters(
        self, plan: Mapping[str, Any], resource_map: Mapping[str, Any]
    ) -> Sequence[Mapping[str, Any]]:
        checks_by_filter = {
            str(item.get("filter_id") or ""): item
            for item in plan.get("validation_checks") or []
            if isinstance(item, Mapping) and item.get("filter_id")
        }
        results: list[dict[str, Any]] = []
        for global_filter in plan.get("global_filters") or []:
            check = checks_by_filter.get(str(global_filter["filter_id"]))
            if not check:
                raise UsageError(f"Missing explicit validation check for {global_filter['filter_id']}.")
            component_ref = str(check.get("component_ref") or "")
            component = _component_resource(resource_map, component_ref)
            if not component:
                raise UsageError(f"Global-filter validation component is missing: {component_ref}")
            unit_id = str(component.get("unit_id") or component.get("resource_id") or "")
            field_id = str((global_filter.get("field") or {}).get("field_id") or "")
            filter_value = check.get("filter_value")
            payload = default_unit_value_payload(unit_id, 200)
            payload["publicFilterList"] = [{"fieldId": field_id, "filterValue": [filter_value]}]
            payload["versionId"] = "draft"
            response = post_json(self.page, EDIT_UNIT_VALUE_API, payload, timeout_ms=60_000)
            data = response.get("data")
            unit_payload = data.get(unit_id) if isinstance(data, Mapping) else None
            rows = unit_payload.get("data") if isinstance(unit_payload, Mapping) else None
            expected_value = check.get("expected_value")
            expected_measure = str(check.get("measure_field_id") or "")
            actual_values: list[Any] = []
            if isinstance(rows, list):
                for row in rows:
                    if not isinstance(row, Mapping):
                        continue
                    raw = row.get(expected_measure)
                    if isinstance(raw, Mapping):
                        raw = raw.get("value", raw.get("data"))
                    actual_values.append(raw)
            assertions_passed = any(
                str(value) == str(expected_value) for value in actual_values
            )
            results.append(
                {
                    "filter_id": global_filter["filter_id"],
                    "ok": assertions_passed,
                    "public_filter_list_applied": True,
                    "assertions_passed": assertions_passed,
                    "component_id": component_ref,
                    "measure_field_id": expected_measure,
                    "expected_value": expected_value,
                }
            )
        return results


PRODUCTION_BUILD_ADAPTER_FACTORIES = {
    "taitan_dashboard_build_v1": lambda *, page, args: TaitanDashboardBuildV1Adapter(
        page=page, args=args
    )
}


def resolve_production_build_adapter(plan: dict[str, Any], *, page: Any, args: Any) -> Any:
    adapter_id = str(plan.get("production_adapter") or "")
    factory = PRODUCTION_BUILD_ADAPTER_FACTORIES.get(adapter_id)
    if factory is None:
        raise UsageError(f"No production DashboardBuild adapter is registered: {adapter_id}")
    return factory(page=page, args=args)


__all__ = [
    "PRODUCTION_BUILD_ADAPTER_FACTORIES",
    "TaitanDashboardBuildV1Adapter",
    "resolve_production_build_adapter",
]
