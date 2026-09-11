# 集团私域与APP主管维度播报

## 固定范围

- 渠道入口：`market_consultant/supervisor_private_app_sync`。
- 渠道顺序：`集团私域`、`app`。
- 目标群仅按不可变 ID `oc_b43002a3c802ee5ae2d5b2f10d7d50a2` 绑定；`💪【0911期】APP+私域+图书直播🔥信息同步` 只是核验用显示名，群改名不改变投递目标。
- 发送身份固定为群内机器人“管家” `ou_f3907e865135732c15a1dfce27828411`。
- Windows 任务：`Codex-Lark-Supervisor-Private-App-Push`。每天 09:23、13:23、17:23、21:23 错峰启动并立即检查，失败后按 `:23/:25/.../:49` 重试；周一至周四只推过程数据，周五至周日推过程与转化数据。
- 该任务、状态目录与 `Codex-Lark-Supervisor-KOC-Douyin-Push` 完全独立，不允许互相改写台账或启停状态。

## 复用的主管报表契约

本渠道直接复用 `supervisor_report.py`，与 KOC+抖音主管播报只有渠道集合、群 ID、状态目录和任务名不同：

- 仅保留高一、高二、高三；图片按 `年级 × 负责人 × 主管` 聚合，每行一个顾问。
- 文字提醒按 `渠道 × 年级 × 主管` 聚合并严格 @主管。主管必须唯一解析到已激活账号且属于目标群。
- 主管聚合后 `退后线索 < 10` 的图片行和提醒候选均隐藏；某渠道没有合格行时返回 `skipped_no_eligible_rows`，不生成或发送空图片。
- 过程表在每个年级内先按未四舍五入的 `5min标记 / 退后线索` 严格降序；同率时按未四舍五入的线索留存率降序，再按负责人名称稳定排序。线索留存率固定色阶为 `<72%` 红、`72%–<75%` 橙、`75%–<80%` 黄、`80%–<88%` 黄绿、`≥88%` 绿。
- 标题为 `🔥 **【实际期次】渠道名渠道过程数据播报**` 和 `🔥 **【实际期次】渠道名渠道转化数据播报**`。

## 本地入口与调度

```powershell
& 'D:\anaconda3\python.exe' 'C:\Users\Ludim\.codex\skills\data-push\scripts\channels\market_consultant\supervisor_private_app_sync.py' describe
& 'D:\anaconda3\python.exe' 'C:\Users\Ludim\.codex\skills\data-push\scripts\channels\market_consultant\supervisor_private_app_sync.py' preview --report-type both
& 'C:\Users\Ludim\.codex\skills\data-push\scripts\register_supervisor_private_app_sync_scheduled_push.ps1' -ConfirmEnable
```

真实发送前按 `operations.md` 使用同一个稳定 request ID 先执行 `preflight-now`，核验后再执行一次 `send-now --confirm-send`。预览、单次发送与启用调度是三个独立阶段。
