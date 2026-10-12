"""Bounded Data Center reads for the internal-books branch of existing batches."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import uuid
from zoneinfo import ZoneInfo

from lark_delivery.common.runtime import CREATE_NO_WINDOW

ROOT = Path(__file__).resolve().parents[3]
OPERATOR = ROOT / "skills/usql-web-query-operator/scripts"
PROCESS_FIELDS = ("qici", "xiaozu", "employee_email_name", "grade_1", "v_lead",
                  "is_friend_lead", "first_call_time_diff_hour", "is_long_call",
                  "first_call_in_24h", "first_call_connected_cnt", "call_duration",
                  "zong_call_ci", "daoke1")
CONVERSION_FIELDS = ("qici", "xiaozu", "employee_email_name", "grade_1", "v_lead",
                     "pay_user", "pay_sub", "income", "refund", "promit", "p_income", "podan", "sc")


def _write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix+".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def _python():
    machine = json.loads((ROOT/"machine.local.json").read_text(encoding="utf-8"))
    return machine["executables"]["python"]


def live_sources(config, models, folder):
    """Use the registered operator read adapter; no save/refresh or knowledge write."""
    if str(OPERATOR) not in sys.path:
        sys.path.insert(0, str(OPERATOR))
    from _shared.env import load_env_file
    from usql_web_query.cli import build_parser
    from usql_web_query.commands.sync_data_center_sql import _fetch_data_center_sql, _resolve_targets
    from usql_web_query.data_center_replacement import canonical_sql_text, sql_sha256

    argv = ["sync-data-center-sql", "--target-skill", "qingcheng"]
    for model in models:
        argv.extend(["--dataset-name", config["source"]["models"][model]["name"]])
    args = build_parser().parse_args(argv)
    load_env_file(args.env_file)
    args.username = args.username or os.environ.get("BAIJIA_USERNAME")
    args.password = args.password or os.environ.get("BAIJIA_PASSWORD")
    _, selected, sources = _fetch_data_center_sql(args, _resolve_targets(args))
    result = {}
    for dataset in selected["qingcheng"]:
        model = dataset.file_value
        expected = config["source"]["models"][model]
        if model not in models or (dataset.id, dataset.name) != (expected["menu_id"], expected["name"]):
            raise ValueError("Internal-books Data Center identity differs")
        sql = canonical_sql_text(sources[dataset.id].execute_sql)
        if sql_sha256(sql) != expected["sql_sha256"]:
            raise ValueError(f"Internal-books Data Center {model} source SQL changed; review its new version")
        folder.mkdir(parents=True, exist_ok=True)
        (folder/f"{model}_live.sql").write_text(sql, encoding="utf-8")
        result[model] = sql
    if set(result) != set(models):
        raise ValueError("Internal-books source discovery is incomplete")
    return result


def _result_rows(query_id):
    from _shared.auth import ensure_authenticated
    from _shared.browser import import_playwright, launch_context
    from _shared.env import load_env_file
    from usql_web_query.cli import build_parser
    from usql_web_query.page_helpers import wait_for_query_page
    from usql_web_query.status_poller_api import fetch_query_result_evidence

    args = build_parser().parse_args(["run", "--sql-file", "unused.sql", "--no-download"])
    load_env_file(args.env_file)
    args.username = args.username or os.environ.get("BAIJIA_USERNAME")
    args.password = args.password or os.environ.get("BAIJIA_PASSWORD")
    with import_playwright()() as pw:
        browser, context = launch_context(pw, args.state_path, False, args.browser_channel, args.executable_path)
        try:
            page = context.new_page()
            ensure_authenticated(page, args, context=context)
            wait_for_query_page(page)
            return fetch_query_result_evidence(page, query_id, max_rows=1000, request_timeout_ms=30000)
        finally:
            context.close()
            browser.close()


def _recover_outcome(folder, attempt, query_hash):
    """Recover only a uniquely bound, completed operator result; never submit."""
    if attempt.get("query_sql_sha256",query_hash) != query_hash:
        raise ValueError("Internal-books query SQL changed inside the same batch")
    pinned = attempt.get("result_artifact")
    candidates = [folder/pinned] if pinned else list((folder/"operator").rglob("result_artifact.json"))
    completed = {}
    for path in candidates:
        if not path.exists():
            continue
        if not path.resolve().is_relative_to((folder/"operator").resolve()):
            raise ValueError("Internal-books query result artifact escaped its own batch")
        artifact = json.loads(path.read_text(encoding="utf-8"))
        query_id = str(artifact.get("query_id", ""))
        if (artifact.get("artifact_type") != "result_artifact" or artifact.get("ok") is not True
                or artifact.get("status") != "Success" or not query_id.isdigit()):
            continue
        if any(value != query_hash for value in (
                artifact.get("sql_sha256"),artifact.get("editor",{}).get("sql_sha256"),
                artifact.get("submission",{}).get("submitted_sql_sha256"))):
            raise ValueError("Internal-books completed query SQL hash differs")
        if artifact.get("validation",{}).get("status") != "passed" or artifact.get("result",{}).get("evidence_conflict"):
            raise ValueError("Internal-books completed query has invalid or conflicting evidence")
        completed[query_id] = {"ok":True,"status":"Success","query_id":query_id,
                               "recovered_from_result_artifact":str(path)}
    if len(completed) > 1:
        raise ValueError("Internal-books completed query identity is ambiguous")
    return next(iter(completed.values()),None)


def _operator_run(command):
    child_env = dict(os.environ,PYTHONIOENCODING="utf-8",PYTHONUTF8="1")
    return subprocess.run(command,cwd=ROOT,capture_output=True,text=True,encoding="utf-8",
                          timeout=750,creationflags=CREATE_NO_WINDOW,env=child_env)


def _query(model, source_sql, period, folder):
    fields = PROCESS_FIELDS if model == "2064" else CONVERSION_FIELDS
    channel1 = "channel_map_1" if model == "2064" else "channel_1"
    sql = ("select " + ", ".join(fields) + ",\n"
           "format_datetime(current_timestamp - interval '3' hour, 'YYYYMMdd') as __snapshot_dt,\n"
           "format_datetime(current_timestamp - interval '3' hour, 'HH') as __snapshot_hour\n"
           "from (\n" + source_sql.rstrip().rstrip(";") + "\n) source_output\n"
           f"where qici = '{period}' and {channel1} = '图书' and channel_map_2 = '内部图书'\n"
           "and grade_1 in ('高一','高二','高三','初三')\nlimit 1000\n")
    folder.mkdir(parents=True, exist_ok=True)
    sql_path, summary_path = folder/"query.sql", folder/"summary.json"
    attempt_path = folder/"query_attempt.json"
    query_hash = hashlib.sha256(sql.encode("utf-8")).hexdigest()
    sql_path.write_text(sql, encoding="utf-8")
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else None
    previous_attempt = json.loads(attempt_path.read_text(encoding="utf-8")) if attempt_path.exists() else None
    if previous_attempt and (previous_attempt.get("status") == "started" or not summary):
        summary = _recover_outcome(folder,previous_attempt,query_hash)
        if not summary:
            raise ValueError("Internal-books prior query attempt has no outcome; review it before retrying")
        _write(summary_path,summary)
        previous_attempt.update(status="outcome_recorded",query_id=summary["query_id"],ok=True,
                                recovered_from_result_artifact=summary["recovered_from_result_artifact"])
        _write(attempt_path,previous_attempt)
    if summary and attempt_path.exists():
        if previous_attempt.get("query_sql_sha256",query_hash) != query_hash:
            raise ValueError("Internal-books query SQL changed inside the same batch")
    if not summary and attempt_path.exists():
        raise ValueError("Internal-books prior query attempt has no outcome; review it before retrying")
    cached_rows = folder/"rows.json"
    if summary and summary.get("ok") and cached_rows.exists():
        old = json.loads(cached_rows.read_text(encoding="utf-8"))
        current = datetime.now(ZoneInfo("Asia/Shanghai"))-timedelta(hours=3)
        expected_snapshot = (current.strftime("%Y%m%d"),current.strftime("%H"))
        if any((r["__snapshot_dt"],r["__snapshot_hour"]) != expected_snapshot for r in old["rows"]):
            summary = None
    # A timed-out query may still run: retain its exact ID rather than duplicate it.
    if summary and not summary.get("ok") and summary.get("query_id") and summary.get("status") not in ("Failed", "Error"):
        raise ValueError(f"Internal-books source query remains unresolved: {summary['query_id']}")
    if not summary or not summary.get("ok"):
        artifact_path = Path("operator")/uuid.uuid4().hex/"result_artifact.json"
        command = [_python(), str(OPERATOR/"usql_web_query.py"), "run", "--sql-file", str(sql_path),
                   "--no-download", "--require-limit", "--policy-mode", "audit",
                   "--required-partition-field", "dt", "--required-partition-field", "hour",
                   "--timeout-ms", "600000", "--artifacts-dir", str(folder/"operator"),
                   "--result-artifact",str(folder/artifact_path)]
        _write(attempt_path,{"model":model,"period":period,"status":"started",
                             "query_sql_sha256":query_hash,"result_artifact":str(artifact_path)})
        proc = _operator_run(command)
        try:
            summary = json.loads(proc.stdout)
        except (json.JSONDecodeError, TypeError) as exc:
            summary = _recover_outcome(folder,{"result_artifact":str(artifact_path)},query_hash)
            if not summary:
                raise ValueError("Internal-books SQL operator did not return a valid result") from exc
        _write(summary_path, summary)
        _write(attempt_path,{"model":model,"period":period,"status":"outcome_recorded",
                             "query_id":summary.get("query_id"),"ok":summary.get("ok"),
                             "query_sql_sha256":query_hash,"result_artifact":str(artifact_path)})
    if summary.get("ok") is not True or not str(summary.get("query_id", "")).isdigit():
        raise ValueError(f"Internal-books {model} query not successful: {summary.get('error_category')}")
    evidence = _result_rows(str(summary["query_id"]))
    preview = evidence.get("preview") or {}
    if evidence.get("state") not in ("success_with_rows", "success_empty_verified", "success_empty_candidate") \
            or preview.get("no_more") is not True:
        raise ValueError("Internal-books source result is incomplete or unresolved")
    raw_rows, headers = preview.get("rows", []), preview.get("headers", [])
    if len(raw_rows) >= 1000 or any(len(r) != len(headers) for r in raw_rows):
        raise ValueError("Internal-books source exceeds the bounded read or has invalid columns")
    rows = [dict(zip(headers, row)) for row in raw_rows]
    if any(r["qici"] != period or r["grade_1"] not in ("高一", "高二", "高三", "初三") for r in rows):
        raise ValueError("Internal-books source scope differs")
    result = {"model":model, "query_id":str(summary["query_id"]), "complete":True,
              "rows":rows, "evidence":evidence, "sql_sha256":query_hash}
    _write(folder/"rows.json", result)
    return result


def fetch(config, report_type, period, folder):
    if not re.fullmatch(r"20\d{6}期", period):
        raise ValueError("Internal-books period is invalid")
    models = ("2064",) if report_type == "process" else ("2064", "2460")
    sources = live_sources(config, models, folder)
    with ThreadPoolExecutor(max_workers=len(models)) as pool:
        futures = {m:pool.submit(_query, m, sources[m], period, folder/m) for m in models}
        result = {m:f.result() for m, f in futures.items()}
    snapshots = {(r["__snapshot_dt"], r["__snapshot_hour"]) for source in result.values() for r in source["rows"]}
    if len(snapshots) > 1:
        raise ValueError("Internal-books process and conversion snapshots differ")
    if snapshots:
        snapshot = next(iter(snapshots))
        source_at = datetime.strptime(" ".join(snapshot), "%Y%m%d %H").replace(tzinfo=ZoneInfo("Asia/Shanghai"))
        age = (datetime.now(ZoneInfo("Asia/Shanghai"))-source_at).total_seconds()/60
        if not 0 <= age <= config["source"]["freshness_max_age_minutes"]:
            raise ValueError("Internal-books source snapshot is stale")
        result["snapshot"] = list(snapshot)
    return result
