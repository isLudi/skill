# Taitan 看板 P3A/P3B 变更工作流

本文件描述独立的 `profile → design spec → diff/dry-run → apply draft → publish confirmation` 安全链路。只有处理看板设计或变更任务时读取；普通 SQL 执行、下载或只读看板浏览不需要加载本文件。

## 目录

1. [能力边界](#能力边界)
2. [Artifact 与 Hash 绑定](#artifact-与-hash-绑定)
3. [P3A：画像、设计和 dry-run](#p3a画像设计和-dry-run)
4. [P3B：草稿 Apply](#p3b草稿-apply)
5. [独立发布确认](#独立发布确认)
6. [公共筛选器稳定定位](#公共筛选器稳定定位)
7. [受支持与阻断的操作](#受支持与阻断的操作)
8. [故障与恢复](#故障与恢复)
9. [Legacy 兼容命令](#legacy-兼容命令)

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

主 `--output` 保持向后兼容，继续包含 `pivot_units`、`dataset_fields`、`text_notes` 和字段详情；同时增加 `domain`、规范快照、`profile_sha256` 和嵌套 `normalized_profile`。`--normalized-output` 可额外写出纯 DashboardProfile Artifact。

`profile_sha256` 只覆盖组件、布局、公式、筛选器、数据集和完整性等可编辑状态。Taitan 每次打开可能重发的 `html_id` 保留为导航元数据但不参与 Hash；否则同一配置会产生伪漂移。Apply/Publish 仍必须使用最新 profile 中的 `html_id` 打开页面，并以完整状态 Hash 做前置校验。

画像必须 `completeness.status=complete` 才能进入后续链路。除接口抓取成功外，完整性还要求每个已配置 pivot 能稳定解析到 unit、component 和 model/dataset identity，组件引用的 selected field、formula、component-filter 均有对应对象，dataset 存在且保留 unit/component 反向引用；启用字段树抓取时，已选字段和公式依赖还必须存在于对应 subject。空白容器、文本和其他非数据组件不参与 pivot 绑定门禁。任一抓取或绑定失败时，rich artifact 仍会保存 `binding_validation` 和错误证据，但命令返回非零；Design、Apply 和 Publish 全部拒绝不完整画像。

规范快照包含：

- 组件稳定 `component_id/node_id`、`unit_id`、父容器和 Tab 路径，以及真实已选维度/指标、formula IDs、component-filter IDs 和 dataset/model identity。
- `x/y/w/h` 等布局。
- 公式 ID、表达式、依赖和影响组件。
- 公共筛选器的 `relation_id + filter_id + field_id`。
- `dynamic_default` 以及平台实际字段 `dynamics_filter`、`dynamics_filter_value`、`auto_search_default_value`。
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

`desired-state` 可包含 `components`、`layout`、`formulas`、`public_filters`、`component_filters`。提供某个集合时，它表示该集合的完整目标状态，不是局部 patch；缺项可能被解释为删除并被 P3B 阻断。组件内筛选器目前只支持 P3A Diff，不能 Apply。

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

该命令不启动浏览器、不调用写接口，并输出 before/after、risk、`write_status`、阻断原因和 `change_plan_sha256`。组件、布局和公式可以完整画像与 Diff，即使当前没有经过生产验证的写接口。

## P3B：草稿 Apply

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
3. 一个 ChangePlan 最多涉及一个 `relation_id`。平台没有已验证的事务或回滚，多 relation 必须拆为多个计划，防止部分写入。
4. 重读当前 draft，要求 `profile_sha256 == base_profile_sha256`；漂移时零写入停止。
5. 使用稳定三元组定位目标，并把即时 relation 中的 field state 与 ChangePlan `before` 逐项核对。
6. 紧邻 POST 再取一次 relation；payload Hash 或目标状态漂移时零写入停止，否则只调用一次更新接口。
7. 再次完整画像 draft，并要求 post profile 与 ChangePlan `target_state` 精确一致。
8. 生成 `DashboardApplyReceipt`。任一 operation 未标记为 `applied` 或回读不一致时，receipt 为失败，禁止发布。

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
| `update_filter_dynamic_default` | 支持 | 支持，仅稳定三元组且单 relation |
| `update_existing_component` | 支持 | `blocked_unsupported` |
| `update_component_fields` | 支持 | `blocked_unsupported` |
| `update_layout` | 支持 | `blocked_unsupported` |
| `update_formula` | 支持 | `blocked_unsupported` |
| 新建、删除、换类型、跨容器移动、数据集重绑 | 支持识别 | 阻断 |

共享公式、跨组件公式和任何影响范围不明的改动必须阻断。没有抓取并验证真实请求的接口，不得凭字段名猜测写 payload。

## 故障与恢复

- `domain unresolved/mismatch`：回到对应业务 SQL skill，重新生成域内 QuerySpec、DatasetSpec 和画像。
- `profile drift`：重新 profile、design 和 diff，不得复用旧 Hash。
- `blocked_unsupported`：保留 dry-run 结果，等待专门接口验证和 allowlist 扩展。
- `multiple relation_id`：拆成多个独立 ChangePlan，逐个 Apply、回读和确认。
- `post profile mismatch`：停止发布，保存失败 ApplyReceipt，并人工检查 draft。
- `publish blocked`：不要重新 Apply；先确认 Receipt/Plan 绑定和 draft 是否发生新编辑。

## Legacy 兼容命令

`edit-public-filters` 仅保留旧序号式计划的 dry-run 检查。任何 legacy `--apply`、`--publish` 或 `--confirm-publish` 都会在浏览器启动前失败。后续生产变更只能使用 stable-ID ChangePlan、ApplyReceipt 和独立 PublishReceipt。
