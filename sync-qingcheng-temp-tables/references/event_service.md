# 青橙 lark-event 本机常驻服务

## 目录

- [1. 目标与边界](#1-目标与边界)
- [2. 已实现组件](#2-已实现组件)
- [3. 身份与权限模型](#3-身份与权限模型)
- [4. 两种模式与回复策略](#4-两种模式与回复策略)
- [5. 飞书前置条件](#5-飞书前置条件)
- [6. 首次配置](#6-首次配置)
- [7. 启动、状态、日志与停止](#7-启动状态日志与停止)
- [8. 登录自启](#8-登录自启)
- [9. 群内使用方法](#9-群内使用方法)
- [10. 郅玲玉发布附件时的行为](#10-郅玲玉发布附件时的行为)
- [11. 任务状态](#11-任务状态)
- [12. 范围化 CLI](#12-范围化-cli)
- [13. 上线顺序](#13-上线顺序)
- [14. lark-cli 常态升级与生产服务重启（固定八步）](#14-lark-cli-常态升级与生产服务重启固定八步)

## 1. 目标与边界

本服务把 `青橙数据对接` 群消息转换为受控的青橙临时表任务。它只处理配置中的固定群、固定来源人、固定五类 Excel 和固定本地/平台映射，不执行任意 shell、任意 SQL 或自由生成的写操作。

完整链路为：

1. `lark-cli event consume im.message.receive_v1 --as bot` 接收消息。
2. 按 `chat_id` 过滤，用 `message_id` 去重。
3. 将文本指令解析为固定意图，或把郅玲玉发布的可识别 Excel 放入附件批次。
4. 生成带 Hash 的 `QingchengTempTableSyncPlan`。
5. 只有配置中的审批人发出明确上传指令，且生产三道开关同时启用时，才执行本地 Apply 和平台 Upload。
6. 每个阶段写入 SQLite 账本、计划和回执；失败立即停止，不跳过 Hash、漂移、备份或校验门禁。

自动识别郅玲玉的附件只会生成计划，永远不会因为“看到附件”自动修改本地文件或上传平台。

## 2. 已实现组件

| 组件 | 路径 | 用途 |
|---|---|---|
| 范围化同步 CLI | `scripts/qingcheng_temp_table_sync.py` | 支持整批、指定文件族、时间下限、精确消息绑定，以及 Plan → Local Apply → Upload |
| 事件服务 | `scripts/qingcheng_event_service.py` | 常驻消费、权限路由、附件批处理、单线程任务执行、账本与状态 |
| Windows 管理器 | `scripts/manage_event_service.ps1` | 隐藏窗口启动、优雅停止、状态、日志、登录自启安装/卸载 |
| 配置模板 | `references/event_service_config.example.json` | 不含凭据的安全 `shadow` 模板 |
| 运行配置 | `C:\Users\Ludim\.codex\runtime\sync-qingcheng-temp-tables\event-service\config.json` | 本机实际配置，不进入技能 Git 目录 |
| 任务账本 | `...\event-service\jobs.sqlite3` | 事件去重、任务状态、附件批次、待发/已发回复 |
| 服务状态 | `...\event-service\status.json` | PID、模式、心跳、生产门禁、账本摘要 |
| 服务日志 | `...\event-service\service.log` | 轮转日志；单文件上限 5 MiB，保留 5 份 |

## 3. 身份与权限模型

| 身份 | 可以做什么 | 不可以做什么 |
|---|---|---|
| 郅玲玉（来源人） | 发布已登记 Excel；服务静默合批并生成预检计划 | 仅凭附件触发本地写入或生产上传 |
| 普通群成员 | `帮助`、`状态`、`预检...` | 本地 Apply、生产上传、确认他人的生产任务 |
| 配置中的审批人 | 普通成员能力；`确认上传 <job_id>`；`上传最新...` | 绕过配置开关、Hash、漂移、备份、校验或既有表映射 |
| 管家机器人 | 监听、读取回复上下文、按配置回复 | 以用户身份发消息、处理其他群、执行任意自然语言代码 |

当前登记的稳定 ID：

- 群：`oc_e604e064976c022ab4289fc2fb979332`
- 来源人郅玲玉：`ou_bf111effd2d71a52ee40c58c7cb4d105`
- 审批人吕帅：`ou_adde1ef52a52e60a272fb4b8a416eb01`
- 管家机器人：`ou_f3907e865135732c15a1dfce27828411`

服务以 bot 身份接收事件、读取精确消息、下载群附件和回复。最新历史文件检索优先复用已登录的 user 身份；user 不可用时，对固定 `chat_id` 回退为 bot 分页读取。附件下载本身使用 bot 身份。

## 4. 两种模式与回复策略

安全初始配置：

```json
{
  "mode": "shadow",
  "send_replies": false,
  "reply_on_commands": true,
  "reply_on_unknown_commands": false,
  "reply_on_source_attachments": false,
  "reply_progress_updates": false,
  "allow_local_apply": false,
  "allow_production_upload": false
}
```

含义：

- `mode=shadow`：所有上传指令都降级为预检计划。
- `send_replies=false`：回复内容只写入 `outbound_messages` 账本，不发送到群；它是回复总开关，不授予任何数据写入权限。
- `reply_on_commands=true`：总开关启用后，只响应已识别的显式 `@管家` 指令。
- `reply_on_unknown_commands=false`：随意 `@管家` 的未知自然语言默认静默，避免帮助消息刷屏。
- `reply_on_source_attachments=false`：郅玲玉发布登记附件时默认静默预检，不自动在群里回执。
- `reply_progress_updates=false`：默认不发“已受理/开始处理”等过程消息，只发最终结果；帮助、状态和拒绝说明不属于过程消息。
- `allow_local_apply=false`：事件服务不能改 E 盘维护表。
- `allow_production_upload=false`：事件服务不能调用平台上传。

需要启用生产写入时，推荐使用以下最小群回复配置，并显式打开两道写入开关：

```json
{
  "mode": "production",
  "send_replies": true,
  "reply_on_commands": true,
  "reply_on_unknown_commands": false,
  "reply_on_source_attachments": false,
  "reply_progress_updates": false,
  "allow_local_apply": true,
  "allow_production_upload": true
}
```

启用 `send_replies=true` 表示允许服务按上述子策略，以 bot 身份向任务原消息发送状态回复。回复策略和生产写入门禁完全独立；启用生产写入后，仍只有 `approver_ids` 中的用户发送明确上传指令才会触发写入，普通成员和来源附件仍只能生成计划。

群内回复只包含任务编号、范围、公开状态和安全错误编号。绝不发送本机路径、Plan/Receipt Hash、回执路径或原始异常；完整证据只保存在本机账本、计划、回执和日志中。飞书回复失败只记录为 `outbound_messages.delivery_status=failed`，不得把已经成功或已生成计划的业务任务改成 `failed`。

## 5. 飞书前置条件

1. 管家应用已加入 `青橙数据对接` 群。
2. 飞书开发者后台已订阅 `im.message.receive_v1`。
3. bot 已具备 `lark-cli event schema im.message.receive_v1 --json` 当前返回的事件 scope。
4. 读取消息/附件需要 `im:message:readonly`；bot 回复需要 `im:message:send_as_bot`。
5. `lark-cli auth status --json --verify` 中 bot 必须为 `ready/verified`。user 身份建议保持可刷新，以便高效检索历史附件；user 失效不会改变生产权限边界。

检查命令：

```powershell
$env:LARKSUITE_CLI_NO_UPDATE_NOTIFIER = '1'
$env:LARKSUITE_CLI_NO_SKILLS_NOTIFIER = '1'
lark-cli auth status --json --verify
lark-cli event schema im.message.receive_v1 --json
```

bot 缺 scope 时应在开发者后台补最小权限，不能用 `auth login` 修复 bot 权限。

## 6. 首次配置

本机已存在安全模板时，可生成运行配置：

```powershell
D:\anaconda3\python.exe `
  C:\Users\Ludim\.codex\skills\sync-qingcheng-temp-tables\scripts\qingcheng_event_service.py `
  init-config `
  --output C:\Users\Ludim\.codex\runtime\sync-qingcheng-temp-tables\event-service\config.json
```

如果目标已存在，命令会拒绝覆盖。只有明确要替换已审阅配置时才加 `--force`。

验证配置但不启动监听：

```powershell
D:\anaconda3\python.exe `
  C:\Users\Ludim\.codex\skills\sync-qingcheng-temp-tables\scripts\qingcheng_event_service.py `
  validate-config `
  --config C:\Users\Ludim\.codex\runtime\sync-qingcheng-temp-tables\event-service\config.json
```

验证器会阻止以下危险组合：

- `shadow` 却启用任一本地/生产写开关；
- 启用生产上传却未启用本地 Apply；
- 非 bot 回复身份；
- 群 ID、审批人、来源人、脚本或 Registry 缺失；
- 关键超时不是正整数。

## 7. 启动、状态、日志与停止

管理器路径：

```powershell
$manager = 'C:\Users\Ludim\.codex\skills\sync-qingcheng-temp-tables\scripts\manage_event_service.ps1'
```

隐藏窗口后台启动：

```powershell
& $manager -Action start
```

查看状态与最近 10 个任务：

```powershell
& $manager -Action status
```

查看最近 200 行服务日志：

```powershell
& $manager -Action logs
```

优雅停止：

```powershell
& $manager -Action stop
```

停止通过 `stop.request` 通知父进程，再由父进程关闭 `lark-event` 的 stdin。管理器不会 `kill -9`；如果正在执行任务，状态会保持 `stopping`，等待当前任务安全结束。

重启：

```powershell
& $manager -Action restart
```

## 8. 登录自启

安装当前用户登录触发的计划任务：

```powershell
& $manager -Action install-startup
```

默认任务名为 `Codex-Qingcheng-LarkEvent`。安装后仍建议手动执行一次 `start` 和 `status`，确认 `status=running`、`event_ready=true`。

卸载登录自启不会删除配置、账本、日志或任务制品：

```powershell
& $manager -Action uninstall-startup
```

## 9. 群内使用方法

除郅玲玉的登记附件自动预检外，文本指令默认必须 `@管家`。

默认回复策略只响应下列已识别指令并只发送最终结果。未知文本默认不回复；若需要提示，可显式设置 `reply_on_unknown_commands=true`。自动附件预检默认不回复；若需要最终回执，可设置 `reply_on_source_attachments=true`。只有同时设置 `reply_progress_updates=true` 才会增加“已受理/开始处理”过程消息。

### 普通成员

```text
@管家 帮助
@管家 预检最新临时表
@管家 预检最新目标表
@管家 预检 个人期度 团队期度 团队月度
@管家 预检 全员结果数据架构
@管家 预检 带班架构
@管家 状态
@管家 状态 qc_20260721123456_ab12cd34
@管家 取消 qc_20260721123456_ab12cd34
```

回复郅玲玉发布的一条已登记 Excel 消息后发送：

```text
@管家 预检此文件
```

服务会用 `im +messages-mget` 回读回复对象，核对群、来源人和文件名，再把该 family 绑定到精确 `message_id`。后续出现同名新文件不会把这项任务悄悄漂移到新消息。

### 审批人

推荐两步方式：

```text
@管家 预检最新目标表
@管家 确认上传 qc_20260721123456_ab12cd34
```

明确希望一次执行到底时：

```text
@管家 上传最新临时表
@管家 上传最新目标表
```

回复单个源附件：

```text
@管家 上传此文件
```

在 `shadow` 模式或生产开关未全部开启时，上传指令只生成计划并明确记录为降级，不会写入本地或平台。

## 10. 郅玲玉发布附件时的行为

1. 只接受固定群、固定来源 open_id、`message_type=file`。
2. 用 Registry 文件名正则识别五类输入；其他文件忽略。
3. 等待 `attachment_quiet_seconds` 的静默窗口，把连续发布的多张表合成一项任务。
4. 同一文件族在一个批次出现多次时，绑定该批次中最新 `message_id`。
5. 生成 `plan` 任务并等待审批；不自动 Apply、不自动 Upload，默认也不向群里回复。

这样能支持“22:00 后连续发布三个目标表”的场景，又避免每收到一张表就重复跑整套流程。

## 11. 任务状态

| 状态 | 含义 |
|---|---|
| `queued` | 已受理，等待单工作线程 |
| `planning` | 正在下载、比较、构造 staged workbook 和 Plan |
| `planned` | 计划通过，等待审批人确认 |
| `applying_local` | 正在备份并替换 E 盘维护表 |
| `uploading` | 正在覆盖已登记平台临时表 |
| `success` | 本地和平台阶段均成功 |
| `failed` | 任一阶段失败，已停止后续步骤 |
| `cancelled` | 在 `queued/planned` 阶段被允许的用户取消 |

突然断电或进程崩溃后：

- 未开始的 `queued` 任务会在下次启动时恢复排队；
- 当时处于 `planning/applying_local/uploading` 的任务标记为 `failed/interrupted`，不会盲目重跑；
- 必须检查计划、备份、Local Receipt、Upload Receipt 和平台导入历史后再重新发起。

## 12. 范围化 CLI

事件服务调用的是同一个可人工审阅的 CLI。示例：

三个目标表：

```powershell
D:\anaconda3\python.exe `
  C:\Users\Ludim\.codex\skills\sync-qingcheng-temp-tables\scripts\qingcheng_temp_table_sync.py plan `
  --family personal_period_goal `
  --family team_period_goal `
  --family team_month_goal
```

只看某时间之后：

```powershell
...\qingcheng_temp_table_sync.py plan `
  --family personal_period_goal `
  --after '2026-07-21T22:00:00+08:00'
```

精确绑定一条消息：

```powershell
...\qingcheng_temp_table_sync.py plan `
  --family period_architecture `
  --message-id period_architecture=om_xxx
```

不带 `--family` 时保持旧行为，处理 Registry 中全部五类文件。Local Apply 和 Upload 会复用 Plan 中的选择条件：`latest_matching` 会阻断后来出现的同族新文件；`explicit_message` 则始终绑定原消息。

## 13. 上线顺序

推荐按以下顺序推进：

1. 保持 `shadow + send_replies=false`，运行至少一个真实附件批次，只核对账本、计划、下载和 staged workbook。
2. 仍保持 `shadow`，经明确同意后仅开启 `send_replies=true`，保持未知指令、自动附件和过程消息关闭，验证群内帮助、状态、预检完成和安全失败回复。
3. 审阅角色 ID、五类映射、备份与上传回执后，切换 `production` 并同时开启两个写开关。
4. 先用“预检 → 确认上传”两步指令做一轮；确认平台导入历史后再使用“一步上传”。
5. 最后安装登录自启。

任何阶段都不要通过关闭 Hash、漂移、校验或回执检查来“修复”失败。

## 14. lark-cli 常态升级与生产服务重启（固定八步）

每次 `lark-cli` 升级都必须依次执行以下八步。任一步失败都阻断后续生产恢复，不得跳步、调序或用一次历史成功替代当前版本验证。

这里的“生产服务”指实际承载群事件的常驻监听实例。“恢复生产”只恢复升级前已审阅的原配置和权限，不自动把 `shadow` 改为 `production`，不自动开启 `allow_local_apply` / `allow_production_upload`，也不授予新的本地或平台写入权限。

### 1. 冻结生产并建立安全验证副本

- 读取管理器状态和 SQLite 账本；存在 `planning`、`applying_local` 或 `uploading` 任务时，等待其安全结束或完成人工核验，不得直接升级。
- 记录实时配置的 SHA-256，以及 `mode`、全部回复开关、`allow_local_apply`、`allow_production_upload`、群和角色 ID；把配置逐字节备份到本次升级的 runtime 维护目录。
- 从备份创建独立验证配置和独立 `runtime_root`，强制使用 `mode=shadow`、`allow_local_apply=false`、`allow_production_upload=false`。不要覆盖实时生产配置。

### 2. 固化升级前版本、路径与回滚证据

- 记录 `Get-Command lark-cli -All`、本地和全局命令的绝对路径与 `--version` 输出，并记录青橙脚本 `resolve_lark_cli()` 实际解析的路径。
- 执行 `lark-cli update --check --json`，保存当前版本、目标版本和 `skills_status`，但不要把 `_notice` 当作升级完成证据。
- 逐字节备份 `package.json`、`package-lock.json`、相关 CLI 包元数据及本次将变化的 Skill 文件，并记录 SHA-256。禁止把凭据、token 或浏览器状态写入维护制品。

### 3. 优雅停止生产事件服务

- 使用 `manage_event_service.ps1 -Action stop`，让父进程关闭 `lark-event` 子进程的 stdin；禁止强杀、`kill -9` 或无条件 `event stop --force`。
- 确认服务不再运行、该事件键无遗留活动消费者，并保留停止日志。停止失败或出现孤儿消费者时先排查，不得边运行边替换 CLI。

### 4. 统一升级 CLI 与官方 Skills

- 按 `lark-shared` 要求，对明确的目标安装使用官方 `lark-cli update`；本机同时保留本地和全局安装时，把两者升级到同一精确版本，禁止只更新未限定路径的一个命令。
- 让本地 `package.json`、锁文件、已安装包和真实命令版本保持一致；任何一处仍指向旧版本都视为版本漂移。
- 核验 `skills_status.in_sync=true`，并把本地 `skills\lark-*` 与对应上游版本的完整文件树比较。同步官方文件时保留本地 `agents/openai.yaml` 注册信息；不得借升级修改青橙业务映射、运行配置或生产权限。

### 5. 执行离线兼容性与 Windows 回归

- 对青橙事件服务和同步脚本执行 `py_compile`，再运行 `D:\anaconda3\python.exe -m unittest discover -s tests -p 'test_*.py' -v`；任何失败都阻断启动。
- 必须覆盖 Windows `.cmd` 多行 JSON 回复、换行转义、`--as bot`、幂等键位于 `--content` 前、50 字符幂等键上限，以及 `{ok,data,error}` JSON 信封解析。
- 通过 `--help`、`event schema im.message.receive_v1 --json` 和无写入 dry-run 核验 `im +messages-mget`、`im +messages-reply`、`--content`、`--msg-type`、`--idempotency-key`、事件 NDJSON 与 `[event] ready` 契约。发现 CLI 漂移时先修复脚本和测试，不得直接上线。

### 6. 仅用 shadow 验证配置启动新版本

- 使用验证配置启动服务，确认实际解析的 CLI 路径和版本正是本次目标版本；不得先用实时生产配置试启动。
- 核验 `status=running`、`event_ready=true`、目标事件键只有一个活动消费者、`dropped=0`，并检查 bot 身份、最小 scope 和最近日志无启动错误。
- 再次确认验证实例的本地 Apply 和生产 Upload 门禁均为 `false`，且升级过程未创建业务写入回执。

### 7. 执行一次受控群回复与幂等回读

- 使用预先指定的维护测试消息；发送前明确记录目标消息、三行测试正文、`bot` 身份和本次唯一幂等键。不得向未确认的消息或群发送测试内容。
- 通过当前 `LarkGateway.reply()` 路径用同一幂等键调用两次，要求两次返回同一个消息 ID 且群内只出现一条回复。
- 使用 `im +messages-mget --as bot` 回读，核对发送者为“管家”应用、三行正文完整、`reply_to` 正确；同时确认没有递归任务、没有新增 Apply/Upload 回执、写入门禁仍关闭。

### 8. 恢复原配置并重启生产服务

- 先优雅停止 shadow 验证实例，再重新读取实时配置并与第 1 步记录的 SHA-256 比较；配置漂移时阻断恢复，禁止自动合并或扩大权限。
- 使用逐字节一致的升级前实时配置启动服务。启动后回读 `mode`、所有回复开关和两道写入门禁，要求与升级前完全一致；升级流程本身不得改变这些值。
- 最终核验 `status=running`、`event_ready=true`、单一活动消费者、`dropped=0`、精确 CLI 路径/版本及无错误启动日志，并保存升级回执。任何核验失败都保持生产停止或退回 shadow，不得宣称升级完成。
