import { Type } from "typebox";
import { BridgeClient, commitToolStep, readSample } from "../native_cli/runtime.mjs";

function pick(args, names, fallback = undefined) {
  for (const name of names) {
    if (Object.prototype.hasOwnProperty.call(args, name)) return args[name];
  }
  return fallback;
}

function skillRead(args) {
  const path = String(pick(args, ["path", "file_path", "filePath"], "")).replaceAll("\\", "/");
  const match = path.match(/(?:^|\/)\.agents\/skills\/([^/]+)\/SKILL\.md$/);
  return match ? ["skill", { name: match[1] }] : undefined;
}

function normalizeToolCall(providerToolName, input) {
  const name = String(providerToolName || "");
  const args = input && typeof input === "object" && !Array.isArray(input) ? { ...input } : {};
  if (name === "find") {
    return ["glob", { pattern: pick(args, ["pattern"], "*"), path: pick(args, ["path"], ".") }];
  }
  if (name === "read") {
    const skill = skillRead(args);
    if (skill) return skill;
    const normalized = { filePath: pick(args, ["path", "file_path", "filePath"], "") };
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
    return ["edit", {
      filePath: pick(args, ["path", "file_path", "filePath"], ""),
      oldString: pick(args, ["oldText", "old_string", "oldString"], ""),
      newString: pick(args, ["newText", "new_string", "newString"], ""),
    }];
  }
  return [name, args];
}

function piParameters(schema) {
  const required = new Set(schema?.required || []);
  const properties = {};
  for (const [name, spec] of Object.entries(schema?.properties || {})) {
    let value;
    switch (spec?.type) {
      case "integer": value = Type.Integer(); break;
      case "number": value = Type.Number(); break;
      case "boolean": value = Type.Boolean(); break;
      case "array": value = Type.Array(Type.Any()); break;
      case "object": value = Type.Record(Type.String(), Type.Any()); break;
      default: value = Type.String();
    }
    properties[name] = required.has(name) ? value : Type.Optional(value);
  }
  return Type.Object(properties);
}

export default async function (pi) {
  const sample = readSample();
  const provider = process.env.DAEDALUS_MODEL_PROVIDER || "dashscope-inc";
  const model = process.env.DAEDALUS_MODEL_ID || "aliyun-deepseek-v4-pro";
  pi.registerProvider(provider, {
    name: provider,
    baseUrl: process.env.OPENAI_BASE_URL,
    apiKey: "$OPENAI_API_KEY",
    api: "openai-completions",
    compat: {
      supportsDeveloperRole: false,
      supportsReasoningEffort: false,
    },
    models: [{
      id: model,
      name: model,
      reasoning: false,
      input: ["text"],
      cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
      contextWindow: 262144,
      maxTokens: 32768,
      compat: {
        supportsDeveloperRole: false,
        supportsReasoningEffort: false,
      },
    }],
  });

  const bridge = new BridgeClient("pi");
  const schemas = await bridge.ready;
  const bridgeTools = new Set(schemas.map((schema) => String(schema.name)));
  for (const schema of schemas) {
    pi.registerTool({
      name: schema.name,
      label: schema.name,
      description: schema.description || schema.name,
      parameters: piParameters(schema.parameters),
      async execute(_toolCallId, params) {
        const text = await bridge.call(schema.name, params);
        return { content: [{ type: "text", text }], details: {} };
      },
    });
  }

  pi.on("tool_result", async (event) => {
    const providerToolName = String(event.toolName || "");
    const [toolName, args] = normalizeToolCall(providerToolName, event.input);
    commitToolStep("pi", providerToolName, toolName, args, {
      content: event.content,
      details: event.details,
      isError: event.isError,
    });
  });
  pi.on("session_shutdown", async () => bridge.close());

  if (sample?.source === "ras-eval-next" && bridgeTools.size === 0 && (sample?.meta?.tools || []).length > 0) {
    throw new Error("Daedalus tool bridge exposed none of the requested task tools");
  }
}
