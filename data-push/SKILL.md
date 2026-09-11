---
name: data-push
description: 按部门和渠道编排数据分发：Base明细聚合、图片和文字预览、负责人提醒、固定群ID多群投递与本地定时；也维护Excel按人私聊分发和妙搭静态看板刷新。用于新增渠道脚本、调整推送格式或接手推送任务。业务指标先走所属部门Skill，普通妙搭应用开发走lark-apps。
metadata:
  short-description: "跨部门、按渠道的数据推送与安全分发"
---

# data-push

为每个渠道维护独立入口和配置，共享飞书基础能力。一个渠道可投递多个群；不同部门的指标、期次、范围和提醒规则不得互相继承。

## 先选工作流

| 需求 | 先读 |
|---|---|
| 新增渠道、重构脚本、扩展推送形式 | [架构与目录](references/architecture.md) → [接口契约](references/interfaces.md) → [扩展指南](references/extension-recipes.md) |
| 修改群、渠道、数据源、开关或时点 | [配置规范](references/channel-configuration.md)；再读目标渠道规范 |
| 当前自孵化KOC播报 | [市场顾问部渠道规则](references/departments/market_consultant/self_incubated_koc_5.md) |
| 商务KOC数学双渠道播报 | [商务KOC数学规则](references/departments/market_consultant/business_koc_math.md) |
| KOC与抖音私信主管维度播报 | [KOC与抖音私信规则](references/departments/market_consultant/supervisor_koc_douyin_sync.md) |
| 自孵化KOC 5元纯课初三主管播报 | [KOC初三规则](references/departments/market_consultant/supervisor_self_incubated_koc_5_grade_9.md) |
| 集团私域与APP主管维度播报 | [集团私域与APP规则](references/departments/market_consultant/supervisor_private_app_sync.md) |
| 青橙渠道接入 | [青橙边界](references/departments/qingcheng.md)；业务语义由青橙Skill确认，尚无已启用渠道 |
| 定时、重试、回执、图片清理、暂停或恢复 | [运行与验收](references/operations.md) |
| Excel按人切割私聊 | [Excel分发](references/workflows/excel-distribution.md) |
| 妙搭静态数据看板刷新、发布 | [妙搭看板](references/workflows/miaoda.md) |

只读取本次操作需要的知识，不把全部参考文档加载进上下文。

## 入口与配置

- 注册表：`config/channels.json`，按 `domain/channel_id` 唯一定位，不按显示名称定位。
- 每渠道配置：`config/departments/<domain>/<channel_id>.json`。
- 每渠道脚本：`scripts/channels/<domain>/<channel_id>.py`，只绑定一个渠道。
- 通用入口：`scripts/channel_push.py`；旧 `group_push.py` / `scheduled_push.py` 等文件名保留为兼容门面，不复制业务逻辑。
- 共享实现：`scripts/lark_delivery/common/`；业务实现：`scripts/lark_delivery/domains/<domain>/`。
- 当前已配置 `market_consultant/self_incubated_koc_5`、`market_consultant/business_koc_math`、`market_consultant/supervisor_koc_douyin_sync`、`market_consultant/supervisor_private_app_sync` 与 `market_consultant/supervisor_self_incubated_koc_5_grade_9`；各自的状态目录、群、渠道集合和启停相互独立。启停状态以渠道配置和Windows任务实时读回为准，不根据旧对话推断。

```powershell
# 本地说明，无API调用；所有Python示例使用D:\anaconda3
& 'D:\anaconda3\python.exe' 'C:\Users\Ludim\.codex\skills\data-push\scripts\channels\market_consultant\self_incubated_koc_5.py' describe

# 读取并预览两种样式，不上传、不发消息
& 'D:\anaconda3\python.exe' 'C:\Users\Ludim\.codex\skills\data-push\scripts\channels\market_consultant\self_incubated_koc_5.py' preview --report-type both
```

## 必须保留的边界

- 未登记部门/渠道/适配器直接报错，不默认套用市场顾问部规则。业务语义分别来自 [市场顾问部](../market-consultant-dashboard-sql/SKILL.md) 和 [青橙](../qingcheng-dashboard-sql/SKILL.md)。
- 群ID、发送身份和源表独立配置；改群名不能改变收件人，新增群必须明确授权并核验。一个目标失败不得把成功目标重复发送。
- 图表/文案纯计算、只读取数、预览、真实投递和启动调度是不同阶段。维护、重命名和测试不授权消息发送、Base写入、天宫修改或恢复计划任务。
- 新增或启用本地播报时必须分配连续且唯一的 `stagger_order`、`windows_task_name` 和对应启动分钟，并通过 `validate_layout.py` 的全局错峰校验；详细规则与实时状态查看见 [运行与验收](references/operations.md)。
- 完整分页、同快照、上游证据、新鲜度、@账号/群成员、幂等及消息读回按渠道规则执行。真实回执持久化后才删除该目标本次PNG；失败或结果不确定保留图片，不自动切身份或盲目重发。
- 当前运行状态和台账位于代码仓库外；迁移目录不清空历史台账。周五至周日只发送结果图，不发送过程图；结果图使用5min橙色进度条及按截面单效降序的绿→红色阶。所有已启用的本地播报仅在13:20、17:20、21:20起按错峰顺序启动，以各自启动分钟为基准每2分钟重试，最晚只在:50再尝试；运行进度只写`live-status.json`，进程结束必须删除，不生成新的持久化运行日志。
- 飞书命令以本地官方Skill和当前CLI帮助为准：Base → [lark-base](../lark-base/SKILL.md)，账号 → [lark-contact](../lark-contact/SKILL.md)，消息 → [lark-im](../lark-im/SKILL.md)，身份/授权 → [lark-shared](../lark-shared/SKILL.md)。不要保存凭证到配置或预览元数据。

## 改造后的验证

```powershell
& 'D:\anaconda3\python.exe' -m pytest 'C:\Users\Ludim\.codex\skills\data-push\tests' -q
& 'D:\anaconda3\python.exe' 'C:\Users\Ludim\.codex\skills\data-push\scripts\validate_layout.py'
```

测试按接口、部门、集成、旧兼容和工作流分组；外部进程默认被测试拦截。新增格式必须增加接口测试、业务口径测试和本地预览核对；不要通过正式群发消息验证代码重构。
