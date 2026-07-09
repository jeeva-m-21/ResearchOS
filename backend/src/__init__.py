"""ResearchOS — Backend API.

NOTE: PYTHONPATH is set to /app/src (docker-compose.yml), but Python looks
for module ``src`` *inside* each path entry (e.g. /app/src/src/__init__.py).
Standalone scripts (``python script.py``) must add ``/app`` to sys.path
*before* project imports:

    import sys
    if "/app" not in sys.path:
        sys.path.insert(0, "/app")
    from xxx import yyy

Tests and uvicorn work automatically because CWD is /app.
"""
