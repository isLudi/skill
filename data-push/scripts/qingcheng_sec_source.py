"""SEC report source preparation with explicit scope and integrity checks."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from types import SimpleNamespace


def latest_verified_snapshot(period, cfg, *, latest_audit, fetch_records, retry_transport, shared_snapshot):
    """Bind the complete period snapshot to one finished process writer."""
    audit = latest_audit(period, cfg["upstream_binding"])
    source = cfg["source"]
    fields = ("期次", "分区日期", "分区小时", "一级渠道", "渠道", "记录键")
    source_filter = {"logic": "and", "conditions": [["期次", "==", period]]}

    def validate_snapshot(rows, base):
        keys = {row["记录键"] for row in rows}
        snapshots = {(str(row["分区日期"]), int(row["分区小时"])) for row in rows}
        expected = audit["snapshot"]
        if (type(base.get("rev")) is not int or not rows
                or len(rows) != audit["period_row_count"] or len(keys) != len(rows)
                or any(not isinstance(key, str) or not key.strip() for key in keys)
                or {row["期次"] for row in rows} != {period}
                or snapshots != {(str(expected[0]), int(expected[1]))}
                or Counter(row["渠道"] for row in rows) != audit["raw_channel_counts"]):
            raise ValueError("SEC current-period Base does not match the completed writer audit")

    def load_snapshot():
        base = {}
        rows = retry_transport(lambda: fetch_records(
            {"base_token": source["base_token"], "table_id": source["table_id"]},
            SimpleNamespace(base_as="user", timeout=120, max_pages=50), fields,
            filter_json=source_filter, temp_prefix="qingcheng-sec-period-", audit=base,
        ))
        validate_snapshot(rows, base)
        return rows, base

    rows, base = shared_snapshot(
        {"domain": "qingcheng", "kind": "sec-period", "base_token": source["base_token"],
         "table_id": source["table_id"], "identity": "user", "fields": fields, "filter": source_filter},
        {"producer": audit, "binding": cfg["upstream_binding"]}, load_snapshot)
    validate_snapshot(rows, base)
    primary_counts = {}
    for row in rows:
        primary_counts.setdefault(row["一级渠道"], Counter())[row["渠道"]] += 1
    return {**audit, "base_revision": base["rev"], "base_pages": base["pages"],
            "primary_secondary_counts": {primary: dict(counts) for primary, counts in primary_counts.items()}}


def prepare_source_rows(source: str, period: str, slot_dir: Path, audit: dict, cfg: dict, *,
                        fetch, read_snapshot, write_json) -> tuple[list[dict], dict]:
    path = slot_dir / source / "source.ndjson"
    match = cfg["source"]["sources"][source]["match"]
    options = ({"secondary_channel": match["渠道"]}
               if source == "sec_order_reuse" and match.get("渠道") else {})
    excluded = cfg["source"]["sources"][source].get("excluded_secondary_channels", [])
    if excluded:
        options["excluded_secondary_channels"] = tuple(excluded)
    fetch(source, period, path, **options)
    # Upstream counts cover every department within the channel. Verify that
    # complete slice before selecting the report's configured department.
    channel_match = {key: value for key, value in match.items() if key != "部门"}
    rows, manifest = read_snapshot(path, {"source": {"match": channel_match}})
    if manifest["rev"] != audit["base_revision"]:
        raise ValueError(f"SEC {source} Base revision differs from the complete period snapshot")
    counts = Counter(row["渠道"] for row in rows)
    if any(name in counts for name in excluded):
        raise ValueError("SEC report source contains an excluded secondary channel")
    expected_scope = None
    if "primary_secondary_counts" in audit:
        expected_scope = {name: count for name, count in audit["primary_secondary_counts"].get(match["一级渠道"], {}).items()
                          if name not in excluded and (not match.get("渠道") or name == match["渠道"])}
        if counts != expected_scope:
            raise ValueError("SEC source counts differ from the verified primary/secondary scope")
    names = ((match["渠道"],) if match.get("渠道") else tuple(counts))
    if any(name not in audit["raw_channel_counts"] for name in names):
        raise ValueError(f"SEC {source} source contains a channel missing from the upstream audit")
    expected = sum(expected_scope.values()) if expected_scope is not None else sum(audit["raw_channel_counts"][name] for name in names)
    if manifest["records_count"] != expected or manifest["period"] != period:
        raise ValueError(f"SEC {source} source count or period differs from upstream audit")
    if (str(manifest["snapshot"][0]), int(manifest["snapshot"][1])) != (
            str(audit["snapshot"][0]), int(audit["snapshot"][1])):
        raise ValueError(f"SEC {source} source snapshot differs from upstream audit")
    if source == "sec_order_reuse":
        for name in names:
            verified_count = expected_scope[name] if expected_scope is not None else audit["raw_channel_counts"][name]
            if counts[name] != verified_count:
                raise ValueError(f"SEC {name} raw source count differs from upstream audit")
    if match.get("部门") and any(not isinstance(row.get("部门"), str) or not row["部门"].strip() for row in rows):
        raise ValueError("SEC source contains a missing department")
    department = match.get("部门")
    selected = [row for row in rows if department is None or row["部门"] == department]
    excluded_departments = Counter(row["部门"] for row in rows if department is not None and row["部门"] != department)
    scope_audit = {
        "department": department, "source_match": match, "excluded_secondary_channels": excluded, "raw_records_count": len(rows),
        "selected_records_count": len(selected), "excluded_records_count": sum(excluded_departments.values()),
        "excluded_department_counts": dict(sorted(excluded_departments.items())),
        "raw_channel_counts": dict(sorted(Counter(row["渠道"] for row in rows).items())),
        "selected_channel_counts": dict(sorted(Counter(row["渠道"] for row in selected).items())),
        "period": period, "source_rev": manifest["rev"], "snapshot": manifest["snapshot"],
    }
    write_json(path.with_name("scope_audit.json"), scope_audit)
    # Keep records_count tied to source.ndjson; selected rows have their own
    # explicit count rather than changing the raw export's manifest.
    return selected, {**manifest, "scope_audit": scope_audit,
                      "upstream_execution_id": audit.get("execution_id"),
                      "upstream_completed_at": audit.get("completed_at")}
