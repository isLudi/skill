# 本地部门与渠道配置

本文件只描述 `execution_surface=local` 的 Python/Windows 配置。当前配置样本：[自孵化KOC-5元纯课](../config/departments/market_consultant/self_incubated_koc_5.json)。这是本地执行面的唯一事实来源，不在 Skill 正文、入口脚本或旧兼容 JSON 再保存第二份同值配置。妙搭部署身份与 runtime 绑定读 [妙搭部署配置](deployment-configuration.md)；不能把本地 JSON 整体复制成云端环境变量。

## 注册和命名

- domain使用稳定英文ID：`market_consultant`、`qingcheng`。中文展示名不作key。
- channel_id使用snake_case，主业务渠道名称保存在 `channel`；同一群同一口径的有序多渠道可登记 `channels`，其中首项必须等于 `channel`，取数时逐项精确匹配并独立生成回执。
- `config/channels.json` 的key是 `domain/channel_id`；值为config目录内的相对路径。
- `scripts/channels/<domain>/<channel_id>.py` 只调用 `cli.main(bound_channel="domain/channel_id")`，不接受跳转到其他部门/渠道的参数。
- 部门业务Skill登记用于语义路由；登记部门不代表已有可执行渠道。
- 这些 key 不包含执行面，是因为 `channels.json` 当前只登记本地渠道；妙搭使用 `domain/miaoda/deployment_id` 的独立 key。

## 配置字段

| 字段 | 用途 / 约束 |
|---|---|
| schema_version | 当前为1；不默默接受未知版本 |
| domain, channel_id, channel, adapter | 精确身份与已实现的adapter；domain不能互相补齐 |
| source | 原始链接/表ID/报告profile等；当前市场配置的source_url只为旧格式兼容，raw_source_url用于当前模式；`channel_match` 必须声明 `field=渠道`、`case_sensitive=true` 和与 `channels` 同序的规范值映射 |
| sender | identity、name、open_id；机器人/用户不可在失败时自动切换 |
| targets | 目标列表：id、chat_id、display_name、enabled；ID唯一、群ID不重复，display_name可变 |
| report | 部门adapter支持的策略参数；当前市场使用period_rule、星期数组、excluded_grades、minimum_post_leads |
| schedule | enabled、first_send_at、timezone、hours、windows_task_name、stagger_order、prepare/send/deadline分钟和retry_minutes |
| upstream | 该渠道自己的证据绑定；当前市场为精确Tiangong任务/版本/执行文件/源码Hash，不用于青橙猜测 |
| base_identity | Base只读身份，与sender分开 |
| state_dir | 渠道独占目录，不同渠道不能相同或父子交叠；原主群历史路径保留 |

目前市场adapter只支持已审阅的自然周周五期次、周一至周四过程、周五至周日仅结果、每日13/17/21三时点与共享重试窗口。已启用本地任务按 `stagger_order=1..N` 连续编号，对应 `prepare_minute=send_minute=19+stagger_order`，即从 `:20` 起每任务错开1分钟；`retry_minutes=2`、`deadline_minute=50` 固定。`windows_task_name` 必须与真实任务唯一对应。单纯改JSON为未实现规则会被调度器及 `validate_layout.py` 阻断；不同规则必须扩展相应adapter并补测试。

## 一渠道多群

仅在用户授权新增目标后向targets添加一个新元素，例如：

```json
{"id":"second_team","chat_id":"oc_exact_verified_id","display_name":"展示名","enabled":true}
```

示例ID不是可执行生产目标。先查真实群ID、核验机器人及@人员成员资格，再填写。

- 不指定 `--target` 时处理全部enabled目标；指定时只能使用登记ID，可重复参数选择多个。
- 默认第一个目标沿用渠道state_dir；额外目标用 `state_dir/targets/<id>`。每目标图片、锁和台账互不影响。
- 群改名只更新display_name；不能更改chat_id来“修复”名字。
- 首个目标ID、排序和state_dir与历史状态有关，不可随手重排或复用。迁移状态路径须另行计划与验证，不清空台账。
- `schedule.enabled=false` 只关闭定时发送，不妨碍本地预览；`run --confirm-send` 不会把它改为true。
- 渠道读取先使用服务端过滤，再按 `source.channel_match` 在本地进行大小写敏感的精确过滤；服务端过滤可能不区分大小写，`raw_read_audit` 必须记录服务端返回数与本地排除数。
- 添加第二个群不会创建第二个Windows任务；渠道入口负责展开目标，各目标在同一轮内独立等待和发送。

## 与妙搭部署的关系

妙搭记录可用 `source_channel_ref` 引用一个同部门本地渠道，供业务等价对照。该引用不授予发送或切换权限，也不继承本地群、机器人、Windows 任务、状态目录和启停；云端必须从自身部署和服务器固定配置独立核验这些资源。

## 兼容配置

`config/push_source.json` 和 `config/scheduled_push.json` 只含 `channel_ref / target_id`，旧命令用catalog展开。不要在指针文件添加同名业务字段试图覆盖；修改真正的渠道配置。

新增渠道默认 `schedule.enabled=false`，目标内容在预览和授权前不投递。不要从私聊测试推导群发或启动调度许可。
