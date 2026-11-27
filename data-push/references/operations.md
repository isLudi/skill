# 本机定时群播报

## 本机共享平台检查与限流（2026-11-20）

市场顾问部和青橙项目部的本机推送共用 `lark_delivery/integrations/push_platform.py`。相同生产者、身份、发布绑定及命令参数的天宫历史、完整成功执行日志和已发布版本检查使用跨进程单飞锁及已校验工件复用；不同部门、任务、执行、版本和权限范围不合并。历史及发布状态最多复用自操作开始起 90 秒，成功终态日志按精确执行 ID 最多复用 1 小时；工件不存在、Hash 改变、绑定变化、操作耗时已超过有效期或时间异常时不复用。状态结果不是上游写锁，不能证明检查之后没有立即开始的新执行。

受控子进程自身持有跨进程平台操作锁，天宫只读 API 请求启动间隔按 1.2 秒控制；单次 API 调用关闭自动重试和重定向，后台推送仅验证并使用已存在的隔离登录态，不打开可产生并发请求的天宫页面。登录态失效或身份不符时该轮失败并留待单独恢复；不得绕过协调器直接请求。相同操作失败后 30 秒内合并失败结果；识别到 HTTP 429、503 或限流时全局冷却 120 秒。内部图书的历史 Data Center/USQL 入口也与本机平台操作串行，但其页面内部流量不由天宫 API 的逐请求间隔保证。本机制只覆盖接入的本机推送进程，不控制其他设备、浏览器或独立 Codex 任务。天宫请求启动记录按 UTC 日期追加到 `paths.push_log_root/_platform/`，不记录凭据、查询参数或数据行；日志写入失败不阻断业务。

市场相同的完整 45 字段线索快照、相同过滤条件的线索切片、相同进量生产者快照，以及青橙过程/转化的相同渠道和期次切片，可在本机按来源身份、表、字段、筛选、期次及可用的生产者证据复用短时快照。青橙过程的 `public_pool`/`special_public_pool` 与非空策略相同的 `partner_books`/`special_books` 复用已证明相同的切片，但各自输出清单仍保留原渠道身份。缓存位于 `runtime/data-push-platform-coordinator`，写入前检查分页完成、记录数、版本和内容 Hash；不同来源、筛选或期次不得串用，已有生产者执行证据的完整快照还必须绑定对应执行。每个渠道仍各自核验业务合同，并在发送前重新探测 Base 版本；版本变化必须阻断并重新准备。青橙转化生产者目前登记 `audit_mode=none`，完整分页和版本稳定不等于已证明上游应写数据全部写齐。

青橙已验证发送的群跳过重复来源准备；所有过程群均已验证时跳过整批上游检查，待确认回执只读回、不重发。转化图书在检查天宫前先验证发送机器人在群状态，排队完成后再次核对两个 Base 版本及授权发送截止时间。青橙过程、专项、伙伴和 SEC 也在实际发送前检查原有窗口；排队超出窗口时不补发。空渠道仍按其既有上游证据和重试窗口处理，不把临时空表当作永久无数据。

## lark-cli 运行时绑定

本地渠道和妙搭模板统一解析同一份包内原生 `lark-cli.exe`；Windows 上拒绝 `.cmd` / `.bat` shim。2026-11-14 已核验绑定版本为 `1.0.100`，原生 exe SHA-256 为 `935f51e02dab23e3266f3fc419f6d140c7c85ae5923712514adb06b7e2548b52`，路径为 `C:\Users\lvshuai01\AppData\Local\Programs\nodejs\node_modules\@larksuite\cli\bin\lark-cli.exe`。`data-push` 常规运行时与模板刷新解析器均回读到该路径并执行出 `1.0.100`；回复元字符 dry-run 和 11 项推送传输相关测试通过。本次升级未改动发送配置或 Windows 推送任务。历史版本记录见 `sync-qingcheng-market-temp-tables/references/event_service.md`。

**历史记录（不构成当前授权）**：2026-09-10曾记录 Windows 任务 `Codex-Lark-Market-KOC-GroupPush` 的恢复授权。脚本维护、预览和 dry-run 本身不构成任务启停授权；实时状态以 Windows 任务查询为准。

## 当前范围

市场顾问部现行范围登记[8项本地任务](departments/market_consultant.md#现行本地推送设置2026-10-29)，包含两个高阳团队、4项渠道群任务、陈瑞春IP及APP进量播报。Windows用户登录后以隐藏方式运行，各群使用独立台账。旧主管、顾问任务的当前恢复及退役状态以部门清单为准。

- 固定群：`oc_b9dc09ba622ca00059bbc472922a803d`。历史显示名为 `【自营koc】&【高阳团队】`；名称改变不影响定位，不按名称重新搜索。
- 唯一渠道：`自孵化KOC-5元纯课`。
- 发送身份：“管家”机器人，open_id为 `ou_f3907e865135732c15a1dfce27828411`。
- 原始数据表：`tbljWRvaqKTdrCx4`；本模式不依赖旧推送配置表、提醒辅助表或Base工作流。
- 年级、10条门槛、9/6列负责人图片、排序、经理最低值和@规则见 [渠道业务规范](departments/market_consultant/self_incubated_koc_5.md)。

## 时间与期次

APP进量为独立的每天17:20任务，每2分钟重试至17:50，绑定进量生产者。期次、指标与配置见[APP进量播报](departments/market_consultant/app_volume.md)。

两个高阳团队继续原13:20、17:20窗口；4项bundle和恢复的陈瑞春IP均每天14:00、19:00独立启动，分别核验13:00、17:00上游SCHEDULE，每2分钟重试至当前槽位:50。已无17:50同期对比任务。陈瑞春保留原顾问图、总计及>5门槛，不套用其他bundle的≥5门槛和紧凑布局；4项bundle于2026-11-01部署原始配色的紧凑图，并为每个渠道模块显示可见人员总计。

当前不再有市场旧任务21点播报。原13:21—13:25、17:21—17:25、21:21—21:25等旧主管/顾问轮次已随9项任务退役。任务、群与开关的唯一当前事实源是 `config/channels.json`，只读汇总命令为 `scripts/show_market_push_settings.py`。

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

两部门本地推送以 `task_key` 引用生产者。发布收尾只更新该生产者的一份 `config/release/` 登记，由所有相关本机入口在运行时读取。Windows 任务、消费者 JSON 和幂等键沿用原有配置。

1. 从天宫 2 的当前发布读回、实际执行详情、完整 stage、独立 Base 回读核对精确项目、任务、版本、源码原文 Hash 和实际执行文件。生产者维持各自的调度、目标表、分区、字段、期次、行数与写入顺序合同。
2. 通过 `scripts/manage_push_upstream.py` 核验并登记已审核的版本、执行文件与新计划执行。源码 Hash 变化时同时审批新原文 Hash。平台目前缺直接版本映射，同 Hash 发布仍需这一次受控登记，时间顺序只用于筛选执行。
3. 四个稳定键为 `market_consultant.leads`、`market_consultant.volume`、`qingcheng.process`、`qingcheng.transformation`。市场进量仍需线索与进量两份当期证据同分区、同双期。青橙转化按过程和转化两个源角色读取原表，图书保留已有实发就绪核验。
4. 先用 `--show-config` 或 `--check-config` 回读涉及的消费者，再验收各自的首个自然窗口。日志或数据合同变化要同步评审生产者解析器及其正反例。

```text
python scripts/manage_push_upstream.py verify <task_key> --version-id <version_id> --exec-file-id <execFileId> --execution-id <execution_id>
python scripts/manage_push_upstream.py adopt <task_key> --version-id <version_id> --exec-file-id <execFileId> --execution-id <execution_id> --review-reference <发布映射与独立Base回读工件>
```

使用机器配置的 Python。`verify` 核对线上当前发布、实际生效调度、唯一且最新的计划执行及完整 stage。`adopt` 要求明确的审核回执，并对现行登记复查漂移后原子替换和读回。新源码需追加 `--approve-source-sha256 <发布源码原文SHA-256>`。核验可复用已有上游维护的发布、自然执行与 Base 回读工件，后续定时入口直接使用新登记。若平台上实际替换了任务本身，先审定新任务身份、调度和目标表，再迁移同一稳定键对应的登记。

市场线索渠道版本升级同时传入 `--channel-mapping-version <四位版本>`，工具核对当前发布源码中的唯一版本常量及完整成功日志的版本标记，并在同一次登记中写入该字段。

青橙已授权的发布写入可使用 `--execution-receipt <execute-task-once回执>` 登记一次受控 `EXECUTE`。工具核对 operator runtime 内的回执与计划 Hash、精确任务、发布版本和源码、执行 ID 及周期，并核对完整终态日志和最新写入状态。回执绑定禁止下游、额外参数、禁用 stage 和既有执行重跑。独立 Base 全字段回读工件作为 `--review-reference`，登记保留执行回执路径及文件 Hash。常规定时实例继续使用原计划执行核验。

2026-09-21 版本联动：`market2lark` V19 / 206390 / `execFileId=823476` / SHA-256 `2250ef80ac0e92727a7936f2f5aa9fbcbae3634071500bd3cf7f0c2935375d3b`，13:00 计划执行 171961094 完整写入并回读 16359 行；相对 V18 仅修正业务期次周归一。`market2lark_jinliang` V24 / 206391 / `execFileId=823477` / SHA-256 `14369e97ae71acce03ee7bed485392e998732c45b2c2db84964e644740930449`，13:00 计划执行 171961249 完整写入并回读 101 行；相对 V23 修正规则期次归一。两任务的当前源码均与最新已发布源码 Hash 一致。进量新增独立 `volume_two_period_create_then_delete_v1` 门禁；此记录只是只读验收和本地绑定，不代表实际群消息已发送。

2026-09-25 进量版本联动：`market2lark_jinliang` V26 / 207067 / `execFileId=827092` / SHA-256 `3ed7b24b81129a1d241bcd52258e51208139b22257761b6bb7e8594625fdb4fc`，21:00 唯一计划执行 172770298 成功，采用 `dt=20260925/hour=19`，49 行、13 列、两期、15 个渠道；创建 49 条、回读 49 条、删除旧 49 条并最终回读 49 条。源码与最新已发布源码 Hash 相同。此版将预估量级和实际进量统一按分配规则渠道汇总，并修复带年份的规则期次解析；本地共用进量 pin 已绑定到该计划实例。

2026-10-13 warning 批次升级收尾：`market2lark_warning` 当前绑定 V8/version `208044`、实际 `execFileId=837867`、源码 SHA-256 `87c47311119ccd42807cad0a28fa520726307896b5413042aa8913632590c1cf`。自有 task `47889`、Nezha `67653`、menu `104255`、schedule `55203` 保持原样。2026-10-12 17:10 的既有唯一 `SCHEDULE` 执行 `175809802` 于 17:20:12 成功完成，26 字段，新记录创建及全量逐字段回读 9857 条、旧记录删除 15432 条、最终回读 9857 条，`exit_code=0`；当前源码与最新已发布源码一致。删除每批 500、写入每批 1000，日志协议仍为 `warning_two_period_create_then_delete_v1`。本机 `supervisor_koc_zhoushuai_warning` 配置已同步版本、源码 Hash、执行文件及验收执行编号。

此次 warning 联动完成晚于本机窗口：2026-10-12 17:45 启动时仍绑定旧版本，KOC-周帅数学、抖音私信、KOC-孟亚飞数学、自孵化 KOC 初三四份报告均 `blocked_before_send`，原因是 `Published warning source/version no longer matches local binding`，没有消息发送。验收监测在北京时间次日凌晨才触发。故障回执位于机器 `paths.push_log_root` 下本渠道 `2026-10-12/174501-Codex-Lark-Market-KOC-Zhoushuai-Warning-Push.result.json`。历史执行日志 parser 仅按执行结束时刻核验历史数据；当前过期快照仍被新鲜度门禁拒绝。未改任务计划、群、发送日历或启停状态，未补发历史报告。将来再次发布应在已启用本机触发前完成绑定，监测配置必须核对时区及实际下一次触发时刻。

未完成上述联动时，旧 `exec_file_id` 门禁应继续拒绝新执行文件；不得删除版本比较、改成自动接受最新版或依靠重试掩盖发布漂移。

**2026-09-14故障记录**：V16于17:15发布，21:00计划实例已使用819021并成功写入Base，但本地四个21点任务仍绑定V14/818459。它们从21:22至约21:50持续命中 `published execution file changed`，最终退出1且没有生成当批图片或写入发送ledger。根因是远端发布与本地pin同步被拆成两个未闭环步骤。

每轮仍须检查：

1. 精确project/folder/menu/task/Nezha/owner、4h调度、本轮唯一SCHEDULE成功实例、已绑定执行文件，且没有更新的执行在替换数据。
2. 所有stage完整成功日志及Hash、创建/回读/旧记录删除/最终回读、exit_code=0。
3. 两期清单的字段数、逐期行数和渠道分布、同一分区、键及字段指纹；所有逐期汇总与日志总量一致。
4. 本群只取业务当期＋唯一渠道；Base完整分页且revision一致，行数与上游该期该渠道一致，再排除初二和小样本年级。
5. 机器人身份和目标群 ID 独立核验；业务提醒名单由已核验 @ 与姓名文字完整覆盖。无法解析、不在群、通讯录或群成员查询失败的人员直接使用姓名文字；实际 @ 集合只与已核验且在群的账号集合一致，不 @all、不自动邀请人员。
6. 图片生成后、发送前再次检查Base版本和时间窗口。SQLite/OS锁防并发，同一群/渠道/时点只允许一条消息。

## 运行记录与日志存储规范

状态目录：`C:\Users\lvshuai01\.codex\runtime\channel-broadcast-push\scheduled`（其余七个渠道使用各自配置中的隔离目录）。

- `deliveries.sqlite3`：真实message_id、上游证据、清理及读回结果。
- `channel_events` 表（同一 SQLite 文件内）：每渠道每轮的结论 `at / slot / channel / status / reason`，追加写。它与 `deliveries` **分开**是因为 `deliveries` 是发送认领表，同一 key 存在任何一行都会让该渠道被当作已处理，观测记录绝不能抑制真实发送。
- `live-status.json`：仅任务运行期间存在的实时状态快照，原子覆盖而不是追加；包含当前步骤、尝试次数、最近错误和下次重试时间。任务成功、失败或异常退出时都必须删除，不作为历史台账。
- `preflight.json`：只读预检结果，不代表发送。

### 日志落盘规范（2026-09-28 起）

根目录取机器本地 `codex_home/machine.local.json` 的 `paths.push_log_root`（模板见技能仓库 `codex-config/machine.local.example.json`）。当前值为 `D:\CodexLogs\data-push`。

约束：

- **不得写系统盘。** 日志根目录放在数据盘且必须位于 `D:\GAOTU` **之外**：`run_*.ps1` 会枚举 `D:\GAOTU` 下 `19002_*` 目录并要求恰好一个，在该目录内新建任何匹配项都会直接打断全部推送任务。
- **写日志失败只降级告警，绝不阻断投递。** 路径不可用时会输出一条 `push_log_unavailable` 事件，运行继续。
- 文本为 UTF-8 无 BOM；`.ps1` 侧用 `[System.IO.File]::AppendAllText` 显式指定 UTF-8，不要用 `Tee-Object`（PowerShell 5.1 下会写 UTF-16）。日志不得包含 token、cookie 或其它凭据。

布局（`<部门>` 为 `market_consultant` 或 `qingcheng`；`<渠道>` 在市场顾问部取 `channel_ref` 的最后一段，在青橙项目部取批次配置的文件名主干，如 `process_batch`、`sec_process_batch`、`special_process_batch`）：

| 路径 | 内容 |
|---|---|
| `<root>/<部门>/<渠道>/<YYYY-MM-DD>/<HHMMSS>-<任务名>.jsonl` | 一次进程运行的完整事件流（含该时点全部重试），JSON Lines |
| `<root>/<部门>/<渠道>/<YYYY-MM-DD>/<HHMMSS>-<任务名>.result.json` | 该次运行结论：`slot`、`started_at`/`finished_at`、`exit_code`、`last_event`、逐渠道 `channels`、逐报告 `outcomes`、`needs_attention` |
| `<root>/<部门>/<渠道>/<YYYY-MM-DD>/<HHMMSS>-process.log` | 进程 stdout/stderr，覆盖事件之外的崩溃、argparse 报错和启动器异常 |
| `<root>/_index/runs.jsonl` | 每次运行一行汇总裁剪，单文件即可回答"今天哪些时段失败、哪些渠道需要关注" |

保留期 30 天；每次开新日志时按天目录清理更早的文件并删除空目录。

约定的事件名：市场顾问部时点生命周期 `started` / `checking_bot_identity` / `checking_upstream` / `preparing_channel_report` / `preparing_volume_report` / `validating_channel_snapshot` / `prepared_waiting_for_send_time` / `delivering_channels` / `round_finished` / `round_needs_attention`；门禁与重试 `not_ready` / `waiting_to_retry` / `deadline_skipped` / `outside_authorized_window` / `another_instance_active` / `all_channels_absent_in_upstream` / `channel_skipped_no_source_rows` / `approved_release_file_bound`；预检 `preflight_passed_no_send` / `preflight_incomplete`；青橙项目部 `run_started` / `report_ready` / `run_finished` / `run_needs_attention`；两者共用的 `outcome`（青橙逐条结论）；未确认送达的重发 `resending_after_uncertain`（市场侧 `channel_outcome`，只标记本轮决策，会被该轮最终结论覆盖）；降级 `push_log_unavailable`。

市场顾问部每渠道每轮的结论统一用 `channel_outcome` 事件承载，`result.json` 的 `channels` 由它归并，取值：`sent_verified` / `sent_unverified` / `uncertain` / `readback_failed` / `duplicate_suppressed` / `skipped_no_eligible_rows` / `skipped_no_source_rows` / `blocked_prepare` / `blocked_snapshot` / `blocked_revision` / `blocked_delivery` / `preflight_ready` / `blocked_preflight`。`readback_failed` 表示**消息已在群内但回读未通过**：不再重发（重发只会多一条），需要人工核对。青橙项目部复用同一套词汇，按 `渠道/年级`（`public_pool/supervisor` 等）或按报告 id（`sec_no_friend_supervisor` 等）落成 `outcomes`；`needs_attention` 取两者中不属于 `push_log.CLEAN_STATUSES` 的键。任何 `return True` 的跳过路径都必须留下 `channel_outcome`、`outcome` 或台账行——只存在于 stdout 的结论视为不可观测。

### 未确认送达的重发与只回读重验（2026-09-29 起）

一次几秒的网络抖动曾经等于一条播报永久丢失：只要收据不是 `sent_verified`，所有后续轮次都读到"需人工复核"而拒绝重试，2 分钟的重试循环空转到 `:50`。判据太宽——**从未拿到 message_id 的发送本来就可以安全重发**。

统一判据只有一条，两个部门共用 `lark_delivery/common/resend.py` 的 `decide(status, message_id)`：

> **有 message_id → 只补回读，绝不重发；没有 message_id → 用原键重发。**

- 重发安全的依据是**幂等键是确定的**：槽位被归一化到固定分钟，所以同一槽位每一轮算出的键逐字节相同（青橙 `_key`，市场 `delivery_ledger.delivery_key`），且市场侧该键已经作为 `--idempotency-key` 传给飞书。若那一条其实已进群，平台按同键去重并**返回原 message_id**，不会重复发；若没进群则补发。这也顺带自愈了"响应丢失"这种真正模糊的情况——拿回原 message_id 后回读通过，槽位收敛。
- **不能靠错误类型判断。** 令牌可能是缓存的，刷新失败时发送照样可能已经出去，所以"错误发生在交付之前"并不证明消息没发。只有幂等键能定这件事。
- 重试节奏两部门不同但都只需"不再挡"即可恢复：市场是 `run_slot` 的**进程内循环**，青橙是任务计划程序 `PT2M` 触发的**每轮全新进程**。
- 只回读的一侧绝不调用发送出口（市场 `reverify_unverified_delivery` 自带乐观锁且没有发送能力；青橙 `send_qingcheng_process.py --reverify-only` 同样只读），所以**已在群内的消息不可能被补发成两条**。持续回读失败就是 `readback_failed`，交人工。
- 重发证据落在收据上（`resend_attempts` / `prior_status`）：青橙每轮重写收据，而运行日志只记最终结论，收据才是唯一能看出"重发了几次、上一轮是什么状态"的地方。

### 内容不可回读的群（保密模式）

2026-09-29 又暴露了第二类假失败：目标群开了**保密模式**时，`restricted_mode_setting.status=true` 且 `message_has_permission_setting="not_anyone"`——**发送是写操作仍然允许，读取消息内容被禁止**。于是 `chat-messages-list` 和 `messages-mget` 一律返回空，收据里的 message_id "取不到"，而消息其实**已经进群**（该群当天确实收到了，同一群在管理端可见）。**读权限缺失与消息缺失在这一状态下完全无法区分。**

这带来两个必须防住的后果，由 `lark_delivery/common/readback.py` 与 `resend.decide(..., readback_available=False)` 处理：

- **永久假失败**：该渠道会每次推送都报 `readback_failed`、任务永远 `exit_code=1`，而群其实一直正常收到。
- **重复发送**：这里"message_id 取不到"是**结构性必然**，所以任何"看起来没发出去就换新键重发"的规则都会**每一轮补发一条**（一个槽位最多约 13 条）。同一天一次手工新键尝试就制造了一条重复。**因此 `decide` 永远不产出新键动作。**

判定顺序：渠道配置里的 `readback_unavailable` 声明最优先；否则在**回读失败的那条路径上**探测一次 `im chats get` 并按进程缓存（正常路径不额外调用）；**任何探测错误都判为"可回读"**——绝不能因为探针自身失败就默默接受一次真实的投递失败。

该状态下的终态记为 `resend.UNVERIFIABLE`（`sent_unverifiable`），它是**干净状态**（在 `push_log.CLEAN_STATUSES` 里），不再计入 `needs_attention`。回读仍然会尝试，所以群里限制解除后会自动恢复为 `sent_verified`——2026-09-29 该群解除保密模式后已实测恢复：历史消息可读、两个已知 message_id 都能取回。

### 发送前只读探测的传输失败：轮内重试（2026-09-29 起）

2026-09-29 16:20 的 SEC 槽位连续丢掉三轮，原因不是数据问题，而是**发送前的 Base 版本探测**撞上连接重置：

```
base +record-list ... --limit 1 --as user
→ wsarecv: An existing connection was forcibly closed by the remote host.
```

探测是**用来判断"此刻发送是否仍然安全"的一次读**。它读不到时，**关于数据什么都没得知**——而旧行为把整轮判为失败，白丢一个 2 分钟的槽位。判据因此拆成两半：

- 探测**返回**了一个不同的版本号 → **这是结论**，立刻 fail-closed，**绝不重试**（数据真的动了）；
- 探测**抛传输错误** → **无法验证**，在轮内短暂重试（默认 3 次、间隔 2 秒），仍失败才让错误冒出去，该轮照旧失败。

**这个方向不可能掩盖真实的版本漂移**：漂移是**返回值**，而重试只作用于**异常**，且仅限传输类——其余异常第一次就原样抛出。

实现：`lark_delivery/common/retry.py` 的 `retry_transport`，配合 `common/runtime.py` 新增的 `LarkTransportError`（`RuntimeError` 的子类，因此既有的 `except RuntimeError` 全部照旧）。已包住的站点：市场侧 `reporting.assert_current_revision`（覆盖 scheduler 与 immediate 的所有调用点），青橙侧四个 runner 的 `probe_revision`。

**这条只保证不白丢轮次，网络故障本身并没有消失。** 另注：源抓取（`fetch`）与上游审计命中传输失败时**仍是整轮失败**（青橙会把整个渠道标成 `blocked_source`）——2026-09-29 14:47 丢掉的正是这一类；同一套 `retry_transport` 可以一行包住它们，是否需要另议。

任务计划程序只能直接显示 `Running/Ready` 与最终退出码，不能展示脚本自定义步骤。用下列只读命令从上述日志汇总各渠道最近一次运行的时点、退出码、最后事件和受影响渠道：

```powershell
& 'C:\Users\lvshuai01\.codex\skills\data-push\scripts\view_live_push_status.ps1' -Watch
```

排查群静默的顺序：先看 `_index/runs.jsonl` 定位失败的时点与渠道，再读对应 `.jsonl` 看 `not_ready` / `deadline_skipped` 的原始 `reason`，最后用 `-process.log` 补 `emit` 之外的崩溃。**不要依赖 `live-status.json`**，它在每次运行结束时按设计删除。

新增任务必须复用该共享 sink（`lark_delivery/common/push_log.py`）与共享状态生命周期，不得自建日志文件或自定义日志格式。市场顾问部的消费者是 `scheduler.emit`（`channel_outcome` 事件，并与 `deliveries.sqlite3` 的 `channel_events` 表同步）。青橙项目部的定时 runner 由任务计划程序直接调用、没有 PowerShell 包装层，因此在各自 `main()` 里用 `push_log.run_scope(部门, 渠道, 任务名)` 包住运行体：它同时镜像 stdout/stderr 到 `-process.log`，并在作用域退出时把批量结果按渠道/年级（或按报告）落成 `outcomes`。即使作用域内抛 `SystemExit`，`result.json` 仍会写完，且**任务退出码不被改变**。`validate_layout.py` 会拒绝不连续/重复的错峰顺序、每分钟超过两个或偏离配对分钟、早于`:20`或晚于`:50`的任务、非2分钟重试或非`:50`截止，以及模块内的未定义名字。

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

### 计划任务后台隐藏运行（2026-10-01 起）

用户反馈任务到点弹出前台控制台窗口。全部 14 个群推送任务已改为无窗口形态：5 个青橙 Python 任务的动作改为 `D:\anaconda3\pythonw.exe`（GUI 子系统，不分配控制台）；9 个市场 PowerShell 任务的动作改为 `pythonw.exe scripts/run_hidden_push.pyw "<原 ps1>"`，该包装器以 `CREATE_NO_WINDOW` 启动 powershell.exe（分配不可见控制台，`[Console]` API 仍可用），子进程继承隐藏控制台。退出码原样传播，`LastTaskResult` 语义不变。

配套脚本改动：`lark_delivery/common/runtime.py` 新增 `CREATE_NO_WINDOW` 常量（`run_lark` 的子进程调用已带上）与 `ensure_console_streams()`（pythonw 下 `sys.stdout` 为 `None`，防止 print 崩溃）；5 个青橙执行器 `main()` 入口均调用该保护；`run_qingcheng_process.py`、`run_qingcheng_transformation.py` 内直连 subprocess 调用已加 `creationflags`。注册/安装脚本已同步（install_qingcheng_*、register_*scheduled_push* 均产出 pythonw 形态），重装与生产一致。

注意事项：S4U（不管用户是否登录都运行）曾被用户首选，但本机安全策略层会拦截新任务创建并把 S4U 规范回 InteractiveToken，不可达，退回 pythonw 方案；任务仍保持 InteractiveToken/LeastPrivilege，只在用户登录时运行。`Codex-Governed-TempTables-LarkEvent` 为常驻监听服务、非推送任务，未改动。多群解耦核验：六群、SEC 五报告、专项四渠道、伙伴三渠道、转化、市场调度器均已有逐渠道 try/except 熔断与独立回执（市场按渠道一任务一配置结构性隔离），本次改造不触碰该逻辑。任务定义备份在 `runtime/task-hidden-backup-20261001/`。

### 计划任务编码与结果恢复

新增渠道或修改本地取数链路时，以下要求同时适用于独立任务和并入现有批次的渠道。

#### 子进程编码

父进程的 `encoding="utf-8"` 只设置读取端，不能改变子进程输出编码。Python 查询工具必须在每次调用时显式设置子进程环境，保留其他环境变量；不得依赖交互终端已有的 UTF-8 设置。沿用机器登记的 Python、工作目录、隐藏窗口和超时，例如：

```python
import os
import subprocess

from lark_delivery.common.runtime import CREATE_NO_WINDOW


def run_python_child(command, workdir, timeout_seconds):
    child_env = os.environ.copy()
    child_env.update(PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    return subprocess.run(
        command,
        cwd=workdir,
        env=child_env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=timeout_seconds,
        creationflags=CREATE_NO_WINDOW,
    )
```

非 Python CLI 按其已核验的输出协议设置编码。禁止用 `errors="replace"`、`errors="ignore"` 或猜测编码把损坏的 JSON 当作有效结果。stdout 为 `None`、空内容或解析失败时，记录为传输/解析异常，不能解释为零条业务数据；按共享日志规范保留失败步骤、异常类型及已知 Query ID/SQL Hash，不输出凭证。

#### 后台环境验收

- 只读回实际任务动作、参数、工作目录、身份和 `LogonType`；用对应的 `pythonw.exe` 或隐藏包装器执行无发送探针，核对登录/session 条件，保持任务定义不变。
- 在独立探针的父进程环境中移除 `PYTHONIOENCODING`、`PYTHONUTF8`，让被测调用自行设置子进程编码。探针至少覆盖含中文渠道、期次的 JSON 往返、返回码和状态工件落盘；结果必须保存为可回读证据。
- 对结果恢复补有意义的验证：上游已成功但 stdout 缺失、SQL Hash 漂移、Query ID 歧义、未知尝试、不完整分页及过期快照。验证不会重复提交未知查询、不会补零，并且其他渠道继续处理；离线验证使用固定工件或 mock，不发送消息。
- 交互预览、后台探针和真实调度投递分别验收。部署后追踪已授权的首个自动窗口，逐渠道检查 push_log result、原始进程日志、发送回执和消息读回；任务退出码或查询 `Success` 不能单独证明消息送达。

#### 查询结果持久化与恢复

提交前原子保存尝试状态，绑定渠道、原始槽位、源身份、期次/范围、SQL Hash 和本次独立结果工件路径；取得 Query ID 后及时持久化。结果工件、summary 和尝试状态采用原子写入，使后续重试能读到完整证据。

本地 summary 缺失或尝试停在 `started` 时，先检查原查询证据：

1. 工件位于本渠道、本尝试绑定的目录；源身份、期次/范围及 SQL Hash 一致。涉及编辑器与提交 Hash 的查询须同时匹配，Query ID 必须唯一且无冲突。
2. 原生状态已终结为成功，工件类型、`ok`、完整性校验均通过；仅有预览行、退出码 0 或 `started` 不足以确认成功。
3. 依据原 Query ID 完整读取分页结果，再核验源版本、分区、同快照和新鲜度，沿原槽位继续准备消息。stdout 解析失败本身不能触发重新提交 SQL。

查询仍运行或结果未知时保留证据并阻断本渠道；禁止删除尝试状态、扩大新鲜度或补零来解锁。已确认原查询完成但快照过期时，按原取数规则刷新数据并保留旧证据。某渠道的查询、解码或恢复失败须落成该渠道 outcome，继续处理其他独立渠道和群。

恢复发送仍使用原槽位、payload 和幂等键；已有 message_id 只补读回，已验证消息不重发，不清空发送台账。实际故障与恢复实例见 [青橙内部图书首轮计划任务编码故障记录](departments/qingcheng/local_broadcast_rules.md)。
