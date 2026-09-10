# 接口契约：给后续维护与扩展的AI

先读 [架构](architecture.md)。可执行类型定义在 [core/contracts.py](../scripts/lark_delivery/core/contracts.py)，真实调用样例在 [市场adapter](../scripts/lark_delivery/domains/market_consultant/adapter.py)。本文件描述已有能力，不意味着可以省略授权、数据验收或适配器登记。

## 1. 注册与配置接口

| 接口 | 输入 | 输出 / 失败规则 |
|---|---|---|
| `catalog.load_channel(key)` | `domain/channel_id` | 验证过的渠道字典；未登记、目录越界、身份不符、状态目录交叠报错 |
| `catalog.select_targets(config, target_ids=None)` | 配置、可选目标ID列表 | 启用目标的深拷贝；默认全部启用目标；拒绝未知、禁用或重复ID |
| `catalog.source_defaults(config, target)` | 单渠道、单目标 | 兼容旧参数的取数默认值，不调用API |
| `catalog.schedule_config(config, target)` | 单渠道、单目标 | 展开的本群调度、身份、源表及状态；主目标保留历史台账 |
| `registry.adapter_for(config)` | 明确的domain和adapter | 仅返回登记过的部门适配器；不做跨域fallback |

这些接口不读取飞书、不修改配置文件、不产生发送授权。配置字段见 [配置规范](channel-configuration.md)。

## 2. 部门adapter接口

`DepartmentAdapter` 是结构化Protocol，模块或对象实现均可。当前由市场部adapter模块实现：

| 方法 | 职责 | 不能做什么 |
|---|---|---|
| `validate_definition(definition)` | 核对本部门支持的策略、发送身份、报告profile | 不接受别的部门语义，不猜缺失配置 |
| `prepare(definition, target, *, report_type="auto", state_dir=None)` | 读取、聚合、账号与群成员核验，生成一个目标独立持有的报告 | 不上传图片，不发消息，不修改Base |
| `write_preview(context)` | 写HTML/Markdown/脱敏元数据，返回三个绝对路径 | 不使用真实发送接口；不把Base token写入元数据 |
| `schedule(definition, target, *, preflight=False)` | 本目标OS锁、时点、证据与台账；preflight只读 | 不启用Windows任务，不改上游，不把不确定发送自动重试 |

新部门实现这四个方法并在 `core/registry.py` 增加**精确的部门＋adapter映射**。只改注册JSON而不提供可用适配器，会报错而非套用市场部代码。

## 3. 只读准备接口 ReportPorts

[FeishuReportPorts](../scripts/lark_delivery/common/report_ports.py) 是现有实现；可把一个同协议的fake对象传给 `workflow.prepare_report(..., ports=fake)`，完全离线测试。不需mock函数内部或调用真实API。

| 方法 | 参数 / 返回 | 保证 |
|---|---|---|
| `resolve_source(args)` | 含source_url/base_as/timeout的参数 → base/table/view坐标 | 不按模糊表名替换目标；坐标只留内存 |
| `field_names(coords, args)` | 坐标 → 字段名集合 | 上层projection负责缺少字段时阻断 |
| `read_records(coords, args, fields, *, filter_json, audit)` | 精确条件、最小字段集 → 全量记录；回填audit | has_more终止、行数/记录ID/分页rev/查询范围一致；临时分页文件结束即清理 |
| `search_users(queries, args)` | 名称查询列表 → queries/users | 每批最多20；保留has_more及错误信息，精确身份判定由部门resolver执行 |
| `verify_target(chat_id, name, identity, timeout)` | 唯一群ID → 当前名称及是否改名 | 名字不用于选群，不因改名换群 |
| `missing_members(chat_id, resolved, identity, timeout)` | 姓名→open_id → 不在群名单 | 必须完整、无截断的群成员列表 |

准备接口没有“上传”或“发送”方法，避免绘图/预览触发外部写入。旧门面仍可通过 `services=` 注入以维持既有调用，新增代码使用 `ports=`。

## 4. 纯计算与表示接口

当前市场适配器的 `grade_report.py`：

| 接口 | 输入 → 输出 | 自定义方式 |
|---|---|---|
| `projection(field_names, report_type)` | 已有字段与类型 → 最小字段列表及分子计数器 | 新指标先确认本部门分子、分母和源字段，再扩字段；不要只加图片列 |
| `validate_scope(records, channel, period)` | 明细 → 唯一分区快照 | 验证期次＋lead_id、范围、非空维度；不能靠丢异常行修复 |
| `build_report(records, counters, period, report_type, *, excluded_grades, min_post_leads)` | 明细 → blocks/totals/负责人最低值 | 先加分子分母；本域规则，不是所有部门的“通用聚合” |
| `sorted_rows(block, section)` | 年级块 → 按精确值降序的行 | 图片排序与提醒最低值方向不同，不混淆 |
| `render_image(report, section, output_path, *, font_loader, center_text, format_value, bar_colors, cell_fill)` | 聚合结果 → 一个PNG及子表几何信息 | 表头、列宽在COLUMNS/WIDTHS；本域色块在style；绘图不能再次查源 |
| `build_markdown(report, period, channel, report_type, mention_info, image_refs)` | 同一聚合结果＋账号映射 → 文案 | 只使用已核验open_id；预览使用图片占位符 |
| `write_preview(context, directory)` | 完整上下文 → HTML/MD/JSON路径 | 不上传，不发消息 |

列和数据条是渲染参数；指标口径、期次、过滤和提醒人选是业务规则。更换图片布局时不要改变汇总结果。输出须用确定性夹具做像素/指标回归与人工查看。

## 5. PreparedReport最小字段

`PreparedReport` 的稳定传输字段包括：

- `report_profile / channel / period / report_type`：本次范围与样式。
- `chat_id / identity`：精确目标与发送身份。
- `raw_count / raw_read_audit / snapshot`：完整读取证据，audit至少含records_count、pages、rev、has_more=false。
- `markdown / idempotency_key`：消息与确定性键；不能把可变群名当主键。
- `image_path / result_image_path`：当前v1最多两种PNG槽位，未选类型为None。
- 市场部门额外提供 `grade_report、mention_info、coords、raw_table_id` 等字段供自己的验收使用。`coords` 中的Base token不得进入持久化预览或日志。

`mention_info` 需含 `resolved、unresolved、ambiguous、lookup_error、nonmembers`。正式负责人提醒必须后三类异常和未解析名单均为空，消息实际@集合与resolved的open_id集合完全一致。

当前接口不是任意图表/卡片万能插件。增加第三张图、附件、卡片或非post消息时，先定义新的artifact/消息接口版本、调整上传/回执读回和清理测试，再在新adapter启用；不要塞入未知字段后假装已支持。

## 6. 传输与真实投递

`common/im.py` 保留 `verify_chat、mention_nonmembers、upload_image、send_markdown`；最后两个是外部写入。`send_markdown(..., dry_run=True)` 不发送。上传与发送必须同身份；机器人私聊可用范围与群成员是不同约束，失败不能自动改成用户身份。

当前真实出口是部门 `scheduler.deliver`：

1. 本轮时间窗口、上游证据、完整Base版本、账号/群资格均通过。
2. 查询目标台账；已成功、已发送待核验或不确定记录都不会自动重发。
3. 上传本目标PNG；再次校验时间和数据版本。
4. SQLite原子claim → 发送 → 保存真实message_id。
5. 回执落盘后删除**本目标生成的**PNG；独立回读图片key、期次、群ID、发送者和@集合。
6. 成功标sent_verified；读回不通过标sent_unverified；响应不确定标uncertain，需要人工处理。

多群通过 `core.fanout.run_targets` 返回逐目标outcomes，不丢弃部分成功信息。它本身不替代单群去重、授权或证据校验。

## 7. 即时推送与定时分离

市场adapter另提供 `send_now(definition, target, request_id, *, preflight=False)`，由 `immediate.py` 实现；CLI只有 `send-now --request-id ... --confirm-send` 才进入真实单次出口。`preflight-now` 不上传、不发送。

`scheduler.deliver` 的常规定时窗口不变。它与即时模式共用 `_deliver_verified(..., key, time_guard)` 的回执/清理/读回实现，但分别传入不可缺失的实时检查：定时检查:20–:50，单次检查请求有效期、最新上游周期、数据新鲜度与业务日历。不能给共享出口传无校验回调；新模式须先实现自己的授权入口、时间/数据证据校验和测试。
