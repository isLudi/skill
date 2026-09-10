---
name: qingcheng-dashboard-sql
description: Resolve 青橙项目部 metrics and contracts; generate, review or repair governed SQL and dashboard designs. Use for explicit qingcheng requests or its registered artifacts, including authorized knowledge maintenance; do not infer another department's semantics.
---

# 青橙项目部 SQL 与契约

本 Skill 负责 `qingcheng` 业务语义、QuerySpec / QueryPlan、SQL 和看板设计。执行、下载、平台修改交给 `usql-web-query-operator`；本 Skill 不操作浏览器或 Excel。“顾问”可能指线索分配顾问或业绩归属顾问；上下文不能唯一确定时必须消歧。

## 按任务读取

先用 `metadata.json` 确认领域，再按问题定位 `semantic/generated/contract_index.json` 中的 ID / 别名。读取命中的 `semantic/contracts/*.json` 及其 `source_path`，核对状态、哈希、范围和粒度。需要候选实体时查 `semantic/domain_manifest.json`；没有命中或发现冲突时，才扩展到 `knowledge/decision_tree.md`、相关反向索引、表或历史 SQL。已有充分证据时停止扩大阅读，不重复遍历整套目录。

| 任务 | 读取内容 |
|---|---|
| 生成、修复、审核生产 SQL / QueryPlan | [查询约束](references/query_governance.md)、命中的 contract 与源文档；只执行适用规则 |
| 新增 SQL、修改 SQL 或判断验证范围 | [SQL 质量验证](references/sql_quality.md) |
| 看板设计、diff、dry-run、字段反查 | [看板设计工作流](knowledge/sql_patterns/dashboard_design_change_workflow.md)；实际能力以 operator registry 为准 |
| 知识入库、contract、schema / canonical SQL / Web profile 同步 | [知识维护](references/knowledge_maintenance.md)；需明确维护授权 |
| 执行、权限或平台错误 | 交给 operator 的对应操作 reference；失败回到原 QuerySpec，不切换领域 |
| 将已确认的数据按渠道推送到群、图片/文案、@提醒与本地调度 | 交给 [data-push](../data-push/SKILL.md) 的 `qingcheng` 渠道适配器；未配置时先登记，不套用市场顾问部期次或指标 |

## 必要边界

- 域未知时不套用本域语义；不同部门同名指标不能互相补齐。跨部门比较分别构造 QuerySpec，再在兼容粒度聚合。
- QuerySpec 明确 intent、metrics、dimensions、filters、business_scope、time_range、计算/输出粒度、candidate_tables、join_path、evidence 与 unresolved_slots。证据只来自本域或共享中性物理 schema。
- 只有源哈希有效的 confirmed contracts 可进入生产 QueryPlan。required unresolved / pending / ambiguous 槽位不得手工删除或标成 executable。confirmed 不代表可以自动编译，后者还需 `automatic_compile=true` 与当前编译器支持。
- 通过 `scripts/text2sql.py` 构造并校验 QuerySpec/QueryPlan；复杂 SQL 按已确认语义和源 SQL 审阅，不能伪装成单表自动编译。SQL 经 AST 与 `scripts/validate_sql_rules.py` 校验后，operator 才能接收精确 Hash 匹配的 executable Plan。
- 默认目标为 Presto。公司平台的三参数 `date_add` 解析有差异，使用 interval 日期偏移。物理表使用完整库名，保留每个物理扫描必要的 `dt` / `hour`、业务范围和探索 limit；不编造缺失字段或范围值。
- 保留计算粒度与输出粒度、Join 基数、去重、NULL 和分子/分母语义；优化不得靠删行、改变业务范围或粒度提速。
- QueryPlan、设计工件、Probe 或本地验证都不构成执行、下载、生产修改、发布或知识写回授权。看板 Apply / Publish 由 operator 的独立阶段完成。

## 交付与维护

按用户问题简洁说明关键口径、具体时间/分区/范围、执行状态和未决风险；附 SQL/Plan/证据路径，需要时列出 Query ID。完整字段、lineage、contracts 和验证证据留在工件中，不要求每次回复展开固定长清单。静态验证与实际查询结果分开报告。

读取和写入使用 UTF-8；发现乱码先重读，不据此推断业务。维护检查按 [仓库验证规则](../references/maintenance-verification.md) 选择，不重复运行已被成功完整检查覆盖的子集。机器可执行契约、知识 Hash 与生产门禁保持有效。
