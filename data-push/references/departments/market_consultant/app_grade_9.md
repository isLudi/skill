# APP 初三顾问与群内有序消息

配置：[app_grade_9.json](../../../config/departments/market_consultant/app_grade_9.json)；入口：[app_grade_9.py](../../../scripts/channels/market_consultant/app_grade_9.py)。需求来自渠道配置 Base 的申请 `market_consultant/app_grade_9`，2026-10-10 读取运营记录 `recvxD76bIB8eG`；转化提醒指标由用户确认使用截面单效。

## 顾问报告

- 源表使用申请所指 Base 中的 `tbljWRvaqKTdrCx4`，实际名称为“市场顾问线索原始数据”。链接中的视图只用于解析坐标，汇总读取整张原始表的期次数据。
- 渠道只接受 `app` 的大小写变体，先完整读取期次再在本地精确匹配；不匹配包含 APP 的其他渠道。仅初三，图片每行显示负责人、主管、顾问。
- 每个负责人、主管、顾问分组的退后线索至少 5，低于门槛不展示、不参加提醒。顾问图片不显示总计行。
- 过程列：期次、负责人、主管、顾问、退后线索、首call、48h外呼、外呼频次、5min、好友率、深沟率、双沟率。首call 为首call完成标记除以退后线索。
- 转化列：期次、负责人、主管、顾问、退后线索、5min、双沟率、首节到课率、当期单效、截面单效。需求展示顺序未列顾问，但数据维度和排版明确需要顾问，故补在主管之后；截面单效按需求展示顺序保留。
- 过程以 5min 标记合计除以退后线索取最低；转化以净收款合计除以退后线索取最低，即截面单效。比较原始分子分母，全部最低值并列顾问均提醒。图片过程按 5min 降序，转化按截面单效降序。
- 沿用市场顾问部深藏青表头、5min 橙色、双沟率蓝色、截面单效排名配色。原主管模块的门槛和总计行为继续由主管配置控制。

## APP 群消息顺序

周五至周日以自然周周五期次生成四条独立消息，全部由 `app_grade_9` 的同一个入口串行投递：

| 顺序 | 消息 | 数据期次 |
|---|---|---|
| 1 | APP主管本期转化 | 本期 |
| 2 | APP顾问本期转化 | 本期 |
| 3 | APP主管下期过程 | 下一周五期次 |
| 4 | APP顾问下期过程 | 下一周五期次 |

周一至周四发送本期主管过程、顾问过程两条消息。主管组件引用 `market_consultant/supervisor_yafei_grade_9` 的现有口径，顾问组件使用本申请口径。

全部组件必须来自同一完整 Base 版本、源表和数仓快照，并逐条通过上游行数、期次、身份、门槛及账号门禁。每条拥有独立且固定的 `report_kind` 和幂等键；前条失败或回执未确定即停止后条。重试复用原键，已有回执的消息不重发；已有尝试记录的版本或期次变化时停止本批次，防止四条混用快照。

协调入口仅在 `schedule.enabled=true` 且 `delivery_sequence.stage=scheduled` 后接管原初三主管入口中的 APP；原入口继续负责 B 站。集团私域与 APP 高中群不受此路由影响。新增配置目前 `schedule.enabled=false`、`stage=preview_only`，未创建或启用 Windows 任务，原群定时行为仍按现有入口执行。

## 本地预览和投递边界

```powershell
python scripts/channels/market_consultant/app_grade_9.py preview --state-dir <本地输出目录>
python scripts/channels/market_consultant/app_grade_9.py preview-order --state-dir <本地输出目录>
```

`preview` 展示顾问本期转化及下期过程；`preview-order` 展示完整四条顺序。两者对 APP 均不查找账号、不邀请群成员、不发消息，姓名显示为待核验。

定时启用需在预览完成并获得启用授权后单独验收：先准备禁用状态的 Windows 任务，在发送窗口外切换协调配置，启用任务后核验原主管入口只处理 B 站、协调入口处理四条 APP 消息，保留原台账。一次性 `send-now` 和补发仍要求显式命令及确认参数，由同一个有序入口执行四条。
