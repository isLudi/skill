# 妙搭部署配置

妙搭全栈推送使用 `config/deployments.json`，不把本地渠道 JSON 直接当云端运行配置。部署键固定为 `domain/miaoda/deployment_id`，表示一个部门独占的 runtime/app；部署内的 `workflows` 再隔离具体推送任务。当前部署是 `market_consultant/miaoda/cloud_data_push`，内含 `supervisor_koc_douyin_sync`。

## 字段与所有权

| 字段 | 约束 |
|---|---|
| `domain` | 必须已在 `config/channels.json` 登记；决定业务 Skill、adapter、fixture 和样式所有者 |
| `execution_surface` | 当前只允许 `miaoda`，不能用同一记录描述 Windows 任务 |
| `deployment_id` | 部门内稳定 ID；与键的第三段一致 |
| `runtime_base/runtime_root` | 当前以 `codex_home` 为基准，必须落在 `runtime/` 下且只属于一个部署 |
| `identity_file/expected_app_id` | 从工程 `.spark/meta.json` 独立读回 app 身份；不同部署不得共享 app_id |
| `lifecycle` | `prototype`、`disabled` 或 `active`；这是事实状态，不是发布、发送或启用授权 |
| `local_schedule_relation` | 当前必须为 `independent`；妙搭开发和测试不得暂停、替换或恢复本地任务 |
| `workflows` | 部署内任务 map；同一部门可以复用自己的 app，但每个 workflow 必须独立登记 |

每个 workflow 的字段：

| 字段 | 约束 |
|---|---|
| `contract_ref` | 必填，指向 `references/departments/<domain>/` 下本部门业务合同；妙搭原生任务也可独立存在 |
| `source_channel_ref` | 可选；迁移时指向同部门已登记本地渠道，仅用于等价对照 |
| `module_root` | workflow 的服务端模块；同一 app 内不得与其他 workflow 重叠 |
| `automation_namespace` | 妙搭触发器命名前缀；跨 workflow 唯一，不能与 Windows 任务名互相推导 |
| `ledger_namespace` | 托管数据库中的台账命名空间；跨 workflow 唯一 |
| `style_owner` | 必须等于部署 `domain`；颜色、列、字体和布局由本部门实现持有 |

## 不继承的字段

`contract_ref` 是云端业务合同入口；可选的 `source_channel_ref` 只说明两个执行面要做等价对照。妙搭端必须独立固定并核验 Base 坐标、发送机器人、目标群、Secret、触发器、数据库台账、幂等键和发布版本；不得自动读取本地配置中的以下字段作为云端生产值：

- `targets`、`sender`、`schedule`、`state_dir`；
- Windows `windows_task_name`、`stagger_order` 和分钟网格；
- 本机登录身份、SQLite 台账或预览目录；
- 一次性测试群和临时降级策略。

业务字段、公式、粒度、期次规则和提醒对象需要做显式等价对照；若妙搭实现尚未版本化为同一合同，报告差异，不宣称“已迁移”。

## 部门隔离

默认一个部门一个妙搭工程和 app；同部门新任务可以作为独立 workflow 加入自己的 app。新建青橙部署时使用新的 runtime 根和 app_id，再创建本部门模块、自动化命名空间、台账命名空间、fixture 和 renderer；不得把 `qingcheng` 加入现有 `cloud-push-demo` 的条件分支。只有用户明确要求跨部门共用 app，且先审阅 app 级 Secret、发布、数据库、自动化和故障域隔离方案后，才能设计共享宿主；仍需保持部门模块与配置物理分离。

`scripts/validate_layout.py` 只做离线身份、路径和唯一性检查。它不读取妙搭线上状态，也不代表部署、启用或真实发送完成。
