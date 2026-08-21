# Tiangong2 自有任务维护会话、源码修复、提交、发布、调试执行与日志

## 适用范围

`scripts/tiangong2_task.py` 在原只读任务探查之外提供八类严格分离的能力：

- `fetch-execution-log`：只读拉取一个精确、自有任务的执行期、执行实例、stage 明细及完整分页日志；
- `list-execution-history`：只读列出一个精确、自有任务最近的执行实例，便于先定位最新 exec id；
- `plan-task-maintenance-session` → `authorize-task-maintenance-session`：把一个精确自有任务、默认参数块、资源、有效期、操作白名单和调试执行预算绑定为一次用户授权；会话内后续阶段不再重复向用户确认；
- `plan-task-python-patch` → `apply-task-python-patch`：只允许不含疑似密钥的精确文本替换，禁止改变 `query_sql`、公司默认参数块和资源绑定；
- `plan-task-query-update` → `apply-task-query-update`：只允许一个自有 Python 任务的唯一 `query_sql` 三引号正文变化，证明公司默认参数块逐字节不变，并强制通过 Hash 绑定的准确性优先 SQL 质量门禁；
- `plan-task-submit` → `submit-task`：把已保存源码和版本说明绑定到只读 Plan，再显式提交该任务的新版本；
- `plan-task-publish` → `publish-task`：先生成 Hash 绑定的只读发布计划，再在单独命令中显式确认发布一个已经保存到平台的任务版本。
- `plan-task-execution` → `execute-task-once`：只允许一个已发布自有任务立即执行一次，强制不触发下游、不注入运行参数、不禁用 stage。

远端写能力继续使用相互独立的只读/写客户端、Plan 和 Receipt。一次维护会话只替代多次人工确认，不会把保存、提交、发布和执行合并为一个未经回读的远端请求：每个阶段仍独立规划、Hash 绑定、检查漂移、单次调用并回读。所有能力都不能作用于当前登录账号不拥有的任务；完整源码文件替换和凭据编辑仍不存在，非 SQL 修复只能走受限精确补丁。

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

## 权限分级与一次授权会话

Tiangong2 命令采用四级权限：

| 级别 | 权限 | 用户确认 |
|---|---|---|
| R | 探查、计划、执行记录和日志等远端只读 | 请求本身即可，不产生远端写入 |
| P | 一个精确阶段的保存、提交、发布或执行 | 精确阶段 Plan Hash 加对应 `--confirm-*` |
| M | 一个精确自有任务的限时维护会话 | 只在激活会话时确认一次；会话内各阶段继续使用精确 Plan Hash，但不重复询问用户 |
| X | 跨负责人/跨一级目录、凭据/默认块/资源/调度/权限修改、下游触发、既有执行重跑、任意完整源码替换 | 永久拒绝，M 级也不能放行 |

M 级先生成只读计划：

```powershell
D:\anaconda3\python.exe scripts\tiangong2_task.py plan-task-maintenance-session `
  --project-id 308 `
  --folder "吕帅" `
  --menu-id 102044 `
  --task-name "market2lark_ip" `
  --reason "修复IP渠道校验并完成写入验收" `
  --duration-minutes 180 `
  --max-executions 3
```

一次确认激活：

```powershell
D:\anaconda3\python.exe scripts\tiangong2_task.py authorize-task-maintenance-session `
  --plan-file <reviewed-session-plan.json> `
  --expected-plan-sha256 <exact-plan-sha256> `
  --confirm-maintenance
```

激活命令只写 Tiangong2 runtime 中的本地授权工件，不调用远端写接口。工件绑定账号、project/folder/menu/task/owner、基线源码/默认块/资源、允许操作、到期时间、激活时版本和执行 ID，以及最大新增执行次数。后续 Apply 命令使用 `--maintenance-session-file` 和 `--expected-maintenance-session-sha256` 替代该阶段的 `--confirm-*`。每个阶段仍必须提供自己的精确 Plan Hash。

维护会话不会授权自动盲重试。每次执行后必须读取新 exec 的终态和完整日志；只有诊断表明需要新源码、形成新补丁 Plan 且执行预算尚未耗尽时，才可在同一会话继续下一轮。会话到期、执行预算耗尽、作用域/默认块/资源漂移或写请求状态不确定时立即停止。

## 执行日志调取

先列出最近执行实例：

```powershell
D:\anaconda3\python.exe scripts\tiangong2_task.py list-execution-history `
  --project-id 308 `
  --folder "吕帅" `
  --menu-id 101900 `
  --task-name "market2lark_koc" `
  --limit 20
```

该命令只读取最新一页执行期，并对每个候选期回读执行实例；所有行必须继续绑定精确 Nezha task id、任务名和已核验负责人。结果脱敏后仅写入 `runtime\usql-web-query-operator\tiangong2-task\execution-history`，不会读取 stage 日志或触发任务。

```powershell
D:\anaconda3\python.exe scripts\tiangong2_task.py fetch-execution-log `
  --project-id 308 `
  --folder "吕帅" `
  --menu-id 101900 `
  --task-name "market2lark_koc" `
  --exec-id 164912112
```

读取链路是固定白名单，不提供通用 URL：

- GET：`nezha/task/getTaskAndSchedule`、`nezha/task/getTaskExecutionDetail`
- JSON POST：`nezha/task/listTaskExecutionPeriods`
- form POST：`nezha/task/listTaskExecutions`、`nezha/stage/getStageLog`

命令必须先证明执行 ID 属于精确 Nezha task，再读取该执行的全部 stage。日志按照 `hasMore/nextBeginPos` 分页，页码必须单调前进且有上限；身份不一致、执行不唯一、stage 不属于任务或分页异常均失败。

日志只写入 Tiangong2 专用 runtime 的时间戳目录。stage 文本先经过敏感值脱敏，`execution.json` 只保留脱敏元数据、日志文件 Hash、诊断签名和使用过的白名单接口；控制台不打印完整日志。

## 非 SQL Python 精确补丁

当完整日志已证明根因位于 `query_sql` 之外的 Python 逻辑时，可以创建无密钥精确补丁 JSON：

```json
{
  "schema_version": "tiangong2-python-exact-patch-v1",
  "replacements": [
    {
      "old": "旧的唯一文本片段",
      "new": "新的文本片段",
      "expected_count": 1
    }
  ]
}
```

每个旧片段必须在当前源码中恰好命中一次；单个片段、总大小和替换数量都有上限。补丁文本不能命中密钥命名或脱敏规则，不能修改 `query_sql`、公司默认参数块、资源绑定，也不能使投影源码语法失效。计划只保存补丁文件 Hash、旧/新片段 Hash、长度、匹配次数和投影源码 Hash；含凭据完整源码仅在进程内读取、投影和提交，不落盘、不打印。

```powershell
D:\anaconda3\python.exe scripts\tiangong2_task.py plan-task-python-patch `
  --project-id 308 `
  --folder "吕帅" `
  --menu-id 102044 `
  --task-name "market2lark_ip" `
  --patch-file <reviewed-exact-patch.json>
```

P 级单阶段保存使用 `--confirm-save-python-patch`；M 级使用已激活会话，不需要再次询问用户：

```powershell
D:\anaconda3\python.exe scripts\tiangong2_task.py apply-task-python-patch `
  --plan-file <reviewed-patch-plan.json> `
  --expected-plan-sha256 <exact-plan-sha256> `
  --maintenance-session-file <active-session.json> `
  --expected-maintenance-session-sha256 <exact-session-sha256>
```

保存前重新读取精确任务、完整源码、默认块、资源和补丁文件；任一 Hash 漂移即阻断。写客户端仅允许一次 `dataDevelop/savePython`，随后必须回读完整源码 Hash、未变 `query_sql`、未变默认块和资源语义。请求发出后回读不确定时停止整个维护链，不得继续提交、发布或执行。

## Python query_sql 限定更新

每个候选 SQL 必须先用 `code-simplifier` 或等价方式做结构化审阅，但不能把“更短”当作准确。审阅 JSON 使用 `tiangong2-query-sql-review-v1`，并与候选 SQL 的精确 SHA-256 绑定，至少声明：

- `accuracy.status=passed`、最终输出粒度、按顺序排列的全部输出列、业务不变量及其证据；
- `simplification.status=passed`、实际简化项、保留的语义和已移除的重复处理；
- `performance.status=static_passed|runtime_passed`；只有提供真实运行证据时才可写 `runtime_passed`；
- 对解析器发现的必要重复扫描、三路以上同源 `UNION ALL`、大结果最终排序或结构复杂度回退，在 `performance.justifications` 中按 finding code 逐项说明其准确性必要性。

解析器无条件拒绝多语句、非 SELECT、物理表 `SELECT *`、`SELECT DISTINCT *`、Python 管理的分区占位符变化、未命名最终列和有序输出列契约不一致。审阅文件、静态分析结果和 SQL 一起写入 Plan Hash；保存前全部重算，任何漂移均阻断。这个门禁约束查询写法，不替代原业务 Skill 的指标、渠道、期次和粒度语义审查。

只读计划命令：

```powershell
D:\anaconda3\python.exe scripts\tiangong2_task.py plan-task-query-update `
  --project-id 308 `
  --folder "吕帅" `
  --menu-id 101900 `
  --task-name "market2lark_koc" `
  --replacement-sql-file <reviewed.sql> `
  --sql-review-file <reviewed-sql-quality.json>
```

计划只接受 `taskType=PYTHON`，源码必须恰好有一个 `query_sql = """..."""`，并且包含唯一的 `# === 默认参数，不需要修改 ===` / `# === end 默认参数，不需要修改 ===`。计划记录当前完整源码、当前 SQL、公司默认参数块、替换 SQL、投影源码、任务元数据和质量审阅的 SHA-256，不把源码、SQL 或凭据写入计划。若静态硬错误或未说明的审阅项仍存在，状态为 `blocked_sql_quality`，不能保存。

显式保存命令：

```powershell
D:\anaconda3\python.exe scripts\tiangong2_task.py apply-task-query-update `
  --plan-file <reviewed-plan.json> `
  --expected-plan-sha256 <exact-sha256> `
  --confirm-save-query
```

若同一精确任务已激活 M 级维护会话，用 `--maintenance-session-file` 与 `--expected-maintenance-session-sha256` 替代 `--confirm-save-query`；SQL Plan、质量审阅、AST 门禁和 SQL Hash 仍全部保留。

保存前重新读取任务作用域、完整源码、当前 SQL、公司默认参数块、任务元数据、当前资源语义和本地 SQL 文件，任何 Hash 漂移都阻断。投影必须证明 Python 前缀和 `query_sql` 后全部后缀逐字节不变；单用途客户端仅能 form POST 一次 `dataDevelop/savePython`，payload 固定为计划 task ID、投影后的完整 Python 与现有 `resourceId`。平台返回 `null` 且项目没有可选资源时，以整数 `0` 传输“无资源”语义，回读时 `null/0` 归一化为同一语义；不得借用其他任务资源。保存后重新读取完整源码，只有投影源码 Hash、替换 SQL Hash、公司默认参数块 Hash 和资源语义全部一致才成功。请求已发出但回读失败时 Receipt 标记需要人工检查，绝不自动重试、回滚、发布或执行。

## 版本提交

提交计划把当前已保存源码、任务元数据、版本状态、调度配置状态和版本说明一起绑定到 Hash。`task/getScheduleConfig` 即使返回非空占位对象，只要其中 `taskId` 为空或不等于当前开发任务 ID，仍必须判定为 `blocked_unconfigured_schedule`；不得等到 `taskConfirm` 返回“调度未配置”后才发现前置条件缺失：

```powershell
D:\anaconda3\python.exe scripts\tiangong2_task.py plan-task-submit `
  --project-id 308 `
  --folder "吕帅" `
  --menu-id 101900 `
  --task-name "market2lark_koc" `
  --note "修复KOC导入SQL_移除高风险多表广播连接"
```

版本说明不能为空、最长 200 字，只允许中文、英文字母、数字和下划线。若已存在源码 Hash 与当前保存源码一致的“未发布”版本，提交计划必须返回 `blocked_already_submitted`，不得重复创建版本。显式提交只接受精确计划 Hash：

```powershell
D:\anaconda3\python.exe scripts\tiangong2_task.py submit-task `
  --plan-file <reviewed-plan.json> `
  --expected-plan-sha256 <exact-sha256> `
  --confirm-submit
```

M 级会话可以替代 `--confirm-submit`，但不能绕过版本说明、调度配置、源码/版本漂移和单次 `taskConfirm` 限制。

提交前重新核验账号、所有权、目录、源码、任务元数据、版本状态及完整调度配置 Hash。调度必须继续绑定当前开发任务 ID；计划后若调度被补配、清空或修改，旧计划一律按漂移阻断并重新生成。单用途客户端只可 form POST 一次 `dataDevelop/taskConfirm`，payload 固定为计划 task ID 与 Hash 绑定的版本说明，不会再次保存源码。平台没有单独的提交状态读取接口：若任务元数据或版本状态发生变化，Receipt 记录 `fully_verified=true`；若成功响应后只观察到源码稳定，则如实记录 `accepted_with_stable_source_readback` 和 `fully_verified=false`，随后必须由独立发布及新版本源码回读给出最终确认。请求失败或响应不确定时不自动重试。

## 发布计划

发布计划必须回读每个“未发布”版本的源码，并且只在恰好一个未发布版本与当前保存源码 Hash 一致时为 `ready`；零个匹配版本说明尚未成功提交，多个匹配版本说明目标歧义，均不得发布。唯一版本 ID、当前源码 Hash 与版本状态一起写入发布计划 Hash，发布后回读也必须证明正是该版本 ID 成为最新已发布版本。

```powershell
D:\anaconda3\python.exe scripts\tiangong2_task.py plan-task-publish `
  --project-id 308 `
  --folder "吕帅" `
  --menu-id 101900 `
  --task-name "market2lark_koc"
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

M 级会话可以替代 `--confirm-publish`，但发布 Plan 仍必须唯一绑定与当前源码相同的未发布版本。

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
  --task-name "market2lark_koc"
```

计划绑定源码、任务元数据、版本状态、最新发布版本、当前执行 ID 集合及 `period_time`。显式执行：

```powershell
D:\anaconda3\python.exe scripts\tiangong2_task.py execute-task-once `
  --plan-file <reviewed-plan.json> `
  --expected-plan-sha256 <exact-sha256> `
  --confirm-execute
```

M 级会话可以替代 `--confirm-execute`；执行 Plan 会按会话激活时的执行 ID 基线计算新增次数，达到预算后拒绝继续执行。

执行前重新验证身份、作用域、源码、元数据、版本和执行历史均未漂移。单用途客户端只可 JSON POST 一次 `nezha/task/executeOnce`；payload 强制为计划 Nezha task ID、计划数据周期、`triggerSuccessor=false`、`params={}`、`disabledStages=[]`。成功 Receipt 还必须只读观察到该数据周期下唯一的新 exec ID；终态和完整日志继续由 `list-execution-history` / `fetch-execution-log` 核验。

## 明确不授权的操作

- query_sql 更新不能夹带其他 Python；非 SQL 修复必须使用无密钥精确补丁。本 Skill 不提供完整源码文件替换、凭据编辑或任意代码编辑入口，任何模式都不得改变公司默认参数块；
- 不使用编辑页试跑，不重跑既有执行；调试只能在新补丁/新版本后生成新的精确执行 Plan，并受会话执行预算约束；不触发下游，不启动或停止调度；
- 不修改调度、资源、负责人、目录或权限；
- 一次会话授权不能把保存、提交、发布、单次执行合并成一个隐式写请求；各阶段的 Plan、Hash、漂移、单次客户端和回读必须保留；
- 不跨项目、跨一级目录或操作其他负责人的任务；
- 不把日志、计划或 Receipt 自动写入业务知识库。

## 维护验证

修改本能力至少运行：

```powershell
D:\anaconda3\python.exe -m pytest tests -q -k tiangong2
D:\anaconda3\python.exe scripts\build_command_reference.py --check
D:\anaconda3\python.exe C:\Users\Ludim\.codex\skills\.system\skill-creator\scripts\quick_validate.py C:\Users\Ludim\.codex\skills\usql-web-query-operator
```

还需覆盖：JSON/form 传输差异、非白名单接口联网前拦截、日志分页与脱敏、跨目录/跨负责人拒绝、任意完整源码替换命令不存在、精确补丁唯一命中/无密钥/query_sql 与默认块保护/语法检查、维护会话作用域/Hash/到期/操作白名单/执行预算、query_sql 唯一替换和默认块逐字节不变、SQL 审阅必填及 Hash 漂移、物理星号/重复同源 Union/占位符/输出列契约门禁、计划篡改、P/M 级授权门、保存/提交/发布/执行单次写入、各阶段漂移与回读。
