"""Check books (图书) and local (本地化) channel rows in the conversion table for 20261002期.

Confirms secondary-channel values, supervisor/consultant/grade distribution,
zero-field conversion output and per-grade 截面单效 numerators for the two
partner channels the user asked to configure (books consultant-only; local
supervisor + consultant).
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from lark_delivery.common.runtime import run_lark

SKILL = Path(__file__).resolve().parents[1]
WORKSPACE = SKILL.parents[1]
BASE_TOKEN = "QOVib6QCXaUvJ2s2PsbcnMmsnGg"
TABLE_ID = "tbl9CcVtXPntqGvP"
OUT_DIR = WORKSPACE / "runtime" / "zhuanhua_monitor"
PAGE_SIZE = 2000
PERIOD = "20261002期"
CHANNELS = {"图书": "partner_books", "本地化": "partner_local"}
GRADES = ("高一", "高二", "高三", "初三")


def fetch_slice(level1: str, tag: str) -> list[dict]:
    filtered = json.dumps({"logic": "and", "conditions": [["一级渠道", "==", level1]]}, ensure_ascii=True)
    rows: list[dict] = []
    revision: int | None = None
    offset = 0
    for page in range(10):
        page_file = OUT_DIR / f"{tag}conv.page{page + 1}.ndjson"
        args = ["base", "+record-list", "--base-token", BASE_TOKEN, "--table-id", TABLE_ID,
                "--filter-json", filtered, "--offset", str(offset), "--limit", str(PAGE_SIZE),
                "--format", "ndjson", "--output", str(page_file), "--as", "user", "--overwrite"]
        run_lark(args, cwd=WORKSPACE, timeout=240)
        manifest = json.loads(page_file.with_suffix(".manifest.json").read_text(encoding="utf-8"))
        page_rows = [json.loads(line) for line in page_file.read_text(encoding="utf-8").splitlines() if line]
        rev = manifest.get("rev")
        if not isinstance(rev, int) or (revision is not None and revision != rev):
            print(f"REVISION_CHANGED {tag} page={page + 1} rev={rev!r}")
            sys.exit(3)
        revision = rev
        rows.extend(page_rows)
        if not manifest.get("has_more"):
            break
        offset += len(page_rows)
    print(f"{tag}: rev={revision} all_periods_rows={len(rows)}")
    rows = [r for r in rows if r.get("期次") == PERIOD]
    print(f"{tag}: rows_{PERIOD}={len(rows)}")
    return rows


def describe(tag: str, rows: list[dict]) -> None:
    sub = Counter((r.get("渠道") or "?") for r in rows)
    print(f"{tag}_subchannel=" + json.dumps(sub, ensure_ascii=False, sort_keys=True))
    src = Counter(str(r.get("记录键", "")).split("|")[1] if len(str(r.get("记录键", "")).split("|")) == 6 else "?" for r in rows)
    print(f"{tag}_source=" + json.dumps(src, ensure_ascii=False, sort_keys=True))
    sup = Counter((r.get("主管") or "?") for r in rows)
    print(f"{tag}_supervisor=" + json.dumps(sup, ensure_ascii=False, sort_keys=True))
    con = Counter((r.get("顾问") or "?") for r in rows)
    print(f"{tag}_consultant=" + json.dumps(con, ensure_ascii=False, sort_keys=True))
    grade = Counter((r.get("年级") or "?") for r in rows)
    print(f"{tag}_grade=" + json.dumps(grade, ensure_ascii=False, sort_keys=True))
    zero_fields = ("收款", "退费", "当期收款", "成交人头", "报科数")
    totals = {f: round(sum(float(r.get(f) or 0) for r in rows), 2) for f in zero_fields}
    print(f"{tag}_totals=" + json.dumps(totals, ensure_ascii=False))
    has_output = any(v != 0 for v in totals.values())
    print(f"{tag}_RESULT=" + ("HAS_DATA" if has_output else "NO_DATA"))
    # per-grade numerators for supervisor-level preview (净收款 / leads come from process table)
    by_grade = defaultdict(lambda: {"净收款": 0.0, "收款": 0.0, "退费": 0.0, "成交人头": 0.0, "报科数": 0.0})
    for r in rows:
        if r.get("年级") not in GRADES or r.get("主管") in (None, "", "未分配主管"):
            continue
        bucket = by_grade[r.get("年级")]
        for f in bucket:
            bucket[f] += float(r.get(f) or 0)
    print(f"{tag}_grade_numerators=" + json.dumps({k: {kk: round(vv, 2) for kk, vv in v.items()} for k, v in sorted(by_grade.items())}, ensure_ascii=False))
    # top consultants by grade by 净收款 (rough; real 截面单效 needs process leads)
    by_grade_con = defaultdict(lambda: defaultdict(float))
    for r in rows:
        if r.get("年级") not in GRADES or r.get("主管") in (None, "", "未分配主管"):
            continue
        by_grade_con[r.get("年级")][r.get("顾问") or "?"] += float(r.get("净收款") or 0)
    for grade in GRADES:
        top = sorted(by_grade_con.get(grade, {}).items(), key=lambda kv: -kv[1])[:5]
        print(f"{tag}_net_by_consultant_{grade}=" + json.dumps(top, ensure_ascii=False))


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for level1, tag in CHANNELS.items():
        describe(tag, fetch_slice(level1, tag))
    return 0


if __name__ == "__main__":
    sys.exit(main())
