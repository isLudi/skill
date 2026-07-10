"""Typed contracts used before and after SQL generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable


SUPPORTED_DOMAINS = {"market_consultant", "qingcheng"}
DOMAIN_SKILLS = {
    "market_consultant": "sql-query-writer-for-dashboard",
    "qingcheng": "qingcheng-dashboard-sql",
}


@dataclass(frozen=True)
class Diagnostic:
    code: str
    severity: str
    message: str
    path: str | None = None
    table: str | None = None
    field: str | None = None
    compat_blocking: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            key: value
            for key, value in {
                "code": self.code,
                "severity": self.severity,
                "message": self.message,
                "path": self.path,
                "table": self.table,
                "field": self.field,
                "compat_blocking": self.compat_blocking,
            }.items()
            if value is not None
        }


@dataclass
class ValidationResult:
    diagnostics: list[Diagnostic] = field(default_factory=list)
    tables: list[str] = field(default_factory=list)
    ctes: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(item.severity == "error" for item in self.diagnostics)

    def extend(self, diagnostics: Iterable[Diagnostic]) -> None:
        self.diagnostics.extend(diagnostics)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "tables": self.tables,
            "ctes": self.ctes,
            "diagnostics": [item.to_dict() for item in self.diagnostics],
        }


@dataclass
class QuerySpec:
    domain: str
    intent: str
    metrics: list[dict[str, Any]] = field(default_factory=list)
    dimensions: list[str] = field(default_factory=list)
    filters: list[dict[str, Any]] = field(default_factory=list)
    time_range: dict[str, Any] | None = None
    calculation_grain: list[str] = field(default_factory=list)
    output_grain: list[str] = field(default_factory=list)
    candidate_tables: list[dict[str, Any]] = field(default_factory=list)
    join_path: list[dict[str, Any]] = field(default_factory=list)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    unresolved_slots: list[str] = field(default_factory=list)
    schema_version: str = "2.0.0"
    spec_id: str | None = None
    business_scope: list[dict[str, Any]] = field(default_factory=list)
    scopes: list[str] = field(default_factory=list)
    execution_mode: str = "production"

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "QuerySpec":
        known = {
            "domain",
            "intent",
            "metrics",
            "dimensions",
            "filters",
            "time_range",
            "calculation_grain",
            "output_grain",
            "candidate_tables",
            "join_path",
            "evidence",
            "unresolved_slots",
            "schema_version",
            "spec_id",
            "business_scope",
            "scopes",
            "execution_mode",
        }
        unknown = sorted(set(value) - known)
        if unknown:
            raise ValueError(f"Unknown QuerySpec fields: {', '.join(unknown)}")
        return cls(**{key: value.get(key) for key in known if key in value})

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "intent": self.intent,
            "metrics": self.metrics,
            "dimensions": self.dimensions,
            "filters": self.filters,
            "time_range": self.time_range,
            "calculation_grain": self.calculation_grain,
            "output_grain": self.output_grain,
            "candidate_tables": self.candidate_tables,
            "join_path": self.join_path,
            "evidence": self.evidence,
            "unresolved_slots": self.unresolved_slots,
            "schema_version": self.schema_version,
            "spec_id": self.spec_id,
            "business_scope": self.business_scope,
            "scopes": self.scopes,
            "execution_mode": self.execution_mode,
        }

    def validate(self, expected_domain: str | None = None) -> list[Diagnostic]:
        diagnostics: list[Diagnostic] = []
        if self.domain == "unresolved":
            diagnostics.append(
                Diagnostic(
                    "SPEC_DOMAIN_UNRESOLVED",
                    "error",
                    "domain must be resolved before SQL can be executable",
                    path="domain",
                )
            )
            return diagnostics
        if self.domain not in SUPPORTED_DOMAINS:
            diagnostics.append(
                Diagnostic(
                    "SPEC_DOMAIN_REQUIRED",
                    "error",
                    "domain must be unresolved, market_consultant, or qingcheng",
                    path="domain",
                )
            )
            return diagnostics
        if expected_domain and self.domain != expected_domain:
            diagnostics.append(
                Diagnostic(
                    "SPEC_DOMAIN_MISMATCH",
                    "error",
                    f"QuerySpec domain {self.domain!r} does not match {expected_domain!r}",
                    path="domain",
                )
            )
        if not self.intent.strip():
            diagnostics.append(Diagnostic("SPEC_INTENT_REQUIRED", "error", "intent is required", path="intent"))
        if self.execution_mode not in {"production", "exploratory"}:
            diagnostics.append(
                Diagnostic(
                    "SPEC_EXECUTION_MODE_INVALID",
                    "error",
                    "execution_mode must be production or exploratory",
                    path="execution_mode",
                )
            )
        expected_prefix = f"{self.domain}:"
        for index, metric in enumerate(self.metrics):
            metric_id = str(metric.get("id", ""))
            source_path = str(metric.get("source_path", ""))
            if not metric_id.startswith(expected_prefix):
                diagnostics.append(
                    Diagnostic(
                        "SPEC_METRIC_NOT_NAMESPACED",
                        "error",
                        f"metric id must start with {expected_prefix}",
                        path=f"metrics[{index}].id",
                    )
                )
            if not source_path.startswith("knowledge/metrics/"):
                diagnostics.append(
                    Diagnostic(
                        "SPEC_METRIC_EVIDENCE_REQUIRED",
                        "error",
                        "metric source_path must point to this domain's knowledge/metrics",
                        path=f"metrics[{index}].source_path",
                    )
                )
        for index, table in enumerate(self.candidate_tables):
            if not str(table.get("name", "")).strip():
                diagnostics.append(
                    Diagnostic(
                        "SPEC_TABLE_NAME_REQUIRED",
                        "error",
                        "candidate table name is required",
                        path=f"candidate_tables[{index}].name",
                    )
                )
            if not str(table.get("source_path", "")).startswith("knowledge/"):
                diagnostics.append(
                    Diagnostic(
                        "SPEC_TABLE_EVIDENCE_REQUIRED",
                        "error",
                        "candidate table must cite a domain knowledge document",
                        path=f"candidate_tables[{index}].source_path",
                    )
                )
        expected_skill = DOMAIN_SKILLS[self.domain]
        other_skill = next(skill for domain, skill in DOMAIN_SKILLS.items() if domain != self.domain)
        for index, evidence in enumerate(self.evidence):
            source_path = str(evidence.get("source_path", "")).replace("\\", "/")
            if not source_path:
                diagnostics.append(
                    Diagnostic(
                        "SPEC_EVIDENCE_PATH_REQUIRED",
                        "error",
                        "evidence source_path is required",
                        path=f"evidence[{index}].source_path",
                    )
                )
            if other_skill in source_path:
                diagnostics.append(
                    Diagnostic(
                        "SPEC_CROSS_DOMAIN_EVIDENCE",
                        "error",
                        f"evidence crosses from {expected_skill} into {other_skill}",
                        path=f"evidence[{index}].source_path",
                    )
                )
        metric_intent = bool(self.metrics) or self.intent in {
            "metric_query",
            "dashboard_query",
            "dashboard_repair",
            "cross_department_comparison",
        }
        if metric_intent and not self.time_range:
            diagnostics.append(
                Diagnostic("SPEC_TIME_RANGE_REQUIRED", "error", "metric SQL requires time_range", path="time_range")
            )
        if metric_intent and not self.calculation_grain:
            diagnostics.append(
                Diagnostic(
                    "SPEC_CALCULATION_GRAIN_REQUIRED",
                    "error",
                    "metric SQL requires calculation_grain",
                    path="calculation_grain",
                )
            )
        if metric_intent and not self.output_grain:
            diagnostics.append(
                Diagnostic(
                    "SPEC_OUTPUT_GRAIN_REQUIRED",
                    "error",
                    "metric SQL requires output_grain",
                    path="output_grain",
                )
            )
        if self.unresolved_slots:
            diagnostics.append(
                Diagnostic(
                    "SPEC_UNRESOLVED_SLOTS",
                    "error",
                    "unresolved slots block executable SQL: " + ", ".join(self.unresolved_slots),
                    path="unresolved_slots",
                )
            )
        return diagnostics

    @property
    def is_executable(self) -> bool:
        return not any(item.severity == "error" for item in self.validate())


@dataclass
class QueryPlan:
    plan_id: str
    domain: str
    intent: str
    status: str
    base_table: str | None
    metrics: list[dict[str, Any]] = field(default_factory=list)
    dimensions: list[dict[str, Any]] = field(default_factory=list)
    filters: list[dict[str, Any]] = field(default_factory=list)
    scopes: list[dict[str, Any]] = field(default_factory=list)
    joins: list[dict[str, Any]] = field(default_factory=list)
    calculation_grain: list[str] = field(default_factory=list)
    output_grain: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    lineage: list[dict[str, Any]] = field(default_factory=list)
    unresolved_slots: list[str] = field(default_factory=list)
    diagnostics: list[Diagnostic] = field(default_factory=list)
    execution_policy: dict[str, Any] = field(
        default_factory=lambda: {
            "allow_download": False,
            "max_direct_download_rows": 1000,
            "requires_preview": True,
        }
    )
    sql_sha256: str | None = None
    schema_version: str = "2.0.0"

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "QueryPlan":
        payload = dict(value)
        payload["diagnostics"] = [
            item if isinstance(item, Diagnostic) else Diagnostic(**item)
            for item in payload.get("diagnostics", [])
        ]
        return cls(**payload)

    @property
    def executable(self) -> bool:
        return self.status == "executable" and not self.unresolved_slots and not any(
            item.severity == "error" for item in self.diagnostics
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "plan_id": self.plan_id,
            "domain": self.domain,
            "intent": self.intent,
            "status": self.status,
            "base_table": self.base_table,
            "metrics": self.metrics,
            "dimensions": self.dimensions,
            "filters": self.filters,
            "scopes": self.scopes,
            "joins": self.joins,
            "calculation_grain": self.calculation_grain,
            "output_grain": self.output_grain,
            "evidence": self.evidence,
            "lineage": self.lineage,
            "unresolved_slots": self.unresolved_slots,
            "diagnostics": [item.to_dict() for item in self.diagnostics],
            "execution_policy": self.execution_policy,
            "sql_sha256": self.sql_sha256,
        }
