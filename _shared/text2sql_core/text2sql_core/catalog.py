"""Load and search deterministic physical and domain catalogs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


@dataclass(frozen=True)
class CatalogBundle:
    domain_manifest: dict[str, Any]
    physical_catalog: dict[str, Any]

    @classmethod
    def load(cls, skill_root: Path, core_root: Path) -> "CatalogBundle":
        return cls(
            domain_manifest=read_json(skill_root / "semantic" / "domain_manifest.json"),
            physical_catalog=read_json(core_root / "catalog" / "physical_catalog.json"),
        )

    @property
    def domain(self) -> str:
        return str(self.domain_manifest["domain"]["id"])

    def known_tables(self) -> set[str]:
        shared = {str(item["name"]).lower() for item in self.physical_catalog.get("tables", [])}
        domain: set[str] = set()
        for category in ("tables", "temp_tables"):
            for item in self.domain_manifest.get("entities", {}).get(category, []):
                table_name = item.get("table_name")
                if table_name:
                    domain.add(str(table_name).lower())
        return shared | domain

    def table_record(self, name: str) -> dict[str, Any] | None:
        lowered = name.lower()
        for item in self.physical_catalog.get("tables", []):
            if str(item.get("name", "")).lower() == lowered:
                return item
        for category in ("tables", "temp_tables"):
            for item in self.domain_manifest.get("entities", {}).get(category, []):
                if str(item.get("table_name", "")).lower() == lowered:
                    return item
        return None

    def search(self, query: str, kind: str = "all", limit: int = 20) -> list[dict[str, Any]]:
        terms = [term.lower() for term in query.split() if term.strip()]
        candidates: list[dict[str, Any]] = []
        entities = self.domain_manifest.get("entities", {})
        categories = sorted(entities) if kind == "all" else [kind]
        for category in categories:
            for item in entities.get(category, []):
                haystack = " ".join(
                    str(value)
                    for value in (
                        item.get("id", ""),
                        item.get("title", ""),
                        item.get("source_path", ""),
                        " ".join(item.get("aliases", [])),
                        " ".join(item.get("table_refs", [])),
                    )
                ).lower()
                if terms and not all(term in haystack for term in terms):
                    continue
                score = sum(haystack.count(term) for term in terms) if terms else 0
                candidates.append(
                    {
                        "score": score,
                        "category": category,
                        "id": item["id"],
                        "title": item.get("title"),
                        "source_path": item["source_path"],
                        "table_refs": item.get("table_refs", []),
                    }
                )
        candidates.sort(key=lambda row: (-row["score"], row["category"], row["source_path"]))
        return candidates[:limit]

    def validate_query_spec(self, spec: Any) -> list[Any]:
        from .models import Diagnostic

        diagnostics = list(spec.validate(expected_domain=self.domain))
        inventory = {
            str(item["source_path"]): item
            for item in self.domain_manifest.get("source_inventory", [])
        }
        entity_by_source = {
            str(item["source_path"]): item
            for items in self.domain_manifest.get("entities", {}).values()
            for item in items
        }
        paths: list[tuple[str, str]] = []
        for index, metric in enumerate(spec.metrics):
            paths.append((f"metrics[{index}].source_path", str(metric.get("source_path", ""))))
        for index, table in enumerate(spec.candidate_tables):
            source_path = str(table.get("source_path", ""))
            paths.append((f"candidate_tables[{index}].source_path", source_path))
            entity = entity_by_source.get(source_path, {})
            documented_name = str(entity.get("table_name", "")).lower()
            requested_name = str(table.get("name", "")).lower()
            if documented_name and documented_name != requested_name:
                diagnostics.append(
                    Diagnostic(
                        "SPEC_TABLE_SOURCE_MISMATCH",
                        "error",
                        f"{requested_name} does not match table documented by {source_path}",
                        path=f"candidate_tables[{index}]",
                        table=requested_name,
                    )
                )
        for index, join in enumerate(spec.join_path):
            paths.append((f"join_path[{index}].source_path", str(join.get("source_path", ""))))
        for index, evidence in enumerate(spec.evidence):
            source_path = str(evidence.get("source_path", "")).replace("\\", "/")
            local_prefix = f"{self.domain_manifest['domain']['skill']}/"
            if source_path.startswith(local_prefix):
                source_path = source_path[len(local_prefix) :]
            if source_path == "semantic/domain_manifest.json" or source_path.startswith(
                "_shared/text2sql_core/catalog/"
            ):
                continue
            paths.append((f"evidence[{index}].source_path", source_path))
        for field_path, source_path in paths:
            if source_path and source_path not in inventory:
                diagnostics.append(
                    Diagnostic(
                        "SPEC_EVIDENCE_NOT_IN_DOMAIN_CATALOG",
                        "error",
                        f"{source_path} is not retained evidence for {self.domain}",
                        path=field_path,
                    )
                )
        return diagnostics
