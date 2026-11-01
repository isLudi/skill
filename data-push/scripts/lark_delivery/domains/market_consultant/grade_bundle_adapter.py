"""Registered adapter for the twelve approved grade-first market intake rules."""
from datetime import datetime
import hashlib
from pathlib import Path

from .channels.grade_compact import TZ, scheduled_report_type
from . import grade_bundle_model as model
from . import grade_bundle_render as rendering
from . import grade_bundle_source as source

PROFILE = 'grade-channel-bundle-v2'
ARTIFACT_PROTOCOL = 'market-grade-bundle-artifacts-v2'
TARGETS = {
    'grade9_supervisor_bundle': 'oc_3be9b914593ba873276cc5aa0a5007fc',
    'localization_advisor_bundle': 'oc_b5dee8b192c11bb8a131ce40c41d5236',
    'high_school_supervisor_bundle': 'oc_02c06f4930147a91d723c46c71bfe6fc',
    'douyin_advisor_bundle': 'oc_a159e70010444751498f793d617d98e8',
}


def validate_definition(definition):
    channel_id = definition['channel_id']
    if (definition.get('domain') != 'market_consultant' or definition.get('adapter') != 'market-grade-bundle-v2'
            or channel_id not in TARGETS or len(definition['targets']) != 1
            or definition['targets'][0]['chat_id'] != TARGETS[channel_id]):
        raise ValueError('Unreviewed grade-bundle target or department')
    if (definition['source']['report_profile'] != PROFILE
            or definition['source']['raw_table_id'] != 'tbljWRvaqKTdrCx4'
            or definition['report']['artifact_protocol'] != ARTIFACT_PROTOCOL
            or definition['report']['process_weekdays'] != [0,1,2,3]
            or definition['report']['result_weekdays'] != [4,5,6]):
        raise ValueError('Bundle source, artifact protocol or calendar drift')
    if definition['sender'] != {'identity':'bot','name':'管家','open_id':'ou_f3907e865135732c15a1dfce27828411'}:
        raise ValueError('Bundle sender changed')
    schedule = definition['schedule']
    if (schedule['kind'] != 'grade_bundle_twice_daily' or schedule['hours'] != [14,19]
            or schedule['upstream_hours'] != {'14':13,'19':17}
            or schedule['prepare_minute'] != 0 or schedule['send_minute'] != 0
            or schedule['retry_minutes'] != 2 or schedule['deadline_minute'] != 50):
        raise ValueError('Bundle daily schedule drift')
    components = definition['components']
    if not components or len({c['id'] for c in components}) != len(components):
        raise ValueError('Missing or repeated bundle component')
    report = definition['report']
    style = report.get('image_style', 'legacy-v2')
    if style not in {'legacy-v2', 'compact-original-colors-v1'}:
        raise ValueError('Unreviewed grade-bundle image style')
    if style == 'compact-original-colors-v1' and (
            report.get('show_totals') is not True or report.get('total_scope') != 'visible_rows'
            or report.get('show_population_labels') is not False):
        raise ValueError('Compact layout requires reviewed visible-row totals without population labels')
    for component in components:
        if (component['label'] not in definition['channels'] or component['minimum_post_leads'] != 5
                or not isinstance(component.get('show_totals'), bool)
                or component['show_totals'] is not report['show_totals'] or not component['source_values']
                or component['match'] not in {'any_exact','casefold_exact'}
                or component['grain'] not in {'主管','顾问'} or not component['grades']):
            raise ValueError('Unreviewed bundle component scope')
        if component['match'] == 'casefold_exact' and component['source_values'] != ['app']:
            raise ValueError('Casefold matching is limited to APP')
        for kind in ['process','result']:
            model.columns(component,kind)
    return definition


schedule_config = source.schedule_config


def channels_for_target(definition, target):
    return [definition['channel']]


def prepare(definition, target, *, state_dir=None, report_type='auto', slot=None,
            period=None, component_ids=None, **_unused):
    validate_definition(definition)
    if target not in definition['targets']:
        raise ValueError('Target is not registered for this bundle')
    at = datetime.now(TZ)
    section = scheduled_report_type(at) if report_type == 'auto' else report_type
    if section not in {'process','result'}:
        raise ValueError('A bundle prepares exactly one report section')
    directory = Path(state_dir or definition['state_dir'])
    directory.mkdir(parents=True,exist_ok=True)
    rows,proof = source.read(definition,target,directory,slot)
    if period is not None and period != proof['period']:
        raise ValueError('Bundle period cannot depart from current business calendar')
    components = [c for c in definition['components'] if component_ids is None or c['id'] in component_ids]
    if component_ids is not None and {c['id'] for c in components} != set(component_ids):
        raise ValueError('Unregistered component selection')
    results,outcomes = model.calculate(rows,proof['evidence'],proof['period'],section,components)
    results,artifacts = rendering.render(results,section,proof['period'],target['display_name'],directory/'images',outcomes,
                                        style=definition['report'].get('image_style','legacy-v2'))
    for artifact in artifacts:
        artifact['sha256'] = hashlib.sha256(Path(artifact['path']).read_bytes()).hexdigest()
    context = {'definition':definition,'definition_sha256':source.fingerprint(definition),'target':target,
        'source':proof,'snapshot':proof['snapshot'],'period':proof['period'],'section':section,
        'directory':str(directory),'artifact_protocol':ARTIFACT_PROTOCOL,'outcomes':outcomes,
        'component_ids':[result['component']['id'] for result in results], 'artifacts':artifacts,
        'skip_delivery':not artifacts,'results':results,'prepared_at':at.isoformat()}
    source.save(directory/'context.json',context)
    return context


write_preview = rendering.write_preview


def send_now(definition,target,request_id,*,preflight=False):
    from .grade_bundle_runner import run
    return run(definition,target,request_id=request_id,preflight=preflight)


def schedule(definition,target,*,preflight=False):
    from .grade_bundle_runner import run
    return run(definition,target,preflight=preflight)
