# Codex Home Versioning

This directory is the Git-versioned configuration layer for the parent Codex
home. It deliberately does **not** turn the whole `.codex` directory into a Git
repository.

## Boundary

Versioned in the `skills` repository:

- portable Agent policy in `../AGENTS.md`;
- the deterministic Agent mirror exporter in `../sync_agents.ps1`;
- shared Codex configuration requirements in `config.shared.toml`;
- the machine-local schema/example and validation code in this directory;
- reusable Skills, scripts, templates, schemas, and tests already owned by this
  repository.

Kept outside Git in the parent Codex home:

- `config.toml`, because it contains machine paths, trusted-project state, and
  generated plugin/MCP registrations;
- `machine.local.json`, which binds logical names to this computer's physical
  paths but contains no credential values;
- authentication, credential files, runtime state, sessions, caches, logs,
  history, attachments, databases, plugin caches, and temporary clones;
- the generated `WORKSPACE_AGENTS.md` runtime mirror.

Organization-restricted and personal Skills remain logically distinct from
universal configuration. Moving existing Skill history into separate remotes is
intentionally outside this change; repository access policy and the second
machine must be confirmed before that migration.

## Bootstrap a machine

1. Place the `skills` repository directly below the intended Codex home.
2. Copy `machine.local.example.json` to `<codex-home>/machine.local.json` and
   replace placeholders with local absolute paths. Do not put passwords, API
   keys, tokens, cookies, or credential contents in that file.
3. Keep the active `<codex-home>/config.toml` local. Ensure the two settings in
   `config.shared.toml` are present with the same values.
4. Export the canonical Agent instructions:

   ```powershell
   .\sync_agents.ps1 -Mode Export -NoCommit
   ```

5. Validate the versioning boundary:

   ```powershell
   <python-from-machine.local.json> .\codex-config\scripts\validate_codex_home_versioning.py
   ```

The validator reads only configuration metadata. It never opens files named by
`credential_file_paths`, and it does not modify the repository or Codex home.

## Codex-native behavior

Codex discovers repository instructions from `AGENTS.md` and configured fallback
filenames. The active `config.toml` remains machine-local, while this repository
tracks the portable contract and verifies the effective values. See the official
[AGENTS.md guidance](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
and [configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference).
