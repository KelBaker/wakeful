"""Entry point: `wakeful` ou `python -m wakeful` sobem o scheduler em foreground.

Roda como processo comum na sessão do usuário logado (não como Windows Service) —
automação de interface precisa da sessão interativa, um serviço roda isolado
na Session 0 e não teria acesso ao desktop. Ver docs/windows-setup.md.
"""
from __future__ import annotations

import argparse
import logging
import signal
import sys
import time

from wakeful.config import load_config
from wakeful.logging_setup import setup_logging
from wakeful.scheduler import build_scheduler

logger = logging.getLogger("wakeful")


def main() -> None:
    parser = argparse.ArgumentParser(prog="wakeful")
    parser.add_argument(
        "-c", "--config", default="config.yaml", help="Caminho do arquivo de config (default: config.yaml)"
    )
    args = parser.parse_args()

    try:
        config = load_config(args.config)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Erro no config: {exc}", file=sys.stderr)
        sys.exit(1)

    setup_logging(config.logging)

    if not config.tasks:
        logger.warning("Nenhuma tarefa configurada em '%s' — nada a agendar.", args.config)

    scheduler = build_scheduler(config)
    scheduler.start()
    logger.info("wakeful rodando com %d tarefa(s). Ctrl+C pra sair.", len(config.tasks))

    stop = {"flag": False}

    def _handle_sigint(signum, frame):
        stop["flag"] = True

    signal.signal(signal.SIGINT, _handle_sigint)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _handle_sigint)

    try:
        while not stop["flag"]:
            time.sleep(1)
    finally:
        logger.info("Encerrando wakeful...")
        scheduler.shutdown(wait=False)


if __name__ == "__main__":
    main()
