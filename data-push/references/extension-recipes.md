# 扩展配方与交付检查

只实现用户当前要求的部门、执行面、渠道/workflow 和格式，不因为已有公共代码就推导其他部门口径。先固定 `domain/local/channel_id` 或 `domain/miaoda/deployment_id/workflow_id`；可执行本地接口见 [interfaces.md](interfaces.md)，妙搭绑定见 [deployment-configuration.md](deployment-configuration.md)。

## 新增同部门、同口径的本地渠道

1. 读取所属部门Skill和现有渠道规范，确认字段、期次、范围、指标及提醒对象兼容。
2. 新建 `config/departments/<domain>/<channel_id>.json`：精确渠道、源、目标ID、身份、独占状态目录；schedule.enabled初始false。若后续获准启用本地调度，先读取所有已启用渠道，为新任务分配下一个连续 `stagger_order` 和唯一 `windows_task_name`；启动分钟必须是 `19+stagger_order`，从 `:20` 起逐任务错开1分钟，`prepare_minute` 与 `send_minute` 相同，重试固定每2分钟、截止 `:50`。不得手工挑一个已占用分钟。
3. 加入 `config/channels.json`；复用适配器仅限它明确支持的规则。
4. 新建独立脚本，内容保持薄入口：

```python
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from lark_delivery.cli import main

if __name__ == "__main__":
    raise SystemExit(main(bound_channel="market_consultant/new_channel"))
```

示例new_channel不是已经注册的渠道。实际提交时用已确认的ID。
5. 新增本部门测试：源过滤、当期缺失、最小量、排序、提醒精确账号和跨群隔离；运行离线测试。
6. 生成本地预览并核对，另行取得明确发送/启用授权。注册或更新任务后读回全部触发器，确认所有时段均保持全局错峰。任务启动器不得创建持久化 `run-*.log`；共享调度层只在运行时原子更新 `state_dir/live-status.json`，结束（成功、失败或异常）即删除。使用 `scripts/view_live_push_status.ps1` 联合查看任务状态与当前步骤。不要批量复制旧2400行脚本。

## 新增青橙或不同口径渠道

先读 [青橙接入边界](departments/qingcheng.md)。创建青橙adapter及自己的数据验证、聚合、渲染、文案、日历和上游验收。只共享中性飞书ports、配置/目标协调、文件布局和锁。

在 `registry.adapter_for` 登记 `("qingcheng", "<reviewed-adapter>")`；同时加“拒绝市场adapter”的测试。没有已确认口径时，仅交付未启用配置/接口设计，不发送或伪造默认规则。

## 新增妙搭推送部署

1. 先读 [架构与隔离](architecture.md) 和目标部门边界。确认是新云端推送还是从同部门本地渠道迁移；迁移时指定 `source_channel_ref`，新建时不得虚构本地渠道。
2. 默认每个部门使用独立 runtime 工程和独立妙搭 app。先在 `config/deployments.json` 形成未启用的 app 绑定；同部门可在该部署的 `workflows` 下新增任务。runtime/app 不跨部署复用，每个 workflow 的 contract、module、automation namespace、ledger namespace 和 style owner 都须明确且不重叠。
3. 在妙搭工程内按 `common/core/domains/<domain>` 或同等单向依赖拆分；字段、聚合、日历、文案、fixture 和 renderer/style 都放部门 workflow/module。不要把新部门加到现有市场 renderer 或自动化的条件分支。
4. 测试按部门分别覆盖配置解析、fixture、字段门禁、公式、视觉回归、幂等与读回；再运行 `validate_layout.py` 证明 Skill 注册与 `.spark/meta.json` 身份一致。
5. commit/push、release、Secret、数据库迁移、云端 dry-run、测试群实发、自动化启用和本地任务切换分别授权、分别读回。默认 `local_schedule_relation=independent`。

青橙首个妙搭部署不得使用当前 `runtime/cloud-data-push-miaoda` 或 `app_17cmm5tn1gs`。若用户明确要求共用 app，先只交付共享宿主的隔离设计和风险清单；未审阅 app 级 Secret、数据库、发布与自动化故障域前不改源码。

## 改图片或文字

- 只改颜色/列宽/布局：改本部门renderer/style，给定同一report时数据和提醒必须不变。
- 增减指标/拆分维度：修改projection、源计数器、聚合、总计、排序、提醒与渲染，补分子/分母测试。不能直接平均行百分比。
- 改文案：复用PreparedReport的period/mention_info和同一批report，别再次取数混入另一个revision。
- 第三张图片、附件、卡片：当前v1槽位不够；新增类型化artifact清单和transport实现，版本化adapter，扩展幂等、回执和清理测试。交互卡片先读官方lark-im卡片说明；不得把卡片JSON当post Markdown发送。
- 不把业务逻辑塞入CLI、注册表或common；不让renderer触达发送API。

## 多群交付与恢复

每个目标都需要自己的成员核验、消息key、图片生命周期和状态；一个群发送成功后，重跑只能补未投递且确定可重试的目标。uncertain/sent_unverified均不能自动再次发送。

换收件人、身份、上游版本、状态目录或真实发送形式涉及不同影响，必须在对应授权后执行。私聊可用范围失败不能当作自动使用user身份的许可。

## 离线验证矩阵

| 改动 | 必须覆盖 |
|---|---|
| source/ports | 分页、版本变化、缺字段/重复键、精确范围、权限失败 |
| 聚合/提醒 | 加权率、0分母、并列最低、小年级过滤、跨期和跨部门隔离 |
| renderer/message | 同一输入输出回归、PNG能打开、字体/列/排序/@集合 |
| targets/fanout | 一个/多个群、改名、重复目标、部分失败、独立状态和去重 |
| scheduler/outlet | 暂停、全局错峰分钟、按各自启动分钟每2分钟重试、`:50`截止、分区未更新/上游失败、不确定响应、临时状态必清理、回执先落盘再清理 |
| 路由/重命名 | Skill/AGENTS链接、入口help、本地渠道与妙搭部署配置读回、runtime/app身份、任务动作路径与暂停状态 |

推荐运行 `D:\anaconda3\python.exe -m pytest tests -q`，测试框架拦截未mock的外部进程。`scripts/validate_layout.py` 检查目录、导入方向、文档链接、本地渠道入口和妙搭部署绑定。两者均不启动生产任务、发布应用或发送消息。

保留默认配置、指标和文案的回归证据；代码变更通过测试不等于已经送达，只有真实message_id及独立读回才是交付证据。
