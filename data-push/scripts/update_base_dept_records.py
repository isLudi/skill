"""Write the dept-level (学部) configuration back to the four Base operator records.

Records: recvwk1kzL4vtb(私域) recvwk1l411M24(图书) recvwk1lwipGZ4(抖音私信)
recvwk1mMwDv9n(公海), all targeting the shared group oc_a95c83e488e0dfcc777d5ffad849d8a4.
Updates: 期望推送时段 (2026-10-03 correction: dept joins only the Fri/Sat/Sun
14:02 window plus the Monday 04:00 closing slot — the 10-02 three-slot write
was a scheduling-side deviation from the 14:00 single-slot request) and
申请状态 (已上线).

Usage: python update_base_dept_records.py [--dry-run]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from lark_delivery.common.runtime import run_lark

WORKSPACE = Path(__file__).resolve().parents[2]
BASE_TOKEN = "OEJrbiCIaazfSss2R3Lcf1OonCc"
TABLE_ID = "tbl3iMKvD52jaMF1"
RECORDS = ["recvwk1kzL4vtb", "recvwk1l411M24", "recvwk1lwipGZ4", "recvwk1mMwDv9n"]
WINDOW_VALUE = "周五/周六/周日 14:02；次周周一 04:00 收官档（学部级单档，2026-10-05 调整）"
STATUS_VALUE = "已上线"


def main() -> int:
    payload = {"update_records": {rid: {"期望推送时段": WINDOW_VALUE, "申请状态": STATUS_VALUE}
                                  for rid in RECORDS}}
    args = ["base", "+record-batch-update", "--base-token", BASE_TOKEN, "--table-id", TABLE_ID,
            "--json", json.dumps(payload, ensure_ascii=False), "--as", "user", "--format", "json"]
    if "--dry-run" in sys.argv:
        args.append("--dry-run")
    out = run_lark(args, cwd=WORKSPACE, timeout=120)
    data = json.loads(out)
    print(json.dumps(data, ensure_ascii=False)[:800])
    if data.get("ok") is not True:
        return 2
    if "--dry-run" not in sys.argv:
        get_args = ["base", "+record-get", "--base-token", BASE_TOKEN, "--table-id", TABLE_ID]
        for rid in RECORDS:
            get_args += ["--record-id", rid]
        get_args += ["--field-id", "期望推送时段", "--field-id", "申请状态",
                     "--format", "json", "--as", "user"]
        verify = json.loads(run_lark(get_args, cwd=WORKSPACE, timeout=120))
        vdata = verify.get("data", {})
        names = vdata.get("fields", [])
        rids = vdata.get("record_id_list", [])
        values = vdata.get("data", [])
        mismatch = []
        for rid, value_row in zip(rids, values):
            row = dict(zip(names, value_row))
            for field, expected in (("期望推送时段", WINDOW_VALUE), ("申请状态", STATUS_VALUE)):
                current = row.get(field)
                if isinstance(current, list):
                    current = "".join(part.get("text", "") if isinstance(part, dict) else str(part)
                                      for part in current)
                if str(current) != expected:
                    mismatch.append((rid, field, str(current)[:80]))
        print(f"verify: {len(rids)} records read back, mismatch={len(mismatch)}")
        for item in mismatch:
            print(f"MISMATCH {item[0]} {item[1]}: {item[2]!r}")
        return 0 if (len(rids) == len(RECORDS) and not mismatch) else 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
