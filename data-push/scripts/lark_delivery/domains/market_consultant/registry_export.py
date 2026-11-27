"""Expand current grouped configurations into stable per-intake Base candidates."""
from copy import deepcopy
import json

from ...core import catalog
from ...paths import CONFIG_ROOT, SKILL_ROOT


def records(ref,definition,kind,link_map=None):
    """Pure export only: never writes Base or changes implementation receipts."""
    if definition['adapter'] not in {'market-grade-bundle-v2','market-highschool-channel-v1'}:
        raise ValueError('Unsupported grouped registry export')
    scopes=[]
    for record_id in definition['intake_record_ids']:
        components=[c for c in definition['components'] if c['operator_record_id']==record_id]
        first=components[0]
        request_key = first.get('request_key') or 'draft_'+str(first['request_row'])
        scopes.append((ref+'/'+request_key,definition['targets'][0],components,record_id))
    result=[]
    for request,target,components,record_id in scopes:
        cfg=catalog.schedule_config(definition,target)
        first=components[0]
        grain=first['grain']
        unrestricted_grades=first.get('grade_scope')=='all'
        combined_grades=first.get('grade_grouping')=='combined'
        grades=[] if unrestricted_grades else first['grades']
        sources=list(dict.fromkeys(value for c in components for value in c['source_values']))
        dims=['期次','渠道','年级','负责人','主管']+(['顾问'] if grain=='顾问' else [])
        if combined_grades:
            dims.remove('年级')
        process=first['column_order']['process']
        conversion=first['column_order']['result']
        source=definition['source']
        url=source.get('raw_source_url') or f"https://gaotuedu.feishu.cn/base/{source['base_token']}?table={source['raw_table_id']}"
        reminder=first['reminders']
        channel_first = definition['adapter']=='market-highschool-channel-v1'
        name='、'.join(c['label'] for c in components) + ('' if channel_first else grain)
        if kind=='operator':
            fields={'申请编号':request,'申请部门':['市场顾问部'],'申请状态':['已上线' if cfg['enabled'] else '已暂停'],
                '渠道标准名称':name,'原始渠道示例':'；'.join(sources),'目标群':[{'id':target['chat_id']}],
                '原始表名称':source.get('raw_table_name','市场顾问原始数据'),'数据源链接':url,'原始表链接':url,
                '匹配关键词或规范值':'；'.join(sources),'渠道匹配方式':['多个精确值' if len(sources)>1 else '精确匹配'],
                '期次规则':['自然周周五期次'],'过程数据星期':['周一','周二','周三','周四'],
                '转化数据星期':['周五','周六','周日'],'期望推送时段':'14:00、19:00',
                '期望首次上线日期':cfg['first_send_at'],'数据维度':dims,'年级范围':grades,'播报层级':[grain],
                '提醒对象':[reminder['target']],'过程文字提醒名次':[reminder['process_rank']],
                '转化文字提醒名次':[reminder['result_rank']],'并列处理':[reminder['ties']],
                '展示门槛指标':'退后线索','门槛运算符':['>='],'门槛值':first['minimum_post_leads'],
                '过程指标（逐项勾选）':[field for field in process if field not in dims],
                '转化指标（逐项勾选）':[field for field in conversion if field not in dims],
                '过程指标展示顺序（选填）':'、'.join(process),'转化指标展示顺序（选填）':'、'.join(conversion),
                '展示总计行':first['show_totals'],
                '图片分组与排版':('每渠道一条消息，一图按高一、高二、高三分块，分年级总计和提醒'
                    if channel_first else ('按年级出图，年级内分渠道；原始配色、紧凑列宽、模块总计，不显示右上角人数'
                    if definition['report'].get('image_style')=='compact-original-colors-v1'
                    else '按年级出图，年级内分渠道')),
                '运营备注':'受治理配置候选导出，不直接覆盖现有实施回执。'}
        else:
            config_path=CONFIG_ROOT/'departments/market_consultant'/(definition['channel_id']+'.json')
            entry=SKILL_ROOT/'scripts/channels/market_consultant'/(definition['channel_id']+'.py')
            fields={'配置单ID':request+'/group','记录类型':['本地渠道推送'],'domain':'market_consultant','execution_surface':'local',
                'channel_ref':ref,'channel_id':definition['channel_id'],'adapter':definition['adapter'],'target_id':target['id'],
                'chat_id':target['chat_id'],'chat_display_name':target['display_name'],'sender_identity':'bot','sender_name':definition['sender']['name'],
                'sender_open_id':definition['sender']['open_id'],'target_enabled':target['enabled'],'schedule_enabled':cfg['enabled'],
                'source_url':url,'raw_source_url':url,'raw_table_id':source['raw_table_id'],
                'raw_table_name':source.get('raw_table_name','市场顾问原始数据'),'base_identity':'user',
                'report_profile':source['report_profile'],'included_grades':json.dumps(grades,ensure_ascii=False),
                'minimum_post_leads':first['minimum_post_leads'],
                'hours':json.dumps(cfg['hours']),'prepare_minute':cfg['prepare_minute'],'send_minute':cfg['send_minute'],
                'deadline_minute':cfg['deadline_minute'],'retry_minutes':cfg['retry_minutes'],'timezone':'Asia/Shanghai',
                'first_send_at':cfg['first_send_at'],'process_weekdays':'[0,1,2,3]','result_weekdays':'[4,5,6]',
                'windows_task_name':cfg['windows_task_name'],'state_dir':cfg['state_dir'],
                '配置文件路径':str(config_path),'定时参数文件路径':str(config_path),'入口脚本路径':str(entry),'任务执行脚本路径':str(entry),
                '任务注册脚本路径':str(SKILL_ROOT/'scripts/register_market_grade_bundle_tasks.ps1'),
                '配置JSON快照':json.dumps({'group_definition':deepcopy(definition),'operator_record_id':record_id,'target_id':target['id']},ensure_ascii=False),
                '实施状态':['已上线' if cfg['enabled'] else '已暂停'],'维护备注':'现行配置候选；不覆盖真实试发、测试与权限回执。'}
            for key in ['project_id','folder','menu_id','task_name','task_id','nezha_task_id','schedule_id','exec_file_id','verified_version_id','verified_source_sha256','log_protocol','owner']:
                fields['upstream_'+key]=cfg['upstream'][key]
            operator_id=(link_map or {}).get(request) or record_id
            if operator_id:
                fields['关联运营申请']=[{'id':operator_id}]
        if unrestricted_grades and kind=='operator':
            fields.pop('年级范围',None)
            fields['其他范围或排除规则']='不限年级。按抖音私信渠道全量读取，实际年级动态参与计算，顾问展示门槛>=3。'
            if combined_grades:
                fields['年级范围']=[]
                fields['图片分组与排版']='抖音私信全部年级合并为一张图。同负责人、主管、顾问跨年级汇总，合并后退后线索≥3展示。紧凑列宽、原始配色、可见人员总计。'
                fields['其他范围或排除规则']='原始渠道精确等于抖音私信，全部年级合并参与计算，包含学习分享及后续新分类。顾问退后线索≥3在跨年级汇总后应用。'
        if kind == 'operator' and first.get('process_5min_target') is not None:
            from decimal import Decimal
            target = Decimal(str(first['process_5min_target'])) * 100
            fields['图片分组与排版'] += (
                f'过程图片增加截面单效（净收款÷退后线索）；5min低于{target:.2f}%的顾问'
                '使用浅红底、红色进度条和深红数字，达标人员保留橙色条及黑色数字，总计保持原样。')
            fields['运营备注'] += (
                f'每次过程播报文字说明5min达标标准≥{target:.2f}%及颜色含义；'
                f'恰好{target:.2f}%视为达标，按原始分子分母判断。')
        if kind == 'operator' and first.get('daily_standards') is not None:
            fields['过程文字提醒名次'] = ['低于每日标准']
            fields['过程数据星期'] = ['周一','周二','周三','周四','周六','周日']
            fields['图片分组与排版'] += (
                '周一至周三过程按5min降序，周四按双沟率降序。周五至周日本期转化按截面单效降序，'
                '仅周六、周日同条消息增加下期过程图，按好友率降序；周五只推本期转化。'
                '每图按高一、高二、高三分块并保留可见人员总计。'
                '低于当日标准的指标使用浅红底、红色条及深红数字。')
            fields['运营备注'] += (
                '周三5min各年级≥30%；周四双沟率高一≥10%、高二≥9%、高三≥10%；'
                '周六下期好友率各年级≥50%，周日≥60%。周一、周二无达标标准，消息不额外说明；周五不播下期过程。'
                '统一说明已设标准，分年级@全部未达标主管，个人后不附数值；AB意向率不纳入。'
                '转化保留原截面单效最低值提醒。')
        if kind == 'technical' and first.get('daily_standards') is not None:
            fields['weekend_next_process_enabled'] = True
            fields['weekend_next_process_minimum_post_leads'] = first['minimum_post_leads']
            fields['process_weekdays'] = '[0,1,2,3,5,6]'
        if definition['report'].get('grade9_daily_policy') is not None:
            if kind == 'operator':
                thresholds = first['grade9_benchmarks']['targets']
                fields['过程数据星期'] = ['周一','周二','周三','周四','周五','周六','周日']
                fields['过程文字提醒名次'] = ['低于每日标准' if thresholds else '不提醒']
                fields['图片分组与排版'] += (
                    '周一、周二仅发图片，无对比和@；周一至周三5min降序，周四双沟率降序。'
                    '周五至周日本期转化按截面单效降序，下期过程按好友率降序，两个期次分开消息与重试。'
                    '同一标准组的两个KOC仍分别展示、分别计算。')
                if thresholds:
                    rates = {key: float(value)*100 for key, value in thresholds.items()}
                    fields['运营备注'] += (
                        f"初三标准：周三5min≥{rates['2']:g}%，周四双沟率≥{rates['3']:g}%，"
                        f"周六下期好友率≥{rates['5']:g}%，周日≥{rates['6']:g}%。"
                        '统一说明标准，@全部未达标主管，提醒不附个人数值；无标准不额外说明。')
                else:
                    fields['运营备注'] += '广东、山东暂不设过程标准，不生成过程达标对比和@；保留原转化最低值提醒。'
            else:
                fields['weekend_next_process_enabled'] = True
                fields['weekend_next_process_minimum_post_leads'] = first['minimum_post_leads']
                fields['process_weekdays'] = '[0,1,2,3,4,5,6]'
        result.append(fields)
    return result
