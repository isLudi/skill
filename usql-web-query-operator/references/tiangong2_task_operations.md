# Tiangong2 任务执行日志与受治理发布

## 适用范围

`scripts/tiangong2_task.py` 在原只读任务探查之外提供两类严格分离的能力：

- `fetch-execution-log`：只读拉取一个精确、自有任务的执行期、执行实例、stage 明细及完整分页日志；
- `plan-task-publish` → `publish-task`：先生成 Hash 绑定的只读发布计划，再在单独命令中显式确认发布一个已经保存到平台的任务版本。

这些命令不保存或编辑源码，不提交任务，不运行、调试、重跑或启动调度，不修改调度配置，也不能作用于当前登录账号不拥有的任务。

## 账号、状态与任务作用域

所有命令继续只读取 `usql_api.env` 的精确区段：

```text
# tiangong2 Web Query (Playwright) credentials
BAIJIA_USERNAME=...
BAIJIA_PASSWORD=...
```

浏览器状态固定在 `runtime\usql-web-query-operator\tiangong2-task\state.json`，不得复用普通 USQL、Data Map 或其他账号状态。每次命令必须核验登录身份。

日志、计划和发布都要求四个稳定标识：`project-id`、`folder`、`menu-id`、`task-name`。解析器从唯一项目的“数据开发”根目录进入精确一级文件夹，再递归找到菜单 ID；任务名必须回读一致，`principal` 或 `creator` 必须与当前登录账号一致。任一项目、目录、菜单、名称或负责人不匹配都会在目标接口调用前失败。

## 执行日志调取

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

## 明确不授权的操作

- 不保存、替换或编辑任务源码；
- 不提交任务；
- 不运行、调试、立即执行、重跑、启动或停止调度；
- 不修改调度、资源、负责人、目录或权限；
- 不跨项目、跨一级目录或操作其他负责人的任务；
- 不把日志、计划或 Receipt 自动写入业务知识库。

## 维护验证

修改本能力至少运行：

```powershell
D:\anaconda3\python.exe -m pytest tests -q -k tiangong2
D:\anaconda3\python.exe scripts\build_command_reference.py --check
D:\anaconda3\python.exe C:\Users\Ludim\.codex\skills\.system\skill-creator\scripts\quick_validate.py C:\Users\Ludim\.codex\skills\usql-web-query-operator
```

还需覆盖：JSON/form 传输差异、非白名单接口联网前拦截、日志分页与脱敏、跨目录/跨负责人拒绝、计划篡改、Hash/确认门、单次发布、发布前漂移和发布后版本/源码回读。
