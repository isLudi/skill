"""Check public-pool (公海) channel rows in the conversion table for 20261002期.

Confirms whether the 公海 channel produces any conversion data this period
(transformation_preview.json matches 一级渠道=公海 & 渠道=顾问未加好友).
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
PERIOD = "20261002期"


def main() -> int:
    filtered = json.dumps(
        {"logic": "and", "conditions": [["期次", "==", PERIOD]]}, ensure_ascii=True
    )
    rows: list[dict] = []
    revision: int | None = None
    offset = 0
    for page in range(10):
        page_file = OUT_DIR / f"poolcheck.page{page + 1}.ndjson"
        args = ["base", "+record-list", "--base-token", BASE_TOKEN, "--table-id", TABLE_ID,
                "--filter-json", filtered, "--offset", str(offset), "--limit", str(PAGE_SIZE),
                "--format", "ndjson", "--output", str(page_file), "--as", "user", "--overwrite"]
        run_lark(args, cwd=WORKSPACE, timeout=240)
        manifest = json.loads(page_file.with_suffix(".manifest.json").read_text(encoding="utf-8"))
        page_rows = [json.loads(line) for line in page_file.read_text(encoding="utf-8").splitlines() if line]
        rev = manifest.get("rev")
        if not isinstance(rev, int) or (revision is not None and revision != rev):
            print(f"REVISION_CHANGED page={page + 1} rev={rev!r}")
            return 3
        revision = rev
        rows.extend(page_rows)
        if not manifest.get("has_more"):
            break
        offset += len(page_rows)

    print(f"rev={revision} rows_{PERIOD}={len(rows)}")
    top = Counter((r.get("一级渠道") or "?") for r in rows)
    print("level1_distribution=" + json.dumps(top, ensure_ascii=False, sort_keys=True))

    pool = [r for r in rows if r.get("一级渠道") == "公海"]
    sub = Counter((r.get("渠道") or "?") for r in pool)
    print(f"pool_rows={len(pool)}")
    print("pool_subchannel_distribution=" + json.dumps(sub, ensure_ascii=False, sort_keys=True))
    for r in sorted(pool, key=lambda x: str(x.get("lead_id"))):
        print(
            "lead {lead}: 渠道={ch!r} 主管={sup!r} 顾问={con!r} 账号={acc!r} 年级={gr!r} "
            "收款={inc!r} 退费={ref!r} 当期收款={cur!r} 部门={dep!r}".format(
                lead=r.get("lead_id"), ch=r.get("渠道"), sup=r.get("主管"), con=r.get("顾问"),
                acc=r.get("顾问账号"), gr=r.get("年级"), inc=r.get("收款"), ref=r.get("退费"),
                cur=r.get("当期收款"), dep=r.get("部门"),
            )
        )
    print("RESULT=" + ("HAS_DATA" if pool else "NO_DATA"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
