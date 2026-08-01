---
name: sync-qingcheng-market-temp-tables
description: 受治理地预检、修订、合并并上传青橙项目部与市场顾问部的已登记临时表。适用于飞书群“青橙数据对接”或“市场顾问部临时表上传”中的最新附件/登记链接、本地工作簿与大航海 temp table 身份映射、来源新鲜度与行数/变化率/必要列空值门禁、E 盘累计工作簿候选生成、已有 USQL 临时表上传，以及 @管家 多群事件服务的配置、停启和审计。异常默认阻断上传。
---

# 青橙与市场顾问部临时表同步

这是两个部门共用的唯一临时表维护入口。它只处理注册表中的固定群聊、发布人、文件族、本地工作簿和平台临时表，不生成业务 SQL，也不接受任意文件名、任意路径或任意表名。

## 先确认路由

| 领域 | 登记群 | 默认来源人 | 文件族 |
|---|---|---|---|
| `qingcheng` | 青橙数据对接 | 郅玲玉；行课表为李怡青 | 个人期度目标、团队期度目标、团队月度目标、全员结果架构、青橙带班架构、青橙行课 |
| `market_consultant` | 市场顾问部临时表上传 | 张君言 | 成本、市场带班架构、到课课次、进量目标、评优架构、分配计划组 ID |

来源身份、精确群 ID、列映射、质量阈值、合并模式与上传顺序以 [workflow_registry.json](references/workflow_registry.json) 为机器可执行真源。开始任务前必须读取 [registered_sources.md](references/registered_sources.md)；市场表还必须读取 [market_transformations.md](references/market_transformations.md)。

## 市场本地表与平台表一一映射

`E:\1900_work\GAOTU\19002_市场顾问部看板维护表格` 当前 9 个 `.xlsx` 与大航海 `temp_table` 数据库的精确映射如下：

| 本地工作簿 | 大航海完整表名 | 自动化范围 |
|---|---|---|
| `ceshiqudao_pingyou.xlsx` | `temp_table.dingxi01_ceshiqudao_pingyou` | 仅登记映射 |
| `cost.xlsx` | `temp_table.dingxi01_cost` | 已纳入自动维护 |
| `daoke_1_6_t.xlsx` | `temp_table.dingxi01_daoke_1_6_t` | 已纳入自动维护 |
| `jiagou_db.xlsx` | `temp_table.dingxi01_jiagou_db` | 已纳入自动维护 |
| `jiagou_xinren.xlsx` | `temp_table.dingxi01_jiagou_xinren` | 仅登记映射 |
| `jiagou_zx.xlsx` | `temp_table.dingxi01_jiagou_zx` | 仅登记映射 |
| `jinliang_goal.xlsx` | `temp_table.dingxi01_jinliang_goal` | 已纳入自动维护 |
| `pingyou_jg.xlsx` | `temp_table.dingxi01_pingyou_jg` | 已纳入自动维护 |
| `plan_id.xlsx` | `temp_table.dingxi01_plan_id` | 已纳入自动维护 |

机器可执行记录位于 `workflow_registry.json.local_temp_table_inventories.market_consultant`。本地文件名和平台表名分别强制唯一，已纳入自动维护的 6 项还必须与文件族的 `target_workbook`、`platform_temp_table` 双向一致。

“仅登记映射”只确认表身份，不代表已有新群来源、合并规则、四类质量门禁或上传授权；这 3 项继续匹配 `deferred_filename_patterns`，不得被事件服务自动同步或上传。2026-07-29 的九表零行解析探针均成功，平台查询 ID 为 `1506786567`。

## 不可跨越的边界

固定流程为：

`下载到运行目录 → 预检与差异比较 → 生成候选工作簿和带哈希 Plan → 明确确认后写入本地 → 再次明确确认后上传`

- `plan` 只读飞书和现有工作簿，可以下载到运行目录并生成候选文件；不得修改 E 盘目标或平台。
- `apply-local` 只接受状态为 `ready` 的精确 Plan 哈希，并在原目录备份、原子替换、读回校验。它不授权上传。
- `upload` 只接受成功的本地回执及其精确哈希；逐表调用 `usql-web-query-operator` 的既有临时表上传适配器并记录回执。
- 来源过旧、行数越界、相对变化过大、必要列空值率超限、键重复、列/切片不合法、来源身份或群聊不匹配、哈希漂移、验证回归，均默认阻断。
- 分析、审计、设计或“预检”请求必须停在 `plan`。未经明确生产授权，不启动写入门禁，不恢复事件服务。
- 任何一次失败都使旧 Plan 失效；修复后必须重新发现来源并生成新 Plan。

## 领域特定保护

- 共享的 `jiagou_db.xlsx` 必须按 `dept_1` 隔离。青橙只能替换 `青橙项目部`，市场只能替换 `市场顾问部`，另一部门行必须原样保留。
- 市场累计源中的人工历史修订不得被整表覆盖。市场带班架构、到课课次和 `plan_id` 使用来源切片哈希，只允许新增或已审查的变更期次进入候选。
- 市场评优表只允许执行已登记的确定性修订：精确去重、邮箱前缀小写、证据可解析的年级填补、`x_qi_count` 重排。无法唯一解释时阻断。
- 市场到课表的空 `channel` 只能从同粒度现有目标记录唯一回填；缺失或多解时阻断。
- 青橙行课链接源需额外遵循 [course_schedule_source.md](references/course_schedule_source.md)。

## 命令入口

默认只生成计划：

```powershell
D:\anaconda3\python.exe C:\Users\Ludim\.codex\skills\sync-qingcheng-market-temp-tables\scripts\governed_temp_table_sync.py plan
```

按领域或文件族缩小范围：

```powershell
D:\anaconda3\python.exe C:\Users\Ludim\.codex\skills\sync-qingcheng-market-temp-tables\scripts\governed_temp_table_sync.py plan `
  --domain market_consultant `
  --family market_cost `
  --family market_plan_id
```

明确本地写入后：

```powershell
D:\anaconda3\python.exe C:\Users\Ludim\.codex\skills\sync-qingcheng-market-temp-tables\scripts\governed_temp_table_sync.py apply-local `
  --plan <sync_plan.json> `
  --expected-plan-sha256 <plan_sha256> `
  --confirm-local-write
```

明确生产上传后：

```powershell
D:\anaconda3\python.exe C:\Users\Ludim\.codex\skills\sync-qingcheng-market-temp-tables\scripts\governed_temp_table_sync.py upload `
  --plan <sync_plan.json> `
  --expected-plan-sha256 <plan_sha256> `
  --local-receipt <local_apply_receipt.json> `
  --expected-local-receipt-sha256 <receipt_sha256> `
  --confirm-production-upload
```

## 飞书事件服务

配置、群隔离、命令语法、审批和安全停启见 [event_service.md](references/event_service.md)。服务必须同时覆盖注册表中的两个精确群，但每条消息只能路由到其所在群的文件族；任务状态和审批也按群隔离。

每次升级 `lark-cli` 后，必须完整执行 `event_service.md` 中的“lark-cli 常态升级与生产重启（固定八步）”。Windows 生产解析路径必须指向 npm 包内的原生 `bin\lark-cli.exe`；解析为 `.cmd` / `.bat`、缺少多行及 `< > | &` 元字符 dry-run、或未在登记群验证“帮助/状态”真实回复，均阻断生产恢复。版本号一致不能替代这些门禁。

维护或验证服务时使用：

- `scripts/governed_temp_table_event_service.py`
- `scripts/manage_event_service.ps1`
- `references/event_service_config.example.json`

仅当用户明确要求启用且全部测试通过后，才允许生成生产配置、安装/更新启动任务并启动服务。

## 完成标准

- 计划列出来源消息 ID/时间/哈希、变换审计、切片选择、四类质量门禁、候选差异和阻断项。
- 本地写入必须有备份、替换结果、读回哈希和验证回执。
- 上传必须逐表返回验证/上传结果；任一失败即整体失败，不得把“候选已生成”或“本地已修改”表述为“平台已完成”。
- 修改本 Skill 后运行全部单测、离线六表回放、UTF-8/乱码检查、`git diff --check` 和仓库级验证；事件服务在完成前保持停用。
