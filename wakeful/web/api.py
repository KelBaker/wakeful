"""API FastAPI que serve o dashboard e faz CRUD de tarefas em cima do Runtime."""
from __future__ import annotations

import threading
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from wakeful.config import TaskConfig
from wakeful.executor import run_task
from wakeful.runtime import Runtime
from wakeful.state import state_store

STATIC_DIR = Path(__file__).parent / "static"


class TaskIn(BaseModel):
    name: str
    command: list[str]
    cron: str
    timeout_seconds: int = 600
    retries: int = 0
    working_dir: str = "."


def create_app(runtime: Runtime) -> FastAPI:
    app = FastAPI(title="wakeful")

    @app.get("/api/tasks")
    def list_tasks():
        return [_task_to_dict(t, runtime) for t in runtime.config.tasks]

    @app.post("/api/tasks", status_code=201)
    def create_task(task_in: TaskIn):
        if any(t.name == task_in.name for t in runtime.config.tasks):
            raise HTTPException(409, f"Já existe uma tarefa chamada '{task_in.name}'")
        runtime.config.tasks.append(TaskConfig(**task_in.model_dump()))
        _persist_and_reload(runtime)
        return _task_to_dict(_find(runtime, task_in.name), runtime)

    @app.put("/api/tasks/{name}")
    def update_task(name: str, task_in: TaskIn):
        existing = _find(runtime, name)
        if existing is None:
            raise HTTPException(404, f"Tarefa '{name}' não encontrada")
        idx = runtime.config.tasks.index(existing)
        runtime.config.tasks[idx] = TaskConfig(**task_in.model_dump())
        _persist_and_reload(runtime)
        return _task_to_dict(_find(runtime, task_in.name), runtime)

    @app.delete("/api/tasks/{name}", status_code=204)
    def delete_task(name: str):
        existing = _find(runtime, name)
        if existing is None:
            raise HTTPException(404, f"Tarefa '{name}' não encontrada")
        runtime.config.tasks.remove(existing)
        _persist_and_reload(runtime)

    @app.post("/api/tasks/{name}/run")
    def run_now(name: str):
        task = _find(runtime, name)
        if task is None:
            raise HTTPException(404, f"Tarefa '{name}' não encontrada")
        # dispara em thread separada — a requisição HTTP não espera a tarefa terminar
        threading.Thread(target=run_task, args=(task,), daemon=True).start()
        return {"status": "disparada"}

    @app.get("/api/tasks/{name}/log")
    def task_log(name: str, lines: int = 200):
        log_dir = Path(runtime.config.logging.dir)
        today_log = log_dir / f"{datetime.now():%Y-%m-%d}.log"
        if not today_log.exists():
            return {"lines": []}
        all_lines = today_log.read_text(encoding="utf-8", errors="replace").splitlines()
        relevant = [ln for ln in all_lines if f"'{name}'" in ln or f"[{name}]" in ln]
        return {"lines": relevant[-lines:]}

    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")

    return app


def _find(runtime: Runtime, name: str) -> TaskConfig | None:
    return next((t for t in runtime.config.tasks if t.name == name), None)


def _persist_and_reload(runtime: Runtime) -> None:
    runtime.save()
    runtime.reload()


def _task_to_dict(task: TaskConfig, runtime: Runtime) -> dict:
    job = runtime.scheduler.get_job(task.name)
    run = state_store.get(task.name)

    status = "nunca-rodou"
    if run is not None:
        if run.finished_at is None:
            status = "rodando"
        else:
            status = "sucesso" if run.success else "falha"

    return {
        "name": task.name,
        "command": task.command,
        "cron": task.cron,
        "timeout_seconds": task.timeout_seconds,
        "retries": task.retries,
        "working_dir": task.working_dir,
        "next_run": job.next_run_time.isoformat() if job and job.next_run_time else None,
        "status": status,
        "last_run": run.started_at.isoformat() if run else None,
    }
