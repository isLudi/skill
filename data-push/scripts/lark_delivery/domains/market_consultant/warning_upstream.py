"""Read the owned daily warning producer through the governed Tiangong2 adapter."""
from __future__ import annotations

from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import re
import subprocess
import uuid
from zoneinfo import ZoneInfo

from ...paths import WORKSPACE_ROOT

TZ = ZoneInfo('Asia/Shanghai')
OPERATOR = WORKSPACE_ROOT / 'skills/usql-web-query-operator/scripts/tiangong2_task.py'
ARTIFACTS = WORKSPACE_ROOT / 'runtime/usql-web-query-operator/tiangong2-task/local-koc-zhoushuai-warning'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def operator(command, definition, *extra):
    u = definition['upstream']
    python = read(WORKSPACE_ROOT / 'machine.local.json')['executables']['python']
    args = [python, str(OPERATOR), command, '--project-id', str(u['project_id']),
            '--folder', u['folder'], '--menu-id', str(u['menu_id']), '--task-name', u['task_name'],
            '--artifacts-dir', str(ARTIFACTS), *extra]
    result = subprocess.run(args, cwd=str(WORKSPACE_ROOT), capture_output=True, text=True,
                            encoding='utf-8', timeout=100,
                            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    if result.returncode:
        raise RuntimeError(f'Governed upstream read failed: {command} exit={result.returncode}')
    reply = json.loads(result.stdout)
    if reply.get('read_only') is not True or reply.get('remote_mutations') != 0:
        raise ValueError('Missing read-only upstream receipt')
    return reply


def verify_scope(doc, definition):
    u = definition['upstream']
    for key in ('project_id', 'folder', 'menu_id', 'task_name', 'task_id', 'nezha_task_id'):
        if doc['scope'].get(key) != u[key]:
            raise ValueError('Warning upstream scope drift: ' + key)
    if doc['identity'].get('name') != u['owner']:
        raise ValueError('Warning upstream owner drift')


def publication(definition):
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    reply = operator('plan-task-publish', definition, '--output-file',
                     str(ARTIFACTS / ('publication-' + uuid.uuid4().hex + '.json')))
    doc = read(reply['plan_file'])
    verify_scope(doc, definition)
    u, baseline = definition['upstream'], doc['baseline']
    age = datetime.now(TZ) - datetime.fromisoformat(doc['created_at'])
    if (not timedelta(0) <= age <= timedelta(minutes=5)
            or baseline['current_source_sha256'] != u['verified_source_sha256']
            or baseline['latest_published_version_id'] != u['verified_version_id']
            or baseline['source_matches_latest_published'] is not True):
        raise ValueError('Published warning source/version no longer matches local binding')
    return {'plan_file': reply['plan_file'], 'plan_sha256': doc['plan_sha256'],
            'verified_at': datetime.now(TZ).isoformat(), 'version_id': u['verified_version_id']}


def select_execution(doc, definition, day, scheduled):
    verify_scope(doc, definition)
    u, schedule = definition['upstream'], doc['task_schedule']
    if (schedule.get('supervisor') != u['owner'] or schedule.get('scheduleId') != u['schedule_id']
            or schedule.get('scheduleFrequency') != '1d' or schedule.get('scheduleStatus') != 0):
        raise ValueError('Warning daily schedule changed or disabled')
    rows = doc['executions']
    if not rows or len({r['id'] for r in rows}) != len(rows):
        raise ValueError('Missing or duplicate upstream execution history')
    if scheduled:
        stamp = day.strftime('%Y-%m-%d') + ' ' + u['scheduled_time']
        matches = [r for r in rows if r.get('planRunTime') == stamp
                   and json.loads(r['runConfig']).get('triggerSourceEnum') == 'SCHEDULE']
        if len(matches) != 1:
            raise ValueError('Today 17:10 scheduled execution missing or ambiguous')
        row = matches[0]
    else:
        row = max(rows, key=lambda r: int(r['id']))
    if (row.get('status') != 6 or row.get('taskId') != u['nezha_task_id']
            or row.get('taskName') != u['task_name']
            or json.loads(row['runConfig']).get('execFileId') != u['exec_file_id']
            or not str(row.get('endTime', '')).startswith(day.strftime('%Y-%m-%d'))
            or any(int(r['id']) > int(row['id']) for r in rows)):
        raise ValueError('Latest warning producer is incomplete, stale or bound to another file')
    return row


def history(definition, day, scheduled=True):
    reply = operator('list-execution-history', definition, '--limit', '12')
    if not reply.get('ok'):
        raise ValueError('Upstream execution history unavailable')
    doc = read(Path(reply['artifact_dir']) / 'history.json')
    return select_execution(doc, definition, day, scheduled)


def parse_log(doc, directory, definition, execution, day):
    verify_scope(doc, definition)
    u = definition['upstream']
    if (doc['execution']['id'] != execution['id'] or doc['execution'].get('status') != 6
            or doc['execution_detail'].get('status') != 6 or not doc.get('stages')):
        raise ValueError('Warning execution detail incomplete')
    for stage in doc['stages']:
        if (stage['metadata'].get('taskId') != u['nezha_task_id']
                or stage['metadata'].get('statusDesc') not in {'success','failed'}):
            raise ValueError('Warning stage not completely finished')
    stage = doc['stages'][-1]
    if stage['metadata'].get('statusDesc') != 'success':
        raise ValueError('Final warning stage did not succeed')
    path = (directory / stage['log_file']).resolve()
    if not path.is_relative_to(directory.resolve()):
        raise ValueError('Stage path escaped execution artifacts')
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != stage['log_sha256']:
        raise ValueError('Warning stage log fingerprint changed')
    log = raw.decode('utf-8')
    required = ['目标多维表格校验通过：table_id=' + definition['source']['raw_table_id'],
                '目标字段校验通过：26个字段', '新记录创建完成：', '新记录回读校验通过',
                '旧记录删除完成：', '最终回读校验通过：', 'SUCCESS:']
    if any(item not in log for item in required) or not re.search(r'exit_code:\s+0\s*$', log):
        raise ValueError('Warning Base replacement did not finish all safety stages')
    positions = [log.index(item) for item in required[2:]]
    if positions != sorted(positions) or '渠道映射版本：' + u['channel_mapping_version'] not in log:
        raise ValueError('Warning replacement sequence or channel mapping changed')
    lines = re.findall(r'^双期快照清单：(\{[^\r\n]+\})\s*$', log, re.M)
    if len(lines) != 1:
        raise ValueError('Warning audit missing or ambiguous')
    audit = json.loads(lines[0])
    friday = day - timedelta(days=day.weekday()) + timedelta(days=4)
    periods = [(friday - timedelta(days=7)).strftime('%Y%m%d') + '期', friday.strftime('%Y%m%d') + '期']
    if (audit.get('schema_version') != 'market2lark-two-period-audit-v1'
            or audit.get('field_count') != 26 or sorted(audit['periods']) != periods
            or audit.get('numeric_hash_decimal_places') != 6):
        raise ValueError('Warning audit schema or conversion-calendar periods mismatch')
    final = re.findall(r'最终回读校验通过：(\d+)条', log)
    created = re.findall(r'新记录创建完成：(\d+)条', log)
    if final != [str(audit['row_count'])] or created != final:
        raise ValueError('Created/final warning row counts disagree')
    snapshots = [audit['periods'][p]['snapshots'] for p in periods]
    if any(len(s) != 1 for s in snapshots):
        raise ValueError('Mixed warning snapshots')
    prior, current = [s[0] for s in snapshots]
    if (current[0] != day.strftime('%Y%m%d')
            or prior[0] != (day - timedelta(days=7)).strftime('%Y%m%d')
            or current[1] != prior[1] or not 0 <= int(current[1]) <= 23):
        raise ValueError('Warning dates or same-hour comparison mismatch')
    snapshot_at = datetime.strptime(current[0] + f'{int(current[1]):02d}', '%Y%m%d%H').replace(tzinfo=TZ)
    if not timedelta(0) <= datetime.now(TZ) - snapshot_at <= timedelta(hours=7):
        raise ValueError('Warning data snapshot outside approved freshness window')
    if sum(info['row_count'] for info in audit['periods'].values()) != audit['row_count']:
        raise ValueError('Warning period totals disagree')
    return {'execution_id': execution['id'], 'audit': audit, 'current_snapshot': {'dt': current[0], 'hour': current[1]},
            'prior_snapshot': {'dt': prior[0], 'hour': prior[1]}, 'artifact_dir': str(directory),
            'log_sha256': stage['log_sha256'], 'end_time': execution['endTime']}


def ready(definition, day, scheduled=True):
    published = publication(definition)
    execution = history(definition, day, scheduled)
    reply = operator('fetch-execution-log', definition, '--exec-id', str(execution['id']))
    if not reply.get('ok'):
        raise ValueError('Warning stage logs unavailable')
    directory = Path(reply['artifact_dir'])
    result = parse_log(read(directory / 'execution.json'), directory, definition, execution, day)
    return {**result, 'publication': published, 'scheduled_execution_required': scheduled}
