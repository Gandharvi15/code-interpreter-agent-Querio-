# safety.py

# ── Dangerous keywords to block ──────────────────────────────────
BLOCKED_KEYWORDS = [
    "import os",
    "import sys",
    "import subprocess",
    "import shutil",
    "import socket",
    "open(",          # file read/write
    "exec(",          # dynamic code execution
    "eval(",          # dynamic code evaluation
    "__import__",     # dynamic imports
    "os.system",
    "os.remove",
    "os.rmdir",
    "shutil.rmtree",
    "subprocess.call",
    "subprocess.run",
]

def is_safe(code: str) -> tuple[bool, str]:
    """
    Check if generated code is safe to run.
    Returns (True, "") if safe, (False, reason) if not.
    """
    code_lower = code.lower()

    for keyword in BLOCKED_KEYWORDS:
        if keyword.lower() in code_lower:
            return False, f"Blocked keyword detected: '{keyword}'"

    return True, ""


def safety_report() -> str:
    """Returns a human-readable list of what's blocked."""
    return "\n".join([f"• {k}" for k in BLOCKED_KEYWORDS])