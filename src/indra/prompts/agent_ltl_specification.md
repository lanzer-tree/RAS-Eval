# LTL Modeling of LLM Agent Tool-Call Traces

## Trace Linearization

Since agent traces may contain concurrent tool calls, in order to clearly characterize the sequential relationship between tool-call entry and return, the trace needs to be linearized. In fact, the original message list is already linearized, for example:

```json
[
    {
        "role": "system",
        "content": "..."
    },
    {
        "role": "user",
        "content": "..."
    },
    {
        "role": "assistant",
        "tool_calls": [
            {
                "type": "function",
                "function": {
                    "name": "tool_a",
                    "arguments": "{}"
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "tool_b",
                    "arguments": "{}"
                }
            }
        ]
    },
    {
        "role": "tool",
        "content": "...",
        "name": "tool_b"
    },
    {
        "role": "tool",
        "content": "...",
        "name": "tool_a"
    },
    {
        "role": "assistant",
        "content": "..."
    }
]
```

We assume that in the original trace, both `tool_calls` and `tool` are ordered according to the real invocation and execution time (precisely collected by backend runtime hooks). After linearizing this message list, we obtain the tool-call trace:

**Example 1**
```json
[
    {
        "role": "assistant",
        "tool_calls": [
            {
                "type": "function",
                "function": {
                    "name": "tool_a",
                    "arguments": "{}"
                }
            }
        ]
    },
    {
        "role": "assistant",
        "tool_calls": [
            {
                "type": "function",
                "function": {
                    "name": "tool_b",
                    "arguments": "{}"
                }
            }
        ]
    },
    {
        "role": "tool",
        "content": "...",
        "name": "tool_b"
    },
    {
        "role": "tool",
        "content": "...",
        "name": "tool_a"
    }
]
```

## Abstraction

We define each dictionary in the linearized list as an event. An event is either a tool call (`call`) or a tool return (`return`).
A tool call contains two attributes: tool name (`name`) and tool arguments (`args`).
The tool name is a symbol, for example `call[name] = read`.
Without JSON parsing, tool arguments are a string, for example `call[args] = '{\"path\": \"environment/reports.md\"}'`.
One may also attempt to JSON-parse the tool arguments and further extract their internal attributes, for example `call[args][path] = 'environment/reports.md'`.
We use `call[args][]` to denote the set of attribute symbols of `call[args]`; if it cannot be JSON-parsed or parses to an empty dictionary, then it is the empty set.
When describing strings in attributes, we use single quotes.

A tool return contains two attributes: tool name (`name`) and tool return content (`content`).
The tool name is a symbol, for example `return[name] = read`.
Without JSON parsing, tool return content is a string, and in most cases it is also not parseable. For example, `return[content] = 'hello.'`
But sometimes it can be parsed, for example `return[content] = '{\"path\": \"environment/reports.md\", \"content\": \"hello.\"}'`. In this case, one may attempt to JSON-parse the tool return content and further extract its internal attributes: `return[content][content] = 'hello'`.
We use `return[content][]` to denote the set of attribute symbols of `return[content]`; if it cannot be JSON-parsed or parses to an empty dictionary, then it is the empty set.
Sometimes, after JSON-parsing tool arguments or tool return values, some attribute may be a list or a dict; we need to convert it into a string. Attribute types may only be string, integer, float, or boolean (`TRUE` and `FALSE`).
Types must be clearly distinguished. For example, `'25.2'` is a string, while `25.2` is a float. `'TRUE'` is a string, while `TRUE` is a boolean.


## Symbols

### Logical Operators

* negation (!)
* conjunction (&)
* disjunction (|)
* implication (->)
* exclusive or (xor)
* equivalence by exclusion (xnor)
* equivalence (<->)

### Temporal Operators

* X p is true at time t if p is true at time t + 1.
* F p is true at time t if p is true at some time t' ≥ t.
* G p is true at time t if p is true at all times t' ≥ t.
* p U q is true at time t if q is true at some time t' ≥ t, and for all time t'' (such that t ≤ t'' < t') p is true.
* p V q is true at time t if q holds at all time steps t' ≥ t up to and including the time step t'' where p also holds. Alternatively, it may be the case that p never holds in which case q must hold in all time steps t' ≥ t.
* Y p is true at time t > t0 if p holds at time t − 1. Y p is false at time t0.
* Z p is equivalent to Y p with the exception that the expression is true at time t0.
* H p is true at time t if p holds in all previous time steps t' ≤ t.
* O p is true at time t if p held in at least one of the previous time steps t' ≤ t.
* p S q is true at time t if q held at time t' ≤ t and p holds in all time steps t'' such that t' < t'' ≤ t.
* p T q is true at time t if p held at time t' ≤ t and q holds in all time steps t'' such that t' ≤ t'' ≤ t. Alternatively, if p has never been true, then q must hold in all time steps t'' such that t0 ≤ t'' ≤ t.

### Custom Operators

#### Membership (in): 

* String membership: `'\"path\"' in call[args]`
* Attribute membership: `path in call[args][]`

#### Environment Observers

Since the operators above can only constrain the agent execution trace and cannot constrain the environment state, we introduce 4 read-only tools (`tool`) as environment observers to observe environment state at a certain time and incorporate it into the specification.

* read (read the content of a file in the code repository):

This tool reads a file and returns its content. The code is:
```py
def read(path: str) -> dict:
    if not path:
        return {"success": False, "description": "path is required."}
    try:
        with open(path, "r", encoding="utf-8") as file:
            content = file.read()
    except Exception as error:
        return {"success": False, "description": f"Error: {error}"}
    return {"success": True, "content": content}
```

* glob (find files by pattern matching):

Use glob patterns such as `**/*.js` or `src/**/*.ts` to search for files. Returns matched file paths. The code is:
```py
import glob as _glob
import os

def glob(pattern: str, path: str) -> dict:
    try:
        results = [p for p in _glob.glob(os.path.join(path, pattern), recursive=True)]
    except Exception as error:
        return {"success": False, "description": f"Error: {error}"}
    return {"success": True, "files": results, "count": len(results)}
```

* grep (search file content using regular expressions):

Quickly search content in the environment. Full regular expression syntax and file-pattern filtering are supported. The code is:
```py
import glob as _glob
import re
import os

def grep(pattern: str, path: str, glob_pattern: str) -> dict:
    if not pattern:
        return {"success": False, "description": "pattern is required."}
    try:
        regex = re.compile(pattern)
    except re.error as error:
        return {"success": False, "description": f"Invalid pattern: {error}"}
    if os.path.isfile(path):
        candidates = [path]
    else:
        candidates = [p for p in _glob.glob(os.path.join(path, "**", glob_pattern), recursive=True) if os.path.isfile(p)]
    matches = []
    for candidate in candidates:
        try:
            with open(candidate, "r", encoding="utf-8", errors="replace") as file:
                for number, line in enumerate(file, 1):
                    if regex.search(line):
                        matches.append(f"{candidate}:{number}: {line.rstrip()}")
        except Exception:
            continue
    return {"success": True, "matches": matches, "count": len(matches)}
```

Environment observers are used in specification expressions by placing a Python-compatible function call inside `tool()`, for example `tool(read(path='README.md'))` or `tool(read('README.md'))`. Its return value follows the same protocol as a tool return (`return`), for example: `content in tool(read(path='README.md'))[] & tool(read(path='README.md'))[success] = TRUE`.

* bash (execute a read-only shell command in the environment root directory):

When `read` / `glob` / `grep` cannot express the environmental fact to be observed (for example, internal content of binary artifacts or file attributes), use this tool to execute one read-only shell command. The command's working directory is the environment root directory. The code is:
```py
import subprocess

def bash(command: str) -> dict:
    if not command:
        return {"success": False, "description": "command is required."}
    try:
        process = subprocess.run(command, shell=True, capture_output=True,
                                 text=True, errors="replace", timeout=30)
    except Exception as error:
        return {"success": False, "description": f"Error: {error}"}
    return {"success": process.returncode == 0, "exit_code": process.returncode,
            "output": process.stdout + process.stderr}
```

Usage examples: `tool(bash(command='ls -a'))[success] = TRUE`, `'backup.log' in tool(bash(command='find . -name "*.log"'))[output]`, `tool(bash(command='test -f report.md'))[exit_code] = 0`.

Constraints on the `bash` observer:

* Only read-only commands may be executed (writing, deleting, moving, chmod, and networking are prohibited). During verification, the environment directory is provided in read-only mode, and write operations will fail.
* It must be a single command (pipes may be used), non-interactive, with a timeout of 30 seconds.
* The output must not depend on values that vary across runs (timestamps, pids, random numbers, auto-incrementing ids), otherwise the specification is not reproducible.
* The command must be available both in containers and on macOS: use only POSIX commands and options, and avoid GNU-specific options.

### Others

Parentheses and spaces are supported in expressions.

### Time

We stipulate that at the initial time `t0`, no tool has been called; only at the next time step do agent events begin to occur.
If an LTL formula is true at the initial time `t0`, then it is said to be true.
After linearization, one event occurs at each time step.
If a certain event occurs at a certain time step, then the true expressions related to that event are true at that time step.
After the trace ends, the model stutters in the "no event" state forever, and all event-related atoms are always false.
The environment state may persist across time steps and remains in its final state after the trace ends.