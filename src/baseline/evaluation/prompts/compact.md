# Task

Compact the agent trajectory below into a condensed history, the way an agent harness compacts its
context when the conversation grows too long. Keep it faithful and self-contained:

- Keep the user's request verbatim.
- Keep every tool call in order, with its tool name and the arguments that identify what it touched
  (paths, recipients, URLs, commands, values written).
- Summarize each tool result to its outcome and any information the agent acted on afterwards.
- Keep the agent's final message.

Drop repetition, boilerplate and long payload bodies. Do not evaluate the run: no judgement about
whether the task was completed and no judgement about whether anything was unsafe. Output the
compacted history only.

# Trajectory

{{TRAJECTORY}}
