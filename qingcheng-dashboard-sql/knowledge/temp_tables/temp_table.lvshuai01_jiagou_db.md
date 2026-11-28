# temp_table.lvshuai01_jiagou_db

字段类型合并说明（2026-11-28）：类型栏采用本地已记录的平台 SQL 解析输出；历史 Excel 推断不作为当前类型结论。查询输出结构不等同完整 DDL，也不证明当前数据覆盖、唯一性或生产消费者已切换。

维护账号迁移：2026-11-28 用户确认同后缀表由 lvshuai01 接续维护；线上新表身份已核实。字段及业务含义沿用已确认结构，历史 SQL、Excel 扫描和 Query 证据不等于新表本次数据验证。当前使用规则见 [临时表维护迁移](../temp_table_maintenance.md)。

## 1. 临时表用途

青橙期次带班架构映射表。2026-11-22 核对现行 2460 线上 SQL：SEC 抖音退费潜客从本表取得 dept_2=SEC 的期次、账号集合，再关联潜客。其他已登记过程、到课分析按各自 QuerySpec 使用架构，不据本次账号迁移扩大业务范围。

## 2. 来源和刷新方式

来源以 sync-qingcheng-market-temp-tables/references/workflow_registry.json 的青橙 period_architecture 为准。登记流程从附件维护累计工作簿，经新鲜度、唯一键和变化率门禁上传既有表。有效期取决于最新成功回执，不能由旧样本推断。本次不执行上传。

## 3. 数据粒度与 Join

登记键为 qici + employee_email_name，按来源期次片段合并，每次上传仍校验唯一性。现行 2460 使用 p.qici=jg.qici 且 p.employee_email_name=jg.employee_email_name。

历史过程 SQL qingcheng_process_data_raw_20260522.sql 使用 employee_email_name + qici；历史到课 SQL qingcheng_daoke_raw_20260522.sql 使用 employee_email_prefix + qici。两个键不能默认互换。新分析使用已登记账号键；复刻旧分析时须单独核对 prefix 映射，不省略期次、不静默改变 Join 粒度。历史 jg.department is not null 的范围门槛也不能被账号迁移删除。

## 4. 字段清单

| 字段 | 类型 | 来源 |
| --- | --- | --- |
| xiaozu_z |  | 登记上传列 |
| employee_email_prefix |  | 登记上传列 |
| xiaozu |  | 登记上传列 |
| employee_email_name |  | 登记上传列 |
| department |  | 登记上传列 |
| zaizhi |  | 登记上传列 |
| qici |  | 登记上传列 |
| dept_1 |  | 登记上传列 |
| dept_2 |  | 登记上传列 |
| jingli |  | 登记上传列 |

以上是登记上传列，不额外推断数据库物理类型。

## 5. 适用看板

现行 2460；历史过程与到课消费者的使用范围见前述说明。

## 6. join key

登记使用 qici + employee_email_name，历史 prefix 键必须单独核对，不得跨期关联。

## 7. 不可复用边界

物理工作簿共享，青橙上传流程只维护 dept_1=青橙项目部 切片；2460 使用 dept_2=SEC 子集。不从市场顾问部借用语义，也不把两域相同物理表理解为相同范围。数据库物理类型、最新行数、刷新状态和每次源新鲜度仍按实际任务核实。多个员工/期次架构记录会放大 Join，必须保留重复键门禁。

## 8. 待确认事项

每次实际使用均核对当前新鲜度、数据覆盖和唯一性；不把维护人迁移当作本次数据质量验收。

## 本地登记与平台核验补充（2026-11-28）

### 1. 临时表用途

2026-11-22核对现行2460线上SQL：2460的SEC抖音退费潜客入选门槛：从本表取得dept_2=SEC的期次、账号集合，关联潜客。

### 2. 来源和刷新方式

来源身份以`sync-qingcheng-market-temp-tables/references/workflow_registry.json`内青橙`period_architecture`登记为准；业务名为青橙期次带班架构。登记上传流程从附件维护累计工作簿，再经新鲜度、唯一键及变化率门禁上传既有平台表。本次只同步知识，不执行上传。刷新依赖登记事件流程；表内覆盖多个qici，有效期依最新成功回执。

### 3. 数据粒度

登记键为`qici + employee_email_name`；按来源期次片段合并。每次上传仍须校验唯一性，不用历史样本替代最新门禁。

### 4. 字段清单

以上为登记上传列，不额外推断数据库物理类型。

### 5. 适用看板

现行2460“转化数据”及已登记转化看板。只证明本次线上SQL的使用关系，不自动扩展其他看板。

### 6. join key

`p.qici = jg.qici and p.employee_email_name = jg.employee_email_name`。其他过滤和匹配保护以当前`resources/raw_sql/data_center_qingcheng_2460.sql`为准。

### 7. 不可复用边界

本表已承接同后缀旧表的维护，仍需按当前数据验证质量，不从市场顾问部引入语义。物理工作簿共享，上传流程只维护dept_1=青橙项目部切片；当前2460读取dept_2=SEC子集。

### 8. 待确认事项

数据库物理类型、每次源新鲜度及最新行数需按需要读取，不能由本登记推断。业务用途和本次SQL使用关系已核验。

### 9. 业务关联补充

按员工与期次关联时保留完整 `qici`，并校验人员键唯一性；只按姓名或期次尾号关联可能跨期放大。不要与全员结果架构表混用。

### 平台结构与迁移核验

2026-11-28 使用平台 SQL 解析器分别读取新、旧表的 `SELECT *` 输出，字段名、类型和顺序一致。解析器返回字段均为 `string`；这是查询输出结构，不等同于完整 DDL，也不证明两表数据内容、覆盖期次、唯一性或最新上传状态相同。

字段顺序：`xiaozu_z`、`employee_email_prefix`、`xiaozu`、`employee_email_name`、`department`、`zaizhi`、`qici`、`dept_1`、`dept_2`、`jingli`。
