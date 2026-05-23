---
name: code-simplifier
description: Simplify and refine code for clarity, consistency, and maintainability while preserving behavior. Use when Codex is asked to simplify recently changed code, reduce duplication or nesting, improve names, clean up conditionals, make code easier to review, or perform low-risk local refactoring without changing outputs, interfaces, or data semantics.
---

# Code Simplifier

Use this skill to make code easier to read, review, debug, and maintain while preserving its current behavior. Apply it only when the user asks for simplification, cleanup, readability improvements, or behavior-preserving refactoring.

## Operating Principles

1. Preserve behavior.
   Keep existing outputs, public interfaces, error behavior, side effects, data semantics, and relevant performance characteristics unchanged unless the user explicitly asks for a behavior change.

2. Prefer clarity over brevity.
   Do not compress code into dense one-liners, nested ternaries, clever chains, or overly generic helpers just to reduce line count.

3. Follow the local project.
   Use existing project patterns, naming conventions, formatting, imports, error handling, type style, and tests. Check local guidance such as `AGENTS.md`, `CONTRIBUTING.md`, formatter config, lint config, package scripts, and nearby code.

4. Keep scope tight.
   Focus on files or diffs the user identified. If the request mentions recent changes, inspect the current Git diff and avoid broad unrelated cleanup.

5. Keep abstractions honest.
   Add or keep abstractions only when they reduce meaningful duplication, clarify a real concept, or match an existing pattern. Remove indirection that obscures simple logic.

## Workflow

1. Identify the requested scope.
   Use the user's file paths, current Git diff, or recent edits. If scope is ambiguous and the worktree contains unrelated changes, state the scope you will touch before editing.

2. Understand behavior before editing.
   Read callers, tests, type definitions, schemas, fixtures, and surrounding code when needed. Note boundary cases that must remain stable.

3. Look for low-risk simplifications.
   Prefer changes such as:
   - replacing deeply nested branches with early returns or clearer conditionals
   - replacing nested ternaries with `if/else` or `switch`
   - removing duplicated branches or repeated calculations
   - improving names for variables, helpers, and intermediate values
   - extracting small helpers only when the extracted concept is reused or clarifies intent
   - deleting comments that restate obvious code while keeping comments that explain constraints, tradeoffs, or domain rules

4. Edit conservatively.
   Avoid public API renames, file moves, dependency changes, schema changes, broad formatting churn, and test rewrites unless required by the requested simplification.

5. Verify.
   Run the narrowest relevant checks available, such as unit tests, type checks, lint, formatting checks, or project-specific validation scripts. If checks cannot be run, explain why and describe the remaining risk.

## Review Checklist

- Does the new code preserve behavior and interfaces?
- Is the code easier to scan than before?
- Did the change avoid unnecessary abstractions?
- Are names more precise without being verbose?
- Did the edit stay inside the requested scope?
- Did tests, type checks, lint, or an equivalent validation pass?

## When To Stop

Stop and report instead of editing when simplification would require changing behavior, guessing business rules, touching unrelated modules, or making unverified high-risk changes.
