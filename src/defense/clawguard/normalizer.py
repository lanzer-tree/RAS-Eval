"""
Command Normalization Module
Normalizes and expands shell commands to detect obfuscated attacks
"""

import re
import shlex
from typing import List, Tuple


class CommandNormalizer:
    """
    Normalizes shell commands to detect obfuscation attempts
    
    Handles:
    - Quote removal and escaping
    - Command substitution expansion
    - Variable expansion detection
    - Encoding detection (hex, base64, octal)
    - IFS delimiter abuse
    - Backslash escape removal
    """
    
    def __init__(self):
        self.encoding_patterns = [
            # Hex encoding
            (r'\\x([0-9a-fA-F]{2})', 'hex'),
            # Octal encoding
            (r'\\([0-7]{3})', 'octal'),
            # Unicode escapes
            (r'\\u([0-9a-fA-F]{4})', 'unicode'),
        ]
    
    def normalize(self, command: str) -> Tuple[str, List[str]]:
        """
        Normalize command and return both normalized version and warnings
        
        Args:
            command: Original command string
            
        Returns:
            Tuple of (normalized_command, warnings)
        """
        warnings = []
        normalized = command
        
        # Step 1: Detect and flag suspicious patterns
        if self._has_command_substitution(normalized):
            warnings.append("command_substitution_detected")
        
        if self._has_encoding(normalized):
            warnings.append("encoding_detected")
            
        if self._has_ifs_abuse(normalized):
            warnings.append("ifs_delimiter_abuse")
        
        # Step 2: Remove obfuscation
        normalized = self._remove_quotes(normalized)
        normalized = self._remove_backslashes(normalized)
        normalized = self._expand_simple_vars(normalized)
        
        # Step 3: Detect base64
        if 'base64' in normalized and ('|' in normalized or '`' in normalized):
            warnings.append("base64_pipeline_detected")
        
        return normalized, warnings
    
    def _has_command_substitution(self, cmd: str) -> bool:
        """Detect command substitution patterns"""
        patterns = [
            r'\$\(',  # $(...)
            r'`',     # `...`
        ]
        return any(re.search(p, cmd) for p in patterns)
    
    def _has_encoding(self, cmd: str) -> bool:
        """Detect encoding patterns"""
        for pattern, _ in self.encoding_patterns:
            if re.search(pattern, cmd):
                return True
        return False
    
    def _has_ifs_abuse(self, cmd: str) -> bool:
        """Detect IFS delimiter abuse"""
        return bool(re.search(r'\$\{IFS\}|\$IFS', cmd))
    
    def _remove_quotes(self, cmd: str) -> str:
        """Remove single and double quotes"""
        # Remove empty quotes
        cmd = re.sub(r"''", '', cmd)
        cmd = re.sub(r'""', '', cmd)
        
        # Remove quotes around words (simple case)
        cmd = re.sub(r"'([^']*)'", r'\1', cmd)
        cmd = re.sub(r'"([^"]*)"', r'\1', cmd)
        
        return cmd
    
    def _remove_backslashes(self, cmd: str) -> str:
        """Remove backslash escapes"""
        # Remove backslash before common characters
        cmd = re.sub(r'\\([a-zA-Z0-9\s\-_/.])', r'\1', cmd)
        return cmd
    
    def _expand_simple_vars(self, cmd: str) -> str:
        """Expand simple variable references (detection only)"""
        # Flag common obfuscation variables
        expansions = {
            '${IFS}': ' ',
            '$IFS': ' ',
            '${PATH}': '/usr/bin:/bin',
        }
        
        for var, value in expansions.items():
            cmd = cmd.replace(var, value)
        
        return cmd
    
    def detect_obfuscation_level(self, command: str) -> str:
        """
        Detect obfuscation level
        
        Returns: 'none', 'low', 'medium', 'high'
        """
        score = 0
        
        # Check for various obfuscation techniques
        if self._has_command_substitution(command):
            score += 2
        
        if self._has_encoding(command):
            score += 3
        
        if self._has_ifs_abuse(command):
            score += 2
        
        # Quote mixing
        if "'" in command and '"' in command:
            score += 1
        
        # Empty quotes
        if "''" in command or '""' in command:
            score += 1
        
        # Backslash escapes
        if re.search(r'\\[a-zA-Z]', command):
            score += 1
        
        # Base64 in pipeline
        if 'base64' in command and ('|' in command or '`' in command):
            score += 3
        
        # Eval usage
        if 'eval' in command.lower():
            score += 2
        
        # Hex sequences
        if re.search(r'\\x[0-9a-fA-F]{2}', command):
            score += 2
        
        if score == 0:
            return 'none'
        elif score <= 2:
            return 'low'
        elif score <= 5:
            return 'medium'
        else:
            return 'high'
    
    def get_suspicious_patterns(self, command: str) -> List[str]:
        """Get list of suspicious patterns found in command"""
        patterns = []
        
        if re.search(r'\$\(.*?\)', command):
            patterns.append('command_substitution_dollar')
        
        if '`' in command:
            patterns.append('command_substitution_backtick')
        
        if re.search(r'\\x[0-9a-fA-F]{2}', command):
            patterns.append('hex_encoding')
        
        if re.search(r'\\[0-7]{3}', command):
            patterns.append('octal_encoding')
        
        if 'base64' in command and '|' in command:
            patterns.append('base64_decode_pipeline')
        
        if 'eval' in command.lower():
            patterns.append('eval_usage')
        
        if re.search(r'\${?IFS}?', command):
            patterns.append('ifs_abuse')
        
        if "''" in command or '""' in command:
            patterns.append('empty_quotes')
        
        if re.search(r'\\[a-z]', command, re.IGNORECASE):
            patterns.append('backslash_escaping')
        
        return patterns
