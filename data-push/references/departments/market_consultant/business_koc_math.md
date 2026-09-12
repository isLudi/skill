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

常规过程/转化报告仍按顺序分别生成并推送 `KOC-周帅数学`、`KOC-孟亚飞数学`，不得合并。新增进量报告是独立范围：动态纳入渠道名包含 KOC（Unicode NFKC 归一化后不区分大小写）且不包含 `自孵化` 的全部渠道，不设精确渠道名白名单；进量与异常流量占比必须使用同一批渠道，并按期次、渠道、年级精确匹配线索明细。各派生指标先按年级汇总原始分子、分母再计算，图片和文字格式复用市场 KOC 进量报告。

进量能力已在预览和一次群内测试验收后进入 `scheduled`。Windows 任务 `Codex-Lark-Business-KOC-Math-Push` 仅保留 `13:21`、`17:21` 两个触发器，并显式配置 13 点常规报告、17 点进量报告：13 点周一至周四分别推两条过程报告，周五至周日分别推两条转化报告；17 点每天推一条合并进量报告，不再运行 21 点播报。失败仍按 `:21/:23/.../:49` 重试。预览、测试发送和调度上线仍是三个独立门槛；渠道配置与 Windows 任务必须同时启用，并遵守上游证据、时点、逐渠道回执和图片清理门禁。
