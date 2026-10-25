"""Main entrypoint for the Tamil Reel Script Agent API backend.

Runs the FastAPI application using Uvicorn.
"""

import sys
import io

# Ensure UTF-8 output encoding across Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import uvicorn


def start_server():
    """Start the Uvicorn ASGI server hosting the FastAPI application."""
    print(">> Starting Tamil Reel Script Agent API Backend on http://localhost:8000")
    print(">> Interactive Swagger Documentation: http://localhost:8000/docs")
    print(">> ReDoc Schema: http://localhost:8000/redoc\n")
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    start_server()
