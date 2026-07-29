# 市场顾问 P2/P3 Text2SQL 语义与看板设计速查

## 1. 边界

- 固定业务域：`market_consultant`。
- 只从本 Skill 的 `semantic/`、`knowledge/` 和 `resources/raw_sql/` 取业务语义证据。
- `_shared/text2sql_core/catalog/physical_catalog.json` 只提供中性物理字段事实，不能补充指标、部门范围、渠道映射、临时表或业务 Join。
- 青橙请求、青橙指标或无法确定业务域的请求不得进入本域 QueryPlan。

## 2. 渐进披露顺序

按以下层级逐步读取，命中后停止扩展无关上下文：

1. `metadata.json` 与 `SKILL.md`：确认域、能力和硬门禁。
2. `semantic/domain_manifest.json`：定位候选实体及其证据路径。
3. `semantic/generated/contract_index.json`：按 ID、名称和别名定位候选 contract；该文件是生成索引，不是业务事实来源。
4. 本文件与 `references/decision_tree.md`：选择 resolve、plan、compile 或 probe 路径。
5. `semantic/contracts/*.json`：读取命中的指标、维度、Join 和 Scope contract。
6. contract 的 `source_path` 以及相关 `knowledge/decision_tree.md`、反向索引和业务文档：核验公式、粒度、范围和风险。
7. 只有需要追溯复杂 CASE、CTE 或历史实现时才读取对应 Raw SQL。

不要先全量加载全部 Markdown 或 Raw SQL。

## 3. Contract 状态门禁

| 状态 | 允许动作 | 禁止动作 |
|---|---|---|
| `confirmed` | 写入 QuerySpec；证据、范围和粒度均满足后构建 QueryPlan | 不得把 confirmed 等同于自动编译许可；还须检查 `automatic_compile` |
| `pending_confirmation` | 展示候选、读取源文档、生成只读物理探查 SQL、向用户确认 | 不得进入可执行 QueryPlan，不得编译生产 SQL |
| alias `ambiguous` | 返回候选 contract ID 和差异，要求消歧 | 不得按最高相似度静默选择 |
| alias `unknown` | 回到 domain manifest、反向索引和目标文档继续取证 | 不得编造 contract 或借用青橙定义 |

`confirmed` 只表示当前 contract 的公式或字段已由引用证据明确记录。时间、部门范围、计算粒度、输出粒度、Join 基数仍必须在当前 QuerySpec 中显式满足。

## 4. 受控流水线

```text
domain_manifest
  -> generated/contract_index
  -> alias resolution
  -> targeted source evidence
  -> QuerySpec
  -> QueryPlan
  -> compile OR probe
  -> AST + platform rules
  -> optional USQL execution
```

常用入口以 `scripts/text2sql.py --help` 为准：

```powershell
D:\anaconda3\python.exe scripts\text2sql.py resolve --query '<业务问题>'
D:\anaconda3\python.exe scripts\text2sql.py validate-spec --spec '<query-spec.json>'
D:\anaconda3\python.exe scripts\text2sql.py plan --spec '<query-spec.json>' --output '<query-plan.json>'
D:\anaconda3\python.exe scripts\text2sql.py compile --spec '<query-spec.json>' --sql-output '<query.sql>' --plan-output '<query-plan.json>'
D:\anaconda3\python.exe scripts\text2sql.py probe --kind freshness --table '<db.table>' --start-value '<YYYYMMDD>' --end-value '<YYYYMMDD>'
D:\anaconda3\python.exe scripts\text2sql.py dataset-spec --plan '<query-plan.json>' --output '<dashboard-dataset-spec.json>'
D:\anaconda3\python.exe scripts\text2sql.py evaluate
```

`compile` 从 QuerySpec 重新构建并校验 QueryPlan；不要把手工改写的 plan 当作绕过 contract 门禁的编译入口。

### QuerySpec

必须明确：

- `schema_version: 2.0.0`
- `domain: market_consultant`
- contract 化的 metrics、dimensions、business scope
- 时间范围、过滤条件、计算粒度、输出粒度
- 候选表、Join path、域内 evidence
- `unresolved_slots`

只要存在 `pending_confirmation`、歧义、缺范围、缺时间、缺粒度或未验证 Join，必须写入 `unresolved_slots`。

### QueryPlan

QueryPlan 只能由已验证 QuerySpec 和 confirmed contracts 生成。可执行计划必须同时满足：

- `status = executable`
- `unresolved_slots = []`
- 所有 evidence 属于本 Skill
- base table、维度和指标存在兼容交集
- 必填 Scope 已转为具体过滤条件
- Join contract 已确认且基数风险已处理
- `execution_policy` 明确预览和下载边界

### Compile

- 只编译 `executable` QueryPlan。
- P2 默认只编译 `automatic_compile=true`、单一基础表上的已注册指标和维度。
- 需要复杂多表 Join、长 CASE 或历史看板 CTE 时，使用 QueryPlan 约束后从目标业务文档/Raw SQL 生成，再做 AST 与平台规则校验；不得把未支持结构伪装成自动编译成功。
- 编译后保存 SQL SHA-256；交给 operator 时 SQL 文本必须与 QueryPlan 哈希一致。

### Probe

Probe 只用于验证物理事实，不用于决定业务指标语义。支持的只读探查包括：

- `freshness`：分区新鲜度和行数。
- `distribution`：字段真实取值分布。
- `duplicates`：候选键重复。
- `join-cardinality`：未匹配键和预计行数放大。

Probe 必须带具体分区范围，结果默认有界；不得把 Probe 的统计结果自动写回 confirmed contract。

## 5. 当前市场域种子能力

- 已确认：截面/当期/跨期转化人数和科目人次、24 小时外呼率、首 call 任务率。
- 待确认：抖音私域合并线索/有效线索、`channel_map` 别名等价、当前虚拟架构历史回溯、地域归属以及若干多对多风险 Join。
- 详细清单以 `semantic/generated/contract_index.json` 为路由入口，以 `semantic/contracts/*.json` 和各自 `source_path` 为证据。

## 6. P3 看板设计与变更

正向链路：

```text
QuerySpec -> QueryPlan -> DashboardDatasetSpec -> DashboardDesignSpec
  -> DashboardChangePlan -> dry-run -> draft apply -> separate publish confirmation
```

- `DashboardDesignSpec.domain` 固定为 `market_consultant`；每个指标、维度、范围和公式依赖必须引用本域 `confirmed` contract ID 与 `source_path`，并绑定 QueryPlan/DatasetSpec/Profile hash。
- component、layout、formula、filter 均可 profile、设计、diff 和 dry-run；P3A 不写平台。
- P3B 仅允许 operator Registry 的九类窄 Apply：字段显示名、局部筛选标签、组件标题、公共筛选标题、Tab 标签、同容器布局、依赖不变公式、公共筛选动态默认项和根背景色；每项必须使用对应稳定 ID，任一 blocked operation 使整份计划零写入。
- 超出九类窄边界的组件字段/标题、局部或公共筛选器、Tab、布局、公式、主题，以及数据集重绑、新建或删除均保留 diff，但必须 `blocked_unsupported`。
- 命令链为 `profile-edit-dashboard -> design-dashboard -> plan-dashboard-change -> apply-dashboard-change -> publish-dashboard-change`。Apply 只写 draft；Publish 消费成功 ApplyReceipt、要求 `--confirm-publish` 并校验草稿 profile hash。
- 反向路由固定为 `live profile -> component/model/filter/field/formula -> contract_index -> market_consultant contract -> source_path/raw SQL`；无法唯一映射或跨域时停止。
- 完整细节按需读取 `knowledge/sql_patterns/dashboard_design_change_workflow.md`；普通 Text2SQL 不加载。

## 7. 维护与自检

业务知识变化后按顺序运行：

1. `scripts/build_reverse_indexes.py`
2. 仓库级 `../scripts/build_text2sql_catalog.py`
3. `scripts/check_skill_integrity.py`
4. 仓库级 `../scripts/validate_text2sql_stack.py`

`semantic/generated/contract_index.json` 是确定性生成物，不手工编辑。contract 的 `source_sha256` 失效时必须重新核对来源后更新，不能只刷新哈希掩盖业务变化。
