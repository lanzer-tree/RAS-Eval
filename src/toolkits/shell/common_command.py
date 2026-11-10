
import bz2
import datetime as dt
import difflib
import getpass
import grp
import gzip as gziplib
import hashlib
import os
import platform
import pwd as pwdlib
import re
import shutil
import signal
import socket
import stat as statmod
import string
import sys
import tarfile
import tempfile
import time
import zipfile

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------

_TR_CLASSES = {
    "alpha": string.ascii_letters,
    "digit": string.digits,
    "alnum": string.ascii_letters + string.digits,
    "lower": string.ascii_lowercase,
    "upper": string.ascii_uppercase,
    "space": " \t\n\r\v\f",
    "blank": " \t",
    "punct": string.punctuation,
    "print": string.printable[:-5],
    "graph": string.printable[:-6],
    "cntrl": "".join(chr(c) for c in list(range(32)) + [127]),
    "xdigit": string.hexdigits,
}

_ESCAPES = {"n": "\n", "t": "\t", "r": "\r", "v": "\v", "f": "\f", "b": "\b", "a": "\a", "0": "\0", "\\": "\\"}


def _as_list(paths):
    if paths is None:
        return []
    if isinstance(paths, str):
        return [paths]
    return list(paths)


def _read_text(paths=None):
    files = _as_list(paths)
    if not files:
        return sys.stdin.read()
    chunks = []
    for path in files:
        if path == "-":
            chunks.append(sys.stdin.read())
            continue
        try:
            with open(path, "r", errors="replace") as f:
                chunks.append(f.read())
        except IsADirectoryError:
            print(f"{path}: Is a directory", file=sys.stderr)
        except OSError as exc:
            print(f"{path}: {exc.strerror}", file=sys.stderr)
    return "".join(chunks)


def _read_lines(paths=None):
    return _read_text(paths).splitlines(keepends=True)


def _read_bytes(path=None):
    if path is None or path == "-":
        return sys.stdin.buffer.read()
    with open(path, "rb") as f:
        return f.read()


def _show_nonprinting(text):
    out = []
    for ch in text:
        code = ord(ch)
        if ch in "\t\n":
            out.append(ch)
        elif code == 127:
            out.append("^?")
        elif code < 32:
            out.append(f"^{chr(code + 64)}")
        elif code < 128:
            out.append(ch)
        elif code == 255:
            out.append("M-^?")
        elif code < 160:
            out.append(f"M-^{chr(code - 128 + 64)}")
        elif code < 256:
            out.append(f"M-{chr(code - 128)}")
        else:
            out.append(ch)
    return "".join(out)


def _parse_ranges(spec, length):
    picked = set()
    for part in str(spec).split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            low, _, high = part.partition("-")
            start = int(low) if low else 1
            end = int(high) if high else length
        else:
            start = end = int(part)
        picked.update(range(max(start, 1), min(end, length) + 1))
    return sorted(picked)


def _expand_set(spec):
    out = []
    i = 0
    while i < len(spec):
        if spec.startswith("[:", i) and spec.find(":]", i) > 0:
            end = spec.find(":]", i)
            out.append(_TR_CLASSES.get(spec[i + 2 : end], ""))
            i = end + 2
        elif spec[i] == "\\" and i + 1 < len(spec):
            out.append(_ESCAPES.get(spec[i + 1], spec[i + 1]))
            i += 2
        elif i + 2 < len(spec) and spec[i + 1] == "-":
            out.append("".join(chr(c) for c in range(ord(spec[i]), ord(spec[i + 2]) + 1)))
            i += 3
        else:
            out.append(spec[i])
            i += 1
    return "".join(out)


def _unescape(text):
    out = []
    i = 0
    while i < len(text):
        if text[i] == "\\" and i + 1 < len(text):
            out.append(_ESCAPES.get(text[i + 1], "\\" + text[i + 1]))
            i += 2
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def _human(size):
    value = float(size)
    for unit in ("", "K", "M", "G", "T", "P"):
        if value < 1024 or unit == "P":
            if unit == "":
                return f"{int(value)}"
            return f"{value:.1f}{unit}" if value < 10 else f"{round(value)}{unit}"
        value /= 1024
    return f"{int(value)}"


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------


def cat(files=None, n=False, b=False, s=False, E=False, T=False, v=False):
    out = []
    number = 1
    prev_blank = False
    for line in _read_lines(files):
        content = line.rstrip("\n")
        is_blank = content == ""
        if s and is_blank and prev_blank:
            continue
        prev_blank = is_blank
        if v:
            content = _show_nonprinting(content)
        if T:
            content = content.replace("\t", "^I")
        if E:
            content += "$"
        prefix = ""
        if b:
            if not is_blank:
                prefix = f"{number:6d}\t"
                number += 1
        elif n:
            prefix = f"{number:6d}\t"
            number += 1
        out.append(prefix + content + "\n")
    return "".join(out)


def tac(files=None):
    lines = [line.rstrip("\n") for line in _read_lines(files)]
    return "".join(line + "\n" for line in reversed(lines))


def nl(files=None, b="t", w=6, s="\t"):
    out = []
    number = 1
    for line in _read_lines(files):
        content = line.rstrip("\n")
        numbered = b == "a" or (b == "t" and content.strip() != "")
        if b != "n" and numbered:
            out.append(f"{number:>{w}}{s}{content}\n")
            number += 1
        else:
            out.append(" " * w + " " * len(s) + content + "\n")
    return "".join(out)


def head(files=None, n=10, c=None, q=False, v=False):
    paths = _as_list(files)
    show_header = v or (len(paths) > 1 and not q)
    if not paths:
        paths = [None]
    out = []
    for index, path in enumerate(paths):
        if show_header:
            out.append(("\n" if index else "") + f"==> {path} <==\n")
        if c is not None:
            out.append(_read_text(path)[:c])
        else:
            out.extend(_read_lines(path)[:n])
    return "".join(out)


def tail(files=None, n=10, c=None, q=False, v=False):
    paths = _as_list(files)
    show_header = v or (len(paths) > 1 and not q)
    if not paths:
        paths = [None]
    out = []
    for index, path in enumerate(paths):
        if show_header:
            out.append(("\n" if index else "") + f"==> {path} <==\n")
        if c is not None:
            out.append(_read_text(path)[-c:])
            continue
        lines = _read_lines(path)
        if isinstance(n, str) and n.startswith("+"):
            out.extend(lines[int(n[1:]) - 1 :])
        else:
            count = int(n)
            out.extend(lines[-count:] if count else [])
    return "".join(out)


def wc(files=None, l=False, w=False, c=False, m=False, L=False):
    if not (l or w or c or m or L):
        l = w = c = True
    paths = _as_list(files)
    totals = [0, 0, 0, 0, 0]
    out = []
    for path in paths or [None]:
        text = _read_text(path)
        counts = [
            text.count("\n"),
            len(text.split()),
            len(text.encode()),
            len(text),
            max((len(line) for line in text.splitlines()), default=0),
        ]
        totals = [a + b for a, b in zip(totals, counts)]
        totals[4] = max(totals[4], counts[4])
        fields = [counts[i] for i, flag in enumerate((l, w, c, m, L)) if flag]
        out.append("".join(f"{value:8d}" for value in fields) + (f" {path}" if path else "") + "\n")
    if len(paths) > 1:
        fields = [totals[i] for i, flag in enumerate((l, w, c, m, L)) if flag]
        out.append("".join(f"{value:8d}" for value in fields) + " total\n")
    return "".join(out)


def cut(files=None, d="\t", f=None, c=None, b=None, s=False, output_delimiter=None):
    sep = output_delimiter if output_delimiter is not None else d
    out = []
    for line in _read_lines(files):
        content = line.rstrip("\n")
        if f is not None:
            if d not in content:
                if not s:
                    out.append(content + "\n")
                continue
            parts = content.split(d)
            picked = _parse_ranges(f, len(parts))
            out.append(sep.join(parts[i - 1] for i in picked) + "\n")
        elif c is not None:
            picked = _parse_ranges(c, len(content))
            out.append("".join(content[i - 1] for i in picked) + "\n")
        elif b is not None:
            raw = content.encode()
            picked = _parse_ranges(b, len(raw))
            out.append(bytes(raw[i - 1] for i in picked).decode(errors="replace") + "\n")
        else:
            out.append(content + "\n")
    return "".join(out)


def paste(files=None, d="\t", s=False):
    paths = _as_list(files)
    columns = []
    for path in paths or [None]:
        columns.append([line.rstrip("\n") for line in _read_lines(path)])
    delims = _unescape(d) or "\t"
    if s:
        return "".join(delims[0].join(col) + "\n" for col in columns)
    height = max((len(col) for col in columns), default=0)
    out = []
    for row in range(height):
        cells = [col[row] if row < len(col) else "" for col in columns]
        line = cells[0]
        for index, cell in enumerate(cells[1:]):
            line += delims[index % len(delims)] + cell
        out.append(line + "\n")
    return "".join(out)


def sort(files=None, n=False, r=False, u=False, k=None, t=None, f=False, b=False, o=None):
    lines = [line.rstrip("\n") for line in _read_lines(files)]
    decorated = []
    for line in lines:
        field = line
        if k is not None:
            parts = line.split(t) if t else line.split()
            index = int(str(k).split(",")[0]) - 1
            field = parts[index] if 0 <= index < len(parts) else ""
        if b:
            field = field.strip()
        if f:
            field = field.lower()
        if n:
            match = re.match(r"\s*[-+]?(\d+\.?\d*|\.\d+)", field)
            key = float(match.group()) if match else 0.0
        else:
            key = field
        decorated.append((key, line))
    decorated.sort(key=lambda item: item[0], reverse=r)
    out = []
    seen = set()
    for key, line in decorated:
        if u:
            if key in seen:
                continue
            seen.add(key)
        out.append(line + "\n")
    text = "".join(out)
    if o:
        with open(o, "w") as handle:
            handle.write(text)
        return ""
    return text


def uniq(files=None, c=False, d=False, u=False, i=False, f=0, s=0, w=None):
    groups = []
    for line in _read_lines(files):
        content = line.rstrip("\n")
        key = content
        if f:
            parts = key.split()
            key = " ".join(parts[f:])
        key = key[s:]
        if w is not None:
            key = key[:w]
        if i:
            key = key.lower()
        if groups and groups[-1][0] == key:
            groups[-1][2] += 1
        else:
            groups.append([key, content, 1])
    out = []
    for _, content, count in groups:
        if d and count < 2:
            continue
        if u and count > 1:
            continue
        out.append(f"{count:7d} {content}\n" if c else content + "\n")
    return "".join(out)


def tr(set1, set2=None, d=False, s=False, c=False):
    source = _expand_set(set1)
    target = _expand_set(set2) if set2 else ""
    text = sys.stdin.read()
    if c:
        source = "".join(chr(code) for code in range(256) if chr(code) not in source)
    if d:
        text = "".join(ch for ch in text if ch not in source)
        squeeze_set = target
    else:
        if target:
            padded = target + target[-1] * (len(source) - len(target))
            text = text.translate(str.maketrans(source, padded[: len(source)]))
        squeeze_set = target or source
    if s and squeeze_set:
        out = []
        for ch in text:
            if out and ch == out[-1] and ch in squeeze_set:
                continue
            out.append(ch)
        text = "".join(out)
    return text


def grep(pattern, files=None, i=False, v=False, n=False, c=False, l=False, r=False, E=False, F=False, w=False, x=False, o=False, h=False, H=False, A=0, B=0, C=0, include=None):
    if C:
        A = A or C
        B = B or C
    expr = re.escape(pattern) if F else pattern
    if w:
        expr = rf"\b(?:{expr})\b"
    if x:
        expr = rf"^(?:{expr})$"
    regex = re.compile(expr, re.IGNORECASE if i else 0)
    targets = []
    for path in _as_list(files) or [None]:
        if path is not None and os.path.isdir(path):
            if not r:
                print(f"grep: {path}: Is a directory", file=sys.stderr)
                continue
            for root, _, names in os.walk(path):
                for name in sorted(names):
                    if include is None or _fnmatch(name, include):
                        targets.append(os.path.join(root, name))
        else:
            targets.append(path)
    prefix = H or (len(targets) > 1 and not h)
    out = []
    for path in targets:
        lines = [line.rstrip("\n") for line in _read_lines(path)]
        hits = [index for index, line in enumerate(lines) if bool(regex.search(line)) != v]
        if l:
            if hits:
                out.append(f"{path}\n")
            continue
        if c:
            out.append((f"{path}:" if prefix else "") + f"{len(hits)}\n")
            continue
        wanted = set()
        for index in hits:
            wanted.update(range(max(index - B, 0), min(index + A + 1, len(lines))))
        previous = None
        for index in sorted(wanted):
            if (A or B) and previous is not None and index != previous + 1:
                out.append("--\n")
            previous = index
            head_part = f"{path}:" if prefix else ""
            if n:
                head_part += f"{index + 1}:"
            if o:
                for match in regex.findall(lines[index]):
                    out.append(head_part + (match if isinstance(match, str) else match[0]) + "\n")
            else:
                out.append(head_part + lines[index] + "\n")
    return "".join(out)


def egrep(pattern, files=None, **kwargs):
    return grep(pattern, files, E=True, **kwargs)


def fgrep(pattern, files=None, **kwargs):
    return grep(pattern, files, F=True, **kwargs)


def _fnmatch(name, pattern):
    expr = re.escape(pattern).replace(r"\*", "[^/]*").replace(r"\?", "[^/]").replace(r"\[", "[").replace(r"\]", "]")
    return re.fullmatch(expr, name) is not None


def _sed_addr_match(addr, lineno, line, total):
    if addr is None:
        return True
    if addr == "$":
        return lineno == total
    if addr.startswith("/"):
        return re.search(addr[1:-1], line) is not None
    return lineno == int(addr)


def _sed_selected(cmd, lineno, line, total):
    first, second = cmd[0], cmd[1]
    if first is None:
        return True
    if second is None:
        return _sed_addr_match(first, lineno, line, total)
    if cmd[6]:
        if _sed_addr_match(second, lineno, line, total):
            cmd[6] = False
        return True
    if _sed_addr_match(first, lineno, line, total):
        numeric_end = not second.startswith("/") and second != "$"
        cmd[6] = not (numeric_end and int(second) <= lineno)
        return True
    return False


def sed(script, files=None, n=False, i=False):
    if i:
        for path in _as_list(files):
            text = sed(script, path, n=n)
            with open(path, "w") as handle:
                handle.write(text)
        return ""
    parsed = []
    for cmd in [script] if isinstance(script, str) else list(script):
        match = re.match(r"^\s*(\$|\d+|/(?:\\.|[^/])*/)?(?:,(\$|\d+|/(?:\\.|[^/])*/))?\s*([sdpq])(.*)$", cmd)
        if not match:
            raise ValueError(f"sed: unsupported script: {cmd}")
        first, second, action, body = match.groups()
        pattern = replacement = ""
        flags = ""
        if action == "s":
            delim = body[0]
            fields = re.split(rf"(?<!\\){re.escape(delim)}", body)
            pattern, replacement = fields[1], fields[2]
            flags = fields[3] if len(fields) > 3 else ""
        parsed.append([first, second, action, pattern, replacement, flags, False])
    lines = [line.rstrip("\n") for line in _read_lines(files)]
    total = len(lines)
    out = []
    for lineno, line in enumerate(lines, 1):
        extra = []
        deleted = False
        stop = False
        for cmd in parsed:
            if not _sed_selected(cmd, lineno, line, total):
                continue
            if cmd[2] == "s":
                count = 0 if "g" in cmd[5] else 1
                reflags = re.IGNORECASE if ("i" in cmd[5] or "I" in cmd[5]) else 0
                line = re.sub(cmd[3], cmd[4].replace("\\n", "\n"), line, count=count, flags=reflags)
            elif cmd[2] == "d":
                deleted = True
                break
            elif cmd[2] == "p":
                extra.append(line)
            elif cmd[2] == "q":
                stop = True
        if not deleted:
            out.extend(item + "\n" for item in extra)
            if not n:
                out.append(line + "\n")
        if stop:
            break
    return "".join(out)


def comm(file1, file2, one=False, two=False, three=False):
    left = [line.rstrip("\n") for line in _read_lines(file1)]
    right = [line.rstrip("\n") for line in _read_lines(file2)]
    out = []
    i = j = 0
    while i < len(left) or j < len(right):
        if j >= len(right) or (i < len(left) and left[i] < right[j]):
            if not one:
                out.append(left[i] + "\n")
            i += 1
        elif i >= len(left) or right[j] < left[i]:
            if not two:
                out.append(("" if one else "\t") + right[j] + "\n")
            j += 1
        else:
            if not three:
                prefix = "" if one and two else ("\t" if one or two else "\t\t")
                out.append(prefix + left[i] + "\n")
            i += 1
            j += 1
    return "".join(out)


def join(file1, file2, one=1, two=1, t=None):
    sep = t or " "
    rows2 = {}
    for line in _read_lines(file2):
        parts = line.rstrip("\n").split(t) if t else line.split()
        if parts:
            rows2.setdefault(parts[two - 1], []).append(parts)
    out = []
    for line in _read_lines(file1):
        parts = line.rstrip("\n").split(t) if t else line.split()
        if not parts:
            continue
        key = parts[one - 1]
        rest1 = [value for index, value in enumerate(parts) if index != one - 1]
        for other in rows2.get(key, []):
            rest2 = [value for index, value in enumerate(other) if index != two - 1]
            out.append(sep.join([key] + rest1 + rest2) + "\n")
    return "".join(out)


def look(pattern, file="/usr/share/dict/words", f=False):
    target = pattern.lower() if f else pattern
    out = []
    for line in _read_lines(file):
        content = line.rstrip("\n")
        probe = content.lower() if f else content
        if probe.startswith(target):
            out.append(content + "\n")
    return "".join(out)


def col(files=None, b=False, x=False):
    out = []
    for line in _read_lines(files):
        content = line.rstrip("\n")
        if b:
            buffer = []
            for ch in content:
                if ch == "\b":
                    if buffer:
                        buffer.pop()
                else:
                    buffer.append(ch)
            content = "".join(buffer)
        if x:
            content = content.expandtabs(8)
        out.append(content + "\n")
    return "".join(out)


def colrm(start=None, stop=None, files=None):
    out = []
    for line in _read_lines(files):
        content = line.rstrip("\n")
        if start is None:
            out.append(content + "\n")
        elif stop is None:
            out.append(content[: start - 1] + "\n")
        else:
            out.append(content[: start - 1] + content[stop:] + "\n")
    return "".join(out)


def fmt(files=None, w=75):
    out = []
    paragraph = []
    for line in _read_lines(files) + ["\n"]:
        content = line.strip()
        if content:
            paragraph.append(content)
            continue
        if paragraph:
            words = " ".join(paragraph).split()
            current = ""
            for word in words:
                if current and len(current) + 1 + len(word) > w:
                    out.append(current + "\n")
                    current = word
                else:
                    current = f"{current} {word}" if current else word
            if current:
                out.append(current + "\n")
            paragraph = []
    return "".join(out)


def fold(files=None, w=80, s=False, b=False):
    out = []
    for line in _read_lines(files):
        content = line.rstrip("\n")
        if b:
            content = content.encode(errors="replace").decode("latin-1")
        while len(content) > w:
            cut_at = w
            if s:
                space = content.rfind(" ", 0, w + 1)
                if space > 0:
                    cut_at = space + 1
            out.append(content[:cut_at] + "\n")
            content = content[cut_at:]
        out.append(content + "\n")
    return "".join(out)


def expand(files=None, tabs=8):
    return "".join(line.expandtabs(tabs) for line in _read_lines(files))


def unexpand(files=None, tabs=8, a=False):
    out = []
    for line in _read_lines(files):
        content = line.rstrip("\n")
        indent = len(content) - len(content.lstrip(" "))
        converted = "\t" * (indent // tabs) + " " * (indent % tabs) + content[indent:]
        if a:
            converted = re.sub(" {%d,}" % tabs, lambda m: "\t" * (len(m.group()) // tabs) + " " * (len(m.group()) % tabs), converted)
        out.append(converted + "\n")
    return "".join(out)


def rev(files=None):
    return "".join(line.rstrip("\n")[::-1] + "\n" for line in _read_lines(files))


def strings(file=None, n=4):
    data = _read_bytes(file)
    found = re.findall(rb"[\x20-\x7e]{%d,}" % n, data)
    return "".join(item.decode() + "\n" for item in found)


def od(file=None, c=False, b=False, x=False, A="o"):
    data = _read_bytes(file)
    out = []
    for offset in range(0, len(data), 16):
        chunk = data[offset : offset + 16]
        if A == "n":
            label = ""
        elif A == "x":
            label = f"{offset:07x} "
        elif A == "d":
            label = f"{offset:07d} "
        else:
            label = f"{offset:07o} "
        if c:
            cells = []
            for byte in chunk:
                named = {0: "\\0", 7: "\\a", 8: "\\b", 9: "\\t", 10: "\\n", 11: "\\v", 12: "\\f", 13: "\\r"}
                cells.append(named.get(byte, chr(byte) if 32 <= byte < 127 else f"{byte:03o}"))
            body = " ".join(f"{cell:>3}" for cell in cells)
        elif b:
            body = " ".join(f"{byte:03o}" for byte in chunk)
        elif x:
            body = " ".join(f"{int.from_bytes(chunk[i : i + 2], 'little'):04x}" for i in range(0, len(chunk), 2))
        else:
            body = " ".join(f"{int.from_bytes(chunk[i : i + 2], 'little'):06o}" for i in range(0, len(chunk), 2))
        out.append(label + body + "\n")
    if A != "n":
        out.append(f"{len(data):07{'x' if A == 'x' else ('d' if A == 'd' else 'o')}}\n")
    return "".join(out)


def cmp(file1, file2, l=False, s=False):
    left = _read_bytes(file1)
    right = _read_bytes(file2)
    if left == right or s:
        return ""
    out = []
    for index in range(min(len(left), len(right))):
        if left[index] != right[index]:
            if l:
                out.append(f"{index + 1:>6} {left[index]:o} {right[index]:o}\n")
                continue
            line = left[: index + 1].count(b"\n") + 1
            return f"{file1} {file2} differ: char {index + 1}, line {line}\n"
    if not l and len(left) != len(right):
        shorter = file1 if len(left) < len(right) else file2
        return f"cmp: EOF on {shorter}\n"
    return "".join(out)


def diff(file1, file2, u=False, i=False, w=False, q=False, context=3):
    left = [line.rstrip("\n") for line in _read_lines(file1)]
    right = [line.rstrip("\n") for line in _read_lines(file2)]
    norm_left = list(left)
    norm_right = list(right)
    if i:
        norm_left = [line.lower() for line in norm_left]
        norm_right = [line.lower() for line in norm_right]
    if w:
        norm_left = [re.sub(r"\s+", "", line) for line in norm_left]
        norm_right = [re.sub(r"\s+", "", line) for line in norm_right]
    if norm_left == norm_right:
        return ""
    if q:
        return f"Files {file1} and {file2} differ\n"
    if u:
        lines = difflib.unified_diff(
            [line + "\n" for line in left],
            [line + "\n" for line in right],
            fromfile=file1,
            tofile=file2,
            n=context,
        )
        return "".join(lines)
    out = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, norm_left, norm_right).get_opcodes():
        if tag == "equal":
            continue
        left_range = f"{i1 + 1}" if i2 - i1 == 1 else f"{i1 + 1},{i2}"
        right_range = f"{j1 + 1}" if j2 - j1 == 1 else f"{j1 + 1},{j2}"
        if tag == "replace":
            out.append(f"{left_range}c{right_range}\n")
            out.extend(f"< {line}\n" for line in left[i1:i2])
            out.append("---\n")
            out.extend(f"> {line}\n" for line in right[j1:j2])
        elif tag == "delete":
            out.append(f"{left_range}d{j1}\n")
            out.extend(f"< {line}\n" for line in left[i1:i2])
        else:
            out.append(f"{i1}a{right_range}\n")
            out.extend(f"> {line}\n" for line in right[j1:j2])
    return "".join(out)


def split(file=None, prefix="x", l=1000, b=None, d=False, a=2):
    alphabet = string.digits if d else string.ascii_lowercase
    index = 0
    if b is not None:
        data = _read_bytes(file)
        chunks = [data[start : start + b] for start in range(0, len(data), b)]
        for chunk in chunks:
            suffix = ""
            number = index
            for _ in range(a):
                suffix = alphabet[number % len(alphabet)] + suffix
                number //= len(alphabet)
            with open(prefix + suffix, "wb") as handle:
                handle.write(chunk)
            index += 1
        return ""
    lines = _read_lines(file)
    for start in range(0, len(lines), l):
        suffix = ""
        number = index
        for _ in range(a):
            suffix = alphabet[number % len(alphabet)] + suffix
            number //= len(alphabet)
        with open(prefix + suffix, "w") as handle:
            handle.write("".join(lines[start : start + l]))
        index += 1
    return ""


def tee(files=None, a=False, text=None):
    content = sys.stdin.read() if text is None else text
    for path in _as_list(files):
        with open(path, "a" if a else "w") as handle:
            handle.write(content)
    return content


_CKSUM_TABLE = []
for _byte in range(256):
    _crc = _byte << 24
    for _ in range(8):
        _crc = ((_crc << 1) ^ 0x04C11DB7) & 0xFFFFFFFF if _crc & 0x80000000 else (_crc << 1) & 0xFFFFFFFF
    _CKSUM_TABLE.append(_crc)


def cksum(files=None):
    out = []
    for path in _as_list(files) or [None]:
        data = _read_bytes(path)
        crc = 0
        for byte in data:
            crc = ((crc << 8) & 0xFFFFFFFF) ^ _CKSUM_TABLE[((crc >> 24) ^ byte) & 0xFF]
        length = len(data)
        while length:
            crc = ((crc << 8) & 0xFFFFFFFF) ^ _CKSUM_TABLE[((crc >> 24) ^ (length & 0xFF)) & 0xFF]
            length >>= 8
        out.append(f"{~crc & 0xFFFFFFFF} {len(data)}" + (f" {path}" if path else "") + "\n")
    return "".join(out)


def sum_(files=None):
    out = []
    for path in _as_list(files) or [None]:
        data = _read_bytes(path)
        checksum = 0
        for byte in data:
            checksum = (checksum >> 1) + ((checksum & 1) << 15)
            checksum = (checksum + byte) & 0xFFFF
        blocks = (len(data) + 1023) // 1024
        out.append(f"{checksum:05d} {blocks:5d}" + (f" {path}" if path else "") + "\n")
    return "".join(out)


def md5sum(files=None):
    out = []
    for path in _as_list(files) or [None]:
        digest = hashlib.md5(_read_bytes(path)).hexdigest()
        out.append(f"{digest}  {path if path else '-'}\n")
    return "".join(out)


def sha256sum(files=None):
    out = []
    for path in _as_list(files) or [None]:
        digest = hashlib.sha256(_read_bytes(path)).hexdigest()
        out.append(f"{digest}  {path if path else '-'}\n")
    return "".join(out)


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------


def ls(paths=".", l=False, a=False, A=False, R=False, t=False, S=False, r=False, h=False, d=False, one=False, i=False, F=False):
    targets = _as_list(paths) or ["."]
    out = []
    queue = []
    for target in targets:
        if d or not os.path.isdir(target):
            out.append(_ls_entry(target, os.path.basename(target.rstrip("/")) or target, l, h, i, F) + "\n")
        else:
            queue.append(target)
    for index, directory in enumerate(queue):
        if len(targets) > 1 or index:
            out.append(("\n" if out or index else "") + f"{directory}:\n")
        try:
            names = os.listdir(directory)
        except OSError as exc:
            print(f"ls: {directory}: {exc.strerror}", file=sys.stderr)
            continue
        if a:
            names += [".", ".."]
        elif not A:
            names = [name for name in names if not name.startswith(".")]
        if t:
            names.sort(key=lambda name: -os.lstat(os.path.join(directory, name)).st_mtime)
        elif S:
            names.sort(key=lambda name: -os.lstat(os.path.join(directory, name)).st_size)
        else:
            names.sort()
        if r:
            names.reverse()
        if l:
            total = sum(os.lstat(os.path.join(directory, name)).st_blocks for name in names if os.path.lexists(os.path.join(directory, name)))
            out.append(f"total {total}\n")
        for name in names:
            out.append(_ls_entry(os.path.join(directory, name), name, l, h, i, F) + "\n")
        if R:
            for name in names:
                full = os.path.join(directory, name)
                if name not in (".", "..") and os.path.isdir(full) and not os.path.islink(full):
                    queue.append(full)
    return "".join(out)


def _ls_entry(path, name, l=False, h=False, i=False, F=False):
    label = name
    if F and os.path.isdir(path):
        label += "/"
    elif F and os.path.isfile(path) and os.access(path, os.X_OK):
        label += "*"
    if not (l or i):
        return label
    try:
        info = os.lstat(path)
    except OSError as exc:
        print(f"ls: {path}: {exc.strerror}", file=sys.stderr)
        return label
    prefix = f"{info.st_ino} " if i else ""
    if not l:
        return prefix + label
    mode = statmod.filemode(info.st_mode)
    owner = pwdlib.getpwuid(info.st_uid).pw_name if _user_exists(info.st_uid) else str(info.st_uid)
    group = grp.getgrgid(info.st_gid).gr_name if _group_exists(info.st_gid) else str(info.st_gid)
    size = _human(info.st_size) if h else str(info.st_size)
    stamp = time.strftime("%b %e %H:%M", time.localtime(info.st_mtime))
    if statmod.S_ISLNK(info.st_mode):
        label += " -> " + os.readlink(path)
    return f"{prefix}{mode} {info.st_nlink:3d} {owner} {group} {size:>8} {stamp} {label}"


def _user_exists(uid):
    try:
        pwdlib.getpwuid(uid)
        return True
    except KeyError:
        return False


def _group_exists(gid):
    try:
        grp.getgrgid(gid)
        return True
    except KeyError:
        return False


def find(path=".", name=None, iname=None, type=None, maxdepth=None, mindepth=None, size=None, mtime=None, newer=None, empty=False, path_pattern=None, regex=None):
    roots = _as_list(path) or ["."]
    results = []
    stack = [(root, 0) for root in reversed(roots)]
    while stack:
        current, depth = stack.pop()
        if not os.path.lexists(current):
            print(f"find: {current}: No such file or directory", file=sys.stderr)
            continue
        if _find_match(current, depth, name, iname, type, mindepth, size, mtime, newer, empty, path_pattern, regex):
            results.append(current)
        if os.path.isdir(current) and not os.path.islink(current) and (maxdepth is None or depth < maxdepth):
            try:
                children = sorted(os.listdir(current), reverse=True)
            except OSError as exc:
                print(f"find: {current}: {exc.strerror}", file=sys.stderr)
                continue
            stack.extend((os.path.join(current, child), depth + 1) for child in children)
    return "".join(item + "\n" for item in results)


def _find_match(current, depth, name, iname, kind, mindepth, size, mtime, newer, empty, path_pattern, regex):
    base = os.path.basename(current.rstrip("/")) or current
    if mindepth is not None and depth < mindepth:
        return False
    if name is not None and not _fnmatch(base, name):
        return False
    if iname is not None and not _fnmatch(base.lower(), iname.lower()):
        return False
    if path_pattern is not None and not _fnmatch(current, path_pattern):
        return False
    if regex is not None and not re.fullmatch(regex, current):
        return False
    info = os.lstat(current)
    if kind == "f" and not statmod.S_ISREG(info.st_mode):
        return False
    if kind == "d" and not statmod.S_ISDIR(info.st_mode):
        return False
    if kind == "l" and not statmod.S_ISLNK(info.st_mode):
        return False
    if size is not None:
        spec = str(size)
        sign = spec[0] if spec[0] in "+-" else ""
        body = spec.lstrip("+-")
        unit = body[-1] if body[-1] in "ckMGb" else "b"
        number = int(body.rstrip("ckMGb"))
        scale = {"c": 1, "k": 1024, "M": 1024**2, "G": 1024**3, "b": 512}[unit]
        blocks = -(-info.st_size // scale)
        if sign == "+" and blocks <= number:
            return False
        if sign == "-" and blocks >= number:
            return False
        if sign == "" and blocks != number:
            return False
    if mtime is not None:
        spec = str(mtime)
        sign = spec[0] if spec[0] in "+-" else ""
        number = int(spec.lstrip("+-"))
        days = int((time.time() - info.st_mtime) // 86400)
        if sign == "+" and days <= number:
            return False
        if sign == "-" and days >= number:
            return False
        if sign == "" and days != number:
            return False
    if newer is not None and info.st_mtime <= os.lstat(newer).st_mtime:
        return False
    if empty:
        if statmod.S_ISDIR(info.st_mode) and os.listdir(current):
            return False
        if statmod.S_ISREG(info.st_mode) and info.st_size:
            return False
    return True


def cp(source, dest, r=False, f=False, p=False, v=False, n=False):
    sources = _as_list(source)
    out = []
    for item in sources:
        target = os.path.join(dest, os.path.basename(item.rstrip("/"))) if os.path.isdir(dest) else dest
        if os.path.lexists(target) and n:
            continue
        try:
            if os.path.isdir(item):
                if not r:
                    print(f"cp: {item} is a directory (not copied).", file=sys.stderr)
                    continue
                shutil.copytree(item, target, symlinks=True, dirs_exist_ok=bool(f))
            else:
                if os.path.lexists(target) and f:
                    os.remove(target)
                shutil.copy2(item, target) if p else shutil.copyfile(item, target)
        except OSError as exc:
            print(f"cp: {item}: {exc.strerror}", file=sys.stderr)
            continue
        if v:
            out.append(f"'{item}' -> '{target}'\n")
    return "".join(out)


def mv(source, dest, f=False, n=False, v=False):
    out = []
    for item in _as_list(source):
        target = os.path.join(dest, os.path.basename(item.rstrip("/"))) if os.path.isdir(dest) else dest
        if os.path.lexists(target) and n:
            continue
        try:
            if os.path.lexists(target) and f and not os.path.isdir(target):
                os.remove(target)
            shutil.move(item, target)
        except OSError as exc:
            print(f"mv: {item}: {exc.strerror}", file=sys.stderr)
            continue
        if v:
            out.append(f"'{item}' -> '{target}'\n")
    return "".join(out)


def rm(paths, r=False, f=False, v=False, d=False):
    out = []
    for path in _as_list(paths):
        if not os.path.lexists(path):
            if not f:
                print(f"rm: {path}: No such file or directory", file=sys.stderr)
            continue
        try:
            if os.path.isdir(path) and not os.path.islink(path):
                if r:
                    shutil.rmtree(path)
                elif d:
                    os.rmdir(path)
                else:
                    print(f"rm: {path}: is a directory", file=sys.stderr)
                    continue
            else:
                os.remove(path)
        except OSError as exc:
            if not f:
                print(f"rm: {path}: {exc.strerror}", file=sys.stderr)
            continue
        if v:
            out.append(f"removed '{path}'\n")
    return "".join(out)


def mkdir(paths, p=False, m=None, v=False):
    out = []
    for path in _as_list(paths):
        try:
            if p:
                os.makedirs(path, exist_ok=True)
            else:
                os.mkdir(path)
            if m is not None:
                os.chmod(path, m)
        except OSError as exc:
            print(f"mkdir: {path}: {exc.strerror}", file=sys.stderr)
            continue
        if v:
            out.append(f"mkdir: created directory '{path}'\n")
    return "".join(out)


def rmdir(paths, p=False, v=False):
    out = []
    for path in _as_list(paths):
        try:
            os.removedirs(path) if p else os.rmdir(path)
        except OSError as exc:
            print(f"rmdir: {path}: {exc.strerror}", file=sys.stderr)
            continue
        if v:
            out.append(f"rmdir: removing directory, '{path}'\n")
    return "".join(out)


def touch(paths, a=False, m=False, c=False, d=None, r=None):
    if r is not None:
        info = os.stat(r)
        atime, mtime = info.st_atime, info.st_mtime
    elif d is not None:
        stamp = float(d[1:]) if d.startswith("@") else dt.datetime.fromisoformat(d).timestamp()
        atime = mtime = stamp
    else:
        atime = mtime = time.time()
    for path in _as_list(paths):
        if not os.path.lexists(path):
            if c:
                continue
            open(path, "a").close()
        info = os.stat(path)
        new_atime = atime if (a or not m) else info.st_atime
        new_mtime = mtime if (m or not a) else info.st_mtime
        os.utime(path, (new_atime, new_mtime))
    return ""


def ln(target, link_name, s=False, f=False, v=False):
    if f and os.path.lexists(link_name):
        os.remove(link_name)
    try:
        os.symlink(target, link_name) if s else os.link(target, link_name)
    except OSError as exc:
        print(f"ln: {link_name}: {exc.strerror}", file=sys.stderr)
        return ""
    return f"'{link_name}' -> '{target}'\n" if v else ""


def readlink(path, f=False):
    try:
        return (os.path.realpath(path) if f else os.readlink(path)) + "\n"
    except OSError as exc:
        print(f"readlink: {path}: {exc.strerror}", file=sys.stderr)
        return ""


def realpath(paths):
    return "".join(os.path.realpath(path) + "\n" for path in _as_list(paths))


def basename(path, suffix=None):
    name = os.path.basename(path.rstrip("/")) or "/"
    if suffix and name.endswith(suffix) and name != suffix:
        name = name[: -len(suffix)]
    return name + "\n"


def dirname(path):
    parent = os.path.dirname(path.rstrip("/"))
    return (parent or ".") + "\n"


def pwd():
    return os.getcwd() + "\n"


def cd(path=None):
    os.chdir(os.path.expanduser(path) if path else os.path.expanduser("~"))
    return ""


def tree(path=".", d=False, L=None, a=False):
    out = [path + "\n"]
    counters = [0, 0]
    _tree_walk(path, "", d, L, a, 1, out, counters)
    out.append(f"\n{counters[0]} directories, {counters[1]} files\n")
    return "".join(out)


def _tree_walk(directory, indent, only_dirs, limit, show_all, depth, out, counters):
    if limit is not None and depth > limit:
        return
    try:
        names = sorted(os.listdir(directory))
    except OSError:
        return
    if not show_all:
        names = [name for name in names if not name.startswith(".")]
    entries = [name for name in names if not only_dirs or os.path.isdir(os.path.join(directory, name))]
    for index, name in enumerate(entries):
        full = os.path.join(directory, name)
        last = index == len(entries) - 1
        out.append(f"{indent}{'└── ' if last else '├── '}{name}\n")
        if os.path.isdir(full) and not os.path.islink(full):
            counters[0] += 1
            _tree_walk(full, indent + ("    " if last else "│   "), only_dirs, limit, show_all, depth + 1, out, counters)
        else:
            counters[1] += 1


def stat(paths, L=False):
    out = []
    for path in _as_list(paths):
        try:
            info = os.stat(path) if L else os.lstat(path)
        except OSError as exc:
            print(f"stat: {path}: {exc.strerror}", file=sys.stderr)
            continue
        kind = "directory" if statmod.S_ISDIR(info.st_mode) else "symbolic link" if statmod.S_ISLNK(info.st_mode) else "regular file"
        out.append(f"  File: {path}\n")
        out.append(f"  Size: {info.st_size}\tBlocks: {info.st_blocks}\tIO Block: {info.st_blksize}\t{kind}\n")
        out.append(f"Device: {info.st_dev}\tInode: {info.st_ino}\tLinks: {info.st_nlink}\n")
        out.append(f"Access: ({statmod.S_IMODE(info.st_mode):04o}/{statmod.filemode(info.st_mode)})\tUid: {info.st_uid}\tGid: {info.st_gid}\n")
        out.append(f"Access: {dt.datetime.fromtimestamp(info.st_atime)}\n")
        out.append(f"Modify: {dt.datetime.fromtimestamp(info.st_mtime)}\n")
        out.append(f"Change: {dt.datetime.fromtimestamp(info.st_ctime)}\n")
    return "".join(out)


def du(paths=".", s=False, h=False, a=False, c=False, max_depth=None, block=1024):
    out = []
    grand_total = 0
    for target in _as_list(paths) or ["."]:
        sizes = {}
        for root, dirs, files in os.walk(target, topdown=False):
            total = 0
            for name in files:
                full = os.path.join(root, name)
                try:
                    size = os.lstat(full).st_size
                except OSError:
                    continue
                total += -(-size // block) * block
                if a:
                    sizes[full] = -(-size // block) * block
            for name in dirs:
                total += sizes.get(os.path.join(root, name), 0)
            sizes[root] = total + block
        if os.path.isfile(target):
            sizes[target] = -(-os.lstat(target).st_size // block) * block
        depths = {name: name.rstrip("/").count("/") - target.rstrip("/").count("/") for name in sizes}
        for name in sorted(sizes, key=lambda item: (-depths[item], item)):
            if s and name != target:
                continue
            if max_depth is not None and depths[name] > max_depth:
                continue
            value = _human(sizes[name]) if h else str(sizes[name] // block)
            out.append(f"{value}\t{name}\n")
        grand_total += sizes.get(target, 0)
    if c:
        value = _human(grand_total) if h else str(grand_total // block)
        out.append(f"{value}\ttotal\n")
    return "".join(out)


def df(paths="/", h=False, block=1024):
    out = ["Filesystem" + " " * 8 + f"{'Size':>8}{'Used':>8}{'Avail':>8} Use% Mounted on\n"]
    for path in _as_list(paths) or ["/"]:
        try:
            usage = shutil.disk_usage(path)
        except OSError as exc:
            print(f"df: {path}: {exc.strerror}", file=sys.stderr)
            continue
        mount = path
        while not os.path.ismount(mount) and mount != "/":
            mount = os.path.dirname(mount)
        percent = round(usage.used * 100 / usage.total) if usage.total else 0
        if h:
            fields = (_human(usage.total), _human(usage.used), _human(usage.free))
        else:
            fields = (str(usage.total // block), str(usage.used // block), str(usage.free // block))
        out.append(f"{mount:<18}{fields[0]:>8}{fields[1]:>8}{fields[2]:>8} {percent:3d}% {mount}\n")
    return "".join(out)


_MAGIC = [
    (b"\x7fELF", "ELF executable"),
    (b"\x89PNG\r\n\x1a\n", "PNG image data"),
    (b"\xff\xd8\xff", "JPEG image data"),
    (b"GIF8", "GIF image data"),
    (b"%PDF", "PDF document"),
    (b"\x1f\x8b", "gzip compressed data"),
    (b"BZh", "bzip2 compressed data"),
    (b"PK\x03\x04", "Zip archive data"),
    (b"\xfd7zXZ", "XZ compressed data"),
    (b"#!", "script text executable"),
]


def file(paths):
    out = []
    for path in _as_list(paths):
        if not os.path.lexists(path):
            out.append(f"{path}: cannot open (No such file or directory)\n")
            continue
        if os.path.islink(path):
            out.append(f"{path}: symbolic link to {os.readlink(path)}\n")
            continue
        if os.path.isdir(path):
            out.append(f"{path}: directory\n")
            continue
        data = _read_bytes(path)
        if not data:
            out.append(f"{path}: empty\n")
            continue
        kind = None
        for magic, label in _MAGIC:
            if data.startswith(magic):
                kind = label
                break
        if kind is None:
            try:
                text = data.decode()
                kind = "ASCII text" if all(ch in string.printable for ch in text) else "UTF-8 Unicode text"
            except UnicodeDecodeError:
                kind = "data"
        out.append(f"{path}: {kind}\n")
    return "".join(out)


def chmod(paths, mode, R=False, v=False):
    targets = []
    for path in _as_list(paths):
        targets.append(path)
        if R and os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                targets.extend(os.path.join(root, name) for name in dirs + files)
    out = []
    for path in targets:
        try:
            if isinstance(mode, int):
                new_mode = mode
            elif re.fullmatch(r"[0-7]{3,4}", str(mode)):
                new_mode = int(str(mode), 8)
            else:
                new_mode = _symbolic_mode(statmod.S_IMODE(os.stat(path).st_mode), str(mode))
            os.chmod(path, new_mode)
        except OSError as exc:
            print(f"chmod: {path}: {exc.strerror}", file=sys.stderr)
            continue
        if v:
            out.append(f"mode of '{path}' changed to {new_mode:04o}\n")
    return "".join(out)


def _symbolic_mode(current, spec):
    bits = {
        "u": {"r": statmod.S_IRUSR, "w": statmod.S_IWUSR, "x": statmod.S_IXUSR},
        "g": {"r": statmod.S_IRGRP, "w": statmod.S_IWGRP, "x": statmod.S_IXGRP},
        "o": {"r": statmod.S_IROTH, "w": statmod.S_IWOTH, "x": statmod.S_IXOTH},
    }
    for clause in spec.split(","):
        match = re.fullmatch(r"([ugoa]*)([-+=])([rwx]*)", clause)
        if not match:
            raise ValueError(f"chmod: invalid mode: {spec}")
        who, op, perms = match.groups()
        who = who or "a"
        classes = "ugo" if "a" in who else who
        mask = 0
        for target in classes:
            for perm in perms:
                mask |= bits[target][perm]
        if op == "+":
            current |= mask
        elif op == "-":
            current &= ~mask
        else:
            clear = 0
            for target in classes:
                clear |= sum(bits[target].values())
            current = (current & ~clear) | mask
    return current


def chown(paths, user=None, group=None, R=False, v=False):
    uid = -1 if user is None else (int(user) if str(user).isdigit() else pwdlib.getpwnam(str(user)).pw_uid)
    gid = -1 if group is None else (int(group) if str(group).isdigit() else grp.getgrnam(str(group)).gr_gid)
    targets = []
    for path in _as_list(paths):
        targets.append(path)
        if R and os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                targets.extend(os.path.join(root, name) for name in dirs + files)
    out = []
    for path in targets:
        try:
            os.chown(path, uid, gid)
        except OSError as exc:
            print(f"chown: {path}: {exc.strerror}", file=sys.stderr)
            continue
        if v:
            out.append(f"changed ownership of '{path}'\n")
    return "".join(out)


def chgrp(paths, group, R=False, v=False):
    return chown(paths, None, group, R=R, v=v)


def umask(mask=None):
    if mask is None:
        current = os.umask(0)
        os.umask(current)
        return f"{current:04o}\n"
    os.umask(int(str(mask), 8) if isinstance(mask, str) else mask)
    return ""


def which(names, a=False):
    out = []
    directories = os.environ.get("PATH", "").split(os.pathsep)
    for name in _as_list(names):
        for directory in directories:
            candidate = os.path.join(directory, name)
            if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                out.append(candidate + "\n")
                if not a:
                    break
    return "".join(out)


def whereis(names):
    directories = [
        "/bin", "/sbin", "/usr/bin", "/usr/sbin", "/usr/local/bin", "/usr/local/sbin",
        "/usr/share/man/man1", "/usr/share/man/man8", "/opt/homebrew/bin",
    ]
    out = []
    for name in _as_list(names):
        hits = []
        for directory in directories:
            for suffix in ("", ".1", ".1.gz", ".8", ".8.gz"):
                candidate = os.path.join(directory, name + suffix)
                if os.path.exists(candidate):
                    hits.append(candidate)
        out.append(f"{name}: " + " ".join(hits) + "\n")
    return "".join(out)


def mktemp(d=False, suffix="", prefix="tmp", directory=None):
    if d:
        return tempfile.mkdtemp(suffix=suffix, prefix=prefix, dir=directory) + "\n"
    handle, path = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=directory)
    os.close(handle)
    return path + "\n"


def dd(if_=None, of=None, bs=512, count=None, skip=0, seek=0, conv=None):
    data = _read_bytes(if_)
    data = data[skip * bs :]
    if count is not None:
        data = data[: count * bs]
    if of is None:
        return data.decode(errors="replace")
    mode = "r+b" if conv == "notrunc" and os.path.exists(of) else "wb"
    with open(of, mode) as handle:
        handle.seek(seek * bs)
        handle.write(data)
    return ""


def sync():
    os.sync()
    return ""


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------


def echo(*args, n=False, e=False):
    text = " ".join(str(item) for item in args)
    if e:
        text = _unescape(text)
    return text if n else text + "\n"


def seq(first, last=None, increment=1, s="\n", w=False):
    if last is None:
        start, stop, step = 1, first, 1
    else:
        start, stop, step = first, last, increment
    values = []
    current = start
    while (step > 0 and current <= stop) or (step < 0 and current >= stop):
        values.append(current)
        current += step
    texts = [f"{value:g}" if isinstance(value, float) else str(value) for value in values]
    if w and texts:
        width = max(len(text) for text in texts)
        texts = [text.rjust(width, "0") for text in texts]
    return s.join(texts) + "\n"


def sleep(duration):
    text = str(duration)
    scale = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    seconds = float(text[:-1]) * scale[text[-1]] if text[-1] in scale else float(text)
    time.sleep(seconds)
    return ""


def date(format="+%a %b %e %H:%M:%S %Z %Y", u=False, d=None, r=None):
    if r is not None:
        moment = dt.datetime.fromtimestamp(os.stat(r).st_mtime, dt.timezone.utc if u else None)
    elif d is not None:
        if d.startswith("@"):
            moment = dt.datetime.fromtimestamp(float(d[1:]), dt.timezone.utc if u else None)
        else:
            moment = dt.datetime.fromisoformat(d)
    else:
        moment = dt.datetime.now(dt.timezone.utc) if u else dt.datetime.now()
    return moment.strftime(format.lstrip("+")) + "\n"


def env(assignments=None):
    for item in _as_list(assignments):
        key, _, value = item.partition("=")
        os.environ[key] = value
    return "".join(f"{key}={value}\n" for key, value in os.environ.items())


def printenv(name=None):
    if name is None:
        return env()
    value = os.environ.get(name)
    return "" if value is None else value + "\n"


def export(name, value=""):
    os.environ[name] = str(value)
    return ""


def unset(name):
    os.environ.pop(name, None)
    return ""


def uname(a=False, s=False, n=False, r=False, v=False, m=False, p=False):
    info = os.uname()
    if a:
        return f"{info.sysname} {info.nodename} {info.release} {info.version} {info.machine}\n"
    fields = []
    if s or not (n or r or v or m or p):
        fields.append(info.sysname)
    if n:
        fields.append(info.nodename)
    if r:
        fields.append(info.release)
    if v:
        fields.append(info.version)
    if m:
        fields.append(info.machine)
    if p:
        fields.append(platform.processor() or info.machine)
    return " ".join(fields) + "\n"


def hostname():
    return socket.gethostname() + "\n"


def whoami():
    return getpass.getuser() + "\n"


def id(user=None):
    entry = pwdlib.getpwnam(user) if user else pwdlib.getpwuid(os.getuid())
    primary = grp.getgrgid(entry.pw_gid)
    members = [group for group in grp.getgrall() if entry.pw_name in group.gr_mem or group.gr_gid == entry.pw_gid]
    groups = ",".join(f"{group.gr_gid}({group.gr_name})" for group in sorted(members, key=lambda item: item.gr_gid))
    return f"uid={entry.pw_uid}({entry.pw_name}) gid={primary.gr_gid}({primary.gr_name}) groups={groups}\n"


def groups(user=None):
    entry = pwdlib.getpwnam(user) if user else pwdlib.getpwuid(os.getuid())
    names = [group.gr_name for group in grp.getgrall() if entry.pw_name in group.gr_mem or group.gr_gid == entry.pw_gid]
    return " ".join(names) + "\n"


def kill(pids, s="TERM"):
    number = int(s) if str(s).isdigit() else getattr(signal, f"SIG{str(s).upper().removeprefix('SIG')}")
    for pid in _as_list(pids) if not isinstance(pids, int) else [pids]:
        try:
            os.kill(int(pid), number)
        except OSError as exc:
            print(f"kill: {pid}: {exc.strerror}", file=sys.stderr)
    return ""


def clear():
    return "\033[H\033[2J\033[3J"


def test(*args):
    if len(args) == 1:
        return bool(args[0])
    if len(args) == 2:
        flag, operand = args
        unary = {
            "-e": os.path.lexists,
            "-f": os.path.isfile,
            "-d": os.path.isdir,
            "-L": os.path.islink,
            "-h": os.path.islink,
            "-s": lambda path: os.path.exists(path) and os.path.getsize(path) > 0,
            "-r": lambda path: os.access(path, os.R_OK),
            "-w": lambda path: os.access(path, os.W_OK),
            "-x": lambda path: os.access(path, os.X_OK),
            "-z": lambda value: len(value) == 0,
            "-n": lambda value: len(value) > 0,
        }
        if flag not in unary:
            raise ValueError(f"test: unsupported operator: {flag}")
        return bool(unary[flag](operand))
    if len(args) == 3:
        left, operator, right = args
        if operator in ("-eq", "-ne", "-lt", "-le", "-gt", "-ge"):
            a, b = int(left), int(right)
            return {
                "-eq": a == b, "-ne": a != b, "-lt": a < b,
                "-le": a <= b, "-gt": a > b, "-ge": a >= b,
            }[operator]
        if operator in ("=", "=="):
            return str(left) == str(right)
        if operator == "!=":
            return str(left) != str(right)
        if operator == "<":
            return str(left) < str(right)
        if operator == ">":
            return str(left) > str(right)
        if operator == "-nt":
            return os.stat(left).st_mtime > os.stat(right).st_mtime
        if operator == "-ot":
            return os.stat(left).st_mtime < os.stat(right).st_mtime
        raise ValueError(f"test: unsupported operator: {operator}")
    raise ValueError("test: unsupported expression")


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------


def tar(f, c=False, x=False, t=False, z=False, j=False, v=False, C=None, files=None):
    compression = "gz" if z else ("bz2" if j else "")
    out = []
    if c:
        with tarfile.open(f, f"w:{compression}" if compression else "w") as archive:
            for item in _as_list(files):
                arcname = os.path.relpath(item, C) if C else item
                archive.add(item if not C else os.path.join(C, arcname), arcname=arcname)
                if v:
                    out.append(arcname + "\n")
        return "".join(out)
    with tarfile.open(f, f"r:{compression}" if compression else "r") as archive:
        if t:
            return "".join(member.name + ("/" if member.isdir() else "") + "\n" for member in archive.getmembers())
        for member in archive.getmembers():
            archive.extract(member, path=C or ".", filter="data")
            if v:
                out.append(member.name + "\n")
    return "".join(out)


def gzip(files, d=False, k=False, c=False, level=9):
    if d:
        return gunzip(files, k=k, c=c)
    out = []
    for path in _as_list(files):
        data = _read_bytes(path)
        blob = gziplib.compress(data, level)
        if c:
            out.append(blob.decode("latin-1"))
            continue
        with open(path + ".gz", "wb") as handle:
            handle.write(blob)
        if not k:
            os.remove(path)
    return "".join(out)


def gunzip(files, k=False, c=False):
    out = []
    for path in _as_list(files):
        with open(path, "rb") as handle:
            data = gziplib.decompress(handle.read())
        if c:
            out.append(data.decode(errors="replace"))
            continue
        target = path[:-3] if path.endswith(".gz") else path + ".out"
        with open(target, "wb") as handle:
            handle.write(data)
        if not k:
            os.remove(path)
    return "".join(out)


def bzip2(files, d=False, k=False, c=False, level=9):
    if d:
        return bunzip2(files, k=k, c=c)
    out = []
    for path in _as_list(files):
        blob = bz2.compress(_read_bytes(path), level)
        if c:
            out.append(blob.decode("latin-1"))
            continue
        with open(path + ".bz2", "wb") as handle:
            handle.write(blob)
        if not k:
            os.remove(path)
    return "".join(out)


def bunzip2(files, k=False, c=False):
    out = []
    for path in _as_list(files):
        with open(path, "rb") as handle:
            data = bz2.decompress(handle.read())
        if c:
            out.append(data.decode(errors="replace"))
            continue
        target = path[:-4] if path.endswith(".bz2") else path + ".out"
        with open(target, "wb") as handle:
            handle.write(data)
        if not k:
            os.remove(path)
    return "".join(out)


def zip_(archive, files, r=False, j=False):
    out = []
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as handle:
        for item in _as_list(files):
            if os.path.isdir(item) and r:
                if not j:
                    handle.write(item, item)
                    out.append(f"  adding: {item}/\n")
                for root, dirs, names in os.walk(item):
                    for name in sorted(dirs):
                        full = os.path.join(root, name)
                        if not j:
                            handle.write(full, full)
                            out.append(f"  adding: {full}/\n")
                    for name in sorted(names):
                        full = os.path.join(root, name)
                        handle.write(full, os.path.basename(full) if j else full)
                        out.append(f"  adding: {full}\n")
            elif os.path.isfile(item):
                handle.write(item, os.path.basename(item) if j else item)
                out.append(f"  adding: {item}\n")
    return "".join(out)


def unzip(archive, d=None, l=False, o=False):
    with zipfile.ZipFile(archive) as handle:
        if l:
            out = [f"Archive:  {archive}\n", "  Length      Date    Time    Name\n"]
            for info in handle.infolist():
                stamp = "%04d-%02d-%02d %02d:%02d" % info.date_time[:5]
                out.append(f"{info.file_size:8d}  {stamp}   {info.filename}\n")
            return "".join(out)
        handle.extractall(d or ".")
        return "".join(f"  inflating: {name}\n" for name in handle.namelist())


def zipinfo(archive):
    with zipfile.ZipFile(archive) as handle:
        infos = handle.infolist()
        total = sum(info.file_size for info in infos)
        out = [f"Archive:  {archive}\n", f"Zip file size: {os.path.getsize(archive)} bytes, number of entries: {len(infos)}\n"]
        for info in infos:
            stamp = "%04d-%02d-%02d %02d:%02d" % info.date_time[:5]
            kind = "drwxr-xr-x" if info.is_dir() else "-rw-r--r--"
            out.append(f"{kind}  2.0 unx {info.file_size:8d} bx defN {stamp} {info.filename}\n")
        out.append(f"{len(infos)} files, {total} bytes uncompressed\n")
        return "".join(out)


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------


def tty():
    try:
        return os.ttyname(0) + "\n"
    except OSError:
        return "not a tty\n"


def logname():
    name = os.environ.get("LOGNAME") or os.environ.get("USER")
    return (name or getpass.getuser()) + "\n"


def yes(text="y", count=None):
    if count is None:
        raise ValueError("yes: this implementation requires an explicit count to avoid infinite output")
    return (str(text) + "\n") * int(count)


def expr(*tokens):
    if len(tokens) == 2 and tokens[0] == "length":
        return f"{len(str(tokens[1]))}\n"
    if len(tokens) == 4 and tokens[0] == "substr":
        _, source, pos, length = tokens
        start = max(int(pos) - 1, 0)
        return str(source)[start : start + int(length)] + "\n"
    if len(tokens) == 3 and tokens[0] == "index":
        _, source, chars = tokens
        for index, ch in enumerate(str(source), 1):
            if ch in str(chars):
                return f"{index}\n"
        return "0\n"
    if len(tokens) == 3 and tokens[0] == "match":
        _, source, pattern = tokens
        match = re.match(pattern, str(source))
        return f"{match.end() if match else 0}\n"
    if len(tokens) == 3 and tokens[1] == ":":
        match = re.match(str(tokens[2]), str(tokens[0]))
        return f"{match.end() if match else 0}\n"
    parts = [str(token) for token in tokens]
    expression = " ".join(parts)
    for src, dst in (("=", "=="), ("\\*", "*"), ("/", "//"), ("|", " or "), ("&", " and ")):
        expression = expression.replace(f" {src} ", f" {dst} ")
    try:
        value = eval(expression, {"__builtins__": {}}, {})
    except Exception as exc:
        raise ValueError(f"expr: cannot evaluate {expression!r}: {exc}") from exc
    if isinstance(value, bool):
        return ("1" if value else "0") + "\n"
    return f"{value}\n"


def csplit(file, patterns, prefix="xx", digits=2, k=False, s=False, z=False):
    lines = _read_lines(file)
    if not isinstance(patterns, (list, tuple)):
        patterns = [patterns]
    boundaries = []
    cursor = 0
    for pattern in patterns:
        match = re.fullmatch(r"\{(\d+)\}", str(pattern))
        if match and boundaries:
            step = boundaries[-1] - (boundaries[-2] if len(boundaries) > 1 else 0)
            for _ in range(int(match.group(1))):
                boundaries.append(boundaries[-1] + step)
            continue
        if isinstance(pattern, int):
            boundaries.append(int(pattern) - 1)
            cursor = boundaries[-1]
            continue
        text = str(pattern).strip("/")
        for index in range(cursor + 1, len(lines)):
            if re.search(text, lines[index].rstrip("\n")):
                boundaries.append(index)
                cursor = index
                break
    boundaries.append(len(lines))
    out = []
    start = 0
    for index, end in enumerate(boundaries):
        chunk = "".join(lines[start:end])
        if z and not chunk:
            start = end
            continue
        path = f"{prefix}{index:0{digits}d}"
        with open(path, "w") as handle:
            handle.write(chunk)
        if not s:
            out.append(f"{len(chunk.encode())}\n")
        start = end
    return "".join(out)


def lndir(source, target=None):
    destination = target or "."
    os.makedirs(destination, exist_ok=True)
    for root, dirs, files in os.walk(source):
        rel = os.path.relpath(root, source)
        for name in dirs:
            os.makedirs(os.path.join(destination, rel, name), exist_ok=True)
        for name in files:
            link = os.path.join(destination, rel, name)
            if os.path.lexists(link):
                continue
            os.symlink(os.path.abspath(os.path.join(root, name)), link)
    return ""


def tmpwatch(hours, path):
    threshold = time.time() - float(hours) * 3600
    for root, _, files in os.walk(path):
        for name in files:
            full = os.path.join(root, name)
            try:
                if os.lstat(full).st_atime < threshold:
                    os.remove(full)
            except OSError as exc:
                print(f"tmpwatch: {full}: {exc.strerror}", file=sys.stderr)
    return ""


def diffstat(diff_text=None):
    if diff_text is None:
        diff_text = sys.stdin.read()
    stats = {}
    current = None
    for line in diff_text.splitlines():
        header = re.match(r"^(?:\+\+\+|---)\s+(\S+)", line)
        if header:
            name = header.group(1)
            if name != "/dev/null" and not name.startswith(("a/", "b/")):
                current = name
            elif name.startswith(("a/", "b/")):
                current = name[2:]
            stats.setdefault(current, [0, 0])
            continue
        if line.startswith("+++") or line.startswith("---") or line.startswith("@@"):
            continue
        if current is None:
            continue
        if line.startswith("+"):
            stats[current][0] += 1
        elif line.startswith("-"):
            stats[current][1] += 1
    if not stats:
        return " 0 files changed\n"
    total_add = sum(item[0] for item in stats.values())
    total_del = sum(item[1] for item in stats.values())
    width = max(len(name) for name in stats)
    out = []
    for name, (add, delete) in stats.items():
        out.append(f" {name:<{width}} | {add + delete:4d} {'+' * add}{'-' * delete}\n")
    out.append(f" {len(stats)} files changed, {total_add} insertions(+), {total_del} deletions(-)\n")
    return "".join(out)


def patch(target=None, patch_file=None, p=1, R=False, dry_run=False):
    diff_text = _read_text(patch_file)
    hunks = _parse_unified_diff(diff_text)
    out = []
    for header, chunks in hunks.items():
        path = target or "/".join(header.split("/")[p:])
        lines = open(path).read().splitlines(keepends=True) if os.path.exists(path) else []
        content = list(lines)
        offset = 0
        for old_start, new_start, block in chunks:
            source_lines = [text for tag, text in block if tag in (" ", "-")]
            replaced = [text for tag, text in block if tag in (" ", "+")]
            if R:
                source_lines, replaced = replaced, source_lines
                anchor = new_start - 1 + offset
            else:
                anchor = old_start - 1 + offset
            if content[anchor : anchor + len(source_lines)] != source_lines:
                raise ValueError(f"patch: hunk does not match {path} @@ {old_start}")
            content[anchor : anchor + len(source_lines)] = replaced
            offset += len(replaced) - len(source_lines)
        if not dry_run:
            with open(path, "w") as handle:
                handle.writelines(content)
        out.append(f"patching file {path}\n")
    return "".join(out)


def _parse_unified_diff(text):
    hunks = {}
    current_file = None
    current_block = None
    old_start = new_start = 0
    for line in text.splitlines(keepends=True):
        header = re.match(r"^\+\+\+\s+(\S+)", line)
        if header:
            current_file = header.group(1)
            hunks.setdefault(current_file, [])
            continue
        if line.startswith("---"):
            continue
        hunk = re.match(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
        if hunk:
            old_start, new_start = int(hunk.group(1)), int(hunk.group(2))
            current_block = []
            hunks[current_file].append((old_start, new_start, current_block))
            continue
        if current_block is None or not line:
            continue
        tag, body = line[0], line[1:]
        if tag in (" ", "+", "-"):
            current_block.append((tag, body))
    return hunks
