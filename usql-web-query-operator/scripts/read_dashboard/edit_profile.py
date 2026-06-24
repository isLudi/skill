"""Read-only profiling for Taitan dashboard edit pages."""

from __future__ import annotations

import re
import time
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse

from _shared.auth import fill_login_if_present
from _shared.debug import save_debug_artifacts
from _shared.errors import UsageError

from .profile import _walk_dicts, extract_component_units, parse_dashboard_html, post_json


EDIT_DASHBOARD_URL = "https://udata.baijia.com/taitan/"
EDIT_API_ROOT = "https://udata.baijia.com/uanalysis-intelligence"
EDIT_DASHBOARD_CONFIG_API = f"{EDIT_API_ROOT}/config/dashBoard"
EDIT_UNIT_DETAIL_API = f"{EDIT_API_ROOT}/value/unit/detail"
EDIT_UNIT_CONSUMER_DETAIL_API = f"{EDIT_API_ROOT}/value/unit/consumer/detail"
EDIT_PUBLIC_FILTER_DETAIL_API = f"{EDIT_API_ROOT}/value/public/unit/relation/detail"
MODEL_DETAIL_DIM_API = f"{EDIT_API_ROOT}/model/detail/dim"
MODEL_DETAIL_METRIC_API = f"{EDIT_API_ROOT}/model/detail/metric"
MODEL_CUSTOM_COLUMN_API = f"{EDIT_API_ROOT}/model/customized/column/list"
MODEL_SUBJECT_PARAM_LIST_API = f"{EDIT_API_ROOT}/model/subject/paramList"

FIELD_GROUPS = (
    ("row_dimension", "unitDimensionList"),
    ("column_dimension", "unitColumnDimensionList"),
    ("measure", "unitMeasureList"),
    ("aide_measure", "unitAideMeasureList"),
    ("filter", "unitFilterList"),
)


class _PlainTextHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"br", "p", "div", "li", "tr"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if data:
            self.parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"p", "div", "li", "tr"}:
            self.parts.append("\n")

    def text(self) -> str:
        text = "".join(self.parts)
        text = re.sub(r"[ \t\r\f\v]+", " ", text)
        text = re.sub(r"\n\s*\n+", "\n", text)
        return text.strip()


def html_to_text(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    parser = _PlainTextHTMLParser()
    try:
        parser.feed(raw)
        text = parser.text()
    except Exception:  # noqa: BLE001
        text = re.sub(r"<[^>]+>", " ", raw)
        text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_edit_url(edit_url: str | None) -> dict[str, str | None]:
    if not edit_url:
        return {"dashboard_id": None, "html_id": None}
    query = parse_qs(urlparse(edit_url).query)
    return {
        "dashboard_id": (query.get("dashboardId") or [None])[0],
        "html_id": (query.get("htmlId") or [None])[0],
    }


def build_edit_url(dashboard_id: str, html_id: str | None = None) -> str:
    query: dict[str, str] = {"dashboardId": dashboard_id}
    if html_id:
        query["htmlId"] = html_id
    return f"{EDIT_DASHBOARD_URL}?{urlencode(query)}"


def extract_loaded_html_id(url: str) -> str | None:
    return parse_edit_url(url).get("html_id")


def open_edit_page(page: Any, args: Any, context: Any | None, edit_url: str) -> None:
    page.goto(edit_url, wait_until="domcontentloaded", timeout=45_000)
    page.wait_for_timeout(getattr(args, "wait_ms", 3000))
    if fill_login_if_present(page, getattr(args, "username", None), getattr(args, "password", None)):
        page.wait_for_load_state("domcontentloaded", timeout=45_000)
        page.wait_for_timeout(3000)
        if context is not None:
            context.storage_state(path=str(args.state_path))
    if "cas.baijia.com" in page.url or "login" in page.url.lower():
        raise UsageError("Login failed or requires manual verification.")


def fetch_edit_dashboard_config(page: Any, dashboard_id: str, version_id: str) -> dict[str, Any]:
    payload = post_json(
        page,
        EDIT_DASHBOARD_CONFIG_API,
        {"dashboardId": dashboard_id, "isConfig": True, "versionId": version_id},
    )
    config = payload.get("data")
    if not isinstance(config, dict):
        raise UsageError(f"Dashboard edit config not found for {dashboard_id}.")
    return config


def fetch_edit_unit_detail(page: Any, unit_id: str, dashboard_id: str, version_id: str) -> dict[str, Any]:
    if unit_id.startswith("public_filter_relation_"):
        payload = post_json(
            page,
            EDIT_PUBLIC_FILTER_DETAIL_API,
            {"id": unit_id, "isConfig": True, "versionId": version_id},
        )
    else:
        try:
            payload = post_json(
                page,
                EDIT_UNIT_DETAIL_API,
                {"id": unit_id, "dashboardId": dashboard_id, "versionId": version_id},
            )
        except Exception:
            payload = post_json(
                page,
                EDIT_UNIT_CONSUMER_DETAIL_API,
                {"id": unit_id, "isConfig": True, "versionId": version_id},
            )
    detail = payload.get("data")
    if not isinstance(detail, dict):
        raise UsageError(f"Edit unit detail not found for {unit_id}.")
    return detail


def render_definition(definition: Any) -> str:
    if definition in (None, "", []):
        return ""
    if isinstance(definition, list):
        return "".join(render_definition(item) for item in definition)
    if isinstance(definition, dict):
        label = str(definition.get("label") or definition.get("value") or "")
        params = definition.get("functionParams")
        if isinstance(params, list) and params:
            return f"{label}({', '.join(render_definition(item) for item in params)})"
        return label
    return str(definition)


def field_role(group_name: str, org_param_type: Any) -> str:
    if group_name in {"row_dimension", "column_dimension", "filter"}:
        return "dimension"
    if str(org_param_type) == "4":
        return "custom_measure"
    if group_name in {"measure", "aide_measure"}:
        return "measure"
    return "unknown"


def summarize_configured_field(field: dict[str, Any], group_name: str) -> dict[str, Any]:
    fmt = field.get("format") if isinstance(field.get("format"), dict) else {}
    field_id = field.get("fieldId") or field.get("paramId")
    org_param_type = fmt.get("orgParamType") or field.get("fieldType")
    definition = fmt.get("definition")
    return {
        "field_id": str(field_id) if field_id is not None else "",
        "show_name": field.get("showName") or field.get("name"),
        "group": group_name,
        "role": field_role(group_name, org_param_type),
        "field_type": field.get("fieldType"),
        "org_param_type": org_param_type,
        "change_param_type": fmt.get("changeParamType"),
        "data_type": fmt.get("dataType"),
        "measure_type": fmt.get("measureType"),
        "dimension_type": fmt.get("dimensionType"),
        "number_type": fmt.get("numberType"),
        "decimal_places": fmt.get("decimalPlaces"),
        "sort_value": field.get("sortValue"),
        "filter_type": fmt.get("filterType") or [],
        "condition": fmt.get("condition"),
        "definition": definition,
        "definition_text": render_definition(definition),
    }


def selected_field_payload(fields: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for field in fields:
        key = str(field.get("field_id") or "")
        if not key:
            continue
        change_param_type = field.get("change_param_type")
        org_param_type = field.get("org_param_type")
        identity = (key, str(change_param_type), str(org_param_type))
        if identity in seen:
            continue
        seen.add(identity)
        selected.append(
            {
                "key": key,
                "changeParamType": change_param_type,
                "orgParamType": org_param_type,
            }
        )
    return selected


def fetch_field_detail(page: Any, field: dict[str, Any], model_type: int | None) -> dict[str, Any]:
    field_id = str(field.get("field_id") or "")
    if not field_id:
        return {}
    org_param_type = field.get("org_param_type")
    if field_id.startswith("customized_") or str(org_param_type) == "4":
        payload = post_json(page, MODEL_CUSTOM_COLUMN_API, {"id": field_id})
    elif str(org_param_type) == "2":
        payload = post_json(page, MODEL_DETAIL_DIM_API, {"id": field_id, "modelType": model_type or 2})
    else:
        payload = post_json(page, MODEL_DETAIL_METRIC_API, {"id": field_id, "modelType": model_type or 2})
    return normalize_field_detail(field_id, payload.get("data"))


def normalize_field_detail(field_id: str, data: Any) -> dict[str, Any]:
    item: dict[str, Any] = {}
    if isinstance(data, list) and data:
        first = data[0]
        if isinstance(first, dict):
            item = first
    elif isinstance(data, dict):
        item = data
    if not item:
        return {"field_id": field_id, "detail_type": "unknown"}
    if "columnKey" in item or "formula" in item:
        return {
            "field_id": field_id,
            "detail_type": "customized_column",
            "column_key": item.get("columnKey"),
            "column_name": item.get("columnName"),
            "column_desc": item.get("columnDesc"),
            "formula": item.get("formula"),
            "indicator_type": item.get("indicatorType"),
            "dependency_indicators": item.get("dependencyIndicators") or [],
            "data_type": item.get("dataType"),
            "owner": item.get("owner") or item.get("createName") or item.get("updateName"),
            "subject_id": item.get("subjectId"),
            "create_time": item.get("createTime"),
            "update_time": item.get("updateTime"),
        }
    if "metricId" in item:
        models = item.get("modelsList") if isinstance(item.get("modelsList"), list) else []
        return {
            "field_id": field_id,
            "detail_type": "metric",
            "metric_id": item.get("metricId"),
            "name_en": item.get("nameEn"),
            "name_cn": item.get("nameCn"),
            "metric_type": item.get("type"),
            "owner": item.get("owner"),
            "models": [
                {
                    "id": model.get("id"),
                    "col_data_field": model.get("colDataField"),
                    "query_sql": model.get("querySql"),
                }
                for model in models
                if isinstance(model, dict)
            ],
            "metric_versions": item.get("metricVersionList") or [],
        }
    if "nameEn" in item or "dimsModelsVoList" in item:
        models = item.get("dimsModelsVoList") if isinstance(item.get("dimsModelsVoList"), list) else []
        return {
            "field_id": field_id,
            "detail_type": "dimension",
            "id": item.get("id"),
            "name_en": item.get("nameEn"),
            "name_cn": item.get("nameCn"),
            "data_type_code": item.get("dataTypeCode"),
            "owner": item.get("owner"),
            "models": [
                {
                    "id": model.get("id"),
                    "col_data_field": model.get("colDataField"),
                    "query_sql": model.get("querySql"),
                }
                for model in models
                if isinstance(model, dict)
            ],
        }
    return {"field_id": field_id, "detail_type": "unknown", "keys": sorted(item.keys())}


def merge_field_detail(field: dict[str, Any], detail: dict[str, Any]) -> dict[str, Any]:
    merged = dict(field)
    merged["detail"] = detail
    merged["formula"] = detail.get("formula") or field.get("definition_text") or ""
    merged["business_name"] = (
        detail.get("column_name")
        or detail.get("name_cn")
        or detail.get("name_en")
        or field.get("show_name")
    )
    merged["description"] = detail.get("column_desc") or ""
    merged["dependencies"] = detail.get("dependency_indicators") or []
    return merged


def summarize_edit_unit(
    page: Any,
    unit_detail: dict[str, Any],
    field_detail_cache: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    model_type = None
    dashboard_model = unit_detail.get("dashboardModel") if isinstance(unit_detail.get("dashboardModel"), dict) else {}
    if isinstance(dashboard_model, dict):
        model_type = dashboard_model.get("modelType")

    configured_fields: list[dict[str, Any]] = []
    for group_name, field_key in FIELD_GROUPS:
        for field in unit_detail.get(field_key) or []:
            if isinstance(field, dict):
                configured_fields.append(summarize_configured_field(field, group_name))

    merged_fields: list[dict[str, Any]] = []
    for field in configured_fields:
        field_id = str(field.get("field_id") or "")
        cache_key = (field_id, str(field.get("org_param_type") or ""))
        detail = field_detail_cache.get(cache_key)
        if detail is None:
            try:
                detail = fetch_field_detail(page, field, model_type)
            except Exception as exc:  # noqa: BLE001
                detail = {"field_id": field_id, "detail_type": "error", "message": str(exc)}
            field_detail_cache[cache_key] = detail
        merged_fields.append(merge_field_detail(field, detail))

    return {
        "unit_id": unit_detail.get("unitId"),
        "unit_name": unit_detail.get("unitName"),
        "unit_type": unit_detail.get("unitType"),
        "model_id": unit_detail.get("modelId"),
        "model_name": unit_detail.get("modelName"),
        "model_type": model_type,
        "description": unit_detail.get("description"),
        "dashboard_model": dashboard_model,
        "format_summary": summarize_unit_format(unit_detail.get("format") if isinstance(unit_detail.get("format"), dict) else {}),
        "selected_fields": selected_field_payload(merged_fields),
        "fields": merged_fields,
        "field_count": len(merged_fields),
        "measure_count": sum(1 for field in merged_fields if field.get("group") in {"measure", "aide_measure"}),
        "custom_formula_count": sum(1 for field in merged_fields if field.get("detail", {}).get("formula")),
    }


def summarize_unit_format(fmt: dict[str, Any]) -> dict[str, Any]:
    return {
        "display_setting_type": fmt.get("displaySettingType"),
        "page_size": fmt.get("pageSize"),
        "is_download": fmt.get("isDownload"),
        "is_open": fmt.get("isOpen"),
        "is_total": fmt.get("isTotal"),
        "field_measure_name_sort_list": fmt.get("fieldMeasureNameSortList") or [],
        "switch_order_list": fmt.get("switchOrderList") or [],
        "switch_groups": fmt.get("switchGroups") or [],
        "display_list_count": len(fmt.get("displayList") or []),
    }


def extract_text_notes(dashboard_html: dict[str, Any], unit_details: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    notes: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add_note(source: str, unit_id: str | None, value: Any) -> None:
        text = html_to_text(value)
        if not text or text in seen:
            return
        seen.add(text)
        notes.append({"source": source, "unit_id": unit_id, "text": text})

    for node in _walk_dicts(dashboard_html):
        settings = node.get("settings") if isinstance(node, dict) else None
        if not isinstance(settings, dict):
            props = node.get("props") if isinstance(node, dict) else None
            settings = props.get("settings") if isinstance(props, dict) else None
        if not isinstance(settings, dict):
            continue
        unit_id = settings.get("unitId")
        rich = settings.get("richTextFormat") if isinstance(settings.get("richTextFormat"), dict) else {}
        textbox = rich.get("textBoxConfig") if isinstance(rich.get("textBoxConfig"), dict) else {}
        add_note("dashboard_html.richTextFormat.textBoxConfig.textContent", unit_id, textbox.get("textContent"))
        add_note("dashboard_html.richTextFormat.textBoxConfig.tempTextContent", unit_id, textbox.get("tempTextContent"))

    for unit_id, detail in unit_details.items():
        fmt = detail.get("format") if isinstance(detail.get("format"), dict) else {}
        textbox = fmt.get("textBoxConfig") if isinstance(fmt.get("textBoxConfig"), dict) else {}
        add_note("unit_detail.format.textBoxConfig.textContent", unit_id, textbox.get("textContent"))
        add_note("unit_detail.format.textBoxConfig.tempTextContent", unit_id, textbox.get("tempTextContent"))
    return notes


def discover_subject_ids(*objects: Any) -> list[int]:
    subject_ids: set[int] = set()
    for obj in objects:
        for node in _walk_dicts(obj):
            value = node.get("subjectId") if isinstance(node, dict) else None
            if value is None and isinstance(node, dict):
                value = node.get("subject_id")
            if value is None:
                continue
            try:
                subject_ids.add(int(value))
            except (TypeError, ValueError):
                continue
    return sorted(subject_ids)


def flatten_param_tree(tree: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    def walk(node: Any, parents: list[str]) -> None:
        if not isinstance(node, dict):
            return
        title = str(node.get("title") or node.get("name") or node.get("key") or "")
        path = parents + ([title] if title else [])
        children = node.get("children") if isinstance(node.get("children"), list) else []
        if node.get("isLeaf") or not children:
            key = node.get("key")
            if key not in {None, "dimension", "metric"}:
                rows.append(
                    {
                        "key": key,
                        "title": title,
                        "path": " / ".join(path),
                        "org_param_type": node.get("orgParamType"),
                        "change_param_type": node.get("changeParamType"),
                        "data_type": node.get("dataType"),
                        "is_choice": node.get("isChoice"),
                        "is_aggregation": node.get("isAggregation"),
                        "definition": node.get("definition"),
                        "definition_text": render_definition(node.get("definition")),
                        "filter_type": node.get("filterType") or [],
                    }
                )
        for child in children:
            walk(child, path)

    walk(tree, [])
    return rows


def fetch_dataset_fields(
    page: Any,
    dashboard_id: str,
    subject_ids: list[int],
    model_types: list[int],
    selected_fields: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    datasets: list[dict[str, Any]] = []
    if not subject_ids:
        return datasets
    model_type = model_types[0] if model_types else 2
    for subject_id in subject_ids:
        try:
            payload = post_json(
                page,
                MODEL_SUBJECT_PARAM_LIST_API,
                {
                    "modelType": model_type,
                    "dashboardId": dashboard_id,
                    "subjectId": subject_id,
                    "selected": selected_fields,
                },
            )
            tree = payload.get("data")
            datasets.append(
                {
                    "subject_id": subject_id,
                    "model_type": model_type,
                    "field_count": len(flatten_param_tree(tree)),
                    "fields": flatten_param_tree(tree),
                }
            )
        except Exception as exc:  # noqa: BLE001
            datasets.append({"subject_id": subject_id, "model_type": model_type, "error": str(exc)})
    return datasets


def profile_edit_dashboard(
    page: Any,
    dashboard_id: str,
    html_id: str | None,
    edit_url: str,
    version_id: str,
    artifacts_dir: Path,
    debug_artifacts: bool,
    include_dataset_fields: bool,
) -> dict[str, Any]:
    config = fetch_edit_dashboard_config(page, dashboard_id, version_id)
    dashboard_html = parse_dashboard_html(config)
    component_units = extract_component_units(dashboard_html)

    unit_details: dict[str, dict[str, Any]] = {}
    public_filters: dict[str, Any] = {}
    pivot_units: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    field_detail_cache: dict[tuple[str, str], dict[str, Any]] = {}

    for component in component_units:
        unit_id = str(component.get("unit_id") or "")
        if not unit_id:
            continue
        try:
            detail = fetch_edit_unit_detail(page, unit_id, dashboard_id, version_id)
            unit_details[unit_id] = detail
            if unit_id.startswith("public_filter_relation_"):
                public_filters[unit_id] = detail
                continue
            if detail.get("unitType") == "u_pivot":
                pivot_profile = summarize_edit_unit(page, detail, field_detail_cache)
                pivot_profile["component"] = component
                pivot_units.append(pivot_profile)
        except Exception as exc:  # noqa: BLE001
            errors.append({"unit_id": unit_id, "message": str(exc)})

    all_selected_fields: list[dict[str, Any]] = []
    model_types: set[int] = set()
    for unit in pivot_units:
        all_selected_fields.extend(unit.get("selected_fields") or [])
        model_type = unit.get("model_type")
        if model_type is not None:
            try:
                model_types.add(int(model_type))
            except (TypeError, ValueError):
                pass

    subject_ids = discover_subject_ids(public_filters, field_detail_cache)
    dataset_fields = (
        fetch_dataset_fields(page, dashboard_id, subject_ids, sorted(model_types), all_selected_fields)
        if include_dataset_fields
        else []
    )
    text_notes = extract_text_notes(dashboard_html, unit_details)
    dashboard_name = str(config.get("dashboardName") or dashboard_id)
    measure_count = sum(int(unit.get("measure_count") or 0) for unit in pivot_units)
    configured_field_count = sum(int(unit.get("field_count") or 0) for unit in pivot_units)
    formula_count = sum(int(unit.get("custom_formula_count") or 0) for unit in pivot_units)

    profile = {
        "ok": True,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source": "taitan_edit_readonly",
        "readonly_boundary": (
            "This profile only calls read endpoints for dashboard config, unit details, "
            "model field details, and custom formulas. It does not call save, publish, "
            "delete, create, or update endpoints."
        ),
        "input": {
            "edit_url": edit_url,
            "dashboard_id": dashboard_id,
            "html_id": html_id,
            "version_id": version_id,
        },
        "loaded_url": page.url,
        "loaded_html_id": extract_loaded_html_id(page.url),
        "dashboard_id": dashboard_id,
        "dashboard_name": dashboard_name,
        "config_html_id": config.get("htmlId"),
        "config_summary": {
            "dashboard_level": config.get("dashboardLevel"),
            "package_version": config.get("packageVersion"),
            "owner_list": config.get("ownerList") or [],
            "have_edit_permission": config.get("haveEditPermission"),
            "component_package_count": len(dashboard_html.get("componentsMap") or []),
            "component_unit_count": len(component_units),
        },
        "components": component_units,
        "pivot_units": pivot_units,
        "public_filter_unit_count": len(public_filters),
        "subject_ids": subject_ids,
        "dataset_fields": dataset_fields,
        "text_notes": text_notes,
        "summary": {
            "pivot_unit_count": len(pivot_units),
            "configured_field_count": configured_field_count,
            "measure_count": measure_count,
            "custom_formula_count": formula_count,
            "text_note_count": len(text_notes),
            "dataset_subject_count": len(dataset_fields),
            "error_count": len(errors),
        },
        "errors": errors,
    }
    if debug_artifacts:
        save_debug_artifacts(page, artifacts_dir, f"edit_profile_{dashboard_id}")
    return profile


def build_edit_profile_summary(profile: dict[str, Any], output_path: Path) -> dict[str, Any]:
    summary = profile.get("summary") or {}
    return {
        "ok": bool(profile.get("ok")),
        "dashboard_name": profile.get("dashboard_name"),
        "dashboard_id": profile.get("dashboard_id"),
        "output_path": str(output_path),
        "pivot_unit_count": summary.get("pivot_unit_count", 0),
        "configured_field_count": summary.get("configured_field_count", 0),
        "measure_count": summary.get("measure_count", 0),
        "custom_formula_count": summary.get("custom_formula_count", 0),
        "text_note_count": summary.get("text_note_count", 0),
        "message": "Dashboard edit metric profile finished." if profile.get("ok") else profile.get("message"),
    }


def build_edit_error_profile(dashboard_id: str, edit_url: str, version_id: str, message: str) -> dict[str, Any]:
    return {
        "ok": False,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source": "taitan_edit_readonly",
        "input": {"edit_url": edit_url, "dashboard_id": dashboard_id, "version_id": version_id},
        "dashboard_id": dashboard_id,
        "message": message,
    }
