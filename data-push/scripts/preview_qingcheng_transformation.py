"""Build local-only Qingcheng transformation previews from process + conversion Base exports.

The conversion table (tbl9CcVtXPntqGvP, written by qing2lark_zhuanhua) holds one row
per in-period lead with user-level 0/1 conversion markers; valid leads, headcount and
first-lesson attendance come from the process table so denominators stay identical to
the process report. Metric formulas follow the Qingcheng 2460 conversion dashboard
front-end definitions (consistent with the market-consultant department):
综合单效 = promit(净收款)/有效线索, 当期单效 = p_income(当期收款)/有效线索,
综合订单转化率 = pay_sub(报科数)/有效线索, 联报率 = pay_sub/pay_user,
破蛋率 = podan/有效线索, 人效 = promit/带班人数, 平均成交周期 = sc/pay_user.
This script performs no network calls, registration, upload, scheduling, or
message sending.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from preview_qingcheng_public_pool_process import (
    _ratio,
    _table_image,
)

SKILL = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = SKILL / "config" / "departments" / "qingcheng" / "transformation_preview.json"

CONVERSION_SOURCES = frozenset({"conversion_fact", "conversion_finance_only"})
GRADES = ("高一", "高二", "高三", "初三")

RATIO_FIELDS = frozenset({"首节到课率", "综合人头转化率", "综合订单转化率", "破蛋率"})
INTEGER_FIELDS = frozenset({"带班人数", "有效线索", "综合营收", "退费金额", "净收款"})
# 联报率 = sum(报科数)/sum(成交人头) 即人均科次，按用户要求以一位小数数值显示（如 1.2、2.0），不使用百分比。
DECIMAL_FIELDS = frozenset({"当期单效", "综合单效", "人效", "平均成交周期", "联报率"})

REMINDER_METRIC = "综合单效"
CONSULTANT_TOP_N = 3
PRAISE_SUFFIX = " 🎉🎉🎉"  # 表扬行末尾的三个鼓励符号（用户指定）
FALLBACK_REMINDER = f"本期暂无{REMINDER_METRIC}可比数据，大家加油呀💪💪💪"  # 全部为 0 时的兜底文案（用户指定）


def _read_rows(path: Path) -> tuple[list[dict], dict]:
    manifest = json.loads(path.with_name(f"{path.stem}.manifest.json").read_text(encoding="utf-8"))
    if manifest.get("has_more") is not False or manifest.get("records_count") is None:
        raise ValueError(f"{path.name}: Base export is incomplete")
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    if len(rows) != manifest["records_count"]:
        raise ValueError(f"{path.name}: export count differs from manifest")
    if len({row.get("record_id") for row in rows}) != len(rows):
        raise ValueError(f"{path.name}: duplicate or missing Base record IDs")
    return rows, manifest


def _number(row: dict, field: str) -> float:
    value = row.get(field)
    if value is None:
        raise ValueError(f"Missing numeric source field: {field}")
    return float(value)


def _validate_channel(rows: list[dict], allowed: set[str], *, table: str) -> None:
    bad = {row.get("一级渠道") for row in rows} - allowed
    if bad:
        raise ValueError(f"{table}: export contains unexpected 一级渠道 values {sorted(map(str, bad))}")


def _source_of(row: dict) -> str:
    parts = str(row.get("记录键", "")).split("|")
    if len(parts) != 6 or parts[1] not in CONVERSION_SOURCES:
        raise ValueError(f"Unexpected conversion record key: {row.get('记录键')!r}")
    return parts[1]


def _group_key(row: dict, level: str, *, split_grade: bool) -> tuple:
    if level == "学部":
        # 学部级按 负责人(经理)×年级 聚合（Base 申请记录数据维度：期次、渠道、负责人、年级）。
        return (row["期次"], row["经理"], row["年级"])
    if level == "主管":
        return (row["期次"], row["主管"], row["年级"]) if split_grade else (row["期次"], row["主管"])
    return (row["期次"], row["主管"], row["顾问账号"], row["年级"])


def _split_grade_for(channel_cfg: dict, slug: str) -> bool:
    """split_grade may be a bool (both levels) or a per-level mapping.

    本地化：主管维度按年级分块（true），顾问维度不分块（false）。
    """
    value = channel_cfg["split_grade"]
    if isinstance(value, bool):
        return value
    return bool(value[slug])


def _rows_in_scope(rows: list[dict], level: str) -> list[dict]:
    """Level-specific row validity filter shared by both aggregation passes."""
    if level == "学部":
        return [row for row in rows
                if row.get("年级") in GRADES and row.get("经理") not in (None, "", "未分配经理")]
    return [row for row in rows
            if row.get("年级") in GRADES and row.get("主管") not in (None, "", "未分配主管")]


def _aggregate(process_rows: list[dict], conversion_rows: list[dict], level: str, request: dict,
               channel_cfg: dict, *, period: str) -> list[dict]:
    if level == "学部":
        split_grade = True  # 学部级恒按年级分块（数据维度含年级）
    else:
        split_grade = _split_grade_for(channel_cfg, "supervisor" if level == "主管" else "consultant")
    minimum = float(request["report"]["minimum"]["value"])
    process_rows = _rows_in_scope(process_rows, level)
    conversion_rows = _rows_in_scope(conversion_rows, level)
    process_groups: dict[tuple, list[dict]] = defaultdict(list)
    for row in process_rows:
        process_groups[_group_key(row, level, split_grade=split_grade)].append(row)

    conversion_groups: dict[tuple, list[dict]] = defaultdict(list)
    for row in conversion_rows:
        _source_of(row)
        conversion_groups[_group_key(row, level, split_grade=split_grade)].append(row)

    output = []
    for key, items in sorted(process_groups.items()):
        leads = sum(_number(item, "退后线索") for item in items)
        if leads < minimum:
            continue
        if level == "顾问" and len({item["顾问"] for item in items}) != 1:
            raise ValueError(f"One consultant account has conflicting names: {key}")
        conversion_items = conversion_groups.get(key, [])
        heads = sum(_number(item, "成交人头") for item in conversion_items)
        income = sum(_number(item, "收款") for item in conversion_items)
        net = sum(_number(item, "净收款") for item in conversion_items)
        period_income = sum(_number(item, "当期收款") for item in conversion_items)
        subjects = sum(_number(item, "报科数") for item in conversion_items)
        accounts = frozenset(item["顾问账号"] for item in items)
        # 指标口径对齐青橙 2460 转化看板前端公式（与市场顾问部定义一致）：
        # 综合人头转化率=pay_user/线索、综合订单转化率=pay_sub(报科数)/线索、
        # 当期单效=p_income(当期收款)/线索、综合单效=promit(净收款)/线索、
        # 人效=promit/带班人数、联报率=pay_sub/pay_user、破蛋率=podan/线索、
        # 平均成交周期=sc/pay_user（分母字段与成交人头标记等价）。
        metrics = {
            "有效线索": leads,
            "带班人数": len(accounts),
            "首节到课率": _ratio(sum(_number(item, "首节到课标记") for item in items), leads),
            "成交人头_分子": heads,
            "综合人头转化率": _ratio(heads, leads),
            "综合订单转化率": _ratio(subjects, leads),
            "综合营收": income,
            "退费金额": sum(_number(item, "退费") for item in conversion_items),
            "净收款": net,
            "当期单效": _ratio(period_income, leads),
            "综合单效": _ratio(net, leads),
            "人效": _ratio(net, len(accounts)) if accounts else None,
            "联报率": _ratio(subjects, heads),
            "破蛋率": _ratio(sum(_number(item, "破蛋人数标记") for item in conversion_items), leads),
            "平均成交周期": _ratio(sum(_number(item, "成交周期天数分子") for item in conversion_items),
                                  sum(_number(item, "成交周期成交人数分母") for item in conversion_items)),
        }
        if level == "学部":
            name, grade = key[1], key[2]
        elif level == "主管":
            name, grade = key[1], (key[2] if split_grade else None)
        else:
            name, grade = None, key[3]
        output.append({
            "key": key,
            # key[1] 是主管名（主管/顾问维度分组键共享），学部维度 key[1]=经理、
            # 无主管语义故置 None。2026-10-03 修复：此前误将顾问维度的主管列清空。
            "主管": None if level == "学部" else key[1],
            "负责人": name if level == "学部" else None,
            "顾问": items[0]["顾问"] if level == "顾问" else None,
            "顾问账号": key[2] if level == "顾问" else None,
            "年级": grade,
            "metrics": metrics,
            "_accounts": accounts,
        })
    return output


def _sort_key_value(metrics: dict) -> float:
    value = metrics.get(REMINDER_METRIC)
    if value is None:
        return float("-inf")
    return float(value)


def _sort_rows(rows: list[dict], *, split_grade: bool, level: str = "主管") -> list[dict]:
    grade_order = {name: index for index, name in enumerate(GRADES)}
    if level == "学部":
        return sorted(rows, key=lambda item: (
            grade_order.get(item["年级"], 99),
            -_sort_key_value(item["metrics"]),
            item["负责人"] or "",
        ))
    return sorted(rows, key=lambda item: (
        grade_order.get(item["年级"], 99) if split_grade else 0,
        -_sort_key_value(item["metrics"]),
        item["主管"],
        item["顾问账号"] or "",
        item["年级"] or "",
    ))


def _display_transformation(value: float | None, field: str, *, integer_fields: frozenset[str] = frozenset()) -> str:
    if value is None:
        return "—"
    if field in RATIO_FIELDS:
        return f"{value:.1%}"
    if field in INTEGER_FIELDS | integer_fields:
        return f"{value:,.0f}"
    if field in DECIMAL_FIELDS:
        return f"{value:,.1f}"
    raise ValueError(f"Transformation display rule missing for field: {field}")


def _total_transformation(rows: list[dict]) -> dict:
    """Recalculate ratios from displayed detail, including distinct headcount."""
    leads = sum(row["metrics"]["有效线索"] for row in rows)
    if not leads:
        raise ValueError("Cannot total an empty report block")
    heads = sum(row["metrics"]["成交人头_分子"] for row in rows)
    subjects = sum(row.get("_subjects", 0.0) for row in rows)
    period_income = sum(row.get("_period_income", 0.0) for row in rows)
    net = sum(row["metrics"]["净收款"] for row in rows)
    income = sum(row["metrics"]["综合营收"] for row in rows)
    accounts = set().union(*(row["_accounts"] for row in rows))
    cycle_num = sum(row.get("_cycle_num", 0.0) for row in rows)
    cycle_den = sum(row.get("_cycle_den", 0.0) for row in rows)
    first_lesson = sum(row.get("_first_lesson", 0.0) for row in rows)
    podan = sum(row.get("_podan", 0.0) for row in rows)
    metrics = {
        "有效线索": leads,
        "带班人数": len(accounts),
        "首节到课率": _ratio(first_lesson, leads),
        "成交人头_分子": heads,
        "综合人头转化率": _ratio(heads, leads),
        "综合订单转化率": _ratio(subjects, leads),
        "综合营收": income,
        "退费金额": sum(row["metrics"]["退费金额"] for row in rows),
        "净收款": net,
        "当期单效": _ratio(period_income, leads),
        "综合单效": _ratio(net, leads),
        "人效": _ratio(net, len(accounts)),
        "联报率": _ratio(subjects, heads),
        "破蛋率": _ratio(podan, leads),
        "平均成交周期": _ratio(cycle_num, cycle_den),
    }
    return {"is_total": True, "metrics": metrics}


def _aggregate_with_extras(process_rows: list[dict], conversion_rows: list[dict], level: str, request: dict,
                           channel_cfg: dict, *, period: str) -> list[dict]:
    """Same as _aggregate but keeps raw numerators/denominators for the total row."""
    rows = _aggregate(process_rows, conversion_rows, level, request, channel_cfg, period=period)
    if level == "学部":
        split_grade = True
    else:
        split_grade = _split_grade_for(channel_cfg, "supervisor" if level == "主管" else "consultant")
    process_rows = _rows_in_scope(process_rows, level)
    conversion_rows = _rows_in_scope(conversion_rows, level)
    process_groups: dict[tuple, list[dict]] = defaultdict(list)
    for row in process_rows:
        process_groups[_group_key(row, level, split_grade=split_grade)].append(row)
    conversion_groups: dict[tuple, list[dict]] = defaultdict(list)
    for row in conversion_rows:
        conversion_groups[_group_key(row, level, split_grade=split_grade)].append(row)
    for out in rows:
        items = process_groups[out["key"]]
        conversion_items = conversion_groups.get(out["key"], [])
        out["_first_lesson"] = sum(_number(item, "首节到课标记") for item in items)
        out["_period_income"] = sum(_number(item, "当期收款") for item in conversion_items)
        out["_subjects"] = sum(_number(item, "报科数") for item in conversion_items)
        out["_podan"] = sum(_number(item, "破蛋人数标记") for item in conversion_items)
        out["_cycle_num"] = sum(_number(item, "成交周期天数分子") for item in conversion_items)
        out["_cycle_den"] = sum(_number(item, "成交周期成交人数分母") for item in conversion_items)
    return rows


def _reminder_supervisor(rows: list[dict]) -> list[dict]:
    eligible = [row for row in rows if row["metrics"].get(REMINDER_METRIC) is not None
                and row["metrics"][REMINDER_METRIC] > 0]
    if not eligible:
        return []
    best = max(row["metrics"][REMINDER_METRIC] for row in eligible)
    tied = sorted((row for row in eligible if row["metrics"][REMINDER_METRIC] == best),
                  key=lambda row: (row["主管"], row["顾问账号"] or "", row["年级"] or ""))
    people = {}
    for row in tied:
        people.setdefault(row["主管"], {"name": row["主管"], "account": None})
    return list(people.values())


def _reminder_grades(rows: list[dict]) -> list[str]:
    """本地化主管提醒：不 @ 主管，按年级点名综合单效表现。

    对齐过程推送 supervisor_local 的『8min较低年级』样式：按年级聚合
    综合单效（sum(净收款)/sum(有效线索)），列出值最高（并列全列）的年级。
    """
    by_grade: dict[str, list[dict]] = {}
    for row in rows:
        if row.get("年级"):
            by_grade.setdefault(row["年级"], []).append(row)
    score = {}
    for grade, grade_rows in by_grade.items():
        leads = sum(row["metrics"]["有效线索"] for row in grade_rows)
        net = sum(row["metrics"]["净收款"] for row in grade_rows)
        if leads > 0 and net / leads > 0:
            score[grade] = net / leads
    if not score:
        return []
    best = max(score.values())
    return [grade for grade in GRADES if score.get(grade) == best]


def _reminder_consultant_by_grade(rows: list[dict]) -> dict[str, list[dict]]:
    present = {row["年级"] for row in rows if row["年级"]}
    result = {}
    for grade in [g for g in GRADES if g in present] + sorted(present - set(GRADES)):
        grade_rows = [row for row in rows if row["年级"] == grade]
        eligible = [row for row in grade_rows if row["metrics"].get(REMINDER_METRIC) is not None
                    and row["metrics"][REMINDER_METRIC] > 0]
        if not eligible:
            continue
        eligible.sort(key=lambda row: (-row["metrics"][REMINDER_METRIC], row["主管"], row["顾问账号"] or ""))
        if len(eligible) > CONSULTANT_TOP_N:
            cutoff = eligible[CONSULTANT_TOP_N - 1]["metrics"][REMINDER_METRIC]
            selected = [row for row in eligible if row["metrics"][REMINDER_METRIC] >= cutoff]
        else:
            selected = eligible
        people = {}
        for row in selected:
            people.setdefault(row["顾问账号"], {"name": row["顾问"], "account": row["顾问账号"]})
        result[grade] = list(people.values())
    return result


def _message(level: str, period: str, channel: str, image_name: str, reminders: list[str]) -> str:
    return "\n".join([
        f"## 🔥 **【{period}】{channel}渠道{level}转化数据播报**",
        "",
        f"![{level}维度转化数据]({image_name})",
        "",
        *reminders,
    ])


def _join_coverage(process_channel: list[dict], conversion_channel: list[dict], *, split_grade: bool) -> dict:
    """Quantify conversion rows excluded by the group-key join at both levels.

    Rows orphaned by the group key (typically conversion_finance_only rows whose
    顾问账号 is 未分配账号) carry conversions the report cannot attribute; report
    them instead of dropping them without a trace. Supervisor-level keys ignore
    顾问账号, so a row can join at supervisor level yet stay orphaned at
    consultant level — that difference is exactly the unattributable part.
    """
    valid = lambda r: (r.get("年级") in GRADES and r.get("主管") not in (None, "", "未分配主管"))
    conv_valid = [r for r in conversion_channel if valid(r)]
    proc_ok = [r for r in process_channel if valid(r)]

    def level_stats(proc_key_set: set, conv_key_fn) -> dict:
        heads = lambda rows: sum(float(r.get("成交人头") or 0) for r in rows)
        income = lambda rows: sum(float(r.get("收款") or 0) for r in rows)
        orphans = [r for r in conv_valid if conv_key_fn(r) not in proc_key_set]
        return {
            "orphans": len(orphans),
            "orphan_heads": heads(orphans),
            "orphan_income": income(orphans),
            "joined_heads": heads(conv_valid) - heads(orphans),
            "joined_income": income(conv_valid) - income(orphans),
        }

    if split_grade:
        sup_keys = {(r.get("期次"), r.get("主管"), r.get("年级")) for r in proc_ok}
        sup_fn = lambda r: (r.get("期次"), r.get("主管"), r.get("年级"))
    else:
        sup_keys = {(r.get("期次"), r.get("主管")) for r in proc_ok}
        sup_fn = lambda r: (r.get("期次"), r.get("主管"))
    con_keys = {(r.get("期次"), r.get("主管"), r.get("顾问账号"), r.get("年级")) for r in proc_ok}
    con_fn = lambda r: (r.get("期次"), r.get("主管"), r.get("顾问账号"), r.get("年级"))
    return {
        "conversion_rows_after_filters": len(conv_valid),
        "supervisor_level": level_stats(sup_keys, sup_fn),
        "consultant_level": level_stats(con_keys, con_fn),
    }


def build(process_source: Path, conversion_source: Path, output: Path,
          config_path: Path = DEFAULT_CONFIG, channels: tuple[str, ...] | None = None) -> dict:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config["domain"] != "qingcheng" or config["report_type"] != "transformation":
        raise ValueError("Transformation config has unexpected scope")
    if (config["status"], config["schedule_enabled"]) not in (("preview_only", False), ("active", True)):
        raise ValueError("Config must be preview_only/unscheduled or active/scheduled")
    period = config["source"]["current_periods"][0]

    process_all, process_manifest = _read_rows(process_source)
    conversion_all, conversion_manifest = _read_rows(conversion_source)
    # Match is per-channel below; validate snapshot coherence first. 2026-10-02:
    # an empty conversion export is allowed (always-send policy) — the report
    # renders all-zero metrics and the fallback line flags it in the message.
    process_dt = {f"{r['分区日期']} {r['分区小时']}:00" for r in process_all}
    conversion_dt = {f"{r['分区日期']} {r['分区小时']}:00" for r in conversion_all}
    if len(process_dt) != 1 or (conversion_all and len(conversion_dt) != 1):
        raise ValueError("Source rows span multiple warehouse snapshots")

    requested = channels or tuple(channel["id"] for channel in config["channels"])
    unknown = set(requested) - {channel["id"] for channel in config["channels"]}
    if unknown:
        raise ValueError(f"Unknown channels: {sorted(unknown)}")
    allowed_channels = {cfg["match"]["一级渠道"] for cfg in config["channels"] if cfg["id"] in requested}
    _validate_channel(process_all, allowed_channels, table="process")
    _validate_channel(conversion_all, allowed_channels, table="conversion")

    results = {}
    for channel_cfg in config["channels"]:
        if channel_cfg["id"] not in requested:
            continue
        match = channel_cfg["match"]
        process_channel = [row for row in process_all
                           if row.get("期次") == period and all(row.get(k) == v for k, v in match.items())]
        conversion_channel = [row for row in conversion_all
                              if row.get("期次") == period and all(row.get(k) == v for k, v in match.items())]
        if not conversion_channel and channel_cfg["id"] != "public_pool" and not channel_cfg.get("allow_empty_conversion"):
            # 2026-10-02 always-send policy: channels listed with allow_empty_conversion
            # render an all-zero report + fallback flag instead of failing the batch.
            raise ValueError(f"{channel_cfg['id']}: no conversion rows for period {period}")
        channel_results = {}
        for slug in ("supervisor", "consultant", "dept"):
            if f"{slug}_request" not in channel_cfg:
                continue  # 渠道可只配置部分维度（图书无主管申请；学部级仅四渠道配置）
            level = {"supervisor": "主管", "consultant": "顾问", "dept": "学部"}[slug]
            request_path = SKILL / "config" / "departments" / "qingcheng" / channel_cfg[f"{slug}_request"]
            request = json.loads(request_path.read_text(encoding="utf-8"))
            profile = channel_cfg["profiles"][slug]
            if (request["reminder"]["report_level"] != level
                    or request["business"]["channel_name"] != channel_cfg["name"]
                    or profile["level"] != level):
                raise ValueError(f"{channel_cfg['id']}/{slug}: request level or channel mismatch")
            if (profile["minimum_effective_leads"] != request["report"]["minimum"]["value"]
                    or request["reminder"]["result_metric"] != REMINDER_METRIC):
                raise ValueError(f"{channel_cfg['id']}/{slug}: minimum or reminder metric mismatch")
            reminder_mode = profile.get("reminder_mode", "mention")
            if reminder_mode == "grade_text" and request["reminder"]["target"] != "不提醒":
                raise ValueError(f"{channel_cfg['id']}/{slug}: grade_text mode requires 不提醒 target")
            if reminder_mode == "none" and request["reminder"]["target"] != "不提醒":
                raise ValueError(f"{channel_cfg['id']}/{slug}: none mode requires 不提醒 target")
            split_grade = True if level == "学部" else _split_grade_for(channel_cfg, slug)
            rows = _aggregate_with_extras(process_channel, conversion_channel, level, request, channel_cfg, period=period)
            rows = _sort_rows(rows, split_grade=split_grade, level=level)
            columns = [c.strip() for c in request["report"]["result_display_order"].split("、")]
            output.mkdir(parents=True, exist_ok=True)
            png = output / f"{channel_cfg['id']}_{slug}_transformation.png"
            bar_specs = {}
            for field, spec in config["transformation_bars"].items():
                scale = spec.get("scale")
                if scale is None:
                    values = [row["metrics"][field] for row in rows if row["metrics"].get(field) is not None]
                    ceiling = max(values) if values else 1.0
                    scale = (0.0, ceiling if ceiling > 0 else 1.0)
                bar_specs[field] = (*scale, spec["color"])
            _table_image(rows, columns, png, level, period, channel_cfg["name"],
                         split_grade=split_grade, bar_specs=bar_specs,
                         total_fn=_total_transformation, display_fn=_display_transformation)
            if reminder_mode == "none":
                # 学部级：文字抬头 + 图片，不 @ 人、不生成文字提醒（含 fallback）。
                top_people = None
                by_grade = None
                grades = None
                reminders = []
            elif level == "主管":
                if reminder_mode == "grade_text":
                    top_people = None
                    by_grade = None
                    grades = _reminder_grades(rows)
                    reminders = ([f"- {REMINDER_METRIC}较高年级：{'、'.join(grades)}{PRAISE_SUFFIX}"]
                                 if grades else [])
                else:
                    top_people = _reminder_supervisor(rows)
                    by_grade = None
                    grades = None
                    reminders = ([f"- {REMINDER_METRIC}较高的{level}：{'、'.join(p['name'] for p in top_people)}{PRAISE_SUFFIX}"]
                                 if top_people else [])
            else:
                top_people = None
                grades = None
                by_grade = _reminder_consultant_by_grade(rows)
                reminders = [f"- {grade}年级{REMINDER_METRIC}较高的{level}：{'、'.join(p['name'] for p in people)}{PRAISE_SUFFIX}"
                             for grade, people in by_grade.items()]
            if not reminders and reminder_mode != "none":
                reminders = [f"- {FALLBACK_REMINDER}"]
            message = _message(level, period, channel_cfg["name"], png.name, reminders)
            message_file = output / f"{channel_cfg['id']}_{slug}_transformation_message.md"
            message_file.write_text(message + "\n", encoding="utf-8")
            channel_results[slug] = {
                "level": level,
                "rows": len(rows),
                "reminder_mode": reminder_mode,
                "reminder_people": top_people,
                "reminder_by_grade": by_grade,
                "reminder_grades": grades,
                "reminders": reminders,
                "png": png.name,
                "message_file": message_file.name,
                "message": message,
            }
        results[channel_cfg["id"]] = {
            "channel": channel_cfg["name"],
            "process_rows": len(process_channel),
            "conversion_rows": len(conversion_channel),
            "join_coverage": _join_coverage(process_channel, conversion_channel,
                                            split_grade=_split_grade_for(channel_cfg, "supervisor")),
            "levels": channel_results,
        }

    review = {
        "status": "preview_only",
        "period": period,
        "process_snapshot": sorted(process_dt)[0] if process_dt else None,
        "conversion_snapshot": sorted(conversion_dt)[0] if conversion_dt else None,
        "process_source_rev": process_manifest.get("rev"),
        "conversion_source_rev": conversion_manifest.get("rev"),
        "bars_status": ("draft_dynamic_ceiling_for_" + "_".join(
            field for field, spec in config["transformation_bars"].items() if spec.get("scale") is None)
            if any(spec.get("scale") is None for spec in config["transformation_bars"].values()) else "fixed"),
        "results": results,
    }
    (output / "review.json").write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8")
    return review


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--process-source", type=Path, required=True)
    parser.add_argument("--conversion-source", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--channels", nargs="*", default=None)
    args = parser.parse_args()
    print(json.dumps(build(args.process_source, args.conversion_source, args.output,
                           args.config, tuple(args.channels) if args.channels else None),
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
