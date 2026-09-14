"""Junta config + scheduler num único objeto, compartilhado entre a API e a UI.

Existe pra que tanto o modo headless (`wakeful`) quanto o modo com janela
(`wakeful-ui`) montem o scheduler do mesmo jeito, sem duplicar lógica.
"""
from __future__ import annotations

import logging
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler

from wakeful.config import AppConfig, load_config, save_config
from wakeful.logging_setup import setup_logging
from wakeful.scheduler import build_scheduler

logger = logging.getLogger("wakeful.runtime")


class Runtime:
    def __init__(self, config_path: str | Path):
        self.config_path = Path(config_path)
        self.config: AppConfig = load_config(self.config_path)
        setup_logging(self.config.logging)
        self.scheduler: BackgroundScheduler = build_scheduler(self.config)

    def start(self) -> None:
        self.scheduler.start()
        logger.info("Scheduler iniciado com %d tarefa(s).", len(self.config.tasks))

    def shutdown(self) -> None:
        self.scheduler.shutdown(wait=False)

    def reload(self) -> None:
        """Recarrega o config.yaml do disco e reconstrói os jobs — chamado após
        criar/editar/apagar tarefa pela UI, pra não precisar reiniciar o processo."""
        self.config = load_config(self.config_path)
        self.scheduler.remove_all_jobs()
        new_scheduler = build_scheduler(self.config)
        for job in new_scheduler.get_jobs():
            self.scheduler.add_job(
                job.func,
                trigger=job.trigger,
                id=job.id,
                name=job.name,
                max_instances=1,
                coalesce=True,
                misfire_grace_time=60,
            )
        logger.info("Config recarregado: %d tarefa(s).", len(self.config.tasks))

    def save(self) -> None:
        save_config(self.config, self.config_path)
