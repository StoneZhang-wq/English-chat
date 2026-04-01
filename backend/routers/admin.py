"""Compatibility export. Prefer `api.routes.admin`."""
from api.routes.admin import router

__all__ = ["router"]
