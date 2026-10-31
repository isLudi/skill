---
name: stss
description: Reduce defensive padding in reader-facing prose, and polish Chinese academic and professional writing while preserving meaning and evidence. Use for 中文润色、论文与学位论文、摘要、经济学/管理学/社科研究报告、数据分析与线上教育报告、述职与工作日报, or for defensive wording in proposals, articles and captions. Supports rewrite, polish, draft and audit; academic Chinese-English translation only when requested. Does not determine AI authorship or execute research or code changes.
license: MIT
---

# Stop That Shit Slop

别再废话。

Make the point without writing for an imaginary critic. Preserve limitations that change what the reader understands or decides. 中文润色以准确、连贯、自然和适合读者为目标，保留作者的研究判断与工作事实。

## Stay in scope

Reduce defensive wording in reader-facing prose, including captions and introductions. For Chinese polishing requests, also improve syntax, terminology, paragraph flow and the presentation of an existing argument. Do not classify text as AI-written or promise detector scores, plagiarism-check results or publication acceptance. Treat requests about “AI 味” as requests to fix observable writing problems.

Judge sentences by their reader use, including sentences introduced during drafting. A request to describe a project's evolution calls for that history; it does not by itself call for an account of how the article's sources were checked.

Use the material already supplied. Language editing does not authorize new analysis, database queries, research-method changes, remote document edits or publication. Follow an explicit instruction to edit a particular file or document; otherwise return the text in the conversation. Use the matching document skill only when file handling is part of the request.

## Select the mode

- `rewrite`: Remove defensive padding. This remains the default for supplied text without a polishing or drafting request.
- `polish`: Improve Chinese language and argument presentation. Infer this from “润色”“学术化”“优化报告表述”; default to local edits, preserving structure unless reorganization is needed or requested.
- `draft`: Turn supplied material into the requested passage, abstract or report. Do not invent missing research or work achievements.
- `audit`: Identify actionable expression problems and propose the smallest useful fix. Do not rewrite the full text.

Follow an explicit mode. Infer the mode from the request only when none is given.

Select references by the actual text, not by keywords alone:

| Current task | Read when applicable |
| --- | --- |
| Chinese language polishing or drafting | [中文表达](references/chinese-style.md) |
| Papers, theses, academic abstracts, economics/management/social-science writing, requested academic translation | [学术写作](references/academic-writing.md), plus 中文表达 for Chinese output |
| Data analysis, management, online education reports, performance reviews, work summaries and daily reports | [报告写作](references/report-writing.md), plus 中文表达 for Chinese output |
| Ambiguous boundary between defensive padding and a useful limitation | [Original examples](references/examples.md) |
| Upstream comparison, attribution or future maintenance | [来源与维护](references/sources.md); not needed for ordinary writing |

A scholarly education study uses the academic reference; an operational education analysis uses the report reference. Load both only when the task actually mixes them. Do not load every reference for a short edit.

## Record the claims

Before editing, build a private Claim Ledger from the supplied material:

- facts and numbers;
- named actors and sources;
- evidence strength;
- stated uncertainty and scope;
- what the reader needs to understand or do.

Also protect specialized terms, variable definitions, denominators, units, dates, citation bindings, and whether an activity is planned, underway or complete. Do not print the ledger unless the user asks for it. Do not invent facts, sources, numbers, certainty or causality. A summary may omit secondary details to meet the requested length; retain the main finding and its material conditions.

Keeping facts accurate does not require printing every editorial note. Keep verification logs and source-checking process in working notes unless the reader needs them. Preserve useful attribution, actual methods, and conditions that affect a claim.

Distinguish a language repair from a substantive correction. If supplied evidence clearly contradicts the wording, calibrate the wording to that evidence. If an edit would resolve a substantive ambiguity or suspected contradiction but the needed evidence is unavailable or conflicting, mark only the affected claim `AUTHOR_CHECK` in a brief separate note; do not silently change its direction or strength. Ordinary polishing does not require independently verifying every supplied fact. Continue unaffected editing. Ask only when the missing fact prevents a faithful result.

## Test each defensive sentence

Apply the Sentence Consumer Test:

1. Who will use this sentence?
2. What understanding or decision does it change for this reader?
3. What becomes false or misleading if it is removed?

Choose one action:

- `DROP`: It only narrates diligence, anticipates criticism, apologizes, or says what the document does not attempt.
- `CALIBRATE`: It contains real uncertainty but uses stacked hedges. Keep one precise limitation.
- `RELOCATE`: The reader needs it beside a particular claim, or only the editor needs it in working notes. Choose the destination by its consumer; moving an unnecessary disclaimer to a footnote does not make it useful.
- `KEEP`: It changes the meaning, evidence strength, attribution, or a legal, safety, financial, methodological, contractual, or scope decision.

Do not decide from a keyword alone. The same phrase can be waste in one context and necessary in another.

## Rewrite

1. Lead with the requested subject, claim, decision, or proposal.
2. State scope positively: say what the work covers.
3. Replace stacked hedges with one evidence-matched qualifier.
4. Remove internal process narration unless the process is requested or material.
5. Put a necessary limitation beside the claim it limits.
6. Check the complete artifact, including captions and assistant-added prefaces, against the Claim Ledger and Sentence Consumer Test. Do not reintroduce dropped defenses in the delivery note.

Return only the requested artifact unless the user asks for commentary. If the text is already direct and faithful, return it unchanged.

## Polish or draft

1. Infer the reader, genre, section, editing depth and output format from the request and material. Use the source's register when nothing else is specified.
2. Identify the central question and each paragraph's purpose. Repair wording and the presentation of relationships already supported by the material; reorganize only within the authorized depth.
3. Apply the relevant Chinese, academic or report guidance. Remove empty wording without deleting an independent argument, condition, method or result merely to shorten the text.
4. Check the complete output against the Claim Ledger and Sentence Consumer Test, including titles, summaries, captions and assistant-added text.

Default to the finished text. Add a comparison, rationale or audit table only when requested; material `AUTHOR_CHECK` notes remain separate from the finished passage. Honor requested wrappers such as `<修改后内容>` or `<摘要>` exactly, but do not add tags by default. Do not append a change diary, self-praise or an offer to continue.

## Audit

Report only actionable findings. For each finding, give:

- the span or sentence;
- `DROP`, `CALIBRATE`, `RELOCATE`, or `KEEP`;
- the reader's interpretation or decision affected;
- the smallest replacement when one is needed.

Use `NO_DECISION_CONSUMER` when a sentence serves neither reader understanding nor a decision. For Chinese polishing, distinguish confirmed language problems, optional improvements, format preferences and `AUTHOR_CHECK` facts. Keep a useful sentence even if it contains a common transition, parallel construction or technical term. If there are no actionable findings, say so and stop.

## Check the claim diff

Before returning the result, verify:

- no supplied fact, number, source, or actor disappeared without reason;
- no unsupported fact, number, source, or actor appeared;
- uncertainty did not become certainty;
- correlation did not become causation;
- a requested or meaning-changing limitation remains visible;
- academic terms, statistical meanings, citations and figure/table references remain aligned;
- scope, metric definitions, ownership and completion status remain accurate;
- the final register and format fit the user's request.

Run one claim-preserving pass. Do not add a score, a probability that text is AI-written, a change diary, or repeated self-review.
