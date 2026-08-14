"""Pure static analysis for Tiangong2 task source text.

The analyzer never imports or executes remote code. It extracts bounded lexical
evidence so the runtime report can explain what each task appears to do.
"""

from __future__ import annotations

import ast
import re
from collections import Counter
from typing import Any, Iterable
from urllib.parse import urlsplit


SQL_OPERATION_PATTERNS: dict[str, re.Pattern[str]] = {
    "select": re.compile(r"\bselect\b", re.I),
    "insert": re.compile(r"\binsert\s+(?:overwrite\s+table|into)\b", re.I),
    "create_table": re.compile(r"\bcreate\s+(?:external\s+)?table\b", re.I),
    "create_view": re.compile(r"\bcreate\s+(?:or\s+replace\s+)?view\b", re.I),
    "create_database": re.compile(r"\bcreate\s+(?:database|schema)\b", re.I),
    "drop_table": re.compile(r"\bdrop\s+table\b", re.I),
    "drop_database": re.compile(r"\bdrop\s+(?:database|schema)\b", re.I),
    "truncate_table": re.compile(r"\btruncate\s+table\b", re.I),
    "alter_table": re.compile(r"\balter\s+table\b", re.I),
    "delete": re.compile(r"\bdelete\s+from\b", re.I),
    "update": re.compile(r"\bupdate\s+[A-Za-z_`]", re.I),
    "merge": re.compile(r"\bmerge\s+into\b", re.I),
}

IDENTIFIER = r"[`\"']?([A-Za-z_][A-Za-z0-9_$-]*(?:\.[A-Za-z_][A-Za-z0-9_$-]*){1,2})[`\"']?"
READ_TABLE = re.compile(rf"\b(?:from|join)\s+{IDENTIFIER}", re.I)
WRITE_TABLE = re.compile(rf"\b(?:insert\s+(?:overwrite\s+table|into)|merge\s+into|update)\s+{IDENTIFIER}", re.I)
CREATE_TABLE = re.compile(rf"\bcreate\s+(?:external\s+)?table\s+(?:if\s+not\s+exists\s+)?{IDENTIFIER}", re.I)
DROP_TABLE = re.compile(rf"\b(?:drop|truncate)\s+table\s+(?:if\s+exists\s+)?{IDENTIFIER}", re.I)
CREATE_DATABASE = re.compile(
    r"\bcreate\s+(?:database|schema)\s+(?:if\s+not\s+exists\s+)?[`\"']?([A-Za-z_][A-Za-z0-9_$-]*)",
    re.I,
)
DROP_DATABASE = re.compile(
    r"\bdrop\s+(?:database|schema)\s+(?:if\s+exists\s+)?[`\"']?([A-Za-z_][A-Za-z0-9_$-]*)",
    re.I,
)
URL_PATTERN = re.compile(r"https?://[^\s\"'<>]+", re.I)
SHELL_COMMAND = re.compile(
    r"(?im)^\s*(?:sudo\s+)?(hive|spark-submit|python(?:3)?|mysql|curl|wget|sh|bash|java|flink|seatunnel[^\s]*)\b"
)


def _unique(values: Iterable[str]) -> list[str]:
    return sorted({value.strip("`\"'") for value in values if value})


def _python_imports(source: str) -> tuple[list[str], str | None]:
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        fallback = re.findall(r"(?m)^\s*(?:from|import)\s+([A-Za-z_][A-Za-z0-9_.]*)", source)
        return _unique(item.split(".", 1)[0] for item in fallback), f"{exc.msg} at line {exc.lineno}"
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".", 1)[0])
    return sorted(imports), None


def _external_hosts(source: str) -> list[str]:
    hosts = []
    for match in URL_PATTERN.finditer(source):
        host = urlsplit(match.group(0).rstrip(".,);]")).hostname
        if host:
            hosts.append(host.lower())
    return _unique(hosts)


def _systems(source: str, imports: list[str], hosts: list[str]) -> list[str]:
    haystack = " ".join([source.lower(), " ".join(imports).lower(), " ".join(hosts).lower()])
    rules = {
        "Hive": ("hive", "gaotu_dw.", "hive_dw."),
        "Spark": ("spark", "pyspark"),
        "Kyuubi": ("kyuubi",),
        "Doris/SelectDB": ("doris", "selectdb", "mysql -h"),
        "SeaTunnel": ("seatunnel",),
        "Feishu/Lark": ("feishu", "lark", "open.feishu.cn", "bitable", "多维表格"),
        "Pandas": ("pandas", "read_sql", "dataframe"),
        "HTTP API": ("requests.", "http://", "https://", "curl "),
        "Excel": ("openpyxl", ".xlsx", "to_excel", "read_excel"),
        "MySQL": ("pymysql", "mysql.connector", "mysql -h"),
    }
    return [name for name, needles in rules.items() if any(needle.lower() in haystack for needle in needles)]


def _workflow_categories(task_name: str, path: list[str], source: str, systems: list[str]) -> list[str]:
    haystack = " ".join([task_name, *path, source[:200_000]]).lower()
    categories: list[str] = []
    rules = [
        ("财务流水与退费", ("refund", "退费", "refund_amount", "cashflow", "流水")),
        ("市场线索与渠道归因", ("mkt", "lead", "channel", "线索", "渠道", "归因")),
        ("语言一对一经营分析", ("语言一对一", "yuyan", "waijiao", "外教", "约课", "续费")),
        ("班级课节与产品维表", ("clazz", "lesson", "inclazz", "product_number", "班级", "课节", "产品")),
        ("直播与投放分析", ("zhibo", "直播", "douyin", "抖音", "cost_yuan", "roi")),
        ("飞书或多维表同步", ("feishu", "lark", "bitable", "多维表格", "open.feishu.cn")),
        ("数仓表构建与同步", ("create table", "insert overwrite", "seatunnel", "dwd_", "dim_", "ads_")),
    ]
    for label, needles in rules:
        if any(needle in haystack for needle in needles):
            categories.append(label)
    if not categories:
        categories.append("通用数据抽取与加工")
    if "Feishu/Lark" in systems and "飞书或多维表同步" not in categories:
        categories.append("飞书或多维表同步")
    return categories


def _primary_workflow(
    task_name: str,
    path: list[str],
    source: str,
    systems: list[str],
) -> str:
    path_text = " ".join([*path, task_name]).lower()
    path_rules = [
        ("语言一对一经营数据", ("语言一对一", "yuyan", "waijiao", "外教")),
        ("班级课节与产品底表", ("clazz", "班级", "课节", "讲义发货", "长期班", "短期班")),
        ("直播投放与经营看板", ("直播间", "zhibo", "douyin", "抖音")),
        ("飞书多维表格调度", ("多维表格数据调度",)),
        ("私域临时经营分析", ("私域", "siyu")),
        ("市场三部临时分析", ("市场三部",)),
        ("市场线索归因与转介绍底表", ("弋广飞", "dwd_mkt", "referral", "线索归因")),
        ("财务退费看板宽表", ("refund", "退费")),
    ]
    for label, needles in path_rules:
        if any(needle in path_text for needle in needles):
            return label
    source_head = source[:200_000].lower()
    if "Feishu/Lark" in systems:
        return "飞书数据抽取与同步"
    if "cashflow" in source_head or "流水" in path_text:
        return "财务流水临时分析"
    if any(token in source_head for token in ("create table", "insert overwrite", "dwd_", "dim_")):
        return "数仓表构建与同步"
    return "通用数据抽取与分析"


def _risk_findings(
    operations: dict[str, int],
    systems: list[str],
    redactions: list[dict[str, Any]],
    source: str,
) -> list[str]:
    findings: list[str] = []
    if redactions:
        findings.append("hardcoded_secret_literal_detected_and_redacted")
    if operations.get("drop_table") or operations.get("truncate_table"):
        findings.append("destructive_table_ddl_present")
    if operations.get("drop_database"):
        findings.append("destructive_database_ddl_present")
    if operations.get("create_table") or operations.get("create_view"):
        findings.append("database_object_creation_present")
    if operations.get("create_database"):
        findings.append("database_or_schema_creation_present")
    if operations.get("insert") or operations.get("merge") or operations.get("update") or operations.get("delete"):
        findings.append("data_write_statement_present")
    if "Feishu/Lark" in systems or re.search(r"(?i)requests\.(?:post|put|patch|delete)\s*\(", source):
        findings.append("external_write_or_message_call_present")
    if SHELL_COMMAND.search(source):
        findings.append("subprocess_or_shell_execution_present")
    return findings


def analyze_source(
    *,
    task_name: str,
    path: list[str],
    task_type_name: str,
    source_kind: str,
    source: str,
    redactions: list[dict[str, Any]],
) -> dict[str, Any]:
    operations = {
        name: len(pattern.findall(source))
        for name, pattern in SQL_OPERATION_PATTERNS.items()
        if pattern.search(source)
    }
    read_tables = _unique(READ_TABLE.findall(source))
    write_tables = _unique(WRITE_TABLE.findall(source))
    created_tables = _unique(CREATE_TABLE.findall(source))
    dropped_tables = _unique(DROP_TABLE.findall(source))
    created_databases = _unique(CREATE_DATABASE.findall(source))
    dropped_databases = _unique(DROP_DATABASE.findall(source))
    imports: list[str] = []
    syntax_note = None
    if source_kind == "python":
        imports, syntax_note = _python_imports(source)
    hosts = _external_hosts(source)
    systems = _systems(source, imports, hosts)
    categories = _workflow_categories(task_name, path, source, systems)
    primary_workflow = _primary_workflow(task_name, path, source, systems)
    shell_commands = sorted(Counter(match.group(1).lower() for match in SHELL_COMMAND.finditer(source)))
    findings = _risk_findings(operations, systems, redactions, source)
    outputs = _unique([*write_tables, *created_tables, *created_databases])
    summary_parts = [f"{task_type_name} task"]
    if read_tables:
        summary_parts.append(f"reads {len(read_tables)} table-like assets")
    if outputs:
        summary_parts.append(f"writes or creates {len(outputs)} assets")
    if systems:
        summary_parts.append("uses " + ", ".join(systems))
    if not read_tables and not outputs and not systems:
        summary_parts.append("contains local transformation or orchestration logic")
    return {
        "summary": "; ".join(summary_parts) + ".",
        "primary_workflow": primary_workflow,
        "workflow_categories": categories,
        "technical_tags": _unique(
            [
                *systems,
                *("表或视图创建" for _ in [0] if operations.get("create_table") or operations.get("create_view")),
                *("数据库或Schema创建" for _ in [0] if operations.get("create_database")),
                *("表删除或重建" for _ in [0] if operations.get("drop_table") or operations.get("truncate_table")),
                *("数据库或Schema删除" for _ in [0] if operations.get("drop_database")),
                *("数据写入" for _ in [0] if any(operations.get(key) for key in ("insert", "merge", "update", "delete"))),
            ]
        ),
        "line_count": len(source.splitlines()),
        "character_count": len(source),
        "python_imports": imports,
        "python_parse_note": syntax_note,
        "sql_operation_counts": operations,
        "read_tables": read_tables,
        "write_tables": write_tables,
        "created_tables": created_tables,
        "dropped_or_truncated_tables": dropped_tables,
        "created_databases_or_schemas": created_databases,
        "dropped_databases_or_schemas": dropped_databases,
        "external_hosts": hosts,
        "systems": systems,
        "shell_commands": shell_commands,
        "risk_findings": findings,
    }
