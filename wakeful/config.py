"""Carrega e valida o config.yaml do usuário."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class TaskConfig:
    name: str
    command: list[str]
    cron: str
    timeout_seconds: int = 600
    retries: int = 0
    working_dir: str = "."


@dataclass
class LoggingConfig:
    dir: str = "logs"
    level: str = "INFO"


@dataclass
class AppConfig:
    tasks: list[TaskConfig] = field(default_factory=list)
    logging: LoggingConfig = field(default_factory=LoggingConfig)


def load_config(path: str | Path) -> AppConfig:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Config não encontrado em {path}. Copie config.example.yaml para config.yaml."
        )

    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    logging_raw = raw.get("logging", {})
    logging_cfg = LoggingConfig(
        dir=logging_raw.get("dir", "logs"),
        level=logging_raw.get("level", "INFO"),
    )

    tasks_raw = raw.get("tasks", [])
    tasks: list[TaskConfig] = []
    seen_names: set[str] = set()
    for i, t in enumerate(tasks_raw):
        _require(t, "name", i)
        _require(t, "command", i)
        _require(t, "cron", i)

        if t["name"] in seen_names:
            raise ValueError(f"Nome de tarefa duplicado no config: '{t['name']}'")
        seen_names.add(t["name"])

        tasks.append(
            TaskConfig(
                name=t["name"],
                command=list(t["command"]),
                cron=t["cron"],
                timeout_seconds=int(t.get("timeout_seconds", 600)),
                retries=int(t.get("retries", 0)),
                working_dir=t.get("working_dir", "."),
            )
        )

    return AppConfig(tasks=tasks, logging=logging_cfg)


def _require(task_dict: dict, key: str, index: int) -> None:
    if key not in task_dict:
        raise ValueError(f"Tarefa #{index} no config está sem o campo obrigatório '{key}'")


def save_config(config: AppConfig, path: str | Path) -> None:
    """Persiste o AppConfig de volta pro YAML — usado pela UI ao criar/editar tarefa."""
    raw = {
        "logging": {"dir": config.logging.dir, "level": config.logging.level},
        "tasks": [
            {
                "name": t.name,
                "command": t.command,
                "cron": t.cron,
                "timeout_seconds": t.timeout_seconds,
                "retries": t.retries,
                "working_dir": t.working_dir,
            }
            for t in config.tasks
        ],
    }
    Path(path).write_text(
        yaml.safe_dump(raw, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
