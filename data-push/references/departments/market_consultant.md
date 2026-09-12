# 市场顾问部推送边界

业务语义入口：[market-consultant-dashboard-sql](../../../market-consultant-dashboard-sql/SKILL.md)。`data-push` 只把已确认的市场顾问部口径实现为本地或妙搭推送，不把这些规则提升为跨部门默认值。

## 当前资源

- 本地渠道以 `config/channels.json` 中 `market_consultant/*` 为准；每个渠道拥有独立配置、入口、Windows 任务和状态目录。
- 妙搭唯一登记部署为 `market_consultant/miaoda/cloud_data_push`，其中 `supervisor_koc_douyin_sync` workflow 对应当前主管播报；源码仍在 `C:\Users\Ludim\.codex\runtime\cloud-data-push-miaoda`，app 身份由该工程 `.spark/meta.json` 读回。
- 该妙搭工程目前是市场顾问部主管 KOC/抖音推送原型，不是通用跨部门宿主，也未因存在本地代码或 app 资产而自动接管 Windows 任务。

## 本部门所有的个性化规则

市场顾问部自行持有字段投影、自然周五期次、高中/年级范围、负责人和主管粒度、最小退后线索门槛、加权指标、提醒对象、图片列、排序、颜色阈值和文案。当前本地实现位于 `scripts/lark_delivery/domains/market_consultant/`；妙搭原型仍把对应实现放在自己的 `server/modules/cloud-push-demo/` 内。

两种执行面可以进行结果等价比较，但不能共享可变运行资源：本地 Windows 任务、SQLite/文件状态与妙搭自动化、PostgreSQL 台账、Secret、release、测试群各自独立。同一市场 app 内的不同 workflow 也必须有独立 module、automation namespace、ledger namespace 和业务合同。迁移或切换必须逐阶段验证，不能因为妙搭 dry-run 成功就暂停本地任务。

具体渠道的范围、指标、配色和提醒规则继续以 `references/departments/market_consultant/` 下对应文件为准。
