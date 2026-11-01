# 已授权期次收紧与过期恢复

用于用户明确同时授权收紧取数时间/期次和续期的既有启用且过期数据集。它是独立恢复操作，不改变普通SQL替换的 `SCHEDULE_EXPIRED` 拦截，也不扩大普通日期续期命令的仅日期范围。原SQL预览失败使原生保存不可用时，先实测已审阅的收紧候选，再将该候选与续期日期作为同一明确审阅的保存。

`plan-data-center-period-renewal --domain market --dataset-id <menu_set_id> --baseline-file <最新完整只读基线.sql> --sql-file <候选.sql> --schedule-start YYYY-MM-DD --schedule-end YYYY-MM-DD` 重新读取精确线上身份、SQL、字段和同步配置。基线文件必须与当前SQL Hash一致。候选只允许正向WHERE合取中的 `>=` 日历日期或期次字面量向后移动；AST及源文本双重还原须与原SQL完全一致，因此不能改字段、部门、渠道CASE、NULL范围、关联、公式、注释或其他字节。禁止OR/NOT/CASE中的边界变化、多语句及非查询SQL。续期仍限90天，原频率、告警、字段元数据和开关全部保留。

`apply-data-center-period-renewal --plan-file <plan.json> --expected-plan-sha256 <精确Hash> --confirm-production-write` 再验证文件、收紧证明和线上基线，以目标独占锁运行。原生编辑器回读基线后填入候选，按精确候选Hash预览一次，成功且字段数不变才选择日期并保存。每个发送请求均核对目标、候选SQL、全部字段和调度；持久意图最多一次保存，不确定写入停止且不自动回滚。

完成恢复必须回读候选SQL Hash、全部原字段及新周期未过期。默认模式不触发正式抽数，也不能宣称业务刷新完成；可随后以独立普通同SQL `--allow-noop` Replacement Plan刷新。若用户同时明确授权重新抽数，可使用下述绑定的保存后刷新模式，避免重复SQL预览和保存。若用户仍明确要求严格先仅日期续期再改SQL，则不能采用此独立合并恢复操作。

字段元数据按字段名与持久字段ID稳定排序后比较全部属性；详情接口按字段ID排序、原生预览保存按SQL输出排序的数组顺序差异不视为字段变化。重复/缺失字段名仍阻断，字段ID、类型编码、显示名和其他属性必须一致；SQL投影及其输出顺序仍由严格源文本/AST还原证明保持。

用户同时明确授权重新抽数时，Plan可显式加 `--refresh-after-save`。该策略绑定在父计划Hash中；保存回读后再次核验身份、候选SQL Hash、全部字段和新周期，生成具有实际taskId/调度Hash/运行基线及预算1的子计划。原生立即执行请求经精确ID和持久单次意图门禁，只触发一次，再等待新SUCCESS。无需重复预览或再保存相同SQL；该模式只有新抽数SUCCESS后才返回fully_verified。任何保存或抽数请求已发出而状态不确定均停止自动写重试，只读回查。
