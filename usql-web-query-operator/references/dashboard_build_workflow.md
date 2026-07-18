# Taitan 看板 P4C 从零创建工作流

本文件描述独立于 P3A/P4B 既有看板修改链路的 P4C 创建 Saga。P4C 的目标是在既有文件夹中创建一个唯一命名、未发布的新看板；它不修改既有生产看板，也不把空板、模板克隆或未经验证的 UI 猜测当作生产实现。

## 当前状态

代码已提供声明式 Artifact、只读 Plan、创建 Saga、失败 Receipt、断点续作、独立 Publish 和脱敏沙箱取证入口。Registry 中所有 P4C 创建 operation 目前仍为 `observed/blocked`：仓库尚未保存满足晋级条件的真实沙箱请求证据，也没有可被生产入口解析的已验证 adapter。因此 `apply-dashboard-build` 会在导入 Playwright 和打开浏览器前拒绝执行。这是安全门禁，不是可绕过的临时开关。

## Artifact 链路

```text
DashboardBuildSpec
  → plan-dashboard-build
  → 必要的 DataCenterDatasetCreationPlan / Apply / SUCCESS
  → 重新 plan-dashboard-build
  → DashboardBuildPlan
  → apply-dashboard-build
  → DashboardBuildReceipt
  → publish-dashboard-build
  → DashboardBuildPublishReceipt
```

- `DashboardBuildSpec`：声明目标文件夹、唯一看板名、数据集、计算列、组件、局部/全局筛选器、布局、主题和验证断言。
- `DashboardBuildPlan`：绑定真实 `application_model_id + subject_id + model_type`、字段 ID、字段树 Hash、上游 QueryPlan/DashboardDatasetSpec Hash 和所需 capability。
- `DashboardBuildReceipt`：记录每一步、真实资源 ID、创建/复用/孤立资源、完整画像 Hash 和取值检查。失败时不得自动删除。
- `DashboardBuildPublishReceipt`：独立发布凭证；没有正式线上版本读取 API 时固定为 `publish_requested_unverified`、`fully_verified=false`。

四类组件映射为：`metric_group → card`、`pivot → u_pivot`、`bar → u_bar`、`pie → u_pie`。Spec 只使用逻辑字段引用；Plan 才能解析为真实 field ID。

## 只读 Plan

```powershell
D:\anaconda3\python.exe scripts\read_dashboard.py plan-dashboard-build `
  --build-spec C:\runtime\dashboard_build_spec.json `
  --dataset-resolutions C:\runtime\dashboard_dataset_resolutions.json `
  --folder-snapshot-sha256 <sha256> `
  --dashboard-name-available `
  --output C:\runtime\dashboard_build_plan.json
```

命令会直接重新读取 Spec 中的 QueryPlan 和 DashboardDatasetSpec 文件，不信任 resolutions 中自报的 ready 状态。它验证：

- QueryPlan 可执行、无未解析槽位、域和文件 Hash 一致。
- DashboardDatasetSpec 为 ready、绑定同一 QueryPlan、域一致且自身 Hash 有效。
- contract 全部 confirmed，业务 Skill 中的 source file Hash 仍有效。
- DatasetSpec 输出与平台字段绑定一对一，field ID 不重复，字段组/类型满足 dimension、measure 和 filter 用途。
- 文件夹快照与看板名称唯一性已经由只读平台读取确认。
- create 模式的数据集已有独立 Data Center Plan/Receipt，并出现 fully verified 的新 `SUCCESS`。

缺少 Data Center 首次 SUCCESS 时，Plan 为 `pending_dataset_creation`；其他身份、域、Hash、字段或类型错误为 `blocked`。Plan 永不授权数据中心 Apply、看板 Apply 或发布。

## 创建 Apply

```powershell
D:\anaconda3\python.exe scripts\read_dashboard.py apply-dashboard-build `
  --build-plan C:\runtime\dashboard_build_plan.json `
  --build-plan-sha256 <exact-sha256> `
  --domain qingcheng `
  --confirm-production-write `
  --output C:\runtime\dashboard_build_receipt.json
```

浏览器启动前必须同时满足：Plan Hash、`status=ready`、域、显式确认，以及全部所需 operation 的 `verified/allowlisted/full readback/creation_saga_no_auto_delete` Registry 条件。生产 adapter 解析失败也会停止。

通过门禁后固定顺序为：创建 dashboard shell → 创建或精确复用 subject 级计算列 → 创建四类新 unit（创建时绑定数据集、字段和局部筛选器）→ 创建全局筛选器关系 → 组装并保存 dashboardHtml 草稿 → 完整 Profile 回读 → 四类组件类型感知取值 → 带 `publicFilterList` 的全局筛选验证。

`--resume-receipt` 只允许重用 exact-match 资源。名称相同但状态不同必须停止，不覆盖。失败 Receipt 把本次创建资源列入 `orphaned_resources`，设置 `manual_cleanup_required=true`，并保持 `automatic_delete_attempted=false`、`rolled_back=false`。

## 独立发布

```powershell
D:\anaconda3\python.exe scripts\read_dashboard.py publish-dashboard-build `
  --build-plan C:\runtime\dashboard_build_plan.json `
  --build-plan-sha256 <exact-plan-sha256> `
  --build-receipt C:\runtime\dashboard_build_receipt.json `
  --build-receipt-sha256 <exact-receipt-sha256> `
  --domain qingcheng `
  --confirm-publish `
  --version-description "approved dashboard build" `
  --output C:\runtime\dashboard_build_publish_receipt.json
```

Publish 只接受成功 BuildReceipt。命令双读 draft Profile 和发布 payload Hash，拒绝任何漂移；Apply 本身没有发布路径。

## P4C 沙箱取证

文件夹级 `create_dashboard` 证据只能在名称明确包含“测试/沙箱/P4C”的既有文件夹中捕获；看板级单操作只允许 `dashboard_3984457934065463296` 且实时名称必须精确为“运营侧数据看板沙箱测试”。每次必须使用可见浏览器和 `--confirm-sandbox-write`。

```powershell
D:\anaconda3\python.exe scripts\read_dashboard.py capture-dashboard-build-evidence `
  --operation create_dashboard `
  --scope folder `
  --domain market_consultant `
  --folder-id <existing-folder-id> `
  --folder-path "<existing-test-folder-path>" `
  --folder-name "P4C看板测试沙箱" `
  --expected-new-dashboard-name "P4C验收-<unique-name>" `
  --confirm-sandbox-write `
  --headed
```

看板级 `create_formula`、四类组件、新 unit 内嵌 dataset/local-filter、公共筛选器和 dashboardHtml 组装使用 `--scope dashboard` 并提供精确 dashboard ID/name。`create_formula` 还必须提供 `--sandbox-subject-id` 和名称带测试/沙箱标记的 `--sandbox-subject-name`，确保测试列只写入专用 subject。命令只保存 host、path、请求字段路径、大小、HTTP 状态和脱敏 Hash；不保存 payload 值、Cookie、token 或截图，也不自动删除或晋级 capability。

收齐证据后使用：

```powershell
D:\anaconda3\python.exe scripts\read_dashboard.py verify-sandbox-dashboard-build `
  --evidence-manifest C:\runtime\dashboard_build_evidence_manifest.json
```

Manifest 的每项 operation 必须显式选择一个成功请求的 `selected_observation_sha256`，避免把后台只读 POST 冒充目标写请求。该命令只离线检查 operation 覆盖、前后身份、脱敏证据 Hash 和禁止操作，不修改 Registry。每项 capability 仍需真实适配器、完整回读、故障/漂移/跨域测试、幂等或 creation-saga 策略、代码与测试 Hash，才可人工审阅晋级。

## 永久边界

- 不创建或移动文件夹，不删除看板、unit、计算列、数据集或权限对象。
- 不修改既有组件的数据集或局部筛选器；P4C 只允许新 unit 创建请求内设置。
- 不使用模板克隆作为生产降级，不自动发布。
- 数据中心创建始终使用自己的 Plan Hash、`--confirm-production-write` 和 SUCCESS Receipt。
- 计算列取证只能使用独立沙箱 subject，不能污染生产看板共享数据集。
- Runtime 证据保存在 `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\`，不得进入仓库。
