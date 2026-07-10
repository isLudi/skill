"""Domain-local semantic contracts and deterministic alias resolution."""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import sqlglot

from .models import Diagnostic


CONTRACT_SCHEMA_VERSION = "2.0.0"
CONTRACT_FILES = {
    "metric": "metric_contracts.json",
    "dimension": "dimension_contracts.json",
    "join": "join_contracts.json",
    "scope": "scope_contracts.json",
}
ALLOWED_STATUSES = {"confirmed", "pending_confirmation"}
IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
TABLE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*$")
DIMENSION_CUE_TEMPLATES = (
    "按{alias}",
    "每{alias}",
    "分{alias}",
    "{alias}维度",
    "{alias}分组",
    "{alias}拆分",
    "by {alias}",
    "group by {alias}",
)
QUERY_PREFIXES = ("请帮我", "帮我", "查询", "查看", "统计", "看一下", "看")


def _normalize_alias(value: str) -> str:
    return " ".join(value.casefold().strip().split())


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _query_content(value: str) -> str:
    """Return a short intent phrase for conservative prefix ambiguity checks."""

    content = value
    changed = True
    while changed:
        changed = False
        for prefix in QUERY_PREFIXES:
            if content.startswith(prefix) and len(content) > len(prefix):
                content = content[len(prefix) :].strip()
                changed = True
                break
    return content


def _dimension_is_requested(query: str, alias: str) -> bool:
    """Avoid treating a department label such as 市场顾问 as a group-by request."""

    return (
        query == alias
        or _query_content(query) == alias
        or any(template.format(alias=alias) in query for template in DIMENSION_CUE_TEMPLATES)
    )


@dataclass(frozen=True)
class ResolutionResult:
    domain: str
    query: str
    kind: str | None
    status: str
    candidates: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "query": self.query,
            "kind": self.kind,
            "status": self.status,
            "candidates": self.candidates,
        }


class ContractRegistry:
    """Load semantic overlays from exactly one domain skill."""

    def __init__(
        self,
        *,
        skill_root: Path,
        domain: str,
        contracts: dict[str, list[dict[str, Any]]],
        diagnostics: list[Diagnostic],
    ) -> None:
        self.skill_root = skill_root.resolve()
        self.domain = domain
        self.contracts = contracts
        self.diagnostics = diagnostics
        self._by_id = {
            str(item["id"]): item
            for values in contracts.values()
            for item in values
            if item.get("id")
        }
        self._alias_index: dict[str, set[str]] = defaultdict(set)
        for contract_id, item in self._by_id.items():
            values = [contract_id, str(item.get("name", "")), *item.get("aliases", [])]
            for extra in (item.get("field"), item.get("output_alias")):
                if extra:
                    values.append(str(extra))
            for alias in values:
                normalized = _normalize_alias(str(alias))
                if normalized:
                    self._alias_index[normalized].add(contract_id)

    @classmethod
    def load(cls, skill_root: Path, domain: str) -> "ContractRegistry":
        root = skill_root.resolve()
        contract_root = root / "semantic" / "contracts"
        diagnostics: list[Diagnostic] = []
        contracts: dict[str, list[dict[str, Any]]] = {}
        seen_ids: set[str] = set()
        for kind, filename in CONTRACT_FILES.items():
            path = contract_root / filename
            if not path.is_file():
                diagnostics.append(
                    Diagnostic(
                        "CONTRACT_FILE_MISSING",
                        "error",
                        f"missing {path.relative_to(root).as_posix()}",
                        path=path.relative_to(root).as_posix(),
                    )
                )
                contracts[kind] = []
                continue
            try:
                envelope = json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:  # noqa: BLE001
                diagnostics.append(Diagnostic("CONTRACT_JSON_INVALID", "error", f"{path}: {exc}"))
                contracts[kind] = []
                continue
            if envelope.get("schema_version") != CONTRACT_SCHEMA_VERSION:
                diagnostics.append(
                    Diagnostic(
                        "CONTRACT_SCHEMA_VERSION",
                        "error",
                        f"{filename} must use schema_version {CONTRACT_SCHEMA_VERSION}",
                    )
                )
            if envelope.get("domain") != domain:
                diagnostics.append(
                    Diagnostic(
                        "CONTRACT_DOMAIN_MISMATCH",
                        "error",
                        f"{filename} domain {envelope.get('domain')!r} does not match {domain!r}",
                    )
                )
            values = envelope.get("contracts")
            if not isinstance(values, list):
                diagnostics.append(Diagnostic("CONTRACT_LIST_REQUIRED", "error", f"{filename} contracts must be a list"))
                contracts[kind] = []
                continue
            normalized_values: list[dict[str, Any]] = []
            for index, raw in enumerate(values):
                if not isinstance(raw, dict):
                    diagnostics.append(
                        Diagnostic("CONTRACT_OBJECT_REQUIRED", "error", f"{filename}[{index}] must be an object")
                    )
                    continue
                item = dict(raw)
                item["kind"] = kind
                diagnostics.extend(cls._validate_contract(root, domain, kind, item, index, filename))
                contract_id = str(item.get("id", ""))
                if contract_id in seen_ids:
                    diagnostics.append(Diagnostic("CONTRACT_ID_DUPLICATE", "error", f"duplicate contract id {contract_id}"))
                seen_ids.add(contract_id)
                normalized_values.append(item)
            contracts[kind] = normalized_values
        by_id = {
            str(item.get("id")): item
            for values in contracts.values()
            for item in values
            if item.get("id")
        }
        for metric in contracts.get("metric", []):
            if metric.get("status") != "confirmed":
                continue
            allowed_dimensions = metric.get("allowed_dimensions")
            if not isinstance(allowed_dimensions, list):
                diagnostics.append(
                    Diagnostic(
                        "METRIC_ALLOWED_DIMENSIONS_INVALID",
                        "error",
                        f"{metric.get('id')} allowed_dimensions must be a list",
                    )
                )
                continue
            for dimension_id in allowed_dimensions:
                dimension = by_id.get(str(dimension_id))
                if dimension is None or dimension.get("kind") != "dimension":
                    diagnostics.append(
                        Diagnostic(
                            "METRIC_DIMENSION_REFERENCE_UNKNOWN",
                            "error",
                            f"{metric.get('id')} references unknown dimension {dimension_id}",
                        )
                    )
        return cls(skill_root=root, domain=domain, contracts=contracts, diagnostics=diagnostics)

    @staticmethod
    def _validate_contract(
        root: Path,
        domain: str,
        kind: str,
        item: dict[str, Any],
        index: int,
        filename: str,
    ) -> list[Diagnostic]:
        diagnostics: list[Diagnostic] = []
        label = f"{filename}[{index}]"
        required = ("id", "name", "aliases", "status", "source_path", "source_sha256")
        for key in required:
            if key not in item:
                diagnostics.append(Diagnostic("CONTRACT_FIELD_REQUIRED", "error", f"{label} missing {key}"))
        contract_id = str(item.get("id", ""))
        if not contract_id.startswith(f"{domain}:{kind}:"):
            diagnostics.append(
                Diagnostic(
                    "CONTRACT_ID_NAMESPACE",
                    "error",
                    f"{label} id must start with {domain}:{kind}:",
                )
            )
        if item.get("status") not in ALLOWED_STATUSES:
            diagnostics.append(
                Diagnostic(
                    "CONTRACT_STATUS_INVALID",
                    "error",
                    f"{label} status must be confirmed or pending_confirmation",
                )
            )
        aliases = item.get("aliases")
        if not isinstance(aliases, list) or not all(isinstance(alias, str) and alias.strip() for alias in aliases):
            diagnostics.append(Diagnostic("CONTRACT_ALIASES_INVALID", "error", f"{label} aliases must be strings"))
        source_path = str(item.get("source_path", "")).replace("\\", "/")
        target = (root / source_path).resolve()
        if not source_path or not target.is_relative_to(root) or not target.is_file():
            diagnostics.append(
                Diagnostic("CONTRACT_SOURCE_MISSING", "error", f"{label} source does not exist: {source_path}")
            )
        elif item.get("source_sha256") != _sha256(target):
            diagnostics.append(
                Diagnostic("CONTRACT_SOURCE_HASH_STALE", "error", f"{label} source hash is stale: {source_path}")
            )
        if item.get("status") == "confirmed":
            if kind == "metric":
                for key in (
                    "sql_expression",
                    "output_alias",
                    "aggregation",
                    "candidate_tables",
                    "calculation_grain",
                    "allowed_dimensions",
                    "required_scope_fields",
                    "automatic_compile",
                ):
                    if key not in item:
                        diagnostics.append(Diagnostic("CONTRACT_FIELD_REQUIRED", "error", f"{label} missing {key}"))
                expression = str(item.get("sql_expression", ""))
                if "{base}" not in expression:
                    diagnostics.append(
                        Diagnostic("METRIC_BASE_ALIAS_REQUIRED", "error", f"{label} sql_expression must use {{base}}")
                    )
                else:
                    try:
                        sqlglot.parse_one(expression.replace("{base}", "t"), read="presto")
                    except sqlglot.errors.ParseError as exc:
                        diagnostics.append(Diagnostic("METRIC_EXPRESSION_INVALID", "error", f"{label}: {exc}"))
                if not IDENTIFIER_RE.fullmatch(str(item.get("output_alias", ""))):
                    diagnostics.append(Diagnostic("METRIC_ALIAS_INVALID", "error", f"{label} output_alias is invalid"))
                if not isinstance(item.get("automatic_compile"), bool):
                    diagnostics.append(
                        Diagnostic("METRIC_COMPILE_FLAG_INVALID", "error", f"{label} automatic_compile must be boolean")
                    )
                tables = item.get("candidate_tables", [])
                if not isinstance(tables, list) or not tables or not all(TABLE_RE.fullmatch(str(table)) for table in tables):
                    diagnostics.append(Diagnostic("METRIC_TABLES_INVALID", "error", f"{label} candidate_tables invalid"))
            elif kind == "dimension":
                if not IDENTIFIER_RE.fullmatch(str(item.get("field", ""))):
                    diagnostics.append(Diagnostic("DIMENSION_FIELD_INVALID", "error", f"{label} field is invalid"))
                if not TABLE_RE.fullmatch(str(item.get("table", ""))):
                    diagnostics.append(Diagnostic("DIMENSION_TABLE_INVALID", "error", f"{label} table is invalid"))
                if "automatic_compile" in item and not isinstance(item.get("automatic_compile"), bool):
                    diagnostics.append(
                        Diagnostic("DIMENSION_COMPILE_FLAG_INVALID", "error", f"{label} automatic_compile must be boolean")
                    )
                expression = item.get("sql_expression")
                if expression is not None:
                    expression_text = str(expression)
                    if "{base}" not in expression_text:
                        diagnostics.append(
                            Diagnostic(
                                "DIMENSION_BASE_ALIAS_REQUIRED",
                                "error",
                                f"{label} sql_expression must use {{base}}",
                            )
                        )
                    else:
                        try:
                            sqlglot.parse_one(expression_text.replace("{base}", "t"), read="presto")
                        except sqlglot.errors.ParseError as exc:
                            diagnostics.append(
                                Diagnostic("DIMENSION_EXPRESSION_INVALID", "error", f"{label}: {exc}")
                            )
            elif kind == "join":
                for key in ("left_table", "right_table", "cardinality"):
                    if not item.get(key):
                        diagnostics.append(Diagnostic("CONTRACT_FIELD_REQUIRED", "error", f"{label} missing {key}"))
                for key in ("left_table", "right_table"):
                    if item.get(key) and not TABLE_RE.fullmatch(str(item[key])):
                        diagnostics.append(
                            Diagnostic("JOIN_TABLE_INVALID", "error", f"{label} {key} is not a qualified table")
                        )
                key_pairs = item.get("key_pairs") or item.get("keys")
                if not isinstance(key_pairs, list) or not key_pairs:
                    diagnostics.append(
                        Diagnostic("JOIN_KEYS_REQUIRED", "error", f"{label} requires non-empty key_pairs or keys")
                    )
                else:
                    for pair_index, pair in enumerate(key_pairs):
                        left = pair.get("left_field", pair.get("left")) if isinstance(pair, dict) else None
                        right = pair.get("right_field", pair.get("right")) if isinstance(pair, dict) else None
                        if not IDENTIFIER_RE.fullmatch(str(left or "")) or not IDENTIFIER_RE.fullmatch(str(right or "")):
                            diagnostics.append(
                                Diagnostic(
                                    "JOIN_KEY_PAIR_INVALID",
                                    "error",
                                    f"{label} key pair {pair_index} requires safe left/right fields",
                                )
                            )
            elif kind == "scope":
                if not isinstance(item.get("filters"), list) or not item.get("filters"):
                    diagnostics.append(Diagnostic("SCOPE_FILTERS_REQUIRED", "error", f"{label} filters are required"))
        return diagnostics

    @property
    def ok(self) -> bool:
        return not any(item.severity == "error" for item in self.diagnostics)

    def by_id(self, contract_id: str) -> dict[str, Any] | None:
        return self._by_id.get(contract_id)

    def values(self, kind: str | None = None) -> list[dict[str, Any]]:
        if kind is not None:
            return list(self.contracts.get(kind, []))
        return [item for values in self.contracts.values() for item in values]

    def resolve_identifier(self, kind: str, value: str) -> dict[str, Any] | None:
        if value in self._by_id and self._by_id[value].get("kind") == kind:
            return self._by_id[value]
        normalized = _normalize_alias(value)
        ids = {
            contract_id
            for contract_id in self._alias_index.get(normalized, set())
            if self._by_id[contract_id].get("kind") == kind
        }
        if len(ids) == 1:
            return self._by_id[next(iter(ids))]
        return None

    def resolve(self, query: str, kind: str | None = None) -> ResolutionResult:
        normalized_query = _normalize_alias(query)
        query_content = _query_content(normalized_query)
        scores: dict[str, int] = defaultdict(int)
        matched_aliases: dict[str, set[str]] = defaultdict(set)
        for alias, contract_ids in self._alias_index.items():
            if len(alias) < 2:
                continue
            if alias == normalized_query:
                score = 10_000 + len(alias)
            elif alias in normalized_query:
                score = len(alias)
            elif len(query_content) >= 4 and alias.startswith(query_content):
                # A short metric-family phrase such as 当期转化 intentionally
                # returns all equally specific metric contracts for disambiguation.
                score = len(query_content)
            else:
                continue
            for contract_id in contract_ids:
                contract = self._by_id[contract_id]
                if kind and contract.get("kind") != kind:
                    continue
                if contract.get("kind") == "dimension" and not _dimension_is_requested(normalized_query, alias):
                    continue
                if alias.startswith(query_content) and alias not in normalized_query and contract.get("kind") != "metric":
                    continue
                scores[contract_id] = max(scores[contract_id], score)
                matched_aliases[contract_id].add(alias)
        if not scores:
            return ResolutionResult(self.domain, query, kind, "unknown", [])
        by_kind: dict[str, dict[str, int]] = defaultdict(dict)
        for contract_id, score in scores.items():
            contract_kind = str(self._by_id[contract_id].get("kind"))
            by_kind[contract_kind][contract_id] = score
        selected_ids: list[str] = []
        ambiguous = False
        for contract_kind in sorted(by_kind):
            kind_scores = by_kind[contract_kind]
            top_score = max(kind_scores.values())
            top_ids = sorted(contract_id for contract_id, score in kind_scores.items() if score == top_score)
            selected_ids.extend(top_ids)
            ambiguous = ambiguous or len(top_ids) > 1
        status = "ambiguous" if ambiguous else "resolved"
        candidates = [
            {
                "id": contract_id,
                "kind": self._by_id[contract_id]["kind"],
                "name": self._by_id[contract_id].get("name"),
                "status": self._by_id[contract_id].get("status"),
                "source_path": self._by_id[contract_id].get("source_path"),
                "score": scores[contract_id],
                "matched_aliases": sorted(matched_aliases[contract_id]),
            }
            for contract_id in sorted(selected_ids)
        ]
        return ResolutionResult(self.domain, query, kind, status, candidates)

    def generated_index(self) -> dict[str, Any]:
        entries = [
            {
                key: value
                for key, value in {
                    "id": item["id"],
                    "kind": item["kind"],
                    "name": item.get("name"),
                    "aliases": item.get("aliases", []),
                    "status": item.get("status"),
                    "source_path": item.get("source_path"),
                    "source_sha256": item.get("source_sha256"),
                    "automatic_compile": (
                        item.get("automatic_compile")
                        if item.get("kind") in {"metric", "dimension"}
                        else None
                    ),
                }.items()
                if value is not None
            }
            for item in sorted(self.values(), key=lambda value: str(value.get("id", "")))
        ]
        collisions = {
            alias: sorted(ids)
            for alias, ids in sorted(self._alias_index.items())
            if len(ids) > 1
        }
        return {
            "schema_version": CONTRACT_SCHEMA_VERSION,
            "domain": self.domain,
            "counts": {
                kind: len(values)
                for kind, values in sorted(self.contracts.items())
            },
            "entries": entries,
            "alias_collisions": collisions,
        }
