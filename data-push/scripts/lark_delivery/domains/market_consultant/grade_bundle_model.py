"""Approved per-channel calculations for grade-first, multi-channel messages."""
from fractions import Fraction
from math import ceil

from . import supervisor_report as supervisor
from . import supervisor_video49_report as advisor_base
from . import supervisor_yafei_advisor_report as advisor
from .workflow import merge_duplicate_lead_ids


def matches(row, component):
    actual = str(row['渠道'])
    if component['match'] == 'casefold_exact':
        return actual.casefold() == component['source_values'][0].casefold()
    return actual in component['source_values']


def calculate(rows, evidence, period, section, components):
    """One bad channel produces its own outcome; other channels remain usable."""
    results, outcomes = [], {}
    counts = evidence['periods'][period]['channel_counts']
    for component in components:
        key = component['id']
        try:
            selected = [row for row in rows if row['期次'] == period and matches(row, component)]
            expected = sum(n for channel, n in counts.items() if matches({'渠道': channel}, component))
            if len(selected) != expected:
                raise ValueError('Channel count differs from the complete upstream audit')
            if not selected:
                outcomes[key] = {'status': 'skipped_no_source_rows', 'channel': component['label']}
                continue
            audit = {}
            selected = merge_duplicate_lead_ids(selected, audit)
            module = supervisor if component['grain'] == '主管' else advisor
            _, counters = module.projection(list(selected[0]), section)
            scope = ({'match_mode': 'casefold_exact', 'value': component['source_values'][0]}
                     if component['match'] == 'casefold_exact' else
                     {'match_mode': 'any_exact', 'values': component['source_values']})
            if component['grain'] == '主管':
                supervisor.validate_scope(selected, component['label'], period, source_channel=scope)
            else:
                if len(component['source_values']) != 1:
                    raise ValueError('Advisor union has not been reviewed')
                advisor.validate_scope(selected, component['label'], period, source_channel=component['source_values'][0])
            report = module.build_report(selected, counters, period, section,
                min_post_leads=component['minimum_post_leads'], included_grades=component['grades'])
            report['show_totals'] = component.get('show_totals', False)
            if not report['blocks']:
                outcomes[key] = {'status': 'skipped_no_eligible_rows', 'channel': component['label']}
                continue
            if component['reminders']['target'] == '不提醒':
                for block in report['blocks']:
                    block['reminders'][section] = []
            elif component['grain'] == '顾问' and component['reminders']['ties'] == '全部提醒':
                for block in report['blocks']:
                    metrics = list(block['advisor_metrics'][section].values())
                    metric = lambda item: Fraction(item['numerator']) / Fraction(item['denominator'])
                    ordered = sorted(metrics, key=metric)
                    quota = max(1, ceil(len(ordered) / 10)) if ordered else 0
                    cutoff = metric(ordered[quota-1]) if quota else None
                    block['reminders'][section] = sorted({item['顾问'] for item in ordered
                        if cutoff is not None and metric(item) <= cutoff})
            results.append({'component': component, 'report': report, 'dedup_audit': audit,
                            'raw_count': expected, 'post_dedup_count': len(selected)})
            outcomes[key] = {'status': 'prepared', 'channel': component['label'], 'raw_count': expected,
                             'visible_rows': sum(len(block['rows']) for block in report['blocks'])}
        except Exception as exc:
            outcomes[key] = {'status': 'blocked_prepare', 'channel': component['label'],
                             'reason': type(exc).__name__ + ': ' + str(exc)[:300]}
    return results, outcomes


def columns(component, section):
    module = supervisor if component['grain'] == '主管' else advisor
    lookup = {item[0]: item for item in module.COLUMNS[section]}
    result = [lookup[name] for name in component['column_order'][section]]
    weights = [155 if name in {'负责人', '主管', '顾问'} else 143 if name == '期次' else 125
               for name, _, _ in result]
    widths = [round(weight * 2380 / sum(weights)) for weight in weights]
    widths[-1] += 2380 - sum(widths)
    return result, widths


def renderer(component):
    return supervisor if component['grain'] == '主管' else advisor_base
