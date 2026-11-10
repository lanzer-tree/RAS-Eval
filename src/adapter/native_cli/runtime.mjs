import fs from "node:fs";
import { spawn, spawnSync } from "node:child_process";
import readline from "node:readline";

const TRACE_PATH = process.env.DAEDALUS_TRACE_PATH || "/workspace/.daedalus_trace.jsonl";
const VERIFIER = "/app/src/evaluator/spec/runtime.py";
const BRIDGE = "/app/src/adapter/native_cli/tool_bridge.py";

export function appendError(framework, stage, error) {
  try {
    fs.appendFileSync(
      "/runtime_verification/plugin_errors.log",
      `[${framework}:${stage}] ${String(error)}\n`,
      "utf8",
    );
  } catch {
    // Runtime verification is observational and must not break the agent run.
  }
}

export function appendTrace(value, framework) {
  try {
    const fd = fs.openSync(TRACE_PATH, "a");
    try {
      fs.writeSync(fd, `${JSON.stringify(value)}\n`);
      fs.fsyncSync(fd);
    } finally {
      fs.closeSync(fd);
    }
  } catch (error) {
    appendError(framework, "trace", error);
  }
}

export function resultText(value) {
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
  if ("output" in value && typeof value.output === "string") return value.output;
  return JSON.stringify(value);
}

export function invokeVerifier(framework, payload) {
  if (!process.env.DAEDALUS_RUNTIME_REQUEST) return;
  const completed = spawnSync("python", [VERIFIER, "step"], {
    env: process.env,
    input: JSON.stringify(payload),
    encoding: "utf8",
  });
  if (completed.error || completed.status !== 0) {
    appendError(framework, "verify", completed.error || completed.stderr || `exit ${completed.status}`);
  }
}

export function commitToolStep(framework, providerToolName, toolName, args, result) {
  const text = resultText(result);
  appendTrace({
    role: "assistant",
    content: "",
    tool_calls: [{ type: "function", function: { name: toolName, arguments: args || {} } }],
  }, framework);
  appendTrace({ role: "tool", name: toolName, content: text }, framework);
  invokeVerifier(framework, {
    provider_tool_name: providerToolName,
    tool_name: toolName,
    arguments: args || {},
    result: text,
  });
}

export function readSample() {
  const path = process.env.RAS_EVAL_SAMPLE_PATH || "/sample.json";
  return JSON.parse(fs.readFileSync(path, "utf8"));
}

export class BridgeClient {
  constructor(framework) {
    this.framework = framework;
    this.nextId = 0;
    this.pending = new Map();
    this.tools = [];
    this.ready = new Promise((resolve, reject) => {
      this.resolveReady = resolve;
      this.rejectReady = reject;
    });
    this.child = spawn("python", ["-u", BRIDGE], {
      cwd: process.env.RAS_EVAL_WORKDIR || "/workspace",
      env: process.env,
      stdio: ["pipe", "pipe", "pipe"],
    });
    const lines = readline.createInterface({ input: this.child.stdout });
    lines.on("line", (line) => this.handleLine(line));
    this.child.stderr.on("data", (chunk) => appendError(framework, "bridge-stderr", chunk.toString().trim()));
    this.child.on("error", (error) => this.fail(error));
    this.child.on("exit", (code, signal) => {
      if (!this.closed) this.fail(new Error(`tool bridge exited code=${code} signal=${signal}`));
    });
  }

  handleLine(line) {
    let message;
    try {
      message = JSON.parse(line);
    } catch (error) {
      appendError(this.framework, "bridge-json", `${error}: ${line.slice(0, 500)}`);
      return;
    }
    if (message.type === "ready") {
      this.tools = Array.isArray(message.tools) ? message.tools : [];
      this.resolveReady(this.tools);
      return;
    }
    if (message.type === "fatal") {
      this.fail(new Error(message.error || "tool bridge failed"));
      return;
    }
    const pending = this.pending.get(message.id);
    if (!pending) return;
    this.pending.delete(message.id);
    if (message.ok) pending.resolve(String(message.result ?? ""));
    else pending.reject(new Error(message.error || "tool bridge call failed"));
  }

  fail(error) {
    this.rejectReady(error);
    for (const pending of this.pending.values()) pending.reject(error);
    this.pending.clear();
    appendError(this.framework, "bridge", error);
  }

  async call(tool, args) {
    await this.ready;
    if (this.closed || !this.child.stdin.writable) throw new Error("tool bridge is closed");
    const id = ++this.nextId;
    const response = new Promise((resolve, reject) => this.pending.set(id, { resolve, reject }));
    this.child.stdin.write(`${JSON.stringify({ id, tool, arguments: args || {} })}\n`);
    return response;
  }

  close() {
    if (this.closed) return;
    this.closed = true;
    try {
      this.child.stdin.end(`${JSON.stringify({ type: "close" })}\n`);
    } catch {
      this.child.kill("SIGTERM");
    }
  }
}
