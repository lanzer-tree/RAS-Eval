"""
Script Analyzer Module
Pre-execution static analysis for script files (Python, Shell, Node.js, etc.)
Catches dangerous imports, network calls, file access, and suspicious patterns
before the script is handed off to an interpreter.
"""

import ast
import re
import os
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, List, Optional, Tuple

if TYPE_CHECKING:
    from .rules import RuleEngine


class ScriptRisk(Enum):
    """Overall risk level of a script"""
    SAFE = "safe"
    SUSPICIOUS = "suspicious"
    DANGEROUS = "dangerous"


@dataclass
class ScriptFinding:
    """A single finding from script analysis"""
    category: str           # e.g. "dangerous_import", "network_call", "file_access"
    description: str        # Human-readable explanation
    line: Optional[int] = None
    severity: str = "medium"    # "low", "medium", "high", "critical"
    evidence: str = ""      # The actual code fragment that triggered this


@dataclass
class ScriptAnalysisResult:
    """Full result of analyzing a script file"""
    path: str
    risk: ScriptRisk
    findings: List[ScriptFinding] = field(default_factory=list)
    recommended_action: str = "allow"   # "allow", "approve", "deny"
    summary: str = ""

    @property
    def has_critical(self) -> bool:
        return any(f.severity == "critical" for f in self.findings)

    @property
    def has_high(self) -> bool:
        return any(f.severity == "high" for f in self.findings)


# ─────────────────────────────────────────────────────────────────────────────
# Dangerous / suspicious catalogues
# ─────────────────────────────────────────────────────────────────────────────

# Python imports that warrant automatic denial
_PYTHON_CRITICAL_IMPORTS = {
    "ctypes":       "Direct memory manipulation; can bypass Python sandbox",
    "cffi":         "C foreign-function interface; native code execution",
    "pickle":       "Arbitrary code execution via deserialization",
    "shelve":       "Uses pickle internally; arbitrary code execution risk",
    "marshal":      "Low-level serialisation; can execute arbitrary bytecode",
}

# Python imports that require human approval
_PYTHON_SUPERVISED_IMPORTS = {
    "subprocess":   "Spawns child processes",
    "os":           "OS-level file and process operations",
    "sys":          "System-level access",
    "shutil":       "High-level file operations (copy, delete, move)",
    "socket":       "Raw network socket access",
    "requests":     "HTTP client; may exfiltrate data",
    "urllib":       "HTTP/FTP client",
    "http":         "HTTP client/server",
    "ftplib":       "FTP client",
    "smtplib":      "SMTP email sending",
    "paramiko":     "SSH client",
    "fabric":       "Remote command execution over SSH",
    "pexpect":      "Spawns and controls child processes",
    "pty":          "Pseudo-terminal creation",
    "signal":       "Process signal manipulation",
    "multiprocessing": "Multi-process execution",
    "threading":    "Multi-threading",
    "importlib":    "Dynamic module loading",
    "zipimport":    "Imports from zip archives",
}

# AST call patterns that are always critical (module.func)
_PYTHON_CRITICAL_CALLS: List[Tuple[str, str]] = [
    ("os", "system"),
    ("os", "popen"),
    ("os", "execve"),
    ("os", "execvp"),
    ("os", "execle"),
    ("os", "spawnl"),
    ("os", "spawnv"),
    ("subprocess", "call"),
    ("subprocess", "run"),
    ("subprocess", "Popen"),
    ("subprocess", "check_call"),
    ("subprocess", "check_output"),
]

# Standalone built-in calls that are always critical
_PYTHON_CRITICAL_BUILTINS = {"eval", "exec", "compile", "__import__"}

# Regex patterns applied to raw source (language-agnostic)
_RAW_PATTERNS: List[Tuple[str, str, str, str]] = [
    # (category, severity, description, regex)

    # Cloud metadata SSRF
    ("network_call", "critical",
     "Cloud metadata endpoint access (SSRF)",
     r"169\.254\.169\.254|metadata\.google\.internal|metadata\.goog|100\.100\.100\.200"),

    # Reverse shells
    ("reverse_shell", "critical",
     "Reverse shell pattern",
     r"bash\s+-i\s+>&\s+/dev/tcp|nc\s+-e\s+/bin/(ba)?sh|"
     r"/bin/sh\s+-i|socat\s+.*exec:|"
     r"python.*-c.*socket.*connect"),

    # Credential file access
    ("file_access", "critical",
     "Credential or shadow file access",
     r"/etc/shadow|/etc/passwd|\.ssh/id_rsa|\.ssh/id_ecdsa|"
     r"\.ssh/id_ed25519|\.aws/credentials|\.docker/config\.json"),

    # Data exfiltration
    ("network_call", "high",
     "Potential data exfiltration (POST with file content)",
     r"requests\.post.*open\(|urllib.*POST.*open\(|"
     r"curl.*-d\s+@|curl.*--data-binary\s+@"),

    # URL shorteners / paste sites (exfil risk)
    ("network_call", "high",
     "Request to paste/tunnel site (exfil risk)",
     r"pastebin\.com|transfer\.sh|ngrok\.io|localtunnel\.me|"
     r"requestbin\.|webhook\.site"),

    # Obfuscated execution
    ("obfuscation", "high",
     "Base64 decode piped to shell",
     r"base64\s*(-d|--decode).*\|.*(bash|sh|python|perl)|"
     r"echo\s+[A-Za-z0-9+/=]{20,}\s*\|\s*(base64|b64)"),

    # Hardcoded IPs (suspicious)
    ("network_call", "medium",
     "Hardcoded non-loopback IP address",
     r"(?<![.\d])(?!127\.|0\.0\.0\.0|255\.)"
     r"(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}"
     r"(?:25[0-5]|2[0-4]\d|[01]?\d\d?)(?![.\d])"),

    # Sensitive path writes
    ("file_access", "high",
     "Write to /etc or /boot",
     r"open\s*\(\s*['\"]\/etc\/|open\s*\(\s*['\"]\/boot\/"),

    # Dynamic import tricks
    ("obfuscation", "high",
     "Dynamic __import__ or importlib usage",
     r"__import__\s*\(|importlib\.import_module\s*\("),
]

# Shell-script specific patterns (applied when file looks like shell)
_SHELL_PATTERNS: List[Tuple[str, str, str, str]] = [
    ("reverse_shell", "critical",
     "Reverse shell",
     r"bash\s+-i\s+>&|/dev/tcp/|nc\s+-[el].*sh"),

    ("remote_exec", "critical",
     "Piping remote content to shell",
     r"curl.*\|\s*(bash|sh|python)|wget.*\|\s*(bash|sh|python)"),

    ("credential_access", "critical",
     "Shadow/credential file read",
     r"cat\s+/etc/shadow|cat\s+.*id_rsa|grep.*password.*\/etc"),

    ("persistence", "high",
     "Cron or rc.local persistence",
     r"crontab\s+-[el]|>>\s*/etc/rc\.local|/etc/cron"),

    ("obfuscation", "high",
     "Base64 decode execution",
     r"base64\s+-d.*\|.*(bash|sh)|echo\s+.*\|\s*base64\s+-d"),
]


# ─────────────────────────────────────────────────────────────────────────────
# Analyzer
# ─────────────────────────────────────────────────────────────────────────────

# Regex to extract file paths from source code (Python open(), shell redirects, etc.)
_SOURCE_PATH_RE = re.compile(
    r'''(?:open|file)\s*\(\s*['"](?P<path>[^'"]+)['"]'''   # open("/path")
    r'''|(?:^|\s)(?P<shpath>/(?:etc|root|home|var|usr|opt)[^\s'"\)\|;&>]+)'''  # /etc/… /home/… (must have subpath)
    r'''|['"](?P<tildepath>~/[^'"\s]+)['"]''',            # "~/…" strings
    re.MULTILINE,
)

# Regex to extract URLs from source code
_SOURCE_URL_RE = re.compile(
    r'''['"](?P<url>https?://[^'"\s]+)['"]''',
    re.MULTILINE,
)


class ScriptAnalyzer:
    """
    Static analyzer for script files.

    Supports:
    - Python  (.py)  – AST-based import and call analysis + raw patterns
    - Shell   (.sh, .bash, .zsh) – raw pattern analysis
    - Node.js (.js, .ts)  – raw pattern analysis
    - Generic fallback    – raw pattern analysis only

    Pass a RuleEngine instance to cross-check extracted paths and URLs
    against the live rules.yaml (denied_paths, allowed_paths, denied_domains, etc.)

    Usage::

        analyzer = ScriptAnalyzer(rule_engine=engine)
        result = analyzer.analyze("/path/to/script.py")
        # result.recommended_action in {"allow", "approve", "deny"}
    """

    def __init__(self, rule_engine: Optional["RuleEngine"] = None):
        """
        Args:
            rule_engine: Optional RuleEngine instance.  When provided, paths and
                         URLs extracted from script source are validated against
                         the live rules.yaml (denied_paths, denied_domains, etc.).
        """
        self._rule_engine = rule_engine

    def analyze(self, path: str) -> ScriptAnalysisResult:
        """
        Analyze a script file and return a risk assessment.

        Args:
            path: Absolute or relative path to the script file.

        Returns:
            ScriptAnalysisResult with risk level, findings, and recommended action.
        """
        abs_path = os.path.abspath(os.path.expanduser(path))

        if not os.path.isfile(abs_path):
            return ScriptAnalysisResult(
                path=abs_path,
                risk=ScriptRisk.DANGEROUS,
                findings=[ScriptFinding(
                    category="file_not_found",
                    description=f"Script file not found: {abs_path}",
                    severity="critical",
                )],
                recommended_action="deny",
                summary="Script file does not exist.",
            )

        try:
            source = Path(abs_path).read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            return ScriptAnalysisResult(
                path=abs_path,
                risk=ScriptRisk.DANGEROUS,
                findings=[ScriptFinding(
                    category="read_error",
                    description=f"Could not read script: {exc}",
                    severity="critical",
                )],
                recommended_action="deny",
                summary="Could not read script file.",
            )

        findings: List[ScriptFinding] = []
        suffix = Path(abs_path).suffix.lower()

        # Language-specific analysis
        if suffix == ".py":
            findings.extend(self._analyze_python(source))
        elif suffix in {".sh", ".bash", ".zsh", ".fish"}:
            findings.extend(self._analyze_shell(source))
        elif suffix in {".js", ".mjs", ".ts"}:
            findings.extend(self._analyze_node(source))

        # Always run generic raw-pattern pass
        findings.extend(self._analyze_raw(source))

        # Cross-check extracted paths/URLs against live rules.yaml
        if self._rule_engine is not None:
            findings.extend(self._check_paths_against_rules(source))
            findings.extend(self._check_urls_against_rules(source))

        # Deduplicate by (category, line, evidence)
        findings = _deduplicate(findings)

        # Compute overall risk and action
        risk, action = _compute_risk(findings)

        summary = _build_summary(findings, risk)

        return ScriptAnalysisResult(
            path=abs_path,
            risk=risk,
            findings=findings,
            recommended_action=action,
            summary=summary,
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Python AST analysis
    # ─────────────────────────────────────────────────────────────────────────

    def _analyze_python(self, source: str) -> List[ScriptFinding]:
        findings: List[ScriptFinding] = []

        try:
            tree = ast.parse(source)
        except SyntaxError as exc:
            findings.append(ScriptFinding(
                category="parse_error",
                description=f"Python syntax error (may be obfuscated): {exc}",
                severity="medium",
                evidence=str(exc),
            ))
            return findings

        for node in ast.walk(tree):
            # ── Import checks ─────────────────────────────────────────────
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                module = ""
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module = alias.name.split(".")[0]
                        self._check_import(module, node.lineno, findings)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    module = node.module.split(".")[0]
                    self._check_import(module, node.lineno, findings)

            # ── Call checks ───────────────────────────────────────────────
            elif isinstance(node, ast.Call):
                # Built-in dangerous calls: eval, exec, compile
                if isinstance(node.func, ast.Name):
                    name = node.func.id
                    if name in _PYTHON_CRITICAL_BUILTINS:
                        findings.append(ScriptFinding(
                            category="dangerous_call",
                            description=f"Dangerous built-in call: {name}()",
                            line=node.lineno,
                            severity="critical",
                            evidence=f"{name}(...)",
                        ))

                # Attribute calls: os.system(), subprocess.Popen(), etc.
                elif isinstance(node.func, ast.Attribute):
                    attr = node.func.attr
                    if isinstance(node.func.value, ast.Name):
                        obj = node.func.value.id
                        for (mod, func) in _PYTHON_CRITICAL_CALLS:
                            if obj == mod and attr == func:
                                findings.append(ScriptFinding(
                                    category="dangerous_call",
                                    description=f"Dangerous call: {obj}.{attr}()",
                                    line=node.lineno,
                                    severity="critical",
                                    evidence=f"{obj}.{attr}(...)",
                                ))

                # open() with write modes
                if isinstance(node.func, ast.Name) and node.func.id == "open":
                    mode_arg = _get_open_mode(node)
                    if mode_arg and any(m in mode_arg for m in ("w", "a", "x")):
                        findings.append(ScriptFinding(
                            category="file_access",
                            description=f"File opened for writing (mode={mode_arg!r})",
                            line=node.lineno,
                            severity="low",
                            evidence=f"open(..., {mode_arg!r})",
                        ))

        return findings

    def _check_import(self, module: str, lineno: int, findings: List[ScriptFinding]):
        if module in _PYTHON_CRITICAL_IMPORTS:
            findings.append(ScriptFinding(
                category="dangerous_import",
                description=f"Critical import '{module}': {_PYTHON_CRITICAL_IMPORTS[module]}",
                line=lineno,
                severity="critical",
                evidence=f"import {module}",
            ))
        elif module in _PYTHON_SUPERVISED_IMPORTS:
            findings.append(ScriptFinding(
                category="supervised_import",
                description=f"Sensitive import '{module}': {_PYTHON_SUPERVISED_IMPORTS[module]}",
                line=lineno,
                severity="medium",
                evidence=f"import {module}",
            ))

    # ─────────────────────────────────────────────────────────────────────────
    # Shell script analysis
    # ─────────────────────────────────────────────────────────────────────────

    def _analyze_shell(self, source: str) -> List[ScriptFinding]:
        return _apply_pattern_list(source, _SHELL_PATTERNS)

    # ─────────────────────────────────────────────────────────────────────────
    # Node.js analysis
    # ─────────────────────────────────────────────────────────────────────────

    def _analyze_node(self, source: str) -> List[ScriptFinding]:
        findings: List[ScriptFinding] = []
        node_critical = {
            "child_process": "Spawns child processes",
            "vm":            "Node.js sandbox escape via vm.runInNewContext",
            "cluster":       "Forking worker processes",
        }
        node_supervised = {
            "fs":            "Filesystem access",
            "net":           "Raw TCP/UDP sockets",
            "http":          "HTTP client/server",
            "https":         "HTTPS client/server",
            "dgram":         "UDP socket",
            "dns":           "DNS resolution",
            "crypto":        "Cryptographic operations",
            "process":       "Process-level control",
        }
        require_pattern = re.compile(
            r"""require\s*\(\s*['"]([^'"]+)['"]\s*\)""", re.MULTILINE
        )
        import_pattern = re.compile(
            r"""import\s+.*?\s+from\s+['"]([^'"]+)['"]""", re.MULTILINE
        )

        for pattern in (require_pattern, import_pattern):
            for m in pattern.finditer(source):
                module = m.group(1).split("/")[0]
                lineno = source[:m.start()].count("\n") + 1
                if module in node_critical:
                    findings.append(ScriptFinding(
                        category="dangerous_import",
                        description=f"Critical Node module '{module}': {node_critical[module]}",
                        line=lineno,
                        severity="critical",
                        evidence=m.group(0),
                    ))
                elif module in node_supervised:
                    findings.append(ScriptFinding(
                        category="supervised_import",
                        description=f"Sensitive Node module '{module}': {node_supervised[module]}",
                        line=lineno,
                        severity="medium",
                        evidence=m.group(0),
                    ))

        # eval() in JS is always suspicious
        for m in re.finditer(r"\beval\s*\(", source):
            lineno = source[:m.start()].count("\n") + 1
            findings.append(ScriptFinding(
                category="dangerous_call",
                description="eval() usage in JavaScript",
                line=lineno,
                severity="high",
                evidence=m.group(0),
            ))

        return findings

    # ─────────────────────────────────────────────────────────────────────────
    # Rule-engine cross-checks (path + URL)
    # ─────────────────────────────────────────────────────────────────────────

    def _check_paths_against_rules(self, source: str) -> List[ScriptFinding]:
        """
        Extract file paths from source and run each through the rule engine's
        check_file_path().  Reports denied or sensitive paths as findings.
        """
        findings: List[ScriptFinding] = []
        seen: set = set()

        for m in _SOURCE_PATH_RE.finditer(source):
            path = m.group('path') or m.group('shpath') or m.group('tildepath')
            if not path or path in seen:
                continue
            seen.add(path)

            lineno = source[:m.start()].count('\n') + 1
            result = self._rule_engine.check_file_path(path, operation='read')

            from .rules import ActionType
            if result.action == ActionType.DENY:
                findings.append(ScriptFinding(
                    category='file_access',
                    description=f"Script accesses denied path: {path} ({result.reason})",
                    line=lineno,
                    severity='critical',
                    evidence=path,
                ))
            elif result.action == ActionType.APPROVE:
                findings.append(ScriptFinding(
                    category='file_access',
                    description=f"Script accesses sensitive path: {path} ({result.reason})",
                    line=lineno,
                    severity='high',
                    evidence=path,
                ))

        return findings

    def _check_urls_against_rules(self, source: str) -> List[ScriptFinding]:
        """
        Extract URLs from source and run each through the rule engine's
        check_network().  Reports denied or unapproved domains as findings.
        """
        findings: List[ScriptFinding] = []
        seen: set = set()

        for m in _SOURCE_URL_RE.finditer(source):
            url = m.group('url')
            if not url or url in seen:
                continue
            seen.add(url)

            lineno = source[:m.start()].count('\n') + 1
            result = self._rule_engine.check_network(url)

            from .rules import ActionType
            if result.action == ActionType.DENY:
                findings.append(ScriptFinding(
                    category='network_call',
                    description=f"Script contacts denied domain/URL: {url} ({result.reason})",
                    line=lineno,
                    severity='critical',
                    evidence=url,
                ))
            elif result.action == ActionType.APPROVE:
                findings.append(ScriptFinding(
                    category='network_call',
                    description=f"Script contacts unapproved domain: {url} ({result.reason})",
                    line=lineno,
                    severity='high',
                    evidence=url,
                ))

        return findings

    # ─────────────────────────────────────────────────────────────────────────
    # Raw (language-agnostic) pattern pass
    # ─────────────────────────────────────────────────────────────────────────

    def _analyze_raw(self, source: str) -> List[ScriptFinding]:
        return _apply_pattern_list(source, _RAW_PATTERNS)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _apply_pattern_list(
    source: str,
    patterns: List[Tuple[str, str, str, str]],
) -> List[ScriptFinding]:
    findings = []
    for category, severity, description, pattern in patterns:
        for m in re.finditer(pattern, source, re.IGNORECASE | re.MULTILINE):
            lineno = source[:m.start()].count("\n") + 1
            findings.append(ScriptFinding(
                category=category,
                description=description,
                line=lineno,
                severity=severity,
                evidence=m.group(0)[:120],   # truncate long matches
            ))
    return findings


def _get_open_mode(call_node: ast.Call) -> Optional[str]:
    """Extract mode argument from an open() call node, if present."""
    # open(path, mode) or open(path, mode=...)
    if len(call_node.args) >= 2:
        arg = call_node.args[1]
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            return arg.value
    for kw in call_node.keywords:
        if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
            return kw.value.value
    return None


def _deduplicate(findings: List[ScriptFinding]) -> List[ScriptFinding]:
    """Remove findings with identical (category, line, evidence)."""
    seen = set()
    result = []
    for f in findings:
        key = (f.category, f.line, f.evidence)
        if key not in seen:
            seen.add(key)
            result.append(f)
    return result


def _compute_risk(findings: List[ScriptFinding]) -> Tuple[ScriptRisk, str]:
    """Derive overall ScriptRisk and recommended_action from findings."""
    if not findings:
        return ScriptRisk.SAFE, "allow"

    severities = {f.severity for f in findings}

    if "critical" in severities:
        return ScriptRisk.DANGEROUS, "deny"

    if "high" in severities:
        return ScriptRisk.SUSPICIOUS, "approve"

    # medium / low only
    has_medium = "medium" in severities
    if has_medium:
        return ScriptRisk.SUSPICIOUS, "approve"

    return ScriptRisk.SAFE, "allow"


def _build_summary(findings: List[ScriptFinding], risk: ScriptRisk) -> str:
    if not findings:
        return "No issues found."
    counts: dict = {}
    for f in findings:
        counts[f.severity] = counts.get(f.severity, 0) + 1
    parts = [f"{v} {k}" for k, v in sorted(counts.items())]
    return (
        f"Risk: {risk.value.upper()} | "
        f"Findings: {', '.join(parts)} | "
        f"Total: {len(findings)}"
    )
