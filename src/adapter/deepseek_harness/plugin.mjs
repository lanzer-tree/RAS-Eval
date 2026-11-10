import { BridgeClient, commitToolStep, readSample, resultText } from "../native_cli/runtime.mjs";

export const name = "daedalus-native-cli-adapter";
export const inject = ["tools"];

function pick(args, names, fallback = undefined) {
  for (const name of names) {
    if (Object.prototype.hasOwnProperty.call(args, name)) return args[name];
  }
  return fallback;
}

function skillRead(args) {
  const path = String(pick(args, ["file_path", "filePath", "path"], "")).replaceAll("\\", "/");
  const match = path.match(/(?:^|\/)\.agents\/skills\/([^/]+)\/SKILL\.md$/);
  return match ? ["skill", { name: match[1] }] : undefined;
}

export function normalizeToolCall(providerToolName, input) {
  const name = String(providerToolName || "").replace(/<\|.*$/, "");
  const args = input && typeof input === "object" && !Array.isArray(input) ? { ...input } : {};
  if (name === "todo_write") return ["todowrite", args];
  if (name === "str_replace_editor") {
    const command = String(args.command || "");
    if (command === "view") {
      const normalized = { filePath: pick(args, ["path", "file_path", "filePath"], "") };
      const range = args.view_range;
      if (Array.isArray(range) && Number.isInteger(range[0]) && range[0] > 0) {
        normalized.offset = range[0];
        if (Number.isInteger(range[1]) && range[1] >= range[0]) {
          normalized.limit = range[1] - range[0] + 1;
        }
      }
      return ["read", normalized];
    }
    if (command === "create" || command === "write") {
      return ["write", {
        filePath: pick(args, ["path", "file_path", "filePath"], ""),
        content: pick(args, ["file_text", "content"], ""),
      }];
    }
    if (command === "str_replace") {
      const normalized = {
        filePath: pick(args, ["path", "file_path", "filePath"], ""),
        oldString: pick(args, ["old_str", "old_string", "oldString"], ""),
        newString: pick(args, ["new_str", "new_string", "newString"], ""),
      };
      const replaceAll = pick(args, ["replace_all", "replaceAll"]);
      if (replaceAll !== undefined) normalized.replaceAll = Boolean(replaceAll);
      return ["edit", normalized];
    }
    return [name, args];
  }
  if (name === "read") {
    const skill = skillRead(args);
    if (skill) return skill;
    const normalized = { filePath: pick(args, ["file_path", "filePath", "path"], "") };
    for (const key of ["offset", "limit"]) {
      if (Object.prototype.hasOwnProperty.call(args, key)) normalized[key] = args[key];
    }
    return ["read", normalized];
  }
  if (name === "write") {
    return ["write", {
      filePath: pick(args, ["file_path", "filePath", "path"], ""),
      content: pick(args, ["content"], ""),
    }];
  }
  if (name === "edit") {
    const normalized = {
      filePath: pick(args, ["file_path", "filePath", "path"], ""),
      oldString: pick(args, ["old_string", "oldString", "oldText"], ""),
      newString: pick(args, ["new_string", "newString", "newText"], ""),
    };
    const replaceAll = pick(args, ["replace_all", "replaceAll"]);
    if (replaceAll !== undefined) normalized.replaceAll = Boolean(replaceAll);
    return ["edit", normalized];
  }
  return [name, args];
}

export async function apply(ctx) {
  const sample = readSample();
  const bridge = new BridgeClient("deepseek-harness");
  const schemas = await bridge.ready;
  const bridgeTools = new Set(schemas.map((schema) => String(schema.name)));
  ctx.effect(() => () => bridge.close(), "daedalus tool bridge");

  for (const schema of schemas) {
    ctx.tools.register({
      name: schema.name,
      description: schema.description || schema.name,
      parameters: schema.parameters,
      output: {
        schema: { type: "string" },
        render: (_args, value) => [{ type: "text", text: String(value ?? "") }],
      },
      async execute(args) {
        return bridge.call(schema.name, args);
      },
    });
  }

  ctx.on("tools/result", (execution, result) => {
    const providerToolName = String(execution?.name || "");
    const [toolName, args] = normalizeToolCall(providerToolName, execution?.arguments);
    // The final registry outcome is authoritative for both native and bridged tools.
    commitToolStep("deepseek-harness", providerToolName, toolName, args, resultText(result));
  });

  if (sample?.source === "ras-eval-next" && bridgeTools.size === 0 && (sample?.meta?.tools || []).length > 0) {
    throw new Error("Daedalus tool bridge exposed none of the requested task tools");
  }
}
