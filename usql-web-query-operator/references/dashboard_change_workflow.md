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
8. [复制重建透视表组件](#复制重建透视表组件)
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
| `update_component_filter_label` | 支持 | 支持，仅稳定 unit/field 的局部筛选器显示标签 |
| `update_component_title` | 支持 | 支持，仅一个稳定既有组件的非空标题 |
| `update_tab_label` | 支持 | 支持，仅稳定 component/slot key/slot ID 的一个标签 |
| `update_layout` | 支持 | 支持，仅同容器/Tab 既有节点 `x/y/w/h`，通过边界与碰撞检查 |
| `update_formula` | 支持 | 支持，仅既有单组件非共享公式表达式，依赖不变 |
| `update_theme` | 支持 | 支持，仅根 `background_color=#RRGGBB` |
| 新建、删除、换类型、跨容器移动、数据集重绑 | 支持识别 | 阻断 |

共享公式、跨组件公式和任何影响范围不明的改动必须阻断。没有抓取并验证真实请求的接口，不得凭字段名猜测写 payload。

## 复制重建透视表组件

复制重建用于处理既有透视表 unit 可见字段正确、但 `value/unit` 仍走旧任务或旧绑定的情况。沙箱验证命令是 `rebind-pivot-fields-sandbox`，生产 draft 命令是 `rebind-pivot-fields-production`。生产路径只允许 registry 中 `verified/allowlisted` 的 `rebuild_pivot_unit_by_copy`，并要求精确 `--manifest-sha256` 与显式 `--confirm-production-write`。两个命令都只保存 draft，不发布。

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

生产 draft 命令：

```powershell
D:\anaconda3\python.exe scripts\read_dashboard.py rebind-pivot-fields-production `
  --target-manifest C:\runtime\pivot_rebind_manifest.json `
  --manifest-sha256 <exact-manifest-hash> `
  --dashboard-id dashboard_123 `
  --expected-dashboard-name "过程数据报表-青橙" `
  --domain qingcheng `
  --confirm-production-write `
  --output C:\runtime\pivot_rebind_production_receipt.json
```

manifest 必须声明 `artifact_type=DashboardPivotFieldRebindManifest`、`schema_version=1.0.0`、域、目标 dashboard、可选 `expected_profile_sha256`、需要先备份的看板，以及 operations。每个 operation 绑定 `target_unit_id`、`source_unit_id`、目标维度 field IDs 和必需指标 field IDs。生产 manifest 还必须声明 `required_public_filters` 和覆盖每个 operation 的 `filtered_value_checks`：每个 check 必须携带完整 `public_filter_list`，并证明它包含目标期次/周期筛选值。只看无 filter 的 `value/unit` 原始结果会把跨期次总量误判为指定期次结果，不能作为生产验证门禁。

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

1. 读取并保存所有指定 backup dashboard 的 draft edit config、组件 unit detail 和 published config；生产看板只能作为只读备份目标。
2. 读取沙箱完整 DashboardProfile，若 manifest 绑定了 `expected_profile_sha256`，必须一致。
3. 对每个 operation 调用 `config/copy/unit` 复制 `source_unit_id`，得到新 unit ID。
4. 对新 unit 调用 `config/update/unit`，把字段重建为目标维度组合和指标组合，必要时保留目标组件的展示名与格式。
5. 批量修改 dashboardHtml 中目标组件的 `settings.unitId`，指向新 unit，并调用 `config/save/dashboardHtml` 保存 draft。
6. 读回 profile，然后按 manifest 中的 `filtered_value_checks` 调用 `value/unit`，请求体必须带 `publicFilterList`，并断言指定期次/周期下的目标行和指标值。
7. receipt 记录 pre/post profile hash、备份路径、新旧 unit 映射、schema 引用验证、filtered value 验证摘要和脱敏请求 shape。

生产命令不会发布，也不会绕过独立 PublishReceipt 边界。若中途失败且 dashboardHtml 已保存，会尝试恢复写前 schema；已经复制出的孤立 unit 可能留在后端，但不会被组件引用。若只是 `touch_before_final=true`，命令会先写入临时字段列表再写回目标字段列表，用于测试缓存失效；但如果旧 unitId 本身绑定了旧任务，通常需要 `rebuild_by_copy=true`。

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
