# OES → Outlook Excel → 飞书 Base

## 功能

稳定入口是 `scripts/oes_achievement.py`。维护 OES 查询导出、本人公司 Outlook 附件接收和 Base 全量覆盖：

- 从 usql_api.env 的精确 OES section 读取账号密码，不使用同名键的其他 section，也不输出敏感值。
- OES 状态保存在 `~/.codex/runtime/usql-web-query-operator/oes-achievement/state.json`；Outlook 独立使用 `oes-outlook/state.json`，并以账号 Hash 绑定状态。二者均读取同一精确 OES 凭据区段，绝不复用 USQL/Data Map/Tiangong2 状态。
- 支持 --date 单日，或 --start-date / --end-date 闭区间。页面实际控件是“筛选时间”，并非业务期次下拉框。
- 原生 `export` 保留分页查询、完整性检查、JSON/CSV 保存后再导出的行为。缺失或变化的总行数、重复行 ID、分页不完整和超过原生 1 万条上限都会阻断原生导出。
- `inspect-range` 只读取一条数据和总行数，用于探查长日期区间及单批是否超过 1 万条，不触发导出。
- `export-and-download` 自动切分超过 1 万条的区间，逐批做邮件登录预检、旧邮件快照、单次提交、新邮件轮询、XLSX 校验和本地文件回读，最终合并全部已验证附件。
- 新邮件须符合发件人、主题关键字、受理时间、旧邮件排除和总行数；附件还须与完整查询逐条按 `(orderNumber, clazzBizNumber, userId, price)` 多重集合核验，保留重复订单的条数。多个符合条件的新邮件会失败，不猜选其中一个。
- 回执记录筛选区间、执行阶段、受理时间、去敏邮件 Hash、行数、文件路径及 SHA-256。结果和附件一律在 Skill 仓库之外保存。
- `base-setup` 初始化 13 个明细字段及“导出配置”；`sync-base` 读取维护的开始时间，以新运行的当前时刻为截止，删除历史记录并写入全部 Excel 字段。开始时间不会推进。
- Base 备份/删除与 OES 导出/收邮件并行；可区分条数的导出批次先全部提交再接收。便携启动器与打包脚本支持迁移到其他 Windows 电脑。
- `sync-base` 自动清理本目标完成超过 7 天、全字段核验成功的完整任务缓存，另存精简完成索引防止旧标识重导；失败/待恢复任务及登录态继续保留。每天生成 JSONL 阶段日志，默认保留 30 个日历日。
- `clean-cache` 仅执行本地维护，不登录网站或调用飞书接口；与同步共用目标文件锁。

## 边界

- 查询接口是 POST /performance/management/attribution/list；原生导出接口是 POST /performance/management/attribution/export；二者复用同一筛选 payload。
- 原生导出只返回受理信息，真实 XLSX 通过 `https://mail.gaotu.cn/owa/` 的邮件附件获取。只有附件下载和核验通过，流水线才返回 `status=completed`。
- 当前适配器经实际验证使用 OWA Light 页面和其 `attachment.ashx` 同源下载链接；不使用 Microsoft Graph、公共 Outlook OAuth，也不发送、回复、转发、移动或删除邮件。打开邮件时 Exchange 可能自动将它标为已读。页面布局漂移必须停下诊断，不能猜测下载地址。
- OES 邮件主题中的日期不能作为筛选区间证据；它可能与筛选日期不同。以回执中的区间、查询结果和附件核验为准。
- 邮件正文的总行数可能包含千分位逗号（例如 `3,676`），按完整整数解析，不能截取成 3。
- 原生 XLSX 可能错误声明 A1 范围；验证器重置维度后扫描实际行，避免把有数据的文件误读成空表。
- CAS 图形验证码不自动识别或绕过。首次或失效时做一次可见登录，之后 session-status 和 export 静默复用状态。
- Outlook 在状态过期时用同一凭据提交一次普通登录并保存状态；登录失败、CAPTCHA、MFA 或风控不自动重试或绕过。
- 本能力支持 Base 配置表和订单覆盖，不自动注册或启用定时任务。每个目标表只使用一台执行电脑，本地文件锁不能保护跨电脑的同时运行。

## 日期跨度与容量实测

2026-10-04 在当前账号下验证，结束日期均为 2026-10-03（页面日历一行除外）：

| 路径 | 区间 | 结果 |
|---|---|---|
| 页面日历 | 2026-08-04 至 2026-09-03，含首尾 31 天 | 可以提交；下一日不可选。控件限制首尾相差不超过 30 天 |
| 查询接口 | 61 / 90 / 180 / 365 / 730 / 1095 / 3650 天 | 均返回成功和有效总行数 |
| 原生导出并下载 | 2026-08-04 至 2026-10-03，61 天 | 3,676 条，邮件与 XLSX 逐条核验通过 |
| 自动分批导出并合并 | 2026-06-19 至 2026-10-03，107 天 | 10,986 条，拆为 7,627 + 3,359 条，两个附件及合并结果核验通过 |
| 查询接口最长已验证区间 | 1970-01-01 至 2026-10-03，20,730 天 | 接口成功，总数 179,477；仅探查总数，未完整下载这个长区间 |

页面日历的 31 天限制不等于查询/导出接口的天数限制。脚本复用实际页面的查询与原生导出 payload，日期语义已与页面提交的毫秒范围对照。当前未找到服务端固定最大天数；只能报告最长**已验证** 20,730 天，不能报告“无限天数”。

同一结束日下，106 天有 9,324 条、107 天有 10,986 条。因此当时可完整单批导出的最长连续区间是 106 天；这是当前账号、结束日和数据量决定的边界，不是固定天数规则。统一流水线超过 1 万条时自动分批，不受这一单批跨度限制。

```powershell
D:\anaconda3\python.exe scripts\oes_achievement.py inspect-range `
  --start-date 2026-04-07 --end-date 2026-10-03
```

## 超过 1 万条的分批与完整性

1. 完整分页查询整个区间；以 OES 明细行 `id` 检查唯一性，保留同一个 `orderNumber` 的多条业绩流水。所有 `tradeTime` 必须位于筛选区间内。
2. 用完整查询结果计算每段条数。优先在自然日午夜切分；某一天仍超过 1 万条时继续在日内按毫秒范围二分，直到每段不超过 1 万条。
3. 每段是闭区间，下一段开始毫秒严格等于上一段结束毫秒加 1。空段也保留在计划中证明覆盖，但不发邮件。计划必须首尾覆盖整个区间、无重叠或空隙，分段条数之和等于完整查询条数。
4. 导出之前逐段调用查询接口验证计划条数，之后复核整个区间总数。任一不一致均在导出前停止。每个实际批次在提交前再次核对当前条数。
5. 每批只提交一次，按新邮件快照及筛选条件下载附件；逐条核验订单、班级、用户和金额的多重集合，不按订单号去重。各批合计及合并 XLSX 必须再次与整个区间的完整查询一致，才返回 `completed`。

多个非空批次条数互不相同时，先逐个完成登录预检、邮件快照及导出提交，让服务端同时生成文件，然后接收附件。任意批次条数相同时使用逐批接收，以免无法区分邮件；每批 `waiting_for_mail` 回执保证重跑提交阶段也不重复导出。

查询/导出接口已经实测接受日内范围：2026-10-03 上午 8 条、下午 44 条，两个查询的行 ID 无重叠且完整覆盖全天 52 条；上午 8 条已原生导出、收到邮件并完成附件逐条核验。若超过 1 万条集中在同一毫秒，时间维度无法继续切分，脚本明确失败并且不提交任何批次；不能用截断文件报告完整。

接口未提供事务快照。分页期间总数变化、分段条数漂移或附件与已保存完整查询不一致都会停止完成流程；不能把正在变化的数据冒充已核验结果。

分批目录含 `partition-plan.json`、完整查询 JSON/CSV、`batch-receipt.json`、各批独立 `receipt.json` 和原始 Excel，成功时另有 `oes-achievement-combined.xlsx`。合并表保留文本订单号、手机号和用户 ID，冻结表头并设置筛选。合并超过单个 Excel 工作表容量时明确失败，已核验原始批次仍保留。

## 推荐的一体命令

```powershell
D:\anaconda3\python.exe scripts\oes_achievement.py export-and-download `
  --start-date 2026-10-01 --end-date 2026-10-03 `
  --output-dir C:\Users\Ludim\.codex\deliverables\oes `
  --run-key oes_orders_20261004_0730
```

`--run-key` 代表一个确定的调度执行，例如“配置名称 + 执行日 + 时段”。同一次执行的重试必须保留该值和输出目录：

- `completed`：核对原文件 Hash 后直接复用，不再登录、查询或发起导出。
- `waiting_for_mail`：只恢复邮件接收；即使 OES 登录态已过期，也不重新导出。
- `export_requesting` / `export_uncertain`：请求是否受理无法证明，停止自动重试；查看回执和邮箱，再决定是否使用新的运行标识。
- `completed_no_data`：查询确认为 0 条，仅保存本地空结果，不请求无数据的邮件导出。
- 分批 `processing_batches`：恢复已有计划；完成批次回读文件后复用，已提交但等待邮件的批次只接收邮件，尚未提交的批次再继续执行。合并失败时重跑也不会重新导出已完成批次。

原文件变化、同一标识绑定的区间或邮箱条件变化会失败。OS 文件锁阻止同时运行两个导出链路，进程退出自动释放锁。CLI 返回 0 表示已完成/无数据，返回 2 表示错误或邮件尚未完成；失败原因和回执路径会出现在 JSON 输出。运行回执必须与下载文件一起保留，删除回执后无法判断该执行是否已经提交。

## 单独接收既有邮件

```powershell
D:\anaconda3\python.exe scripts\oes_achievement.py mail-login
D:\anaconda3\python.exe scripts\oes_achievement.py mail-session-status
D:\anaconda3\python.exe scripts\oes_achievement.py download-mail `
  --mail-subject 20261002业绩数据明细导出 `
  --received-after 2026-10-03T23:45:00+08:00 `
  --received-before 2026-10-04T00:00:00+08:00 `
  --expected-count 52 --output-dir C:\Users\Ludim\.codex\deliverables\oes
```

可增加 `--query-json <原查询结果.json>` 做订单、班级、用户和金额核验；没有它时只证明文件可读和行数，不证明它对应某个筛选区间。默认只扫描一次；增加 `--wait-seconds 600 --poll-seconds 15` 可等待邮件。

Outlook 接收时间精确到分钟；`received-after` 向该分钟起点取整。一体流程同时使用旧邮件快照消除这一分钟内的旧邮件；单独下载时需用主题、时间上界、查询 JSON 收紧条件。多封匹配默认失败，只有显式 `--latest` 且最新分钟只包含一封匹配时才选最新邮件。

## 日期配置与定时脚本

配置模板：[oes_mail_job.example.json](../assets/oes_mail_job.example.json)。Base 字段模板：[oes_base_date_config_template.md](../assets/oes_base_date_config_template.md)。配置不能含密码或 Cookie。

`date_filter.mode` 支持：`absolute`（开始/结束闭区间）、`previous_day`（昨天）、`rolling_days`（截至昨天的最近 N 个完整自然日）。滚动日期按 Asia/Shanghai 解析，不是课程业务期次；同时传配置文件和日期参数会失败。

```powershell
D:\anaconda3\python.exe scripts\oes_achievement.py export-and-download `
  --config-file assets\oes_mail_job.example.json `
  --output-dir C:\Users\Ludim\.codex\deliverables\oes `
  --run-key oes_orders_20261004_0730

powershell.exe -NoProfile -File scripts\run_oes_mail_job.ps1 `
  -JobConfig C:\Users\Ludim\.codex\runtime\oes-job.json `
  -OutputDir C:\Users\Ludim\.codex\deliverables\oes `
  -RunKey oes_orders_20261004_0730
```

这个邮件独立包装器从 `machine.local.json` 的 `executables.python` 解析 Python，使用参数数组传输路径和运行标识，透传 CLI 退出码。只运行一次，不注册 Windows 计划任务。Base 集成使用下面的便携入口，直接读取“开始时间”，无需把 Base 配置转换为邮件独立 JSON。分批策略由实际条数决定，不需要在 Base 中手工拆日期。

## Base 覆盖与性能

字段模板：[oes_base_date_config_template.md](../assets/oes_base_date_config_template.md)。配置维护“开始时间”，不维护截止日期。按 Asia/Shanghai 使用毫秒闭区间 `[开始时间, 本次固定截止时刻]`；同一次运行重试保留原截止。

```powershell
python scripts/oes_achievement.py base-setup `
  --base-token <BaseToken> --table-id <明细表ID> `
  --start-time 2026-06-19T00:00:00+08:00 --output-dir <仓库外目录>

python scripts/oes_achievement.py sync-base `
  --base-token <BaseToken> --table-id <明细表ID> `
  --config-table-id <配置表ID> --config-record-id <配置记录ID> `
  --output-dir <仓库外目录> --run-key <配置与执行时段的稳定标识> `
  --wait-seconds 600 --poll-seconds 3 --scan-pages 5
```

`base-setup` 重跑不会覆盖维护的开始时间。目标字段只允许匹配 Excel 的 13 个字段；存在无关字段或初始主字段包含数据时停止，不删除字段。姓名、手机号、订单号、用户 ID 和班级 bizNumber 按文本保存，金额为数值，时间为毫秒日期。

飞书通过官方 CLI 的本人用户身份授权。原生 `bitable/v1` `batch_create/batch_delete` 每批最大 **500 条**；避免走只支持 200 条的快捷批量写入接口。读取通过官方 `base/v3` 适配器每页 **2000 条**，检查版本、全表范围、重复记录 ID、`has_more=false` 和权威 `next_offset`。Python 不提取 OAuth Token。容量依据：[批量新增](https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table-record/batch_create)、[批量删除](https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table-record/batch_delete)。

后台完整备份旧数据并按 500 条删除，主线程同时完成 OES 查询、导出和邮件下载。等待删除任务确认表空后按 500 条串行写入，最后完整回读比较 **全部 13 个字段的多重集合**，重复订单保留。完成后回写配置中的截止、完成时间、状态和明细行数。

Base 不提供整表原子替换。失败会尽可能恢复备份的旧数据值；恢复产生新 record_id。写入结果不确定时保留备份和 pending 回执，停止自动重复写入。已完成运行重试只做全字段远端核验；失败且已恢复的运行可复用已下载文件重新覆盖。

## 同事电脑部署

模板：[oes_base_job.example.json](../assets/oes_base_job.example.json)；空白凭据格式：[oes_credentials.env.example](../assets/oes_credentials.env.example)；说明：[oes_base_deployment.md](../assets/oes_base_deployment.md)，包含每台电脑的登录态位置、首次登录/恢复、换账号、缓存规则、taskschd.msc 导入和防休眠配置。

```powershell
python scripts/build_oes_deployment.py --output-dir <仓库外新目录> --lark-cli <官方原生lark-cli.exe>
python scripts/run_oes_base_job.py check --settings <本机settings.json>
python scripts/run_oes_base_job.py sync --settings <本机settings.json>
python scripts/run_oes_base_job.py cleanup --settings <本机settings.json>
```

便携 ZIP 含源码、官方 CLI 和独立环境安装器，需要 Python 3.11+、Edge 和公司网络。相对路径按设置文件目录解析，`OES_AUTOMATION_HOME` 隔离本机登录态、回执和锁。不依赖 Codex、Anaconda 或 Node.js。每台电脑自行维护凭据和完成飞书用户授权，不复制开发电脑登录态或 Token。启动器默认用当前上海半小时时段生成稳定标识，但不自动启用计划任务。

包内 `prepare-task.ps1` 使用模板生成当前 Windows 用户 SID、绝对路径及上海时区开始时间的 XML，默认禁用，不注册任务或修改电源。部署者在未来执行电脑通过 taskschd.msc 导入、核对并启用。模板每天重复、30 分钟间隔、`Hidden=true`、`InteractiveToken`、`IgnoreNew`；动作直接使用 `.venv/Scripts/pythonw.exe` 与 `run_oes_base_silent.py`。静默入口补齐 pythonw 的无控制台环境，只保存元信息启动日志，吞掉原始输出，保留真实退出码。启动日志在运行根目录 launcher-logs，跟随 log_retention_days 保留。

执行电脑按部署说明把 AC/DC 自动睡眠设为“从不”、关闭系统休眠，笔记本合盖不采取操作；账号保持登录。Hidden 不表示窗口控制，静默由 pythonw、headless 浏览器和 CLI 的 CREATE_NO_WINDOW 实现。此交付只制作配置与说明，不在原开发机安装定时任务或更改电源。

每个新运行先保留原 Excel；分批时另保留合并表，写 Base 后保留字段快照、旧表备份与远端回读。每次同步在目标文件锁内先清理本目标 `completed`、13 字段零差异且完成超过 7×24 小时的整个 `base-sync-*` 目录，失败/待恢复/未确认任务保留。以 `completed_at` 计算，不能按订单日期或文件修改时间删除。符号链接/junction、索引或回执身份变化会阻止该目录清理并记录日志。

精简完成索引在 `OES_AUTOMATION_HOME/completed-runs/<目标Hash>/`（开发默认 `runtime/usql-web-query-operator/completed-runs/`）单独长期保留。删除前保存索引；旧标识的完整缓存已清理或缺失时返回 `completed_cache_expired`、`remote_readback_performed=false`，不重新执行导出或替换，也不能把历史核验摘要当作当前表核验。日志在同一运行根目录 `logs/<目标Hash>/oes-base-YYYY-MM-DD.jsonl`，按上海日期换文件；默认保留 30 个日历日，记录元信息，不包含凭据、明细或原始异常。初始日志失败会停止覆盖，后续写日志失败通过 `log_write_errors` 报告。

保留天数通过 `settings.json` 的 `cache_retention_days` / `log_retention_days` 或 CLI 的同名短横线参数设置，默认 7 / 30，范围 1～3650。旧配置自动采用默认值。`cleanup` 单独维护不产生远端访问；输出包含清理目录/文件/字节及失败数量。详细路径与恢复步骤见部署说明。

## 用法

首次建立或恢复状态：

    D:\anaconda3\python.exe scripts\oes_achievement.py login --headed

静默验证状态：

    D:\anaconda3\python.exe scripts\oes_achievement.py session-status

单日导出：

    D:\anaconda3\python.exe scripts\oes_achievement.py export --date 2026-10-03 --output-dir C:\Users\Ludim\.codex\deliverables\oes

范围导出：

    D:\anaconda3\python.exe scripts\oes_achievement.py export --start-date 2026-10-01 --end-date 2026-10-03 --output-dir C:\Users\Ludim\.codex\deliverables\oes

## 登录态有效期

状态可跨浏览器进程复用。当前持久 Cookie _const_d_jsession_id_ 声明 7 天；CAS、JSESSIONID、hbsessionid 是会话 Cookie，服务端可能提前失效，因此 7 天是声明上限而非保证。以 session-status 实测为准。

## 维护验证

运行 OES/Outlook/分批/Base 受影响测试、入口 help、command reference builder/check 和 Skill quick_validate。真实验收包括长日期区间、日内边界、完整分页、每批单次受理、新邮件、文件 Hash、查询/邮件/XLSX 核验、原生 500 条批次、历史删除、Base 全部 13 字段回读和并行耗时。还需验证同一 RunKey 重跑和恢复不重复导出，以及从仓库外部署包完成只读检查。
