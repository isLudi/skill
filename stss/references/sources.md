# 来源、取舍与后续维护

本地定制版核验日期：2026-11-01（Asia/Shanghai）。本文件记录来源与维护信息，日常写作按任务读取语言和文体参考。

本地论文与报告的抽象方法见 [本地语料来源与取舍](local-corpus-sources.md)。源文件路径、文件名、段落定位与原文均保留在本地，不同步到此仓库。

## 原始 STSS 上游

- 仓库：[lennney/stop-that-shit](https://github.com/lennney/stop-that-shit)。核验的 `main` 提交为 `e4fe5296f6917849f7eec0860d6a1b68bc0292de`。
- 入口：[skills/stss/SKILL.md](https://github.com/lennney/stop-that-shit/blob/e4fe5296f6917849f7eec0860d6a1b68bc0292de/skills/stss/SKILL.md)。同时核对其 `agents/openai.yaml` 和 `references/examples.md`。
- 本次扩展前，以上三个本地文件与该提交逐字节相同。核验时仓库 Release 为 [0.2.5](https://github.com/lennney/stop-that-shit/releases/tag/0.2.5)；该版本属于上游插件。本地沿用 `stss` 名称维护中文扩展。
- 保留 Claim Ledger、Sentence Consumer Test、`DROP / CALIBRATE / RELOCATE / KEEP`、原有 `rewrite / audit` 行为和完整 [原始案例](examples.md)。原案例保留原文标点，中文标点偏好只作用于当前编辑任务。
- 上游 MIT 许可原文保存在 [LICENSE](../LICENSE)。

## 用户写作模板

本地来源为用户授权读取的写作模板，仅整合其中可复用的表达和结构要求。

| 内容类别 | 整合内容 | 使用位置 |
| --- | --- | --- |
| 中文表达 | 准确用词、连贯句法、信息推进与格式要求 | 入口、中文表达 |
| 学术写作 | 研究结构、摘要、引用与文献综述 | 学术写作 |
| 专业报告 | 读者需求、数据与建议的联系、标题和篇章结构 | 报告写作、中文表达 |

模板中的自然表达要求落实为准确用词、连贯句法和篇章推进。学术性以概念与论证表达体现。硕士摘要篇幅、触达主题和管理目标分别在相应场景中使用。

## 已阅读并择取的 GitHub 资源

以下资源均按作者仓库的固定提交核验，许可均为 MIT，许可原文与版权声明见 [第三方声明](third-party-notices.md)。本地按写作功能适配相应原则。

| 原始资源与固定提交 | 吸收的原则 | 本地落点 |
| --- | --- | --- |
| [holygeek00/humanizer-zh-cn](https://github.com/holygeek00/humanizer-zh-cn/blob/401e372eeb1a91045d15ec21c2d13b9d0f7842ea/SKILL.md) · `401e372eeb1a91045d15ec21c2d13b9d0f7842ea` | 从黑话中恢复主体、动作、对象和依据；适配语域；避免机械同义替换与声线磨平 | 中文表达 |
| [hanlulong/econ-writing-skill](https://github.com/hanlulong/econ-writing-skill/blob/f2bf7a22c5e3b37921a5e6c73bd1fb380a5e00e8/skills/econ-write/SKILL.md) · `f2bf7a22c5e3b37921a5e6c73bd1fb380a5e00e8` | 研究问题与发现前置；按章节职责写作；交代经济量级；准确呈现零结果、识别与机制边界 | 学术写作 |
| [M1kasaYU/paper-expression-editor-skill](https://github.com/M1kasaYU/paper-expression-editor-skill/blob/c8c96acc7fa430b8313af6a93690b90daf7cbb6e/paper-expression-editor/SKILL.md) · `c8c96acc7fa430b8313af6a93690b90daf7cbb6e` | 信息与命题优先于句式；按实际功能判断学术表达；区分语言与实质修改；按研究范式适配。另阅读其 `references/revision-guide.md` | 共享原则、学术写作 |
| [xuedai-mayi/humanities-report-writing-suite](https://github.com/xuedai-mayi/humanities-report-writing-suite/blob/9d2032b0285024633662c426d88acce23b21c65d/skills/humanities-report-writer/SKILL.md) · `9d2032b0285024633662c426d88acce23b21c65d` | 事实与来源对应；区分发现、解释与建议；明确工作阶段和样本范围 | 学术写作、报告写作 |
| [wshobson/agents · data-storytelling](https://github.com/wshobson/agents/blob/7e2fb559cf4b824b27f1fec49fe88f7511066d26/plugins/business-analytics/skills/data-storytelling/SKILL.md) · `7e2fb559cf4b824b27f1fec49fe88f7511066d26` | 面向读者的发现前置、比较基准、图文对应和行动连接。另阅读其 `references/details.md` | 报告写作 |

适配后的结构、篇幅、语态与表达方式由当前文体和任务决定。全文沿用一个共同编辑约定，各模块集中说明措辞、论证、结构和成稿方法。

`humanizer-zh-cn` 自述改编自 blader/Humanizer；随其提供的 MIT 文件已保留相应版权声明。

## 后续更新

在临时目录获取上游固定提交，比较 `skills/stss/` 与记录基线，再合并上游变化、本地中文模块和注册信息。

修改后核对入口触发范围、按需链接、UTF-8、YAML、编辑约定和相关文体案例，更新核验提交与适配说明。下载快照、临时验证脚本和原始摘录保留在本地运行目录。
