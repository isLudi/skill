"""Assemble recurring Qingcheng cashflow with the mandatory TT source check.

Does not execute SQL. Finance defaults to backslash-escaped template CSV;
TT defaults to standard CSV from the small-result download. The output is
standard CSV. Unknown attribution codes remain blank.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pandas as pd


KEYS = ["order_number", "trade_timestamp", "performance_employee_id"]
MONEY = ["income_yuan", "refund_yuan", "gross_profit_yuan"]
EVENT_KEYS = ["order_number", "trade_timestamp"]
TT_MISSING_COLUMNS = ["biz_type", "goods_type"]
TT_FIRST_DEPARTMENTS = {"TT业务线", "TT"}
TT_SECOND_DEPARTMENTS = {"V学部", "T学部", "TT小学学部"}
TEMPLATE = Path(__file__).resolve().parents[1] / "knowledge/sql_patterns/qingcheng_monthly_cashflow_columns.json"


def read_download(path: Path, dialect: str = "template") -> pd.DataFrame:
    if dialect not in {"template", "standard"}:
        raise ValueError("CSV dialect must be template or standard")
    return pd.read_csv(path, dtype=str, keep_default_na=False,
                       escapechar="\\" if dialect == "template" else None).replace(
        {"NULL": "", "null": "", "\\N": ""}
    )


def normalize_timestamps(frame: pd.DataFrame, columns: list[str]) -> None:
    def normalize(value: str) -> str:
        if not value:
            return ""
        stamp = pd.Timestamp(value)
        if pd.isna(stamp) or stamp.tzinfo is not None or stamp.microsecond or stamp.nanosecond:
            raise ValueError("Timestamp must be a valid timezone-free whole second; review source precision")
        return stamp.strftime("%Y-%m-%d %H:%M:%S")

    for column in columns:
        frame[column] = frame[column].map(normalize)


def normalize_facts(frame: pd.DataFrame, start_date: str, end_date: str) -> None:
    start, end = date.fromisoformat(start_date), date.fromisoformat(end_date)
    if end < start:
        raise ValueError("end_date must be on or after start_date")
    normalize_timestamps(frame, ["trade_timestamp", "order_timestamp"])
    trades = frame["trade_timestamp"]
    if not (trades.ge(start.isoformat()) & trades.lt((end + timedelta(days=1)).isoformat())).all():
        raise ValueError("Cashflow is outside the requested transaction period")
    if not frame["dt"].eq(trades.str[:10].str.replace("-", "", regex=False)).all():
        raise ValueError("Output dt must equal the transaction date, not snapshot dt")
    if frame["order_number"].eq("").any():
        raise ValueError("Missing order identifier")
    frame["course_number"] = frame["course_number"].replace({"": "0"})

    def money(value: str) -> str:
        number = Decimal(value)
        if not number.is_finite() or number != number.quantize(Decimal(".01")):
            raise ValueError("Cash amount must be finite and exact to cents")
        return str(number.quantize(Decimal(".01")))

    for column in MONEY:
        frame[column] = frame[column].map(money)
    for income, refund, net in frame[MONEY].itertuples(index=False, name=None):
        if Decimal(income) - Decimal(refund) != Decimal(net):
            raise ValueError("Net cash does not equal income minus refund")
        if Decimal(income) == 0 and Decimal(refund) == 0:
            raise ValueError("Unexpected both-zero cashflow row")


def merge_tt(facts: pd.DataFrame, tt: pd.DataFrame, columns: list[str]) -> tuple[pd.DataFrame, int]:
    common = [column for column in columns if column not in TT_MISSING_COLUMNS]
    if list(tt.columns) != common:
        raise ValueError("TT download must contain the 26 source-backed columns in template order")
    scope = (tt.course_first_level_department_name.isin(TT_FIRST_DEPARTMENTS)
             & tt.course_second_level_department_name.isin(TT_SECOND_DEPARTMENTS)
             & tt.performance_second_level_department_name.eq("青橙项目部"))
    if not scope.all():
        raise ValueError("TT supplement contains an unreviewed department or a non-Qingcheng attribution")
    # Compare whole event multisets, not just order IDs or one arbitrarily chosen
    # row. A changed split/amount/department is ambiguous and must not be appended.
    existing = {key: Counter(group[common].itertuples(index=False, name=None))
                for key, group in facts.groupby(EVENT_KEYS, dropna=False, sort=False)}
    additions, overlap_rows = [], 0
    for key, group in tt.groupby(EVENT_KEYS, dropna=False, sort=False):
        if key in existing:
            if Counter(group[common].itertuples(index=False, name=None)) != existing[key]:
                raise ValueError("Conflicting TT event: source grain, amounts or shared fields differ")
            overlap_rows += len(group)
        else:
            additions.append(group)
    extra = pd.concat(additions, ignore_index=True) if additions else tt.iloc[:0].copy()
    for column in TT_MISSING_COLUMNS:
        extra[column] = ""
    # Keep the base order and append TT rows: safe to compare an existing Sheet
    # against the output prefix before writing only the new suffix.
    return pd.concat([facts[columns], extra[columns]], ignore_index=True), overlap_rows


def assemble(finance: Path, lookup: Path, output: Path, qa_path: Path, *,
             tt_supplement: Path, start_date: str, end_date: str,
             tt_zero_verified: bool = False, finance_csv_dialect: str = "template",
             tt_csv_dialect: str = "standard") -> dict:
    columns = [item["name"] for item in json.loads(TEMPLATE.read_text(encoding="utf-8"))["columns"]]
    facts, labels = read_download(finance, finance_csv_dialect), read_download(lookup)
    expected = [column for column in columns if column != "stat_judge_type"]
    if list(facts.columns) != expected:
        raise ValueError("Finance columns/order differ from the 27-column extraction contract")
    if not set(KEYS + ["stat_judge_type"]).issubset(labels.columns):
        raise ValueError("Lookup is missing key/stat columns")
    normalize_timestamps(labels, ["trade_timestamp"])
    # The reference Excel renders an absent course ID as text 0; no department
    # or course name is inferred for these non-course products.
    absent_courses = int(facts["course_number"].eq("").sum())
    normalize_facts(facts, start_date, end_date)
    grouped = labels.groupby(KEYS, dropna=False)["stat_judge_type"].agg(lambda values: sorted(set(values)))
    if grouped.map(len).gt(1).any():
        raise ValueError("Conflicting stat_judge_type values for a lookup key; refusing a multiplying join")
    unique = grouped.map(lambda values: values[0]).reset_index()
    result = facts.merge(unique, on=KEYS, how="left", validate="many_to_one", sort=False)
    result["stat_judge_type"] = result["stat_judge_type"].fillna("")
    if len(result) != len(facts):
        raise ValueError("Stat lookup multiplied finance facts")
    result = result[columns].sort_values(["trade_timestamp", "order_number", "performance_employee_id"], kind="stable")
    tt = read_download(tt_supplement, tt_csv_dialect)
    if tt.empty and not tt_zero_verified:
        raise ValueError("Empty TT download requires --tt-zero-verified and operator success_empty_verified evidence")
    normalize_facts(tt, start_date, end_date)
    result, overlap_rows = merge_tt(result, tt, columns)
    unmatched = result[result["stat_judge_type"].eq("")]
    totals = lambda frame: {column: str(sum(map(Decimal, frame[column]), Decimal(0))) for column in MONEY}
    qa = {
        "row_count": len(result), "column_count": len(columns),
        "business_period": {"start_date": start_date, "end_date_inclusive": end_date},
        "finance_rows": len(facts), "finance_totals": totals(facts), "totals": totals(result),
        "tt_source_checked": True, "tt_source_rows": len(tt), "tt_overlap_rows_skipped": overlap_rows,
        "tt_rows_added": len(result) - len(facts), "tt_source_totals": totals(tt),
        "tt_added_totals": totals(result.iloc[len(facts):]),
        "tt_zero_verified_assertion": tt_zero_verified if tt.empty else None,
        "tt_blank_source_columns": TT_MISSING_COLUMNS,
        "csv_dialects": {"finance": finance_csv_dialect, "tt_supplement": tt_csv_dialect},
        "source_coverage_issue": "bdg_ba.dwd_crm_crm_order_income_refund_info_hf lacks TT orders; always check service supplement",
        "full_population_confirmed": False,
        "input_sha256": {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in
                         [("finance", finance), ("stat_lookup", lookup), ("tt_supplement", tt_supplement)]},
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
    parser.add_argument("--tt-supplement", type=Path, required=True, help="Mandatory 26-column service TT download")
    parser.add_argument("--start-date", required=True, help="Inclusive business date YYYY-MM-DD")
    parser.add_argument("--end-date", required=True, help="Inclusive business date YYYY-MM-DD")
    parser.add_argument("--tt-zero-verified", action="store_true", help="Only after operator verified an empty TT result")
    parser.add_argument("--finance-csv-dialect", choices=["template", "standard"], default="template")
    parser.add_argument("--tt-csv-dialect", choices=["template", "standard"], default="standard")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--qa", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(assemble(args.finance, args.lookup, args.output, args.qa,
                              tt_supplement=args.tt_supplement, start_date=args.start_date,
                              end_date=args.end_date, tt_zero_verified=args.tt_zero_verified,
                              finance_csv_dialect=args.finance_csv_dialect, tt_csv_dialect=args.tt_csv_dialect),
                     ensure_ascii=False, indent=2))
