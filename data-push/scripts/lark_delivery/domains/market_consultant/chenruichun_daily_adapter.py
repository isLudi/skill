"""Restored Chen Ruichun advisor report on isolated 14:00/19:00 slots."""
from datetime import datetime
import hashlib
from pathlib import Path

from ...common.images import _find_font, _center_text
from ...common.values import _format_value, _rate
from . import grade_bundle_source as source
from . import grade_bundle_render as rendering
from . import supervisor_video49_report as report
from .channels.grade_compact import TZ, scheduled_report_type
from .workflow import merge_duplicate_lead_ids

KEY='market_consultant/supervisor_chenruichun'
TARGET='oc_510ee233f666207fbda3a4ec473bf388'


def image_columns(definition,section):
    """Resolve this channel's configured order without mutating shared templates."""
    default=report.COLUMNS[section]
    lookup={item[0]:item for item in default}
    widths={item[0]:width for item,width in zip(default,report.WIDTHS[section])}
    if section=='result':
        lookup.update({'当期单效':('当期单效','当期单效','amount'),
                       '截面单效':('截面单效','截面单效','amount')})
        widths.update({'当期单效':widths['单效（当期）'],'截面单效':widths['单效']})
    order=definition['report'].get('column_order',{}).get(section,[item[0] for item in default])
    if (not isinstance(order,list) or len(order)!=len(set(order))
            or any(name not in lookup for name in order)
            or order[:4]!=['期次','负责人','主管','顾问']):
        raise ValueError('Unreviewed Chen Ruichun image columns')
    return [lookup[name] for name in order],[widths[name] for name in order]


def validate_definition(definition):
    if (definition.get('domain')!='market_consultant' or definition.get('channel_id')!='supervisor_chenruichun'
            or definition.get('adapter')!='market-chenruichun-daily-v1' or definition['channels']!=['陈瑞春']
            or len(definition['targets'])!=1 or definition['targets'][0]['chat_id']!=TARGET):
        raise ValueError('Unreviewed Chen Ruichun route')
    if definition['source']['channel_match']!={'field':'渠道','match_mode':'contains','keyword':'陈瑞春','case_sensitive':True}:
        raise ValueError('Chen Ruichun must retain the full contains-keyword scope')
    rules=definition['report']
    if (rules['minimum_post_leads']!=6 or rules['included_grades']!=['高一','高二','高三']
            or rules['show_totals'] is not True or rules['process_weekdays']!=[0,1,2,3] or rules['result_weekdays']!=[4,5,6]):
        raise ValueError('Chen Ruichun grade/threshold/calendar changed')
    if definition['sender']!={'identity':'bot','name':'管家','open_id':'ou_f3907e865135732c15a1dfce27828411'}:
        raise ValueError('Chen Ruichun sender changed')
    schedule=definition['schedule']
    if (schedule['kind']!='chenruichun_twice_daily' or schedule['hours']!=[14,19]
            or schedule['upstream_hours']!={'14':13,'19':17} or schedule['prepare_minute']!=0
            or schedule['send_minute']!=0 or schedule['deadline_minute']!=50 or schedule['retry_minutes']!=2
            or schedule['windows_task_name']!='Codex-Lark-Supervisor-Chen-Ruichun-Push'):
        raise ValueError('Chen Ruichun daily slot drift')
    if (definition['source']['raw_table_id']!='tbljWRvaqKTdrCx4'
            or definition['source']['field_contract']!='release/market2lark_raw_fields.json'
            or definition['components']!=[{'id':'chenruichun_all','label':'陈瑞春','grain':'顾问'}]):
        raise ValueError('Chen Ruichun source/component changed')
    for section in ['process','result']:
        image_columns(definition,section)
    return definition


schedule_config=source.schedule_config


def channels_for_target(definition,target):
    return ['陈瑞春']


def prepare(definition,target,*,state_dir=None,report_type='auto',slot=None,period=None,component_ids=None,**_unused):
    validate_definition(definition)
    if target not in definition['targets'] or component_ids not in (None,['chenruichun_all']):
        raise ValueError('Unregistered Chen Ruichun target/component')
    at=datetime.now(TZ)
    section=scheduled_report_type(at)if report_type=='auto'else report_type
    if section not in {'process','result'}:
        raise ValueError('Prepare one current-calendar report section')
    root=Path(state_dir or definition['state_dir'])
    root.mkdir(parents=True,exist_ok=True)
    rows,proof=source.read(definition,target,root,slot)
    if period is not None and period!=proof['period']:
        raise ValueError('Chen Ruichun must use the current calendar period')
    selected=[row for row in rows if row['期次']==proof['period']and'陈瑞春'in str(row['渠道'])]
    expected=sum(n for channel,n in proof['evidence']['periods'][proof['period']]['channel_counts'].items()if'陈瑞春'in channel)
    if len(selected)!=expected:
        raise ValueError('Chen Ruichun source count differs from upstream')
    audit={}
    selected=merge_duplicate_lead_ids(selected,audit)
    outcomes={};artifacts=[];computed=None
    if not selected:
        outcomes['chenruichun_all']={'status':'skipped_no_source_rows','channel':'陈瑞春'}
    else:
        report.validate_scope(selected,'陈瑞春',proof['period'],source_channel={'match_mode':'contains','keyword':'陈瑞春','case_sensitive':True})
        _,counters=report.projection(list(selected[0]),section)
        computed=report.build_report(selected,counters,proof['period'],section,min_post_leads=6,included_grades=['高一','高二','高三'])
        computed['show_totals']=True
        if not computed['blocks']:
            outcomes['chenruichun_all']={'status':'skipped_no_eligible_rows','channel':'陈瑞春'}
        else:
            image=root/'chenruichun.png'
            columns,widths=image_columns(definition,section)
            geometry=report.render_image(computed,section,image,font_loader=_find_font,center_text=_center_text,
                                          format_value=_format_value,rate_parser=_rate,columns=columns,widths=widths)
            reminders=[{'channel':'陈瑞春 · '+block['grade'],'grain':'顾问','rank':'minimum_all_ties',
                        'names':block['reminders'][section]}for block in computed['blocks']if block['reminders'][section]]
            artifacts=[{'grade':'高一 / 高二 / 高三','path':str(image),'component_ids':['chenruichun_all'],
                'sha256':hashlib.sha256(image.read_bytes()).hexdigest(),'reminders':reminders,'geometry':geometry}]
            outcomes['chenruichun_all']={'status':'prepared','channel':'陈瑞春','raw_count':expected,
                'visible_rows':sum(len(block['rows'])for block in computed['blocks'])}
    context={'definition':definition,'definition_sha256':source.fingerprint(definition),'target':target,
        'directory':str(root),'source':proof,'snapshot':proof['snapshot'],'period':proof['period'],'section':section,
        'component_ids':['chenruichun_all']if artifacts else[],'artifacts':artifacts,'outcomes':outcomes,
        'artifact_protocol':'market-chenruichun-advisor-artifacts-v1','skip_delivery':not artifacts,
        'message_title':f"🔥【{proof['period']}】陈瑞春IP渠道{report.SECTIONS[section]}播报",
        'computed_report':computed,'source_channel_values':sorted({row['渠道']for row in selected}),
        'dedup_audit':audit,'prepared_at':at.isoformat()}
    source.save(root/'context.json',context)
    return context


write_preview=rendering.write_preview


def schedule(definition,target,*,preflight=False):
    from .grade_bundle_runner import run
    return run(definition,target,preflight=preflight)


def send_now(definition,target,request_id,*,preflight=False):
    from .grade_bundle_runner import run
    return run(definition,target,request_id=request_id,preflight=preflight)
