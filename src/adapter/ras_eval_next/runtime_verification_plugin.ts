const PROVIDER_PREFIX = "ras_eval_next_"
const VERIFIER = "/app/src/evaluator/spec/runtime.py"

function toolName(providerToolName: string): string {
  return providerToolName.startsWith(PROVIDER_PREFIX)
    ? providerToolName.slice(PROVIDER_PREFIX.length)
    : providerToolName
}

function resultText(output: unknown): string {
  if (typeof output === "string") return output
  if (!output || typeof output !== "object") return String(output ?? "")
  const value = output as { output?: unknown; content?: unknown }
  if (typeof value.output === "string") return value.output
  if (Array.isArray(value.content)) {
    return value.content
      .map((item) => {
        if (item && typeof item === "object" && "text" in item) {
          return String((item as { text: unknown }).text)
        }
        return JSON.stringify(item)
      })
      .join("\n")
  }
  return JSON.stringify(output)
}

async function invoke(command: "init" | "step", payload?: unknown): Promise<void> {
  try {
    const process = Bun.spawn(["python", VERIFIER, command], {
      env: Bun.env,
      stdin: payload === undefined ? "ignore" : "pipe",
      stdout: "ignore",
      stderr: "pipe",
    })
    if (payload !== undefined) {
      process.stdin.write(JSON.stringify(payload))
      process.stdin.end()
    }
    const exitCode = await process.exited
    if (exitCode !== 0) {
      const error = await new Response(process.stderr).text()
      await Bun.write(
        "/runtime_verification/plugin_errors.log",
        `[${command}] ${error.trim()}\n`,
      )
    }
  } catch (error) {
    await Bun.write(
      "/runtime_verification/plugin_errors.log",
      `[${command}] ${String(error)}\n`,
    ).catch(() => undefined)
  }
}

async function isMainSession(sessionID?: string): Promise<boolean> {
  const directory = Bun.env.INFORMATION_FLOW_DIR
  if (!directory) return true
  if (!sessionID) return false
  try {
    const record = await Bun.file(`${directory}/main_session.json`).json() as {
      session_id?: unknown; review_session_ids?: unknown
    }
    return typeof record.session_id === "string"
      && record.session_id === sessionID
      && !(Array.isArray(record.review_session_ids) && record.review_session_ids.includes(sessionID))
  } catch {
    return false
  }
}

export const RuntimeVerificationPlugin = async () => {
  const admitted = new Set<string>()
  const callKey = (input: { sessionID?: string; callID?: string }) =>
    JSON.stringify([input.sessionID, input.callID])
  return {
    "tool.execute.before": async (input: { sessionID?: string; callID?: string } = {}) => {
      if (!await isMainSession(input.sessionID)) return
      await invoke("init")
      if (Bun.env.INFORMATION_FLOW_DIR) admitted.add(callKey(input))
    },
    "tool.execute.after": async (
      input: { tool: string; args: unknown; sessionID?: string; callID?: string },
      output: unknown,
    ) => {
      const wasAdmitted = admitted.delete(callKey(input))
      if (!await isMainSession(input.sessionID)) return
      if (Bun.env.INFORMATION_FLOW_DIR && !wasAdmitted) return
      await invoke("step", {
        provider_tool_name: input.tool,
        tool_name: toolName(input.tool),
        arguments: input.args,
        result: resultText(output),
      })
    },
  }
}
