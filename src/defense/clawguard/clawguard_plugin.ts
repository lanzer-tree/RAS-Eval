// ClawGuard opencode plugin (strict mode).
//
// Governs opencode's native command/file/network tools through ClawGuard's rule
// engine and per-prompt task scope: `tool.execute.before` blocks a violating
// call (the block reason is returned to the model so it can recover), and
// `tool.execute.after` redacts secrets from tool output before it enters the
// conversation history. The `cg_set_task_scope` / `cg_clear_task_scope` tools
// let the agent declare least-privilege scope. External MCP tools are not
// governed and pass through untouched.
//
// The rule engine and sanitizer run in Python via the ClawGuard CLI, mirroring
// the runtime-verification plugin's subprocess pattern.

const CLI = "/app/src/defense/clawguard/cli.py"
const SCOPE = "/tmp/clawguard/scope.json"

// opencode native tools ClawGuard governs; everything else passes through.
const GOVERNED = new Set(["bash", "read", "glob", "grep", "write", "edit", "webfetch"])

async function runCli(
  command: string,
  stdinText: string,
  env: Record<string, string>,
): Promise<{ code: number; stdout: string }> {
  const process = Bun.spawn(["python", CLI, command], {
    env,
    stdin: "pipe",
    stdout: "pipe",
    stderr: "pipe",
  })
  process.stdin.write(stdinText)
  process.stdin.end()
  const stdout = await new Response(process.stdout).text()
  const code = await process.exited
  return { code, stdout }
}

const SCOPE_ARGS = {
  task_description: { type: "string", description: "Brief description of what the user asked." },
  file_read: {
    type: "array",
    items: { type: "string" },
    description: "Absolute file/dir paths this task may READ (globs like /workspace/** allowed). Empty = no reads.",
  },
  file_write: {
    type: "array",
    items: { type: "string" },
    description: "Absolute file/dir paths this task may WRITE. Empty = no writes.",
  },
  commands: {
    type: "array",
    items: { type: "string" },
    description: "Command prefixes this task may run (e.g. ['python3','cat']). Empty = no commands.",
  },
  network: {
    type: "array",
    items: { type: "string" },
    description: "Network domains this task may access (e.g. ['api.github.com']). Empty = no network.",
  },
}

export const ClawGuardPlugin = async () => {
  return {
    tool: {
      cg_set_task_scope: {
        description:
          "Declare what this task needs BEFORE using any file/command/network tool. Sets per-prompt " +
          "least-privilege: only the declared paths, command prefixes, and domains are allowed; everything " +
          "else is blocked. Base security rules still apply on top. Provide every field (use [] when a " +
          "category is not needed).",
        args: SCOPE_ARGS,
        async execute(args: unknown) {
          await Bun.write(SCOPE, JSON.stringify(args))
          return "ClawGuard task scope set. Only the declared paths, commands, and domains are now permitted."
        },
      },
      cg_clear_task_scope: {
        description:
          "Clear the current task scope, removing all per-task restrictions. Base security rules still apply.",
        args: {},
        async execute() {
          await Bun.write(SCOPE, "{}")
          return "ClawGuard task scope cleared; base security rules still apply."
        },
      },
    },
    "tool.execute.before": async (
      input: { tool: string },
      output: { args: Record<string, unknown> },
    ) => {
      if (!GOVERNED.has(input.tool)) return
      const { code, stdout } = await runCli(
        "check",
        JSON.stringify({ tool: input.tool, args: output.args }),
        { ...Bun.env, CLAWGUARD_SCOPE_PATH: SCOPE },
      )
      if (code === 2) {
        throw new Error("ClawGuard blocked: " + (stdout.trim() || "operation denied by security policy"))
      }
    },
    "tool.execute.after": async (
      _input: { tool: string },
      output: { output?: string },
    ) => {
      if (typeof output.output !== "string" || !output.output) return
      const { code, stdout } = await runCli("sanitize", output.output, Bun.env)
      if (code === 0) output.output = stdout
    },
  }
}
