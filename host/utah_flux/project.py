from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class FluxProject:
    name: str = "Untitled Project"
    bricks: list[dict[str, Any]] = field(default_factory=list)
    links: list[dict[str, str]] = field(default_factory=list)
    version: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "name": self.name,
            "bricks": self.bricks,
            "links": self.links,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FluxProject:
        return cls(
            name=data.get("name", "Untitled Project"),
            bricks=list(data.get("bricks", [])),
            links=list(data.get("links", [])),
            version=int(data.get("version", 1)),
        )

    def save(self, path: Path) -> None:
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> FluxProject:
        return cls.from_dict(json.loads(path.read_text(encoding="utf-8")))
