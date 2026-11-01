"""Pure full-field market raw-source fingerprinting; no warning delivery."""
from collections import Counter
import hashlib
import json


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
