
import ast
import glob as _glob
import json
import os
import re
import subprocess
import tempfile

LTL_TOKENS = {"X", "F", "G", "U", "V", "Y", "Z", "H", "O", "S", "T",
              "xor", "xnor", "TRUE", "FALSE"}

OBSERVER_PARAMS = {
    "read": ["path"],
    "glob": ["pattern", "path"],
    "grep": ["pattern", "path", "glob_pattern"],
    "bash": ["command"],
}


def linearize(response):
    events = []
    for message in response:
        if message.get("role") == "assistant":
            for tool_call in message.get("tool_calls") or []:
                function = tool_call["function"]
                events.append(("call", function["name"], function["arguments"]))
        elif message.get("role") == "tool":
            events.append(("return", message["name"], message["content"]))
    return events


def parse_spec(spec, atom_index):
    n = len(spec)

    def skip_ws(i):
        while i < n and spec[i].isspace():
            i += 1
        return i

    def read_string(i):
        j = spec.index("'", i + 1)
        return spec[i + 1:j], j + 1

    def read_ident(i):
        j = i
        while j < n and (spec[j].isalnum() or spec[j] == "_"):
            j += 1
        return spec[i:j], j

    def read_bracket(i):
        i = skip_ws(i + 1)
        if i < n and spec[i] == "]":
            return None, i + 1
        name, j = read_ident(i)
        j = skip_ws(j)
        if not name or j >= n or spec[j] != "]":
            raise ValueError(f"position {i} has illegal bracket content")
        return name, j + 1

    def read_balanced(i):
        depth, j = 0, i
        while j < n:
            c = spec[j]
            if c in "'\"":
                j = spec.index(c, j + 1)
            elif c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    return spec[i + 1:j], j + 1
            j += 1
        raise ValueError(f"position {i} has unmatched parentheses")

    def read_value(i):
        i = skip_ws(i)
        if i >= n:
            raise ValueError("missing comparison value")
        c = spec[i]
        if c == "'":
            s, j = read_string(i)
            return "str", s, j
        if c.isdigit() or c == "-":
            j = i + 1
            while j < n and (spec[j].isdigit() or spec[j] == "."):
                j += 1
            text = spec[i:j]
            if "." in text:
                return "float", float(text), j
            return "int", int(text), j
        ident, j = read_ident(i)
        if not ident:
            raise ValueError(f"position {i} has an illegal value")
        if ident == "TRUE":
            return "bool", True, j
        if ident == "FALSE":
            return "bool", False, j
        return "sym", ident, j

    def read_term(i):
        i = skip_ws(i)
        ident, j = read_ident(i)
        if ident in ("call", "return"):
            j = skip_ws(j)
            if j >= n or spec[j] != "[":
                raise ValueError(f"{ident} is missing [field]")
            field, j = read_bracket(j)
            valid = ("name", "args") if ident == "call" else ("name", "content")
            if field not in valid:
                raise ValueError(f"{ident}[{field}] is an illegal field")
            sel = None
            if field != "name":
                k = skip_ws(j)
                if k < n and spec[k] == "[":
                    key, j = read_bracket(k)
                    sel = "*" if key is None else key
            return ("event", ident, field, sel), j
        if ident == "tool":
            j = skip_ws(j)
            if j >= n or spec[j] != "(":
                raise ValueError("tool is missing parentheses")
            inner, j = read_balanced(j)
            node = ast.parse(inner.strip(), mode="eval").body
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name) \
                    or node.func.id not in OBSERVER_PARAMS:
                raise ValueError(f"illegal environment observer call: {inner}")
            kwargs = {}
            for param, arg in zip(OBSERVER_PARAMS[node.func.id], node.args):
                kwargs[param] = ast.literal_eval(arg)
            for kw in node.keywords:
                kwargs[kw.arg] = ast.literal_eval(kw.value)
            j = skip_ws(j)
            if j >= n or spec[j] != "[":
                raise ValueError("tool(...) is missing [attr] or []")
            key, j = read_bracket(j)
            sel = "*" if key is None else key
            return ("env", node.func.id, tuple(sorted(kwargs.items())), sel), j
        raise ValueError(f"position {i} is not a valid term")

    def register(op, term, vtype, value):
        if op == "member" and term[3] != "*":
            raise ValueError("attribute membership requires the term to end with []")
        if op != "member" and term[3] == "*":
            raise ValueError("[] can only be used for attribute membership")
        if op == "eq" and term[0] == "event" and term[2] == "name" and vtype != "sym":
            raise ValueError("tool name can only be compared with symbols")
        atom = (op, term, vtype, value)
        if atom not in atom_index:
            atom_index[atom] = len(atom_index)
        return f"p{atom_index[atom]}"

    out = []
    i = 0
    while i < n:
        c = spec[i]
        if c.isspace() or c in "()!&|":
            out.append(c)
            i += 1
        elif spec.startswith("<->", i):
            out.append("<->")
            i += 3
        elif spec.startswith("->", i):
            out.append("->")
            i += 2
        elif c == "'":
            s, j = read_string(i)
            j = skip_ws(j)
            word, j = read_ident(j)
            if word != "in":
                raise ValueError("expected 'in' after string")
            term, i = read_term(j)
            out.append(register("substr", term, "str", s))
        elif c.isalnum() or c == "_":
            ident, j = read_ident(i)
            after = skip_ws(j)
            if ident in ("call", "return") and after < n and spec[after] == "[":
                term, j = read_term(i)
                j = skip_ws(j)
                if j >= n or spec[j] != "=":
                    raise ValueError(f"{ident}[...] is missing =")
                vtype, value, i = read_value(j + 1)
                out.append(register("eq", term, vtype, value))
            elif ident == "tool" and after < n and spec[after] == "(":
                term, j = read_term(i)
                j = skip_ws(j)
                if j >= n or spec[j] != "=":
                    raise ValueError("tool(...)[...] is missing =")
                vtype, value, i = read_value(j + 1)
                out.append(register("eq", term, vtype, value))
            elif ident in LTL_TOKENS:
                out.append(ident)
                i = j
            else:
                word, j2 = read_ident(after)
                if word != "in":
                    raise ValueError(f"unrecognized symbol {ident!r}")
                term, i = read_term(j2)
                out.append(register("member", term, "attr", ident))
        else:
            raise ValueError(f"position {i} has an illegal character {c!r}")
    return "".join(out)


def _compare(op, vtype, expected, actual):
    if isinstance(actual, (list, dict)):
        actual = json.dumps(actual, ensure_ascii=False)
    if op == "substr":
        return isinstance(actual, str) and expected in actual
    if vtype == "bool":
        return isinstance(actual, bool) and actual == expected
    if vtype == "int":
        return isinstance(actual, int) and not isinstance(actual, bool) and actual == expected
    if vtype == "float":
        return isinstance(actual, float) and actual == expected
    if vtype == "str":
        return isinstance(actual, str) and actual == expected
    return False


def eval_event_atom(atom, event):
    op, (_, side, field, sel), vtype, value = atom
    kind, name, payload = event
    if kind != side:
        return False
    if field == "name":
        return name == value
    if sel is None:
        if op == "eq":
            return vtype == "str" and payload == value
        return op == "substr" and value in payload
    try:
        parsed = json.loads(payload)
    except Exception:
        parsed = None
    if not isinstance(parsed, dict):
        return False
    if sel == "*":
        return value in parsed
    if sel not in parsed:
        return False
    return _compare(op, vtype, value, parsed[sel])


def _under(base, path):
    return path if os.path.isabs(path) else os.path.join(base, path)


def _relative(base, path):
    prefix = base if base.endswith(os.sep) else base + os.sep
    return path[len(prefix):] if path.startswith(prefix) else path


def _obs_read(base, path=""):
    if not path:
        return {"success": False, "description": "path is required."}
    target = _under(base, path)
    try:
        with open(target, "r", encoding="utf-8") as file:
            content = file.read()
    except Exception as error:
        return {"success": False, "description": f"Error: {str(error).replace(target, path)}"}
    return {"success": True, "content": content}


def _obs_glob(base, pattern="", path=""):
    try:
        results = [
            _relative(base, p)
            for p in _glob.glob(os.path.join(_under(base, path), pattern), recursive=True)
        ]
    except Exception as error:
        return {"success": False, "description": f"Error: {error}"}
    return {"success": True, "files": results, "count": len(results)}


def _obs_grep(base, pattern="", path="", glob_pattern=""):
    if not pattern:
        return {"success": False, "description": "pattern is required."}
    try:
        regex = re.compile(pattern)
    except re.error as error:
        return {"success": False, "description": f"Invalid pattern: {error}"}
    target = _under(base, path)
    if os.path.isfile(target):
        candidates = [target]
    else:
        candidates = [p for p in _glob.glob(os.path.join(target, "**", glob_pattern), recursive=True) if os.path.isfile(p)]
    matches = []
    for candidate in candidates:
        try:
            with open(candidate, "r", encoding="utf-8", errors="replace") as file:
                for number, line in enumerate(file, 1):
                    if regex.search(line):
                        matches.append(f"{_relative(base, candidate)}:{number}: {line.rstrip()}")
        except Exception:
            continue
    return {"success": True, "matches": matches, "count": len(matches)}


def _obs_bash(base, command=""):
    if not command:
        return {"success": False, "description": "command is required."}
    try:
        process = subprocess.run(command, shell=True, cwd=base, capture_output=True,
                                 text=True, errors="replace", timeout=30)
    except Exception as error:
        return {"success": False, "description": f"Error: {error}"}
    return {"success": process.returncode == 0, "exit_code": process.returncode,
            "output": process.stdout + process.stderr}


OBSERVERS = {"read": _obs_read, "glob": _obs_glob, "grep": _obs_grep, "bash": _obs_bash}


def eval_env_atom(atom, env_dir, cache):
    op, (_, func, args, sel), vtype, value = atom
    key = (func, args)
    if key not in cache:
        cache[key] = OBSERVERS[func](env_dir, **dict(args))
    result = cache[key]
    if sel == "*":
        return value in result
    if sel not in result:
        return False
    return _compare(op, vtype, value, result[sel])


def build_model(events, atom_index, ltl_specs, env_dir):
    sink = len(events) + 1
    obs_cache = {}
    lines = [
        "MODULE main",
        "VAR",
        f"    t : 0..{sink};",
        "ASSIGN",
        "    init(t) := 0;",
        f"    next(t) := case t < {sink} : t + 1; TRUE : t; esac;",
        "DEFINE",
    ]
    for atom, idx in atom_index.items():
        if atom[1][0] == "env":
            expr = "TRUE" if eval_env_atom(atom, env_dir, obs_cache) else "FALSE"
        else:
            times = [i + 1 for i, event in enumerate(events) if eval_event_atom(atom, event)]
            expr = " | ".join(f"(t = {time})" for time in times) or "FALSE"
        lines.append(f"    p{idx} := {expr};")
    for ltl in ltl_specs:
        lines.append(f"LTLSPEC {ltl}")
    return "\n".join(lines) + "\n"


def verify_task(response, specs, env_dir, nuxmv_bin, timeout=60):
    events = linearize(response)
    atom_index = {}
    results = [None] * len(specs)
    compiled = []
    for pos, spec in enumerate(specs):
        try:
            compiled.append((pos, parse_spec(spec, atom_index)))
        except Exception as error:
            results[pos] = f"error: {error}"

    model = build_model(events, atom_index, [ltl for _, ltl in compiled], env_dir)
    output = ""
    if compiled:
        script = "go\n" + "".join(f"check_ltlspec -n {i}\n" for i in range(len(compiled))) + "quit\n"
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "task.xmv")
            with open(path, "w", encoding="utf-8") as file:
                file.write(model)
            try:
                process = subprocess.run([nuxmv_bin, "-int", path], input=script,
                                         capture_output=True, text=True, timeout=timeout)
                output = (process.stdout or "") + (process.stderr or "")
            except subprocess.TimeoutExpired:
                output = "nuXmv timeout"
        verdicts = re.findall(r"-- specification .* is (true|false)\s*$", output, re.MULTILINE)
        if len(verdicts) == len(compiled):
            for (pos, _), verdict in zip(compiled, verdicts):
                results[pos] = "sat" if verdict == "true" else "unsat"
        else:
            for pos, _ in compiled:
                results[pos] = f"error: nuXmv output anomaly ({len(verdicts)}/{len(compiled)}  results)"
    return {"results": results, "model": model, "output": output}
