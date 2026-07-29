# 市场顾问 P2/P3 Text2SQL 决策树

## A. 先判定业务域

1. 请求是否明确属于市场顾问部，或已知看板/指标/SQL 是否在 `semantic/domain_manifest.json` 注册为 `market_consultant`？
   - 是：继续。
   - 否且明确属于青橙：停止本 Skill，切换 `qingcheng-dashboard-sql`。
   - 无法确定：保持 `domain: unresolved`，只允许查看中性物理目录；不得加载本域指标或范围。

## B. 解析语义实体

1. 先查 `semantic/generated/contract_index.json` 的 ID、name 和 aliases。
2. 命中唯一 contract：读取对应 `semantic/contracts/*.json` 和 `source_path`。
3. 同 kind 命中多个最高候选：返回 `ambiguous`，让用户明确人数/科目人次、当期/截面、字段或范围。
4. 未命中：查 `semantic/domain_manifest.json` 和 `knowledge/reverse_index/`，再定向读取 `knowledge/decision_tree.md` 路由出的业务文档。
5. 仍无证据：返回 `unknown` 或建立待维护项；本次不得生成生产 SQL。

## C. 检查 contract 状态

1. 指标或维度为 `pending_confirmation`？
   - 是：把 contract ID 和待确认原因写入 `unresolved_slots`；可生成物理 Probe，不可生成可执行计划。
2. Join 为 `pending_confirmation`？
   - 是：优先生成 duplicates / join-cardinality Probe；验证结果供人工判断，不自动改成 confirmed。
3. Scope 为 `pending_confirmation`，或用户给出的范围与 confirmed Scope 不一致？
   - 是：要求用户确认业务范围；不可静默扩大或替换。

## D. 构建 QuerySpec

依次回答：

1. 指标 contract ID 和证据是什么？
2. 维度字段是否 confirmed 且在指标允许维度中？
3. 时间字段和区间是什么？
4. 市场顾问部门/期次/渠道范围是什么？
5. 指标计算粒度和最终输出粒度是否一致？
6. 候选表是否有共同基础表？
7. 是否需要 Join；Join key、去重和基数是否已确认？
8. evidence 是否全部位于本 Skill？
9. `unresolved_slots` 是否为空？

任一答案缺失时，QuerySpec 不可执行。

## E. 选择 QueryPlan 或 Probe

- 语义明确、contracts 全部 confirmed、范围/时间/粒度齐全：构建 QueryPlan。
- 表是否有最新分区未知：生成 freshness Probe。
- 实际范围取值未知：生成 distribution Probe。
- 主键/Join 唯一性未知：生成 duplicates 或 join-cardinality Probe。
- Probe 结束后仍需回到 contract 和 QuerySpec 门禁；Probe 本身不授权生产编译。

## F. 编译和校验

1. QueryPlan 是否 `status = executable` 且 `unresolved_slots = []`？
   - 否：停止编译。
2. 是否属于单基础表、已注册公式和已确认维度？
   - 是：允许确定性 compile。
   - 否：按 QueryPlan 定向读取历史业务 SQL/模式生成受控 SQL，并明确当前不是自动编译覆盖范围。
3. 运行 Presto AST、QuerySpec/QueryPlan 域边界和 `scripts/validate_sql_rules.py` 校验。
4. SQL 哈希与 QueryPlan 一致后，才可交给 `usql-web-query-operator`。
5. operator 默认只预览；下载仍受 1000 行门禁与显式授权约束。

## G. 看板数据集设计

- 从可执行 QueryPlan 派生 `DashboardDatasetSpec`，声明字段、类型、粒度、聚合方式、分子/分母和筛选能力。
- 每个字段继续保留本域 contract ID 与 `source_path`，不从青橙 Skill 补充口径。

## H. P3 看板设计与受控变更

1. 是否已有最新 `DashboardProfile`，且 dashboard/draft identity 与 profile hash 明确？
   - 否：先运行 operator 的 `profile-edit-dashboard`。
2. 是否能从 QueryPlan/DatasetSpec 和市场顾问 confirmed contracts 构建 `DashboardDesignSpec`？
   - 否：保留 unresolved/ambiguous，不生成可 Apply 计划。
3. 运行 `design-dashboard -> plan-dashboard-change`；component、layout、formula、filter 均可生成 diff，dry-run 不调用写接口。
4. ChangePlan 是否只包含 stable-ID `update_filter_dynamic_default`，且 `relation_id + filter_id + field_id` 完整？
   - 是：用户显式授权后可交 `apply-dashboard-change` 写 draft。
   - 否：标记 `blocked_unsupported`；任一 blocked operation 使整次 Apply 零写入。
5. Apply 后重新 profile 并生成 `DashboardApplyReceipt`。发布必须另用 `publish-dashboard-change --confirm-publish`，校验成功 receipt 和最新草稿 profile hash。
6. 组件/字段/公式反查按 `live profile -> contract_index -> market_consultant contract -> source_path/raw SQL`；unknown、ambiguous 或青橙依赖不得静默补齐。

详细规则只在看板设计/编辑场景读取 `knowledge/sql_patterns/dashboard_design_change_workflow.md`。本 Skill 不保存登录态、不调用写接口。
