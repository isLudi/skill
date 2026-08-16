# 飞书多群临时表事件服务

`governed_temp_table_event_service.py` 是统一 Skill 的事件入口。它监听一个飞书应用机器人，但按注册表把两个精确群隔离成两个领域适配器。

## 路由和隔离

| 群 | 可识别文件族 |
|---|---|
| 青橙数据对接 | 6 个 `qingcheng` 文件族 |
| 市场顾问部临时表上传 | 6 个 `market_consultant` 文件族 |

服务同时要求：

- `chat_id` 属于配置的 `chat_ids`，并与文件族注册的群完全一致；
- 来源人 open_id 与文件族一致；
- 文件名或登记链接与注册规则一致；
- 同一命令只能选择当前群的文件族；
- 任务、状态查询、取消和审批按创建任务的群隔离；
- 机器人/应用自己发送的消息不再触发任务。

历史私聊不在监听范围。相同文件名从错误群或错误来源人发出时，不进入待处理队列。

## 运行模式

### shadow

安全默认值：

- 自动识别附件后只生成 Plan；
- 上传指令降级为 Plan；
- `allow_local_apply=false`；
- `allow_production_upload=false`；
- 推荐初次联调时 `send_replies=false`。

### production

只有全部条件同时满足才可能写入：

- `mode=production`；
- `allow_local_apply=true`；
- `allow_production_upload=true`；
- 指令发起人或确认人位于 `approver_ids`；
- Plan、来源质量、来源消息、目标工作簿和来源切片基线均未漂移。

生产命令仍按 `plan → apply-local → upload` 顺序执行。服务配置只是开启门禁，不替代每个任务的哈希和审批检查。

## 固定指令

在任一登记群中：

- `@管家 帮助`
- `@管家 预检最新临时表`
- `@管家 预检 <表名或别名>`
- 回复一个已登记源附件/链接：`@管家 预检此表`
- `@管家 状态 [job_id]`
- `@管家 取消 <job_id>`

仅审批人：

- `@管家 上传最新临时表`
- `@管家 确认上传 <job_id>`

群内来源人连续发送附件时，服务等待 `attachment_quiet_seconds`，按同一群分别成批；每个文件族只取本批最新消息并绑定精确 message_id。

## 配置

运行时配置位于：

`C:\Users\Ludim\.codex\runtime\sync-qingcheng-market-temp-tables\event-service\config.json`

Skill 中只保存安全示例：

`references/event_service_config.example.json`

初始化：

```powershell
D:\anaconda3\python.exe C:\Users\Ludim\.codex\skills\sync-qingcheng-market-temp-tables\scripts\governed_temp_table_event_service.py init-config `
  --output C:\Users\Ludim\.codex\runtime\sync-qingcheng-market-temp-tables\event-service\config.json
```

必要字段：

- 两个精确 `chat_ids`；
- 郅玲玉、李怡青、张君言的 `source_sender_ids`；
- 吕帅等被明确授权人的 `approver_ids`；
- 管家机器人的 `bot_open_id` 和 `bot_names`；
- Python、同步脚本、注册表和两个 runtime 根路径。

配置不得包含飞书密钥或 USQL 凭据。身份、授权和缺失 scope 由 `lark-shared` 处理；USQL 凭据仍只通过 operator 的 env file。

## 配置验证和离线事件测试

验证不启动服务：

```powershell
D:\anaconda3\python.exe C:\Users\Ludim\.codex\skills\sync-qingcheng-market-temp-tables\scripts\governed_temp_table_event_service.py validate-config `
  --config C:\Users\Ludim\.codex\runtime\sync-qingcheng-market-temp-tables\event-service\config.json
```

离线处理一个已保存事件时会强制 shadow、禁回复、禁本地写入和禁上传：

```powershell
D:\anaconda3\python.exe C:\Users\Ludim\.codex\skills\sync-qingcheng-market-temp-tables\scripts\governed_temp_table_event_service.py process-event `
  --config <config.json> `
  --event-file <event.json>
```

必须分别覆盖：

1. 青橙合法附件进入青橙文件族；
2. 市场合法附件进入市场文件族；
3. 同名文件发到错误群被拒绝；
4. 两群附件不会合并成同一批；
5. 一群无法查询、取消或审批另一群任务；
6. shadow 上传命令只生成 Plan；
7. 非审批人不能发起或确认生产上传。

## 安全停启

管理脚本：

```powershell
$manager = 'C:\Users\Ludim\.codex\skills\sync-qingcheng-market-temp-tables\scripts\manage_event_service.ps1'
& $manager -Action status
& $manager -Action logs
& $manager -Action stop
& $manager -Action start
```

`stop` 只写停止请求并等待当前任务结束，不强杀进程。`start` 会先验证配置并等待运行状态。

统一启动任务名：

`Codex-Governed-TempTables-LarkEvent`

安装或删除登录启动任务属于外部状态变更，必须有明确授权：

```powershell
& $manager -Action install-startup
& $manager -Action uninstall-startup
```

从旧 Skill 迁移时，旧任务 `Codex-Qingcheng-LarkEvent` 不得与新任务并存；先确认旧服务已停止，再删除旧启动任务。不要在验证完成前安装或启动新任务。

## 账本和回执

runtime 中保存：

- `status.json`：服务状态和 PID；
- `jobs.sqlite3`：事件幂等键、群隔离任务、待批附件、出站消息审计；
- `service.log`：详细错误；
- 同步脚本生成的 Plan、staged 工作簿和回执。

群回复只显示任务 ID、阶段、范围和公开错误编号 `TT-XXXXXXXXXX`。本地路径、哈希和原始错误不发到群里。

## 启用前门禁

必须全部通过：

1. 同步脚本和事件服务 `py_compile`；
2. Skill 全部单测；
3. 市场六表离线回放；
4. 两群 shadow 离线事件回放；
5. 注册表、示例配置、运行配置的群/来源覆盖验证；
6. UTF-8、乱码、`git diff --check` 和仓库级验证；
7. 用户明确同意重新启用。

任何一项失败都保持服务停用。

## lark-cli 常态升级与生产重启（固定八步）

每次 `lark-cli` 升级都必须依次执行以下八步。任一步失败都阻断生产恢复，不得跳步、调序或使用历史成功回执替代当前版本验证。恢复生产只恢复升级前已审阅的配置和权限，不自动改变 `mode`、回复策略或两道写入门禁。

### 事故基线：Windows 批处理启动器不可进入生产

2026-08-01 升级到 `lark-cli 1.0.81` 后，本地和全局版本号及原生二进制 SHA-256 均一致，但 Python 解析器仍优先命中了工作区根目录的 `lark-cli.cmd`。服务随后通过 `cmd.exe /c` 传递 `--content`：帮助正文中的 `<表名或别名>` 被解释为输入重定向，状态正文中的 `|` 被解释为管道，导致事件和指令均已成功处理、出站回复却分别以 1/255 退出。

因此，版本一致只证明包版本没有漂移，不能证明生产回复链路安全。Windows 上必须直接执行 npm 包内的 `node_modules\@larksuite\cli\bin\lark-cli.exe`；`.cmd` / `.bat` 解析结果属于阻断项。回复 dry-run 必须同时覆盖换行和 shell 元字符，不能只测普通三行文本。

### 2026-08-16：1.0.87 升级加固

- 本地 `.codex` 与全局 npm 包必须同时为 `1.0.87`，并核对两份原生 `lark-cli.exe` 的版本与 SHA-256。
- Windows 解析器发现多个原生包且 `package.json` 版本不一致时必须直接阻断，禁止按当前目录或 PATH 顺序静默选择旧包。
- 生产恢复前必须看到解析路径为包内原生 `lark-cli.exe`、`event_ready=true`、单一消费者；版本漂移、批处理 shim 或回复回归失败均保持停止。

### 1. 冻结生产并记录基线

- 读取管理器状态和 SQLite 账本；存在 `queued`、`planning`、`applying_local` 或 `uploading` 任务时，等待安全结束并人工核验，不得直接升级。
- 记录实时配置 SHA-256，以及 `mode`、全部回复开关、两道写入门禁、群和角色 ID；逐字节备份配置到本次 runtime 维护目录。
- 记录当前消费者数量、`received`、`dropped`、失败出站消息数和最近错误；验证副本必须使用独立 runtime，并强制 `shadow`、禁本地 Apply、禁生产 Upload。

### 2. 固化升级前版本、路径和回滚证据

- 记录 `Get-Command lark-cli -All`、本地/全局 `package.json` 版本、原生 `lark-cli.exe` 路径和 SHA-256。
- 调用同步脚本的 `resolve_lark_cli()` 并记录真实解析路径；Windows 结果若以 `.cmd` / `.bat` 结尾，立即阻断。
- 执行 `lark-cli update --check --json`，保存版本和 `skills_status`；备份本次会变化的包元数据和 Skill 文件，但不得保存凭据、token 或浏览器状态。

### 3. 优雅停止生产事件服务

- 使用 `manage_event_service.ps1 -Action stop`，由父进程关闭事件消费者；禁止强杀或无条件 `event stop --force`。
- 确认服务状态为 `stopped`、事件键无遗留消费者并保留停止日志。停止失败或出现孤儿消费者时先排查，不得边运行边替换 CLI。

### 4. 统一升级 CLI 与官方 Skills

- 按 `lark-shared` 使用官方 `lark-cli update`；同时存在本地和全局安装时，二者必须升级到同一精确版本。
- 核对本地/全局 `package.json`、锁文件、`--version` 和原生 exe SHA-256；任一处仍指向旧版本都属于版本漂移。
- 核验 `skills_status.in_sync=true`，同步官方 `lark-*` 文件时保留 `agents/openai.yaml`；不得借升级修改业务注册表、运行配置或生产权限。

### 5. 执行离线兼容性和 Windows 元字符回归

- 执行两个生产脚本的 `py_compile` 和 Skill 全部 `unittest`；任何失败都阻断启动。
- `resolve_lark_cli()` 必须返回原生 `...\node_modules\@larksuite\cli\bin\lark-cli.exe`，且执行层必须拒绝 `.cmd` / `.bat`。
- 回复回归正文必须至少包含三行文本及 `<target> | failed & retry > audit`、`%PATH% ^ (test)`；要求这些字符逐字保留、换行只作为 JSON 转义、不得被 shell 展开或执行。
- 核对 `--as bot` 和 50 字符以内的 `--idempotency-key` 位于 `--content` 之前，`--content` 是可重新解析的 JSON；同时验证 `{ok,data,error}` 信封。
- 通过当前原生 exe 执行无写入 `--dry-run`，并核验 `im +messages-mget`、`im +messages-reply`、事件 NDJSON 和 `[event] ready` 契约。仅普通文本成功不足以通过此门禁。

### 6. 只用 shadow 验证新版本启动

- 使用独立 shadow 配置启动，确认实际 CLI 路径和版本正是本次目标版本；不得先用实时生产配置试启动。
- 核验 `status=running`、`event_ready=true`、单一活动消费者、`dropped=0`，并确认本地 Apply 和生产 Upload 均为 `false`。
- 检查 bot 身份、最小 scope 和启动日志；升级验证不得创建业务写入回执。

### 7. 在登记群执行帮助/状态端到端回复测试

- 经明确授权后，以用户身份在一个登记群分别发送带真实 mention 的 `@管家 帮助` 和 `@管家 状态`；这两条指令不得创建 Plan、Apply 或 Upload。
- 必须观察到事件消费者各新增一次接收，日志结果分别为 `help`、`status`，SQLite 出站账本新增两条 `sent` 且没有新增 `failed`。
- 以 bot 身份回读群消息，确认两条回复的 `reply_to`、发送者和完整正文。帮助回复覆盖 `< >`，状态回复覆盖 `|`，因此两者都是升级后的强制真实回归，而不是可选冒烟测试。
- 若还执行幂等测试，同一目标消息和同一幂等键调用两次必须只出现一条回复；机器人自发消息不得递归生成任务。

### 8. 恢复原配置并重启生产服务

- 优雅停止 shadow 实例，重新读取实时配置并与第 1 步 SHA-256 比较；配置漂移时阻断恢复。
- 用逐字节一致的原生产配置启动，回读 `mode`、所有回复开关和两道写入门禁，要求与升级前一致。
- 最终核验 `status=running`、`event_ready=true`、单一消费者、`dropped=0`、原生 exe 精确路径/版本、日志无启动错误，并保存升级回执。任一条件失败都保持生产停止或退回 shadow，不得宣称升级完成。
