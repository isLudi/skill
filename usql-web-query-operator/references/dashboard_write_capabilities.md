# P4A/P4B/P4C 看板写能力治理

P4A 只建立写能力证据和白名单，不把自然语言请求直接变成平台写入。P4B 管理既有对象的可补偿修改；P4C 管理只创建新资源且不自动删除的 Saga。机器注册表位于 `references/dashboard_write_capabilities.json`，Schema 位于相邻 JSON Schema 文件。

## 能力状态

| maturity | write_policy | 含义 |
|---|---|---|
| `verified` | `allowlisted` | 已有稳定 ID、真实写适配器、完整回读和测试，可由受控 Apply 使用 |
| `sandbox_verified` | `sandbox_only` | 真实沙箱已通过写入、漂移、回读和恢复，适配器只能由显式沙箱验证命令调用，不能进入生产 Apply |
| `partial` | `separate_confirmation` | 只验证了部分链路，必须走独立确认并如实记录未验证部分 |
| `observed` | `blocked` | Profile 能读取目标状态，但尚无经过验证的写接口 |
| `unverified` | `blocked` | 写请求、稳定身份或回读均未建立 |

默认策略始终是 `block_unverified`。一次沙箱探测不会自动修改或提升注册表。

P4B 当前生产 `allowlisted` 操作为 `update_component_fields`、`update_component_filter_label`、`update_component_title`、`update_public_filter_title`、`update_tab_label`、`update_layout`、`update_formula`、`update_filter_dynamic_default`、`update_theme`，另有独立的透视表 copy-rebind allowlist。这不是开放式写权限：每类操作都受共享 Diff 或专用 manifest 的窄约束，必须绑定完整 Profile、精确 Hash、目标双读、写后回读、最终全量画像和恢复策略。

Registry 1.1.0 共 29 项：23 项 `verified/allowlisted`、5 项 `blocked`、1 项 `separate_confirmation`。P4C 的 `create_dashboard`、`create_formula`、四类组件创建、`create_public_filter`、`assemble_new_dashboard`、`rename_new_component_metrics`、`style_new_components`、`create_tab_container`、`assemble_tab_slots` 和 `create_text_component` 共十三项 operation，均为 `transaction_class=creation_saga`、`recovery_policy=creation_saga_no_auto_delete`，生产 adapter 为 `taitan_dashboard_build_v1`。既有局部筛选器只开放单个 `showName` 标签修改，泛化 `update_component_filter` 仍 blocked；其余 blocked 项是既有组件 `bind_dataset`、模板克隆、移动文件夹和权限修改。详见 `references/dashboard_build_workflow.md`。

## 离线检查

```powershell
D:\anaconda3\python.exe scripts\read_dashboard.py inspect-write-capabilities
```

该命令验证 Registry Schema、Registry Hash、operation 唯一性、allowlist 约束以及所有代码/测试证据的 SHA-256，不启动浏览器。

## 沙箱手工抓证据

只有用户明确指定测试看板、确认允许测试写入且浏览器可见时，才运行：

```powershell
D:\anaconda3\python.exe scripts\read_dashboard.py capture-write-evidence `
  --operation update_layout `
  --sandbox-dashboard-id dashboard_123 `
  --expected-dashboard-name "P4A测试沙箱" `
  --domain market_consultant `
  --confirm-sandbox-write `
  --headed
```

命令先读取完整 draft Profile，再给出有限时间执行一个人工动作，记录非 GET 请求的 host、URL path、payload 大小和字段路径，不保存 payload 值。结束后再次读取 Profile，并生成带 Hash 的 `DashboardWriteProbe`。

安全边界：

- 只允许已登记的草稿候选操作。
- dashboard ID 必须为 `dashboard_*`，实时名称必须与 `--expected-dashboard-name` 完全一致并包含 P4A/测试/沙箱标记，且当前身份必须有明确编辑权限。
- `publish_dashboard`、`update_permissions`、创建/移动看板和删除操作不能使用该命令。
- 捕获窗口内主动阻断 publish、delete、permission 和 auth 写请求。
- Probe 只保存到 runtime，不进入业务 Skill 知识库。
- Probe 成功只代表“获得候选接口证据”，不代表接口已验证，也不会改变 Apply allowlist。

## 自动可逆适配器验证

已建立候选接口和稳定目标后，使用独立 manifest 运行正式适配器：

```powershell
D:\anaconda3\python.exe scripts\read_dashboard.py verify-sandbox-write-adapters `
  --target-manifest C:\runtime\sandbox-adapter-manifest.json `
  --sandbox-dashboard-id dashboard_123 `
  --expected-dashboard-name "P4A测试沙箱" `
  --domain market_consultant `
  --confirm-sandbox-write
```

命令先按固定顺序逐项执行单动作写入、目标态回读、恢复前漂移校验、目标字段恢复和恢复回读；随后再执行九操作连续 Apply、逆序恢复，最后重新生成完整 DashboardProfile，并要求最终 Profile Hash 与 manifest 基线完全一致。2026-07-20 的青橙 P4C 沙箱验证覆盖九项操作，verification SHA-256 为 `ccc9bbccc7d6cad3d26ecfae93c1691ddc19256d2a274fcb8db68d26b3762231`，最终 Profile Hash 精确恢复为 `64856e0fdd685f9c8ffe1027c5fc8985dd2d87c3e82fa97e063a9d0d046f750e`。原始验证 bundle 留在 runtime；仓库只保留不含 payload 值的脱敏证据摘要。

当前 P4B 适配器边界：

- 布局：生产只允许已有稳定 node 的 `x/y/w/h`，同容器/Tab 且不得引入越界或新碰撞；不创建、删除或跨容器移动。
- 组件字段：生产只允许已有 unit 中一个稳定 field ID 的 `showName`/`display_name` 更新，不增删/排序字段，不变更业务字段名、公式、筛选器绑定或数据集。
- 局部筛选器标签：只允许稳定 `unit_id + field_id` 对应 `unitFilterList.showName`；条件、值、增删和绑定仍走 blocked 的泛化 `update_component_filter`。
- 组件标题：只允许一个稳定组件的非空标题；数据组件同时保持 schema `componentName` 与 unit `unitName` 一致，部分写失败必须补偿恢复。
- 公共筛选器标题：只允许稳定 `relation_id + filter_id + field_id` 的叶子 `unitName`；字段、目标组件、值和默认项不随标题修改。
- Tab 标签：只允许稳定 `component_id + slot_key + slot_id` 的一个非空标签；插槽增删、排序、成员、容器配置和样式均不开放。
- 公式：生产只允许已有、组件内、非共享公式的表达式更新，依赖必须不变；不创建、删除或扩大影响组件。
- 公共筛选器动态默认项：稳定 `relation_id + filter_id + field_id`，权威动态字段精确回读；恢复时允许平台重新派生 `filterValue/preFilter*`，最终完整 Profile 仍必须回到基线。
- 主题：P4B 对既有看板只允许根 `#RRGGBB` 背景色；既有组件 style identity、完整调色板和组件级样式仍未开放。P4C 的新组件样式是独立 capability，只接受高级证据中固定的 Page/Pivot/Text/SingleTabs 投影，不能反向扩大 P4B。

## 能力晋级条件

一个 operation 从 `blocked` 或 `sandbox_only` 晋级到 `allowlisted` 前必须同时具备：

1. 明确的稳定目标 ID 与域/看板边界。
2. 至少一次真实沙箱请求证据和前后 Profile。
3. 请求 Schema、payload 最小化和敏感字段检查。
4. 写前即时回读与漂移检查。
5. 写后完整回读，可证明目标状态精确一致。
6. 幂等或明确的补偿/恢复方案；多操作必须验证正向顺序、反向恢复顺序和完整 Profile Hash 复原。
7. 正向、反向、漂移、跨域和错误 payload 测试。
8. 接入共享 Profile/DesignSpec/Diff/ChangePlan 和生产 ApplyReceipt；沙箱命令本身不能作为生产入口。
9. 更新 Registry evidence SHA、重新计算 Registry Hash，并通过完整 Text2SQL stack。

Chrome 插件只用于需要现有登录态的人工动作、页面观察和视觉确认。正式自动 Apply 必须回到 operator 的已验证适配器。

## P4C 取证与晋级差异

P4C 创建不能用 P4B 的逆序恢复假装事务。使用 `capture-dashboard-build-evidence` 取得文件夹级创建请求或明确沙箱看板内的单 operation 证据，再用 `verify-sandbox-dashboard-build` 离线验证脱敏 manifest。创建过程中产生的新 dashboard、formula、unit 或 relation 在失败后保留，由 `DashboardBuildReceipt` 列入 `orphaned_resources` 和 `manual_cleanup_required`；operator 禁止自动 delete。

2026-07-18 的基础生产晋级证据保存在 `references/dashboard_build_evidence_20260718.json`，聚合证据 SHA-256 为 `7eaf0c07395f8271c30da9dd04d3b1de78c2714583a4a2725e4d34f4bd422e3c`，覆盖最初八项 operation。高级证据保存在 `references/dashboard_build_advanced_evidence_20260718.json`，SHA-256 为 `bd245dc59c78d7f628a7add3242bdd9e403e303411012597b058a2b3b77644e3`，增加五项 production capability，并用最终真实草稿证明 11 个指标实例全部重命名、2 个创建时局部筛选器、2 个全局筛选器/8 条目标边、双插槽内 2 个透视表、受限富文本、页面/透视表/Tab 样式、7 个 `value/unit` shape 和 2 个明确筛选断言。基础与高级证据的合并 manifest 已由 `verify-sandbox-dashboard-build` 通过 13/13 完整性校验，manifest/verification 文件 SHA-256 分别为 `56119e70b4c31a3750ebb6398731c9ea0cc35cd85ba2409cd6c436598526028e` 和 `3cfe7c85ee22b9a68ef7a0f4cab5be91ba88086bba77f920a7fafba3c4690ceb`。最终 Receipt 为成功态、0 orphan、未发布。Registry 的代码、测试、证据和自身 Hash 仍由 `inspect-write-capabilities` 每次执行时重新校验。

创建 capability 晋级还必须证明：

1. 新资源由 build ID 和逻辑 ID 稳定定位，exact match 可幂等复用，冲突状态停止。
2. 新 unit 的 dataset binding 和 local filter 只能作为同一创建请求的一部分；不得放宽既有 `bind_dataset`、`update_component_filter`。
3. `card/u_pivot/u_bar/u_pie`、subject 级计算列、公共筛选器关系、dashboardHtml、全量指标别名、Page/Pivot/Text/SingleTabs 样式、双插槽关系和富文本均有真实请求证据、完整 Profile/取值回读、故障注入和不可变代码/测试/evidence Hash。
4. `apply-dashboard-build` 的生产 adapter registry 明确提供实现，且所有所需 operation 同时为 `verified/allowlisted`。
5. 发布继续使用 `separate_publish`，不得包含在创建 Apply 中。
