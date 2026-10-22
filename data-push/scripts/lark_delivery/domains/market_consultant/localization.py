"""Isolate explicit one-time delivery of the two province reports."""
import json
from pathlib import Path
import time

from ...core import catalog
from . import immediate


def send_now(definition, target, request_id, *, preflight=False):
    cfg = catalog.schedule_config(definition, target)
    folder = Path(cfg["state_dir"]) / "immediate" / request_id
    folder.mkdir(parents=True, exist_ok=True)
    name = "preflight" if preflight else "send-summary"
    outcomes = []
    for index, channel in enumerate(cfg["channels"], 1):
        child = folder / f"channel-{index}-{name}.json"
        started = time.time()
        try:
            code = immediate.run(definition, target, request_id, preflight=preflight, only_channels=[channel])
            path = folder / (name + ".json")
            if path.is_file() and path.stat().st_mtime >= started:
                data = json.loads(path.read_text(encoding="utf-8"))
                if [row["channel"] for row in data["channels"]] != [channel]:
                    raise ValueError("Immediate report receipt channel differs")
                child.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            elif child.is_file():
                data = json.loads(child.read_text(encoding="utf-8"))
            else:
                raise ValueError("Immediate report receipt missing")
            outcomes.append({"channel": channel, "exit_code": code, "status": data["status"],
                             "artifact": str(child), "channels": data["channels"]})
        except (Exception, SystemExit) as exc:
            outcomes.append({"channel": channel, "exit_code": 1, "status": "failed",
                             "error": type(exc).__name__ + ": " + str(exc)[:240]})
        (folder / (name + "-bundle.json")).write_text(json.dumps({"request_id": request_id,
            "preflight": preflight, "outcomes": outcomes}, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if all(row["exit_code"] == 0 for row in outcomes) else 1
