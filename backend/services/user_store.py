"""Compatibility wrapper. Prefer `services.user_service`."""
from services.user_service import user_service as store

__all__ = ["store"]
