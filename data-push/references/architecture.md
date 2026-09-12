# 架构与隔离

`data-push` 是本地 Python/Windows 与飞书妙搭全栈推送的统一编排 Skill。统一的是身份模型、业务合同、验收语言和安全边界；运行配置、任务、状态、应用和发布生命周期仍按部门与执行面物理隔离。

## 路由键

任何推送先解析显式地址：

```text
local:  domain / local  / channel_id
miaoda: domain / miaoda / deployment_id / workflow_id
        │        │            │              └─ app 内隔离的推送任务
        │        │            └─ 部门独占的 runtime/app
        │        └─ execution_surface
        └─ market_consultant | qingcheng
```

缺少 `domain` 时只检查中性物理事实，不从群名、字段、配色、任务名或当前 runtime 工程猜部门。未登记的地址直接阻断，不允许跨部门或跨执行面 fallback。

## 四象限现状

| | `local` | `miaoda` |
|---|---|---|
| `market_consultant` | 六个已登记渠道；Python adapter、Windows 任务、文件/SQLite 状态 | 一个 app 原型 `cloud_data_push`，内含 `supervisor_koc_douyin_sync` workflow；工程 `runtime/cloud-data-push-miaoda` |
| `qingcheng` | 仅登记部门，无渠道和 adapter | 无部署；首个实现默认使用独立 runtime 工程与独立 app |

“已登记原型”只证明本地工程与 app 身份绑定，不代表已有 release、线上变量、自动化、生产目标或发送授权。动态状态始终从对应平台实时读回。

## 控制面与执行面

```text
部门业务 Skill
  → 部门 PushContract（字段、粒度、公式、日历、提醒、样式）
      ├─ local deployment
      │    channel config → Python adapter → Windows task → local ledger
      └─ miaoda deployment
           app binding → isolated workflow/domain module → Miaoda automation → hosted ledger
```

- `PushContract` 是审阅概念，不是让两个执行面读取同一份可变 JSON。迁移时显式比较业务字段和输出，不继承目标、身份、调度或授权。
- 本地执行面由 `config/channels.json`、`config/departments/<domain>/` 和 `scripts/lark_delivery/domains/<domain>/` 管理。
- 妙搭执行面由 `config/deployments.json` 绑定到部门独占的 runtime/app；app 内每个 workflow 再绑定自己的业务合同、模块、自动化与台账 namespace。工程源码、`.spark/meta.json`、Secret、数据库和 release 由该部署管理。
- `lark_delivery/common` 只提供中性 Base/IM/文件能力；部门聚合、日历、文案和样式不进入 common。妙搭工程也遵循同样的依赖方向。

## 必须物理隔离的资源

| 资源 | 隔离键 | 规则 |
|---|---|---|
| 业务配置与 adapter | `domain/channel_id` | 不接受别的部门字段、公式、日期或提醒规则 |
| 图片配色与布局 | `domain + contract_version` | renderer/style 由部门拥有；共享层只提供绘图原语和类型 |
| 本地任务 | `domain/channel_id` | `windows_task_name`、错峰顺序、启停和状态根唯一 |
| 妙搭工程与 app | `domain/deployment_id` | 默认一部门一 app；runtime 根和 app_id 不跨部门/部署复用 |
| 妙搭 workflow | `domain/deployment_id/workflow_id` | contract、module、automation 和 ledger namespace 分离；样式所有者必须等于部门 |
| 妙搭自动化 | `domain/deployment_id/workflow_id/trigger` | namespace 唯一；创建、启用与发送分别授权 |
| 状态与台账 | `domain/surface/deployment/target` | 本地与云端不共用目录、表、幂等 claim 或恢复状态 |
| 发送配置 | `deployment/target` | Base、机器人、群、Secret 独立固定并回读，不从另一执行面复制 |
| fixture 与视觉回归 | `domain/contract_version` | 不用市场样本证明青橙口径或配色正确 |

对“共用”的判断以故障域为准：字体加载器、Base 分页客户端、哈希函数等中性能力可以复用；字段名、渠道集合、年级、阈值、期次、列、颜色、任务分钟、群和机器人都不是公共默认值。

## 本地目录职责

| 位置 | 用途 |
|---|---|
| `config/channels.json` | 本地渠道注册与部门语义入口 |
| `config/departments/<domain>/<channel_id>.json` | 单一渠道的本地运行配置 |
| `scripts/channels/<domain>/<channel_id>.py` | 绑定一个本地渠道的薄入口 |
| `scripts/lark_delivery/core/` | 显式注册、接口与多目标协调，不含业务指标 |
| `scripts/lark_delivery/common/` | 中性飞书能力，不导入 domains/legacy |
| `scripts/lark_delivery/domains/<domain>/` | 部门 adapter、聚合、样式、文案与本地调度 |
| `config/deployments.json` | 妙搭部门 app 与 workflow/contract/module/namespace 绑定 |
| `runtime/<deployment>/` | 妙搭实际工程；不复制进 Skill 仓库，不跨部门共享可变运行资源 |
| `templates/` | 独立工作流可复制模板；不能读取渠道或部署生产配置 |

旧 `group_push.py`、`scheduled_push.py` 等文件名只是兼容门面；新渠道不可复制其中的业务逻辑。当前市场实现不能导入 `legacy`，`core` 只有 `registry.py` 可以选择部门 adapter。

## 跨执行面迁移

迁移是并行验证后切换所有权，不是把 `execution_surface` 改一个字符串：

1. 固定同部门的源渠道和目标妙搭部署，生成字段、公式、粒度、日历、文案、样式与目标差异。
2. 妙搭在 fixture、真实 Base dry-run、测试群实发和消息读回阶段分别验收；每阶段保留独立证据。
3. 妙搭自动化初始禁用，本地任务状态不随开发、发布或测试变化。
4. 只有用户另行授权切换且云端连续满足验收条件，才计划停用精确本地任务；停用后读回 Windows 任务与云端自动化状态。
5. 不确定发送在所属台账中人工对账；不得换执行面重发同一业务消息。

详细本地接口见 [interfaces.md](interfaces.md)，本地配置见 [channel-configuration.md](channel-configuration.md)，妙搭绑定见 [deployment-configuration.md](deployment-configuration.md)，云端阶段见 [miaoda-broadcast-migration.md](workflows/miaoda-broadcast-migration.md)。
