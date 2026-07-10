# SQL取数错误处理

验证时间：2026-06-06，使用 `scripts/usql_web_query.py run` 验证。

## 必须遵守的响应流程

当运行结果返回 `ok=false` 时，修改 SQL 前必须先读取 `error_details`。

读取顺序：

1. `error_details.detail`
2. `error_details.raw_snippet`
3. `error_details.title`

不要盲目重跑同一段 SQL。应根据捕获到的平台错误修复 SQL，然后再重跑。

如果 summary 中存在以下字段，也要优先读取：

1. `error_category`
2. `error_category_label`
3. `repair_guidance`

这些字段是脚本最后一层错误分类，应优先于根据页面状态做临时猜测。

## 最终错误分类

| `error_category` | `error_category_label` | 含义 | 必要处理 |
|---|---|---|---|
| `immediate_platform_error` | `即时错误` | 页面在可靠创建查询历史行之前就拒绝了 SQL，通常来自右上角 notification/message/alert。 | 立即停止重复运行。先根据弹窗文本修复 SQL，再重跑。 |
| `query_log_error` | `日志区错误` | 查询任务已经创建，失败信息在查询历史/日志区。 | 打开日志，依据 `VALIDATE_SQL_ERROR`、行列号、表名、字段名或运行时错误文本修复后再重跑。 |
| `other_platform_error` | `其他平台错误` | 页面暴露了错误，但不匹配上面两类主要已验证路径。 | 保留原始文本，先检查页面状态或 debug artifact，再决定是否修改业务逻辑。 |

## 错误来源

| source | 含义 | 典型下一步 |
|---|---|---|
| `notification` / `message` / `alert` | 平台在提交前或提交中拒绝 SQL，可能没有 query id。 | 读取 notification 明细，先修复本地 SQL 规则。 |
| `log_area` | 查询历史行已创建，执行日志中包含失败原因。 | 使用日志明细，尤其是 `VALIDATE_SQL_ERROR`、行列号、表名和字段名。 |
| `none` | 未找到可靠的平台错误文本。 | 按自动化或页面状态问题处理；修改 SQL 逻辑前，先用 `--debug-artifacts` 重跑。 |

## 已验证案例

| 案例 | 观察到的状态 | 来源 | 修复规则 |
|---|---|---|---|
| 缺少部门/范围边界 | `Failed` | `notification` -> `immediate_platform_error` | 根据 SQL skill 规则补齐必要的部门或架构过滤；如果用户没有给值，用占位符，不要编造。不要在 SQL 未修改时继续点击运行。 |
| 无效字段 | `Failed` | `log_area` -> `query_log_error` | 读取 `VALIDATE_SQL_ERROR(code=1017)` 明细，然后查表文档/schema，替换或删除错误字段。 |
| Presto 语法错误 | `Failed` | `notification` -> `immediate_platform_error` | 根据平台提示的行列位置修复 Presto 语法后再重试。 |
| 无查询权限 / 未知表 | `Failed` | `notification` -> `immediate_platform_error` | 不要解释成“数据为空”。改用可读表、缩小到已知有权限的表，或让用户确认权限/表可用性。 |
| 查询任务创建后的类型/cast/join 不匹配 | `Failed` | `log_area` -> `query_log_error` | 读取日志里的 cast、类型、join mismatch 等文本，修复字段类型转换、聚合粒度或 join key 后再重跑。 |

## 修复建议使用规则

当 JSON summary 中存在 `repair_guidance` 时，直接优先使用它。

对于 `即时错误`：

- 优先怀疑缺少部门/架构范围过滤、权限范围不满足，或提交阶段语法问题。
- SQL 在稳定查询行创建前已被拒绝，反复重试只会浪费时间和资源。
- 先修 SQL，再重跑一次。

对于 `日志区错误`：

- 平台已经接受提交并创建查询任务。
- 下一步是读日志，不是只凭 SQL 文本猜。
- 优先处理 `VALIDATE_SQL_ERROR`、行列号、缺失字段/表、类型转换、运行时 join/聚合问题。

编码说明：部分中文平台 notification 在 Playwright 文本提取中可能出现 mojibake。仍要保留 raw snippet，因为其中通常还能保留表名、字段名和 SQL 文本；notification 的标题/source 足以把运行分类为 `Failed`。

## 非错误发现

测试中，网页平台并不总是稳定拦截缺失 `dt`/`hour` 过滤的 SQL。这不代表可以放松 SQL 生成规则：运行前仍必须校验分区和必要范围过滤。

## 下载规则

只有 `status=Success` 后才能使用 `--download`。脚本会执行本地下载安全策略：SQL 必须明显包含 `LIMIT 1000` 或更低限制，或者结果页能证明输出不超过 1000 行。

如果本次使用了 `run --query-plan`，下载还必须同时满足 QueryPlan 的 `execution_policy.allow_download=true`。QueryPlan 允许下载不代表可以绕过本地 1000 行策略；任一门禁不通过都必须停止下载。契约校验本身发生在浏览器启动前，相关失败应回到上游业务 SQL skill 修正计划或 SQL，不应按平台 SQL 错误重试。
