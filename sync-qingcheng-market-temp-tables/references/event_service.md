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
