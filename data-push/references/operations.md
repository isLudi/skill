# 本机定时群播报

## lark-cli 运行时绑定

本地渠道和妙搭模板统一解析同一份包内原生 `lark-cli.exe`；Windows 上拒绝 `.cmd` / `.bat` shim。2026-09-25 已核验当前绑定版本为 `1.0.96`，原生 exe SHA-256 为 `f71aeff4a094fe3b401dcfc23d28bb9c1d7fe4923d144d15e01d1e917ba37ea`，路径为 `C:\Users\lvshuai01\AppData\Local\Programs\nodejs\node_modules\@larksuite\cli\bin\lark-cli.exe`。CLI 升级后先完成版本、原生 exe 哈希和 dry-run 回归。2026-09-25 实时查询显示六个 Windows 推送任务均为 Ready/Enabled；本次升级未改动其发送配置。

**历史记录（不构成当前授权）**：2026-09-10曾记录 Windows 任务 `Codex-Lark-Market-KOC-GroupPush` 的恢复授权。脚本维护、预览和 dry-run 本身不构成任务启停授权；实时状态以 Windows 任务查询为准。

## 当前范围

任务启动器指向新技能目录下各自的 `scripts/run_*_scheduled_push.ps1`，统一调用共享 `scripts/scheduled_push.py` 及对应的 JSON 配置。它展开登记的目标群列表；各渠道台账和错峰时点彼此独立，运行方式为隐藏窗口、Windows已登录时执行。

- 固定群：`oc_b9dc09ba622ca00059bbc472922a803d`。历史显示名为 `【自营koc】&【高阳团队】`；名称改变不影响定位，不按名称重新搜索。
- 唯一渠道：`自孵化KOC-5元纯课`。
- 发送身份：“管家”机器人，open_id为 `ou_f3907e865135732c15a1dfce27828411`。
- 原始数据表：`tbljWRvaqKTdrCx4`；本模式不依赖旧推送配置表、提醒辅助表或Base工作流。
- 年级、10条门槛、9/6列负责人图片、排序、经理最低值和@规则见 [渠道业务规范](departments/market_consultant/self_incubated_koc_5.md)。

## 时间与期次

北京时间13、17、21点为业务轮次，具体任务只运行自身配置的小时。所有本地播报按全局 `stagger_order` 排序，每分钟同时启动两个任务：第N项使用 `:20+(N-1)//2`，不改变原有群、小时或投递顺序。分区较上一快照未更新、上游未成功或其他可重试门禁失败时，以该任务自己的启动分钟为基准每2分钟重查；只允许落在 `:50` 或更早的网格点，下一次超过 `:50` 就结束，不补历史轮次。

当前八项顺序：`:20` 为 `Market-KOC-GroupPush`、`Business-KOC-Math-Push`；`:21` 为 `Supervisor-KOC-Douyin-Push`、`Supervisor-Private-App-Push`；`:22` 为 `Supervisor-KOC-Grade9-Push`、`Supervisor-Yafei-Grade9-Push`；`:23` 为 `Supervisor-Zhu-Doctor-Video49-Push`、`Supervisor-Chen-Ruichun-Push`。这些名称均有 `Codex-Lark-` 前缀；前两项仅13、17点，其余项13、17、21点。共享调度器仍以 `:50` 为统一硬截止；例如 `:23` 任务最后一个有效重试点是 `:49`。

- 周一至周四：当期过程数据，一张分年级图片。
- 周五至周日：仅当期结果数据，一张结果图片；结果列为期次、负责人、（主管）、退后线索、5min、双沟率、首节到课率、当期单效、截面单效。结果行按截面单效严格降序，5min 使用橙色进度条，截面单效按当前可见行由绿到红着色。
- 当期取当前自然周（周一至周日）的周五日期。9月7日至13日是20260911期；9月14日起是20260918期。不能取Base最大期次。
- 当期数据不存在、全部年级被门槛排除时停止，不改发下一期或旧期。

电脑需开机联网、Windows用户已登录；锁屏可运行，关机或休眠不能保证准时。不需要Codex常开。本次未改全局电源设置或天宫每4小时调度。

## 已核验上游与门禁

2026-09-15只读验收的上游为 `market2lark` V16，版本205577，执行文件819021；源码SHA-256 `f25f642bb80877bc3fcc0a525d672b22a618d0aec7ae313f45a16ebbd9fa1655`。发布计划回读证明当前源码等于最新已发布源码。验收执行170703854是2026-09-14 21:00的唯一 `SCHEDULE` 实例：task与单一stage成功、`exit_code=0`，采用dt=20260914/hour=19，输出20436行、45字段、20260911期与20260918期、50个渠道、未识别渠道0，Base创建、逐字段回读和最终20436条回读一致。

V16与V17均使用 `two_period_clear_then_replace_v1`：先校验旧/新两期数量保护，再清空旧记录并回读0条，随后创建并全量回读新记录。本地 parser 必须同时校验清空前数量、实际清空数量、空表回读、创建数量、双期清单、最终数量和成功退出。该协议不是可恢复的原子替换；创建失败或新记录回读失败时只能清理本批可识别新记录，不能恢复已经删除的旧快照。上游失败时本地必须拒绝发送，不能把平台终态或单个 `SUCCESS` 文本当作完整交付。

2026-09-16 21:00 的唯一 `SCHEDULE` 成功实例 `171092302` 使用 `market2lark` V17（版本 `205860`、执行文件 `819901`、源码 SHA-256 `9b2fe8a252be4c86a06bb7df7add937c16ea0a6a4dfb5cd28b2d500d12c6d941`）。单一 stage 成功且 `exit_code=0`，采用 `dt=20260916/hour=19`，输出 21493 行、45 字段、两期、50 个渠道；清空旧记录、创建新记录和最终 21493 条回读一致。六份本地配置已同步绑定此版本，真实日志通过六份配置的 parser 校验。`scripts/lark_delivery/integrations/tiangong_release.py` 仅保留历史兼容测试与明确批准迁移的能力；不能自动接受未来新版本。

### 天宫版本与本地配置联动

每次 `market2lark` 保存、提交或发布导致最新已发布源码、版本 ID、执行文件或日志协议变化时，远端维护不能单独视为完成。必须在下一次已启用的本地触发前完成同一发布收尾：

1. 用Tiangong2只读operator回读当前源码和最新已发布源码Hash、最新发布版本ID，并从一个新的唯一 `SCHEDULE` 成功实例取得实际 `execFileId`。
2. 拉取该实例的全部stage和分页日志，按当前数据合同核验精确任务/负责人/4h调度、stage与退出码、分区新鲜度、45字段、双期清单、渠道映射、行数/渠道分布、Base目标、创建/删除或清空顺序及最终全量回读。
3. 同一次本地变更更新所有已登记市场顾问部渠道（2026-09-21 为八个）的 `exec_file_id`、`verified_version_id`、`verified_source_sha256` 及 `config/release/market2lark.json`；解析后值必须完全一致。日志文案或替换顺序变化时，同时新增独立 `log_protocol`、更新 fail-closed parser 和正反例测试，禁止复用旧协议名称掩盖行为变化。
4. 若进量生产者 `market2lark_jinliang` 同步发布，另行核验其已发布源码 Hash、唯一 `SCHEDULE` 执行文件、完整成功日志和进量 Base 表，再更新 `config/release/market2lark_jinliang.json`。17点进量报告必须同时通过两项上游门禁，且进量表行数和所选最新期次与该次上游写入一致；不得只更新版本标签。
5. 运行所有兼容配置的 `--show-config` 一致性检查、两项真实脱敏日志 parser 验证、受影响测试、Skill校验和 scoped `git diff --check`。不得通过正式群发验证配置修改。

2026-09-21 版本联动：`market2lark` V19 / 206390 / `execFileId=823476` / SHA-256 `2250ef80ac0e92727a7936f2f5aa9fbcbae3634071500bd3cf7f0c2935375d3b`，13:00 计划执行 171961094 完整写入并回读 16359 行；相对 V18 仅修正业务期次周归一。`market2lark_jinliang` V24 / 206391 / `execFileId=823477` / SHA-256 `14369e97ae71acce03ee7bed485392e998732c45b2c2db84964e644740930449`，13:00 计划执行 171961249 完整写入并回读 101 行；相对 V23 修正规则期次归一。两任务的当前源码均与最新已发布源码 Hash 一致。进量新增独立 `volume_two_period_create_then_delete_v1` 门禁；此记录只是只读验收和本地绑定，不代表实际群消息已发送。

2026-09-25 进量版本联动：`market2lark_jinliang` V26 / 207067 / `execFileId=827092` / SHA-256 `3ed7b24b81129a1d241bcd52258e51208139b22257761b6bb7e8594625fdb4fc`，21:00 唯一计划执行 172770298 成功，采用 `dt=20260925/hour=19`，49 行、13 列、两期、15 个渠道；创建 49 条、回读 49 条、删除旧 49 条并最终回读 49 条。源码与最新已发布源码 Hash 相同。此版将预估量级和实际进量统一按分配规则渠道汇总，并修复带年份的规则期次解析；本地共用进量 pin 已绑定到该计划实例。

未完成上述联动时，旧 `exec_file_id` 门禁应继续拒绝新执行文件；不得删除版本比较、改成自动接受最新版或依靠重试掩盖发布漂移。

**2026-09-14故障记录**：V16于17:15发布，21:00计划实例已使用819021并成功写入Base，但本地四个21点任务仍绑定V14/818459。它们从21:22至约21:50持续命中 `published execution file changed`，最终退出1且没有生成当批图片或写入发送ledger。根因是远端发布与本地pin同步被拆成两个未闭环步骤。

每轮仍须检查：

1. 精确project/folder/menu/task/Nezha/owner、4h调度、本轮唯一SCHEDULE成功实例、已绑定执行文件，且没有更新的执行在替换数据。
2. 所有stage完整成功日志及Hash、创建/回读/旧记录删除/最终回读、exit_code=0。
3. 两期清单的字段数、逐期行数和渠道分布、同一分区、键及字段指纹；所有逐期汇总与日志总量一致。
4. 本群只取业务当期＋唯一渠道；Base完整分页且revision一致，行数与上游该期该渠道一致，再排除初二和小样本年级。
5. 机器人、群ID和负责人账号/群成员资格；所有最低负责人@集合精确一致，不@all。
6. 图片生成后、发送前再次检查Base版本和时间窗口。SQLite/OS锁防并发，同一群/渠道/时点只允许一条消息。

## 运行记录

状态目录：`C:\Users\lvshuai01\.codex\runtime\channel-broadcast-push\scheduled`（其余七个渠道使用各自配置中的隔离目录）。

- `deliveries.sqlite3`：真实message_id、上游证据、清理及读回结果。
- `live-status.json`：仅任务运行期间存在的实时状态快照，原子覆盖而不是追加；包含当前步骤、尝试次数、最近错误和下次重试时间。任务成功、失败或异常退出时都必须删除，不作为历史台账。启动器不再生成新的 `run-*.out.log` / `run-*.err.log`；旧文件是改造前历史，不代表当前实现仍会落日志。
- `preflight.json`：只读预检结果，不代表发送。

任务计划程序只能直接显示 `Running/Ready` 与最终退出码，不能展示脚本自定义步骤。用下列只读命令同时查看已登记任务和仅运行期存在的详细步骤；任务不在运行时 `CurrentStep` 留空是正常现象：

```powershell
& 'C:\Users\lvshuai01\.codex\skills\data-push\scripts\view_live_push_status.ps1' -Watch
```

新增任务必须复用共享状态生命周期，不得通过保留日志来实现进度查看。`validate_layout.py` 会拒绝不连续/重复的错峰顺序、每分钟超过两个或偏离配对分钟、早于`:20`或晚于`:50`的任务、非2分钟重试或非`:50`截止。

消息返回真实ID后先持久保存回执，再删除本次PNG，最后独立读回图片、期次、群ID、发送人和@账号集合。上传失败保留PNG；发送状态不确定不盲目重发；不删除或清空历史发送台账。

## 检查与恢复

### 用户明确要求立即推送一次

使用渠道入口的 `preflight-now --request-id <本次稳定ID>` 只读预检，核对后再用 `send-now --request-id <同一ID> --confirm-send`。此动作不依赖定时窗口，也不会启用或修改定时开关；必须有独立的单次发送授权。

进量图单次发送使用 `preflight-volume-now --request-id <本次稳定ID>` 与 `send-volume-now --request-id <同一ID> --confirm-send`。它沿用最新天宫周期的双生产者发布版本、唯一计划执行、完整日志、同分区/双期、进量 Base 全量及线索 Base 版本门禁；发送键与常规负责人报表分离。此入口仅发送一条进量图，不改变 13/17 点本地定时路由。

单次出口绑定最新应执行的天宫周期（含01/05点），不回退到更早成功周期；核验发布版本/源码Hash、完整日志与Base范围、身份及群成员。准备限10分钟、源快照不超过7小时；新周期开始即阻断。发送前再次核验执行历史、Base版本与星期规则。

单次使用独立请求键和同一SQLite台账。相同request-id已发送、待核验或不确定时均不重发；与后续定时轮次分开记账。预检元数据和单次回执保存在状态目录的 `immediate/<request-id>/`，发送后仅清理该次发送的PNG。

### 定时启停

```powershell
Get-ScheduledTask -TaskName 'Codex-Lark-Market-KOC-GroupPush'
Get-ScheduledTaskInfo -TaskName 'Codex-Lark-Market-KOC-GroupPush'

# 仅在相应时段执行只读预检；不会因为enabled=false而打开发送出口
& 'D:\anaconda3\python.exe' 'C:\Users\lvshuai01\.codex\skills\data-push\scripts\scheduled_push.py' --preflight
```

恢复需用户另行明确授权，并重新核验当时的上游版本、账号权限、群成员和预览；届时再设置 `enabled=true` 并启用原Windows任务。不要重建/重复注册任务，也不要改动天宫调度。仅启用其中一个开关不足以恢复正常定时发送。

暂停后续触发使用 `Disable-ScheduledTask`。若当时已有运行实例，须先核对任务/发送台账，再停止该精确实例；不能停其他飞书服务。
