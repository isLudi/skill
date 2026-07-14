# 数据中心 SQL 生产替换与刷新

## 目录

- [权限边界](#权限边界)
- [生产链路](#生产链路)
- [命令](#命令)
- [完成与失败判据](#完成与失败判据)

## 权限边界

三个命令面必须分开授权：

| 命令 | 远端行为 | 本地行为 | 权限级别 |
|---|---|---|---|
| `sync-data-center-sql` | 只读菜单和详情 | dry-run；加 `--write` 只更新本地业务 Skill 知识库 | 远端只读 |
| `plan-data-center-sql-replacement` | 只读一个数据集、SQL 和同步配置 | 写 runtime `DataCenterSqlReplacementPlan` | 远端只读 |
| `apply-data-center-sql-replacement` | 替换 SQL、预览运行、保存、立即执行同步 | 写 runtime `DataCenterSqlReplacementReceipt` | 远端生产写 |

`sync-data-center-sql --write` 绝不代表远端写权限；它只把远端已保存 SQL 同步到本地知识库。Replacement Plan 也不授予 Apply 权限。

## 生产链路

Apply 必须按固定顺序执行：

1. 按 `domain + menu_set_*` 回读数据集，核对名称、路径、`fileValue`、`subjectId`、`dataSourceId`、同步 `taskId` 和当前 SQL Hash。
2. 从详情页点击“编辑”，等待异步 CodeMirror 内容达到详情 API 的当前 SQL Hash；然后整体替换为计划绑定 SQL，并立即回读编辑器 Hash。
3. 点击 `play-circle` 运行，等待 `POST /data/set/execute` 返回 `status=success` 和 `errorCode=0`。
4. 点击保存，等待 `POST /data/set/saveAndUpdate` 成功；随后调用详情接口回读已保存 `executeSql`，要求 Hash 与计划完全一致。
5. 打开“同步状态”，记录当前执行记录基线，点击“立即执行”并确认，等待 `POST /data/set/schedules/executeOnce` 成功。
6. 轮询 `POST /data/set/schedules/list`；只有出现不属于基线的新记录且 `status=SUCCESS`，才标记 `fully_verified=true`。

Apply 使用单数据集跨进程锁。任一写前身份或 Hash 漂移都会阻断。保存后若刷新失败，不自动回滚 SQL；receipt 必须保留 `remote_sql_saved`、失败阶段和人工检查要求，任务不能报告成功。

## 命令

先生成只读计划：

```powershell
D:\anaconda3\python.exe scripts\usql_web_query.py plan-data-center-sql-replacement `
  --domain market `
  --dataset-name "分触达时间段--抖音咨询" `
  --sql-file C:\path\to\replacement.sql
```

同 SQL 只用于显式刷新演练，必须增加 `--allow-noop`；默认会以 `NO_CONTENT_CHANGE` 阻断。

审阅计划后执行生产写：

```powershell
D:\anaconda3\python.exe scripts\usql_web_query.py apply-data-center-sql-replacement `
  --plan-file C:\path\to\data_center_replacement_plan.json `
  --expected-plan-sha256 <exact_hash> `
  --confirm-production-write
```

SQL 文件必须是 UTF-8 without BOM。Apply 会重新读取 SQL 文件并核对 Hash；计划生成后修改文件会在浏览器写入前阻断。

## 完成与失败判据

- 成功：预览成功、保存响应成功、详情 SQL Hash 回读一致、立即执行响应成功、新同步记录 `SUCCESS`，五项缺一不可。
- 失败：SQL 漂移、身份漂移、预览失败、保存失败、保存 Hash 不一致、新记录失败或超时，任一情况均返回非零。
- Receipt：成功或失败都写入 `runtime/usql-web-query-operator/data-center/replacement/`；不保存 cookie、密码或完整 SQL。
- 发布语义：本链路更新数据中心数据集并刷新底层同步，不等同于 BI 看板发布，也不修改业务 Skill 知识库。需要更新本地 canonical SQL 时，另行运行只读/本地写命令 `sync-data-center-sql`。

## 已验证生产证据

2026-07-14 使用 `分触达时间段--抖音咨询`（`menu_set_3861085202969292800`）完成同 Hash 无差异刷新演练：

- 计划与保存后回读 SQL SHA-256 均为 `4e548fe6e06f5b10ab84992a8649f10467035853d166cf6117d87aa552f987d0`。
- 预览返回 44 列、100 行可见结果；保存响应成功。
- 基线最新执行记录为 `158865162`；新记录 `158865443` 于 `2026-07-14 20:22:58` 开始、`20:23:10` 结束，状态 `SUCCESS`。
- Apply 总耗时约 42.4 秒；成功 receipt 位于 operator runtime 的 `data-center/replacement` 目录。
