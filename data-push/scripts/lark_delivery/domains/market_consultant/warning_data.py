"""Complete, revision-consistent warning data read and weighted aggregation."""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
import hashlib
import json
from pathlib import Path

from ...common.runtime import run_lark
from ...paths import CONFIG_ROOT, WORKSPACE_ROOT

FIELDS = ('退后线索', '5min标记', '首call完成标记', '外呼次数', '收款', '退费', '净收款')


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str) + '\n', encoding='utf-8')
    temp.replace(path)


def api(args):
    reply = json.loads(run_lark(args, timeout=60))
    if reply.get('ok') is False or reply.get('code', 0) != 0:
        raise RuntimeError('Feishu read did not succeed')
    return reply


def contract(definition):
    path = (CONFIG_ROOT / definition['source']['field_contract']).resolve()
    if not path.is_relative_to(CONFIG_ROOT.resolve()):
        raise ValueError('Warning field contract escaped config root')
    return json.loads(path.read_text(encoding='utf-8'))


def read_page(definition, directory, offset, page, fields):
    path = Path(directory).resolve() / f'page-{page:03d}.ndjson'
    if not path.is_relative_to((WORKSPACE_ROOT / 'runtime').resolve()):
        raise ValueError('Warning Base read artifacts must stay in workspace runtime')
    path.parent.mkdir(parents=True, exist_ok=True)
    s = definition['source']
    args = ['base', '+record-list', '--base-token', s['base_token'], '--table-id', s['raw_table_id'],
            '--limit', '2000', '--offset', str(offset), '--format', 'ndjson',
            '--output', path.relative_to(WORKSPACE_ROOT).as_posix(), '--as', definition['base_identity']]
    for field in fields:
        args += ['--field-id', field]
    manifest = api(args)
    rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
    if len(rows) != manifest['records_count']:
        raise ValueError('Warning Base page count mismatch')
    return rows, manifest


def audit(rows, field_contract):
    mapping, numeric = field_contract['field_mapping'], set(field_contract['numeric_fields'])
    names = sorted(mapping)
    result = {'schema_version': 'market2lark-two-period-audit-v1', 'field_count': len(names),
              'row_count': len(rows), 'numeric_hash_decimal_places': 6, 'periods': {}}
    for period in sorted({r['期次'] for r in rows}):
        subset = sorted((r for r in rows if r['期次'] == period), key=lambda r: r['记录键'])
        digest, keys = hashlib.sha256(), []
        totals = {name: 0.0 for name in names if name in numeric}
        for row in subset:
            keys.append(row['记录键'])
            values = []
            for name in names:
                value = row.get(mapping[name])
                if value is not None:
                    if name in numeric:
                        totals[name] += float(value)
                        value = f'{float(value):.6f}'
                    else:
                        value = str(value).strip()
                values.append(value)
            digest.update((json.dumps(values, ensure_ascii=True, separators=(',', ':')) + '\n').encode('utf-8'))
        result['periods'][period] = {
            'row_count': len(subset), 'key_sha256': hashlib.sha256('\n'.join(keys).encode('utf-8')).hexdigest(),
            'records_sha256': digest.hexdigest(), 'channel_counts': dict(Counter(r['渠道'] for r in subset)),
            'snapshots': [list(x) for x in sorted({(r['分区日期'], r['分区小时']) for r in subset})],
            'numeric_totals': {key: f'{value:.6f}' for key, value in sorted(totals.items())}}
    return result


def validate_rows(rows, field_contract):
    mapping = field_contract['field_mapping']
    ids, keys = set(), set()
    for row in rows:
        if set(row) - {'record_id'} != set(mapping.values()) or row['record_id'] in ids:
            raise ValueError('Incomplete projection or repeated record id')
        ids.add(row['record_id'])
        key = '|'.join(str(row[mapping[k]]) for k in field_contract['business_grain'])
        if key != row['记录键'] or key in keys:
            raise ValueError('Warning allocation key mismatch or duplicate')
        keys.add(key)
        for name in field_contract['numeric_fields']:
            value = Decimal(str(row[mapping[name]]))
            if not value.is_finite():
                raise ValueError('Non-finite warning number')
        for field in ('退前线索', '退后线索', '外呼次数'):
            value = Decimal(str(row[field]))
            if value < 0 or value != value.to_integral_value():
                raise ValueError('Invalid lead/call count')
        for field in ('退前线索', '退后线索', '5min标记', '首call完成标记'):
            if Decimal(str(row[field])) not in {Decimal(0), Decimal(1)}:
                raise ValueError('Invalid binary lead/process flag')
        if any(Decimal(str(row[f])) > Decimal(str(row['退后线索'])) for f in ('5min标记', '首call完成标记')):
            raise ValueError('Process flag on a non-post lead')
        if abs(Decimal(str(row['收款'])) - Decimal(str(row['退费'])) - Decimal(str(row['净收款']))) > Decimal('0.000001'):
            raise ValueError('Net revenue conservation failed')


def read_all(definition, directory, expected):
    field_contract = contract(definition)
    rows, manifests, offset, rev = [], [], 0, None
    for page in range(100):
        chunk, manifest = read_page(definition, directory, offset, page, field_contract['field_mapping'].values())
        if rev is None:
            rev = manifest['rev']
        if manifest['rev'] != rev:
            raise ValueError('Base revision changed during warning pagination')
        rows.extend(chunk)
        manifests.append(manifest)
        if manifest['has_more'] is False:
            break
        next_offset = manifest['next_offset']
        if next_offset <= offset:
            raise ValueError('Warning pagination failed to advance')
        offset = next_offset
    else:
        raise ValueError('Warning pagination safety limit exceeded')
    if not rows or manifests[-1]['has_more'] is not False:
        raise ValueError('No complete warning source data')
    validate_rows(rows, field_contract)
    actual = audit(rows, field_contract)
    save(Path(directory) / 'actual_audit.json', actual)
    if actual != expected:
        raise ValueError('Full warning Base contents disagree with the latest successful task audit')
    save(Path(directory) / 'source_receipt.json', {'row_count': len(rows), 'page_count': len(manifests),
         'rev': rev, 'complete': True, 'all_field_hashes_match': True, 'manifests': manifests})
    return rows, rev


def unchanged(definition, directory, rev):
    _, manifest = read_page(definition, directory, 0, 0, ['记录键'])
    if manifest['rev'] != rev:
        raise ValueError('Source revision changed after preparing the warning message')


def ratio(a, b):
    return a / b if b > 0 else None


def relative(a, b):
    return (a - b) / b if a is not None and b is not None and b > 0 else None


def metrics(values):
    return {'first_call': ratio(values['首call完成标记'], values['退后线索']),
            'five_min': ratio(values['5min标记'], values['退后线索']),
            'frequency': ratio(values['外呼次数'], values['退后线索']),
            'unit': ratio(values['净收款'], values['退后线索']), 'refund': ratio(values['退费'], values['收款'])}


def aggregate(definition, target, rows, rev, evidence, kind):
    periods = sorted(evidence['audit']['periods'])
    prior, period = periods
    selected = [r for r in rows if r['渠道'] == definition['channel'] and r['年级'] in definition['report']['included_grades']]
    current = [r for r in selected if r['期次'] == period]
    if not current or sum(Decimal(str(r['退后线索'])) for r in current) <= 0:
        return None
    totals = {p: {f: Decimal(0) for f in FIELDS} for p in periods}
    groups = defaultdict(lambda: {f: Decimal(0) for f in FIELDS})
    counts = Counter()
    for row in selected:
        p, supervisor = row['期次'], row['主管']
        if not supervisor or row['主管匹配来源'] == '未匹配':
            raise ValueError('Channel historical supervisor unresolved')
        expected_finance = (datetime.strptime(row['分区日期'], '%Y%m%d') - timedelta(days=1)).strftime('%Y%m%d')
        if row['主管匹配来源'] not in {'期次架构', '财务历史快照:' + expected_finance}:
            raise ValueError('Channel historical supervisor source invalid')
        counts[p, supervisor] += 1
        for field in FIELDS:
            value = Decimal(str(row[field]))
            totals[p][field] += value
            groups[p, supervisor][field] += value
    team = {'supervisor': '团队整体', 'now_sums': totals[period], 'prior_sums': totals[prior],
            'now': metrics(totals[period]), 'prior': metrics(totals[prior])}
    keys = ('first_call', 'five_min', 'frequency') if kind == 'process' else ('unit', 'refund')
    if any(team['prior'][k] is None or team['now'][k] is None for k in keys):
        raise ValueError('Channel team comparison denominator unavailable')
    result_rows = []
    for supervisor in sorted({s for p, s in groups if p == period}):
        before = groups.get((prior, supervisor), {f: Decimal(0) for f in FIELDS})
        row = {'supervisor': supervisor, 'now_sums': groups[period, supervisor], 'prior_sums': before,
               'now_rows': counts[period, supervisor], 'prior_rows': counts[prior, supervisor],
               'now': metrics(groups[period, supervisor]), 'prior': metrics(before)}
        for key in keys:
            row[key + '_mom'] = relative(row['now'][key], row['prior'][key])
            row[key + '_team'] = relative(row['now'][key], team['now'][key])
        result_rows.append(row)
    for key in keys:
        team[key + '_mom'] = relative(team['now'][key], team['prior'][key])
        team[key + '_team'] = None
    sort_key = 'five_min' if kind == 'process' else 'unit'
    result_rows.sort(key=lambda r: (r['now'][sort_key] is None,
                     -r['now'][sort_key] if r['now'][sort_key] is not None else Decimal(0), r['supervisor']))
    return {'source_table_id': definition['source']['raw_table_id'], 'source_rev': rev,
            'channel': definition['channel'], 'target_chat_id': target['chat_id'],
            'grades': definition['report']['included_grades'], 'period': period, 'previous_period': prior,
            'current_snapshot': evidence['current_snapshot'], 'prior_snapshot': evidence['prior_snapshot'],
            'team': team, 'rows': result_rows, 'selected_rows': len(selected), 'all_source_rows': len(rows),
            'report_kind': kind, 'local_only': True, 'message_sent': False}
