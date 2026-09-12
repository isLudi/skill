---
name: data-push
description: 统一设计和维护本地 Python/Windows 与飞书妙搭全栈数据推送，并按市场顾问部、青橙项目部、渠道和执行面隔离业务口径、配置、配色、任务、状态、应用与回执。用于新增、迁移或维护部门推送、预览、调度和投递；Excel 私聊与妙搭静态看板仍是独立工作流。业务语义先走所属部门 Skill，普通妙搭应用开发走 lark-apps。
metadata:
  short-description: "按部门隔离编排本地脚本与妙搭全栈数据推送、配置和调度"
---

# data-push

把数据推送视为带执行面的显式地址：本地用 `domain/local/channel_id`，妙搭用 `domain/miaoda/deployment_id/workflow_id`。必须先固定 `domain`，再选执行面和已登记资源；不得从群名、任务名、配色或现有代码反推部门。

## 先定路由地址

| 部门 | 本地脚本 | 妙搭全栈 |
|---|---|---|
| `market_consultant` | 已有登记渠道和 Windows 任务；读 [市场顾问部边界](references/departments/market_consultant.md) | 当前 `cloud_data_push` app 原型及 `supervisor_koc_douyin_sync` workflow 绑定见 `config/deployments.json`；读 [妙搭云端播报](references/workflows/miaoda-broadcast-migration.md) |
| `qingcheng` | 尚无已登记可执行渠道或 adapter | 尚无已登记部署；不得复用市场顾问部的妙搭 app、工程、模块、触发器、台账或配色；读 [青橙边界](references/departments/qingcheng.md) |

当前 `runtime/cloud-data-push-miaoda` 只属于 `market_consultant/miaoda/cloud_data_push`，其中已登记 `supervisor_koc_douyin_sync` workflow；整个 app 仍是原型，不代表已接管本地任务。同一部门可在自己的 app 中新增物理隔离的 workflow，青橙则默认创建独立工程和独立 app；若用户明确要求跨部门共用 app，必须先形成隔离设计并审查 app 级环境变量、发布、自动化、数据库与故障域，不能直接往现有市场模块加分支。

## 先选工作流

| 需求 | 先读 |
|---|---|
| 设计整体结构、跨本地/妙搭迁移 | [架构与隔离](references/architecture.md) → [扩展指南](references/extension-recipes.md) |
| 新增或重构本地渠道 | [本地渠道配置](references/channel-configuration.md) → [接口契约](references/interfaces.md) → 目标部门规范 |
| 新增或修改妙搭推送部署 | [妙搭部署配置](references/deployment-configuration.md) → [妙搭云端播报](references/workflows/miaoda-broadcast-migration.md)；平台操作同时走 lark-apps |
| 修改群、渠道、数据源、开关或时点 | 先固定部门和执行面；本地读 [本地渠道配置](references/channel-configuration.md)，妙搭读 [妙搭部署配置](references/deployment-configuration.md) |
| 当前自孵化KOC播报 | [市场顾问部渠道规则](references/departments/market_consultant/self_incubated_koc_5.md) |
| 商务KOC数学双渠道播报 | [商务KOC数学规则](references/departments/market_consultant/business_koc_math.md) |
| KOC与抖音私信主管维度播报 | [KOC与抖音私信规则](references/departments/market_consultant/supervisor_koc_douyin_sync.md) |
| KOC孟亚飞数学与自孵化5元纯课初三主管播报 | [KOC初三规则](references/departments/market_consultant/supervisor_self_incubated_koc_5_grade_9.md) |
| 亚飞B站初三主管播报 | [亚飞初三规则](references/departments/market_consultant/supervisor_yafei_grade_9.md) |
| 集团私域与APP主管维度播报 | [集团私域与APP规则](references/departments/market_consultant/supervisor_private_app_sync.md) |
| 青橙渠道或部署接入 | [青橙边界](references/departments/qingcheng.md)；业务语义由青橙 Skill 确认，当前无可执行资源 |
| 本地定时、重试、回执、图片清理、暂停或恢复 | [本地运行与验收](references/operations.md) |
| Excel按人切割私聊 | [Excel分发](references/workflows/excel-distribution.md) |
| 妙搭静态数据看板刷新、发布 | [妙搭看板](references/workflows/miaoda.md) |

只读取本次操作需要的知识，不把全部参考文档加载进上下文。

## 两个注册表，不跨面继承

- `config/channels.json` 只登记当前本地 Python 渠道；每个配置位于 `config/departments/<domain>/<channel_id>.json`，入口位于 `scripts/channels/<domain>/<channel_id>.py`。
- `config/deployments.json` 只登记妙搭全栈部署；部署键为 `domain/miaoda/deployment_id`，绑定部门独占的 runtime 工程和 app。部署内每个 workflow 再绑定自己的业务合同、模块、自动化命名空间、台账命名空间和样式所有者。
- 迁移型 workflow 可以用 `source_channel_ref` 指向一个已审阅本地渠道；妙搭原生 workflow 只需自己的同部门 `contract_ref`。二者都**不会**继承本地 `targets`、`sender`、`schedule`、`state_dir` 或发送授权。
- `scripts/lark_delivery/common/` 只放中性飞书能力；聚合、字段、日历、文案、配色和提醒规则属于部门 adapter。妙搭工程也必须保持相同边界，不能在共享 renderer 中写“如果是青橙/市场”。

```powershell
# 本地说明，无API调用；所有Python示例使用D:\anaconda3
& 'D:\anaconda3\python.exe' 'C:\Users\Ludim\.codex\skills\data-push\scripts\channels\market_consultant\self_incubated_koc_5.py' describe

# 读取并预览两种样式，不上传、不发消息
& 'D:\anaconda3\python.exe' 'C:\Users\Ludim\.codex\skills\data-push\scripts\channels\market_consultant\self_incubated_koc_5.py' preview --report-type both
```

## 必须保留的边界

- 未登记部门、渠道、部署或 adapter 直接报错，不默认套用市场顾问部规则。业务语义分别来自 [市场顾问部](../market-consultant-dashboard-sql/SKILL.md) 和 [青橙](../qingcheng-dashboard-sql/SKILL.md)。
- 任务、自动化、配色和配置都必须有唯一所有者：`windows_task_name` 只属于一个本地渠道；妙搭 app/runtime 只属于一个部门部署，workflow 的 module、automation namespace、ledger namespace 和 style owner 互不重叠。不同部门不得共享这些可变资源。
- 群ID、发送身份和源表独立配置；改群名不能改变收件人，新增群必须明确授权并核验。一个目标失败不得把成功目标重复发送。
- 图表/文案纯计算、只读取数、预览、真实投递、启用调度、妙搭发布和启用自动化是不同阶段。维护、重命名和测试不授权消息发送、Base写入、天宫修改、本地任务恢复、妙搭发布或自动化启用。
- 新增或启用本地播报时必须分配连续且唯一的 `stagger_order`、`windows_task_name` 和对应启动分钟，并通过 `validate_layout.py` 的全局错峰校验；详细规则与实时状态查看见 [运行与验收](references/operations.md)。
- 完整分页、同快照、上游证据、新鲜度、@账号/群成员、幂等及消息读回按渠道规则执行。真实回执持久化后才删除该目标本次PNG；失败或结果不确定保留图片，不自动切身份或盲目重发。
- 运行状态和台账位于代码仓库外，并按 `domain/surface/deployment/target` 隔离；迁移或重命名不清空历史台账。市场顾问部的图片、时间窗和重试细节只保留在对应渠道与本地运行文档中，不能成为青橙或妙搭默认值。
- 本地飞书命令以官方 Skill 和当前 CLI 帮助为准：Base → [lark-base](../lark-base/SKILL.md)，账号 → [lark-contact](../lark-contact/SKILL.md)，消息 → [lark-im](../lark-im/SKILL.md)，身份/授权 → [lark-shared](../lark-shared/SKILL.md)。妙搭 app、环境、数据库、release 和自动化走 [lark-apps](../lark-apps/SKILL.md)。不要保存凭证到配置或预览元数据。

## 离线验证

```powershell
& 'D:\anaconda3\python.exe' -m pytest 'C:\Users\Ludim\.codex\skills\data-push\tests' -q
& 'D:\anaconda3\python.exe' 'C:\Users\Ludim\.codex\skills\data-push\scripts\validate_layout.py'
```

`validate_layout.py` 会同时核验本地渠道与妙搭部署的身份、路径和资源唯一性，但不会调用 API、发布应用、启停任务或发送消息。新增格式必须增加接口测试、部门口径测试和离线预览；不要通过正式群发消息验证代码重构。
