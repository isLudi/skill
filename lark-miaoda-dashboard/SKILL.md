---
name: lark-miaoda-dashboard
description: |
  【妙搭看板 + 数据分发专项】两件事的完整 SOP：
  A. 做飞书妙搭（Miaoda）数据看板：飞书 Base 取数 → 本地聚合 data.json → git 推送妙搭仓库 → release 发布 → Windows 每日定时刷新。
  B. 数据分发：把 Excel 按列切割（如按顾问/部门）→ 飞书私聊逐个发给对应的人。
  C. 本地群推送：全渠道 Base 线索明细 → 选择渠道/期次 → 过程和结果图片/文字 → 渠道后25%顾问名单（不@）→ 指定群发送。

  以下场景必须加载此 skill：
  1. "做一个妙搭看板""把看板发布到妙搭""看板每日自动更新""接手/交接妙搭看板"
  2. "把表按 xx 切开发给对应的人""切割 Excel 私聊发送""分发表格""按人拆分下发"
  关键词：妙搭 / miaoda / 看板 / dashboard / data.json / release / 切割 / 拆分 / 分发 / 私聊发送 / 群推送 / 多维表格推送
  普通妙搭应用创建、云端开发、数据库、成员或运行时权限等不属于本 SOP 的请求仍走 lark-apps；本 skill 聚焦静态数据看板刷新、Excel 分发和 Base 群推送。

  前置：lark-cli 已登录 user 身份；发布妙搭需 apps 域授权，私聊发送需 im:message.send_as_user。
  在本地 Codex 中优先使用本地 lark-base / lark-apps / lark-contact / lark-im / lark-shared Skill；deps/ 仅是随包快照，命令事实以本地权威 Skill 和 lark-cli --help 为准。
metadata:
  short-description: "妙搭看板搭建与飞书 Excel 安全分发"
---

# 妙搭看板搭建 + 数据分发（lark-miaoda-dashboard）

三部分：A. 从零做/接手一个妙搭看板；B. 把 Excel 切割后飞书私聊分发；C. 本地执行 Base 按渠道过程/结果数据群推送。
模板：`templates/export_base.py`（Base 分页导出）、`templates/refresh.py`（每日刷新流水线）、`scripts/excel_split_send.py`（切割分发）、`scripts/group_push.py`（Base→群消息）。用户确认的推送源保存在 `config/push_source.json`；Base token 在运行时解析，不在配置、消息或日志中保存凭证。

## 本地 Codex 适配

- 安装位置是 `C:\Users\Ludim\.codex\skills\lark-miaoda-dashboard`，入口是本文件；`agents/openai.yaml` 提供 Codex UI 可见性与自动路由元数据。
- Windows 下脚本默认使用本机 npm 包内的原生 `lark-cli.exe`，也可通过 `LARK_CLI` 指定已验证的可执行文件；不自动退回 `.cmd`/`.bat` shim。
- Python 示例统一使用 `D:\anaconda3\python.exe`。脚本内部会继承当前解释器，但计划任务仍应显式指定该解释器。
- 脚本通过参数列表调用 CLI 并强制 UTF-8，不使用 `shell=True`；Base token 等敏感参数不会拼进失败摘要。
- `refresh.py` 的发布必须显式传 `--confirm-publish`；普通推送失败时不会自动强推，只有设置 `MIAODA_ALLOW_FORCE_PUSH=1` 才允许一次 `--force-with-lease` 尝试。

---

## A. 妙搭看板全流程

### A.1 架构认知（先理解再动手）

```
飞书多维表格 Base
  → lark-cli base +record-list 拉数（--output ndjson，每页≤2000，--as user）
  → build_data.py 本地聚合成 data.json（含 meta.exported_at）
  → 拷贝进应用仓库 app/（index.html + data.json）
  → git push 到 miaoda-git.feishu.cn（妙搭自带代码仓，凭证走 lark-cli）
  → lark-cli apps +release-create 发布 → 页面更新
```

- 页面是**纯静态 HTML**，浏览器 fetch 同目录 `data.json` 渲染，无后端；所以数据更新 = 换 data.json + 重新发布
- **一个妙搭应用 = 一个独立 git 仓库 + 一个独立 app_id**。分支不等于页面！（踩坑：曾把同一业务线的两个看板当成"同一应用的两个分支"，实际其中一个有独立 app_id，发布全打在了错误的应用上）
- 拿到别人的看板先确认真实 app_id：打开页面 → iframe src 里的 `app_XXX` 才是真身，别信文档描述

### A.2 搭建步骤

1. **取数**：在 PowerShell 中用 `templates/export_base.py` 分页拉 Base 表：`$env:BASE_TOKEN='<base_token>'; $env:TABLE_ID='<tblXXX>'; $env:FIELDS='字段1,字段2'; & 'D:\anaconda3\python.exe' '.\templates\export_base.py'`，多张表跑多次
2. **聚合**：build_data.py 输出紧凑 data.json（先聚合再进仓库，别塞明细；1.5MB 以内为宜）
3. **页面**：index.html 里 `fetch('data.json?t='+Date.now(), {cache:'no-store'})`，表头显示 `meta.exported_at` 快照时间
4. **仓库与凭证**（关键，否则 git 弹账号密码框）：
   ```bash
   cd app/
   lark-cli apps +git-credential-init --app-id <app_id> --as user   # 自动配好 credential helper + 提交者身份
   git push origin sprint/default                          # 历史分叉时先停下核验，不自动强推
   ```
5. **发布**：
   ```bash
   lark-cli apps +release-create --app-id <app_id> --branch sprint/default --as user
   lark-cli apps +release-get --app-id <app_id> --release-id <rid> --as user   # 轮询到 finished
   ```
   **必须显式带 `--branch`**：不带时服务端取的分支不确定（踩坑：曾把全量版数据发到了在职版分支的发布）
6. **权限**：Base 加协作者（可编辑）；妙搭应用 `+member-add` 加管理员；开放平台自建应用加成员

### A.3 每日自动刷新（Windows 计划任务）

- 封装单脚本 `templates/refresh.py`：导出→构建→闸门校验→commit→push→release→轮询，失败即停；用 `MIAODA_APP_ID` 环境变量传入 app_id，不写死。正式发布必须显式传 `--confirm-publish`，仅推送调试用 `--no-publish`。
- 本地 Codex 的 Windows 计划任务优先直接调用 `D:\anaconda3\python.exe <项目>\refresh.py --confirm-publish`，避免 PowerShell、cmd shim 和解释器漂移；如必须使用 bat，保持 GBK + CRLF 并只把它作为薄启动器。
- 多个任务共用同一 git 仓库时**错开时间**（实例：8:00 / 8:20 / 8:40）
- 任务属性是"仅用户登录时运行"：开机+登录即跑，锁屏没事，关机当天不刷
- 发布前数据闸门不可省：`exported_at` 必须是当日、关键数组非空（2026-08-19 曾出现约课字段全 0 差点发空数据）

### A.4 接手别人看板的检查清单

1. 确认真 app_id（iframe src）和真仓库（`lark-cli apps +git-credential-init --app-id X` 会返回 repository_url）
2. Base / 应用 / 自建应用三类权限转到自己名下
3. 脚本里的硬编码路径改相对路径；子进程强制 `encoding="utf-8"`（Windows GBK 解码会炸）
4. 运行前以 `lark-cli base +record-list --help` 检查 `--output/--overwrite`；本机当前已验证 1.0.87 提供这些参数，若环境不一致先按 `lark-shared` 处理版本/授权，不在脚本中自动升级
5. **确认原负责人的定时任务已关停**（否则两边互顶 git，push rejected 后 force 互相覆盖）
6. 手动全链路跑一次：导出→推送→release finished→浏览器核对页面快照日期

---

## B. Excel 切割分发（飞书私聊）

脚本 `scripts/excel_split_send.py`：一张总表 → 按列切成 N 份 → 逐个私聊发送。

```bash
Set-Location 'C:\Users\Ludim\.codex\skills\lark-miaoda-dashboard'
$env:PYTHONIOENCODING='utf-8'
$env:PYTHONUTF8='1'
$PY='D:\anaconda3\python.exe'

# ① 切割：按「顾问姓名」拆，每人一个 xlsx，文件名=姓名
& $PY '.\scripts\excel_split_send.py' split --file 底表.xlsx --sheet 顾问分周 --by 顾问姓名 --out out/distribute/

# ② 演练：只打印"谁收到什么"，不真发（重名/查无此人会列清单）
& $PY '.\scripts\excel_split_send.py' send --dir out/distribute/ --dry-run

# ③ 正式发送（文件名带工号如 丁雪04.xlsx 时加 --strip-digits）
& $PY '.\scripts\excel_split_send.py' send --dir out/distribute/ --strip-digits --message "你的数据见附件，请查收：{name}"
```

**规则（安全红线）**：
- 收件人 = 文件名去扩展名，按飞书姓名**唯一精确匹配**；重名/模糊/查无此人一律跳过并列清单，绝不猜着发
- `--dry-run` 必跑；正式发送前把「收件人数 + 跳过名单 + 附言」给用户确认
- 切割后抽查 1~2 个文件确认没串行（切错列会把别人的数据发错人）
- split 会生成 `_mapping.csv`（收件人/行数/文件）用于对账
- 需要授权 `im:message.send_as_user`（一次性）：`lark-cli auth login --scope "im:message.send_as_user"`，scope 授权一次长期有效

---

---

## C. 多维表格按渠道群推送（本地脚本）

`scripts/group_push.py` 编排官方 CLI 取数、图片上传和群消息发送，`scripts/lead_report.py` 负责纯本地汇总。当前推送统一只列姓名，不查询通讯录、不生成任何 @。无需妙搭额度或常驻服务；只有执行期间需要电脑开机、联网及有效的 CLI 登录。

### C.1 默认数据源和计算口径

用户已确认后续使用 [全渠道播报_推送配置](https://gaotuedu.feishu.cn/wiki/MrPNwuFvPiiDX0k4jTXcLU8anse?table=tblqvlnqNslL1nWA&view=veweZNrbGI)。源配置保存在 `config/push_source.json`，默认 `source_mode=lead-detail`。该链接指向**配置表**，同一 Base 的 `市场顾问原始数据`（`tbljWRvaqKTdrCx4`）才是线索来源。

- 配置表：仅请求 `配置名称`、`渠道`、`推送类型`、`推送标题`、`推送期次`、`推送说明`、`接收群` 7 个字段，通过固定视图 `veweZNrbGI` 按本次渠道、类型选取唯一记录。该视图必须保留并覆盖有效配置；不能用筛选隐藏正式任务的配置。未配置的新渠道可使用本地默认文案，不自动建配置记录。
- 线索表：按**精确渠道 + 期次**筛选，图片粒度是 `期次 × 渠道 × 经理 × 主管`。必须显式选择 `--channel`，不会默认把所有渠道发出；`--channel 全部渠道` 才读取全部渠道，并在图片中增加渠道列。
- 各率和总计：先累加原始分子/分母再相除，不平均汇总行的百分比。`总通时=总通时秒/60`，`单效=净收款/退后线索`，`单效(当期)=当期净收款/退后线索`，`人均报科=报科数/成交人头`，`订单转化=报科数/退后线索`，`退费率=退费/收款`，沿用已核验的原始指标口径。负单效和超过 100% 的退费率不截断显示。
- 提醒：用户最新确认采用**同一期次、所属渠道后25%**，不再比较主管或渠道均值。本地按 `渠道 × 主管 × 顾问账号` 汇总，并校验姓名唯一性；维度键为 `渠道|主管|顾问`。过程按 `5min标记之和/退后线索之和` 从低到高排名；结果按 `净收款之和/退后线索之和` 从低到高排名。只纳入退后线索大于 0 的顾问维度，名额为 `ROUNDUP(有效顾问数×25%,0)`，同分按维度键升序固定取足名额，选中姓名再去重。计算不提前四舍五入。选择全部渠道时，各渠道独立排名和取名额。
- 全员同分（包括单效全部为 0）时，仍按维度键取后25%名额，这是已确认的规则；不能自动改成“不提醒”或扩成“并列全部提醒”。群消息说明不展示提醒规则，过程提醒写作“本次5min率较低顾问：……”，结果提醒写作“本次单效较低顾问：……”。最新要求统一只展示顾问名称，不 @ 顾问、主管或其他人员，也不附加“请主管关注”名单；后台排名和名额不变。
- 提醒的有效顾问范围以**原始线索全量**为准（`reminder_population=raw_leads`），不依赖提醒辅助表及其工作流；原始线索新顾问自动纳入本地排名。远端 `计算_提醒顾问`/`提醒` 不是读取依赖；缺少这两列时，不产生虚假的辅助名单缺失告警。内部同名字段只是本地计算结果，不需要在 Base 重建。
- 图片、汇总文字和提醒均由同一批线索生成。原始表不增加公式、关联或计算列，适配天宫 2 全量覆盖写入。动态 `推送期次` 公式仅依赖原始表的 `期次`，必须保留。

精简 Base 时不能只检查本地读表：当前天宫写入还依赖原始表全部 45 个接收字段，以及经理表 `tblvBLOSRUggxsBF`、主管表 `tblQp7kAaLd6rkIh` 的 `汇总键`、`顾问账号`、`渠道` 3 个文本字段和全渠道键记录；删除会使上游失败。两张表的旧指标/图片视图不是本地推送来源。原始表视图 `vewO4yxS3O` 也因上游源链接固定引用而保留。完整依赖与定时任务运维见 [config/SCHEDULED_PUSH.md](config/SCHEDULED_PUSH.md)。

数据完整性门禁：完整分页到 `has_more=false`，使用真实 `next_offset`，校验分页行数、记录 ID、`rev` 和 `query_context`；校验 `期次+lead_id` 唯一、必要字段及数值有效、数据分区一致。分页遇到版本变化、多期不明确、重复线索、混合分区、缺字段或全零占位数据立即停止。此门禁不替代上游“全量写入完成”信号；实际推送应安排在天宫写入完成之后。

每个选中类型固定五部分：**推送标题 → 图片 → 推送期次 → 推送说明（含汇总数据）→ 提醒**。说明使用实际 `分区日期/分区小时`，不再沿用模板中静态的“2小时前”。图片保留参考样式：深蓝表头和总计、线索留存条件色及数据条。过程图不含结果指标；结果图包含单效、人均报科、人头/订单转化、净收款和退费率。源表没有的 `6h/12h/24h` 列不显示。

过程图和结果图均隐藏 `退前线索=0 且 退后线索=0` 的人员明细行，即使该行还有通话或其他指标；只要其中一列不为 0，就保留。空值或缺失值不能当作 0。此过滤仅影响图片展示，不删除原始记录，不改变全范围总计、文字汇总和提醒名单；如果全部人员行被隐藏，只显示表头和总计。预览输出显示隐藏行数。

### C.2 先预览，不发送

先按 `lark-base` 的当前指引核验读取权限，涉及发送时再使用 `lark-im`。当前不启用 @，无需 `lark-contact` 或提醒人员入群核验。PowerShell 示例：

```powershell
Set-Location 'C:\Users\Ludim\.codex\skills\lark-miaoda-dashboard'
$env:PYTHONIOENCODING='utf-8'
$env:PYTHONUTF8='1'
[Console]::InputEncoding=[System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new($false)
$OutputEncoding=[Console]::OutputEncoding
$PY='D:\anaconda3\python.exe'

# 只读查看已配置的渠道和期次
& $PY '.\scripts\group_push.py' list-channels

# 生成两张图片及文字预览；此处不查询通讯录、不发送
& $PY '.\scripts\group_push.py' preview --channel 'KOC-周帅数学' --report-type both --no-mentions

# 只推过程数据时，连原始收款/退费等结果字段也不读取
& $PY '.\scripts\group_push.py' preview --channel 'KOC-周帅数学' --report-type process --period '20260911期' --no-mentions
```

`--report-type` 可选 `process`、`result`、`both`（默认两类）。未指定 `--period` 时采用所选配置的期次；配置不明确且源表有多个期次时必须指定。预览文件写入当前工作目录下 `runtime/channel-broadcast-push/preview-<唯一标识>/`，过程/结果 PNG 文件名包含期次和渠道，避免多次预览互相覆盖。可用 `--state-dir` 改路径；显式图片路径已存在时不覆盖。`--no-image` 只生成文字和汇总。NDJSON 明细只存临时目录，读取完即清理，不持久保存原始线索。

默认新源**不继承**旧 `SOURCE_URL`、`BASE_TOKEN`、`TABLE_ID`、`VIEW_ID` 环境变量，避免悄悄退回旧表。覆盖数据源必须显式传 `--source-url` / 坐标参数以及匹配的 `--raw-table-id`。旧汇总视图只通过 `--source-mode summary-view` 兼容，且需显式提供旧源 URL 和文字源 URL；新流程不要调用 `sync-helper`，也不再读取旧 IP 汇总/提醒表。

### C.3 显式确认后发送

先确认本次渠道、期次、类型、目标群、发送身份、两张图片和顾问提醒名单。配置中只有一个共同接收群时可读取该群，否则用 `--chat-id` 明确；参数与配置群冲突时停止。精简配置表没有“启用/发送触发”，不通过 Base 工作流触发本地任务；手动发送的授权来自本次确认和 `--confirm-send`。

```powershell
# 只校验请求形状，不上传、不发送；仅列顾问姓名
& $PY '.\scripts\group_push.py' preview --channel 'KOC-周帅数学' --report-type both `
  --chat-id '<oc_xxx>' --chat-name '<群精确名称>' --no-mentions --cli-dry-run

# 仅在用户确认同一目标与内容后执行
& $PY '.\scripts\group_push.py' send --channel 'KOC-周帅数学' --report-type both `
  --period '<已确认期次>' --chat-id '<oc_xxx>' --chat-name '<群精确名称>' `
  --as user --no-mentions --confirm-send
```

`config/push_source.json` 的 `mention_target=none` 统一启用 `--no-mentions`，新明细模式和旧汇总视图均只列顾问姓名。它优先于遗留的 `--mention-target consultant/supervisor`、`--mention-map`、`--strict-mentions` 和提醒人员群资格参数：不读取映射文件、不解析账号、不核验提醒人员入群，也不因此阻止推送。目标群和发送机器人本身的资格、消息权限及数据质量检查仍保留。顾问和主管的旧 @ 能力仅作兼容保留，未经用户重新明确要求，不调整该策略恢复 @。

图片上传需相应发送身份的资源权限。成功的完成边界是**消息返回实际 `message_id`**，不是本地图片生成、dry-run 或仅上传成功。此后立即分别删除本次过程/结果 PNG，释放磁盘空间；上传后消息失败、未返回 ID、预览和 dry-run 都保留 PNG 供检查。删除失败单独告警，删除状态写入台账。不要为了清理图片递归删除整个状态目录。

幂等台账默认 `runtime/channel-broadcast-push/send_ledger.jsonl`；键绑定来源、渠道、期次、类型、分区、群、发送身份、图片开关、指标、文案和提醒模式。相同内容已有成功回执时跳过重复发送。实际外发后的验收还应使用 `lark-im` 独立读取消息，确认目标群、两张图片、文字及不含任何 @；本地测试回执不算真实送达。

### C.4 定时执行和验证

已获授权的本机方案使用 `scripts/scheduled_push.py` 和 Windows 任务 `Codex-Lark-Market-KOC-GroupPush`，每天仅 09:20、13:20、17:20、21:20 向 `【自营koc】&【高阳团队】` 分别发送周帅、孟亚飞两渠道的过程和结果，身份为机器人“管家”。时点前 5 分钟隐藏启动准备，未就绪每 2 分钟重查至 :50，不发送旧数据或补历史轮次；执行版本绑定、上游完整日志、Base 行数/版本、文件锁、SQLite 回执和独立读回均不可省略。实际到达包含接口耗时，运行时电脑需开机联网且 Windows 用户已登录。

时点、首轮时间、渠道及目标身份以 `config/scheduled_push.json` 为运行依据，管理和故障处理见 [config/SCHEDULED_PUSH.md](config/SCHEDULED_PUSH.md)。本地维护或回归测试不授权额外群消息、重注册任务、重启服务、修改天宫或清空发送回执。

修改后运行受影响的离线测试，并用新源真实读取做本地预览和数值核对。测试消息接口必须 mock；不能把回归测试发到业务群：

```powershell
& $PY '-m' 'unittest' 'discover' '-s' '.\tests' '-v'
```

## 依赖（已打包在 deps/）

| 用途 | 技能 | 命令 |
|---|---|---|
| Base 取数 | `lark-base` | 先读 `../lark-base/SKILL.md`，再按当前 CLI help 使用 `base +record-list` |
| 姓名 → open_id | `lark-contact` | `contact +search-user --query <姓名> --as user` |
| 私聊发文件/文字 | `lark-im` | `im +messages-send --user-id <id> --file/--markdown --as user` |
| 群推送/图片 | `lark-im` | `im images create`（仅真实发送时）→ `im +messages-send --chat-id <id> --markdown ...` |
| 妙搭应用管理 | `lark-apps` | `apps +release-create / +git-credential-init / +member-list` |
| 授权排查 | `lark-shared` | `auth status` / `auth login` |

deps/ 为随源 Skill 打包的离线快照；在本地 Codex 中权威版本是 `C:\Users\Ludim\.codex\skills\lark-*` 下对应 Skill，命令参数还要以当前 `lark-cli <service> <command> --help` 为准。
