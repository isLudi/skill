"""Concrete read-only Feishu ports; backend injection also supports legacy callers."""
from . import feishu
from .values import _unwrap, _json_payload, _iter_dicts, _string


class FeishuReportPorts:
    def __init__(self, backend=feishu):
        self.backend = backend

    def resolve_source(self, args):
        return self.backend.resolve_coordinates(args)

    def field_names(self, coordinates, args):
        data = _unwrap(_json_payload(self.backend.run_lark([
            "base", "+field-list", "--base-token", coordinates["base_token"], "--table-id", args.raw_table_id,
            "--as", args.base_as, "--format", "json"], timeout=args.timeout)))
        return {_string(item.get("name") or item.get("field_name")) for item in _iter_dicts(data)}

    def read_records(self, coordinates, args, fields, *, filter_json, audit):
        return self.backend._fetch_view_records(coordinates, args, fields, temp_prefix=".grade-leads-",
                                                filter_json=filter_json, audit=audit)

    def search_users(self, queries, args):
        result = {"queries": [], "users": []}
        for start in range(0, len(queries), 20):
            data = _unwrap(_json_payload(self.backend.run_lark([
                "contact", "+search-user", "--queries", ",".join(queries[start:start + 20]),
                "--exclude-external-users", "--lang", "zh_cn", "--as", "user", "--format", "json"],
                timeout=args.timeout)))
            result["queries"].extend(data.get("queries", []))
            result["users"].extend(data.get("users", []))
        return result

    def verify_target(self, chat_id, name, identity, timeout):
        return self.backend.verify_chat(chat_id, name, identity, timeout)

    def missing_members(self, chat_id, resolved, identity, timeout):
        return self.backend.mention_nonmembers(chat_id, resolved, identity, timeout)
