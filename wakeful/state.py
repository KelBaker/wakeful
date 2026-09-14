"""Estado em runtime das tarefas (última execução, status) — em memória.

Não precisa persistir em disco: se o wakeful reiniciar, o histórico de
execução também reseta, e isso é aceitável (os logs em arquivo continuam
existindo pra auditoria). Guardar só em memória evita lidar com concorrência
de escrita em arquivo entre o scheduler e a UI.
"""
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TaskRun:
    started_at: datetime
    finished_at: datetime | None = None
    success: bool | None = None  # None enquanto ainda está rodando


class StateStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._runs: dict[str, TaskRun] = {}

    def start(self, task_name: str) -> None:
        with self._lock:
            self._runs[task_name] = TaskRun(started_at=datetime.now())

    def finish(self, task_name: str, success: bool) -> None:
        with self._lock:
            run = self._runs.get(task_name)
            if run is None:
                run = TaskRun(started_at=datetime.now())
                self._runs[task_name] = run
            run.finished_at = datetime.now()
            run.success = success

    def get(self, task_name: str) -> TaskRun | None:
        with self._lock:
            return self._runs.get(task_name)


# instância única compartilhada entre scheduler e API — processo único, sem IPC
state_store = StateStore()
