"""Main entrypoint for the Tamil Reel Script Agent API backend.

Runs the FastAPI application using Uvicorn.
"""

from src.utils import setup_utf8_console

setup_utf8_console()

import uvicorn


def start_server():
    """Start the Uvicorn ASGI server hosting the FastAPI application."""
    print(">> Starting Tamil Reel Script Agent API Backend on http://localhost:8000")
    print(">> Interactive Swagger Documentation: http://localhost:8000/docs")
    print(">> ReDoc Schema: http://localhost:8000/redoc\n")
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    start_server()
