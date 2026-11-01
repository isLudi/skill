"""Fetch one Qingcheng process period with complete, same-revision Base pages."""

from __future__ import annotations

import argparse
from collections import Counter
import json
import re
from pathlib import Path

from lark_delivery.common.runtime import run_lark


SKILL = Path(__file__).resolve().parents[1]
WORKSPACE = SKILL.parents[1]
BASE_TOKEN = "QOVib6QCXaUvJ2s2PsbcnMmsnGg"
TABLE_ID = "tblXU4tla3bY36DE"
PRIMARY = {"public_pool": "公海", "private": "私域", "douyin_dm": "抖音私信",
           "sec_public": "公域", "sec_order_reuse": "订单复用",
           "special_books": "图书", "special_public_pool": "公海",
           "partner_books": "图书", "partner_local": "本地化", "internal_books": "图书"}
PRIVATE_CHANNELS = ("私域表单", "私域品效", "表单浙江", "表单江苏")
PAGE_SIZE = 2000


def fetch(channel: str, period: str, output: Path, *, secondary_channel: str | None = None,
          allow_empty: bool = False) -> dict:
    if channel not in PRIMARY or not re.fullmatch(r"20\d{6}期", period):
        raise ValueError("Channel or period is invalid")
    output.parent.mkdir(parents=True, exist_ok=True)
    condition = [["一级渠道", "==", PRIMARY[channel]], ["期次", "==", period]]
    if secondary_channel is not None:
        if channel != "sec_order_reuse" or secondary_channel not in {"SEC未加好友", "SEC首期掉海"}:
            raise ValueError("Unreviewed SEC report secondary channel")
        condition.append(["渠道", "==", secondary_channel])
    if channel == "public_pool":
        condition.append(["渠道", "==", "顾问未加好友"])
    elif channel == "douyin_dm":
        condition.append(["渠道", "==", "抖音私信"])
    elif channel == "sec_public":
        condition.append(["渠道", "==", "公域学霸"])
    elif channel == "internal_books":
        condition.append(["渠道", "==", "内部图书"])
    filtered = json.dumps({"logic": "and", "conditions": condition}, ensure_ascii=True)
    rows = []
    revision = None
    snapshot = None
    offset = 0
    for page in range(50):
        page_file = output.with_name(f"{output.stem}.page{page + 1}.ndjson")
        args = ["base", "+record-list", "--base-token", BASE_TOKEN, "--table-id", TABLE_ID,
                "--filter-json", filtered, "--offset", str(offset), "--limit", str(PAGE_SIZE),
                "--format", "ndjson", "--output", str(page_file), "--as", "user", "--overwrite"]
        run_lark(args, cwd=WORKSPACE, timeout=240)
        manifest = json.loads(page_file.with_suffix(".manifest.json").read_text(encoding="utf-8"))
        page_rows = [json.loads(line) for line in page_file.read_text(encoding="utf-8").splitlines() if line]
        if (manifest.get("base_token"), manifest.get("table_id"), manifest.get("records_count")) != (BASE_TOKEN, TABLE_ID, len(page_rows)):
            raise ValueError("Base page identity or row count changed")
        if not isinstance(manifest.get("rev"), int) or (revision is not None and revision != manifest["rev"]):
            raise ValueError("Base revision changed during pagination")
        revision = manifest["rev"]
        for row in page_rows:
            if row.get("一级渠道") != PRIMARY[channel] or row.get("期次") != period:
                raise ValueError("Server filter returned another channel or period")
            if channel == "public_pool" and row.get("渠道") != "顾问未加好友":
                raise ValueError("Public-pool secondary channel changed")
            if channel == "douyin_dm" and row.get("渠道") != "抖音私信":
                raise ValueError("Douyin secondary channel changed")
            if channel == "sec_public" and row.get("渠道") != "公域学霸":
                raise ValueError("SEC public secondary channel changed")
            if channel == "internal_books" and row.get("渠道") != "内部图书":
                raise ValueError("Internal-books secondary channel changed")
            if secondary_channel is not None and row.get("渠道") != secondary_channel:
                raise ValueError("SEC report secondary channel changed")
            if channel == "sec_order_reuse" and (not isinstance(row.get("渠道"), str) or not row["渠道"].strip()):
                raise ValueError("SEC order-reuse secondary channel is missing")
            if channel == "private" and not row.get("渠道"):
                raise ValueError("Private secondary channel is missing")
            point = (row.get("分区日期"), row.get("分区小时"))
            if snapshot is not None and point != snapshot:
                raise ValueError("Raw Base rows span multiple snapshots")
            snapshot = point
        rows.extend(page_rows)
        if manifest.get("has_more") is False:
            break
        if not page_rows or manifest.get("has_more") is not True:
            raise ValueError("Base pagination is incomplete")
        offset += len(page_rows)
    else:
        raise ValueError("Base pagination exceeded the reviewed bound")
    empty_scope_verified = False
    if not rows and allow_empty and channel == "partner_books":
        # An empty channel still needs a current-period snapshot at the same
        # Base revision. Never infer freshness from an old period or a clock.
        witness = output.with_name(output.stem + ".period_snapshot.ndjson")
        period_filter = json.dumps({"logic": "and", "conditions": [["期次", "==", period]]}, ensure_ascii=True)
        run_lark(["base", "+record-list", "--base-token", BASE_TOKEN, "--table-id", TABLE_ID,
                  "--filter-json", period_filter, "--limit", "1", "--format", "ndjson",
                  "--output", str(witness), "--as", "user", "--overwrite"], cwd=WORKSPACE, timeout=120)
        proof = json.loads(witness.with_suffix(".manifest.json").read_text(encoding="utf-8"))
        sample = [json.loads(line) for line in witness.read_text(encoding="utf-8").splitlines() if line]
        if ((proof.get("base_token"), proof.get("table_id"), proof.get("rev"), proof.get("records_count"))
                != (BASE_TOKEN, TABLE_ID, revision, 1) or len(sample) != 1 or sample[0].get("期次") != period):
            raise ValueError("Empty channel snapshot witness is missing or changed revision")
        snapshot = (sample[0].get("分区日期"), sample[0].get("分区小时"))
        if (not re.fullmatch(r"20\d{6}", str(snapshot[0]))
                or not re.fullmatch(r"\d{1,2}", str(snapshot[1])) or not 0 <= int(snapshot[1]) <= 23):
            raise ValueError("Empty channel snapshot witness is invalid")
        empty_scope_verified = True
    if (not rows and not empty_scope_verified) or len({row.get("record_id") for row in rows}) != len(rows) or len({row.get("记录键") for row in rows}) != len(rows):
        raise ValueError("Missing or duplicate Qingcheng process source rows")
    exported_count = len(rows)
    excluded_channels = Counter()
    if channel == "private":
        excluded_channels = Counter(row["渠道"] for row in rows if row["渠道"] not in PRIVATE_CHANNELS)
        rows = [row for row in rows if row["渠道"] in PRIVATE_CHANNELS]
        if not rows:
            raise ValueError("No rows match the reviewed private secondary channels")
    output.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    combined = {"manifest_version": "v1", "format": "ndjson", "base_token": BASE_TOKEN,
                "table_id": TABLE_ID, "rev": revision, "records_count": len(rows),
                "page_count": page + 1, "has_more": False, "channel": channel, "period": period,
                "snapshot": list(snapshot)}
    if empty_scope_verified:
        combined["empty_scope_verified"] = True
    if secondary_channel is not None:
        combined["secondary_channel"] = secondary_channel
    if channel == "private":
        combined.update(export_records_count=exported_count,
                        excluded_secondary_channel_counts=dict(sorted(excluded_channels.items())))
    output.with_suffix(".manifest.json").write_text(json.dumps(combined, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return combined


def probe_revision(channel: str, period: str, output: Path, *, secondary_channel: str | None = None,
                   allow_empty: bool = False) -> int:
    if channel not in PRIMARY or not re.fullmatch(r"20\d{6}期", period):
        raise ValueError("Channel or period is invalid")
    conditions = [["一级渠道", "==", PRIMARY[channel]], ["期次", "==", period]]
    if secondary_channel is not None:
        if channel != "sec_order_reuse" or secondary_channel not in {"SEC未加好友", "SEC首期掉海"}:
            raise ValueError("Unreviewed SEC report secondary channel")
        conditions.append(["渠道", "==", secondary_channel])
    if channel == "public_pool":
        conditions.append(["渠道", "==", "顾问未加好友"])
    elif channel == "douyin_dm":
        conditions.append(["渠道", "==", "抖音私信"])
    elif channel == "sec_public":
        conditions.append(["渠道", "==", "公域学霸"])
    elif channel == "internal_books":
        conditions.append(["渠道", "==", "内部图书"])
    output.parent.mkdir(parents=True, exist_ok=True)
    run_lark(["base", "+record-list", "--base-token", BASE_TOKEN, "--table-id", TABLE_ID,
              "--filter-json", json.dumps({"logic": "and", "conditions": conditions}, ensure_ascii=True),
              "--limit", "1", "--format", "ndjson", "--output", str(output),
              "--as", "user", "--overwrite"], cwd=WORKSPACE, timeout=120)
    manifest = json.loads(output.with_suffix(".manifest.json").read_text(encoding="utf-8"))
    count = manifest.get("records_count")
    verified_empty = allow_empty and channel == "partner_books" and count == 0 and manifest.get("has_more") is False
    if ((manifest.get("base_token"), manifest.get("table_id")) != (BASE_TOKEN, TABLE_ID)
            or (count != 1 and not verified_empty) or not isinstance(manifest.get("rev"), int)):
        raise ValueError("Raw Base revision probe failed")
    return manifest["rev"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--channel", choices=tuple(PRIMARY), required=True)
    parser.add_argument("--period-date", required=True, help="Business Friday in YYYYMMDD format")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"20\d{6}", args.period_date):
        raise ValueError("Period date must be YYYYMMDD")
    result = fetch(args.channel, args.period_date + "期", args.output)
    print(json.dumps({key: result[key] for key in ("channel", "period", "rev", "records_count", "page_count", "snapshot")}, ensure_ascii=True))


if __name__ == "__main__":
    main()
