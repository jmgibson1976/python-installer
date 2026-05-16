from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Answers:
    """Collected answers from the interactive project wizard."""

    # Core identity
    project_name: str = ""
    version: str = "0.0.1"
    target_path: str = ""

    # Infrastructure
    git: bool = True
    docker: bool = False

    # Data layer
    db_driver: str = "none"
    db_abstraction: str = "none"

    # Testing
    testing_frameworks: list[str] = field(default_factory=lambda: ["pytest"])

    # Runtime config
    logging: bool = True
    env_parsing: str = "dotenv"
    cli_support: str = "none"

    # Dev tooling
    optional_deps: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "project_name": self.project_name,
            "version": self.version,
            "target_path": self.target_path,
            "git": self.git,
            "docker": self.docker,
            "db_driver": self.db_driver,
            "db_abstraction": self.db_abstraction,
            "testing_frameworks": self.testing_frameworks,
            "logging": self.logging,
            "env_parsing": self.env_parsing,
            "cli_support": self.cli_support,
            "optional_deps": self.optional_deps,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Answers":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
