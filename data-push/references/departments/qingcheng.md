# 青橙接入边界

`qingcheng` 已作为独立部门登记，但当前没有登记可执行的本地渠道、妙搭部署、源表、群ID、周期规则或适配器。未知渠道/部署必须阻断，不能落到市场顾问部默认 KOC 渠道，也不能使用 `runtime/cloud-data-push-miaoda`。

业务语义入口：[qingcheng-dashboard-sql](../../../qingcheng-dashboard-sql/SKILL.md)。用户明确新增青橙渠道后，先确认：

- 权威数据源、业务范围、字段和唯一键；
- 计算粒度、图片展示粒度、指标分子/分母及零分母语义；
- 期次和业务日历，过程/转化等推送内容的适用日期；
- 真实目标群ID、发送身份、提醒对象与账号来源；
- 数据就绪证据、重试/截止、去重和读回策略。

本地实现随后创建本部门 adapter，并按 [扩展配方](../extension-recipes.md) 注册自己的渠道配置与脚本。妙搭实现默认创建新的 runtime 工程和新的 app，再登记为 `qingcheng/miaoda/<deployment_id>` 并添加本部门 workflow；必须使用独立模块、Secret、Base/群/机器人坐标、自动化 namespace、托管台账、fixture、renderer 和配色。

公共 Base/IM 客户端、哈希和绘图原语可以复用；市场的周五期次、10 条门槛、最低经理/主管、字段列、market2lark 日志协议、Windows 分钟、妙搭触发器及蓝橙红绿配色不可自动继承。若用户明确要求两个部门共用一个妙搭 app，先停在隔离设计与风险审阅，不直接把青橙分支写入现有市场模块。
