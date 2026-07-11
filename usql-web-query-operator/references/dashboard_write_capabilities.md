# P4A/P4B 看板写能力治理

P4A 只建立写能力证据和白名单，不把自然语言请求直接变成平台写入。机器注册表位于 `references/dashboard_write_capabilities.json`，Schema 位于相邻 JSON Schema 文件。

## 能力状态

| maturity | write_policy | 含义 |
|---|---|---|
| `verified` | `allowlisted` | 已有稳定 ID、真实写适配器、完整回读和测试，可由受控 Apply 使用 |
| `sandbox_verified` | `sandbox_only` | 真实沙箱已通过写入、漂移、回读和恢复，适配器只能由显式沙箱验证命令调用，不能进入生产 Apply |
| `partial` | `separate_confirmation` | 只验证了部分链路，必须走独立确认并如实记录未验证部分 |
| `observed` | `blocked` | Profile 能读取目标状态，但尚无经过验证的写接口 |
| `unverified` | `blocked` | 写请求、稳定身份或回读均未建立 |

默认策略始终是 `block_unverified`。一次沙箱探测不会自动修改或提升注册表。

P4B 当前生产 `allowlisted` 操作为 `update_component_fields`、`update_layout`、`update_formula`、`update_filter_dynamic_default`、`update_theme`。这不是开放式写权限：每类操作都受共享 Diff 的窄约束，必须绑定完整 Profile、精确 ChangePlan Hash、目标双读、写后回读、最终全量画像和失败逆序恢复。Registry 中其余 9 类操作保持 `blocked`；发布仍为 `separate_confirmation`。

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

命令先按固定顺序逐项执行单动作写入、目标态回读、恢复前漂移校验、目标字段恢复和恢复回读；随后再执行五操作连续 Apply、逆序恢复，最后重新生成完整 DashboardProfile，并要求最终 Profile Hash 与 manifest 基线完全一致。原始验证 bundle 留在 runtime；仓库只保留不含 payload 值的脱敏证据摘要。

当前 P4B 适配器边界：

- 布局：生产只允许已有稳定 node 的 `x/y/w/h`，同容器/Tab 且不得引入越界或新碰撞；不创建、删除或跨容器移动。
- 组件：生产只允许已有 unit 中一个稳定 field ID 的显示名更新，不增删/排序字段，不变更公式、筛选器绑定或数据集。
- 公式：生产只允许已有、组件内、非共享公式的表达式更新，依赖必须不变；不创建、删除或扩大影响组件。
- 筛选器：稳定 `relation_id + filter_id + field_id`，恢复时同时清理平台派生的 `filterValue/preFilter*`。
- 主题：生产只允许看板根 `#RRGGBB` 背景色；theme/style identity、完整调色板和组件级样式仍未开放。

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
