"""Shared utilities for the Tamil Reel Script Agent."""

import sys
import io


def setup_utf8_console():
    """Ensure standard output and error streams use UTF-8 encoding on Windows consoles.
    
    Prevents UnicodeEncodeError when logging Tamil script characters and emojis.
    """
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
