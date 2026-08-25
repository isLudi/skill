---
name: lark-miaoda-dashboard
description: |
  【妙搭看板 + 数据分发专项】两件事的完整 SOP：
  A. 做飞书妙搭（Miaoda）数据看板：飞书 Base 取数 → 本地聚合 data.json → git 推送妙搭仓库 → release 发布 → Windows 每日定时刷新。
  B. 数据分发：把 Excel 按列切割（如按顾问/部门）→ 飞书私聊逐个发给对应的人。
  C. 本地群推送：飞书 Base 视图 → 过程字段白名单 → 仿表格图片/文字数据 → 精确 @ → 指定群发送。

  以下场景必须加载此 skill：
  1. "做一个妙搭看板""把看板发布到妙搭""看板每日自动更新""接手/交接妙搭看板"
  2. "把表按 xx 切开发给对应的人""切割 Excel 私聊发送""分发表格""按人拆分下发"
  关键词：妙搭 / miaoda / 看板 / dashboard / data.json / release / 切割 / 拆分 / 分发 / 私聊发送 / 群推送 / 多维表格推送
  普通妙搭应用创建、云端开发、数据库、成员或运行时权限等不属于本 SOP 的请求仍走 lark-apps；本 skill 聚焦静态数据看板刷新和 Excel 分发。

  前置：lark-cli 已登录 user 身份；发布妙搭需 apps 域授权，私聊发送需 im:message.send_as_user。
  在本地 Codex 中优先使用本地 lark-base / lark-apps / lark-contact / lark-im / lark-shared Skill；deps/ 仅是随包快照，命令事实以本地权威 Skill 和 lark-cli --help 为准。
metadata:
  short-description: "妙搭看板搭建与飞书 Excel 安全分发"
---

# 妙搭看板搭建 + 数据分发（lark-miaoda-dashboard）

三部分：A. 从零做/接手一个妙搭看板；B. 把 Excel 切割后飞书私聊分发；C. 本地执行 Base 过程数据群推送。
模板：`templates/export_base.py`（Base 分页导出）、`templates/refresh.py`（每日刷新流水线）、`scripts/excel_split_send.py`（切割分发）、`scripts/group_push.py`（Base 视图→群消息）。全部用占位符/环境变量，不写死 app_id、Base token 或业务文件路径。

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

## C. 多维表格过程数据群推送（本地脚本）

`scripts/group_push.py` 用官方 CLI 编排本地推送：`base +record-list` 读取过程视图和同表「结果数据」视图，读取独立的「推送文字」配置视图，`contact +search-user` 对提醒姓名做唯一精确解析，Pillow 生成过程/结果两张仿参考图的宽表 PNG，最后由 `im +messages-send` 发送 Markdown post。它不依赖妙搭额度，也不需要本地服务常驻；可以手动运行，也可以由 Windows 计划任务按周期启动。

提醒计算放在独立的「IP播报_提醒计算」表：它只维护顾问/主管/渠道维度，使用公式读取「IP原始数据」的 lead_id、5min 标记、退后线索和净收款，并用 Lookup 对照「IP播报_主管」的主管汇总值。「IP原始数据」不新增任何提醒公式或计算列，适配天宫 2 全量覆盖原始表的写入方式；原始表重写后，独立表会重新计算。现有维度行新增顾问时，需要补充一行“顾问|主管|渠道”维度记录，不能把原始明细复制进提醒计算表。

群消息由「推送文字」表的 `推送标题`、`推送期次`、`推送说明`、`提醒` 组成：过程数据段附过程图片；结果数据段附 `IP播报_主管 / 结果数据` 汇总图片，并列出单效偏低的顾问姓名用于提醒。结果图仿附件的宽表版式，包含 `经理、主管、退前/退后线索、各过程率、单效(当期)、人均报科、人头转化、订单转化、净收款、退费率、单效`。提醒姓名来自 `计算_提醒顾问`，发送前必须唯一解析为飞书 open_id。

图片版式固定为：深蓝表头、白色表格、`线索留存率` 条件色、`首call/5min/双沟` 数据条、底部深蓝总计行。文字消息同步保留部门/渠道、过程指标和汇总；过程白名单不包含收款、成交、退费、单效等结果字段。参考图中的 `6h/12h/24h` 列只有在当前视图实际提供字段值时才显示，避免发出空指标列。

### C.1 先预览，不发送

PowerShell 先准备 UTF-8 和环境变量。`SOURCE_URL` 可以直接放原始 Base/Wiki URL；脚本会调用 `base +url-resolve` 取坐标。也可以直接提供 `BASE_TOKEN`、`TABLE_ID`、`VIEW_ID`。

```powershell
Set-Location 'C:\Users\Ludim\.codex\skills\lark-miaoda-dashboard'
$env:PYTHONIOENCODING='utf-8'
$env:PYTHONUTF8='1'
$PY='D:\anaconda3\python.exe'
$env:SOURCE_URL='<Base或Wiki URL>'
$env:TEXT_SOURCE_URL='<推送文字表的 Base/Wiki URL>'
$env:CHAT_ID='<oc_xxx>'
$env:CHAT_NAME='<指定群的精确名称>'

& $PY '.\scripts\group_push.py' preview --cli-dry-run
```

预览会读取过程视图、同表「结果数据」视图和文字配置视图，生成本地 `runtime/ip-broadcast-push/IP过程数据_<期次>.png` 与 `IP结果数据_<期次>.png`，打印消息 Markdown 和幂等键，并用 `im +messages-send --dry-run` 校验请求形状；不会上传图片，也不会发送群消息。结果视图默认使用 `--result-view-id 结果数据`，也可以传稳定的结果视图 ID。多期视图必须加 `--period 20260821期`。不需要 @ 时使用 `--no-mentions`；需要 @ 时默认只按「提醒」中的顾问姓名精确查通讯录，重名、查无此人或权限不足都不会猜测。

原始表每次被天宫 2 全量覆盖前后，可先运行维度同步预览；它只检查独立提醒计算表是否缺少新顾问维度，不会改动或删除「IP原始数据」：

```powershell
& $PY '.\scripts\group_push.py' sync-helper `
  --source-url $env:SOURCE_URL `
  --helper-table-id '<IP播报_提醒计算表 ID>' `
  --helper-raw-table-id '<IP原始数据表 ID>'
```

预览确认缺失维度无误后，才加 `--confirm-helper-sync` 执行追加；该命令只调用 `base +record-batch-create`，不更新、不删除已有维度或原始数据。当前提醒计算表的公式和查找引用列保持在独立表中，原始表覆盖不会清除它们。

### C.2 显式确认后发送

确认预览中的期次、行数、群名称、图片和 @ 结果后，才执行：

```powershell
& $PY '.\scripts\group_push.py' send --confirm-send --strict-mentions
```

真实发送还要求当前 `CHAT_ID` 与群名称已核验、发送身份（`SEND_AS=user` 或 `SEND_AS=bot`）权限可用，并且会把实际返回的 `message_id` 写入 `runtime/ip-broadcast-push/send_ledger.jsonl`。相同内容的幂等键在台账中已标记为 sent 时会跳过，避免重复播报。带图片时，上传步骤还需要该发送身份具备 `im:resource`；没有这个权限时脚本会在图片上传前后明确阻断，不能把文字接口成功误判为图片消息已送达。只有真实发送返回 `message_id` 后，脚本才会立即分别删除过程 PNG 和结果 PNG；如果上传成功但最终消息发送失败，会保留两张 PNG 便于重试。两张 PNG 的删除状态会同时写入输出和发送台账。预览、`--dry-run` 和本地图片生成不会删除图片，以便检查效果。

如果通讯录不能按姓名唯一解析，可以先准备本地映射（只保存必要的 open_id，不要把 token 或 access token 写入文件）：

```json
{
  "主管姓名": "ou_xxx",
  "顾问姓名": "ou_yyy"
}
```

然后传 `--mention-map .\mention-map.json`。脚本会在群消息中生成 `<at user_id="ou_xxx">姓名</at>`；没有唯一映射时，`--strict-mentions` 会在发送前阻断。

### C.3 定时执行边界

Windows 计划任务只应调用 `D:\anaconda3\python.exe` 和该脚本，环境变量通过任务的启动器或受控配置注入。建议定时任务默认执行 `preview --cli-dry-run`，由人工确认后再执行一次 `send --confirm-send`；若确需无人值守，必须提前固定 `CHAT_ID`、`SEND_AS`、`PERIOD`、字段白名单和幂等台账路径，并单独验证 bot 已在群内且拥有发送/图片资源权限。

离线测试：

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
