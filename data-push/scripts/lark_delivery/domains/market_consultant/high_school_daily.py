"""Prepare one KOC card with independently audited current and following periods."""
from pathlib import Path

from . import grade_bundle_model as model
from . import grade_bundle_source as source
from . import high_school_daily_policy as policy
from .high_school_channel_render import render_channel
from .channels.grade_compact import next_business_period, scheduled_report_type


def prepare(definition, target, rows, proof, directory, at, component):
    policy.validate(component)
    results, artifacts, parts = [], [], []
    for specification in policy.specifications(at.weekday(), proof['period'], next_business_period(proof['period'])):
        period, section = specification['period'], specification['section']
        if period not in proof['evidence']['periods']:
            raise ValueError('Daily KOC period is absent from the complete source audit: ' + period)
        calculated, outcomes = model.calculate(rows, proof['evidence'], period, section, [component])
        outcome = outcomes[component['id']]
        if outcome['status'] == 'blocked_prepare':
            raise ValueError(outcome['reason'])
        if not calculated:
            parts.append({'specification': specification, 'status': outcome['status'], 'audits': []})
            continue
        result = policy.apply(calculated[0], specification)
        artifact, checks = render_channel(result, section, period, Path(directory) / specification['role'] / 'images')
        artifact['period'] = period
        parts.append({'specification': specification, 'status': 'prepared', 'artifact_index': len(artifacts),
                      'audits': result['daily_audits'], 'checks': checks})
        results.append(result)
        artifacts.append(artifact)
    context = {'definition': definition, 'definition_sha256': source.fingerprint(definition), 'target': target,
        'source': proof, 'snapshot': proof['snapshot'], 'period': proof['period'], 'section': scheduled_report_type(at),
        'directory': str(directory), 'artifact_protocol': definition['report']['artifact_protocol'],
        'message_type': 'interactive', 'component_ids': [component['id']] if artifacts else [],
        'artifacts': artifacts, 'results': results, 'skip_delivery': not artifacts, 'prepared_at': at.isoformat(),
        'daily_policy_date': at.date().isoformat(), 'daily_weekday': at.weekday(), 'daily_sections': parts,
        'delivery_periods': list(dict.fromkeys(artifact['period'] for artifact in artifacts)),
        'outcomes': {component['id']: {'status': 'prepared' if artifacts else 'skipped_no_eligible_rows',
            'channel': component['label'], 'sections': [{key: item[key] for key in ['specification', 'status']} for item in parts]}}}
    source.save(Path(directory) / 'context.json', context)
    return context
