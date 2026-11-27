# 山东本地化群播报

原始渠道为“北京直播山东”，采用精确匹配。两条申请由王绅宇填写，数据范围均为初三，展示门槛为同年级、同架构下退后线索≥5。用户于2026-11-14确认显示模块总计，按可见人员的原始分子、分母重算比率、频次和单效。

| 配置 | 运营申请 | 目标群 | 组件ID |
|---|---|---|---|
| 初三主管 | reczz28Z69Zq9c5b | oc_3be9b914593ba873276cc5aa0a5007fc | shandong_supervisor |
| 本地化顾问 | reczz28Z69oCFwc8 | oc_b5dee8b192c11bb8a131ce40c41d5236 | shandong_advisor |

两条组件分别位于 `grade9_supervisor_bundle.json`、`localization_advisor_bundle.json`，显示名称为山东本地化，图内排列在广东本地化之后。共用各自已有群任务、14:00/19:00时点及自然周周五期次，周一至周四过程、周五至周日转化。

过程按5min率降序，转化按截面单效降序。主管提醒对应指标最低值及全部并列人员，顾问提醒底部10%，每年级至少一人且临界并列全部纳入。人员提醒遵循全局原生@与姓名文字兜底规则。

本期无源记录时记录 `skipped_no_source_rows`。门槛以下记录 `skipped_no_eligible_rows`。计算、列宽测量或制图异常只影响该组件，其他已就绪组件继续合图及投递。定时任务使用真实业务期次校验，预览期次可以通过已审计的其他期次事实进行本地样式验证。

新申请使用 `request_key=shandong` 生成稳定申请编号，各群分别为 `market_consultant/grade9_supervisor_bundle/shandong` 与 `market_consultant/localization_advisor_bundle/shandong`。运营、技术记录通过各自申请record_id关联，同群的全部技术快照同步包含完整群配置。部署、后台预览和首轮自然投递分别验收。
