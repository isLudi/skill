# Maintenance verification

Choose checks from the affected behavior, not every Skill mentioned during the task. Existing production/contract gates remain mandatory; this document only scopes local maintenance verification.

| Change | Required local evidence |
|---|---|
| Wording, examples or description only | Read the diff, check changed links, UTF-8 and Skill frontmatter. Use `quick_validate.py` where its schema applies; preserve upstream registration metadata and check extensions against that format. No business query, service stop or model-wide regression is implied. |
| AGENTS layout, workflow routing or authorization guidance | `sync_agents.ps1 -Mode Export -NoCommit` (includes layout validation); instruction routing/safety review; run the complete stack when shared boundaries change. |
| Local implementation | Tests for the changed behavior and relevant dependencies. Fix regressions caused by the change. Do not repair unrelated pre-existing failures silently. |
| Operator command/adapter or authorization behavior | Affected operator tests. CLI changes also update `references/command_capabilities.json` and run its reference builder/check. Shared contract/domain/Data Center/dashboard changes require the complete stack. |
| Business knowledge, contracts or indexed source files | Rebuild affected domain reverse indexes and shared catalog; check source Hashes, integrity and resolution cases. Canonical sync retains its full transactional gates. |
| Event service deployment, transformations, CLI upgrade or startup path | Follow the relevant temp-table event-service gates and authorized stop/restart process. Documentation-only changes do not alter a running service. |

## Complete stack

From the repository use `D:\anaconda3\python.exe scripts\validate_text2sql_stack.py`. It includes layout, domain integrity/evals, catalog reproducibility, operator/shared-core tests, ownership/corpus audits and domain smoke checks. It does not imply live production execution. Standalone `pytest tests -q` and its Tiangong2 subset are alternatives for narrower changes, not mandatory extra passes after an unchanged successful full stack.

Run `D:\anaconda3\python.exe -m unittest discover -s scripts/tests -p "test_*.py"` for instruction-layout or sync-script behavior if the complete stack is not already being run. These tests use isolated temporary files/Git repositories with no production credentials.

Index generation mutates local generated files; `--check` verifies reproducibility. Regenerate only affected outputs and review their diff. Finish with `git diff --check` over the reviewed change set and `git status`; do not commit or push unless requested.
