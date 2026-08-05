"""Hash-bound plans, receipts, and readback for permanent parameterized templates."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from _shared.errors import UsageError

from .sql_policy import analyze_sql_policy


PLAN_SCHEMA_VERSION = "1.0.0"
PLAN_OPERATION = "create_permanent_parameterized_template"
UPDATE_PLAN_OPERATION = "update_permanent_parameterized_template"
CREATE_RECEIPT_OPERATION = "apply_permanent_parameterized_template_creation"
UPDATE_RECEIPT_OPERATION = "apply_permanent_parameterized_template_update"
PUBLISH_RECEIPT_OPERATION = "publish_permanent_parameterized_template"
DEFAULT_INSTANCE_KEY = "dlc_presto"
TEMPLATE_NAME_PATTERN = re.compile(r"^.{1,20}$", re.DOTALL)
PLACEHOLDER_RE = re.compile(r"\$\{([A-Za-z0-9_.:-]+)\}")
ANY_PLACEHOLDER_RE = re.compile(r"\$\{[^}]*\}|\{\{[^}]*\}\}")
SUPPORTED_PARAMETER_MODES = frozenset({"condition", "date"})


@dataclass(frozen=True)
class PermanentTemplateCreationPlan:
    schema_version: str
    operation: str
    created_at: str
    status: str
    template_name: str
    description: str
    owner: str
    creator: str
    sql_file: str
    sql_sha256: str
    sql_bytes: int
    instance_key: str
    baseline_template_ids: tuple[int, ...]
    template_variables: tuple[dict[str, Any], ...]
    template_params: tuple[dict[str, Any], ...]
    table_names: tuple[str, ...]
    parser_sha256: str
    metadata_sha256: str
    sql_policy: dict[str, Any]
    diagnostics: tuple[dict[str, str], ...]
    policy: dict[str, Any]
    plan_sha256: str

    def hash_payload(self) -> dict[str, Any]:
        payload = self.to_json()
        payload.pop("plan_sha256", None)
        return payload

    def computed_sha256(self) -> str:
        return sha256_json(self.hash_payload())

    def to_json(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "operation": self.operation,
            "created_at": self.created_at,
            "status": self.status,
            "template_name": self.template_name,
            "description": self.description,
            "owner": self.owner,
            "creator": self.creator,
            "sql_file": self.sql_file,
            "sql_sha256": self.sql_sha256,
            "sql_bytes": self.sql_bytes,
            "instance_key": self.instance_key,
            "baseline_template_ids": list(self.baseline_template_ids),
            "template_variables": list(self.template_variables),
            "template_params": list(self.template_params),
            "table_names": list(self.table_names),
            "parser_sha256": self.parser_sha256,
            "metadata_sha256": self.metadata_sha256,
            "sql_policy": self.sql_policy,
            "diagnostics": list(self.diagnostics),
            "policy": self.policy,
            "plan_sha256": self.plan_sha256,
        }

    @classmethod
    def from_json(cls, payload: dict[str, Any]) -> "PermanentTemplateCreationPlan":
        if payload.get("schema_version") != PLAN_SCHEMA_VERSION:
            raise UsageError("unsupported permanent-template plan schema_version")
        if payload.get("operation") not in {PLAN_OPERATION, UPDATE_PLAN_OPERATION}:
            raise UsageError("artifact is not a permanent-template creation or update plan")
        try:
            plan = cls(
                schema_version=str(payload["schema_version"]),
                operation=str(payload["operation"]),
                created_at=str(payload["created_at"]),
                status=str(payload["status"]),
                template_name=str(payload["template_name"]),
                description=str(payload["description"]),
                owner=str(payload["owner"]),
                creator=str(payload["creator"]),
                sql_file=str(payload["sql_file"]),
                sql_sha256=str(payload["sql_sha256"]),
                sql_bytes=int(payload["sql_bytes"]),
                instance_key=str(payload["instance_key"]),
                baseline_template_ids=tuple(int(item) for item in payload["baseline_template_ids"]),
                template_variables=tuple(dict(item) for item in payload["template_variables"]),
                template_params=tuple(dict(item) for item in payload["template_params"]),
                table_names=tuple(str(item) for item in payload["table_names"]),
                parser_sha256=str(payload["parser_sha256"]),
                metadata_sha256=str(payload["metadata_sha256"]),
                sql_policy=dict(payload["sql_policy"]),
                diagnostics=tuple(dict(item) for item in payload.get("diagnostics") or []),
                policy=dict(payload["policy"]),
                plan_sha256=str(payload["plan_sha256"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise UsageError("invalid permanent-template creation plan structure") from exc
        if plan.plan_sha256 != plan.computed_sha256():
            raise UsageError("permanent-template plan hash is invalid or the artifact was modified")
        return plan


def build_permanent_template_plan(
    *,
    template_name: str,
    description: str,
    owner: str,
    creator: str,
    sql_file: Path,
    sql_text: str,
    instance_key: str,
    existing_template_ids: list[int],
    parser_payload: dict[str, Any],
    parameter_config: dict[str, Any],
    variable_display_names: dict[str, str],
    target_template_id: int | None = None,
    baseline_state: dict[str, Any] | None = None,
    created_at: datetime | None = None,
) -> PermanentTemplateCreationPlan:
    diagnostics: list[dict[str, str]] = []
    name = template_name.strip()
    if name != template_name or not TEMPLATE_NAME_PATTERN.fullmatch(name):
        diagnostics.append(
            _diagnostic(
                "INVALID_TEMPLATE_NAME",
                "Template name must be 1-20 characters without leading or trailing whitespace.",
            )
        )
    if target_template_id is None and existing_template_ids:
        diagnostics.append(
            _diagnostic(
                "TEMPLATE_NAME_ALREADY_EXISTS",
                "A created template already uses the requested exact name.",
            )
        )
    if target_template_id is not None:
        if target_template_id not in set(existing_template_ids):
            diagnostics.append(
                _diagnostic(
                    "TARGET_TEMPLATE_NOT_FOUND",
                    "The exact target template id was not found in the authenticated created-template listing.",
                )
            )
        if not isinstance(baseline_state, dict) or not baseline_state:
            diagnostics.append(
                _diagnostic(
                    "MISSING_UPDATE_BASELINE",
                    "An in-place template update requires a read-only baseline state.",
                )
            )
    if not creator.strip():
        diagnostics.append(_diagnostic("MISSING_CREATOR", "Authenticated creator name is required."))
    if not instance_key.strip():
        diagnostics.append(_diagnostic("MISSING_INSTANCE_KEY", "Template data-source instanceKey is required."))

    placeholder_names, placeholder_diagnostics = extract_placeholder_names(sql_text)
    diagnostics.extend(placeholder_diagnostics)
    if not placeholder_names:
        diagnostics.append(
            _diagnostic(
                "PARAMETERIZED_SQL_REQUIRED",
                "Permanent-template creation requires at least one ${name} SQL parameter.",
            )
        )

    sql_policy = analyze_parameterized_sql_policy(sql_text)
    if sql_policy.get("allowed") is not True:
        codes = ", ".join(
            str(item.get("code"))
            for item in sql_policy.get("diagnostics", [])
            if item.get("severity") == "error"
        )
        diagnostics.append(
            _diagnostic(
                "SQL_POLICY_BLOCKED",
                f"Parameterized SQL failed the read-only SQL policy: {codes or 'unknown error'}.",
            )
        )

    parser_fingerprint = parser_fingerprint_payload(parser_payload)
    parser_param_names = [item["name"] for item in parser_fingerprint["template_params"]]
    if sorted(placeholder_names) != sorted(parser_param_names):
        diagnostics.append(
            _diagnostic(
                "PARSER_PARAMETER_MISMATCH",
                "SQL placeholder names do not exactly match the platform parser parameters.",
            )
        )

    template_variables, variable_diagnostics = build_template_variables(
        parser_payload.get("templateVariable"), variable_display_names
    )
    diagnostics.extend(variable_diagnostics)
    template_params, parameter_diagnostics = build_template_params(
        parser_payload.get("templateParam"), parameter_config
    )
    diagnostics.extend(parameter_diagnostics)
    table_names = tuple(sorted({str(item).strip() for item in parser_payload.get("tableName") or [] if str(item).strip()}))
    metadata = metadata_payload(
        instance_key=instance_key,
        template_variables=template_variables,
        template_params=template_params,
        table_names=table_names,
    )
    timestamp = created_at or datetime.now(timezone.utc)
    canonical_sql = canonical_template_sql(sql_text)
    operation = UPDATE_PLAN_OPERATION if target_template_id is not None else PLAN_OPERATION
    plan = PermanentTemplateCreationPlan(
        schema_version=PLAN_SCHEMA_VERSION,
        operation=operation,
        created_at=timestamp.isoformat(),
        status="blocked" if diagnostics else "ready",
        template_name=name,
        description=description,
        owner=owner.strip(),
        creator=creator.strip(),
        sql_file=str(sql_file.expanduser().resolve()),
        sql_sha256=template_sql_sha256(canonical_sql),
        sql_bytes=len(canonical_sql.encode("utf-8")),
        instance_key=instance_key.strip(),
        baseline_template_ids=tuple(sorted(set(existing_template_ids))),
        template_variables=tuple(template_variables),
        template_params=tuple(template_params),
        table_names=table_names,
        parser_sha256=sha256_json(parser_fingerprint),
        metadata_sha256=sha256_json(metadata),
        sql_policy=sql_policy,
        diagnostics=tuple(diagnostics),
        policy={
            "read_only_plan": True,
            "apply_requires_exact_plan_sha256": True,
            "apply_requires_explicit_production_confirmation": True,
            "apply_creates_unpublished_template_only": target_template_id is None,
            "apply_updates_existing_template_in_place": target_template_id is not None,
            "preserve_existing_template_id_and_access": target_template_id is not None,
            "publish_requires_successful_exact_create_receipt": True,
            "publish_requires_separate_confirmation": True,
            "post_create_and_post_publish_readback": True,
            "automatic_delete_offline_or_rollback": False,
            "target_template_id": target_template_id,
            "baseline_state": dict(baseline_state or {}),
        },
        plan_sha256="",
    )
    return replace(plan, plan_sha256=plan.computed_sha256())


def extract_placeholder_names(sql_text: str) -> tuple[list[str], list[dict[str, str]]]:
    diagnostics: list[dict[str, str]] = []
    names = PLACEHOLDER_RE.findall(sql_text)
    recognized = PLACEHOLDER_RE.sub("NULL", sql_text)
    if ANY_PLACEHOLDER_RE.search(recognized):
        diagnostics.append(
            _diagnostic(
                "INVALID_TEMPLATE_PARAMETER",
                "SQL contains an empty or unsupported template-parameter token.",
            )
        )
    return list(dict.fromkeys(names)), diagnostics


def analyze_parameterized_sql_policy(sql_text: str) -> dict[str, Any]:
    sanitized = PLACEHOLDER_RE.sub("NULL", sql_text)
    return analyze_sql_policy(sanitized, mode="audit")


def parser_fingerprint_payload(parser_payload: dict[str, Any]) -> dict[str, Any]:
    variables = []
    for row in parser_payload.get("templateVariable") or []:
        if not isinstance(row, dict):
            continue
        variables.append(
            {
                "name": _text(row.get("name")),
                "attribute": _int_or_text(row.get("attribute")),
                "type": _text(row.get("type")),
            }
        )
    params = []
    for row in parser_payload.get("templateParam") or []:
        if not isinstance(row, dict):
            continue
        params.append(
            {
                "name": _text(row.get("name")),
                "type": _text(row.get("type")),
                "condition": _text(row.get("condition")),
            }
        )
    return {
        "template_variables": variables,
        "template_params": params,
        "table_names": sorted(
            {str(item).strip() for item in parser_payload.get("tableName") or [] if str(item).strip()}
        ),
    }


def build_template_variables(
    rows: Any,
    display_names: dict[str, str],
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    diagnostics: list[dict[str, str]] = []
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        name = _text(row.get("name"))
        if not name or name in seen:
            diagnostics.append(_diagnostic("INVALID_TEMPLATE_VARIABLE", "Parser returned an empty or duplicate output variable."))
            continue
        seen.add(name)
        show_name = display_names.get(name, _text(row.get("showName")) or name).strip()
        if not show_name:
            diagnostics.append(_diagnostic("EMPTY_VARIABLE_DISPLAY_NAME", f"Output variable {name} has an empty display name."))
            show_name = name
        normalized.append(
            {
                "name": name,
                "showName": show_name,
                "attribute": _int_or_text(row.get("attribute")),
                "type": _text(row.get("type")),
                "category": 1,
            }
        )
    unknown = sorted(set(display_names) - seen)
    if unknown:
        diagnostics.append(
            _diagnostic(
                "UNKNOWN_VARIABLE_DISPLAY_NAME",
                "Display-name overrides reference unknown parser variables: " + ", ".join(unknown),
            )
        )
    if not normalized:
        diagnostics.append(_diagnostic("NO_TEMPLATE_VARIABLES", "Platform parser returned no output variables."))
    return normalized, diagnostics


def build_template_params(
    rows: Any,
    parameter_config: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    diagnostics: list[dict[str, str]] = []
    normalized: list[dict[str, Any]] = []
    parser_names: set[str] = set()
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        name = _text(row.get("name"))
        if not name or name in parser_names:
            diagnostics.append(_diagnostic("INVALID_TEMPLATE_PARAM", "Parser returned an empty or duplicate parameter."))
            continue
        parser_names.add(name)
        config = parameter_config.get(name)
        if not isinstance(config, dict):
            diagnostics.append(_diagnostic("MISSING_PARAMETER_CONFIG", f"Parameter {name} has no reviewed configuration."))
            config = {}
        mode = _text(config.get("mode")).lower()
        if mode not in SUPPORTED_PARAMETER_MODES:
            diagnostics.append(
                _diagnostic(
                    "UNSUPPORTED_PARAMETER_MODE",
                    f"Parameter {name} mode must be date or condition.",
                )
            )
            mode = "condition"
        show_name = _text(config.get("showName"))
        if not show_name:
            diagnostics.append(_diagnostic("MISSING_PARAMETER_DISPLAY_NAME", f"Parameter {name} requires showName."))
            show_name = name
        mandatory = config.get("mandatory", 2)
        if mandatory != 2:
            diagnostics.append(
                _diagnostic(
                    "UNSUPPORTED_PARAMETER_MANDATORY",
                    f"Parameter {name} must be configured as mandatory=2.",
                )
            )
            mandatory = 2
        item: dict[str, Any] = {
            "name": name,
            "showName": show_name,
            "category": 0,
            "mandatory": mandatory,
            "condition": _text(row.get("condition")),
        }
        if mode == "date":
            date_format = _text(config.get("format")) or "yyyy-MM-dd"
            if date_format != "yyyy-MM-dd":
                diagnostics.append(
                    _diagnostic(
                        "UNSUPPORTED_DATE_FORMAT",
                        f"Parameter {name} date format must be yyyy-MM-dd.",
                    )
                )
                date_format = "yyyy-MM-dd"
            item.update({"format": date_format, "paramType": 3})
        else:
            parameter_type = _text(config.get("type")) or _text(row.get("type"))
            if not parameter_type:
                diagnostics.append(_diagnostic("MISSING_PARAMETER_TYPE", f"Parameter {name} requires a condition type."))
            item.update({"type": parameter_type, "paramType": 1})
        normalized.append(item)
    unknown = sorted(set(parameter_config) - parser_names)
    if unknown:
        diagnostics.append(
            _diagnostic(
                "UNKNOWN_PARAMETER_CONFIG",
                "Parameter configuration references unknown parser parameters: " + ", ".join(unknown),
            )
        )
    return normalized, diagnostics


def template_params_for_save(rows: tuple[dict[str, Any], ...] | list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        keys = ["name", "showName", "category", "mandatory", "paramType"]
        keys.append("format" if int(row.get("paramType") or 0) == 3 else "type")
        output.append({key: row[key] for key in keys if key in row})
    return output


def normalize_readback_metadata(detail: dict[str, Any]) -> dict[str, Any]:
    variables: list[dict[str, Any]] = []
    for row in detail.get("templateVariable") or []:
        if not isinstance(row, dict):
            continue
        variables.append(
            {
                "name": _text(row.get("name")),
                "showName": _text(row.get("showName")),
                "attribute": _int_or_text(row.get("attribute")),
                "type": _text(row.get("type")),
                "category": 1,
            }
        )
    params: list[dict[str, Any]] = []
    for row in detail.get("templateParam") or []:
        if not isinstance(row, dict):
            continue
        param_type = int(row.get("paramType") or 0)
        item: dict[str, Any] = {
            "name": _text(row.get("name")),
            "showName": _text(row.get("showName")),
            "category": 0,
            "mandatory": int(row.get("mandatory") or 0),
            "condition": _text(row.get("condition")),
            "paramType": param_type,
        }
        if param_type == 3:
            item["format"] = _text(row.get("format"))
        else:
            item["type"] = _text(row.get("type"))
        params.append(item)
    return metadata_payload(
        instance_key=_text(detail.get("instanceKey")),
        template_variables=variables,
        template_params=params,
        table_names=tuple(sorted({str(item).strip() for item in detail.get("tableName") or [] if str(item).strip()})),
    )


def metadata_payload(
    *,
    instance_key: str,
    template_variables: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    template_params: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    table_names: tuple[str, ...] | list[str],
) -> dict[str, Any]:
    return {
        "instance_key": instance_key,
        "template_variables": list(template_variables),
        "template_params": list(template_params),
        "table_names": list(table_names),
    }


def verify_template_readback(
    detail: dict[str, Any],
    plan: PermanentTemplateCreationPlan,
    *,
    expected_status: int,
) -> dict[str, Any]:
    failures: list[str] = []
    template_id = _int_value(detail.get("id"))
    if not template_id:
        failures.append("missing template id")
    if _text(detail.get("name")) != plan.template_name:
        failures.append("template name mismatch")
    if _int_value(detail.get("status")) != expected_status:
        failures.append("template status mismatch")
    actual_sql_sha256 = template_sql_sha256(_text_raw(detail.get("sqlDetail")))
    if actual_sql_sha256 != plan.sql_sha256:
        failures.append("SQL hash mismatch")
    actual_metadata = normalize_readback_metadata(detail)
    actual_metadata_sha256 = sha256_json(actual_metadata)
    if actual_metadata_sha256 != plan.metadata_sha256:
        failures.append("parameter/output metadata hash mismatch")
    result = {
        "verified": not failures,
        "template_id": template_id,
        "template_name": _text(detail.get("name")),
        "status": _int_value(detail.get("status")),
        "sql_sha256": actual_sql_sha256,
        "metadata_sha256": actual_metadata_sha256,
        "instance_key": _text(detail.get("instanceKey")),
        "variable_count": len(actual_metadata["template_variables"]),
        "parameter_count": len(actual_metadata["template_params"]),
        "failures": failures,
    }
    if failures:
        raise UsageError("permanent-template readback failed: " + "; ".join(failures))
    return result


def validate_parser_drift(parser_payload: dict[str, Any], plan: PermanentTemplateCreationPlan) -> None:
    actual = sha256_json(parser_fingerprint_payload(parser_payload))
    if actual != plan.parser_sha256:
        raise UsageError("platform SQL parser metadata changed after the reviewed template plan")


def load_parameter_config(path: Path) -> dict[str, Any]:
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise UsageError(f"parameter configuration file does not exist: {resolved}")
    try:
        payload = json.loads(resolved.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise UsageError(f"parameter configuration is not valid UTF-8 JSON: {resolved}") from exc
    if not isinstance(payload, dict):
        raise UsageError("parameter configuration root must be an object keyed by parser parameter name")
    return payload


def parse_display_name_overrides(values: list[str] | None) -> dict[str, str]:
    output: dict[str, str] = {}
    for value in values or []:
        if "=" not in value:
            raise UsageError("variable display-name overrides must use parser_name=display_name")
        name, display_name = value.split("=", 1)
        name = name.strip()
        display_name = display_name.strip()
        if not name or not display_name or name in output:
            raise UsageError("variable display-name overrides require unique non-empty names and values")
        output[name] = display_name
    return output


def load_template_sql(path: Path) -> str:
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise UsageError(f"template SQL file does not exist: {resolved}")
    content = resolved.read_bytes()
    if content.startswith(b"\xef\xbb\xbf"):
        raise UsageError("template SQL must be UTF-8 without BOM")
    try:
        sql_text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise UsageError("template SQL is not valid UTF-8") from exc
    if "\x00" in sql_text or not sql_text.strip():
        raise UsageError("template SQL is empty or contains NUL bytes")
    return canonical_template_sql(sql_text)


def canonical_template_sql(sql_text: str) -> str:
    return sql_text.replace("\r\n", "\n").replace("\r", "\n").rstrip() + "\n"


def template_sql_sha256(sql_text: str) -> str:
    return hashlib.sha256(canonical_template_sql(sql_text).encode("utf-8")).hexdigest()


def write_plan(path: Path, plan: PermanentTemplateCreationPlan) -> None:
    _write_json(path, plan.to_json())


def load_plan(path: Path) -> PermanentTemplateCreationPlan:
    payload = _load_json(path, "permanent-template plan")
    return PermanentTemplateCreationPlan.from_json(payload)


def finalize_receipt(receipt: dict[str, Any]) -> dict[str, Any]:
    finalized = dict(receipt)
    finalized.pop("receipt_sha256", None)
    finalized["receipt_sha256"] = sha256_json(finalized)
    return finalized


def write_receipt(path: Path, receipt: dict[str, Any]) -> dict[str, Any]:
    finalized = finalize_receipt(receipt)
    _write_json(path, finalized)
    return finalized


def load_create_receipt(path: Path) -> dict[str, Any]:
    payload = _load_json(path, "permanent-template creation receipt")
    if payload.get("schema_version") != PLAN_SCHEMA_VERSION or payload.get("operation") not in {
        CREATE_RECEIPT_OPERATION,
        UPDATE_RECEIPT_OPERATION,
    }:
        raise UsageError("artifact is not a permanent-template creation or update receipt")
    supplied_hash = _text(payload.get("receipt_sha256"))
    if not supplied_hash or finalize_receipt(payload).get("receipt_sha256") != supplied_hash:
        raise UsageError("permanent-template creation receipt hash is invalid or modified")
    return payload


@contextmanager
def permanent_template_lock(template_name: str) -> Iterator[Path]:
    key = hashlib.sha256(template_name.casefold().encode("utf-8")).hexdigest()[:20]
    lock_path = Path(tempfile.gettempdir()) / f"codex-template-create-{key}.lock"
    try:
        descriptor = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise UsageError(f"another permanent-template operation is active for {template_name}: {lock_path}") from exc
    try:
        os.write(descriptor, f"pid={os.getpid()}\n".encode("ascii"))
        os.close(descriptor)
        yield lock_path
    finally:
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass


def sha256_json(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _diagnostic(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


def _load_json(path: Path, label: str) -> dict[str, Any]:
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise UsageError(f"{label} file does not exist: {resolved}")
    try:
        payload = json.loads(resolved.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise UsageError(f"{label} is not valid UTF-8 JSON: {resolved}") from exc
    if not isinstance(payload, dict):
        raise UsageError(f"{label} root must be an object")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")


def _text(value: Any) -> str:
    return str(value or "").strip()


def _text_raw(value: Any) -> str:
    return "" if value is None else str(value)


def _int_value(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _int_or_text(value: Any) -> int | str:
    parsed = _int_value(value)
    return parsed if parsed is not None else _text(value)
