"""
security/checks.py — Security layer.

1. Input sanitisation — validate user claim before hitting the agent
2. Tool output sanitisation — strip prompt injection from fetched content
"""

import re

MAX_CLAIM_LENGTH = 300
MIN_CLAIM_LENGTH = 10

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"you\s+are\s+now\s+a?\s+different",
    r"new\s+instructions?:",
    r"system\s*:",
    r"<\s*system\s*>",
    r"disregard\s+(all\s+)?",
    r"forget\s+(all\s+)?previous",
    r"act\s+as\s+(if\s+you\s+are\s+)?a?\s+different",
    r"your\s+new\s+(role|task|job|instructions?)",
]
COMPILED_INJECTION = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]

TOOL_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"new\s+task\s*:",
    r"system\s+prompt\s*:",
    r"you\s+are\s+now",
    r"disregard\s+(all\s+)?previous",
    r"<\s*/?system\s*>",
    r"<\s*/?instructions?\s*>",
    r"\[\s*system\s*\]",
    r"print\s+(your\s+)?(system\s+)?prompt",
    r"reveal\s+(your\s+)?(system\s+)?instructions",
]
COMPILED_TOOL_INJECTION = [re.compile(p, re.IGNORECASE) for p in TOOL_INJECTION_PATTERNS]


class InputValidationError(ValueError):
    pass


def sanitise_claim(claim: str) -> str:
    """Validate and sanitise user claim. Raises InputValidationError if invalid."""
    if not claim or not claim.strip():
        raise InputValidationError("Please enter a claim to investigate.")

    claim = claim.strip()

    if len(claim) < MIN_CLAIM_LENGTH:
        raise InputValidationError(
            f"Claim is too short (minimum {MIN_CLAIM_LENGTH} characters)."
        )
    if len(claim) > MAX_CLAIM_LENGTH:
        raise InputValidationError(
            f"Claim is too long (maximum {MAX_CLAIM_LENGTH} characters). "
            "Please enter a concise claim."
        )
    for pattern in COMPILED_INJECTION:
        if pattern.search(claim):
            raise InputValidationError(
                "That doesn't look like a scientific claim. "
                "Try something like 'Coffee causes cancer' or 'Vitamin C prevents colds'."
            )
    return claim


def sanitise_tool_output(content: str, source: str = "unknown") -> str:
    """Strip prompt injection attempts from tool-fetched content."""
    if not content:
        return content

    lines = content.split("\n")
    sanitised = []
    redacted = 0

    for line in lines:
        if any(p.search(line) for p in COMPILED_TOOL_INJECTION):
            sanitised.append("[REDACTED: potential prompt injection]")
            redacted += 1
        else:
            sanitised.append(line)

    result = "\n".join(sanitised)
    if redacted:
        result = (
            f"[SECURITY: {redacted} line(s) redacted from {source}]\n\n" + result
        )
    return result