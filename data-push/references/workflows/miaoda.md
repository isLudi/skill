# 妙搭静态看板

## 1 架构认知（先理解再动手）

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

## 2 搭建步骤

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

## 3 每日自动刷新（Windows 计划任务）

- 封装单脚本 `templates/refresh.py`：导出→构建→闸门校验→commit→push→release→轮询，失败即停；用 `MIAODA_APP_ID` 环境变量传入 app_id，不写死。正式发布必须显式传 `--confirm-publish`，仅推送调试用 `--no-publish`。
- 本地 Codex 的 Windows 计划任务优先直接调用 `D:\anaconda3\python.exe <项目>\refresh.py --confirm-publish`，避免 PowerShell、cmd shim 和解释器漂移；如必须使用 bat，保持 GBK + CRLF 并只把它作为薄启动器。
- 多个任务共用同一 git 仓库时**错开时间**（实例：8:00 / 8:20 / 8:40）
- 任务属性是"仅用户登录时运行"：开机+登录即跑，锁屏没事，关机当天不刷
- 发布前数据闸门不可省：`exported_at` 必须是当日、关键数组非空（2026-08-19 曾出现约课字段全 0 差点发空数据）

## 4 接手别人看板的检查清单

1. 确认真 app_id（iframe src）和真仓库（`lark-cli apps +git-credential-init --app-id X` 会返回 repository_url）
2. Base / 应用 / 自建应用三类权限转到自己名下
3. 脚本里的硬编码路径改相对路径；子进程强制 `encoding="utf-8"`（Windows GBK 解码会炸）
4. 运行前以 `lark-cli base +record-list --help` 检查 `--output/--overwrite`；本机当前已验证 1.0.87 提供这些参数，若环境不一致先按 `lark-shared` 处理版本/授权，不在脚本中自动升级
5. **确认原负责人的定时任务已关停**（否则两边互顶 git，push rejected 后 force 互相覆盖）
6. 手动全链路跑一次：导出→推送→release finished→浏览器核对页面快照日期

---



模板仍位于 `templates/`，因为刷新脚本会被复制到独立应用仓库。它不加载任何部门播报配置；不要让看板发布自动启用群播报。
