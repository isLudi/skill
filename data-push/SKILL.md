---
name: data-push
description: 按部门、渠道与执行面设计和维护本地 Python/Windows 及飞书妙搭数据推送。用于推送配置、预览、调度、投递、回执、迁移和渠道配置 Base；业务口径与渠道特例从对应知识库读取。
metadata:
  short-description: "按部门与执行面隔离数据推送的配置、运行和回执"
---

# data-push

数据推送使用显式地址：本地为 `domain/local/channel_id`，妙搭为 `domain/miaoda/deployment_id/workflow_id`。先确认部门，再确认执行面与已登记资源；不要从群名、任务名、配色或现有代码反推归属。未登记的地址保持未就绪，不自动继承其他部门的口径或执行资源。

## 路由与知识库

| 目标 | 入口 |
|---|---|
| 市场顾问部 | [部门边界与渠道索引](references/departments/market_consultant.md)；业务语义走 [市场顾问部 SQL Skill](../market-consultant-dashboard-sql/SKILL.md) |
| 青橙项目部 | [部门边界与渠道索引](references/departments/qingcheng.md)；业务语义走 [青橙 SQL Skill](../qingcheng-dashboard-sql/SKILL.md) |

部门文件负责引导到对应渠道、报表及执行面的专项规则。指标定义、筛选范围、排名提醒、图片列与配色、群和时点、源表身份、任务状态及故障历史只写在所属部门或渠道知识库及受治理配置中，不写进本入口。

## 按任务选择参考

| 工作 | 读取顺序 |
|---|---|
| 设计架构或迁移执行面 | [架构与隔离](references/architecture.md) → [扩展指南](references/extension-recipes.md) → 目标部门知识库 |
| 新增或修改本地渠道 | [本地渠道配置](references/channel-configuration.md) → [接口契约](references/interfaces.md) → 目标部门和渠道知识库 |
| 新增或修改妙搭部署 | [妙搭部署配置](references/deployment-configuration.md) → [妙搭云端播报](references/workflows/miaoda-broadcast-migration.md) → 目标部门知识库；平台操作走 lark-apps |
| 运营申请与技术参数 Base | [渠道配置中心 Base](references/channel-registry-base.md) → 目标部门知识库；Base 操作走 lark-base |
| 本地调度、重试、回执、状态与日志落盘 | [运行与验收](references/operations.md)（含日志存储规范）→ 目标渠道知识库 |
| Excel 按人私聊 | [Excel 分发](references/workflows/excel-distribution.md) |
| 妙搭静态看板刷新 | [妙搭看板](references/workflows/miaoda.md) |

只读取当前任务所需的参考文件；遇到缺失、过期或矛盾证据时再向对应部门知识库扩展。

## 配置与执行边界

- `config/channels.json` 登记本地渠道，部门配置位于 `config/departments/<domain>/<channel_id>.json`，入口位于 `scripts/channels/<domain>/<channel_id>.py`。`config/deployments.json` 登记妙搭部署和 workflow。两个注册表互不继承目标群、发送身份、任务、状态或授权。
- 聚合、指标、日历、图片、配色、排名和文案归部门 adapter 或部署模块所有；`scripts/lark_delivery/common/` 只承载中性传输能力。任务名、应用、自动化、台账和状态目录必须有明确且唯一的所有者。
- 纯计算、只读取数、预览、真实投递、启用调度、妙搭发布和启用自动化分别验收。前一阶段的成功不自动授权后一阶段；维护与测试不授权群消息、生产任务或发布。
- 群以稳定 ID 绑定，发送身份与源表分别核验。完整分页、同快照、上游证据、新鲜度、群成员、幂等、结果读回和不确定结果处理见 [运行与验收](references/operations.md) 与目标渠道规则。
- 每次运行的日志按 [运行与验收](references/operations.md) 的日志存储规范追加到机器本地 `paths.push_log_root`（数据盘、非系统盘、且在 `D:\GAOTU` 之外）；写日志失败只降级告警，不得阻断投递。任何跳过路径都必须留下可事后还原的记录。
- 同群多个渠道分别生成、发送和记回执；空渠道跳过必须有当期上游证据。失败、跳过和重试按渠道隔离，规则见 [本地渠道配置](references/channel-configuration.md)。
- Base 是需求和实施台账；生产事实源仍是受治理的本地配置。角色权限按部门失败关闭，只读候选不直接发布或启用推送；具体字段和权限方案见 [渠道配置中心 Base](references/channel-registry-base.md)。
- 飞书 Base、联系人、消息、身份和妙搭平台操作分别走 [lark-base](../lark-base/SKILL.md)、[lark-contact](../lark-contact/SKILL.md)、[lark-im](../lark-im/SKILL.md)、[lark-shared](../lark-shared/SKILL.md)、[lark-apps](../lark-apps/SKILL.md)。不要把凭证写入配置或预览产物。

## 离线验证

按变更范围运行受影响测试、`scripts/validate_layout.py` 和对应渠道的无发送预览。Python 使用机器本地 `machine.local.json` 中的 `executables.python`。验证不发送消息，不启停任务，不修改上游生产资源。
