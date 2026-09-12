# 妙搭全栈云端播报

本工作流负责新建、维护或迁移妙搭服务端推送。先从 `config/deployments.json` 解析精确的 `domain/miaoda/deployment_id`，再读取同部门业务 Skill；妙搭应用、环境、托管数据库、发布、日志与自动化能力由 lark-apps 执行。静态看板刷新继续使用 [miaoda.md](miaoda.md)，不得混用。

当前唯一部署是 `market_consultant/miaoda/cloud_data_push`，源码位于 `C:\Users\Ludim\.codex\runtime\cloud-data-push-miaoda`，其 `.spark/meta.json` 绑定 `app_17cmm5tn1gs`。其中 `supervisor_koc_douyin_sync` workflow 绑定现有 `cloud-push-demo` 模块；四渠道、字段、自然周、主管聚合、自动化名称、数据库表和配色全部视为市场顾问部所有。该工程不是跨部门模板；青橙不得在此工程中追加条件分支，默认另建工程和 app。

## 固定边界

- 将代码改造、commit/push、release、环境变量、数据库迁移、云端 dry-run、测试群实发、自动化启用视为可独立授权和核验的阶段。应用已绑定不等于代码已部署，release finished 不等于消息已送达。
- 妙搭部署与引用的本地渠道保持业务合同对照，但运行配置不继承：云端 Base、群、机器人、Secret、触发器、台账和 app 身份必须独立固定并读回。本地任务保持独立；开发、发布或 dry-run 不得自动暂停、替换或恢复它。
- 浏览器只提交期次、已登记渠道、图类型和动作；Base、table、view、chat_id、bot open_id 及密钥必须由服务端固定并再次校验。密钥只能进入妙搭 Secret，不得返回前端或写入日志、README、截图和回执。
- 默认 DELIVERY_MODE=dry-run。真实发送同时要求真实 Base、妙搭生产执行标记、固定测试群、预期机器人、明确 send 动作以及不存在的幂等键。环境为 enabled 不能把 dry-run 请求升级为发送。
- 手工测试一次只处理一个显式 period/channel/section，并固定手工 slot。调用方不得自定义 slot 或 chat_id 绕过幂等。自动化在单次测试验收前保持未创建或禁用，触发源显式调用 dry-run。
- 主管真实 @ 必须使用经通讯录解析、群成员核验的 open_id 映射；缺项立即失败，不降级成纯文本姓名。测试群不含所有目标成员时，停止实发并补齐成员或获得新的测试策略。
- 用户明确授权图片链路优先验收时，可为固定测试群设置独立的 skip-reminder 门禁：只允许省略提醒消息，图片上传、图片发送、sender/chat/image_key 回读及幂等台账仍必须通过，并在回执中标记 skipped-in-test-chat。该门禁不得用于正式群；正式群及真实 @ 仍需新的目标核验和发送授权。

## 实现分层

1. Deployment Resolver 只接受登记的 `domain/miaoda/deployment_id/workflow_id` 并核对 runtime/app/contract/module/namespace；请求参数不能切换部门、app、workflow 或生产目标。
2. Domain Module 拥有本部门的 Base Reader、聚合、日历、文案、fixture 和 StyleSpec；共享层不能按部门分支。
3. Base Reader 完整分页，只投影渠道契约字段，严格匹配期次和大小写敏感渠道；输出页数、原始/有效行数、revision、fingerprint 和 schema hash。
4. 聚合器保持本地语义与 grain。字段标题与来源字段分别声明，例如图片“负责人”可来自 Base“经理”，不可用 fixture 名称替代真实字段。
5. Renderer 使用部署内固定哈希的中文字体和本部门 StyleSpec，经 SVG 到真实 PNG；输出宽高、字节数、SHA-256，并人工检查中文、长名称、色块、进度条和清晰度。市场视觉回归不能证明青橙样式正确。
6. Delivery 依次执行身份/坐标预检、图片上传、原子 claim、图片发送、消息回读、提醒发送与回读。上传后任何不确定状态都写 receipt 并禁止盲目重发。
7. Ledger 至少保存 run、partition snapshot、claim 和 receipt；表/namespace 只属于该部署，run 带 trace_id、错误阶段和时间戳。RLS 默认只允许服务端角色，不开放匿名或无条件 authenticated 读写。
8. Console 提供状态、脱敏测试群、期次/渠道/图类型、只读、预览、dry-run、受控实发、最近运行和详情。一次点击只创建一个 run_id；浏览器不能切换未登记部门或目标。

## 上线顺序与完成证据

1. 本地：锁文件安装、类型检查、生产构建、字体/图片/Base/投递/自动化/控制台/readiness 验证；真实 Base 预览须人工查看。
2. Git：仅在用户明确授权后，按审阅文件 scoped commit 并 push 到绑定应用分支；记录本地 SHA 与远端分支 SHA。
3. 妙搭：创建 release 并等到 finished；写入 Secret 后只读回变量名和是否配置；执行数据库迁移并从服务端读回表结构与最小台账。
4. 云端 dry-run：读取真实 Base、生成真实 PNG 和提醒预览，但不上传、不发消息；核对日志、trace_id、run、snapshot、PNG 元数据。
5. 单次测试：重新核对机器人、Base、测试群、成员映射、幂等键和人工图片预览；临时启用 delivery，显式触发一次 send，随即回读 message、image_key、sender、chat_id、内容与 mention 集合，再恢复 dry-run。
6. 若发送接口结果不确定，先按幂等键、run 和群消息回读，绝不再次点击。只有 receipt 为 verified 且无重复消息，才能报告真实测试完成。

本地任务切换是上述验收后的独立阶段。只有用户明确授权替换某个精确任务时，才先读回云端部署/自动化/台账，再停用对应 Windows 任务并再次读回两端状态；不要删除本地配置或历史台账，也不要把一次测试发送当作接管证明。

最终报告必须分开陈述本地验证、push、release、云端 dry-run、真实发送、消息回读和自动化状态。缺少任一线上证据时使用 blocked_before_real_delivery 或 delivery_uncertain，不得用 fixture 或离线成功替代。
