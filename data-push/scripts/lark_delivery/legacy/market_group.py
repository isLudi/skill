"""Compatibility API only. New channels use core/catalog, a department adapter and common ports."""
from __future__ import annotations
import argparse
import json
import sys
from typing import Any

from ..common.runtime import run_lark
from ..common.values import _json_payload, _unwrap, _iter_dicts, _find_first, _string, _number, _rate, _format_rate, _format_value
from ..common.images import _find_font, _center_text, _cleanup_local_image, _image_slots
from ..common.im import _message_id
from ..common import base as base_io, im as im_io
from ..domains.market_consultant import grade_report
from . import market_leads as lead_report
from ..domains.market_consultant.channels import self_incubated_koc_5 as broadcast_policy
from ..domains.market_consultant.style import _result_cell_fill, _retention_color
from ..paths import SKILL_ROOT
from .market_schema import PROCESS_FIELDS, TEXT_FIELDS, TEXT_SECTION_ORDER, HELPER_RAW_FIELDS, HELPER_DIMENSION_FIELDS, RESULT_FIELDS, RESULT_IMAGE_COLUMNS, RESULT_RATE_DENOMINATORS, RESULT_SUM_FIELDS, RESULT_BAR_FIELDS, RESULT_IMAGE_WIDTHS, IMAGE_COLUMNS, FIELD_ALIASES, RATE_NUMERATORS, RATE_FIELDS, BAR_FIELDS, IMAGE_WIDTHS, OUTCOME_TERMS, IMAGE_ROW_FILTER

SCRIPT_DIR = SKILL_ROOT / "scripts"

from . import market_aggregation
from .market_aggregation import _raw_field, _safe_period, _source_fields, select_period, select_rows, reminder_names, select_text_config, _display, available_image_columns, _weighted_rate, make_total_row, _sum_result_field, _result_ratio, _weighted_result_rate, _result_effect, _result_group_key, _aggregate_result_group, aggregate_result_rows, make_result_total_row, _result_bar_fraction, visible_image_rows, _image_value

from . import market_images
from .market_images import render_result_image, render_process_image

from . import market_messages
from .market_messages import _mention, _render_configured_reminder, _build_configured_markdown, build_markdown, idempotency_key

from . import market_source


def resolve_text_coordinates(*args, **kwargs):
    return market_source.resolve_text_coordinates(*args, services=sys.modules[__name__], **kwargs)


def fetch_records(*args, **kwargs):
    return market_source.fetch_records(*args, services=sys.modules[__name__], **kwargs)


def fetch_result_records(*args, **kwargs):
    return market_source.fetch_result_records(*args, services=sys.modules[__name__], **kwargs)


def fetch_text_records(*args, **kwargs):
    return market_source.fetch_text_records(*args, services=sys.modules[__name__], **kwargs)


def _read_channel_configs(*args, **kwargs):
    return market_source._read_channel_configs(*args, services=sys.modules[__name__], **kwargs)


def list_channels(*args, **kwargs):
    return market_source.list_channels(*args, services=sys.modules[__name__], **kwargs)

from . import market_contacts
from .market_contacts import _load_mention_map, _user_candidates


def resolve_mentions(*args, **kwargs):
    return market_contacts.resolve_mentions(*args, services=sys.modules[__name__], **kwargs)

from . import market_helper
from .market_helper import _dimension_record


def sync_helper_dimension(*args, **kwargs):
    return market_helper.sync_helper_dimension(*args, services=sys.modules[__name__], **kwargs)

from . import market_prepare


def prepare_lead_report(*args, **kwargs):
    return market_prepare.prepare_lead_report(*args, services=sys.modules[__name__], **kwargs)


def prepare_summary_view(*args, **kwargs):
    return market_prepare.prepare_summary_view(*args, services=sys.modules[__name__], **kwargs)


def prepare(*args, **kwargs):
    return market_prepare.prepare(*args, services=sys.modules[__name__], **kwargs)

from . import market_ledger
from .market_ledger import _ledger_records, _append_ledger

from . import market_cli
from .market_cli import _state_dir, push_defaults, effective_mention_target, print_preview


def add_common_arguments(*args, **kwargs):
    return market_cli.add_common_arguments(*args, services=sys.modules[__name__], **kwargs)


def main(*args, **kwargs):
    return market_cli.main(*args, services=sys.modules[__name__], **kwargs)


def verify_grade_bot_identity() -> None:
    status = json.loads(run_lark(["auth", "status", "--json", "--verify"], timeout=60))
    bot = status.get("identities", {}).get("bot", {})
    if not bot.get("verified") or bot.get("openId") != broadcast_policy.BOT_OPEN_ID:
        raise ValueError("当前CLI机器人不是已核验的管家身份")


def resolve_coordinates(args):
    return base_io.resolve_coordinates(args, runner=run_lark)


def _fetch_view_records(coords, args, fields, *, temp_prefix, filter_json=None, audit=None):
    return base_io._fetch_view_records(coords, args, fields, temp_prefix=temp_prefix,
                                       filter_json=filter_json, audit=audit, runner=run_lark)


def verify_chat(chat_id, chat_name, identity, timeout):
    return im_io.verify_chat(chat_id, chat_name, identity, timeout, runner=run_lark)


def mention_nonmembers(chat_id, resolved, identity, timeout):
    return im_io.mention_nonmembers(chat_id, resolved, identity, timeout, runner=run_lark)


def upload_image(image_path, identity, timeout):
    return im_io.upload_image(image_path, identity, timeout, runner=run_lark)


def send_markdown(chat_id, markdown, key, identity, *, dry_run, timeout):
    return im_io.send_markdown(chat_id, markdown, key, identity, dry_run=dry_run, timeout=timeout, runner=run_lark)


def prepare_grade_report(args: argparse.Namespace) -> dict[str, Any]:
    from ..core import catalog
    from ..domains.market_consultant.workflow import prepare_report

    definition = catalog.load_channel(catalog.DEFAULT_CHANNEL)
    return prepare_report(args, definition, services=sys.modules[__name__])


if __name__ == "__main__":
    raise SystemExit(main())
