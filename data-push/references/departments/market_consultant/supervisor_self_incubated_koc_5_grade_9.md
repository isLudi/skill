# KOC 孟亚飞数学与自孵化 5 元纯课初三主管播报

本渠道只负责 `KOC-孟亚飞数学` 与 `自孵化KOC-5元纯课` 的 `初三` 数据，使用主管明细模板，并固定投递到群 `oc_601bde838d4fbda7ac09840a58228f9c`（核验名称 `💗0925期【KOC初中】沟通群`）。两个渠道分别生成图片、文案和主管提醒，不合并汇总；群名仅用于漂移核验，不用于搜索替代 `chat_id`。

## 固定范围

- 渠道入口：`market_consultant/supervisor_self_incubated_koc_5_grade_9`
- 渠道：`KOC-孟亚飞数学`、`自孵化KOC-5元纯课`，各自独立生成图片与消息。
- 唯一年级：`初三`
- 数据源、期次、主管解析、图片列、文案及颜色规则均与 [KOC与抖音私信主管播报](supervisor_koc_douyin_sync.md) 一致。本期转化及周一至周四过程数据的主管入图门槛为退后线索不少于 10 条；周五至周日下一期过程数据的门槛为不少于 5 条。
- 每张图保留负责人和主管；每个初三色块内的过程数据按未四舍五入的 5min 率降序，转化数据按未四舍五入的截面单效降序；等值使用相同色阶。
- 过程和转化分别@初三范围内精确最低主管，所有并列者都提醒；仅使用唯一解析且已验证属于目标群的 `open_id`。
- 本地预览以已认证 user 身份只读核验群名和成员；正式消息仍固定由 `sender.identity=bot` 的“管家”发送，两个身份不得互相替代。

## 周期与调度

周一至周四播报本期过程数据。周五至周日每个渠道的一条消息先播报本期转化数据，再播报下一自然周周五期次的过程数据；两期独立制图和计算最低主管提醒。某期某渠道没有主管达到对应门槛时只跳过该部分。它加入 13、17、21 点三轮全局播报，固定为第 5 顺位并与第 6 顺位任务在每轮 `:22` 同分钟启动，失败时每 2 分钟重试，最后有效点为 `:50`。Windows 任务名为 `Codex-Lark-Supervisor-KOC-Grade9-Push`。

配置中 `schedule.enabled=true` 只是已审阅的目标状态；只有运行注册脚本并读回任务后才算真正启用。预览、立即群发和启用调度是三个独立阶段。

## 本地入口

以下命令只读取数据和生成本地预览，不上传图片、不发送消息：

周末双期预览会标明本期转化与下一期过程各自的入图门槛；未达到门槛的部分会在预览中说明跳过原因，该说明不会进入群消息。

```powershell
& 'D:\anaconda3\python.exe' 'C:\Users\Ludim\.codex\skills\data-push\scripts\channels\market_consultant\supervisor_self_incubated_koc_5_grade_9.py' describe
& 'D:\anaconda3\python.exe' 'C:\Users\Ludim\.codex\skills\data-push\scripts\channels\market_consultant\supervisor_self_incubated_koc_5_grade_9.py' preview
```

审阅通过后，立即群发使用同一入口的 `send-now` 并提供唯一 `request-id`；确认一次真实回执后，才可执行：

```powershell
& 'C:\Users\Ludim\.codex\skills\data-push\scripts\register_supervisor_self_incubated_koc_5_grade_9_scheduled_push.ps1' -ConfirmEnable
```

注册后必须读回任务名、动作、三个触发时间和下一次运行时间；不得改动或重启其他播报任务。
