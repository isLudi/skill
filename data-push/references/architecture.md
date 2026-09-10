# 架构与目录

本技能有三条独立工作流：按渠道群播报、Excel私聊分发、妙搭静态刷新。它们共享CLI执行能力，但不共享业务口径或发布权限。

## 群播报依赖方向

```text
渠道脚本 → core注册/配置/目标选择 → 部门adapter → 只读ReportPorts
                                   ├→ 纯聚合 → 绘图 → 文案 → 本地预览
                                   └→ 部门scheduler → 上游证据/时间门禁
                                                        → 逐群回执/读回
```

`common` 不导入部门或旧实现；`core` 仅由 `registry.py` 显式选择部门adapter，其他core模块不导入业务实现。当前部门实现不导入 `legacy`。禁止在共享库里判断“如果是青橙就用市场规则”。

## 文件职责

| 位置 | 用途 | 允许放什么 |
|---|---|---|
| `scripts/channels/<domain>/<channel_id>.py` | 每渠道独立可执行入口 | 固定渠道key；不复制CLI或业务代码 |
| `config/channels.json` | 注册表 | 部门语义Skill和渠道配置路径 |
| `config/departments/<domain>/<channel_id>.json` | 单渠道唯一配置 | 源、群列表、身份、策略参数、调度、上游绑定、状态目录 |
| `scripts/lark_delivery/core/` | 配置、接口和多目标协调 | 显式路由、隔离、目标结果、OS锁；没有业务指标 |
| `scripts/lark_delivery/common/` | 中性飞书能力 | JSON、CLI、Base分页、群核验、图片上传/清理、字体 |
| `scripts/lark_delivery/domains/market_consultant/` | 市场顾问部现有实现 | 经理维度汇总、图片、最低值、期次、market2lark验收 |
| `scripts/lark_delivery/integrations/` | 受限外部证据适配 | 原Tiangong发布绑定核验，不执行上游生产修改 |
| `scripts/lark_delivery/workflows/` | 非群播报工作流 | Excel分发 |
| `templates/` | 复制到应用仓库的独立模板 | 妙搭刷新/导出；不能依赖本机渠道配置 |
| `tests/common,core,market_consultant,integrations,legacy,workflows/` | 对应边界的离线测试 | 合成夹具、mock、输出一致性和安全边界 |

原2400余行群推送脚本已拆成两条清晰路径：

- **当前渠道**：`workflow.py` 只负责编排；`grade_report.py` 负责聚合/排序/表图/文案；`style.py` 负责本域配色；`channels/self_incubated_koc_5.py` 负责该已审阅业务周期；`scheduler.py` 负责运行门禁及逐目标验收。
- **旧格式兼容**：`legacy/market_schema.py`（字段）、`market_aggregation.py`（选择/加权汇总）、`market_images.py`（旧布局）、`market_messages.py`（文案/内容键）、`market_source.py`（旧视图）、`market_contacts.py`（旧查人）、`market_prepare.py`（组合）、`market_delivery.py`（旧手动投递）、`market_ledger.py`（旧JSONL）、`market_helper.py`（旧辅助表）、`market_cli.py`（参数/展示）。`market_group.py` 只是兼容门面，不再承载大段实现。

旧文件名兼容是为保留用户已有命令、导入和计划任务，不是新扩展入口。新渠道不可导入旧市场门面，更不能复制其中的汇总公式。

## 状态与失败边界

每个渠道必须有不重叠的状态根目录；每个额外目标在 `targets/<target_id>` 下独立锁定、记账。当前主群沿用已有状态目录和去重键，避免因迁移重发。

多群定时并行运行，不让一个群的等待窗口阻塞其他群。每个群独立验证成员、生成自己持有的PNG、上传、保存回执和清理。共享同一个PNG路径后让第一个群删除它的做法不可用。

本地配置中的 `enabled` 是配置，不是用户授权；`--confirm-send` 不会开启已暂停的渠道。未发布/未登记的部门实现直接阻断。详见 [接口](interfaces.md)、[配置](channel-configuration.md) 和 [运行](operations.md)。
