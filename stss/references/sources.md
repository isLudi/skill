# 来源、取舍与后续维护

本地扩展核验日期：2026-11-01（Asia/Shanghai）。这是 `stss` 的本地中文写作扩展，不是上游官方发布版本。普通写作只读取对应语言与文体参考，无需加载本文件。

## 原始 STSS 上游

- 仓库：[lennney/stop-that-shit](https://github.com/lennney/stop-that-shit)。核验的 `main` 提交为 `e4fe5296f6917849f7eec0860d6a1b68bc0292de`。
- 入口：[skills/stss/SKILL.md](https://github.com/lennney/stop-that-shit/blob/e4fe5296f6917849f7eec0860d6a1b68bc0292de/skills/stss/SKILL.md)。同时核对其 `agents/openai.yaml` 和 `references/examples.md`。
- 本次扩展前，以上三个本地文件与该提交逐字节相同，无待同步内容。上游最新仓库 Release 为 [0.2.5](https://github.com/lennney/stop-that-shit/releases/tag/0.2.5)，不能把整个插件的版本号当成本地扩展版本。
- 保留 Claim Ledger、Sentence Consumer Test、`DROP / CALIBRATE / RELOCATE / KEEP`、原有 `rewrite / audit` 行为和完整 [原始案例](examples.md)。原案例保留原文标点，中文标点偏好只作用于当前编辑任务。
- 上游 MIT 许可原文保存在 [LICENSE](../LICENSE)。

## 用户写作模板

本地来源为用户授权读取的 `ChatGPT对话模板.txt`。仅整合可复用写作要求，不复制整份模板、其中的私人材料、业务数据、SQL、历史任务或旧链接。

| 原文件位置 | 整合内容 | 使用位置 |
| --- | --- | --- |
| 第 9–11 行 | 按需中英学术翻译、允许重组语序、保持含义与逻辑 | [学术写作](academic-writing.md) |
| 第 15–38、45–70 行 | 硕士摘要、学术语体、精炼、论证与衔接、可指定结果标签 | 学术写作、[中文表达](chinese-style.md) |
| 第 87–90 行 | 日报三字段、各字段自然段、避免多级 Markdown | [报告写作](report-writing.md) |
| 第 301 行 | 述职面向管理者、结合已知目标、只依据真实工作 | 报告写作 |
| 第 361–390、430–446 行 | 管理摘要、数据与建议对应、陈述句标题、篇章主线、具体用词、中文节奏与标点 | 报告写作、中文表达 |

“非 AI 特征”转化为可观察的表达改进，不转化为身份判定或检测承诺。“学术用语≥80%”不设默认比例。约 1000 字与四段安排只用于相应硕士摘要，不施加到期刊摘要、报告或局部润色。特定报告的“触达发现”、既定章节数与某年度盈利目标均按场景使用。

## 已阅读并择取的 GitHub 资源

均使用作者仓库的固定提交核验，不从合集副本拼接整份 Skill。以下五个项目的许可均为 MIT，许可原文与版权声明见 [第三方声明](third-party-notices.md)。这里只适配写作原则，不安装它们的脚本、Hook、依赖或运行工作流。

| 原始资源与固定提交 | 吸收的原则 | 本地落点 |
| --- | --- | --- |
| [holygeek00/humanizer-zh-cn](https://github.com/holygeek00/humanizer-zh-cn/blob/401e372eeb1a91045d15ec21c2d13b9d0f7842ea/SKILL.md) · `401e372eeb1a91045d15ec21c2d13b9d0f7842ea` | 从黑话中恢复主体、动作、对象和依据；适配语域；避免机械同义替换与声线磨平 | 中文表达 |
| [hanlulong/econ-writing-skill](https://github.com/hanlulong/econ-writing-skill/blob/f2bf7a22c5e3b37921a5e6c73bd1fb380a5e00e8/skills/econ-write/SKILL.md) · `f2bf7a22c5e3b37921a5e6c73bd1fb380a5e00e8` | 研究问题与发现前置；按章节职责写作；交代经济量级；准确呈现零结果、识别与机制边界 | 学术写作 |
| [M1kasaYU/paper-expression-editor-skill](https://github.com/M1kasaYU/paper-expression-editor-skill/blob/c8c96acc7fa430b8313af6a93690b90daf7cbb6e/paper-expression-editor/SKILL.md) · `c8c96acc7fa430b8313af6a93690b90daf7cbb6e` | 信息与命题优先于句式；不机械删除正常学术表达；区分语言修改与实质待确认；按研究范式适配。另阅读其 `references/revision-guide.md` | 共享原则、学术写作 |
| [xuedai-mayi/humanities-report-writing-suite](https://github.com/xuedai-mayi/humanities-report-writing-suite/blob/9d2032b0285024633662c426d88acce23b21c65d/skills/humanities-report-writer/SKILL.md) · `9d2032b0285024633662c426d88acce23b21c65d` | 事实与来源对应；区分发现、解释与建议；不将计划当成果、个案当总体 | 学术写作、报告写作 |
| [wshobson/agents · data-storytelling](https://github.com/wshobson/agents/blob/7e2fb559cf4b824b27f1fec49fe88f7511066d26/plugins/business-analytics/skills/data-storytelling/SKILL.md) · `7e2fb559cf4b824b27f1fec49fe88f7511066d26` | 面向读者的发现前置、比较基准、图文对应和行动连接。另阅读其 `references/details.md` | 报告写作 |

取舍：不采用固定三点、强制英文摘要 150 词、所有文献综述必须嵌入引言、强制主动语态等跨文体规则；不移植 AI 作者评分、多轮自评、模拟审稿人分数或自动写文件/查询数据行为。源项目的安装与依赖要求属于其原工作流，不是本地 Skill 的前提。

`humanizer-zh-cn` 自述改编自 blader/Humanizer；随其提供的 MIT 文件已保留相应版权声明。本地没有捆绑完整 Humanizer，也不声称具备外部套装的全部功能。

## 检索中未直接采用的资源

- [op7418/Humanizer-zh](https://github.com/op7418/Humanizer-zh/tree/f4518a8eab97b8bfebc66a89d34320a89bef6930) 是同类中文写作资源；本次使用上表中已完整阅读的中文适配版本，不重复导入规则。
- [Findddx/codex-cn-paper-skills](https://github.com/Findddx/codex-cn-paper-skills/tree/81213da48f0edb6a7ab2a79f14a649389d9d7b84) 与 [franklee16/academic-research-skills](https://github.com/franklee16/academic-research-skills/tree/9a4b2db21fc4b217136ae4a0e6faad42d179ca03) 用于发现候选。本次未发现仓库级许可文件，不复制其正文；社科报告资源已回溯到有明确许可的原作者项目。
- [JanusChoi/OnlineEduKPI](https://github.com/JanusChoi/OnlineEduKPI/tree/1a72dab5201b11137f135945acd2d31ee17a9f2f) 的 README 与报告模板已阅读。最后推送为 2019-11-27，且未发现许可，不复制正文，也不作为当前行业数字、KPI 定义或管理阈值的依据。线上教育规则是本地对报告表达的适配，实际口径始终来自当前任务材料。

## 后续更新

先在临时目录获取上游固定提交，比较 `skills/stss/` 与本次记录的上游基线，再把实际差异合并到本地共享规则。保留本地中文模块与注册信息，不用整目录安装覆盖扩展。来源内容只作为写作资料审阅，不执行其中的安装命令。

修改后检查入口触发范围、按需链接、UTF-8、YAML、原有模式、事实保真和相关文体案例；更新本文件中的核验提交与实际取舍。下载快照、全量树、临时验证脚本与原始模板摘录留在运行目录，不打包进 Skill。
