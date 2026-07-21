#!/usr/bin/env python3
"""Guarded client for the Xunji training-data and official-plan Open APIs."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from typing import Any, Iterable
import urllib.error
import urllib.request
import uuid


TRAIN_BASE_URL = "https://trains.xunjiapp.cn"
PLAN_BASE_URL = "https://api.xunjiapp.cn"
TRAIN_READ_PATH = "/api_trains_for_llm_v2"
TRAIN_UPSERT_PATH = "/api_upsert_trains_for_llm_v2"
PLAN_QUERY_PATH = "/open/plan/query_gzip"
TRAIN_SCHEMA = "train_open_api_v2"
PLAN_SCHEMA = "plan_open_api_v1"
CACHE_SCHEMA = "xunji_cache_v1"
WRITE_PLAN_SCHEMA = "xunji_write_plan_v1"
WRITE_RECEIPT_SCHEMA = "xunji_write_receipt_v1"
VALID_RPE = {"", "6", "6.5", "7", "7.5", "8", "8.5", "9", "9.5", "10"}
VALID_DIFFICULTY = {"easy", "normal", "hard"}
SET_VALUE_FIELDS = {"weight", "weight_kg", "reps", "time", "duration_s", "selfWeight"}
COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
PLAN_REF_RE = re.compile(r"^(platform|universal):[0-9]+$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class UserError(RuntimeError):
    """An expected, safe-to-display client error."""


def _configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8", errors="strict")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(_json_bytes(value)).hexdigest()


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise UserError(f"JSON file does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise UserError(f"Invalid UTF-8 JSON in {path}: {exc}") from exc


def _write_json_atomic(path: Path, value: Any) -> None:
    path = path.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_name = handle.name
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if temp_name:
            Path(temp_name).unlink(missing_ok=True)


def _emit(value: Any, output: str | None = None) -> None:
    if output:
        target = Path(output).expanduser().resolve()
        _write_json_atomic(target, value)
        print(json.dumps({"output_path": str(target)}, ensure_ascii=False, indent=2))
        return
    print(json.dumps(value, ensure_ascii=False, indent=2))


def _default_cache_dir() -> Path:
    configured = os.environ.get("XUNJI_CACHE_DIR", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return (Path.home() / ".codex" / "runtime" / "xunji-training-data" / "cache").resolve()


def _cache_dir(argument: str | None) -> Path:
    path = Path(argument).expanduser().resolve() if argument else _default_cache_dir()
    anchor = Path(path.anchor).resolve()
    if path == anchor:
        raise UserError("Refusing to use a filesystem root as the cache directory.")
    return path


def _parse_date(value: str, label: str) -> date:
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise UserError(f"{label} must use YYYY-MM-DD: {value}") from exc
    if parsed.isoformat() != value:
        raise UserError(f"{label} must use zero-padded YYYY-MM-DD: {value}")
    return parsed


def _training_cache_path(cache_dir: Path, datestr: str, full: bool) -> Path:
    _parse_date(datestr, "datestr")
    mode = "full" if full else "light"
    return cache_dir / "training" / datestr / f"{mode}.json"


def _cache_record(response: Any, request: dict[str, Any], source: str) -> dict[str, Any]:
    return {
        "cache_schema": CACHE_SCHEMA,
        "cached_at": _now_iso(),
        "source": source,
        "request": request,
        "response": response,
    }


def _unwrap_cache(value: Any) -> Any:
    if isinstance(value, dict) and value.get("cache_schema") == CACHE_SCHEMA:
        if "response" not in value:
            raise UserError("Cache record is missing its response payload.")
        return value["response"]
    return value


def _load_cache(path: Path) -> Any | None:
    if not path.is_file():
        return None
    return _unwrap_cache(_read_json(path))


def _save_cache(path: Path, response: Any, request: dict[str, Any], source: str) -> None:
    _write_json_atomic(path, _cache_record(response, request, source))


def _api_key() -> str:
    key = os.environ.get("XUNJI_API_KEY", "").strip()
    if not key:
        raise UserError(
            "XUNJI_API_KEY is not configured. Configure or regenerate it privately in the app; "
            "do not pass it as a command argument or commit it to a file."
        )
    return key


def _auth_headers(key: str) -> dict[str, str]:
    mode = os.environ.get("XUNJI_AUTH_HEADER", "authorization").strip().lower()
    if mode in {"authorization", "bearer"}:
        return {"Authorization": f"Bearer {key}"}
    if mode == "x-api-key":
        return {"x-api-key": key}
    raise UserError("XUNJI_AUTH_HEADER must be 'authorization' or 'x-api-key'.")


def _decode_response(raw: bytes, content_encoding: str | None) -> Any:
    if "gzip" in (content_encoding or "").lower() or raw.startswith(b"\x1f\x8b"):
        try:
            raw = gzip.decompress(raw)
        except OSError as exc:
            raise UserError("The server returned invalid gzip content.") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise UserError("The server response was not valid UTF-8 JSON.") from exc
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise UserError(f"The server returned invalid JSON: {exc}") from exc


def _find_nested_key(value: Any, wanted: str) -> Any | None:
    if isinstance(value, dict):
        if wanted in value:
            return value[wanted]
        for child in value.values():
            found = _find_nested_key(child, wanted)
            if found is not None:
                return found
    elif isinstance(value, list):
        for child in value:
            found = _find_nested_key(child, wanted)
            if found is not None:
                return found
    return None


def _api_error_message(status: int, data: Any, key: str) -> str:
    parts = [f"HTTP {status}"]
    if isinstance(data, dict):
        for field in ("message", "msg", "error", "detail"):
            candidate = _find_nested_key(data, field)
            if isinstance(candidate, (str, int, float)) and str(candidate).strip():
                parts.append(str(candidate).strip())
                break
        retry_after = _find_nested_key(data, "retry_after_ms")
        if isinstance(retry_after, (int, float, str)):
            parts.append(f"retry_after_ms={retry_after}")
    message = ": ".join(parts)
    return message.replace(key, "[REDACTED]")


def _require_res(response: Any, key: str) -> None:
    if isinstance(response, dict) and "res" in response:
        return
    details: list[str] = []
    if isinstance(response, dict):
        for field in ("message", "msg", "error", "detail"):
            candidate = _find_nested_key(response, field)
            if isinstance(candidate, (str, int, float)) and str(candidate).strip():
                details.append(str(candidate).strip())
                break
        retry_after = _find_nested_key(response, "retry_after_ms")
        if isinstance(retry_after, (int, float, str)):
            details.append(f"retry_after_ms={retry_after}")
    suffix = f" Details: {'; '.join(details)}" if details else ""
    message = f"The API response is missing required core data in 'res'.{suffix}"
    raise UserError(message.replace(key, "[REDACTED]"))


def _post_json(url: str, payload: dict[str, Any], timeout: float = 60.0) -> dict[str, Any]:
    key = _api_key()
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "Content-Type": "application/json; charset=utf-8",
        "User-Agent": "codex-xunji-training-data/1.0",
        **_auth_headers(key),
    }
    request = urllib.request.Request(
        url=url,
        data=_json_bytes(payload),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = _decode_response(response.read(), response.headers.get("Content-Encoding"))
    except urllib.error.HTTPError as exc:
        try:
            data = _decode_response(exc.read(), exc.headers.get("Content-Encoding"))
        except UserError:
            data = None
        raise UserError(_api_error_message(exc.code, data, key)) from exc
    except urllib.error.URLError as exc:
        reason = str(exc.reason).replace(key, "[REDACTED]")
        raise UserError(f"Network request failed: {reason}") from exc
    _require_res(data, key)
    return data


def _extract_trains(value: Any) -> list[dict[str, Any]]:
    value = _unwrap_cache(value)
    if isinstance(value, list):
        trains = value
    elif isinstance(value, dict) and "res" in value:
        return _extract_trains(value["res"])
    elif isinstance(value, dict) and "trains" in value:
        trains = value["trains"]
    elif isinstance(value, dict) and "datestr" in value:
        trains = [value]
    else:
        raise UserError("Could not find a training array in the supplied JSON.")
    if not isinstance(trains, list) or not all(isinstance(item, dict) for item in trains):
        raise UserError("Training data must be an array of objects.")
    return trains


def _validate_note(note: Any, path: str) -> dict[str, Any] | None:
    parsed = note
    if isinstance(note, str):
        try:
            parsed = json.loads(note)
        except json.JSONDecodeError:
            return None
    if parsed is None:
        return None
    if not isinstance(parsed, dict):
        raise UserError(f"{path} must be an object or a JSON object string.")
    if "trainColor" in parsed:
        color = parsed["trainColor"]
        if not isinstance(color, str) or (color != "" and not COLOR_RE.fullmatch(color)):
            raise UserError(f"{path}.trainColor must be an empty string or #RRGGBB.")
    return parsed


def _validate_set(set_value: Any, path: str) -> None:
    if not isinstance(set_value, dict):
        raise UserError(f"{path} must be an object.")
    if "rpe" in set_value:
        rpe = set_value["rpe"]
        if not isinstance(rpe, str) or rpe not in VALID_RPE:
            raise UserError(f"{path}.rpe must be a permitted string value or an empty string.")
    if "done" in set_value and not isinstance(set_value["done"], bool):
        raise UserError(f"{path}.done must be true or false.")
    items = set_value.get("items")
    if not any(field in set_value for field in SET_VALUE_FIELDS) and not items:
        fields = ", ".join(sorted(SET_VALUE_FIELDS))
        raise UserError(f"{path} must contain one of {fields}, or a non-empty items array.")
    if items is not None:
        if not isinstance(items, list) or not items:
            raise UserError(f"{path}.items must be a non-empty array.")
        for index, item in enumerate(items):
            item_path = f"{path}.items[{index}]"
            if not isinstance(item, dict) or not isinstance(item.get("set"), dict):
                raise UserError(f"{item_path}.set must be an object.")
            _validate_set(item["set"], f"{item_path}.set")


def _validate_training(training: Any, index: int) -> None:
    path = f"res[{index}]"
    if not isinstance(training, dict):
        raise UserError(f"{path} must be an object.")
    datestr = training.get("datestr")
    if not isinstance(datestr, str):
        raise UserError(f"{path}.datestr is required.")
    _parse_date(datestr, f"{path}.datestr")
    movements = training.get("movements")
    if not isinstance(movements, list):
        raise UserError(f"{path}.movements must be an array.")
    if len(movements) > 15:
        raise UserError(f"{path} has {len(movements)} movements; the maximum is 15.")
    if "note" in training:
        _validate_note(training["note"], f"{path}.note")
    for movement_index, movement in enumerate(movements):
        movement_path = f"{path}.movements[{movement_index}]"
        if not isinstance(movement, dict):
            raise UserError(f"{movement_path} must be an object.")
        name = movement.get("name")
        if not isinstance(name, str) or not name.strip():
            raise UserError(f"{movement_path}.name must be a confirmed Chinese movement name.")
        if "key" in movement:
            raise UserError(f"{movement_path} must not contain an internal key.")
        if "difficulty" in movement and movement["difficulty"] not in VALID_DIFFICULTY:
            raise UserError(f"{movement_path}.difficulty must be easy, normal, or hard.")
        sets = movement.get("sets")
        if not isinstance(sets, list):
            raise UserError(f"{movement_path}.sets must be an array.")
        if len(sets) > 20:
            raise UserError(f"{movement_path} has {len(sets)} sets; the maximum is 20.")
        for set_index, set_value in enumerate(sets):
            _validate_set(set_value, f"{movement_path}.sets[{set_index}]")


def _normalize_write_input(value: Any, include_full_data: bool) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    original = value
    if isinstance(value, dict) and "res" in value:
        trains = _extract_trains(value["res"])
        include_full_data = bool(value.get("include_full_data", include_full_data))
        client_request_id = value.get("client_request_id")
    else:
        trains = _extract_trains(value)
        client_request_id = None
    if not 1 <= len(trains) <= 4:
        raise UserError("A write must contain between 1 and 4 training rows.")
    dates = set()
    for index, training in enumerate(trains):
        _validate_training(training, index)
        dates.add(training["datestr"])
    if len(dates) != 1:
        raise UserError("All training rows in one write must have the same datestr.")
    if not isinstance(client_request_id, str) or not client_request_id.strip():
        client_request_id = f"codex-xunji-{uuid.uuid4()}"
    body = {
        "schema_version": TRAIN_SCHEMA,
        "client_request_id": client_request_id,
        "dry_run": False,
        "include_full_data": include_full_data,
        "res": trains,
    }
    if isinstance(original, dict) and original.get("schema_version") not in (None, TRAIN_SCHEMA):
        raise UserError(f"schema_version must be {TRAIN_SCHEMA}.")
    return body, trains


def _load_baseline(
    cache_dir: Path,
    datestr: str,
    explicit_path: str | None,
) -> tuple[list[dict[str, Any]], str]:
    if explicit_path:
        path = Path(explicit_path).expanduser().resolve()
    else:
        path = _training_cache_path(cache_dir, datestr, full=True)
    if not path.is_file():
        raise UserError(
            "Updating an existing training requires a full baseline. Run read-training --full "
            f"for {datestr}, or pass --baseline. Expected: {path}"
        )
    return _extract_trains(_read_json(path)), str(path)


def _movement_groups(movements: Iterable[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for movement in movements:
        groups[str(movement.get("name", ""))].append(movement)
    return groups


def _removed_paths(before: Any, after: Any, path: str) -> list[str]:
    removed: list[str] = []
    if isinstance(before, dict):
        if not isinstance(after, dict):
            return [path]
        for key, value in before.items():
            child_path = f"{path}.{key}" if path else key
            if key not in after:
                removed.append(child_path)
            else:
                removed.extend(_removed_paths(value, after[key], child_path))
    elif isinstance(before, list):
        if not isinstance(after, list):
            return [path]
        for index, value in enumerate(before):
            child_path = f"{path}[{index}]"
            if index >= len(after):
                removed.append(child_path)
            else:
                removed.extend(_removed_paths(value, after[index], child_path))
    return removed


def _check_preservation(
    baseline: dict[str, Any],
    candidate: dict[str, Any],
    allow_removal: bool,
    allow_time_change: bool,
) -> None:
    localid = candidate.get("localid")
    for field in ("start", "end"):
        if field in baseline and field not in candidate:
            raise UserError(f"Training {localid} is missing preserved field '{field}'.")
        if (
            field in baseline
            and candidate.get(field) != baseline.get(field)
            and not allow_time_change
        ):
            raise UserError(
                f"Training {localid} changes '{field}'. Use --allow-time-change only after an "
                "explicit user request to change training time."
            )

    ignored = {"movements", "note"}
    missing_top_level = sorted(key for key in baseline if key not in candidate and key not in ignored)
    if missing_top_level and not allow_removal:
        raise UserError(
            f"Training {localid} removes top-level fields: {', '.join(missing_top_level)}. "
            "Preserve them or use --allow-removal after explicit approval."
        )

    baseline_movements = baseline.get("movements", [])
    candidate_movements = candidate.get("movements", [])
    if not isinstance(baseline_movements, list) or not isinstance(candidate_movements, list):
        raise UserError(f"Training {localid} has invalid movements in its baseline or candidate.")
    before_counts = Counter(str(item.get("name", "")) for item in baseline_movements if isinstance(item, dict))
    after_counts = Counter(str(item.get("name", "")) for item in candidate_movements if isinstance(item, dict))
    removed_names = sorted((before_counts - after_counts).elements())
    if removed_names and not allow_removal:
        raise UserError(
            f"Training {localid} removes movements: {', '.join(removed_names)}. "
            "Preserve them or use --allow-removal after explicit approval."
        )

    before_groups = _movement_groups(item for item in baseline_movements if isinstance(item, dict))
    after_groups = _movement_groups(item for item in candidate_movements if isinstance(item, dict))
    removed_nested: list[str] = []
    for name, before_items in before_groups.items():
        after_items = after_groups.get(name, [])
        for occurrence, before_item in enumerate(before_items):
            if occurrence >= len(after_items):
                continue
            removed_nested.extend(
                _removed_paths(
                    before_item,
                    after_items[occurrence],
                    f"movement[{name!r}#{occurrence + 1}]",
                )
            )
    if removed_nested and not allow_removal:
        preview = ", ".join(removed_nested[:8])
        suffix = " ..." if len(removed_nested) > 8 else ""
        raise UserError(
            f"Training {localid} removes movement/set data: {preview}{suffix}. "
            "Preserve it or use --allow-removal after explicit approval."
        )

    if "note" in baseline:
        if "note" not in candidate:
            if not allow_removal:
                raise UserError(
                    f"Training {localid} removes note metadata. Preserve it or use --allow-removal "
                    "after explicit approval."
                )
        else:
            before_note = _validate_note(baseline["note"], "baseline.note")
            after_note = _validate_note(candidate["note"], "candidate.note")
            if before_note is not None:
                note_removed = _removed_paths(before_note, after_note, "note")
                if note_removed and not allow_removal:
                    preview = ", ".join(note_removed[:8])
                    raise UserError(
                        f"Training {localid} removes note fields: {preview}. Preserve them or use "
                        "--allow-removal after explicit approval."
                    )


def _short_value(value: Any, limit: int = 120) -> Any:
    if isinstance(value, str):
        return value if len(value) <= limit else value[: limit - 3] + "..."
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    if isinstance(value, list):
        return {"type": "array", "items": len(value)}
    if isinstance(value, dict):
        return {"type": "object", "keys": sorted(str(key) for key in value)[:20]}
    return str(value)[:limit]


def _diff_values(before: Any, after: Any, path: str, output: list[dict[str, Any]]) -> None:
    if before == after:
        return
    if isinstance(before, dict) and isinstance(after, dict):
        for key in sorted(set(before) | set(after), key=str):
            child_path = f"{path}.{key}" if path else str(key)
            if key not in before:
                output.append({"path": child_path, "kind": "added", "after": _short_value(after[key])})
            elif key not in after:
                output.append({"path": child_path, "kind": "removed", "before": _short_value(before[key])})
            else:
                _diff_values(before[key], after[key], child_path, output)
        return
    if isinstance(before, list) and isinstance(after, list):
        length = max(len(before), len(after))
        for index in range(length):
            child_path = f"{path}[{index}]"
            if index >= len(before):
                output.append({"path": child_path, "kind": "added", "after": _short_value(after[index])})
            elif index >= len(after):
                output.append({"path": child_path, "kind": "removed", "before": _short_value(before[index])})
            else:
                _diff_values(before[index], after[index], child_path, output)
        return
    output.append(
        {
            "path": path,
            "kind": "changed",
            "before": _short_value(before),
            "after": _short_value(after),
        }
    )


def _count_sets(movements: list[dict[str, Any]]) -> tuple[int, int]:
    total = 0
    unfinished = 0

    def visit(set_value: Any) -> None:
        nonlocal total, unfinished
        if not isinstance(set_value, dict):
            return
        total += 1
        if set_value.get("done") is False:
            unfinished += 1
        for item in set_value.get("items", []) if isinstance(set_value.get("items"), list) else []:
            if isinstance(item, dict):
                visit(item.get("set"))

    for movement in movements:
        for set_value in movement.get("sets", []) if isinstance(movement, dict) else []:
            visit(set_value)
    return total, unfinished


def _build_summary(
    trains: list[dict[str, Any]],
    baselines: dict[str, dict[str, Any]],
    allow_removal: bool,
    allow_time_change: bool,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    total_changes = 0
    all_changes: list[dict[str, Any]] = []
    for index, training in enumerate(trains):
        movements = training.get("movements", [])
        set_count, unfinished_count = _count_sets(movements)
        localid = training.get("localid")
        row = {
            "index": index,
            "operation": "update" if localid is not None else "create",
            "datestr": training["datestr"],
            "localid": localid,
            "title": training.get("title", ""),
            "movement_count": len(movements),
            "set_count_including_nested": set_count,
            "unfinished_set_count": unfinished_count,
        }
        if localid is not None:
            changes: list[dict[str, Any]] = []
            _diff_values(baselines[str(localid)], training, "training", changes)
            row["change_count"] = len(changes)
            total_changes += len(changes)
            for change in changes:
                all_changes.append({"localid": localid, **change})
        else:
            row["change_count"] = 1
            total_changes += 1
            all_changes.append(
                {
                    "localid": None,
                    "path": "training",
                    "kind": "created",
                    "after": {
                        "title": training.get("title", ""),
                        "movements": len(movements),
                        "sets": set_count,
                    },
                }
            )
        rows.append(row)
    limit = 200
    return {
        "datestr": trains[0]["datestr"],
        "training_count": len(trains),
        "total_change_count": total_changes,
        "allow_removal": allow_removal,
        "allow_time_change": allow_time_change,
        "rows": rows,
        "changes": all_changes[:limit],
        "changes_truncated": len(all_changes) > limit,
    }


def _plan_hash(plan: dict[str, Any]) -> str:
    material = dict(plan)
    material.pop("plan_sha256", None)
    return _sha256(material)


def _cmd_read_training(args: argparse.Namespace) -> int:
    _parse_date(args.datestr, "datestr")
    cache_dir = _cache_dir(args.cache_dir)
    requested_path = _training_cache_path(cache_dir, args.datestr, args.full)
    if not args.refresh:
        candidates = [requested_path]
        if not args.full:
            candidates.append(_training_cache_path(cache_dir, args.datestr, full=True))
        for candidate in candidates:
            cached = _load_cache(candidate)
            if cached is not None:
                print(f"cache_hit={candidate}", file=sys.stderr)
                _emit(cached, args.output)
                return 0
    payload = {
        "schema_version": TRAIN_SCHEMA,
        "datestr": args.datestr,
        "include_full_data": bool(args.full),
    }
    response = _post_json(TRAIN_BASE_URL + TRAIN_READ_PATH, payload)
    _save_cache(requested_path, response, payload, "read-training")
    print(f"cache_updated={requested_path}", file=sys.stderr)
    _emit(response, args.output)
    return 0


def _cmd_list_plans(args: argparse.Namespace) -> int:
    cache_dir = _cache_dir(args.cache_dir)
    cache_path = cache_dir / "plans" / "list.json"
    if not args.refresh:
        cached = _load_cache(cache_path)
        if cached is not None:
            print(f"cache_hit={cache_path}", file=sys.stderr)
            _emit(cached, args.output)
            return 0
    payload = {"schema_version": PLAN_SCHEMA, "action": "list"}
    response = _post_json(PLAN_BASE_URL + PLAN_QUERY_PATH, payload)
    _save_cache(cache_path, response, payload, "list-plans")
    print(f"cache_updated={cache_path}", file=sys.stderr)
    _emit(response, args.output)
    return 0


def _cmd_get_plan(args: argparse.Namespace) -> int:
    if not PLAN_REF_RE.fullmatch(args.plan_ref):
        raise UserError("plan_ref must look like platform:155 or universal:155.")
    if bool(args.start_date) != bool(args.end_date):
        raise UserError("Provide both --start-date and --end-date, or neither.")
    payload: dict[str, Any] = {
        "schema_version": PLAN_SCHEMA,
        "action": "get",
        "plan_ref": args.plan_ref,
        "include_movements": not args.without_movements,
    }
    if args.start_date and args.end_date:
        start = _parse_date(args.start_date, "start_date")
        end = _parse_date(args.end_date, "end_date")
        if end < start:
            raise UserError("end_date must not be before start_date.")
        if (end - start).days + 1 > 92:
            raise UserError("A custom official-plan range may contain at most 92 inclusive days.")
        payload["start_date"] = args.start_date
        payload["end_date"] = args.end_date
    cache_dir = _cache_dir(args.cache_dir)
    cache_path = cache_dir / "plans" / "get" / f"{_sha256(payload)}.json"
    if not args.refresh:
        cached = _load_cache(cache_path)
        if cached is not None:
            print(f"cache_hit={cache_path}", file=sys.stderr)
            _emit(cached, args.output)
            return 0
    response = _post_json(PLAN_BASE_URL + PLAN_QUERY_PATH, payload)
    _save_cache(cache_path, response, payload, "get-plan")
    print(f"cache_updated={cache_path}", file=sys.stderr)
    _emit(response, args.output)
    return 0


def _cmd_prepare_upsert(args: argparse.Namespace) -> int:
    input_path = Path(args.input).expanduser().resolve()
    body, trains = _normalize_write_input(_read_json(input_path), args.include_full_data)
    cache_dir = _cache_dir(args.cache_dir)
    datestr = trains[0]["datestr"]
    existing = [training for training in trains if training.get("localid") is not None]
    baselines: dict[str, dict[str, Any]] = {}
    baseline_source: str | None = None
    if existing:
        baseline_rows, baseline_source = _load_baseline(cache_dir, datestr, args.baseline)
        for baseline in baseline_rows:
            if baseline.get("localid") is not None:
                baselines[str(baseline["localid"])] = baseline
        for candidate in existing:
            key = str(candidate["localid"])
            if key not in baselines:
                raise UserError(
                    f"The full baseline does not contain localid {candidate['localid']}; refusing update."
                )
            _check_preservation(
                baselines[key],
                candidate,
                allow_removal=args.allow_removal,
                allow_time_change=args.allow_time_change,
            )
    summary = _build_summary(
        trains,
        baselines,
        allow_removal=args.allow_removal,
        allow_time_change=args.allow_time_change,
    )
    plan: dict[str, Any] = {
        "schema_version": WRITE_PLAN_SCHEMA,
        "created_at": _now_iso(),
        "source_input": str(input_path),
        "source_input_sha256": _sha256(_read_json(input_path)),
        "baseline_source": baseline_source,
        "cache_dir": str(cache_dir),
        "safety": {
            "allow_removal": bool(args.allow_removal),
            "allow_time_change": bool(args.allow_time_change),
            "requires_explicit_confirmation": True,
        },
        "summary": summary,
        "request": body,
    }
    plan["plan_sha256"] = _plan_hash(plan)
    if args.plan_out:
        plan_path = Path(args.plan_out).expanduser().resolve()
    else:
        plan_path = (
            cache_dir.parent
            / "plans"
            / f"{datestr}-{datetime.now().strftime('%Y%m%dT%H%M%S')}-{plan['plan_sha256'][:12]}.json"
        ).resolve()
    _write_json_atomic(plan_path, plan)
    _emit(
        {
            "plan_path": str(plan_path),
            "plan_sha256": plan["plan_sha256"],
            "summary": summary,
            "next_action": "Show this summary and exact hash to the user, then wait for confirmation.",
        }
    )
    return 0


def _assert_child_path(path: Path, parent: Path) -> None:
    resolved_path = path.resolve()
    resolved_parent = parent.resolve()
    try:
        resolved_path.relative_to(resolved_parent)
    except ValueError as exc:
        raise UserError(f"Refusing cache operation outside {resolved_parent}: {resolved_path}") from exc


def _replace_training_cache(
    cache_dir: Path,
    datestr: str,
    full: bool,
    response: dict[str, Any],
    request: dict[str, Any],
) -> Path:
    training_root = (cache_dir / "training" / datestr).resolve()
    _assert_child_path(training_root, cache_dir)
    for mode in (False, True):
        stale = _training_cache_path(cache_dir, datestr, mode).resolve()
        _assert_child_path(stale, training_root)
        stale.unlink(missing_ok=True)
    target = _training_cache_path(cache_dir, datestr, full).resolve()
    _assert_child_path(target, training_root)
    _save_cache(target, response, {"datestr": datestr, "include_full_data": full}, "apply-upsert")
    return target


def _cmd_apply_upsert(args: argparse.Namespace) -> int:
    if not args.confirm_write:
        raise UserError("Writeback requires --confirm-write after explicit user confirmation.")
    expected = args.expected_sha256.strip().lower()
    if not SHA256_RE.fullmatch(expected):
        raise UserError("--expected-sha256 must be a lowercase 64-character SHA-256 value.")
    plan_path = Path(args.plan).expanduser().resolve()
    plan = _read_json(plan_path)
    if not isinstance(plan, dict) or plan.get("schema_version") != WRITE_PLAN_SCHEMA:
        raise UserError(f"Plan must use schema_version {WRITE_PLAN_SCHEMA}.")
    stored = plan.get("plan_sha256")
    computed = _plan_hash(plan)
    if stored != computed:
        raise UserError("The write plan was modified after creation; its stored hash is invalid.")
    if expected != computed:
        raise UserError("The confirmed SHA-256 does not match this write plan.")
    receipt_path = plan_path.with_name(f"{plan_path.stem}.receipt.json")
    if receipt_path.exists():
        raise UserError(f"This plan already has an apply receipt: {receipt_path}")
    request = plan.get("request")
    if not isinstance(request, dict):
        raise UserError("The write plan is missing its request object.")
    request_body, trains = _normalize_write_input(request, bool(request.get("include_full_data")))
    if request_body != request:
        raise UserError("The write request is not in the canonical guarded-client form.")
    response = _post_json(TRAIN_BASE_URL + TRAIN_UPSERT_PATH, request)
    cache_dir = _cache_dir(plan.get("cache_dir"))
    datestr = trains[0]["datestr"]
    cache_path = _replace_training_cache(
        cache_dir,
        datestr,
        bool(request.get("include_full_data")),
        response,
        request,
    )
    receipt = {
        "schema_version": WRITE_RECEIPT_SCHEMA,
        "applied_at": _now_iso(),
        "plan_path": str(plan_path),
        "plan_sha256": computed,
        "cache_path": str(cache_path),
        "response": response,
    }
    _write_json_atomic(receipt_path, receipt)
    _emit(
        {
            "receipt_path": str(receipt_path),
            "plan_sha256": computed,
            "cache_path": str(cache_path),
            "res": response["res"],
        }
    )
    return 0


def _add_cache_output_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--cache-dir", help="Private non-repository cache directory")
    parser.add_argument("--refresh", action="store_true", help="Bypass an existing cache entry")
    parser.add_argument("--output", help="Write UTF-8 JSON output to this file")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Guarded Xunji training-data and official-plan Open API client."
    )
    parser.add_argument("--version", action="version", version="xunji_open_api.py 1.0")
    subparsers = parser.add_subparsers(dest="command", required=True)

    read = subparsers.add_parser("read-training", help="Read and cache one training date")
    read.add_argument("--datestr", required=True, help="Training date in YYYY-MM-DD format")
    read.add_argument("--full", action="store_true", help="Request full training data")
    _add_cache_output_options(read)
    read.set_defaults(func=_cmd_read_training)

    list_plans = subparsers.add_parser("list-plans", help="List official plans")
    _add_cache_output_options(list_plans)
    list_plans.set_defaults(func=_cmd_list_plans)

    get_plan = subparsers.add_parser("get-plan", help="Read one official plan")
    get_plan.add_argument("--plan-ref", required=True, help="Returned plan reference")
    get_plan.add_argument("--start-date", help="Inclusive start date in YYYY-MM-DD format")
    get_plan.add_argument("--end-date", help="Inclusive end date in YYYY-MM-DD format")
    get_plan.add_argument(
        "--without-movements",
        action="store_true",
        help="Return calendar data without movement details",
    )
    _add_cache_output_options(get_plan)
    get_plan.set_defaults(func=_cmd_get_plan)

    prepare = subparsers.add_parser(
        "prepare-upsert",
        help="Validate a candidate and create a hash-bound write plan without network access",
    )
    prepare.add_argument("--input", required=True, help="Candidate UTF-8 JSON file")
    prepare.add_argument("--baseline", help="Explicit full baseline JSON or cache file")
    prepare.add_argument("--plan-out", help="Write plan path; defaults to the private runtime directory")
    prepare.add_argument("--cache-dir", help="Private non-repository cache directory")
    prepare.add_argument(
        "--include-full-data",
        action="store_true",
        help="Request a full normalized response after writeback",
    )
    prepare.add_argument(
        "--allow-removal",
        action="store_true",
        help="Allow explicit movement, set, or metadata removals in this plan",
    )
    prepare.add_argument(
        "--allow-time-change",
        action="store_true",
        help="Allow an explicitly requested start/end change in this plan",
    )
    prepare.set_defaults(func=_cmd_prepare_upsert)

    apply_upsert = subparsers.add_parser(
        "apply-upsert",
        help="Apply one exact, explicitly confirmed write plan",
    )
    apply_upsert.add_argument("--plan", required=True, help="Prepared write plan JSON")
    apply_upsert.add_argument(
        "--expected-sha256",
        required=True,
        help="Exact SHA-256 previously shown to and confirmed by the user",
    )
    apply_upsert.add_argument(
        "--confirm-write",
        action="store_true",
        help="Assert that the user explicitly confirmed this exact plan",
    )
    apply_upsert.set_defaults(func=_cmd_apply_upsert)
    return parser


def main(argv: list[str] | None = None) -> int:
    _configure_stdio()
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except UserError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("error: interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
