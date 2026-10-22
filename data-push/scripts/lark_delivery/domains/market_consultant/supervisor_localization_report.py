"""Province-specific column selection; reuse supervisor calculations and reminders."""
from . import supervisor_report as base

SUPERVISOR_REPORT = True
MENTION_TARGET = "supervisor"
SECTIONS = base.SECTIONS
PROCESS_ORDER = ("期次", "负责人", "主管", "退前线索", "退后线索", "首call率", "48h外呼",
                 "外呼频次", "5min", "好友率", "APP登陆率", "深沟率", "双沟率")
process_columns = {column[0]: column for column in base.COLUMNS["process"]}
process_widths = dict(zip((column[0] for column in base.COLUMNS["process"]), base.WIDTHS["process"]))
COLUMNS = {"process": tuple(process_columns[name] for name in PROCESS_ORDER), "result": base.COLUMNS["result"]}
WIDTHS = {"process": tuple(process_widths[name] for name in PROCESS_ORDER), "result": base.WIDTHS["result"]}
DISPLAY_COLUMNS = {section: [column[1] for column in columns] for section, columns in COLUMNS.items()}
sections = base.sections
projection = base.projection
validate_scope = base.validate_scope
build_report = base.build_report
manager_queries = base.manager_queries
resolve_manager_candidates = base.resolve_manager_candidates
sorted_rows = base.sorted_rows
build_markdown = base.build_markdown
write_preview = base.write_preview


def render_image(report, section, output_path, **kwargs):
    return base.render_image(report, section, output_path, columns=COLUMNS[section], widths=WIDTHS[section],
                             show_totals=False, **kwargs)
