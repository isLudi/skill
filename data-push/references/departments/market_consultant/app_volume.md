# APP渠道进量播报

渠道键为 `market_consultant/app_volume`，入口为 `scripts/channels/market_consultant/app_volume.py`。目标群固定为 `oc_9dc33c5731ce57c03d0589a2ac1d2e99`，展示名为“【APP】&【高阳】市场业务对接”，发送身份为管家机器人。

## 数据与指标

按进量原始表 `tblGUCxgUTZPjv3c` 的分配规则渠道匹配APP，渠道名经Unicode NFKC规范化、去首尾空白后忽略大小写精确比较。使用APP最新可用期次，按实际年级汇总。预估量级和实际进量直接汇总原始计数。

图片列顺序为期次、年级、预估量级、实际进量、线索留存率、人均带班、量级完成度。线索留存率为合计退后线索除以合计退前线索，人均带班为合计实际进量除以合计接量顾问数，量级完成度为合计实际进量除以合计预估量级。总计行使用合计分子、分母重算。

年级按初三、高一、高二、高三及其他实际分类排列，缺失分类跳过。深蓝表头和总计行、蓝色留存率数据条、橙色完成度数据条沿用KOC进量模板。文字提示完成度最低的一个年级，最低值并列按图片顺序取第一个。消息使用原生post和一张PNG。

本报告读取进量表的8个字段。异常流量占比在本报告中关闭。源数据、PNG、原生post、预览及配置均属于本渠道。

## 调度与验收

每天17:20启动，每2分钟重试至17:50，与KOC进量窗口一致。Windows任务为 `Codex-Lark-Market-APP-Volume-Push`，状态目录为 `runtime/channel-broadcast-push/market_consultant/app_volume`。调度读取同小时17:00的 `market_consultant.volume` 发布登记，校验唯一SCHEDULE执行、绑定版本及源码Hash、完整stage、创建删除数量和Base全量回读。

发送前复核配置Hash、生产者绑定、执行编号、Base revision、PNG Hash、机器人身份及发送群成员资格。重试沿用确定的幂等键，有message_id时只补回读。其他群任务使用独立进程、锁和台账。

预览命令为渠道入口的 `preview --state-dir <目录>`。任务注册脚本为 `scripts/register_app_volume_push.ps1`，支持 `-CreateDisabled` 与已授权的 `-ConfirmEnable` 两种阶段。新目标群的机器人入群核验通过后启用调度，本地配置和Base登记分别回读验收。
