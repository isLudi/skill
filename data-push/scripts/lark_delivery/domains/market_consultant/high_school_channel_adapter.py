"""High-school channel-first cards using the approved raw-data calculation path."""
from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path

from . import grade_bundle_adapter as grouped
from . import grade_bundle_model as model
from . import grade_bundle_source as source
from . import high_school_channel_card as card
from .high_school_channel_render import render_channel
from .channels.grade_compact import TZ, scheduled_report_type

ADAPTER = 'market-highschool-channel-v1'
ARTIFACT_PROTOCOL = 'market-channel-grade-artifacts-v1'


def validate_definition(definition):
    if definition.get('adapter') != ADAPTER or definition.get('channel_id') != 'high_school_supervisor_bundle':
        raise ValueError('Channel-first adapter is limited to the approved high-school group')
    base = deepcopy(definition)
    base['adapter'] = 'market-grade-bundle-v2'
    base['report']['artifact_protocol'] = grouped.ARTIFACT_PROTOCOL
    grouped.validate_definition(base)
    report = definition['report']
    if (report.get('artifact_protocol') != ARTIFACT_PROTOCOL or report.get('layout') != 'channel_then_grade'
            or report.get('message_unit') != 'logical_channel' or report.get('image_unit') != 'logical_channel_all_grades'
            or report.get('message_format') != 'interactive_card_2' or report.get('reminder_group') != 'grade'):
        raise ValueError('Channel-first message protocol drift')
    expected = {'external_koc':['KOC-周帅数学','KOC-孟亚飞数学'],
                'draft_21_1':['自孵化KOC-5元纯课'], 'draft_22_1':['app'], 'draft_23_1':['人工外呼','唐山TMK']}
    if {component['id']:component['source_values'] for component in definition['components']} != expected:
        raise ValueError('Unreviewed channel union')
    return definition


schedule_config = source.schedule_config


def channels_for_target(definition, target):
    return definition['channels']


def prepare(definition, target, *, state_dir=None, report_type='auto', slot=None,
            period=None, component_ids=None, channel=None, **_unused):
    validate_definition(definition)
    if target not in definition['targets']:
        raise ValueError('Unregistered high-school channel target')
    components = [component for component in definition['components']
                  if (component_ids is None or component['id'] in component_ids)
                  and (channel is None or component['label'] == channel)]
    if len(components)!=1 or (component_ids is not None and component_ids != [components[0]['id']]):
        raise ValueError('Prepare exactly one registered logical channel')
    at = datetime.now(TZ)
    section = scheduled_report_type(at) if report_type=='auto' else report_type
    if section not in {'process','result'}:
        raise ValueError('Prepare one process or conversion section')
    directory = Path(state_dir or definition['state_dir'])
    directory.mkdir(parents=True,exist_ok=True)
    rows,proof = source.read(definition,target,directory,slot)
    if period is not None and period != proof['period']:
        raise ValueError('The current business period is required')
    results,outcomes = model.calculate(rows,proof['evidence'],proof['period'],section,components)
    if outcomes[components[0]['id']]['status'] == 'blocked_prepare':
        raise ValueError(outcomes[components[0]['id']]['reason'])
    artifacts = []
    if results:
        artifact,_checks = render_channel(results[0],section,proof['period'],directory/'images')
        artifacts.append(artifact)
    context = {'definition':definition,'definition_sha256':source.fingerprint(definition),'target':target,
        'source':proof,'snapshot':proof['snapshot'],'period':proof['period'],'section':section,
        'directory':str(directory),'artifact_protocol':ARTIFACT_PROTOCOL,'message_type':'interactive',
        'outcomes':outcomes,'component_ids':[result['component']['id'] for result in results],
        'artifacts':artifacts,'skip_delivery':not artifacts,'results':results,'prepared_at':at.isoformat()}
    source.save(directory/'context.json',context)
    return context


write_preview = card.write_preview


def dry_run(context):
    from . import grade_bundle_delivery as delivery
    people = delivery.resolve_people(context)
    payload = card.build(context,['LOCAL_PREVIEW_IMAGE_KEY'],people)
    return delivery.api(['im','+messages-send','--chat-id',context['target']['chat_id'],
        '--msg-type','interactive','--content',json.dumps(payload,ensure_ascii=True),
        '--as','bot','--format','json','--dry-run'])


def round_once(*args, **kwargs):
    from .high_school_channel_runner import round_once as run_round
    return run_round(*args, **kwargs)


def send_now(definition,target,request_id,*,preflight=False):
    from .grade_bundle_runner import run
    return run(definition,target,request_id=request_id,preflight=preflight)


def schedule(definition,target,*,preflight=False):
    from .grade_bundle_runner import run
    return run(definition,target,preflight=preflight)
