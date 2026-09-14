"""Execução de tarefas: dispara o subprocesso, aplica timeout e retry, loga resultado."""
from __future__ import annotations

import logging
import subprocess
import time

from wakeful.config import TaskConfig

logger = logging.getLogger("wakeful.executor")


def run_task(task: TaskConfig) -> bool:
    """Roda a tarefa (com retries). Retorna True se terminou com sucesso."""
    attempts = task.retries + 1

    for attempt in range(1, attempts + 1):
        logger.info("Iniciando '%s' (tentativa %d/%d)", task.name, attempt, attempts)
        start = time.monotonic()
        try:
            result = subprocess.run(
                task.command,
                cwd=task.working_dir,
                timeout=task.timeout_seconds,
                capture_output=True,
                text=True,
            )
        except subprocess.TimeoutExpired:
            elapsed = time.monotonic() - start
            logger.error(
                "'%s' estourou o timeout de %ds (rodou %.1fs)",
                task.name, task.timeout_seconds, elapsed,
            )
            continue
        except OSError as exc:
            # comando não encontrado, permissão negada etc — não adianta tentar de novo
            logger.error("'%s' falhou ao iniciar: %s", task.name, exc)
            return False

        elapsed = time.monotonic() - start

        if result.stdout:
            logger.info("[%s] stdout:\n%s", task.name, result.stdout.strip())
        if result.stderr:
            logger.warning("[%s] stderr:\n%s", task.name, result.stderr.strip())

        if result.returncode == 0:
            logger.info("'%s' concluída em %.1fs (exit 0)", task.name, elapsed)
            return True

        logger.error(
            "'%s' terminou com exit code %d (tentativa %d/%d, %.1fs)",
            task.name, result.returncode, attempt, attempts, elapsed,
        )

    logger.error("'%s' falhou em todas as %d tentativa(s)", task.name, attempts)
    return False
