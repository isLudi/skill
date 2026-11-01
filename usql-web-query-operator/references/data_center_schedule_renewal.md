# 过期数据集同步周期续期

适用于注册域内已经启用、且 `isExpire=true` 的既有数据集。先续期，再从线上重读完整 SQL，重新生成 SQL 替换计划；不能删除或忽略替换流程的 `SCHEDULE_EXPIRED` 门禁。

`plan-data-center-schedule-renewal --domain market --dataset-id <menu_set_id>` 只读精确身份、完整保存 SQL、字段和同步配置，默认计划当天至 90 天后（平台允许的三个月周期）。可用 `--schedule-start`、`--schedule-end` 指定不超过 90 天的日期区间。计划绑定全部身份、SQL Hash、字段元数据、旧同步配置和日期候选，不能作用于未过期或停用的任务。

`apply-data-center-schedule-renewal --plan-file <plan.json> --expected-plan-sha256 <hash> --confirm-production-write` 使用与 SQL 替换相同的目标独占锁。写前重新读取身份、SQL、字段和完整同步配置；任一漂移阻断。通过 USQL 原生编辑页只改变日期，网络发送前再验证完整保存请求中的目标、SQL Hash、字段、频率、时点、告警和开关，只允许一次 `saveAndUpdate`。持久声明阻断重复意图；响应不确定或回读失败时保留失败回执并停止，不能自动重试或回滚。

编辑页异步弹出的既有 `SQL执行失败 / MEM_LIMIT_EXCEEDED` 单按钮“知道了”通知可精确确认，其他弹窗仍阻断。若原生保存按钮因原预览失败而禁用，计划中的 `saved_sql_once_if_save_disabled` 策略仅允许对相同 SQL Hash 预览一次；请求发送前检查 SQL Hash 和单次调用，失败即停止，不强行启用按钮，不修改 SQL 或字段。预览成功不代表正式抽数成功。

成功必须证明 `isExpire=false`、新周期一致、SQL及字段未变、原频率/时点/告警/开关未变；平台重建的同步 `taskId` 单独记录。本命令不触发正式抽数、不修改 SQL、不新建数据集。续期成功只完成续期阶段，后续 SQL 更新或同SQL刷新仍须新基线、独立计划、预览、保存回读和新抽数 `SUCCESS`。
