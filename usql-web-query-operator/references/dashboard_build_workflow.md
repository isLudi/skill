# Taitan 看板 P4C 从零创建工作流

本文件描述独立于 P3A/P4B 既有看板修改链路的 P4C 创建 Saga。P4C 的目标是在既有文件夹中创建一个唯一命名、未发布的新看板；它不修改既有生产看板，也不把空板、模板克隆或未经验证的 UI 猜测当作生产实现。

## 当前状态

代码已提供声明式 Artifact、只读 Plan、创建 Saga、失败 Receipt、断点续作、独立 Publish 和脱敏沙箱取证入口。2026-07-18 已在青橙“P4C看板构建沙箱”完成基础与高级两轮真实从零草稿端到端验收，十三项 P4C operation 已由不可变证据、生产适配器、完整 Profile/取值回读和故障/恢复测试晋级为 `verified/allowlisted`。高级验收覆盖全部指标别名、多个创建时局部/全局筛选器、证据限定样式、双插槽透视容器和受限富文本。生产适配器 ID 为 `taitan_dashboard_build_v1`；`apply-dashboard-build` 仍在 Plan、Hash、Registry、域、文件夹或字段树任一门禁不满足时于浏览器/写入前停止。

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

- `DashboardBuildSpec`：声明目标文件夹、唯一看板名、数据集、计算列、组件、每个指标实例的显示名、多个局部/全局筛选器、双插槽容器、富文本、布局、证据限定样式、主题和验证断言。
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

通过门禁后固定顺序为：创建 dashboard shell → 对 `dashboard_scoped_clone` 数据集先创建所有无公式 unit 以取得平台分配的真实 subject → 在该 subject 创建或精确复用计算列 → 创建依赖计算列的 unit（所有新 unit 在创建时绑定数据集、字段和多个局部筛选器）→ 创建文本框和双插槽容器/嵌套透视表 → 对每一个新指标实例写入并回读 `showName` → 创建多个全局筛选器关系 → 组装并保存 dashboardHtml 草稿 → 应用页面、透视表、Tab 和文本的证据限定样式 → 完整 Profile 回读 → 四类数据组件及插槽透视表类型感知取值 → 每个全局筛选器至少一次带 `publicFilterList` 的明确值验证。普通复用 subject 的数据集仍可直接先创建计算列。

指标显示名采用全量门禁：只要一个 measure 声明 `display_name`，同一 Build 中所有 measure 实例都必须声明；平台回读按 `field_id + showName` 精确匹配，不能以展示名猜字段。局部筛选器只允许作为新根 data unit 创建请求的一部分，当前插槽内透视表不能携带局部筛选器。容器仅支持恰好两个命名 slot，每个 slot 恰有一个新建 `u_pivot`。样式只支持 `Page` 背景、`u_pivot=arco_blue`、`SingleTabs=wide` 和受限富文本；`card/u_bar/u_pie` 的任意 raw style 仍未开放。

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

文件夹级 `create_dashboard` 证据只能在名称明确包含“测试/沙箱/P4C”的既有文件夹中捕获；看板级单操作只能在用户精确授权且实时名称包含测试/沙箱/P4C 标记的新建草稿中执行。每次必须使用可见浏览器和 `--confirm-sandbox-write`，禁止发布、删除、权限和认证写。

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

看板级 `create_formula`、四类数据组件、新 unit 内嵌 dataset/local-filter、公共筛选器、dashboardHtml、文本框、双插槽 Tab、指标别名和样式使用 `--scope dashboard` 并提供精确 dashboard ID/name。`create_formula` 还必须提供 `--sandbox-subject-id` 和名称带测试/沙箱标记的 `--sandbox-subject-name`，确保测试列只写入专用 subject。命令只保存 host、path、请求字段路径、大小、HTTP 状态和脱敏 Hash；不保存 payload 值、Cookie、token、查询结果或截图，也不自动删除或晋级 capability。

收齐证据后使用：

```powershell
D:\anaconda3\python.exe scripts\read_dashboard.py verify-sandbox-dashboard-build `
  --evidence-manifest C:\runtime\dashboard_build_evidence_manifest.json
```

Manifest 的每项 operation 必须显式选择一个成功请求的 `selected_observation_sha256`，避免把后台只读 POST 冒充目标写请求。该命令只离线检查 operation 覆盖、前后身份、脱敏证据 Hash 和禁止操作，不修改 Registry。每项 capability 仍需真实适配器、完整回读、故障/漂移/跨域测试、幂等或 creation-saga 策略、代码与测试 Hash，才可人工审阅晋级。

基础聚合证据为 `references/dashboard_build_evidence_20260718.json`，SHA-256 `7eaf0c07395f8271c30da9dd04d3b1de78c2714583a4a2725e4d34f4bd422e3c`。基础验收看板 `dashboard_3994454707150426113` 的 Profile SHA-256 为 `8266f995038ec6b9d6955c1f3ffbdcad354dba472c6dee8ab0be06adfe6e0f5f`，BuildPlan 为 `b802340b0ce68961b27d273a5d953ef427db6889f351ba96dd1e2c0b2ac86d48`，BuildReceipt 为 `6bdcbe9f64400d3c678cd2643ac7ddd91a426f95e75841d14748e80974247e29`。

高级聚合证据为 `references/dashboard_build_advanced_evidence_20260718.json`，SHA-256 `bd245dc59c78d7f628a7add3242bdd9e403e303411012597b058a2b3b77644e3`。基础与高级能力的合并清单已由 `verify-sandbox-dashboard-build` 离线验证为 13/13 完整，manifest 文件 SHA-256 为 `56119e70b4c31a3750ebb6398731c9ea0cc35cd85ba2409cd6c436598526028e`，verification 文件 SHA-256 为 `3cfe7c85ee22b9a68ef7a0f4cab5be91ba88086bba77f920a7fafba3c4690ceb`。高级生产验收看板为 `dashboard_3994584279860838400`，BuildSpec SHA-256 `544e208789b976c34767e0ad7021032c44c4efa8091339a4aebb7379d42558f3`，BuildPlan SHA-256 `db930c4bb9e1534b4ca657925cb72152c0f6e91e7a9b1df63d586e4d240f33e4`，目标态 SHA-256 `7f55bc02f423ad56bac0d2dfe250c7b8ec0ce05d00a7905dd40a636177394175`，独立完整 Profile 与 Receipt 内 Profile SHA-256 均为 `64856e0fdd685f9c8ffe1027c5fc8985dd2d87c3e82fa97e063a9d0d046f750e`，成功 BuildReceipt SHA-256 `f7995cbb4516afcc074fe04737968567aa88a6434b32abab38f1cc57a5d0d625`。草稿包含 1 个 card、4 个 pivot（含双插槽内 2 个）、1 个 bar、1 个 pie、1 个计算列、2 个局部筛选器、2 个全局筛选器及 8 条目标边、11 个已回读别名指标、1 个富文本和证据限定样式；7 个 value shape 与 2 个全局筛选断言均通过，最终 0 orphan、`manual_cleanup_required=false`，未发布。

## 永久边界

- 不创建或移动文件夹，不删除看板、unit、计算列、数据集或权限对象。
- 不修改既有组件的数据集或局部筛选器；P4C 只允许新 unit 创建请求内设置。
- 不把 P4C 新组件样式能力扩大为既有组件样式修改；不接受未取证的任意 raw style、任意 HTML/CSS 或任意 Tab 嵌套结构。
- 不使用模板克隆作为生产降级，不自动发布。
- 数据中心创建始终使用自己的 Plan Hash、`--confirm-production-write` 和 SUCCESS Receipt。
- 计算列取证只能使用独立沙箱 subject，不能污染生产看板共享数据集。
- Runtime 证据保存在 `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\`，不得进入仓库。
