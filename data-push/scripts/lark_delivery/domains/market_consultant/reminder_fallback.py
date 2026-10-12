"""Keep every selected reminder while using native @ only for verified people."""
from __future__ import annotations

import html
import re
from collections import Counter


def normalize(names, info, *, membership_error=""):
    """Partition reminders into verified mentions and plain names, with reasons."""
    expected = set(names)
    resolved = dict(info.get("resolved", {}))
    reasons = dict(info.get("fallback_reasons", {}))
    fallback = set(info.get("text_fallback_names", ()))
    for field, reason in (("unresolved", "identity_not_resolved"),
                          ("ambiguous", "identity_ambiguous"),
                          ("nonmembers", "not_in_chat")):
        for name in info.get(field, ()):
            fallback.add(name)
            reasons[name] = reason
    if info.get("lookup_error"):
        for name in expected - set(resolved):
            fallback.add(name)
            reasons[name] = "identity_lookup_failed"
    if membership_error:
        for name in expected:
            fallback.add(name)
            reasons[name] = "membership_not_verified"
    for name in expected:
        if not re.fullmatch(r"ou_[A-Za-z0-9]+", str(resolved.get(name, ""))):
            fallback.add(name)
            reasons.setdefault(name, "identity_not_resolved")
    counts = Counter(oid for oid in resolved.values() if isinstance(oid, str))
    for name, open_id in resolved.items():
        if isinstance(open_id, str) and counts[open_id] > 1:
            fallback.add(name)
            reasons[name] = "identity_ambiguous"
    resolved = {name: open_id for name, open_id in resolved.items()
                if name in expected and name not in fallback}
    fallback = expected - set(resolved)
    return {**info, "names": list(names), "resolved": resolved,
            "unresolved": [], "ambiguous": {}, "lookup_error": "", "nonmembers": [],
            "text_fallback_names": sorted(fallback),
            "fallback_reasons": {name: reasons.get(name, "identity_not_resolved") for name in sorted(fallback)}}


def validate_coverage(names, info, markdown):
    """Require all selected people to appear, without requiring everyone to be @."""
    expected, resolved = set(names), info.get("resolved", {})
    fallback = set(info.get("text_fallback_names", ()))
    if set(resolved) | fallback != expected or set(resolved) & fallback:
        raise ValueError("reminder account/name coverage mismatch")
    if any(not re.fullmatch(r"ou_[A-Za-z0-9]+", str(open_id)) for open_id in resolved.values()):
        raise ValueError("invalid verified reminder account")
    for name in fallback:
        label = html.escape(info.get("display_names", {}).get(name, name))
        if label not in markdown:
            raise ValueError("plain-name reminder missing from message")


def refresh_before_send(context, chat_id, lookup):
    """Downgrade late departures or failed membership reads before transmission."""
    resolved = context.get("mention_info", {}).get("resolved", {})
    if not resolved:
        return
    error = ""
    try:
        absent = set(lookup(chat_id, resolved, "bot", 60))
    except Exception as exc:
        absent, error = set(resolved), type(exc).__name__
    children = list(context["dual_sections"].values()) if context.get("dual_sections") else [context]
    for child in children:
        info = child["mention_info"]
        before = dict(info.get("resolved", {}))
        candidate = {**info, "nonmembers": sorted(set(info.get("nonmembers", ())) | (absent & set(before)))}
        names = child.get("grade_report", {}).get("reminder_names", info.get("names", ()))
        updated = normalize(names, candidate, membership_error=error)
        removed_ids = set(before.values()) - set(updated["resolved"].values())

        def plain_name(match):
            return match.group(2) if match.group(1) in removed_ids else match.group(0)

        child["markdown"] = re.sub(r'<at user_id="(ou_[A-Za-z0-9]+)">(.*?)</at>',
                                   plain_name, child["markdown"])
        child["mention_info"] = updated
    if context.get("dual_sections"):
        from .weekend_dual import compose_markdown, merge_mention_info
        context["mention_info"] = merge_mention_info(*(child["mention_info"] for child in children))
        context["markdown"] = compose_markdown(context)


def review_before_send(context, evidence, cfg, slot, validate, lookup, emit):
    """Recheck reminder coverage around the final membership read."""
    validate(context, evidence, cfg, slot)
    refresh_before_send(context, cfg["chat_id"], lookup)
    validate(context, evidence, cfg, slot)
    fallback = context["mention_info"].get("text_fallback_names", [])
    if fallback:
        emit("reminder_text_fallback", channel=context["channel"], names=fallback,
             reasons=context["mention_info"].get("fallback_reasons", {}), slot=slot.isoformat())


def harmonize_contexts(*children):
    """A cross-section identity conflict becomes plain text in every section."""
    accounts, labels = {}, {}
    for child in children:
        for name, open_id in child["mention_info"].get("resolved", {}).items():
            accounts.setdefault(name, set()).add(open_id)
            labels.setdefault(open_id, set()).add(name)
    conflicts = {name for name, ids in accounts.items() if len(ids) > 1}
    conflicts.update(name for names in labels.values() if len(names) > 1 for name in names)
    for child in children:
        info = child["mention_info"]
        removed = {oid for name, oid in info.get("resolved", {}).items() if name in conflicts}
        candidate = {**info, "text_fallback_names": sorted(set(info.get("text_fallback_names", ())) | conflicts),
                     "fallback_reasons": {**info.get("fallback_reasons", {}),
                                          **{name: "identity_ambiguous" for name in conflicts}}}
        child["mention_info"] = normalize(info.get("names", ()), candidate)
        child["markdown"] = re.sub(r'<at user_id="(ou_[A-Za-z0-9]+)">(.*?)</at>',
                                    lambda m: m.group(2) if m.group(1) in removed else m.group(0), child["markdown"])
