"""Reviewed high-school KOC weekday standards, exact ratios and visible-supervisor reminders."""
from copy import deepcopy
from fractions import Fraction

GRADES = ('高一', '高二', '高三')
WEEKDAYS = ('周一', '周二', '周三', '周四', '周五', '周六', '周日')
NUMERATORS = {'5min': '5min标记', '双沟率': '双沟标记', '好友率': '好友标记', '截面单效': '净收款'}
TARGETS = {
    0: None, 1: None,
    2: {'高一': '0.30', '高二': '0.30', '高三': '0.30'},
    3: {'高一': '0.10', '高二': '0.09', '高三': '0.10'},
    4: None,
    5: {'高一': '0.50', '高二': '0.50', '高三': '0.50'},
    6: {'高一': '0.60', '高二': '0.60', '高三': '0.60'},
}


def ratio(row, metric):
    denominator = Fraction(row['sums']['退后线索'])
    return Fraction(row['sums'][NUMERATORS[metric]]) / denominator if denominator else None


def below(value, target):
    return value is not None and target is not None and value < Fraction(target)


def specifications(weekday, current, following):
    if weekday < 4:
        return [{'role': 'current_process', 'period': current, 'section': 'process',
                 'metric': '双沟率' if weekday == 3 else '5min', 'targets': TARGETS[weekday]}]
    current_result = [
        {'role': 'current_conversion', 'period': current, 'section': 'result',
         'metric': '截面单效', 'targets': None, 'reminder_mode': 'retain_existing_minimum'},
    ]
    if weekday == 4:
        return current_result
    return current_result + [
        {'role': 'next_process', 'period': following, 'section': 'process',
         'metric': '好友率', 'targets': TARGETS[weekday]},
    ]


def apply(result, specification):
    result = deepcopy(result)
    component = result['component']
    metric, targets = specification['metric'], specification['targets']
    section = specification['section']
    component['daily_sort_metric'] = metric
    audits = []
    for block in result['report']['blocks']:
        def key(row):
            value = ratio(row, metric)
            return (value is None, -value if value is not None else Fraction(0),
                    row['fields']['负责人'], row['fields']['主管'])
        ordered = sorted(block['rows'], key=key)
        block['ordered_rows'] = ordered
        block['sort_metric'] = metric
        target = targets.get(block['grade']) if targets else None
        for row in block['rows']:
            row['below_standard_fields'] = [metric] if below(ratio(row, metric), target) else []
        supervisor_sums = {}
        for row in block['rows']:
            name = row['fields']['主管']
            sums = supervisor_sums.setdefault(name, {'numerator': Fraction(0), 'denominator': Fraction(0)})
            sums['numerator'] += Fraction(row['sums'][NUMERATORS[metric]])
            sums['denominator'] += Fraction(row['sums']['退后线索'])
        values = {name: sums['numerator'] / sums['denominator'] for name, sums in supervisor_sums.items()
                  if sums['denominator']}
        if specification.get('reminder_mode') == 'retain_existing_minimum':
            names = block['reminders'][section]
        else:
            names = sorted(name for name, value in values.items() if below(value, target))
            block['reminders'][section] = names
        audits.append({'grade': block['grade'], 'metric': metric, 'target': target,
            'names': names, 'values': {name: {'numerator': str(value.numerator),
                'denominator': str(value.denominator), 'display': f'{float(value) * (1 if metric == "截面单效" else 100):.2f}'}
                for name, value in values.items()},
            'row_order': [row['fields']['主管'] for row in ordered],
            'unconfigured': target is None and section == 'process'})
    result['daily_audits'] = audits
    return result


def settings():
    return {'version': 2, 'targets': {str(key): deepcopy(value) for key, value in TARGETS.items()},
            'weekend_next_process': True, 'next_process_weekdays': [5, 6],
            'conversion_reminders': 'retain_existing_minimum',
            'reminder_person_values': False, 'explain_no_standard': False, 'ab_intent_in_scope': False}


def validate(component):
    if component.get('daily_standards') is None:
        return
    if (component.get('id') not in {'external_koc', 'draft_21_1', 'koc_channel'} or component.get('grain') != '主管'
            or tuple(component.get('grades', [])) != GRADES or component['daily_standards'] != settings()):
        raise ValueError('Unreviewed daily KOC standards or scope')
