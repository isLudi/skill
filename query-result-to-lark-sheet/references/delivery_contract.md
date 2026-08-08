# Delivery contract

## Target topology

The configured parent identifies the Wiki space that contains `openclaw`. The default placement is the knowledge-space root, matching the existing root-level Sheet entries:

```text
openclaw knowledge space root
├── openclaw (docx Wiki node)
├── existing Sheet nodes
└── <one new Sheet node per delivery>
    ├── 原始数据 / other caller-named source sheets
    ├── native pivot child sheet(s), when requested
    ├── 口径说明 (optional caller-provided sheet)
    └── 运行元数据 (automatically added)
```

The new Sheet URL is the propagation link. The `openclaw` document URL is only used to resolve the target space and must not be passed to a grid-writing command as if it were a spreadsheet. `placement=space-root` is the default and creates a root node with no `parent_node_token`; `placement=parent` is an explicit compatibility option that creates below the `openclaw` document node.

## Sheet naming contract

The title is validated during the read-only plan stage and is copied into the receipt:

| `metadata.domain` | Required title prefix | Example |
| --- | --- | --- |
| `market_consultant` | `市场顾问部_` | `市场顾问部_20260808_渠道数据` |
| `qingcheng` | `青橙项目部_` | `青橙项目部_20260626期_抖音正价复用_过程数据` |

Use single underscores between period/date/data-description segments. Reject spaces, hyphens, slashes, empty segments, unknown domains, and mismatched department prefixes before any remote node creation.

## Plan fields

The runtime plan is JSON with:

- `schema_version`, `plan_created_at`, `plan_sha256`;
- `parent_url`, `parent_node_token`, `parent_space_id`, `parent_title`, `parent_obj_type`;
- `title`, `placement`, `inputs[]`, and `metadata`;
- `pivots[]` when native pivot output is requested; each item records its source range and official pivot properties;
- each input's `name`, absolute source `path`, `source_sha256`, `size_bytes`, `row_count`, `columns`, `dtypes`, and `schema_sha256`.

Apply must re-read the parent and recompute each source hash. It must stop on drift.

## Receipt fields

The runtime receipt must contain:

```text
delivery_id
status
fully_verified
parent_url
node_url
node_token
spreadsheet_token (if returned, never a credential)
sheet_ids
query_id
sql_sha256
result_artifact_hash
input_hashes
expected_sheets
readback_sheets
revision_before
revision_after
orphaned_node
failure_reason
```

`fully_verified=true` requires successful node creation, successful typed writes, complete readback of all expected sheets, matching row/column counts, matching normalized content hashes, and a final revision.
When `pivots[]` is non-empty, it additionally requires every requested pivot to be observed by `+pivot-list` and every returned `info.error_state` to be empty/`None`.

## Data typing

- Numeric measures stay numeric and dates stay date/datetime values.
- IDs, codes, phone numbers, and other identifiers stay text, including leading zeroes.
- Formulas require the official Lark formula translation and verification workflow.
- Grouped summaries require a native Lark pivot; a locally computed static table must not be mislabeled as a pivot.
- Native pivot creation defaults to an automatically created empty child sheet, so the pivot cannot cover the raw-data or metadata sheets. The delivery receipt records the create response and post-create `+pivot-list` evidence.

## Authorization boundary

`plan` is read-only. `apply` is a remote write and requires `--confirm-write`; it creates exactly one new Sheet node and never deletes or overwrites an existing node. A failed apply returns a failed receipt with any created node listed for manual cleanup.
