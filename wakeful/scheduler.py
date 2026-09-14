"""Monta o BackgroundScheduler a partir do AppConfig e liga cada tarefa ao executor."""
from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from wakeful.config import AppConfig, TaskConfig
from wakeful.executor import run_task

logger = logging.getLogger("wakeful.scheduler")


def _cron_trigger(expr: str) -> CronTrigger:
    # cron de 5 campos, formato crontab clássico: minuto hora dia mes dia-semana
    fields = expr.split()
    if len(fields) != 5:
        raise ValueError(
            f"Expressão cron inválida '{expr}' — esperado 5 campos (min hora dia mes dia-semana)"
        )
    minute, hour, day, month, day_of_week = fields
    return CronTrigger(minute=minute, hour=hour, day=day, month=month, day_of_week=day_of_week)


def build_scheduler(config: AppConfig) -> BackgroundScheduler:
    scheduler = BackgroundScheduler()

    for task in config.tasks:
        scheduler.add_job(
            _make_job(task),
            trigger=_cron_trigger(task.cron),
            id=task.name,
            name=task.name,
            # se a execução anterior ainda está rodando, não empilha uma nova por cima
            max_instances=1,
            coalesce=True,
            misfire_grace_time=60,
        )
        logger.info("Tarefa registrada: '%s' (cron: %s)", task.name, task.cron)

    return scheduler


def _make_job(task: TaskConfig):
    def job() -> None:
        run_task(task)

    return job
