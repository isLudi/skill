# 精品班学部渠道、触达、学习与退款原因

## 渠道归因

历史渠道规则来自 Base `O2Rdb1v58ac1VTs6PsrcWtZHnSh`、表 `tblCiP801wWblywT`、视图 `vewrdx1WO6`，当前快照有46个历史版本。按线索所属业务期间选择历史CASE并保持原始 `WHEN` 顺序；未命中时依次使用经审阅的 `rule_name` 清洗、原始渠道层级，最后保留未知。未知不进入前10是质量目标，不是强制归类许可。

全链路线索表必须由精品班财务集合的 `lead_id` 或 `lead_id+业绩顾问` 做受限Join，并比较覆盖、重复和金额膨胀。

历史CASE与 `rule_name` 仍无法归类时，可将已限定精品班课程范围的业财订单 `lead_id` 与 `gaotu_hl.dwd_mkt_h_lead_detail_df` 受限关联。H表必须先按 `lead_id` 去重：有效 `channel_map` 优先，再按 `has_rule_config`、`is_current_period_lead`、`stat_period_name` 选择稳定记录；`channel_map='其他未知流量'` 不视为有效映射。订单 `lead_id` 缺失时，才允许用同学员历史线索兜底，并优先选择其 `lead_id` 出现在范围订单集合中的H表记录。回挂前后必须对账GMV、退款金额、购买人数和退费人数，不能直接把H表明细Join到财务明细后聚合。

最终交付同时保留一级渠道结构和明细渠道。一级结构可依据H表 `channel_group` 与历史规则语义统一商务渠道、信息流、赠课、公海回捞、B站信息流等稳定类别；明细渠道保留原始映射用于追溯。该标准化只能合并有明确共同语义的已知渠道，不能拆分或重命名无证据订单来改变未知排名。

## 触达与学习

有效接通为 `call_status=1 AND call_duration>0`。支付前及支付后至首次合格退款前的平均通话时长均用有效接通总时长/次数；无接通与短通话分开。24/48/72小时、7天、正价首节等节点只纳入节点前未发生合格退款的风险集。

二讲首次联系三状态为退款前已接通、首次接通未早于退款、截至观察日未见该老师已接通外呼。`assistant_email_prefix` 只是候选身份；支付时历史二讲来源和跨业绩部门组织范围未确认前不生成指标。

学习明细候选为 `service_dw.dws_service_user_learn_detail_hf`。有效直播要求 `is_valid_live_learn=1` 且直播时长大于0。“未匹配”表示无法建立课程/班级关联，“未上课”表示已匹配但无有效直播。暑期三期和秋季正价首节排课需从精品班实际日历取得并与学习明细交叉验证。

## 系统原因、ASR与AI

系统原因候选为 `finance_dw.dwd_finance_order_refund_df`，需按退款订单和版本去重并对账。ASR候选为 `one_dw.dwd_mkt_ai_assistant_asr_record_df`，通过 `origin_file_url` 连接录音URL；AI候选为 `service_dw.ods_service_ai_ones_business_copilot__ai_call_analysis_result_df`，通过 `call_id` 连接。两者先在call grain按更新时间/版本去重。

证据层级为R（明确退款原因）、S（退款前有支持的问题）、U（证据不足或仅流程对话）、A（AI补充候选）。A不能并入R。“先报后退”自动筛选仅形成候选，顾问人数、学员数和退款金额需标记人工复核状态。原始ASR、手机号、学员标识、订单号和个人证据不进入飞书。

## 顾问司龄

司龄使用支付时业绩顾问，以支付日员工快照 `email_prefix` 连接并读取 `last_enroll_date`。分为未满3个月、3至未满6个月、6至未满12个月、1年及以上。员工表要求组织范围，必须先从精品班财务事实形成完整支付时顾问组织枚举，不能只筛当前在职或单一部门。缺失、冲突和异常关联单列质量状态。
