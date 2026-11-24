"""CipherCraft opaque-envelope messenger; stdlib WSGI and SQLite."""
from .app import create_app

__all__ = ["create_app"]
