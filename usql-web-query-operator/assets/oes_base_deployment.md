# OES → Outlook Excel → 飞书 Base 部署

包内只含脚本、官方飞书 CLI 可执行文件和配置模板，不含账号密码、浏览器登录态或飞书 Token。不依赖 Codex、Anaconda、Node.js 或原开发电脑的绝对路径。需要 Windows、Python 3.11 及以上、Microsoft Edge 和公司网络连接。

## 每台电脑需要维护的信息

| 项目 | 默认位置 | 维护方式 |
|---|---|---|
| 程序和依赖 | `skills/`、`tools/`、`run.ps1`、`setup.ps1`、`requirements.txt` | 随运行包升级；保留本机配置、凭据及运行目录 |
| 定时任务模板 | `prepare-task.ps1`、`task-scheduler/task-template.xml` | 在同事电脑生成本机 XML，再通过 `taskschd.msc` 导入并启用 |
| 本机配置 | `settings.json` | 维护 Base/表/配置记录 ID、凭据路径、运行目录、邮件等待及保留天数 |
| OES / Outlook 账号密码 | `private/usql_api.env` | 两站读取同一精确区段；新电脑自行填写，密码变化时更新此文件 |
| OES 登录态 | `data/runtime/oes-achievement/state.json` | 登录或成功访问后由脚本保存，后续复用 |
| Outlook 登录态 | `data/runtime/oes-outlook/state.json` | 成功访问邮箱后由脚本保存；普通登录失效时凭据登录一次并保存 |
| Outlook 账号绑定 | `data/runtime/oes-outlook/state.account` | 脚本生成用户名 Hash，用于防止复用其他邮箱账号的状态 |
| 飞书授权 | 官方 CLI 在本机维护的 OAuth 凭据 | 每台电脑自行用户授权，由 CLI 存储及刷新；与 OES/Outlook 密码分开管理 |
| Excel、备份及回执 | `data/runs/base-sync-*` | 成功且完整核验的任务保留 7 天；每次运行自动清理到期缓存 |
| 精简完成索引 | `data/runtime/completed-runs/<目标Hash>/` | 长期保留运行 Hash、完成时刻、行数及核验摘要，防止清理后重复执行旧任务 |
| 按日日志 | `data/runtime/logs/<目标Hash>/oes-base-YYYY-MM-DD.jsonl` | 记录执行阶段、耗时、行数及清理结果；默认保留 30 个日历日 |
| 静默启动日志 | `data/runtime/launcher-logs/oes-launcher-YYYY-MM-DD.jsonl` | 记录 pythonw 启动、异常类型、退出码；随日志保留天数清理，不保存控制台原文 |

上述相对路径均从 `settings.json` 所在目录解析。修改 `credentials_file`、`runtime_dir` 或 `output_dir` 后，以实际配置路径为准。账号密码必须在本机文件中维护；说明和模板只记录键名及格式，不填写真实值。浏览器状态含 Cookie 等会话信息，也只在本机保存。

## 首次配置

1. 解压到本机可写目录。使用本机 Python 建立独立环境：`powershell -NoProfile -File setup.ps1 -PythonExecutable C:\Python311\python.exe`。将 Python 路径替换为本机路径。
2. 修改 `settings.json` 的 Base、数据表、配置表和配置记录 ID。保持相对路径时，脚本按 settings.json 所在目录解析。`lark_cli` 指向包内 `tools/lark-cli.exe`。
3. 复制包内的空白凭据模板：`Copy-Item -LiteralPath .\private\usql_api.env.example -Destination .\private\usql_api.env`，再填写该同事自己的账号密码。已有凭据文件时直接编辑，不覆盖。只需维护以下精确区段：

```dotenv
# mi.gaotu100.com OES Web Query (Playwright) credentials
BAIJIA_USERNAME=填写账号
BAIJIA_PASSWORD=填写密码
```

4. 在该电脑按官方飞书 CLI 流程完成应用配置与本人用户授权：运行 `tools/lark-cli.exe config init --help`、`tools/lark-cli.exe auth login --help` 查阅当前步骤。需要目标 Base 的编辑权限以及读取、创建和删除记录权限；所有 API 都使用用户身份。不要复制开发电脑的 CLI 凭据目录。
5. 运行 `powershell -NoProfile -File run.ps1 -Action login`，完成一次 OES 可见验证码登录；运行 `-Action mail-login` 建立 Outlook 状态；运行 `-Action check` 验证配置和目标 13 字段结构。

## 首次登录和登录态恢复

在解压目录执行：

```powershell
powershell -NoProfile -File .\run.ps1 -Action login
powershell -NoProfile -File .\run.ps1 -Action mail-login
powershell -NoProfile -File .\run.ps1 -Action check
```

- OES：读取 `usql_api.env` 并自动填账号密码；验证码由本人输入并点击登录。登录成功后脚本保存 `oes-achievement/state.json`，以后直接使用状态访问。无人值守运行遇到失效状态和验证码会报错，需要再次执行 `-Action login`。仅账号密码不足以自动完成图形验证码。
- Outlook：优先复用匹配本账号的状态；没有状态或普通登录失效时，用相同区段的账号密码提交一次登录。成功后保存 `oes-outlook/state.json` 和账号 Hash。遇到 MFA、额外验证码或页面变化时停止报错，当前适配器不提供这些额外验证的自动完成流程。
- `-Action check` 验证 Base 字段、启用配置和凭据区段，不验证两站的在线登录态；前两个登录命令实际访问对应页面。只有浏览器内登录完成、命令返回成功并写入状态，后续脚本才可复用；独立打开常规浏览器登录不会自动更新脚本的 Playwright 状态文件。

如果状态 JSON 损坏，或切换了账号，先停用定时任务并确认没有正在运行的实例，再把对应 `state.json` 改名备份；Outlook 同时备份 `state.account`。随后重新执行上面的登录命令，让脚本建立新状态。切换账号时两站状态都重建。只处理登录态文件，保留 `data/runs` 的运行回执和备份；不要清空整个运行目录。改密码时先更新凭据文件，需要重新认证时再按此流程登录。

新电脑使用自己的凭据、浏览器状态和飞书用户授权。旧机器的运行目录可留作归档；回执内含原绝对路径，不保证直接搬到新目录后能续跑旧任务，新电脑使用新的运行标识。

## 单次运行和后续调度

`powershell -NoProfile -File run.ps1 -Action sync` 执行一次。脚本自动用上海时区的当前半小时时段生成稳定运行标识；同一时段重复调用会核对已完成的远端结果或继续原任务。也可以显式传 `-RunKey 任意稳定标识`。已完成且缓存已清理的旧标识只返回历史完成摘要，不再查询、导出、删除或写入；摘要不代表重新核验当前远端表。

每次新运行从 Base 的“导出配置”记录读取“开始时间”，固定本次运行截止时间，然后查询这个完整区间。开始时间不会推进，也不会作为增量游标。续跑保留原截止时间；配置起点改变后必须使用新的运行标识。

Base 完整备份、历史记录删除与 OES/邮件链路并行；每张表的写请求串行，单批写入和删除均使用原生接口最大 500 条，完整读取每页 2000 条并持续检查 `has_more/next_offset` 和版本。确认目标表为空才写入全部 Excel 字段；最终完整回读逐条比较 13 个字段，包含重复流水、文本订单号、手机号、用户 ID、金额和时间。

多个导出批次条数互不相同时，先全部提交再接收邮件，让 OES 服务端同时准备附件。条数相同时逐批提交并接收，避免无法区分邮件；已有受理回执的批次不会重复导出。

原生批量写入/删除通过 `bitable/v1` 接口；读取、字段与配置维护通过官方 `base/v3` 适配器，获得 2000 条读取页。官方 CLI 负责 OAuth 存储和刷新，Python 不读取或分发 Token。每个新增批次附 UUIDv4 幂等参数；结果不确定时停止自动重复写入。

同一目标表只配置一台执行电脑。本地文件锁能防止这台电脑的任务重叠，不能锁住另一台电脑；迁移时先停用旧电脑任务。安装定时任务前，先手工运行一次并检查 Base 及回执；本包不会自动注册或启用计划任务。后续计划任务可每 30 分钟调用上述单次命令，并设置“已有实例运行时不启动新实例”。

## 使用 taskschd.msc 部署每 30 分钟任务

先完成本机 Python 环境、OES/Outlook 登录、飞书授权与手工同步验收。以下步骤只在未来的执行电脑操作；交付包生成与配置脚本都不会在原开发机安装任务或修改电源设置。

1. 使用将来执行任务的同一个 Windows 账号登录，在包根目录运行：

   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File .\prepare-task.ps1
   ```

   生成 `task-scheduler/oes-base.task.xml`，填入本机当前账号 SID、绝对路径和上海时区的下一个整点/半点开始时间。已有 XML 时脚本停止，需换 `-OutputPath` 或先归档旧文件。生成器只写 XML，任务初始禁用。包被移动、用户名或 Python 环境改变后重新生成。

2. `Win+R` 输入 `taskschd.msc`。在“任务计划程序库”选择“导入任务”，打开生成的 `oes-base.task.xml`。不要导入仍含 `REPLACE_WITH_...` 的原始模板。检查下表后保存；先完成下一节的防休眠配置，再右键“启用”。

| 页签 | 必须核对的值 |
|---|---|
| 常规 | 名称 `OES-Base-Sync`；账号为已完成飞书授权和网页登录的同一 Windows 用户；“只在用户登录时运行”（InteractiveToken）；勾选“隐藏”（Hidden）；普通权限即可 |
| 触发器 | 每天，重复间隔 30 分钟，持续 1 天；每天重复形成持续运行；开始时间按生成 XML；不要勾选重复结束时停止任务 |
| 操作 | 程序为本包 `.venv\Scripts\pythonw.exe`；参数为下面的专用静默入口；“起始于”为包根目录 |
| 条件 | 不要求空闲；允许电池供电及转为电池后继续；仅网络可用时执行；唤醒计算机运行任务 |
| 设置 | 允许按需运行、错过开始时间后尽快运行；已有实例时“不启动新实例”（IgnoreNew）；不设置失败自动重启或强制运行时限 |

3. 操作页示例（把 `C:\OES-Automation` 换为实际解压目录，参数保留双引号）：

   ```text
   程序：C:\OES-Automation\.venv\Scripts\pythonw.exe
   参数："C:\OES-Automation\skills\usql-web-query-operator\scripts\run_oes_base_silent.py" --settings "C:\OES-Automation\settings.json"
   起始于：C:\OES-Automation
   ```

   任务直接启动 `pythonw.exe`，使用已登录用户会话及 Hidden 属性。浏览器正常同步保持 headless，原生飞书 CLI 子进程使用 `CREATE_NO_WINDOW`。静默入口将控制台输出转到空设备，并额外记录启动/失败/退出码；OES、邮件、Base 阶段仍写原有 JSONL 日志。

4. 启用后右键“运行”一次。通过任务的“上次运行结果”与两类日志确认成功，最终再检查 Base 最近截止、行数和回读完成状态。`0x0` 表示退出码 0，`0x2` 表示脚本错误；运行中先等待，不要反复点击。任务被隐藏时，在菜单“查看 → 显示隐藏的任务”中找到它。可启用任务历史辅助诊断。

InteractiveToken 要求账号已经登录；可锁屏，但注销或重启后尚未登录时不会执行。Hidden 是任务列表显示属性，控制台静默由 pythonw 和静默入口实现。登录态过期需按上文手工刷新 OES 验证码登录，不把 `login --headed` 放进定时任务。[微软 InteractiveToken](https://learn.microsoft.com/en-us/windows/win32/taskschd/taskschedulerschema-logontype-principaltype-element)、[Hidden 属性](https://learn.microsoft.com/en-us/windows/win32/taskschd/tasksettings-hidden)。

## 执行电脑禁止自动睡眠和休眠

在未来执行电脑的“设置 → 系统 → 电源/电源和电池”中，将接通电源及电池供电时“使设备进入睡眠”设为“从不”。屏幕可以关闭，Windows 账号保持登录。笔记本在“控制面板 → 电源选项 → 选择关闭盖子的功能”中，把接电和电池下的合盖行为设为“不采取任何操作”。

管理员 PowerShell 可执行下面的等效电源配置。先记录原方案并导出备份；这是对该电脑电源设置的修改，只由部署者在执行电脑主动操作，安装和运行脚本不会自动执行这些命令。

```powershell
$oesPowerScheme = [regex]::Match((powercfg /getactivescheme | Out-String), '[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}').Value
if (-not $oesPowerScheme) { throw 'Cannot resolve the active power scheme.' }
$oesPowerBackup = Join-Path (Get-Location).Path ('power-before-oes-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.pow')
powercfg /export $oesPowerBackup $oesPowerScheme
powercfg /change standby-timeout-ac 0
powercfg /change standby-timeout-dc 0
powercfg /change hibernate-timeout-ac 0
powercfg /change hibernate-timeout-dc 0
powercfg /hibernate off
# 笔记本合盖不睡眠；台式机可略过以下两项
powercfg /setacvalueindex SCHEME_CURRENT SUB_BUTTONS LIDACTION 0
powercfg /setdcvalueindex SCHEME_CURRENT SUB_BUTTONS LIDACTION 0
powercfg /setactive SCHEME_CURRENT
```

执行每条命令后确认没有错误，并在 GUI 中复核“从不”及合盖行为。`/hibernate off` 会关闭系统休眠功能；公司电源策略若覆盖本机设置，需由公司的设备管理员维护允许持续运行的配置。保留方案 GUID、备份及原休眠状态；停止使用此电脑执行任务时，可导入备份方案并选择导入后的 GUID，原来启用休眠的电脑再执行 `powercfg /hibernate on`。[微软 powercfg 文档](https://learn.microsoft.com/en-us/windows-hardware/design/device-experiences/powercfg-command-line-options)、[合盖行为](https://learn.microsoft.com/en-us/windows-hardware/customize/power-settings/power-button-and-lid-settings-lid-switch-close-action)。

“唤醒计算机运行此任务”是辅助设置；电脑关机、注销或人为进入睡眠会影响执行。每半小时任务之间电脑也必须保持运行，因此只在 Python 运行期间防休眠不能替代上述电源配置。

## 文件和故障恢复

- `data/runtime`：OES 与 Outlook 各自的登录态、文件锁、精简完成索引及日志。
- `data/runs/base-sync-*`：完整 Excel、源查询、旧 Base 备份、切分计划、删除阶段回执、覆盖写入回执、逐字段远端回读文件及耗时。
- `completed`：数据已覆盖且全部字段核验一致。重复同一运行标识会重新核验远端表，不再导出、删除或写入。
- `completed_cache_expired`：该标识已完成，但完整缓存已被清理或缺失；只返回精简索引，不做远端回读或再次覆盖。
- `failed_restored`：源获取或确定的后续阶段失败，旧数据值已恢复并核验；同一标识可再次尝试，已完成导出结果会复用。
- `base_write_uncertain/failed_requires_recovery`：保留备份和回执，先判断远端请求是否已受理，不能盲目重复批次。

## Excel 缓存与磁盘维护

查询有数据的新运行会先把邮箱 Excel 下载到本机，校验附件与完整 OES 查询一致，再读取其全部字段写 Base。确认 0 条时保存空结果，不请求无数据的邮件。默认位置为：

```text
data/runs/base-sync-<运行标识Hash>/
  base-receipt.json
  excel-records.json
  previous-records.json
  source/oes-run-<标识Hash>/
    # 未分批：本层保存原始附件和查询文件
    # 分批：batches/oes-run-<批次Hash>/ 内保存各份原始附件
    oes-achievement-combined.xlsx   # 分批成功后额外保存合并文件
```

原附件以邮件 Hash 命名，每个新运行使用独立目录。文件在下载时校验行数、订单/班级/用户/金额及 SHA-256，Base 写入后另存完整字段快照和远端回读。重复同一运行标识优先复用已完成文件或已有受理回执，避免重复导出；每个新的半小时时段会产生一轮新文件。

**默认自动清理完成超过 7×24 小时的成功任务目录。** 每次 `sync` 在目标表文件锁内、查询和删除前执行清理。年龄以回执的 `completed_at` 为准，与订单日期、配置起点和文件修改时间无关；恰好 7 天仍保留。删除整个目录，包括原始/合并 Excel、查询 JSON/CSV、旧表备份、分页回读和回执；因此不会只删附件而留下大量其他缓存。

仅清理本配置对应 Base/目标表、状态为 `completed` 且具备完整 13 字段零差异核验摘要的任务。失败、进行中、写入结果不确定、其他目标或无法确认的目录继续保留；登录态、凭据及飞书授权不在清理范围。包含符号链接或 Windows junction 的目录停止清理并记日志，防止递归删除越出目标。旧版本完整成功回执首次遇到时会先登记精简索引；删除前持久化索引，途中被文件锁阻断可在下次继续。精简索引必须与 `data/runs` 分开，不能整体删除它。

`settings.json` 中 `cache_retention_days` 默认 7，`log_retention_days` 默认 30；范围均为 1～3650 的整数，旧配置缺少键时使用默认值。原生 CLI 对应 `--cache-retention-days`、`--log-retention-days`。可单独执行本地清理：

```powershell
powershell -NoProfile -File .\run.ps1 -Action cleanup
```

`cleanup` 不登录 OES/Outlook，也不读取或修改飞书表。清理错误记录在日志及输出的 `cache_cleanup.failed_runs` 中，保留无法删除的文件；不妨碍正常的新任务同步。

日志按上海日期自动换文件，保留当前日和前 29 个日历日。记录运行开始/完成/失败、OES 查询和切分、导出受理、邮件附件核验、Base 备份/删除/每批写入/回读、恢复状态，以及清理目录数、文件数和释放字节。只记录运行元信息，账号密码、Cookie、Token、订单明细及原始异常内容不写入日志。输出提供 `log_file` 和 `log_write_errors`；启动时日志无法写入会在覆盖前停止，远端操作已开始后的日志失败只累计错误，不撤销已核验的数据。

2026-10-04 的 11,013 条验收运行有 57 个文件，共 39,747,045 字节（约 39.7 MB），其中 3 份 Excel 共约 2.3 MB。若每天 48 次且每轮大小相同，最近 7 天成功任务约占 13.4 GB，此外还有失败任务、精简索引及日志。清理控制保留时长；容量会随数据量变化，这只是样本估算。

目标表短暂为空是删除后覆盖流程的正常阶段；Base 不提供整表原子替换事务。OES 或邮件失败会尽可能恢复已备份的旧数据值，恢复不保证保留旧 record_id。若进程被强制结束，回执用于诊断和续跑；写入阶段不确定时停止自动重复操作。

OES 状态过期遇到验证码时重新执行 `-Action login`；Outlook 普通登录失效时尝试一次恢复，额外验证需人工处理。Base 保持启用配置不会自行启动调度。输出包含个人信息，回执、备份和登录态目录由部署者按公司要求限制访问及定期归档。
