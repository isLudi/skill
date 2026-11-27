"""Audit and render each grade-nine period separately without changing source dates."""
from datetime import datetime
import hashlib
from pathlib import Path

from . import grade9_daily_policy as policy
from . import grade_bundle_model as model
from . import grade_bundle_render as rendering
from . import grade_bundle_source as source
from .channels.grade_compact import TZ, business_period, next_business_period, scheduled_report_type


def build_period(definition, target, rows, proof, directory, at, specification, components):
    policy.validate(definition)
    report_period, section = specification['period'], specification['section']
    if report_period not in proof['evidence']['periods']:
        results = []
        outcomes = {item['id']: {'status': 'blocked_source_period', 'channel': item['label'],
            'reason': 'Required report period has no upstream audit: ' + report_period} for item in components}
    else:
        results, outcomes = model.calculate(rows, proof['evidence'], report_period, section, components)
        kept = []
        for result in results:
            try:
                kept.append(policy.apply(result, specification, at.weekday()))
            except Exception as exc:
                item = result['component']
                outcomes[item['id']] = {'status': 'blocked_prepare', 'channel': item['label'],
                    'reason': 'standard evaluation: ' + type(exc).__name__ + ': ' + str(exc)[:200]}
        results = kept
    results, artifacts = rendering.render(results, section, report_period, target['display_name'],
        Path(directory) / 'images', outcomes, style=definition['report']['image_style'])
    for artifact in artifacts:
        audits = [audit for result in results if result['component']['id'] in artifact['component_ids']
                  for audit in result['grade9_audits'] if audit['grade'] == artifact['grade']]
        lookup = {audit['channel']: audit for audit in audits}
        artifact['standards'] = [{name: audit[name] for name in ['channel', 'metric', 'target']}
                                for audit in audits if audit['target'] is not None]
        for reminder in artifact['reminders']:
            audit = lookup[reminder['channel']]
            reminder.update(metric=audit['metric'], standard=audit['target'])
        artifact['period'] = report_period
        artifact['sha256'] = hashlib.sha256(Path(artifact['path']).read_bytes()).hexdigest()
    label = {'current_process': '本期过程', 'current_conversion': '本期转化', 'next_process': '下期过程'}[specification['role']]
    context = {'definition': definition, 'definition_sha256': source.fingerprint(definition), 'target': target,
        'source': proof, 'snapshot': proof['snapshot'], 'period': proof['period'], 'report_period': report_period,
        'section': section, 'directory': str(directory), 'artifact_protocol': definition['report']['artifact_protocol'],
        'grade9_role': specification['role'], 'grade9_policy_date': at.date().isoformat(), 'grade9_weekday': at.weekday(),
        'delivery_periods': [report_period] if artifacts else [], 'message_type': 'post',
        'message_title': f'🔥【{report_period}】初三主管{label}数据播报',
        'outcomes': outcomes, 'results': results, 'component_ids': [result['component']['id'] for result in results],
        'artifacts': artifacts, 'skip_delivery': not artifacts, 'prepared_at': at.isoformat()}
    source.save(Path(directory) / 'context.json', context)
    return context


def prepare(definition, target, directory, slot=None, component_ids=None, specification=None, loader=None):
    at = datetime.now(TZ)
    rows, proof = loader() if loader else source.read(definition, target, directory, slot)
    if business_period(at) != proof['period']:
        raise ValueError('Source period differs from the current business calendar')
    expected = policy.specifications(at.weekday(), proof['period'], next_business_period(proof['period']))
    if specification is not None and specification not in expected:
        raise ValueError('Unregistered grade-nine report period or section')
    components = [item for item in definition['components'] if component_ids is None or item['id'] in component_ids]
    if component_ids is not None and {item['id'] for item in components} != set(component_ids):
        raise ValueError('Unregistered grade-nine component selection')
    parts = [build_period(definition, target, rows, proof,
        Path(directory) if specification is not None else Path(directory) / item['role'], at, item, components)
        for item in ([specification] if specification is not None else expected)]
    if len(parts) == 1:
        return parts[0]
    wrapper = {'definition': definition, 'definition_sha256': source.fingerprint(definition), 'target': target,
        'source': proof, 'snapshot': proof['snapshot'], 'period': proof['period'],
        'section': scheduled_report_type(at), 'directory': str(directory), 'grade9_preview_only': True,
        'grade9_preview_parts': parts, 'artifacts': [item for part in parts for item in part['artifacts']],
        'component_ids': sorted({name for part in parts for name in part['component_ids']}),
        'outcomes': {part['grade9_role'] + '/' + name: value for part in parts for name, value in part['outcomes'].items()},
        'skip_delivery': not any(part['artifacts'] for part in parts),
        'artifact_protocol': definition['report']['artifact_protocol']}
    source.save(Path(directory) / 'context.json', wrapper)
    return wrapper


def validate_context(context, definition, at):
    if context.get('grade9_preview_only'):
        raise ValueError('Combined grade-nine preview is not an executable message')
    if context.get('grade9_role') is None:
        return
    policy.validate(definition)
    expected = policy.specifications(at.weekday(), business_period(at), next_business_period(business_period(at)))
    match = [item for item in expected if item['role'] == context['grade9_role']]
    if (not policy.enabled(definition) or len(match) != 1 or context['grade9_policy_date'] != at.date().isoformat()
            or context['grade9_weekday'] != at.weekday() or context['report_period'] != match[0]['period']
            or context['section'] != match[0]['section'] or context['delivery_periods'] != [match[0]['period']]):
        raise ValueError('Grade-nine date, period or standards changed; prepare again')
