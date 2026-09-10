#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
export_base.py — 从飞书多维表格分页导出一张表到本地 JSON（通用模板）

用法：
    PowerShell: $env:BASE_TOKEN='<base_token>'; $env:TABLE_ID='<tblXXX>'; & 'D:\anaconda3\python.exe' export_base.py
    # 可选：FIELDS='字段1,字段2' 只导指定列；OUT=data/mytable.json 改输出文件

要点（已内建踩坑处理）：
- lark-cli >= 1.0.88 才有 --output/--overwrite；旧版先升级
- 每页最多 2000 行，用 offset 翻页直到 has_more=false
- 子进程强制 utf-8 解码，Windows 默认 GBK 会炸
"""
import json, os, shutil, sys, tempfile
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
from lark_runtime import run_lark

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

B = os.environ.get("BASE_TOKEN", "")  # 多维表格 token（URL 里 /base/ 后面那段）
T = os.environ.get("TABLE_ID", "")    # 表 ID（tbl 开头）
if not B or not T:
    raise SystemExit("请设置 BASE_TOKEN 和 TABLE_ID 环境变量")
FIELDS = [f for f in os.environ.get("FIELDS", "").split(",") if f]
OUT = Path(os.environ.get("OUT", "data/export.json")).expanduser().resolve()
OUT.parent.mkdir(parents=True, exist_ok=True)
page_dir = Path(tempfile.mkdtemp(prefix=".miaoda-pages-", dir=str(OUT.parent)))
page_file = page_dir / "page.ndjson"
cli_page_file = os.path.relpath(page_file, OUT.parent).replace(os.sep, "/")

try:
    all_recs, offset, page = [], 0, 0
    while True:
        page += 1
        cmd = ["base", "+record-list", "--base-token", B, "--table-id", T,
               "--limit", "2000", "--offset", str(offset),
               "--format", "ndjson", "--output", cli_page_file,
               "--overwrite", "--as", "user"]
        for f in FIELDS:
            cmd += ["--field-id", f]
        info = json.loads(run_lark(cmd, cwd=str(OUT.parent), timeout=600))
        cnt = info.get("records_count", 0)
        with page_file.open(encoding="utf-8") as fp:
            all_recs += [json.loads(x) for x in fp if x.strip()]
        print("  page=%d offset=%d got=%d has_more=%s total=%d"
              % (page, offset, cnt, info.get("has_more"), len(all_recs)), flush=True)
        if not info.get("has_more") or cnt == 0:
            break
        offset += cnt

    with OUT.open("w", encoding="utf-8") as fp:
        json.dump(all_recs, fp, ensure_ascii=False)
    print("导出完成: %s 共 %d 行" % (OUT, len(all_recs)))
finally:
    shutil.rmtree(page_dir, ignore_errors=True)
