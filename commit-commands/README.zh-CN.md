# Commit Commands Skill 中文使用说明

## 这个 skill 是做什么的

`commit-commands` skill 用于简化常见 Git 工作流，包括创建提交、提交并推送、创建 Pull Request，以及清理远端已删除但本地仍残留的分支。它适合在你希望 Codex 代为检查改动、整理暂存区、生成符合仓库风格的 commit message、推送分支或做基础分支维护时使用。

这个 skill 来源于 Anthropic 的 `claude-plugins-official/plugins/commit-commands`。本地已保留原始 Claude plugin 结构，包括 `.claude-plugin/`、`commands/`、`README.md` 和 `LICENSE`，并额外提供 `SKILL.md` 供 Codex 识别。这个文件是中文上手说明，实际执行规则仍以同目录下的 `SKILL.md`、`commands/*.md`、`README.md` 和 `LICENSE` 为准。

## 适合使用的场景

- 检查当前 Git 工作区并创建一次提交。
- 根据 staged 和 unstaged diff 自动拟定 commit message。
- 按仓库近期提交风格生成 Conventional Commit 风格或本仓库惯用风格的提交。
- 提交后推送到已配置好的远程分支。
- 在 GitHub 仓库中提交、推送并创建 Pull Request。
- 清理被远端删除后仍留在本地的 `[gone]` 分支。
- 在提交前检查是否误包含 `.env`、token、cookie、日志、缓存、数据库或其他敏感文件。

## 不适合使用的场景

- 需要强制推送、改写历史、rebase、reset、回滚或删除分支，但用户没有明确授权。
- 工作区包含多组互不相关改动，且用户没有说明要提交哪些范围。
- 远程仓库、账号认证或 GitHub CLI 状态不清楚，却要直接创建 PR。
- 用户只想查看状态或 diff，不希望创建提交。
- 仓库中存在疑似敏感文件，尚未确认是否排除。

## 基本使用方法

在 Codex 中直接描述 Git 目标即可。请求中包含“提交一下”“git一下”“commit 当前改动”“提交并推送”“创建 PR”“清理 gone 分支”等上下文时，Codex 可以根据 skill 描述决定是否加载 `commit-commands`。

推荐提供这些信息：

- 要提交的文件、目录或功能范围。
- 是否需要包含当前所有改动，还是只提交指定部分。
- 期望的 commit message 或提交风格。
- 是否需要 push，以及目标远程和分支。
- 是否需要创建 Pull Request。
- 是否允许创建新分支。
- 是否有必须排除的本地文件、敏感文件或临时文件。

## 常用 Prompt 模板

### 创建一次提交

```text
请使用 commit-commands skill 检查当前仓库改动并创建一次提交。
提交前请先运行 git status 和 git diff，排除敏感文件、缓存文件和无关改动。
提交后输出 commit hash 和当前 git status。
```

### 只提交指定文件

```text
请使用 commit-commands skill 只提交以下文件：
- <文件路径 1>
- <文件路径 2>

不要暂存或提交其他文件。提交信息请根据 diff 自动生成，并保持仓库现有提交风格。
```

### 提交并推送

```text
请使用 commit-commands skill 将当前仓库最新改动提交并推送到 origin 的当前分支。
提交前检查敏感文件；提交后输出远程地址、分支、commit hash 和最终 git status。
```

### 创建 Pull Request

```text
请使用 commit-commands skill 将当前改动提交、推送，并在 GitHub 上创建 Pull Request。
如果当前在 main 分支，请先创建一个合适的新分支。
PR 描述请包含变更摘要和测试计划。
```

### 清理 gone 分支

```text
请使用 commit-commands skill 清理本地已经显示为 [gone] 的分支。
先运行 git fetch --prune、git branch -v 和 git worktree list。
如果某个 gone 分支绑定了 worktree，请先说明并安全移除对应 worktree 后再删除分支。
```

## 常见工作流程

### 快速提交

1. 查看 `git status`。
2. 查看 staged 和 unstaged diff。
3. 检查近期提交风格。
4. 排除敏感文件和无关文件。
5. 暂存目标文件。
6. 创建 commit。
7. 输出 commit hash 和最终状态。

### 提交并推送

1. 完成快速提交流程。
2. 查看当前分支和远程地址。
3. 执行 `git push` 或 `git push -u origin <branch>`。
4. 确认本地分支与远程分支同步。

### 提交、推送并创建 PR

1. 确认仓库远程是 GitHub，且 `gh` 已安装并认证。
2. 如当前在默认分支，先创建 feature 分支。
3. 提交改动并推送分支。
4. 使用 `gh pr create` 创建 PR。
5. 输出 PR URL。

### 清理远端已删除分支

1. 执行 `git fetch --prune` 更新远程跟踪状态。
2. 用 `git branch -v` 找出 `[gone]` 分支。
3. 用 `git worktree list` 检查是否有关联 worktree。
4. 先移除关联 worktree，再删除对应本地分支。
5. 跳过当前分支和不确定是否安全删除的分支。

## 依赖和环境

根据任务不同，可能需要：

- `git`：必需，用于查看状态、暂存、提交、推送和管理分支。
- 已配置的 Git 身份：`user.name` 和 `user.email`。
- 已配置的远程仓库：通常是 `origin`。
- 网络和远程仓库认证：执行 push 时需要。
- `gh`：仅在创建 GitHub Pull Request 时需要，并且必须已登录。

## 使用注意

- 提交前必须检查工作区状态和 diff，避免把无关改动提交进去。
- 不允许提交 `.env`、token、cookie、credentials、密钥、日志、缓存、数据库、本地账号资料或生成的字节码。
- 不要默认提交整个工作区；如果存在多组无关改动，应按用户指定范围暂存。
- 不要在没有明确授权时执行 `git reset --hard`、强制 push、删除分支或改写历史。
- 创建 PR 前应确认远程仓库是 GitHub；Gitee 等仓库不能直接使用 `gh pr create`。
- Push 失败通常是认证、网络或远程保护规则问题，应停止并说明错误。
- 该 skill 的许可证为 Apache License 2.0，集成、分发或二次修改前请阅读 `LICENSE`。
