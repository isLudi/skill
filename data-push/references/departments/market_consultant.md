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

渠道配置中心 Base 的新增三列已按本部门 9 条申请填写：2 条负责人、4 条主管、3 条顾问；其中 8 条过程和转化均取“最低值”，亚飞 B 站初三顾问取“底部10%（每年级至少1名）”。现有 `并列处理=全部提醒` 继续表达最低值并列者的提醒方式。Base 只是申请镜像，执行仍以各渠道本地配置和下列专项规则为准，不使用青橙的人数上限。

| 渠道或工作流 | 专项规则 |
|---|---|
| 自孵化 KOC 5 元纯课 | [分年级精简与进量播报](market_consultant/self_incubated_koc_5.md) |
| 商务 KOC 数学 | [双渠道与进量播报](market_consultant/business_koc_math.md) |
| KOC 与抖音私信主管 | [高中主管播报](market_consultant/supervisor_koc_douyin_sync.md) |
| KOC 初三主管 | [双渠道初三播报](market_consultant/supervisor_self_incubated_koc_5_grade_9.md) |
| 亚飞 B 站初三主管与顾问 | [初三双维度播报](market_consultant/supervisor_yafei_grade_9.md) |
| 集团私域与 APP 主管 | [多渠道同步播报](market_consultant/supervisor_private_app_sync.md) |
| 朱博士视频号 49 | [顾问播报](market_consultant/supervisor_zhu_doctor_video49.md) |
| 陈瑞春 | [顾问播报](market_consultant/supervisor_chenruichun.md) |

## 2026-09-13 跨渠道指标归属故障

### 故障原因

- 数据中心数据集 2253 先对事实表原始行做 `DISTINCT`，再按期次、渠道、规则、年级、组织和顾问等分配粒度汇总。只有来源经理为韩正卿的抖音私信线索分母改取 `merge_assign_lead_count` / `merge_valid_lead_count`；收款、退费、到课、沟通等事实仍按原始行相加。
- `market2lark` V10 在上述分配维度形成之后，又用 `ROW_NUMBER() OVER (PARTITION BY period_name, lead_id)` 全局只保留一个维度行。同一 lead 横跨渠道、顾问或组织时，事实会被任意归到其中一行，导致渠道图片中的收款、退费及截面单效失真。
- V11 用“期次 + lead”窗口求和后再保留一行，虽然试图保住全局金额，却仍把求和结果归到单一渠道/顾问，不能满足渠道级守恒，因此不是完整修复。
- 事故排查时，数据中心截图为“渠道：全选”，而群播报是单渠道；截图与播报还可能来自不同小时快照。未对齐期次、渠道、年级、组织和 `dt/hour` 时，二者不能直接比较。

### 修复与生产验收

- `market2lark` V13（版本 `205491`、执行文件 `818418`）删除全局 lead 选行，保留 2253 的 `DISTINCT 原始行 -> 分配粒度聚合` 合同；记录键改为 `期次|渠道|lead_id|user_id|顾问账号`，Python 唯一性校验同步到该键。45 个下游字段、渠道映射和两阶段 Bitable 替换协议保持不变。
- 发布后源码 SHA-256 为 `757b68e2df3376278496551a440d10c0fd04bb5421e3baa882edf0b9056310b3`，查询 SHA-256 为 `37b7d508ecae42b3e686cfbf3ddfd1272aab87a58607dd867c85cda94e207ffa`。
- 生产执行 `170476273` 成功：查询与回读均为 18,870 行，覆盖 20260911期和 20260918期、47 个渠道、未识别渠道 0；先创建并回读新记录，再删除旧 18,841 条记录。六个群配置随后锁定到该版本。
- 六个群共 11 个实际报表面使用同一 Bitable 修订 `5900` 和快照 `20260913-13` 完成只读预览；903 项比率/单效复算无误，全部 `message_sent=false`。

### 防回归门禁

- 任何源查询去重、窗口或记录键变更，都必须按“期次 + 渠道 + 年级 + 经理 + 主管”比较变更前后数据，并检查图片门槛以下的隐藏行；只验证全局总额不足以证明渠道归属正确。
- 对每个已配置渠道分别证明退前/退后线索、收款、退费、当期收款、到课和沟通指标的加法守恒；抖音 merge 字段只允许替换线索分母，不能替换财务事实。
- 生产写入必须保留“创建新记录 -> 完整回读 -> 删除旧记录 -> 最终回读”顺序，并核对期次、渠道数、字段数、行数和快照清单。
- 数据中心与群播报对账前，必须显式对齐期次、渠道筛选、年级/组织粒度和 `dt/hour`。低于图片最小退后线索门槛的财务行仍属于底层渠道总额，不得因未显示在图片中而判定为丢失。
- 手工 Tiangong2 执行只能用于受控验收；Windows `preflight-now` 必须继续只接受当前计划批次的已验证执行文件，不得用手工成功放宽定时门禁。
