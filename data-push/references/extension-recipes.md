# 扩展配方与交付检查

只实现用户当前要求的渠道/格式，不因为已有公共代码就推导其他部门口径。可执行接口见 [interfaces.md](interfaces.md)。

## 新增同部门、同口径渠道

1. 读取所属部门Skill和现有渠道规范，确认字段、期次、范围、指标及提醒对象兼容。
2. 新建 `config/departments/<domain>/<channel_id>.json`：精确渠道、源、目标ID、身份、独占状态目录；schedule.enabled初始false。
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
6. 生成本地预览并核对，另行取得明确发送/启用授权。不要批量复制旧2400行脚本。

## 新增青橙或不同口径渠道

先读 [青橙接入边界](departments/qingcheng.md)。创建青橙adapter及自己的数据验证、聚合、渲染、文案、日历和上游验收。只共享中性飞书ports、配置/目标协调、文件布局和锁。

在 `registry.adapter_for` 登记 `("qingcheng", "<reviewed-adapter>")`；同时加“拒绝市场adapter”的测试。没有已确认口径时，仅交付未启用配置/接口设计，不发送或伪造默认规则。

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
| scheduler/outlet | 暂停、时点、旧数据/上游失败、不确定响应、回执先落盘再清理 |
| 路由/重命名 | Skill/AGENTS链接、入口help、配置读回、任务动作路径与暂停状态 |

推荐运行 `D:\anaconda3\python.exe -m pytest tests -q`，测试框架拦截未mock的外部进程。`scripts/validate_layout.py` 检查目录、导入方向、文档链接和渠道入口。两者均不启动生产任务。

保留默认配置、指标和文案的回归证据；代码变更通过测试不等于已经送达，只有真实message_id及独立读回才是交付证据。
