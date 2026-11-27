"""Grade-nine channel standards; independent of the high-school KOC calendar."""
from copy import deepcopy
from fractions import Fraction

PROFILE_BY_ID = {'draft_13_1': 'jiangsu', 'draft_14_1': 'anhui', 'draft_15_1': 'none',
                 'shandong_supervisor': 'none', 'draft_16_1': 'koc', 'draft_16_2': 'koc'}
RATES = {'jiangsu': {'2': '0.30', '3': '0.10', '5': '0.30', '6': '0.40'},
         'anhui': {'2': '0.35', '3': '0.12', '5': '0.30', '6': '0.40'},
         'koc': {'2': '0.35', '3': '0.12', '5': '0.40', '6': '0.50'}, 'none': {}}
NUMERATORS = {'5min': '5min标记', '双沟率': '双沟标记', '好友率': '好友标记', '截面单效': '净收款'}


def group_settings():
    return {'version': 1, 'next_process_weekdays': [4, 5, 6], 'images_only_weekdays': [0, 1],
            'conversion_reminders': 'retain_existing_minimum', 'person_values': False,
            'explain_missing_standard': False}


def channel_settings(profile):
    return {'version': 1, 'benchmark_group': profile, 'targets': deepcopy(RATES[profile])}


def enabled(definition):
    return (definition.get('channel_id') == 'grade9_supervisor_bundle'
            and definition.get('report', {}).get('grade9_daily_policy') is not None)


def validate(definition):
    settings = definition.get('report', {}).get('grade9_daily_policy')
    if settings is None:
        return
    if not enabled(definition) or settings != group_settings():
        raise ValueError('Unreviewed grade-nine daily calendar')
    if {item['id'] for item in definition['components']} != set(PROFILE_BY_ID):
        raise ValueError('Grade-nine benchmark components changed')
    for item in definition['components']:
        if (item['grain'] != '主管' or item['grades'] != ['初三']
                or item.get('grade9_benchmarks') != channel_settings(PROFILE_BY_ID[item['id']])):
            raise ValueError('Grade-nine channel standard or grade changed')


def specifications(weekday, current, following):
    if weekday < 4:
        return [{'role': 'current_process', 'period': current, 'section': 'process',
                 'metric': '双沟率' if weekday == 3 else '5min'}]
    return [{'role': 'current_conversion', 'period': current, 'section': 'result', 'metric': '截面单效'},
            {'role': 'next_process', 'period': following, 'section': 'process', 'metric': '好友率'}]


def ratio(row, metric):
    denominator = Fraction(row['sums']['退后线索'])
    return Fraction(row['sums'][NUMERATORS[metric]]) / denominator if denominator else None


def apply(result, specification, weekday):
    result = deepcopy(result)
    metric, section = specification['metric'], specification['section']
    target = result['component']['grade9_benchmarks']['targets'].get(str(weekday)) if section == 'process' else None
    audits = []
    for block in result['report']['blocks']:
        def key(row):
            value = ratio(row, metric)
            return (value is None, -value if value is not None else Fraction(0),
                    row['fields']['负责人'], row['fields']['主管'])
        block['ordered_rows'] = sorted(block['rows'], key=key)
        block['sort_metric'] = metric
        totals = {}
        for row in block['rows']:
            value = ratio(row, metric)
            below = target is not None and value is not None and value < Fraction(target)
            row['below_standard_fields'] = [metric] if below else []
            sums = totals.setdefault(row['fields']['主管'], [Fraction(0), Fraction(0)])
            sums[0] += Fraction(row['sums'][NUMERATORS[metric]])
            sums[1] += Fraction(row['sums']['退后线索'])
        values = {name: numerator / denominator for name, (numerator, denominator) in totals.items() if denominator}
        if section == 'process':
            block['reminders'][section] = sorted(name for name, value in values.items()
                if target is not None and value < Fraction(target))
        audits.append({'grade': block['grade'], 'channel': result['component']['label'], 'metric': metric,
            'target': target, 'names': block['reminders'][section],
            'values': {name: {'numerator': str(value.numerator), 'denominator': str(value.denominator)}
                       for name, value in values.items()}})
    result['grade9_audits'] = audits
    return result
