"""Minimal shim for missing stdlib imghdr on some Python builds.

Provides a very small `what()` implementation returning None for unknown
content — enough for libraries that only query image type.
"""
from typing import Optional


def what(file, h: Optional[bytes] = None) -> Optional[str]:
    return None
