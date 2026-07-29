---
name: sync-qingcheng-temp-tables
description: 将飞书群“青橙数据对接”中郅玲玉发布的已登记 Excel 附件，以及李怡青发布的已登记“青橙行课开课时间”文档链接，同步到青橙及共享维护工作簿；完成整表校验后，再上传到各自已有的 USQL 临时表。也用于配置或运行受治理的本地 lark-event 服务：把“@管家”命令及已登记来源消息转化为计划、审批、本地应用和上传任务；还用于 lark-cli 的常态升级及升级后受治理的生产事件服务重启。适用于“上传最新开课时间表”“上传郅玲玉在青橙数据对接内发布的最新临时表到线上平台”、限定范围的预演对比、事件服务配置、lark-cli 升级/重启维护或工作流审计等请求。
---

# 同步青橙临时表

## 适用目标

将一条自然语言请求转化为受治理的“飞书 → 本地 → USQL”工作流，处理以下六类传入工作簿：

- 个人期度目标表
- 团队期度目标表
- 团队月度目标表
- 全员结果数据架构
- `****期带班架构`
- 青橙行课开课时间（李怡青发布的登记文档链接）

该工作流从精确配置的发布人处下载最新的已登记附件或文档链接，将单元格有效值与本地累计工作簿进行比较，在暂存副本中执行切片替换或追加并校验结果；只有经过确认后才写入已审核的本地副本，并且只有获得独立的生产确认后才上传完整的本地工作簿。

## 必须加载的 Skill 顺序

执行操作前，必须完整阅读并遵循以下 Skill：

1. 先用 `lark-shared`，再用 `lark-event` 进行持久事件消费，然后用 `lark-im`；必须同时阅读来源发现和受治理状态回复所需的消息 mget/search、资源下载及回复参考说明。
2. 当选中的文件族为 `course_schedule` 时，使用 `playwright` 完成已登记的非 USQL 文档登录与下载。
3. 使用 `xlsx` 检查工作簿、处理公式缓存、重新计算并执行质量检查。
4. 使用 `usql-web-query-operator` 校验手工表并执行生产上传。

进行历史映射或工作流维护时，还必须阅读 [historical_file_mapping.md](references/historical_file_mapping.md)、[course_schedule_source.md](references/course_schedule_source.md) 和 [workflow_registry.json](references/workflow_registry.json)。

不得使用青橙或市场 SQL 生成 Skill 重新解释这些工作簿结构。目标工作簿虽跨越两个业务域，但本工作流只执行注册表中明确定义的文件映射。

## 授权边界

各阶段必须视为彼此独立的授权边界：

1. 对 E 盘工作簿和平台而言，`plan` 是只读阶段。它可以搜索飞书、将附件下载到运行时存储、构建暂存副本、重新计算并校验。
2. `apply-local` 只有在提供精确且已审核的计划哈希及 `--confirm-local-write` 时，才可以更新指定的 E 盘工作簿。替换前必须创建带时间戳的备份，失败时必须回滚。
3. `upload` 只能覆盖选中的既有平台临时表，并且必须提供精确且成功的本地回执哈希及 `--confirm-production-upload`。

持久服务还设有独立的运行时门禁。`shadow` 只能创建计划；`send_replies` 只是机器人可见回复的总开关，绝不授予工作簿或平台写权限。默认回复策略只响应已知的 `@管家` 命令，忽略未知命令和自动来源消息的回复，并只发送最终结果，不发送过程噪声。在 `production` 模式下，只有同时启用 `allow_local_apply` 与 `allow_production_upload`，审批人命令才可能触发写入。识别到的来源附件或链接始终只能生成计划。公开回复不得包含本地路径、制品哈希、回执路径、凭据或原始异常；回复发送失败也绝不能改变底层任务状态。

如果请求仅要求分析、解释、审计或设计工作流，则必须在 `plan` 后停止。明确请求“上传郅玲玉在青橙数据对接内发布的最新临时表到线上平台”或“上传最新开课时间表”时，才授权所选范围的端到端操作；即便如此，也必须依次执行并验证全部三个阶段，不得绕过哈希、漂移检查、备份或回执。

## 来源选择

必须使用注册表中的稳定 ID 解析群聊和发布人，不能只依赖显示名称。附件文件族只接受郅玲玉发布且符合登记模式的文件。`course_schedule` 只接受李怡青发布的已登记 `docs.baijia.com` HTTPS URL，并且文档标题标记必须精确匹配登记值。每个选中文件族都应选择最新的匹配消息。

处理 `course_schedule` 时，如果已设置 `QINGCHENG_DOCS_ENV_FILE`，则从该文件完成认证；否则使用注册表登记的本地环境文件。不得打印、复制或持久化其中的凭据值。必须使用临时浏览器上下文，校验最终 URL 和文档标题，将下载的 XLSX 保存到运行时目录，并在读取前完成校验。当前活动工作表是唯一的来源期次。

不得将以下历史文件或中间文件视为当前输入：

- `qi*daibanguocheng.xlsx`
- `qing_team_moth_jg.xlsx`
- `task_*.xlsx`
- `CRM线索数据*.xlsx`

如果任何选中文件族缺失、存在歧义、格式异常或含有重复业务键，必须阻断计划。不得静默复用较旧的本地切片。计划可以用 `--family` 选择子集，用 `--after` 限定消息范围，或用 `--message-id <family>=<om_id>` 将文件族绑定到精确消息。即使采用精确绑定，也仍须通过已配置的群聊、发布人、文件名、结构和工作簿校验。

每个文件族还必须通过 `workflow_registry.json` 中的 `source_quality` 门禁：

- 来源消息年龄不得超过该文件族的 `max_age_hours`；
- 来源总行数必须落在 `row_count.min/max` 范围内；
- 每个来源切片优先与目标同切片比较；新切片与目标最新切片比较，变化率不得超过 `relative_change.max_ratio`；
- `required_column_null_rate` 中每个必要列的空值率不得超过各自阈值；
- 缺少比较基线、门禁配置缺失、门禁过期或任一检查超限都必须使计划进入 `blocked`，不得本地 Apply 或上传。

阈值是受版本控制的安全策略。确认属于正常业务结构变化时，应先审阅并修改注册表、补充测试，再重新生成计划；不得用命令行参数临时绕过。

## 合并规则

绝不能盲目追加行。

- 只规范化注册表中明确配置的列别名和常量。
- 比较公式缓存的有效值，而不是公式字符串，避免无意义地重写含外部链接公式的工作簿。
- 对来源中的每个 `qici` 或 `month`，先删除对应目标切片，再插入当前来源切片。
- 重建 `result_architecture` 暂存候选时，必须逐字节保留目标工作簿的 `xl/externalLinks/**` 包；在 Excel COM 打开前校验所有工作簿级和外部链接 `r:id`，重新计算后再次校验这些关系。
- 对于 `course_schedule`，将已登记的中文表头映射到 `qing_daoke.xlsx`；只忽略多出的来源列 `工作日`，折叠 `begin_time` 中的重复空白，将 `ke_1` 保存为文本，并物化有效值，确保外部链接公式不会被复制到维护工作簿。
- 保留来源中未出现的所有目标切片。
- 对于 `jiagou_db.xlsx`，只替换 `dept_1 = 青橙项目部` 且 `qici` 重叠的行。必须保留所有市场顾问部行，包括同一期次的行。
- 合并后强制校验已配置的业务键。
- 保持已配置的排序方向和目标列顺序。

有效值比较结果不变时，应视为有效的本地无操作（no-op）。不得仅因公式或工作簿元数据不同就重建工作簿。生产上传仍须有明确的上传请求和成功的本地回执。

## 运行工作流

使用指定的 Python 运行时：

```powershell
D:\anaconda3\python.exe C:\Users\Ludim\.codex\skills\sync-qingcheng-temp-tables\scripts\qingcheng_temp_table_sync.py plan
```

审核 `sync_plan.json`，尤其要检查：

- 每条选中飞书消息的 ID 和来源哈希；
- 来源切片、行数、键唯一性和校验结果；
- 来源年龄、行数上下界、逐切片相对变化和必要列空值率；
- 每张表的新增、替换、移除和未变化数量；
- 暂存工作簿哈希及所有阻断项；
- 每张选中表是否均为 no-op。

如需限定计划范围，可重复传入 `--family`；例如选择三张目标表：

```powershell
D:\anaconda3\python.exe C:\Users\Ludim\.codex\skills\sync-qingcheng-temp-tables\scripts\qingcheng_temp_table_sync.py plan `
  --family personal_period_goal `
  --family team_period_goal `
  --family team_month_goal
```

使用 `--after '2026-07-21T22:00:00+08:00'` 设置严格的时间下界，或使用 `--message-id period_architecture=om_xxx` 绑定回复所指向的来源消息。绑定精确的李怡青链接时，使用 `--family course_schedule --message-id course_schedule=om_xxx`。省略全部选择参数时，将处理六个已登记文件族。

使用输出的精确值应用已审核的本地计划：

```powershell
D:\anaconda3\python.exe C:\Users\Ludim\.codex\skills\sync-qingcheng-temp-tables\scripts\qingcheng_temp_table_sync.py apply-local `
  --plan <absolute-sync-plan-path> `
  --expected-plan-sha256 <exact-plan-sha256> `
  --confirm-local-write
```

审核 `local_apply_receipt.json`、备份、最终本地哈希和写入后校验结果，然后上传完整的本地工作簿：

```powershell
D:\anaconda3\python.exe C:\Users\Ludim\.codex\skills\sync-qingcheng-temp-tables\scripts\qingcheng_temp_table_sync.py upload `
  --local-receipt <absolute-local-receipt-path> `
  --expected-receipt-sha256 <exact-receipt-sha256> `
  --confirm-production-upload
```

上传阶段必须重新检查计划的选择契约（`latest_matching` 或 `explicit_message`），确认所有本地哈希仍与回执一致，使用 operator 校验每个工作簿，并按注册表顺序通过既有表覆盖工作流上传选中的文件族。

上传前还必须重新检查计划中的 `source_expires_at`。只要任一来源在 Apply 或 Upload 前已经超过最大年龄，就必须停止并创建新计划；旧计划 Hash 不能豁免新鲜度门禁。

## 持久 lark-event 服务

在启动服务、启用回复、安装登录启动项或切换到生产模式前，必须阅读并遵循 [event_service.md](references/event_service.md)。纳入版本控制的配置模板为 [event_service_config.example.json](references/event_service_config.example.json)；实时配置和全部服务状态只能存放在运行时目录中，绝不能放在 Skill 目录中。

该服务必须：

- 保持 `lark-event` 子进程的 stdin 打开，等待其 `[event] ready` 标记，并通过关闭 stdin 实现优雅停止；
- 在认领事件前精确过滤目标群，并使用 `message_id` 作为幂等键；
- 除白名单来源附件和已登记来源链接外，文本命令必须提及机器人；
- 基于稳定 open ID 和确定性命令做角色判定，绝不能根据 LLM 生成的权限判断作出决定；
- 通过单一工作进程串行处理工作簿任务，并将任务及出站状态持久化到 SQLite；
- 即使在生产模式下，自动来源消息也始终只能触发计划；
- 只有收到审批人明确的 `上传...` 或 `确认上传 <job_id>` 命令，且全部配置门禁均通过后，才允许执行生产操作；
- 绝不能强制终止事件消费者，也不能静默重试被中断的生产任务。

### lark-cli 强制升级门禁

每次可能影响本工作流的 `lark-cli` 升级，都必须阅读并执行 [event_service.md](references/event_service.md#14-lark-cli-常态升级与生产服务重启固定八步) 中固定的八步操作手册。不得跳过或调整门禁顺序。最终步骤之前发生任何失败，都必须阻止恢复生产监听器。

“重启生产”只表示：完成兼容性校验后，精确恢复升级前已审核的服务配置。它绝不表示可以静默切换 `mode`、启用 `allow_local_apply` 或 `allow_production_upload`、扩大身份/权限范围，或授予新的工作簿/平台写权限。

## 失败处理

- 如果计划存在阻断项或任何暂存校验结果退化，必须在本地写入前停止。
- 仅当候选版本没有新增或加重问题时，才允许保留共享 `jiagou_db.xlsx` 中的基线校验问题。不得在本工作流中修复无关的市场顾问部数据。
- 在 Windows 上，本地 Apply 必须先把每个暂存工作簿复制到唯一的同级文件，再针对临时共享/权限故障重试原子替换。若替换仍失败，必须保留候选文件和备份证据，写出 `local_apply_failure_receipt.json`，验证每个目标仍处于计划前哈希，并报告结构化失败，不能只返回非 JSON traceback。
- 如果已经替换任一工作簿后本地替换失败，只能原子回滚本轮已替换的工作簿；必须逐一验证所有选中目标均恢复至计划前哈希。除非回滚得到完整验证，否则必须阻断上传。
- 如果上传失败，必须立即停止。记录已成功上传的文件族、失败文件族，并将失败文件族及其后续文件族标记为待处理。绝不能把部分上传报告为成功。
- 执行期间不得删除下载文件、暂存文件、计划、备份或回执。

## 完成报告

报告必须包含：

- 选中的来源文件、消息时间和消息 ID；
- 来源 → 本地 → 平台的映射关系；
- 切片级差异以及各文件族是否发生变化；
- 发生写入时的本地备份路径和回执路径；
- 每个文件族的平台上传状态及最终回执；
- 所有排除文件、既有基线警告、阻断项或部分失败。

如果所有选中文件族均已对齐且未执行生产上传，必须明确说明。
