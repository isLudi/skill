# Tiangong2 任务 query_sql 更新、提交、发布、单次执行与日志

## 适用范围

`scripts/tiangong2_task.py` 在原只读任务探查之外提供六类严格分离的能力：

- `fetch-execution-log`：只读拉取一个精确、自有任务的执行期、执行实例、stage 明细及完整分页日志；
- `list-execution-history`：只读列出一个精确、自有任务最近的执行实例，便于先定位最新 exec id；
- `plan-task-query-update` → `apply-task-query-update`：只允许一个自有 Python 任务的唯一 `query_sql` 三引号正文变化，并证明公司默认参数块逐字节不变；
- `plan-task-submit` → `submit-task`：把已保存源码和版本说明绑定到只读 Plan，再显式提交该任务的新版本；
- `plan-task-publish` → `publish-task`：先生成 Hash 绑定的只读发布计划，再在单独命令中显式确认发布一个已经保存到平台的任务版本。
- `plan-task-execution` → `execute-task-once`：只允许一个已发布自有任务立即执行一次，强制不触发下游、不注入运行参数、不禁用 stage。

六类能力使用相互独立的只读/写客户端、Plan 和 Receipt。query_sql 保存不能顺带提交、发布或执行；提交不能顺带保存、发布或执行；发布不能顺带保存、提交或执行；执行不能保存、提交、发布、调试、重跑或修改调度。所有能力都不能作用于当前登录账号不拥有的任务，也不能修改唯一 query_sql 之外的 Python 源码。

故障分类、禁止盲目重跑、外部承接系统写入证据及端到端完成判据见 [tiangong2_python_task_diagnostics_acceptance.md](tiangong2_python_task_diagnostics_acceptance.md)。该验收规范只扩大证据要求，不扩大任何写权限。

## 账号、状态与任务作用域

所有命令继续只读取 `usql_api.env` 的精确区段：

```text
# tiangong2 Web Query (Playwright) credentials
BAIJIA_USERNAME=...
BAIJIA_PASSWORD=...
```

浏览器状态固定在 `runtime\usql-web-query-operator\tiangong2-task\state.json`，不得复用普通 USQL、Data Map 或其他账号状态。每次命令必须核验登录身份。

日志、计划、保存、提交、发布和执行都要求四个稳定标识：`project-id`、`folder`、`menu-id`、`task-name`。解析器从唯一项目的“数据开发”根目录进入精确一级文件夹，再递归找到菜单 ID；任务名必须回读一致，`principal` 或 `creator` 必须与当前登录账号一致。任一项目、目录、菜单、名称或负责人不匹配都会在目标接口调用前失败。

## 执行日志调取

先列出最近执行实例：

```powershell
D:\anaconda3\python.exe scripts\tiangong2_task.py list-execution-history `
  --project-id 308 `
  --folder "吕帅" `
  --menu-id 101900 `
  --task-name "market_conversion_2_lark" `
  --limit 20
```

该命令只读取最新一页执行期，并对每个候选期回读执行实例；所有行必须继续绑定精确 Nezha task id、任务名和已核验负责人。结果脱敏后仅写入 `runtime\usql-web-query-operator\tiangong2-task\execution-history`，不会读取 stage 日志或触发任务。

```powershell
D:\anaconda3\python.exe scripts\tiangong2_task.py fetch-execution-log `
  --project-id 308 `
  --folder "吕帅" `
  --menu-id 101900 `
  --task-name "market_conversion_2_lark" `
  --exec-id 164912112
```

读取链路是固定白名单，不提供通用 URL：

- GET：`nezha/task/getTaskAndSchedule`、`nezha/task/getTaskExecutionDetail`
- JSON POST：`nezha/task/listTaskExecutionPeriods`
- form POST：`nezha/task/listTaskExecutions`、`nezha/stage/getStageLog`

命令必须先证明执行 ID 属于精确 Nezha task，再读取该执行的全部 stage。日志按照 `hasMore/nextBeginPos` 分页，页码必须单调前进且有上限；身份不一致、执行不唯一、stage 不属于任务或分页异常均失败。

日志只写入 Tiangong2 专用 runtime 的时间戳目录。stage 文本先经过敏感值脱敏，`execution.json` 只保留脱敏元数据、日志文件 Hash、诊断签名和使用过的白名单接口；控制台不打印完整日志。

## Python query_sql 限定更新

只读计划命令：

```powershell
D:\anaconda3\python.exe scripts\tiangong2_task.py plan-task-query-update `
  --project-id 308 `
  --folder "吕帅" `
  --menu-id 101900 `
  --task-name "market_conversion_2_lark" `
  --replacement-sql-file <reviewed.sql>
```

计划只接受 `taskType=PYTHON`，源码必须恰好有一个 `query_sql = """..."""`，并且包含唯一的 `# === 默认参数，不需要修改 ===` / `# === end 默认参数，不需要修改 ===`。计划记录当前完整源码、当前 SQL、公司默认参数块、替换 SQL、投影源码和任务元数据的 SHA-256，不把源码、SQL 或凭据写入计划。

显式保存命令：

```powershell
D:\anaconda3\python.exe scripts\tiangong2_task.py apply-task-query-update `
  --plan-file <reviewed-plan.json> `
  --expected-plan-sha256 <exact-sha256> `
  --confirm-save-query
```

保存前重新读取任务作用域、完整源码、当前 SQL、公司默认参数块、任务元数据、当前资源语义和本地 SQL 文件，任何 Hash 漂移都阻断。投影必须证明 Python 前缀和 `query_sql` 后全部后缀逐字节不变；单用途客户端仅能 form POST 一次 `dataDevelop/savePython`，payload 固定为计划 task ID、投影后的完整 Python 与现有 `resourceId`。平台返回 `null` 且项目没有可选资源时，以整数 `0` 传输“无资源”语义，回读时 `null/0` 归一化为同一语义；不得借用其他任务资源。保存后重新读取完整源码，只有投影源码 Hash、替换 SQL Hash、公司默认参数块 Hash 和资源语义全部一致才成功。请求已发出但回读失败时 Receipt 标记需要人工检查，绝不自动重试、回滚、发布或执行。

## 版本提交

提交计划把当前已保存源码、任务元数据、版本状态和版本说明一起绑定到 Hash：

```powershell
D:\anaconda3\python.exe scripts\tiangong2_task.py plan-task-submit `
  --project-id 308 `
  --folder "吕帅" `
  --menu-id 101900 `
  --task-name "market_conversion_2_lark" `
  --note "修复KOC导入SQL_移除高风险多表广播连接"
```

版本说明不能为空、最长 200 字，只允许中文、英文字母、数字和下划线。显式提交只接受精确计划 Hash：

```powershell
D:\anaconda3\python.exe scripts\tiangong2_task.py submit-task `
  --plan-file <reviewed-plan.json> `
  --expected-plan-sha256 <exact-sha256> `
  --confirm-submit
```

提交前重新核验账号、所有权、目录、源码、任务元数据和版本状态。单用途客户端只可 form POST 一次 `dataDevelop/taskConfirm`，payload 固定为计划 task ID 与 Hash 绑定的版本说明，不会再次保存源码。平台没有单独的提交状态读取接口：若任务元数据或版本状态发生变化，Receipt 记录 `fully_verified=true`；若成功响应后只观察到源码稳定，则如实记录 `accepted_with_stable_source_readback` 和 `fully_verified=false`，随后必须由独立发布及新版本源码回读给出最终确认。请求失败或响应不确定时不自动重试。

## 发布计划

```powershell
D:\anaconda3\python.exe scripts\tiangong2_task.py plan-task-publish `
  --project-id 308 `
  --folder "吕帅" `
  --menu-id 101900 `
  --task-name "market_conversion_2_lark"
```

计划命令只读取当前已保存源码、任务元数据和版本状态，记录：

- 精确身份、项目、目录、菜单、task/Nezha ID 和负责人；
- 当前源码精确 SHA-256 与规范化比较 SHA-256；
- 任务元数据 SHA-256；
- 全部版本状态 SHA-256、版本 ID 清单和最新已发布源码 Hash；
- 是否与最新已发布源码一致；
- 对完整计划正文计算的 `plan_sha256`。

若当前源码已经等于最新已发布版本，计划状态为 `blocked_already_published`，避免重复发布。计划工件只能写入 Tiangong2 专用 runtime。

## 显式发布

发布只接受已审阅的 ready 计划：

```powershell
D:\anaconda3\python.exe scripts\tiangong2_task.py publish-task `
  --plan-file <reviewed-plan.json> `
  --expected-plan-sha256 <exact-sha256> `
  --confirm-publish
```

命令在浏览器启动前验证计划自身 Hash、外部提交的精确 Hash 和显式确认；登录后重新核验账号、项目、目录、菜单、任务名与负责人，并重新读取源码、任务元数据和版本状态防止漂移。

写客户端与只读客户端分离，只暴露一个单次方法；同一 menu 先取得本机互斥锁，唯一允许的写接口为 form POST `dataDevelop/publishTask`，且菜单 ID 必须等于授权计划。请求不做自动重试。发布后必须观察到版本状态变化，并从新“已发布”版本回读源码 Hash 与计划源码一致，才产生 `fully_verified=true` 的成功 Receipt。

若发布请求已经发出但响应或回读失败，Receipt 标记 `manual_attention_required=true`，不得自动重试、回滚、下线、重新发布或运行任务。

## 单次立即执行

执行计划仅允许当前已保存源码与最新已发布版本一致：

```powershell
D:\anaconda3\python.exe scripts\tiangong2_task.py plan-task-execution `
  --project-id 308 `
  --folder "吕帅" `
  --menu-id 101900 `
  --task-name "market_conversion_2_lark"
```

计划绑定源码、任务元数据、版本状态、最新发布版本、当前执行 ID 集合及 `period_time`。显式执行：

```powershell
D:\anaconda3\python.exe scripts\tiangong2_task.py execute-task-once `
  --plan-file <reviewed-plan.json> `
  --expected-plan-sha256 <exact-sha256> `
  --confirm-execute
```

执行前重新验证身份、作用域、源码、元数据、版本和执行历史均未漂移。单用途客户端只可 JSON POST 一次 `nezha/task/executeOnce`；payload 强制为计划 Nezha task ID、计划数据周期、`triggerSuccessor=false`、`params={}`、`disabledStages=[]`。成功 Receipt 还必须只读观察到该数据周期下唯一的新 exec ID；终态和完整日志继续由 `list-execution-history` / `fetch-execution-log` 核验。

## 明确不授权的操作

- 不在 query_sql 限定更新中编辑其他 Python；本 Skill 不提供完整源码替换入口，任何模式都不得改变公司默认参数块；
- 如果修复涉及字段映射、外部系统写入、批次、回滚或其他 Python 逻辑，只能诊断并报告，不能借 query_sql 更新保存这些变化；
- 不使用编辑页试跑/调试，不重跑既有执行，不触发下游，不启动或停止调度；
- 不修改调度、资源、负责人、目录或权限；
- 不把保存、提交、发布、单次执行合并成一个隐式写阶段；
- 不跨项目、跨一级目录或操作其他负责人的任务；
- 不把日志、计划或 Receipt 自动写入业务知识库。

## 维护验证

修改本能力至少运行：

```powershell
D:\anaconda3\python.exe -m pytest tests -q -k tiangong2
D:\anaconda3\python.exe scripts\build_command_reference.py --check
D:\anaconda3\python.exe C:\Users\Ludim\.codex\skills\.system\skill-creator\scripts\quick_validate.py C:\Users\Ludim\.codex\skills\usql-web-query-operator
```

还需覆盖：JSON/form 传输差异、非白名单接口联网前拦截、日志分页与脱敏、跨目录/跨负责人拒绝、完整源码替换命令不存在、query_sql 唯一替换和默认块逐字节不变、计划篡改、Hash/确认门、保存/提交/发布/执行单次写入、各阶段漂移与回读。
