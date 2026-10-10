"""One daily slot, one durable send claim, complete bot message readback."""
from __future__ import annotations

from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import time

from ...core.catalog import load_channel
from ...core.locks import runner_lock
from ...common.im import upload_image, send_markdown, _message_id, mention_nonmembers
from ...common.push_log import run_scope
from .delivery_ledger import connect_ledger, delivery_key, claim, record_outcome
from . import warning_adapter as wa, warning_data as wd, warning_upstream as wu
from .upstream import verify_bot


def now():
    return datetime.now(wu.TZ)


def verify_message(definition, target, message_id, markdown, mentions, image_key):
    response = wd.api(['im', '+messages-mget', '--message-ids', message_id,
                       '--no-reactions', '--as', 'bot', '--format', 'json'])
    messages = response['data']['messages']
    if response.get('identity') != 'bot' or response['data']['total'] != 1 or len(messages) != 1:
        raise ValueError('Warning message readback missing or ambiguous')
    message = messages[0]
    expected_mentions = {p['open_id'] for p in mentions['resolved'].values()}
    if (message['message_id'] != message_id or message['chat_id'] != target['chat_id']
            or message.get('deleted') is not False or message.get('msg_type') != 'post'
            or message['sender'].get('open_bot_id') != definition['sender']['open_id']
            or message['sender'].get('name') != definition['sender']['name']
            or message['content'].strip() != markdown.strip() or image_key not in message['content']
            or {m['id'] for m in message.get('mentions', [])} != expected_mentions
            or len(message.get('mentions', [])) != len(expected_mentions)):
        raise ValueError('Warning message content, image, sender or mentions do not match')
    return response


def run(definition, target, preflight=False):
    wa.validate_definition(definition)
    started = now()
    cfg = wa.schedule_config(definition, target)
    state = Path(definition['state_dir'])
    slot = started.replace(hour=17, minute=50, second=0, microsecond=0)
    first = datetime.fromisoformat(definition['schedule']['first_send_at'])
    live = state / 'live-status.json'
    with run_scope(definition['domain'], definition['channel_id'], cfg['windows_task_name'], started) as log:
        with runner_lock(state) as locked:
            db = connect_ledger(state)
            def outcome(status, reason='', **extra):
                record_outcome(db, now().isoformat(), slot, definition['channel'], status, reason)
                log.event('channel_outcome', channel=definition['channel'], status=status, reason=reason,
                          slot=slot.isoformat(), **extra)
                log.outcome(definition['channel'], status, reason, **extra)
                log.exit_code = 0 if status in {'prepared','sent_verified','skipped_no_source_rows'} else 1
                return {'status': status, 'reason': reason, 'slot': slot.isoformat(), **extra}
            claimed, key = False, None
            try:
                if not locked:
                    return outcome('blocked_parallel_run', 'Process lock already held; no send attempted')
                if preflight:
                    context = wa.prepare(definition, target, state_dir=state / 'preflight', scheduled=False)
                    files = wa.write_preview(context)
                    return outcome('prepared', 'Read-only preflight; no upload or send', files=files)
                if not definition['schedule']['enabled'] or not target['enabled']:
                    return outcome('prepared', 'Schedule or target paused; no send')
                if slot < first:
                    return outcome('prepared', 'Before the explicitly configured first daily slot')
                if not slot - timedelta(minutes=5) <= started < slot + timedelta(minutes=1):
                    return outcome('blocked_outside_slot', 'Only prepare 17:45–17:50 and send during 17:50; no catch-up')
                kind = wa.report_kind(definition, started)
                key = delivery_key(cfg, slot, definition['channel'], kind)
                prior = db.execute('SELECT status,message_id FROM deliveries WHERE key=?', (key,)).fetchone()
                if prior:
                    if prior[0] in {'sent_verified','skipped_no_source_rows'}:
                        return outcome(prior[0], 'This daily slot is already handled; no resend', message_id=prior[1])
                    return outcome('blocked_previous_attempt', 'Existing send claim requires readback; never resend blindly', message_id=prior[1])
                wd.save(live, {'status': 'preparing', 'slot': slot.isoformat(), 'report_kind': kind, 'started_at': started.isoformat()})
                context = wa.prepare(definition, target, state_dir=state / 'batches', scheduled=True)
                files = wa.write_preview(context)
                if context['skip_delivery']:
                    if claim(db, key, slot, definition['channel']):
                        db.execute("UPDATE deliveries SET status='skipped_no_source_rows',detail=? WHERE key=?",
                                   (json.dumps({'execution_id': context['evidence']['execution_id']}), key))
                        db.commit()
                    return outcome('skipped_no_source_rows', 'Full successful current source has no eligible current channel post leads')
                if load_channel(wa.KEY) != definition:
                    raise ValueError('Canonical channel configuration changed during preparation')
                # Read current publication/history again before the only possible send.
                wu.publication(definition)
                latest = wu.history(definition, slot, scheduled=True)
                if latest['id'] != context['evidence']['execution_id']:
                    raise ValueError('Newer warning producer replaced the prepared data')
                verify_bot(cfg)
                targets = {name: person['open_id'] for name, person in context['mentions']['resolved'].items()}
                if mention_nonmembers(target['chat_id'], targets, 'bot', 60):
                    raise ValueError('Reminder targets left the group after preparation')
                wd.unchanged(definition, context['root'] / 'revision-check', context['source_rev'])
                if now() >= slot + timedelta(minutes=1):
                    raise ValueError('Preparation finished after the daily send window')
                if hashlib.sha256(context['image'].read_bytes()).hexdigest() != context['receipt']['image_sha256']:
                    raise ValueError('Prepared warning image changed')
                image_key = upload_image(context['image'], 'bot', 45)
                markdown = context['markdown'].replace('(' + context['image'].name + ')', '(' + image_key + ')')
                wd.save(context['root'] / 'send_payload.json', {'chat_id': target['chat_id'], 'markdown': markdown,
                        'idempotency_key': key, 'image_key': image_key, 'slot': slot.isoformat()})
                wd.save(live, {'status': 'waiting_for_17_50', 'slot': slot.isoformat(), 'files': files})
                while now() < slot:
                    time.sleep(min(1, (slot - now()).total_seconds()))
                if now() >= slot + timedelta(minutes=1):
                    raise ValueError('Daily send window expired; no late send')
                if load_channel(wa.KEY) != definition:
                    raise ValueError('Channel paused or changed while waiting for the daily slot')
                if wu.history(definition, slot, scheduled=True)['id'] != context['evidence']['execution_id']:
                    raise ValueError('Producer started another execution before the daily send')
                wd.unchanged(definition, context['root'] / 'send-revision-check', context['source_rev'])
                if now() >= slot + timedelta(minutes=1):
                    raise ValueError('Final source check exceeded the send window')
                if not claim(db, key, slot, definition['channel']):
                    return outcome('blocked_previous_attempt', 'Another process already claimed this slot')
                claimed = True
                response = send_markdown(target['chat_id'], markdown, key, 'bot', dry_run=False, timeout=45)
                message_id = _message_id(response)
                wd.save(context['root'] / 'send_response.json', response)
                if not message_id.startswith('om_'):
                    raise ValueError('Send acknowledged without a verifiable message id')
                db.execute("UPDATE deliveries SET status='sent_pending_readback',message_id=?,detail=? WHERE key=?",
                           (message_id, json.dumps({'image_key': image_key, 'batch': str(context['root'])}), key))
                db.commit()
                readback = verify_message(definition, target, message_id, markdown, context['mentions'], image_key)
                wd.save(context['root'] / 'message_readback.json', readback)
                receipt = {'status': 'sent_verified', 'message_id': message_id, 'slot': slot.isoformat(),
                           'report_kind': kind, 'source_rev': context['source_rev'],
                           'execution_id': context['evidence']['execution_id'], 'current_snapshot': context['data']['current_snapshot'],
                           'image_sha256': context['receipt']['image_sha256'], 'image_key': image_key,
                           'chat_id': target['chat_id'], 'sender_open_id': definition['sender']['open_id'],
                           'mentions': targets, 'verified_at': now().isoformat()}
                wd.save(context['root'] / 'delivery_receipt.json', receipt)
                db.execute("UPDATE deliveries SET status='sent_verified',detail=? WHERE key=?", (json.dumps(receipt), key))
                db.commit()
                return outcome('sent_verified', message_id=message_id, report_kind=kind, receipt=str(context['root'] / 'delivery_receipt.json'))
            except Exception as exc:
                status = 'send_uncertain' if claimed else 'blocked_before_send'
                if claimed:
                    db.execute('UPDATE deliveries SET status=? WHERE key=?', (status, key))
                    db.commit()
                return outcome(status, str(exc)[:1000])
            finally:
                if locked:
                    live.unlink(missing_ok=True)
                db.close()
