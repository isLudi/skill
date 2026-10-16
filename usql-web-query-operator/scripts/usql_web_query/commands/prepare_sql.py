"""Prepare a separate local SQL copy without submitting or rebinding a plan."""

from __future__ import annotations

import argparse
import json

from _shared.errors import UsageError
from usql_web_query.query_contract import exact_sql_sha256
from usql_web_query.sql_utils import prepare_query_sql, read_sql


def cmd_prepare_sql(args: argparse.Namespace) -> int:
    if args.sql_file.resolve() == args.output.resolve():
        raise UsageError("Prepared SQL must be a separate file; the source is preserved.")
    source = read_sql(args.sql_file)
    prepared = prepare_query_sql(source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # A fresh path avoids replacing unrelated source or an approved candidate.
    try:
        with args.output.open("x", encoding="utf-8", newline="") as stream:
            stream.write(prepared)
    except FileExistsError as exc:
        raise UsageError("Prepared output already exists; choose a fresh output path.") from exc
    if read_sql(args.output) != prepared:
        raise UsageError("Prepared SQL readback differs from the intended text.")
    print(json.dumps({
        "ok": True, "output": str(args.output),
        "source_sql_sha256": exact_sql_sha256(source),
        "prepared_sql_sha256": exact_sql_sha256(prepared),
        "removed_prefix_characters": len(source) - len(prepared),
        "submitted": False, "query_plan_rebound": False,
    }, ensure_ascii=True, indent=2))
    return 0
