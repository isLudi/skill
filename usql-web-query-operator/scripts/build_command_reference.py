"""Generate command_reference.md from CLI help plus the capability registry."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_ROOT / "scripts"
REFERENCES_DIR = SKILL_ROOT / "references"
REGISTRY_PATH = REFERENCES_DIR / "command_capabilities.json"
SCHEMA_PATH = REFERENCES_DIR / "command_capabilities.schema.json"
OUTPUT_PATH = REFERENCES_DIR / "command_reference.md"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from read_dashboard.cli import build_parser as build_dashboard_parser  # noqa: E402
from tiangong2_task.cli import build_parser as build_tiangong2_task_parser  # noqa: E402
from usql_web_query.cli import build_parser as build_usql_parser  # noqa: E402


PARSER_BUILDERS = {
    "usql_web_query.py": build_usql_parser,
    "read_dashboard.py": build_dashboard_parser,
    "tiangong2_task.py": build_tiangong2_task_parser,
}


def _command_help(parser: argparse.ArgumentParser) -> dict[str, str]:
    subparsers = next(
        action for action in parser._actions if isinstance(action, argparse._SubParsersAction)
    )
    help_by_name = {
        action.dest: str(action.help or "")
        for action in subparsers._choices_actions
    }
    return {name: help_by_name.get(name, "") for name in subparsers.choices}


def _subparser(parser: argparse.ArgumentParser, command: str) -> argparse.ArgumentParser:
    subparsers = next(
        action for action in parser._actions if isinstance(action, argparse._SubParsersAction)
    )
    return subparsers.choices[command]


def _option_choices(parser: argparse.ArgumentParser, command: str, option: str) -> list[str]:
    command_parser = _subparser(parser, command)
    action = next(
        (item for item in command_parser._actions if option in item.option_strings),
        None,
    )
    if action is None or action.choices is None:
        return []
    return [str(item) for item in action.choices]


def _option_default(parser: argparse.ArgumentParser, command: str, option: str) -> Any:
    command_parser = _subparser(parser, command)
    action = next(
        (item for item in command_parser._actions if option in item.option_strings),
        None,
    )
    return None if action is None else action.default


def load_registry() -> dict[str, Any]:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(registry), key=lambda item: list(item.path))
    if errors:
        rendered = "\n".join(
            f"{'.'.join(map(str, item.path)) or '<root>'}: {item.message}"
            for item in errors
        )
        raise ValueError("Command capability registry schema validation failed:\n" + rendered)
    return registry


def validate_registry(registry: dict[str, Any]) -> dict[str, dict[str, str]]:
    registered_entrypoints = {item["entrypoint"] for item in registry["entrypoints"]}
    if registered_entrypoints != set(PARSER_BUILDERS):
        raise ValueError(
            "Command registry entrypoints do not match parser entrypoints: "
            f"registry={sorted(registered_entrypoints)}, parsers={sorted(PARSER_BUILDERS)}"
        )
    help_index: dict[str, dict[str, str]] = {}
    for entry in registry["entrypoints"]:
        entrypoint = entry["entrypoint"]
        parser_help = _command_help(PARSER_BUILDERS[entrypoint]())
        names = [item["name"] for item in entry["commands"]]
        if len(names) != len(set(names)):
            raise ValueError(f"Command registry contains duplicate names for {entrypoint}")
        if set(names) != set(parser_help):
            missing = sorted(set(parser_help) - set(names))
            stale = sorted(set(names) - set(parser_help))
            raise ValueError(
                f"Command registry drift for {entrypoint}: missing={missing}, stale={stale}"
            )
        for item in entry["commands"]:
            reference_path = REFERENCES_DIR / item["reference"]
            if not reference_path.is_file():
                raise ValueError(f"Command reference does not exist: {reference_path}")
            registered_engine_choices = (item.get("parameters") or {}).get("engine_choices")
            if registered_engine_choices is not None:
                parser_engine_choices = _option_choices(
                    PARSER_BUILDERS[entrypoint](),
                    item["name"],
                    "--engine",
                )
                if registered_engine_choices != parser_engine_choices:
                    raise ValueError(
                        f"Command engine choices drift for {entrypoint} {item['name']}: "
                        f"registry={registered_engine_choices}, parser={parser_engine_choices}"
                    )
            registered_engine_default = (item.get("parameters") or {}).get("default_engine")
            if registered_engine_default is not None:
                if (
                    registered_engine_choices is None
                    or registered_engine_default not in registered_engine_choices
                ):
                    raise ValueError(
                        f"Command default engine is not registered as a choice for "
                        f"{entrypoint} {item['name']}: {registered_engine_default}"
                    )
                parser_engine_default = _option_default(
                    PARSER_BUILDERS[entrypoint](),
                    item["name"],
                    "--engine",
                )
                if registered_engine_default != parser_engine_default:
                    raise ValueError(
                        f"Command default engine drift for {entrypoint} {item['name']}: "
                        f"registry={registered_engine_default}, parser={parser_engine_default}"
                    )
            registered_fallback_choices = (item.get("parameters") or {}).get("fallback_engine_choices")
            if registered_fallback_choices is not None:
                parser_fallback_choices = _option_choices(
                    PARSER_BUILDERS[entrypoint](),
                    item["name"],
                    "--fallback-engine",
                )
                if registered_fallback_choices != parser_fallback_choices:
                    raise ValueError(
                        f"Command fallback engine choices drift for {entrypoint} {item['name']}: "
                        f"registry={registered_fallback_choices}, parser={parser_fallback_choices}"
                    )
            registered_empty_choices = (item.get("parameters") or {}).get("empty_result_policy_choices")
            if registered_empty_choices is not None:
                parser_empty_choices = _option_choices(
                    PARSER_BUILDERS[entrypoint](),
                    item["name"],
                    "--empty-result-policy",
                )
                if registered_empty_choices != parser_empty_choices:
                    raise ValueError(
                        f"Command empty-result policy choices drift for {entrypoint} {item['name']}: "
                        f"registry={registered_empty_choices}, parser={parser_empty_choices}"
                    )
        help_index[entrypoint] = parser_help
    return help_index


def render_command_reference(registry: dict[str, Any], help_index: dict[str, dict[str, str]]) -> str:
    lines = [
        "<!-- Generated by scripts/build_command_reference.py; do not edit directly. -->",
        "# 命令与能力索引",
        "",
        "命令集合来自当前 CLI parser，能力边界来自 `command_capabilities.json`。生成器要求两者完全一致；参数仍以各入口的 `--help` 为准。",
        "",
    ]
    for entry in registry["entrypoints"]:
        entrypoint = entry["entrypoint"]
        lines.extend(
            [
                f"## `scripts/{entrypoint}`",
                "",
                "| 命令 | CLI 作用 | 影响类型 | 授权门禁 | 详细说明 |",
                "|---|---|---|---|---|",
            ]
        )
        for item in entry["commands"]:
            description = help_index[entrypoint][item["name"]].replace("|", "\\|")
            lines.append(
                f"| `{item['name']}` | {description} | `{item['effect']}` | "
                f"`{item['authorization']}` | [{item['reference']}]({item['reference']}) |"
            )
        lines.append("")
    lines.extend(
        [
            "QueryPlan、Trace、ResultArtifact、Profile、Plan 或 Receipt 均不扩展注册表中的授权边界。任何文档示例也不能替代当前 CLI 参数校验、Hash、确认和 capability registry。",
            "",
        ]
    )
    return "\n".join(lines)


def build() -> str:
    registry = load_registry()
    return render_command_reference(registry, validate_registry(registry))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail when command_reference.md is stale.")
    args = parser.parse_args(argv)
    rendered = build()
    if args.check:
        current = OUTPUT_PATH.read_text(encoding="utf-8") if OUTPUT_PATH.is_file() else ""
        if current != rendered:
            print(f"Command reference is stale: {OUTPUT_PATH}", file=sys.stderr)
            return 1
        print("Command capability registry and generated reference are current.")
        return 0
    OUTPUT_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(f"Wrote {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
