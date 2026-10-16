# APP 与 B站初三主管、顾问统一任务

配置：[app_grade_9.json](../../../config/departments/market_consultant/app_grade_9.json)；入口：[app_grade_9.py](../../../scripts/channels/market_consultant/app_grade_9.py)。需求来自渠道配置 Base 的申请 `market_consultant/app_grade_9`，2026-10-10 读取运营记录 `recvxD76bIB8eG`；转化提醒指标由用户确认使用截面单效。

## 顾问报告

- 源表使用申请所指 Base 中的 `tbljWRvaqKTdrCx4`，实际名称为“市场顾问线索原始数据”。链接中的视图只用于解析坐标，汇总读取整张原始表的期次数据。
- 渠道只接受 `app` 的大小写变体，先完整读取期次再在本地精确匹配；不匹配包含 APP 的其他渠道。仅初三，图片每行显示负责人、主管、顾问。
- APP 每个负责人、主管、顾问分组的退后线索至少 5，低于门槛不展示、不参加提醒。APP 顾问图片显示可见顾问总计；总计先汇总原始分子分母，再计算比率和单效。B站顾问继续使用自身原有列、门槛及底部10%提醒。
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

上述四条 APP 顺序保留；随后按相同粒度发送 B站主管本期转化、B站顾问本期转化、B站主管下期过程、B站顾问下期过程，总共八条独立消息。周一至周四发送 APP主管过程、APP顾问过程、B站主管过程、B站顾问过程四条消息。

每条消息独立完成源表完整分页、期次/分区/源行数、组件日历、角色模板、提醒名单及发送窗口核验。主管和顾问使用各自的配置校验，周末单独核验本期转化或下期过程，不放宽角色、数据或日历门禁。

2026-10-14 按用户要求取消“前条失败阻断后条”：准备、预览、图片、校验、发送或回读失败仅影响本条消息，继续处理其他渠道、角色、期次。每条拥有独立固定的 `report_kind`、幂等键和回执；重试只处理失败项，成功消息不重发。已有尝试的版本/期次漂移仅停止该条消息，不停止其他消息。上游身份/发布绑定及发送 bot 为共享必要门禁。

协调入口在 `schedule.enabled=true` 且 `delivery_sequence.stage=scheduled` 后接管本群 APP 与 B站的主管、顾问消息。原主管和B站顾问 Windows 任务保留原历史台账，但运行时记录 `delegated_to_group_coordinator` 后退出，避免重复发送。

目标群固定 `oc_3c652da1589558f0b0585d2bdb2f8cb9`。统一任务为 `Codex-Lark-App-Grade9-Push`，每天13:24、17:24、21:24启动，每两分钟重试失败消息至:50截止。状态目录仍为 `runtime/channel-broadcast-push/app-grade-9`，日志位于机器 `paths.push_log_root/market_consultant/app_grade_9`。后台使用 machine.local.json 的 Python、pythonw 及隐藏 PowerShell 启动链。

## 本地预览和投递边界

```powershell
python scripts/channels/market_consultant/app_grade_9.py preview --state-dir <本地输出目录>
python scripts/channels/market_consultant/app_grade_9.py preview-order --state-dir <本地输出目录>
```

`preview` 展示 APP 顾问消息；`preview-order` 展示两渠道本轮四条或八条独立消息，失败条目单独显示错误，其他预览继续。预览均不发送群消息。

部署按用户本次授权，在发送窗口外准备禁用任务、完成真实隐藏环境的无发送预检、切换协调配置并启用该任务。登记脚本为 `register_app_grade_9_scheduled_push.ps1`，驱动为 `run_app_grade_9_scheduled_push.ps1`，兼容指针为 `config/app_grade_9_scheduled_push.json`。一次性发送和补发继续要求显式命令及授权。
