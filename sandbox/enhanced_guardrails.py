"""
Enhanced Guardrails for Agent Evaluator.

Provides offline input sanitization, prompt injection detection,
and PII/secret pattern redactors.
"""

import re
from typing import Dict, Any, List, Tuple


class EnhancedGuardrails:
    """
    Offline deterministic guardrail checks.
    Evaluates inputs and outputs for security and privacy violations.
    """

    INJECTION_PATTERNS = [
        re.compile(r"ignore\s+(?:all\s+)?(?:previous|prior)\s+instructions", re.IGNORECASE),
        re.compile(r"dump\s+(?:all\s+)?(?:system|admin|secret)\s+(?:keys|passwords)", re.IGNORECASE),
        re.compile(r"system\s*:\s*you\s+are\s+now", re.IGNORECASE),
        re.compile(r"bypass\s+(?:safety|guardrails|filters)", re.IGNORECASE),
    ]

    SECRET_PATTERNS = [
        (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "[REDACTED_EMAIL]"),
        (re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"), "[REDACTED_PHONE]"),
        (re.compile(r"\b(?:sk|pk)_(?:live|test)_[A-Za-z0-9]{20,}\b"), "[REDACTED_API_KEY]"),
        (re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"), "[REDACTED_CARD]"),
    ]

    @classmethod
    def check_prompt_injection(cls, prompt: str) -> Tuple[bool, List[str]]:
        """
        Check if a user prompt contains known prompt injection or jailbreak patterns.
        Returns: (is_injection_detected, matched_patterns)
        """
        if not isinstance(prompt, str):
            return False, []

        matches = []
        for pattern in cls.INJECTION_PATTERNS:
            if pattern.search(prompt):
                matches.append(pattern.pattern)

        return len(matches) > 0, matches

    @classmethod
    def redact_pii(cls, text: str) -> str:
        """
        Redact sensitive PII and credentials from a text string.
        """
        if not isinstance(text, str):
            return text

        redacted = text
        for pattern, replacement in cls.SECRET_PATTERNS:
            redacted = pattern.sub(replacement, redacted)

        return redacted

    @classmethod
    def sanitize_arguments(cls, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively sanitize dictionary arguments for trace persistence.
        """
        if not isinstance(arguments, dict):
            return arguments

        sanitized = {}
        for key, value in arguments.items():
            if isinstance(value, str):
                sanitized[key] = cls.redact_pii(value)
            elif isinstance(value, dict):
                sanitized[key] = cls.sanitize_arguments(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    cls.redact_pii(v) if isinstance(v, str)
                    else cls.sanitize_arguments(v) if isinstance(v, dict)
                    else v
                    for v in value
                ]
            else:
                sanitized[key] = value

        return sanitized
