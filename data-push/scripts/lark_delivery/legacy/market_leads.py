"""Legacy consultant-quartile lead aggregation; not the current manager report."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from fractions import Fraction
from typing import Any, Mapping, Sequence
from ..common.records import numeric, text, value

SECTIONS = {"process": ("过程数据",), "result": ("结果数据",), "both": ("过程数据", "结果数据")}
CONFIG_FIELDS = (
    "配置名称", "渠道", "推送类型", "推送标题", "推送期次", "推送说明",
    "接收群",
)
DIMENSION_FIELDS = ("lead_id", "期次", "渠道", "经理", "主管", "部门", "顾问", "顾问账号", "分区日期", "分区小时")
COUNTERS = {
    "退前线索": "退前线索", "退后线索": "退后线索", "总通时秒": "总通时秒",
    "外呼次数": "外呼次数", "首call完成数": "首call完成标记",
    "48h外呼数": "48h外呼标记", "5min线索数": "5min标记",
    "好友线索数": "好友标记", "APP登陆线索数": "APP登陆标记",
    "深沟线索数": "深沟标记", "双沟线索数": "双沟标记",
}
RESULT_COUNTERS = {
    "首节到课线索数": "首节到课标记", "报科数": "报科数", "成交人头": "成交人头",
    "当期净收款": "当期净收款", "净收款": "净收款", "收款": "收款", "退费": "退费",
}
OPTIONAL_COUNTERS = {f"{hour}h外呼数": f"{hour}h外呼标记" for hour in (6, 12, 24)}
RATES = {
    "线索留存率": ("退后线索", "退前线索"),
    "首call率": ("首call完成数", "退后线索"), "48h外呼": ("48h外呼数", "退后线索"),
    "5min": ("5min线索数", "退后线索"), "好友率": ("好友线索数", "退后线索"),
    "APP登陆率": ("APP登陆线索数", "退后线索"), "深沟率": ("深沟线索数", "退后线索"),
    "双沟率": ("双沟线索数", "退后线索"),
    "首节到课率": ("首节到课线索数", "退后线索"),
    "人头转化": ("成交人头", "退后线索"), "订单转化": ("报科数", "退后线索"),
    "退费率": ("退费", "收款"),
    **{f"{hour}h外呼": (f"{hour}h外呼数", "退后线索") for hour in (6, 12, 24)},
}


def projection(field_names: set[str], report_type: str) -> tuple[list[str], dict[str, str]]:
    counters = dict(COUNTERS)
    if report_type != "process":
        counters.update(RESULT_COUNTERS)
    missing = sorted(set(DIMENSION_FIELDS + tuple(counters.values())) - field_names)
    if missing:
        raise ValueError("原始表缺少必要字段：" + "、".join(missing))
    counters.update({out: source for out, source in OPTIONAL_COUNTERS.items() if source in field_names})
    return list(DIMENSION_FIELDS) + list(counters.values()), counters


def select_configs(records: Sequence[Mapping[str, Any]], channel: str, report_type: str, period: str) -> dict[str, dict[str, Any]]:
    selected = {}
    for section in SECTIONS[report_type]:
        candidates = [r for r in records if text(value(r, "渠道")) == channel and text(value(r, "推送类型")) == section]
        if period:
            exact = [r for r in candidates if text(value(r, "推送期次")) == period]
            if exact:
                candidates = exact
        if len(candidates) > 1:
            raise ValueError(f"渠道 {channel} 的{section}存在多条配置，请在配置视图中明确唯一记录")
        if candidates:
            row = candidates[0]
            selected[section] = {"record_id": row.get("record_id", ""), "fields": dict(row.get("fields", row))}
        else:
            selected[section] = {"record_id": "", "fields": {
                "推送标题": f"【{channel}】{section}播报", "推送类型": section, "渠道": [channel],
                "推送期次": period, "推送说明": "", "接收群": [],
            }}
    return selected


def requested_period(configs: Mapping[str, Mapping[str, Any]], explicit: str) -> str:
    if explicit:
        return explicit
    periods = {text(value(r, "推送期次")) for r in configs.values()} - {""}
    if len(periods) > 1:
        raise ValueError("所选过程/结果配置的期次不一致，请指定 --period")
    return next(iter(periods), "")


def validate_scope(records: Sequence[Mapping[str, Any]], channel: str, requested: str) -> tuple[list[Mapping[str, Any]], str, list[str]]:
    scoped = [r for r in records if channel == "全部渠道" or text(value(r, "渠道")) == channel]
    periods = {text(value(r, "期次")) for r in scoped}
    if not requested:
        if len(periods) != 1 or "" in periods:
            raise ValueError("所选渠道包含多个期次或无数据，请用 --period 指定")
        requested = next(iter(periods))
    scoped = [r for r in scoped if text(value(r, "期次")) == requested]
    if not scoped:
        raise ValueError(f"渠道 {channel} 在 {requested} 没有线索数据")
    seen = set()
    snapshots = set()
    for row in scoped:
        for field in DIMENSION_FIELDS:
            if not text(value(row, field)):
                raise ValueError(f"线索缺少 {field}，请检查源数据")
        key = (requested, text(value(row, "lead_id")))
        if key in seen:
            raise ValueError("所选数据存在重复的期次 + lead_id，停止汇总以避免重复计数")
        seen.add(key)
        snapshots.add((text(value(row, "分区日期")), text(value(row, "分区小时"))))
    if len(snapshots) != 1:
        raise ValueError("所选线索属于不同数据分区，可能正在全量刷新，请稍后重新读取")
    snapshot = next(iter(snapshots))
    return scoped, requested, list(snapshot)


def metrics(sums: Mapping[str, Decimal]) -> dict[str, Any]:
    result: dict[str, Any] = {k: float(v) for k, v in sums.items()}
    for field, (num, den) in RATES.items():
        if num in sums and den in sums:
            result[field] = f"{sums[num] / sums[den] * 100:.8f}%" if sums[den] else "-"
    result["总通时"] = float(sums["总通时秒"] / 60)
    for field, num, den in (
        ("外呼频次", "外呼次数", "退后线索"),
        ("单效", "净收款", "退后线索"), ("单效（当期）", "当期净收款", "退后线索"),
        ("人均报科", "报科数", "成交人头"),
    ):
        if num in sums and den in sums:
            result[field] = float(sums[num] / sums[den]) if sums[den] else 0.0
    return result


def build_report(records: Sequence[Mapping[str, Any]], counters: Mapping[str, str], period: str) -> dict[str, Any]:
    teams: dict[tuple[str, ...], dict[str, Decimal]] = {}
    channels: set[str] = set()
    consultants: dict[tuple[str, str, str], dict[str, Any]] = {}
    grand = {field: Decimal(0) for field in counters}
    labels: dict[tuple[str, ...], set[str]] = defaultdict(set)
    for row in records:
        amounts = {out: numeric(value(row, source), source) for out, source in counters.items()}
        channel = text(value(row, "渠道"))
        team_key = (channel, text(value(row, "经理")), text(value(row, "主管")))
        supervisor = text(value(row, "主管"))
        name = text(value(row, "顾问"))
        # Match the Base helper's channel|supervisor|consultant dimensions;
        # retain the account internally to detect ambiguous same-name people.
        person_key = (channel, supervisor, text(value(row, "顾问账号")))
        team = teams.setdefault(team_key, {field: Decimal(0) for field in counters})
        channels.add(channel)
        person = consultants.setdefault(person_key, {"name": name, "supervisor": supervisor, "dimension_key": f"{channel}|{supervisor}|{name}",
                                                     "sums": {field: Decimal(0) for field in counters}})
        if person["name"] != text(value(row, "顾问")):
            raise ValueError("同一顾问账号对应多个姓名，无法可靠生成提醒")
        labels[team_key].add(text(value(row, "部门")))
        for field, amount in amounts.items():
            team[field] += amount
            person["sums"][field] += amount
            grand[field] += amount
    rows = []
    for (channel, manager, supervisor), sums in sorted(teams.items()):
        if not any(sums.values()):
            continue
        fields = metrics(sums)
        fields.update({"期次": period, "渠道": channel, "经理": manager, "主管": supervisor,
                       "顾问": manager, "部门": "、".join(sorted(labels[(channel, manager, supervisor)]))})
        rows.append({"record_id": "", "fields": fields})
    if not rows:
        raise ValueError("所选渠道的线索和指标均为零，仅有占位记录，本次不生成推送")
    reminders: dict[str, set[str]] = {section: set() for section in SECTIONS["both"]}
    reminder_supervisors: dict[str, set[str]] = {section: set() for section in SECTIONS["both"]}
    name_accounts: dict[str, set[str]] = defaultdict(set)
    for (_channel, _supervisor, account), person in consultants.items():
        name_accounts[person["name"]].add(account)
    quotas = {}
    for channel in sorted(channels):
        eligible = [person for (ch, _supervisor, _account), person in consultants.items()
                    if ch == channel and person["sums"]["退后线索"] > 0]
        quota = (len(eligible) + 3) // 4
        quotas[channel] = {"eligible_count": len(eligible), "quota": quota}
        for section, numerator in (("过程数据", "5min线索数"), ("结果数据", "净收款")):
            if numerator not in counters:
                continue
            ranked = sorted(eligible, key=lambda person: (
                Fraction(person["sums"][numerator]) / Fraction(person["sums"]["退后线索"]),
                person["dimension_key"],
            ))
            reminders[section].update(person["name"] for person in ranked[:quota])
            reminder_supervisors[section].update(person["supervisor"] for person in ranked[:quota])
    reminded = set().union(*reminders.values())
    ambiguous = sorted(name for name in reminded if len(name_accounts[name]) > 1)
    if ambiguous:
        raise ValueError("提醒存在同名不同账号的顾问，需人工消歧：" + "、".join(ambiguous))
    return {"rows": rows, "totals": metrics(grand), "reminders": {k: sorted(v) for k, v in reminders.items()},
            "reminder_supervisors": {k: sorted(v) for k, v in reminder_supervisors.items()},
            "channels": sorted(channels), "consultant_count": len(consultants), "reminder_quotas": quotas}


def configured_chat(configs: Mapping[str, Mapping[str, Any]], explicit: str) -> str:
    targets = []
    for row in configs.values():
        groups = value(row, "接收群") or []
        ids = {text(g.get("id")) for g in groups if isinstance(g, Mapping) and text(g.get("id"))}
        targets.append(ids)
    if explicit:
        if any(ids and explicit not in ids for ids in targets):
            raise ValueError("指定群与所选配置的接收群不一致，请选择匹配的配置")
        return explicit
    if not any(targets):
        return ""
    if any(not ids for ids in targets):
        raise ValueError("部分所选配置未设置接收群，请明确 --chat-id")
    common = set.intersection(*targets)
    if len(common) != 1:
        raise ValueError("所选配置对应多个或不同群，请用 --chat-id 明确本次目标")
    return next(iter(common))


def text_sections(configs: Mapping[str, Mapping[str, Any]], report: Mapping[str, Any], period: str, channel: str, snapshot: list[str]) -> dict[str, dict[str, Any]]:
    result = {}
    date, hour = snapshot
    stamp = f"{date[:4]}-{date[4:6]}-{date[6:8]} {int(hour):02d}:00（Asia/Shanghai）"
    for section, row in configs.items():
        fields = dict(row["fields"])
        names = report["reminders"][section]
        fields.update({"说明": section, "推送期次": period, "计算_提醒顾问": "、".join(names)})
        metric = "5min率" if section == "过程数据" else "单效"
        fields["提醒"] = f"本次{metric}较低顾问：" + ("、".join(names) or "无")
        # The Base templates contain a static '2小时前'; the actual partition
        # is more precise and is shared by both pictures and reminders.
        explanation = [line for line in text(fields.get("推送说明")).splitlines()
                       if not line.lstrip().startswith(("渠道：", "数据截止：", "数据分区：", "提醒规则：", "提醒规则:"))]
        totals = report["totals"]
        summary = f"退前线索：{totals['退前线索']:g}｜退后线索：{totals['退后线索']:g}"
        if section == "过程数据":
            rate = totals["5min"]
            summary += "｜5min率：" + (f"{float(rate[:-1]):.2f}%" if rate.endswith("%") else rate)
        else:
            summary += f"｜净收款：{totals['净收款']:.2f}｜单效：{totals['单效']:.2f}"
        fields["推送说明"] = "\n".join([f"渠道：{channel}", f"数据分区：{stamp}", *explanation, summary])
        result[section] = {"record_id": row.get("record_id", ""), "fields": fields}
    return result
