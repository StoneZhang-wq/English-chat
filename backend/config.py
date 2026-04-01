"""Compatibility exports. Prefer `core.settings` for new code."""
from core.settings import Settings, get_settings, load_settings

__all__ = ["Settings", "get_settings", "load_settings"]
