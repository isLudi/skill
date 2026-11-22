# Taitan 看板 P3A/P4B 变更工作流

本文件描述独立的 `profile → design spec → diff/dry-run → apply draft → publish confirmation` 安全链路。只有处理看板设计或变更任务时读取；普通 SQL 执行、下载或只读看板浏览不需要加载本文件。

本链路只处理既有对象。若目标是从零创建唯一命名的新看板，必须改用 `references/dashboard_build_workflow.md` 的 P4C 创建 Saga；禁止把创建 operation 塞入 `DashboardChangePlan`。

## 目录

1. [能力边界](#能力边界)
2. [Artifact 与 Hash 绑定](#artifact-与-hash-绑定)
3. [P3A：画像、设计和 dry-run](#p3a画像设计和-dry-run)
4. [P4B：草稿 Apply](#p4b草稿-apply)
5. [独立发布确认](#独立发布确认)
6. [公共筛选器稳定定位](#公共筛选器稳定定位)
7. [受支持与阻断的操作](#受支持与阻断的操作)
8. [透视表字段同步与沙箱复制重建](#透视表字段同步与沙箱复制重建)
   - [在既有看板底部追加同模型透视表](#在既有看板底部追加同模型透视表)
9. [故障与恢复](#故障与恢复)
10. [Legacy 兼容命令](#legacy-兼容命令)

## 能力边界

- `profile-edit-dashboard` 只调用读取接口。
- `design-dashboard` 和 `plan-dashboard-change` 是纯本地命令，`write_calls=0`。
- `DashboardProfile`、`DashboardDesignSpec`、`DashboardChangePlan` 都不是写入授权。
- `apply-dashboard-change` 只能修改草稿，命令没有发布参数。
- `publish-dashboard-change` 是独立命令，必须显式传入 `--confirm-publish`。
- QueryPlan、DatasetSpec、DesignSpec 或 ChangePlan 不能授予发布权限。
- 看板变更必须绑定 `market_consultant` 或 `qingcheng`；`unresolved` 画像只能用于调查，不能进入 DesignSpec、Apply 或 Publish。
- operator 不推断业务指标。指标公式和筛选器语义必须来自已选择业务 skill 的域内证据。

## Artifact 与 Hash 绑定

| Artifact | 关键绑定 | 是否授权写入 |
|---|---|---:|
| `DashboardProfile` | `domain + dashboard_id + draft state` | 否 |
| `DashboardDesignSpec` | `source_profile_sha256 + dataset_spec_sha256 + query_plan_sha256` | 否 |
| `DashboardChangePlan` | `base_profile_sha256 + design_sha256` | 否，仅 dry-run |
| `DashboardApplyReceipt` | `change_plan_sha256 + pre/post profile hash` | 否，不授予发布 |
| `DashboardPublishReceipt` | `apply_receipt_sha256 + pre-publish profile hash + confirmation` | 发布后的审计凭证 |

Hash 使用规范 JSON 的 SHA-256。每个 Artifact 计算 Hash 时只排除自身的 Hash 字段，保留所有上游 Hash 绑定。

## P3A：画像、设计和 dry-run

### 1. 画像

```powershell
D:\anaconda3\python.exe scripts\read_dashboard.py profile-edit-dashboard `
  --dashboard-id dashboard_123 `
  --domain qingcheng `
  --output C:\runtime\dashboard_123.rich_profile.json `
  --normalized-output C:\runtime\dashboard_123.dashboard_profile.json
```

主 `--output` 保持向后兼容，继续包含 `pivot_units`、`dataset_fields`、`text_notes` 和字段详情；同时增加覆盖 `card/u_pivot/u_bar/u_pie` 的 `data_units`、`domain`、规范快照、`profile_sha256` 和嵌套 `normalized_profile`。`pivot_units` 是透视表兼容视图，`--normalized-output` 可额外写出纯 DashboardProfile Artifact。

`profile_sha256` 只覆盖组件、布局、公式、筛选器、数据集和完整性等可编辑状态。Taitan 每次打开可能重发的 `html_id` 保留为导航元数据但不参与 Hash；否则同一配置会产生伪漂移。Apply/Publish 仍必须使用最新 profile 中的 `html_id` 打开页面，并以完整状态 Hash 做前置校验。

画像必须 `completeness.status=complete` 才能进入后续链路。除接口抓取成功外，完整性还要求每个已配置 pivot 能稳定解析到 unit、component 和 model/dataset identity，组件引用的 selected field、formula、component-filter 均有对应对象，dataset 存在且保留 unit/component 反向引用；启用字段树抓取时，已选字段和公式依赖还必须存在于对应 subject。空白容器、文本和其他非数据组件不参与 pivot 绑定门禁。任一抓取或绑定失败时，rich artifact 仍会保存 `binding_validation` 和错误证据，但命令返回非零；Design、Apply 和 Publish 全部拒绝不完整画像。

规范快照包含：

- 组件稳定 `component_id/node_id`、`unit_id`、父容器和 Tab 路径，以及真实已选维度/指标、formula IDs、component-filter IDs 和 dataset/model identity。
- `x/y/w/h` 等布局。
- 公式 ID、表达式、依赖和影响组件。
- 公共筛选器的 `relation_id + filter_id + field_id`。
- `dynamic_default` 以及平台实际字段 `dynamics_filter`、`dynamics_filter_value`、`auto_search_default_value`。
- 根主题的 `background_color + theme_type + style_id`；P4B 只允许修改 `background_color`。
- `binding_validation`：逐项记录 pivot、dataset、selected field、formula、component-filter 的绑定计数和悬空引用错误；它属于只读证据，不授予写入权限。

### 2. 生成 DesignSpec

```powershell
D:\anaconda3\python.exe scripts\read_dashboard.py design-dashboard `
  --profile C:\runtime\dashboard_123.rich_profile.json `
  --dataset-spec C:\runtime\dashboard_dataset_spec.json `
  --desired-state C:\runtime\desired_dashboard_state.json `
  --domain qingcheng `
  --query-plan-sha256 <64-hex> `
  --output C:\runtime\dashboard_design_spec.json
```

`desired-state` 可包含 `components`、`layout`、`formulas`、`public_filters`、`component_filters`、`theme`。提供某个集合时，它表示该集合的完整目标状态，不是局部 patch；缺项可能被解释为删除并被 P4B 阻断。组件内筛选器目前只支持 P3A Diff，不能 Apply。

DesignSpec 只接受 `status=ready` 且带 canonical `query_plan_sha256/dataset_spec_sha256` 的 DatasetSpec。所有 contract-backed field、scope 和 filter evidence 必须为本域 `confirmed` contract，并携带本域 `source_domain`、相对 `source_path` 和 `source_sha256`；缺失、pending 或跨域证据会生成 blocked DesignSpec，命令返回非零。

Design gate 还会用两个业务 Skill 的 domain manifest 回查 `dashboard_id`。只有已同步到当前业务 Skill 的 Web BI profile 目录、证据文件 Hash 仍一致且未出现在另一业务域的 dashboard 才能进入 ready；未注册看板先执行只读画像并按知识维护流程写入正确业务 Skill、重建 catalog，不允许仅凭 `--domain` 声明进入修改链路。

公共筛选器目标状态应从规范画像复制完整列表，只修改目标三元组。动态默认项示例：

```json
{
  "public_filters": [
    {
      "filter_key": "relation_1::public_filter_1::grade",
      "filter_id": "public_filter_1",
      "relation_id": "relation_1",
      "field_id": "grade",
      "dynamics_filter": true,
      "dynamics_filter_value": "2",
      "auto_search_default_value": false
    }
  ]
}
```

### 3. Diff 与 dry-run

```powershell
D:\anaconda3\python.exe scripts\read_dashboard.py plan-dashboard-change `
  --profile C:\runtime\dashboard_123.rich_profile.json `
  --design-spec C:\runtime\dashboard_design_spec.json `
  --domain qingcheng `
  --output C:\runtime\dashboard_change_plan.json
```

该命令不启动浏览器、不调用写接口，并输出 before/after、risk、`write_status`、阻断原因和 `change_plan_sha256`。Diff 可以覆盖全部设计状态；只有满足下文窄约束的九类操作会得到 `write_status=supported`。

## P4B：草稿 Apply

```powershell
D:\anaconda3\python.exe scripts\read_dashboard.py apply-dashboard-change `
  --change-plan C:\runtime\dashboard_change_plan.json `
  --change-plan-sha256 <exact-plan-hash> `
  --domain qingcheng `
  --output C:\runtime\dashboard_apply_receipt.json
```

Apply 门禁顺序：

1. 在导入 Playwright、打开浏览器前验证 Artifact 类型、域、精确 Hash、状态和 operation allowlist。
2. 要求 `status=ready_for_dry_run` 且至少存在一个受支持 operation；`no_changes` 不允许 Apply。
3. 重读当前 draft，要求 `profile_sha256 == base_profile_sha256`；漂移时零写入停止。
4. 每个 operation 使用稳定目标 ID，并在紧邻写入前连续读取两次目标；目标 Hash 漂移时零写入停止。
5. 写后立即读取目标，证明精确目标状态；筛选器允许平台生成缓存字段，但动态默认三元组必须一致。
6. 多 operation 按 ChangePlan 固定顺序执行。平台没有服务端事务 API，因此任一步失败时停止后续写入，并按完成顺序的反向逐项补偿恢复。
7. 恢复过程也要求写前目标仍等于刚完成的 after 状态；若目标被并发编辑，不猜测覆盖，receipt 标记恢复失败并转人工检查。
8. 全部成功后再次完整画像，要求 post profile 与 ChangePlan `target_state` 精确一致；不一致也触发反向恢复。
9. 恢复完成后再次完整画像，只有回到 `base_profile_sha256` 才记录 `recovery.status=restored`。
10. 生成 `DashboardApplyReceipt`。任一 operation 未标记为 `applied`、最终目标不一致或恢复不可证明时，receipt 为失败，禁止发布。

Apply 命令不接受 `--publish`，也不会调用发布接口。

## 独立发布确认

```powershell
D:\anaconda3\python.exe scripts\read_dashboard.py publish-dashboard-change `
  --change-plan C:\runtime\dashboard_change_plan.json `
  --change-plan-sha256 <exact-plan-hash> `
  --apply-receipt C:\runtime\dashboard_apply_receipt.json `
  --apply-receipt-sha256 <exact-receipt-hash> `
  --domain qingcheng `
  --confirm-publish `
  --version-description "approved dashboard change" `
  --output C:\runtime\dashboard_publish_receipt.json
```

发布前再次验证：

- ChangePlan 和 ApplyReceipt 的精确 Hash。
- Receipt 与 ChangePlan 的绑定。
- `status=applied`、至少一个 `status=applied` operation。
- 当前 draft Hash 仍等于 ApplyReceipt 的 `post_profile_sha256`。
- `--confirm-publish` 和非空版本说明。
- 发布前连续两次完整 draft/profile 与 publish-payload Hash 一致；API 返回后再次回读完整 draft，并把 `post_publish_draft_profile_sha256` 写入 PublishReceipt。

Apply 与 Publish 不允许在同一个新流程命令中完成。

平台当前没有已验证的 ETag、事务锁或正式发布版本读取 API，因此仍存在极短的服务端并发窗口。当前链路用即时双读和 payload Hash 将窗口压缩；API 成功时 PublishReceipt 明确记录 `publish_status=publish_requested_unverified`、`verification_status=draft_only_unverified_published_version`、`fully_verified=false`。这只表示发布请求已被平台接受且 draft 回读一致，不得描述成正式发布版本内容证明。

## 公共筛选器稳定定位

P3B 不再使用“第一个/第二个筛选器”定位。每个可写 operation 必须同时提供：

- `relation_id`：公共筛选器关系 ID。
- `filter_id`：叶子筛选器 `unitId`。
- `field_id`：筛选字段 ID。

`filter_key = relation_id::filter_id::field_id` 仅用于规范 Artifact 的复合 identity。平台写入仍使用三个真实 ID。缺失、多匹配或三者任一漂移都必须停止。

## 受支持与阻断的操作

| operation | P3A Diff | P3B Apply |
|---|---:|---:|
| `update_filter_dynamic_default` | 支持 | 支持，仅稳定三元组和显式动态默认值 |
| `update_public_filter_title` | 支持 | 支持，仅稳定三元组对应的一个非空叶子标题 |
| `update_existing_component` | 支持 | `blocked_unsupported` |
| `update_component_fields` | 支持 | 支持，仅既有稳定 field ID 的单个显示名修改 |
| `replace_pivot_measure_fields` | 支持识别并保留前后有序 ID | 阻断；本地适配器未进入生产白名单，等待真实沙箱写入/回读/恢复证据 |
| `update_component_filter_label` | 支持 | 支持，仅稳定 unit/field 的局部筛选器显示标签 |
| `update_component_title` | 支持 | 支持，仅一个稳定既有组件的非空标题 |
| `update_tab_label` | 支持 | 支持，仅稳定 component/slot key/slot ID 的一个标签 |
| `update_layout` | 支持 | 支持，仅同容器/Tab 既有节点 `x/y/w/h`，通过边界与碰撞检查 |
| `update_formula` | 支持 | 支持，仅既有单组件非共享公式表达式，依赖不变 |
| `update_theme` | 支持 | 支持，仅根 `background_color=#RRGGBB` |
| 新建、删除、换类型、跨容器移动、数据集重绑 | 支持识别 | 阻断 |

共享公式、跨组件公式和任何影响范围不明的改动必须阻断。没有抓取并验证真实请求的接口，不得凭字段名猜测写 payload。

## 透视表字段同步与沙箱复制重建

### 在已有透视表中配置比例指标

`plan-pivot-ratio-draft` 核对市场顾问部的一张已有行透视表、负责人身份、模型和看板级 subject，生成精确 Plan。输入 JSON 的 `selection` 绑定 `domain`、`dashboard_id`、`dashboard_name`、`owner`、`model_id`、`subject_id`、`component_id`、`unit_id`、`unit_name`、共同 `denominator` 和有序 `ratios`。物理字段用 `field_id` 和 `field_name` 表示，每个比例有 `name` 和 `numerator`。`remove_ids`、`move_to_end_ids` 和 `anchor_id` 控制已有列；`remove_ids` 仅可指向已有计算百分比字段，不能移除物理指标。`header_color` 和 `decimals` 控制新比例的表头及百分比精度。沙箱验证所需的比例样式来自实读的待移除百分比列。仅移除透视表中的列引用。

输入的 `checks` 为同粒度的数据对账控制，每项包含 `label`、`row`、`filters`、`denominator` 和按比例顺序排列的 `numerators`。筛选项填写 `[field_id, filter_id, value]`，全量合计使用空行键及空筛选数组。请求按已经核对的筛选器及行维度执行，核对原始比率、退后线索数，并按原始比率反算分子与独立 SQL 对账。

```powershell
D:\anaconda3\python.exe scripts\read_dashboard.py plan-pivot-ratio-draft `
  --domain market_consultant --sandbox --input C:\runtime\selection.json --output C:\runtime\ratio-plan.json `
  --state-path C:\runtime\owner-state.json

D:\anaconda3\python.exe scripts\read_dashboard.py apply-pivot-ratio-draft `
  --domain market_consultant --sandbox --headed --input C:\runtime\ratio-plan.json --plan-sha256 <exact-plan-sha256> `
  --confirm-sandbox-write --output C:\runtime\ratio-receipt.json --state-path C:\runtime\owner-state.json
```

当前 `configure_pivot_ratio_fields_draft` 为 `sandbox_verified/sandbox_only`。Plan 和 Apply 均必须用明确命名的沙箱，Apply 另加 `--confirm-sandbox-write --headed`；生产 Apply 在 capability registry 门禁处阻断。适配器依据物理指标身份构造固定的 `ifnull(sum(分子)/sum(分母),0)` 计算式，回读同名现有公式的依赖和定义，冲突时停止。写入绑定完整 Profile、精确 Plan Hash、已认证的 owner、写前双读及单看板锁。保存后核对完整草稿、其他组件及发布版，失败时只在精确预期状态下补偿恢复。沙箱验证后恢复原透视表，新建的测试公式留在沙箱 subject，回执列出待复用。不得以沙箱回执自动开放生产 Apply；正式草稿支持需另行授权并完成独立验证。

### 修改草稿转化率的分母

`plan-conversion-ratio-draft` 绑定一个市场顾问部看板及其草稿 subject，确认一至三条转化率的全部共享引用都处于所选行透视表中。输入 `selection` 包含 `domain`、`dashboard_id`、`dashboard_name`、`owner`、`model_id`、`subject_id`、`targets`、`all_leads` 和 `ratios`。每个目标绑定 `component_id` 和 `unit_id`，每个比例提供 `name`、`formula_id`、`share_name`、`share_id`、`converted` 和 `qualified`。物理指标使用 `field_id` 和 `field_name`。现有占比必须等于达标量除以总量，现有转化率必须等于转化量除以总量，才允许将转化率分母换为达标量。

`checks` 每项包含 `unit_id`、`label`、`filters`、`row`、`all_leads` 和按比例顺序排列的 `counts`。每个计数是 `[converted, qualified]`。关联筛选写为 `[field_id, filter_id, value]`，空行键读取合计。保存前按独立汇总核对原始比率、分子、分母和不变的占比，保存后核对完整公式配置和发布版。

```powershell
D:\anaconda3\python.exe scripts\read_dashboard.py plan-conversion-ratio-draft `
  --domain market_consultant --sandbox --input C:\runtime\conversion-selection.json --output C:\runtime\conversion-plan.json `
  --state-path C:\runtime\owner-state.json

D:\anaconda3\python.exe scripts\read_dashboard.py apply-conversion-ratio-draft `
  --domain market_consultant --sandbox --headed --input C:\runtime\conversion-plan.json --plan-sha256 <exact-plan-sha256> `
  --confirm-sandbox-write --output C:\runtime\conversion-receipt.json --state-path C:\runtime\owner-state.json
```

当前 `change_draft_conversion_ratio_denominators` 为 `sandbox_verified/sandbox_only`。沙箱验证要求精确沙箱身份及 `--sandbox --headed --confirm-sandbox-write`，完成后恢复原公式；生产 Apply 在 capability registry 门禁处阻断。发现引用越界、数据不同期或读回失败时停止，并在精确状态下恢复已经修改的公式。不得以沙箱回执自动开放生产 Apply；正式草稿支持需另行授权并完成独立验证。

### 共享期次筛选器与日期维度重绑

`plan-period-date-rebind` 只读绑定市场顾问部既有看板、同一模型和 subject、一个公共筛选器叶子及其全部目标组件。只允许把一个文本期次字段换成同一模型的文本期次字段，并将目标透视表和折线图各自的一个文本行维度换成同一模型的真实日期字段。保留原组件 ID、布局、指标公式、其他筛选器及该筛选器的动态默认规则。原日期另有局部筛选或筛选器连接未列出的组件时，计划停止。

Selection JSON 包含 `domain`、`dashboard_id`、`dashboard_name`、`owner`、`model_id`、`subject_id`、`relation_id`、`filter_id`、`charts`、`period_from_field_id`、`period_to_field_id`、`date_to_field_id`、`period_label`、`date_label` 和 `verification_periods`。每个 `charts` 项包含 `unit_id`、`unit_type` 和 `from_field_id`。

```powershell
D:\anaconda3\python.exe scripts\read_dashboard.py plan-period-date-rebind `
  --domain market_consultant --input C:\runtime\selection.json --output C:\runtime\rebind-plan.json

D:\anaconda3\python.exe scripts\read_dashboard.py apply-period-date-rebind `
  --domain market_consultant --input C:\runtime\rebind-plan.json `
  --plan-sha256 <exact-plan-sha256> --confirm-production-write --output C:\runtime\rebind-receipt.json
```

测试看板须在 Plan 和 Apply 均声明 `--sandbox`，并在 Apply 加 `--headed --confirm-sandbox-write`。该模式执行写入、逐个回读、草稿保存、指定期次取值和恢复基线。正式模式通过 `rebind_period_and_date_dimensions_draft` 专用 capability 门禁，另要求现有域登记和已发布 schema 基线。精确 Hash、写前双读、专属写锁、写后完整画像及反序恢复适用于两种模式。若遇到第三种状态则保留备份与回执，停止自动恢复。Apply 只保存草稿。

独立专用入口 `sync-pivot-fields-draft` 可原位同步一个既有透视表，但不扩展通用 `ChangePlan` 的九类 Apply 操作。它必须以 `--manifest-sha256` 绑定审阅清单，并绑定完整目标 Profile Hash、来源/目标单元投影 Hash、稳定 unit ID 与同模型来源。执行器必须验证 capability registry 中对应操作为 `verified/allowlisted`。该命令禁止复制或替换 unit，不改 dashboard 布局或结构；组件样式仅可按注册表允许的 projection 同步。写前完整备份；写后核对目标 unit 和完整 dashboard schema Hash，并重建完整 draft profile；失败时仅在状态仍符合本次尝试时补偿恢复。新建公式若无法确认或操作失败，回执列出可能孤立资源；不自动删除。该命令没有发布参数。

专用 manifest 必须声明 `artifact_type=DashboardPivotFieldRebindManifest`、`schema_version=1.0.0`、`production_draft_sync=true`、域、目标 dashboard ID/name、`expected_profile_sha256` 和恰好一个 operation。operation 必须绑定 `operation_id`、target/source unit ID、维度 field IDs、`expected_before_sha256` 和 `expected_source_sha256`；若启用组件样式同步，还必须提供来源与目标样式 Hash。来源包含自定义公式时必须完整声明 `source_custom_formulas`，绑定来源公式 Hash；无法识别的来源字段引用会阻断执行。`--manifest-sha256` 是最终 manifest 对象按 UTF-8、键排序、无空白分隔规范化后的 SHA-256，不包含外置参数本身。

原位换列可按结果列顺序提供 `target_measure_format_ids`，每列绑定目标透视表中一个已核对的原指标 ID。适配器核对指标类型并沿用原列的数值格式和列样式，更新表头排序中的对应名称，同时回读新字段和格式。该选项用于一次原位更新，与预热写入和来源整表格式同步互斥。

取值校验支持已配置的图表内期次筛选器。`component_period_filter` 指定 `field_id`、`filter_unit_id` 和单个期次 `value`，由草稿组件实读校验绑定，响应只允许出现指定期次。每个校验选用一种筛选方式，局部筛选校验使用固定的草稿取值请求。

同次指标同步可提供 `metric_note_replacements`，在既有文本组件中替换精确的口径文字。每项绑定 `unit_id`、`before` 和 `after`，仅接受纯文本，并要求正文及编辑暂存正文各唯一命中一次。适配器沿用完整 schema Hash、精确回读及失败恢复，保留表格标记、格式和布局。

保留目标显示配置时同时保留目标行维度排序。`dimension_sort_values` 可按已选维度 ID 精确声明 `asc` 或 `desc`，用于经过审阅的排序设置或恢复。

```powershell
D:\anaconda3\python.exe scripts\read_dashboard.py sync-pivot-fields-draft `
  --target-manifest C:\runtime\pivot_sync_manifest.json `
  --dashboard-id dashboard_123 `
  --expected-dashboard-name "转化数据" `
  --domain market_consultant `
  --manifest-sha256 REPLACE_WITH_64_CHAR_MANIFEST_SHA256 `
  --confirm-production-write `
  --output C:\runtime\pivot_sync_receipt.json
```

复制重建用于在明确的沙箱/测试看板中验证“既有透视表 unit 可见字段正确、但 `value/unit` 仍走旧任务或旧绑定”的修复方式。唯一入口是 `rebind-pivot-fields-sandbox`；Registry 将 `rebuild_pivot_unit_by_copy` 固定为 `sandbox_verified/sandbox_only`。该入口只接受沙箱确认参数；生产 copy/rebind 通过专用入口也会在浏览器启动前被拒绝。该沙箱能力不能进入 P4B 生产 Apply。

沙箱命令：

```powershell
D:\anaconda3\python.exe scripts\read_dashboard.py rebind-pivot-fields-sandbox `
  --target-manifest C:\runtime\pivot_rebind_manifest.json `
  --sandbox-dashboard-id dashboard_123 `
  --expected-dashboard-name "过程数据报表-青橙-沙箱" `
  --domain qingcheng `
  --confirm-sandbox-write `
  --output C:\runtime\pivot_rebind_receipt.json
```

manifest 必须声明 `artifact_type=DashboardPivotFieldRebindManifest`、`schema_version=1.0.0`、域、目标 sandbox dashboard、可选 `expected_profile_sha256`、需要先备份的看板，以及 operations。每个 operation 绑定 `target_unit_id`、`source_unit_id`、目标维度 field IDs 和必需指标 field IDs。沙箱验证可声明 `required_public_filters` 和 `filtered_value_checks`：每个 check 携带完整 `public_filter_list` 并证明目标期次/周期筛选值。无 filter 的 `value/unit` 原始结果只能作为诊断证据，不能证明指定期次业务值。

```json
{
  "required_public_filters": [
    {
      "field_id": "qici",
      "field_name": "期次",
      "expected_values": ["20260722期"]
    }
  ],
  "filtered_value_checks": [
    {
      "check_id": "channel1_book_sec_20260722",
      "operation_id": "channel1_overall",
      "public_filter_list": [
        {
          "fieldId": "qici",
          "filterValue": ["20260722期"],
          "condition": "in"
        }
      ],
      "row_match": {
        "channel_map_1": "图书",
        "dept_2": "SEC"
      },
      "measure_field_id": "v_lead",
      "expected_value": 55
    }
  ]
}
```

若设置 `rebuild_by_copy=true`，命令按以下顺序执行：

1. 读取并保存所有指定 backup dashboard 的 draft edit config、组件 unit detail 和 published config；非沙箱看板只能作为只读备份目标。
2. 读取沙箱完整 DashboardProfile，若 manifest 绑定了 `expected_profile_sha256`，必须一致。
3. 对每个 operation 调用 `config/copy/unit` 复制 `source_unit_id`，得到新 unit ID。
4. 对新 unit 调用 `config/update/unit`，把字段重建为目标维度组合和指标组合，必要时保留目标组件的展示名与格式。
5. 批量修改 dashboardHtml 中目标组件的 `settings.unitId`，指向新 unit，并调用 `config/save/dashboardHtml` 保存 draft。
6. 读回 profile；若 manifest 提供 `filtered_value_checks`，则调用 `value/unit`，请求体必须带 `publicFilterList`，并断言指定期次/周期下的目标行和指标值。
7. receipt 记录 pre/post profile hash、备份路径、新旧 unit 映射、schema 引用验证、filtered value 验证摘要和脱敏请求 shape。

沙箱命令不会发布。若中途失败且 dashboardHtml 已保存，会尝试恢复写前 schema；已经复制出的孤立 unit 可能留在后端，但不会被组件引用。若只是 `touch_before_final=true`，命令会先写入临时字段列表再写回目标字段列表，用于测试缓存失效；但如果旧 unitId 本身绑定了旧任务，通常需要 `rebuild_by_copy=true`。任何生产透视表重绑需求都保持 `blocked_unsupported`，需先重新纳入共享 ChangePlan 治理并完成单独审查，不能复用沙箱 receipt 或 manifest 授权。

### 只同步既有透视表样式

在 `sync-pivot-fields-draft` 清单的同一 operation 内设置 `sync_component_style=true` 和 `sync_unit_fields=false`。绑定来源和目标单元、目标维度 ID、两侧单元投影及样式的精确 Hash。Apply 只保存该组件允许同步的主题与样式属性。字段投影保留期次值及动态规则，跳过平台每次读值时生成的临时取值任务 ID。

### 在既有看板底部追加同模型透视表

`plan-pivot-append` 在已登记的同域看板间生成一张透视表的草稿追加计划。绑定来源看板和单元、目标看板和网格容器、目标现有模型单元、新表标题以及当前动态默认值。当前适配器支持顶层磁吸网格、同一 SQL 应用模型、单个可见的下拉筛选器和最新一项默认值。源表使用的自定义指标须在目标主题中有唯一同名、公式与依赖等价的字段。新表继承来源显示名、顺序和数值格式，表头与行维度使用 `arco_blue` 的蓝色配置。

`apply-pivot-append` 使用 `--plan`、`--plan-sha256` 和 `--confirm-production-write`，并要求提供与计划相同的 `--dashboard-id`、`--expected-dashboard-name` 和 `--domain`。两条命令均通过 `--output` 写运行工件。以各命令的 `--help` 查看参数。

专属 capability 验证后，Apply 复核两侧完整画像、目标草稿和已发布 schema、公式映射及底部布局。分别为局部筛选器和透视表分配新 ID，校验绑定及筛选后结果，再保存草稿。回读要求完整草稿 schema、原有单元、已发布 schema、逐行数据和总计匹配。每份计划有独占尝试日志。保存异常时仅在草稿精确匹配本次投影且原有单元仍匹配时恢复原 schema，回执记录可能遗留的资源。该入口的写入范围限定在草稿。

## 故障与恢复

- `domain unresolved/mismatch`：回到对应业务 SQL skill，重新生成域内 QuerySpec、DatasetSpec 和画像。
- `profile drift`：重新 profile、design 和 diff，不得复用旧 Hash。
- `blocked_unsupported`：保留 dry-run 结果，等待专门接口验证和 allowlist 扩展。
- `operation failure`：停止后续操作，逆序恢复已完成项；恢复后完整 Profile Hash 必须回到 baseline。
- `recovery target drift`：不得覆盖并发编辑，保存 `recovery.status=failed` 的 ApplyReceipt 并人工检查 draft。
- `post profile mismatch`：按事务故障处理并恢复；若恢复不可证明，停止发布并人工检查 draft。
- `publish blocked`：不要重新 Apply；先确认 Receipt/Plan 绑定和 draft 是否发生新编辑。

## Legacy 兼容命令

`edit-public-filters` 仅保留旧序号式计划的 dry-run 检查。任何 legacy `--apply`、`--publish` 或 `--confirm-publish` 都会在浏览器启动前失败。后续生产变更只能使用 stable-ID ChangePlan、ApplyReceipt 和独立 PublishReceipt。
