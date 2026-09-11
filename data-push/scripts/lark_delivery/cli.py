"""Channel-first entrypoint. Describe is local; delivery remains explicitly gated."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

from .core import catalog
from .core.registry import adapter_for
from .core.fanout import run_targets
from .common import feishu


def main(argv=None, *, bound_channel=None):
    parser = argparse.ArgumentParser(description="data-push: department/channel-scoped Feishu delivery")
    parser.add_argument("command", nargs="?", default="describe", choices=("describe", "preview", "dry-run", "preflight", "run", "preflight-now", "send-now"))
    parser.add_argument("--domain", required=bound_channel is None)
    parser.add_argument("--channel", required=bound_channel is None, help="Registered channel ID, not its display label")
    parser.add_argument("--target", action="append", help="Repeatable registered target ID; default: all enabled targets")
    parser.add_argument("--report-type", default="auto", choices=("auto", "process", "result", "both"))
    parser.add_argument("--state-dir", type=Path, help="Preview output root only; cannot override a scheduled ledger")
    parser.add_argument("--confirm-send", action="store_true")
    parser.add_argument("--request-id", help="Stable idempotency ID for one explicitly authorized immediate request")
    args = parser.parse_args(argv)
    if bound_channel and (args.domain or args.channel):
        parser.error("A dedicated channel script cannot be redirected to another channel")
    key = bound_channel or f"{args.domain}/{args.channel}"
    definition = catalog.load_channel(key)
    adapter = adapter_for(definition)
    targets = catalog.select_targets(definition, args.target)
    if args.command in {"run", "preflight", "preflight-now", "send-now"} and (args.state_dir or args.report_type != "auto"):
        parser.error("Scheduled execution cannot override the ledger or weekday report policy")
    if args.command in {"run", "send-now"} and not args.confirm_send:
        parser.error("Sending requires --confirm-send; this does not enable a paused schedule")
    if args.command in {"preflight-now", "send-now"} and not args.request_id:
        parser.error("One-time delivery requires --request-id")
    if args.command == "describe":
        print(json.dumps({"channel_key": key, "adapter": definition["adapter"], "channel": definition["channel"],
                          "targets": targets, "schedule_enabled": definition["schedule"]["enabled"],
                          "state_dir": definition["state_dir"]}, ensure_ascii=False, indent=2))
        return 0
    if args.command == "run" and not definition["schedule"]["enabled"]:
        print(json.dumps({"status": "paused_no_send", "channel_key": key}, ensure_ascii=False))
        return 0

    def operation(target):
        if args.command in {"preflight-now", "send-now"}:
            return adapter.send_now(definition, target, args.request_id, preflight=args.command == "preflight-now")
        if args.command in {"preflight", "run"}:
            return adapter.schedule(definition, target, preflight=args.command == "preflight")
        root = args.state_dir or (Path(definition["state_dir"]) / "previews")
        state = root / definition["domain"] / definition["channel_id"] / target["id"]
        channels = definition.get("channels", [definition["channel"]])
        previews = []
        for index, channel in enumerate(channels, start=1):
            channel_state = state if len(channels) == 1 else state / f"channel-{index}"
            context = adapter.prepare(definition, target, channel=channel, report_type=args.report_type, state_dir=channel_state)
            artifacts = adapter.write_preview(context)
            previews.append({"channel": channel,
                             "status": "skipped_no_eligible_rows" if context.get("skip_delivery") else "preview_generated",
                             "files": artifacts})
            if args.command == "dry-run" and not context.get("skip_delivery"):
                feishu.send_markdown(target["chat_id"], context["markdown"], context["idempotency_key"],
                                     definition["sender"]["identity"], dry_run=True, timeout=60)
        print(json.dumps({"target_id": target["id"], "chat_id": target["chat_id"],
                          "period": context["period"], "previews": previews, "message_sent": False},
                         ensure_ascii=False, indent=2))
        return 0

    outcomes = run_targets(targets, operation, parallel=args.command in {"preflight", "run"})
    print(json.dumps({"channel_key": key, "outcomes": outcomes}, ensure_ascii=False, indent=2))
    return 0 if all(item["ok"] for item in outcomes) else 1


if __name__ == "__main__":
    raise SystemExit(main())
