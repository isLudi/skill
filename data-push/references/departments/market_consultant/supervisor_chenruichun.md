# 陈瑞春顾问维度播报

## 已确认配置

- 部门：`market_consultant`
- 本地渠道：`market_consultant/supervisor_chenruichun`
- 标准渠道名：`陈瑞春`
- 原始渠道范围：原始表 `渠道` 字段中**包含 `陈瑞春` 的全部渠道**，过程与转化共用此规则。关键词可出现在渠道名的任何位置；不使用固定渠道清单。`陈瑞春-视频号49`、`陈瑞春-百度`、`陈瑞春-B站`、`陈瑞春-抖音199`、`陈瑞春抖音199`、`B站信息流-陈瑞春` 都在范围内，后续新增包含该关键词的渠道自动纳入。
- 目标群：`oc_510ee233f666207fbda3a4ec473bf388`，展示名 `💪0925期【春春】大麦「市场顾问部」`
- 报告模板：顾问粒度，图片同时列出负责人、主管、顾问三级
- 年级：高一、高二、高三
- 顾问行展示及提醒门槛：同一年级、负责人、主管、顾问聚合后的退后线索 `> 5`（即 `>= 6`）
- 提醒对象：顾问；过程取 5min 率最低，转化取净收款/退后线索对应的单效最低；并列全部提醒
- 周期：自然周周五期次；周一至周四过程，周五至周日转化
- 正式调度：`Codex-Lark-Supervisor-Chen-Ruichun-Push` 已启用，每日 13:23、17:23、21:23 与第 7 顺位任务同分钟触发；是否实际投递仍以对应发送回执为准。

## 图片字段

过程图：期次、负责人、主管、顾问、退前线索、退后线索、线索留存率、总通时(min)、首call率、48h外呼、外呼频次、5min、好友率、APP登陆率、深沟率、双沟率。

转化图：期次、负责人、主管、顾问、退后线索、首节到课率、单效（当期）、人均报科、人头转化、订单转化、净收款、退费率、单效。

低于门槛的顾问行不进入图片、总计和提醒；底层原始数据仍保留并记录隐藏原因。数据源按期次、渠道、lead_id 和快照一致性校验，不能用其他期次补数。

## 渠道匹配与汇总（2026-10-03 核对）

- 本地事实配置 `config/departments/market_consultant/supervisor_chenruichun.json` 已使用 `source.channel_match={field:渠道, match_mode:contains, keyword:陈瑞春, case_sensitive:true}`。Windows 任务通过 `supervisor_chenruichun_scheduled_push.json` 的指针读取这份配置，过程与转化没有独立的三渠道限制。
- 取数时服务端按当期期次及 `渠道 contains 陈瑞春` 筛选，完整分页后在本地再次匹配；上游行数校验也汇总所有包含 `陈瑞春` 的渠道。`raw_read_audit.matched_channel_values` 记录本轮实际纳入的原始渠道，不能把示例名称当作白名单。
- 所有匹配渠道合并为一份 `陈瑞春` 顾问报告，按同一年级、负责人、主管、顾问汇总分子分母并计算指标；展示门槛在跨渠道汇总后应用。新增渠道沿用既有期次、年级、门槛、提醒和发送门禁。
- 本地发送台账证明：2026-10-01 21:00 过程批次和 2026-10-03 13:00 转化批次均为 `sent_verified`；两轮都纳入 `B站信息流-陈瑞春`、`陈瑞春-B站`、`陈瑞春-抖音199`、`陈瑞春-百度`、`陈瑞春-视频号49`。这是已核验快照中的实际渠道，完整范围仍由关键词决定。

## 预览入口

```powershell
& 'D:\anaconda3\python.exe' 'scripts/channels/market_consultant/supervisor_chenruichun.py' describe
& 'D:\anaconda3\python.exe' 'scripts/channels/market_consultant/supervisor_chenruichun.py' preview --report-type both
```

如果目标群尚未加入全部被提醒顾问，可使用以下仅预览参数保留真实已解析 @，并把未入群人员显示为“待核验”；该参数不能用于 `run` 或 `send-now`：

```powershell
& 'D:\anaconda3\python.exe' 'scripts/channels/market_consultant/supervisor_chenruichun.py' preview --report-type both --preview-allow-mention-gaps
```

预览只读取数据并生成本地图片、Markdown 和 JSON，不上传图片、不发送消息，也不更改已启用的计划任务。正式调度仍须逐次通过上游、源表、群成员、幂等和发送回读门禁；预览参数不能替代这些校验。
