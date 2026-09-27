"""Weekend dual-period report helpers for reviewed market channels."""
from __future__ import annotations

import html
import json
import os
from pathlib import Path
import shutil
from urllib.parse import quote

from .channels.grade_compact import next_business_period


REPORT_TYPE = "result_and_next_process"
SECTION_ORDER = ("result", "process")
SECTION_LABELS = {"result": "转化数据", "process": "过程数据"}


def merge_mention_info(*infos):
    """Merge reminder resolution from the two independently prepared reports."""
    resolved, display_names, ambiguous, nonmembers = {}, {}, {}, set()
    unresolved, lookup_errors = set(), []
    for info in infos:
        for name, open_id in info.get("resolved", {}).items():
            if name in resolved and resolved[name] != open_id:
                raise ValueError("同名提醒对象解析到不同账号：" + name)
            resolved[name] = open_id
        display_names.update(info.get("display_names", {}))
        unresolved.update(info.get("unresolved", ()))
        nonmembers.update(info.get("nonmembers", ()))
        for name, candidates in info.get("ambiguous", {}).items():
            ambiguous[name] = candidates
        if info.get("lookup_error"):
            lookup_errors.append(str(info["lookup_error"]))
    return {
        "names": sorted(set(resolved) | unresolved | set(ambiguous)),
        "resolved": resolved,
        "display_names": display_names,
        "unresolved": sorted(unresolved),
        "ambiguous": ambiguous,
        "lookup_error": "; ".join(dict.fromkeys(lookup_errors)),
        "nonmembers": sorted(nonmembers),
    }


def compose_markdown(context):
    parts = []
    for section in SECTION_ORDER:
        child = context["dual_sections"][section]
        if not child.get("skip_delivery") and child.get("markdown"):
            parts.append(child["markdown"])
    return "\n\n".join(parts)


def write_preview(context, directory):
    """Write one local preview containing current conversion then next process."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    markdown = context["markdown"]
    cards = []
    skipped_notes = []
    image_files = {}
    section_metadata = {}
    for section in SECTION_ORDER:
        child = context["dual_sections"][section]
        path = child.get("result_image_path" if section == "result" else "image_path")
        if path is None:
            minimum = child["grade_report"]["min_post_leads"]
            section_metadata[section] = {
                "period": child["period"], "raw_count": child["raw_count"],
                "minimum_post_leads": minimum,
                "skipped": True, "reason": child.get("skip_reason", ""),
            }
            grain = "顾问" if child.get("mention_target") == "consultant" else "主管"
            skipped_notes.append(
                f'<p>{html.escape(context["channel"])}渠道{html.escape(child["period"])}'
                f'{SECTION_LABELS[section]}：没有{grain}达到退后线索≥{minimum}'
                '的入图门槛，按当前规则跳过；此说明不会发送到群。</p>'
            )
            continue
        path = Path(path)
        preview_path = directory / path.name
        if path.resolve() != preview_path.resolve():
            shutil.copy2(path, preview_path)
        image_files[section] = str(preview_path)
        placeholder = "img_result_preview" if section == "result" else "img_process_preview"
        markdown = markdown.replace(f"]({placeholder})", f"]({preview_path.as_posix()})")
        local = quote(os.path.relpath(preview_path, directory).replace(os.sep, "/"))
        escaped = html.escape(local, quote=True)
        report = child["grade_report"]
        info = child["mention_info"]
        reminders = []
        metric = "单效" if section == "result" else "5min 率"
        for block in report["blocks"]:
            names = block["reminders"].get(section, [])
            if not names:
                continue
            people = []
            for name in names:
                label = html.escape(info.get("display_names", {}).get(name, name))
                if name in info.get("nonmembers", ()):
                    people.append(label + "（未入群，待核验）")
                elif name in info.get("resolved", {}):
                    people.append(f'<span class="mention">@{label}</span>')
                else:
                    people.append(label + "（待核验）")
            reminders.append(
                f"<li>{html.escape(context['channel'])}渠道{html.escape(block['grade'])}年级 "
                f"{metric}较低：{'、'.join(people)}</li>"
            )
        cards.append(
            f'<section><h2>🔥 <strong>【{child["period"]}】'
            f'{html.escape(context["channel"])}渠道{SECTION_LABELS[section]}播报</strong></h2>'
            f'<a href="{escaped}"><img src="{escaped}"></a><ul>'
            f'<li>推送期次：{child["period"]}</li>{"".join(reminders)}</ul></section>'
        )
        section_metadata[section] = {
            "period": child["period"], "raw_count": child["raw_count"],
            "minimum_post_leads": child["grade_report"]["min_post_leads"],
            "raw_read_audit": child["raw_read_audit"],
            "image": str(preview_path), "mention_info": child["mention_info"],
        }
    dt, hour = context["snapshot"]
    document = (
        '<!doctype html><html lang="zh-CN"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width">'
        '<title>飞书群消息预览</title>'
        '<style>body{margin:0;background:#f4f6fa;color:#1f2329;font:16px/1.6 '
        '"Microsoft YaHei",sans-serif}.wrap{max-width:1300px;margin:28px auto;padding:0 20px}'
        '.note{background:#eaf1ff;color:#244c87;border-radius:12px;padding:16px 20px}'
        '.bubble{background:#fff;border:1px solid #e3e7ef;border-radius:14px;padding:22px;margin-top:18px}'
        'h2{margin:12px 0}img{width:100%;height:auto;border:1px solid #e3e7ef}'
        '.mention{color:#3370ff;background:#eff4ff;padding:1px 4px}'
        'section+section{border-top:1px solid #ddd;margin-top:24px;padding-top:18px}</style>'
        f'<body><main class="wrap"><h1>{html.escape(context["chat_name"])}</h1>'
        f'<div class="note">仅本地预览：没有发送消息，也不会触发@通知。<br>'
        f'固定群ID：{context["chat_id"]}｜数据分区：{dt} {int(hour):02d}:00<br>'
        f'周末双期顺序：{context["period"]}转化 → '
        f'{context["dual_sections"]["process"]["period"]}过程<br>'
        f'入图门槛：转化≥{context["dual_sections"]["result"]["grade_report"]["min_post_leads"]}条；'
        f'下一期过程≥{context["dual_sections"]["process"]["grade_report"]["min_post_leads"]}条</div>'
        f'<div class="bubble"><b>管家 · 消息样式预览</b>{"".join(cards)}</div>'
        f'{"<div class=note>" + "".join(skipped_notes) + "</div>" if skipped_notes else ""}'
        '</main></body></html>'
    )
    html_path = directory / "message-preview.html"
    markdown_path = directory / "message-preview.md"
    metadata_path = directory / "preview-metadata.json"
    html_path.write_text(document, encoding="utf-8")
    markdown_path.write_text(markdown + "\n", encoding="utf-8")
    metadata = {
        "report_profile": context["report_profile"], "period": context["period"],
        "next_process_period": context["dual_sections"]["process"]["period"],
        "report_type": context["report_type"], "channel": context["channel"],
        "chat_id": context["chat_id"], "chat_name": context["chat_name"],
        "identity": context["identity"], "raw_count": context["raw_count"],
        "raw_read_audit": context["raw_read_audit"], "snapshot": context["snapshot"],
        "mention_info": context["mention_info"], "image_files": image_files,
        "sections": section_metadata, "mode": "preview_only", "message_sent": False,
    }
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"html": str(html_path), "markdown": str(markdown_path), "metadata": str(metadata_path)}
