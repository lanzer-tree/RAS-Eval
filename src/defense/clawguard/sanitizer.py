"""
Sensitive Information Sanitization Module (Sanitizer Module)
Automatically identifies and filters 15 types of sensitive information, supports bidirectional sanitization (input + output)
"""

import re
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import yaml


@dataclass
class SanitizerPattern:
    """Sanitization pattern definition"""
    name: str
    pattern: str
    replacement: str
    compiled: re.Pattern = None
    
    def __post_init__(self):
        self.compiled = re.compile(self.pattern)


class Sanitizer:
    """
    Sensitive Information Sanitization Engine
    
    Supports 15 types of sensitive information detection:
    - AWS Access Key / Secret Key
    - GitHub Token / GitLab Token
    - JWT Token / Bearer Token
    - SSH Private Keys
    - Database Connection Strings
    - API Key (generic pattern)
    - Slack / Stripe / SendGrid Token
    - Private Key (generic)
    - Password / Secret (in config files)
    """
    
    # Built-in default patterns
    DEFAULT_PATTERNS = [
        # AWS Access Key
        {
            "name": "aws_access_key",
            "pattern": r"(A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}",
            "replacement": "[AWS_ACCESS_KEY_REDACTED]"
        },
        # AWS Secret Key
        {
            "name": "aws_secret_key", 
            "pattern": r"(?i)aws(.{0,20})?['\"][0-9a-zA-Z/+=]{40}['\"]",
            "replacement": "[AWS_SECRET_KEY_REDACTED]"
        },
        # GitHub Token
        {
            "name": "github_token",
            "pattern": r"ghp_[A-Za-z0-9]{36}|gho_[A-Za-z0-9]{36}|ghu_[A-Za-z0-9]{36}|ghs_[A-Za-z0-9]{36}|ghr_[A-Za-z0-9]{36}",
            "replacement": "[GITHUB_TOKEN_REDACTED]"
        },
        # GitLab Token
        {
            "name": "gitlab_token",
            "pattern": r"glpat-[A-Za-z0-9\-_]{20}",
            "replacement": "[GITLAB_TOKEN_REDACTED]"
        },
        # JWT Token
        {
            "name": "jwt_token",
            "pattern": r"eyJ[A-Za-z0-9-_=]+\.eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_.+/=]*",
            "replacement": "[JWT_TOKEN_REDACTED]"
        },
        # Bearer Token
        {
            "name": "bearer_token",
            "pattern": r"(?i)bearer\s+[A-Za-z0-9\-._~+/]+=*",
            "replacement": "[BEARER_TOKEN_REDACTED]"
        },
        # SSH Private Key
        {
            "name": "ssh_private_key",
            "pattern": r"-----BEGIN (?:RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----[\s\S]*?-----END (?:RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----",
            "replacement": "[SSH_PRIVATE_KEY_REDACTED]"
        },
        # Database Connection String
        {
            "name": "db_connection_string",
            "pattern": r"(?i)(mysql|postgres|mongodb|redis|postgresql)://[^\s'\"]+:[^\s'\"]+@[^\s'\"]+",
            "replacement": "[DB_CONNECTION_REDACTED]"
        },
        # Generic API Key
        {
            "name": "api_key",
            "pattern": r"(?i)(api[_-]?key|apikey)\s*[=:]\s*['\"][A-Za-z0-9\-_]{20,}['\"]",
            "replacement": "[API_KEY_REDACTED]"
        },
        # Slack Token
        {
            "name": "slack_token",
            "pattern": r"xox[baprs]-[0-9]{10,13}-[0-9]{10,13}-[A-Za-z0-9]{24}",
            "replacement": "[SLACK_TOKEN_REDACTED]"
        },
        # Stripe Key
        {
            "name": "stripe_key",
            "pattern": r"(?i)sk_live_[0-9a-zA-Z]{24}|rk_live_[0-9a-zA-Z]{24}",
            "replacement": "[STRIPE_KEY_REDACTED]"
        },
        # SendGrid Token
        {
            "name": "sendgrid_token",
            "pattern": r"SG\.[A-Za-z0-9\-_]{22}\.[A-Za-z0-9\-_]{43}",
            "replacement": "[SENDGRID_TOKEN_REDACTED]"
        },
        # Private Key (Generic)
        {
            "name": "private_key",
            "pattern": r"-----BEGIN PRIVATE KEY-----[\s\S]*?-----END PRIVATE KEY-----",
            "replacement": "[PRIVATE_KEY_REDACTED]"
        },
        # Password
        {
            "name": "password",
            "pattern": r"(?i)(password|passwd|pwd)\s*[=:]\s*['\"][^'\"]{8,}['\"]",
            "replacement": "[PASSWORD_REDACTED]"
        },
        # Secret/Token generic
        {
            "name": "secret_token",
            "pattern": r"(?i)(secret|token)\s*[=:]\s*['\"][A-Za-z0-9\-_]{16,}['\"]",
            "replacement": "[SECRET_REDACTED]"
        },
    ]
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        patterns: Optional[List[Dict]] = None,
        skill_whitelist: Optional[List[str]] = None,
        enabled: bool = True,
        input_sanitization: bool = True,
        output_sanitization: bool = True,
    ):
        """
        Initialize sanitization engine
        
        Args:
            config: Configuration dictionary (loaded from rules.yaml)
            patterns: Custom pattern list
            skill_whitelist: Skill whitelist (exempt from sanitization)
            enabled: Whether sanitization is enabled
            input_sanitization: Whether to sanitize input
            output_sanitization: Whether to sanitize output
        """
        self.enabled = enabled
        self.input_sanitization = input_sanitization
        self.output_sanitization = output_sanitization
        self.skill_whitelist = set(skill_whitelist or [])
        self.patterns: List[SanitizerPattern] = []
        
        # Load patterns
        if patterns:
            self._load_patterns(patterns)
        else:
            self._load_patterns(self.DEFAULT_PATTERNS)
    
    def _load_patterns(self, patterns):
        """Load sanitization patterns
        
        Supports two formats:
        1. List format: [{"name": "...", "pattern": "...", "replacement": "..."}]
        2. Dict format: {"name": {"pattern": "...", "replacement": "..."}}  (from YAML config)
        """
        # Convert dict format to list format
        if isinstance(patterns, dict):
            patterns = [
                {"name": k, "pattern": v["pattern"], "replacement": v["replacement"]}
                for k, v in patterns.items()
                if isinstance(v, dict) and "pattern" in v and "replacement" in v
            ]
        
        for p in patterns:
            try:
                sp = SanitizerPattern(
                    name=p["name"],
                    pattern=p["pattern"],
                    replacement=p["replacement"]
                )
                self.patterns.append(sp)
            except Exception as e:
                print(f"Warning: Failed to load pattern {p.get('name')}: {e}")
    
    def sanitize(self, text: str, skill_name: Optional[str] = None) -> str:
        """
        Sanitize sensitive information in text
        
        Args:
            text: Text to sanitize
            skill_name: Skill name (if in whitelist, skip sanitization)
            
        Returns:
            Sanitized text
        """
        if not self.enabled:
            return text
        
        # Check whitelist
        if skill_name and skill_name in self.skill_whitelist:
            return text
        
        # Apply all patterns
        result = text
        for pattern in self.patterns:
            result = pattern.compiled.sub(pattern.replacement, result)
        
        return result
    
    def sanitize_input(self, text: str, skill_name: Optional[str] = None) -> str:
        """Sanitize input"""
        if not self.input_sanitization:
            return text
        return self.sanitize(text, skill_name)
   
    def sanitize_output(self, text: str, skill_name: Optional[str] = None) -> str:
        """Sanitize output"""
        if not self.output_sanitization:
            return text
        return self.sanitize(text, skill_name)
    
    def detect_secrets(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect sensitive information in text (no sanitization, only return detection results)
        
        Args:
            text: Text to detect
            
        Returns:
            List of detected sensitive information
        """
        detected = []
        
        for pattern in self.patterns:
            matches = pattern.compiled.finditer(text)
            for match in matches:
                detected.append({
                    "type": pattern.name,
                    "value": match.group()[:20] + "..." if len(match.group()) > 20 else match.group(),
                    "start": match.start(),
                    "end": match.end(),
                })
        
        return detected
    
    def add_pattern(self, name: str, pattern: str, replacement: str):
        """Dynamically add sanitization pattern"""
        sp = SanitizerPattern(name=name, pattern=pattern, replacement=replacement)
        self.patterns.append(sp)
    
    def add_to_whitelist(self, skill_name: str):
        """Add Skill to whitelist"""
        self.skill_whitelist.add(skill_name)
    
    def remove_from_whitelist(self, skill_name: str):
        """Remove Skill from whitelist"""
        self.skill_whitelist.discard(skill_name)
    
    @classmethod
    def from_config(cls, config_path: str) -> "Sanitizer":
        """Create instance from config file"""
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        sanitizer_config = config.get('sanitizer_rules', {})
        
        return cls(
            enabled=sanitizer_config.get('enabled', True),
            patterns=sanitizer_config.get('patterns'),
            skill_whitelist=sanitizer_config.get('skill_whitelist', []),
        )
