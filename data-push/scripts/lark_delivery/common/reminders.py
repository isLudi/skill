"""Optional human reminders: verified native mentions or complete plain names."""
from __future__ import annotations

import re
from collections import Counter

from .im import mention_nonmembers


def resolve_contacts(people, lookup, *, account_keys=False, member_ids=None):
    """Resolve independent contact batches; person failures only produce text."""
    if any(not isinstance(p.get("name"), str) or not p["name"].strip() for p in people):
        raise ValueError("Reminder source records must contain display names")
    keyed, conflicts = {}, set()
    for person in people:
        key = (person.get("account") or person["name"]) if account_keys else person["name"]
        if key in keyed and keyed[key].get("account") != person.get("account"):
            conflicts.add(key)
        keyed[key] = person
    if member_ids is not None and not member_ids:
        return {}, {}, {key: "membership_unverified_or_absent" for key in keyed}

    def query_for(person):
        return (f'{person["account"]}@gaotu.cn' if person.get("account")
                else re.sub(r"\d+$", "", person["name"]))

    queries = sorted({query_for(p) for p in keyed.values()})
    statuses, users = {}, []
    for start in range(0, len(queries), 20):
        chunk = queries[start:start + 20]
        try:
            result = lookup(["contact", "+search-user", "--queries", ",".join(chunk),
                             "--exclude-external-users", "--lang", "zh_cn", "--as", "user", "--format", "json"])
            batch_status = result.get("queries", [])
            batch_users = result.get("users", [])
            if not isinstance(batch_status, list) or not isinstance(batch_users, list):
                raise ValueError("Malformed contact search response")
            statuses.update({item["query"]: item for item in batch_status
                             if isinstance(item, dict) and item.get("query") in chunk})
            users.extend(item for item in batch_users if isinstance(item, dict))
        except Exception:
            for query in chunk:
                statuses[query] = {"error": "contact_lookup_failed"}

    resolved, display, fallback = {}, {}, {}
    for key, person in keyed.items():
        name, query = person["name"], query_for(person)
        status = statuses.get(query, {})
        if key in conflicts or status.get("error") or status.get("has_more") is not False:
            fallback[key] = "identity_ambiguous" if key in conflicts else "contact_lookup_incomplete"
            continue
        suffix, candidates = re.search(r"(\d+)$", name), {}
        for user in users:
            if (user.get("matched_query") != query or user.get("is_activated") is not True
                    or user.get("is_cross_tenant")):
                continue
            label, email = user.get("localized_name"), str(user.get("enterprise_email") or "")
            if not isinstance(label, str):
                continue
            if person.get("account"):
                if email.casefold() != query.casefold():
                    continue
            elif label not in {name, query} or (suffix and not email.split("@", 1)[0].endswith(suffix.group(1))):
                continue
            open_id = user.get("open_id")
            if isinstance(open_id, str) and re.fullmatch(r"ou_[A-Za-z0-9]+", open_id):
                candidates[open_id] = label or name
        if len(candidates) > 1 and member_ids is not None:
            in_chat = {oid: label for oid, label in candidates.items() if oid in member_ids}
            if len(in_chat) == 1:
                candidates = in_chat
        if len(candidates) != 1:
            fallback[key] = "identity_ambiguous" if candidates else "identity_not_resolved"
            continue
        open_id, label = next(iter(candidates.items()))
        if member_ids is not None and open_id not in member_ids:
            fallback[key] = "not_in_chat"
            continue
        resolved[key], display[key] = open_id, label
    counts = Counter(resolved.values())
    for key, open_id in list(resolved.items()):
        if counts[open_id] > 1:
            fallback[key] = "identity_ambiguous"
            resolved.pop(key)
            display.pop(key, None)
    return resolved, display, fallback


def refresh_membership(chat_id, resolved, *, timeout=60):
    """A failed member lookup invalidates every optional native @, never routing."""
    if not resolved:
        return {}, {"text_fallback_names": [], "fallback_reasons": {}}
    error = ""
    try:
        missing = set(mention_nonmembers(chat_id, resolved, "bot", timeout))
    except Exception as exc:
        missing, error = set(resolved), type(exc).__name__
    return ({name: oid for name, oid in resolved.items() if name not in missing},
            {"text_fallback_names": sorted(missing), "member_lookup_error": error,
             "fallback_reasons": {name: "membership_unverified" if error else "not_in_chat"
                                  for name in sorted(missing)}})
