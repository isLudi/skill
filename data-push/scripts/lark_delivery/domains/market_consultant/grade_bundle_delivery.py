"""Native multi-image posts with durable component claims and same-key retries."""
import hashlib
import json
from pathlib import Path

from ...common import im, reminders, resend
from ...common.runtime import run_lark
from ...common.values import _unwrap
from . import grade_bundle_source as source
from . import grade_report


def api(args):
    return _unwrap(json.loads(run_lark(args,timeout=60)))


def init(db):
    db.execute('CREATE TABLE IF NOT EXISTS bundle_messages (key TEXT PRIMARY KEY, slot TEXT, status TEXT, message_id TEXT, context_path TEXT, component_ids TEXT, detail TEXT)')
    db.commit()


def resolve_people(context):
    names = sorted({name for artifact in context['artifacts'] for reminder in artifact['reminders'] for name in reminder['names']})
    member_ids, member_error = set(), ''
    if names:
        try:
            members = api(['im','+chat-members-list','--chat-id',context['target']['chat_id'],
                '--member-types','user','--member-id-type','open_id','--page-all','--page-limit','10',
                '--as','bot','--format','json'])
            member_ids = {user['member_id'] for user in members['users']}
            if (members.get('has_more') is not False or members.get('truncations')
                    or len(member_ids) != members['user_total'] or not all(member_ids)):
                raise ValueError('Incomplete user membership')
        except Exception as exc:
            member_ids,member_error = set(),type(exc).__name__
    resolved,display,fallback = reminders.resolve_contacts([{'name':name} for name in names],api,member_ids=member_ids)
    if set(resolved) | set(fallback) != set(names) or set(resolved) & set(fallback):
        raise ValueError('Reminder coverage mismatch')
    return {'names':names,'resolved':resolved,'display_names':display,'fallback_reasons':fallback,'member_error':member_error}


def native_post(context,image_keys,people):
    content = [[{'tag':'text','text':f"截至dt={context['snapshot'][0]}，hour={context['snapshot'][1]}时"}]]
    for artifact,key in zip(context['artifacts'],image_keys):
        content.extend([[{'tag':'text','text':artifact['grade'],'style':['bold']}], [{'tag':'img','image_key':key}]])
        for reminder in artifact['reminders']:
            metric = '5min率' if context['section'] == 'process' else '截面单效'
            rank = '较低' if reminder['grain'] == '主管' or reminder.get('rank') == 'minimum_all_ties' else '位于底部10%'
            row = [{'tag':'text','text':reminder['channel']+'：'}]
            for index,name in enumerate(reminder['names']):
                if index:
                    row.append({'tag':'text','text':'、'})
                if name in people['resolved']:
                    row.append({'tag':'at','user_id':people['resolved'][name], 'user_name':people['display_names'].get(name,name)})
                else:
                    row.append({'tag':'text','text':name})
            row.append({'tag':'text','text':f'，{metric}{rank}。'})
            content.append(row)
    content.append([{'tag':'text','text':'继续加油，'},{'tag':'text','text':'【祝本期爆单】','style':['bold']},
                    {'tag':'text','text':' 🚀🔥'}])
    label = '过程' if context['section'] == 'process' else '转化'
    title=context.get('message_title') or f"🔥【{context['period']}】{context['definition']['components'][0]['grain']}{label}数据播报"
    return {'zh_cn':{'title':title,'content':content}}


def readback(message_id,context,detail):
    reply = api(['im','+messages-mget','--message-ids',message_id,'--no-reactions','--as','bot','--format','json'])
    matches = [msg for msg in reply.get('messages',[]) if msg.get('message_id') == message_id]
    if len(matches) != 1:
        raise ValueError('Bundle message readback missing or ambiguous')
    msg = matches[0]
    text = json.dumps(msg.get('content',''),ensure_ascii=False)
    if (msg.get('chat_id') != context['target']['chat_id'] or msg.get('deleted') is not False
            or msg.get('msg_type') != 'post' or msg['sender'].get('open_bot_id') != context['definition']['sender']['open_id']
            or context['period'] not in text or any(key not in text for key in detail['image_keys'])):
        raise ValueError('Bundle target/sender/period/images differ from staged message')
    actual = grade_report.mention_ids(msg.get('content','')) | grade_report.mention_ids({'mentions':msg.get('mentions',[])})
    if actual != set(detail['people']['resolved'].values()):
        raise ValueError('Bundle native reminder ID set differs')
    return {'message_id':message_id,'chat_id':msg['chat_id'],'sender':msg['sender'],
            'image_keys':detail['image_keys'],'mention_ids':sorted(actual),'verified':True}


def update(db,key,status,message_id,detail,context):
    encoded = json.dumps(detail,ensure_ascii=False)
    db.execute('UPDATE bundle_messages SET status=?,message_id=?,detail=? WHERE key=?',(status,message_id,encoded,key))
    for component in context['component_ids']:
        component_key = hashlib.sha256((key+'|'+component).encode()).hexdigest()[:40]
        db.execute('UPDATE deliveries SET status=?,message_id=?,detail=? WHERE key=?',(status,message_id,encoded,component_key))
    db.commit()


def send_staged(db,row,time_guard):
    key,slot,status,message_id,path,component_ids,encoded = row
    context = json.loads(Path(path).read_text(encoding='utf-8'))
    detail = json.loads(encoded)
    action = resend.decide(status,message_id)
    if action == resend.DONE:
        return {'status':'sent_verified','message_id':message_id,'component_ids':json.loads(component_ids)}
    if action == resend.REVERIFY:
        try:
            detail['readback'] = readback(message_id,context,detail)
            update(db,key,'sent_verified',message_id,detail,context)
            return {'status':'sent_verified','message_id':message_id,'component_ids':context['component_ids']}
        except Exception as exc:
            return {'status':'readback_failed','message_id':message_id,'reason':str(exc)[:240]}
    time_guard()
    source.guard(context)
    cfg = source.schedule_config(context['definition'],context['target'])
    from .upstream import verify_bot
    verify_bot(cfg)
    im.verify_sender_membership(context['target']['chat_id'],context['definition']['sender']['open_id'])
    for artifact in context['artifacts']:
        if hashlib.sha256(Path(artifact['path']).read_bytes()).hexdigest() != artifact['sha256']:
            raise ValueError('Prepared bundle PNG changed')
    if not detail.get('image_keys'):
        detail['image_keys'] = [im.upload_image(Path(artifact['path']),'bot',60) for artifact in context['artifacts']]
        update(db,key,'sending','',detail,context)
    if not detail.get('people'):
        detail['people'] = resolve_people(context)
    kept,late = reminders.refresh_membership(context['target']['chat_id'],detail['people']['resolved'])
    detail['people']['resolved'] = kept
    detail['people']['fallback_reasons'].update(late.get('fallback_reasons',{}))
    post = native_post(context,detail['image_keys'],detail['people'])
    detail['post'] = post
    update(db,key,'sending','',detail,context)
    source.guard(context)
    time_guard()
    api(['im','+messages-send','--chat-id',context['target']['chat_id'],'--msg-type','post',
        '--content',json.dumps(post,ensure_ascii=True),'--idempotency-key',key,'--as','bot','--format','json','--dry-run'])
    try:
        reply = api(['im','+messages-send','--chat-id',context['target']['chat_id'],'--msg-type','post',
            '--content',json.dumps(post,ensure_ascii=True),'--idempotency-key',key,'--as','bot','--format','json'])
        message_id = im._message_id(reply)
        if not message_id:
            raise ValueError('No message ID returned; keep the original idempotency key')
    except Exception as exc:
        detail['send_error'] = type(exc).__name__+': '+str(exc)[:250]
        update(db,key,'uncertain','',detail,context)
        raise
    update(db,key,'sent',message_id,detail,context)
    try:
        detail['readback'] = readback(message_id,context,detail)
        update(db,key,'sent_verified',message_id,detail,context)
        source.save(Path(context['directory'])/'delivery-receipt.json',{'status':'sent_verified',**detail['readback'],
            'component_ids':context['component_ids'],'reminders':detail['people'],'slot':slot,'idempotency_key':key})
        # Successful reads remain possible from the durable receipt; PNG cleanup is
        # independent of delivery state and never causes a replacement send.
        for artifact in context['artifacts']:
            try:
                Path(artifact['path']).unlink(missing_ok=True)
            except OSError:
                pass
        return {'status':'sent_verified','message_id':message_id,'component_ids':context['component_ids']}
    except Exception as exc:
        detail['readback_error'] = str(exc)[:250]
        update(db,key,'sent_unverified',message_id,detail,context)
        return {'status':'readback_failed','message_id':message_id,'reason':str(exc)[:250]}


def stage_and_send(db,context,slot_token,time_guard):
    scope = '|'.join([context['definition']['adapter'],context['definition']['channel_id'],context['target']['chat_id'],
                      slot_token,context['section'],','.join(sorted(context['component_ids']))])
    key = hashlib.sha256(scope.encode()).hexdigest()[:40]
    path = Path(context['directory'])/'context.json'
    db.execute('INSERT OR IGNORE INTO bundle_messages VALUES (?,?,?,?,?,?,?)',
        (key,slot_token,'sending','',str(path),json.dumps(context['component_ids']),json.dumps({})))
    for component in context['component_ids']:
        component_key = hashlib.sha256((key+'|'+component).encode()).hexdigest()[:40]
        db.execute('INSERT OR IGNORE INTO deliveries VALUES (?,?,?,?,?,?)',
            (component_key,slot_token,component,'sending','',json.dumps({'bundle_key':key})))
    db.commit()
    row = db.execute('SELECT * FROM bundle_messages WHERE key=?',(key,)).fetchone()
    return send_staged(db,row,time_guard)
