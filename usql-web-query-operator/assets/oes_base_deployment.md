# OES → Outlook Excel → 飞书 Base 一键部署

同事电脑无需 AI 工具、Python、Anaconda 或 Node.js。本包内置官方 Python 3.13.16 Windows x64 嵌入版、固定版本的全部依赖，以及原生官方飞书 CLI。向导使用 Windows 自带 PowerShell 5.1，不修改系统 PATH 或全局 Python。

支持 Windows 10/11 Intel/AMD 64 位电脑。优先使用 Edge；无法启动 Edge 时自动联网下载本应用私有 Chromium。公司网络、两站登录及飞书 API 仍需在线连接。ARM64、32 位 Windows，以及公司禁止脚本或浏览器自动化的环境，需管理员另行适配。

## 同事只需四步

1. 将整个 ZIP **全部解压**到本地，双击 `Install.cmd`。不要直接在压缩包内运行，不要以其他用户身份启动向导。
2. 填本人 OES / Outlook 账号密码，以及管理员提供的飞书应用 App ID / App Secret。Base、配置表和配置记录已填好，通常无需修改。默认安装到 `%LOCALAPPDATA%\Gaotu\OesBaseSync`，不用手工编辑 JSON 或 env。
3. 核对目标，勾选“删除历史并覆盖写入”的确认；按需勾选启用自动任务和电源调整（两项默认均关闭），再点击“一键安装 / 修复并验收”。按弹窗的链接或二维码完成本人飞书授权；在程序打开的 OES 浏览器中输入验证码并点击登录。Outlook 使用相同账号密码登录并保存状态。
4. 等待首次完整同步及全部 13 字段回读成功。仅在选择了电源调整时，向导才请求管理员批准并调整本机电源；仅在选择启用自动任务时，向导才注册、回读并启用每 30 分钟任务。显示 `active` 才代表自动运行已启用；未选择时保持 `disabled`，首次同步仍会执行。

安装期间保持向导打开，收邮件及全量验收可能需要几分钟，界面显示当前步骤。失败会停用本安装的后续调度，保留回执及备份；再次打开可修复。失败或结果不确定的首次同步保留原运行标识，不自动换标识重提。已完成的验收或已清理的完成索引允许以后维护时生成新的验收运行。

## 交付前管理员准备

| 项目 | 要求 |
|---|---|
| 飞书公司应用 | 提供 App ID / Secret；开通并发布 Base 域所需权限：字段 / 配置 / 全表记录读取、原生批量创建 / 删除、配置状态回写和用户 OAuth 授权。向导只申请 `--domain base` |
| 本人权限 | 应用允许该同事使用，本人有目标 Base 编辑权限，OES 账号能查看所需业绩范围 |
| 单一执行电脑 | 同一目标表仅由一台电脑运行；迁移前暂停旧电脑任务。本地锁不能防止跨电脑覆盖 |
| 网络与策略 | 可访问 OES、CAS、Outlook、飞书；允许 PowerShell、官方 CLI、Python 和自动化浏览器；电源调整有管理员协助 |
| 日期配置 | 已创建的“导出配置”记录启用，开始时间由 Base 维护。原验收值为 `2026-06-19 00:00`；安装不重设开始时间 |

应用权限、公司审批、本人授权、验证码及可能的 MFA 必须由本人或管理员完成。向导已代替手工命令、环境安装、目录创建、参数填写和任务导入。Outlook 当前支持普通 OWA Light 登录，额外验证或页面变化会停止并提示维护。

## 后续维护

双击桌面“**OES同步管理**”快捷方式，或安装目录的 `Install.cmd`。桌面受公司策略限制时可继续用安装目录入口。账号可显示，密码和 App Secret 不回显。

| 按钮 | 行为 |
|---|---|
| 一键安装 / 修复并验收 | 暂停并检查本安装的任务，保留配置与运行数据，修复授权及登录，完整同步验收后重新启用。已有密码 / 应用配置时相应密码框可留空 |
| 只读检查 | 在线检查两站登录、Base 13 字段、启用配置和凭据，不导出或替换 Base。Outlook 普通登录过期时可更新本机状态 |
| 暂停自动同步 | 禁止后续定时启动，正在执行的同步继续，不强制中断 |
| 移除定时任务 | 检查身份后移除本安装任务，保留程序、凭据、缓存、日志和备份。正在执行 / 排队时等待完成 |
| 恢复原电源设置 | 先暂停任务，申请管理员权限，根据首次备份恢复并回读；独立变更或活动电源计划变化时停止，交由管理员核对 |
| 打开日志 | 打开本机 `data`，包含部署日志、运行日志与失败回执 |
| 任务计划程序 | 打开 `taskschd.msc`；用“查看 → 显示隐藏的任务”找到任务 |

改密码或换账号时填新值，向导只重建两站状态，不清空任务数据。应用变更时填写新 App ID / Secret 并重新授权。OES 登录态失效需要再次可见验证码登录；独立打开普通浏览器登录不会保存到脚本状态。

维护时现有任务正在执行 / 排队会停止，等待完成后再操作。不要强行结束全量替换进程。`write_pending`、`export_uncertain` 等回执须先核对实际邮箱和 Base，再处理恢复；失败目录不会被 7 天规则删除。

## 本机信息及缓存

相对路径以安装目录为准。`private` 和 `data` 的 NTFS 权限限制为当前用户、SYSTEM 和本机管理员。凭据、登录态、明细及备份仍是敏感本机文件，不随部署 ZIP 转发。

| 内容 | 位置 / 说明 |
|---|---|
| 本机参数 | `settings.json`：目标 ID、专属飞书 profile、相对路径及保留天数，不含密码 / Token |
| OES / Outlook 凭据 | `private/usql_api.env`，共用精确 `# mi.gaotu100.com OES Web Query (Playwright) credentials` 区段，由向导生成 |
| 安装进度 | `private/install-state.json`：SID、安装 ID、任务名、阶段及验收运行标识 |
| 飞书授权 | 官方 CLI 本机命名 profile `oes-base-<安装ID前16位>`；API 显式指定 profile，Python 不提取 Token；App Secret 仅通过 stdin 给 CLI |
| OES 登录态 | `data/runtime/oes-achievement/state.json` |
| Outlook 状态 / 绑定 | `data/runtime/oes-outlook/state.json`、`state.account` |
| 私有 Python | `runtime/python/`；`payload/` 为固定离线安装源，不是每日缓存 |
| 私有浏览器 | Edge 不可用时下载到 `data/browsers/`，不按 Excel 缓存删除 |
| Excel、备份、核验 | `data/runs/base-sync-*`：原始附件、合并 Excel、旧表备份、字段快照、回执与完整回读 |
| 精简完成索引 | `data/runtime/completed-runs/<目标Hash>/`，长期保留，防止旧标识重复运行 |
| 阶段日志 | `data/runtime/logs/<目标Hash>/oes-base-YYYY-MM-DD.jsonl`，默认 30 个日历日 |
| 静默启动日志 | `data/runtime/launcher-logs/oes-launcher-YYYY-MM-DD.jsonl`，跟随日志保留参数 |
| 部署日志 | `data/installer-logs/installer-YYYY-MM-DD.jsonl`，保留 30 日，仅记录阶段和状态，不保存控制台原文、密钥、登录 URL 或设备码 |
| 电源备份 / 回执 | `private/power-before.json`、`power-before.pow`、`power-result.json`，首次原值不被重复安装覆盖 |
| 任务 XML | `task-scheduler/task-*.xml`，本机 SID、绝对路径、上海开始时间；任务名 `OES-Base-Sync-<安装路径Hash前8位>` |

每次运行会生成本地 Excel 和核验缓存。以完成时刻计算，本目标已完成且全字段核验成功、超过 **7×24 小时**的整任务目录自动删除。失败 / 待恢复任务、状态、凭据、完成索引及电源备份保留。缓存 / 日志参数为 `cache_retention_days` / `log_retention_days`，默认 7 / 30。到期旧标识仅返回历史完成摘要，不能冒充当前远端已再次核验。

## 自动同步及性能

每次新运行从 Base 固定开始时间查询，截至本次运行的实际上海时间；开始时间不推进。超过 1 万条按连续毫秒闭区间拆分，下一段从上一段末尾加 1 毫秒开始。每段及合并 Excel 与完整查询核验，保留重复流水。

完整备份 / 删除旧 Base 数据与 OES 导出 / 邮件下载并行。表空后原生接口每批最大 **500 条**写入全部字段；读取每页 **2000 条**并检测 `has_more/next_offset` 和版本，最终完整验证 13 字段。每张表写请求保持串行。按当前上海半小时时段生成稳定标识，续跑不重复受理导出；`IgnoreNew` 与本机目标锁防重叠。

Base 没有整表原子替换，运行期间可能暂时为空。失败按回执尝试恢复历史值，恢复可能产生新 record_id；结果不确定时停止自动重复写入并保留备份。

## 电源及 Windows 登录

默认在未来执行电脑首次备份活动电源计划及 AC / DC 睡眠、休眠、合盖值，设为不自动睡眠 / 合盖不采取操作，关闭系统休眠。独立提权进程执行并回读；拒绝 UAC 时自动任务不会启用。飞书授权与任务仍属于启动向导的 Windows 用户。

电脑保持开机、网络在线，该 Windows 用户**保持已登录**，可以锁屏。注销 / 关机后 `InteractiveToken` 不能执行。`Hidden` 控制任务列表，静默由 `pythonw.exe`、headless 浏览器及 CLI 的 `CREATE_NO_WINDOW` 实现。低电量、公司强制策略、人工关机和更新可能中断运行。

恢复只针对本安装备份的相关设置，不自动导入整张计划覆盖其他变更；独立变更或恢复失败由管理员结合 JSON / `.pow` 处理。制作及测试交付包不在开发电脑注册真实任务、更改电源或执行生产替换。

## 升级、迁移、卸载

同一运行时版本升级：解压新包、双击新包 `Install.cmd`，选择原安装目录；暂停本安装任务后更新代码，保留本机配置、凭据、状态、索引及失败备份，再验收。运行时版本变化时向导停止，使用新目录部署，并先停用旧任务。

2026-10-04 的手工部署包还没有安装身份记录，首次使用本向导应选择新的默认目录；先在任务计划程序中暂停原手工任务。向导不会自动接管未绑定安装身份的旧任务，也不会覆盖其他程序目录。

新电脑重新填写本人凭据并授权，不复制旧 Token 或浏览器状态。旧回执含绝对路径，不保证搬到新路径后续跑；旧失败任务先在旧电脑核对处理。

卸载：移除定时任务，按需恢复电源，归档日志 / 失败备份后自行删除安装目录。飞书服务端授权由本人在授权管理页撤销；“移除任务”不静默删除 profile、数据和凭据。

## 管理员入口

高级命令仍保留：`run.ps1 -Action login/mail-login/check/health/sync/cleanup`。默认使用内置 Python，旧 `.venv` 路径兼容。

`prepare-task.ps1` 仅生成禁用 XML，可手动用 `taskschd.msc` 导入。`install.ps1 -Mode VerifyPackage` 只校验清单；`-Mode PrepareOnly -InstallRoot <隔离目录>` 仅复制文件及离线运行时，拒绝修改已注册任务，不配置凭据 / 授权 / 任务 / 电源。`power.ps1 -Mode Plan -Root <安装目录>` 只读返回计划。真实修改由向导明确勾选和 UAC 同意发起。

参考：[Python 官方嵌入式分发](https://docs.python.org/3.13/using/windows.html#the-embeddable-package)、[3.13.16 下载及 SHA-256](https://www.python.org/downloads/release/python-31316/)、[飞书官方 CLI](https://github.com/larksuite/cli)。
