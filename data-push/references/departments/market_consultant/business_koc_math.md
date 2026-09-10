# 商务 KOC 数学渠道群播报

渠道入口为 `scripts/channels/market_consultant/business_koc_math.py`，配置为 `config/departments/market_consultant/business_koc_math.json`。目标固定为群 `oc_978fde959e5aad96ec1aa03fe4c20b22`（核验名称 `【商务KOC】&【高阳团队】`），按顺序分别推送 `KOC-周帅数学`、`KOC-孟亚飞数学`。群名仅供漂移核验，不用于搜索替代 chat_id。

## 格式和提醒

两渠道完全复用 [自孵化 KOC 5 元纯课](self_incubated_koc_5.md) 的 `grade-compact` 接口：自然周周五期次、排除初二、退后线索至少 10 条才出图、过程图 9 列、转化图 6 列；年级按初一/初三/高一/高二/高三，负责人按各指标精确值降序。提醒按每个年级的经理最低值且并列全提醒，正式消息只使用已核验且属于目标群的 open_id。

两个渠道独立生成图片、文案、幂等键和回执，顺序固定为周帅后孟亚飞；某个渠道没有当期数据或账号核验失败时停止该渠道，不回退期次、不借用另一渠道数据，也不静默去掉 @。

## 本地预览与常态运行

```powershell
& 'D:\anaconda3\python.exe' 'C:\Users\Ludim\.codex\skills\data-push\scripts\channels\market_consultant\business_koc_math.py' describe
& 'D:\anaconda3\python.exe' 'C:\Users\Ludim\.codex\skills\data-push\scripts\channels\market_consultant\business_koc_math.py' preview --report-type both
```

预览只读 Base、核验群和账号、写本地 HTML/Markdown/PNG，不上传图片、不发消息。长期运行由 Windows 任务 `Codex-Lark-Business-KOC-Math-Push` 调用 `scripts/run_business_koc_math_scheduled_push.ps1`，每天 09:15、13:15、17:15、21:15 隐藏启动，并在 :20 后通过共享调度器发送。渠道配置与 Windows 任务必须同时启用；仍须遵守上游证据、时点、逐渠道回执和图片清理门禁。
