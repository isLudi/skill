"""Per-target outcomes: failures and uncertain sends never replay successful groups."""
from concurrent.futures import ThreadPoolExecutor


def run_targets(targets, operation, *, parallel=False):
    targets = list(targets)
    if len({target["chat_id"] for target in targets}) != len(targets):
        raise ValueError("Duplicate chat ID in fanout")

    def run(target):
        try:
            value = operation(target)
            return {"target_id": target["id"], "chat_id": target["chat_id"], "ok": value == 0,
                    "exit_code": value}
        except (Exception, SystemExit) as exc:
            return {"target_id": target["id"], "chat_id": target["chat_id"], "ok": False,
                    "error_type": type(exc).__name__, "error": str(exc)[:300]}

    if parallel and len(targets) > 1:
        # Do not queue a registered target behind another target's 30-minute retry window.
        with ThreadPoolExecutor(max_workers=len(targets)) as executor:
            return list(executor.map(run, targets))
    return [run(target) for target in targets]
