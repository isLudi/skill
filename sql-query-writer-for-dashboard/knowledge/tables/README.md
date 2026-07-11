# tables 知识库

每张表一个 Markdown 文件，文件名格式为：

```text
库名.表名.md
```

如果库名无法确认，使用 `unknown.表名.md`，并在文件中标记“库名前缀待确认”。生成生产 SQL 前必须确认库名。

物理表字段、类型、分区和 DDL 以 `usql-web-query-operator sync-datamap-fields` 获取的天工数据地图结果为准；业务含义、范围、Join 和指标口径仍以本 Skill 的业务文档及 confirmed contract 为准。数据地图不可用或字段身份不唯一时保留“待人工确认”，不要回退到 PDF、截图或手工 OCR。
