"""Portable one-shot launcher; Python/Edge/official CLI, no Codex installation."""

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import sys
from zoneinfo import ZoneInfo


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("sync", "login", "mail-login", "check", "cleanup"))
    parser.add_argument("--settings", type=Path, required=True)
    parser.add_argument("--run-key", help="Omit to use the current Shanghai 30-minute scheduler occurrence.")
    args = parser.parse_args(argv)
    settings_path = args.settings.expanduser().resolve()
    settings = json.loads(settings_path.read_text(encoding="utf-8-sig"))
    root = settings_path.parent
    def path(key):
        value = Path(settings[key]).expanduser()
        return value if value.is_absolute() else root / value
    os.environ["OES_AUTOMATION_HOME"] = str(path("runtime_dir").resolve())
    os.environ["USQL_ENV_FILE"] = str(path("credentials_file").resolve())
    # Imports occur only after per-machine runtime and credential paths have been configured.
    from oes_achievement.cli import main as oes_main
    retention = ["--cache-retention-days", str(settings.get("cache_retention_days", 7)),
                 "--log-retention-days", str(settings.get("log_retention_days", 30))]
    if args.action == "cleanup":
        return oes_main(["clean-cache", "--base-token", settings["base_token"], "--table-id", settings["table_id"],
                         "--output-dir", str(path("output_dir")), *retention])
    common = ["--env-file", str(path("credentials_file")), "--browser-channel", settings.get("browser_channel", "msedge")]
    if args.action == "login":
        return oes_main(["login", "--headed", *common])
    if args.action == "mail-login":
        return oes_main(["mail-login", *common])
    if args.action == "check":
        from oes_achievement.base_client import BaseClient
        from oes_achievement.base_records import validate_schema, timestamp_ms
        from oes_achievement.base_sync import CONFIG_FIELDS
        from oes_achievement.session import load_credentials
        client = BaseClient(settings["base_token"], path("runtime_dir") / "doctor", str(path("lark_cli")))
        validate_schema(client.fields(settings["table_id"]))
        rows = client.records(settings["config_table_id"], [field["name"] for field in CONFIG_FIELDS], "configuration")
        selected = [row for row in rows if row.get("record_id") == settings["config_record_id"]
                    and row.get("数据表ID") == settings["table_id"] and row.get("启用") is True]
        if len(selected) != 1:
            raise SystemExit("Check the selected enabled Base configuration and its target table.")
        timestamp_ms(selected[0].get("开始时间"))
        load_credentials(path("credentials_file"))
        print(json.dumps({"status": "ok", "data_table_schema_verified": True, "base_configuration_verified": True,
                          "credentials_section_verified": True, "runtime_dir": str(path("runtime_dir")),
                          "python": sys.executable}, ensure_ascii=False))
        return 0
    clock = datetime.now(ZoneInfo("Asia/Shanghai"))
    slot = clock.replace(minute=clock.minute // 30 * 30, second=0, microsecond=0)
    key = args.run_key or f"oes_base_{settings['config_record_id']}_{slot:%Y%m%d_%H%M}"
    return oes_main(["sync-base", *common, "--base-token", settings["base_token"], "--table-id", settings["table_id"],
        "--config-table-id", settings["config_table_id"], "--config-record-id", settings["config_record_id"],
        "--lark-cli", str(path("lark_cli")), "--output-dir", str(path("output_dir")), "--run-key", key,
        "--wait-seconds", str(settings.get("mail_wait_seconds", 600)), "--poll-seconds", str(settings.get("mail_poll_seconds", 3)),
        "--scan-pages", str(settings.get("mail_scan_pages", 5)), *retention])


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
