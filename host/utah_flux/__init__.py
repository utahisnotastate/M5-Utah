"""Utah-Flux: visual Lego-style hardware intent composer for M5Stack."""

from .bricks import BRICK_CATALOG, get_brick
from .compiler import compile_project
from .project import FluxProject

__version__ = "0.3.0"

__all__ = [
    "BRICK_CATALOG",
    "FluxProject",
    "compile_project",
    "get_brick",
]
