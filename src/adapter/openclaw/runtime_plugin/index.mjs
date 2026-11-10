import fs from "node:fs";
import { spawnSync } from "node:child_process";

const TRACE_PATH = process.env.DAEDALUS_TRACE_PATH || "/workspace/.daedalus_trace.jsonl";
const SAMPLE_PATH = process.env.RAS_EVAL_SAMPLE_PATH || "/sample.json";
const VERIFIER = "/app/src/evaluator/spec/runtime.py";
const MCP_PREFIX = "ras_eval_next__";
const taskToolNames = new Map();
let sample = {};
try {
  sample = JSON.parse(fs.readFileSync(SAMPLE_PATH, "utf8"));
  for (const name of sample?.meta?.tools || []) taskToolNames.set(String(name).toLowerCase(), String(name));
} catch {
  // The runner still preserves native-tool traces when sample metadata is unavailable.
}
const pendingCalls = new Map();
const pendingByName = new Map();
const completedCalls = new Set();
let fallbackCallId = 0;

function appendLine(value) {
  try {
    const fd = fs.openSync(TRACE_PATH, "a");
    try {
      fs.writeSync(fd, `${JSON.stringify(value)}\n`);
      fs.fsyncSync(fd);
    } finally {
      fs.closeSync(fd);
    }
  } catch (error) {
    appendError("trace", error);
  }
}

function appendError(stage, error) {
  try {
    fs.appendFileSync(
      "/runtime_verification/plugin_errors.log",
      `[openclaw:${stage}] ${String(error)}\n`,
      "utf8",
    );
  } catch {
    // Runtime verification is observational and must not break the agent run.
  }
}

function pick(args, names, fallback = undefined) {
  for (const name of names) {
    if (Object.prototype.hasOwnProperty.call(args, name)) return args[name];
  }
  return fallback;
}

function normalizeToolCall(providerToolName, input) {
  const name = String(providerToolName || "");
  const args = input && typeof input === "object" && !Array.isArray(input) ? { ...input } : {};
  if (name.startsWith(MCP_PREFIX)) {
    const rawName = name.slice(MCP_PREFIX.length);
    return [taskToolNames.get(rawName.toLowerCase()) || rawName, args];
  }
  if (name === "exec") {
    const normalized = { command: pick(args, ["command"], "") };
    if (Object.prototype.hasOwnProperty.call(args, "timeout")) normalized.timeout = args.timeout;
    const workdir = pick(args, ["cwd", "workdir"]);
    if (workdir !== undefined) normalized.workdir = workdir;
    return ["bash", normalized];
  }
  if (name === "read") {
    const path = pick(args, ["path", "file_path", "filePath"], "");
    const match = String(path).replaceAll("\\", "/").match(/(?:^|\/)\.agents\/skills\/([^/]+)\/SKILL\.md$/);
    if (match) return ["skill", { name: match[1] }];
    const normalized = { filePath: path };
    for (const key of ["offset", "limit"]) {
      if (Object.prototype.hasOwnProperty.call(args, key)) normalized[key] = args[key];
    }
    return ["read", normalized];
  }
  if (name === "write") {
    return ["write", {
      filePath: pick(args, ["path", "file_path", "filePath"], ""),
      content: pick(args, ["content"], ""),
    }];
  }
  if (name === "edit") {
    const normalized = {
      filePath: pick(args, ["path", "file_path", "filePath"], ""),
      oldString: pick(args, ["oldText", "old_string", "oldString"], ""),
      newString: pick(args, ["newText", "new_string", "newString"], ""),
    };
    const replaceAll = pick(args, ["replaceAll", "replace_all"]);
    if (replaceAll !== undefined) normalized.replaceAll = Boolean(replaceAll);
    return ["edit", normalized];
  }
  if (name === "apply_patch") return ["patch", args];
  return [name, args];
}

function resultText(value) {
  if (typeof value === "string") return value;
  if (value === null || value === undefined) return "";
  if (typeof value !== "object") return String(value);
  if (Array.isArray(value.content)) {
    return value.content
      .map((item) => {
        if (item && typeof item === "object" && "text" in item) return String(item.text);
        return JSON.stringify(item);
      })
      .join("\n");
  }
  return JSON.stringify(value);
}

function rememberCall(event, ctx) {
  const providerToolName = String(event.toolName || ctx.toolName || "");
  const [toolName, args] = normalizeToolCall(providerToolName, event.params);
  const callId = String(event.toolCallId || ctx.toolCallId || `fallback-${++fallbackCallId}`);
  const call = { callId, providerToolName, toolName, args };
  pendingCalls.set(callId, call);
  const queue = pendingByName.get(providerToolName) || [];
  queue.push(callId);
  pendingByName.set(providerToolName, queue);
  invokeVerifier("init");
  appendLine({
    role: "assistant",
    content: "",
    tool_calls: [{ type: "function", function: { name: toolName, arguments: args } }],
  });
}

function takeCall(event, ctx) {
  const providerToolName = String(event.toolName || ctx.toolName || "");
  const explicitId = event.toolCallId || ctx.toolCallId;
  if (explicitId && pendingCalls.has(String(explicitId))) {
    const callId = String(explicitId);
    const call = pendingCalls.get(callId);
    pendingCalls.delete(callId);
    return call;
  }
  const queue = pendingByName.get(providerToolName) || [];
  while (queue.length > 0) {
    const callId = queue.shift();
    const call = pendingCalls.get(callId);
    if (call) {
      pendingCalls.delete(callId);
      return call;
    }
  }
  const [toolName, args] = normalizeToolCall(providerToolName, event.params);
  return {
    callId: String(explicitId || `unmatched-${++fallbackCallId}`),
    providerToolName,
    toolName,
    args,
  };
}

function invokeVerifier(command, payload = undefined) {
  if (!process.env.DAEDALUS_RUNTIME_REQUEST) return;
  const completed = spawnSync("python", [VERIFIER, command], {
    env: process.env,
    input: payload === undefined ? undefined : JSON.stringify(payload),
    encoding: "utf8",
  });
  if (completed.error || completed.status !== 0) {
    appendError(command, completed.error || completed.stderr || `exit ${completed.status}`);
  }
}

function finishCall(event, ctx, result) {
  const explicitId = event.toolCallId || ctx.toolCallId;
  if (explicitId && completedCalls.has(String(explicitId))) return;
  const call = takeCall(event, ctx);
  if (completedCalls.has(call.callId)) return;
  completedCalls.add(call.callId);
  const text = resultText(result);
  appendLine({ role: "tool", name: call.toolName, content: text });
  invokeVerifier("step", {
    provider_tool_name: call.providerToolName,
    tool_name: call.toolName,
    arguments: call.args,
    result: text,
  });
}

function persistedResult(message) {
  if (!message || typeof message !== "object") return message;
  return Object.prototype.hasOwnProperty.call(message, "content") ? message.content : message;
}

export default {
  id: "daedalus-runtime-verification",
  name: "Daedalus Runtime Verification",
  register(api) {
    api.on("before_prompt_build", () => {
      const systemPrompt = sample?.meta?.system_prompt;
      return systemPrompt ? { prependSystemContext: String(systemPrompt) } : undefined;
    });
    api.on("before_tool_call", (event, ctx) => {
      rememberCall(event, ctx);
    });
    api.on("tool_result_persist", (event, ctx) => {
      finishCall(event, ctx, persistedResult(event.message));
    });
    api.on("after_tool_call", (event, ctx) => {
      if (!completedCalls.has(String(event.toolCallId || ctx.toolCallId || ""))) {
        finishCall(event, ctx, event.error || event.result);
      }
    });
  },
};
