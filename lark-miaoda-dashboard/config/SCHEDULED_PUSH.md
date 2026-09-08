# 本机正式群播报

本地配置：`scheduled_push.json`。首次允许发送为 **2026-09-07 21:20（北京时间）**。

- 每天仅 09:20、13:20、17:20、21:20 推送；01:20、05:20 不推送。
- 一个群：`【自营koc】&【高阳团队】`；机器人身份：`管家`。
- `KOC-周帅数学`、`KOC-孟亚飞数学` 分别发送，每条含过程和结果两张图片与各自文字、动态期次、后25%顾问提醒。
- 提醒仅姓名，不 @ 任何顾问、主管或全部成员。图片继续隐藏退前与退后线索均为0的明细行。

## Windows 任务

任务名：`Codex-Lark-Market-KOC-GroupPush`。每天对应时点的 :15 启动隐藏的准备进程，提前取数和制图；代码在 :20 之前不会上传/发送正式消息。:20 重新核验上游和 Base 数据版本后发送，因此实际到达有接口耗时。

未就绪按 :20、:22……:50 网格重查。:50 是最后一次检查窗口；到 :51 不再开始本轮检查，不补历史轮次。Windows 错过触发后可补启动，但代码仍限制当前四个小时的有效窗口。

运行使用已登录的 Windows 用户、普通权限和 `D:\anaconda3\python.exe`；无需 Codex 常开，无可见控制台。电脑必须开机、联网并保持 Windows 登录；锁屏可运行，关机/休眠无法保证准时。本配置没有修改全局电源设置或天宫调度。

## 安全门禁与运行记录

1. 通过现有受治理 Tiangong 只读操作器核验精确任务、所有者、计划轮次、执行成功及完整 stage 日志。
2. 绑定当前已核验的执行文件版本。上游发布新版本、改变调度或日志协议时会停止推送，须重新核验，不自动放宽。
3. 校验最终回读、全量/分渠道行数、真实分区和期次；Base 完整分页并确认两个渠道同一版本，发送前再次校验版本。
4. SQLite 主键和操作系统文件锁防止同一轮同一渠道并发或重复发送。发送请求超时/回执不确定不盲目重发，转人工核对。
5. 实际返回 `message_id` 后先持久保存回执，再删除本次两张 PNG，最后独立读取消息验证图片、期次、发送人及无 @。上传或发送失败保留图片。

状态目录：`C:\Users\Ludim\.codex\runtime\channel-broadcast-push\scheduled`。

- `deliveries.sqlite3`：每轮每渠道的真实消息ID、上游证据、图片清理及独立读回结果。
- `run-*.out.log` / `run-*.err.log`：隐藏进程的输出和错误日志。
- `preflight.json`：只读预检，不代表已发送。

`sent_verified` 表示已发送且读回验证通过；`sent_unverified` 表示接口返回真实ID但独立验收未通过；`sending`/`uncertain` 必须先核对群内事实，不能清空台账后重发。

## Base 的最小依赖

同一个 `市场顾问部_全渠道线索播报` Base 保留以下 4 张表；不要迁移到旧 IP Base，也不要只看本地脚本就删除上游表。

| 表 | 必须保留的字段和视图 | 原因 |
|---|---|---|
| 市场顾问原始数据 `tbljWRvaqKTdrCx4` | 天宫映射的全部 45 个字段；`vewO4yxS3O` | 本地汇总的唯一明细来源；天宫会校验并全量写入 45 个字段，源链接还固定引用该视图。原始表不嵌入计算逻辑。 |
| 全渠道播报_推送配置 `tblqvlnqNslL1nWA` | `配置名称、渠道、推送类型、推送标题、推送期次、推送说明、接收群`；`veweZNrbGI` | 本地直接读取这 7 列；两渠道各有过程/结果配置，共 4 条。主视图保持无筛选。 |
| 市场顾问播报_经理 `tblvBLOSRUggxsBF` | 文本字段 `汇总键、顾问账号、渠道`；`vewcDSJJq0` | 天宫在写入结束后主动同步 `渠道\|经理` 键并检查覆盖率，不能删除表或上述字段。 |
| 市场顾问播报_主管 `tblQp7kAaLd6rkIh` | 文本字段 `汇总键、顾问账号、渠道`；`vewcDSJJq0` | 天宫主动同步 `渠道\|主管` 键并检查覆盖率，不能删除表或上述字段。 |

原始表和两张键表保留全部渠道，不局限于当前推送的两渠道；天宫对全部渠道做全量检查。本地取明细不绑定图片视图，而是显式按渠道和期次筛选。

推送期次保留公式 `IFERROR(FIRST([市场顾问原始数据].[期次].LISTCOMBINE().UNIQUE()),"")`。同一期次校验继续生效，不能以公式首项代替数据完整性检查。标题和业务说明仍在 Base 编辑；收件群由本地正式配置指定，Base `接收群` 留空时采用本地值，非空且冲突则停止。

Base 不再需要提醒辅助表、后25%名单/摘要公式、经理/主管指标公式、发送触发列或任何旧工作流。提醒、图片及汇总文字均在本地从同一批原始线索重算。停用推送应调整 Windows 任务或本地 `enabled`，不是寻找已删除的 Base “启用”字段。

清理取证与恢复材料：`C:\Users\Ludim\.codex\runtime\channel-broadcast-push\base-cleanup-20260907`。删除前保留了被删表/配置的记录、字段定义、视图设置及工作流定义；`verification.json` 是清理后的读回验收。材料可用于重建，不能保证恢复原对象 ID，不应自动重建或恢复旧工作流。

## 管理

只读预检（不上传、不发群消息）：

```powershell
& 'D:\anaconda3\python.exe' 'C:\Users\Ludim\.codex\skills\lark-miaoda-dashboard\scripts\scheduled_push.py' --preflight
```

查看状态：

```powershell
Get-ScheduledTask -TaskName 'Codex-Lark-Market-KOC-GroupPush'
Get-ScheduledTaskInfo -TaskName 'Codex-Lark-Market-KOC-GroupPush'
```

暂停后续触发需明确执行 `Disable-ScheduledTask`；它不会自动停止已在运行的进程。若需要立刻阻断当前轮次，先核对任务状态和发送台账，再明确停止该精确任务，不能停其他飞书服务。

维护中不删除成功回执数据库、不复制个人登录缓存到其他账号、不把 Base 配置中的启用开关误当作本地任务开关。暂停本方案以 Windows 任务状态和本地 `enabled` 为准。

任务设置参考：[微软 Register-ScheduledTask](https://learn.microsoft.com/en-us/powershell/module/scheduledtasks/register-scheduledtask?view=windowsserver2025-ps)。
