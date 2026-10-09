"""Assemble the Shen Excel layout from finance facts and a verified stat lookup.

Does not execute SQL. Input CSVs are operator template downloads (backslash
escaped); the output is standard CSV. Unknown attribution codes remain blank.
"""
from __future__ import annotations

import argparse
import json
from decimal import Decimal
from pathlib import Path

import pandas as pd


KEYS = ["order_number", "trade_timestamp", "performance_employee_id"]
MONEY = ["income_yuan", "refund_yuan", "gross_profit_yuan"]


def read_download(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False, escapechar="\\").replace(
        {"NULL": "", "null": "", "\\N": ""}
    )


def assemble(finance: Path, lookup: Path, output: Path, qa_path: Path) -> dict:
    template = Path(__file__).resolve().parents[1] / "knowledge/sql_patterns/qingcheng_monthly_cashflow_columns.json"
    columns = [item["name"] for item in json.loads(template.read_text(encoding="utf-8"))["columns"]]
    facts, labels = read_download(finance), read_download(lookup)
    expected = [column for column in columns if column != "stat_judge_type"]
    if list(facts.columns) != expected:
        raise ValueError("Finance columns/order differ from the 27-column extraction contract")
    if not set(KEYS + ["stat_judge_type"]).issubset(labels.columns):
        raise ValueError("Lookup is missing key/stat columns")
    for frame in (facts, labels):
        frame["trade_timestamp"] = frame["trade_timestamp"].str[:19]
    facts["order_timestamp"] = facts["order_timestamp"].str[:19]
    # The reference Excel renders an absent course ID as text 0; no department
    # or course name is inferred for these non-course products.
    absent_courses = int(facts["course_number"].eq("").sum())
    facts["course_number"] = facts["course_number"].replace({"": "0"})
    grouped = labels.groupby(KEYS, dropna=False)["stat_judge_type"].agg(lambda values: sorted(set(values)))
    if grouped.map(len).gt(1).any():
        raise ValueError("Conflicting stat_judge_type values for a lookup key; refusing a multiplying join")
    unique = grouped.map(lambda values: values[0]).reset_index()
    result = facts.merge(unique, on=KEYS, how="left", validate="many_to_one", sort=False)
    result["stat_judge_type"] = result["stat_judge_type"].fillna("")
    assert len(result) == len(facts)
    for column in MONEY:
        result[column] = result[column].map(lambda value: str(Decimal(value).quantize(Decimal(".01"))))
    for income, refund, net in result[MONEY].itertuples(index=False, name=None):
        if Decimal(income) - Decimal(refund) != Decimal(net):
            raise ValueError("Net cash does not equal income minus refund")
        if Decimal(income) == 0 and Decimal(refund) == 0:
            raise ValueError("Unexpected both-zero cashflow row")
    result = result[columns].sort_values(["trade_timestamp", "order_number", "performance_employee_id"], kind="stable")
    unmatched = result[result["stat_judge_type"].eq("")]
    qa = {
        "row_count": len(result), "column_count": len(columns),
        "totals": {column: str(sum(map(Decimal, result[column]), Decimal(0))) for column in MONEY},
        "stat_lookup_rows": len(labels), "stat_lookup_unique_keys": len(unique),
        "stat_matched_rows": len(result) - len(unmatched), "stat_unmatched_rows": len(unmatched),
        "stat_unmatched_by_course_department": unmatched.groupby("course_second_level_department_name").size().to_dict(),
        "course_number_null_rendered_zero": absent_courses,
        "course_name_missing_rows": int(result.course_name.eq("").sum()),
        "net_identity_passed": True, "join_preserved_finance_rows": True,
        "trade_min": result.trade_timestamp.min() if len(result) else None,
        "trade_max": result.trade_timestamp.max() if len(result) else None,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output, index=False, encoding="utf-8-sig")
    qa_path.parent.mkdir(parents=True, exist_ok=True)
    qa_path.write_text(json.dumps(qa, ensure_ascii=False, indent=2), encoding="utf-8")
    return qa


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--finance", type=Path, required=True)
    parser.add_argument("--lookup", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--qa", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(assemble(args.finance, args.lookup, args.output, args.qa), ensure_ascii=False, indent=2))
