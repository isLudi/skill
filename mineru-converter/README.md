# mineru-converter

基于 [MinerU](https://mineru.net) 的 Codex 文档转换技能。

## 功能

将 PDF、图片、Office 文档转换为 Markdown、Word、HTML、LaTeX 或纯文本。支持扫描件 OCR，覆盖 80+ 语言。

## 安装

```bash
npx skills add tanis90/pdf-converter-mineru
```

## 使用方式

在 Codex 中自然对话即可，无需记忆命令：

- "帮我把这个PDF转成markdown"
- "这篇论文讲了什么？"
- "提取PDF里的表格"
- "把 report.pdf 转成 Word"

Codex 会自动调用 `mineru-open-api` 提取文档内容并完成你的需求。

## 两种模式

| 模式 | 适用场景 | 限制 |
|---|---|---|
| `flash-extract` | 快速阅读，无需认证 | 10 MB / 20 页 |
| `extract` | 高精度提取，保留图片/表格/公式，批量处理 | 200 MB / 600 页 |

默认使用 `flash-extract`。API Token 已预配置，可直接使用 `extract` 模式。

## 输出格式

`md`、`docx`、`html`、`latex`、`json` — 通过 `-f md,docx` 指定。

## 认证信息

API Token 有效期至 **2026-09-09**，过期后需重新配置。

## 驱动引擎

[MinerU Open API](https://mineru.net/ecosystem?tab=cli) · [OpenDataLab](https://github.com/opendatalab/MinerU)（上海人工智能实验室）
