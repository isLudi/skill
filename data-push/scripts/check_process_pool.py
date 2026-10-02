"""Check public-pool rows in the PROCESS table (tblXU4tla3bY36DE) for 20261002期."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

from lark_delivery.common.runtime import run_lark

WORKSPACE = Path(__file__).resolve().parents[2]
OUT = WORKSPACE / "runtime" / "zhuanhua_monitor"
PAGE_SIZE = 2000
PERIOD = "20261002期"


def main() -> int:
    filtered = json.dumps(
        {"logic": "and", "conditions": [["期次", "==", PERIOD], ["一级渠道", "==", "公海"]]},
        ensure_ascii=True,
    )
    rows: list[dict] = []
    offset = 0
    revision = None
    for page in range(20):
        page_file = OUT / f"process_pool.page{page + 1}.ndjson"
        args = ["base", "+record-list", "--base-token", "QOVib6QCXaUvJ2s2PsbcnMmsnGg",
                "--table-id", "tblXU4tla3bY36DE", "--filter-json", filtered,
                "--offset", str(offset), "--limit", str(PAGE_SIZE), "--format", "ndjson",
                "--output", str(page_file), "--as", "user", "--overwrite"]
        run_lark(args, cwd=WORKSPACE, timeout=240)
        manifest = json.loads(page_file.with_suffix(".manifest.json").read_text(encoding="utf-8"))
        page_rows = [json.loads(line) for line in page_file.read_text(encoding="utf-8").splitlines() if line]
        rev = manifest.get("rev")
        if revision is not None and revision != rev:
            print(f"REVISION_CHANGED rev={rev!r}")
            return 3
        revision = rev
        rows.extend(page_rows)
        if not manifest.get("has_more"):
            break
        offset += len(page_rows)

    print(f"rev={revision} process_pool_rows={len(rows)}")
    print("supervisor_dist_top20=" + json.dumps(Counter(r.get("主管") for r in rows).most_common(20), ensure_ascii=False))
    print("grade_dist=" + json.dumps(Counter(r.get("年级") for r in rows), ensure_ascii=False, sort_keys=True))
    leads = sum(float(r.get("退后线索") or 0) for r in rows)
    print(f"sum_taohou_leads={leads:.0f}")
    for sup, cnt in Counter(r.get("主管") for r in rows if float(r.get("退后线索") or 0) > 0).most_common(20):
        print(f"supervisor_with_leads: {sup!r}")
    print("RESULT=" + ("HAS_LEADS" if leads > 0 else "NO_LEADS"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
