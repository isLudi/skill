# 亚飞 B 站与 APP 初三主管播报

本渠道负责 `B站信息流-亚飞` 与 `app` 的 `初三` 数据，使用主管明细模板，并固定投递到群 `oc_3c652da1589558f0b0585d2bdb2f8cb9`（机器人检索名称 `💪1009期【B站＋APP】沟通群`）。群名仅用于漂移核验，不用于搜索替代 `chat_id`。

## 固定范围

- 渠道入口：`market_consultant/supervisor_yafei_grade_9`
- 渠道：`B站信息流-亚飞`、`app`。`app`、`APP`、`App` 仅按完整渠道值忽略大小写匹配，其他含 APP 的渠道名不纳入。
- 唯一年级：`初三`。
- 数据源、期次、主管解析、最少退后线索 10 条、图片列、文案及颜色规则均与 [KOC与抖音私信主管播报](supervisor_koc_douyin_sync.md) 一致。
- 每张图保留负责人和主管；过程数据按未四舍五入的 5min 率降序，转化数据按未四舍五入的截面单效降序；等值使用相同色阶。
- 每个渠道分别按初三范围@最低过程/转化指标主管，所有并列者都提醒；图片与提醒按渠道分开生成，仅使用唯一解析且已验证属于目标群的 `open_id`。
- 当上游审计证明某个渠道当期为 0 行时，只跳过该渠道并保留另一渠道的播报；APP 有行但筛选后没有符合门槛的初三主管时也只跳过 APP，不阻断 B 站。审计缺失或数据不一致仍失败关闭。
- 本地预览与正式消息均使用 `bot` 身份核验并操作目标群；消息由“管家”发送。

## 周期与调度

周一至周四自动播报过程数据；周五至周日自动播报当前期转化结果，并追加下一期过程数据。它加入 13、17、21 点三轮全局播报，固定为第 6 顺位并与第 5 顺位任务在每轮 `:22` 同分钟启动，失败时每 2 分钟重试，最后有效点为 `:50`。Windows 任务名为 `Codex-Lark-Supervisor-Yafei-Grade9-Push`。

配置中 `schedule.enabled=true` 只是已审阅的目标状态；只有运行注册脚本并读回任务后才算真正启用。预览、立即群发和启用调度是三个独立阶段。

## 本地入口

以下命令只读取数据和生成本地预览，不上传图片、不发送消息：

```powershell
& 'D:\anaconda3\python.exe' 'C:\Users\Ludim\.codex\skills\data-push\scripts\channels\market_consultant\supervisor_yafei_grade_9.py' describe
& 'D:\anaconda3\python.exe' 'C:\Users\Ludim\.codex\skills\data-push\scripts\channels\market_consultant\supervisor_yafei_grade_9.py' preview --report-type both
```

审阅通过后，立即群发使用同一入口的 `preflight-now` 与 `send-now` 并提供同一个唯一 `request-id`；确认每个非空渠道均取得真实回执后，才可执行：

```powershell
& 'C:\Users\Ludim\.codex\skills\data-push\scripts\register_supervisor_yafei_grade_9_scheduled_push.ps1' -ConfirmEnable
```

注册后必须读回任务名、动作、三个触发时间和下一次运行时间；不得改动或重启其他播报任务。

## 顾问维度扩展

同一群新增独立顾问维度入口 `market_consultant/supervisor_yafei_grade_9_advisor`，仍绑定群 ID `oc_3c652da1589558f0b0585d2bdb2f8cb9`，渠道为 `B站信息流-亚飞`，年级为 `初三`。

- 图片同时展示负责人、主管、顾问三级维度；顾问退后线索少于 5 条不展示。
- 周一至周四推送过程数据；周五至周日推送当前期转化数据并追加下一期过程数据；当前本地配置保留 13、17、21 点时段，错峰分钟为 `:24`，独立于主管任务的 `:22`。
- 过程提醒按顾问维度取 5min 底部 10%，每个年级至少提醒 1 名；转化提醒按顾问维度取截面单效底部 10%，每个年级至少提醒 1 名。
- 转化图片按截面单效降序排列并标色；5min 使用橙色色块，双沟率使用蓝色色块，截面单效沿用主管维度结果色阶。
- 入口脚本为 `scripts/channels/market_consultant/supervisor_yafei_grade_9_advisor.py`；主管与顾问任务均启用周末双期播报，Windows 任务注册状态以任务读回为准。
