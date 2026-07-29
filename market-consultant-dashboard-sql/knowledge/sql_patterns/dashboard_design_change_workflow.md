# 市场顾问 P3 看板设计与受控变更工作流

> 仅用于 `domain=market_consultant` 的看板设计、差异分析和受控变更路由。指标、维度、范围和公式语义仍以本 Skill 的市场顾问契约及其 `source_path` 为准。

## 1. 域与证据门禁

- `DashboardDesignSpec.domain` 必须为 `market_consultant`。
- 每个指标、维度、范围和公式依赖都必须记录本域 `confirmed` contract ID 与 `source_path`；指标 ID 必须以 `market_consultant:metric:` 开头，维度和范围同理使用 `market_consultant:` 前缀。
- DesignSpec 只引用当前 `QueryPlan`、`DashboardDatasetSpec` 和命中契约已经证明的语义；不得从青橙 Skill 借用同名指标、渠道、期次、顾问、范围或公式。
- Profile 必须为 `completeness.status=complete`，DatasetSpec 必须为 `status=ready` 并绑定 QueryPlan/DatasetSpec Hash；其中 contract-backed 字段、范围和筛选器必须保留 `confirmed`、`source_domain=market_consultant`、`source_path` 与 `source_sha256`。
- Design gate 必须回查真实市场顾问 ContractRegistry、源文件 SHA-256 与本 Skill 的 `dashboard_registry`；未注册、Hash 过期或跨域 dashboard 只允许只读画像，先同步 Web BI profile 并重建 catalog。
- 任一 contract 为 `pending_confirmation`、别名歧义、来源哈希漂移、字段无法反查或 profile 域不明时，只允许画像和 diff，禁止形成可 apply 的变更计划。
- 布局本身可以复用通用设计原则，但组件绑定的字段、指标、公式和筛选器必须通过市场顾问证据门禁。

## 2. 正向链路

```text
QuerySpec(market_consultant) -> QueryPlan -> DashboardDatasetSpec
  -> profile-edit-dashboard -> design-dashboard
  -> plan-dashboard-change（DashboardChangePlan + dry-run）
  -> apply-dashboard-change（仅 P3B 白名单，写 draft）
  -> DashboardApplyReceipt + 回读 profile
  -> publish-dashboard-change --confirm-publish
```

构建 `DashboardDesignSpec` 时至少保留：

- `domain`、目标 dashboard/draft identity、基线 `DashboardProfile` hash。
- `query_plan_sha256`、`dataset_spec_sha256` 和 `profile_sha256`；后续按 `design_sha256 -> change_plan_sha256 -> apply_receipt_sha256 -> publish_receipt_sha256` 逐级绑定，任一前序 hash 漂移都必须重新规划。
- 每个组件的稳定 identity、类型、数据集、字段、聚合、排序和显示要求。
- 指标/维度/范围 contract ID、`source_path`、组件公式依赖和筛选器字段依赖。
- 布局位置与尺寸、期望筛选器关系，以及无法确定的槽位。

## 3. P3A：全类型设计、Diff 与 Dry-run

P3A 可对以下对象做只读画像、目标设计、结构化 diff 和 dry-run：

- component：组件类型、字段绑定、排序、分页和显示配置。
- layout：父容器、位置、尺寸、顺序和碰撞检查。
- formula：组件局部公式、依赖指标、聚合语义和影响范围。
- filter：公共筛选器、字段绑定、关系和动态默认项。

P3A 不调用写接口。Dry-run 必须基于最新 profile，输出 before/after、风险、阻断项和拟议 payload；profile hash 漂移时重新画像并重新 diff。

所有 P3 工件默认 `apply_authorized=false` 且 `publish=false`；生成或校验成功不改变授权状态。

## 4. P3B：当前 Apply 白名单

当前允许交给 operator Apply 的九类窄变更是：

- `update_component_fields`：稳定 `component_id + unit_id + field_group + field_id` 的一个既有字段显示名。
- `update_component_filter_label`：稳定 `unit_id + field_id` 的一个既有局部筛选器显示标签。
- `update_component_title`：一个稳定既有组件的非空标题；数据组件保持 schema 与 unit 名称一致。
- `update_public_filter_title`：稳定 `relation_id + filter_id + field_id` 的一个公共筛选器标题。
- `update_tab_label`：稳定 `component_id + slot_key + slot_id` 的一个既有 Tab 标签。
- `update_layout`：同容器/Tab 内既有节点的 `x/y/w/h`，通过边界与碰撞校验。
- `update_formula`：一个既有、组件内、非共享公式的表达式，依赖不变。
- `update_filter_dynamic_default`：稳定 `relation_id + filter_id + field_id` 的显式动态默认项。
- `update_theme`：看板根节点的显式 `#RRGGBB` 背景色。

以下对象即使已完成 DesignSpec、diff 和 dry-run，也必须标为 `blocked_unsupported`，不得写入：

- component 新建、删除、克隆、换类型、字段增删/排序、数据集/公式/筛选器绑定或任意展示配置修改。
- layout 跨容器/Tab 移动、z 轴或未通过边界/碰撞校验的调整。
- formula 新建、删除、共享/跨组件修改、依赖变化或组件公式切换。
- dataset 新建、替换、重绑或 SQL 变更。
- filter 新建、删除、字段/目标重绑、条件/值修改或关系重构；泛化 `update_component_filter` 继续阻断。
- Tab 插槽增删、排序、成员、容器配置、样式或布局修改。

Apply 只能写 draft，且必须由 `usql-web-query-operator` 按其当前 `--help` 与 allowlist 执行。ChangePlan 含任一 blocked operation 时整次 Apply 必须零写入，不得只执行其中白名单子集。本 Skill 不保存登录态、不调用看板写接口，也不把 QueryPlan、DesignSpec 或 ChangePlan 当作写入授权。发布必须通过独立的 `publish-dashboard-change --confirm-publish`，并由 operator 校验成功的 `DashboardApplyReceipt` 与最新 draft profile hash。

## 5. 反向链路

从现有看板追溯口径时按以下顺序读取：

```text
live DashboardProfile
  -> dashboard/component/model/relation/filter/field identity
  -> 组件字段与公式依赖
  -> semantic/generated/contract_index.json
  -> 本域 semantic/contracts/*.json
  -> contract.source_path
  -> 市场顾问 dashboard/metric/table/join 文档或 retained raw SQL
```

- 先用 `knowledge/dashboard_web_profiles/` 确认组件和模型，再用 `knowledge/metrics/market_consultant_dashboard_metric_formula_linkage.md` 连接前端公式与数据中心 SQL。
- 反向解析必须产出唯一市场顾问 contract ID；无法唯一映射时保留 `unknown/ambiguous`，不得根据字段显示名猜测。
- Profile 中若出现青橙来源或未知业务域，只能记录为外部/未决依赖；不得写入市场顾问 DesignSpec 的业务语义引用。

## 6. 职责边界

- 本 Skill：解析市场顾问业务语义，生成域内 contract/source 引用和设计约束。
- 共享 Text2SQL Core：校验 DashboardProfile、DashboardDesignSpec、DashboardChangePlan 和 receipt 的结构、hash 与策略。
- `usql-web-query-operator`：独占浏览器登录态、profile、dry-run、白名单 Apply、回读和发布确认。
