---
name: data-push
description: 按部门、渠道与执行面设计和维护本地 Python/Windows 及飞书妙搭数据推送。用于推送配置、预览、调度、投递、回执、迁移和渠道配置 Base；青橙本地批次按审定时段启动并每两分钟重试；业务口径与渠道特例从对应知识库读取。
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

### 青橙本地批次（2026-10-08 调整）

青橙项目部当前启用的本地过程批次：公海/私域/抖音私信六群及伙伴三群为周二至周四 `13:50`、`17:50`、`21:50`；专项四渠道仅 `13:50`。每两分钟重试，窗口持续 50 分钟，跨小时归一化为原始槽位，最晚为 `14:40/18:40/22:40`。SEC 五报告保持周二至周日 `12:00/16:00/20:00` 启动、每两分钟重试至 `:50`；不受本次提前十分钟调整影响。

转化使用同一 `run_qingcheng_transformation.py`，两类独立任务：普通主管/顾问九条报告由 `Codex-Lark-Qingcheng-Transformation-GroupPush` 在周五至次周周一每天 `13:52/17:52/21:52` 启动，保留两分钟错峰；专项学部四条报告由 `Codex-Lark-Qingcheng-Special-Transformation-GroupPush` 通过 `--audience dept` 每天仅 `13:50` 启动。取消周一凌晨单档，周一期次仍回溯到上周五。两类任务使用独立锁、源分页目录、批次和回执，每两分钟重试，窗口持续 53 分钟；普通末次有效重试为 `14:44/18:44/22:44`，专项为 `14:42`。配置以 `transformation_batch.json` 的 `business_calendar` / `dept_schedule.business_calendar` 为准，与 Base 配置时点保持一致。各群准备、解析、发送失败独立记录，正常推送不回写配置 Base。

四个执行器的 `upstream` 必须与当前已验证的 `qing2lark_guocheng` 绑定一致（菜单 `103625`、task `47728`、Nezha `67318`、V29/version `207387`/exec `831981`）；上游任务改版后，先读回最新版本和执行文件，再同步本地批次配置及技术 Base，不能只改任务计划程序。

上游审计仍按固定槽位减 20 分钟后向下取整到小时：过程/专项/伙伴的 `13:50/17:50/21:50` 对应 Nezha `13:00/17:00/21:00`（实际约 `13:40/17:40/21:40`），SEC `12:00/16:00/20:00` 对应 `11:00/15:00/19:00`。重试跨小时也使用原始槽位审计；唯一成功执行、最新执行、版本/执行文件和完整 stage 日志门禁不变。

天宫2 的 `qing2lark_guocheng`（过程）与 `qing2lark_zhuanhua`（转化）是两条独立上游，不能互换 task、版本或执行文件。调度保持每 2 小时一次的全部 `:40` 时刻（`23:40/01:40/03:40/05:40/07:40/09:40/11:40/13:40/15:40/17:40/19:40/21:40`）；两条任务已按精确 task/Nezha ID 更新并回读。`qing2lark_zhuanhua` 当前绑定 V6/version `207547`、源码 SHA-256 `97aed7e48398d6a4321e0b11fab0cff44de67edb8f5f21622e7d1424a0521a39`，T-1 至 T-5 探针已发布；上游 task ID `47775`、Nezha `67397` 未变化。USQL operator 提供 `plan-task-schedule-update`/`apply-task-schedule-update` 与 `plan-nezha-schedule-update`/`apply-nezha-schedule-update`，调度修改后必须重读版本/执行信息并同步本地配置。

## 离线验证

按变更范围运行受影响测试、`scripts/validate_layout.py` 和对应渠道的无发送预览。Python 使用机器本地 `machine.local.json` 中的 `executables.python`。验证不发送消息，不启停任务，不修改上游生产资源。

run 驱动脚本（`run_*.py`）改造后除 py_compile/单测外，必须再做两项：① `pyflakes` 或等价静态检查——py_compile 查不出函数体内未定义名（2026-10-02 转化批次因漏 import `retry_transport` 首轮调度 8 个 level 全 blocked）；② 盯改造后首个调度窗口的 push_log result（`machine.local.json` 的 `paths.push_log_root` 下按日期落盘）。注意任务 MultipleInstances=Parallel：手动触发与自动触发并行时，第二个实例被 `_single_instance()` 文件锁拒绝会以 exit 1 + 空 outcomes 退出，这是防重发保护不是故障。
