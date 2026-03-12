"""
FastAPI dependency injection for database sessions.

Provides proper session lifecycle management via Depends().
"""
from app.db.session import get_db

# Re-export for clean imports
__all__ = ["get_db"]
