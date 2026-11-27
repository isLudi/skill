"""Operator-facing configuration export for reviewed volume reports."""
from .volume_report import IMAGE_COLUMNS


def operator_record(ref, definition):
    target = definition['targets'][0]
    channel = definition['channel']
    spec = definition['volume_report']
    business_channels = spec.get('business_channels', [channel])
    source_values = spec.get('source_values', [channel])
    metrics = ['预估量级','实际进量','线索留存率','人均带班','量级完成度']
    return {'申请编号':ref, '申请部门':['市场顾问部'],
        '申请状态':['已上线' if definition['schedule']['enabled'] else '待上线'],
        '渠道标准名称':channel+'进量播报', '原始渠道示例':'；'.join(business_channels), '目标群':[{'id':target['chat_id']}],
        '数据源链接':definition['source']['raw_source_url'], '原始表链接':definition['source']['raw_source_url'],
        '原始表名称':'市场顾问进量原始数据', '匹配关键词或规范值':'；'.join(source_values),
        '渠道匹配方式':['多个精确值' if len(source_values)>1 else '精确匹配'], '期次规则':['其他待评审'],
        '其他范围或排除规则':'使用进量表选定分配规则渠道的最新可用期次。渠道名Unicode规范化后精确匹配，忽略大小写，按年级汇总。',
        '过程数据星期':['周一','周二','周三','周四','周五','周六','周日'],
        '转化数据星期':[], '期望推送时段':'每天17:20',
        '期望首次上线日期':definition['schedule']['first_send_at'],
        '数据维度':['期次','渠道','年级'], '年级范围':spec.get('included_grades',[]), '播报层级':[],
        '提醒对象':['不提醒'],
        '过程文字提醒名次':['不适用'], '转化文字提醒名次':['不适用'],
        '过程指标（逐项勾选）':metrics, '转化指标（逐项勾选）':[],
        '过程指标展示顺序（选填）':'、'.join(IMAGE_COLUMNS), '转化指标展示顺序（选填）':'',
        '展示总计行':True, '图片分组与排版':'一张分年级进量表，深蓝表头与总计行，线索留存率和量级完成度使用进度条。',
        '运营备注':'每天播报进量数据。按年级汇总原始分子、分母后计算，总计同口径重算，文字提示完成度最低的一个年级。'}
