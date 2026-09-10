"""Injectable CLI boundary shared by department workflows; no metric or period rules."""
from .runtime import run_lark
from . import base, im
from .values import _json_payload, _unwrap, _iter_dicts, _find_first, _string
from .images import _image_slots, _cleanup_local_image
from .im import _message_id


def resolve_coordinates(args):
    return base.resolve_coordinates(args, runner=run_lark)


def _fetch_view_records(coords, args, fields, *, temp_prefix, filter_json=None, audit=None):
    return base._fetch_view_records(coords, args, fields, temp_prefix=temp_prefix,
                                   filter_json=filter_json, audit=audit, runner=run_lark)


def verify_chat(chat_id, chat_name, identity, timeout):
    return im.verify_chat(chat_id, chat_name, identity, timeout, runner=run_lark)


def mention_nonmembers(chat_id, resolved, identity, timeout):
    return im.mention_nonmembers(chat_id, resolved, identity, timeout, runner=run_lark)


def upload_image(path, identity, timeout):
    return im.upload_image(path, identity, timeout, runner=run_lark)


def send_markdown(chat_id, markdown, key, identity, *, dry_run, timeout):
    return im.send_markdown(chat_id, markdown, key, identity, dry_run=dry_run, timeout=timeout, runner=run_lark)
