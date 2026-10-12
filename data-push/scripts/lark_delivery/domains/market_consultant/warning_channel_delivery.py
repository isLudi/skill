"""Independent warning channel state, staging and durable delivery."""
from __future__ import annotations

from datetime import datetime, timedelta
import hashlib
import json

from ...common.im import upload_image, _message_id, mention_nonmembers
from ...core.catalog import load_channel
from .delivery_ledger import connect_ledger, delivery_key, claim
from . import warning_adapter as wa, warning_data as wd, warning_upstream as wu
from . import warning_routes as routes
from . import warning_card_message as cards


def now():
    return datetime.now(wu.TZ)


def state_for(definition, route):
    return routes.state_for(definition, route)


def existing_outcome(definition, route, slot, kind):
    target, channel = route['target'], route['channel']
    db = connect_ledger(state_for(definition, route))
    try:
        key = delivery_key(wa.schedule_config(definition, target), slot, channel, kind)
        prior = db.execute('SELECT status,message_id FROM deliveries WHERE key=?', (key,)).fetchone()
        if not prior:
            return None
        status = prior[0] if prior[0] in {'sent_verified', 'skipped_no_source_rows'} else 'blocked_previous_attempt'
        return {'status': status, 'reason': 'Existing daily claim; never resend blindly', 'message_id': prior[1]}
    finally:
        db.close()


def mark_absent(definition, route, slot, kind, evidence):
    target, channel = route['target'], route['channel']
    db = connect_ledger(state_for(definition, route))
    try:
        key = delivery_key(wa.schedule_config(definition, target), slot, channel, kind)
        if not claim(db, key, slot, channel):
            raise ValueError('Another process already claimed this channel slot')
        db.execute("UPDATE deliveries SET status='skipped_no_source_rows',detail=? WHERE key=?",
                   (json.dumps({'execution_id': evidence['execution_id']}), key))
        db.commit()
    finally:
        db.close()


def prepare_channel(definition, route, source, kind, preflight):
    context = wa.prepare(definition, route['target'], channel=route['channel'], report_type=kind,
                         state_dir=state_for(definition, route) / ('preflight' if preflight else 'batches'),
                         scheduled=not preflight, shared_source=source)
    context['files'] = wa.write_preview(context)
    return context


def stage_upload(context, slot):
    definition, target = context['definition'], context['target']
    if load_channel(wa.KEY) != definition:
        raise ValueError('Canonical warning configuration changed during preparation')
    validate_routing(context)
    if now() >= slot + timedelta(minutes=1):
        raise ValueError('Daily send window expired before upload')
    if hashlib.sha256(context['image'].read_bytes()).hexdigest() != context['receipt']['image_sha256']:
        raise ValueError('Prepared channel image changed')
    if cards.fingerprint(context['card']) != context['receipt']['message_card_sha256']:
        raise ValueError('Prepared channel card changed')
    cards.validate(context['card'], context['mentions'])
    refresh_reminders(context)
    if now() >= slot + timedelta(minutes=1):
        raise ValueError('Daily send window expired after reminder verification')
    image_key = upload_image(context['image'], 'bot', 45)
    key = delivery_key(wa.schedule_config(definition, target), slot, context['channel'], context['kind'])
    payload = {'chat_id': target['chat_id'], 'message_type': 'interactive',
               'card': cards.materialize(context['card'], image_key, context['mentions']),
               'idempotency_key': key, 'image_key': image_key, 'slot': slot.isoformat()}
    wd.save(context['root'] / 'send_payload.json', payload)
    context['send_payload'] = payload
    return context


def refresh_reminders(context):
    """Keep the audited image and replace unverifiable card @ with plain names."""
    evidence = context['mentions']
    targets = {name: person['open_id'] for name, person in evidence['resolved'].items()}
    if not targets:
        return
    error = ''
    try:
        absent = set(mention_nonmembers(context['target']['chat_id'], targets, 'bot', 60))
    except Exception as exc:
        absent, error = set(targets), type(exc).__name__
    if not absent:
        return
    for name in absent:
        person = evidence['resolved'].pop(name)
        evidence.setdefault('fallback_names', {})[name] = {
            'display_name': person['display_name'],
            'reason': 'Chat membership not verified' if error else 'No longer in target chat'}
    evidence['all_reminder_people_in_chat'] = not evidence['fallback_names']
    if error:
        evidence.update(member_read_complete=False, member_lookup_error=error)
    image_sha256 = context['receipt']['image_sha256']
    wd.save(context['root'] / 'mention_evidence.json', evidence)
    context['files'] = wa.write_preview(context)
    if context['receipt']['image_sha256'] != image_sha256:
        raise ValueError('Reminder fallback changed the audited warning image')
    validate_routing(context)
    cards.validate(context['card'], evidence)


def verify_message(definition, target, message_id, markdown, mentions, image_key):
    is_card = isinstance(markdown, dict)
    native = None
    if is_card:
        cards.validate(markdown, mentions, image_key=image_key)
        native = cards.read_original(message_id)
        items = native.get('data', {}).get('items', [])
        if (native.get('identity') != 'bot' or len(items) != 1
                or items[0].get('message_id') != message_id or items[0].get('chat_id') != target['chat_id']
                or items[0].get('msg_type') != 'interactive' or items[0].get('deleted') is not False
                or json.loads(items[0]['body']['content']) != markdown):
            raise ValueError('Warning card original JSON readback differs from the sent card')
    response = wd.api(['im', '+messages-mget', '--message-ids', message_id,
                       '--no-reactions', '--as', 'bot', '--format', 'json'])
    messages = response['data']['messages']
    if response.get('identity') != 'bot' or response['data']['total'] != 1 or len(messages) != 1:
        raise ValueError('Warning message readback missing or ambiguous')
    message = messages[0]
    expected_mentions = {p['open_id'] for p in mentions['resolved'].values()}
    if (message['message_id'] != message_id or message['chat_id'] != target['chat_id']
            or message.get('deleted') is not False or message.get('msg_type') != ('interactive' if is_card else 'post')
            or message['sender'].get('open_bot_id') != definition['sender']['open_id']
            or message['sender'].get('name') != definition['sender']['name']
            or (not is_card and (message['content'].strip() != markdown.strip() or image_key not in message['content']))
            or {m['id'] for m in message.get('mentions', [])} != expected_mentions
            or len(message.get('mentions', [])) != len(expected_mentions)):
        raise ValueError('Warning content, image, sender or mentions do not match')
    if native is not None:
        response['original_card_readback'] = native
    return response


def send_channel(context, slot):
    definition, target, channel = context['definition'], context['target'], context['channel']
    payload = context['send_payload']
    key, message_id, claimed = payload['idempotency_key'], '', False
    validate_routing(context)
    db = connect_ledger(state_for(definition, context['route']))
    try:
        if load_channel(wa.KEY) != definition or not slot <= now() < slot + timedelta(minutes=1):
            raise ValueError('Configuration changed or daily send window expired')
        if (payload['chat_id'] != target['chat_id'] or payload.get('message_type') != 'interactive'
                or cards.fingerprint(context['card']) != context['receipt']['message_card_sha256']
                or payload['card'] != cards.materialize(context['card'], payload['image_key'], context['mentions'])):
            raise ValueError('Staged warning card differs from the reviewed report and group')
        if not claim(db, key, slot, channel):
            return {'status': 'blocked_previous_attempt', 'reason': 'Another process claimed this channel slot'}
        claimed = True
        response = cards.send(target['chat_id'], payload['card'], key, context['root'])
        message_id = _message_id(response)
        wd.save(context['root'] / 'send_response.json', response)
        if not message_id.startswith('om_'):
            raise ValueError('Send acknowledged without a verifiable message id')
        receipt = {'status': 'sent_pending_readback', 'message_id': message_id, 'slot': slot.isoformat(),
                   'channel': channel, 'report_id': context['route']['id'],
                   'included_grades': context['route']['included_grades'],
                   'report_kind': context['kind'], 'source_rev': context['source_rev'],
                   'execution_id': context['evidence']['execution_id'],
                   'current_snapshot': context['data']['current_snapshot'],
                   'image_sha256': context['receipt']['image_sha256'], 'image_key': payload['image_key'],
                   'message_type': 'interactive', 'card_schema': '2.0',
                   'message_card_sha256': cards.fingerprint(payload['card']),
                   'chat_id': target['chat_id'], 'sender_open_id': definition['sender']['open_id'],
                   'plain_name_reminders': context['receipt'].get('plain_name_reminders', []),
                   'mentions': {n: p['open_id'] for n, p in context['mentions']['resolved'].items()}}
        db.execute("UPDATE deliveries SET status='sent_pending_readback',message_id=?,detail=? WHERE key=?",
                   (message_id, json.dumps(receipt, ensure_ascii=True), key))
        db.commit()
        wd.save(context['root'] / 'delivery_receipt.json', receipt)
        readback = verify_message(definition, target, message_id, payload['card'],
                                  context['mentions'], payload['image_key'])
        wd.save(context['root'] / 'message_readback.json', readback)
        receipt.update(status='sent_verified', verified_at=now().isoformat())
        wd.save(context['root'] / 'delivery_receipt.json', receipt)
        db.execute("UPDATE deliveries SET status='sent_verified',detail=? WHERE key=?",
                   (json.dumps(receipt, ensure_ascii=True), key))
        db.commit()
        # Delete only this delivered generated PNG after its hash and receipt
        # are durable; retain the local preview PNGs until an actual delivery.
        image = context['image'].resolve()
        if image.is_relative_to(context['root'].resolve()):
            image.unlink(missing_ok=True)
        return {'status': 'sent_verified', 'message_id': message_id, 'report_kind': context['kind'],
                'receipt': str(context['root'] / 'delivery_receipt.json')}
    except Exception as exc:
        status = 'readback_failed' if message_id else 'send_uncertain' if claimed else 'blocked_delivery'
        if claimed:
            db.execute('UPDATE deliveries SET status=?,message_id=? WHERE key=?', (status, message_id, key))
            db.commit()
        return {'status': status, 'reason': str(exc)[:1000], 'message_id': message_id}
    finally:
        db.close()


def validate_routing(context):
    """Check the prepared scope again before every external write."""
    route = routes.for_target(context['definition'], context['target'], context['channel'])
    data = context['data']
    if (route != context['route'] or data['delivery_route_id'] != route['id']
            or data['included_grades'] != route['included_grades']
            or data['target_chat_id'] != route['target']['chat_id']
            or context['receipt']['target_chat_id'] != route['target']['chat_id']
            or context['mentions']['chat_id'] != route['target']['chat_id']):
        raise ValueError('Prepared warning report no longer matches its channel, grade scope and group')
