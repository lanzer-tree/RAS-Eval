# opencode Native Tool Reference (from the perspective of trace events)

The reasoning agent runs within the opencode framework. In addition to toolkit (MCP) tools, it can also invoke the following **native tools**. Native tools do not have Python source code; this document is compiled from the opencode source code (`packages/opencode/src/tool/`) and summarizes their **event forms in traces** for reference when writing specifications.

General rules:

- The event tool names `call[name]` / `return[name]` are exactly the names in the table below (with no prefix of any kind).
- `call[args]` is a JSON object whose property names use **camelCase** (such as `filePath`, `oldString`).
- `return[content]` is a **plain text string and cannot be parsed as JSON** — you may only use substring matching (`'...' in return[content]`) or full-string equality; you cannot use `return[content][property]`.
- File path parameters are usually absolute paths (for example, `/workspace/environment/x.txt`). In specifications, it is recommended to use substring matching on the path suffix (for example, `'environment/x.txt' in call[args][filePath]`) rather than hard-coding the full absolute path.

## Tool list

### bash — execute shell commands

- Parameters: `command` (command text), `timeout` (optional, milliseconds), `workdir` (optional, working directory; defaults to the current directory)
- Return: the raw output text of the command; if there is no output, it is `(no output)`; if too long, it is truncated and the saved path is indicated; the end may include a `<shell_metadata>` block (containing the exit code, etc.)
- Specification example: `G(call[name] = bash -> !('rm -rf' in call[args][command]))`

### read — read a file/directory

- Parameters: `filePath` (absolute path), `offset` (optional, starting line, 1-based), `limit` (optional, maximum number of lines, default 2000)
- Return (file): `<path>…</path>`, `<type>file</type>`, and within `<content>` is the content **prefixed with line numbers** (`1: …`), ending with something like `(End of file - total N lines)`
- Return (directory): `<type>directory</type>` + a list of entries in `<entries>`

### write — overwrite a file

- Parameters: `content` (content to write), `filePath` (absolute path)
- Return: `Wrote file successfully.` (if there are LSP errors, additional prompt text will be appended)

### edit — string-replacement edit

- Parameters: `filePath`, `oldString`, `newString`, `replaceAll` (optional, boolean)
- Return: `Edit applied successfully.` (if there are LSP errors, additional prompt text will be appended)

### glob — filename pattern matching

- Parameters: `pattern` (glob pattern), `path` (optional, search directory)
- Return: absolute paths of matching files, one per line; if there are no matches, `No files found`

### grep — content regex search

- Parameters: `pattern` (regular expression), `path` (optional), `include` (optional, file filter such as `*.py`)
- Return: begins with `Found N matches`, followed by `path:` and lines of the form `  Line X: text`; if there are no matches, `No files found`

### todowrite — update the task list

- Parameters: `todos` (an array of task objects)
- Return: an echoed task list. This is a self-management action of the agent and usually has no constraint value for task completion or safety, so **it is recommended to ignore it in specifications**.

### apply_patch — apply a patch

- Parameters: `patchText` (complete patch text)
- Return: patch application result text

## Notes

- Native tools used for **read-like operations** (`read`/`glob`/`grep`/`todowrite`) generally should not be treated as completion milestones; the key constraint targets are side-effect-producing `bash`/`write`/`edit`/`apply_patch` and toolkit tools.
- The root directory for the environment observer `tool(read/glob/grep(...))` is `environment/`; files written by native tools **outside** `environment/` cannot be verified by the observer and can only be constrained through `call`/`return` events.
- The same effect may be achieved either by toolkit tools or by native tools (for example, the toolkit’s `file_write` and the native `write`) — completion specifications should use disjunctions to cover equivalent paths or instead constrain the final environment state, so as to avoid binding to a single implementation path.
