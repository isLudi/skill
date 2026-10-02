"""Write the adjusted push windows back to the nine operator records (tbl3iMKvD52jaMF1).

Usage: python update_base_push_windows.py [--dry-run]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from lark_delivery.common.runtime import run_lark

WORKSPACE = Path(__file__).resolve().parents[2]
BASE_TOKEN = "OEJrbiCIaazfSss2R3Lcf1OonCc"
TABLE_ID = "tbl3iMKvD52jaMF1"
RECORDS = ["recvwjZ8GbkWV7", "recvwjAT4WbHAS", "recvwjZ9JJylEQ", "recvwjX2koAHjx",
           "recvwjZbPTL5aH", "recvwjX5b2YILG",
           "recvwjW9ZAvRBW", "recvwjX409k8f2", "recvwjZaMMix5H"]
NEW_VALUE = "周五/周六/周日 14:02、18:02、22:02；次周周一仅 02:02（2026-10-01 调整）"


def main() -> int:
    payload = {"update_records": {rid: {"期望推送时段": NEW_VALUE} for rid in RECORDS}}
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
        get_args += ["--field-id", "期望推送时段", "--format", "json", "--as", "user"]
        verify = json.loads(run_lark(get_args, cwd=WORKSPACE, timeout=120))
        data = verify.get("data", {})
        names = data.get("fields", [])
        rids = data.get("record_id_list", [])
        values = data.get("data", [])
        mismatch = []
        for rid, value_row in zip(rids, values):
            row = dict(zip(names, value_row))
            current = row.get("期望推送时段")
            if isinstance(current, list):
                current = "".join(part.get("text", "") if isinstance(part, dict) else str(part)
                                  for part in current)
            if str(current) != NEW_VALUE:
                mismatch.append((rid, str(current)[:80]))
        print(f"verify: {len(rids)} records read back, mismatch={len(mismatch)}")
        for rid, text in mismatch:
            print(f"MISMATCH {rid}: {text!r}")
        return 0 if (len(rids) == len(RECORDS) and not mismatch) else 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
