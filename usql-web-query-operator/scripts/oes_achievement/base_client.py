"""Portable official Feishu CLI adapter; no shell shims or token extraction."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import uuid
from typing import Any

from _shared.errors import UsageError
from .workbook import atomic_json, validate_output_dir


def resolve_cli(explicit: str | None = None) -> str:
    candidates = []
    if explicit or os.environ.get("OES_LARK_CLI"):
        candidates.append(Path(explicit or os.environ["OES_LARK_CLI"]).expanduser())
    for name in ("lark-cli.exe", "lark-cli", "lark-cli.cmd"):
        found = shutil.which(name)
        if found:
            path = Path(found)
            if path.suffix.lower() in (".cmd", ".ps1", ".bat"):
                candidates.append(path.parent / "node_modules/@larksuite/cli/bin/lark-cli.exe")
            else:
                candidates.append(path)
    for path in candidates:
        if path.is_file() and path.suffix.lower() not in (".cmd", ".ps1", ".bat"):
            return str(path.resolve())
    raise UsageError("Install the official lark-cli and authenticate as user, or provide --lark-cli with its native executable path.")


class BaseClient:
    def __init__(self, base_token: str, directory: Path, executable: str | None = None):
        self.base_token = base_token
        self.directory = validate_output_dir(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.executable = resolve_cli(executable)

    def call(self, command: str, *options: str, payload: Any = None, payload_flag: str = "--json",
             confirm: bool = False) -> dict[str, Any]:
        argv = [self.executable, "base", command, "--base-token", self.base_token, "--as", "user", *options]
        temporary = None
        if payload is not None:
            temporary = self.directory / f"payload-{uuid.uuid4().hex}.json"
            atomic_json(temporary, payload)
            argv.extend([payload_flag, "@" + temporary.name])
        if confirm:
            argv.append("--yes")  # The sync command explicitly authorizes replacing this exact target table.
        environment = {**os.environ, "LARKSUITE_CLI_NO_UPDATE_NOTIFIER": "1", "LARKSUITE_CLI_NO_SKILLS_NOTIFIER": "1"}
        try:
            completed = subprocess.run(argv, cwd=self.directory, capture_output=True, text=True, encoding="utf-8",
                                       timeout=180, env=environment, shell=False,
                                       creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            raw = completed.stdout if completed.returncode == 0 else completed.stderr
            try:
                result = json.loads(raw)
            except ValueError as exc:
                raise UsageError(f"Feishu {command} returned an unreadable result; a write must not be blindly repeated.") from exc
            if completed.returncode != 0 or result.get("ok") is False:
                error = result.get("error", {})
                raise UsageError(f"Feishu {command} failed: type={error.get('type')}, code={error.get('code')}, subtype={error.get('subtype')}. Check CLI auth and target permissions; no automatic write retry.")
            if result.get("identity", "user") != "user":
                raise UsageError("Feishu operator identity changed; only the authenticated user is supported.")
            return result.get("data", result)
        except subprocess.TimeoutExpired as exc:
            raise UsageError(f"Feishu {command} timed out; its write outcome may be uncertain. No automatic retry.") from exc
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    def fields(self, table_id: str) -> list[dict[str, Any]]:
        result = self.call("+field-list", "--table-id", table_id, "--format", "json")
        fields = result.get("fields")
        if not isinstance(fields, list) or result.get("total") != len(fields):
            raise UsageError("Feishu field-list schema is incomplete or changed.")
        return fields

    def native(self, table_id: str, operation: str, payload: dict, *, params: dict | None = None) -> dict:
        """The native v1 API supports 500 writes/deletes; CLI owns OAuth tokens."""
        if operation not in ("batch_create", "batch_delete") or not table_id.startswith("tbl"):
            raise UsageError("Unsupported native Base operation or target table ID.")
        path = f"/open-apis/bitable/v1/apps/{self.base_token}/tables/{table_id}/records/{operation}"
        argv = [self.executable, "api", "POST", path, "--as", "user", "--format", "json", "--data", "-"]
        if params:
            argv.extend(["--params", json.dumps(params, ensure_ascii=True)])
        environment = {**os.environ, "LARKSUITE_CLI_NO_UPDATE_NOTIFIER": "1", "LARKSUITE_CLI_NO_SKILLS_NOTIFIER": "1"}
        try:
            completed = subprocess.run(argv, input=json.dumps(payload, ensure_ascii=True), cwd=self.directory,
                capture_output=True, text=True, encoding="utf-8", timeout=180, env=environment, shell=False,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            result = json.loads(completed.stdout if completed.returncode == 0 else completed.stderr)
        except (subprocess.TimeoutExpired, ValueError) as exc:
            raise UsageError(f"Native Base {operation} outcome is uncertain; no blind write retry.") from exc
        if completed.returncode != 0 or result.get("ok") is False or result.get("identity", "user") != "user":
            error = result.get("error", {})
            raise UsageError(f"Native Base {operation} failed: type={error.get('type')}, code={error.get('code')}, subtype={error.get('subtype')}. Keep the receipt and verify required user scopes.")
        body = result.get("data", result)
        if "code" in body:
            if body["code"] != 0:
                raise UsageError(f"Native Base {operation} rejected the request: code={body['code']}.")
            body = body["data"]
        return body

    def records(self, table_id: str, fields: list[str], label: str) -> list[dict[str, Any]]:
        offset, revision, scope, rows, ids = 0, None, None, [], set()
        while True:
            filename = f"{label}-{offset}.ndjson"
            options = ["--table-id", table_id, "--format", "ndjson", "--output", filename,
                       "--overwrite", "--limit", "2000", "--offset", str(offset)]
            for field in fields:
                options.extend(["--field-id", field])
            manifest = self.call("+record-list", *options)
            if manifest.get("base_token") != self.base_token or manifest.get("table_id") != table_id:
                raise UsageError("Feishu readback coordinates changed.")
            if revision is None:
                revision, scope = manifest.get("rev"), manifest.get("query_context")
            elif (revision, scope) != (manifest.get("rev"), manifest.get("query_context")):
                raise UsageError("Feishu table changed during full pagination; no complete readback was established.")
            if not scope or scope.get("record_scope") != "all_records":
                raise UsageError("Feishu readback is not scoped to the whole target table.")
            path = self.directory / filename
            block = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
            if len(block) != manifest.get("records_count"):
                raise UsageError("Feishu NDJSON row count differs from its manifest.")
            for row in block:
                identity = row.get("record_id")
                if not identity or identity in ids:
                    raise UsageError("Feishu full pagination returned missing or duplicate record IDs.")
                ids.add(identity)
            rows.extend(block)
            if manifest.get("has_more") is False:
                return rows
            next_offset = manifest.get("next_offset")
            if manifest.get("has_more") is not True or not isinstance(next_offset, int) or next_offset <= offset:
                raise UsageError("Feishu pagination has no authoritative next_offset.")
            offset = next_offset

    def create(self, table_id: str, records: list[dict[str, Any]]) -> list[str]:
        if not 1 <= len(records) <= 500:
            raise UsageError("Native Feishu create batches must contain 1 to 500 records.")
        result = self.native(table_id, "batch_create", {"records": [{"fields": row} for row in records]},
                             params={"client_token": str(uuid.uuid4())})
        created = result.get("records")
        ids = [row.get("record_id") for row in created] if isinstance(created, list) else None
        if not ids or any(not value for value in ids) or len(ids) != len(records) or len(set(ids)) != len(ids):
            raise UsageError("Feishu create response is incomplete or ignored fields; write outcome must be diagnosed before retry.")
        return ids

    def delete(self, table_id: str, ids: list[str]) -> None:
        if not ids:
            return
        if len(ids) > 500:
            raise UsageError("Native Feishu deletion supports at most 500 records per batch.")
        result = self.native(table_id, "batch_delete", {"records": ids})
        deleted = result.get("records")
        if not isinstance(deleted, list) or {row.get("record_id") for row in deleted} != set(ids) or any(row.get("deleted") is not True for row in deleted):
            raise UsageError("Feishu did not confirm the requested record deletion.")
