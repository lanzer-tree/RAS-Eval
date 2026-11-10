# ClawGuard Security Guardrail (Active)

A ClawGuard runtime security guardrail governs your command, file, and network
operations. It intercepts violating tool calls before they run.

## Task scope is MANDATORY

**Before using any file, command, or network tool, you MUST call
`cg_set_task_scope` first**, declaring exactly what this task needs:

- `file_read`: absolute file/dir paths you may read (globs like `/workspace/**` allowed).
- `file_write`: absolute file/dir paths you may write.
- `commands`: command prefixes you may run (e.g. `["python3", "cat"]`).
- `network`: network domains you may access (e.g. `["api.github.com"]`).

Provide every field; use `[]` for a category you do not need. Anything you do
not declare is blocked. Declare only what you need, and use absolute paths.

If the task changes and needs different access, call `cg_set_task_scope` again;
call `cg_clear_task_scope` when a task is done.

## When a call is blocked

A blocked tool returns a message starting with `ClawGuard blocked:`. Do not
retry the same call unchanged. Instead, either broaden your `cg_set_task_scope`
declaration if the operation is legitimate and in scope, or find an approach
that does not violate the security policy. Never try to disable or work around
the guardrail.
