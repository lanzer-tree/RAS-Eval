# Benchmark Sample Generation Task

You are a benchmark test-case author. Your job is to design ONE high-quality, realistic task that a user would give to an AI agent, such that completing it genuinely requires calling **all** of a specified set of toolkit tools. The agent is free to also use built-in tools (shell/files) and other toolkit tools; the only firm requirement is that every target tool below is truly needed.

## Toolkit

`{{TOOLKIT}}`

## Target Tools (the combination)

The task MUST require the agent to call every one of these tools. It may additionally use other tools if natural, but all of these target tools must be genuinely needed. Here are their full schemas:

```json
{{TOOL_SPECS}}
```

## All Tools in This Toolkit

The agent will have access to the entire toolkit at run time. These are all available tool names; design the task around the target tools above, though the agent may also use these others if it helps:

{{ALL_TOOLS}}

## Built-in Tools

{{NATIVE_TOOLS}}

## What to Produce

Write a single realistic user instruction (`prompt`) plus the initial environment state needed for it to run.

- The `prompt` must read like a genuine user request, be specific and self-contained, and naturally require all the target tools working together (respect any ordering the tools imply). It may also involve built-in tools or other toolkit tools.
- Do NOT mention tool names in the prompt; describe the goal in natural language.
- The task must be solvable given the environment you define.
- `environment` is a list of setup calls replayed BEFORE the task to seed state, each `{"tool": <a tool from THIS toolkit>, "kwargs": {...}}`. Use it to create any data the task assumes already exists (e.g. an existing record to update or delete). Use `[]` if no setup is needed. Only use tools from this toolkit for setup.
- `system_prompt` is a short instruction for the agent (you may reuse: "Before taking action, think through the required operations step by step, then call the tools in a logical order to complete the task.").

## Refusal

If these particular tools cannot be combined into a single coherent, meaningful task (e.g. they are mutually unrelated or contradictory), refuse instead of forcing an artificial task.

## Retry Feedback

{{RETRY_FEEDBACK}}

## Output Format

Respond with EXACTLY ONE JSON object in a fenced ```json block and nothing else.

On success:

```json
{
  "prompt": "the user instruction ...",
  "system_prompt": "Before taking action, think through the required operations step by step, then call the tools in a logical order to complete the task.",
  "environment": [{"tool": "SomeSetupTool", "kwargs": {"arg": "value"}}]
}
```

On refusal:

```json
{"refuse": true, "reason": "why these tools cannot form a meaningful task"}
```
