"""Re-export conversion table (tbl9CcVtXPntqGvP) slices for preview refresh.

Usage (CLI): python export_conversion_refresh.py <channel> <output_ndjson> [period]
  channel = douyin_dm | private | public_pool | partner_books | partner_local
  period  = optional 20261002期-style filter applied locally after export

Importable: export_conversion(channel, period, output) -> manifest dict
Writes <output>.manifest.json (has_more=False, records_count, rev) compatible with
preview_qingcheng_transformation._read_rows. records_count is the row count AFTER
the local period filter (manifest keeps export_records_count for the raw slice).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from lark_delivery.common.runtime import run_lark

SKILL = Path(__file__).resolve().parents[1]
WORKSPACE = SKILL.parents[1]
BASE_TOKEN = "QOVib6QCXaUvJ2s2PsbcnMmsnGg"
TABLE_ID = "tbl9CcVtXPntqGvP"
OUT_DIR = WORKSPACE / "runtime" / "qingcheng_refresh"
PAGE_SIZE = 2000

FILTERS = {
    "douyin_dm": {"logic": "and", "conditions": [["渠道", "==", "抖音私信"]]},
    "private": {"logic": "or", "conditions": [
        ["渠道", "==", "私域表单"], ["渠道", "==", "私域品效"]]},
    "public_pool": {"logic": "and", "conditions": [["一级渠道", "==", "公海"]]},
    # 伙伴渠道与公海同构：服务端只按一级渠道裁剪，二级渠道（武汉图书/河南本地化）
    # 由 transformation_preview.json 的 match 在本地强校验。
    "partner_books": {"logic": "and", "conditions": [["一级渠道", "==", "图书"]]},
    "partner_local": {"logic": "and", "conditions": [["一级渠道", "==", "本地化"]]},
}


def export_conversion(channel: str, period: str, output: Path, *, cache_dir: Path | None = None) -> dict:
    """Export one channel's conversion slice, optionally filtered to one period."""
    if channel not in FILTERS:
        raise ValueError("channel must be one of: " + ", ".join(sorted(FILTERS)))
    if period and not re.fullmatch(r"20\d{6}期", period):
        raise ValueError(f"Unexpected period format: {period!r}")
    output.parent.mkdir(parents=True, exist_ok=True)
    page_dir = cache_dir or OUT_DIR
    page_dir.mkdir(parents=True, exist_ok=True)
    filtered = json.dumps(FILTERS[channel], ensure_ascii=True)
    rows: list[dict] = []
    revision: int | None = None
    offset = 0
    page = 0
    for page in range(20):
        page_file = page_dir / f"{channel}.page{page + 1}.ndjson"
        args = ["base", "+record-list", "--base-token", BASE_TOKEN, "--table-id", TABLE_ID,
                "--filter-json", filtered, "--offset", str(offset), "--limit", str(PAGE_SIZE),
                "--format", "ndjson", "--output", str(page_file), "--as", "user", "--overwrite"]
        run_lark(args, cwd=WORKSPACE, timeout=240)
        manifest = json.loads(page_file.with_suffix(".manifest.json").read_text(encoding="utf-8"))
        page_rows = [json.loads(line) for line in page_file.read_text(encoding="utf-8").splitlines() if line]
        rev = manifest.get("rev")
        if not isinstance(rev, int) or (revision is not None and revision != rev):
            raise ValueError(f"revision changed during pagination: {rev!r}")
        revision = rev
        rows.extend(page_rows)
        if not manifest.get("has_more"):
            break
        offset += len(page_rows)
    else:
        raise ValueError("Conversion export exceeded the page limit without a complete result")
    export_count = len(rows)
    if period:
        rows = [row for row in rows if row.get("期次") == period]
    output.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    manifest = {"base_token": BASE_TOKEN, "table_id": TABLE_ID, "rev": revision,
                "records_count": len(rows), "export_records_count": export_count,
                "page_count": page + 1, "has_more": False, "channel": channel, "period": period}
    output.with_suffix(".manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    return manifest


def main() -> int:
    if len(sys.argv) not in (3, 4):
        raise ValueError("usage: export_conversion_refresh.py <channel> <output_ndjson> [period]")
    channel, output = sys.argv[1], Path(sys.argv[2])
    period = sys.argv[3] if len(sys.argv) == 4 else ""
    manifest = export_conversion(channel, period, output)
    print(json.dumps(manifest, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
