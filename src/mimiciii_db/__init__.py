from typing import Callable, Dict

from .db import DB

_registry: Dict[str, Callable] = {}


def registry(name: str):
    """Decorator to register a query globally in the package registry."""

    def _decorator(fn: Callable):
        _registry[name] = fn
        return fn

    return _decorator


# user can only import DB and registry
__all__ = ["DB", "registry"]
