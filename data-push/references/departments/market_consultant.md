# 市场顾问部推送边界

业务语义入口：[market-consultant-dashboard-sql](../../../market-consultant-dashboard-sql/SKILL.md)。`data-push` 只把已确认的市场顾问部口径实现为本地或妙搭推送，不把这些规则提升为跨部门默认值。

## 当前资源

- 本地渠道以 `config/channels.json` 中 `market_consultant/*` 为准；每个渠道拥有独立配置、入口、Windows 任务和状态目录。
- 妙搭唯一登记部署为 `market_consultant/miaoda/cloud_data_push`，其中 `supervisor_koc_douyin_sync` workflow 对应当前主管播报；源码仍在 `C:\Users\Ludim\.codex\runtime\cloud-data-push-miaoda`，app 身份由该工程 `.spark/meta.json` 读回。
- 该妙搭工程目前是市场顾问部主管 KOC/抖音推送原型，不是通用跨部门宿主，也未因存在本地代码或 app 资产而自动接管 Windows 任务。

## 本部门所有的个性化规则

市场顾问部自行持有字段投影、自然周五期次、高中/年级范围、负责人和主管粒度、最小退后线索门槛、加权指标、提醒对象、图片列、排序、颜色阈值和文案。当前本地实现位于 `scripts/lark_delivery/domains/market_consultant/`；妙搭原型仍把对应实现放在自己的 `server/modules/cloud-push-demo/` 内。

两种执行面可以进行结果等价比较，但不能共享可变运行资源：本地 Windows 任务、SQLite/文件状态与妙搭自动化、PostgreSQL 台账、Secret、release、测试群各自独立。同一市场 app 内的不同 workflow 也必须有独立 module、automation namespace、ledger namespace 和业务合同。迁移或切换必须逐阶段验证，不能因为妙搭 dry-run 成功就暂停本地任务。

具体渠道的范围、指标、配色和提醒规则继续以 `references/departments/market_consultant/` 下对应文件为准。

渠道配置中心 Base 的新增三列已按本部门 9 条申请填写：2 条负责人、4 条主管、3 条顾问；其中 8 条过程和转化均取“最低值”，亚飞 B 站初三顾问取“底部10%（每年级至少1名）”。现有 `并列处理=全部提醒` 继续表达最低值并列者的提醒方式。Base 只是申请镜像，执行仍以各渠道本地配置和下列专项规则为准，不使用青橙的人数上限。

| 渠道或工作流 | 专项规则 |
|---|---|
| 自孵化 KOC 5 元纯课 | [分年级精简与进量播报](market_consultant/self_incubated_koc_5.md) |
| 商务 KOC 数学 | [双渠道与进量播报](market_consultant/business_koc_math.md) |
| KOC 与抖音私信主管 | [高中主管播报](market_consultant/supervisor_koc_douyin_sync.md) |
| KOC 初三主管 | [双渠道初三播报](market_consultant/supervisor_self_incubated_koc_5_grade_9.md) |
| 亚飞 B 站与 APP 初三主管、顾问 | [初三双维度播报](market_consultant/supervisor_yafei_grade_9.md) |
| APP 初三顾问及四条消息顺序 | [APP有序播报](market_consultant/app_grade_9.md) |
| 集团私域与 APP 主管 | [多渠道同步播报](market_consultant/supervisor_private_app_sync.md) |
| 朱博士视频号 49 | [顾问播报](market_consultant/supervisor_zhu_doctor_video49.md) |
| 陈瑞春（渠道名包含“陈瑞春”的全部渠道） | [顾问播报](market_consultant/supervisor_chenruichun.md) |

## 2026-09-13 跨渠道指标归属故障

### 故障原因

- 数据中心数据集 2253 先对事实表原始行做 `DISTINCT`，再按期次、渠道、规则、年级、组织和顾问等分配粒度汇总。只有来源经理为韩正卿的抖音私信线索分母改取 `merge_assign_lead_count` / `merge_valid_lead_count`；收款、退费、到课、沟通等事实仍按原始行相加。
- `market2lark` V10 在上述分配维度形成之后，又用 `ROW_NUMBER() OVER (PARTITION BY period_name, lead_id)` 全局只保留一个维度行。同一 lead 横跨渠道、顾问或组织时，事实会被任意归到其中一行，导致渠道图片中的收款、退费及截面单效失真。
- V11 用“期次 + lead”窗口求和后再保留一行，虽然试图保住全局金额，却仍把求和结果归到单一渠道/顾问，不能满足渠道级守恒，因此不是完整修复。
- 事故排查时，数据中心截图为“渠道：全选”，而群播报是单渠道；截图与播报还可能来自不同小时快照。未对齐期次、渠道、年级、组织和 `dt/hour` 时，二者不能直接比较。

### 修复与生产验收

- `market2lark` V13（版本 `205491`、执行文件 `818418`）删除全局 lead 选行，保留 2253 的 `DISTINCT 原始行 -> 分配粒度聚合` 合同；记录键改为 `期次|渠道|lead_id|user_id|顾问账号`，Python 唯一性校验同步到该键。45 个下游字段、渠道映射和两阶段 Bitable 替换协议保持不变。
- 发布后源码 SHA-256 为 `757b68e2df3376278496551a440d10c0fd04bb5421e3baa882edf0b9056310b3`，查询 SHA-256 为 `37b7d508ecae42b3e686cfbf3ddfd1272aab87a58607dd867c85cda94e207ffa`。
- 生产执行 `170476273` 成功：查询与回读均为 18,870 行，覆盖 20260911期和 20260918期、47 个渠道、未识别渠道 0；先创建并回读新记录，再删除旧 18,841 条记录。六个群配置随后锁定到该版本。
- 六个群共 11 个实际报表面使用同一 Bitable 修订 `5900` 和快照 `20260913-13` 完成只读预览；903 项比率/单效复算无误，全部 `message_sent=false`。

### 防回归门禁

- 任何源查询去重、窗口或记录键变更，都必须按“期次 + 渠道 + 年级 + 经理 + 主管”比较变更前后数据，并检查图片门槛以下的隐藏行；只验证全局总额不足以证明渠道归属正确。
- 对每个已配置渠道分别证明退前/退后线索、收款、退费、当期收款、到课和沟通指标的加法守恒；抖音 merge 字段只允许替换线索分母，不能替换财务事实。
- 生产写入必须保留“创建新记录 -> 完整回读 -> 删除旧记录 -> 最终回读”顺序，并核对期次、渠道数、字段数、行数和快照清单。
- 数据中心与群播报对账前，必须显式对齐期次、渠道筛选、年级/组织粒度和 `dt/hour`。低于图片最小退后线索门槛的财务行仍属于底层渠道总额，不得因未显示在图片中而判定为丢失。
- 手工 Tiangong2 执行只能用于受控验收；Windows `preflight-now` 必须继续只接受当前计划批次的已验证执行文件，不得用手工成功放宽定时门禁。

## 2026-09-28 四群静默与逐渠道隔离

### 故障原因

- 当日是业务期次切到 `20261002期` 后的第一个过程日。四个群没有推送，原因互不相同，其中只有一个是"当期确实没有合格数据"。
- **朱博士群**（`supervisor_zhu_doctor_video49`）：`20261002期` 的 `朱博士` 渠道在 Base 里只有 1 条线索（高三、退前 0、退后 0），低于 `minimum_post_leads=1`；顾问粒度聚合后没有任何可见行，命中"零合格行静默跳过"。任务退出码 0，既不建预览目录也不写台账，事后完全无声。上游 `stage_*_market2lark.log` 的渠道分布证明 `朱博士-视频号49` 合计 130 = 20260925期 129 + 20261002期 1，数据形态本身正常，不是上游断数。
- **KOC 与抖音私信群 / 商务 KOC 群**：`20261002期` 的 `KOC-周帅数学` 出现同一 `lead_id=334814970` 的两行（顾问账号不同，退前 0/0 与 1/0）。上游记录键含 `顾问账号`，而 Python 的 `validate_scope` 只按 `(期次, lead_id)` 判重，比受治理的记录键更严，于是抛"期次+lead_id重复，停止汇总"。同群其他渠道本身可发，但 `run_slot` 当时把整轮准备放在同一个 try 里，任一渠道异常就作废整轮并从头重试，导致 13:21/17:21/21:21 三次都跑满窗口后 `deadline_skipped`。
- **商务 KOC 群 / 自营 KOC 群的 17 点进量报告**：`20261002期` 线索表有 1001 行 `规则=未识别规则`，其中 998 行同时 `渠道=KOC-退款订单复用`、`年级=未识别年级`。`assignment_rule_channel` 要求 `规则` 按 `-` 切分至少 3 段且第 3 段非空，这些行不满足即抛错；`aggregate_abnormal` 在渠道/年级过滤之前按整期逐行调用它，因此一行坏行同时阻断该批次所有进量渠道。该兜底模式长期存在（20260925期已有 124 行），不是本期新发生。
- **自营 KOC 群 13 点**：常规报告的准备与发送都成功，但发送响应没有取到 `message_id`，按既有约定落为 `uncertain`。该消息可能已进群，需人工核对，不能按"未发送"直接补发。

### 修复与生产验收

- **逐渠道隔离**：`run_slot` 的逐渠道准备、快照复验、Base 版本一致性和投递四处改为按渠道独立 `try/except`。单渠道失败只记 `blocked_prepare` / `blocked_snapshot` / `blocked_revision` / `blocked_delivery` 并只重试该渠道，同群其他渠道照常生成与发送；退出码仍为 1，以便任务历史暴露异常。共享门禁保持全局：bot 身份、上游 release 钉、以及"同群各渠道必须同一 Base 版本"仍一次性校验，后者由 `rev_consensus` 保留多数版本、只隔离离群渠道。该行为与各渠道文档既有的"某个渠道没有当期数据或账号核验失败时停止该渠道"一致，此前代码并未实现。
- **重复线索口径（已评审）**：`workflow.merge_duplicate_lead_ids` 在 `validate_scope` 之前按 `(期次, lead_id)` 合并，保留 `退前线索`/`退后线索` 非零的那一行，并列时取先读到的一行；被丢弃行写入 `raw_read_audit.duplicate_lead_id_merged` 并随投递 detail 落台账。`validate_scope` 的唯一性断言保留在合并之后，因此仍然失败关闭。以 `20261002期` 真实数据复算：保留张宏胜（退前 1）、丢弃左颖雪（0/0），既不虚增也不丢真实线索，分年级报表数字不变。
- **不可解析规则口径（已评审）**：`aggregate_abnormal` 跳过不可解析行并按规则值计数，计数写入 `dimension_matching.unparseable_rule_rows`，经 `delivery_detail` 落台账。`assignment_rule_channel` 本身保持严格，评审策略只放在调用点。以 `20261002期` 真实全量复算：跳过 1001 行后两个进量渠道的维度全部匹配（商务 KOC 11/11、自营 KOC 7/7），四个进量渠道的数字与剔除坏行前一致。
- **可观测性**：`emit` 的事件流按运行追加到机器本地 `paths.push_log_root`（`D:\CodexLogs\data-push\<渠道>\<日期>\`），同时写 `<HHMMSS>-<任务>.result.json` 结论与 `_index/runs.jsonl` 汇总；`run_*.ps1` 另把进程 stdout/stderr 落 `-process.log`，覆盖 `emit` 之外的崩溃与 argparse 报错。日志写入失败只降级为告警，不阻断投递。零合格行跳过现在写入台账 `channel_events`（`skipped_no_eligible_rows`），不再无声。
- 离线验收：`tests` 304 项通过，3 项失败为既有的 Miaoda 部署与渠道导出问题，与本次改动无关；`validate_layout.py` 除同一条既有 Miaoda 报错外通过；9 个渠道 `--show-config` 与 9 个 `run_*.ps1` 语法校验通过；`runtime/channel-broadcast-push/investigation-20261002/verify-reviewed-narrowing.py` 在真实坏行上复现了两处故障并验证了两条评审口径。日志落盘以一次真实 `-Preflight` 运行端到端验证，未向任何群发送消息。

### 未确认送达的重发与只回读重验（2026-09-29 起）

`deliveries` 的 `key`（`delivery_key`）是**确定的**——只由 `chat_id|slot|channel|report_kind|bot`（配置了 `channel_key` 时再加前缀）决定，同槽位同渠道每一轮算出的键相同——而且它已经作为 `--idempotency-key` 传给飞书。因此判据收窄为一条（共享模块 `lark_delivery/common/resend.py` 的 `decide(status, message_id)`）：

> **有 message_id → 只补回读，绝不重发；没有 message_id → 用原键重发。**

`_deliver_verified` 原先是"任何 prior 行一律 `duplicate_suppressed` 并返回 `prior[0] == "sent_verified"`"，于是 `sending` / `uncertain` / `sent` / `sent_unverified` 全部永久挡死：一次令牌端点的传输重置就足以让该渠道烧完整个 `:20`–`:50` 窗口而从不重试。现在：

- `sent_verified` → 原样返回 `True`，仍记 `duplicate_suppressed`。
- **有 message_id**（`sent_unverified`，以及进程死在提交回执与回读之间的 `sent`）→ 走 `reverify_unverified_delivery`：它自带 `WHERE ... AND status=?` 乐观锁且**没有发送能力**，所以不可能把已在群内的消息补成两条。该函数此前已存在却无人调用；本次把它的资格判据从 `sent_unverified` 放宽到 `resend.DISPATCHED_STATUSES`，并接上调用点。持续回读失败记 `readback_failed`（不属于 `CLEAN_STATUSES`，交人工）。
- **没有 message_id**（`sending` / `uncertain`）→ 落到发送路径并记 `resending_after_uncertain`；**不重新 `claim`**——`claim` 是 `INSERT OR IGNORE`，行已存在会返回 `False` 从而又挡死自己，所以只在无 prior 行时 claim。
- `immediate.py`（`send-now` / `send-backfill` 一次性路径）的两处 prior 判断同样改为按判据分流：全部已结算才短路，其余落到逐渠道循环里重发或回读。
- 重发安全的依据同上：平台按同键去重并**返回原 message_id**，于是"响应丢失"这种真正模糊的情况也能收敛，而不是停在 `uncertain`。

### 防回归门禁

- 新增或修改渠道时，单渠道异常必须只影响该渠道：不得再把逐渠道准备放回同一个 try，也不得让已就绪渠道随整轮作废被丢弃。
- 上游记录键、Python 判重键和下游聚合粒度三者必须一致。当前上游键含 `顾问账号`，判重按 `(期次, lead_id)` 合并为一行；再改任一层都要同步本文与渠道文档，以及 `workflow.merge_duplicate_lead_ids`。
- 进量报告的坏行只允许"跳过并计数"，不允许静默丢弃；`unparseable_rule_count` 必须出现在投递回执里。
- 任何 `return True` 的跳过路径都必须留下 `channel_events` 行或运行日志；只存在于 stdout 的结论视为不可观测。
- 排查群静默时先读 `paths.push_log_root` 下的 `result.json` 与 `_index/runs.jsonl`，再用 `view_live_push_status.ps1` 汇总；不要依赖 `live-status.json`，它在每次运行结束时按设计删除。
- 收据/台账判据不得回到"非 `sent_verified` 一律不重发"。任何新增状态都必须先过 `resend.decide`；**记录里有 message_id 就绝不能重发**，没有才可以同键重发。靠错误类型判断（例如"取令牌失败就一定没发出去"）是错的——令牌可能被缓存，刷新失败时发送仍可能已经出门。
- **发送前探测的传输失败必须轮内重试。** `reporting.assert_current_revision` 是"此刻发送是否仍然安全"的一次读；它**返回**不同版本号才是结论（fail-closed、绝不重试），它**抛传输错误**只说明没能验证。该调用已包在 `common/retry.py` 的 `retry_transport` 里（3 次、间隔 2 秒），不要把它退回成"一次失败即整轮失败" —— 那会白丢一个 2 分钟槽位。新增任何"发送前的只读校验"都应同样包一层，并保持这个方向：**漂移是返回值，只重试异常**。
- **内容不可回读的群不得判为投递失败，也不得换新键重发。** 目标群开启保密模式时（`restricted_mode_setting.status=true` / `message_has_permission_setting="not_anyone"`）发送仍被允许但消息内容读不到，"message_id 取不到"成为结构性必然。这种群的回读失败记 `sent_unverifiable`（干净终态，见 `resend.UNVERIFIABLE`）；换新键会每轮补发一条。判定见 `lark_delivery/common/readback.py`，配置声明优先、探测失败一律判为可回读。

## @ 解析降级链与核验身份（2026-10-04，现行）

- 群成员核验身份统一为发送 bot 管家（`verification_identity="bot"`），与个人用户身份解耦；历史 `verification_identity="user"` 的 5 条渠道（陈瑞春、自孵化KOC5-9年级、亚飞9年级、亚飞9年级顾问、朱博士视频49）已改。2026-10-04 陈瑞春/自孵化/亚飞三渠道曾因个人身份被移出群而 blocked_prepare（232011 operator is not in the chat），当日已补发完成（陈瑞春 om_x100b6316c7a634a0c2ae3a54cfcdef0、自孵化 om_x100b6316fb3af0a0c39b05ea6ae5a85、亚飞 om_x100b6316fba35ca0dd8bb412a9d837a、亚飞顾问 ×2 om_x100b6316f7d39ca0c45b029cef41fde/om_x100b6316f2fae8a4c2b917969f7cda5，均 sent_verified）。
- @ 降级链与青橙一致：解析→bot 邀请入群并复核→纯名字兜底，人员问题不再阻断推送；`workflow.py` 中 strict_mentions 的阻断语义已移除，发送前 resolved 集合只保留在群成员（`build_markdown` 对无 open_id 者渲染纯名字）。
- 既存测试漂移备忘（与本改动无关，待业务确认后修）：`tests/core/test_channel_registry_export.py` 期望陈瑞春门槛值 1，而生产配置 minimum_post_leads=6。
