"""Legacy mention lookup; current grade reports use the strict manager resolver."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Mapping, Sequence
from ..common.values import _iter_dicts, _string


def _load_mention_map(path: str | None) -> dict[str, str]:
    if not path:
        return {}
    data = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    if not isinstance(data, Mapping):
        raise SystemExit("--mention-map 必须是 JSON 对象，格式为 {\"姓名\": \"ou_xxx\"}")
    result: dict[str, str] = {}
    for name, value in data.items():
        open_id = value.get("open_id") if isinstance(value, Mapping) else value
        if isinstance(open_id, str) and open_id.startswith("ou_"):
            result[str(name)] = open_id
        else:
            raise SystemExit("--mention-map 中 %s 的 open_id 不是 ou_ 开头" % name)
    return result


def _user_candidates(payload: Any) -> list[Mapping[str, Any]]:
    seen: set[str] = set()
    result: list[Mapping[str, Any]] = []
    for item in _iter_dicts(payload):
        open_id = _string(item.get("open_id") or item.get("user_id"))
        if open_id and open_id.startswith("ou_") and open_id not in seen:
            seen.add(open_id)
            result.append(item)
    return result


def resolve_mentions(
    rows: Sequence[Mapping[str, Any]],
    *,
    mention_map: Mapping[str, str],
    no_lookup: bool,
    disable_mentions: bool = False,
    extra_names: Sequence[str] = (),
    timeout: int,
 services) -> dict[str, Any]:
    names = []
    for row in rows:
        for field in ("顾问", "主管"):
            name = services._string(services._raw_field(row, field))
            if name and name not in names:
                names.append(name)
    for name in extra_names:
        name = services._string(name)
        if name and name not in names:
            names.append(name)
    resolved = {name: mention_map[name] for name in names if name in mention_map}
    unresolved = [name for name in names if name not in resolved]
    ambiguous: dict[str, list[str]] = {}
    lookup_error = ""
    if disable_mentions:
        return {
            "resolved": {},
            "unresolved": [],
            "ambiguous": {},
            "lookup_error": "",
            "names": names,
        }
    if unresolved and not no_lookup:
        try:
            for start in range(0, len(unresolved), 20):
                chunk = unresolved[start : start + 20]
                payload = services._unwrap(
                    services._json_payload(
                        services.run_lark(
                            [
                                "contact",
                                "+search-user",
                                "--queries",
                                ",".join(chunk),
                                "--lang",
                                "zh_cn",
                                "--format",
                                "json",
                                "--as",
                                "user",
                            ],
                            timeout=timeout,
                        )
                    )
                )
                users = _user_candidates(payload)
                for name in chunk:
                    exact = []
                    for user in users:
                        labels = {
                            services._string(user.get("localized_name")),
                            services._string(user.get("name")),
                            services._string(user.get("real_name")),
                        }
                        if name in labels:
                            exact.append(user)
                    ids = sorted({services._string(item.get("open_id") or item.get("user_id")) for item in exact})
                    if len(ids) == 1:
                        resolved[name] = ids[0]
                    elif len(ids) > 1:
                        ambiguous[name] = ids
        except Exception as exc:  # preview remains useful when contact scope is absent
            lookup_error = str(exc)
    unresolved = [name for name in names if name not in resolved]
    return {
        "resolved": resolved,
        "unresolved": unresolved,
        "ambiguous": ambiguous,
        "lookup_error": lookup_error,
        "names": names,
    }
