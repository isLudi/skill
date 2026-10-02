"""Monitor zhuanhua 18:00 rerun: read back Base conversion table and check the
2 '未分配账号' finance-only rows (lead 335471948 / 325331858, douyin_dm 20261002期).

Exit codes: 0 = fix confirmed; 2 = still not fixed; 3 = read error.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

from lark_delivery.common.runtime import run_lark

SKILL = Path(__file__).resolve().parents[1]
WORKSPACE = SKILL.parents[1]
BASE_TOKEN = "QOVib6QCXaUvJ2s2PsbcnMmsnGg"
TABLE_ID = "tbl9CcVtXPntqGvP"
OUT_DIR = WORKSPACE / "runtime" / "zhuanhua_monitor"
PAGE_SIZE = 2000

TARGET_LEADS = {"335471948", "325331858"}


def read_once() -> tuple[int | None, list[dict]]:
    filtered = json.dumps(
        {"logic": "and", "conditions": [["期次", "==", "20261002期"], ["渠道", "==", "抖音私信"]]},
        ensure_ascii=True,
    )
    rows: list[dict] = []
    revision: int | None = None
    offset = 0
    for page in range(10):
        page_file = OUT_DIR / f"monitor_base.page{page + 1}.ndjson"
        args = ["base", "+record-list", "--base-token", BASE_TOKEN, "--table-id", TABLE_ID,
                "--filter-json", filtered, "--offset", str(offset), "--limit", str(PAGE_SIZE),
                "--format", "ndjson", "--output", str(page_file), "--as", "user", "--overwrite"]
        run_lark(args, cwd=WORKSPACE, timeout=240)
        manifest = json.loads(page_file.with_suffix(".manifest.json").read_text(encoding="utf-8"))
        page_rows = [json.loads(line) for line in page_file.read_text(encoding="utf-8").splitlines() if line]
        rev = manifest.get("rev")
        if not isinstance(rev, int) or (revision is not None and revision != rev):
            print(f"REVISION_CHANGED page={page + 1} rev={rev!r}")
            sys.exit(3)
        revision = rev
        rows.extend(page_rows)
        if not manifest.get("has_more"):
            break
        offset += len(page_rows)
    return revision, rows


def main() -> int:
    rev, rows = read_once()
    dist = Counter(r.get("顾问账号") for r in rows)
    print(f"rev={rev} rows={len(rows)}")
    print("account_distribution=" + json.dumps(dist, ensure_ascii=False, sort_keys=True))

    unassigned = [r for r in rows if r.get("顾问账号") == "未分配账号"]
    print(f"unassigned_rows={len(unassigned)}")

    targets = {r.get("lead_id"): r for r in rows if str(r.get("lead_id")) in TARGET_LEADS}
    for lead in sorted(TARGET_LEADS):
        r = targets.get(lead)
        if r is None:
            print(f"lead {lead}: MISSING")
            continue
        print(
            "lead {lead}: account={acc!r} supervisor={sup!r} consultant={con!r} "
            "income={inc!r} refund={ref!r} dept={dep!r}".format(
                lead=lead, acc=r.get("顾问账号"), sup=r.get("主管"), con=r.get("顾问"),
                inc=r.get("收款"), ref=r.get("退费"), dep=r.get("部门"),
            )
        )

    fixed = all(
        str(targets.get(lead, {}).get("顾问账号")) not in ("未分配账号", "None")
        for lead in TARGET_LEADS
    ) and len(unassigned) == 0
    if fixed:
        print("RESULT=FIXED")
        return 0
    print("RESULT=NOT_FIXED")
    return 2


if __name__ == "__main__":
    sys.exit(main())
