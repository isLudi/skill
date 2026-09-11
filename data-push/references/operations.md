# 本机定时群播报

**2026-09-10经用户明确授权恢复**：Windows任务 `Codex-Lark-Market-KOC-GroupPush` 已启用，渠道配置的 `schedule.enabled=true`。后续检查仍须实时读回两个开关；脚本维护、预览和dry-run本身不构成恢复授权。

## 当前范围

任务启动器指向新技能目录下 `scripts/run_scheduled_push.ps1`，内部调用本渠道独立入口 `scripts/channels/market_consultant/self_incubated_koc_5.py`。它展开登记的目标群列表；主群台账及四个触发时点保持不变，运行方式为隐藏窗口、Windows已登录时执行。

- 固定群：`oc_b9dc09ba622ca00059bbc472922a803d`。历史显示名为 `【自营koc】&【高阳团队】`；名称改变不影响定位，不按名称重新搜索。
- 唯一渠道：`自孵化KOC-5元纯课`。
- 发送身份：“管家”机器人，open_id为 `ou_f3907e865135732c15a1dfce27828411`。
- 原始数据表：`tbljWRvaqKTdrCx4`；本模式不依赖旧推送配置表、提醒辅助表或Base工作流。
- 年级、10条门槛、9/6列负责人图片、排序、经理最低值和@规则见 [渠道业务规范](departments/market_consultant/self_incubated_koc_5.md)。

## 时间与期次

北京时间每天09、13、17、21点各有一轮。所有已启用本地播报按全局 `stagger_order` 错峰，依次在 `:20`、`:21`、`:22`、`:23` 启动并立即检查；以后新增第N个任务使用 `:19+N`，不得复用已有分钟。分区较上一快照未更新、上游未成功或其他可重试门禁失败时，以该任务自己的启动分钟为基准每2分钟重查；只允许落在 `:50` 或更早的网格点，下一次超过 `:50` 就结束，不补历史轮次。

当前顺序：`Codex-Lark-Market-KOC-GroupPush` 为 `:20`，`Codex-Lark-Business-KOC-Math-Push` 为 `:21`，`Codex-Lark-Supervisor-KOC-Douyin-Push` 为 `:22`，`Codex-Lark-Supervisor-Private-App-Push` 为 `:23`。共享调度器仍以 `:50` 为统一硬截止；例如 `:23` 任务最后一个有效重试点是 `:49`。

- 周一至周四：当期过程数据，一张分年级图片。
- 周五至周日：仅当期结果数据，一张结果图片；结果列为期次、负责人、（主管）、退后线索、5min、双沟率、首节到课率、当期单效、截面单效。结果行按截面单效严格降序，5min 使用橙色进度条，截面单效按当前可见行由绿到红着色。
- 当期取当前自然周（周一至周日）的周五日期。9月7日至13日是20260911期；9月14日起是20260918期。不能取Base最大期次。
- 当期数据不存在、全部年级被门槛排除时停止，不改发下一期或旧期。

电脑需开机联网、Windows用户已登录；锁屏可运行，关机或休眠不能保证准时。不需要Codex常开。本次未改全局电源设置或天宫每4小时调度。

## 已核验上游与门禁

2026-09-10只读核验的上游为 `market2lark` V7，版本205254，执行文件816853；源码SHA-256 `7fbf76134c9eb18079f511703ecf1ed69afc20a4ce976d172e9f308564046e10`。该版本仍使用45字段和 `market2lark-two-period-audit-v1` 双期快照清单。

当前配置直接绑定已核验的执行文件，不再使用已经结束的V4一次性迁移窗口。`scripts/lark_delivery/integrations/tiangong_release.py` 仅保留历史兼容测试与明确批准迁移的能力；不能自动接受未来新版本。

每轮仍须检查：

1. 精确project/folder/menu/task/Nezha/owner、4h调度、本轮唯一SCHEDULE成功实例、已绑定执行文件，且没有更新的执行在替换数据。
2. 所有stage完整成功日志及Hash、创建/回读/旧记录删除/最终回读、exit_code=0。
3. 两期清单的字段数、逐期行数和渠道分布、同一分区、键及字段指纹；所有逐期汇总与日志总量一致。
4. 本群只取业务当期＋唯一渠道；Base完整分页且revision一致，行数与上游该期该渠道一致，再排除初二和小样本年级。
5. 机器人、群ID和负责人账号/群成员资格；所有最低负责人@集合精确一致，不@all。
6. 图片生成后、发送前再次检查Base版本和时间窗口。SQLite/OS锁防并发，同一群/渠道/时点只允许一条消息。

## 运行记录

状态目录：`C:\Users\Ludim\.codex\runtime\channel-broadcast-push\scheduled`。

- `deliveries.sqlite3`：真实message_id、上游证据、清理及读回结果。
- `live-status.json`：仅任务运行期间存在的实时状态快照，原子覆盖而不是追加；包含当前步骤、尝试次数、最近错误和下次重试时间。任务成功、失败或异常退出时都必须删除，不作为历史台账。启动器不再生成新的 `run-*.out.log` / `run-*.err.log`；旧文件是改造前历史，不代表当前实现仍会落日志。
- `preflight.json`：只读预检结果，不代表发送。

任务计划程序只能直接显示 `Running/Ready` 与最终退出码，不能展示脚本自定义步骤。用下列只读命令同时查看四个任务和仅运行期存在的详细步骤；任务不在运行时 `CurrentStep` 留空是正常现象：

```powershell
& 'C:\Users\Ludim\.codex\skills\data-push\scripts\view_live_push_status.ps1' -Watch
```

新增任务必须复用共享状态生命周期，不得通过保留日志来实现进度查看。`validate_layout.py` 会拒绝不连续/重复的错峰顺序、早于`:20`的任务、非2分钟重试或非`:50`截止。

消息返回真实ID后先持久保存回执，再删除本次PNG，最后独立读回图片、期次、群ID、发送人和@账号集合。上传失败保留PNG；发送状态不确定不盲目重发；不删除或清空历史发送台账。

## 检查与恢复

### 用户明确要求立即推送一次

使用渠道入口的 `preflight-now --request-id <本次稳定ID>` 只读预检，核对后再用 `send-now --request-id <同一ID> --confirm-send`。此动作不依赖定时窗口，也不会启用或修改定时开关；必须有独立的单次发送授权。

单次出口绑定最新应执行的天宫周期（含01/05点），不回退到更早成功周期；核验发布版本/源码Hash、完整日志与Base范围、身份及群成员。准备限10分钟、源快照不超过7小时；新周期开始即阻断。发送前再次核验执行历史、Base版本与星期规则。

单次使用独立请求键和同一SQLite台账。相同request-id已发送、待核验或不确定时均不重发；与后续定时轮次分开记账。预检元数据和单次回执保存在状态目录的 `immediate/<request-id>/`，发送后仅清理该次发送的PNG。

### 定时启停

```powershell
Get-ScheduledTask -TaskName 'Codex-Lark-Market-KOC-GroupPush'
Get-ScheduledTaskInfo -TaskName 'Codex-Lark-Market-KOC-GroupPush'

# 仅在相应时段执行只读预检；不会因为enabled=false而打开发送出口
& 'D:\anaconda3\python.exe' 'C:\Users\Ludim\.codex\skills\data-push\scripts\scheduled_push.py' --preflight
```

恢复需用户另行明确授权，并重新核验当时的上游版本、账号权限、群成员和预览；届时再设置 `enabled=true` 并启用原Windows任务。不要重建/重复注册任务，也不要改动天宫调度。仅启用其中一个开关不足以恢复正常定时发送。

暂停后续触发使用 `Disable-ScheduledTask`。若当时已有运行实例，须先核对任务/发送台账，再停止该精确实例；不能停其他飞书服务。
